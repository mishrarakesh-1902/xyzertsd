from fastapi import APIRouter
from ..models.schemas import DataQualityReport
from ..services.data_pipeline import pipeline

router = APIRouter(tags=["Data Quality"])

@router.get("/data-quality", response_model=DataQualityReport)
def get_data_quality():
    """
    Returns data completeness metrics, raw counts, duplicate checks,
    and methodology transparency disclosures for January 2026.
    """
    # Fetch base analysis to get the quality report
    analysis = pipeline.get_analysis()
    return analysis.dataQuality
