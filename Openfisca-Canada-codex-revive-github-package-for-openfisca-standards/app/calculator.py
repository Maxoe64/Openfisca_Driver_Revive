from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class WorkInput:
    weekly_hours_bus: float
    weekly_hours_city: float
    weekly_hours_highway: float
    weekly_hours_other: float
    hourly_rate: float


@dataclass
class DailyEntry:
    day: str  # "Mon", "Tue", etc.
    hours_bus: float = 0.0
    hours_city: float = 0.0
    hours_highway: float = 0.0
    hours_other: float = 0.0
    is_holiday: bool = False


@dataclass
class DailyWorkInput:
    days: List[DailyEntry] = field(default_factory=list)
    hourly_rate: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _positive(value: float) -> float:
    return max(float(value), 0.0)


# MVOHWR standard thresholds from the parameter YAML files:
#   CLC (bus/other):  8 h/day, 40 h/week
#   CMVO (city):      9 h/day, 45 h/week
#   HMVO (highway):   no daily OT, 60 h/week
DAILY_THRESHOLDS = {"bus": 8.0, "city": 9.0, "highway": 0.0, "other": 8.0}
WEEKLY_THRESHOLDS = {"bus": 40.0, "city": 45.0, "highway": 60.0, "other": 40.0}
OVERTIME_RATE = 1.5


# ---------------------------------------------------------------------------
# Worker classification
# ---------------------------------------------------------------------------

def classify_worker(work: WorkInput) -> str:
    hours = {
        "bus": _positive(work.weekly_hours_bus),
        "city": _positive(work.weekly_hours_city),
        "highway": _positive(work.weekly_hours_highway),
        "other": _positive(work.weekly_hours_other),
    }
    non_zero = [k for k, v in hours.items() if v > 0]
    if not non_zero:
        return "no-hours"
    if len(non_zero) == 1:
        return f"{non_zero[0]}-only"
    return "mixed"


def majority_category(work: WorkInput) -> str:
    """Determine majority work type using MVOHWR majority-hours rule.

    For mixed employment the regulation groups hours into three buckets:
      highway | city | other (bus + other/forklift/shunt)
    The bucket with the most hours determines the applicable standard.
    """
    highway = _positive(work.weekly_hours_highway)
    city = _positive(work.weekly_hours_city)
    clc = _positive(work.weekly_hours_bus) + _positive(work.weekly_hours_other)

    if highway >= city and highway >= clc and highway > 0:
        return "highway"
    if city >= highway and city >= clc and city > 0:
        return "city"
    return "other"


def standard_weekly_hours(classification: str) -> float:
    # Mirrors repository OpenFisca parameter defaults.
    return {
        "bus-only": 40.0,
        "other-only": 40.0,
        "city-only": 45.0,
        "highway-only": 60.0,
        "mixed": 40.0,
        "no-hours": 40.0,
    }[classification]


def standard_weekly_hours_for_category(category: str) -> float:
    return WEEKLY_THRESHOLDS.get(category, 40.0)


# ---------------------------------------------------------------------------
# Simple weekly preview (original behaviour, now with majority logic)
# ---------------------------------------------------------------------------

def calculate_overtime_preview(work: WorkInput) -> dict:
    classification = classify_worker(work)
    total_hours = (
        _positive(work.weekly_hours_bus)
        + _positive(work.weekly_hours_city)
        + _positive(work.weekly_hours_highway)
        + _positive(work.weekly_hours_other)
    )

    if classification == "mixed":
        maj = majority_category(work)
        base_threshold = standard_weekly_hours_for_category(maj)
        explanation = (
            f"Mixed employment: majority hours are '{maj}', "
            f"so the {base_threshold}h weekly threshold applies."
        )
    else:
        base_threshold = standard_weekly_hours(classification)
        maj = classification.replace("-only", "")
        explanation = f"Single work type: {base_threshold}h weekly threshold applies."

    overtime_hours = max(total_hours - base_threshold, 0.0)
    base_hours = total_hours - overtime_hours
    hourly_rate = _positive(work.hourly_rate)

    return {
        "classification": classification,
        "majority_category": maj,
        "total_hours": round(total_hours, 2),
        "standard_hours": base_threshold,
        "overtime_hours": round(overtime_hours, 2),
        "regular_pay": round(base_hours * hourly_rate, 2),
        "overtime_pay": round(overtime_hours * hourly_rate * OVERTIME_RATE, 2),
        "total_pay": round(
            base_hours * hourly_rate + overtime_hours * hourly_rate * OVERTIME_RATE,
            2,
        ),
        "overtime_rate": OVERTIME_RATE,
        "explanation": explanation,
        "mode": "preview",
    }


# ---------------------------------------------------------------------------
# Daily breakdown calculator — gives both daily OT and weekly OT,
# then takes the better of the two (as MVOHWR requires).
# ---------------------------------------------------------------------------

def _daily_ot_for_entry(entry: DailyEntry) -> float:
    """Calculate daily overtime for a single day.

    Highway-only days have NO daily overtime (MVOHWR uses weekly 60h rule).
    For non-highway work, daily OT = max(0, non_highway_hours - daily_threshold).
    Holidays also have no daily OT.
    """
    if entry.is_holiday:
        return 0.0

    bus = _positive(entry.hours_bus)
    city = _positive(entry.hours_city)
    highway = _positive(entry.hours_highway)
    other = _positive(entry.hours_other)

    non_highway = bus + city + other
    total = non_highway + highway

    if total == 0:
        return 0.0

    # If highway-only day, no daily OT
    if non_highway == 0 and highway > 0:
        return 0.0

    # Determine daily threshold based on majority non-highway type
    if city >= bus and city >= other and city > 0:
        threshold = DAILY_THRESHOLDS["city"]  # 9h
    else:
        threshold = DAILY_THRESHOLDS["other"]  # 8h (CLC standard)

    return max(non_highway - threshold, 0.0)


def calculate_daily_breakdown(input_data: DailyWorkInput) -> dict:
    """Full 7-day breakdown with daily OT, weekly OT, and best-of comparison."""
    days_detail = []
    total_bus = 0.0
    total_city = 0.0
    total_highway = 0.0
    total_other = 0.0
    total_daily_ot = 0.0
    holiday_count = 0

    for entry in input_data.days:
        bus = _positive(entry.hours_bus)
        city = _positive(entry.hours_city)
        highway = _positive(entry.hours_highway)
        other = _positive(entry.hours_other)
        day_total = bus + city + highway + other
        daily_ot = _daily_ot_for_entry(entry)

        total_bus += bus
        total_city += city
        total_highway += highway
        total_other += other
        total_daily_ot += daily_ot
        if entry.is_holiday:
            holiday_count += 1

        days_detail.append({
            "day": entry.day,
            "hours_bus": round(bus, 2),
            "hours_city": round(city, 2),
            "hours_highway": round(highway, 2),
            "hours_other": round(other, 2),
            "day_total": round(day_total, 2),
            "daily_overtime": round(daily_ot, 2),
            "is_holiday": entry.is_holiday,
        })

    # Weekly totals
    weekly_total = total_bus + total_city + total_highway + total_other

    # Determine majority category for weekly threshold
    work = WorkInput(
        weekly_hours_bus=total_bus,
        weekly_hours_city=total_city,
        weekly_hours_highway=total_highway,
        weekly_hours_other=total_other,
        hourly_rate=input_data.hourly_rate,
    )
    classification = classify_worker(work)
    maj = majority_category(work)

    if classification == "mixed":
        weekly_threshold = standard_weekly_hours_for_category(maj)
    else:
        weekly_threshold = standard_weekly_hours(classification)

    weekly_ot = max(weekly_total - weekly_threshold, 0.0)

    # MVOHWR: take the BETTER of daily vs weekly OT (higher = better for worker)
    best_ot = max(total_daily_ot, weekly_ot)
    ot_method = "daily" if total_daily_ot >= weekly_ot else "weekly"

    hourly_rate = _positive(input_data.hourly_rate)
    regular_hours = weekly_total - best_ot
    regular_pay = round(regular_hours * hourly_rate, 2)
    overtime_pay = round(best_ot * hourly_rate * OVERTIME_RATE, 2)

    return {
        "days": days_detail,
        "classification": classification,
        "majority_category": maj,
        "weekly_total_hours": round(weekly_total, 2),
        "weekly_threshold": weekly_threshold,
        "holiday_count": holiday_count,
        "daily_overtime_total": round(total_daily_ot, 2),
        "weekly_overtime": round(weekly_ot, 2),
        "best_overtime_hours": round(best_ot, 2),
        "overtime_method": ot_method,
        "regular_pay": regular_pay,
        "overtime_pay": overtime_pay,
        "total_pay": round(regular_pay + overtime_pay, 2),
        "overtime_rate": OVERTIME_RATE,
        "hourly_rate": hourly_rate,
        "mode": "daily-breakdown",
    }
