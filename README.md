# JobMail

**JobMail helps job seekers keep applications and follow-ups in one clear pipeline.**

[Open the product site](https://founderhouseventures-coder.github.io/applypost/) · [Run the script](#run-the-script) · [Review privacy and OAuth](#oauth-flow-explanation)

---

## Product status

The repository now contains two pieces: the existing local-first Gmail → Google Sheets utility (`src/`) and a new Django SaaS beta (`saas/`). The SaaS currently tracks applications entered by the user; it does not request Gmail access or sync inboxes. The production SaaS, outgoing email, and payment account are not configured yet. Its proposed ₹299/month price is an unvalidated beta hypothesis, not an active charge or proven revenue.

To run the web beta locally, see [`saas/README.md`](saas/README.md). The original CLI still works independently.

## Project overview

JobMail is a Python automation tool that connects to the **Gmail API** and **Google Sheets API** through **OAuth 2.0**. It runs on your computer; the companion product site is static and uses fictional sample messages only.

The [JobMail product site](https://founderhouseventures-coder.github.io/applypost/) is a static overview. Its sample sorter can reveal and copy fictional spreadsheet-ready rows so you can review the output shape; it does not connect to Gmail or Sheets and contains no real email data.

## Paid setup support

JobMail itself runs locally and does not require a subscription. If you want help configuring Gmail/Sheets OAuth, filters, and a safe first preview, request a one-off setup session by email; scope and fee are agreed before work starts. Never email passwords, OAuth tokens, inbox exports, or private messages. No paid customers or revenue are claimed.

It reads real unread emails from a Gmail inbox, intelligently filters job-related emails, extracts structured information, and appends the data into a Google Sheet in an append-only and duplicate-safe manner.

The system is designed to be **idempotent**, meaning running the script multiple times will not create duplicate rows in the spreadsheet.

---

## 🎯 Objective

For each qualifying unread email in the Gmail inbox, the script appends a new row to Google Sheets with the following fields:

| Column | Description |
|--------|------------|
| From | Sender email address |
| Subject | Email subject |
| Date | Date & time received |
| Content | Empty by default; up to 1,000 characters only when `STORE_EMAIL_BODY=true` |
| Gmail message ID | Internal duplicate-recovery key (column E) |

Only **job-related emails** are logged to maintain signal over noise.

---

## 🎯 Smart Job Email Filtering

The system intelligently filters emails to log only job-related messages.

### 🔎 Filtering Logic:
- Keyword-based detection:
  - interview
  - application
  - internship
  - hiring
  - offer
  - shortlisted
  - opportunity
  - assessment
- Sender-based blocking:
  - newsletters and clear marketing/promotional mailers

No-reply senders and job platforms such as LinkedIn, Internshala, Unstop and Fastweb are not blocked by address or brand alone; messages still need a job-related keyword match. Clear newsletter/marketing senders are filtered.

This transforms the system into a focused **Job Opportunity Tracker** instead of a generic email logger.

---

## 🏗️ High-Level Architecture

```
Gmail Inbox
    │
    │ (Gmail API + OAuth 2.0)
    ▼
Python Automation Script
    ├── Email Parsing
    ├── Smart Filtering
    ├── Duplicate Detection (state.json)
    ├── Keep unread by default; mark read only when explicitly requested
    ▼
Google Sheets
```

---

## 🛠️ Tech Stack

- **Language:** Python 3  
- **APIs:** Gmail API, Google Sheets API  
- **Authentication:** OAuth 2.0 (Installed App Flow)  
- **Libraries:**
  - google-api-python-client
  - google-auth
  - google-auth-oauthlib
  - google-auth-httplib2
  - beautifulsoup4
  - python-dateutil

---

## 📂 Project Structure

```
gmail-to-sheets/
├── src/
│   ├── gmail_service.py
│   ├── sheets_service.py
│   ├── email_parser.py
│   ├── state_manager.py
│   └── main.py
│
├── credentials/
│   └── credentials.json (NOT committed)
│
├── proof/
│   ├── inbox.png
│   ├── sheet.png
│   └── oauth.png
│
├── config.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone <YOUR_REPOSITORY_LINK>
cd gmail-to-sheets
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Google Cloud Configuration

1. Create a Google Cloud Project  
2. Enable:
   - Gmail API  
   - Google Sheets API  
3. Configure OAuth Consent Screen (External)  
4. Add your Gmail address as a test user  
5. Create OAuth Client (Desktop App)  
6. Download `credentials.json`  

Place it inside:

```
credentials/credentials.json
```

---

### 4️⃣ Configure Google Sheet

Copy `.env.example` to `.env`, then set the spreadsheet ID and sheet name. Email bodies are not copied to Sheets by default; set `STORE_EMAIL_BODY=true` only if you want that sensitive data stored there.

The normal run uses Gmail read-only access and keeps processed messages unread by default. It writes matching rows to your selected Google Sheet and saves a local checkpoint. `--mark-read` opts into the broader `gmail.modify` scope and removes the UNREAD label after logging. `--dry-run` uses Gmail read-only access and never writes Sheets rows or changes Gmail labels. Review the OAuth consent screen and revoke the token when you no longer use the app.

---

### 5️⃣ Run the Script

<a id="run-the-script"></a>

```bash
python src/main.py --dry-run
python src/main.py --replay-demo
python src/main.py --replay-demo --explain-matches
python src/main.py --dry-run --export-csv jobmail-preview.csv
python src/main.py --dry-run --since 2026-11-01 --job-keyword fellowship
python src/main.py --dry-run --explain-matches
python src/main.py --receipt-jsonl data/run-receipts.jsonl
python src/main.py --status
python src/main.py --keep-unread
python src/main.py --mark-read
python src/main.py
```

Each command scans up to 10 unread Inbox messages by default. Pass `--limit N` to choose a per-run batch from 1 to 500, for example `python src/main.py --dry-run --limit 100`. A larger limit processes more messages in one run. Normal runs keep Gmail messages unread; only `--mark-read` asks for permission to change their labels.

`--replay-demo` runs the real parser and filters against three bundled synthetic Gmail-shaped messages. It does not open OAuth, contact Gmail or Sheets, or read/write the local checkpoint. The sample includes one interview invite, one newsletter, and one unrelated notice. It is safe for first-run setup checks; the normal `--dry-run` still reads the user's inbox.

Use the preview first to see match counts before enabling spreadsheet writes. Add `--export-csv PATH` to save only matched rows from that read-only preview in spreadsheet-ready CSV format. Message bodies stay blank unless `STORE_EMAIL_BODY=true`; the CSV can contain sender and subject details, so keep it private and do not commit it. CSV formula-like values are escaped for spreadsheet safety.

Use `--since YYYY-MM-DD` to scan unread messages received after a date, and repeat `--job-keyword WORD` to include role-specific terms in job matching. `--status` reports local processed and pending counts without opening Gmail or Sheets.

The dry-run summary separates blocked senders from messages without job signals, helping you tune filtering. Add `--explain-matches` to log only which job keyword labels matched; it never logs sender, subject, or body. Sender values are stored as email addresses when the header includes a display name. Normal runs write and checkpoint matches while leaving Gmail's unread labels in place; processed messages will not be logged twice on later runs. Use `--mark-read` only if you explicitly want JobMail to remove the UNREAD label. See `docs/ARCHITECTURE.md` and `docs/FEATURE_ROADMAP.md` for current design and next steps.

`--receipt-jsonl PATH` appends an optional local processing receipt for each message outcome. It contains Gmail message IDs, outcome labels, and UTC timestamps only; protect or delete the file like other local account data.

---

## 🔐 OAuth Flow Explanation

The project uses the OAuth 2.0 Installed App flow.

### On First Run:
- Browser window opens
- Preview grants Gmail read-only access and creates `token-readonly.json` locally
- Normal run grants Gmail read-only and Sheets access and creates `token.json` locally
- `--mark-read` requests Gmail modify access so the script can remove the UNREAD label

### On Subsequent Runs:
- Stored token is reused
- Access tokens refresh automatically

This ensures secure authentication without storing user passwords.

---

## 🧠 Duplicate Prevention Logic

Each Gmail email has a unique **Message ID**. The tracker stores that ID in column E of the Google Sheet and in a local JSON checkpoint. Column E is used to recover safely if a Sheets write succeeds but the API response or process is interrupted before the local checkpoint is updated.

### Execution Flow:

1. Fetch unread emails
2. Skip IDs already in the local checkpoint
3. Save a pending checkpoint before writing a job email
4. Append the row and Message ID to columns A–E
5. Save the completed checkpoint, then mark the email read
6. On restart, check column E to recover an interrupted write without appending it twice

The local state uses sets for constant-time ID checks and is saved by atomic file replacement. Existing state files with a `processed_ids` list are migrated automatically. Add `Gmail message ID` as the header in E1 if the sheet already has a header row.

---

## 💾 State Persistence Method

Processed email IDs are stored locally:

```json
{
  "processed_ids": [
    "message_id_1",
    "message_id_2"
  ]
}
```

### Why This Approach?

- Lightweight
- Fast
- No external database required
- Survives script re-runs
- Simple and reliable for automation tasks

---

## 🛡️ Reliability Guarantees

- Duplicate recovery across interrupted Sheets writes
- Append-only Google Sheets writes
- Message ID-based duplicate detection
- Atomic local checkpoint updates
- Invalid checkpoints fail closed with a repair hint instead of silently resetting duplicate history
- Automatic token refresh; revoked tokens and tokens missing the requested scopes start OAuth again, while temporary refresh failures are surfaced
- Email marked as read after processing
- Smart filtering reduces noise

---

## 🚧 Challenges Faced & Solutions

### Issue: OAuth Insufficient Scope Errors

Encountered:
```
403 Insufficient Authentication Scopes
```

**Cause:** Reusing tokens created with limited permissions.

**Solution:**
- JobMail checks saved OAuth scopes before use and starts the consent flow again when a token is missing a required scope or Google reports `invalid_grant`.
- Temporary refresh failures are returned instead of opening a new login flow, so network errors do not silently change accounts.

---

## ⚠️ Limitations

- Email attachments are not processed
- Only unread Inbox emails are handled
- Local state file not suitable for distributed systems
- Very large inboxes may require pagination handling

---

## 🔄 Future Enhancements

- Filter emails from last 24 hours
- Categorize into multiple Sheet tabs (Interviews, Offers, Applications)
- Add structured logging
- Add pagination for large inboxes
- Replace JSON state with SQLite
- Dockerize and deploy to Cloud Run

---

## 🔐 Security Notice

This project requires Google OAuth credentials.

For security reasons:
- `credentials.json`
- `token.json`
- `state.json`

are not included in this repository.

To run locally, you must create your own Google Cloud OAuth credentials.

---

## ✅ Conclusion

This project demonstrates:

- Secure OAuth-based API integration

## 🧪 Offline tests

Run `python -m unittest discover -s src -p 'test_*.py' -v`. These tests use mocked Gmail and Sheets services and do not access a real account.
- Modular Python architecture
- Idempotent system design
- Smart filtering logic
- Reliable duplicate prevention
- Real-world Gmail → Sheets automation pipeline

It simulates a production-style backend automation workflow suitable for CRM ingestion, job tracking systems, and workflow integrations.

## Optional product updates and related products

The static site includes a double-opt-in LeadHub signup and a related-products prompt. Both stay hidden unless the leadhub-url meta tag in site/index.html contains the verified HTTPS origin of the personal LeadHub service. The visitor must check the update consent box; cross-product suggestions require a separate opt-in checkbox. The form sends only email, consent, a site source label and a honeypot field. It never sends Gmail contents, OAuth tokens, job searches or Sheet data. The current URL is blank, so signup and related-product features are not live. Do not enable them until the LeadHub host, sender, privacy notice and unsubscribe flow are verified.
