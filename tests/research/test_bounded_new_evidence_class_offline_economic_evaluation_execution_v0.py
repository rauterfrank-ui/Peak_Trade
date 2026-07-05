"""Contract tests for bounded_new_evidence_class_offline_economic_evaluation_execution_v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.bounded_new_evidence_class_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    NEW_BINDING_COMPLETION_DIGEST,
    NEW_EVIDENCE_CLASS_SCOPE_DIGEST,
    NEW_EVIDENCE_CLASS_SEMANTIC_DIGEST,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    EconomicExecutionVerdict,
    classify_candidate_verdict_v0,
    classify_fleet_verdict_v0,
    verify_execution_start_state_v0,
    verify_new_evidence_class_scope_v0,
    verify_preconditions_v0,
)
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = REPO_ROOT / "config/research/final_research_fleet_new_evidence_class_scope_v0.json"
BINDING_CONFIG = (
    REPO_ROOT
    / "config/research/final_research_fleet_okx_full_panel_versioned_binding_completion_v0.json"
)


@pytest.fixture(name="scope_config")
def fixture_scope_config() -> dict:
    return json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(name="binding_completion")
def fixture_binding_completion() -> dict:
    return json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))


def test_go_token_and_scope_classification() -> None:
    assert GO_TOKEN == "GO_BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    assert (
        SCOPE_CLASSIFICATION
        == "BOUNDED_NEW_EVIDENCE_CLASS_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )


def test_no_runtime_authority_order_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_expected_origin_main_sha() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "ab851bd6a9fa102208f834b998367bd2ab7416f7"


def test_new_evidence_class_scope_digests(scope_config: dict) -> None:
    assert scope_config["scope_digest"] == NEW_EVIDENCE_CLASS_SCOPE_DIGEST
    assert scope_config["semantic_digest"] == NEW_EVIDENCE_CLASS_SEMANTIC_DIGEST
    assert scope_config["new_binding_completion_digest"] == NEW_BINDING_COMPLETION_DIGEST
    assert scope_config["evidence_class_id"] == EVIDENCE_CLASS_ID
    assert (
        scope_config["previous_completion_digest"] == HISTORICAL_STEP31F_BINDING_COMPLETION_DIGEST
    )


def test_verify_new_evidence_class_scope_accepted(
    scope_config: dict, binding_completion: dict
) -> None:
    ok, reasons = verify_new_evidence_class_scope_v0(
        scope_config,
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


def test_verify_execution_start_state_accepted_on_main() -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        require_clean_worktree=False,
    )
    assert result.valid is True
    assert result.origin_main_sha == EXPECTED_ORIGIN_MAIN_SHA
    assert result.fleet_binding_completion["completion_digest"] == NEW_BINDING_COMPLETION_DIGEST


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
