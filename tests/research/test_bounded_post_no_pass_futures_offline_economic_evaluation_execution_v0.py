"""Contract tests for bounded_post_no_pass_futures_offline_economic_evaluation_execution_v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.bounded_post_no_pass_futures_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CLASS_D_BINDING_COMPLETION_DIGEST,
    EVIDENCE_CLASS_ID,
    EXECUTION_SCOPE_DIGEST,
    EXECUTION_SEMANTIC_DIGEST,
    EXPECTED_ORIGIN_MAIN_SHA,
    CONFIRM_GO,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    EconomicExecutionVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    verify_execution_scope_v0,
    verify_execution_start_state_v0,
    verify_preconditions_v0,
    verify_scope_definition_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/bounded_post_no_pass_futures_offline_economic_evaluation_execution_scope_v0.json"
)
SCOPE_DEFINITION_CONFIG = (
    REPO_ROOT / "config/research/bounded_post_no_pass_futures_research_scope_definition_v0.json"
)
BINDING_CONFIG = (
    REPO_ROOT / "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)


@pytest.fixture(name="execution_scope_config")
def fixture_execution_scope_config() -> dict:
    return json.loads(EXECUTION_SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="scope_definition_config")
def fixture_scope_definition_config() -> dict:
    return json.loads(SCOPE_DEFINITION_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="binding_completion")
def fixture_binding_completion() -> dict:
    return json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))


def test_go_token_and_scope_classification() -> None:
    assert CONFIRM_GO == "GO_BOUNDED_POST_NO_PASS_FUTURES_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    assert (
        SCOPE_CLASSIFICATION
        == "BOUNDED_POST_NO_PASS_FUTURES_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_expected_origin_main_sha() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "17d70364e27ec12d9f648a043ae08eed4eb87cb5"


def test_execution_scope_digests(execution_scope_config: dict) -> None:
    assert execution_scope_config["scope_digest"] == EXECUTION_SCOPE_DIGEST
    assert execution_scope_config["semantic_digest"] == EXECUTION_SEMANTIC_DIGEST
    assert execution_scope_config["binding_completion_digest"] == CLASS_D_BINDING_COMPLETION_DIGEST
    assert execution_scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
    assert execution_scope_config["execution_go_token"] == CONFIRM_GO
    assert (
        execution_scope_config["previous_completion_digest"]
        == HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
    )


def test_verify_execution_scope_accepted(
    execution_scope_config: dict, binding_completion: dict
) -> None:
    ok, reasons = verify_execution_scope_v0(
        execution_scope_config,
        fleet_binding_completion=binding_completion,
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


def test_verify_scope_definition_rejects_after_execution(scope_definition_config: dict) -> None:
    ok, reasons = verify_scope_definition_v0(scope_definition_config)
    assert ok is False
    assert any("SCOPE_DEFINITION_STATUS_INVALID" in reason for reason in reasons)
    assert scope_definition_config["status"] == "SCOPE_EXECUTED_COMPLETE_ROBUSTNESS_FAILED"
    assert scope_definition_config["required_next_go_for_execution"] == CONFIRM_GO


def test_verify_execution_start_state_rejects_after_execution() -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        require_clean_worktree=False,
    )
    assert result.valid is False
    assert any("SCOPE_DEFINITION_STATUS_INVALID" in reason for reason in result.fail_reasons)


def test_classify_fleet_verdict_robustness_failed() -> None:
    verdict = classify_fleet_verdict_v0(
        [
            EconomicExecutionVerdict.ROBUSTNESS_FAILED,
            EconomicExecutionVerdict.ROBUSTNESS_FAILED,
            EconomicExecutionVerdict.ROBUSTNESS_FAILED,
        ]
    )
    assert verdict is EconomicExecutionVerdict.ROBUSTNESS_FAILED


def test_classify_candidate_verdict_economically_viable() -> None:
    result = CandidateExecutionResultV0(
        strategy_id="trend_following",
        strategy_version="v1",
        canonical_candidate_identifier="trend_following/v1",
        config_path="config/ops/example.json",
        output_dir="/tmp/out",
        run_id="run-1",
        terminal_status=CandidateTerminalStatus.PASS,
        economic_validity_result="PASS",
        economic_validity_offline_gate_pass=True,
        evidence_status="ECONOMICALLY_VIABLE_OFFLINE",
        manifest_verify_rc=0,
        reason_codes=(),
        stage_return_codes={},
        runner_execution_success=True,
    )
    assert (
        classify_candidate_verdict_v0(result)
        is EconomicExecutionVerdict.ECONOMICALLY_VIABLE_OFFLINE
    )
