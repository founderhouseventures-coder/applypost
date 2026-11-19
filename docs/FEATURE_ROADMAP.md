# JobMail feature roadmap

Impact and effort are estimates. Competitor gaps are hypotheses unless tied to a public review in [`MARKET_RESEARCH.md`](MARKET_RESEARCH.md). Build only after user interviews confirm the problem. Sensitive email content must stay local and blank by default.

| # | Feature | User problem solved | Gap to test | Impact | Effort | Status |
|---:|---|---|---|---|---|---|
| 1 | Platform-aware sender filtering with job-signal check | Relevant notices from job platforms can be missed by broad sender blocks | Sender rules can hide legitimate recruiter updates | High | Low | Implemented locally; regression tests cover LinkedIn, Internshala, Unstop and Fastweb |
| 2 | Privacy-safe match explanation | Users cannot tell why a message qualified without inspecting its contents | Match-score tools can encourage over-optimization | High | Low | Implemented locally: `--dry-run --explain-matches` logs keyword labels only, never sender/subject/body; regression test added |
| 3 | Preview-first Google permission wizard | OAuth scope and side effects are hard to understand | Competitors emphasize features more than least-privilege setup | High | Medium | Planned |
| 4 | Per-message write receipt | Users need proof that the row reached Sheets before Gmail changes | Cloud trackers obscure the handoff between inbox and destination | High | Medium | Implemented locally as optional `--receipt-jsonl`; records local message ID, outcome and UTC time only, never sender/subject/body |
| 5 | Recoverable interrupted-write queue | A crash between Sheet write and local checkpoint can create uncertainty | Manual spreadsheet workflows lack reconciliation | High | Medium | Existing ID reconciliation; add a clearer recovery report |
| 6 | Local date-range and role keyword presets | Users have different target roles and search windows | General-purpose trackers need repeated manual filtering | High | Low | Existing CLI flags; add named presets after interviews |
| 7 | One-click sanitized CSV export | Users need a portable, non-Google fallback | SaaS products keep the workflow inside their account | Medium | Low | Implemented locally; formula-like cells are escaped even after leading whitespace/newlines, with regression coverage; body remains blank by default |
| 8 | Local response funnel summary | Users cannot see reply/interview progress from application emails | Existing tools may require manual status updates | Medium | Medium | Planned; do not infer success from mail classification |
| 9 | Duplicate-safe import of existing sheet rows | Users switching tools fear duplicate entries | Importers vary in handling prior records | High | Medium | Existing Gmail ID checks; broader import not validated |
| 10 | Editable sender allow/deny rules | False positives and noisy senders need user control | Static filters do not fit each inbox | High | Medium | Planned; never override message-level job-signal rules silently |
| 11 | Follow-up reminders derived from explicit dates | A job seeker forgets promised follow-up dates | Email trackers may depend on a hosted account | Medium | Medium | Planned; local notification only, no email sending |
| 12 | CSV backup/restore validation | Users want recovery without handing data to a hosted service | Cloud accounts create another data store | Medium | Medium | Planned |
| 13 | Fake-inbox replay mode | Users need to test parsing without granting Gmail access | OAuth setup makes first-run testing costly | High | Medium | Implemented locally as `--replay-demo`; runs the real parser against synthetic messages without OAuth, Gmail, Sheets, or checkpoint access |
| 14 | Accessibility and keyboard-only review flow | Batch review can be slow without a mouse | Desktop-first email tools may hide keyboard state | Medium | Medium | Planned |
| 15 | Optional multi-language message labels | Non-English notices may be missed | Keyword matching is language-dependent | Medium | High | Planned; validate supported languages and local processing first |

## Build order

Features 1, 2, 4, 7 and 13 are implemented locally. Feature 2 is opt-in behind `--dry-run --explain-matches`; it reports only matching keyword labels for a matched message. Feature 4 is opt-in behind `--receipt-jsonl` and writes only message IDs, outcomes and timestamps to a local file. Feature 7 is a dry-run export that neutralizes formula prefixes, including after leading whitespace/newlines. Feature 13 uses a bundled fictional fixture; it neither authorizes a Google connection nor touches the user's checkpoint. Do not add AI processing, body storage, cloud sync, or automatic outreach without explicit user research and a separate privacy review. All remaining items need tests, usage help, and a first-time-user walkthrough before being marked complete.
