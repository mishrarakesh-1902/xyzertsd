import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.data_pipeline import pipeline
from backend.app.models.schemas import FuelHHRecord, WindforRecord

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_pipeline_data(monkeypatch):
    """Seed pipeline with small controlled test dataset for fast API testing."""
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
        WindforRecord(
            startTime="2026-01-01T00:00:00Z",
            publishTime="2025-12-31T11:00:00Z",
            generation=950.0,
        ),
        WindforRecord(
            startTime="2026-01-01T01:00:00Z",
            publishTime="2025-12-31T11:00:00Z",
            generation=1250.0,
        ),
    ]
    pipeline._cached_fuelhh_clean = sample_actual
    pipeline._cached_windfor_clean = sample_forecast
    pipeline._fuelhh_diag = {"fuel_type_wind": 2}
    pipeline._windfor_diag = {"cleaned_total": 2}
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
    assert any(c["id"] == "d1_1200" for c in data)

def test_analysis_endpoint():
    resp = client.get("/api/analysis?cutoff_type=d1_1200&alignment=exact&start_date=2026-01-01&end_date=2026-01-01")
    assert resp.status_code == 200
    data = resp.json()
    assert "period" in data
    assert "methodology" in data
    assert "metrics" in data
    assert "dataQuality" in data
    assert "records" in data
    assert data["metrics"]["matchedIntervals"] >= 1
    # Check sign convention error = forecast - actual: 950 - 1000 = -50
    rec0 = next(r for r in data["records"] if r["deliveryTime"] == "2026-01-01T00:00:00Z")
    assert rec0["error"] == -50.0
    assert rec0["absError"] == 50.0

def test_vintages_endpoint():
    resp = client.get("/api/forecasts/vintages?delivery_time=2026-01-01T00:00:00Z&cutoff_type=d1_1200")
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
