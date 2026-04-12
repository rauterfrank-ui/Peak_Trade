"""
Local Kraken parquet cache health for Ops Cockpit ``dependencies_state`` — read-only.

Uses ``check_data_health_only`` from ``kraken_cache_loader`` (offline filesystem reads only).
Does **not** call exchanges or assert live market data quality — **local cache file / QC only**.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

READER_SCHEMA_VERSION = "market_data_cache_observation_reader/v0"


def _map_health_to_rollout(status: str) -> str:
    if status == "ok":
        return "ok"
    if status in ("missing_file", "too_few_bars", "empty", "invalid_format"):
        return "degraded"
    if status == "other":
        return "warn"
    return "unknown"


def read_market_data_cache_observation(
    repo_root: Path | None,
    config_path: Optional[Path],
) -> Dict[str, Any]:
    """
    Resolve ``[real_market_smokes]`` from config (when present), run ``check_data_health_only``
    on the local cache directory, return observation metadata for the cockpit payload.

    ``market_data_cache`` in the result is the same rollup string used in
    ``dependencies_state.market_data_cache`` when non-unknown (ok / degraded / warn).
    """
    provenance: Dict[str, Any] = {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "data_source": "none",
    }

    def _unknown(reason: str, **extra: Any) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "market_data_cache": "unknown",
            "data_source": provenance.get("data_source", "none"),
            "observation_reason": reason,
            "provenance": {**provenance, **extra},
            "details": None,
            "last_updated_utc": None,
        }
        return out

    if config_path is None or not config_path.exists():
        return _unknown("no_config_path")

    try:
        from src.data.kraken_cache_loader import (
            check_data_health_only,
            get_real_market_smokes_config,
        )

        rms = get_real_market_smokes_config(str(config_path))
    except Exception as e:
        logger.debug("market_data_cache_observation_reader: config load: %s", e)
        return _unknown("config_load_failed", error_type=type(e).__name__)

    rel_cfg = None
    try:
        if repo_root is not None:
            rel_cfg = str(config_path.relative_to(repo_root))
    except ValueError:
        rel_cfg = str(config_path)
    provenance["config_path"] = rel_cfg or str(config_path)

    base_path = repo_root / rms["base_path"] if repo_root else Path(rms["base_path"])
    provenance["cache_base_path"] = str(rms.get("base_path", "data/cache"))
    try:
        provenance["resolved_base_path"] = (
            str(base_path.relative_to(repo_root)) if repo_root else str(base_path)
        )
    except ValueError:
        provenance["resolved_base_path"] = str(base_path)

    if not base_path.exists():
        return _unknown("cache_base_path_absent", resolved_base=str(base_path))

    try:
        health = check_data_health_only(
            base_path,
            market=str(rms.get("default_market", "BTC/EUR")),
            timeframe=str(rms.get("default_timeframe", "1h")),
            min_bars=int(rms.get("min_bars", 500)),
        )
    except Exception as e:
        logger.debug("market_data_cache_observation_reader: check_data_health_only: %s", e)
        return _unknown("health_check_failed", error_type=type(e).__name__)

    raw_status = str(health.status)
    rollout = _map_health_to_rollout(raw_status)
    if rollout == "unknown":
        return _unknown(
            "unmapped_health_status",
            kraken_health_status=raw_status,
        )

    provenance["data_source"] = "kraken_parquet_cache_local"
    provenance["kraken_health_status"] = raw_status

    last_utc = None
    if health.end_ts is not None:
        try:
            last_utc = health.end_ts.isoformat()
        except Exception:
            last_utc = str(health.end_ts)

    details = {
        "kraken_health_status": raw_status,
        "num_bars": health.num_bars,
        "notes": (health.notes or "")[:500] if health.notes else None,
        "file_path": health.file_path,
    }

    obs_reason = f"kraken_cache_health_{raw_status}"

    return {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "market_data_cache": rollout,
        "data_source": "kraken_parquet_cache_local",
        "observation_reason": obs_reason,
        "provenance": provenance,
        "details": details,
        "last_updated_utc": last_utc,
    }
