import pytest
from datetime import datetime, timezone
from backend.app.models.schemas import FuelHHRecord, WindforRecord
from backend.app.services.forecast_selection import (
    calculate_cutoff_datetime,
    select_forecasts_and_match,
)

def test_cutoff_calculation_d1_1200():
    # Delivery on Jan 15 14:00 UTC -> Cutoff is Jan 14 12:00:00 UTC
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

def test_forecast_selection_latest_eligible_and_excludes_after_cutoff():
    # Delivery interval: 2026-01-02T12:00:00Z
    # D-1 12:00 cutoff: 2026-01-01T12:00:00Z
    # Forecast A: published 2026-01-01T06:00:00Z, gen=100 (Eligible)
    # Forecast B: published 2026-01-01T11:30:00Z, gen=120 (Eligible, latest eligible!)
    # Forecast C: published 2026-01-01T14:00:00Z, gen=150 (After cutoff -> Excluded)
    # Forecast D: published 2026-01-02T08:00:00Z, gen=180 (After cutoff -> Excluded)
    delivery_iso = "2026-01-02T12:00:00Z"
    actual_rec = FuelHHRecord(
        startTime=delivery_iso,
        settlementDate="2026-01-02",
        settlementPeriod=25,
        fuelType="WIND",
        generation=125.0,
    )
    forecasts = [
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T06:00:00Z", generation=100.0),
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T11:30:00Z", generation=120.0),
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T14:00:00Z", generation=150.0),
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-02T08:00:00Z", generation=180.0),
    ]

    records, diag = select_forecasts_and_match(
        actual_records=[actual_rec],
        forecast_records=forecasts,
        cutoff_type="d1_1200",
        alignment="exact",
        start_date_iso=delivery_iso,
        end_date_iso=delivery_iso,
    )

    assert len(records) == 1
    match = records[0]
    assert match.deliveryTime == delivery_iso
    assert match.status == "MATCHED"
    # Must pick Forecast B (120 MW, published at 11:30 UTC), NOT C or D
    assert match.forecastGeneration == 120.0
    assert match.forecastPublishTime == "2026-01-01T11:30:00Z"
    assert match.actualGeneration == 125.0
    assert match.error == -5.0  # 120 - 125
    assert match.absError == 5.0

def test_forecast_selection_no_eligible_forecast():
    # All forecasts were published AFTER cutoff
    delivery_iso = "2026-01-02T12:00:00Z"
    actual_rec = FuelHHRecord(
        startTime=delivery_iso,
        settlementDate="2026-01-02",
        settlementPeriod=25,
        fuelType="WIND",
        generation=125.0,
    )
    forecasts = [
        WindforRecord(startTime=delivery_iso, publishTime="2026-01-01T15:00:00Z", generation=150.0),
    ]

    records, diag = select_forecasts_and_match(
        actual_records=[actual_rec],
        forecast_records=forecasts,
        cutoff_type="d1_1200",
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
    # Cutoff D-1 12:00 is Dec 31 12:00 UTC
    # Forecast published Dec 31 08:00 UTC must be selected!
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
        cutoff_type="d1_1200",
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
