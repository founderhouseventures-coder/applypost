# JobMail owner inputs required

These steps need the founder's Google account and a dedicated test inbox. No OAuth client credentials, token, `.env`, or spreadsheet ID are present in this worktree. Do not upload credentials or inbox data to GitHub or Vercel.

The public contact address is `founderhouse.ventures@gmail.com`; it received and completed Vercel identity verification.

## 1. Create a founder-controlled Google OAuth client

1. Open [Google Cloud Console](https://console.cloud.google.com/) while signed in as the founder.
2. Create/select a project, then enable **Gmail API** and **Google Sheets API**.
3. Configure the OAuth consent screen as **External**, add only the dedicated test inbox as a test user, and create an OAuth client of type **Desktop app**.
4. Download its client JSON into the local repository folder `credentials/credentials.json`. Keep that file private and untracked.

## 2. Set up a disposable test sheet and run the checks

1. Create a blank Google Sheet under the founder account and copy its ID from the URL between `/d/` and `/edit`.
2. Copy `.env.example` to `.env` locally, then set:

   ```dotenv
   SPREADSHEET_ID=<ID from the disposable test Sheet>
   SHEET_NAME=Sheet1
   STORE_EMAIL_BODY=false
   ```

3. Put synthetic job alerts and unrelated messages in the dedicated test inbox; do not use a real inbox for the first run.
4. Run `python src/main.py --dry-run` and confirm the consent prompt requests Gmail read-only access, then verify preview does not change messages.
5. Run `python src/main.py` and confirm the consent prompt requests Sheets access, then verify only matching rows reach the disposable sheet and duplicates are not appended.
6. Do not run `--mark-read` without a separate explicit decision; it requests broader Gmail modify access.
7. Revoke the test OAuth token when finished. Public multi-user use still needs Google OAuth consent verification.

## 3. Connect the shared LeadHub signup

- JobMail's signup and recommendations stay hidden because `site/index.html` has an empty `leadhub-url` setting.
- The shared service is now copied to the private founder repo [`founderhouseventures-coder/leadhub`](https://github.com/founderhouseventures-coder/leadhub), commit `2b38514`; its four local tests and founder GitHub CI pass. The previous personal repo remains unchanged, and the local `previous-personal` remote is retained only as a reference.
- To activate this funnel, deploy `founderhouseventures-coder/leadhub` as a Render Blueprint. Its current blueprint requires the paid Starter plan and persistent disk. It also needs a public HTTPS `BASE_URL`, Resend account/API key, verified sender for `MAIL_FROM`, and generated `ADMIN_TOKEN`/per-project event keys. Keep all secret values in the service dashboard, not chat or GitHub.
- Once the founder-owned service is live and its confirmation/unsubscribe flow is verified, provide its HTTPS origin. Then the JobMail widget can be configured and redeployed.

## Current evidence

- Synthetic offline replay, 43 JobMail unit tests, 4 LeadHub local tests, Ruff, compile checks, static-site checks, and Node tests passed locally. GitHub CI and Vercel deployment are verified in the founder repo for the current published revision.
- Live production host: `https://jobmail-ruby.vercel.app/`.
- Real OAuth, inbox read, Sheets write, and the shared signup have not been run against live services because the required local credentials, test inbox/sheet, and deployed LeadHub are not present.
