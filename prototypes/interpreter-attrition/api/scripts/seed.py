"""Seed a realistic demo dataset for ChurnScope.

Design:
- Deterministic via a single seeded RNG so the demo is reproducible.
- Each interpreter is tagged red/yellow/green at generation, and their
  behavior curves (session volume, decline rate, latency, feedback,
  availability) are drawn from tag-appropriate distributions. The Day 4
  scoring engine, working blind, should then place them back into the
  same bucket (that's the whole point).
- Row counts land around ~400 interpreters, ~100k sessions, ~85k
  dispatches, ~6k feedback rows, ~5k availability snapshots. Small
  enough to be fast, large enough to look real in the demo.
- Generation is pure (returns lists of dicts). DB insert is one function
  at the bottom. Tests exercise the pure part with no DB.

Usage:
    python -m scripts.seed --reset
    python -m scripts.seed --reset --seed 7 --total 200
    python -m scripts.seed --dry-run   # generate + print stats, no DB
"""
from __future__ import annotations

import argparse
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import text

from app.db import engine
from app.models import (
    AvailabilitySnapshot,
    Dispatch,
    Feedback,
    Interpreter,
)
from app.models import Session as SessionModel

# ────────────────────────────────────────────────────────────────
# Config knobs — edit here for demo variations
# ────────────────────────────────────────────────────────────────

TOTAL_INTERPRETERS = 400
RED_TARGET_PCT = 12    # % of roster tagged Red
YELLOW_TARGET_PCT = 22  # % of roster tagged Yellow; rest is Green
DAYS_OF_HISTORY = 90
AVAILABILITY_WEEKS = 12
DEFAULT_SEED = 42

# Session/day baseline per risk bucket, before the last-14-day decay
BASELINE_SESSIONS_PER_DAY = {"green": 3.0, "yellow": 3.0, "red": 3.0}

# Multiplicative factor applied to the last 14 days of session count
LAST14_MULTIPLIER = {"green": 1.00, "yellow": 0.80, "red": 0.45}

# Baseline dispatch decline rate (0-1)
DECLINE_RATE_BASELINE = {"green": 0.05, "yellow": 0.09, "red": 0.10}
# Decline rate in the last 14 days
DECLINE_RATE_RECENT = {"green": 0.06, "yellow": 0.18, "red": 0.32}

# Response latency (seconds) baseline and recent
LATENCY_BASELINE_SECS = {"green": 12, "yellow": 15, "red": 18}
LATENCY_RECENT_SECS = {"green": 13, "yellow": 24, "red": 42}

# Weekly availability hours baseline (mean) and recent (last 3 weeks)
AVAIL_HOURS_BASELINE = {"green": 30.0, "yellow": 28.0, "red": 26.0}
AVAIL_HOURS_RECENT = {"green": 30.0, "yellow": 22.0, "red": 12.0}

# Probability a session gets a rating record; sub-fraction that are low
FEEDBACK_ANY_PROB = {"green": 0.05, "yellow": 0.09, "red": 0.14}
FEEDBACK_LOW_FRACTION = {"green": 0.05, "yellow": 0.20, "red": 0.55}

# Language distribution (weight, iso code). Long tail after Spanish.
LANGUAGE_WEIGHTS: list[tuple[str, float]] = [
    ("es", 0.35), ("zh", 0.08), ("ar", 0.06), ("vi", 0.04), ("ru", 0.04),
    ("pt", 0.03), ("fr", 0.03), ("ko", 0.03), ("hi", 0.03), ("so", 0.02),
    ("my", 0.02), ("ne", 0.02), ("sw", 0.02), ("bn", 0.02), ("ta", 0.02),
    ("fa", 0.02), ("ur", 0.02), ("am", 0.015), ("ht", 0.015), ("th", 0.015),
    ("tl", 0.015), ("uk", 0.010), ("pl", 0.010), ("de", 0.010), ("it", 0.010),
    ("ja", 0.008), ("ka", 0.005), ("hy", 0.005), ("kar", 0.004), ("dz", 0.003),
]

TIMEZONES = [
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Phoenix", "America/Anchorage", "Pacific/Honolulu", "America/Mexico_City",
    "America/Bogota", "Europe/London", "Europe/Madrid", "Africa/Nairobi",
    "Asia/Dubai", "Asia/Kolkata", "Asia/Manila", "Asia/Shanghai",
]

CERTS = ["CMI", "CHI-Spanish", "CoreCHI", "NBCMI", "ATA", "Court-Certified"]

FIRST_NAMES = [
    "Maria", "Ana", "Jose", "Luis", "Carmen", "Wei", "Ling", "Hiroshi", "Yuki",
    "Ahmed", "Fatima", "Amir", "Priya", "Raj", "Diego", "Sofia", "Marcus",
    "Amara", "Kwame", "Fatou", "Nia", "Ivan", "Olga", "Nadia", "Tariq",
    "Isabella", "Miguel", "Elena", "Nikolai", "Aisha", "Omar", "Yasmin",
    "Chen", "Mei", "Kenji", "Ravi", "Deepa", "Aleksandar", "Milena",
]
LAST_NAMES = [
    "Garcia", "Martinez", "Chen", "Nguyen", "Patel", "Khan", "Silva", "Kim",
    "Diallo", "Osei", "Petrov", "Kowalski", "Rossi", "Yamada", "Ali",
    "Suzuki", "Reyes", "Fernandez", "Okonkwo", "Nakamura", "Ivanova",
    "Sanchez", "Hernandez", "Sokolov", "Rahimov", "Tekle",
]


@dataclass
class InterpreterRow:
    external_id: str
    full_name: str
    languages: list[str]
    certifications: list[str]
    hired_at: date
    status: str
    home_timezone: str
    risk_bucket: str  # NOT persisted — for behavior generation only


# ────────────────────────────────────────────────────────────────
# Generators (pure — no DB)
# ────────────────────────────────────────────────────────────────

def _weighted_pick(rng: random.Random, choices: list[tuple[Any, float]]) -> Any:
    total = sum(w for _, w in choices)
    r = rng.random() * total
    upto = 0.0
    for item, w in choices:
        upto += w
        if r <= upto:
            return item
    return choices[-1][0]


def _tenure_hired_at(rng: random.Random, today: date) -> date:
    """40% <12 months, 30% 1-3 years, 30% 3+ years."""
    r = rng.random()
    if r < 0.40:
        days = rng.randint(30, 365)
    elif r < 0.70:
        days = rng.randint(365, 3 * 365)
    else:
        days = rng.randint(3 * 365, 8 * 365)
    return today - timedelta(days=days)


def _pick_languages(rng: random.Random) -> list[str]:
    """Every interpreter speaks English + 1-2 other languages, weighted."""
    langs = ["en"]
    primary = _weighted_pick(rng, LANGUAGE_WEIGHTS)
    langs.append(primary)
    if rng.random() < 0.20:  # 20% add a second non-English language
        second = _weighted_pick(rng, LANGUAGE_WEIGHTS)
        if second not in langs:
            langs.append(second)
    return langs


def build_roster(rng: random.Random, total: int, today: date) -> list[InterpreterRow]:
    red_count = round(total * RED_TARGET_PCT / 100)
    yellow_count = round(total * YELLOW_TARGET_PCT / 100)
    green_count = total - red_count - yellow_count

    buckets = ["red"] * red_count + ["yellow"] * yellow_count + ["green"] * green_count
    rng.shuffle(buckets)

    roster: list[InterpreterRow] = []
    for i, bucket in enumerate(buckets):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        certs = rng.sample(CERTS, k=rng.randint(0, 2))
        roster.append(
            InterpreterRow(
                external_id=f"lsp-{i:05d}",
                full_name=f"{first} {last}",
                languages=_pick_languages(rng),
                certifications=certs,
                hired_at=_tenure_hired_at(rng, today),
                status="active",
                home_timezone=rng.choice(TIMEZONES),
                risk_bucket=bucket,
            )
        )
    return roster


def build_sessions(
    rng: random.Random, roster: list[InterpreterRow], today: date
) -> list[dict[str, Any]]:
    """Emit 90 days of sessions. Volume is Poisson-ish; last 14 days decay per bucket."""
    sessions: list[dict[str, Any]] = []
    now = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)
    for interp in roster:
        baseline = BASELINE_SESSIONS_PER_DAY[interp.risk_bucket]
        recent_mult = LAST14_MULTIPLIER[interp.risk_bucket]
        interpreter_key = interp.external_id
        primary_pair = f"en-{[l for l in interp.languages if l != 'en'][0]}"
        for day_offset in range(DAYS_OF_HISTORY):
            day = today - timedelta(days=DAYS_OF_HISTORY - 1 - day_offset)
            in_last_14 = day_offset >= (DAYS_OF_HISTORY - 14)
            mean = baseline * (recent_mult if in_last_14 else 1.0)
            n = _poisson(rng, mean)
            for _ in range(n):
                started = datetime.combine(
                    day, datetime.min.time(), tzinfo=timezone.utc
                ) + timedelta(hours=rng.randint(6, 20), minutes=rng.randint(0, 59))
                duration = int(rng.gauss(600, 180))
                duration = max(60, min(3600, duration))
                sessions.append(
                    {
                        "id": uuid.uuid4(),
                        "interpreter_id": interpreter_key,  # placeholder — swap to real UUID at insert time
                        "client_id": None,
                        "session_type": rng.choices(["opi", "vri", "onsite"], weights=[7, 3, 1])[0],
                        "language_pair": primary_pair,
                        "started_at": started,
                        "duration_seconds": duration,
                        "outcome": rng.choices(
                            ["completed", "dropped", "no_show", "cancelled"],
                            weights=[92, 3, 3, 2],
                        )[0],
                    }
                )
    return sessions


def build_dispatches(
    rng: random.Random, roster: list[InterpreterRow], today: date
) -> list[dict[str, Any]]:
    """Emit dispatches. Each interpreter gets more dispatches than accepted sessions
    (some are declined). Decline rate rises in the last 14 days per bucket."""
    dispatches: list[dict[str, Any]] = []
    for interp in roster:
        interpreter_key = interp.external_id
        primary_pair = f"en-{[l for l in interp.languages if l != 'en'][0]}"
        baseline_dispatches_per_day = BASELINE_SESSIONS_PER_DAY[interp.risk_bucket] * 1.15
        for day_offset in range(DAYS_OF_HISTORY):
            day = today - timedelta(days=DAYS_OF_HISTORY - 1 - day_offset)
            in_last_14 = day_offset >= (DAYS_OF_HISTORY - 14)
            decline_p = (
                DECLINE_RATE_RECENT[interp.risk_bucket]
                if in_last_14
                else DECLINE_RATE_BASELINE[interp.risk_bucket]
            )
            latency_mean = (
                LATENCY_RECENT_SECS[interp.risk_bucket]
                if in_last_14
                else LATENCY_BASELINE_SECS[interp.risk_bucket]
            )
            n = _poisson(rng, baseline_dispatches_per_day)
            for _ in range(n):
                offered = datetime.combine(
                    day, datetime.min.time(), tzinfo=timezone.utc
                ) + timedelta(hours=rng.randint(6, 20), minutes=rng.randint(0, 59))
                r = rng.random()
                if r < decline_p:
                    response = "declined"
                elif r < decline_p + 0.02:
                    response = "timeout"
                else:
                    response = "accepted"
                latency = max(1, int(rng.gauss(latency_mean, latency_mean * 0.4)))
                responded = offered + timedelta(seconds=latency)
                dispatches.append(
                    {
                        "id": uuid.uuid4(),
                        "interpreter_id": interpreter_key,
                        "offered_at": offered,
                        "responded_at": responded,
                        "response": response,
                        "language_pair": primary_pair,
                    }
                )
    return dispatches


def build_feedback(
    rng: random.Random, sessions: list[dict[str, Any]], roster_by_key: dict[str, InterpreterRow]
) -> list[dict[str, Any]]:
    feedback: list[dict[str, Any]] = []
    for session in sessions:
        interp = roster_by_key[session["interpreter_id"]]
        p_any = FEEDBACK_ANY_PROB[interp.risk_bucket]
        if rng.random() >= p_any:
            continue
        low_frac = FEEDBACK_LOW_FRACTION[interp.risk_bucket]
        is_low = rng.random() < low_frac
        rating = rng.randint(1, 3) if is_low else rng.randint(4, 5)
        complaint = is_low and rng.random() < 0.6
        submitted = session["started_at"] + timedelta(hours=rng.randint(1, 72))
        feedback.append(
            {
                "id": uuid.uuid4(),
                "session_id": session["id"],
                "rating": rating,
                "complaint_flag": complaint,
                "category": rng.choice(["quality", "behavior", "punctuality"]) if is_low else None,
                "notes": None,
                "submitted_at": submitted,
            }
        )
    return feedback


def build_availability(
    rng: random.Random, roster: list[InterpreterRow], today: date
) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    for interp in roster:
        interpreter_key = interp.external_id
        for w in range(AVAILABILITY_WEEKS):
            week_of = today - timedelta(weeks=(AVAILABILITY_WEEKS - 1 - w))
            in_recent = w >= (AVAILABILITY_WEEKS - 3)
            mean = (
                AVAIL_HOURS_RECENT[interp.risk_bucket]
                if in_recent
                else AVAIL_HOURS_BASELINE[interp.risk_bucket]
            )
            hours = max(0.0, rng.gauss(mean, mean * 0.15))
            snapshots.append(
                {
                    "interpreter_id": interpreter_key,
                    "week_of": week_of,
                    "hours_declared": Decimal(f"{hours:.2f}"),
                }
            )
    return snapshots


def _poisson(rng: random.Random, mean: float) -> int:
    """Small Poisson sampler good enough for demo means (< 30). Knuth."""
    if mean <= 0:
        return 0
    import math

    l = math.exp(-mean)
    k, p = 0, 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= l:
            return k - 1


# ────────────────────────────────────────────────────────────────
# DB insert
# ────────────────────────────────────────────────────────────────

def _swap_external_to_uuid(
    rows: list[dict[str, Any]], key_map: dict[str, uuid.UUID], key_field: str = "interpreter_id"
) -> None:
    for row in rows:
        row[key_field] = key_map[row[key_field]]


def insert_all(
    engine_,
    roster: list[InterpreterRow],
    sessions: list[dict[str, Any]],
    dispatches: list[dict[str, Any]],
    feedback: list[dict[str, Any]],
    availability: list[dict[str, Any]],
    reset: bool,
) -> None:
    from sqlalchemy.orm import Session as ORMSession

    with ORMSession(engine_) as db:
        if reset:
            for table in ("feedback", "dispatches", "sessions", "availability_snapshots",
                          "interventions", "churn_scores", "interpreters"):
                db.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))
            db.commit()

        interpreter_rows = []
        key_to_uuid: dict[str, uuid.UUID] = {}
        for interp in roster:
            iid = uuid.uuid4()
            key_to_uuid[interp.external_id] = iid
            interpreter_rows.append(
                {
                    "id": iid,
                    "external_id": interp.external_id,
                    "full_name": interp.full_name,
                    "languages": interp.languages,
                    "certifications": interp.certifications,
                    "hired_at": interp.hired_at,
                    "status": interp.status,
                    "home_timezone": interp.home_timezone,
                }
            )
        _swap_external_to_uuid(sessions, key_to_uuid)
        _swap_external_to_uuid(dispatches, key_to_uuid)
        _swap_external_to_uuid(availability, key_to_uuid)

        db.bulk_insert_mappings(Interpreter, interpreter_rows)
        db.bulk_insert_mappings(SessionModel, sessions)
        db.bulk_insert_mappings(Dispatch, dispatches)
        db.bulk_insert_mappings(Feedback, feedback)
        db.bulk_insert_mappings(AvailabilitySnapshot, availability)
        db.commit()


# ────────────────────────────────────────────────────────────────
# Orchestration
# ────────────────────────────────────────────────────────────────

def generate(seed: int, total: int, today: date | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    today = today or datetime.now(timezone.utc).date()
    roster = build_roster(rng, total, today)
    sessions = build_sessions(rng, roster, today)
    dispatches = build_dispatches(rng, roster, today)
    roster_by_key = {r.external_id: r for r in roster}
    feedback = build_feedback(rng, sessions, roster_by_key)
    availability = build_availability(rng, roster, today)
    return {
        "roster": roster,
        "sessions": sessions,
        "dispatches": dispatches,
        "feedback": feedback,
        "availability": availability,
    }


def print_summary(data: dict[str, Any]) -> None:
    roster: list[InterpreterRow] = data["roster"]
    counts = {"red": 0, "yellow": 0, "green": 0}
    for r in roster:
        counts[r.risk_bucket] += 1
    total = len(roster)
    print("── seed summary ──────────────────────────────────")
    print(f"interpreters:        {total}")
    print(f"  red:               {counts['red']:>4}  ({counts['red']/total*100:5.1f} %)")
    print(f"  yellow:            {counts['yellow']:>4}  ({counts['yellow']/total*100:5.1f} %)")
    print(f"  green:             {counts['green']:>4}  ({counts['green']/total*100:5.1f} %)")
    print(f"sessions:            {len(data['sessions']):>7}")
    print(f"dispatches:          {len(data['dispatches']):>7}")
    print(f"feedback:            {len(data['feedback']):>7}")
    print(f"availability:        {len(data['availability']):>7}")
    print("──────────────────────────────────────────────────")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--reset", action="store_true", help="TRUNCATE all tables before insert")
    p.add_argument("--dry-run", action="store_true", help="generate + summarize, skip DB")
    p.add_argument("--seed", type=int, default=DEFAULT_SEED, help="RNG seed (default: 42)")
    p.add_argument("--total", type=int, default=TOTAL_INTERPRETERS, help="interpreter count")
    args = p.parse_args(argv)

    data = generate(seed=args.seed, total=args.total)
    print_summary(data)

    if args.dry_run:
        print("dry-run: skipping DB insert")
        return 0

    insert_all(
        engine,
        data["roster"],
        data["sessions"],
        data["dispatches"],
        data["feedback"],
        data["availability"],
        reset=args.reset,
    )
    print("inserted into DB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
