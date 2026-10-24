import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple, Optional
from dateutil import parser as date_parser
from ..models.schemas import FuelHHRecord, WindforRecord

logger = logging.getLogger(__name__)

JAN_2026_START = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
JAN_2026_END = datetime(2026, 1, 31, 23, 30, 0, tzinfo=timezone.utc)
TOTAL_EXPECTED_INTERVALS = 1488 # 31 days * 48 half-hours

def parse_utc_timestamp(ts_str: Any) -> Optional[datetime]:
    """Parse any valid ISO datetime string and normalize to timezone-aware UTC datetime."""
    if not ts_str or not isinstance(ts_str, str):
        return None
    try:
        dt = date_parser.isoparse(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception as e:
        logger.debug(f"Failed to parse timestamp '{ts_str}': {e}")
        return None

def format_iso_utc(dt: datetime) -> str:
    """Format datetime as UTC ISO-8601 string: YYYY-MM-DDTHH:MM:SSZ."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_expected_intervals() -> List[Dict[str, Any]]:
    """Generate the full canonical list of 1,488 half-hour intervals for Jan 2026."""
    intervals = []
    current = JAN_2026_START
    step = timedelta(minutes=30)
    
    while current <= JAN_2026_END:
        # Settlement period calculation: 1 to 48 per day
        # Half-hour index: hour * 2 + (1 if minute == 30 else 0) + 1
        settlement_period = current.hour * 2 + (1 if current.minute >= 30 else 0) + 1
        intervals.append({
            "deliveryTime": format_iso_utc(current),
            "settlementDate": current.strftime("%Y-%m-%d"),
            "settlementPeriod": settlement_period,
            "dt": current,
        })
        current += step
        
    return intervals

def clean_fuelhh_records(raw_records: List[Dict[str, Any]]) -> Tuple[List[FuelHHRecord], Dict[str, Any]]:
    """
    Clean and validate FUELHH records.
    Filters:
      - fuelType == 'WIND'
      - Delivery startTime within Jan 2026
      - Non-null, finite numeric generation
      - Deduplicates records on startTime
    """
    cleaned: Dict[str, FuelHHRecord] = {}
    diagnostics = {
        "raw_total": len(raw_records),
        "fuel_type_wind": 0,
        "invalid_timestamps": 0,
        "out_of_range": 0,
        "invalid_generation": 0,
        "duplicates_resolved": 0,
    }

    for item in raw_records:
        fuel = str(item.get("fuelType", "")).upper()
        if fuel != "WIND":
            continue
        diagnostics["fuel_type_wind"] += 1

        dt = parse_utc_timestamp(item.get("startTime"))
        if not dt:
            diagnostics["invalid_timestamps"] += 1
            continue

        if dt < JAN_2026_START or dt > JAN_2026_END:
            diagnostics["out_of_range"] += 1
            continue

        gen_raw = item.get("generation")
        if gen_raw is None:
            diagnostics["invalid_generation"] += 1
            continue

        try:
            gen = float(gen_raw)
            if math.isnan(gen) or math.isinf(gen):
                diagnostics["invalid_generation"] += 1
                continue
        except (ValueError, TypeError):
            diagnostics["invalid_generation"] += 1
            continue

        iso_time = format_iso_utc(dt)
        pub_raw = item.get("publishTime")
        pub_dt = parse_utc_timestamp(pub_raw)
        pub_iso = format_iso_utc(pub_dt) if pub_dt else None

        settlement_date = item.get("settlementDate") or dt.strftime("%Y-%m-%d")
        settlement_period = item.get("settlementPeriod")
        if settlement_period is None:
            settlement_period = dt.hour * 2 + (1 if dt.minute >= 30 else 0) + 1

        record = FuelHHRecord(
            startTime=iso_time,
            publishTime=pub_iso,
            settlementDate=str(settlement_date),
            settlementPeriod=int(settlement_period),
            fuelType="WIND",
            generation=gen,
        )

        if iso_time in cleaned:
            diagnostics["duplicates_resolved"] += 1
            # Keep the record with the latest publishTime if available
            existing = cleaned[iso_time]
            if pub_iso and existing.publishTime and pub_iso > existing.publishTime:
                cleaned[iso_time] = record
        else:
            cleaned[iso_time] = record

    sorted_records = sorted(cleaned.values(), key=lambda r: r.startTime)
    diagnostics["cleaned_total"] = len(sorted_records)
    return sorted_records, diagnostics

def clean_windfor_records(raw_records: List[Dict[str, Any]]) -> Tuple[List[WindforRecord], Dict[str, Any]]:
    """
    Clean and validate WINDFOR forecast records.
    Filters:
      - Delivery startTime within Jan 2026 (Preserves Dec 2025 publish times!)
      - Non-null, finite numeric generation
      - Deduplicates on (startTime, publishTime)
    """
    cleaned: Dict[Tuple[str, str], WindforRecord] = {}
    diagnostics = {
        "raw_total": len(raw_records),
        "invalid_timestamps": 0,
        "out_of_range_start": 0,
        "invalid_generation": 0,
        "duplicates_removed": 0,
    }

    for item in raw_records:
        start_dt = parse_utc_timestamp(item.get("startTime"))
        pub_dt = parse_utc_timestamp(item.get("publishTime"))

        if not start_dt or not pub_dt:
            diagnostics["invalid_timestamps"] += 1
            continue

        # Filter strictly for Jan 2026 delivery period
        if start_dt < JAN_2026_START or start_dt > JAN_2026_END:
            diagnostics["out_of_range_start"] += 1
            continue

        gen_raw = item.get("generation")
        if gen_raw is None:
            diagnostics["invalid_generation"] += 1
            continue

        try:
            gen = float(gen_raw)
            if math.isnan(gen) or math.isinf(gen):
                diagnostics["invalid_generation"] += 1
                continue
        except (ValueError, TypeError):
            diagnostics["invalid_generation"] += 1
            continue

        start_iso = format_iso_utc(start_dt)
        pub_iso = format_iso_utc(pub_dt)

        key = (start_iso, pub_iso)
        if key in cleaned:
            diagnostics["duplicates_removed"] += 1
        else:
            cleaned[key] = WindforRecord(
                startTime=start_iso,
                publishTime=pub_iso,
                generation=gen,
            )

    sorted_records = sorted(cleaned.values(), key=lambda r: (r.startTime, r.publishTime))
    diagnostics["cleaned_total"] = len(sorted_records)
    return sorted_records, diagnostics
