"""Plain-English "why fired" copy for each signal.

Given the signal inputs and the computed score, produce ≤1 sentence
that an ops manager can read and act on. When a signal scores 0, the
explanation is a neutral note that nothing fired.

Design: no per-signal magic strings scattered across the codebase.
`explain_signal(key, inputs)` returns the right sentence for that
signal number, using data from the same SignalInputs the scorer used.
"""
from __future__ import annotations

from datetime import date

from app.services.scoring import (
    BASELINE_DAYS,
    FEEDBACK_WINDOW_DAYS,
    RECENT_DAYS,
    SignalInputs,
    signal_1_volume,
    signal_2_decline,
    signal_3_latency,
    signal_4_feedback,
    signal_5_tenure,
    signal_6_availability,
)

SIGNAL_NAMES: dict[int, str] = {
    1: "Session volume decline",
    2: "Dispatch decline-rate rise",
    3: "Response latency growth",
    4: "Negative feedback spike",
    5: "Tenure vulnerability",
    6: "Availability shrinkage",
}


def _pct_drop(a: float, b: float) -> int:
    """Percent decrease from b (baseline) to a (recent). Positive if a < b."""
    if b == 0:
        return 0
    return round((1 - a / b) * 100)


def explain_volume(inp: SignalInputs) -> str:
    recent_per_day = inp.sessions_recent / RECENT_DAYS
    baseline_days = BASELINE_DAYS - RECENT_DAYS
    baseline_per_day = inp.sessions_baseline / baseline_days if baseline_days > 0 else 0
    if baseline_per_day == 0:
        return "No baseline session history to compare against."
    drop = _pct_drop(recent_per_day, baseline_per_day)
    if drop <= 0:
        return f"Session volume steady ({recent_per_day:.1f}/day recent vs {baseline_per_day:.1f}/day baseline)."
    return (
        f"Sessions in the last {RECENT_DAYS} days are {drop}% below the "
        f"prior {baseline_days}-day baseline "
        f"({recent_per_day:.1f}/day vs {baseline_per_day:.1f}/day)."
    )


def explain_decline(inp: SignalInputs) -> str:
    if inp.dispatches_recent == 0 or inp.dispatches_baseline == 0:
        return "No dispatch history to compare."
    recent_pct = round(inp.declines_recent / inp.dispatches_recent * 100)
    baseline_pct = round(inp.declines_baseline / inp.dispatches_baseline * 100)
    rise = recent_pct - baseline_pct
    if rise <= 0:
        return f"Decline rate steady ({recent_pct}% recent vs {baseline_pct}% baseline)."
    return (
        f"Declining {recent_pct}% of dispatch offers in the last {RECENT_DAYS} days, "
        f"up from {baseline_pct}% baseline (+{rise} pts)."
    )


def explain_latency(inp: SignalInputs) -> str:
    r, b = inp.latency_recent_median, inp.latency_baseline_median
    if r is None or b is None or b == 0:
        return "Not enough response data to compare."
    growth = round((r / b - 1) * 100)
    if growth <= 0:
        return f"Response latency steady (median {r:.0f}s recent vs {b:.0f}s baseline)."
    return (
        f"Median response time has grown {growth}% "
        f"(from {b:.0f}s baseline to {r:.0f}s in the last {RECENT_DAYS} days)."
    )


def explain_feedback(inp: SignalInputs) -> str:
    n = inp.negative_events_recent
    if n <= 0:
        return f"No complaints or low ratings in the last {FEEDBACK_WINDOW_DAYS} days."
    if n == 1:
        return f"1 complaint or low rating logged in the last {FEEDBACK_WINDOW_DAYS} days."
    return f"{n} complaints or low ratings logged in the last {FEEDBACK_WINDOW_DAYS} days."


def explain_tenure(inp: SignalInputs, as_of: date) -> str:
    months = (as_of - inp.hired_at).days / 30.44
    if 3 <= months <= 6:
        return f"Tenure {months:.1f} months — inside the 3-6 month early-attrition window."
    if 18 <= months <= 24:
        return f"Tenure {months:.1f} months — inside the 18-24 month mid-tenure disengagement window."
    if months < 3:
        return f"Tenure {months:.1f} months — still ramping."
    if months > 48:
        return f"Tenure {months / 12:.1f} years — long-tenured, low structural risk."
    return f"Tenure {months:.1f} months — outside the two high-risk tenure windows."


def explain_availability(inp: SignalInputs) -> str:
    r, b = inp.hours_recent_avg, inp.hours_baseline_avg
    if r is None or b is None or b == 0:
        return "No availability history to compare."
    drop = _pct_drop(r, b)
    if drop <= 0:
        return f"Availability holding steady ({r:.0f}h/wk recent vs {b:.0f}h/wk baseline)."
    return (
        f"Declared availability dropped {drop}% "
        f"(from {b:.0f}h/wk baseline to {r:.0f}h/wk in the last 3 weeks)."
    )


def explain_signal(key: int, inp: SignalInputs, as_of: date) -> str:
    if key == 1:
        return explain_volume(inp)
    if key == 2:
        return explain_decline(inp)
    if key == 3:
        return explain_latency(inp)
    if key == 4:
        return explain_feedback(inp)
    if key == 5:
        return explain_tenure(inp, as_of)
    if key == 6:
        return explain_availability(inp)
    raise ValueError(f"unknown signal key: {key}")


SIGNAL_FUNCS = {
    1: signal_1_volume,
    2: signal_2_decline,
    3: signal_3_latency,
    4: signal_4_feedback,
    5: signal_5_tenure,
    6: signal_6_availability,
}


def score_signal(key: int, inp: SignalInputs, as_of: date) -> int:
    """Recompute a single signal score. Handy for the read endpoints
    that need per-signal readouts alongside the "why" copy."""
    if key == 5:
        return signal_5_tenure(inp, as_of)
    return SIGNAL_FUNCS[key](inp)
