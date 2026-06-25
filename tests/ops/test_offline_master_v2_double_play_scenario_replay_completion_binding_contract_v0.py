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
    VALIDATOR_EVENT_STREAM,
    VALIDATOR_OPERATOR_CLOSURE,
    VALIDATOR_RECONCILIATION,
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    VALIDATOR_WALLCLOCK,
    execute_proof_binding_validation_graph,
)
from src.ops.durable_completion_validation.validators.event_stream import (
    MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL,
    evaluate_glb019_event_stream_validation,
    evaluate_master_v2_state_event_stream_validation,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
)
from src.ops.bounded_master_v2_testnet_completion_path_wiring_v0 import (
    TestnetCompletionPathMarketInputV0,
    evaluate_bounded_master_v2_testnet_completion_path_wiring,
)
from src.ops.offline_master_v2_replay_six_node_validation_graph_binding_v0 import (
    PROOF_CLASSIFICATION_FULL_E2E_BOUND,
    PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
    PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
    build_completion_integration_input_from_offline_replay_result,
    build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result,
    build_validation_context_from_completion_integration_input,
    prove_offline_replay_six_node_validation_graph_binding_v0,
    verify_dashboard_display_projection_digest_six_node_evidence,
)
from trading.master_v2.double_play_futures_input import (
    FuturesFreshnessState,
    FuturesInputSnapshot,
    FuturesMarketDataProvenanceStatus,
)
from trading.master_v2.double_play_state import ScopeEvent, SideState
from trading.master_v2.offline_double_play_scenario_replay_v0 import (
    SYNTHETIC_FUTURES_INSTRUMENT,
    OfflineDoublePlayProofEvent,
    OfflineDoublePlayScenarioReplayInputV0,
    OfflineDoublePlayScenarioReplayResultV0,
    OfflineDoublePlayScenarioTickV0,
    build_default_bull_bear_bull_scenario_ticks,
    build_offline_replay_futures_input_snapshot,
    run_offline_double_play_scenario_replay_v0,
    validate_offline_double_play_scenario_replay_input_v0,
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
    return build_completion_integration_input_from_offline_replay_result(replay_result)


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
    assert VALIDATOR_EVENT_STREAM in PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_COMPLETION_CHAIN in PROOF_BINDING_VALIDATION_ORDER
    assert PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN] == (
        VALIDATOR_OPERATOR_CLOSURE,
        VALIDATOR_TRACEABILITY,
        VALIDATOR_RECOVERY,
        VALIDATOR_WALLCLOCK,
        VALIDATOR_EVENT_STREAM,
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


def test_replay_builder_wires_glb019_result_present(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    assert context.glb019_result is not None
    assert context.glb019_result["validation_pass"] is True


def test_replay_builder_glb019_result_matches_canonical_evaluation(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    expected = evaluate_glb019_event_stream_validation(
        integration_input.glb019_event_stream_validation_input
    )
    assert context.glb019_result == expected


def test_replay_builder_glb019_identity_digest_coherence(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    proof = integration_input.glb019_event_stream_proof
    assert context.glb019_result is not None
    assert proof.validation_input_digest == context.glb019_result["validation_input_digest"]
    assert proof.validation_result_digest == context.glb019_result["validation_result_digest"]
    assert proof.event_stream_identity == context.glb019_result["event_stream_identity"]


def test_replay_builder_glb019_result_missing_fail_closed_graph(integration_input) -> None:
    context = build_validation_context_from_completion_integration_input(integration_input)
    context.glb019_result = None
    graph_result = execute_proof_binding_validation_graph(context)
    assert any("glb019_result required" in reason for reason in graph_result.fail_reasons)
    assert VALIDATOR_EVENT_STREAM not in context.completed_validators
    assert VALIDATOR_COMPLETION_CHAIN not in context.completed_validators


def test_replay_builder_incoherent_glb019_proof_fail_closed(integration_input) -> None:
    bad_proof = replace(
        integration_input.glb019_event_stream_proof,
        validation_result_digest="0" * 64,
    )
    bad = replace(integration_input, glb019_event_stream_proof=bad_proof)
    context = build_validation_context_from_completion_integration_input(bad)
    graph_result = execute_proof_binding_validation_graph(context)
    assert graph_result.fail_reasons
    assert VALIDATOR_EVENT_STREAM not in context.completed_validators


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
    assert proof.projection_pass is True
    assert proof.integration_pass is True
    assert proof.six_node_graph_pass is True
    assert proof.proof_classification == PROOF_CLASSIFICATION_FULL_E2E_BOUND
    assert proof.completed_validators == PROOF_BINDING_VALIDATION_ORDER
    assert proof.state_event_projection_digest is not None
    assert proof.master_v2_state_event_stream_identity is not None
    assert proof.event_stream_non_authorizing is True
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
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
) -> None:
    proof = prove_offline_replay_six_node_validation_graph_binding_v0()
    assert proof.binding_pass, proof.fail_reasons
    assert proof.six_node_graph_pass is True
    assert proof.dashboard_display_projection_digest is not None
    assert len(proof.dashboard_display_projection_digest) == 64
    assert (
        proof.dashboard_display_projection_digest
        == replay_result.dashboard_display_projection_digest
    )
    binding = replay_result.master_v2_decision_state_digest_binding
    assert binding is not None
    assert proof.dashboard_display_projection_digest == binding.dashboard_display_projection_digest
    chain = integration_input.completion_proof_chain
    assert (
        proof.dashboard_display_projection_digest
        == chain.completion_referenced_dashboard_display_projection_digest
    )


def test_six_node_machine_lines_contains_dashboard_display_projection_digest(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    proof = prove_offline_replay_six_node_validation_graph_binding_v0()
    machine = proof.to_machine_lines()
    assert (
        machine["DASHBOARD_DISPLAY_PROJECTION_DIGEST"] == proof.dashboard_display_projection_digest
    )
    assert machine["DASHBOARD_DISPLAY_PROJECTION_DIGEST"] == (
        replay_result.dashboard_display_projection_digest or ""
    )
    assert machine["DASHBOARD_DISPLAY_PROJECTION_DIGEST"] != ""


def test_six_node_display_projection_digest_matches_testnet_completion_wiring(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
) -> None:
    proof = prove_offline_replay_six_node_validation_graph_binding_v0()
    market_input = TestnetCompletionPathMarketInputV0(
        selected_future_id=replay_result.selected_future_id,
        ticks=tuple(tick for tick in build_default_bull_bear_bull_scenario_ticks()),
        source_run_id="six-node-digest-crosscheck-v0",
    )
    wiring = evaluate_bounded_master_v2_testnet_completion_path_wiring(market_input)
    assert wiring.dashboard_display_projection_digest == proof.dashboard_display_projection_digest


def test_six_node_missing_dashboard_display_projection_digest_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
) -> None:
    bad_replay = replace(replay_result, dashboard_display_projection_digest=None)
    digest, reasons = verify_dashboard_display_projection_digest_six_node_evidence(
        bad_replay,
        integration_input,
    )
    assert digest is None
    assert any("dashboard_display_projection_digest missing" in reason for reason in reasons)


def test_six_node_dashboard_display_projection_digest_mismatch_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
) -> None:
    bad_binding = replace(
        replay_result.master_v2_decision_state_digest_binding,
        dashboard_display_projection_digest="1" * 64,
    )
    bad_replay = replace(
        replay_result,
        master_v2_decision_state_digest_binding=bad_binding,
    )
    digest, reasons = verify_dashboard_display_projection_digest_six_node_evidence(
        bad_replay,
        integration_input,
    )
    assert digest is None
    assert any("dashboard_display_projection_digest" in reason for reason in reasons)


def test_six_node_dashboard_display_projection_digest_drift_fails_closed(
    replay_result: OfflineDoublePlayScenarioReplayResultV0,
    integration_input,
) -> None:
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_dashboard_display_projection_digest="0" * 64,
    )
    bad_input = replace(integration_input, completion_proof_chain=bad_chain)
    digest, reasons = verify_dashboard_display_projection_digest_six_node_evidence(
        replay_result,
        bad_input,
    )
    assert digest is None
    assert any("dashboard_display_projection_digest" in reason for reason in reasons)


def test_replay_sourced_master_v2_state_event_stream_wired_into_integration(
    integration_input,
) -> None:
    validation_input = integration_input.master_v2_state_event_stream_validation_input
    proof = integration_input.master_v2_state_event_stream_proof
    assert validation_input is not None
    assert proof is not None
    assert validation_input.events
    assert proof.master_v2_state_event_validation_pass is True
    assert proof.event_stream_non_authorizing is True


def test_replay_sourced_master_v2_state_event_proof_matches_canonical_evaluation(
    integration_input,
) -> None:
    validation_input = integration_input.master_v2_state_event_stream_validation_input
    proof = integration_input.master_v2_state_event_stream_proof
    assert validation_input is not None
    expected = evaluate_master_v2_state_event_stream_validation(validation_input)
    assert proof.validation_input_digest == expected["validation_input_digest"]
    assert proof.validation_result_digest == expected["validation_result_digest"]
    assert proof.state_event_stream_identity == expected["state_event_stream_identity"]


def test_end_to_end_projection_digest_deterministic() -> None:
    first = prove_offline_replay_six_node_validation_graph_binding_v0()
    second = prove_offline_replay_six_node_validation_graph_binding_v0()
    assert first.state_event_projection_digest == second.state_event_projection_digest
    assert (
        first.master_v2_state_event_stream_identity == second.master_v2_state_event_stream_identity
    )


def _default_ticks() -> tuple[OfflineDoublePlayScenarioTickV0, ...]:
    return build_default_bull_bear_bull_scenario_ticks()


def _assert_replay_executed(result: OfflineDoublePlayScenarioReplayResultV0) -> None:
    """Partial scenario slices may omit full default proof-event bundle; ticks must still replay."""
    assert result.tick_records, "scenario replay must produce tick records"
    blocking = [
        r
        for r in result.fail_reasons
        if "zero-order violated" in r
        or "decision snapshot missing" in r
        or "master_v2_decision_state_digest_binding missing" in r
        or "dashboard_display_projection_digest missing" in r
    ]
    assert not blocking, blocking


def _run_scenario_ticks(
    ticks: tuple[OfflineDoublePlayScenarioTickV0, ...],
    *,
    futures_input_snapshot: FuturesInputSnapshot | None = None,
) -> OfflineDoublePlayScenarioReplayResultV0:
    return run_offline_double_play_scenario_replay_v0(
        OfflineDoublePlayScenarioReplayInputV0(
            selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
            ticks=ticks,
            source_revision="offline-e2e-scenario-v0",
            futures_input_snapshot=futures_input_snapshot,
        )
    )


def _prove_scenario_ticks(
    ticks: tuple[OfflineDoublePlayScenarioTickV0, ...],
    *,
    futures_input_snapshot: FuturesInputSnapshot | None = None,
):
    replay_input = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=ticks,
        source_revision="offline-e2e-scenario-v0",
        futures_input_snapshot=futures_input_snapshot,
    )
    return prove_offline_replay_six_node_validation_graph_binding_v0(replay_input)


@pytest.mark.parametrize(
    ("scenario_id", "ticks_builder", "expect_full_e2e"),
    [
        ("A", lambda: _default_ticks()[:5], False),
        ("B", lambda: _default_ticks()[:12], False),
        ("C", lambda: _default_ticks()[:6], False),
        ("D", lambda: _default_ticks()[:12] + _default_ticks()[16:20], True),
        ("G", lambda: _default_ticks()[:5] + (_default_ticks()[15],), False),
        ("H", lambda: _default_ticks()[:12] + _default_ticks()[12:15], True),
    ],
)
def test_scenario_end_to_end_replay_proof_binding(
    scenario_id: str,
    ticks_builder,
    expect_full_e2e: bool,
) -> None:
    ticks = ticks_builder()
    replay_result = _run_scenario_ticks(ticks)
    _assert_replay_executed(replay_result)
    proof = _prove_scenario_ticks(ticks)
    assert proof.orders_total == 0
    assert proof.event_stream_non_authorizing is True
    if scenario_id == "C":
        assert OfflineDoublePlayProofEvent.BULL_TO_BEAR in replay_result.summary.proof_events
    if expect_full_e2e:
        assert proof.binding_pass is True, proof.fail_reasons
        assert proof.projection_pass is True
        assert proof.proof_classification == PROOF_CLASSIFICATION_FULL_E2E_BOUND
        assert proof.state_event_projection_digest is not None
    else:
        assert proof.binding_pass is False
        assert proof.proof_classification in (
            PROOF_CLASSIFICATION_PROJECTION_FAIL_CLOSED,
            PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED,
        )


def test_scenario_e_end_to_end_replay_fail_closed() -> None:
    base = build_offline_replay_futures_input_snapshot(SYNTHETIC_FUTURES_INSTRUMENT)
    stale = FuturesInputSnapshot(
        candidate=base.candidate,
        ranking=base.ranking,
        instrument=base.instrument,
        provenance=FuturesMarketDataProvenanceStatus(
            complete=True,
            freshness_state=FuturesFreshnessState.STALE,
            dataset_id=base.provenance.dataset_id,
            source=base.provenance.source,
            mark_available=True,
            index_available=True,
            last_available=True,
            ohlcv_available=True,
            funding_available=True,
            open_interest_available=True,
            missing_fields=(),
        ),
        volatility=base.volatility,
        liquidity=base.liquidity,
        derivatives=base.derivatives,
        opportunity=base.opportunity,
    )
    ticks = _default_ticks()[:5]
    inp = OfflineDoublePlayScenarioReplayInputV0(
        selected_future_id=SYNTHETIC_FUTURES_INSTRUMENT,
        ticks=ticks,
        futures_input_snapshot=stale,
    )
    assert validate_offline_double_play_scenario_replay_input_v0(inp)
    proof = prove_offline_replay_six_node_validation_graph_binding_v0(inp)
    assert proof.replay_pass is False
    assert proof.binding_pass is False
    assert proof.proof_classification == PROOF_CLASSIFICATION_REPLAY_FAIL_CLOSED


def test_scenario_f_end_to_end_kill_all_path_bound() -> None:
    kill_tick = OfflineDoublePlayScenarioTickV0(
        tick_index=12,
        timestamp_ms=1_700_000_000_000 + 12 * 60_000,
        price=95.0,
        scope_event=ScopeEvent.KILL_ALL_REQUIRED,
        safety_decision_allowed=False,
    )
    ticks = _default_ticks()[:12] + (kill_tick,)
    replay_result = _run_scenario_ticks(ticks)
    _assert_replay_executed(replay_result)
    assert replay_result.summary.final_side_state == SideState.KILL_ALL
    assert OfflineDoublePlayProofEvent.KILLSWITCH_BLOCKED in replay_result.summary.proof_events
    for rec in replay_result.tick_records:
        assert rec.orders == 0
        assert rec.cancels == 0
        assert rec.fills == 0
        assert rec.positions_opened == 0

    base = default_minimal_completion_integration_input()
    glb019_input = base.glb019_event_stream_validation_input
    validation_input, proof_binding, projection_digest, failures = (
        build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result(
            replay_result,
            source_revision=base.source_revision,
            completion_identity_digest=glb019_input.completion_identity_digest,
            manifest_identity_digest=glb019_input.manifest_identity_digest,
            run_identity_digest=glb019_input.run_identity_digest,
            correlation_id=glb019_input.correlation_id,
        )
    )
    assert not failures, failures
    assert validation_input is not None
    assert proof_binding is not None
    assert validation_input.evidence_chain_profile == MASTER_V2_EVIDENCE_CHAIN_PROFILE_KILL_ALL
    assert proof_binding.event_stream_non_authorizing is True
    assert projection_digest is not None
    assert len(projection_digest) == 64


def test_missing_projection_event_fail_closed(replay_result) -> None:
    base = default_minimal_completion_integration_input()
    glb019_input = base.glb019_event_stream_validation_input
    validation_input, proof, _digest, failures = (
        build_replay_sourced_master_v2_state_event_stream_binding_from_replay_result(
            replay_result,
            source_revision=base.source_revision,
            completion_identity_digest=glb019_input.completion_identity_digest,
            manifest_identity_digest=glb019_input.manifest_identity_digest,
            run_identity_digest=glb019_input.run_identity_digest,
            correlation_id=glb019_input.correlation_id,
        )
    )
    assert validation_input is not None
    assert proof is not None
    assert not failures
    tampered_events = validation_input.events[1:]
    bad_validation = replace(validation_input, events=tampered_events)
    bad_result = evaluate_master_v2_state_event_stream_validation(bad_validation)
    assert bad_result["validation_pass"] is False


def test_unknown_scenario_ticks_fail_closed() -> None:
    proof = _prove_scenario_ticks(())
    assert proof.replay_pass is False
    assert proof.binding_pass is False
