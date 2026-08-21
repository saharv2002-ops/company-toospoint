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

**Day 4 starting.** Day 3 shipped: seed script generates a realistic 400-interpreter dataset with 106K sessions, 123K dispatches, 7.3K feedback, 4.8K availability snapshots. Distribution lands exactly on 12% Red / 22% Yellow / 66% Green targets. Ready to build the scoring engine.

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
- ✅ **Day 3** — seed script + tests (commit pending)
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

## Immediate next actions (Day 4)

Per `PLAN.md` § Day 4 — the scoring engine:

1. `api/app/services/scoring.py` — one function per signal, each returning 0-100:
   - `signal_volume_decline(interpreter_id, as_of)` — last 14 vs 90-day rolling avg; drop >30% = signal
   - `signal_decline_rate_rise(...)` — 14-day decline % vs 90-day baseline; rise >15pts = signal
   - `signal_response_latency(...)` — median seconds; growth >40% vs baseline = signal
   - `signal_feedback_spike(...)` — complaints or ratings <3 in last 30 days; 2+ = strong
   - `signal_tenure_vulnerability(...)` — bell weighting, peak at 3-6mo and 18-24mo
   - `signal_availability_shrinkage(...)` — declared hours drop >25% vs 90-day = signal
2. Composite scorer: weighted average per SPEC § 3 weights (25/20/10/15/15/15). Bands: 0-39 green, 40-64 yellow, 65-100 red.
3. Unit tests per signal: 3 fixture cases (clear green input, clear red input, edge case). Composite test covers weighting math.
4. `POST /api/scores/recompute?as_of=YYYY-MM-DD` endpoint — batches all interpreters, writes to `churn_scores`.
5. Materialization: one `churn_scores` row per (interpreter_id, as_of).
6. Commit + push.

**Acceptance:** After seeding + `POST /api/scores/recompute`, band distribution matches Day-3 seed target within 3 points. All signal unit tests pass.

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
- **2026-08-21** — Day 3 shipped: seed.py + 9 in-memory tests. Dry-run against target 400 interpreters produces 12% red / 22% yellow / 66% green + 106K sessions / 123K dispatches / 7.3K feedback / 4.8K availability. CI now smoke-runs `seed --reset --total 200` against postgres between migrations and pytest. Local: 17 passed + 9 skipped.
