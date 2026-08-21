"""Unit tests for the pure signal functions in app.services.scoring.

Three cases per signal: clearly green input (expect low score), clearly
red input (expect high score), edge case (empty / zero baseline / etc).
Plus composite weighting + band boundary tests. No DB required.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.enums import ChurnBand
from app.services.scoring import (
    BAND_RED_MIN,
    BAND_YELLOW_MIN,
    RECENT_DAYS,
    WEIGHTS,
    SignalInputs,
    band_from_score,
    score_interpreter,
    signal_1_volume,
    signal_2_decline,
    signal_3_latency,
    signal_4_feedback,
    signal_5_tenure,
    signal_6_availability,
)

TODAY = date(2026, 8, 21)


def _base(**over) -> SignalInputs:
    defaults = dict(interpreter_id=uuid4(), hired_at=TODAY - timedelta(days=365 * 3))
    defaults.update(over)
    return SignalInputs(**defaults)


# ── signal 1 ─────────────────────────────────────────────────────────────
def test_signal_1_no_decline_scores_zero():
    # 3/day recent, 3/day baseline
    inp = _base(sessions_recent=3 * RECENT_DAYS, sessions_baseline=3 * (90 - RECENT_DAYS))
    assert signal_1_volume(inp) == 0


def test_signal_1_sharp_decline_scores_red():
    # 1/day recent vs 3/day baseline = 67% drop
    inp = _base(sessions_recent=1 * RECENT_DAYS, sessions_baseline=3 * (90 - RECENT_DAYS))
    s = signal_1_volume(inp)
    assert s >= 80, s


def test_signal_1_zero_baseline_is_zero():
    inp = _base(sessions_recent=5, sessions_baseline=0)
    assert signal_1_volume(inp) == 0


# ── signal 2 ─────────────────────────────────────────────────────────────
def test_signal_2_no_rise_scores_zero():
    inp = _base(
        dispatches_recent=100, declines_recent=5,
        dispatches_baseline=800, declines_baseline=40,
    )  # 5% both
    assert signal_2_decline(inp) == 0


def test_signal_2_sharp_rise_scores_red():
    # 32% recent vs 10% baseline = 22 pts rise
    inp = _base(
        dispatches_recent=100, declines_recent=32,
        dispatches_baseline=800, declines_baseline=80,
    )
    s = signal_2_decline(inp)
    assert s >= 70, s


def test_signal_2_no_dispatches_scores_zero():
    inp = _base(dispatches_recent=0, dispatches_baseline=0)
    assert signal_2_decline(inp) == 0


# ── signal 3 ─────────────────────────────────────────────────────────────
def test_signal_3_no_growth_scores_zero():
    inp = _base(latency_recent_median=12.0, latency_baseline_median=12.0)
    assert signal_3_latency(inp) == 0


def test_signal_3_large_growth_scores_red():
    inp = _base(latency_recent_median=42.0, latency_baseline_median=15.0)  # 180% growth
    s = signal_3_latency(inp)
    assert s >= 90, s


def test_signal_3_missing_baseline_is_zero():
    inp = _base(latency_recent_median=30.0, latency_baseline_median=None)
    assert signal_3_latency(inp) == 0


# ── signal 4 ─────────────────────────────────────────────────────────────
def test_signal_4_no_negatives_scores_zero():
    assert signal_4_feedback(_base(negative_events_recent=0)) == 0


def test_signal_4_multiple_negatives_scores_red():
    assert signal_4_feedback(_base(negative_events_recent=3)) == 100


def test_signal_4_single_negative_mid_score():
    assert signal_4_feedback(_base(negative_events_recent=1)) == 50


# ── signal 5 ─────────────────────────────────────────────────────────────
def test_signal_5_peak_at_4_months_scores_high():
    hired = TODAY - timedelta(days=int(4.5 * 30.44))
    s = signal_5_tenure(_base(hired_at=hired), TODAY)
    assert s >= 75, s


def test_signal_5_stable_veteran_low_score():
    hired = TODAY - timedelta(days=int(6 * 365))
    s = signal_5_tenure(_base(hired_at=hired), TODAY)
    assert s <= 25, s


def test_signal_5_second_peak_at_21_months():
    hired = TODAY - timedelta(days=int(21 * 30.44))
    s = signal_5_tenure(_base(hired_at=hired), TODAY)
    assert s >= 75, s


# ── signal 6 ─────────────────────────────────────────────────────────────
def test_signal_6_no_shrinkage_scores_zero():
    inp = _base(hours_recent_avg=30.0, hours_baseline_avg=30.0)
    assert signal_6_availability(inp) == 0


def test_signal_6_large_shrinkage_scores_red():
    inp = _base(hours_recent_avg=10.0, hours_baseline_avg=30.0)  # 67% drop
    s = signal_6_availability(inp)
    assert s >= 90, s


def test_signal_6_missing_baseline_is_zero():
    inp = _base(hours_recent_avg=None, hours_baseline_avg=30.0)
    assert signal_6_availability(inp) == 0


# ── composite + band ────────────────────────────────────────────────────
def test_composite_weighting_matches_spec():
    # Craft an input where every signal is exactly 100 → composite must be 100
    inp = _base(
        sessions_recent=0, sessions_baseline=1000,          # signal_1 = 100
        dispatches_recent=100, declines_recent=100,
        dispatches_baseline=800, declines_baseline=0,        # signal_2 = 100
        latency_recent_median=100.0, latency_baseline_median=10.0,  # signal_3 = 100
        negative_events_recent=5,                            # signal_4 = 100
        hired_at=TODAY - timedelta(days=int(4.5 * 30.44)),  # signal_5 high
        hours_recent_avg=0.0, hours_baseline_avg=30.0,       # signal_6 = 100
    )
    b = score_interpreter(inp, TODAY)
    # Signal 5 caps at 90, others at 100 — composite ~ (100*85 + 90*15)/100 = 98.5 → 99
    assert b.composite_score >= 95, b
    assert b.band == ChurnBand.red


def test_composite_all_zero_is_green_low():
    inp = _base(
        sessions_recent=30, sessions_baseline=228,  # 3/day both, no decline
        dispatches_recent=100, declines_recent=5,
        dispatches_baseline=800, declines_baseline=40,
        latency_recent_median=10.0, latency_baseline_median=10.0,
        negative_events_recent=0,
        hired_at=TODAY - timedelta(days=6 * 365),
        hours_recent_avg=30.0, hours_baseline_avg=30.0,
    )
    b = score_interpreter(inp, TODAY)
    assert b.band == ChurnBand.green


def test_weights_sum_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_band_boundaries():
    assert band_from_score(0) == ChurnBand.green
    assert band_from_score(BAND_YELLOW_MIN - 1) == ChurnBand.green
    assert band_from_score(BAND_YELLOW_MIN) == ChurnBand.yellow
    assert band_from_score(BAND_RED_MIN - 1) == ChurnBand.yellow
    assert band_from_score(BAND_RED_MIN) == ChurnBand.red
    assert band_from_score(100) == ChurnBand.red
