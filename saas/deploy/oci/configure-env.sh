#!/usr/bin/env bash
set -euo pipefail
umask 077

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
app_dir="$(cd -- "$script_dir/../.." && pwd)"
env_file="$app_dir/.env"

if [[ -e "$env_file" ]]; then
  echo "Refusing to overwrite existing $env_file." >&2
  exit 1
fi

read -r -p 'DuckDNS hostname (example: jobmail.duckdns.org): ' site_domain
if [[ ! "$site_domain" =~ ^[A-Za-z0-9.-]+$ ]]; then
  echo "Hostname must contain only letters, numbers, dots, and hyphens." >&2
  exit 2
fi
read -r -s -p 'Founder Gmail App Password: ' email_password
printf '\n'
email_password="${email_password// /}"
if [[ -z "$email_password" || ! "$email_password" =~ ^[A-Za-z0-9]+$ ]]; then
  echo "App Password must contain letters and numbers only." >&2
  exit 2
fi

django_secret="$(openssl rand -hex 32)"
postgres_password="$(openssl rand -hex 32)"
cat > "$env_file" <<EOF
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=$django_secret
ALLOWED_HOSTS=$site_domain,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://$site_domain
SECURE_SSL_REDIRECT=true
SITE_URL=https://$site_domain
SITE_DOMAIN=$site_domain
POSTGRES_DB=jobmail
POSTGRES_USER=jobmail
POSTGRES_PASSWORD=$postgres_password
DEFAULT_FROM_EMAIL=JobMail <founderhouse.ventures@gmail.com>
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=founderhouse.ventures@gmail.com
EMAIL_HOST_PASSWORD=$email_password
EMAIL_USE_TLS=true
PRO_PRICE_DISPLAY=INR 299 / month (proposed beta price)
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_PLAN_ID=
RAZORPAY_MODE=test
LIVE_BILLING_ENABLED=false
SENTRY_DSN=
EOF
chmod 600 "$env_file"
unset email_password django_secret postgres_password
echo "Private environment written to $env_file. Secrets were not printed."
