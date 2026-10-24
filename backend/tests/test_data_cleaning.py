import pytest
from backend.app.services.data_cleaning import (
    clean_fuelhh_records,
    clean_windfor_records,
    generate_expected_intervals,
    TOTAL_EXPECTED_INTERVALS,
)

def test_expected_intervals_january_2026():
    intervals = generate_expected_intervals()
    assert len(intervals) == TOTAL_EXPECTED_INTERVALS
    assert len(intervals) == 1488  # 31 days * 48 periods
    assert intervals[0]["deliveryTime"] == "2026-01-01T00:00:00Z"
    assert intervals[0]["settlementPeriod"] == 1
    assert intervals[-1]["deliveryTime"] == "2026-01-31T23:30:00Z"
    assert intervals[-1]["settlementPeriod"] == 48

def test_clean_fuelhh_filters_wind_and_dates():
    raw_data = [
        # Valid WIND record in Jan 2026
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T00:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 10500.5,
        },
        # Non-wind (SOLAR) -> Must be ignored
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2026-01-01T00:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 1,
            "fuelType": "SOLAR",
            "generation": 0,
        },
        # WIND but in February 2026 -> Must be ignored
        {
            "startTime": "2026-02-01T00:00:00Z",
            "publishTime": "2026-02-01T00:30:00Z",
            "settlementDate": "2026-02-01",
            "settlementPeriod": 1,
            "fuelType": "WIND",
            "generation": 8000,
        },
        # Invalid generation (NaN/null) -> Must be ignored
        {
            "startTime": "2026-01-01T01:00:00Z",
            "publishTime": "2026-01-01T01:30:00Z",
            "settlementDate": "2026-01-01",
            "settlementPeriod": 3,
            "fuelType": "WIND",
            "generation": None,
        },
    ]

    cleaned, diag = clean_fuelhh_records(raw_data)
    assert len(cleaned) == 1
    assert cleaned[0].startTime == "2026-01-01T00:00:00Z"
    assert cleaned[0].generation == 10500.5
    assert cleaned[0].fuelType == "WIND"
    assert diag["fuel_type_wind"] == 3
    assert diag["out_of_range"] == 1
    assert diag["invalid_generation"] == 1

def test_clean_windfor_filters_and_preserves_december_publishes():
    raw_data = [
        # Valid forecast for Jan 1 delivery, published in late Dec
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-30T12:00:00Z",
            "generation": 9800,
        },
        # Duplicate of above (same startTime and publishTime)
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-30T12:00:00Z",
            "generation": 9800,
        },
        # Updated forecast for Jan 1 delivery, published in Dec 31
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T12:00:00Z",
            "generation": 9900,
        },
        # Forecast for Feb 1 delivery -> Must be excluded
        {
            "startTime": "2026-02-01T00:00:00Z",
            "publishTime": "2026-01-30T12:00:00Z",
            "generation": 11000,
        },
    ]

    cleaned, diag = clean_windfor_records(raw_data)
    assert len(cleaned) == 2
    assert diag["duplicates_removed"] == 1
    assert diag["out_of_range_start"] == 1
    assert cleaned[0].startTime == "2026-01-01T00:00:00Z"
    assert cleaned[1].startTime == "2026-01-01T00:00:00Z"
