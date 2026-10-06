"""Decision-time Dynamic Scope / Geometry read-only evidence (GHV trace plane).

Immutable snapshot derived from authoritative productive scope trace values only.
Does not recompute geometry, mutate scope, or confer trading authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Final, Mapping

from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "ghv_decision_time_geometry_evidence.v1"
OWNER: Final[str] = "full_core_live_path_composition_root_v1.ghv_decision_time_geometry_evidence_v1"
GEOMETRY_EVIDENCE_AUTHORITY: Final[str] = "NONE"
GHV_AUTHORITY: Final[str] = "NONE"
LEDGER_FILENAME: Final[str] = "ghv_decision_time_geometry_evidence_v1.jsonl"
SCOPE_TRACE_SCHEMA: Final[str] = "golden_happy_scope_decision_trace.v1"


def derive_geometry_evidence_id_v1(*, content_digest: str) -> str:
    digest = str(content_digest or "").lower()
    if len(digest) != 64:
        raise ValueError("geometry_evidence_digest_invalid")
    return f"ghv.gev.{digest[:40]}"


def build_decision_time_geometry_evidence_v1_from_scope_trace_v1(
    scope_trace: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one scope decision trace row into immutable geometry evidence."""
    if str(scope_trace.get("schema_version") or "") != SCOPE_TRACE_SCHEMA:
        raise ValueError("scope_trace_schema_mismatch")
    runtime_before = scope_trace.get("runtime_scope_state_before") or {}
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "geometry_evidence_authority": GEOMETRY_EVIDENCE_AUTHORITY,
        "ghv_authority": GHV_AUTHORITY,
        "owner": OWNER,
        "cycle_id": str(scope_trace.get("cycle_id") or ""),
        "replay_id": str(scope_trace.get("replay_id") or ""),
        "instrument_id": str(scope_trace.get("instrument_id") or ""),
        "venue_native_id": str(scope_trace.get("venue_instrument_id") or ""),
        "trading_epoch": scope_trace.get("trading_epoch"),
        "now_tick": scope_trace.get("now_tick"),
        "observation_event_time_unix": scope_trace.get("observation_event_time_unix"),
        "c1_venue_event_time": scope_trace.get("c1_venue_event_time"),
        "decision_input_mark": scope_trace.get("decision_input_mark"),
        "decision_input_anchor": scope_trace.get("decision_input_anchor"),
        "decision_input_volatility": scope_trace.get("decision_input_volatility"),
        "g17_typed_volatility": scope_trace.get("g17_typed_volatility"),
        "cmc_pre_bind_volatility": scope_trace.get("cmc_pre_bind_volatility"),
        "cmc_post_bind_volatility": scope_trace.get("cmc_post_bind_volatility"),
        "scope_resolved_volatility": scope_trace.get("scope_resolved_volatility"),
        "raw_scope_distance": scope_trace.get("raw_scope_distance"),
        "effective_hysteresis_band": scope_trace.get("effective_hysteresis_band"),
        "layer_c_up_distance": scope_trace.get("layer_c_up_distance"),
        "layer_c_adverse_exit_distance": scope_trace.get("layer_c_adverse_exit_distance"),
        "layer_c_reversal_distance": scope_trace.get("layer_c_reversal_distance"),
        "runtime_scope_upscope_boundary": (runtime_before or {}).get("current_upscope_boundary"),
        "runtime_scope_downscope_boundary": (runtime_before or {}).get(
            "current_downscope_boundary"
        ),
        "runtime_scope_hysteresis_band": (runtime_before or {}).get("current_hysteresis_band"),
        "runtime_scope_anchor_price": (runtime_before or {}).get("anchor_price"),
        "scope_trace_capture_timestamp": str(scope_trace.get("capture_timestamp") or ""),
        "scope_trace_repository_sha": str(scope_trace.get("repository_sha") or ""),
        "master_v2_decision_outcome": str(scope_trace.get("master_v2_decision_outcome") or ""),
        "entry_policy_decision_outcome": str(
            scope_trace.get("entry_policy_decision_outcome") or ""
        ),
        "scope_trace_ref": str(scope_trace.get("cycle_id") or ""),
    }
    digest = compute_content_sha256(payload)
    evidence_id = derive_geometry_evidence_id_v1(content_digest=digest)
    payload["geometry_evidence_id"] = evidence_id
    payload["content_digest"] = digest
    return payload


def append_geometry_evidence_from_scope_trace_v1(
    *,
    evidence_root: Path,
    scope_trace: Mapping[str, Any],
) -> dict[str, Any]:
    record = build_decision_time_geometry_evidence_v1_from_scope_trace_v1(scope_trace)
    path = evidence_root / LEDGER_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    return record


def find_enter_scope_trace_for_cycle_v1(
    *,
    evidence_root: Path,
    cycle_id: str,
) -> dict[str, Any] | None:
    trace_path = evidence_root / "golden_happy_scope_decision_trace_v1.jsonl"
    if not trace_path.is_file():
        return None
    match: dict[str, Any] | None = None
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("cycle_id") or "") != cycle_id:
            continue
        outcome = str(row.get("master_v2_decision_outcome") or "").lower()
        if outcome in {"enter_long", "enter_short"}:
            match = row
    return match


def resolve_geometry_evidence_for_pending_v1(
    *,
    evidence_root: Path,
    cycle_id: str,
) -> tuple[str, str]:
    """Build or resolve geometry evidence ref for a Natural-Enter cycle (read-only)."""
    trace = find_enter_scope_trace_for_cycle_v1(evidence_root=evidence_root, cycle_id=cycle_id)
    if trace is None:
        return "", ""
    record = build_decision_time_geometry_evidence_v1_from_scope_trace_v1(trace)
    return str(record["geometry_evidence_id"]), str(record["content_digest"])


def load_geometry_evidence_by_id_v1(
    *,
    evidence_root: Path,
    geometry_evidence_id: str,
) -> dict[str, Any] | None:
    path = evidence_root / LEDGER_FILENAME
    if not path.is_file() or not geometry_evidence_id:
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if str(row.get("geometry_evidence_id") or "") == geometry_evidence_id:
            return row
    return None


def geometry_evidence_immutable_digest_check_v1(record: Mapping[str, Any]) -> bool:
    body = {k: v for k, v in record.items() if k not in {"content_digest", "geometry_evidence_id"}}
    expected = str(record.get("content_digest") or "")
    actual = compute_content_sha256(body)
    return expected == actual and derive_geometry_evidence_id_v1(content_digest=actual) == str(
        record.get("geometry_evidence_id") or ""
    )


__all__ = [
    "GEOMETRY_EVIDENCE_AUTHORITY",
    "GHV_AUTHORITY",
    "LEDGER_FILENAME",
    "OWNER",
    "SCHEMA_VERSION",
    "append_geometry_evidence_from_scope_trace_v1",
    "build_decision_time_geometry_evidence_v1_from_scope_trace_v1",
    "derive_geometry_evidence_id_v1",
    "find_enter_scope_trace_for_cycle_v1",
    "geometry_evidence_immutable_digest_check_v1",
    "load_geometry_evidence_by_id_v1",
    "resolve_geometry_evidence_for_pending_v1",
]
