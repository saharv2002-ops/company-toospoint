"""Churn scoring engine.

Design:
- Six signals, rules-based, explainable. Each takes a `SignalInputs`
  dataclass and returns a score 0-100.
- Composite score is a weighted average using WEIGHTS from SPEC § 3.
- Data collection (`collect_all_inputs`) does the aggregation work in
  bulk SQL — one query per signal across the full roster — so scoring
  the whole roster is a handful of queries, not per-interpreter.
- `recompute_all` writes to `churn_scores` with idempotent upsert on
  (interpreter_id, as_of).

Signal functions are pure: given inputs, always return the same score.
That's what makes the demo defensible ("here's why she was flagged"
becomes a matter of reading the inputs, no black box).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.enums import ChurnBand, DispatchResponse
from app.models import (
    AvailabilitySnapshot,
    ChurnScore,
    Dispatch,
    Feedback,
    Interpreter,
)
from app.models import Session as SessionModel

# ────────────────────────────────────────────────────────────────
# Signal weights (SPEC § 3). Must sum to 100.
# ────────────────────────────────────────────────────────────────
WEIGHTS: dict[int, int] = {
    1: 25,  # session volume decline
    2: 20,  # dispatch decline-rate rise
    3: 10,  # response latency growth
    4: 15,  # negative feedback spike
    5: 15,  # tenure vulnerability
    6: 15,  # availability shrinkage
}
assert sum(WEIGHTS.values()) == 100

# Band boundaries. Half-open on the right: green [0,40), yellow [40,65), red [65,100].
BAND_YELLOW_MIN = 40
BAND_RED_MIN = 65

# Windows in days
RECENT_DAYS = 14
BASELINE_DAYS = 90
FEEDBACK_WINDOW_DAYS = 30
AVAIL_RECENT_WEEKS = 3
AVAIL_BASELINE_WEEKS = 12


# ────────────────────────────────────────────────────────────────
# Inputs (one per interpreter). All fields are pre-aggregated.
# ────────────────────────────────────────────────────────────────
@dataclass
class SignalInputs:
    interpreter_id: UUID
    hired_at: date

    # Signal 1 — volume
    sessions_recent: int = 0        # count in last RECENT_DAYS
    sessions_baseline: int = 0      # count in the (BASELINE_DAYS - RECENT_DAYS) prior window

    # Signal 2 — decline rate
    dispatches_recent: int = 0
    declines_recent: int = 0
    dispatches_baseline: int = 0
    declines_baseline: int = 0

    # Signal 3 — response latency (median seconds)
    latency_recent_median: float | None = None
    latency_baseline_median: float | None = None

    # Signal 4 — negative feedback
    negative_events_recent: int = 0  # complaints OR ratings < 3 in last FEEDBACK_WINDOW_DAYS

    # Signal 6 — availability
    hours_recent_avg: float | None = None    # last AVAIL_RECENT_WEEKS weeks
    hours_baseline_avg: float | None = None  # weeks BEFORE the recent window, up to AVAIL_BASELINE_WEEKS


# ────────────────────────────────────────────────────────────────
# Pure signal functions
# ────────────────────────────────────────────────────────────────
def _clamp(x: float) -> int:
    return int(max(0, min(100, round(x))))


def signal_1_volume(inp: SignalInputs) -> int:
    """Session volume decline: last 14 days vs prior (BASELINE - RECENT) days.

    A drop of 30% scores 50. A drop of 60%+ scores 100. Any rise = 0.
    Zero baseline volume returns 0 (nothing to compare against).
    """
    recent_per_day = inp.sessions_recent / RECENT_DAYS
    baseline_days = BASELINE_DAYS - RECENT_DAYS
    baseline_per_day = inp.sessions_baseline / baseline_days
    if baseline_per_day == 0:
        return 0
    drop = 1.0 - (recent_per_day / baseline_per_day)  # positive if recent < baseline
    if drop <= 0:
        return 0
    # 30% drop → 50, 60% drop → 100, linear ramp in between
    score = 50 * (drop / 0.30) if drop <= 0.30 else 50 + 50 * ((drop - 0.30) / 0.30)
    return _clamp(score)


def signal_2_decline(inp: SignalInputs) -> int:
    """Dispatch decline-rate rise: recent decline % minus baseline decline %.

    Rise of 15 pts scores 50. Rise of 30 pts+ scores 100.
    """
    if inp.dispatches_recent == 0 or inp.dispatches_baseline == 0:
        return 0
    recent_rate = inp.declines_recent / inp.dispatches_recent
    baseline_rate = inp.declines_baseline / inp.dispatches_baseline
    rise_pts = (recent_rate - baseline_rate) * 100
    if rise_pts <= 0:
        return 0
    score = 50 * (rise_pts / 15) if rise_pts <= 15 else 50 + 50 * ((rise_pts - 15) / 15)
    return _clamp(score)


def signal_3_latency(inp: SignalInputs) -> int:
    """Response-latency growth: median seconds recent vs baseline.

    Growth of 40% scores 50. Growth of 100%+ scores 100.
    """
    if inp.latency_baseline_median is None or inp.latency_baseline_median == 0:
        return 0
    if inp.latency_recent_median is None:
        return 0
    growth = (inp.latency_recent_median / inp.latency_baseline_median) - 1.0
    if growth <= 0:
        return 0
    score = 50 * (growth / 0.40) if growth <= 0.40 else 50 + 50 * ((growth - 0.40) / 0.60)
    return _clamp(score)


def signal_4_feedback(inp: SignalInputs) -> int:
    """Negative-feedback spike in the last FEEDBACK_WINDOW_DAYS.

    0 negative events → 0. 1 → 50. 2 → 80. 3+ → 100.
    """
    n = inp.negative_events_recent
    if n <= 0:
        return 0
    if n == 1:
        return 50
    if n == 2:
        return 80
    return 100


def signal_5_tenure(inp: SignalInputs, as_of: date) -> int:
    """Tenure-vulnerability bell.

    Highest risk clusters at ~4.5 months and ~21 months (industry
    pattern). Trough at 12 months and at 3+ years. Bell centred at
    those two peaks; anything else has a low floor of 15.
    """
    months = (as_of - inp.hired_at).days / 30.44
    if months < 0:
        return 0
    # Two Gaussian bumps: mean 4.5 (sd 2), mean 21 (sd 6). Peaks scaled to 90.
    import math

    def bump(mean: float, sd: float, peak: float = 90) -> float:
        return peak * math.exp(-((months - mean) ** 2) / (2 * sd * sd))

    score = max(bump(4.5, 2.0), bump(21.0, 6.0))
    # Long-tenured interpreters drift back down to a small baseline
    if months > 48:
        score = max(score * 0.4, 10)
    else:
        score = max(score, 15)
    return _clamp(score)


def signal_6_availability(inp: SignalInputs) -> int:
    """Availability-window shrinkage: hours declared recent vs baseline.

    Drop of 25% scores 50. Drop of 50%+ scores 100.
    """
    if inp.hours_baseline_avg is None or inp.hours_baseline_avg == 0:
        return 0
    if inp.hours_recent_avg is None:
        return 0
    drop = 1.0 - (inp.hours_recent_avg / inp.hours_baseline_avg)
    if drop <= 0:
        return 0
    score = 50 * (drop / 0.25) if drop <= 0.25 else 50 + 50 * ((drop - 0.25) / 0.25)
    return _clamp(score)


def band_from_score(score: int) -> ChurnBand:
    if score >= BAND_RED_MIN:
        return ChurnBand.red
    if score >= BAND_YELLOW_MIN:
        return ChurnBand.yellow
    return ChurnBand.green


@dataclass
class ScoreBreakdown:
    interpreter_id: UUID
    signal_1_volume: int
    signal_2_decline: int
    signal_3_latency: int
    signal_4_feedback: int
    signal_5_tenure: int
    signal_6_availability: int
    composite_score: int
    band: ChurnBand


def score_interpreter(inp: SignalInputs, as_of: date) -> ScoreBreakdown:
    s1 = signal_1_volume(inp)
    s2 = signal_2_decline(inp)
    s3 = signal_3_latency(inp)
    s4 = signal_4_feedback(inp)
    s5 = signal_5_tenure(inp, as_of)
    s6 = signal_6_availability(inp)
    weighted = (
        s1 * WEIGHTS[1] + s2 * WEIGHTS[2] + s3 * WEIGHTS[3]
        + s4 * WEIGHTS[4] + s5 * WEIGHTS[5] + s6 * WEIGHTS[6]
    )
    composite = _clamp(weighted / 100)
    return ScoreBreakdown(
        interpreter_id=inp.interpreter_id,
        signal_1_volume=s1,
        signal_2_decline=s2,
        signal_3_latency=s3,
        signal_4_feedback=s4,
        signal_5_tenure=s5,
        signal_6_availability=s6,
        composite_score=composite,
        band=band_from_score(composite),
    )


# ────────────────────────────────────────────────────────────────
# Bulk data collection
# ────────────────────────────────────────────────────────────────
def _utc_dt_at_midnight(d: date) -> datetime:
    return datetime.combine(d, time.min, tzinfo=timezone.utc)


def collect_all_inputs(db: Session, as_of: date) -> list[SignalInputs]:
    """Aggregate all signals for the entire roster in a fixed number of queries.

    Complexity is O(interpreters) rows returned per query, not O(sessions).
    On a 400-interpreter / 100K-session dataset this is <1s total.
    """
    recent_cutoff = _utc_dt_at_midnight(as_of - timedelta(days=RECENT_DAYS))
    baseline_cutoff = _utc_dt_at_midnight(as_of - timedelta(days=BASELINE_DAYS))
    feedback_cutoff = _utc_dt_at_midnight(as_of - timedelta(days=FEEDBACK_WINDOW_DAYS))
    avail_recent_cutoff = as_of - timedelta(weeks=AVAIL_RECENT_WEEKS)
    avail_baseline_cutoff = as_of - timedelta(weeks=AVAIL_BASELINE_WEEKS)

    # Base roster: id + hired_at
    inputs: dict[UUID, SignalInputs] = {
        row.id: SignalInputs(interpreter_id=row.id, hired_at=row.hired_at)
        for row in db.execute(select(Interpreter.id, Interpreter.hired_at)).all()
    }

    # Signal 1 — sessions recent and baseline
    session_rows = db.execute(
        select(
            SessionModel.interpreter_id,
            func.count().filter(SessionModel.started_at >= recent_cutoff).label("recent"),
            func.count()
            .filter(
                SessionModel.started_at >= baseline_cutoff,
                SessionModel.started_at < recent_cutoff,
            )
            .label("baseline"),
        )
        .where(SessionModel.started_at >= baseline_cutoff)
        .group_by(SessionModel.interpreter_id)
    ).all()
    for iid, recent, baseline in session_rows:
        if iid in inputs:
            inputs[iid].sessions_recent = int(recent or 0)
            inputs[iid].sessions_baseline = int(baseline or 0)

    # Signal 2 — dispatches + declines (both windows)
    declined = DispatchResponse.declined.value
    dispatch_rows = db.execute(
        select(
            Dispatch.interpreter_id,
            func.count().filter(Dispatch.offered_at >= recent_cutoff).label("d_recent"),
            func.count()
            .filter(Dispatch.offered_at >= recent_cutoff, Dispatch.response == declined)
            .label("decl_recent"),
            func.count()
            .filter(
                Dispatch.offered_at >= baseline_cutoff,
                Dispatch.offered_at < recent_cutoff,
            )
            .label("d_base"),
            func.count()
            .filter(
                Dispatch.offered_at >= baseline_cutoff,
                Dispatch.offered_at < recent_cutoff,
                Dispatch.response == declined,
            )
            .label("decl_base"),
        )
        .where(Dispatch.offered_at >= baseline_cutoff)
        .group_by(Dispatch.interpreter_id)
    ).all()
    for iid, d_recent, decl_recent, d_base, decl_base in dispatch_rows:
        if iid in inputs:
            inputs[iid].dispatches_recent = int(d_recent or 0)
            inputs[iid].declines_recent = int(decl_recent or 0)
            inputs[iid].dispatches_baseline = int(d_base or 0)
            inputs[iid].declines_baseline = int(decl_base or 0)

    # Signal 3 — median response latency (recent + baseline)
    #   Postgres has percentile_cont; expose it via SQLAlchemy text() for portability.
    latency_recent = db.execute(
        text(
            "SELECT interpreter_id, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (responded_at - offered_at))) "
            "FROM dispatches "
            "WHERE offered_at >= :cutoff AND responded_at IS NOT NULL "
            "GROUP BY interpreter_id"
        ),
        {"cutoff": recent_cutoff},
    ).all()
    for iid, median in latency_recent:
        if iid in inputs and median is not None:
            inputs[iid].latency_recent_median = float(median)

    latency_baseline = db.execute(
        text(
            "SELECT interpreter_id, "
            "percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (responded_at - offered_at))) "
            "FROM dispatches "
            "WHERE offered_at >= :b_cutoff AND offered_at < :r_cutoff "
            "AND responded_at IS NOT NULL "
            "GROUP BY interpreter_id"
        ),
        {"b_cutoff": baseline_cutoff, "r_cutoff": recent_cutoff},
    ).all()
    for iid, median in latency_baseline:
        if iid in inputs and median is not None:
            inputs[iid].latency_baseline_median = float(median)

    # Signal 4 — negative feedback in last 30 days (complaints or rating < 3)
    negative_rows = db.execute(
        select(SessionModel.interpreter_id, func.count().label("n"))
        .join(Feedback, Feedback.session_id == SessionModel.id)
        .where(
            Feedback.submitted_at >= feedback_cutoff,
            (Feedback.complaint_flag.is_(True)) | (Feedback.rating < 3),
        )
        .group_by(SessionModel.interpreter_id)
    ).all()
    for iid, n in negative_rows:
        if iid in inputs:
            inputs[iid].negative_events_recent = int(n or 0)

    # Signal 6 — availability averages
    avail_recent = db.execute(
        select(
            AvailabilitySnapshot.interpreter_id,
            func.avg(AvailabilitySnapshot.hours_declared),
        )
        .where(AvailabilitySnapshot.week_of >= avail_recent_cutoff)
        .group_by(AvailabilitySnapshot.interpreter_id)
    ).all()
    for iid, avg in avail_recent:
        if iid in inputs and avg is not None:
            inputs[iid].hours_recent_avg = float(avg)

    avail_baseline = db.execute(
        select(
            AvailabilitySnapshot.interpreter_id,
            func.avg(AvailabilitySnapshot.hours_declared),
        )
        .where(
            AvailabilitySnapshot.week_of >= avail_baseline_cutoff,
            AvailabilitySnapshot.week_of < avail_recent_cutoff,
        )
        .group_by(AvailabilitySnapshot.interpreter_id)
    ).all()
    for iid, avg in avail_baseline:
        if iid in inputs and avg is not None:
            inputs[iid].hours_baseline_avg = float(avg)

    return list(inputs.values())


@dataclass
class RecomputeResult:
    as_of: date
    scored: int
    band_counts: dict[str, int] = field(default_factory=dict)


def recompute_all(db: Session, as_of: date) -> RecomputeResult:
    inputs = collect_all_inputs(db, as_of)
    breakdowns = [score_interpreter(inp, as_of) for inp in inputs]
    if not breakdowns:
        return RecomputeResult(as_of=as_of, scored=0, band_counts={"red": 0, "yellow": 0, "green": 0})

    rows = [
        {
            "interpreter_id": b.interpreter_id,
            "as_of": as_of,
            "composite_score": b.composite_score,
            "signal_1_volume": b.signal_1_volume,
            "signal_2_decline": b.signal_2_decline,
            "signal_3_latency": b.signal_3_latency,
            "signal_4_feedback": b.signal_4_feedback,
            "signal_5_tenure": b.signal_5_tenure,
            "signal_6_availability": b.signal_6_availability,
            "band": b.band.value,
        }
        for b in breakdowns
    ]
    stmt = pg_insert(ChurnScore).values(rows)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in ChurnScore.__table__.columns
        if c.name not in ("interpreter_id", "as_of")
    }
    stmt = stmt.on_conflict_do_update(index_elements=["interpreter_id", "as_of"], set_=update_cols)
    db.execute(stmt)
    db.commit()

    band_counts = {"red": 0, "yellow": 0, "green": 0}
    for b in breakdowns:
        band_counts[b.band.value] += 1
    return RecomputeResult(as_of=as_of, scored=len(breakdowns), band_counts=band_counts)
