# Interpreter Attrition Dashboard

![ci](https://github.com/saharv2002-ops/company-toospoint/actions/workflows/churnscope-ci.yml/badge.svg?branch=prototype%2Finterpreter-attrition)

Early-warning dashboard that flags interpreters likely to churn in the next 30 days, so LSP operations teams can intervene before losing capacity.

**Working name:** ChurnScope (placeholder — rename before first pitch)

**Status:** planning complete, build starting on branch `prototype/interpreter-attrition`.

## Documents

- [`SPEC.md`](./SPEC.md) — product spec: signals, data model, screens, API, non-goals.
- [`PLAN.md`](./PLAN.md) — day-by-day 2-week build plan with acceptance criteria and checkpoints.

## Repo layout

```
api/       FastAPI service (Python 3.12, Postgres, SQLAlchemy, Alembic)
web/       Next.js 14 app (TypeScript, Tailwind, shadcn/ui, Recharts)
infra/     docker-compose + deploy configs
scripts/   seed.py + dev helpers
docs/      demo script, one-pager, ADRs if any
```

## Quick start (Day 1 lands the skeleton)

```bash
# API + Postgres via Docker
docker compose -f infra/docker-compose.yml up

# Frontend (in a separate shell)
cd web && npm install && npm run dev

# Verify
curl http://localhost:8000/health           # → {"status":"ok","ts":"..."}
open http://localhost:3000                  # → ChurnScope Day 1 placeholder
```

Local dev without Docker (API only):

```bash
cd api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
pytest -q
```

## Target prospects (see `../../outreach/`)

Cloudbreak/Voyce · CyraCom · Propio · GLOBO · AMN Language

First-pitch recommendation: **GLOBO** (smallest, most nimble; decline-rate signal maps best to their on-demand model).
