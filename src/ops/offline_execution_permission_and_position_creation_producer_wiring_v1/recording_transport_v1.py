"""Recording/simulated transport. Distinct from SimulatedExecutionPort accounting."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.order_lifecycle_state_machine_v1 import (
    OrderLifecycleStateMachineV1,
    OrderLifecycleTransitionError,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1 import (
    constants_v1 as _constants,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    PositionCreationRequestCandidateV1,
    RecordingTransportRecordV1,
    ReconObligationV1,
    TransportOutcomeKindV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.reconciliation_hooks_v1 import (
    advance_lifecycle_for_recording_outcome_v1,
)


class RecordingTransportError(RuntimeError):
    """Fail-closed recording-transport violation."""


_FROZEN_FALSE_ATTRS = frozenset(
    {
        "PRODUCTIVE_WIRE_ENABLED",
        "PRODUCTIVE_WIRE_REACHABLE",
        "wire_send_enabled",
        "venue_live_contact",
        "network_call_performed",
    }
)


@dataclass
class OfflineRecordingTransportV1:
    """Records one logical action. Cannot send HTTP or load secrets."""

    PORT_KIND: str = "OFFLINE_RECORDING_TRANSPORT_V1"
    PRODUCTIVE_WIRE_ENABLED: bool = False
    PRODUCTIVE_WIRE_REACHABLE: bool = False
    venue_live_contact: bool = False
    wire_send_enabled: bool = False
    simulate_unknown: bool = False
    simulate_reject: bool = False
    _records: dict[str, RecordingTransportRecordV1] = field(default_factory=dict)
    _lifecycles: dict[str, OrderLifecycleStateMachineV1] = field(default_factory=dict)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _FROZEN_FALSE_ATTRS and value is not False:
            raise RecordingTransportError(f"WIRE_FENCE_IMMUTABLE:{name}")
        object.__setattr__(self, name, value)

    def handoff(self, candidate: PositionCreationRequestCandidateV1) -> RecordingTransportRecordV1:
        if (
            _constants.PRODUCTIVE_WIRE_ENABLED
            or _constants.PRODUCTIVE_WIRE_REACHABLE
            or _constants.BLIND_RESEND_ALLOWED
        ):
            raise RecordingTransportError("STANDING_WIRE_FENCE_VIOLATION")
        if self.PRODUCTIVE_WIRE_ENABLED or self.wire_send_enabled or self.venue_live_contact:
            raise RecordingTransportError("INSTANCE_WIRE_FENCE_VIOLATION")
        identity = candidate.action_identity.action_identity
        existing = self._records.get(identity)
        if existing is not None:
            if (
                existing.instrument_id != candidate.instrument_id
                or existing.side != candidate.side
                or existing.quantity != candidate.quantity
            ):
                raise RecordingTransportError("CONFLICTING_DUPLICATE_REJECTED")
            if existing.outcome is TransportOutcomeKindV1.UNKNOWN:
                raise RecordingTransportError("AMBIGUOUS_SUBMIT_NO_RESEND")
            return RecordingTransportRecordV1(
                outcome=TransportOutcomeKindV1.DUPLICATE_SUPPRESSED,
                action_identity=existing.action_identity,
                client_order_id=existing.client_order_id,
                instrument_id=existing.instrument_id,
                side=existing.side,
                quantity=existing.quantity,
                body_sha256=existing.body_sha256,
                lifecycle_state=existing.lifecycle_state,
                recon_obligation=existing.recon_obligation,
                duplicate_suppressed=True,
                productive_wire_reachable=False,
                network_call_performed=False,
                secret_materialized=False,
                reason_codes=("DUPLICATE_LOGICAL_INVOCATION",),
            )
        body_text = json.dumps(
            dict(candidate.venue_native_body),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        body_sha256 = hashlib.sha256(body_text.encode("utf-8")).hexdigest()
        machine = OrderLifecycleStateMachineV1(
            client_order_id=candidate.action_identity.client_order_id,
            intent_id=candidate.action_identity.plan_digest,
            order_plan_id=candidate.action_identity.action_identity,
        )
        if self.simulate_unknown:
            outcome = TransportOutcomeKindV1.UNKNOWN
        elif self.simulate_reject:
            outcome = TransportOutcomeKindV1.REJECTED
        else:
            outcome = TransportOutcomeKindV1.RECORDED
        try:
            lifecycle_state, recon = advance_lifecycle_for_recording_outcome_v1(
                machine, outcome=outcome
            )
        except OrderLifecycleTransitionError as exc:
            raise RecordingTransportError(f"LIFECYCLE_FAIL_CLOSED:{exc.code}") from exc
        record = RecordingTransportRecordV1(
            outcome=outcome,
            action_identity=identity,
            client_order_id=candidate.action_identity.client_order_id,
            instrument_id=candidate.instrument_id,
            side=candidate.side,
            quantity=candidate.quantity,
            body_sha256=body_sha256,
            lifecycle_state=lifecycle_state,
            recon_obligation=recon,
            duplicate_suppressed=False,
            productive_wire_reachable=False,
            network_call_performed=False,
            secret_materialized=False,
            reason_codes=(outcome.value,),
        )
        self._records[identity] = record
        self._lifecycles[identity] = machine
        return record

    def recorded_count(self) -> int:
        return sum(
            1
            for item in self._records.values()
            if item.outcome
            in {
                TransportOutcomeKindV1.RECORDED,
                TransportOutcomeKindV1.REJECTED,
                TransportOutcomeKindV1.UNKNOWN,
            }
        )
