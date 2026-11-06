"""Bind observed position quantity to an existing reducing decision/intent.

No sizing policy, fraction, order construction, execution or authority is added.
"""

from dataclasses import dataclass, replace
import hashlib
import json
from decimal import Decimal
from typing import Any
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
    FullCoreFinalOrderEnvelopeError,
)

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    compute_semantic_digest,
    compute_quantity_provenance_ref,
    validate_canonical_order_intent_v1,
    build_canonical_full_close_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CloseOnlyQuantityDecisionV1,
    evaluate_full_position_close_quantity_v1,
)
from trading.master_v2.replay_execution_safety_contract_v1 import ReplayExecutionSafetyV1
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
    PerLanePositionTruthV1,
)
from src.ops.governed_productive_instrument_metadata_authority_producer_v1.current_productive_okx_instruments_row_producer_v1 import (
    CurrentProductiveInstrumentMetadataProducerOutputV1,
    PRODUCER_IDENTITY,
)


@dataclass(frozen=True)
class PositionManagementQuantityHandoffV1:
    status: str
    reason_codes: tuple[str, ...]
    lane_id: str
    instrument_id: str
    venue_native_id: str
    instrument_epoch: str
    decision_id: str
    decision_outcome: str
    position_side: str
    open_quantity: Decimal | None
    quantity_unit: str
    position_snapshot_digest: str
    instrument_metadata_ref: str
    requested_quantity: Decimal | None
    canonical_intent_ref: str
    submission_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "reason_codes": list(self.reason_codes),
            "open_quantity": None if self.open_quantity is None else str(self.open_quantity),
            "requested_quantity": None
            if self.requested_quantity is None
            else str(self.requested_quantity),
        }


def bind_position_management_quantity_handoff_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    position: PerLanePositionTruthV1,
    replay: Any,
    metadata: CurrentProductiveInstrumentMetadataProducerOutputV1 | None,
    reconciliation_admitted: bool,
) -> PositionManagementQuantityHandoffV1:
    """Carry exact contracts; validate a supplied intent without resizing it."""
    observation = position.quantity_observation
    evidence = getattr(replay, "evidence", None)
    intermediate = getattr(replay, "intermediate", None)
    policy = getattr(intermediate, "entry_exit_decision", None)
    outcome = str(getattr(evidence, "decision_outcome", "")).lower()
    decision_id = str(getattr(evidence, "decision_id", ""))
    quantity = None if observation is None else observation.quantity
    metadata_ref = ""
    unit = "UNBOUND"
    requested = None
    intent_ref = ""

    def result(status, *reasons):
        return PositionManagementQuantityHandoffV1(
            status=status,
            reason_codes=tuple(reasons),
            lane_id=identity.lane_id,
            instrument_id=identity.canonical_instrument_id,
            venue_native_id=identity.venue_native_id,
            instrument_epoch=identity.lane_identity.instrument_epoch,
            decision_id=decision_id,
            decision_outcome=outcome,
            position_side=position.existing_position_side.value,
            open_quantity=quantity,
            quantity_unit=unit,
            position_snapshot_digest="" if observation is None else observation.snapshot_digest,
            instrument_metadata_ref=metadata_ref,
            requested_quantity=requested,
            canonical_intent_ref=intent_ref,
        )

    if not reconciliation_admitted or not getattr(replay, "replay_pass", False):
        return result("REJECTED", "POSITION_RECONCILIATION_OR_REPLAY_UNAVAILABLE")
    if outcome not in {"reduce", "exit"} or policy is None or not policy.reduce_only:
        return result("REJECTED", "REDUCING_POLICY_DECISION_REQUIRED")
    if (
        getattr(evidence, "instrument_id", "") != identity.canonical_instrument_id
        or policy.instrument_id != identity.canonical_instrument_id
        or policy.decision_outcome.value != outcome
        or policy.trading_epoch != evidence.trading_epoch
    ):
        return result("REJECTED", "POSITION_MANAGEMENT_DECISION_IDENTITY_MISMATCH")
    if position.venue_flat or observation is None:
        return result("REJECTED", "OBSERVED_POSITION_QUANTITY_REQUIRED")
    if (
        observation.lane_id != identity.lane_id
        or observation.canonical_instrument_id != identity.canonical_instrument_id
        or observation.venue_native_id != identity.venue_native_id
        or observation.instrument_epoch != identity.lane_identity.instrument_epoch
        or observation.position_side != position.existing_position_side
    ):
        return result("REJECTED", "POSITION_QUANTITY_IDENTITY_MISMATCH")
    if (
        quantity is None
        or not quantity.is_finite()
        or quantity <= 0
        or not observation.snapshot_digest
    ):
        return result("REJECTED", "OBSERVED_POSITION_QUANTITY_INVALID")
    if (
        metadata is None
        or not metadata.produced
        or metadata.constraints is None
        or metadata.producer_identity != PRODUCER_IDENTITY
    ):
        return result("POSITION_OBSERVATION_BOUND", "POSITION_QUANTITY_METADATA_REQUIRED")
    constraints = metadata.constraints
    if (
        constraints.instrument_id != identity.canonical_instrument_id
        or constraints.market_type != "futures"
        or constraints.contract_kind != "LINEAR"
        or not constraints.instrument_metadata_version
    ):
        return result("REJECTED", "POSITION_QUANTITY_METADATA_MISMATCH")
    metadata_ref = constraints.instrument_metadata_version
    unit = "CONTRACTS"
    intent = getattr(intermediate, "canonical_order_intent", None)
    if intent is None:
        return result("POSITION_QUANTITY_BOUND", "CANONICAL_REDUCING_INTENT_REQUIRED")
    if not isinstance(intent, CanonicalOrderIntentV1):
        return result("REJECTED", "CANONICAL_REDUCING_INTENT_INVALID")
    requested = intent.quantity
    if (
        not requested.is_finite()
        or requested <= 0
        or compute_semantic_digest(intent) != intent.semantic_digest
        or validate_canonical_order_intent_v1(intent).validation_status != "VALID"
    ):
        return result("REJECTED", "CANONICAL_REDUCING_INTENT_INVALID")
    sizing = getattr(intermediate, "capital_risk_sizing_decision", None)
    if (
        sizing is None
        or sizing.outcome.value != "PASS"
        or sizing.quantity_provenance is None
        or sizing.final_quantity != requested
        or compute_quantity_provenance_ref(sizing.quantity_provenance) != intent.quantity_provenance
    ):
        return result("REJECTED", "REDUCING_INTENT_SIZING_BINDING_MISMATCH")
    if (
        intent.instrument_id != identity.canonical_instrument_id
        or intent.decision_id != decision_id
        or intent.trading_epoch != str(evidence.trading_epoch)
        or intent.intent_action.lower() != outcome
        or not intent.reduce_only
        or intent.side.lower() != position.existing_position_side.value
        or intent.expected_position_side.lower() != position.existing_position_side.value
        or intent.quantity_unit != unit
        or intent.instrument_metadata_ref != metadata_ref
    ):
        return result("REJECTED", "REDUCING_INTENT_POSITION_BINDING_MISMATCH")
    if requested > quantity:
        return result("REJECTED", "REDUCING_QUANTITY_EXCEEDS_OPEN_POSITION")
    if outcome == "exit" and requested != quantity:
        return result("REJECTED", "EXIT_QUANTITY_DOES_NOT_CLOSE_POSITION")
    lot = constraints.lot_size
    if (
        not lot.is_finite()
        or lot <= 0
        or requested % lot != 0
        or requested < constraints.minimum_quantity
    ):
        return result("REJECTED", "REDUCING_QUANTITY_CONSTRAINT_MISMATCH")
    intent_ref = intent.semantic_digest
    return result("BOUND_TO_CANONICAL_INTENT")


@dataclass(frozen=True)
class PositionManagementCloseIntentHandoffV1:
    quantity_handoff: PositionManagementQuantityHandoffV1
    close_quantity_decision: CloseOnlyQuantityDecisionV1 | None
    canonical_intent: CanonicalOrderIntentV1 | None
    reason_codes: tuple[str, ...]


def _resolved_close_safety_v1(replay: Any) -> bool:
    policy = replay.intermediate.entry_exit_decision
    safety = getattr(replay, "replay_execution_safety", None)
    return (
        policy.reconciliation_state.value == "reconciled"
        and policy.position_state.value in {"open_full", "open_partial"}
        and isinstance(safety, ReplayExecutionSafetyV1)
        and not (safety.cancel_only and not (safety.reduce_only or safety.flatten_only))
        and any(ref.startswith("safety:") for ref in safety.source_refs)
        and not set(safety.reason_codes)
        & {"reconciliation_required", "submission_unknown", "position_reconciliation_required"}
    )


def _canonical_close_matches_assessment_v1(handoff: PositionManagementCloseIntentHandoffV1) -> bool:
    if not isinstance(handoff, PositionManagementCloseIntentHandoffV1):
        return False
    close, intent, receipt = (
        handoff.close_quantity_decision,
        handoff.canonical_intent,
        handoff.quantity_handoff,
    )
    if (
        not isinstance(close, CloseOnlyQuantityDecisionV1)
        or not isinstance(intent, CanonicalOrderIntentV1)
        or not isinstance(receipt, PositionManagementQuantityHandoffV1)
        or receipt.status != "CANONICAL_CLOSE_INTENT_BOUND"
    ):
        return False
    rebuilt = build_canonical_full_close_intent_v1(
        close=close,
        intent_id=intent.intent_id,
        canonical_trading_logic_version=intent.canonical_trading_logic_version,
    )
    return (
        rebuilt.intent is not None
        and rebuilt.intent == intent
        and not handoff.reason_codes
        and not receipt.reason_codes
        and not receipt.submission_authorized
        and receipt.decision_outcome == "exit"
        and receipt.decision_id == close.decision_id
        and receipt.instrument_id == close.instrument_id
        and receipt.position_side.upper() == close.position_side
        and receipt.open_quantity == receipt.requested_quantity == close.final_quantity
        and receipt.quantity_unit == "CONTRACTS"
        and receipt.instrument_metadata_ref == close.instrument_metadata_ref
        and receipt.position_snapshot_digest == close.position_snapshot_ref
        and receipt.canonical_intent_ref == intent.semantic_digest
    )


def validate_full_close_execution_source_v1(
    handoff: PositionManagementCloseIntentHandoffV1, *, replay: Any, bound_instrument: Any
) -> bool:
    """Admit only the checked close assessment; never reuse entry budget approval."""
    if not _canonical_close_matches_assessment_v1(handoff):
        return False
    receipt, close = handoff.quantity_handoff, handoff.close_quantity_decision
    identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id=receipt.lane_id, bound=bound_instrument
    )
    binding_ref = hashlib.sha256(
        json.dumps(identity.to_manifest_dict(), sort_keys=True).encode()
    ).hexdigest()
    policy = replay.intermediate.entry_exit_decision
    return (
        replay.replay_pass is True
        and replay.evidence.decision_outcome == "exit"
        and replay.evidence.decision_id == close.decision_id
        and str(replay.evidence.trading_epoch) == close.trading_epoch
        and policy.decision_outcome.value == "exit"
        and policy.instrument_id == close.instrument_id == bound_instrument.instrument_id
        and policy.trading_epoch == replay.evidence.trading_epoch
        and policy.reduce_only
        and receipt.venue_native_id == identity.venue_native_id
        and receipt.instrument_epoch == identity.lane_identity.instrument_epoch
        and close.binding_ref == binding_ref
        and _resolved_close_safety_v1(replay)
    )


@dataclass(frozen=True)
class PositionManagementExecutionHandoffV1:
    source: PositionManagementCloseIntentHandoffV1
    envelope: FinalOrderEnvelopeV1


def validates_position_management_envelope_v1(handoff: Any) -> bool:
    """Preserve the canonical close through the immutable execution envelope."""
    if not isinstance(handoff, PositionManagementExecutionHandoffV1):
        return False
    if not _canonical_close_matches_assessment_v1(handoff.source):
        return False
    receipt = handoff.source.quantity_handoff
    intent = handoff.source.canonical_intent
    envelope = handoff.envelope
    if not isinstance(envelope, FinalOrderEnvelopeV1):
        return False
    try:
        assert_envelope_unmodified_v1(envelope)
    except FullCoreFinalOrderEnvelopeError:
        return False
    return (
        receipt.venue_native_id == envelope.instrument_id
        and envelope.reduce_only is True
        and envelope.side == ("sell" if intent.side == "LONG" else "buy")
        and envelope.quantity == str(intent.quantity)
        and envelope.quantity_unit == intent.quantity_unit
        and envelope.order_type == "market"
        and envelope.provenance_ref == intent.semantic_digest
    )


def validates_position_management_execution_handoff_v1(
    handoff: Any, *, native_id: str, positions_payload: Any
) -> bool:
    """Recheck the envelope against the original observed snapshot at the host seam."""
    if not validates_position_management_envelope_v1(handoff):
        return False
    snapshot_digest = hashlib.sha256(
        json.dumps(positions_payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return (
        handoff.envelope.instrument_id == native_id
        and snapshot_digest == handoff.source.quantity_handoff.position_snapshot_digest
    )


def compose_position_management_full_close_intent_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    position: PerLanePositionTruthV1,
    replay: Any,
    metadata: CurrentProductiveInstrumentMetadataProducerOutputV1 | None,
    reconciliation_admitted: bool,
) -> PositionManagementCloseIntentHandoffV1:
    """Original EXIT decision → close-only quantity owner → canonical intent owner.

    The replay is not rewritten. No partial REDUCE sizing or execution is added.
    """
    handoff = bind_position_management_quantity_handoff_v1(
        identity=identity,
        position=position,
        replay=replay,
        metadata=metadata,
        reconciliation_admitted=reconciliation_admitted,
    )
    if handoff.decision_outcome != "exit":
        return PositionManagementCloseIntentHandoffV1(
            handoff, None, None, ("REDUCE_RISK_RULE_REQUIRED",)
        )
    if handoff.status not in {"POSITION_QUANTITY_BOUND", "BOUND_TO_CANONICAL_INTENT"}:
        return PositionManagementCloseIntentHandoffV1(handoff, None, None, handoff.reason_codes)
    policy = replay.intermediate.entry_exit_decision
    if not _resolved_close_safety_v1(replay):
        reasons = ("FULL_CLOSE_SAFETY_OR_POSITION_UNRESOLVED",)
        return PositionManagementCloseIntentHandoffV1(
            replace(handoff, status="REJECTED", reason_codes=reasons), None, None, reasons
        )
    if handoff.status == "BOUND_TO_CANONICAL_INTENT":
        return PositionManagementCloseIntentHandoffV1(
            handoff, None, replay.intermediate.canonical_order_intent, ()
        )
    binding_ref = hashlib.sha256(
        json.dumps(identity.to_manifest_dict(), sort_keys=True).encode()
    ).hexdigest()
    close = evaluate_full_position_close_quantity_v1(
        decision_id=handoff.decision_id,
        instrument_id=handoff.instrument_id,
        trading_epoch=str(replay.evidence.trading_epoch),
        decision_outcome="exit",
        position_side=handoff.position_side,
        open_quantity=handoff.open_quantity,
        position_snapshot_ref=handoff.position_snapshot_digest,
        binding_ref=binding_ref,
        reconciliation_status=policy.reconciliation_state.value,
        instrument=metadata.constraints,
    )
    built = build_canonical_full_close_intent_v1(
        close=close,
        intent_id=f"close-{close.semantic_digest[:32]}",
        canonical_trading_logic_version="integrated_offline_trading_logic_replay_v1",
    )
    if built.intent is None:
        reasons = close.reason_codes if close.quantity_provenance is None else built.reason_codes
        return PositionManagementCloseIntentHandoffV1(
            replace(handoff, status="REJECTED", reason_codes=reasons),
            close,
            None,
            reasons,
        )
    handoff = replace(
        handoff,
        status="CANONICAL_CLOSE_INTENT_BOUND",
        requested_quantity=built.intent.quantity,
        canonical_intent_ref=built.intent.semantic_digest,
        reason_codes=(),
    )
    return PositionManagementCloseIntentHandoffV1(handoff, close, built.intent, ())
