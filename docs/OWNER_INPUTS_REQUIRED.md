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

## 4. SaaS production setup (free OCI path)

The Django app in `saas/` is not deployed. The free deployment bundle is in `saas/deploy/oci/README.md`: Django, PostgreSQL, and Caddy run on one founder OCI Always Free VM. No OCI account or server credentials are connected here, so provisioning is still founder-only. Always Free has no SLA; Oracle may reclaim underused compute.

1. Create/sign in to the founder's Oracle Cloud Free Tier account, complete card verification without upgrading, and provision only an Always Free Ubuntu A1 VM within the console's quotas.
2. Create a DuckDNS hostname, point it to the VM, and restrict SSH ingress to the founder's current IP. Keep its token private.
3. Follow the repo's OCI guide to configure `saas/.env`, deploy the containers, and verify HTTPS plus `/health/`.
4. Add a founder Gmail App Password only to the server `.env` for low-volume account emails; test signup activation and password reset.
5. Use Razorpay Test Mode only. The owner must complete merchant onboarding, supply test plan and webhook credentials on the server, and verify checkout/cancellation/webhook tests.
6. Before live billing, complete legal/tax review, pricing validation, off-server encrypted backups, a restore drill, and account-specific Razorpay live approval. Keep live keys and `LIVE_BILLING_ENABLED=true` off until then.

## 5. Product and compliance owner work

- Validate recurring willingness to pay and decide whether the 25-item free cap / proposed ₹299 monthly tier solves a real repeated problem.
- Provide accurate business identity, support email/domain, jurisdiction, refund/cancellation rules, privacy retention/deletion policy, and terms for professional review.
- Gmail server sync is deliberately excluded. `gmail.readonly` is a restricted scope and Google may require verification and a security assessment when restricted data is stored/transmitted on servers. Use local client mode until approvals are complete.

## Current evidence

- Synthetic offline replay, 43 JobMail unit tests, 4 LeadHub local tests, Ruff, compile checks, static-site checks, and Node tests passed locally. GitHub CI and Vercel deployment are verified in the founder repo for the current published revision.
- Live production host: `https://jobmail-ruby.vercel.app/`.
- Real OAuth, inbox read, Sheets write, and the shared signup have not been run against live services because the required local credentials, test inbox/sheet, and deployed LeadHub are not present.
