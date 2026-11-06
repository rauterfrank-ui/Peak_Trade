"""
Session end mismatch observation for Ops Cockpit — read-only, artifact-driven.

Combines live session registry JSONs and ``live_runs`` run metadata/events to
surface **local** closure consistency hints. Does **not** query brokers or
exchanges and does **not** enforce session gates.

Fail-safe: on missing paths, schema drift, or I/O errors → conservative
``unknown`` / ``no_signal`` outcomes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

READER_SCHEMA_VERSION = "session_end_mismatch_reader/v0"
RUNBOOK_REF = "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH"

_TERMINAL_STATUSES = frozenset({"completed", "failed", "aborted"})


def _safe_int(mapping: Dict[str, Any], key: str) -> Optional[int]:
    try:
        v = mapping.get(key)
        if v is None:
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def _scan_events_for_session_markers(run_dir: Path) -> Dict[str, bool]:
    """Best-effort scan for session lifecycle strings in event tables."""
    out = {"has_session_end_like": False, "has_session_start_like": False}
    try:
        from src.live.run_logging import load_run_events
    except ImportError as e:
        logger.debug("session_end_mismatch_reader: import failed: %s", e)
        return out
    try:
        df = load_run_events(run_dir)
    except (FileNotFoundError, OSError):
        return out
    except Exception as e:
        logger.debug("session_end_mismatch_reader: load_run_events %s: %s", run_dir, e)
        return out
    if df is None or getattr(df, "empty", True):
        return out
    for col in getattr(df, "columns", []):
        cl = str(col).lower()
        if not (
            cl.startswith("extra_")
            or cl in ("event_type", "type", "kind", "event", "msg", "message")
        ):
            continue
        try:
            ser = df[col].astype(str).str.lower()
            if ser.str.contains("session_end", na=False).any():
                out["has_session_end_like"] = True
            if ser.str.contains("session_start", na=False).any():
                out["has_session_start_like"] = True
        except Exception:
            continue
    return out


def _latest_live_run_metadata(
    live_runs_root: Path,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[bool]]:
    """Returns (meta_dict, run_id, ended_at_present) for newest run by list_runs order."""
    try:
        from src.live.run_logging import list_runs, load_run_metadata
    except ImportError as e:
        logger.debug("session_end_mismatch_reader: import failed: %s", e)
        return None, None, None
    if not live_runs_root.exists():
        return None, None, None
    try:
        run_ids = list_runs(live_runs_root)
    except Exception as e:
        logger.debug("session_end_mismatch_reader: list_runs: %s", e)
        return None, None, None
    if not run_ids:
        return None, None, None
    rid = run_ids[0]
    run_dir = live_runs_root / rid
    try:
        meta = load_run_metadata(run_dir)
        md = meta.to_dict()
        ended = md.get("ended_at")
        ended_present = ended is not None and str(ended).strip() != ""
        return md, rid, ended_present
    except Exception as e:
        logger.debug("session_end_mismatch_reader: metadata %s: %s", run_dir, e)
        return None, rid, None


def build_session_end_mismatch_state(
    *,
    sessions_root: Path,
    live_runs_root: Path,
    stale_state: Dict[str, Any],
    balance_semantics_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build ``session_end_mismatch_state`` payload (read-only observation).

    ``blocked_next_session`` is an operator **hint** derived from artifacts only;
    it does not perform enforcement.
    """
    provenance: Dict[str, Any] = {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "registry_present": False,
        "registry_num_sessions": None,
        "registry_started_count": None,
        "registry_latest_status": None,
        "registry_latest_finished_at_present": None,
        "live_runs_present": live_runs_root.exists(),
        "live_runs_latest_run_id": None,
        "live_runs_latest_ended_at_present": None,
        "live_runs_events_session_markers": None,
    }

    balance_stale = str(stale_state.get("balance") or "unknown")
    sem = str(balance_semantics_state.get("balance_semantic_state") or "")
    balance_blocked_hint = balance_stale == "blocked" or sem == "balance_semantics_blocked"

    registry_has_files = False
    summary_by_status: Dict[str, int] = {}
    started_count = 0
    latest_status: Optional[str] = None
    latest_finished_at_present: Optional[bool] = None

    if sessions_root.exists():
        try:
            from src.experiments.live_session_registry import (
                STATUS_STARTED,
                get_session_summary,
                list_session_records,
            )

            provenance["registry_present"] = True
            summ = get_session_summary(base_dir=sessions_root)
            provenance["registry_num_sessions"] = _safe_int(summ, "num_sessions")
            summary_by_status = dict(summ.get("by_status") or {})
            started_count = int(summary_by_status.get(STATUS_STARTED, 0) or 0)
            provenance["registry_started_count"] = started_count
            recs = list_session_records(base_dir=sessions_root, limit=1)
            registry_has_files = len(recs) > 0
            if recs:
                r0 = recs[0]
                latest_status = str(r0.status or "")
                provenance["registry_latest_status"] = latest_status
                fa = r0.finished_at
                latest_finished_at_present = fa is not None
                provenance["registry_latest_finished_at_present"] = latest_finished_at_present
        except Exception as e:
            logger.debug("session_end_mismatch_reader: registry: %s", e)

    _meta_d, run_id, ended_present = _latest_live_run_metadata(live_runs_root)
    provenance["live_runs_latest_run_id"] = run_id
    provenance["live_runs_latest_ended_at_present"] = ended_present

    event_markers: Optional[Dict[str, bool]] = None
    if run_id and live_runs_root.exists():
        try:
            event_markers = _scan_events_for_session_markers(live_runs_root / run_id)
            provenance["live_runs_events_session_markers"] = event_markers
        except Exception as e:
            logger.debug("session_end_mismatch_reader: event scan: %s", e)

    data_sources: List[str] = []
    if registry_has_files or (provenance.get("registry_num_sessions") or 0) > 0:
        data_sources.append("live_session_registry")
    if run_id:
        data_sources.append("live_runs")
    data_source = "+".join(data_sources) if data_sources else "none"

    reasons: List[str] = []

    if not registry_has_files and not run_id:
        return {
            "status": "unknown",
            "summary": "no_signal",
            "blocked_next_session": False,
            "runbook": RUNBOOK_REF,
            "data_source": "none",
            "observation_reason": "no_registry_or_live_runs_artifacts",
            "provenance": provenance,
            "reader_schema_version": READER_SCHEMA_VERSION,
        }

    mismatch = False
    ambiguous = False

    if started_count > 0:
        mismatch = True
        reasons.append("registry_by_status_started_nonzero")

    if latest_status == "started":
        mismatch = True
        reasons.append("registry_latest_status_is_started")

    if (
        latest_status is not None
        and latest_status in _TERMINAL_STATUSES
        and latest_finished_at_present is False
    ):
        ambiguous = True
        reasons.append("registry_terminal_missing_finished_at")

    if run_id and ended_present is False:
        ambiguous = True
        reasons.append("live_run_metadata_not_finalized")

    if (
        event_markers
        and event_markers.get("has_session_start_like")
        and not event_markers.get("has_session_end_like")
    ):
        ambiguous = True
        reasons.append("event_table_start_without_end_marker")

    if balance_blocked_hint:
        ambiguous = True
        reasons.append("balance_semantics_or_stale_balance_blocked")

    aligned = False
    if not mismatch and not ambiguous:
        reg_ok = (
            latest_status in _TERMINAL_STATUSES
            and latest_finished_at_present is True
            and started_count == 0
        )
        lr_ok = ended_present is True
        if registry_has_files and run_id:
            aligned = reg_ok and lr_ok
            if aligned:
                reasons.append("registry_and_live_runs_closure_signals")
        elif registry_has_files and not run_id:
            aligned = reg_ok
            if aligned:
                reasons.append("registry_closure_signals_only")
        elif not registry_has_files and run_id and lr_ok:
            aligned = True
            reasons.append("live_runs_metadata_closure_only")

    status: str
    summary: str
    blocked_hint: bool

    if mismatch:
        status = "mismatch_signal"
        if "registry_latest_status_is_started" in reasons:
            summary = "registry_latest_session_not_terminal"
        else:
            summary = "registry_has_sessions_in_started_status"
        blocked_hint = True
    elif ambiguous:
        status = "ambiguous"
        if "live_run_metadata_not_finalized" in reasons:
            summary = "live_runs_latest_run_missing_ended_at_in_metadata"
        elif "registry_terminal_missing_finished_at" in reasons:
            summary = "registry_terminal_but_finished_at_missing"
        elif "event_table_start_without_end_marker" in reasons:
            summary = "live_runs_events_suggest_start_without_end_marker"
        elif "balance_semantics_or_stale_balance_blocked" in reasons:
            summary = "balance_observation_conflict_or_blocked"
        else:
            summary = "ambiguous_local_closure_signals"
        blocked_hint = True
    elif aligned:
        status = "aligned"
        summary = "local_artifacts_consistent_for_closure_observation"
        blocked_hint = False
    else:
        status = "unknown"
        summary = "no_signal"
        blocked_hint = False
        if not reasons:
            reasons.append("insufficient_distinguishable_signals")

    return {
        "status": status,
        "summary": summary,
        "blocked_next_session": blocked_hint,
        "runbook": RUNBOOK_REF,
        "data_source": data_source,
        "observation_reason": "; ".join(reasons) if reasons else "artifact_observation",
        "provenance": provenance,
        "reader_schema_version": READER_SCHEMA_VERSION,
    }
