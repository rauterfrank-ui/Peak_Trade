"""Offline Master V2 replay → six-node validation graph binding proof v0."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    DurableRunPrimaryEvidenceCompletionIntegrationInput,
    _build_admission_presentation_lifecycle_input_from_completion,
    default_minimal_completion_integration_input,
    default_minimal_completion_proof_chain,
    evaluate_durable_run_primary_evidence_completion_integration,
)
from src.ops.bounded_futures_testnet_handoff_staleness_revocation_recovery_boundary_contract_v0 import (
    evaluate_handoff_staleness_revocation_recovery_boundary,
)
from src.ops.bounded_futures_testnet_operator_closure_lifecycle_integration_contract_v0 import (
    evaluate_operator_closure_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_operator_review_admission_presentation_lifecycle_integration_contract_v0 import (
    evaluate_operator_review_admission_presentation_lifecycle_integration,
)
from src.ops.bounded_futures_testnet_operator_review_chain_durable_evidence_traceability_boundary_contract_v0 import (
    evaluate_durable_evidence_traceability_boundary,
)
from src.ops.bounded_futures_testnet_reconciliation_review_lifecycle_integration_contract_v0 import (
    evaluate_reconciliation_review_lifecycle_integration,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_ORDER,
    execute_proof_binding_validation_graph,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.event_stream import (
    MasterV2StateEventStreamProofBinding,
    MasterV2StateEventStreamValidationInput,
    default_minimal_master_v2_state_event_proof_binding,
    evaluate_glb019_event_stream_validation,
    evaluate_master_v2_state_event_stream_validation,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    build_default_bull_bear_bull_scenario_ticks,
    build_master_v2_state_event_stream_validation_input_from_replay,
    compute_master_v2_replay_state_event_projection_digest,
    run_offline_double_play_scenario_replay_v0,
)

OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_LAYER_VERSION = "v0"
OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER = (
    "ops.offline_master_v2_replay_six_node_validation_graph_binding_v0"
)
OFFLINE_END_TO_END_REPLAY_PROOF_BINDING_LAYER_VERSION = (
    OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_LAYER_VERSION
)

PROOF_CLASSIFICATION_FULL_E2E_BOUND = "FULL_E2E_BOUND"
PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED = "REPLAY_FAIL_CLOSED"
PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED = "PROJECTION_FAIL_CLOSED"
PROOF_CLASSIFICATION_INTEGRATION_FAIL_CLOSED = "INTEGRATION_FAIL_CLOSED"
PROOF_CLASSIFICATION_GRAPH_FAIL_CLOSED = "GRAPH_FAIL_CLOSED"


@dataclass(frozen=True)
class OfflineReplaySixNodeValidationGraphBindingResultV0:
    layer_version: str
    binding_pass: bool
    replay_pass: bool
    projection_pass: bool
    integration_pass: bool
    six_node_graph_pass: bool
    completed_validators: tuple[str, ...]
    fail_reasons: tuple[str, ...]
    orders_total: int
    cancels_total: int
    fills_total: int
    positions_opened_total: int
    dashboard_display_projection_digest: str | None = None
    state_event_projection_digest: str | None = None
    master_v2_state_event_stream_identity: str | None = None
    evidence_chain_profile: str | None = None
    proof_classification: str = PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED
    event_stream_non_authorizing: bool = True

    def to_machine_lines(self) -> dict[str, str | bool | int]:
        return {
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_PASS": self.binding_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_REPLAY_PASS": self.replay_pass,
            "OFFLINE_END_TO_END_REPLAY_PROJECTION_PASS": self.projection_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_INTEGRATION_PASS": self.integration_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_SIX_NODE_GRAPH_PASS": (
                self.six_node_graph_pass
            ),
            "OFFLINE_END_TO_END_REPLAY_PROOF_CLASSIFICATION": self.proof_classification,
            "OFFLINE_END_TO_END_EVENT_STREAM_NON_AUTHORIZING": self.event_stream_non_authorizing,
            "ORDERS_TOTAL": self.orders_total,
            "CANCELS_TOTAL": self.cancels_total,
            "FILLS_TOTAL": self.fills_total,
            "POSITIONS_OPENED_TOTAL": self.positions_opened_total,
            "DASHBOARD_DISPLAY_PROJECTION_DIGEST": self.dashboard_display_projection_digest or "",
            "STATE_EVENT_PROJECTION_DIGEST": self.state_event_projection_digest or "",
            "MASTER_V2_STATE_EVENT_STREAM_IDENTITY": self.master_v2_state_event_stream_identity
            or "",
        }


def build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    *,
    source_revision: str,
    completion_identity_digest: str,
    manifest_identity_digest: str,
    run_identity_digest: str,
    correlation_id: str,
) -> tuple[
    MasterV2StateEventStreamValidationInput | None,
    MasterV2StateEventStreamProofBinding | None,
    str | None,
    tuple[str, ...],
]:
    """Project replay ticks into canonical Master-V2 state event stream proof surfaces."""
    validation_input, build_failures = (
        build_master_v2_state_event_stream_validation_input_from_replay(
            replay_result=replay_result,
            correlation_id=correlation_id,
            completion_identity_digest=completion_identity_digest,
            manifest_identity_digest=manifest_identity_digest,
            run_identity_digest=run_identity_digest,
            source_revision=source_revision,
        )
    )
    if validation_input is None:
        return None, None, None, build_failures

    validation_result = evaluate_master_v2_state_event_stream_validation(validation_input)
    if not validation_result.get("validation_pass"):
        return (
            validation_input,
            None,
            None,
            tuple(build_failures) + tuple(validation_result.get("fail_reasons", ())),
        )

    proof_binding = default_minimal_master_v2_state_event_proof_binding(
        validation_input,
        validation_result,
    )
    projection_digest = compute_master_v2_replay_state_event_projection_digest(
        events=validation_input.events,
        evidence_chain_profile=validation_input.evidence_chain_profile,
        correlation_id=correlation_id,
    )
    return validation_input, proof_binding, projection_digest, ()


def build_completion_integration_input_from_offline_replay_result(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> DurableRunPrimaryEvidenceCompletionIntegrationInput:
    """Wire canonical replay output into the existing completion integration input contract."""
    binding = replay_result.master_v2_decision_state_digest_binding
    if binding is None:
        raise ValueError("replay_result.master_v2_decision_state_digest_binding is required")
    base = default_minimal_completion_integration_input()
    binding_aligned = replace(binding, source_revision=base.source_revision)
    glb019_input = base.glb019_event_stream_validation_input
    (
        master_v2_validation_input,
        master_v2_proof,
        _projection_digest,
        projection_failures,
    ) = build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result(
        replay_result,
        source_revision=base.source_revision,
        completion_identity_digest=glb019_input.completion_identity_digest,
        manifest_identity_digest=glb019_input.manifest_identity_digest,
        run_identity_digest=glb019_input.run_identity_digest,
        correlation_id=glb019_input.correlation_id,
    )
    if master_v2_validation_input is None or master_v2_proof is None:
        reasons = projection_failures or ("master_v2_state_event_stream_binding required",)
        raise ValueError("; ".join(reasons))

    with_binding = replace(
        base,
        master_v2_decision_state_digest_binding=binding_aligned,
        master_v2_state_event_stream_validation_input=master_v2_validation_input,
        master_v2_state_event_stream_proof=master_v2_proof,
    )
    chain = default_minimal_completion_proof_chain(with_binding)
    return replace(with_binding, completion_proof_chain=chain)


def build_validation_context_from_completion_integration_input(
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> ValidationContext:
    """Build the graph ValidationContext using the same evaluated PE surfaces as completion."""
    pe31_result = evaluate_reconciliation_review_lifecycle_integration(
        integration_input.pe31_reconciliation_review_integration_input
    )
    pe35_result = evaluate_handoff_staleness_revocation_recovery_boundary(
        integration_input.pe35_handoff_staleness_revocation_recovery_boundary_input
    )
    pe37_result = evaluate_durable_evidence_traceability_boundary(
        integration_input.pe37_traceability_boundary_input
    )
    admission_input = _build_admission_presentation_lifecycle_input_from_completion(
        integration_input
    )
    admission_result = evaluate_operator_review_admission_presentation_lifecycle_integration(
        admission_input
    )
    pe25_result = evaluate_operator_closure_lifecycle_integration(
        integration_input.pe25_closure_integration_input
    )
    glb019_result = evaluate_glb019_event_stream_validation(
        integration_input.glb019_event_stream_validation_input
    )
    return ValidationContext(
        integration_input=integration_input,
        pe31_result=pe31_result,
        pe35_result=pe35_result,
        pe37_result=pe37_result,
        pe25_result=pe25_result,
        admission_result=admission_result,
        glb019_result=glb019_result,
    )


def verify_dashboard_display_projection_digest_six_node_evidence(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input: DurableRunPrimaryEvidenceCompletionIntegrationInput,
) -> tuple[str | None, list[str]]:
    """Fail-closed verification that replay, binding, and completion chain share one digest."""
    fail_reasons: list[str] = []
    prefix = "dashboard_display_projection_digest"
    replay_digest = replay_result.dashboard_display_projection_digest
    binding = replay_result.master_v2_decision_state_digest_binding
    chain = integration_input.completion_proof_chain

    if not replay_digest:
        fail_reasons.append(f"{prefix} missing from replay result")
        return None, fail_reasons

    binding_digest = binding.dashboard_display_projection_digest if binding else None
    chain_digest = (
        chain.completion_referenced_dashboard_display_projection_digest if chain else None
    )

    if not binding_digest:
        fail_reasons.append(f"{prefix} missing from decision state binding")
    if not chain_digest:
        fail_reasons.append(f"{prefix} missing from completion proof chain")
    if binding_digest and replay_digest != binding_digest:
        fail_reasons.append(f"{prefix} drift: replay vs decision state binding")
    if chain_digest and binding_digest and chain_digest != binding_digest:
        fail_reasons.append(f"{prefix} drift: completion proof chain vs decision state binding")
    if chain_digest and replay_digest != chain_digest:
        fail_reasons.append(f"{prefix} drift: replay vs completion proof chain")

    if fail_reasons:
        return None, fail_reasons
    return chain_digest, []


def prove_offline_replay_six_node_validation_graph_binding_v0(
    replay_input: OfflineDoublePlayScenarioReplayInputV0 | None = None,
) -> OfflineReplaySixNodeValidationGraphBindingResultV0:
    """Run replay and prove fail-closed pass through the full six-node validation graph."""
    fail_reasons: list[str] = []
    resolved_input = replay_input or OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=build_default_bull_bear_bull_scenario_ticks(),
        source_revision="offline-replay-six-node-graph-binding-v0",
    )
    replay_result = run_offline_double_play_scenario_replay_v0(resolved_input)
    if not replay_result.replay_pass:
        fail_reasons.extend(replay_result.fail_reasons)
        return _binding_result(
            replay_result=replay_result,
            projection_pass=False,
            integration_pass=False,
            six_node_graph_pass=False,
            completed_validators=(),
            fail_reasons=fail_reasons,
            proof_classification=PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
        )

    base = default_minimal_completion_integration_input()
    glb019_input = base.glb019_event_stream_validation_input
    (
        master_v2_validation_input,
        master_v2_proof,
        projection_digest,
        projection_failures,
    ) = build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result(
        replay_result,
        source_revision=base.source_revision,
        completion_identity_digest=glb019_input.completion_identity_digest,
        manifest_identity_digest=glb019_input.manifest_identity_digest,
        run_identity_digest=glb019_input.run_identity_digest,
        correlation_id=glb019_input.correlation_id,
    )
    projection_pass = master_v2_validation_input is not None and master_v2_proof is not None
    evidence_chain_profile = (
        master_v2_validation_input.evidence_chain_profile if master_v2_validation_input else None
    )
    master_v2_state_event_stream_identity = None
    event_stream_non_authorizing = True
    if projection_failures:
        fail_reasons.extend(projection_failures)
    if not projection_pass:
        return _binding_result(
            replay_result=replay_result,
            projection_pass=False,
            integration_pass=False,
            six_node_graph_pass=False,
            completed_validators=(),
            fail_reasons=fail_reasons,
            proof_classification=PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
            evidence_chain_profile=evidence_chain_profile,
            state_event_projection_digest=projection_digest,
        )

    assert master_v2_validation_input is not None
    assert master_v2_proof is not None
    master_v2_state_event_stream_identity = master_v2_proof.state_event_stream_identity
    event_stream_non_authorizing = master_v2_proof.event_stream_non_authorizing

    try:
        integration_input = build_completion_integration_input_from_offline_replay_result(
            replay_result
        )
    except ValueError as exc:
        fail_reasons.append(str(exc))
        return _binding_result(
            replay_result=replay_result,
            projection_pass=False,
            integration_pass=False,
            six_node_graph_pass=False,
            completed_validators=(),
            fail_reasons=fail_reasons,
            proof_classification=PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
            evidence_chain_profile=evidence_chain_profile,
            state_event_projection_digest=projection_digest,
            master_v2_state_event_stream_identity=master_v2_state_event_stream_identity,
            event_stream_non_authorizing=event_stream_non_authorizing,
        )

    display_digest, display_digest_reasons = (
        verify_dashboard_display_projection_digest_six_node_evidence(
            replay_result,
            integration_input,
        )
    )
    if display_digest_reasons:
        fail_reasons.extend(display_digest_reasons)

    integration_result: dict[str, Any] = (
        evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    )
    integration_pass = bool(integration_result.get("integration_pass"))
    if not integration_pass:
        fail_reasons.extend(integration_result.get("fail_reasons", ()))

    context = build_validation_context_from_completion_integration_input(integration_input)
    graph_result = execute_proof_binding_validation_graph(context)
    six_node_graph_pass = not graph_result.fail_reasons
    if graph_result.fail_reasons:
        fail_reasons.extend(graph_result.fail_reasons)

    completed = tuple(
        node for node in PROOF_BINDING_VALIDATION_ORDER if node in context.completed_validators
    )
    if six_node_graph_pass and completed != PROOF_BINDING_VALIDATION_ORDER:
        fail_reasons.append(f"six_node_graph: incomplete validator completion order={completed!r}")
        six_node_graph_pass = False

    binding_pass = (
        replay_result.replay_pass
        and projection_pass
        and integration_pass
        and six_node_graph_pass
        and not fail_reasons
    )
    proof_classification = PROOF_CLASSIFICATION_FULL_E2E_BOUND
    if not binding_pass:
        if not integration_pass:
            proof_classification = PROOF_CLASSIFICATION_INTEGRATION_FAIL_CLOSED
        elif not six_node_graph_pass:
            proof_classification = PROOF_CLASSIFICATION_GRAPH_FAIL_CLOSED

    return _binding_result(
        replay_result=replay_result,
        projection_pass=projection_pass,
        integration_pass=integration_pass,
        six_node_graph_pass=six_node_graph_pass,
        completed_validators=completed,
        fail_reasons=fail_reasons,
        binding_pass=binding_pass,
        dashboard_display_projection_digest=display_digest,
        state_event_projection_digest=projection_digest,
        master_v2_state_event_stream_identity=master_v2_state_event_stream_identity,
        evidence_chain_profile=evidence_chain_profile,
        proof_classification=proof_classification,
        event_stream_non_authorizing=event_stream_non_authorizing,
    )


def _binding_result(
    *,
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    projection_pass: bool,
    integration_pass: bool,
    six_node_graph_pass: bool,
    completed_validators: tuple[str, ...],
    fail_reasons: list[str],
    binding_pass: bool | None = None,
    dashboard_display_projection_digest: str | None = None,
    state_event_projection_digest: str | None = None,
    master_v2_state_event_stream_identity: str | None = None,
    evidence_chain_profile: str | None = None,
    proof_classification: str = PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
    event_stream_non_authorizing: bool = True,
) -> OfflineReplaySixNodeValidationGraphBindingResultV0:
    summary = replay_result.summary
    resolved_binding_pass = (
        binding_pass
        if binding_pass is not None
        else replay_result.replay_pass
        and projection_pass
        and integration_pass
        and six_node_graph_pass
        and not fail_reasons
    )
    return OfflineReplaySixNodeValidationGraphBindingResultV0(
        layer_version=OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_LAYER_VERSION,
        binding_pass=resolved_binding_pass,
        replay_pass=replay_result.replay_pass,
        projection_pass=projection_pass,
        integration_pass=integration_pass,
        six_node_graph_pass=six_node_graph_pass,
        completed_validators=completed_validators,
        fail_reasons=tuple(fail_reasons),
        orders_total=summary.orders_total,
        cancels_total=summary.cancels_total,
        fills_total=summary.fills_total,
        positions_opened_total=summary.positions_opened_total,
        dashboard_display_projection_digest=dashboard_display_projection_digest,
        state_event_projection_digest=state_event_projection_digest,
        master_v2_state_event_stream_identity=master_v2_state_event_stream_identity,
        evidence_chain_profile=evidence_chain_profile,
        proof_classification=proof_classification,
        event_stream_non_authorizing=event_stream_non_authorizing,
    )
