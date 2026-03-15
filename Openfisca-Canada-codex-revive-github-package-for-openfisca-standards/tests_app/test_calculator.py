from app.calculator import (
    DailyEntry, DailyWorkInput, WorkInput,
    calculate_daily_breakdown, calculate_overtime_preview,
    classify_worker, majority_category,
)


# ---------------------------------------------------------------------------
# classify_worker
# ---------------------------------------------------------------------------

def test_classify_single_city():
    w = WorkInput(0, 50, 0, 0, 20)
    assert classify_worker(w) == "city-only"


def test_classify_mixed():
    w = WorkInput(10, 20, 5, 0, 20)
    assert classify_worker(w) == "mixed"


def test_classify_no_hours():
    w = WorkInput(0, 0, 0, 0, 20)
    assert classify_worker(w) == "no-hours"


# ---------------------------------------------------------------------------
# majority_category (MVOHWR majority-hours rule)
# ---------------------------------------------------------------------------

def test_majority_highway():
    w = WorkInput(5, 10, 30, 0, 20)
    assert majority_category(w) == "highway"


def test_majority_city():
    w = WorkInput(5, 30, 10, 0, 20)
    assert majority_category(w) == "city"


def test_majority_other():
    w = WorkInput(20, 5, 5, 10, 20)
    # bus + other = 30, highway = 5, city = 5 => "other" bucket wins
    assert majority_category(w) == "other"


# ---------------------------------------------------------------------------
# Quick estimate (weekly)
# ---------------------------------------------------------------------------

def test_city_operator_overtime():
    result = calculate_overtime_preview(
        WorkInput(weekly_hours_bus=0, weekly_hours_city=50, weekly_hours_highway=0, weekly_hours_other=0, hourly_rate=20)
    )
    assert result["classification"] == "city-only"
    assert result["standard_hours"] == 45.0
    assert result["overtime_hours"] == 5.0
    assert result["total_pay"] == 1050.0


def test_highway_operator_no_overtime():
    result = calculate_overtime_preview(
        WorkInput(weekly_hours_bus=0, weekly_hours_city=0, weekly_hours_highway=60, weekly_hours_other=0, hourly_rate=30)
    )
    assert result["classification"] == "highway-only"
    assert result["overtime_hours"] == 0.0
    assert result["total_pay"] == 1800.0


def test_mixed_uses_majority_category():
    # 30h highway + 15h city => majority = highway => threshold = 60h
    result = calculate_overtime_preview(
        WorkInput(weekly_hours_bus=0, weekly_hours_city=15, weekly_hours_highway=30, weekly_hours_other=0, hourly_rate=20)
    )
    assert result["classification"] == "mixed"
    assert result["majority_category"] == "highway"
    assert result["standard_hours"] == 60.0
    assert result["overtime_hours"] == 0.0  # 45h < 60h threshold


def test_mixed_city_majority():
    # 30h city + 5h bus => majority = city => threshold = 45h
    result = calculate_overtime_preview(
        WorkInput(weekly_hours_bus=5, weekly_hours_city=30, weekly_hours_highway=0, weekly_hours_other=15, hourly_rate=25)
    )
    assert result["classification"] == "mixed"
    assert result["majority_category"] == "city"
    assert result["standard_hours"] == 45.0
    assert result["overtime_hours"] == 5.0  # 50h - 45h


def test_result_includes_explanation():
    result = calculate_overtime_preview(
        WorkInput(0, 50, 0, 0, 20)
    )
    assert "explanation" in result
    assert len(result["explanation"]) > 0


# ---------------------------------------------------------------------------
# Daily breakdown
# ---------------------------------------------------------------------------

def test_daily_breakdown_no_overtime():
    days = [
        DailyEntry("Mon", hours_city=8),
        DailyEntry("Tue", hours_city=8),
        DailyEntry("Wed", hours_city=8),
        DailyEntry("Thu", hours_city=8),
        DailyEntry("Fri", hours_city=8),
        DailyEntry("Sat"),
        DailyEntry("Sun"),
    ]
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["weekly_total_hours"] == 40.0
    assert result["best_overtime_hours"] == 0.0
    assert result["classification"] == "city-only"


def test_daily_overtime_exceeds_weekly():
    # 5 days of 11h city = 55h total
    # Daily OT: each day 11-9 = 2h, total = 10h daily OT
    # Weekly OT: 55 - 45 = 10h
    # Both 10h => daily wins (>=)
    days = [DailyEntry(d, hours_city=11) for d in ["Mon", "Tue", "Wed", "Thu", "Fri"]]
    days += [DailyEntry("Sat"), DailyEntry("Sun")]
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["daily_overtime_total"] == 10.0
    assert result["weekly_overtime"] == 10.0
    assert result["best_overtime_hours"] == 10.0


def test_daily_overtime_better_than_weekly():
    # 3 days of 14h city + 2 days of 5h city = 52h total
    # Daily OT: 3 * (14-9) = 15h, 2 days under threshold = 0
    # Weekly OT: 52 - 45 = 7h
    # Daily (15h) > weekly (7h) => daily wins
    days = [
        DailyEntry("Mon", hours_city=14),
        DailyEntry("Tue", hours_city=14),
        DailyEntry("Wed", hours_city=14),
        DailyEntry("Thu", hours_city=5),
        DailyEntry("Fri", hours_city=5),
        DailyEntry("Sat"),
        DailyEntry("Sun"),
    ]
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["daily_overtime_total"] == 15.0
    assert result["weekly_overtime"] == 7.0
    assert result["best_overtime_hours"] == 15.0
    assert result["overtime_method"] == "daily"


def test_weekly_overtime_better_than_daily():
    # 6 days of 9h city = 54h total
    # Daily OT: each day 9-9 = 0h (exactly at threshold)
    # Weekly OT: 54 - 45 = 9h
    # Weekly wins
    days = [DailyEntry(d, hours_city=9) for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]]
    days.append(DailyEntry("Sun"))
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["daily_overtime_total"] == 0.0
    assert result["weekly_overtime"] == 9.0
    assert result["best_overtime_hours"] == 9.0
    assert result["overtime_method"] == "weekly"


def test_highway_only_day_no_daily_ot():
    # Highway-only days should have 0 daily OT
    days = [
        DailyEntry("Mon", hours_highway=12),
        DailyEntry("Tue", hours_highway=12),
        DailyEntry("Wed", hours_highway=12),
        DailyEntry("Thu", hours_highway=12),
        DailyEntry("Fri", hours_highway=12),
        DailyEntry("Sat"),
        DailyEntry("Sun"),
    ]
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["daily_overtime_total"] == 0.0
    assert result["weekly_overtime"] == 0.0  # 60h = 60h threshold


def test_holiday_skips_daily_ot():
    # A holiday with 12h city should NOT generate daily OT
    days = [
        DailyEntry("Mon", hours_city=12, is_holiday=True),
        DailyEntry("Tue", hours_city=8),
        DailyEntry("Wed"),
        DailyEntry("Thu"),
        DailyEntry("Fri"),
        DailyEntry("Sat"),
        DailyEntry("Sun"),
    ]
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["days"][0]["daily_overtime"] == 0.0  # holiday
    assert result["holiday_count"] == 1


def test_daily_breakdown_pay_calculation():
    # 50h city at $20/h with 5h OT => regular: 45*20=900, OT: 5*20*1.5=150
    days = [DailyEntry(d, hours_city=10) for d in ["Mon", "Tue", "Wed", "Thu", "Fri"]]
    days.append(DailyEntry("Sat"))
    days.append(DailyEntry("Sun"))
    result = calculate_daily_breakdown(DailyWorkInput(days=days, hourly_rate=20))
    assert result["weekly_total_hours"] == 50.0
    assert result["total_pay"] == 1050.0
