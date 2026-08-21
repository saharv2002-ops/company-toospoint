# Interpreter Attrition Early-Warning Dashboard

**Working name:** ChurnScope (placeholder — rename before demo)
**Purpose:** A demo-quality web app ToosPoint can walk into 5 mid-tier interpretation LSPs (Cloudbreak/Voyce, CyraCom, Propio, GLOBO, AMN) that flags interpreters likely to churn in the next 30 days, so operations leaders can intervene before losing capacity.
**Not building:** a production system. Building enough that a VP of Operations opens it, immediately understands what it does, and asks "can we pilot this on our data."

---

## 1. The problem (what we're claiming to solve)

Interpretation LSPs lose 20-40% of active interpreters per year. Attrition is expensive twice: recruitment cost to replace, and coverage failure during the gap. Everyone in ops "sort of knows" who's about to leave — session decline, more requests refused, tone shift in feedback — but nobody has that intuition in a dashboard.

Existing LSP internal tooling almost always has:
- Session logs (who did what session, when, how long, which client)
- Interpreter profiles (languages, certifications, tenure)
- Request/dispatch logs (offered, accepted, declined)
- Complaint/feedback records

Nobody blends these signals into a churn score. That's the gap.

## 2. What the app does (in one paragraph, for the demo)

Ingest an LSP's interpreter roster + last 90 days of session, dispatch, and feedback data. Compute a per-interpreter **Churn Risk Score (0-100)** from six weighted signals. Present a dashboard where an ops manager sees who's high-risk, why they're flagged, and what the recommended intervention is. Click into an interpreter → see the signal timeline and past interventions.

## 3. Churn signals (v1 — rules-based, no ML)

Rules-based is deliberate — it's explainable, defensible, and doesn't require training data we don't have. ML in v2 once a real client shares 12 months of data.

| # | Signal | How it's computed | Weight |
|---|---|---|---|
| 1 | **Session volume decline** | Sessions in last 14 days vs interpreter's 90-day rolling avg. Drop > 30% = signal. | 25 |
| 2 | **Decline rate rising** | % of dispatched requests declined in last 14 days vs 90-day baseline. Rise > 15 pts = signal. | 20 |
| 3 | **Response latency growth** | Median seconds to accept/decline a request. Growth > 40% vs baseline = signal. | 10 |
| 4 | **Negative feedback spike** | Complaints or ratings < 3 in last 30 days. Any complaint = signal; 2+ = strong. | 15 |
| 5 | **Tenure vulnerability** | Highest risk at 3-6 months and 18-24 months tenure (industry pattern). Bell weighting. | 15 |
| 6 | **Availability window shrinkage** | Marked-available hours per week vs 90-day baseline. Drop > 25% = signal. | 15 |

Each signal returns 0-100. Composite = weighted average. Bands: **Green (0-39), Yellow (40-64), Red (65-100)**.

## 4. Data model (Postgres)

Small, wide-enough-to-be-real, narrow-enough-to-seed.

```
interpreters
  id (uuid, pk)
  external_id (text)                     -- LSP's own interpreter id
  full_name (text)
  languages (text[])                     -- ISO codes
  certifications (text[])
  hired_at (date)
  status (enum: active|paused|inactive)
  home_timezone (text)

sessions
  id (uuid, pk)
  interpreter_id (fk)
  client_id (fk, nullable)
  session_type (enum: opi|vri|onsite)
  language_pair (text)                   -- 'en-es'
  started_at (timestamptz)
  duration_seconds (int)
  outcome (enum: completed|dropped|no_show|cancelled)

dispatches
  id (uuid, pk)
  interpreter_id (fk)
  offered_at (timestamptz)
  responded_at (timestamptz, nullable)
  response (enum: accepted|declined|timeout)
  language_pair (text)

feedback
  id (uuid, pk)
  session_id (fk)
  rating (int, 1-5, nullable)
  complaint_flag (bool)
  category (text, nullable)              -- 'quality'|'behavior'|'punctuality'
  notes (text, nullable)
  submitted_at (timestamptz)

availability_snapshots
  id (uuid, pk)
  interpreter_id (fk)
  week_of (date)
  hours_declared (numeric)

interventions                            -- for click-through detail view
  id (uuid, pk)
  interpreter_id (fk)
  action (enum: coach_call|assign_mentor|schedule_flex|comp_bonus|no_action)
  created_at (timestamptz)
  outcome (text, nullable)               -- 'retained'|'churned'|'pending'

churn_scores (computed nightly, materialized)
  interpreter_id (fk, pk with as_of)
  as_of (date, pk with interpreter_id)
  composite_score (int 0-100)
  signal_1_volume (int)
  signal_2_decline (int)
  signal_3_latency (int)
  signal_4_feedback (int)
  signal_5_tenure (int)
  signal_6_availability (int)
  band (enum: green|yellow|red)
```

## 5. Backend

**Stack:** Python 3.12 + FastAPI + Postgres 16 + SQLAlchemy. Nightly score-recompute via a single scheduled task (APScheduler or a cron-triggered endpoint).

**Endpoints (all JSON):**

```
POST /api/ingest/sessions           -- bulk upsert; used by seed script + future CSV upload
POST /api/ingest/dispatches
POST /api/ingest/feedback
POST /api/ingest/availability
POST /api/ingest/interpreters

POST /api/scores/recompute          -- recompute all scores for a given date
GET  /api/interpreters              -- list, filterable by band/language/tenure
GET  /api/interpreters/{id}         -- detail: profile + score + signal breakdown
GET  /api/interpreters/{id}/timeline -- 90-day signal history (for the chart)
GET  /api/dashboard/summary         -- counts by band, week-over-week delta

POST /api/interventions             -- log an intervention against an interpreter
GET  /api/interventions?since=...   -- history
```

**Seed script (`seed.py`):** generates a realistic roster of 400 synthetic interpreters, 90 days of sessions/dispatches/feedback, tuned so ~12% land in Red, ~22% Yellow, ~66% Green. Enough to feel real in the demo. **Never seed with a real LSP's data.**

## 6. Frontend

**Stack:** Next.js 14 (App Router) + Tailwind + shadcn/ui + Recharts. TypeScript. Deployed to Vercel — one-click for the demo link.

**Three screens, that's it:**

### Screen 1 — Dashboard (`/`)

- Top: 3 KPI cards → "Red band (12)", "Yellow band (68)", "Total active (312)". Week-over-week delta arrow on each.
- Middle: **Attrition risk table**, default-sorted by score descending, band-colored row indicator.
  - Columns: Name | Languages | Tenure | Score | Top signal | Last session | Action
  - "Action" is a button → opens the intervention modal.
  - Filters: band, language, tenure bucket, days-since-last-session.
- Right rail (optional): "This week's 5 highest-risk" — quick-scan for the ops manager's morning coffee.

### Screen 2 — Interpreter detail (`/interpreters/[id]`)

- Header: name, languages, tenure, current score with band pill.
- Signal breakdown: 6 progress bars, one per signal, each with a one-sentence "why this fired" plain-English explanation.
- 90-day signal timeline: small multiples chart (6 sparklines), Recharts.
- Intervention log: table of past interventions + outcomes.
- CTA: "Log intervention" button → modal (action, notes).

### Screen 3 — Interventions (`/interventions`)

- Table of all interventions across the roster, filterable by outcome.
- Small chart: intervention type → retention rate. Answers "which interventions actually work" as data accumulates.
- This screen is what turns the tool from "risk report" into "operating loop." Sells the deeper value.

## 7. What makes the demo land

- **Explainability**: every Red flag has a plain-English "why". Ops people distrust black boxes.
- **Explorable, not just staring**: filters, drill-in, log-an-action. Feels like a tool, not a slide.
- **A believable dataset**: 400 synthetic interpreters, 90 days of behavior, tuned distributions. Not 5 rows.
- **One-page walkthrough**: I open the dashboard, I click a Red interpreter, I see the signals, I log an intervention — 90 seconds.
- **Deployed on a URL**: send the link ahead of the meeting. Half the meetings will pre-play with it.

## 8. Explicit non-goals for v1

- No auth (single demo tenant; if a prospect asks, "we'll add SSO in the pilot").
- No real ML — rules only, and honest about that.
- No CSV upload UI — ingest is API-only, seed script populates.
- No mobile — LSP ops runs on desktop.
- No white-label / theming — logo swap only for pilots.
- No integrations with Boostlingo, Salesforce, etc — those are pilot-phase asks.

## 9. Two-week build plan (10 working days)

Assumes one person building full-time, or ToosPoint contracting a dev.

| Day | Deliverable |
|---|---|
| 1 | Repo scaffolding: FastAPI + Postgres (docker-compose), Next.js app, shared types. CI green. |
| 2 | Data model migrations, SQLAlchemy models, ingest endpoints wired + tested. |
| 3 | Seed script generating a realistic 400-interpreter, 90-day dataset. Numbers land in target distribution. |
| 4 | Score computation engine: all 6 signals, weighted composite, band assignment. Unit tests per signal. |
| 5 | Nightly recompute job + `/api/scores/recompute` endpoint. Dashboard summary + list endpoints. |
| 6 | Dashboard screen: KPI cards, risk table with filters, band-colored rows. |
| 7 | Interpreter detail screen: header, signal bars with "why" copy, timeline sparklines. |
| 8 | Intervention modal, log endpoint, interventions screen with retention chart. |
| 9 | Polish pass: empty states, loading skeletons, filter persistence, README, deploy to Vercel + Railway/Fly for the API. |
| 10 | Demo script: 90-second walk-through, one-page PDF one-pager, sanity check on realistic data, prospect-specific screenshot pack. |

**Actual elapsed calendar time:** budget 2.5–3 weeks with normal life. Nothing here is exotic.

## 10. Demo playbook (per prospect)

1. **Before the meeting:** send the live URL with a one-line email — "Built this to solve the interpreter attrition problem. It's demo data. 3 minutes to click around before we talk."
2. **In the meeting (15 min):**
   - 90-second live walkthrough (screen 1 → 2 → 3).
   - Ask: "Which of these 6 signals do you already track? Which do you wish you did?"
   - Real conversation: their attrition rate, current intervention loop, what's in their session data.
3. **The ask:** "If we pilot on 3 months of your session data, we can tell you within a week whether the signals predict *your* attrition. If they do, we retain to run the intervention loop for you."
4. **Retainer conversion:** the app is the door-opener. The ToosPoint engagement is running the *intervention discipline* the app surfaces — that's where the $5K/month lives.

## 11. Positioning around each prospect (30-second custom hook)

- **Cloudbreak/Voyce**: healthcare VRI — attrition is a compliance problem too (interpreter continuity in patient encounters).
- **CyraCom**: gov + healthcare — CMS-adjacent scrutiny means retention hits SLA compliance.
- **Propio**: growth-stage — scaling roster fast makes attrition the P&L bottleneck.
- **GLOBO**: on-demand model — decline-rate signal is *especially* predictive for them.
- **AMN Language**: healthcare staffing DNA — they already think in retention/renewal terms; this is native language for their leadership.

## 12. What comes after v1 works

- **Real-data pilot** with the first prospect that says yes → refine weights on their data.
- **ML swap-in** once we have 12+ months of real attrition outcomes: gradient-boosted classifier replaces rules, "why" explanations from SHAP.
- **Boostlingo integration**: if Boostlingo becomes a partner, ChurnScope reads their session API directly.
- **Multi-tenant + auth**: only after the third paying pilot.

## 13. Cost + risk

- **Build cost**: $6-10K if outsourced (2 weeks of a competent full-stack dev), or Sahar's time if in-house.
- **Hosting**: <$50/month (Vercel free + Railway hobby Postgres).
- **Legal risk**: zero if we never ingest real data before a signed pilot agreement. The demo runs entirely on synthetic data.
- **Positioning risk**: if a prospect thinks it's a full product, we lose the consulting angle. Frame from minute one: "This is a diagnostic tool. The value is what you do with the signals — that's where we help."

---

**Decision point before writing code:** confirm (a) build in-house vs contract, (b) demo name (ChurnScope? RetainIQ? something ToosPoint-branded?), (c) which prospect gets the first live pitch.
