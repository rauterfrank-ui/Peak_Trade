"""Contract tests for bouchaud OHLCV proxy v1 STEP29M adapter implementation v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.backtest import (
    step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 as admissibility,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0 import (
    EVALUATION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    classify_go_token_v0,
    run_adapter_implementation_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    REPO_ROOT
    / "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0.py"
)


def test_implementation_go_runs_adapter_without_evaluation() -> None:
    implementation_operator_go = IMPLEMENTATION_GO_TOKEN
    result = run_adapter_implementation_v0(
        repo_root=REPO_ROOT,
        confirm_operator_go=implementation_operator_go,
    )
    assert "PASS_BOUCHAUD" in result.verdict
    assert result.economic_evaluation_executed is False
    assert result.runtime_effect == "NONE"
    assert result.authority_effect == "NONE"
    assert result.research_scope == "bouchaud_microstructure_ohlcv_proxy/v1"


def test_evaluation_go_blocked_in_runner() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--confirm-go-token", EVALUATION_GO_TOKEN],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "evaluation_go_blocked_in_implementation_slice" in proc.stderr + proc.stdout


def test_wrong_go_rejected_in_runner() -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--confirm-go-token", "GO_WRONG_TOKEN"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "invalid_go_token" in proc.stderr + proc.stdout


def test_classify_go_tokens() -> None:
    impl = classify_go_token_v0(IMPLEMENTATION_GO_TOKEN)
    assert impl.classification.value == "IMPLEMENTATION"
    assert impl.accepted_for_validation_only is True

    eval_result = classify_go_token_v0(EVALUATION_GO_TOKEN)
    assert eval_result.classification.value == "EVALUATION"
    assert "evaluation_go_blocked_in_implementation_slice" in eval_result.blocking_reasons


def test_admissibility_with_evaluation_go_does_not_execute_evaluation() -> None:
    evaluation_operator_go = EVALUATION_GO_TOKEN
    result = (
        admissibility.evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
            repo_root=REPO_ROOT,
            operator_go=evaluation_operator_go,
        )
    )
    assert result.admissibility_result.value == "PASS"


def test_runtime_import_boundary_no_scheduler() -> None:
    runner_text = RUNNER.read_text(encoding="utf-8")
    for forbidden in ("mv2_research_wiring", "BacktestEngine", "execution.live", "order_adapter"):
        assert forbidden not in runner_text


def test_runner_does_not_import_backtest_engine_for_evaluation() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "mv2_research_wiring" not in text
    assert "BacktestEngine" not in text
    assert "run_mv2_research_backtest" not in text


def test_canonical_step29m_entry_point_named_in_binding() -> None:
    binding = json.loads(
        (
            REPO_ROOT
            / "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
        ).read_text(encoding="utf-8")
    )
    refs = binding["binding"]["external_bindings"]
    assert "admissibility_contract_ref" in refs
    assert "adapter_owner_ref" in refs
    assert "evaluation_config_ref" in refs
