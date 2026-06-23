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
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)

OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_LAYER_VERSION = "v0"
OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_OWNER = (
    "ops.offline_master_v2_replay_six_node_validation_graph_binding_v0"
)


@dataclass(frozen=True)
class OfflineReplaySixNodeValidationGraphBindingResultV0:
    layer_version: str
    binding_pass: bool
    replay_pass: bool
    integration_pass: bool
    six_node_graph_pass: bool
    completed_validators: tuple[str, ...]
    fail_reasons: tuple[str, ...]
    orders_total: int
    cancels_total: int
    fills_total: int
    positions_opened_total: int
    dashboard_display_projection_digest: str | None = None

    def to_machine_lines(self) -> dict[str, str | bool | int]:
        return {
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_PASS": self.binding_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_REPLAY_PASS": self.replay_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_INTEGRATION_PASS": self.integration_pass,
            "OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_SIX_NODE_GRAPH_PASS": (
                self.six_node_graph_pass
            ),
            "ORDERS_TOTAL": self.orders_total,
            "CANCELS_TOTAL": self.cancels_total,
            "FILLS_TOTAL": self.fills_total,
            "POSITIONS_OPENED_TOTAL": self.positions_opened_total,
            "DASHBOARD_DISPLAY_PROJECTION_DIGEST": self.dashboard_display_projection_digest or "",
        }


def build_completion_integration_input_from_offline_replay_result(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> DurableRunPrimaryEvidenceCompletionIntegrationInput:
    """Wire canonical replay output into the existing completion integration input contract."""
    binding = replay_result.master_v2_decision_state_digest_binding
    if binding is None:
        raise ValueError("replay_result.master_v2_decision_state_digest_binding is required")
    base = default_minimal_completion_integration_input()
    binding_aligned = replace(binding, source_revision=base.source_revision)
    with_binding = replace(
        base,
        master_v2_decision_state_digest_binding=binding_aligned,
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
    return ValidationContext(
        integration_input=integration_input,
        pe31_result=pe31_result,
        pe35_result=pe35_result,
        pe37_result=pe37_result,
        pe25_result=pe25_result,
        admission_result=admission_result,
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
            integration_pass=False,
            six_node_graph_pass=False,
            completed_validators=(),
            fail_reasons=fail_reasons,
        )

    integration_input = build_completion_integration_input_from_offline_replay_result(replay_result)
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
        replay_result.replay_pass and integration_pass and six_node_graph_pass and not fail_reasons
    )
    return _binding_result(
        replay_result=replay_result,
        integration_pass=integration_pass,
        six_node_graph_pass=six_node_graph_pass,
        completed_validators=completed,
        fail_reasons=fail_reasons,
        binding_pass=binding_pass,
        dashboard_display_projection_digest=display_digest,
    )


def _binding_result(
    *,
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_pass: bool,
    six_node_graph_pass: bool,
    completed_validators: tuple[str, ...],
    fail_reasons: list[str],
    binding_pass: bool | None = None,
    dashboard_display_projection_digest: str | None = None,
) -> OfflineReplaySixNodeValidationGraphBindingResultV0:
    summary = replay_result.summary
    resolved_binding_pass = (
        binding_pass
        if binding_pass is not None
        else replay_result.replay_pass
        and integration_pass
        and six_node_graph_pass
        and not fail_reasons
    )
    return OfflineReplaySixNodeValidationGraphBindingResultV0(
        layer_version=OFFLINE_REPLAY_SIX_NODE_VALIDATION_GRAPH_BINDING_LAYER_VERSION,
        binding_pass=resolved_binding_pass,
        replay_pass=replay_result.replay_pass,
        integration_pass=integration_pass,
        six_node_graph_pass=six_node_graph_pass,
        completed_validators=completed_validators,
        fail_reasons=tuple(fail_reasons),
        orders_total=summary.orders_total,
        cancels_total=summary.cancels_total,
        fills_total=summary.fills_total,
        positions_opened_total=summary.positions_opened_total,
        dashboard_display_projection_digest=dashboard_display_projection_digest,
    )
