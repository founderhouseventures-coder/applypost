# JobMail founder-account handoff

Updated: 2026-11-19

## Target

- GitHub owner: `founderhouseventures-coder`
- Repository: `applypost`
- Intended visibility: public
- Default branch: `main`
- Pages URL after the repository exists and Pages deploy succeeds: `https://founderhouseventures-coder.github.io/applypost/`
- Public contact address in the site: `eatitall.founder@gmail.com`; verify that mailbox before publishing or accepting inquiries.

## Local handoff state

- Prepare the canonical source from the `JobMail-tracker` checkout. Do not delete the separate `JobMail-tracker-next3` checkout until its uncommitted changes have been reviewed; both folders contain distinct edits.
- This source now defaults to Gmail read-only scope and keeps messages unread. `--mark-read` is an explicit opt-in to Gmail label changes.
- This checkout's local Git author is set to `Founder House Ventures <eatitall.founder@gmail.com>` for future commits; verify the address on the new GitHub account before publishing commits.
- `origin` now points to the intended founder repository. The old personal URL is retained as `previous-personal` for reference; neither remote has been pushed to in this task.
- CI and a GitHub Pages Actions workflow are already present. Pages must be enabled with **Build and deployment → Source → GitHub Actions** on the new repository.
- No `credentials.json`, OAuth token, or `.env` file is tracked. Do not add Google credentials, tokens, or inbox data to GitHub Actions secrets; this is a local desktop app.
- Existing commit history was authored under the former personal identity. Keep history intact; only new commits should use the verified founder email.

## Owner actions still required

1. Sign in to GitHub as `founderhouseventures-coder` and create an empty public repository named `applypost` (do not initialize it with a README, license, or `.gitignore`).
2. Verify `eatitall.founder@gmail.com`, then use that verified email for new commits and as the public setup-contact address.
3. Authenticate Git/CLI as the founder account only. The current local GitHub CLI session is authenticated to the previous personal account; a separate company identity is also saved there and must not be selected.
4. Push the reviewed `main` branch to the new repository, enable Pages through GitHub Actions, and confirm CI plus the exact commit's Pages deployment are green.
5. Verify the new site URL, canonical/SEO URLs, GitHub links, contact address, and mobile page. Keep the old repository and old site until these checks pass.
6. For real Gmail/Sheets testing, use a dedicated test inbox and a Google Cloud OAuth project controlled by the founder. Test the read-only preview and Sheet write before any optional `--mark-read` test. Public multi-user distribution needs the applicable Google OAuth consent verification.

## Product boundary

JobMail is currently a local-first utility with a static product page and a proposed one-off setup service. It has no hosted user accounts, recurring billing, paid customer, or verified revenue. Do not describe it as a production SaaS or claim sales until those capabilities and demand are proven.
