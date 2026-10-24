import logging
from typing import Optional, Dict, Any, Tuple
from ..models.schemas import (
    AnalysisResponse,
    MethodologyInfo,
    DataQualityReport,
    CutoffOption,
)
from .data_cache import data_cache_service
from .data_cleaning import (
    clean_fuelhh_records,
    clean_windfor_records,
    TOTAL_EXPECTED_INTERVALS,
)
from .forecast_selection import (
    select_forecasts_and_match,
    CUTOFF_OPTIONS,
    get_delivery_vintages,
    VintageResponse,
)
from .metrics import calculate_metrics

logger = logging.getLogger(__name__)

class DataPipeline:
    """End-to-end data pipeline orchestrating ingestion, cleaning, selection, and metrics."""

    def __init__(self):
        self._cached_fuelhh_clean = None
        self._cached_windfor_clean = None
        self._fuelhh_diag = None
        self._windfor_diag = None
        self._is_cached = False
        self._cache_ts = None

    def initialize_data(self, force_refresh: bool = False):
        """Loads or fetches raw records, runs cleaning pipeline, and caches in memory."""
        logger.info(f"Initializing data pipeline (force_refresh={force_refresh})...")
        raw_fuelhh, f_cached, f_ts = data_cache_service.load_or_fetch_fuelhh(force_refresh=force_refresh)
        raw_windfor, w_cached, w_ts = data_cache_service.load_or_fetch_windfor(force_refresh=force_refresh)

        clean_f, diag_f = clean_fuelhh_records(raw_fuelhh)
        clean_w, diag_w = clean_windfor_records(raw_windfor)

        self._cached_fuelhh_clean = clean_f
        self._cached_windfor_clean = clean_w
        self._fuelhh_diag = diag_f
        self._windfor_diag = diag_w
        self._is_cached = f_cached and w_cached
        self._cache_ts = f_ts or w_ts

        logger.info(
            f"Pipeline initialized: {len(clean_f)} actual records, {len(clean_w)} forecast records."
        )

    def get_analysis(
        self,
        cutoff_type: str = "d1_1200",
        custom_cutoff: Optional[str] = None,
        alignment: str = "exact",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AnalysisResponse:
        """Executes full analysis query with the specified cutoff and alignment settings."""
        if self._cached_fuelhh_clean is None or self._cached_windfor_clean is None:
            self.initialize_data()

        matched_records, diag = select_forecasts_and_match(
            actual_records=self._cached_fuelhh_clean,
            forecast_records=self._cached_windfor_clean,
            cutoff_type=cutoff_type,
            custom_cutoff_iso=custom_cutoff,
            alignment=alignment,
            start_date_iso=start_date,
            end_date_iso=end_date,
        )

        metrics = calculate_metrics(matched_records)

        # Lookup cutoff info
        cutoff_info = next((c for c in CUTOFF_OPTIONS if c.id == cutoff_type), None)
        cutoff_desc = cutoff_info.description if cutoff_info else f"Custom cutoff: {custom_cutoff}"

        methodology = MethodologyInfo(
            selectionRule="latest_eligible_forecast_by_cutoff",
            cutoffType=cutoff_type,
            cutoffDescription=cutoff_desc,
            alignment=alignment,
            unit="MW",
            signConvention="error = forecast - actual (Positive: Overforecast, Negative: Underforecast)",
        )

        # Unique forecast delivery timestamps
        unique_forecast_deliveries = len(set(f.startTime for f in self._cached_windfor_clean))
        actual_count = len(self._cached_fuelhh_clean)
        
        # Quality calculation
        expected_eval = diag["total_intervals_in_range"]
        matched_count = diag["matched_count"]
        missing_forecast_count = diag["missing_forecast_count"]
        missing_actual_count = diag["missing_actual_count"]

        actual_comp = round((1.0 - (missing_actual_count / expected_eval)) * 100.0, 1) if expected_eval > 0 else 0.0
        forecast_comp = round((1.0 - (missing_forecast_count / expected_eval)) * 100.0, 1) if expected_eval > 0 else 0.0
        matched_comp = round((matched_count / expected_eval) * 100.0, 1) if expected_eval > 0 else 0.0

        warnings = []
        if missing_forecast_count > 0:
            warnings.append(
                f"{missing_forecast_count} interval(s) had no eligible forecast published prior to the selected cutoff ({cutoff_type})."
            )
        if missing_actual_count > 0:
            warnings.append(f"{missing_actual_count} interval(s) are missing actual outturn records in FUELHH.")

        res_notice = (
            "Elexon BMRS FUELHH provides 30-minute outturn data (1,488 intervals for Jan 2026). "
            "WINDFOR provides 60-minute forecast snapshots (744 unique intervals). "
            f"Current view is using '{alignment}' alignment."
        )

        data_quality = DataQualityReport(
            analysisPeriod={
                "start": start_date or "2026-01-01T00:00:00Z",
                "end": end_date or "2026-01-31T23:30:00Z",
            },
            expectedDeliveryIntervals=TOTAL_EXPECTED_INTERVALS,
            actualRecordsRetrieved=actual_count,
            rawForecastRecordsRetrieved=len(self._cached_windfor_clean),
            uniqueForecastDeliveryIntervals=unique_forecast_deliveries,
            matchedIntervals=matched_count,
            missingActualIntervals=missing_actual_count,
            missingForecastIntervals=missing_forecast_count,
            actualCompletenessPct=actual_comp,
            forecastCompletenessPct=forecast_comp,
            matchedCompletenessPct=matched_comp,
            resolutionNotice=res_notice,
            warnings=warnings,
            cached=self._is_cached,
            cacheTimestamp=self._cache_ts,
        )

        return AnalysisResponse(
            period={
                "start": start_date or "2026-01-01T00:00:00Z",
                "end": end_date or "2026-01-31T23:30:00Z",
            },
            methodology=methodology,
            metrics=metrics,
            dataQuality=data_quality,
            records=matched_records,
        )

    def get_vintages_for_delivery(
        self,
        delivery_iso: str,
        cutoff_type: str = "d1_1200",
        custom_cutoff: Optional[str] = None,
    ) -> VintageResponse:
        """Returns all published vintages for an individual delivery timestamp."""
        if self._cached_fuelhh_clean is None or self._cached_windfor_clean is None:
            self.initialize_data()

        return get_delivery_vintages(
            delivery_iso=delivery_iso,
            actual_records=self._cached_fuelhh_clean,
            forecast_records=self._cached_windfor_clean,
            cutoff_type=cutoff_type,
            custom_cutoff_iso=custom_cutoff,
        )

pipeline = DataPipeline()
