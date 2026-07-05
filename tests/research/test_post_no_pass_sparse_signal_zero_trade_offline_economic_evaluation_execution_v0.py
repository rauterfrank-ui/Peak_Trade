"""Contract tests for post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXPECTED_ORIGIN_MAIN_SHA,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    SPARSE_BINDING_COMPLETION_DIGEST,
    EconomicExecutionVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    verify_execution_scope_v0,
    verify_execution_start_state_v0,
    verify_preconditions_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_execution_scope_v0.json"
)
BINDING_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0.json"
)
RATIFICATION_CONFIG = (
    REPO_ROOT
    / "config/research/post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification_v0.json"
)


@pytest.fixture(name="execution_scope_config")
def fixture_execution_scope_config() -> dict:
    return json.loads(EXECUTION_SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="binding_completion")
def fixture_binding_completion() -> dict:
    return json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))


def test_go_token_and_scope_classification() -> None:
    assert (
        CONFIRM_GO
        == "GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )
    assert (
        SCOPE_CLASSIFICATION
        == "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_expected_origin_main_sha() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "4698b49739976cdc3270922a38fad4b044ae5d26"


def test_execution_scope_digests(execution_scope_config: dict) -> None:
    assert execution_scope_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
    assert execution_scope_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
    assert execution_scope_config["binding_completion_digest"] == SPARSE_BINDING_COMPLETION_DIGEST
    assert execution_scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
    assert execution_scope_config["execution_go_token"] == CONFIRM_GO


def test_verify_execution_scope_accepted(
    execution_scope_config: dict, binding_completion: dict
) -> None:
    ok, reasons = verify_execution_scope_v0(
        execution_scope_config,
        sparse_binding_completion=binding_completion,
    )
    assert ok is True
    assert not reasons


def test_verify_preconditions_rejects_invalid_go_token() -> None:
    ok, reasons = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="INVALID",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        require_clean_worktree=False,
    )
    assert ok is False
    assert any("GO_TOKEN_INVALID" in reason for reason in reasons)


def test_verify_execution_start_state_rejects_after_execution() -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        require_clean_worktree=False,
    )
    assert result.valid is False
    assert any("ECONOMIC_EVALUATION_ALREADY_EXECUTED" in reason for reason in result.fail_reasons)


def test_classify_fleet_verdict_sparse_signal_zero_trade() -> None:
    verdict = classify_fleet_verdict_v0(
        [
            EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE,
            EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE,
            EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE,
        ]
    )
    assert verdict is EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE


def test_classify_candidate_verdict_sparse_signal() -> None:
    result = CandidateExecutionResultV0(
        strategy_id="trend_following",
        strategy_version="v2",
        canonical_candidate_identifier="trend_following/v2",
        config_path="config/ops/example.json",
        output_dir="/tmp/out",
        run_id="run-1",
        terminal_status=CandidateTerminalStatus.FAIL,
        economic_validity_result="FAIL",
        economic_validity_offline_gate_pass=False,
        evidence_status="ROBUSTNESS_FAILED",
        manifest_verify_rc=0,
        reason_codes=(),
        stage_return_codes={},
        runner_execution_success=True,
    )
    verdict = classify_candidate_verdict_v0(
        result,
        sparse_metrics={"instruments_with_nonzero_trades": 0},
    )
    assert verdict is EconomicExecutionVerdict.SPARSE_SIGNAL_ZERO_TRADE


def test_scope_ratification_config_exists() -> None:
    payload = json.loads(RATIFICATION_CONFIG.read_text(encoding="utf-8"))
    assert payload["offline_economic_evaluation_scope_ratified"] is True
    assert payload["economic_evaluation_executed"] is True
    assert payload["fleet_binding_digest"] == SPARSE_BINDING_COMPLETION_DIGEST


def test_registry_metadata_reflects_execution_complete() -> None:
    assert authoritative_field_value("CURRENT_STATE") == (
        "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_COMPLETE_V0"
    )
    assert authoritative_field_value("NEXT_CANONICAL_STEP") == (
        "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
    )
    assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
    assert (
        authoritative_field_value(
            "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_STATUS"
        )
        == "EXECUTION_COMPLETE_INCONCLUSIVE"
    )
    assert (
        authoritative_field_value(
            "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_FLEET_VERDICT"
        )
        == "EXECUTION_FAILED_FAIL_CLOSED"
    )
    assert (
        authoritative_field_value(
            "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0_MANIFEST_VERIFY_RC"
        )
        == "0"
    )
