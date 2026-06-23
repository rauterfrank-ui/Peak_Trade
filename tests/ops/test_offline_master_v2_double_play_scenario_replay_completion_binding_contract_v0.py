"""Contract: offline replay output feeds existing Master-V2 completion binding chain."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    classify_master_v2_binding_presence,
    default_minimal_completion_integration_input,
    default_minimal_completion_proof_chain,
    evaluate_durable_run_primary_evidence_completion_integration,
    validate_durable_run_primary_evidence_completion_integration_input,
)
from src.ops.durable_completion_validation.graph import (
    PROOF_BINDING_VALIDATION_GRAPH,
    PROOF_BINDING_VALIDATION_ORDER,
    VALIDATOR_COMPLETION_CHAIN,
    VALIDATOR_OPERATOR_CLOSURE,
    VALIDATOR_RECONCILIATION,
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    VALIDATOR_WALLCLOCK,
    execute_proof_binding_validation_graph,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
)
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    build_completion_integration_input_from_offline_replay_result,
    build_validation_context_from_completion_integration_input,
    prove_offline_replay_six_node_validation_graph_binding_v0,
)
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    build_default_bull_bear_bull_scenario_ticks,
    run_offline_double_play_scenario_replay_v0,
)


@pytest.fixture(scope="module", name="replay_result")
def _replay_result() -> OfflineDoublePlayScenarioReplayResultV0:
    replay = run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
            ticks=build_default_bull_bear_bull_scenario_ticks(),
            source_revision="offline-replay-ops-test-v0",
        )
    )
    assert replay.replay_pass, replay.fail_reasons
    return replay


@pytest.fixture(scope="module", name="integration_input")
def _integration_input(replay_result: OfflineDoublePlayScenarioReplayResultV0):
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    base = default_minimal_completion_integration_input()
    binding_aligned = replace(binding, source_revision=base.source_revision)
    with_binding = replace(
        base,
        master_v2_decision_state_digest_binding=binding_aligned,
    )
    chain = default_minimal_completion_proof_chain(with_binding)
    return replace(with_binding, completion_proof_chain=chain)


def test_replay_output_accepted_by_completion_binding(integration_input) -> None:
    assert (
        classify_master_v2_binding_presence(
            binding=integration_input.master_v2_decision_state_digest_binding,
            chain=integration_input.completion_proof_chain,
        )
        == "MASTER_V2_BINDING_PRESENT"
    )
    assert not validate_durable_run_primary_evidence_completion_integration_input(integration_input)
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons


@pytest.mark.parametrize(
    ("binding_field", "chain_field"),
    [
        ("master_v2_decision_id", "completion_referenced_master_v2_decision_id"),
        ("master_v2_decision_digest", "completion_referenced_master_v2_decision_digest"),
        ("selected_future_id", "completion_referenced_selected_future_id"),
        ("bull_layer_state_digest", "completion_referenced_bull_layer_state_digest"),
        ("bear_layer_state_digest", "completion_referenced_bear_layer_state_digest"),
        ("active_side_digest", "completion_referenced_active_side_digest"),
        ("dynamic_scope_state_digest", "completion_referenced_dynamic_scope_state_digest"),
        (
            "hysteresis_cooldown_state_digest",
            "completion_referenced_hysteresis_cooldown_state_digest",
        ),
        ("killswitch_state_digest", "completion_referenced_killswitch_state_digest"),
        ("capital_slot_state_digest", "completion_referenced_capital_slot_state_digest"),
        ("inactivity_exit_state_digest", "completion_referenced_inactivity_exit_state_digest"),
        ("execution_intent_digest", "completion_referenced_execution_intent_digest"),
        (
            "dashboard_display_projection_digest",
            "completion_referenced_dashboard_display_projection_digest",
        ),
    ],
)
def test_all_master_v2_fields_bound(
    binding_field: str, chain_field: str, integration_input
) -> None:
    binding = integration_input.master_v2_decision_state_digest_binding
    chain = integration_input.completion_proof_chain
    assert binding is not None
    assert getattr(chain, chain_field) == getattr(binding, binding_field)


def test_partial_replay_binding_fail_closed(integration_input) -> None:
    binding = integration_input.master_v2_decision_state_digest_binding
    assert binding is not None
    bad_binding = replace(binding, bear_layer_state_digest="")
    bad = replace(integration_input, master_v2_decision_state_digest_binding=bad_binding)
    reasons = validate_durable_run_primary_evidence_completion_integration_input(bad)
    assert any("bear_layer_state_digest" in reason for reason in reasons)


def test_decision_id_drift_fail_closed(integration_input) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_master_v2_decision_id="drift-id",
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("master_v2_decision_id" in reason for reason in reasons)


def test_digest_drift_fail_closed(integration_input) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_master_v2_decision_digest="0" * 64,
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("master_v2_decision_digest" in reason for reason in reasons)


def test_selected_future_drift_fail_closed(integration_input) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_selected_future_id="SOL-PERP",
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("selected_future_id" in reason for reason in reasons)


def test_legacy_ops_only_unchanged() -> None:
    integration_input = default_minimal_completion_integration_input()
    assert (
        classify_master_v2_binding_presence(
            binding=integration_input.master_v2_decision_state_digest_binding,
            chain=integration_input.completion_proof_chain,
        )
        == "MASTER_V2_BINDING_NOT_PRESENT"
    )
    assert evaluate_durable_run_primary_evidence_completion_integration(integration_input)[
        "integration_pass"
    ]


def test_six_node_validation_graph_unchanged() -> None:
    assert VALIDATOR_WALLCLOCK in PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_COMPLETION_CHAIN in PROOF_BINDING_VALIDATION_ORDER
    assert PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN] == (
        VALIDATOR_OPERATOR_CLOSURE,
        VALIDATOR_TRACEABILITY,
        VALIDATOR_RECOVERY,
        VALIDATOR_WALLCLOCK,
    )


def test_no_paper_shadow_testnet_live_proof_claim(integration_input) -> None:
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    safety = integration_input.safety_snapshot
    assert safety.orders_allowed is False
    assert safety.network_allowed is False
    assert safety.execution_authorized is False
    assert safety.live_authorized is False


def test_replay_sourced_integration_input_matches_builder(replay_result, integration_input) -> None:
    built = build_completion_integration_input_from_offline_replay_result(replay_result)
    assert (
        built.master_v2_decision_state_digest_binding
        == integration_input.master_v2_decision_state_digest_binding
    )
    assert built.completion_proof_chain == integration_input.completion_proof_chain


def test_replay_sourced_six_node_validation_graph_passes(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    graph_result = execute_proof_binding_validation_graph(context)
    assert graph_result.fail_reasons == ()
    assert set(context.completed_validators) == set(PROOF_BINDING_VALIDATION_ORDER)
    assert context.completed_validators == {
        VALIDATOR_RECONCILIATION,
        VALIDATOR_RECOVERY,
        VALIDATOR_TRACEABILITY,
        VALIDATOR_OPERATOR_CLOSURE,
        VALIDATOR_WALLCLOCK,
        VALIDATOR_COMPLETION_CHAIN,
    }


def test_replay_sourced_six_node_graph_node_order_preserved(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    execute_proof_binding_validation_graph(context)
    completed_in_order = [
        node for node in PROOF_BINDING_VALIDATION_ORDER if node in context.completed_validators
    ]
    assert completed_in_order == list(PROOF_BINDING_VALIDATION_ORDER)


def test_orchestrator_proves_offline_replay_six_node_graph_binding() -> None:
    proof = prove_offline_replay_six_node_validation_graph_binding_v0()
    assert proof.binding_pass is True
    assert proof.replay_pass is True
    assert proof.integration_pass is True
    assert proof.six_node_graph_pass is True
    assert proof.completed_validators == PROOF_BINDING_VALIDATION_ORDER
    assert proof.orders_total == 0
    assert proof.cancels_total == 0
    assert proof.fills_total == 0
    assert proof.positions_opened_total == 0


def test_replay_graph_binding_fail_closed_on_digest_drift(integration_input) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_master_v2_decision_digest="0" * 64,
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    context = build_validation_context_from_completion_integration_input(bad)
    graph_result = execute_proof_binding_validation_graph(context)
    assert graph_result.fail_reasons
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_replay_graph_binding_zero_order_boundary(replay_result) -> None:
    for record in replay_result.tick_records:
        assert record.orders == 0
        assert record.cancels == 0
        assert record.fills == 0
        assert record.positions_opened == 0


def test_replay_display_projection_digest_bound_in_decision_state_binding(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert replay_result.dashboard_display_projection_digest is not None
    assert (
        binding.dashboard_display_projection_digest
        == replay_result.dashboard_display_projection_digest
    )


def test_replay_display_projection_digest_bound_in_completion_chain(
    integration_input,
) -> None:
    binding = integration_input.master_v2_decision_state_digest_binding
    chain = integration_input.completion_proof_chain
    assert binding is not None
    assert (
        chain.completion_referenced_dashboard_display_projection_digest
        == binding.dashboard_display_projection_digest
    )


def test_replay_display_projection_digest_drift_fail_closed(integration_input) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("dashboard_display_projection_digest" in reason for reason in reasons)


def test_replay_sourced_six_node_graph_includes_display_projection_digest(
    integration_input,
) -> None:
    proof = prove_offline_replay_six_node_validation_graph_binding_v0()
    assert proof.binding_pass, proof.fail_reasons
    assert proof.six_node_graph_pass is True
