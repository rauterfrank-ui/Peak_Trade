import json
from pathlib import Path

CLASSIFICATION_PATH = Path(
    "docs/research/step29m_execution_result_fail_closed_preconditions_not_admissible_v0.json"
)
MD_PATH = Path(
    "docs/research/STEP29M_EXECUTION_RESULT_FAIL_CLOSED_PRECONDITIONS_NOT_ADMISSIBLE_V0.md"
)


def test_step29m_execution_result_fail_closed_classification_is_bound_v0():
    payload = json.loads(CLASSIFICATION_PATH.read_text(encoding="utf-8"))

    assert (
        payload["schema_version"]
        == "step29m_execution_result_fail_closed_preconditions_not_admissible_v0"
    )
    assert payload["status"] == "binding_classification"
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert (
        payload["execution_pipeline_verdict"]
        == "PASS_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )
    assert payload["execution_runner_rc"] == 0
    assert (
        payload["economic_evaluation_result_verdict"]
        == "FAIL_CLOSED_STEP29M_EXECUTION_PRECONDITIONS_NOT_ADMISSIBLE"
    )
    assert payload["economic_evaluation_executed"] is False
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["live_authorized"] is False
    assert payload["orders_allowed"] is False

    classification = payload["classification"]
    assert classification["pipeline_materialization_pass"] is True
    assert classification["economic_execution_blocked_fail_closed"] is True
    assert classification["negative_or_positive_profitability_claim_created"] is False
    assert classification["promotion_candidate_created"] is False
    assert classification["runtime_authority_created"] is False

    failed = payload["failed_preconditions"]
    assert failed["FULL_CANONICAL_CHAIN_WIRED"] is False
    assert failed["BACKTEST_RUNTIME_DECISION_PARITY_PASS"] is False
    assert failed["REALISTIC_COSTS_BOUND"] is False
    assert failed["ROBUSTNESS_EVIDENCE_PASS"] is False

    assert payload["reason_codes"] == [
        "SYSTEM_ECONOMIC_EVIDENCE_NOT_ADMISSIBLE_FROM_PLAN_PRECONDITIONS"
    ]
    assert (
        payload["next_step"]
        == "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE"
    )

    allowed = payload["allowed_next_scope"]
    assert "CORE_SYSTEM_COMPLETION" in allowed
    assert "OFFLINE_PARITY_ASSESSMENT" in allowed
    assert "NARROW_REUSE_FIRST_REWIRE" in allowed

    disallowed = payload["disallowed_next_scope"]
    assert "LIVE_EVIDENCE" in disallowed
    assert "ORDER_SUBMISSION" in disallowed
    assert "CREDENTIAL_USE" in disallowed

    source = payload["source_evidence"]
    assert source["manifest_verify_required"] is True
    assert source["manifest_verify_rc"] == 0


def test_step29m_execution_result_fail_closed_classification_doc_states_no_eval_v0():
    text = MD_PATH.read_text(encoding="utf-8")
    assert "PASS_STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0" in text
    assert "FAIL_CLOSED_STEP29M_EXECUTION_PRECONDITIONS_NOT_ADMISSIBLE" in text
    assert "does not execute economic evaluation" in text.lower()
    assert "AUTHORITY_EFFECT=NONE" in text
    assert "RUNTIME_EFFECT=NONE" in text
    assert (
        "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AND_REWIRE_SCOPE"
        in text
    )
