import json
from pathlib import Path


CONFIG = Path(
    "config/research/ratify_versioned_final_fleet_bindings_and_offline_economic_evaluation_scope_v0.json"
)


def test_final_fleet_is_exact_and_versioned_binding_scope_only():
    payload = json.loads(CONFIG.read_text())
    assert payload["final_research_fleet"] == ["trend_following", "bollinger_bands", "momentum_1h"]
    assert payload["candidate_binding_status"] == "RATIFIED_FOR_VERSIONED_BINDING_MATERIALIZATION"
    assert payload["offline_evaluation_scope_defined"] is True
    assert payload["economic_evaluation_authorized"] is False


def test_required_bindings_are_complete_before_evaluation():
    payload = json.loads(CONFIG.read_text())
    required = set(payload["required_bindings_per_candidate"])
    assert {
        "strategy_id",
        "strategy_version",
        "parameter_binding",
        "dataset_binding",
        "period_binding",
        "instrument_binding",
        "fee_model_binding",
        "slippage_model_binding",
        "funding_model_binding",
        "execution_model_binding",
        "economic_policy_binding",
        "implementation_digest",
        "config_digest",
        "data_digest",
    } <= required


def test_no_runtime_or_order_authority_is_introduced():
    payload = json.loads(CONFIG.read_text())
    blocked_flags = [
        "runtime_rewire_admissible",
        "economic_validity_offline_gate_pass",
        "live_authorized",
        "shadow_authorized",
        "paper_authorized",
        "testnet_authorized",
        "scheduler_runtime_allowed",
        "orders_allowed",
        "credentials_allowed",
        "core_system_mutation_allowed",
        "canonical_trading_logic_mutation_allowed",
        "master_v2_mutation_allowed",
        "double_play_mutation_allowed",
        "risk_sizing_mutation_allowed",
        "safety_runtime_mutation_allowed",
    ]
    for flag in blocked_flags:
        assert payload[flag] is False


def test_allowed_followup_is_offline_only_and_requires_separate_go():
    payload = json.loads(CONFIG.read_text())
    assert payload["allowed_after_separate_go"] == [
        "OFFLINE_BACKTEST",
        "WALK_FORWARD",
        "MONTE_CARLO",
        "STRESS",
        "PARAMETER_SENSITIVITY",
        "ECONOMIC_VIABILITY_EVIDENCE",
    ]
    assert (
        payload["next_step"]
        == "MATERIALIZE_VERSIONED_FINAL_FLEET_BINDINGS_PRECONDITIONS_OR_SEPARATE_OFFLINE_EVALUATION_GO_REQUIRED"
    )
