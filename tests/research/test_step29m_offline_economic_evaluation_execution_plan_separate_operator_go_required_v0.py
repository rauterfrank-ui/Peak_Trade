import json
from pathlib import Path

PLAN_PATH = Path(
    "docs/research/step29m_offline_economic_evaluation_execution_plan_separate_operator_go_required_v0.json"
)
MD_PATH = Path(
    "docs/research/STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED_V0.md"
)


def test_step29m_execution_plan_is_read_only_separate_operator_go_required_v0():
    payload = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

    assert (
        payload["schema_version"]
        == "Step29MOfflineEconomicEvaluationExecutionPlanSeparateOperatorGoRequiredV0"
    )
    assert (
        payload["verdict"]
        == "PASS_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED_READ_ONLY_V0"
    )
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["separate_operator_go_required_before_execution"] is True
    assert (
        payload["operator_go_token_required"]
        == "GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )

    assert payload["economic_evaluation_executed"] is False
    assert payload["offline_backtest_executed"] is False
    assert payload["walk_forward_executed"] is False
    assert payload["monte_carlo_executed"] is False
    assert payload["stress_executed"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["system_economic_evidence_admissible"] is False

    allowed = payload["allowed_scope_now"]
    assert "READ_ONLY_EXECUTION_PLAN" in allowed
    assert "BIND_MANIFEST_EVIDENCE_LAYOUT" in allowed

    disallowed = payload["disallowed_scope_now"]
    assert "ECONOMIC_EVALUATION_RUN" in disallowed
    assert "BACKTEST_RUN" in disallowed
    assert "LIVE" in disallowed
    assert "ORDER_SUBMISSION" in disallowed

    preconditions = payload["execution_preconditions"]
    assert preconditions["full_canonical_chain_wired"] == "REQUIRED_TRUE_MANIFEST_VERIFIED"
    assert (
        preconditions["backtest_runtime_decision_parity_pass"] == "REQUIRED_TRUE_MANIFEST_VERIFIED"
    )
    assert preconditions["realistic_costs_bound"] == "REQUIRED_TRUE_MANIFEST_VERIFIED"

    required_inputs = payload["required_operator_inputs_for_execution_go"]
    assert required_inputs["operator"] == "Frank Rauter"
    assert required_inputs["go_token"] == "GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    assert required_inputs["instrument_universe"] == "FUTURES_ONLY_NO_BTC_XBT_NO_SPOT_REQUIRED"
    assert required_inputs["robustness_scope"] == "WALK_FORWARD_MONTE_CARLO_STRESS_REQUIRED"

    execution_plan = payload["execution_plan_after_separate_go"]
    assert execution_plan[0] == "verify_preconditions_and_source_manifests"
    assert "run_offline_backtest_on_full_canonical_chain_only" in execution_plan
    assert "run_walk_forward_oos_validation" in execution_plan
    assert "run_monte_carlo_robustness" in execution_plan
    assert "manifest_and_verify_evidence_bundle" in execution_plan[-1]

    boundaries = payload["hard_boundaries"]
    assert boundaries["futures_only"] is True
    assert boundaries["bitcoin_direction_allowed"] is False
    assert boundaries["spot_allowed"] is False
    assert boundaries["ols_runtime_authority"] is False
    assert boundaries["no_economic_claim_before_execution"] is True


def test_step29m_execution_plan_doc_states_no_eval_v0():
    text = MD_PATH.read_text(encoding="utf-8")
    assert (
        "PASS_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED_READ_ONLY_V0"
        in text
    )
    assert "GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0" in text
    assert "does not execute economic evaluation" in text.lower()
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "RUNTIME_EFFECT=NONE" in text
    assert (
        "SEPARATE_OPERATOR_GO_REQUIRED_WITH_TOKEN_GO_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
        in text
    )
