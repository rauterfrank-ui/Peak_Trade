"""Read current S5/Core outputs; never promote historical labels to runtime truth."""

from dataclasses import dataclass
import json
import math
from decimal import Decimal, InvalidOperation

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    validate_canonical_order_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    venue_side_from_core_intent_v1,
    FullCoreVenueTranslationError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    validates_position_management_envelope_v1,
)

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FullCoreFinalOrderEnvelopeError,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pending_decision_context_v1 import (
    PendingDecisionContextV1,
)


@dataclass(frozen=True)
class CurrentRuntimeBoundaryEvidenceV1:
    reached: bool = False
    decision_outcome: str = ""
    envelope_identity: str = ""
    cycle_instance_id: str = ""
    reason: str = "CURRENT_S5_PRE_EXTERNAL_NOT_PROVEN"
    reduce_only: bool = False


def current_runtime_cycle_records_v1(result):
    """Consistent original completed cycle observations, without financial grants."""
    trace = result.trace
    policy = result.policy_result
    if policy is None:
        return ()
    orch = policy.orchestrator_result
    records = orch.cycle_records
    if not records:
        return ()
    last = records[-1]
    if not (
        result.ok
        and result.owner_go_consumed
        and result.authority_invariants_ok
        and trace.continuous_admission_granted
        and trace.terminal_disposition == orch.disposition
        and (trace.terminal_disposition == "PRE_EXTERNAL_EFFECT")
        == (last.s5_disposition == "PRE_EXTERNAL_EFFECT")
        and trace.governed_cycle_count == trace.accepted_c1_count == len(records)
        and orch.cycles_completed == orch.accepted_c1_count == len(records)
        and last.c1_venue_event_time == orch.last_accepted_c1 == orch.cursor_floor_after
        and all(
            row.s5_disposition in {"HOLD_CLOSED", "PRE_EXTERNAL_EFFECT"}
            and math.isfinite(row.c1_venue_event_time)
            and row.c1_venue_event_time > 0
            for row in records
        )
        and len({row.cycle_instance_id for row in records}) == len(records)
        and all(
            later.c1_venue_event_time > earlier.c1_venue_event_time
            for earlier, later in zip(records, records[1:])
        )
        and not any(row.s5_disposition == "PRE_EXTERNAL_EFFECT" for row in records[:-1])
        and trace.post_count == orch.post_count == orch.external_effect_count == 0
        and orch.permit_created is False
        and policy.post_allowed is False
        and policy.external_effect_authorized is False
    ):
        return ()
    return tuple(records)


def current_runtime_boundary_evidence_v1(result) -> CurrentRuntimeBoundaryEvidenceV1:
    """A current PRE_EXTERNAL is an observed boundary, not a fill or restart grant."""
    absent = CurrentRuntimeBoundaryEvidenceV1()
    records = current_runtime_cycle_records_v1(result)
    if not records:
        return absent
    trace = result.trace
    last = records[-1]
    if (
        trace.terminal_disposition != "PRE_EXTERNAL_EFFECT"
        or last.s5_disposition != "PRE_EXTERNAL_EFFECT"
    ):
        return absent
    envelope = getattr(last, "final_order_envelope", None)
    context = getattr(last, "pending_decision_context", None)
    intent = getattr(last, "canonical_order_intent", None)
    if (
        getattr(last, "envelope_created", False) is not True
        or not isinstance(context, PendingDecisionContextV1)
        or not isinstance(intent, CanonicalOrderIntentV1)
    ):
        return absent
    try:
        assert_envelope_unmodified_v1(envelope)
        expected_identity = f"envelope_id={envelope.envelope_id};digest={envelope.envelope_digest}"
        decision = json.loads(context.producer_payload_json)
        outcome = decision["decision_outcome"]
        if validate_canonical_order_intent_v1(intent).validation_status != "VALID":
            return absent
        quantity = Decimal(envelope.quantity)
        if not (
            getattr(last, "envelope_identity", "") == expected_identity
            and context.instrument_id == trace.bound_instrument_id
            and envelope.instrument_id == context.native_id == trace.venue_native_id
            and decision["instrument_id"] == context.instrument_id
            and isinstance(outcome, str)
            and outcome in {"enter_long", "enter_short", "exit"}
            and intent.intent_action == outcome.upper()
            and bool(intent.semantic_digest)
            and context.canonical_decision_id
            and intent.decision_id == context.canonical_decision_id
            and intent.instrument_id == context.instrument_id
            and str(decision["trading_epoch"]) == str(intent.trading_epoch)
            and decision["reduce_only"] is intent.reduce_only is envelope.reduce_only
            and envelope.side == venue_side_from_core_intent_v1(intent)
            and quantity.is_finite()
            and quantity > 0
            and quantity == intent.quantity
            and envelope.quantity_unit == intent.quantity_unit
            and math.isfinite(context.decision_timestamp_unix)
            and context.decision_timestamp_unix >= last.c1_venue_event_time
        ):
            return absent
        if outcome.startswith("enter_") and (
            decision["selected_side"] != intent.side.lower() or intent.reduce_only
        ):
            return absent
        if outcome == "exit":
            close = getattr(last, "position_management_execution_handoff", None)
            if not validates_position_management_envelope_v1(close) or (
                close.envelope != envelope or close.source.canonical_intent != intent
            ):
                return absent
    except (
        FullCoreFinalOrderEnvelopeError,
        FullCoreVenueTranslationError,
        InvalidOperation,
        ValueError,
        TypeError,
        KeyError,
    ):
        return absent
    return CurrentRuntimeBoundaryEvidenceV1(
        reached=True,
        decision_outcome=outcome,
        envelope_identity=envelope.envelope_id,
        cycle_instance_id=last.cycle_instance_id,
        reason="ORIGINAL_CURRENT_S5_ENVELOPE_AND_CORE_DECISION",
        reduce_only=envelope.reduce_only is True,
    )
