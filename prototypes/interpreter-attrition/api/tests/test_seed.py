"""Tests for scripts/seed.py — pure generators, no DB required.

Verifies distributions land within tolerance and that risk-bucket
behavior differences are actually present in the generated data.
"""
from datetime import date, timedelta

import pytest

from scripts import seed


@pytest.fixture(scope="module")
def data():
    return seed.generate(seed=42, total=400, today=date(2026, 8, 21))


def _within(actual_pct: float, target_pct: float, tolerance: float = 2.0) -> bool:
    return abs(actual_pct - target_pct) <= tolerance


def test_roster_size(data):
    assert len(data["roster"]) == 400


def test_risk_bucket_distribution(data):
    roster = data["roster"]
    total = len(roster)
    red_pct = sum(1 for r in roster if r.risk_bucket == "red") / total * 100
    yellow_pct = sum(1 for r in roster if r.risk_bucket == "yellow") / total * 100
    green_pct = sum(1 for r in roster if r.risk_bucket == "green") / total * 100
    assert _within(red_pct, seed.RED_TARGET_PCT), red_pct
    assert _within(yellow_pct, seed.YELLOW_TARGET_PCT), yellow_pct
    assert _within(green_pct, 100 - seed.RED_TARGET_PCT - seed.YELLOW_TARGET_PCT), green_pct


def test_all_interpreters_speak_english(data):
    assert all("en" in r.languages for r in data["roster"])


def test_tenure_spread(data):
    today = date(2026, 8, 21)
    tenures_days = [(today - r.hired_at).days for r in data["roster"]]
    lt_1yr = sum(1 for d in tenures_days if d < 365) / len(tenures_days)
    yr_3_plus = sum(1 for d in tenures_days if d >= 3 * 365) / len(tenures_days)
    # 40 / 30 / 30 with tolerance
    assert 0.30 <= lt_1yr <= 0.50, lt_1yr
    assert 0.20 <= yr_3_plus <= 0.45, yr_3_plus


def test_sessions_present_and_bucketed(data):
    sessions = data["sessions"]
    assert len(sessions) > 30_000  # ~3/day * 90 days * 400 with recent decay
    roster_by_key = {r.external_id: r for r in data["roster"]}
    # Every session references an interpreter that exists
    ids = {r.external_id for r in data["roster"]}
    assert all(s["interpreter_id"] in ids for s in sessions[:200])
    # Red interpreters should have visibly fewer sessions in last 14 days
    today = date(2026, 8, 21)
    cutoff = today - timedelta(days=14)
    red_recent = 0
    red_baseline = 0
    green_recent = 0
    green_baseline = 0
    for s in sessions:
        bucket = roster_by_key[s["interpreter_id"]].risk_bucket
        recent = s["started_at"].date() >= cutoff
        if bucket == "red":
            if recent:
                red_recent += 1
            else:
                red_baseline += 1
        elif bucket == "green":
            if recent:
                green_recent += 1
            else:
                green_baseline += 1
    # Red per-day recent should be materially lower than red per-day baseline
    red_recent_per_day = red_recent / 14
    red_baseline_per_day = red_baseline / (seed.DAYS_OF_HISTORY - 14)
    assert red_recent_per_day < red_baseline_per_day * 0.7, (
        red_recent_per_day, red_baseline_per_day
    )
    # Green should hold roughly steady
    green_recent_per_day = green_recent / 14
    green_baseline_per_day = green_baseline / (seed.DAYS_OF_HISTORY - 14)
    assert green_recent_per_day > green_baseline_per_day * 0.85, (
        green_recent_per_day, green_baseline_per_day
    )


def test_dispatches_recent_decline_rate_higher_for_red(data):
    today = date(2026, 8, 21)
    cutoff = today - timedelta(days=14)
    roster_by_key = {r.external_id: r for r in data["roster"]}

    def decline_rate(bucket: str, recent: bool) -> float:
        total = declined = 0
        for d in data["dispatches"]:
            b = roster_by_key[d["interpreter_id"]].risk_bucket
            if b != bucket:
                continue
            is_recent = d["offered_at"].date() >= cutoff
            if is_recent != recent:
                continue
            total += 1
            if d["response"] == "declined":
                declined += 1
        return declined / total if total else 0.0

    assert decline_rate("red", True) > decline_rate("red", False) + 0.10
    assert decline_rate("green", True) < 0.15
    assert decline_rate("red", True) > 0.20


def test_feedback_complaints_cluster_on_at_risk(data):
    roster_by_key = {r.external_id: r for r in data["roster"]}
    session_bucket = {s["id"]: roster_by_key[s["interpreter_id"]].risk_bucket for s in data["sessions"]}
    complaints_by_bucket = {"red": 0, "yellow": 0, "green": 0}
    for f in data["feedback"]:
        if f["complaint_flag"]:
            complaints_by_bucket[session_bucket[f["session_id"]]] += 1
    total_complaints = sum(complaints_by_bucket.values())
    if total_complaints == 0:
        pytest.fail("no complaints generated — distributions are off")
    red_pct = complaints_by_bucket["red"] / total_complaints
    green_pct = complaints_by_bucket["green"] / total_complaints
    assert red_pct > green_pct, (complaints_by_bucket, red_pct, green_pct)


def test_availability_shrinks_for_at_risk(data):
    roster_by_key = {r.external_id: r for r in data["roster"]}
    today = date(2026, 8, 21)
    recent_cutoff_week = today - timedelta(weeks=3)

    def avg_hours(bucket: str, recent: bool) -> float:
        totals: list[float] = []
        for a in data["availability"]:
            b = roster_by_key[a["interpreter_id"]].risk_bucket
            if b != bucket:
                continue
            is_recent = a["week_of"] >= recent_cutoff_week
            if is_recent != recent:
                continue
            totals.append(float(a["hours_declared"]))
        return sum(totals) / len(totals) if totals else 0.0

    assert avg_hours("red", True) < avg_hours("red", False) * 0.7
    assert avg_hours("green", True) > avg_hours("green", False) * 0.85


def test_determinism(data):
    data2 = seed.generate(seed=42, total=400, today=date(2026, 8, 21))
    assert len(data2["roster"]) == len(data["roster"])
    assert [r.external_id for r in data2["roster"]] == [r.external_id for r in data["roster"]]
    assert [r.risk_bucket for r in data2["roster"]] == [r.risk_bucket for r in data["roster"]]
