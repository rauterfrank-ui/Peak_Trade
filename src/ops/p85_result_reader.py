"""
Read P85_RESULT.json artifacts for Ops Cockpit ``dependencies_state.exchange`` — read-only.

Uses **local files only** under ``out/ops/**`` (or equivalent base). Does **not** perform live
connectivity checks; ``connectivity.ok`` is interpreted as a **persisted** P85 run outcome, not a
runtime guarantee from the Cockpit build.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

READER_SCHEMA_VERSION = "p85_exchange_reader/v0"
DEFAULT_P85_OUT_BASE = "out/ops"
DEFAULT_MAX_ARTIFACT_AGE_SEC = 3600.0
ARTIFACT_NAME = "P85_RESULT.json"


def read_p85_exchange_observation(
    repo_root: Path | None,
    *,
    out_ops_base: Path | None = None,
    max_age_sec: float = DEFAULT_MAX_ARTIFACT_AGE_SEC,
) -> Dict[str, Any]:
    """
    Select the newest ``P85_RESULT.json`` under the search base (by mtime), parse defensively,
    map ``connectivity.ok`` to ``exchange`` when the artifact is **fresh**.

    Returns a single dict suitable for ``dependencies_state['p85_exchange_observation']`` and
    for setting top-level ``dependencies_state['exchange']``.
    """
    base = out_ops_base
    if base is None:
        base = repo_root / DEFAULT_P85_OUT_BASE if repo_root else Path(DEFAULT_P85_OUT_BASE)

    provenance: Dict[str, Any] = {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "search_base": str(base),
        "artifact_glob": f"**/{ARTIFACT_NAME}",
    }

    def _empty(reason: str) -> Dict[str, Any]:
        return {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "exchange": "unknown",
            "data_source": "none",
            "artifact_path": None,
            "last_updated_utc": None,
            "stale": False,
            "observation_reason": reason,
            "provenance": provenance,
        }

    if not base.exists():
        return _empty("p85_search_base_missing")

    try:
        candidates = sorted(
            base.glob(f"**/{ARTIFACT_NAME}"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError as e:
        logger.debug("p85_result_reader: glob failed: %s", e)
        return _empty("search_failed")

    if not candidates:
        return _empty("no_p85_artifact")

    p85_path = candidates[0]
    provenance["selected_artifact"] = ARTIFACT_NAME
    try:
        rel = p85_path.relative_to(repo_root) if repo_root else None
        provenance["artifact_path"] = str(rel) if rel is not None else str(p85_path)
    except ValueError:
        provenance["artifact_path"] = str(p85_path)

    try:
        st = p85_path.stat()
        mtime = st.st_mtime
        age_sec = time.time() - mtime
        last_utc = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
    except OSError as e:
        logger.debug("p85_result_reader: stat failed: %s", e)
        return _empty("artifact_stat_failed")

    is_stale = age_sec > max_age_sec
    if is_stale:
        return {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "exchange": "unknown",
            "data_source": "p85_result_json",
            "artifact_path": provenance.get("artifact_path"),
            "last_updated_utc": last_utc,
            "stale": True,
            "observation_reason": "artifact_stale",
            "provenance": provenance,
        }

    try:
        raw = p85_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        logger.debug("p85_result_reader: read/parse failed: %s", e)
        return {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "exchange": "unknown",
            "data_source": "p85_result_json",
            "artifact_path": provenance.get("artifact_path"),
            "last_updated_utc": last_utc,
            "stale": False,
            "observation_reason": "parse_error",
            "provenance": provenance,
        }

    if not isinstance(data, dict):
        return {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "exchange": "unknown",
            "data_source": "p85_result_json",
            "artifact_path": provenance.get("artifact_path"),
            "last_updated_utc": last_utc,
            "stale": False,
            "observation_reason": "root_not_object",
            "provenance": provenance,
        }

    conn = data.get("connectivity")
    if not isinstance(conn, dict):
        return {
            "reader_schema_version": READER_SCHEMA_VERSION,
            "exchange": "unknown",
            "data_source": "p85_result_json",
            "artifact_path": provenance.get("artifact_path"),
            "last_updated_utc": last_utc,
            "stale": False,
            "observation_reason": "connectivity_missing_or_invalid",
            "provenance": provenance,
        }

    ok_val = conn.get("ok")
    if ok_val is True:
        obs_reason = "p85_connectivity_ok_true"
        exch = "ok"
    elif ok_val is False:
        obs_reason = "p85_connectivity_ok_false"
        exch = "degraded"
    else:
        obs_reason = "connectivity_ok_not_boolean"
        exch = "unknown"

    return {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "exchange": exch,
        "data_source": "p85_result_json",
        "artifact_path": provenance.get("artifact_path"),
        "last_updated_utc": last_utc,
        "stale": False,
        "observation_reason": obs_reason,
        "provenance": provenance,
    }
