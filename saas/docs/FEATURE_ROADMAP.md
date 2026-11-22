# JobMail feature roadmap

This is a hypothesis backlog based on `MARKET_RESEARCH.md`, not a commitment to build every item. Free trackers already cover a lot of individual job tracking, so validate willingness to pay before adding expensive AI, integrations or team infrastructure. Do not ship a feature that increases private-data collection without a clear user benefit and consent.

| Priority | Feature | User problem solved | Competitor gap or review signal | Impact | Effort |
|---:|---|---|---|---|---|
| 1 | CSV import with preview, duplicate check and row-level errors | Moving from a spreadsheet is slow and risky | Jobscan/Huntr support tracker workflows; JobMail now has a bounded preview/confirm import flow | High | Medium |
| 2 | “Next action” date and today/overdue queue | Users forget follow-ups | Teal/Jobscan list reminders; JobMail should make the next action the primary view | High | Medium |
| 3 | Search, filter and saved views | Finding one company among many records is tedious | Existing products expose boards/filters; JobMail's single list is basic | High | Medium |
| 4 | Calendar file export for interviews/follow-ups | Events are split from the job record | Competitors advertise interview schedules; keep integration optional and local-first | High | Medium |
| 5 | Stale-application nudges with snooze/complete controls | Old records clutter the pipeline | Review feedback highlights need for clear sorting; notifications should stay user-controlled | High | Medium |
| 6 | Job-description snapshot and source URL history | A job post disappears after saving | Competitor trackers attach job data; preserve only what the user chooses | High | Medium |
| 7 | Company/contact fields with explicit “last contacted” date | Recruiter context gets lost | Huntr/Careerflow include contact tools; validate whether this matters to JobMail's users | Medium | Medium |
| 8 | Weekly search review with application/interview/follow-up counts | Users cannot see which search steps need work | Competitors offer insights; avoid making outcome predictions | High | Medium |
| 9 | Duplicate-role warning before save/import | Same role is tracked twice from different boards | Capture/import products can create duplicates | Medium | Low |
| 10 | Private resume-version label per application | Users forget which resume they sent | Competitors store documents; begin with labels, not resume uploads | Medium | Low |
| 11 | Interview prep notes and checklist attached to a role | Interview details are scattered | Teal/Huntr bundle more career tools; make this contextual and lightweight | Medium | Medium |
| 12 | Optional coach workspace and candidate-owned sharing | Coaches lack a consented cohort view | Careerflow explicitly sells organizational plans; test B2B need before building roles/workspaces | High | High |
| 13 | AI follow-up draft from user-entered role context | Writing a polite follow-up takes effort | Teal/Simplify offer AI writing; competitors' reviews mention generic output, so drafts must be editable and never auto-send | Medium | Medium |
| 14 | Optional Google Calendar sync with revoke/disconnect controls | Users miss scheduled interviews | Competing products support integrations; only build after consent and scope review | Medium | High |
| 15 | Personal job-search goal and configurable weekly cadence | Users need structure without shame-based streaks | Personalization can improve return use; avoid fake urgency and productivity pressure | Medium | Medium |

## Build order and gate

- First validate the problem with five job seekers and at least three coaches/placement operators. Do not contact them automatically; the owner conducts these conversations.
- If individuals show willingness to pay, prioritize items 1–5 and a free trial before billing. If organizations show a paid need, test a one-cohort pilot before item 12.
- The AI, calendar and workspace features remain blocked until users confirm value, privacy constraints are written, and implementation cost/support are understood.
- Each built item needs a test, empty/loading/success/error state, accessibility check and help text. Do not label roadmap items as implemented.

## Implementation evidence · 2026-11-21

- Roadmap item 1 (CSV import) is implemented locally: 1 MB/100-row limits, form validation, duplicate detection, row-level skip reasons, a 10-minute confirm preview, account quota check, and protection against stale preview tabs.
- Roadmap item 3 (search/filter) is implemented locally: company, role and source search; validated status filter; filter-preserving pagination; helpful empty state.
- Roadmap item 2 (follow-up date and due queue) now has a due/overdue filter that excludes closed applications. Django and Chromium cover import, filtering, core CRUD, date boundaries, and mobile overflow. Items 4–15 remain planned or gated as listed above.
