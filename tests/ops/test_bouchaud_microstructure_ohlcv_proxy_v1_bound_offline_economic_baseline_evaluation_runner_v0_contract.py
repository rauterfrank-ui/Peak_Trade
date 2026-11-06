"""Contract tests for bouchaud OHLCV proxy v1 bound offline evaluation runner v0."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from src.backtest.step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 import (
    EVALUATION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import (
    DATA_PERIOD,
    DATASET_DIGEST,
    INSTRUMENT_ID,
    PRIOR_BINDING_DIGEST,
    PRIOR_CONFIG_DIGEST,
    PRIOR_IMPLEMENTATION_DIGEST,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0 import (
    classify_go_token_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    REPO_ROOT
    / "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"
)
ADAPTER_RUNNER = (
    REPO_ROOT
    / "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0.py"
)
SCOPE_CONFIG = REPO_ROOT / SCOPE_RATIFICATION_CONFIG_REL_PATH


def _run_runner(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(RUNNER), *args]
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        env=run_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_admissibility_validation_accepts_evaluation_go_without_execution() -> None:
    evaluation_operator_go = EVALUATION_GO_TOKEN
    proc = _run_runner(
        "--confirm-go-token",
        evaluation_operator_go,
        "--admissibility-validation-only",
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == "ADMISSIBILITY_PASS"
    assert payload["economic_evaluation_executed"] is False
    assert payload["evaluation_execution_count"] == 0
    assert payload["runtime_effect"] == "NONE"
    assert payload["authority_effect"] == "NONE"
    assert payload["config_digest"] == PRIOR_CONFIG_DIGEST


def test_invalid_operator_go_rejected() -> None:
    proc = _run_runner("--confirm-go-token", "GO_WRONG_TOKEN", "--admissibility-validation-only")
    assert proc.returncode != 0
    assert "invalid_go_token" in proc.stderr + proc.stdout


def test_implementation_go_rejected_by_evaluation_runner() -> None:
    proc = _run_runner(
        "--confirm-go-token",
        IMPLEMENTATION_GO_TOKEN,
        "--admissibility-validation-only",
    )
    assert proc.returncode != 0
    assert "invalid_go_token" in proc.stderr + proc.stdout


def test_adapter_still_rejects_direct_evaluation_go() -> None:
    proc = subprocess.run(
        [sys.executable, str(ADAPTER_RUNNER), "--confirm-go-token", EVALUATION_GO_TOKEN],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "evaluation_go_blocked_in_implementation_slice" in proc.stderr + proc.stdout


def test_stale_config_digest_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["config_digest"] = "0" * 64
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "config_digest_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_stale_implementation_digest_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["implementation_digest"] = PRIOR_IMPLEMENTATION_DIGEST
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "implementation_digest_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_stale_binding_digest_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["binding_digest"] = PRIOR_BINDING_DIGEST
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "binding_digest_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_wrong_instrument_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["instrument_id"] = "inst-btc-usdt-perp"
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "instrument_id_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_wrong_data_period_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["data_period"] = "2020-01-01 00:00:00+00:00..2020-02-01 00:00:00+00:00"
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "data_period_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_wrong_dataset_digest_rejected() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    scope["data_digest"] = "0" * 64
    SCOPE_CONFIG.write_text(json.dumps(scope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        proc = _run_runner(
            "--confirm-go-token",
            EVALUATION_GO_TOKEN,
            "--admissibility-validation-only",
        )
        assert proc.returncode != 0
        assert "data_digest_mismatch" in proc.stderr + proc.stdout
    finally:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import materialize_ratification_bundle; materialize_ratification_bundle(Path('.'))",
            ],
            cwd=REPO_ROOT,
            check=True,
        )


def test_forbidden_runtime_environment_rejected() -> None:
    proc = _run_runner(
        "--confirm-go-token",
        EVALUATION_GO_TOKEN,
        "--admissibility-validation-only",
        env={"PEAK_TRADE_RUNTIME_MODE": "live"},
    )
    assert proc.returncode != 0
    assert "forbidden_runtime_environment" in proc.stderr + proc.stdout


def test_classify_go_tokens_adapter_boundary_preserved() -> None:
    eval_result = classify_go_token_v0(EVALUATION_GO_TOKEN)
    assert eval_result.classification.value == "EVALUATION"
    assert "evaluation_go_blocked_in_implementation_slice" in eval_result.blocking_reasons


def test_scope_ratification_invariants_bound() -> None:
    scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
    assert scope["instrument_id"] == INSTRUMENT_ID
    assert scope["data_digest"] == DATASET_DIGEST
    assert scope["data_period"] == DATA_PERIOD
    assert scope["implementation_digest"] != PRIOR_IMPLEMENTATION_DIGEST
    assert scope["binding_digest"] != PRIOR_BINDING_DIGEST


def test_runner_offline_import_boundary() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "mv2_research_wiring" in text
    assert "run_baseline_evaluation" in text
    assert "admissibility-validation-only" in text
