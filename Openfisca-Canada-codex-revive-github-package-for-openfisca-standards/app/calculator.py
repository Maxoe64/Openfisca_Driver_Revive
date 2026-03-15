from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkInput:
    weekly_hours_bus: float
    weekly_hours_city: float
    weekly_hours_highway: float
    weekly_hours_other: float
    hourly_rate: float


def _positive(value: float) -> float:
    return max(float(value), 0.0)


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


def calculate_overtime_preview(work: WorkInput) -> dict:
    classification = classify_worker(work)
    total_hours = (
        _positive(work.weekly_hours_bus)
        + _positive(work.weekly_hours_city)
        + _positive(work.weekly_hours_highway)
        + _positive(work.weekly_hours_other)
    )
    base_threshold = standard_weekly_hours(classification)
    overtime_hours = max(total_hours - base_threshold, 0.0)
    base_hours = total_hours - overtime_hours
    hourly_rate = _positive(work.hourly_rate)
    overtime_rate = 1.5

    return {
        "classification": classification,
        "total_hours": round(total_hours, 2),
        "standard_hours": base_threshold,
        "overtime_hours": round(overtime_hours, 2),
        "regular_pay": round(base_hours * hourly_rate, 2),
        "overtime_pay": round(overtime_hours * hourly_rate * overtime_rate, 2),
        "total_pay": round(
            base_hours * hourly_rate + overtime_hours * hourly_rate * overtime_rate,
            2,
        ),
        "mode": "preview",
    }
