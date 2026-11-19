# JobMail founder-account handoff

Updated: 2026-11-19

## Target

- GitHub owner: `founderhouseventures-coder`
- Repository: `applypost`
- Intended visibility: public
- Default branch: `main`
- Vercel production URL (founder `EatItOut` team): `https://jobmail-ruby.vercel.app/`
- GitHub Pages fallback: `https://founderhouseventures-coder.github.io/applypost/`
- Public contact address in the site: `founderhouse.ventures@gmail.com`; the address received and completed Vercel identity verification.

## Completed handoff state

- Public repository `founderhouseventures-coder/applypost` exists and `origin` points to it. Commit `4fb26c0` is on founder `main`.
- GitHub Actions CI and Vercel both passed for `5feff78`. Founder Vercel project `jobmail` serves production at `https://jobmail-ruby.vercel.app/`; the homepage, `robots.txt`, and `sitemap.xml` return HTTP 200, and live HTML uses the production host for canonical, Open Graph, and structured data URLs.
- Sheets access now requests only the Sheets scope; Gmail modify permission is reserved for the deliberate `--mark-read` option.
- The local Git author is set to `Founder House Ventures <eatitall.founder@gmail.com>` for new commits. Verify the address on GitHub before relying on its attribution or accepting inquiries.
- `vercel.json` is ready to publish only the `site/` directory and set response security headers. `.vercel/` is ignored.
- This source defaults to Gmail read-only scope and keeps messages unread. `--mark-read` explicitly opts into Gmail label changes.
- No `credentials.json`, OAuth token, or `.env` file is tracked. Do not add Google credentials, tokens, or inbox data to GitHub Actions or Vercel variables; this is a local desktop app.
- Existing commit history remains unchanged. The old personal remote is retained locally as `previous-personal`; the old repository has not been removed.

## Remaining owner access and product checks

1. Complete the account and Google API setup in [`OWNER_INPUTS_REQUIRED.md`](OWNER_INPUTS_REQUIRED.md).
2. Keep the old repository until owner-controlled OAuth checks pass.

## Product boundary

JobMail is currently a local-first utility with a static product page and a proposed one-off setup service. It has no hosted user accounts, recurring billing, paid customer, or verified revenue. Do not describe it as a production SaaS or claim sales until those capabilities and demand are proven.
