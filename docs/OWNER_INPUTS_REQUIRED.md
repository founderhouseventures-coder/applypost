# JobMail owner inputs required

These steps need founder-owned service accounts and secrets. Do not upload credentials, payment keys, database exports, or inbox data to GitHub.

Google OAuth steps below are only for the optional local Gmail-to-Sheets connector; they are not required to deploy the new SaaS beta.

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

## 4. SaaS production setup (new local foundation)

The Django app in `saas/` has not been deployed. It keeps Gmail data out of its database and uses a Render web service plus PostgreSQL.

1. **Add a payment method to the founder Render workspace.** Current Blueprint planning returned `need_payment_info` for both the web service and Postgres; no resources were created. The proposed minimum is about **$13/month** before bandwidth/storage growth (`0.5c-512mb` web $7 + `0.1c-256mb` Postgres $6). Confirm the exact checkout amount in Render before accepting it. The $0 Hobby workspace does not make paid compute free.
2. After payment is available, deploy the repository Blueprint from `render.yaml`; confirm the exact plan/cost shown in Render before approving the sync.
3. Set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL` to the exact Render host (or owned domain). Do not use wildcards.
4. Configure a verified founder-owned sender and SMTP credentials in Render (`DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`). Verify signup activation and password reset arrive.
5. In Razorpay Test Mode, create a monthly plan, then set `RAZORPAY_KEY_ID` (`rzp_test_...`), `RAZORPAY_KEY_SECRET`, `RAZORPAY_PLAN_ID`, and `RAZORPAY_WEBHOOK_SECRET` in Render. Register webhook URL `https://<jobmail-host>/billing/razorpay/webhook/` for subscription lifecycle events. Set `PRO_PRICE_DISPLAY` to the exact plan amount.
6. Complete test checkout, activation, payment failure, cancellation, duplicate webhook, and account-deletion checks. Do not enter live keys before all tests pass and legal terms are reviewed.
7. Configure database backups and complete an actual restore drill. Then connect alerting/error tracking. Neither is yet configured.
8. Live billing requires deliberate dashboard changes: `RAZORPAY_MODE=live` and `LIVE_BILLING_ENABLED=true`, plus live keys. Do this only after launch approval, legal/tax setup, and test-mode evidence.

## 5. Product and compliance owner work

- Validate recurring willingness to pay and decide whether the 25-item free cap / proposed ₹299 monthly tier solves a real repeated problem.
- Provide accurate business identity, support email/domain, jurisdiction, refund/cancellation rules, privacy retention/deletion policy, and terms for professional review.
- Gmail server sync is deliberately excluded. `gmail.readonly` is a restricted scope and Google may require verification and a security assessment when restricted data is stored/transmitted on servers. Use local client mode until approvals are complete.

## Current evidence

- Synthetic offline replay, 43 JobMail unit tests, 4 LeadHub local tests, Ruff, compile checks, static-site checks, and Node tests passed locally. GitHub CI and Vercel deployment are verified in the founder repo for the current published revision.
- Live production host: `https://jobmail-ruby.vercel.app/`.
- Real OAuth, inbox read, Sheets write, and the shared signup have not been run against live services because the required local credentials, test inbox/sheet, and deployed LeadHub are not present.
