# JobMail SaaS beta

This Django app is separate from the local Gmail-to-Sheets utility. It offers user accounts and a private, user-entered job application pipeline. It does **not** connect to Gmail or claim revenue. The displayed ₹299/month is a proposed pricing hypothesis that needs buyer validation.

## Run locally

```powershell
cd saas
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
$env:DJANGO_DEBUG='true'
python manage.py migrate
python manage.py runserver
```

In local development, account activation and password-reset messages print to the terminal. Use a dedicated test account and synthetic job records.

## Current workflow

- Signup creates an inactive account and sends a signed, 24-hour activation link.
- Django provides login, logout, and password reset. Reset/activation emails require SMTP configuration outside local development.
- Users can create, edit, delete, and export their own applications. Other users' records are scoped out.
- The dashboard can search company, role, and source; filter by status and due/overdue follow-up; and paginate while retaining filters.
- CSV import accepts the JobMail export format, previews rows, validates fields, skips duplicates, and saves only after confirmation. Uploads are limited to 1 MB and 100 rows; the free-beta cap is enforced before importing.
- Free beta allows 25 tracked applications. Pro is intended to remove that cap; payment is unavailable until a Razorpay plan and test keys are configured.
- Account removal is blocked while a provider subscription can still bill. Cancel and wait for provider confirmation first.
- Product update consent is optional and unchecked by default. No marketing sequence is sent by this app yet.
- `/health/`, `/robots.txt`, and `/sitemap.xml` are available.

## Billing safety

Use test keys with `RAZORPAY_MODE=test` first. The server creates a subscription using the configured `RAZORPAY_PLAN_ID` and redirects to Razorpay's hosted link. It verifies webhooks against the raw request bytes and rejects duplicate event IDs. The app does not see card numbers. Never set live keys or `LIVE_BILLING_ENABLED=true` until the owner has tested checkout, activation, failed payment, cancellation, and webhook replay in test mode.

## Production environment

For the free deployment path, follow [`deploy/oci/README.md`](deploy/oci/README.md). It runs Django and PostgreSQL together on one OCI Always Free VM, with Caddy providing HTTPS. Free-tier use is best-effort and has no uptime SLA. The old paid Render blueprint is retained as `../render.paid.yaml`; do not use it for the zero-cost setup.

The OCI environment uses a founder-owned sender via SMTP for transactional account messages. Keep Razorpay in test mode until the founder account, plan, webhook, business details, and test lifecycle have been verified. Never enable live billing without owner approval and legal/tax readiness.

## Backup and restore

The OCI guide includes a daily local database dump with rotation and a restore script. This is not an off-site backup; copy encrypted backups to a separate private location and perform a restore drill before inviting real customers. Do not keep database dumps in this Git repository or public object storage.

## Verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test tracker
python manage.py collectstatic --noinput
```

Tests cover login isolation, application create/edit/export/delete, CSV import preview and limits, search/status/follow-up filters, missing billing configuration, and signed/idempotent webhook intake. They do not prove live email, Razorpay, or deployment behavior.
