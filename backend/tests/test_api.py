import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.data_pipeline import pipeline
from backend.app.models.schemas import FuelHHRecord, WindforRecord

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_pipeline_data(monkeypatch):
    """Seed pipeline with small controlled test dataset for fast reproducible API testing."""
    sample_actual = [
        FuelHHRecord(
            startTime="2026-01-01T00:00:00Z",
            publishTime="2026-01-01T00:30:00Z",
            settlementDate="2026-01-01",
            settlementPeriod=1,
            fuelType="WIND",
            generation=1000.0,
        ),
        FuelHHRecord(
            startTime="2026-01-01T01:00:00Z",
            publishTime="2026-01-01T01:30:00Z",
            settlementDate="2026-01-01",
            settlementPeriod=3,
            fuelType="WIND",
            generation=1200.0,
        ),
    ]
    sample_forecast = [
        # Delivery 00:00: published on D-1 at 08:30 UTC (eligible for d1_0920; lead 15.5h)
        WindforRecord(
            startTime="2026-01-01T00:00:00Z",
            publishTime="2025-12-31T08:30:00Z",
            generation=950.0,
        ),
        # Delivery 00:00: published 3 hours prior (lead 3h -> in 0-6h bucket for horizon; excluded from d1_0920)
        WindforRecord(
            startTime="2026-01-01T00:00:00Z",
            publishTime="2025-12-31T21:00:00Z",
            generation=1050.0,
        ),
        # Delivery 01:00: published on D-1 at 08:30 UTC (eligible for d1_0920; lead 16.5h)
        WindforRecord(
            startTime="2026-01-01T01:00:00Z",
            publishTime="2025-12-31T08:30:00Z",
            generation=1250.0,
        ),
    ]
    pipeline._cached_fuelhh_clean = sample_actual
    pipeline._cached_windfor_clean = sample_forecast
    pipeline._fuelhh_diag = {"fuel_type_wind": 2}
    pipeline._windfor_diag = {"cleaned_total": 3}
    pipeline._is_cached = True
    pipeline._cache_ts = "2026-01-01T00:00:00Z"

def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

def test_cutoffs_endpoint():
    resp = client.get("/api/forecasts/cutoffs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # d1_0920 must exist and be default
    default_c = next(c for c in data if c["id"] == "d1_0920")
    assert default_c["isDefault"] is True
    assert "09:20" in default_c["label"]
    # d1_1200 must exist as late sensitivity case
    sens_c = next(c for c in data if c["id"] == "d1_1200")
    assert sens_c["isDefault"] is False

def test_analysis_endpoint_default_cutoff():
    # Calling /api/analysis without cutoff_type parameter must default to d1_0920
    resp = client.get("/api/analysis?alignment=exact&start_date=2026-01-01&end_date=2026-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert data["methodology"]["cutoffType"] == "d1_0920"
    assert "metrics" in data
    assert "p50AbsoluteError" in data["metrics"]
    assert "normalizedMaePct" in data["metrics"]
    assert "dataQuality" in data
    assert "records" in data

def test_analysis_endpoint_with_explicit_cutoff():
    resp = client.get("/api/analysis?cutoff_type=d1_0920&alignment=exact&start_date=2026-01-01&end_date=2026-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "period" in data
    assert "methodology" in data
    assert "metrics" in data
    assert data["metrics"]["matchedIntervals"] >= 1

def test_horizon_endpoint():
    # Test lead-time horizon endpoint /api/analysis/horizon
    # Expected buckets:
    # 0-6h: lead 3h (1050 - 1000 = +50 error) -> n=1, mae=50.0, bias=50.0
    # 12-24h: lead 13h (950 - 1000 = -50) and lead 14h (1250 - 1200 = +50)
    #   -> n=2, mae=(50+50)/2=50.0, bias=(-50+50)/2=0.0
    resp = client.get("/api/analysis/horizon?alignment=exact&start_date=2026-01-01&end_date=2026-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "buckets" in data
    assert "takeaway" in data
    assert len(data["buckets"]) == 6

    b_0_6 = next(b for b in data["buckets"] if b["bucket"] == "0-6h")
    assert b_0_6["n"] == 1
    assert b_0_6["mae"] == 50.0
    assert b_0_6["bias"] == 50.0

    b_12_24 = next(b for b in data["buckets"] if b["bucket"] == "12-24h")
    assert b_12_24["n"] == 2
    assert b_12_24["mae"] == 50.0
    assert b_12_24["bias"] == 0.0

def test_vintages_endpoint():
    resp = client.get("/api/forecasts/vintages?delivery_time=2026-01-01T00:00:00Z&cutoff_type=d1_0920")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deliveryTime"] == "2026-01-01T00:00:00Z"
    assert data["actualGeneration"] == 1000.0
    assert data["totalVintages"] >= 1

def test_data_quality_endpoint():
    resp = client.get("/api/data-quality")
    assert resp.status_code == 200
    data = resp.json()
    assert data["expectedDeliveryIntervals"] == 1488
    assert "resolutionNotice" in data
