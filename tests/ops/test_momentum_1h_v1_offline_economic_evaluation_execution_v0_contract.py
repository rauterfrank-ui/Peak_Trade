"""Contract tests for momentum_1h/v1 offline economic evaluation execution v0."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from src.research.momentum_1h_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BINDING_MATERIALIZATION_CONFIG_REL,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_REASON,
    MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0,
    OPERATOR_GO,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_BINDING_CONFIG_REL,
    SCOPE_CLASSIFICATION,
    STRATEGY_BINDING_DIGEST,
    STRATEGY_BINDING_REF,
    PersistenceExecutionVerdict,
    verify_binding_materialization_preflight_v0,
    verify_preconditions_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = REPO_ROOT / BINDING_MATERIALIZATION_CONFIG_REL
SCOPE_BINDING_CONFIG = REPO_ROOT / SCOPE_BINDING_CONFIG_REL
RUNNER = REPO_ROOT / "scripts/ops/run_momentum_1h_v1_offline_economic_evaluation_execution_v0.py"
LARGE_EVIDENCE_GLOBS = (
    "**/TRADE_LEDGER_V1.jsonl",
    "**/EQUITY_CURVE_V1.jsonl",
)


def test_go_token_and_scope_classification() -> None:
    assert OPERATOR_GO == "GO_MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    assert SCOPE_CLASSIFICATION == "MOMENTUM_1H_V1_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"


def test_no_runtime_authority_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_expected_origin_main_sha() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "bda1e4e92e1352e65fd2f2cf0d3aca9e44328ccc"


def test_scope_binding_config_exists_and_complete() -> None:
    assert SCOPE_BINDING_CONFIG.is_file()
    payload = json.loads(SCOPE_BINDING_CONFIG.read_text(encoding="utf-8"))
    assert payload["strategy_binding_digest"] == STRATEGY_BINDING_DIGEST
    assert payload["binding_selection_status"] == "BINDING_MATERIALIZATION_COMPLETE"
    assert payload["missing_binding_artifacts"] == []


def test_binding_materialization_preflight_accepted() -> None:
    ok, reasons, binding = verify_binding_materialization_preflight_v0(
        repo_root=REPO_ROOT,
        binding_config_path=BINDING_CONFIG,
        scope=MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0,
    )
    assert ok is True
    assert not reasons
    assert binding["strategy_binding_digest"] == STRATEGY_BINDING_DIGEST
    assert binding["strategy_binding_ref"] == STRATEGY_BINDING_REF
    assert binding["evidence_class_id"] == EVIDENCE_CLASS_ID
    assert binding["parent_offline_evaluation_scope_config_ref"] == SCOPE_BINDING_CONFIG_REL


def test_verify_preconditions_rejects_invalid_go_token() -> None:
    ok, reasons = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="INVALID",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        require_clean_worktree=False,
        scope=MOMENTUM_PERSISTENCE_EXECUTION_SCOPE_V0,
    )
    assert ok is False
    assert any("GO_TOKEN_INVALID" in reason for reason in reasons)


def test_fail_closed_runner_exits_non_zero_without_go() -> None:
    result = subprocess.run(
        ["python3", str(RUNNER)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert FAIL_CLOSED_REASON in result.stderr


def test_persistence_verdict_enum_values() -> None:
    assert PersistenceExecutionVerdict.PASS.value == "PASS"
    assert PersistenceExecutionVerdict.FAIL_CLOSED.value == "FAIL_CLOSED"
    assert PersistenceExecutionVerdict.INCONCLUSIVE.value == "INCONCLUSIVE"


def test_execution_binding_safety_flags() -> None:
    payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    assert payload["authority_effect"] == "NONE"
    assert payload["promotion_eligible"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["runtime_authorized"] is False
    assert payload["evaluation_execution"] is False


def test_no_large_evidence_files_in_repo() -> None:
    for pattern in LARGE_EVIDENCE_GLOBS:
        matches = list(REPO_ROOT.glob(pattern))
        assert not matches, f"large evidence file must not be in repo: {pattern}"
