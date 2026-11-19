import csv
import json
import tempfile
import unittest
from argparse import ArgumentTypeError
from pathlib import Path
from unittest.mock import Mock, patch

from gmail_service import MAX_UNREAD_MESSAGES, get_unread_messages
from main import (
    is_blocked_sender,
    is_job_related,
    main,
    matching_job_signals,
    parse_batch_size,
    parse_since_date,
    preview_messages,
    process_messages,
    run_replay_demo,
)


class MessageProcessingTests(unittest.TestCase):
    def test_replay_demo_uses_synthetic_messages_without_auth_or_checkpoint(self):
        with patch("main.get_gmail_service", side_effect=AssertionError("Gmail must not be reached")), \
             patch("main.get_sheets_service", side_effect=AssertionError("Sheets must not be reached")), \
             patch("main.load_state", side_effect=AssertionError("checkpoint must not be read")), \
             patch("main.logger.info"):
            result = run_replay_demo()

        self.assertEqual(result, (1, 2, 0, 0, 1, 1))

    def test_replay_demo_exports_only_the_synthetic_match_and_keeps_body_blank(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "replay.csv"
            with patch("main.STORE_EMAIL_BODY", False), patch("main.logger.info"):
                run_replay_demo(export_csv=path)
            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1][1:], ["Interview invitation", "2026-11-16 10:00:00", "", "demo-interview-001"])

    def test_replay_demo_rejects_gmail_side_effect_flags(self):
        with patch("main.logger.error") as log_error, patch("main.get_gmail_service") as get_service:
            main(replay_demo=True, keep_unread=False)
        log_error.assert_called_once()
        get_service.assert_not_called()

    def test_normal_run_keeps_gmail_read_only_unless_mark_read_is_selected(self):
        shared_patches = (
            patch("main.get_gmail_service", return_value=Mock()),
            patch("main.get_sheets_service"),
            patch("main.get_unread_messages", return_value=[]),
            patch("main.load_state", return_value={"processed_ids": set(), "pending_ids": set()}),
            patch("main.logger.info"),
            patch("main.SPREADSHEET_ID", "sheet-id"),
        )
        with shared_patches[0] as get_service, shared_patches[1], shared_patches[2], \
             shared_patches[3], shared_patches[4], shared_patches[5]:
            main()
        get_service.assert_called_once_with(read_only=True)

        with shared_patches[0] as get_service, shared_patches[1], shared_patches[2], \
             shared_patches[3], shared_patches[4], shared_patches[5]:
            main(keep_unread=False)
        get_service.assert_called_once_with(read_only=False)

    def test_job_platform_senders_are_not_blocked_by_platform_name(self):
        for sender in (
            "no-reply@company.example",
            "Recruiter <recruiter@linkedin.com>",
            "jobs@internshala.com",
            "opportunities@unstop.com",
            "jobs@fastweb.com",
        ):
            with self.subTest(sender=sender):
                self.assertFalse(is_blocked_sender(sender))

    def test_invalid_checkpoint_stops_before_authentication_or_inbox_access(self):
        with patch("main.load_state", side_effect=ValueError("checkpoint is invalid")), \
             patch("main.get_gmail_service") as get_service, \
             patch("main.get_unread_messages") as get_messages, \
             patch("main.logger.error") as log_error:
            main(dry_run=True)

        get_service.assert_not_called()
        get_messages.assert_not_called()
        log_error.assert_called_once()

    def test_batch_size_parser_enforces_gmail_request_bounds(self):
        self.assertEqual(parse_batch_size("1"), 1)
        self.assertEqual(parse_batch_size(str(MAX_UNREAD_MESSAGES)), MAX_UNREAD_MESSAGES)
        for value in ("0", str(MAX_UNREAD_MESSAGES + 1), "many"):
            with self.subTest(value=value), self.assertRaises(ArgumentTypeError):
                parse_batch_size(value)

    def test_since_date_parser_requires_iso_date(self):
        self.assertEqual(parse_since_date("2026-11-01"), "2026-11-01")
        with self.assertRaises(ArgumentTypeError):
            parse_since_date("11/01/2026")

    def test_custom_job_keywords_extend_default_matching(self):
        email = {"subject": "Research fellowship", "content": "The lab is welcoming candidates."}
        self.assertFalse(is_job_related(email))
        self.assertFalse(is_job_related(email, [""]))
        self.assertTrue(is_job_related(email, ["fellowship"]))

    def test_explain_matches_reports_only_signal_labels_not_message_content(self):
        email = {
            "from": "recruiter@private.example",
            "subject": "Interview invite for candidate@example.com",
            "content": "Your secret-token-123 assessment is ready.",
        }
        self.assertEqual(matching_job_signals(email, [" assessment "]), ("interview", "assessment"))
        state = {"processed_ids": set(), "pending_ids": set()}
        with patch("main.parse_email", return_value=email), patch("main.logger.info") as log:
            preview_messages(Mock(), [{"id": "private-message-id"}], state, explain_matches=True)

        log.assert_called_once_with("Dry-run match signals: %s", "interview, assessment")
        self.assertNotIn("candidate@example.com", str(log.call_args))
        self.assertNotIn("secret-token-123", str(log.call_args))

    def test_status_reads_checkpoint_without_gmail_authentication(self):
        state = {"processed_ids": {"one", "two"}, "pending_ids": {"three"}}
        with patch("main.load_state", return_value=state), \
             patch("main.logger.info") as log, \
             patch("main.get_gmail_service") as get_service:
            main(status=True)
        log.assert_called_once_with("Local checkpoint: %d processed, %d pending reconciliation items.", 2, 1)
        get_service.assert_not_called()

    def test_unread_query_rejects_out_of_range_limits_before_api_call(self):
        service = Mock()
        for value in (0, MAX_UNREAD_MESSAGES + 1, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                get_unread_messages(service, max_results=value)
        service.users.assert_not_called()

    def test_dry_run_passes_an_explicit_limit_to_gmail_read_only_query(self):
        gmail = Mock()
        with patch("main.get_gmail_service", return_value=gmail) as get_service, \
             patch("main.get_unread_messages", return_value=[]) as get_messages, \
             patch("main.load_state", return_value={"processed_ids": set(), "pending_ids": set()}), \
             patch("main.logger.info"):
            main(dry_run=True, max_results=42)

        get_service.assert_called_once_with(read_only=True)
        get_messages.assert_called_once_with(gmail, max_results=42)

    def test_preview_counts_without_mutating_gmail_sheets_or_checkpoint(self):
        state = {
            "processed_ids": {"logged"},
            "pending_ids": {"pending"},
        }
        emails = {
            "job": {"from": "recruiter@example.com", "subject": "Interview invite", "content": "Let's talk"},
            "promo": {"from": "newsletter@example.com", "subject": "Application tips", "content": "A newsletter"},
            "other": {"from": "person@example.com", "subject": "Welcome", "content": "Your account is ready"},
        }
        gmail = Mock()
        messages = [{"id": key} for key in ("job", "promo", "other", "logged", "pending", "job")]

        with patch("main.parse_email", side_effect=lambda _, message_id: emails[message_id]) as parse, \
             patch("main.append_row") as append, \
             patch("main.mark_email_as_read") as mark_read, \
             patch("main.save_state") as save:
            result = preview_messages(gmail, messages, state)

        self.assertEqual(result, (1, 2, 1, 1, 1, 1))
        self.assertEqual(parse.call_count, 3)
        append.assert_not_called()
        mark_read.assert_not_called()
        save.assert_not_called()
        self.assertEqual(state, {"processed_ids": {"logged"}, "pending_ids": {"pending"}})

    def test_dry_run_csv_exports_only_matches_and_keeps_body_blank_by_default(self):
        state = {"processed_ids": set(), "pending_ids": set()}
        emails = {
            "job": {"from": "recruiter@example.com", "subject": "=Interview invite", "date": "2026-01-15", "content": "Private body"},
            "noise": {"from": "newsletter@example.com", "subject": "Application tips", "date": "2026-01-15", "content": "Newsletter"},
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "preview.csv"
            with patch("main.parse_email", side_effect=lambda _, message_id: emails[message_id]), \
                 patch("main.STORE_EMAIL_BODY", False):
                result = preview_messages(Mock(), [{"id": "job"}, {"id": "noise"}], state, path)

            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))

        self.assertEqual(result, (1, 1, 0, 0, 1, 0))
        self.assertEqual(rows[0], ["From", "Subject", "Date", "Content", "Gmail message ID"])
        self.assertEqual(rows[1], ["recruiter@example.com", "'=Interview invite", "2026-01-15", "", "job"])

    def test_dry_run_csv_escapes_formula_prefixes_after_leading_whitespace(self):
        state = {"processed_ids": set(), "pending_ids": set()}
        email = {
            "from": "recruiter@example.com", "subject": "  =HYPERLINK(\"https://bad.example\") interview",
            "date": "2026-01-15", "content": "\n+SUM(1,1)",
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "preview.csv"
            with patch("main.parse_email", return_value=email), patch("main.STORE_EMAIL_BODY", True):
                preview_messages(Mock(), [{"id": "job"}], state, path)
            with path.open(newline="", encoding="utf-8") as file:
                row = list(csv.reader(file))[1]

        self.assertEqual(row[1], "'  =HYPERLINK(\"https://bad.example\") interview")
        self.assertEqual(row[3], "'\n+SUM(1,1)")

    def test_csv_export_requires_dry_run_before_authentication(self):
        with patch("main.get_gmail_service") as get_service, patch("main.logger.error"):
            main(export_csv="preview.csv")
        get_service.assert_not_called()

    def test_empty_dry_run_still_creates_csv_header(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "preview.csv"
            with patch("main.get_gmail_service", return_value=Mock()), \
                 patch("main.get_unread_messages", return_value=[]), \
                 patch("main.load_state", return_value={"processed_ids": set(), "pending_ids": set()}), \
                 patch("main.logger.info"):
                main(dry_run=True, export_csv=path)
            with path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.reader(file))
        self.assertEqual(rows, [["From", "Subject", "Date", "Content", "Gmail message ID"]])

    def test_successful_append_persists_id_before_marking_read(self):
        gmail = Mock()
        state = {"processed_ids": set(), "pending_ids": set()}
        email = {
            "from": "recruiter@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Details",
        }
        events = []

        with patch("main.parse_email", return_value=email), \
             patch("main.append_row", side_effect=lambda *args: events.append("append")), \
             patch("main.save_state", side_effect=lambda _: events.append("save")), \
             patch("main.mark_email_as_read", side_effect=lambda *args: events.append("read")):
            process_messages(gmail, Mock(), [{"id": "message-1"}], state, "sheet", "Sheet1")

        self.assertEqual(events, ["save", "append", "save", "read"])
        self.assertIn("message-1", state["processed_ids"])
        self.assertNotIn("message-1", state["pending_ids"])

    def test_write_receipt_records_outcome_without_email_content(self):
        state = {"processed_ids": set(), "pending_ids": set()}
        email = {
            "from": "private@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Confidential message body",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipts.jsonl"
            with patch("main.parse_email", return_value=email), \
                 patch("main.append_row"), patch("main.save_state"), \
                 patch("main.mark_email_as_read"):
                process_messages(
                    Mock(), Mock(), [{"id": "message-1"}], state, "sheet", "Sheet1",
                    receipt_jsonl=path,
                )
            receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["message_id"], "message-1")
        self.assertEqual(receipt["outcome"], "sheet_row_appended")
        self.assertIn("recorded_at", receipt)
        self.assertNotIn("private@example.com", str(receipt))
        self.assertNotIn("Confidential message body", str(receipt))

    def test_keep_unread_logs_and_checkpoints_without_changing_gmail_labels(self):
        state = {"processed_ids": set(), "pending_ids": set()}
        email = {
            "from": "recruiter@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Details",
        }
        with patch("main.parse_email", return_value=email), \
             patch("main.append_row") as append, \
             patch("main.mark_email_as_read") as mark_read, \
             patch("main.save_state"):
            process_messages(
                Mock(), Mock(), [{"id": "message-1"}], state,
                "sheet", "Sheet1", keep_unread=True,
            )
        append.assert_called_once()
        mark_read.assert_not_called()
        self.assertIn("message-1", state["processed_ids"])

    def test_recovers_a_sheet_write_that_succeeded_before_crash(self):
        state = {"processed_ids": set(), "pending_ids": {"message-1"}}

        with patch("main.get_logged_message_ids", return_value={"message-1"}), \
             patch("main.append_row") as append, \
             patch("main.parse_email") as parse, \
             patch("main.save_state"):
            process_messages(Mock(), Mock(), [], state, "sheet", "Sheet1")

        append.assert_not_called()
        parse.assert_not_called()
        self.assertIn("message-1", state["processed_ids"])
        self.assertFalse(state["pending_ids"])

    def test_retries_a_pending_write_missing_from_the_sheet(self):
        state = {"processed_ids": set(), "pending_ids": {"message-1"}}
        email = {
            "from": "recruiter@example.com",
            "subject": "Interview invite",
            "date": "2026-01-15 10:00:00",
            "content": "Details",
        }

        with patch("main.get_logged_message_ids", return_value=set()), \
             patch("main.parse_email", return_value=email), \
             patch("main.append_row") as append, \
             patch("main.save_state"), \
             patch("main.mark_email_as_read"):
            process_messages(Mock(), Mock(), [], state, "sheet", "Sheet1")

        append.assert_called_once()
        self.assertIn("message-1", state["processed_ids"])
        self.assertFalse(state["pending_ids"])

    def test_persisted_processed_message_is_never_appended_twice(self):
        state = {"processed_ids": {"message-1"}, "pending_ids": set()}

        with patch("main.append_row") as append, patch("main.mark_email_as_read"):
            process_messages(Mock(), Mock(), [{"id": "message-1"}], state, "sheet", "Sheet1")

        append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
