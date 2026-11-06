"""Contract tests for trade ledger equity curve persistence offline evaluation execution v0."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from src.research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BINDING_MATERIALIZATION_CONFIG_REL,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    FAIL_CLOSED_REASON,
    OPERATOR_GO,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    STRATEGY_BINDING_DIGEST,
    STRATEGY_BINDING_REF,
    PersistenceExecutionVerdict,
    verify_binding_materialization_preflight_v0,
    verify_preconditions_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CONFIG = REPO_ROOT / BINDING_MATERIALIZATION_CONFIG_REL
RUNNER = REPO_ROOT / (
    "scripts/ops/run_trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0.py"
)


def test_go_token_and_scope_classification() -> None:
    assert OPERATOR_GO == "GO_TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"
    assert (
        SCOPE_CLASSIFICATION
        == "TRADE_LEDGER_EQUITY_CURVE_PERSISTENCE_OFFLINE_EVALUATION_EXECUTION_V0"
    )


def test_no_runtime_authority_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_expected_origin_main_sha() -> None:
    assert EXPECTED_ORIGIN_MAIN_SHA == "5e86ed8e0ab21c42fbbd97c8510d58e74db263ec"


def test_binding_materialization_preflight_accepted() -> None:
    ok, reasons, binding = verify_binding_materialization_preflight_v0(
        repo_root=REPO_ROOT,
        binding_config_path=BINDING_CONFIG,
    )
    assert ok is True
    assert not reasons
    assert binding["strategy_binding_digest"] == STRATEGY_BINDING_DIGEST
    assert binding["strategy_binding_ref"] == STRATEGY_BINDING_REF
    assert binding["evidence_class_id"] == EVIDENCE_CLASS_ID


def test_verify_preconditions_rejects_invalid_go_token() -> None:
    ok, reasons = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="INVALID",
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        require_clean_worktree=False,
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
