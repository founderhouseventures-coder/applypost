# JobMail market research

**Checked:** 2026-11-21  
**Scope:** hosted manual job-application tracker in `saas/`. The local Gmail-to-Sheets CLI is a separate product and is excluded. Prices are public USD prices when found; vendors can change them. User feedback below is a summary of public reviews, not representative research or proof that the complaints are universal.

## Candidate user and problem

- **Current product user:** an individual job seeker who manually tracks companies, roles, application stages, follow-up dates and notes.
- **Likely payer (unvalidated):** the individual job seeker; ₹299/month remains a hypothesis. A second segment worth interviewing is a career coach, bootcamp or placement team that needs visibility across a candidate cohort. Careerflow publicly offers organization plans for universities, bootcamps, outplacement firms and coaches, showing that this buyer category exists, not that it will buy JobMail ([Careerflow FAQ](https://www.careerflow.ai/faq)).
- **Pain hypothesis:** job details live across job boards, spreadsheets and email; people lose the next follow-up and cannot see which part of their search needs attention. Jobscan and Teal both describe replacing spreadsheets and organizing application progress ([Jobscan Tracker](https://www.jobscan.co/job-tracker), [Teal pricing/features](https://www.tealhq.com/pricing)).
- **Why JobMail could win:** a calm, India-priced tracker that tells a job seeker what to do next, works without inbox access, and makes export/deletion clear. That is a positioning hypothesis, not a competitive moat yet. Existing trackers already offer generous free tiers, reminders, capture and analytics.

## Competitor snapshot

| Product | Public pricing / tracker scope | Three user-reported weaknesses to investigate |
|---|---|---|
| [Teal](https://www.tealhq.com/pricing) | Free plan includes unlimited job tracking. Teal+ lists $13/week, $29/month or $79/quarter ([official comparison](https://help.tealhq.com/en/articles/9530153-teal-vs-teal)). | Public reviewers report billing/refund-policy confusion; some say generated resume copy feels generic; some report support did not answer. Trustpilot shows 120 reviews and warns reviews may not represent all customers; treat these as complaints to test, not product-wide facts ([Trustpilot](https://www.trustpilot.com/review/tealhq.com)). |
| [Huntr](https://huntr.co/) | Free plan tracks up to 100 jobs; Pro lists $40/month, $90/quarter or $160/6 months ([official pricing](https://api.huntr.co/pricing)). | Extension reviewers say autofill is hit-or-miss; a review aggregator summarizes learning curve/navigation concerns and AI text that needs editing. Email integration, sorting and shared-board criticism appeared only once each in that sample, so these are weak signals, not recurring proof ([review sample](https://chrome-stats.com/d/mihdfbecejheednfigjpdacgeilhlmnf/reviews)). Trustpilot has only 21 reviews and is mostly positive, too small to claim broad dissatisfaction ([Trustpilot](https://www.trustpilot.com/review/huntr.co)). |
| [Simplify](https://simplify.jobs/) | Tracker and core job-search tools are free. Simplify+ lists $19.99/week, $39.99/month or $89.99/quarter ([official pricing/help](https://help.simplify.jobs/en/articles/5623502-whats-included-in-simplify-features-and-pricing)). | Reviewers report paid-plan refund/cancellation confusion; autofill or job-description parsing fails on some sites; slow support responses. Trustpilot's small sample is unclaimed/not invited, while the free Chrome extension has strong ratings; complaints should be separated by free vs paid experience ([Trustpilot](https://uk.trustpilot.com/review/simplify.jobs), [Chrome Web Store](https://chromewebstore.google.com/publisher/simplify-jobs/ua5e47b24fb6adb335148b99574a58244)). |
| [Careerflow](https://www.careerflow.ai/) | Job tracker is free with no job-count cap. Premium is shown at $8.99/week, $23.99/month, $54.99/quarter or $172.99/year; Plus is $19.99/week, $44.99/month, $119.99/quarter or $299.99/year ([official pricing](https://www.careerflow.ai/premium), [FAQ](https://www.careerflow.ai/faq)). | Reviewers mention account deletion difficulty, renewal/refund disputes and slow support; some criticize repetitive AI wording. The Trustpilot sample is small and includes freelancer reviews as well as job-seeker reports, so these are not all tracker-specific ([Trustpilot](https://www.trustpilot.com/review/careerflow.ai)). |
| [Jobscan](https://www.jobscan.co/job-tracker) | Job tracker is advertised as free. Paid resume tools are separate; official promo page offers a 7-day trial with the quarterly plan at $89.95/3 months. The public page does not reliably expose a current monthly price before sign-in ([official tracker](https://www.jobscan.co/job-tracker), [official promos](https://www.jobscan.co/promos)). | Reviewers report trial/renewal or cancellation-charge confusion; some say PDF parsing misses industry-specific terms; some report slow or limited email support. Trustpilot shows 348 reviews, but says the company has not recently invited reviews; these reports are not independently verified ([Trustpilot](https://www.trustpilot.com/review/jobscan.co)). |

## Competitive read

1. **The individual tracker alone is not a strong paid offer.** Teal, Simplify, Careerflow and Jobscan provide free tracking; Huntr includes 100 free jobs. A ₹299/month charge for manual CRUD would have weak differentiation.
2. **Do not compete on auto-apply volume.** Simplify and Huntr already bundle autofill, AI materials and capture; they also attract complaints around parsing, editing quality and paid-plan expectations. JobMail should not promise submissions it cannot verify.
3. **A paid B2B cohort workflow is the strongest testable adjacent offer, not a decided roadmap.** Interview coaches/placement operators about candidate follow-up visibility, consent, workload and willingness to pay before adding team accounts or candidate monitoring.
4. **Recommended initial positioning:** “A private job-search follow-through workspace: every application has a next step, and your inbox stays yours.” Keep manual entry, CSV export/delete and no-inbox-access as concrete product promises; do not claim faster hiring or better employment outcomes.

## Interview questions

1. Tell me how you tracked the last 10 roles you applied to. Show the tools or steps, with personal data hidden.
2. Which follow-up or interview detail was hardest to remember? What happened because it was missed?
3. What do you use now, and what have you tried or paid for? What made you stop?
4. If a private tracker reminded you of the next action and kept a timeline, what would you still need before using it weekly?
5. Would you choose a free tracker, a one-time setup, or a monthly plan? What have you actually paid for a similar job-search tool?
6. For coaches/placement teams: how many candidates do you support, how do you learn who needs help, and what consent/data controls would be mandatory?

**Status:** no target users or buyers were interviewed for this research pass. Validate these claims before committing to a paid feature set. Prices checked 2026-11-21; reconfirm at checkout before making pricing decisions.
