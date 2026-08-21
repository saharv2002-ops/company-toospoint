# Interpreter Attrition Dashboard — 2-Week Build Plan

Companion to `SPEC.md`. This document is the day-by-day execution plan: what gets built each day, the acceptance criteria for "done," what blocks the next day, and the checkpoints where we stop and reassess.

**Branch:** `prototype/interpreter-attrition`
**Target completion:** 10 working days from Day 1
**Success definition:** A live URL that Sahar can send to any of the 5 target LSPs 3 days before a meeting, and the recipient walks through it unaided.

---

## Day 0 — Pre-flight (before Day 1 starts)

Decisions locked before any code lands.

- [ ] **Product name.** Placeholder is `ChurnScope`. Alternatives to consider: `Retain`, `SignalOps`, `RosterHealth`. Ship with something ToosPoint can defend.
- [ ] **Build resourcing.** Sahar building solo? Contracting a dev? Pair with someone? Affects daily throughput assumption.
- [ ] **First-pitch prospect.** Which LSP hears the demo first? (Recommendation: **GLOBO** — smallest, most nimble, decline-rate signal maps best to their on-demand model. Reserve Cloudbreak/Voyce for pitch #2 with lessons applied.)
- [ ] **Hosting accounts.** Vercel account (frontend), Railway or Fly.io account (Postgres + FastAPI). Both free-tier for demo.
- [ ] **Domain.** `churnscope.toospoint.com` (or product-name equivalent). DNS ready before Day 9.
- [ ] **Repo & tooling.** Confirm Python 3.12, Node 20, Docker Desktop installed on build machine.
- [ ] **Design reference.** Pull 2–3 dashboards to reference visual style (Linear, Vercel, Retool templates). Not to copy — to calibrate polish level.

**Time budget for Day 0:** 90 minutes. Do not skip; every hour here saves three during the build.

---

## Week 1 — Backend, data, and scoring engine

Goal: by end of Friday, the API can ingest an LSP's data (via seed or CSV), compute churn scores, and return everything the frontend needs. No UI yet.

### Day 1 — Repo scaffolding

**Deliverables**
- Monorepo layout committed:
  ```
  prototypes/interpreter-attrition/
    api/               # FastAPI service
    web/               # Next.js app
    infra/             # docker-compose, deploy scripts
    scripts/           # seed.py, dev helpers
    docs/              # README, ADRs if we make any decisions
  ```
- `docker-compose.yml` with Postgres 16 + FastAPI (hot-reload) + a `pgadmin` optional sidecar.
- `api/`: FastAPI project skeleton with `/health` endpoint returning `{status:"ok", ts:"..."}`. Pytest wired.
- `web/`: `npx create-next-app@latest` (TypeScript, App Router, Tailwind). Home page shows placeholder text.
- Both services boot with `docker compose up`.
- GitHub Actions workflow: on push, run `pytest` in api/ and `pnpm build` in web/. Both green.

**Acceptance:** `curl localhost:8000/health` → 200, and `open localhost:3000` shows the Next.js page. CI badge green in the README.

**Blockers to next day:** none if this ships. If Docker networking or CI is flaky, spend Day 1 evening fixing — don't carry it forward.

### Day 2 — Data model + ingest endpoints

**Deliverables**
- Alembic migrations for 7 tables per SPEC section 4: `interpreters`, `sessions`, `dispatches`, `feedback`, `availability_snapshots`, `interventions`, `churn_scores`.
- SQLAlchemy models + Pydantic schemas mirroring the tables.
- Ingest endpoints (all `POST /api/ingest/*`), batch upsert semantics using `ON CONFLICT DO UPDATE`.
- Integration tests: for each ingest endpoint, insert 100 rows, verify count + a few field values, re-insert same batch, verify no duplicates.
- Rate-limit + payload-size guard on ingest (10MB max, generous but bounded).

**Acceptance:** `pytest api/tests/test_ingest.py` — all green. Migrations run cleanly against a fresh Postgres.

**Definition of "done":** if I nuke the DB and re-run migrations + tests, everything comes back clean.

### Day 3 — Seed script

**Deliverables**
- `scripts/seed.py` generates:
  - 400 interpreters (language distribution weighted: Spanish 35%, Mandarin 8%, Arabic 6%, Vietnamese 4%, Russian 4%, ... long tail. Tenure spread realistic: 40% under 12 months, 30% 1-3 years, 30% 3+ years.)
  - 90 days of sessions per interpreter, with volume declining for the ~12% we want in Red band.
  - Dispatches with realistic decline rates (2-8% baseline, rising to 20-40% for at-risk interpreters).
  - Feedback: 92% no rating, 6% 4-5 stars, 2% low ratings / complaints. Complaints cluster on at-risk interpreters.
  - Weekly availability snapshots for last 12 weeks.
- Config knobs at top of file: `RED_TARGET_PCT`, `YELLOW_TARGET_PCT`, `TOTAL_INTERPRETERS`.
- Idempotent: `python seed.py --reset` wipes and reseeds.
- Verification step at end of script: prints computed band distribution — should land within 2 pts of target.

**Acceptance:** After running `python seed.py --reset`, DB contains 400 interpreters and enough behavior data that scoring on Day 4 will produce the target distribution.

**Trap:** don't spend Day 3 tuning distributions to perfection. "Close enough that the demo doesn't look weird" is the bar.

### Day 4 — Scoring engine

**Deliverables**
- `api/services/scoring.py` with one function per signal (returns 0-100):
  - `signal_volume_decline(interpreter_id, as_of) → int`
  - `signal_decline_rate_rise(...)`
  - `signal_response_latency(...)`
  - `signal_feedback_spike(...)`
  - `signal_tenure_vulnerability(...)`
  - `signal_availability_shrinkage(...)`
- Composite scorer that combines with weights from SPEC section 3, returns band.
- Unit tests: for each signal, 3 fixture cases (clearly Green input, clearly Red input, edge case). Composite test covers weighting math.
- `POST /api/scores/recompute?as_of=YYYY-MM-DD` endpoint that batches all interpreters.
- Materialization: writes to `churn_scores` table, one row per interpreter per day computed.

**Acceptance:** After recomputing on seeded data, band distribution matches Day 3 seed target within 3 points. All signal unit tests pass.

**Definition of "done":** I can hit `POST /api/scores/recompute` and 2 seconds later query `SELECT band, COUNT(*) FROM churn_scores WHERE as_of = CURRENT_DATE GROUP BY band` and see believable numbers.

### Day 5 — Read APIs + Friday checkpoint

**Deliverables**
- `GET /api/interpreters?band=red&language=es&min_tenure=90` — filterable list, paginated, includes latest score.
- `GET /api/interpreters/{id}` — profile + latest score + all 6 signal values + human-readable "why" strings.
- `GET /api/interpreters/{id}/timeline?days=90` — daily signal history for the sparklines.
- `GET /api/dashboard/summary` — band counts, week-over-week delta, top 5 highest-risk.
- `POST /api/interventions` + `GET /api/interventions` — log and list.
- OpenAPI docs at `/docs` are complete (types, examples, response schemas).
- Postman collection or `.http` file committed in `api/tests/manual/` for smoke-testing.

**End-of-week checkpoint (Friday afternoon, 30 min):**
1. Run through the Postman collection top to bottom — every endpoint returns clean JSON.
2. Do the numbers on the summary endpoint match what a raw SQL count says?
3. Are any endpoint response times over 500ms? If yes, add an index and re-check.
4. Is the API deployable? Push to Railway/Fly staging, smoke test.
5. **Decision:** if Week 1 slipped by >1 day, cut scope from Week 2 (drop the interventions retention chart, drop timeline sparklines — keep it to Dashboard + basic detail view).

---

## Week 2 — Frontend, polish, deploy, demo prep

Goal: by end of Friday, a live production URL that walks a stranger through the value in 90 seconds.

### Day 6 — Dashboard screen

**Deliverables**
- Shared UI kit: install `shadcn/ui`, add `card`, `table`, `badge`, `button`, `dialog`, `select`, `input`.
- Data fetching: `@tanstack/react-query` wired against the API base URL.
- `/` page:
  - Header: product name, current date, "Recompute" button (dev-only, hidden in production).
  - 3 KPI cards (Red / Yellow / Total active) with week-over-week delta arrow.
  - Attrition risk table: sortable, filterable (band, language, tenure bucket, days-since-last-session), band-colored left border on each row.
  - Row action: "Log intervention" opens a modal.
- Loading skeletons for all data-fetches. Empty state if no interpreters (won't happen with seeded data but do it right).

**Acceptance:** Open `/`, see 12 Red / 68 Yellow / 312 Total-ish. Sort by score. Filter to Spanish only. Filter to Red band. It all works and stays fast (<200ms interactive).

### Day 7 — Interpreter detail screen

**Deliverables**
- `/interpreters/[id]` page:
  - Header: name, languages, tenure, current score with band pill, "Log intervention" button.
  - Signal breakdown card: 6 rows, each with signal name, progress bar (0-100), plain-English "why" copy.
  - 90-day signal timeline: 6 sparkline small multiples (Recharts), one per signal. Hover shows date + value.
  - Intervention log: table of past interventions with outcomes, most-recent first.
- Back link to dashboard.
- Deep linking works — hitting `/interpreters/abc-123` directly loads correctly.

**Acceptance:** Click any interpreter in the table on `/`, see their detail page. Sparklines render. "Why" copy makes sense (e.g., "Sessions in the last 14 days are 62% below her 90-day average"). Log an intervention, see it appear in the log immediately.

**Trap:** Recharts sparkline rendering with 90 daily points can look noisy. Add a 7-day rolling smooth if it looks bad.

### Day 8 — Interventions screen + intervention modal

**Deliverables**
- Intervention modal (used from both dashboard and detail screen):
  - Select: action type (`coach_call`, `assign_mentor`, `schedule_flex`, `comp_bonus`, `no_action`).
  - Textarea: notes.
  - Submit → POST + toast confirmation + optimistic UI update.
- `/interventions` page:
  - Table of all interventions across the roster, filterable by outcome.
  - Chart: intervention type → retention rate (bar chart). With seeded data this will look thin — acceptable, story is "this fills in as we log more."
  - Copy at bottom: "Retention outcomes update as interpreters continue or churn over the next 30 days."

**Acceptance:** Log 5 interventions across different interpreters. See them appear on `/interventions`. Chart renders even with sparse data.

### Day 9 — Polish + deploy

**Deliverables**
- Visual pass:
  - Typography: single font family (Geist or Inter), consistent hierarchy.
  - Color: band colors consistent (Red `#dc2626`, Yellow `#eab308`, Green `#16a34a`) with 10% alpha backgrounds for row highlights.
  - Spacing pass: nothing cramped, nothing floating.
  - Mobile: does not need to work perfectly, but the dashboard should at least be scrollable on iPad width.
- Empty states, error states, loading states — audit every screen.
- README at repo root:
  - What this is (2 sentences), who it's for.
  - How to run locally (`docker compose up`, `python seed.py`).
  - Live demo URL.
  - Screenshots.
- Deploy:
  - Frontend → Vercel from `web/`.
  - API → Railway from `api/`, with a Railway Postgres.
  - Custom domain: `churnscope.toospoint.com` (or product-name).
  - Environment variables set on both platforms.
  - Seeded data loaded into production DB.
- Smoke test the live URL from a phone, then a fresh incognito browser.

**Acceptance:** Send the live URL to a friend outside the industry. They can tell you what the app is doing within 30 seconds of clicking around.

### Day 10 — Demo materials + first pitch

**Deliverables**
- **90-second demo script** (`docs/demo-script.md`) — literal words Sahar says on the walkthrough, timed.
- **One-page PDF one-pager** — problem, screenshot, 6 signals, "what a pilot looks like." Suitable for pre-meeting attachment.
- **Per-prospect screenshot pack** — mock a screenshot with the target's logo swapped in for the header (or a subtle "For [prospect] pilot" tag). One screenshot per prospect, 5 total.
- **Send list** — email drafts ready to go to the 5 targets, each pointing to the live URL + one-pager. Reuses tone from `outreach/<prospect>/`.
- Final review with Sahar: does the demo flow feel confident? Any signals or copy that don't hold up?

**Acceptance:** The live URL is up. The one-pager is a PDF. The 5 emails are drafted and ready to send. Sahar has done the 90-second walkthrough once out loud without stumbling.

**Ship the first email at end of Day 10.**

---

## Checkpoints where we stop and reassess

- **End of Day 5** — Backend complete. If Week 1 slipped >1 day, cut interventions retention chart + sparkline detail from Week 2 scope.
- **End of Day 7** — Dashboard + detail live. If it doesn't feel demo-worthy at this point, DO NOT ship Week 2 as planned. Take an extra 2 days for polish before the interventions screen. A weak demo is worse than a late one.
- **End of Day 10** — Live URL ready. If it's live but rough, delay the first email 3 days for one more polish pass. First impression matters more than the launch date.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Seed data doesn't produce believable distributions | Med | High | Day 3 has explicit verification step. Budget half of Day 4 to re-tune if needed. |
| Recharts sparklines look noisy with daily data | High | Low | Add 7-day rolling smooth. Fallback: fewer signals in the timeline. |
| Vercel + Railway deploy fights us | Med | Med | Deploy to staging on Day 5, not Day 9. Break it early. |
| API response times slow with 400 interpreters | Low | Med | Add indexes on `interpreter_id` + `as_of`. Materialize summary counts. |
| Sahar can't get to 90-second walkthrough smoothly | Med | High | Day 10 rehearsal is non-negotiable. If script feels forced, cut a screen. |
| Prospect asks "does this work with our real data" in first meeting | High | Good (this is what we want) | Answer: "Give us 3 months of session history under a pilot agreement — we'll tell you within a week whether the signals predict *your* attrition." |

---

## What we do NOT build in these 2 weeks

Repeated from SPEC section 8 because scope discipline is the whole game:

- No auth. Single demo tenant. If pressed: "SSO is a pilot ask."
- No real ML. Rules only, and honest about that in the demo.
- No CSV upload UI. Seed script only.
- No mobile-first design. Desktop is fine; iPad-viewable is enough.
- No white-label / theming. Logo swap is fine for pilot-phase screenshots, not the live URL.
- No integrations with Boostlingo, Salesforce, EHRs. Those are pilot asks.

If anyone (including us) suggests adding one of these mid-build: the answer is "yes, in the pilot phase." Nothing on this list ships in v1.

---

## Day 11+ (out of scope but obvious next moves)

- First-prospect pilot signed → real data ingest CSV → refine weights on their historical attrition.
- ML swap-in once 12+ months of attrition outcomes exist.
- Auth + multi-tenant once 3+ paying pilots exist.
- Boostlingo integration if partnership discussion advances (see `outreach/boostlingo/`).

---

**Sign-off:** this plan is committed when the first email is sent on Day 10. Everything before that is a rehearsal.
