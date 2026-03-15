from app.calculator import WorkInput, calculate_overtime_preview


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
