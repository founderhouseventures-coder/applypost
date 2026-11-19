# JobMail SaaS: founder launch checklist

Local code and checks are ready. The SaaS is not live; the existing Vercel URL is the separate static site. Complete these founder-only steps in order.

## 1. Publish the prepared code to the founder GitHub repo (about 5 minutes)

1. Open [founderhouseventures-coder/applypost](https://github.com/founderhouseventures-coder/applypost).
2. In the local repo, review the changes, then commit and push the `main` branch to `origin` (the founder repo). Do not push to `previous-personal` or any company account.
3. Open the repository's **Actions** tab and confirm the new workflow run is green.

## 2. Create the JobMail SaaS on Render (about 15–25 minutes, plus provider setup)

1. Open [Render Dashboard](https://dashboard.render.com/), sign in to the founder workspace, choose **New → Blueprint**, and connect `founderhouseventures-coder/applypost`.
2. Select the repository's `render.yaml`. Before confirming, review the web service and PostgreSQL plan/cost shown by Render; approve only if the monthly spend is acceptable.
3. In the `jobmail-saas` service, set `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL` to its exact HTTPS hostname. Keep `DJANGO_DEBUG=false` and `LIVE_BILLING_ENABLED=false`.
4. Add a verified sender and SMTP credentials in the service's **Environment** page: `DEFAULT_FROM_EMAIL`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`.
5. Wait for **Live**. Open `https://<jobmail-host>/health/` and confirm it returns `{"status":"ok"}`.

## 3. Verify account email (about 10 minutes)

1. Open `https://<jobmail-host>/signup/`, create a test account, and verify the activation email arrives and its link signs in.
2. Use **Forgot password** and confirm the reset email works.
3. Add, edit, export, and delete a synthetic application; verify one account cannot see another account's records.

## 4. Configure Razorpay test mode (about 20–40 minutes)

1. Open [Razorpay Dashboard](https://dashboard.razorpay.com/) and switch to **Test Mode**.
2. Create the monthly test plan. Add its `plan_...` ID and test credentials as Render environment variables: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_PLAN_ID`, `RAZORPAY_WEBHOOK_SECRET`.
3. Set `PRO_PRICE_DISPLAY` to the same amount as the Razorpay plan.
4. Register webhook `https://<jobmail-host>/billing/razorpay/webhook/` for subscription lifecycle events. Run checkout, activation, failed payment, cancellation, and duplicate-webhook checks. Keep live billing disabled.

## 5. Before any real customer or live charge (founder decision; typically 1–2 weeks)

- Interview at least five target job seekers; confirm repeat pain, paid feature, and price. ₹299/month is only a hypothesis.
- Supply the legal business identity, support contact, jurisdiction, refund/cancellation terms, and data-retention rules; get privacy/terms reviewed.
- Configure automated database backups, complete a restore drill, and add an error-alert destination such as Sentry (`SENTRY_DSN`).
- Review the live Razorpay account and tax obligations. Only then deliberately add live keys and enable live billing.
- Keep Gmail sync off the hosted SaaS until Google's restricted-scope approval requirements are satisfied. The current product uses manually entered applications and never reads users' inboxes.

Do not paste passwords, API keys, webhook secrets, OAuth files, or customer data into chat, GitHub, or this checklist.
