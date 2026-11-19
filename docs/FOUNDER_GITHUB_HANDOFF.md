# JobMail founder-account handoff

Updated: 2026-11-19

## Target

- GitHub owner: `founderhouseventures-coder`
- Repository: `applypost`
- Intended visibility: public
- Default branch: `main`
- Pages URL after the repository exists and Pages deploy succeeds: `https://founderhouseventures-coder.github.io/applypost/`
- Public contact address in the site: `eatitall.founder@gmail.com`; verify that mailbox before publishing or accepting inquiries.

## Completed handoff state

- Public repository `founderhouseventures-coder/applypost` exists and `origin` points to it. Commit `669cc6b` is on founder `main`.
- GitHub Actions CI passed for that commit. GitHub Pages was enabled and the homepage, `robots.txt`, and `sitemap.xml` returned HTTP 200. Pages is a temporary fallback; the requested final host is founder-owned Vercel.
- The local Git author is set to `Founder House Ventures <eatitall.founder@gmail.com>` for new commits. Verify the address on GitHub before relying on its attribution or accepting inquiries.
- `vercel.json` is ready to publish only the `site/` directory and set response security headers. `.vercel/` is ignored.
- This source defaults to Gmail read-only scope and keeps messages unread. `--mark-read` explicitly opts into Gmail label changes.
- No `credentials.json`, OAuth token, or `.env` file is tracked. Do not add Google credentials, tokens, or inbox data to GitHub Actions or Vercel variables; this is a local desktop app.
- Existing commit history remains unchanged. The old personal remote is retained locally as `previous-personal`; the old repository has not been removed.

## Remaining owner access and product checks

1. Connect/sign in to Vercel using the founder account. The current Vercel connector is authenticated as the former personal account, so no founder Vercel project has been created.
2. In the founder Vercel workspace, import `founderhouseventures-coder/applypost` as project `jobmail`, deploy `main`, and verify the exact production URL plus security headers.
3. After Vercel provides its production hostname, update the canonical URL, Open Graph URL, schema URL, `robots.txt`, and `sitemap.xml` from the temporary GitHub Pages URL, then redeploy.
4. Verify `eatitall.founder@gmail.com` before accepting setup inquiries.
5. For real Gmail/Sheets testing, use a dedicated test inbox and a Google Cloud OAuth project controlled by the founder. Test the read-only preview and Sheet write before any optional `--mark-read` test. Public multi-user distribution needs the applicable Google OAuth consent verification.
6. Keep the old repository until the Vercel deployment and owner-controlled OAuth checks pass.

## Product boundary

JobMail is currently a local-first utility with a static product page and a proposed one-off setup service. It has no hosted user accounts, recurring billing, paid customer, or verified revenue. Do not describe it as a production SaaS or claim sales until those capabilities and demand are proven.
