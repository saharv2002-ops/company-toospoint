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

**Day 3 starting.** Day 2 shipped: data model + ingest endpoints + integration tests. CI now runs against a live Postgres service. Ready for the seed script.

## Done

- ✅ **Day 0 pre-flight** — product name (ChurnScope placeholder), first-pitch prospect (GLOBO), 2-week plan locked
- ✅ **Day 1** — repo skeleton (commit `0e8cf9e`)
  - FastAPI 0.115 + Python 3.12; `GET /health`; Next.js 14 + Tailwind; docker-compose; CI wired
- ✅ **Day 2** — data model + ingest (commit pending)
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

## Immediate next actions (Day 3)

Per `PLAN.md` § Day 3 — the seed script:

1. `scripts/seed.py` generates:
   - 400 interpreters, language distribution weighted (Spanish 35%, Mandarin 8%, Arabic 6%, Vietnamese 4%, Russian 4%, long tail)
   - Tenure spread: 40% <12 months, 30% 1-3 years, 30% 3+ years
   - 90 days of sessions, volume declining for the ~12% we want in Red band
   - Dispatches with realistic decline rates (2-8% baseline, 20-40% for at-risk)
   - Feedback: 92% none, 6% 4-5 stars, 2% low/complaints, clustered on at-risk interpreters
   - Weekly availability snapshots for last 12 weeks
2. Config knobs at top: `RED_TARGET_PCT`, `YELLOW_TARGET_PCT`, `TOTAL_INTERPRETERS`
3. Idempotent: `python seed.py --reset` wipes and reseeds
4. Verification step at end: prints computed band distribution (should land within 2 pts of target)
5. Commit + push

**Acceptance:** After `python seed.py --reset`, DB contains 400 interpreters and behaviour data such that Day-4 scoring lands ~12% Red / ~22% Yellow / ~66% Green.

**Trap:** don't spend Day 3 tuning distributions to perfection. "Close enough that the demo doesn't look weird" is the bar.

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
- **2026-08-21** — Day 2 shipped: 7-table data model, 6 pg enums, initial Alembic migration, Pydantic 2 ingest schemas (MAX_BATCH_SIZE=5000, extra=forbid, tight validators), 6 ingest endpoints with pg upsert, 10MB payload middleware, 9 integration tests + 7 schema unit tests. CI now runs against postgres:16 service. Local: 8 passed + 9 skipped (integration gated on POSTGRES_TEST_URL).
