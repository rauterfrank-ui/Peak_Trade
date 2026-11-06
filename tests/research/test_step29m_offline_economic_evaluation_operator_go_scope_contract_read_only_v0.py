import json
from pathlib import Path

CONTRACT_PATH = Path(
    "docs/research/step29m_offline_economic_evaluation_operator_go_scope_contract_read_only_v0.json"
)
MD_PATH = Path(
    "docs/research/STEP29M_OFFLINE_ECONOMIC_EVALUATION_OPERATOR_GO_SCOPE_CONTRACT_READ_ONLY_V0.md"
)


def test_step29m_operator_go_scope_contract_is_bound_read_only_v0():
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert (
        payload["contract_id"]
        == "STEP29M_OFFLINE_ECONOMIC_EVALUATION_OPERATOR_GO_SCOPE_CONTRACT_READ_ONLY_V0"
    )
    assert payload["status"] == "OPERATOR_GO_SCOPE_CONTRACT_BOUND_READ_ONLY"
    assert (
        payload["operator_go_token"]
        == "GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_SCOPE_CONTRACT_READ_ONLY_V0"
    )

    fleet_ids = [item["strategy_id"] for item in payload["research_fleet"]]
    assert fleet_ids == ["trend_following", "bollinger_bands", "momentum_1h"]
    for item in payload["research_fleet"]:
        assert item["binding_status_required"] == "CONTRACT_BOUND_READ_ONLY_NO_EVAL"

    allowed = payload["allowed_next_execution_scope_after_separate_run_command"]
    assert allowed["offline_backtest"] is True
    assert allowed["walk_forward"] is True
    assert allowed["monte_carlo"] is True
    assert allowed["stress"] is True
    assert allowed["parameter_sensitivity"] is True
    assert allowed["offline_linear_evidence_support_diagnostics"] is True
    assert allowed["economic_viability_evidence_assembly"] is True

    forbidden = payload["forbidden_in_this_contract"]
    assert forbidden["economic_evaluation_execution"] is True
    assert forbidden["runtime_rewire"] is True
    assert forbidden["live"] is True
    assert forbidden["orders"] is True
    assert forbidden["core_system_mutation"] is True

    preconditions = payload["preconditions_for_future_execution"]
    assert preconditions["versioned_strategy_bindings_present"] is True
    assert preconditions["canonical_decision_chain_digest_required"] is True
    assert preconditions["backtest_runtime_parity_digest_required"] is True

    flags = payload["authority_flags"]
    assert flags["economic_evaluation_executed"] is False
    assert flags["economic_evaluation_authorized_for_this_contract_only"] is False
    assert flags["system_economic_evidence_admissible"] is False
    assert flags["runtime_rewire_admissible"] is False
    assert flags["live_authorized"] is False
    assert flags["orders_allowed"] is False
    assert flags["authority_effect"] == "NONE"
    assert flags["runtime_effect"] == "NONE"

    linear = payload["linear_evidence_boundary"]
    assert linear["linear_diagnostics_support_only"] is True
    assert linear["ols_can_not_set_economically_viable_offline"] is True
    assert linear["ols_runtime_authority"] is False
    assert linear["ols_promotion_pass_authority"] is False

    created_after = payload["created_after"]
    assert (
        created_after["step29m_binding_contracts_merge_closeout_verdict"]
        == "PASS_MERGE_CLOSEOUT_STEP29M_VERSIONED_BINDING_CONTRACTS_READ_ONLY_NO_EVAL"
    )
    assert created_after["post_merge_head"] == "88619c1f"

    assert (
        payload["next_step"]
        == "CREATE_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED"
    )


def test_step29m_operator_go_scope_contract_doc_states_no_eval_v0():
    text = MD_PATH.read_text(encoding="utf-8")
    assert "STEP29M_OFFLINE_ECONOMIC_EVALUATION_OPERATOR_GO_SCOPE_CONTRACT_READ_ONLY_V0" in text
    assert "GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_SCOPE_CONTRACT_READ_ONLY_V0" in text
    assert "does not execute" in text.lower()
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "RUNTIME_EFFECT=NONE" in text
    assert (
        "CREATE_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED"
        in text
    )
