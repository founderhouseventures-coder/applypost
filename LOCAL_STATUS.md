# ApplyPost

Track applications and follow-ups so you know what to do next in a job search.

**For** Active job seekers

## Local verification

- Code changes locally verified.
- Local proof: 21 Django, 43 CLI and 2 Node
- [Recorded evidence](docs/FOUNDER_VERIFICATION.md)

## Engineering checklist

- **Product scope** — Prior brief exists; 15-point review open
- **System design** — Open
- **Frontend** — Open
- **Backend apis** — Local proof: rejects malformed signed webhook events and caps metadata
- **Database** — Open
- **Login permissions** — Open
- **Security privacy** — Partial: webhook validation regression covered
- **Integrations** — Partial: webhook tested locally; merchant checkout unverified
- **Code quality** — Local proof: Ruff and targeted Django-stubs typecheck
- **Performance cost** — Open
- **Testing** — Local proof: 21 Django, 43 CLI and 2 Node
- **Environments deployment** — Open
- **Monitoring recovery** — Local proof: uncached DB probe returns 503 when query fails
- **Startup operations** — Open
- **Docs handoff** — Open

## 22 November 2026 workflow verification

Fresh local rerun passed all 21 Django SaaS tests, including activation, application create/export/delete and test checkout cases. A single connected journey and provider checkout remain open.

## Connected account and billing workflow

A paused or halted Razorpay subscription now blocks a duplicate checkout, consistently with account deletion. The connected local test covers signup, activation, application entry, CSV export, test checkout, duplicate prevention and account/data deletion after cancellation. Ruff, targeted mypy and all 22 Django tests passed. Razorpay was stubbed and email stayed in memory.

## 23 November 2026 selling path

Local selling path verified for ApplyPost. Active job seekers can sign up for updates through LeadHub with explicit consent, create a tracker account, add an application and follow-up, and start one 14-day unlimited trial. The ₹299 one-time pilot creates a server-side Razorpay order in test mode with notes.project=applypost. Test orders are reused on repeat checkout. Provider calls were mocked. No real email or charge occurred.

Passed Ruff, targeted mypy, 25 SaaS Django tests, 43 CLI tests, two static-site Node tests, migration drift, checkout JavaScript syntax and collectstatic. The mock tests assert the consent payload, expiry and retained records, test-mode guard, exact amount and product note, secret omission, and repeat-order behavior. Skipped real LeadHub delivery, Razorpay merchant checkout and payment confirmation.

## 23 November 2026 quality bar

- **Passed** — 28 Django tests, 43 CLI tests, two Node tests, Ruff, targeted mypy, migration drift, collectstatic, static-site validation and the SaaS dependency audit.
- **Browser** — At 390 px and 1440 px, a seeded account signed in, got an empty pipeline, saved a synthetic application and exported it to CSV. Loading feedback, focus, reduced motion and axe WCAG A/AA smoke passed. Account activation and billing use local stubs in the Django suite.
- **Hardening** — Added IP and account throttling, safe custom errors, a tested database index and keyboard skip link. Check 429 and Retry-After in the route tests. Founder provider work remains outside local verification.
- **Open** — Query budget and local recovery evidence are being tracked separately. Audit signals 12/14 → 13/14.

## 23 November 2026 quality bar follow-up

QB done locally. The restored SQLite snapshot recovered the synthetic application, integrity check passed, and the dashboard query count stayed flat as rows increased. Fresh SaaS verification now has 29 Django tests.

## 24 November 2026: demo-ready wave 4

- Added a Kanban board at `/board/` grouped by stage. Overdue follow-ups are flagged in red.
- Each application now has a resume version (migration 0004). The CSV export includes it.
- Added `/insights/`: KPI cards (tracked, sent, interview rate, follow-ups due), an SVG chart of applications sent per week over the last 8 weeks, and interview counts per resume version.
- Added a `seed_demo` command (24 synthetic applications) and a `DEMO_MODE=1` one-click "Try the demo" login that lands on the board.
- The landing page now shows three plans (Starter ₹0, Pro, Career coach ₹2,999) and 4 FAQs.
- Checks:
  - Passed: 33/33 Django tests (4 new), ruff check, and mypy on the changed files.
  - Pre-existing failure: mypy reports `forms.py:12 UserCreationForm.Meta` (not touched in this wave).
  - Clicked through locally with curl: demo login → board → insights → export all return 200. Insights shows 24 tracked, 20 sent, 25%, 8 due.
  - Skipped: browser screenshot, because the Playwright browser was busy.
