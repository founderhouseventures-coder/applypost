# Founder worktree verification · 2026-11-22

The Django billing webhook keeps a verified event retryable when it arrives before the matching subscription row. Malformed or invalid signatures return a controlled rejection. The existing dashboard CSV preview/import changes were verified alongside this fix.

Ruff passed for the CLI and SaaS. The CLI suite passed 43 tests, Django passed 21 tests, and two Node signup-loader tests passed. Django system and migration drift checks and the static JobMail site check passed. Test fixtures do not contact Gmail or Razorpay.

Hosted authentication, production PostgreSQL, tested Razorpay checkout on the founder host, monitored backups and alert delivery remain open. Live mail and real payment processing are disabled for this work.

A paused or halted Razorpay subscription now blocks a duplicate checkout, consistently with account deletion. The connected local test covers signup, activation, application entry, CSV export, test checkout, duplicate prevention and account/data deletion after cancellation. Ruff, targeted mypy and all 22 Django tests passed. Razorpay was stubbed and email stayed in memory.

## 23 November 2026 selling path

Local selling path verified for ApplyPost. Active job seekers can sign up for updates through LeadHub with explicit consent, create a tracker account, add an application and follow-up, and start one 14-day unlimited trial. The ₹299 one-time pilot creates a server-side Razorpay order in test mode with notes.project=applypost. Test orders are reused on repeat checkout. Provider calls were mocked. No real email or charge occurred.

Passed Ruff, targeted mypy, 25 SaaS Django tests, 43 CLI tests, two static-site Node tests, migration drift, checkout JavaScript syntax and collectstatic. The mock tests assert the consent payload, expiry and retained records, test-mode guard, exact amount and product note, secret omission, and repeat-order behavior. Skipped real LeadHub delivery, Razorpay merchant checkout and payment confirmation.
