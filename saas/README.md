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
- Free beta allows 25 tracked applications. Pro is intended to remove that cap; payment is unavailable until a Razorpay plan and test keys are configured.
- Account removal is blocked while a provider subscription can still bill. Cancel and wait for provider confirmation first.
- Product update consent is optional and unchecked by default. No marketing sequence is sent by this app yet.
- `/health/`, `/robots.txt`, and `/sitemap.xml` are available.

## Billing safety

Use test keys with `RAZORPAY_MODE=test` first. The server creates a subscription using the configured `RAZORPAY_PLAN_ID` and redirects to Razorpay's hosted link. It verifies webhooks against the raw request bytes and rejects duplicate event IDs. The app does not see card numbers. Never set live keys or `LIVE_BILLING_ENABLED=true` until the owner has tested checkout, activation, failed payment, cancellation, and webhook replay in test mode.

## Production environment

The Render Blueprint is at repository root `render.yaml`. It expects a Render web service and PostgreSQL database. Add the following values only in the founder-owned service dashboard:

- `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`
- `DEFAULT_FROM_EMAIL` and verified SMTP host/user/password
- Razorpay test `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`, and `RAZORPAY_PLAN_ID`
- `PRO_PRICE_DISPLAY` that exactly matches the provider plan
- Optional `SENTRY_DSN` to enable error reporting without sending user PII

Do not configure live billing until test lifecycle proof exists. Follow Django's production deployment checklist and run `python manage.py check --deploy` in the deployed environment.

## Backup and restore

PostgreSQL backups are not automated by this app. Configure provider backups before inviting real customers. Use the provider's native backup and restore process; do not keep database dumps in this Git repository or public object storage. A documented owner-run drill is still required before calling operations production-ready.

## Verification

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test tracker
python manage.py collectstatic --noinput
```

Tests cover login isolation, application creation/export/delete, missing billing configuration, and signed/idempotent webhook intake. They do not prove live email, Razorpay, or deployment behavior.
