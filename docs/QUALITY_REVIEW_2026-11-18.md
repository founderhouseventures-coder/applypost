# JobMail quality evidence — 2026-11-18

## Scope and changes

Personal repository: `YashRaJShaRMaCODE/applypost` (`JobMail-tracker` folder). Existing local edits in `src/main.py`, `src/test_main.py`, `scripts/check_site.py`, and research/roadmap docs were preserved. This pass adds a restrictive meta CSP, Open Graph/Twitter metadata, truthful SoftwareApplication JSON-LD, and a native keyboard-friendly mobile menu. No real mailbox, OAuth credentials, or user message was accessed.

## Verified locally

- Python unit suite: 41 passed; Ruff, compileall, static site checks, synthetic replay, 2 LeadHub loader tests, JavaScript syntax, and `git diff --check` pass.
- Playwright Chromium, Firefox, and WebKit: desktop 1440px and mobile 390px rendered without horizontal overflow or browser errors. Sample filters and row preview work in all 3. Mobile menu opens and navigates to Privacy in all 3; keyboard interaction was verified in Chromium and Firefox. WebKit headless keyboard emulation was not used as proof.
- The page has a main landmark, named navigation, skip link, keyboard-visible focus, social metadata, canonical, sitemap, robots, and schema markup. This is not a screen-reader or independent WCAG audit.
- Fresh visual captures: [`jobmail-1440.png`](quality-review/jobmail-1440.png), [`jobmail-390.png`](quality-review/jobmail-390.png).

## Live proof and limits

- Live homepage, `robots.txt`, and `sitemap.xml` returned HTTP 200. The GitHub Pages response included HSTS; it did not include CSP or `X-Frame-Options` response headers.
- The local meta CSP is uncommitted and undeployed. It does not provide `frame-ancestors`; a host or reverse proxy that can set response headers is needed for the full header set. If LeadHub is enabled, allow only its verified HTTPS origin in both script and connection policy, then re-test the consent flow.
- The browser mock is not Gmail/Sheets OAuth proof. Real-mailbox runs are intentionally not part of this pass; the tool writes spreadsheet rows and can mark mail as read on a normal run.
- No consent-based production analytics, verified lead capture, paid checkout, buyer interview, client, or paid receipt is configured. The site currently advertises optional one-off setup support without a confirmed price.
- No production Core Web Vitals or real-device/screen-reader/WCAG conformance result is claimed.
- No push, deploy, commit, or staging operation occurred. Changes are local and uncommitted.

## Still required for a release claim

Restore/confirm the Gmail and Sheets test project under owner control; test OAuth using a synthetic or dedicated test inbox; decide whether to supply approved LeadHub domain and email/unsubscribe setup; select a privacy-respecting analytics approach or keep analytics off; obtain buyer/pricing evidence; configure response security headers on a supported host; and run independent WCAG, real-device, and production performance checks.

## Visual/accessibility refinement addendum

- Added the mobile `Menu` disclosure using native `<details>/<summary>`; section links are now reachable at 390px without replacing the desktop nav.
- Chromium, Firefox, WebKit at 1440/390px pass menu, filter, and sample-row toggle smoke tests with no horizontal overflow or console errors. Chromium/Firefox verify keyboard activation; WebKit headless run verifies pointer activation only.
- Contrast spot checks after palette correction: blue on yellow 5.17:1; muted body labels on paper 4.75:1, warm white 5.14:1, and card surface 4.96:1. This is a sampled check, not full WCAG validation.
- Fresh screenshot files reflect the default, unfocused state. The Impeccable detector also reports legacy small-text/style heuristics; it was run once and was not rerun after fixes.
- Expanded responsive matrix: Chromium, Firefox, and WebKit at 320, 360, 390, 580, 768, and 1440px had no document-level horizontal overflow; the tested mobile-nav interaction and demo flow remain covered at 390px.
- Static source sizes from local files: HTML 4.07KB gzip, CSS 4.16KB, JavaScript 0.90KB, favicon 0.21KB (about 9.34KB combined). This omits protocol/header overhead and is not a live performance measurement.
