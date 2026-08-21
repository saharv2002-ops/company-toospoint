# Continuation — Interpreter Attrition Dashboard

**Purpose of this file:** state at the end of the last session, so the next session (or a fresh Claude) can pick up without re-deriving context.

**Update this file at the end of every working session.** Move completed days to "Done", update "Where we are right now", refresh "Immediate next actions."

---

## Quick orient

- **Working directory:** `~/company-toospoint`
- **Prototype directory:** `prototypes/interpreter-attrition/`
- **Branch:** `prototype/interpreter-attrition` (pushed, tracking `origin`)
- **Product working name:** ChurnScope (placeholder — rename before first pitch)
- **Owner:** Sahar Feiz / ToosPoint
- **Purpose:** demo-quality churn early-warning dashboard for 5 mid-tier interpretation LSPs (GLOBO first, then Cloudbreak/Voyce, CyraCom, Propio, AMN)
- **Read first:** `SPEC.md` (product spec), `PLAN.md` (2-week build plan). This file assumes you've skimmed both.

## Where we are right now

**Day 8 starting.** Day 7 shipped the interpreter detail screen: header + signal breakdown with why copy + 30-day Recharts sparklines + intervention log. Dashboard rows link to detail. Build clean. Ready for the interventions screen + polish.

## Done

- ✅ **Day 0 pre-flight** — product name (ChurnScope placeholder), first-pitch prospect (GLOBO), 2-week plan locked
- ✅ **Day 1** — repo skeleton (commit `0e8cf9e`)
  - FastAPI 0.115 + Python 3.12; `GET /health`; Next.js 14 + Tailwind; docker-compose; CI wired
- ✅ **Day 2** — data model + ingest (commit `341ccd1`)
  - `app/enums.py`: 6 native pg enums (InterpreterStatus, SessionType, SessionOutcome, DispatchResponse, InterventionAction, ChurnBand)
  - `app/models/*.py`: 7 SQLAlchemy 2 models (Interpreter, Session, Dispatch, Feedback, AvailabilitySnapshot, Intervention, ChurnScore)
  - `app/schemas/ingest.py`: Pydantic 2 ingest schemas with strict validation, batch envelope, MAX_BATCH_SIZE=5000
  - `app/routers/ingest.py`: 6 endpoints (`POST /api/ingest/{interpreters,sessions,dispatches,feedback,availability,interventions}`) with `ON CONFLICT DO UPDATE` upsert semantics
  - `app/middleware.py`: PayloadSizeLimitMiddleware (10MB guard)
  - `alembic/versions/20260821_0001_initial_schema.py`: initial migration, 7 tables + 6 enum types + indexes + FK CASCADEs + check constraints
  - `tests/test_schemas.py`: 7 no-DB Pydantic validation tests
  - `tests/test_ingest.py`: 9 integration tests (skipped locally when POSTGRES_TEST_URL unset; run in CI)
  - CI extended: postgres:16 service + alembic upgrade head + full pytest with POSTGRES_TEST_URL wired
  - Local verification: 8 passed + 9 skipped (integration tests gated)
- ✅ **Day 3** — seed script + tests (commit `a3faf36`)
  - `api/scripts/seed.py` — one file, pure generators + one DB insert function
  - Config knobs at top: `TOTAL_INTERPRETERS=400`, `RED_TARGET_PCT=12`, `YELLOW_TARGET_PCT=22`, `DAYS_OF_HISTORY=90`, `AVAILABILITY_WEEKS=12`, `DEFAULT_SEED=42`
  - Roster: 400 interpreters, English + weighted secondary language (Spanish 35%, Mandarin 8%, Arabic 6%, Vietnamese 4%, Russian 4%, long tail of 30 languages), tenure spread 40/30/30 (<1yr / 1-3yr / 3+yr), 16 timezones, 6 certifications
  - Behavior generators produce distinct curves per risk bucket:
    - Sessions: `LAST14_MULTIPLIER` (green 1.00, yellow 0.80, red 0.45) applied to last 14 days of Poisson-sampled daily counts
    - Dispatches: baseline vs recent decline rates (green 0.05→0.06, yellow 0.09→0.18, red 0.10→0.32) + response-latency growth
    - Feedback: `FEEDBACK_ANY_PROB` × `FEEDBACK_LOW_FRACTION` clusters complaints on at-risk interpreters
    - Availability: last 3 weeks show `AVAIL_HOURS_RECENT` (green 30h, yellow 22h, red 12h) vs baseline
  - CLI: `python -m scripts.seed --reset [--dry-run] [--seed N] [--total N]`
  - `tests/test_seed.py` — 9 no-DB tests: roster size, band distribution within 2pts, tenure spread, session decay for red, decline-rate rise for red, complaint clustering, availability shrinkage, English present, determinism
  - Dry-run output: 400 interpreters (48 red / 88 yellow / 264 green) → 106K sessions / 123K dispatches / 7.3K feedback / 4.8K availability = ~241K rows total
  - CI: `python -m scripts.seed --reset --total 200` runs against the postgres:16 service between `alembic upgrade head` and `pytest` — proves the full ingest pipeline end-to-end
  - Local verification: pytest → 17 passed + 9 skipped
- ✅ **Day 4** — scoring engine (commit `eca0018`)
  - `api/app/services/scoring.py` — 6 pure signal functions + composite + band + bulk collection + recompute
    - `SignalInputs` dataclass with pre-aggregated per-interpreter fields
    - Weights locked from SPEC § 3: `WEIGHTS = {1:25, 2:20, 3:10, 4:15, 5:15, 6:15}` (sum=100, asserted)
    - Bands: `[0,40) green, [40,65) yellow, [65,100] red` via `BAND_YELLOW_MIN=40`, `BAND_RED_MIN=65`
    - Signal 1 (volume): recent-per-day vs baseline-per-day; drop 30% → 50, drop 60%+ → 100
    - Signal 2 (decline rate): recent % minus baseline %; rise 15pts → 50, rise 30pts+ → 100
    - Signal 3 (latency): median growth; 40% → 50, 100%+ → 100
    - Signal 4 (feedback): complaints OR rating<3 in last 30d; 0→0, 1→50, 2→80, 3+→100
    - Signal 5 (tenure): bimodal Gaussian bumps at 4.5mo (sd=2, peak=90) and 21mo (sd=6, peak=90); floor 15, decays after 48mo
    - Signal 6 (availability): recent avg vs baseline avg; drop 25% → 50, drop 50%+ → 100
    - `collect_all_inputs()` — bulk SQL: one aggregate query per signal across full roster, uses Postgres `percentile_cont(0.5) WITHIN GROUP` for medians
    - `recompute_all()` — upserts into `churn_scores` via `INSERT ... ON CONFLICT (interpreter_id, as_of) DO UPDATE`
  - `api/app/routers/scores.py` — `POST /api/scores/recompute?as_of=YYYY-MM-DD` (defaults to today UTC). Returns `RecomputeResponse{as_of, scored, band_counts}`.
  - `api/tests/test_scoring.py` — 22 unit tests: 3 fixture cases per signal (green input, red input, edge case) + composite weighting math + weights sum + band boundaries
  - `api/tests/test_scoring_e2e.py` — 4 integration tests (requires_postgres): seed 200 → recompute → band distribution within 3pts of seed target (12/22/66), churn_scores populated, idempotent recompute, POST endpoint returns correct payload
  - Local verification: pytest → 39 passed + 13 skipped
  - CI already covers the e2e path via existing seed step
- ✅ **Day 5** — read APIs + Friday checkpoint (commit `5b9f8ea`)
  - `api/app/services/explanations.py` — plain-English "why" copy generator per signal, e.g. "Sessions in the last 14 days are 62% below the prior 76-day baseline (1.4/day vs 3.0/day)."
  - `api/app/services/scoring.py` — added `recompute_range(db, end, days)` (capped at MAX_BACKFILL_DAYS=90) that loops recompute over consecutive dates
  - `api/app/routers/scores.py` — added `POST /api/scores/backfill?days=N&end=YYYY-MM-DD` for timeline data
  - `api/app/schemas/reads.py` — 10 response schemas (InterpreterListItem/Response, InterpreterDetail, SignalReadout, LatestScore, TimelinePoint/Response, TopAtRisk, DashboardSummary, InterventionCreate/Read/ListResponse)
  - `api/app/routers/interpreters.py`:
    - `GET /api/interpreters` — filters (band, language, min_tenure_days, max_days_since_last_session, status) + pagination (limit/offset), joins latest churn_score via DISTINCT ON, includes top-signal-key
    - `GET /api/interpreters/{id}` — profile + latest score + 6-signal readouts with per-signal "why" copy + recent intervention count
    - `GET /api/interpreters/{id}/timeline?days=N` — reads from `churn_scores` (needs backfill first), max 90 days
  - `api/app/routers/dashboard.py`:
    - `GET /api/dashboard/summary` — total_active, band_counts, week-over-week deltas (compares latest as_of vs -7d), top-5 at-risk sorted by composite_score desc
  - `api/app/routers/interventions.py`:
    - `GET /api/interventions?interpreter_id=&outcome=&since_days=&limit=&offset=` — filterable list
    - `POST /api/interventions` — 201 on create, 400 on unknown interpreter (separate from bulk-ingest endpoint)
  - `api/tests/test_reads.py` — 12 integration tests (requires_postgres): list total, band filter, language filter, pagination disjoint, detail returns 6 signals with why copy, detail 404, timeline count, dashboard summary correctness + top-5 sort, intervention create+list, intervention unknown_interpreter 400, backfill endpoint totals, backfill days cap
  - `api/tests/manual/smoke.http` — VS Code REST Client / httpie-friendly smoke file covering every endpoint
  - `api/app/main.py` — registers 5 routers total (ingest, scores, interpreters, dashboard, interventions)
  - Local verification: pytest → 39 passed + 25 skipped (integration + scoring-e2e + read tests gated on POSTGRES_TEST_URL; all 64 tests run in CI against real Postgres)

### Friday checkpoint (per PLAN.md § End-of-week)

- ✅ Every endpoint returns valid OpenAPI schema (`/docs` renders cleanly)
- ✅ 14 routes wired: 1 health + 6 ingest + 2 scores + 3 interpreters + 1 dashboard + 2 interventions
- ✅ Full test suite green locally (39 pass, 25 skip) and in CI (all 64 vs Postgres)
- ⏳ Deploy API to Railway/Fly staging — deferred; will land on Day 9 as part of production deploy
- ⏳ Endpoint latency measurement (target < 500ms) — deferred; on-demand data volumes with the seeded 200-row dataset are all sub-100ms locally; retest after Day 9 deploy against real hosting

**Week 1 verdict: on schedule.** No scope needs to be cut from Week 2.
- ✅ **Day 6** — dashboard screen (commit `9118ef7`)
  - web/package.json — added @tanstack/react-query, @radix-ui/react-dialog, lucide-react, class-variance-authority, clsx, tailwind-merge
  - web/lib/utils.ts — cn(), formatDate, daysAgo, bandBorderClass, bandBadgeClass helpers
  - web/lib/types.ts — TypeScript mirrors of backend Pydantic schemas (12 types)
  - web/lib/api.ts — typed fetch client for all 14 endpoints, ApiError, qs helper
  - web/components/providers.tsx — QueryClientProvider (staleTime 30s, no refetch-on-focus, retry 1)
  - web/components/ui/{card,button,badge,input,dialog,table}.tsx — minimal shadcn-inspired primitives with Tailwind + CVA. Radix Dialog for a11y. Native styled `<select>` for filters.
  - web/components/kpi-card.tsx — 3 KPI cards with accent bar + week-over-week delta arrow (red/green trend coloring depends on whether "up" is bad for that band)
  - web/components/interpreter-table.tsx — the risk table:
    - 4 filters (band, language, min-tenure, silent-within) + reset button
    - Columns: interpreter (name + external_id), languages, tenure (months), score + band badge, top signal name, last session (relative time), action button
    - 4px band-colored left border per row
    - Row action opens the intervention modal for that interpreter
    - Loading + error states, "Showing X of Y (N filters applied)" footer
  - web/components/intervention-dialog.tsx — Radix Dialog for logging interventions:
    - action select (5 options), notes textarea
    - Mutation → POST /api/interventions → invalidate ["interventions"] + ["interpreters"]
    - Error banner on failure
  - web/app/page.tsx — dashboard orchestration:
    - Header with product name eyebrow + "As of" date badge + dev-only Recompute button (calls recompute + backfill(14) then invalidates all queries)
    - 3 KPI cards (Red / Yellow / Active roster) driven by GET /api/dashboard/summary
    - InterpreterTable + InterventionDialog wired to selected interpreter state
  - web/app/layout.tsx — Providers wrapping children
  - Verified: `npm run build` clean, 27.3 kB dashboard bundle, 87.2 kB shared JS
- ✅ **Day 7** — interpreter detail screen (commit pending)
  - web/package.json — added recharts 2.13
  - web/components/ui/progress.tsx — simple width-% progress bar; colour ramps green → yellow → red at 40 / 65 (matches band boundaries)
  - web/components/signal-breakdown.tsx — 6-row card, per row: signal name + weight tag + progress bar + score + plain-English why copy from `GET /api/interpreters/{id}.signals[].why`
  - web/components/sparkline-grid.tsx — 6 small-multiple LineCharts (Recharts) for signal_1..signal_6 across the last 30 days from `GET /api/interpreters/{id}/timeline?days=30`. Custom tooltip shows value + formatted date. Hidden Y axis, domain locked to [0,100]. Empty-state hint tells user to run backfill.
  - web/components/intervention-log.tsx — reads `GET /api/interventions?interpreter_id=...&limit=50`. Row layout: action badge (32ch), notes + optional outcome, right-aligned date. Empty-state copy invites user to log next intervention.
  - web/app/interpreters/[id]/page.tsx — detail page:
    - "Back to dashboard" chevron link
    - Header: external_id + status in mono, full name (3xl), language badges + tenure + hired date + timezone
    - Right-side: Score card (composite + band pill + as_of) + "Log intervention" button
    - 2-column grid: SignalBreakdown (2/3 width) + InterventionLog (1/3 width)
    - Full-width: SparklineGrid (30 days)
    - Footer: recent intervention count note
    - Reuses InterventionDialog from Day 6 (Radix). Mutation invalidates ['interventions'] which re-renders the log immediately.
  - web/components/interpreter-table.tsx — name column wrapped in `<Link href="/interpreters/{id}">` with `group-hover:underline`. Action button unaffected (separate click target).
  - Verified: `npm run build` clean.
    - Dashboard bundle: 6.57 kB (dropped from 27.3 kB — code-splitting kicked in)
    - Detail page bundle: 104 kB (Recharts inline)
    - Shared JS: 87.4 kB
    - Route `/interpreters/[id]` correctly detected as dynamic (server-rendered on demand)

## Immediate next actions (Day 8)

Per `PLAN.md` § Day 8 — interventions screen + polish:

1. `web/app/interventions/page.tsx` — cross-roster intervention log:
   - Table of all interventions across the roster, filterable by outcome, action type, since_days
   - Chart: intervention type → retention rate (bar chart, Recharts). Copy: "Retention outcomes update as interpreters continue or churn over the next 30 days."
   - Link back to dashboard from every row (interpreter_id → detail page)
2. Nav / breadcrumbs so users can move Dashboard ↔ Detail ↔ Interventions cleanly.
3. Empty states, error states, loading skeletons — full audit across all screens.

**Acceptance:** Log 5 interventions across different interpreters, see them appear on /interventions. Chart renders (thin at first, that's fine — the story is "this fills in as we log more").

## Locked decisions

- **Product name:** ChurnScope (working — decide final before Day 10)
- **First prospect:** GLOBO
- **Stack:** Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + Postgres 16 (backend); Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui + Recharts (frontend); Vercel + Railway (deploy)
- **v1 non-goals:** no auth, no ML, no CSV upload UI, no mobile, no white-label, no third-party integrations
- **Signals:** 6 rules-based signals with weights locked in `SPEC.md` § 3 — do NOT re-derive
- **Data model:** 7 tables locked in `SPEC.md` § 4 — do NOT re-derive

## Open questions / decisions to revisit

- **Final product name** — before Day 10 demo. Candidates: ChurnScope, Retain, SignalOps, RosterHealth.
- **Build resourcing** — Sahar solo vs contract dev. Affects daily throughput assumption.
- **Domain** — `churnscope.toospoint.com` or product-name equivalent. Needed by Day 9.
- **First-pitch date** — target end of Day 10 (or +3 days for polish).

## How to resume (new session)

1. Read this file top to bottom
2. Read `SPEC.md` and `PLAN.md` if you haven't
3. `cd ~/company-toospoint && git checkout prototype/interpreter-attrition && git pull`
4. `cd prototypes/interpreter-attrition/api && source .venv/bin/activate` (or recreate venv from `requirements-dev.txt`)
5. Look at "Immediate next actions" above — that's where you start
6. When the session ends, update this file: move finished items to "Done", refresh "Immediate next actions", note any new decisions

## Session log

- **2026-08-21** — Day 1 shipped (commit `0e8cf9e`). Live `/health` verified. CI configured. CONTINUATION.md added (commit `a484444`).
- **2026-08-21** — Day 2 shipped (commit `341ccd1`): 7-table data model, 6 pg enums, initial Alembic migration, Pydantic 2 ingest schemas (MAX_BATCH_SIZE=5000, extra=forbid, tight validators), 6 ingest endpoints with pg upsert, 10MB payload middleware, 9 integration tests + 7 schema unit tests. CI now runs against postgres:16 service. Local: 8 passed + 9 skipped (integration gated on POSTGRES_TEST_URL).
- **2026-08-21** — Day 3 shipped (commit `a3faf36`): seed.py + 9 in-memory tests. Dry-run against target 400 interpreters produces 12% red / 22% yellow / 66% green + 106K sessions / 123K dispatches / 7.3K feedback / 4.8K availability. CI now smoke-runs `seed --reset --total 200` against postgres between migrations and pytest. Local: 17 passed + 9 skipped.
- **2026-08-21** — Day 4 shipped (commit `eca0018`): scoring engine with 6 pure signal functions (volume, decline-rate, latency, feedback, tenure bimodal bell, availability), weighted composite (25/20/10/15/15/15), band assignment, bulk SQL aggregation (uses percentile_cont for medians), `POST /api/scores/recompute` endpoint. 22 unit tests + 4 e2e tests. e2e verifies blind scoring recovers seeded bucket distribution within 3pts. Local: 39 passed + 13 skipped.
- **2026-08-21** — Day 5 shipped (commit `5b9f8ea`): read APIs. 6 new endpoints (list, detail, timeline, dashboard summary, intervention list+create) + backfill endpoint. Explanations service produces plain-English "why" strings per signal. 10 new Pydantic response schemas. 12 read integration tests. 14 routes total in OpenAPI. Week 1 complete on schedule; no Week 2 scope cuts.
- **2026-08-21** — Day 6 shipped (commit `9118ef7`): dashboard screen. shadcn-style primitives (card/button/badge/input/dialog/table) + Radix Dialog. Typed API client hits all 14 endpoints. KPI cards + filterable/sortable risk table + intervention modal. Next.js build clean at 27.3 kB dashboard bundle.
- **2026-08-21** — Day 7 shipped: interpreter detail screen. Recharts sparklines (6 small multiples over 30 days), signal breakdown card with plain-English why copy, intervention log, header with score + band pill + Log intervention button. Dashboard rows link to detail. Build clean (dashboard 6.57 kB after code-split, detail 104 kB with Recharts).
