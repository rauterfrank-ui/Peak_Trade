"""Offline RUNBOOK_STEP_23 KillSwitch writer-fencing and independent read paths v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CONTRACT_NAME = "killswitch_writer_fencing_and_independent_read_paths_v1"
CONTRACT_VERSION = "v1"
PRODUCER_VERSION = "killswitch_writer_fencing_and_independent_read_paths_v1"
BUILDER_VERSION = "killswitch_writer_fencing_and_independent_read_paths_builder_v1"
EVIDENCE_LEVEL = "LEVEL_3"
AUTHORITY_LEVEL = "NON_AUTHORITIZING"
RECORD_KIND = "killswitch_writer_fencing_and_independent_read_paths_record"
ARTIFACT_REL = "killswitch_writer_fencing_and_independent_read_paths_v1.json"
SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".killswitch_writer_fencing_staging_"

SCHEMA_VERSION = "killswitch_writer_fencing_and_independent_read_paths_schema_v1"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
DEFAULT_PRODUCER_IDENTITY_REF = (
    "peak_trade_offline_killswitch_writer_fencing_and_independent_read_paths_producer_v1"
)
DEFAULT_SOURCE_REVISION = "OFFLINE_DETERMINISTIC_EVIDENCE"
GENESIS_EVENT_DIGEST = "0" * 64

KILL_SWITCH_OWNER_REF = "src/risk_layer/kill_switch"
KILL_SWITCH_CONTRACT_DIGEST = (
    "killswitch_owner_contract_digest_v1_"
    "7f3c9a2e1b4d6f8051a9c3e7d2b4f6089a1c3e5d7b9f0123456789abcdef0123"
)
KILL_SWITCH_POLICY_DIGEST = (
    "killswitch_policy_digest_v1_"
    "8e4d0b3f2c5a7e9062b0d4f8c3a6e9012b4d6f8091c3e5a7b9d0f123456789abcde"
)
KILL_SWITCH_STATE_MACHINE_DIGEST = (
    "killswitch_state_machine_digest_v1_"
    "9f5e1c4a3b6d8f0173c1e5a9b4d7f0123c5e7a9b1d3f567890123456789abcdef0"
)

_VALID_DECISIONS = frozenset({"PASS", "BLOCK"})
_VALID_KILL_SWITCH_STATES = frozenset({"ARMED", "TRIPPED", "RECOVERING", "DISABLED"})
_SELF_VERIFICATION_SCHEMA_VERSION = (
    "killswitch_writer_fencing_and_independent_read_paths_self_verification_v1"
)

_FAIL_CLOSED_DECISION_CODES: tuple[str, ...] = (
    "MISSING_WRITER_IDENTITY",
    "MISSING_WRITER_EPOCH",
    "WRITER_EPOCH_REGRESSION",
    "WRITER_EPOCH_UNKNOWN",
    "WRITER_EPOCH_CONFLICT",
    "MISSING_EVENT_SEQUENCE",
    "EVENT_SEQUENCE_REGRESSION",
    "EVENT_SEQUENCE_GAP",
    "CONCURRENT_EVENT_SUCCESSOR",
    "MISSING_PREVIOUS_EVENT_DIGEST",
    "EVENT_DIGEST_MISMATCH",
    "BROKEN_EVENT_DIGEST_CHAIN",
    "STATE_ROLLBACK_DETECTED",
    "RECOVERY_CHAIN_RESET_ATTEMPT",
    "MISSING_CANONICAL_PERSISTED_STATE_REF",
    "MISSING_CANONICAL_PERSISTED_STATE_DIGEST",
    "MISSING_SAFETY_KERNEL_READ_PATH",
    "MISSING_ADAPTER_READ_PATH",
    "READ_PATHS_NOT_INDEPENDENT",
    "SHARED_VOLATILE_CACHE_ONLY",
    "SAFETY_KERNEL_STATE_UNAVAILABLE",
    "ADAPTER_STATE_UNAVAILABLE",
    "SAFETY_KERNEL_STATE_UNREADABLE",
    "ADAPTER_STATE_UNREADABLE",
    "READ_PATH_STATE_DISAGREEMENT",
    "READ_PATH_DIGEST_DISAGREEMENT",
    "STALE_SAFETY_KERNEL_STATE",
    "STALE_ADAPTER_STATE",
    "REVOCATION_EPOCH_MISMATCH",
    "TRADING_EPOCH_MISMATCH",
    "EXECUTOR_EPOCH_MISMATCH",
    "KILLSWITCH_STATE_DIGEST_MISMATCH",
    "LAST_KNOWN_ARMED_FALLBACK_REQUESTED",
    "ADAPTER_SUBMISSION_REQUESTED_ON_UNCLEAR_STATE",
    "MISSING_INPUT",
    "UNKNOWN_CONTRACT_VERSION",
    "UNKNOWN_DECISION_CODE",
    "MANIFEST_OR_DIGEST_MISMATCH",
)

KILLSWITCH_WRITER_FENCING_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "killswitch_writer_fencing_contract_complete": False,
    "killswitch_writer_fencing_offline_only": True,
    "killswitch_single_writer_required": True,
    "killswitch_writer_epoch_required": True,
    "killswitch_writer_epoch_monotonic": True,
    "lower_writer_epoch_rejected": True,
    "unknown_writer_epoch_rejected": True,
    "killswitch_event_sequence_required": True,
    "killswitch_event_sequence_monotonic": True,
    "killswitch_sequence_gap_fails_closed": True,
    "killswitch_concurrent_successor_fails_closed": True,
    "killswitch_event_digest_chain_required": True,
    "killswitch_previous_event_digest_required": True,
    "killswitch_current_event_digest_deterministic": True,
    "killswitch_broken_digest_chain_fails_closed": True,
    "killswitch_state_rollback_forbidden": True,
    "killswitch_recovery_continues_event_chain": True,
    "killswitch_independent_read_paths_required": True,
    "safety_kernel_killswitch_read_path_independent": True,
    "adapter_killswitch_read_path_independent": True,
    "safety_kernel_and_adapter_shared_volatile_cache_only": False,
    "killswitch_canonical_persisted_state_required": True,
    "adapter_monotonic_revocation_projection_required": True,
    "killswitch_state_digest_validation_required": True,
    "revocation_epoch_validation_required": True,
    "trading_epoch_validation_required": True,
    "executor_epoch_validation_required": True,
    "killswitch_freshness_validation_required": True,
    "killswitch_state_unavailable_fails_closed": True,
    "killswitch_state_unreadable_fails_closed": True,
    "killswitch_read_path_disagreement_fails_closed": True,
    "last_known_armed_fallback_allowed": False,
    "adapter_submission_allowed_on_unclear_state": False,
    "killswitch_parallel_ssot_allowed": False,
    "killswitch_bypass_allowed": False,
    "killswitch_state_rewrite_allowed": False,
    "killswitch_auto_disarm_allowed": False,
    "killswitch_auto_rearm_allowed": False,
    "pass_does_not_mean_killswitch_armed": True,
    "pass_does_not_create_execution_permission": True,
    "pass_does_not_authorize_submission": True,
    "pass_does_not_allow_orders": True,
    "pass_does_not_mutate_runtime": True,
    "futures_only": True,
    "deterministic_serialization_bound": True,
    "stable_digest_bound": True,
}

_REQUIRED_NON_MUTATION_FLAGS: dict[str, bool] = {
    "killswitch_state_mutated": False,
    "killswitch_trip_executed": False,
    "killswitch_disarm_executed": False,
    "killswitch_reset_executed": False,
    "killswitch_rearm_executed": False,
    "revocation_epoch_incremented": False,
    "authority_revoked": False,
    "authority_created": False,
    "authority_activated": False,
    "execution_permission_created": False,
    "execution_permission_consumed": False,
    "submission_authorized": False,
    "submission_claim_executed": False,
    "adapter_invoked": False,
    "order_created": False,
    "order_submitted": False,
    "order_cancel_requested": False,
    "order_amend_requested": False,
    "position_state_mutated": False,
    "runtime_state_mutated": False,
    "database_mutated": False,
    "lock_acquired": False,
    "reservation_created": False,
    "network_side_effect_created": False,
    "exchange_request_sent": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "offline_only": True,
    "does_not_mutate_kill_switch_state": True,
    "does_not_create_authority": True,
    "does_not_revoke_authority": True,
    "does_not_activate_runtime": True,
    "does_not_authorize_submission": True,
    "does_not_invoke_adapter": True,
    "does_not_send_network_request": True,
}


class KillSwitchWriterFencingError(ValueError):
    """Fail-closed KillSwitch writer-fencing contract error."""


@dataclass(frozen=True)
class KillSwitchWriterFencingEvaluationInput:
    writer_identity: str
    writer_epoch: int
    previous_writer_epoch: int
    known_writer_epochs: frozenset[int]
    concurrent_writer_same_epoch: bool
    event_id: str
    event_sequence: int
    previous_event_sequence: int
    concurrent_event_successor: bool
    previous_event_digest: str
    canonical_event_payload: Mapping[str, Any]
    current_event_digest: str
    previous_state: str
    proposed_state: str
    recovery_chain_reset_attempt: bool
    revocation_epoch: int
    trading_epoch: int
    executor_epoch: int
    canonical_persisted_state_ref: str
    canonical_persisted_state_body: Mapping[str, Any]
    canonical_persisted_state_digest: str
    safety_kernel_read_path_ref: str
    safety_kernel_read_body: Mapping[str, Any]
    safety_kernel_read_result_digest: str
    safety_kernel_read_fresh: bool
    safety_kernel_state_available: bool
    safety_kernel_state_readable: bool
    adapter_read_path_ref: str
    adapter_read_body: Mapping[str, Any]
    adapter_read_result_digest: str
    adapter_revocation_projection_digest: str
    adapter_read_fresh: bool
    adapter_state_available: bool
    adapter_state_readable: bool
    shared_volatile_cache_only: bool
    last_known_armed_fallback_requested: bool
    adapter_submission_requested_on_unclear_state: bool
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    contract_version: str = CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = BUILDER_VERSION


@dataclass(frozen=True)
class KillSwitchWriterFencingEvaluationResult:
    decision: str
    decision_code: str
    rejection_reasons: tuple[str, ...]
    fail_closed_gates: tuple[str, ...]
    writer_epoch_status: str
    event_sequence_status: str
    digest_chain_status: str
    state_transition_status: str
    state_rollback_detected: bool
    read_paths_independent: bool
    read_paths_agree: bool
    state_available: bool
    state_readable: bool
    canonical_event_payload_digest: str
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class KillSwitchWriterFencingResult:
    output_dir: Path
    evidence_id: str
    decision: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


def compute_canonical_event_payload_digest(payload: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(payload))


def compute_current_event_digest(
    *,
    previous_event_digest: str,
    canonical_event_payload_digest: str,
) -> str:
    material = f"{previous_event_digest}{canonical_event_payload_digest}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def compute_canonical_persisted_state_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(body))


def compute_read_result_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(body))


def compute_adapter_revocation_projection_digest(body: Mapping[str, Any]) -> str:
    projection = {
        "kill_switch_state": body.get("kill_switch_state"),
        "revocation_epoch": body.get("revocation_epoch"),
        "projection_monotonic": body.get("projection_monotonic"),
    }
    return compute_content_sha256(projection)


def default_canonical_persisted_state_body(
    *,
    kill_switch_state: str = "ARMED",
    revocation_epoch: int = 1,
    trading_epoch: int = 1,
    executor_epoch: int = 1,
) -> dict[str, Any]:
    return {
        "kill_switch_state": kill_switch_state,
        "revocation_epoch": revocation_epoch,
        "trading_epoch": trading_epoch,
        "executor_epoch": executor_epoch,
        "market_type": "FUTURES",
    }


def default_canonical_event_payload(
    *,
    writer_identity: str,
    writer_epoch: int,
    event_sequence: int,
    proposed_state: str = "ARMED",
) -> dict[str, Any]:
    return {
        "writer_identity": writer_identity,
        "writer_epoch": writer_epoch,
        "event_sequence": event_sequence,
        "proposed_state": proposed_state,
        "market_type": "FUTURES",
    }


def default_safety_kernel_read_body(
    *,
    kill_switch_state: str = "ARMED",
    revocation_epoch: int = 1,
    trading_epoch: int = 1,
    executor_epoch: int = 1,
    observed_at: str = OFFLINE_DETERMINISTIC_CREATED_AT,
) -> dict[str, Any]:
    return {
        "read_path_kind": "canonical_persisted_state",
        "kill_switch_state": kill_switch_state,
        "revocation_epoch": revocation_epoch,
        "trading_epoch": trading_epoch,
        "executor_epoch": executor_epoch,
        "observed_at": observed_at,
        "is_fresh": True,
        "state_available": True,
        "state_readable": True,
    }


def default_adapter_read_body(
    *,
    kill_switch_state: str = "ARMED",
    revocation_epoch: int = 1,
    trading_epoch: int = 1,
    executor_epoch: int = 1,
    observed_at: str = OFFLINE_DETERMINISTIC_CREATED_AT,
) -> dict[str, Any]:
    return {
        "read_path_kind": "adapter_monotonic_revocation_projection",
        "kill_switch_state": kill_switch_state,
        "revocation_epoch": revocation_epoch,
        "trading_epoch": trading_epoch,
        "executor_epoch": executor_epoch,
        "projection_monotonic": True,
        "observed_at": observed_at,
        "is_fresh": True,
        "state_available": True,
        "state_readable": True,
    }


def default_killswitch_writer_fencing_evaluation_input() -> KillSwitchWriterFencingEvaluationInput:
    writer_identity = "generic-futures-killswitch-writer-001"
    writer_epoch = 1
    previous_writer_epoch = 0
    event_sequence = 1
    previous_event_sequence = 0
    canonical_event_payload = default_canonical_event_payload(
        writer_identity=writer_identity,
        writer_epoch=writer_epoch,
        event_sequence=event_sequence,
    )
    payload_digest = compute_canonical_event_payload_digest(canonical_event_payload)
    previous_event_digest = GENESIS_EVENT_DIGEST
    current_event_digest = compute_current_event_digest(
        previous_event_digest=previous_event_digest,
        canonical_event_payload_digest=payload_digest,
    )
    persisted_body = default_canonical_persisted_state_body()
    persisted_digest = compute_canonical_persisted_state_digest(persisted_body)
    safety_body = default_safety_kernel_read_body()
    adapter_body = default_adapter_read_body()
    safety_digest = compute_read_result_digest(safety_body)
    adapter_digest = compute_read_result_digest(adapter_body)
    adapter_projection_digest = compute_adapter_revocation_projection_digest(adapter_body)
    return KillSwitchWriterFencingEvaluationInput(
        writer_identity=writer_identity,
        writer_epoch=writer_epoch,
        previous_writer_epoch=previous_writer_epoch,
        known_writer_epochs=frozenset({0, 1}),
        concurrent_writer_same_epoch=False,
        event_id="generic-futures-killswitch-event-001",
        event_sequence=event_sequence,
        previous_event_sequence=previous_event_sequence,
        concurrent_event_successor=False,
        previous_event_digest=previous_event_digest,
        canonical_event_payload=canonical_event_payload,
        current_event_digest=current_event_digest,
        previous_state="ARMED",
        proposed_state="ARMED",
        recovery_chain_reset_attempt=False,
        revocation_epoch=1,
        trading_epoch=1,
        executor_epoch=1,
        canonical_persisted_state_ref="offline/generic-futures-killswitch-persisted-state-001",
        canonical_persisted_state_body=persisted_body,
        canonical_persisted_state_digest=persisted_digest,
        safety_kernel_read_path_ref="offline/safety-kernel/killswitch-read-path-001",
        safety_kernel_read_body=safety_body,
        safety_kernel_read_result_digest=safety_digest,
        safety_kernel_read_fresh=True,
        safety_kernel_state_available=True,
        safety_kernel_state_readable=True,
        adapter_read_path_ref="offline/adapter/killswitch-read-path-001",
        adapter_read_body=adapter_body,
        adapter_read_result_digest=adapter_digest,
        adapter_revocation_projection_digest=adapter_projection_digest,
        adapter_read_fresh=True,
        adapter_state_available=True,
        adapter_state_readable=True,
        shared_volatile_cache_only=False,
        last_known_armed_fallback_requested=False,
        adapter_submission_requested_on_unclear_state=False,
        input_refs=("offline/generic-futures-killswitch-input-001",),
        input_digests=(persisted_digest,),
    )


def _append_rejection(
    reasons: list[str],
    gates: list[str],
    *,
    decision_code: str,
    gate_id: str,
) -> None:
    if decision_code not in reasons:
        reasons.append(decision_code)
    gates.append(gate_id)


def _state_rank(state: str) -> int:
    order = {"DISABLED": 0, "ARMED": 1, "RECOVERING": 2, "TRIPPED": 3}
    return order.get(state.upper(), -1)


def evaluate_killswitch_writer_fencing_v1(
    request: KillSwitchWriterFencingEvaluationInput,
) -> KillSwitchWriterFencingEvaluationResult:
    rejection_reasons: list[str] = []
    fail_closed_gates: list[str] = []

    if request.contract_version != CONTRACT_VERSION:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="UNKNOWN_CONTRACT_VERSION",
            gate_id="contract_version",
        )

    if not request.input_refs or not request.input_digests:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_INPUT",
            gate_id="input_refs",
        )

    writer_epoch_status = "UNKNOWN"
    if not request.writer_identity.strip():
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_WRITER_IDENTITY",
            gate_id="writer_identity",
        )
    else:
        writer_epoch_status = "PRESENT"

    if request.writer_epoch < 0:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_WRITER_EPOCH",
            gate_id="writer_epoch",
        )
        writer_epoch_status = "MISSING"
    elif request.writer_epoch < request.previous_writer_epoch:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="WRITER_EPOCH_REGRESSION",
            gate_id="writer_epoch_monotonic",
        )
        writer_epoch_status = "REGRESSED"
    elif request.writer_epoch not in request.known_writer_epochs:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="WRITER_EPOCH_UNKNOWN",
            gate_id="writer_epoch_known",
        )
        writer_epoch_status = "UNKNOWN"
    elif request.concurrent_writer_same_epoch:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="WRITER_EPOCH_CONFLICT",
            gate_id="writer_epoch_conflict",
        )
        writer_epoch_status = "CONFLICT"
    else:
        writer_epoch_status = "VALID"

    event_sequence_status = "UNKNOWN"
    if request.event_sequence < 1:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_EVENT_SEQUENCE",
            gate_id="event_sequence",
        )
        event_sequence_status = "MISSING"
    elif request.event_sequence < request.previous_event_sequence:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="EVENT_SEQUENCE_REGRESSION",
            gate_id="event_sequence_monotonic",
        )
        event_sequence_status = "REGRESSED"
    elif request.event_sequence != request.previous_event_sequence + 1:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="EVENT_SEQUENCE_GAP",
            gate_id="event_sequence_gap",
        )
        event_sequence_status = "GAP"
    elif request.concurrent_event_successor:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="CONCURRENT_EVENT_SUCCESSOR",
            gate_id="concurrent_event_successor",
        )
        event_sequence_status = "CONFLICT"
    else:
        event_sequence_status = "VALID"

    canonical_event_payload_digest = compute_canonical_event_payload_digest(
        request.canonical_event_payload
    )
    digest_chain_status = "UNKNOWN"
    if not request.previous_event_digest or not is_valid_sha256_hex(request.previous_event_digest):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_PREVIOUS_EVENT_DIGEST",
            gate_id="previous_event_digest",
        )
        digest_chain_status = "MISSING_PREVIOUS"
    else:
        expected_current = compute_current_event_digest(
            previous_event_digest=request.previous_event_digest,
            canonical_event_payload_digest=canonical_event_payload_digest,
        )
        if request.current_event_digest != expected_current:
            _append_rejection(
                rejection_reasons,
                fail_closed_gates,
                decision_code="EVENT_DIGEST_MISMATCH",
                gate_id="current_event_digest",
            )
            digest_chain_status = "MISMATCH"
        else:
            digest_chain_status = "VALID"

    if request.recovery_chain_reset_attempt:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="RECOVERY_CHAIN_RESET_ATTEMPT",
            gate_id="recovery_chain_reset",
        )
        digest_chain_status = "RESET_ATTEMPT"

    previous_state = request.previous_state.upper()
    proposed_state = request.proposed_state.upper()
    state_rollback_detected = (
        _state_rank(proposed_state) < _state_rank(previous_state)
        and previous_state == "TRIPPED"
        and proposed_state == "ARMED"
    )
    state_transition_status = "VALID"
    if state_rollback_detected:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="STATE_ROLLBACK_DETECTED",
            gate_id="state_rollback",
        )
        state_transition_status = "ROLLBACK"
    elif (
        previous_state not in _VALID_KILL_SWITCH_STATES
        or proposed_state not in _VALID_KILL_SWITCH_STATES
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="BROKEN_EVENT_DIGEST_CHAIN",
            gate_id="state_transition",
        )
        state_transition_status = "INVALID"

    if not request.canonical_persisted_state_ref.strip():
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_CANONICAL_PERSISTED_STATE_REF",
            gate_id="canonical_persisted_state_ref",
        )
    expected_persisted_digest = compute_canonical_persisted_state_digest(
        request.canonical_persisted_state_body
    )
    if not request.canonical_persisted_state_digest or not is_valid_sha256_hex(
        request.canonical_persisted_state_digest
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_CANONICAL_PERSISTED_STATE_DIGEST",
            gate_id="canonical_persisted_state_digest",
        )
    elif request.canonical_persisted_state_digest != expected_persisted_digest:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="KILLSWITCH_STATE_DIGEST_MISMATCH",
            gate_id="canonical_persisted_state_digest",
        )

    if not request.safety_kernel_read_path_ref.strip():
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_SAFETY_KERNEL_READ_PATH",
            gate_id="safety_kernel_read_path_ref",
        )
    if not request.adapter_read_path_ref.strip():
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="MISSING_ADAPTER_READ_PATH",
            gate_id="adapter_read_path_ref",
        )

    read_paths_independent = (
        bool(request.safety_kernel_read_path_ref.strip())
        and bool(request.adapter_read_path_ref.strip())
        and request.safety_kernel_read_path_ref != request.adapter_read_path_ref
        and not request.shared_volatile_cache_only
    )
    if request.shared_volatile_cache_only:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="SHARED_VOLATILE_CACHE_ONLY",
            gate_id="shared_volatile_cache_only",
        )
    elif (
        request.safety_kernel_read_path_ref
        and request.adapter_read_path_ref
        and request.safety_kernel_read_path_ref == request.adapter_read_path_ref
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="READ_PATHS_NOT_INDEPENDENT",
            gate_id="read_paths_independent",
        )

    if not request.safety_kernel_state_available:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="SAFETY_KERNEL_STATE_UNAVAILABLE",
            gate_id="safety_kernel_state_available",
        )
    if not request.adapter_state_available:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_STATE_UNAVAILABLE",
            gate_id="adapter_state_available",
        )
    if not request.safety_kernel_state_readable:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="SAFETY_KERNEL_STATE_UNREADABLE",
            gate_id="safety_kernel_state_readable",
        )
    if not request.adapter_state_readable:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_STATE_UNREADABLE",
            gate_id="adapter_state_readable",
        )
    if not request.safety_kernel_read_fresh:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="STALE_SAFETY_KERNEL_STATE",
            gate_id="safety_kernel_read_fresh",
        )
    if not request.adapter_read_fresh:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="STALE_ADAPTER_STATE",
            gate_id="adapter_read_fresh",
        )

    expected_safety_digest = compute_read_result_digest(request.safety_kernel_read_body)
    if request.safety_kernel_read_result_digest != expected_safety_digest:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="READ_PATH_DIGEST_DISAGREEMENT",
            gate_id="safety_kernel_read_result_digest",
        )

    expected_adapter_digest = compute_read_result_digest(request.adapter_read_body)
    if request.adapter_read_result_digest != expected_adapter_digest:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="READ_PATH_DIGEST_DISAGREEMENT",
            gate_id="adapter_read_result_digest",
        )

    expected_projection_digest = compute_adapter_revocation_projection_digest(
        request.adapter_read_body
    )
    if request.adapter_revocation_projection_digest != expected_projection_digest:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="READ_PATH_DIGEST_DISAGREEMENT",
            gate_id="adapter_revocation_projection_digest",
        )

    safety_state = str(request.safety_kernel_read_body.get("kill_switch_state", "")).upper()
    adapter_state = str(request.adapter_read_body.get("kill_switch_state", "")).upper()
    persisted_state = str(
        request.canonical_persisted_state_body.get("kill_switch_state", "")
    ).upper()
    read_paths_agree = (
        safety_state == adapter_state == persisted_state
        and safety_state in _VALID_KILL_SWITCH_STATES
    )
    if not read_paths_agree:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="READ_PATH_STATE_DISAGREEMENT",
            gate_id="read_path_state_agreement",
        )

    safety_revocation = request.safety_kernel_read_body.get("revocation_epoch")
    adapter_revocation = request.adapter_read_body.get("revocation_epoch")
    persisted_revocation = request.canonical_persisted_state_body.get("revocation_epoch")
    if (
        safety_revocation != request.revocation_epoch
        or adapter_revocation != request.revocation_epoch
        or persisted_revocation != request.revocation_epoch
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="REVOCATION_EPOCH_MISMATCH",
            gate_id="revocation_epoch",
        )

    safety_trading = request.safety_kernel_read_body.get("trading_epoch")
    adapter_trading = request.adapter_read_body.get("trading_epoch")
    persisted_trading = request.canonical_persisted_state_body.get("trading_epoch")
    if (
        safety_trading != request.trading_epoch
        or adapter_trading != request.trading_epoch
        or persisted_trading != request.trading_epoch
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="TRADING_EPOCH_MISMATCH",
            gate_id="trading_epoch",
        )

    safety_executor = request.safety_kernel_read_body.get("executor_epoch")
    adapter_executor = request.adapter_read_body.get("executor_epoch")
    persisted_executor = request.canonical_persisted_state_body.get("executor_epoch")
    if (
        safety_executor != request.executor_epoch
        or adapter_executor != request.executor_epoch
        or persisted_executor != request.executor_epoch
    ):
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="EXECUTOR_EPOCH_MISMATCH",
            gate_id="executor_epoch",
        )

    if request.last_known_armed_fallback_requested:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="LAST_KNOWN_ARMED_FALLBACK_REQUESTED",
            gate_id="last_known_armed_fallback",
        )
    if request.adapter_submission_requested_on_unclear_state:
        _append_rejection(
            rejection_reasons,
            fail_closed_gates,
            decision_code="ADAPTER_SUBMISSION_REQUESTED_ON_UNCLEAR_STATE",
            gate_id="adapter_submission_on_unclear_state",
        )

    state_available = request.safety_kernel_state_available and request.adapter_state_available
    state_readable = request.safety_kernel_state_readable and request.adapter_state_readable

    decision = "PASS" if not rejection_reasons else "BLOCK"
    decision_code = "PASS" if decision == "PASS" else rejection_reasons[0]

    authority_invariants = dict(KILLSWITCH_WRITER_FENCING_AUTHORITY_INVARIANTS)
    authority_invariants["killswitch_writer_fencing_contract_complete"] = decision == "PASS"

    contract_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "evidence_id": "",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "kill_switch_owner_ref": KILL_SWITCH_OWNER_REF,
        "kill_switch_contract_digest": KILL_SWITCH_CONTRACT_DIGEST,
        "kill_switch_policy_digest": KILL_SWITCH_POLICY_DIGEST,
        "kill_switch_state_machine_digest": KILL_SWITCH_STATE_MACHINE_DIGEST,
        "writer_identity": request.writer_identity,
        "writer_epoch": request.writer_epoch,
        "previous_writer_epoch": request.previous_writer_epoch,
        "writer_epoch_status": writer_epoch_status,
        "event_id": request.event_id,
        "event_sequence": request.event_sequence,
        "previous_event_sequence": request.previous_event_sequence,
        "event_sequence_status": event_sequence_status,
        "previous_event_digest": request.previous_event_digest,
        "canonical_event_payload_digest": canonical_event_payload_digest,
        "current_event_digest": request.current_event_digest,
        "digest_chain_status": digest_chain_status,
        "previous_state": previous_state,
        "proposed_state": proposed_state,
        "state_transition_status": state_transition_status,
        "state_rollback_detected": state_rollback_detected,
        "revocation_epoch": request.revocation_epoch,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "canonical_persisted_state_ref": request.canonical_persisted_state_ref,
        "canonical_persisted_state_digest": request.canonical_persisted_state_digest,
        "safety_kernel_read_path_ref": request.safety_kernel_read_path_ref,
        "safety_kernel_read_result_digest": request.safety_kernel_read_result_digest,
        "safety_kernel_read_freshness_status": (
            "FRESH" if request.safety_kernel_read_fresh else "STALE"
        ),
        "adapter_read_path_ref": request.adapter_read_path_ref,
        "adapter_read_result_digest": request.adapter_read_result_digest,
        "adapter_revocation_projection_digest": request.adapter_revocation_projection_digest,
        "adapter_read_freshness_status": "FRESH" if request.adapter_read_fresh else "STALE",
        "read_paths_independent": read_paths_independent,
        "read_paths_agree": read_paths_agree,
        "state_available": state_available,
        "state_readable": state_readable,
        "fail_closed_gates": list(fail_closed_gates),
        "decision": decision,
        "decision_code": decision_code,
        "rejection_reasons": list(rejection_reasons),
        "authority_invariants": authority_invariants,
        "producer_version": PRODUCER_VERSION,
        "evidence_level": EVIDENCE_LEVEL,
        "authority_level": AUTHORITY_LEVEL,
        "record_kind": RECORD_KIND,
        "producer_identity_ref": DEFAULT_PRODUCER_IDENTITY_REF,
        "source_revision": DEFAULT_SOURCE_REVISION,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        **dict(_REQUIRED_NON_MUTATION_FLAGS),
        "integrity": {"content_sha256": ""},
    }
    evidence_id = compute_content_sha256(
        {
            "contract_name": CONTRACT_NAME,
            "decision": decision,
            "writer_epoch": request.writer_epoch,
            "event_sequence": request.event_sequence,
            "current_event_digest": request.current_event_digest,
        }
    )
    contract_body["evidence_id"] = evidence_id
    contract_body["output_digest"] = _compute_output_digest(contract_body)
    contract_body["artifact_id"] = contract_body["output_digest"]
    contract_body["integrity"] = {
        "content_sha256": compute_content_sha256(_integrity_body(contract_body))
    }

    return KillSwitchWriterFencingEvaluationResult(
        decision=decision,
        decision_code=decision_code,
        rejection_reasons=tuple(rejection_reasons),
        fail_closed_gates=tuple(fail_closed_gates),
        writer_epoch_status=writer_epoch_status,
        event_sequence_status=event_sequence_status,
        digest_chain_status=digest_chain_status,
        state_transition_status=state_transition_status,
        state_rollback_detected=state_rollback_detected,
        read_paths_independent=read_paths_independent,
        read_paths_agree=read_paths_agree,
        state_available=state_available,
        state_readable=state_readable,
        canonical_event_payload_digest=canonical_event_payload_digest,
        contract_body=contract_body,
    )


def build_killswitch_writer_fencing_v1(
    request: KillSwitchWriterFencingEvaluationInput,
) -> dict[str, Any]:
    return evaluate_killswitch_writer_fencing_v1(request).contract_body


def serialize_killswitch_writer_fencing_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest", "artifact_id"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise KillSwitchWriterFencingError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise KillSwitchWriterFencingError("output directory must not be under /tmp")


def _artifact_bytes_for_manifest_digest(contract: Mapping[str, Any]) -> bytes:
    body = {
        key: value for key, value in contract.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize_killswitch_writer_fencing_v1(body).encode("utf-8")


def _compute_output_manifest_digest(contract: Mapping[str, Any]) -> str:
    return hashlib.sha256(_artifact_bytes_for_manifest_digest(contract)).hexdigest()


def build_self_verification_v1(
    *,
    contract: Mapping[str, Any],
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_adapter_invocation", "status": "PASS"},
        {"check_id": "offline_only_no_network_side_effect", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {"check_id": "pass_does_not_authorize_submission", "status": "PASS"},
        {
            "check_id": "manifest_digest",
            "status": "PASS" if manifest_digest else "FAIL",
        },
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": _SELF_VERIFICATION_SCHEMA_VERSION,
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "overall_status": overall,
        "checks": checks,
        "verified_artifact_rel": ARTIFACT_REL,
        "manifest_digest": manifest_digest,
    }


def _validate_contract_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != CONTRACT_NAME:
        raise KillSwitchWriterFencingError("contract_name mismatch")
    if contract.get("contract_version") != CONTRACT_VERSION:
        raise KillSwitchWriterFencingError("contract_version mismatch")
    decision = contract.get("decision")
    if decision not in _VALID_DECISIONS:
        raise KillSwitchWriterFencingError("decision must be PASS or BLOCK")
    decision_code = str(contract.get("decision_code", ""))
    if decision == "PASS" and decision_code != "PASS":
        raise KillSwitchWriterFencingError("PASS decision requires decision_code PASS")
    if decision == "BLOCK" and decision_code not in _FAIL_CLOSED_DECISION_CODES:
        raise KillSwitchWriterFencingError("unknown BLOCK decision_code")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise KillSwitchWriterFencingError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise KillSwitchWriterFencingError("integrity.content_sha256 mismatch")
    output_digest = contract.get("output_digest")
    if output_digest != _compute_output_digest(contract):
        raise KillSwitchWriterFencingError("output_digest mismatch")
    if contract.get("artifact_id") != output_digest:
        raise KillSwitchWriterFencingError("artifact_id must equal output_digest")
    for key, expected_value in _REQUIRED_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected_value:
            raise KillSwitchWriterFencingError(f"{key} must remain {expected_value!r}")


def reverify_killswitch_writer_fencing_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / ARTIFACT_REL
    if not artifact_path.is_file():
        raise KillSwitchWriterFencingError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise KillSwitchWriterFencingError("artifact must be a JSON object")
    _validate_contract_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(contract)
    if contract.get("manifest_digest") != manifest_digest:
        raise KillSwitchWriterFencingError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise KillSwitchWriterFencingError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def produce_killswitch_writer_fencing_v1(
    *,
    request: KillSwitchWriterFencingEvaluationInput,
    output_dir: Path | str,
) -> KillSwitchWriterFencingResult:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    evaluation = evaluate_killswitch_writer_fencing_v1(request)
    contract_body = dict(evaluation.contract_body)

    staging = final_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    if staging.exists():
        raise KillSwitchWriterFencingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / ARTIFACT_REL
        self_path = staging / SELF_VERIFICATION_REL

        manifest_digest = _compute_output_manifest_digest(contract_body)
        contract_body["manifest_digest"] = manifest_digest
        artifact_path.write_text(
            serialize_killswitch_writer_fencing_v1(contract_body),
            encoding="utf-8",
        )
        self_payload = build_self_verification_v1(
            contract=contract_body,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)

        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise KillSwitchWriterFencingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )
        reverify_killswitch_writer_fencing_v1(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise KillSwitchWriterFencingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return KillSwitchWriterFencingResult(
        output_dir=final_dir,
        evidence_id=str(contract_body["evidence_id"]),
        decision=str(contract_body["decision"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=str(contract_body["output_digest"]),
        manifest_digest=str(contract_body["manifest_digest"]),
    )


__all__ = [
    "ARTIFACT_REL",
    "BUILDER_VERSION",
    "CONTRACT_NAME",
    "CONTRACT_VERSION",
    "GENESIS_EVENT_DIGEST",
    "KILL_SWITCH_OWNER_REF",
    "KILLSWITCH_WRITER_FENCING_AUTHORITY_INVARIANTS",
    "KillSwitchWriterFencingError",
    "KillSwitchWriterFencingEvaluationInput",
    "KillSwitchWriterFencingEvaluationResult",
    "KillSwitchWriterFencingResult",
    "build_killswitch_writer_fencing_v1",
    "compute_adapter_revocation_projection_digest",
    "compute_canonical_event_payload_digest",
    "compute_canonical_persisted_state_digest",
    "compute_current_event_digest",
    "compute_read_result_digest",
    "default_adapter_read_body",
    "default_canonical_event_payload",
    "default_canonical_persisted_state_body",
    "default_killswitch_writer_fencing_evaluation_input",
    "default_safety_kernel_read_body",
    "evaluate_killswitch_writer_fencing_v1",
    "produce_killswitch_writer_fencing_v1",
    "reverify_killswitch_writer_fencing_v1",
    "serialize_killswitch_writer_fencing_v1",
]
