import argparse
import csv
import json
import os
import sys
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SHEET_NAME, SPREADSHEET_ID, STORE_EMAIL_BODY
from email_parser import parse_email
from gmail_service import MAX_UNREAD_MESSAGES, get_gmail_service, get_unread_messages
from logger import logger
from sheets_service import append_row, get_logged_message_ids, get_sheets_service
from state_manager import (
    clear_pending,
    is_processed,
    load_state,
    mark_pending,
    mark_processed,
    save_state,
)


def parse_batch_size(value):
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("limit must be a whole number") from exc
    if not 1 <= size <= MAX_UNREAD_MESSAGES:
        raise argparse.ArgumentTypeError(f"limit must be between 1 and {MAX_UNREAD_MESSAGES}")
    return size


def parse_since_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("since date must use YYYY-MM-DD format") from exc


# ✅ Mark email as read
def mark_email_as_read(service, message_id):
    service.users().messages().modify(
        userId='me',
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


# ✅ Job-related keyword filter
JOB_KEYWORDS = (
    "interview",
    "application",
    "job",
    "internship",
    "hiring",
    "offer",
    "shortlisted",
    "opportunity",
    "career",
    "assessment",
    "position",
    "role",
)
REPLAY_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "samples" / "replay-inbox.json"


class _ReplayRequest:
    def __init__(self, message):
        self.message = message

    def execute(self):
        return self.message


class _ReplayGmailService:
    """Read-only in-memory substitute for the Gmail message lookup used by the parser."""

    def __init__(self, messages):
        self._messages = {message["id"]: message for message in messages}

    def users(self):
        return self

    def messages(self):
        return self

    def get(self, userId, id, format):
        if userId != "me" or format != "full" or id not in self._messages:
            raise ValueError("Replay requested an unknown local sample message.")
        return _ReplayRequest(self._messages[id])


def run_replay_demo(max_results=10, export_csv=None, extra_keywords=(), explain_matches=False):
    """Run the parser and filters against synthetic messages without OAuth or checkpoint access."""
    with REPLAY_FIXTURE_PATH.open(encoding="utf-8") as fixture:
        messages = json.load(fixture)
    if not isinstance(messages, list) or any(
        not isinstance(message, dict)
        or not isinstance(message.get("id"), str)
        or not isinstance(message.get("payload"), dict)
        for message in messages
    ):
        raise ValueError("The bundled replay fixture has an invalid structure.")
    messages = messages[:max_results]
    state = {"processed_ids": set(), "pending_ids": set()}
    result = preview_messages(
        _ReplayGmailService(messages),
        messages,
        state,
        export_csv,
        extra_keywords,
        explain_matches,
    )
    matched, filtered, *_ = result
    logger.info(
        "Fake-inbox replay: %d matched, %d filtered. Synthetic messages only; no Gmail, Sheets, OAuth, or checkpoint was accessed.",
        matched,
        filtered,
    )
    return result


def matching_job_signals(email_data, extra_keywords=()):
    combined_text = (
        email_data["subject"] + " " + email_data["content"]
    ).lower()

    custom_keywords = [str(keyword).strip().lower() for keyword in extra_keywords]
    return tuple(dict.fromkeys(
        keyword for keyword in (*JOB_KEYWORDS, *custom_keywords)
        if keyword and keyword in combined_text
    ))


def is_job_related(email_data, extra_keywords=()):
    return bool(matching_job_signals(email_data, extra_keywords))


# ✅ Block common newsletter / spam senders
def is_blocked_sender(sender):
    blocked_keywords = [
        "newsletter",
        "marketing",
        "promotional",
        "promotions",
        "beehiiv",
    ]

    sender = sender.lower()
    return any(word in sender for word in blocked_keywords)


def spreadsheet_safe_csv_value(value):
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return f"'{text}"
    return value


def preview_messages(
    gmail_service, messages, state, export_path=None, extra_keywords=(), explain_matches=False,
):
    seen_ids = set()
    matched = filtered = already_processed = pending = blocked_senders = no_job_signal = 0
    with (open(export_path, "w", newline="", encoding="utf-8") if export_path else nullcontext()) as output:
        writer = csv.writer(output) if output else None
        if writer:
            writer.writerow(["From", "Subject", "Date", "Content", "Gmail message ID"])
        for message in messages:
            message_id = message.get("id")
            if not message_id or message_id in seen_ids:
                continue
            seen_ids.add(message_id)
            if is_processed(state, message_id):
                already_processed += 1
                continue
            if message_id in state["pending_ids"]:
                pending += 1
                continue
            email_data = parse_email(gmail_service, message_id)
            if is_blocked_sender(email_data["from"]):
                filtered += 1
                blocked_senders += 1
                continue
            if not is_job_related(email_data, extra_keywords):
                filtered += 1
                no_job_signal += 1
                continue
            matched += 1
            if explain_matches:
                logger.info("Dry-run match signals: %s", ", ".join(matching_job_signals(email_data, extra_keywords)))
            if writer:
                values = [email_data["from"], email_data["subject"], email_data["date"],
                          email_data["content"][:1000] if STORE_EMAIL_BODY else "", message_id]
                writer.writerow([spreadsheet_safe_csv_value(value) for value in values])
    return matched, filtered, already_processed, pending, blocked_senders, no_job_signal


def write_receipt(path, message_id, outcome):
    if not path:
        return
    receipt = {
        "message_id": message_id,
        "outcome": outcome,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    try:
        with open(path, "a", encoding="utf-8") as file:
            file.write(json.dumps(receipt, ensure_ascii=True) + "\n")
    except OSError as exc:
        logger.warning("Could not write local receipt: %s", exc)


def process_messages(
    gmail_service, sheets_service, messages, state, spreadsheet_id, sheet_name,
    store_email_body=False, extra_keywords=(), keep_unread=False, receipt_jsonl=None,
):
    message_ids = []
    seen_ids = set()
    for message in messages:
        message_id = message["id"]
        if message_id not in seen_ids:
            message_ids.append(message_id)
            seen_ids.add(message_id)

    pending_ids = state["pending_ids"]
    if pending_ids:
        logged_ids = get_logged_message_ids(sheets_service, spreadsheet_id, sheet_name)
        for message_id in pending_ids & logged_ids:
            mark_processed(state, message_id)
            clear_pending(state, message_id)
        if pending_ids:
            message_ids.extend(sorted(pending_ids - seen_ids))
        save_state(state)

    for msg_id in message_ids:
        if is_processed(state, msg_id):
            write_receipt(receipt_jsonl, msg_id, "already_processed")
            if not keep_unread:
                mark_email_as_read(gmail_service, msg_id)
            continue

        email_data = parse_email(gmail_service, msg_id)
        if is_blocked_sender(email_data["from"]) or not is_job_related(email_data, extra_keywords):
            if not keep_unread:
                mark_email_as_read(gmail_service, msg_id)
            mark_processed(state, msg_id)
            save_state(state)
            write_receipt(receipt_jsonl, msg_id, "filtered")
            continue

        if msg_id not in state["pending_ids"]:
            mark_pending(state, msg_id)
            save_state(state)

        append_row(sheets_service, spreadsheet_id, sheet_name, [
            email_data["from"],
            email_data["subject"],
            email_data["date"],
            email_data["content"][:1000] if store_email_body else "",
            msg_id,
        ])
        mark_processed(state, msg_id)
        clear_pending(state, msg_id)
        save_state(state)
        write_receipt(receipt_jsonl, msg_id, "sheet_row_appended")
        logger.info("Logged a job email")
        if not keep_unread:
            mark_email_as_read(gmail_service, msg_id)


def main(
    dry_run=False, max_results=10, export_csv=None, since=None,
    extra_keywords=(), status=False, keep_unread=True, explain_matches=False,
    receipt_jsonl=None, replay_demo=False,
):
    if replay_demo:
        if status or not keep_unread or receipt_jsonl or since:
            logger.error("--replay-demo cannot be combined with --status, --mark-read, --receipt-jsonl, or --since.")
            return
        if not 1 <= max_results <= MAX_UNREAD_MESSAGES:
            logger.error("Message limit must be between 1 and %d.", MAX_UNREAD_MESSAGES)
            return
        try:
            return run_replay_demo(max_results, export_csv, extra_keywords, explain_matches)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Could not run the local replay: %s", exc)
            return
    if status:
        state = load_state()
        logger.info("Local checkpoint: %d processed, %d pending reconciliation items.",
                    len(state["processed_ids"]), len(state["pending_ids"]))
        return
    if type(max_results) is not int or not 1 <= max_results <= MAX_UNREAD_MESSAGES:
        logger.error("Message limit must be between 1 and %d.", MAX_UNREAD_MESSAGES)
        return
    if export_csv and not dry_run:
        logger.error("--export-csv requires --dry-run; no Gmail or Sheets changes were made.")
        return

    if not dry_run and not SPREADSHEET_ID:
        logger.error("Set SPREADSHEET_ID before running the tracker.")
        return

    try:
        state = load_state()
    except (TypeError, ValueError) as exc:
        logger.error("Cannot use the local checkpoint: %s", exc)
        return

    try:
        gmail_service = get_gmail_service(read_only=dry_run or keep_unread)
        sheets_service = None if dry_run else get_sheets_service()
    except FileNotFoundError:
        logger.error(
            "credentials/credentials.json not found. "
            "Download OAuth credentials from Google Cloud Console and place them there."
        )
        return

    if since:
        messages = get_unread_messages(gmail_service, max_results=max_results, since=since)
    else:
        messages = get_unread_messages(gmail_service, max_results=max_results)
    if not messages and not state["pending_ids"] and not (dry_run and export_csv):
        logger.info("No new unread emails found.")
        return

    if dry_run:
        try:
            matched, filtered, processed, pending, blocked, no_signal = preview_messages(
                gmail_service, messages, state, export_csv, extra_keywords, explain_matches
            )
        except OSError as exc:
            logger.error("Could not write CSV export: %s", exc)
            return
        logger.info(
            "Dry run: %d job-related, %d filtered (%d blocked senders, %d without job signals), %d already logged, and %d pending reconciliation items left untouched%s. No Sheets rows or Gmail labels were changed.",
            matched, filtered, blocked, no_signal, processed, pending,
            f"; matched rows exported to {export_csv}" if export_csv else "",
        )
        return

    process_messages(
        gmail_service, sheets_service, messages, state,
        SPREADSHEET_ID, SHEET_NAME, STORE_EMAIL_BODY, extra_keywords, keep_unread,
        receipt_jsonl,
    )
    logger.info("🎉 Processing completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Track job-related Gmail messages in Google Sheets.")
    parser.add_argument("--dry-run", action="store_true", help="Preview unread email matches without changing Gmail or Sheets.")
    parser.add_argument("--export-csv", metavar="PATH", help="Save matched dry-run rows to a local CSV file (requires --dry-run).")
    parser.add_argument("--since", type=parse_since_date, metavar="YYYY-MM-DD", help="Scan unread messages received after this date.")
    parser.add_argument("--job-keyword", action="append", default=[], metavar="WORD", help="Also match this job-related word or phrase; may be repeated.")
    parser.add_argument("--explain-matches", action="store_true", help="In dry-run mode, log only matching keyword labels (not email details).")
    parser.add_argument("--status", action="store_true", help="Show local checkpoint counts without signing in to Gmail.")
    gmail_action = parser.add_mutually_exclusive_group()
    gmail_action.add_argument("--keep-unread", dest="keep_unread", action="store_true", help="Keep matched messages unread (default).")
    gmail_action.add_argument("--mark-read", dest="keep_unread", action="store_false", help="Remove the UNREAD label after logging; grants Gmail modify access.")
    parser.set_defaults(keep_unread=True)
    parser.add_argument("--receipt-jsonl", metavar="PATH", help="Append per-message outcome receipts (message IDs only; no email content).")
    parser.add_argument("--replay-demo", action="store_true", help="Run synthetic inbox messages through the parser without OAuth, Gmail, Sheets, or checkpoint access.")
    parser.add_argument(
        "--limit",
        type=parse_batch_size,
        default=10,
        metavar="N",
        help=f"Max unread Inbox messages to scan this run (1-{MAX_UNREAD_MESSAGES}; default: 10).",
    )
    arguments = parser.parse_args()
    main(
        dry_run=arguments.dry_run,
        max_results=arguments.limit,
        export_csv=arguments.export_csv,
        since=arguments.since,
        extra_keywords=arguments.job_keyword,
        status=arguments.status,
        keep_unread=arguments.keep_unread,
        explain_matches=arguments.explain_matches,
        receipt_jsonl=arguments.receipt_jsonl,
        replay_demo=arguments.replay_demo,
    )
