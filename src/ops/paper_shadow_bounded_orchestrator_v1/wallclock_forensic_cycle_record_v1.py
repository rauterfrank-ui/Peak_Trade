"""Passive wallclock forensic cycle record (observation only; no decision feedback).

Each FIELD maps to a canonical producer on the productive bridge path.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "wallclock_forensic_cycle_record.v1"

# FIELD → metadata for operators / evidence contracts (documentation-only here).
FIELD_MANIFEST: tuple[dict[str, str], ...] = (
    {
        "FIELD": "cycle_sequence",
        "CANONICAL_PRODUCER": "paper_shadow operational_run cycle_index",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "int",
        "SEMANTIC_MEANING": "Monotonic productive cycle ordinal in session",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "omit_record_if_missing_bridge_cycle",
    },
    {
        "FIELD": "cycle_id",
        "CANONICAL_PRODUCER": "hardening_cycle_bridge_v2",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Bridge cycle identifier",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "empty_string",
    },
    {
        "FIELD": "timestamp_unix",
        "CANONICAL_PRODUCER": "observation tick receive_ts_unix / wall clock",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "float",
        "SEMANTIC_MEANING": "Wall-clock observation time",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "instrument_id",
        "CANONICAL_PRODUCER": "bridge_cycle.instrument_id",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Bound productive instrument",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "empty_string",
    },
    {
        "FIELD": "market_data_reference_digest",
        "CANONICAL_PRODUCER": "bridge_cycle.market_data_reference",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Digest of price basis / MD reference object",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "feature_digest",
        "CANONICAL_PRODUCER": "bridge_cycle.feature_digest",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Deterministic feature vector digest",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "decision_outcome",
        "CANONICAL_PRODUCER": "bridge_cycle.decision_outcome",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Terminal decision label for cycle",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "empty_string",
    },
    {
        "FIELD": "reason_codes",
        "CANONICAL_PRODUCER": "bridge_cycle.reason_codes",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "list[str]",
        "SEMANTIC_MEANING": "Ordered diagnostic reason codes",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "empty_list",
    },
    {
        "FIELD": "selected_side",
        "CANONICAL_PRODUCER": "bridge_cycle.selected_side",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Selection / side binding outcome",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "direction",
        "CANONICAL_PRODUCER": "bridge_cycle.direction",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Direction / SideState projection",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "regime_id",
        "CANONICAL_PRODUCER": "bridge_cycle.regime_id",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Feature regime / Bull-Bear context digest owner",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "pre_external_emitted",
        "CANONICAL_PRODUCER": "productive_cycle_step projection",
        "CAPTURE_CALLSITE": "operational_run_v1",
        "TYPE": "bool",
        "SEMANTIC_MEANING": "Whether PRE_EXTERNAL was projected this cycle",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "false",
    },
    {
        "FIELD": "fill_present",
        "CANONICAL_PRODUCER": "bridge_cycle.fill",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "bool",
        "SEMANTIC_MEANING": "Simulated fill occurred",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "false",
    },
    {
        "FIELD": "portfolio_state_after_hash",
        "CANONICAL_PRODUCER": "bridge_cycle.portfolio_state_after_hash",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Position/accounting state digest after cycle",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "record_digest",
        "CANONICAL_PRODUCER": "wallclock_forensic_cycle_record_v1",
        "CAPTURE_CALLSITE": "build_wallclock_forensic_cycle_record_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Deterministic digest of record payload",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "computed",
    },
    {
        "FIELD": "dual_ledger_correlation_key",
        "CANONICAL_PRODUCER": "PreExternalProductiveEventV1.event_key or run_id:cycle_id",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "str",
        "SEMANTIC_MEANING": "Forensic-only key linking bridge and shadow observations for one causal cycle",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "run_id:cycle_id_fallback",
    },
    {
        "FIELD": "pre_external_event_key",
        "CANONICAL_PRODUCER": "PreExternalProductiveEventV1.event_key",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "str|null",
        "SEMANTIC_MEANING": "PRE_EXTERNAL carrier identity when emitted",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
    {
        "FIELD": "bridge_domain_effect_present",
        "CANONICAL_PRODUCER": "bridge_cycle.fill",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "bool",
        "SEMANTIC_MEANING": "Bridge portfolio simulated fill applied this cycle",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "false",
    },
    {
        "FIELD": "shadow_domain_effect_present",
        "CANONICAL_PRODUCER": "route_pre_external_to_shadow_v1 result",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "bool",
        "SEMANTIC_MEANING": "Shadow SimulatedExecutionPort observed continuation for correlated PRE_EXTERNAL",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "false",
    },
    {
        "FIELD": "shadow_fill_present",
        "CANONICAL_PRODUCER": "ShadowExecutionEvidenceV1.simulated_fill_present",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "bool",
        "SEMANTIC_MEANING": "Shadow isolated accounting simulated fill",
        "OPTIONALITY": "required",
        "FAIL_CLOSED_BEHAVIOR": "false",
    },
    {
        "FIELD": "causal_chain_terminator",
        "CANONICAL_PRODUCER": "ShadowRoutingResultV1.fail_reason",
        "CAPTURE_CALLSITE": "apply_dual_ledger_passive_correlation_v1",
        "TYPE": "str|null",
        "SEMANTIC_MEANING": "Where PRE_EXTERNAL→shadow path stopped when shadow effect absent",
        "OPTIONALITY": "optional",
        "FAIL_CLOSED_BEHAVIOR": "null",
    },
)


def _digest(payload: Mapping[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _md_ref_digest(market_data_reference: Any) -> str | None:
    if market_data_reference is None:
        return None
    if isinstance(market_data_reference, str):
        return _digest({"market_data_reference": market_data_reference})
    if isinstance(market_data_reference, Mapping):
        return _digest(dict(market_data_reference))
    return _digest({"market_data_reference": str(market_data_reference)})


def build_wallclock_forensic_cycle_record_v1(
    *,
    bridge_cycle: Mapping[str, Any] | None,
    cycle_sequence: int,
    timestamp_unix: float,
    instrument_id: str,
    pre_external_emitted: bool,
    paper_shadow_consumed: bool | None = None,
) -> dict[str, Any] | None:
    """Build passive forensic record; returns None if bridge_cycle absent."""
    if bridge_cycle is None:
        return None
    outcome = str(bridge_cycle.get("decision_outcome") or "")
    reason_codes = list(bridge_cycle.get("reason_codes") or [])
    if not reason_codes and bridge_cycle.get("blockers"):
        reason_codes = [str(x) for x in bridge_cycle.get("blockers") or []]
    fill = bridge_cycle.get("fill")
    decision_binding = bridge_cycle.get("decision_config_binding") or {}
    confirmation_reason_codes = [
        str(r)
        for r in reason_codes
        if any(token in str(r).upper() for token in ("CONFIRM", "C0_", "C1_", "C2_", "SCOPE_C"))
    ]
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "cycle_sequence": int(cycle_sequence),
        "cycle_id": str(bridge_cycle.get("cycle_id") or ""),
        "timestamp_unix": float(timestamp_unix),
        "instrument_id": str(bridge_cycle.get("instrument_id") or instrument_id),
        "market_data_reference_digest": _md_ref_digest(bridge_cycle.get("market_data_reference")),
        "feature_digest": bridge_cycle.get("feature_digest"),
        "regime_id": bridge_cycle.get("regime_id"),
        "required_window_complete": bridge_cycle.get("required_window_complete"),
        "feature_blockers": list(bridge_cycle.get("feature_blockers") or []),
        "decision_outcome": outcome,
        "reason_codes": reason_codes,
        "selected_side": bridge_cycle.get("selected_side"),
        "direction": bridge_cycle.get("direction"),
        "confirmation_epochs": decision_binding.get("confirmation_epochs"),
        "confirmation_reason_codes": confirmation_reason_codes or None,
        "natural_enter": outcome in {"enter_long", "enter_short"},
        "pre_external_emitted": bool(pre_external_emitted),
        "paper_shadow_consumed": paper_shadow_consumed,
        "fill_present": fill is not None,
        "portfolio_state_before_hash": bridge_cycle.get("portfolio_state_before_hash"),
        "portfolio_state_after_hash": bridge_cycle.get("portfolio_state_after_hash"),
        "config_digest": bridge_cycle.get("config_digest"),
        "simulation_result": "fill_applied" if fill is not None else "no_fill",
    }
    record["record_digest"] = _digest({k: v for k, v in record.items() if k != "record_digest"})
    return record


def apply_dual_ledger_passive_correlation_v1(
    record: dict[str, Any],
    *,
    run_id: str,
    pre_external_event: Any | None = None,
    shadow_route: Any | None = None,
) -> None:
    """Passive forensic projection only — no productive or shadow state writeback."""
    cycle_id = str(record.get("cycle_id") or "")
    seq = record.get("cycle_sequence")
    if pre_external_event is not None:
        event_key = str(getattr(pre_external_event, "event_key", "") or "")
        record["pre_external_event_key"] = event_key or None
        record["dual_ledger_correlation_key"] = event_key or f"{run_id}:{cycle_id or seq}"
    else:
        record["pre_external_event_key"] = None
        record["dual_ledger_correlation_key"] = (
            f"{run_id}:{cycle_id}" if cycle_id else f"{run_id}:seq{seq}"
        )

    record["bridge_domain_effect_present"] = bool(record.get("fill_present"))
    record["shadow_domain_effect_present"] = False
    record["shadow_fill_present"] = False
    record["causal_chain_terminator"] = None
    record["paper_shadow_consumed"] = False

    if pre_external_event is None or shadow_route is None:
        return

    ok = bool(getattr(shadow_route, "ok", False))
    record["paper_shadow_consumed"] = ok
    record["shadow_domain_effect_present"] = ok
    evidence = getattr(shadow_route, "shadow_evidence", None) or {}
    if isinstance(evidence, dict):
        record["shadow_fill_present"] = bool(evidence.get("simulated_fill_present"))
    if not ok:
        record["causal_chain_terminator"] = (
            str(getattr(shadow_route, "fail_reason", "") or "") or None
        )
