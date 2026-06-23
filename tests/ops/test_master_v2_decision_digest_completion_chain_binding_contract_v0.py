"""Contract: optional Master-V2 decision/state digest binding in completion proof chain."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.ops.bounded_futures_testnet_durable_run_primary_evidence_completion_integration_contract_v0 import (
    MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER,
    MasterV2DecisionStateDigestBinding,
    classify_master_v2_binding_presence,
    compute_master_v2_component_state_digest,
    compute_master_v2_decision_digest_from_snapshot,
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
    VALIDATOR_RECOVERY,
    VALIDATOR_TRACEABILITY,
    VALIDATOR_WALLCLOCK,
)
from src.ops.durable_completion_validation.models import ValidationContext
from src.ops.durable_completion_validation.validators.completion_chain import (
    validate_completion_proof_chain_binding,
)
from trading.master_v2.decision_packet_fixtures_v1 import sample_master_v2_decision_packet_v1
from trading.master_v2.decision_packet_snapshot_v1 import decision_packet_to_snapshot_v1
from trading.master_v2.double_play_state import ActiveSide, SideState

_SELECTED_FUTURE = "ETH-PERP"


def _component_digest(component: str, **state: object) -> str:
    return compute_master_v2_component_state_digest(component=component, state=state)


def _sample_master_v2_binding(*, source_revision: str) -> MasterV2DecisionStateDigestBinding:
    packet = sample_master_v2_decision_packet_v1()
    snapshot = decision_packet_to_snapshot_v1(packet, require_consistent_packet=True)
    return MasterV2DecisionStateDigestBinding(
        binding_owner=MASTER_V2_DECISION_STATE_DIGEST_BINDING_OWNER,
        source_revision=source_revision,
        master_v2_decision_id=packet.correlation_id,
        master_v2_decision_digest=compute_master_v2_decision_digest_from_snapshot(snapshot),
        selected_future_id=_SELECTED_FUTURE,
        bull_layer_state_digest=_component_digest(
            "bull_layer_state", side_state=SideState.LONG_ACTIVE.value
        ),
        bear_layer_state_digest=_component_digest(
            "bear_layer_state", side_state=SideState.SHORT_ARMED.value
        ),
        active_side_digest=_component_digest("active_side", active_side=ActiveSide.LONG.value),
        dynamic_scope_state_digest=_component_digest(
            "dynamic_scope_state", anchor_price=100.0, upscope_boundary=105.0
        ),
        hysteresis_cooldown_state_digest=_component_digest(
            "hysteresis_cooldown_state", last_switch_tick=10, min_switch_cooldown_ticks=3
        ),
        killswitch_state_digest=_component_digest("killswitch_state", safety_decision_allowed=True),
        capital_slot_state_digest=_component_digest(
            "capital_slot_state", active_slot_base=1000.0, allow_auto_top_up=False
        ),
        inactivity_exit_state_digest=_component_digest(
            "inactivity_exit_state", release_reason="opportunity_cost"
        ),
        execution_intent_digest=_component_digest(
            "execution_intent", zero_order=True, orders_allowed=False
        ),
    )


def _with_master_v2_binding(integration_input):
    binding = _sample_master_v2_binding(source_revision=integration_input.source_revision)
    with_binding = replace(integration_input, master_v2_decision_state_digest_binding=binding)
    chain = default_minimal_completion_proof_chain(with_binding)
    return replace(with_binding, completion_proof_chain=chain)


def test_legacy_ops_only_reports_master_v2_binding_not_present() -> None:
    integration_input = default_minimal_completion_integration_input()
    assert (
        classify_master_v2_binding_presence(
            binding=integration_input.master_v2_decision_state_digest_binding,
            chain=integration_input.completion_proof_chain,
        )
        == "MASTER_V2_BINDING_NOT_PRESENT"
    )
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons
    assert not validate_durable_run_primary_evidence_completion_integration_input(integration_input)
    assert evaluate_durable_run_primary_evidence_completion_integration(integration_input)[
        "integration_pass"
    ]


def test_complete_master_v2_binding_accepted() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    assert (
        classify_master_v2_binding_presence(
            binding=integration_input.master_v2_decision_state_digest_binding,
            chain=integration_input.completion_proof_chain,
        )
        == "MASTER_V2_BINDING_PRESENT"
    )
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons
    assert not validate_durable_run_primary_evidence_completion_integration_input(integration_input)


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
    ],
)
def test_master_v2_fields_bound_through_integration_and_validator(
    binding_field: str,
    chain_field: str,
) -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    binding = integration_input.master_v2_decision_state_digest_binding
    chain = integration_input.completion_proof_chain
    assert binding is not None
    assert getattr(chain, chain_field) == getattr(binding, binding_field)


def test_missing_single_field_when_binding_present_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    binding = integration_input.master_v2_decision_state_digest_binding
    assert binding is not None
    bad_binding = replace(binding, bull_layer_state_digest="")
    bad = replace(integration_input, master_v2_decision_state_digest_binding=bad_binding)
    reasons = validate_durable_run_primary_evidence_completion_integration_input(bad)
    assert any("bull_layer_state_digest" in reason for reason in reasons)


def test_invalid_digest_format_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    binding = integration_input.master_v2_decision_state_digest_binding
    assert binding is not None
    bad_binding = replace(binding, master_v2_decision_digest="not-a-digest")
    bad = replace(integration_input, master_v2_decision_state_digest_binding=bad_binding)
    reasons = validate_durable_run_primary_evidence_completion_integration_input(bad)
    assert any("master_v2_decision_digest" in reason for reason in reasons)


def test_digest_drift_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_master_v2_decision_digest="0" * 64,
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("master_v2_decision_digest" in reason for reason in reasons)


def test_decision_id_drift_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_master_v2_decision_id="drift-id",
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("master_v2_decision_id" in reason for reason in reasons)


def test_selected_future_drift_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_selected_future_id="OTHER-PERP",
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any("selected_future_id" in reason for reason in reasons)


def test_owner_drift_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    binding = integration_input.master_v2_decision_state_digest_binding
    assert binding is not None
    bad_binding = replace(binding, binding_owner="wrong.owner.v0")
    bad = replace(integration_input, master_v2_decision_state_digest_binding=bad_binding)
    reasons = validate_durable_run_primary_evidence_completion_integration_input(bad)
    assert any("binding_owner" in reason for reason in reasons)


def test_partial_chain_reference_fail_closed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    bad_chain = replace(
        integration_input.completion_proof_chain,
        completion_referenced_execution_intent_digest=None,
    )
    bad = replace(integration_input, completion_proof_chain=bad_chain)
    reasons = validate_completion_proof_chain_binding(
        ValidationContext(integration_input=bad)
    ).fail_reasons
    assert any(
        "partial Master-V2 completion chain reference forbidden" in reason
        or "all Master-V2 completion chain reference fields required" in reason
        for reason in reasons
    )


def test_binding_presence_does_not_imply_trading_logic_executed() -> None:
    integration_input = _with_master_v2_binding(default_minimal_completion_integration_input())
    result = evaluate_durable_run_primary_evidence_completion_integration(integration_input)
    assert result["integration_pass"] is True
    safety = integration_input.safety_snapshot
    assert safety.orders_allowed is False
    assert safety.network_allowed is False
    assert safety.credentials_allowed is False
    assert safety.execution_authorized is False


def test_six_node_validation_graph_unchanged() -> None:
    assert VALIDATOR_WALLCLOCK in PROOF_BINDING_VALIDATION_ORDER
    assert VALIDATOR_COMPLETION_CHAIN in PROOF_BINDING_VALIDATION_ORDER
    assert PROOF_BINDING_VALIDATION_GRAPH[VALIDATOR_COMPLETION_CHAIN] == (
        VALIDATOR_OPERATOR_CLOSURE,
        VALIDATOR_TRACEABILITY,
        VALIDATOR_RECOVERY,
        VALIDATOR_WALLCLOCK,
    )
    integration_input = default_minimal_completion_integration_input()
    assert not validate_completion_proof_chain_binding(
        ValidationContext(integration_input=integration_input)
    ).fail_reasons
