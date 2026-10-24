import logging
import time
from typing import List, Dict, Any, Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

class ElexonClient:
    """Official Elexon BMRS API client for FUELHH and WINDFOR streams."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ELEXON_API_BASE_URL).rstrip("/")
        self.timeout = httpx.Timeout(45.0, connect=10.0)

    def fetch_fuelhh_stream(
        self,
        settlement_date_from: str = "2026-01-01",
        settlement_date_to: str = "2026-01-31",
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Fetch FUELHH (Half-hourly generation outturn by fuel type) stream.
        Endpoint: /datasets/FUELHH/stream?settlementDateFrom=YYYY-MM-DD&settlementDateTo=YYYY-MM-DD
        """
        url = f"{self.base_url}/datasets/FUELHH/stream"
        params = {
            "settlementDateFrom": settlement_date_from,
            "settlementDateTo": settlement_date_to,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": f"WindScope/{settings.APP_VERSION} (UK Energy Analytics)",
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching FUELHH from {settlement_date_from} to {settlement_date_to} (attempt {attempt}/{max_retries})...")
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        logger.info(f"Successfully retrieved {len(data)} FUELHH records.")
                        return data
                    elif resp.status_code in (429, 502, 503, 504):
                        logger.warning(f"Elexon API returned status {resp.status_code}. Retrying in {attempt * 2}s...")
                        time.sleep(attempt * 2)
                        continue
                    else:
                        resp.raise_for_status()
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(f"HTTP error fetching FUELHH (attempt {attempt}): {e}")
                time.sleep(attempt * 2)

        raise RuntimeError(f"Failed to fetch FUELHH stream after {max_retries} attempts: {last_error}")

    def fetch_windfor_stream(
        self,
        publish_datetime_from: str = "2025-12-30T00:00:00Z",
        publish_datetime_to: str = "2026-02-01T00:00:00Z",
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Fetch WINDFOR (Wind generation forecast) stream.
        Endpoint: /datasets/WINDFOR/stream?publishDateTimeFrom=...&publishDateTimeTo=...
        """
        url = f"{self.base_url}/datasets/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": publish_datetime_from,
            "publishDateTimeTo": publish_datetime_to,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": f"WindScope/{settings.APP_VERSION} (UK Energy Analytics)",
        }

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching WINDFOR from {publish_datetime_from} to {publish_datetime_to} (attempt {attempt}/{max_retries})...")
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(url, params=params, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        logger.info(f"Successfully retrieved {len(data)} WINDFOR records.")
                        return data
                    elif resp.status_code in (429, 502, 503, 504):
                        logger.warning(f"Elexon API returned status {resp.status_code}. Retrying in {attempt * 2}s...")
                        time.sleep(attempt * 2)
                        continue
                    else:
                        resp.raise_for_status()
            except httpx.HTTPError as e:
                last_error = e
                logger.warning(f"HTTP error fetching WINDFOR (attempt {attempt}): {e}")
                time.sleep(attempt * 2)

        raise RuntimeError(f"Failed to fetch WINDFOR stream after {max_retries} attempts: {last_error}")

elexon_client = ElexonClient()
