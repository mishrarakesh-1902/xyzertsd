from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from ..models.schemas import CutoffOption, VintageResponse
from ..services.forecast_selection import CUTOFF_OPTIONS
from ..services.data_pipeline import pipeline

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])

@router.get("/cutoffs", response_model=List[CutoffOption])
def list_cutoffs():
    """Returns available forecast-selection cutoffs with industry context and definitions."""
    return CUTOFF_OPTIONS

@router.get("/vintages", response_model=VintageResponse)
def get_vintages(
    delivery_time: str = Query(..., description="Delivery timestamp to inspect, e.g. 2026-01-15T12:00:00Z"),
    cutoff_type: str = Query("d1_1200", description="Cutoff rule id"),
    custom_cutoff: Optional[str] = Query(None, description="Custom cutoff ISO datetime"),
):
    """
    Returns the publication history (all forecast vintages) for a specific delivery interval.
    Enables detailed inspection of forecast evolution across different lead times.
    """
    try:
        return pipeline.get_vintages_for_delivery(
            delivery_iso=delivery_time,
            cutoff_type=cutoff_type,
            custom_cutoff=custom_cutoff,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve vintages: {str(e)}")
