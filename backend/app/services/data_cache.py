import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple, List, Dict, Any, Optional
from ..config import settings
from .elexon import elexon_client

logger = logging.getLogger(__name__)

class DataCacheService:
    """Manages file-based caching for January 2026 Elexon datasets."""

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.DATA_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.fuelhh_file = self.cache_dir / "fuelhh_jan2026.json"
        self.windfor_file = self.cache_dir / "windfor_jan2026.json"
        self.metadata_file = self.cache_dir / "metadata.json"

    def get_cache_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading metadata file: {e}")
        return {}

    def _save_metadata(self, meta: Dict[str, Any]):
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            logger.warning(f"Error writing cache metadata: {e}")

    def load_or_fetch_fuelhh(self, force_refresh: bool = False) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """
        Returns: (records, is_cached, cache_timestamp)
        """
        if not force_refresh and self.fuelhh_file.exists():
            try:
                with open(self.fuelhh_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = self.get_cache_metadata()
                ts = meta.get("fuelhh_updated_at")
                logger.info(f"Loaded {len(data)} FUELHH records from local verified cache.")
                return data, True, ts
            except Exception as e:
                logger.warning(f"Failed to read FUELHH cache: {e}. Refetching from API.")

        # Fetch from Elexon
        data = elexon_client.fetch_fuelhh_stream(
            settlement_date_from="2026-01-01",
            settlement_date_to="2026-01-31",
        )
        # Write to cache
        try:
            with open(self.fuelhh_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            now_str = datetime.now(timezone.utc).isoformat()
            meta = self.get_cache_metadata()
            meta["fuelhh_updated_at"] = now_str
            meta["fuelhh_count"] = len(data)
            self._save_metadata(meta)
            return data, False, now_str
        except Exception as e:
            logger.error(f"Failed to cache FUELHH to disk: {e}")
            return data, False, None

    def load_or_fetch_windfor(self, force_refresh: bool = False) -> Tuple[List[Dict[str, Any]], bool, Optional[str]]:
        """
        Returns: (records, is_cached, cache_timestamp)
        """
        if not force_refresh and self.windfor_file.exists():
            try:
                with open(self.windfor_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = self.get_cache_metadata()
                ts = meta.get("windfor_updated_at")
                logger.info(f"Loaded {len(data)} WINDFOR records from local verified cache.")
                return data, True, ts
            except Exception as e:
                logger.warning(f"Failed to read WINDFOR cache: {e}. Refetching from API.")

        # Fetch from Elexon
        data = elexon_client.fetch_windfor_stream(
            publish_datetime_from="2025-12-30T00:00:00Z",
            publish_datetime_to="2026-02-01T00:00:00Z",
        )
        # Write to cache
        try:
            with open(self.windfor_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
            now_str = datetime.now(timezone.utc).isoformat()
            meta = self.get_cache_metadata()
            meta["windfor_updated_at"] = now_str
            meta["windfor_count"] = len(data)
            self._save_metadata(meta)
            return data, False, now_str
        except Exception as e:
            logger.error(f"Failed to cache WINDFOR to disk: {e}")
            return data, False, None

data_cache_service = DataCacheService()
