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

**Day 2 starting.** Day 1 shipped and pushed as commit `0e8cf9e`. Ready to build the data model + ingest endpoints.

## Done

- ✅ **Day 0 pre-flight** — product name (ChurnScope placeholder), first-pitch prospect (GLOBO), 2-week plan locked
- ✅ **Day 1** — repo skeleton (commit `0e8cf9e`)
  - FastAPI 0.115 + Python 3.12; `GET /health` returns `{status, ts}`; pytest green
  - Next.js 14 App Router + TypeScript + Tailwind; `npm run build` clean
  - `infra/docker-compose.yml` (Postgres 16 + api with hot-reload)
  - `.github/workflows/churnscope-ci.yml` (path-scoped, api·pytest + web·build)
  - Root `.gitignore` extended for Node; README has CI badge + quick start

## Immediate next actions (Day 2)

Per `PLAN.md` § Day 2:

1. Alembic init inside `api/` (`alembic init alembic`)
2. Migration for 7 tables (see `SPEC.md` § 4):
   - `interpreters`, `sessions`, `dispatches`, `feedback`, `availability_snapshots`, `interventions`, `churn_scores`
3. SQLAlchemy 2 declarative models mirroring the migration
4. Pydantic 2 schemas for ingest (in `app/schemas/`)
5. Ingest endpoints — all `POST /api/ingest/*`, batch upsert via `ON CONFLICT DO UPDATE`
6. Integration tests (`tests/test_ingest.py`) — insert 100 rows, verify count + fields, re-insert same batch, verify no duplicates
7. Rate-limit + 10MB payload guard on ingest endpoints
8. Commit + push

**Acceptance:** `pytest api/tests/test_ingest.py` green; drop DB + rerun migrations + tests still green.

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

- **2026-08-21** — Day 1 shipped (commit `0e8cf9e`). Live `/health` verified. CI configured. CONTINUATION.md added.
