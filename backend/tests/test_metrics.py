import pytest
import math
from backend.app.models.schemas import MatchedRecord
from backend.app.services.metrics import calculate_metrics

def test_metrics_known_values():
    # Known dataset:
    # Pair 1: Actual = 100, Forecast = 110 -> Error = +10
    # Pair 2: Actual = 200, Forecast = 190 -> Error = -10
    # Pair 3: Actual = 150, Forecast = 170 -> Error = +20
    # Pair 4: Actual = 120, Forecast = 120 -> Error = 0
    # Errors: [10, -10, 20, 0]
    # Abs Errors: [10, 10, 20, 0] -> Sum = 40, Mean = 10.0 (MAE)
    # Squared Errors: [100, 100, 400, 0] -> Sum = 600, Mean = 150 -> Sqrt(150) = 12.247... -> 12.25 (RMSE)
    # Sum of Errors: 10 - 10 + 20 + 0 = 20 -> Mean = 5.0 (Bias)
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
            actualGeneration=120.0,
            forecastGeneration=120.0,
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
    assert metrics.overforecastCount == 2
    assert metrics.underforecastCount == 1
    assert metrics.exactMatchCount == 1

def test_metrics_empty_records():
    metrics = calculate_metrics([])
    assert metrics.matchedIntervals == 0
    assert metrics.mae is None
    assert metrics.rmse is None
    assert metrics.bias is None
    assert metrics.totalIntervalsEvaluated == 0

def test_metrics_ignores_unmatched_records():
    # Only records with status="MATCHED" and non-null error should be included
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

def test_metrics_systematic_underforecast():
    # Every forecast underestimates by 5 MW
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
