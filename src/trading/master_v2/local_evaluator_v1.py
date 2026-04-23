# src/trading/master_v2/local_evaluator_v1.py
"""
Master V2 — Lokaler Dry-Flow (v1): aufeinanderfolgende Contract-Auswertung ohne I/O.

Keine Runtime, keine Live-Autorisierung, keine Engine — nur bestehende validate/
build/critic/snapshot-Surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .decision_packet_critic_v1 import (
    DecisionPacketCriticReportV1,
    critique_master_v2_decision_packet_v1,
)
from .decision_packet_snapshot_v1 import decision_packet_to_snapshot_v1
from .decision_packet_v1 import (
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    MasterV2DecisionPacketValidationV1,
    RiskExposureCapHandoffV1,
    SafetyKillSwitchHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    UniverseSelectionHandoffV1,
    build_master_v2_decision_packet_v1,
    validate_master_v2_decision_packet_v1,
)
from .staged_execution_enablement_v1 import (
    StagedExecutionEnablementInputV1,
    validate_staged_execution_enablement_input_v1,
)

LOCAL_FLOW_LAYER_VERSION = "v1"


@dataclass(frozen=True)
class MasterV2LocalFlowResultV1:
    """
    `flow_ok` ist True, wenn Staged-Input gueltig ist und `validate` fuer das
    assemblierte Paket `ok` meldet. Critic-Warnungen blockieren `flow_ok` nicht.
    """

    layer_version: str
    flow_ok: bool
    correlation_id: str
    packet: Optional[MasterV2DecisionPacketV1] = None
    validation: Optional[MasterV2DecisionPacketValidationV1] = None
    critic_report: Optional[DecisionPacketCriticReportV1] = None
    snapshot: Optional[Dict[str, Any]] = None
    """Nur bei `with_snapshot=True` und `validation.ok`."""

    rejection_reason: Optional[str] = None
    """Fail-closed: z. B. leere correlation_id, ungueltiger staged-Input, Snapshot abgelehnt."""


def evaluate_master_v2_local_flow_v1(
    correlation_id: str,
    staged: StagedExecutionEnablementInputV1,
    *,
    universe: Optional[UniverseSelectionHandoffV1] = None,
    doubleplay: Optional[DoubleplayResolutionHandoffV1] = None,
    scope_envelope: Optional[ScopeCapitalEnvelopeHandoffV1] = None,
    risk_cap: Optional[RiskExposureCapHandoffV1] = None,
    safety: Optional[SafetyKillSwitchHandoffV1] = None,
    with_snapshot: bool = True,
) -> MasterV2LocalFlowResultV1:
    """
    Reihenfolge: Staged-validate → build → validate → critic → optional snapshot.

    Keine stille Reparatur: ungueltiger Staged-Input abgelehnt, kein Paket; bei
    Snapshot-Refusal trotz gueltigem Paket: `rejection_reason` setzen, `flow_ok` False.
    """
    if not isinstance(correlation_id, str) or not correlation_id.strip():
        return MasterV2LocalFlowResultV1(
            layer_version=LOCAL_FLOW_LAYER_VERSION,
            flow_ok=False,
            correlation_id=correlation_id if isinstance(correlation_id, str) else "",
            rejection_reason="INVALID_CORRELATION_ID",
        )

    if not isinstance(staged, StagedExecutionEnablementInputV1):
        return MasterV2LocalFlowResultV1(
            layer_version=LOCAL_FLOW_LAYER_VERSION,
            flow_ok=False,
            correlation_id=correlation_id.strip(),
            rejection_reason="STAGED_INPUT_INVALID: expected StagedExecutionEnablementInputV1",
        )
    try:
        validate_staged_execution_enablement_input_v1(staged)
    except TypeError as e:
        return MasterV2LocalFlowResultV1(
            layer_version=LOCAL_FLOW_LAYER_VERSION,
            flow_ok=False,
            correlation_id=correlation_id.strip(),
            rejection_reason=f"STAGED_INPUT_INVALID: {e.args[0] if e.args else 'type error'}",
        )

    p = build_master_v2_decision_packet_v1(
        correlation_id.strip(),
        staged,
        universe=universe,
        doubleplay=doubleplay,
        scope_envelope=scope_envelope,
        risk_cap=risk_cap,
        safety=safety,
    )
    v = validate_master_v2_decision_packet_v1(p)
    cr = critique_master_v2_decision_packet_v1(p)

    snap: Optional[Dict[str, Any]] = None
    rejection: Optional[str] = None
    if with_snapshot and v.ok:
        try:
            snap = decision_packet_to_snapshot_v1(p, require_consistent_packet=True)
        except ValueError as e:
            rejection = f"SNAPSHOT_REFUSED: {e.args[0] if e.args else 'error'}"
    elif with_snapshot and not v.ok:
        rejection = None  # valide snapshot nicht angefordert, validation schon nicht ok
    flow = v.ok and (rejection is None)

    return MasterV2LocalFlowResultV1(
        layer_version=LOCAL_FLOW_LAYER_VERSION,
        flow_ok=flow,
        correlation_id=correlation_id.strip(),
        packet=p,
        validation=v,
        critic_report=cr,
        snapshot=snap,
        rejection_reason=rejection,
    )
