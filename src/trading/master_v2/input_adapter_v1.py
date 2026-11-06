# src/trading/master_v2/input_adapter_v1.py
"""
Master V2 — Input-Adapter (v1): repo-nahe, JSON-affine Mappings -> typisierte Contracts.

Erlaubtes Rohformat: flaches Objekt mit `correlation_id`, `staged` und optionalen
Handoff-Blocks (gleiche Bedeutung wie `build_master_v2_decision_packet_v1`- kwargs).
Keine I/O, keine neue Entscheidungslogik — nur Parsing/Validierung fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
    build_master_v2_decision_packet_v1,
)
from .local_evaluator_v1 import MasterV2LocalFlowResultV1, evaluate_master_v2_local_flow_v1
from .staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
    validate_staged_execution_enablement_input_v1,
)

INPUT_ADAPTER_LAYER_VERSION = "v1"

_OPTIONAL_HANDOFF_KEYS = frozenset(
    {
        "universe",
        "doubleplay",
        "scope_envelope",
        "risk_cap",
        "safety",
    }
)


@dataclass(frozen=True)
class MasterV2InputAdapterResultV1:
    layer_version: str
    ok: bool
    rejection_reason: Optional[str] = None
    correlation_id: Optional[str] = None
    staged: Optional[StagedExecutionEnablementInputV1] = None
    packet: Optional[MasterV2DecisionPacketV1] = None
    local_flow: Optional[MasterV2LocalFlowResultV1] = None


def _fail(msg: str) -> MasterV2InputAdapterResultV1:
    return MasterV2InputAdapterResultV1(
        layer_version=INPUT_ADAPTER_LAYER_VERSION,
        ok=False,
        rejection_reason=msg,
    )


def _layer_version(d: Mapping[str, Any]) -> str:
    v = d.get("layer_version", MASTER_V2_DECISION_PACKET_LAYER_VERSION)
    if not isinstance(v, str) or not v.strip():
        raise ValueError("layer_version must be a non-empty string when set")
    return v.strip()


def _parse_stage_value(v: Any, field: str) -> ExecutionStageV1:
    if not isinstance(v, str):
        raise ValueError(f"{field} must be a string")
    try:
        return ExecutionStageV1(v)
    except ValueError as e:
        raise ValueError(f"{field} must be a known stage (ExecutionStageV1)") from e


def _parse_staged_block(raw: Any) -> StagedExecutionEnablementInputV1:
    if not isinstance(raw, Mapping):
        raise ValueError("staged must be an object")
    cur = _parse_stage_value(raw.get("current_stage"), "staged.current_stage")
    req = _parse_stage_value(raw.get("requested_stage"), "staged.requested_stage")
    sd = raw.get("safety_decision_allowed")
    if sd is not True and sd is not False:
        raise ValueError("staged.safety_decision_allowed must be a boolean")
    la = raw.get("live_authority_acknowledged", False)
    if la is not True and la is not False:
        raise ValueError("staged.live_authority_acknowledged must be a boolean")
    return StagedExecutionEnablementInputV1(
        current_stage=cur,
        requested_stage=req,
        safety_decision_allowed=sd,
        live_authority_acknowledged=la,
    )


def _parse_universe(d: Mapping[str, Any]) -> UniverseSelectionHandoffV1:
    sym = d.get("symbols", [])
    if not isinstance(sym, (list, tuple)):
        raise ValueError("universe.symbols must be a list")
    if not all(isinstance(x, str) for x in sym):
        raise ValueError("universe.symbols entries must be strings")
    return UniverseSelectionHandoffV1(
        layer_version=_layer_version(d),
        symbols=tuple(sym),
    )


def _parse_doubleplay(d: Mapping[str, Any]) -> DoubleplayResolutionHandoffV1:
    res = d.get("resolution", "ok")
    if not isinstance(res, str):
        raise ValueError("doubleplay.resolution must be a string")
    return DoubleplayResolutionHandoffV1(
        layer_version=_layer_version(d),
        resolution=res,
    )


def _parse_scope(d: Mapping[str, Any]) -> ScopeCapitalEnvelopeHandoffV1:
    we = d.get("within_envelope", True)
    if we is not True and we is not False:
        raise ValueError("scope_envelope.within_envelope must be a boolean")
    return ScopeCapitalEnvelopeHandoffV1(
        layer_version=_layer_version(d),
        within_envelope=we,
    )


def _parse_risk(d: Mapping[str, Any]) -> RiskExposureCapHandoffV1:
    cs = d.get("cap_satisfied")
    if cs is not True and cs is not False:
        raise ValueError("risk_cap.cap_satisfied must be a boolean")
    return RiskExposureCapHandoffV1(
        layer_version=_layer_version(d),
        cap_satisfied=cs,
    )


def _parse_safety(d: Mapping[str, Any]) -> SafetyKillSwitchHandoffV1:
    sa = d.get("safety_decision_allowed")
    if sa is not True and sa is not False:
        raise ValueError("safety.safety_decision_allowed must be a boolean")
    return SafetyKillSwitchHandoffV1(
        layer_version=_layer_version(d),
        safety_decision_allowed=sa,
    )


def _parse_optional_mapping(
    raw: Mapping[str, Any],
    key: str,
    parser,
):
    if key not in raw:
        return None
    val = raw[key]
    if val is None:
        raise ValueError(f"{key} must not be null when present")
    if not isinstance(val, Mapping):
        raise ValueError(f"{key} must be an object when present")
    return parser(val)


def adapt_inputs_to_master_v2_flow_v1(
    raw: Mapping[str, Any],
    *,
    run_evaluator: bool = False,
    with_snapshot: bool = True,
) -> MasterV2InputAdapterResultV1:
    """
    Mappt ein einfaches Mapping (z. B. aus JSON) auf `build_master_v2_decision_packet_v1`
    und optional `evaluate_master_v2_local_flow_v1`.

    Fail-closed: unbekannte Top-Level-Schluessel werden ignoriert; fehlende Pflichtfelder
    oder typwidrige Werte fuehren zu `ok=False` und kurzem `rejection_reason`.
    """
    try:
        if not isinstance(raw, Mapping):
            return _fail("RAW_INPUT_NOT_OBJECT")

        cid_val = raw.get("correlation_id")
        if not isinstance(cid_val, str) or not cid_val.strip():
            return _fail("INVALID_CORRELATION_ID")

        if "staged" not in raw:
            return _fail("MISSING_STAGED")

        staged = _parse_staged_block(raw["staged"])
        validate_staged_execution_enablement_input_v1(staged)

        u = _parse_optional_mapping(raw, "universe", _parse_universe)
        dp = _parse_optional_mapping(raw, "doubleplay", _parse_doubleplay)
        sc = _parse_optional_mapping(raw, "scope_envelope", _parse_scope)
        rk = _parse_optional_mapping(raw, "risk_cap", _parse_risk)
        sf = _parse_optional_mapping(raw, "safety", _parse_safety)

        packet = build_master_v2_decision_packet_v1(
            cid_val.strip(),
            staged,
            universe=u,
            doubleplay=dp,
            scope_envelope=sc,
            risk_cap=rk,
            safety=sf,
        )

        lf: Optional[MasterV2LocalFlowResultV1] = None
        if run_evaluator:
            lf = evaluate_master_v2_local_flow_v1(
                cid_val.strip(),
                staged,
                universe=u,
                doubleplay=dp,
                scope_envelope=sc,
                risk_cap=rk,
                safety=sf,
                with_snapshot=with_snapshot,
            )

        return MasterV2InputAdapterResultV1(
            layer_version=INPUT_ADAPTER_LAYER_VERSION,
            ok=True,
            correlation_id=cid_val.strip(),
            staged=staged,
            packet=packet,
            local_flow=lf,
        )
    except ValueError as e:
        return _fail(f"ADAPTER_REJECT: {e.args[0] if e.args else 'value error'}")
    except TypeError as e:
        return _fail(f"ADAPTER_REJECT: {e.args[0] if e.args else 'type error'}")


def iter_unexpected_top_level_keys(raw: Mapping[str, Any]) -> frozenset[str]:
    """Hilfsfunktion fuer Tests/Diagnosen: unerwartete Top-Level-Schluessel."""
    allowed = (
        "correlation_id",
        "staged",
        *_OPTIONAL_HANDOFF_KEYS,
    )
    return frozenset(k for k in raw if k not in allowed)
