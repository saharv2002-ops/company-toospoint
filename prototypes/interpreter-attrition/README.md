# Interpreter Attrition Dashboard

Early-warning dashboard that flags interpreters likely to churn in the next 30 days, so LSP operations teams can intervene before losing capacity.

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

## Quick start (after Day 1 lands)

```bash
docker compose -f infra/docker-compose.yml up      # api + postgres
cd web && pnpm dev                                  # frontend
python scripts/seed.py --reset                      # populate demo data
open http://localhost:3000
```

## Target prospects (see `../../outreach/`)

Cloudbreak/Voyce · CyraCom · Propio · GLOBO · AMN Language

First-pitch recommendation: **GLOBO** (smallest, most nimble; decline-rate signal maps best to their on-demand model).
