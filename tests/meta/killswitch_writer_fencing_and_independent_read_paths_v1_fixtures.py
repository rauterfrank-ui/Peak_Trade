"""Fixtures for killswitch_writer_fencing_and_independent_read_paths_v1 tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KillSwitchWriterFencingEvaluationInput,
    compute_adapter_revocation_projection_digest,
    compute_canonical_event_payload_digest,
    compute_canonical_persisted_state_digest,
    compute_current_event_digest,
    compute_read_result_digest,
    default_adapter_read_body,
    default_canonical_event_payload,
    default_canonical_persisted_state_body,
    default_killswitch_writer_fencing_evaluation_input,
    default_safety_kernel_read_body,
    produce_killswitch_writer_fencing_v1,
)


@dataclass(frozen=True)
class KillSwitchWriterFencingFixtureBundle:
    request: KillSwitchWriterFencingEvaluationInput
    bundle_dir: Path | None = None


def build_valid_killswitch_writer_fencing_input(
    **overrides: object,
) -> KillSwitchWriterFencingEvaluationInput:
    base = default_killswitch_writer_fencing_evaluation_input()
    if not overrides:
        return base

    data = {
        "writer_identity": base.writer_identity,
        "writer_epoch": base.writer_epoch,
        "previous_writer_epoch": base.previous_writer_epoch,
        "known_writer_epochs": base.known_writer_epochs,
        "concurrent_writer_same_epoch": base.concurrent_writer_same_epoch,
        "event_id": base.event_id,
        "event_sequence": base.event_sequence,
        "previous_event_sequence": base.previous_event_sequence,
        "concurrent_event_successor": base.concurrent_event_successor,
        "previous_event_digest": base.previous_event_digest,
        "canonical_event_payload": dict(base.canonical_event_payload),
        "current_event_digest": base.current_event_digest,
        "previous_state": base.previous_state,
        "proposed_state": base.proposed_state,
        "recovery_chain_reset_attempt": base.recovery_chain_reset_attempt,
        "revocation_epoch": base.revocation_epoch,
        "trading_epoch": base.trading_epoch,
        "executor_epoch": base.executor_epoch,
        "canonical_persisted_state_ref": base.canonical_persisted_state_ref,
        "canonical_persisted_state_body": dict(base.canonical_persisted_state_body),
        "canonical_persisted_state_digest": base.canonical_persisted_state_digest,
        "safety_kernel_read_path_ref": base.safety_kernel_read_path_ref,
        "safety_kernel_read_body": dict(base.safety_kernel_read_body),
        "safety_kernel_read_result_digest": base.safety_kernel_read_result_digest,
        "safety_kernel_read_fresh": base.safety_kernel_read_fresh,
        "safety_kernel_state_available": base.safety_kernel_state_available,
        "safety_kernel_state_readable": base.safety_kernel_state_readable,
        "adapter_read_path_ref": base.adapter_read_path_ref,
        "adapter_read_body": dict(base.adapter_read_body),
        "adapter_read_result_digest": base.adapter_read_result_digest,
        "adapter_revocation_projection_digest": base.adapter_revocation_projection_digest,
        "adapter_read_fresh": base.adapter_read_fresh,
        "adapter_state_available": base.adapter_state_available,
        "adapter_state_readable": base.adapter_state_readable,
        "shared_volatile_cache_only": base.shared_volatile_cache_only,
        "last_known_armed_fallback_requested": base.last_known_armed_fallback_requested,
        "adapter_submission_requested_on_unclear_state": (
            base.adapter_submission_requested_on_unclear_state
        ),
        "input_refs": base.input_refs,
        "input_digests": base.input_digests,
        "contract_version": base.contract_version,
        "created_at": base.created_at,
        "builder_version": base.builder_version,
    }
    data.update(overrides)

    if "canonical_event_payload" in overrides and "current_event_digest" not in overrides:
        payload = dict(data["canonical_event_payload"])
        payload_digest = compute_canonical_event_payload_digest(payload)
        data["canonical_event_payload"] = payload
        data["current_event_digest"] = compute_current_event_digest(
            previous_event_digest=str(data["previous_event_digest"]),
            canonical_event_payload_digest=payload_digest,
        )
    if "canonical_persisted_state_body" in overrides and (
        "canonical_persisted_state_digest" not in overrides
    ):
        body = dict(data["canonical_persisted_state_body"])
        data["canonical_persisted_state_body"] = body
        data["canonical_persisted_state_digest"] = compute_canonical_persisted_state_digest(body)
    if (
        "safety_kernel_read_body" in overrides
        and "safety_kernel_read_result_digest" not in overrides
    ):
        body = dict(data["safety_kernel_read_body"])
        data["safety_kernel_read_body"] = body
        data["safety_kernel_read_result_digest"] = compute_read_result_digest(body)
    if "adapter_read_body" in overrides and "adapter_read_result_digest" not in overrides:
        body = dict(data["adapter_read_body"])
        data["adapter_read_body"] = body
        data["adapter_read_result_digest"] = compute_read_result_digest(body)
        data["adapter_revocation_projection_digest"] = compute_adapter_revocation_projection_digest(
            body
        )

    return KillSwitchWriterFencingEvaluationInput(**data)


def build_monotonic_writer_epoch_change_input() -> KillSwitchWriterFencingEvaluationInput:
    base = default_killswitch_writer_fencing_evaluation_input()
    payload = default_canonical_event_payload(
        writer_identity=base.writer_identity,
        writer_epoch=2,
        event_sequence=2,
        proposed_state="ARMED",
    )
    payload_digest = compute_canonical_event_payload_digest(payload)
    previous_event_digest = base.current_event_digest
    return build_valid_killswitch_writer_fencing_input(
        writer_epoch=2,
        previous_writer_epoch=1,
        known_writer_epochs=frozenset({0, 1, 2}),
        event_sequence=2,
        previous_event_sequence=1,
        canonical_event_payload=payload,
        current_event_digest=compute_current_event_digest(
            previous_event_digest=previous_event_digest,
            canonical_event_payload_digest=payload_digest,
        ),
        previous_event_digest=previous_event_digest,
    )


def build_recovery_continuation_input() -> KillSwitchWriterFencingEvaluationInput:
    base = build_monotonic_writer_epoch_change_input()
    payload = default_canonical_event_payload(
        writer_identity=base.writer_identity,
        writer_epoch=2,
        event_sequence=3,
        proposed_state="RECOVERING",
    )
    payload_digest = compute_canonical_event_payload_digest(payload)
    previous_event_digest = base.current_event_digest
    persisted_body = default_canonical_persisted_state_body(kill_switch_state="RECOVERING")
    safety_body = default_safety_kernel_read_body(kill_switch_state="RECOVERING")
    adapter_body = default_adapter_read_body(kill_switch_state="RECOVERING")
    return build_valid_killswitch_writer_fencing_input(
        writer_epoch=2,
        previous_writer_epoch=2,
        known_writer_epochs=frozenset({0, 1, 2}),
        event_sequence=3,
        previous_event_sequence=2,
        previous_state="TRIPPED",
        proposed_state="RECOVERING",
        canonical_event_payload=payload,
        previous_event_digest=previous_event_digest,
        current_event_digest=compute_current_event_digest(
            previous_event_digest=previous_event_digest,
            canonical_event_payload_digest=payload_digest,
        ),
        canonical_persisted_state_body=persisted_body,
        safety_kernel_read_body=safety_body,
        adapter_read_body=adapter_body,
    )


def produce_killswitch_writer_fencing_fixture(
    tmp_path: Path,
    durable_root: Path,
    *,
    produce_output: bool = True,
    bundle_name: str = "killswitch_writer_fencing",
    request: KillSwitchWriterFencingEvaluationInput | None = None,
) -> KillSwitchWriterFencingFixtureBundle:
    evaluation_request = request or default_killswitch_writer_fencing_evaluation_input()
    bundle_dir: Path | None = None
    if produce_output:
        bundle_dir = durable_root / bundle_name
        produce_killswitch_writer_fencing_v1(
            request=evaluation_request,
            output_dir=bundle_dir,
        )
    return KillSwitchWriterFencingFixtureBundle(
        request=evaluation_request,
        bundle_dir=bundle_dir,
    )
