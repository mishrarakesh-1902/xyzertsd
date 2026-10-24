import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from ..models.schemas import (
    FuelHHRecord,
    WindforRecord,
    MatchedRecord,
    CutoffOption,
    VintageItem,
    VintageResponse,
)
from .data_cleaning import parse_utc_timestamp, format_iso_utc, generate_expected_intervals

logger = logging.getLogger(__name__)

CUTOFF_OPTIONS: List[CutoffOption] = [
    CutoffOption(
        id="d1_1200",
        label="Day-Ahead 12:00 UTC (D-1 12:00)",
        description="Forecasts published by 12:00 UTC on the day before delivery. Standard UK Day-Ahead wholesale market auction benchmark (EPEX/NordPool).",
        isDefault=True,
        group="Day-Ahead Auction Cutoffs",
    ),
    CutoffOption(
        id="d1_1700",
        label="Day-Ahead 17:00 UTC (D-1 17:00)",
        description="Forecasts published by 17:00 UTC on the day before delivery (Post-auction / Evening Schedule).",
        isDefault=False,
        group="Day-Ahead Auction Cutoffs",
    ),
    CutoffOption(
        id="d1_0900",
        label="Day-Ahead 09:00 UTC (D-1 09:00)",
        description="Forecasts published by 09:00 UTC on the day before delivery (Pre-auction morning briefing).",
        isDefault=False,
        group="Day-Ahead Auction Cutoffs",
    ),
    CutoffOption(
        id="lead_24h",
        label="24 Hours Ahead (Rolling D-24h)",
        description="Forecast published at least 24 hours prior to each delivery interval.",
        isDefault=False,
        group="Rolling Lead-Time Cutoffs",
    ),
    CutoffOption(
        id="lead_12h",
        label="12 Hours Ahead (Rolling D-12h)",
        description="Forecast published at least 12 hours prior to each delivery interval.",
        isDefault=False,
        group="Rolling Lead-Time Cutoffs",
    ),
    CutoffOption(
        id="lead_48h",
        label="48 Hours Ahead (Rolling D-48h)",
        description="Forecast published at least 48 hours prior to each delivery interval (Medium-range outlook).",
        isDefault=False,
        group="Rolling Lead-Time Cutoffs",
    ),
    CutoffOption(
        id="latest",
        label="Gate Closure / 0h Lead Time",
        description="Latest forecast published on or before the start of the delivery interval.",
        isDefault=False,
        group="Intraday / Gate Closure",
    ),
]

def calculate_cutoff_datetime(
    delivery_dt: datetime,
    cutoff_type: str = "d1_1200",
    custom_cutoff_iso: Optional[str] = None,
) -> Optional[datetime]:
    """
    Computes the decision cutoff datetime for a specific delivery timestamp.
    Prevents look-ahead bias by strictly defining the historical eligibility boundary.
    """
    if custom_cutoff_iso:
        parsed = parse_utc_timestamp(custom_cutoff_iso)
        if parsed:
            return parsed

    if cutoff_type == "d1_1200":
        # Day before delivery at 12:00:00 UTC
        prev_day = delivery_dt.date() - timedelta(days=1)
        return datetime(prev_day.year, prev_day.month, prev_day.day, 12, 0, 0, tzinfo=timezone.utc)

    elif cutoff_type == "d1_1700":
        prev_day = delivery_dt.date() - timedelta(days=1)
        return datetime(prev_day.year, prev_day.month, prev_day.day, 17, 0, 0, tzinfo=timezone.utc)

    elif cutoff_type == "d1_0900":
        prev_day = delivery_dt.date() - timedelta(days=1)
        return datetime(prev_day.year, prev_day.month, prev_day.day, 9, 0, 0, tzinfo=timezone.utc)

    elif cutoff_type == "lead_24h":
        return delivery_dt - timedelta(hours=24)

    elif cutoff_type == "lead_12h":
        return delivery_dt - timedelta(hours=12)

    elif cutoff_type == "lead_48h":
        return delivery_dt - timedelta(hours=48)

    elif cutoff_type == "latest":
        return delivery_dt

    else:
        # Default fallback to D-1 12:00
        prev_day = delivery_dt.date() - timedelta(days=1)
        return datetime(prev_day.year, prev_day.month, prev_day.day, 12, 0, 0, tzinfo=timezone.utc)

def select_forecasts_and_match(
    actual_records: List[FuelHHRecord],
    forecast_records: List[WindforRecord],
    cutoff_type: str = "d1_1200",
    custom_cutoff_iso: Optional[str] = None,
    alignment: str = "exact",
    start_date_iso: Optional[str] = None,
    end_date_iso: Optional[str] = None,
) -> Tuple[List[MatchedRecord], Dict[str, Any]]:
    """
    Executes forecast selection and matches actual generation records against selected forecasts.
    
    Selection Rule:
      For each delivery interval T:
        1. Find all forecasts associated with delivery interval T (or hour block T in hourly_block mode).
        2. Filter to forecasts where publishTime <= cutoff(T).
        3. Exclude all forecasts published after cutoff(T) (No look-ahead bias).
        4. Select the eligible record with max(publishTime).
        5. Calculate error = forecast - actual (MW).
    """
    # Build lookup for actual records by delivery startTime
    actual_by_time: Dict[str, FuelHHRecord] = {r.startTime: r for r in actual_records}

    # Group forecast records by forecast startTime
    forecasts_by_target: Dict[str, List[WindforRecord]] = defaultdict(list)
    for f in forecast_records:
        forecasts_by_target[f.startTime].append(f)

    # Date filtering
    filter_start = parse_utc_timestamp(start_date_iso) if start_date_iso else None
    filter_end = parse_utc_timestamp(end_date_iso) if end_date_iso else None

    # Canonical Jan 2026 delivery intervals (1,488)
    expected_intervals = generate_expected_intervals()

    matched_records: List[MatchedRecord] = []
    diagnostics = {
        "cutoff_type": cutoff_type,
        "alignment": alignment,
        "total_intervals_in_range": 0,
        "matched_count": 0,
        "missing_forecast_count": 0,
        "missing_actual_count": 0,
        "both_missing_count": 0,
    }

    for interval in expected_intervals:
        delivery_dt: datetime = interval["dt"]
        delivery_iso: str = interval["deliveryTime"]

        # Date range filter check
        if filter_start and delivery_dt < filter_start:
            continue
        if filter_end and delivery_dt > filter_end:
            continue

        # In exact alignment mode, WINDFOR only has hourly records (:00).
        # If user selected exact alignment, we only evaluate on the hour intervals (:00).
        # If user selected hourly_block, both :00 and :30 intervals are evaluated.
        is_half_hour = delivery_dt.minute >= 30
        if alignment == "exact" and is_half_hour:
            continue

        diagnostics["total_intervals_in_range"] += 1

        actual_rec = actual_by_time.get(delivery_iso)

        # Determine target forecast key for this delivery interval
        if alignment == "hourly_block" and is_half_hour:
            # Map :30 back to :00 hour start
            hour_start_dt = delivery_dt.replace(minute=0, second=0)
            forecast_target_key = format_iso_utc(hour_start_dt)
        else:
            forecast_target_key = delivery_iso

        available_vintages = forecasts_by_target.get(forecast_target_key, [])

        cutoff_dt = calculate_cutoff_datetime(delivery_dt, cutoff_type, custom_cutoff_iso)

        # Filter strictly by publishTime <= cutoff_dt
        eligible_forecasts = []
        for f in available_vintages:
            pub_dt = parse_utc_timestamp(f.publishTime)
            if pub_dt and cutoff_dt and pub_dt <= cutoff_dt:
                eligible_forecasts.append(f)

        # Select latest eligible forecast
        selected_forecast: Optional[WindforRecord] = None
        if eligible_forecasts:
            selected_forecast = max(eligible_forecasts, key=lambda f: f.publishTime)

        # Record matching and error calculation
        actual_val = actual_rec.generation if actual_rec else None
        forecast_val = selected_forecast.generation if selected_forecast else None
        forecast_pub = selected_forecast.publishTime if selected_forecast else None

        lead_hours = None
        if selected_forecast:
            pub_dt = parse_utc_timestamp(selected_forecast.publishTime)
            if pub_dt:
                lead_hours = round((delivery_dt - pub_dt).total_seconds() / 3600.0, 2)

        error_val = None
        abs_error_val = None

        if actual_val is not None and forecast_val is not None:
            # error = forecast - actual
            error_val = round(forecast_val - actual_val, 2)
            abs_error_val = round(abs(forecast_val - actual_val), 2)
            status = "MATCHED"
            diagnostics["matched_count"] += 1
        elif actual_val is None and forecast_val is not None:
            status = "MISSING_ACTUAL"
            diagnostics["missing_actual_count"] += 1
        elif actual_val is not None and forecast_val is None:
            status = "MISSING_FORECAST"
            diagnostics["missing_forecast_count"] += 1
        else:
            status = "MISSING_BOTH"
            diagnostics["both_missing_count"] += 1

        matched_records.append(
            MatchedRecord(
                deliveryTime=delivery_iso,
                settlementPeriod=interval["settlementPeriod"],
                actualGeneration=actual_val,
                forecastGeneration=forecast_val,
                forecastPublishTime=forecast_pub,
                leadHours=lead_hours,
                error=error_val,
                absError=abs_error_val,
                status=status,
            )
        )

    return matched_records, diagnostics

def get_delivery_vintages(
    delivery_iso: str,
    actual_records: List[FuelHHRecord],
    forecast_records: List[WindforRecord],
    cutoff_type: str = "d1_1200",
    custom_cutoff_iso: Optional[str] = None,
) -> VintageResponse:
    """Returns all forecast publications (vintages) for a specific delivery interval."""
    delivery_dt = parse_utc_timestamp(delivery_iso)
    if not delivery_dt:
        raise ValueError(f"Invalid delivery timestamp: {delivery_iso}")

    actual_by_time = {r.startTime: r for r in actual_records}
    actual_rec = actual_by_time.get(delivery_iso)
    actual_val = actual_rec.generation if actual_rec else None

    # Handle hourly key if needed
    hour_key = delivery_iso
    if delivery_dt.minute >= 30:
        hour_start_dt = delivery_dt.replace(minute=0, second=0)
        hour_key = format_iso_utc(hour_start_dt)

    matching_forecasts = [f for f in forecast_records if f.startTime in (delivery_iso, hour_key)]
    # Deduplicate by publishTime
    unique_by_pub = {f.publishTime: f for f in matching_forecasts}
    vintages_sorted = sorted(unique_by_pub.values(), key=lambda f: f.publishTime)

    cutoff_dt = calculate_cutoff_datetime(delivery_dt, cutoff_type, custom_cutoff_iso)

    items: List[VintageItem] = []
    eligible_items: List[WindforRecord] = []
    for f in vintages_sorted:
        pub_dt = parse_utc_timestamp(f.publishTime)
        is_eligible = bool(pub_dt and cutoff_dt and pub_dt <= cutoff_dt)
        if is_eligible:
            eligible_items.append(f)
        lead_h = round((delivery_dt - pub_dt).total_seconds() / 3600.0, 2) if pub_dt else 0.0
        items.append(
            VintageItem(
                publishTime=f.publishTime,
                generation=f.generation,
                leadHours=lead_h,
                isEligible=is_eligible,
            )
        )

    selected = max(eligible_items, key=lambda f: f.publishTime) if eligible_items else None

    return VintageResponse(
        deliveryTime=delivery_iso,
        actualGeneration=actual_val,
        selectedForecast=selected,
        cutoffApplied=cutoff_type,
        totalVintages=len(items),
        vintages=items,
    )
