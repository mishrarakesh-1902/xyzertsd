import math
import logging
from typing import List, Optional
from ..models.schemas import MatchedRecord, AnalysisMetrics, ExtremeRecord

logger = logging.getLogger(__name__)

def compute_percentile(sorted_values: List[float], p: float) -> Optional[float]:
    """
    Computes p-th percentile (0 <= p <= 100) using linear interpolation between closest ranks.
    Equivalent to numpy.percentile(..., method='linear').
    """
    if not sorted_values:
        return None
    n = len(sorted_values)
    if n == 1:
        return float(sorted_values[0])
    rank = (p / 100.0) * (n - 1)
    lower_idx = int(math.floor(rank))
    upper_idx = int(math.ceil(rank))
    weight = rank - lower_idx
    val = sorted_values[lower_idx] * (1.0 - weight) + sorted_values[upper_idx] * weight
    return round(float(val), 2)

def calculate_metrics(records: List[MatchedRecord]) -> AnalysisMetrics:
    """
    Computes rigorous forecast error and risk-sizing metrics strictly over valid matched intervals.
    
    Formulas:
      error = forecast - actual (MW)
      MAE   = mean(|forecast - actual|)
      RMSE  = sqrt(mean((forecast - actual)^2))
      Bias  = mean(forecast - actual)
      P50   = 50th percentile of |forecast - actual|
      P90   = 90th percentile of |forecast - actual|
      P95   = 95th percentile of |forecast - actual|
      nMAE  = (MAE / mean(actual)) * 100 (%)
      
    Sign convention:
      Positive error: Overforecast (forecast > actual; thermal under-procured)
      Negative error: Underforecast (forecast < actual; thermal over-procured)
    """
    valid_records: List[MatchedRecord] = []
    valid_errors: List[float] = []
    valid_actuals: List[float] = []
    over_count = 0
    under_count = 0
    exact_count = 0

    for r in records:
        if r.status == "MATCHED" and r.error is not None:
            if not math.isnan(r.error) and not math.isinf(r.error):
                err = float(r.error)
                valid_records.append(r)
                valid_errors.append(err)
                if r.actualGeneration is not None and not math.isnan(r.actualGeneration):
                    valid_actuals.append(float(r.actualGeneration))
                if err > 0.001:
                    over_count += 1
                elif err < -0.001:
                    under_count += 1
                else:
                    exact_count += 1

    n = len(valid_errors)
    total_evaluated = len(records)

    if n == 0:
        return AnalysisMetrics(
            mae=None,
            rmse=None,
            bias=None,
            p50AbsoluteError=None,
            p90AbsoluteError=None,
            p95AbsoluteError=None,
            normalizedMaePct=None,
            meanActualGeneration=None,
            maxOverforecast=None,
            maxUnderforecast=None,
            p95OverforecastError=None,
            p95UnderforecastError=None,
            matchedIntervals=0,
            totalIntervalsEvaluated=total_evaluated,
            overforecastCount=0,
            underforecastCount=0,
            exactMatchCount=0,
        )

    # MAE = mean(|e|)
    abs_errors = [abs(e) for e in valid_errors]
    mae_val = sum(abs_errors) / n

    # RMSE = sqrt(mean(e^2))
    mse_val = sum(e * e for e in valid_errors) / n
    rmse_val = math.sqrt(mse_val)

    # Bias = mean(e)
    bias_val = sum(valid_errors) / n

    # Percentiles of absolute error
    abs_errors_sorted = sorted(abs_errors)
    p50_val = compute_percentile(abs_errors_sorted, 50.0)
    p90_val = compute_percentile(abs_errors_sorted, 90.0)
    p95_val = compute_percentile(abs_errors_sorted, 95.0)

    # Normalised MAE (% of mean actual generation)
    mean_actual = sum(valid_actuals) / len(valid_actuals) if valid_actuals else 0.0
    nmae_val = None
    if mean_actual > 0:
        nmae_val = round((mae_val / mean_actual) * 100.0, 2)

    # Worst single-interval over-forecast and under-forecast
    worst_over_rec = max(valid_records, key=lambda r: r.error if r.error is not None else -float('inf'))
    worst_under_rec = min(valid_records, key=lambda r: r.error if r.error is not None else float('inf'))

    max_over = None
    if worst_over_rec.error is not None and worst_over_rec.error > 0:
        max_over = ExtremeRecord(
            error=round(float(worst_over_rec.error), 2),
            deliveryTime=worst_over_rec.deliveryTime,
            actualGeneration=worst_over_rec.actualGeneration,
            forecastGeneration=worst_over_rec.forecastGeneration,
        )

    max_under = None
    if worst_under_rec.error is not None and worst_under_rec.error < 0:
        max_under = ExtremeRecord(
            error=round(float(worst_under_rec.error), 2),
            deliveryTime=worst_under_rec.deliveryTime,
            actualGeneration=worst_under_rec.actualGeneration,
            forecastGeneration=worst_under_rec.forecastGeneration,
        )

    # Suggestion buffers for procurement decision support
    over_errors_sorted = sorted([e for e in valid_errors if e > 0])
    under_mags_sorted = sorted([abs(e) for e in valid_errors if e < 0])

    p95_over = compute_percentile(over_errors_sorted, 95.0) if over_errors_sorted else None
    p95_under = compute_percentile(under_mags_sorted, 95.0) if under_mags_sorted else None

    return AnalysisMetrics(
        mae=round(mae_val, 2),
        rmse=round(rmse_val, 2),
        bias=round(bias_val, 2),
        p50AbsoluteError=p50_val,
        p90AbsoluteError=p90_val,
        p95AbsoluteError=p95_val,
        normalizedMaePct=nmae_val,
        meanActualGeneration=round(mean_actual, 2) if mean_actual else None,
        maxOverforecast=max_over,
        maxUnderforecast=max_under,
        p95OverforecastError=p95_over,
        p95UnderforecastError=p95_under,
        matchedIntervals=n,
        totalIntervalsEvaluated=total_evaluated,
        overforecastCount=over_count,
        underforecastCount=under_count,
        exactMatchCount=exact_count,
    )
