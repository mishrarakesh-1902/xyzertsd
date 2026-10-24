import math
import logging
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone, timedelta
from ..models.schemas import (
    AnalysisResponse,
    MethodologyInfo,
    DataQualityReport,
    CutoffOption,
    HorizonBucketResult,
    HorizonAnalysisResponse,
)
from .data_cache import data_cache_service
from .data_cleaning import (
    clean_fuelhh_records,
    clean_windfor_records,
    parse_utc_timestamp,
    format_iso_utc,
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

HORIZON_BUCKET_DEFS = [
    {"bucket": "0-6h", "label": "0-6h Ahead", "min": 0.0, "max": 6.0},
    {"bucket": "6-12h", "label": "6-12h Ahead", "min": 6.0, "max": 12.0},
    {"bucket": "12-24h", "label": "12-24h Ahead", "min": 12.0, "max": 24.0},
    {"bucket": "24-36h", "label": "24-36h Ahead", "min": 24.0, "max": 36.0},
    {"bucket": "36-48h", "label": "36-48h Ahead", "min": 36.0, "max": 48.0},
    {"bucket": "48h+", "label": "48h+ Ahead", "min": 48.0, "max": None},
]

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
        cutoff_type: str = "d1_0920",
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

        unique_forecast_deliveries = len(set(f.startTime for f in self._cached_windfor_clean))
        actual_count = len(self._cached_fuelhh_clean)
        
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

    def get_horizon_analysis(
        self,
        alignment: str = "exact",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> HorizonAnalysisResponse:
        """
        Computes forecast error metrics across all publication lead times (horizons)
        using ALL forecast vintages (not just the selected snapshot).
        Buckets: 0-6h, 6-12h, 12-24h, 24-36h, 36-48h, 48h+.
        """
        if self._cached_fuelhh_clean is None or self._cached_windfor_clean is None:
            self.initialize_data()

        actual_by_time = {r.startTime: r for r in self._cached_fuelhh_clean}
        filter_start = parse_utc_timestamp(start_date) if start_date else None
        filter_end = parse_utc_timestamp(end_date) if end_date else None

        # Prepare bucket error collectors
        bucket_errors: Dict[str, List[float]] = {b["bucket"]: [] for b in HORIZON_BUCKET_DEFS}

        for f in self._cached_windfor_clean:
            delivery_dt = parse_utc_timestamp(f.startTime)
            pub_dt = parse_utc_timestamp(f.publishTime)
            if not delivery_dt or not pub_dt:
                continue

            # Target delivery evaluation
            targets = []
            if alignment == "exact":
                targets.append((delivery_dt, f.startTime))
            elif alignment == "hourly_block":
                targets.append((delivery_dt, f.startTime))
                # Add the :30 interval of the same hour
                half_hour_dt = delivery_dt + timedelta(minutes=30)
                targets.append((half_hour_dt, format_iso_utc(half_hour_dt)))

            for tgt_dt, tgt_iso in targets:
                if filter_start and tgt_dt < filter_start:
                    continue
                if filter_end and tgt_dt > filter_end:
                    continue

                actual_rec = actual_by_time.get(tgt_iso)
                if not actual_rec or actual_rec.generation is None:
                    continue

                lead_hours = (tgt_dt - pub_dt).total_seconds() / 3600.0
                if lead_hours < 0:
                    continue

                err = float(f.generation - actual_rec.generation)

                # Determine bucket
                for b in HORIZON_BUCKET_DEFS:
                    min_h = b["min"]
                    max_h = b["max"]
                    if max_h is not None:
                        if min_h <= lead_hours < max_h:
                            bucket_errors[b["bucket"]].append(err)
                            break
                    else:
                        if lead_hours >= min_h:
                            bucket_errors[b["bucket"]].append(err)
                            break

        bucket_results: List[HorizonBucketResult] = []
        for b in HORIZON_BUCKET_DEFS:
            errs = bucket_errors[b["bucket"]]
            n = len(errs)
            if n > 0:
                mae_val = round(sum(abs(e) for e in errs) / n, 2)
                rmse_val = round(math.sqrt(sum(e * e for e in errs) / n), 2)
                bias_val = round(sum(errs) / n, 2)
            else:
                mae_val = None
                rmse_val = None
                bias_val = None

            bucket_results.append(
                HorizonBucketResult(
                    bucket=b["bucket"],
                    label=b["label"],
                    minLeadHours=b["min"],
                    maxLeadHours=b["max"],
                    mae=mae_val,
                    rmse=rmse_val,
                    bias=bias_val,
                    n=n,
                )
            )

        # Generate automated plain-English takeaway
        valid_buckets = [b for b in bucket_results if b.n > 0 and b.mae is not None]
        if valid_buckets:
            best_bucket = min(valid_buckets, key=lambda b: b.mae)
            worst_bucket = max(valid_buckets, key=lambda b: b.mae)
            takeaway = (
                f"Forecast error increases with lead time: the {best_bucket.label} horizon achieved the lowest MAE "
                f"({best_bucket.mae:,.2f} MW across {best_bucket.n:,} vintage pairs), while the {worst_bucket.label} horizon "
                f"had the highest uncertainty ({worst_bucket.mae:,.2f} MW MAE)."
            )
        else:
            takeaway = "Insufficient matched forecast vintages to assess lead-time horizon error."

        return HorizonAnalysisResponse(
            period={
                "start": start_date or "2026-01-01T00:00:00Z",
                "end": end_date or "2026-01-31T23:30:00Z",
            },
            alignment=alignment,
            buckets=bucket_results,
            takeaway=takeaway,
        )

    def get_vintages_for_delivery(
        self,
        delivery_iso: str,
        cutoff_type: str = "d1_0920",
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
