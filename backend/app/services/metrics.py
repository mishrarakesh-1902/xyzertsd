import math
import logging
from typing import List, Optional
from ..models.schemas import MatchedRecord, AnalysisMetrics

logger = logging.getLogger(__name__)

def calculate_metrics(records: List[MatchedRecord]) -> AnalysisMetrics:
    """
    Computes rigorous forecast error metrics strictly over valid matched intervals.
    
    Formulas:
      error = forecast - actual (MW)
      MAE   = mean(|forecast - actual|)
      RMSE  = sqrt(mean((forecast - actual)^2))
      Bias  = mean(forecast - actual)
      
    Sign convention:
      Positive bias: Systematic overforecast (forecast > actual)
      Negative bias: Systematic underforecast (forecast < actual)
    """
    # Filter strictly for valid matched pairs with non-null, finite numerical errors
    valid_errors: List[float] = []
    over_count = 0
    under_count = 0
    exact_count = 0

    for r in records:
        if r.status == "MATCHED" and r.error is not None:
            if not math.isnan(r.error) and not math.isinf(r.error):
                err = float(r.error)
                valid_errors.append(err)
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
            matchedIntervals=0,
            totalIntervalsEvaluated=total_evaluated,
            overforecastCount=0,
            underforecastCount=0,
            exactMatchCount=0,
        )

    # MAE = mean(|e|)
    mae_val = sum(abs(e) for e in valid_errors) / n

    # RMSE = sqrt(mean(e^2))
    mse_val = sum(e * e for e in valid_errors) / n
    rmse_val = math.sqrt(mse_val)

    # Bias = mean(e)
    bias_val = sum(valid_errors) / n

    return AnalysisMetrics(
        mae=round(mae_val, 2),
        rmse=round(rmse_val, 2),
        bias=round(bias_val, 2),
        matchedIntervals=n,
        totalIntervalsEvaluated=total_evaluated,
        overforecastCount=over_count,
        underforecastCount=under_count,
        exactMatchCount=exact_count,
    )
