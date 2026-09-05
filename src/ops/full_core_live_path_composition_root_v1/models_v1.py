"""Typed contracts for the offline Core→Live composition root."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ExecutionAdmissionDecisionV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)


class CompositionStatusV1(str, Enum):
    PASS = "PASS"
    DENY = "DENY"
    HALT = "HALT"


class PathStageV1(str, Enum):
    COMPOSITION = "COMPOSITION"
    VENUE_TRANSLATION = "VENUE_TRANSLATION"
    PRETRADE = "PRETRADE"
    EXECUTION_BOUNDARY = "EXECUTION_BOUNDARY"


@dataclass(frozen=True)
class FrozenPretradeEvidenceV1:
    """Offline frozen venue-pretrade snapshot. Not a GET. Not a cache for Live.

    FROZEN_OFFLINE_PRETRADE_EVIDENCE != FRESH_GET_PER_PRETRADE_DECISION.
    freshness_status defaults to FROZEN_OFFLINE and is never live-fresh.
    """

    max_available: Decimal
    max_size: Decimal
    available_margin_ok: bool
    price_band_ok: bool
    instrument_state_ok: bool
    account_mode_ok: bool
    pos_mode_ok: bool
    margin_mode_ok: bool
    leverage_ok: bool
    source_kind: str = "FROZEN_OFFLINE_PRETRADE_EVIDENCE"
    freshness_status: str = "FROZEN_OFFLINE"


@dataclass(frozen=True)
class CoreLiveExecutionIntentV1:
    instrument_id: str
    venue_native_id: str
    side: str
    quantity: Decimal
    quantity_unit: str
    quantity_provenance: str
    intent_action: str
    order_type_policy: str
    reduce_only: bool
    source_intent_id: str
    source_decision_id: str
    source_semantic_digest: str
    source_trading_epoch: str
    replay_id: str
    selection_id: str
    ranking_snapshot_id: str
    universe_snapshot_id: str
    sizing_result_ref: str
    capital_envelope_ref: str
    safety_boundary_ref: str
    decision_outcome: str
    mode: str
    path_kind: str
    composed_epoch: str
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    execution_eligible: bool
    submission_authorized: bool
    capital_risk_mode: str = "OFFLINE_ALGEBRA"

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "venue_native_id": self.venue_native_id,
            "side": self.side,
            "quantity": str(self.quantity),
            "quantity_unit": self.quantity_unit,
            "quantity_provenance": self.quantity_provenance,
            "intent_action": self.intent_action,
            "order_type_policy": self.order_type_policy,
            "reduce_only": self.reduce_only,
            "source_intent_id": self.source_intent_id,
            "source_decision_id": self.source_decision_id,
            "source_semantic_digest": self.source_semantic_digest,
            "source_trading_epoch": self.source_trading_epoch,
            "replay_id": self.replay_id,
            "selection_id": self.selection_id,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "universe_snapshot_id": self.universe_snapshot_id,
            "sizing_result_ref": self.sizing_result_ref,
            "capital_envelope_ref": self.capital_envelope_ref,
            "safety_boundary_ref": self.safety_boundary_ref,
            "decision_outcome": self.decision_outcome,
            "mode": self.mode,
            "path_kind": self.path_kind,
            "composed_epoch": self.composed_epoch,
            "live_enabled": self.live_enabled,
            "live_armed": self.live_armed,
            "wire_send_permitted": self.wire_send_permitted,
            "execution_eligible": self.execution_eligible,
            "submission_authorized": self.submission_authorized,
            "capital_risk_mode": self.capital_risk_mode,
        }


@dataclass(frozen=True)
class VenuePlanCandidateV1:
    instrument_id: str
    side: str
    quantity: str
    order_type: str
    td_mode: str
    reduce_only: bool
    clordid: str
    venue_native_payload: Mapping[str, Any]
    quantity_source: str
    side_source: str
    instrument_source: str
    path_kind: str


@dataclass(frozen=True)
class PretradeConjunctionResultV1:
    ok: bool
    reason_codes: tuple[str, ...]
    core_intent_valid: bool
    instrument_binding_valid: bool
    pretrade_valid: bool
    live_enabled: bool
    live_armed: bool
    owner_go_valid: bool
    wire_send_permitted: bool


@dataclass(frozen=True)
class ExecutionBoundaryResultV1:
    status: CompositionStatusV1
    reason_codes: tuple[str, ...]
    wire_send_occurred: bool
    live_execution_port_constructed: bool
    canary_http_invoked: bool
    halt_before_wire: bool
    admission: Optional[ExecutionAdmissionDecisionV1] = None


@dataclass(frozen=True)
class FullCoreLivePathInputV1:
    replay: IntegratedOfflineReplayResultV1
    bound_instrument: BoundInstrumentV1
    frozen_pretrade: FrozenPretradeEvidenceV1
    mode: str
    composed_epoch: str
    seen_semantic_digests: frozenset[str] = frozenset()
    expected_trading_epoch: Optional[str] = None
    owner_go: Optional[str] = None
    td_mode: str = "cross"
    session_id: str = "offline-full-core"
    run_id: str = "offline-full-core-run"


@dataclass(frozen=True)
class FullCoreLivePathResultV1:
    status: CompositionStatusV1
    stage: PathStageV1
    reason_codes: tuple[str, ...]
    intent: Optional[CoreLiveExecutionIntentV1]
    canonical_intent: Optional[CanonicalOrderIntentV1]
    venue_plan: Optional[VenuePlanCandidateV1]
    pretrade: Optional[PretradeConjunctionResultV1]
    boundary: Optional[ExecutionBoundaryResultV1]
    wire_send_occurred: bool
    path_kind: str
    canary_venue_proof_path: bool
    full_core_system_e2e_proven: bool
    current_live_core_path_proven: bool
    full_core_restart_test_authorized: bool
    recon_classes_reached: tuple[str, ...]
