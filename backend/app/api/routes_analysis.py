import logging
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from ..models.schemas import AnalysisResponse
from ..services.data_pipeline import pipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Analysis"])

@router.get("/analysis", response_model=AnalysisResponse)
def get_analysis(
    cutoff_type: str = Query("d1_1200", description="Cutoff rule id (e.g. d1_1200, lead_24h, latest)"),
    custom_cutoff: Optional[str] = Query(None, description="Custom cutoff ISO datetime if cutoff_type=custom"),
    alignment: str = Query("exact", pattern="^(exact|hourly_block)$", description="Alignment resolution: exact or hourly_block"),
    start_date: Optional[str] = Query(None, description="Filter start timestamp or date (YYYY-MM-DD or ISO)"),
    end_date: Optional[str] = Query(None, description="Filter end timestamp or date (YYYY-MM-DD or ISO)"),
):
    """
    Returns complete January 2026 forecast vs. actual analysis.
    Computes MAE, RMSE, forecast bias, and aligned time series using the chosen cutoff.
    """
    try:
        # Normalize date strings if passed as YYYY-MM-DD
        start_iso = start_date
        if start_date and len(start_date) == 10:
            start_iso = f"{start_date}T00:00:00Z"

        end_iso = end_date
        if end_date and len(end_date) == 10:
            end_iso = f"{end_date}T23:59:59Z"

        result = pipeline.get_analysis(
            cutoff_type=cutoff_type,
            custom_cutoff=custom_cutoff,
            alignment=alignment,
            start_date=start_iso,
            end_date=end_iso,
        )
        return result
    except Exception as e:
        logger.exception("Error executing analysis query")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

@router.post("/analysis/refresh")
def refresh_data():
    """Forces refetch from official Elexon BMRS API and updates the local cache."""
    try:
        pipeline.initialize_data(force_refresh=True)
        return {"status": "success", "message": "Successfully refreshed Elexon datasets from upstream API."}
    except Exception as e:
        logger.exception("Failed to refresh datasets")
        raise HTTPException(status_code=502, detail=f"Upstream Elexon refresh failed: {str(e)}")
