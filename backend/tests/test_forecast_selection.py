import pytest
from datetime import datetime, timezone
from backend.app.models.schemas import FuelHHRecord, WindforRecord
from backend.app.services.forecast_selection import (
    calculate_cutoff_datetime,
    select_forecasts_and_match,
)

def test_cutoff_calculation_d1_0920():
    # Delivery on Jan 15 14:00 UTC -> D-1 is Jan 14. Cutoff is Jan 14 09:20:00 UTC (Europe/London GMT)
    dt = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_cutoff_datetime(dt, cutoff_type="d1_0920")
    assert cutoff == datetime(2026, 1, 14, 9, 20, 0, tzinfo=timezone.utc)

def test_cutoff_calculation_d1_1200():
    # Sensitivity case: Delivery on Jan 15 14:00 UTC -> Cutoff is Jan 14 12:00:00 UTC
    dt = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_cutoff_datetime(dt, cutoff_type="d1_1200")
    assert cutoff == datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc)

def test_cutoff_calculation_lead_24h():
    # Delivery on Jan 15 14:00 UTC -> Cutoff is Jan 14 14:00:00 UTC
    dt = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_cutoff_datetime(dt, cutoff_type="lead_24h")
    assert cutoff == datetime(2026, 1, 14, 14, 0, 0, tzinfo=timezone.utc)

def test_cutoff_calculation_latest():
    # Delivery on Jan 15 14:00 UTC -> Cutoff is Jan 15 14:00:00 UTC
    dt = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_cutoff_datetime(dt, cutoff_type="latest")
    assert cutoff == dt

def test_d1_0920_eligibility_boundary():
    # Requirement: A forecast published at 09:19 on D-1 is eligible; one at 09:21 is not.
    delivery_iso = "2026-01-02T12:00:00Z"
    actual_rec = FuelHHRecord(
        startTime=delivery_iso,
        settlementDate="2026-01-02",
        settlementPeriod=25,
        fuelType="WIND",
        generation=100.0,
    )
    forecasts = [
        # Published at 09:19 UTC on D-1 (Jan 1) -> Eligible
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T09:19:00Z", generation=110.0),
        # Published at 09:21 UTC on D-1 (Jan 1) -> Excluded (after 09:20 cutoff)
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T09:21:00Z", generation=130.0),
    ]

    records, diag = select_forecasts_and_match(
        actual_records=[actual_rec],
        forecast_records=forecasts,
        cutoff_type="d1_0920",
        alignment="exact",
        start_date_iso=delivery_iso,
        end_date_iso=delivery_iso,
    )

    assert len(records) == 1
    match = records[0]
    assert match.status == "MATCHED"
    # Selected must be the 09:19 publication (110 MW), NOT the 09:21 publication (130 MW)
    assert match.forecastGeneration == 110.0
    assert match.forecastPublishTime == "2026-01-01T09:19:00Z"
    assert match.error == 10.0  # 110 - 100

def test_forecast_selection_no_eligible_forecast():
    delivery_iso = "2026-01-02T12:00:00Z"
    actual_rec = FuelHHRecord(
        startTime=delivery_iso,
        settlementDate="2026-01-02",
        settlementPeriod=25,
        fuelType="WIND",
        generation=125.0,
    )
    # Forecast published after 09:20 UK cutoff
    forecasts = [
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T09:30:00Z", generation=150.0),
    ]

    records, diag = select_forecasts_and_match(
        actual_records=[actual_rec],
        forecast_records=forecasts,
        cutoff_type="d1_0920",
        alignment="exact",
        start_date_iso=delivery_iso,
        end_date_iso=delivery_iso,
    )

    assert len(records) == 1
    match = records[0]
    assert match.status == "MISSING_FORECAST"
    assert match.forecastGeneration is None
    assert match.actualGeneration == 125.0
    assert match.error is None

def test_preserves_december_published_forecast():
    # Delivery on Jan 1 02:00 UTC
    # Cutoff D-1 09:20 is Dec 31 09:20 UTC
    delivery_iso = "2026-01-01T02:00:00Z"
    actual_rec = FuelHHRecord(
        startTime=delivery_iso,
        settlementDate="2026-01-01",
        settlementPeriod=5,
        fuelType="WIND",
        generation=500.0,
    )
    forecasts = [
        WindforRecord(startTime=delivery_iso, publishTime="2025-12-31T08:00:00Z", generation=480.0),
    ]

    records, diag = select_forecasts_and_match(
        actual_records=[actual_rec],
        forecast_records=forecasts,
        cutoff_type="d1_0920",
        alignment="exact",
        start_date_iso=delivery_iso,
        end_date_iso=delivery_iso,
    )

    assert len(records) == 1
    match = records[0]
    assert match.status == "MATCHED"
    assert match.forecastGeneration == 480.0
    assert match.forecastPublishTime == "2025-12-31T08:00:00Z"
    assert match.error == -20.0
