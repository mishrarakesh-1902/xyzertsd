import pytest
import math
from backend.app.models.schemas import MatchedRecord
from backend.app.services.metrics import calculate_metrics, compute_percentile

def test_compute_percentile_linear():
    # 5 numbers: [10, 20, 30, 40, 50]
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert compute_percentile(data, 0.0) == 10.0
    assert compute_percentile(data, 50.0) == 30.0
    assert compute_percentile(data, 100.0) == 50.0
    # 25th percentile: index = 4 * 0.25 = 1.0 -> 20.0
    assert compute_percentile(data, 25.0) == 20.0
    # 75th percentile: index = 4 * 0.75 = 3.0 -> 40.0
    assert compute_percentile(data, 75.0) == 40.0

def test_metrics_known_values():
    # Known dataset:
    # Pair 1: Actual = 100, Forecast = 110 -> Error = +10, Abs = 10
    # Pair 2: Actual = 200, Forecast = 190 -> Error = -10, Abs = 10
    # Pair 3: Actual = 150, Forecast = 170 -> Error = +20, Abs = 20
    # Pair 4: Actual = 150, Forecast = 150 -> Error = 0, Abs = 0
    # Errors: [10, -10, 20, 0]
    # Abs Errors: [0, 10, 10, 20]
    # MAE = (10 + 10 + 20 + 0) / 4 = 10.0
    # RMSE = sqrt((100 + 100 + 400 + 0) / 4) = sqrt(150) = 12.25
    # Bias = (10 - 10 + 20 + 0) / 4 = 5.0
    # Mean actual = (100 + 200 + 150 + 150) / 4 = 150.0
    # nMAE = (10.0 / 150.0) * 100 = 6.67%
    # P50 of abs errors [0, 10, 10, 20]: median is (10 + 10) / 2 = 10.0
    # Worst overforecast: +20 at 2026-01-01T02:00:00Z
    # Worst underforecast: -10 at 2026-01-01T01:00:00Z
    records = [
        MatchedRecord(
            deliveryTime="2026-01-01T00:00:00Z",
            actualGeneration=100.0,
            forecastGeneration=110.0,
            error=10.0,
            absError=10.0,
            status="MATCHED",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T01:00:00Z",
            actualGeneration=200.0,
            forecastGeneration=190.0,
            error=-10.0,
            absError=10.0,
            status="MATCHED",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T02:00:00Z",
            actualGeneration=150.0,
            forecastGeneration=170.0,
            error=20.0,
            absError=20.0,
            status="MATCHED",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T03:00:00Z",
            actualGeneration=150.0,
            forecastGeneration=150.0,
            error=0.0,
            absError=0.0,
            status="MATCHED",
        ),
    ]

    metrics = calculate_metrics(records)
    assert metrics.matchedIntervals == 4
    assert metrics.mae == 10.0
    assert metrics.rmse == 12.25
    assert metrics.bias == 5.0
    assert metrics.p50AbsoluteError == 10.0
    assert metrics.normalizedMaePct == 6.67
    assert metrics.meanActualGeneration == 150.0
    assert metrics.maxOverforecast is not None
    assert metrics.maxOverforecast.error == 20.0
    assert metrics.maxOverforecast.deliveryTime == "2026-01-01T02:00:00Z"
    assert metrics.maxUnderforecast is not None
    assert metrics.maxUnderforecast.error == -10.0
    assert metrics.maxUnderforecast.deliveryTime == "2026-01-01T01:00:00Z"
    assert metrics.overforecastCount == 2
    assert metrics.underforecastCount == 1
    assert metrics.exactMatchCount == 1

def test_metrics_empty_records():
    metrics = calculate_metrics([])
    assert metrics.matchedIntervals == 0
    assert metrics.mae is None
    assert metrics.rmse is None
    assert metrics.bias is None
    assert metrics.p50AbsoluteError is None
    assert metrics.p90AbsoluteError is None
    assert metrics.p95AbsoluteError is None
    assert metrics.normalizedMaePct is None
    assert metrics.maxOverforecast is None
    assert metrics.maxUnderforecast is None
    assert metrics.totalIntervalsEvaluated == 0

def test_metrics_ignores_unmatched_records():
    records = [
        MatchedRecord(
            deliveryTime="2026-01-01T00:00:00Z",
            actualGeneration=100.0,
            forecastGeneration=110.0,
            error=10.0,
            absError=10.0,
            status="MATCHED",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T01:00:00Z",
            actualGeneration=200.0,
            forecastGeneration=None,
            error=None,
            absError=None,
            status="MISSING_FORECAST",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T02:00:00Z",
            actualGeneration=None,
            forecastGeneration=150.0,
            error=None,
            absError=None,
            status="MISSING_ACTUAL",
        ),
    ]
    metrics = calculate_metrics(records)
    assert metrics.matchedIntervals == 1
    assert metrics.totalIntervalsEvaluated == 3
    assert metrics.mae == 10.0
    assert metrics.rmse == 10.0
    assert metrics.bias == 10.0
    assert metrics.p50AbsoluteError == 10.0

def test_metrics_systematic_underforecast():
    records = [
        MatchedRecord(
            deliveryTime="2026-01-01T00:00:00Z",
            actualGeneration=50.0,
            forecastGeneration=45.0,
            error=-5.0,
            absError=5.0,
            status="MATCHED",
        ),
        MatchedRecord(
            deliveryTime="2026-01-01T01:00:00Z",
            actualGeneration=80.0,
            forecastGeneration=75.0,
            error=-5.0,
            absError=5.0,
            status="MATCHED",
        ),
    ]
    metrics = calculate_metrics(records)
    assert metrics.mae == 5.0
    assert metrics.rmse == 5.0
    assert metrics.bias == -5.0
    assert metrics.underforecastCount == 2
    assert metrics.overforecastCount == 0
    assert metrics.maxOverforecast is None  # No overforecast occurred
    assert metrics.maxUnderforecast is not None
    assert metrics.maxUnderforecast.error == -5.0
