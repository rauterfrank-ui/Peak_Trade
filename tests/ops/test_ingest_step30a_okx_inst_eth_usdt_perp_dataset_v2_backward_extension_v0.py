from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = (
    _REPO_ROOT
    / "scripts/ops/ingest_step30a_okx_inst_eth_usdt_perp_dataset_v2_backward_extension_v0.py"
)
_GO_LITERAL = (
    "GO_BOUNDED_STEP30A_RSI_REVERSION_V1_EXTENDED_HOLDOUT_SEPARATED_FUTURES_ECONOMIC_RESEARCH_V0"
)


def _load_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_step30a_ingest", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_holdout_constants_match_step29m_frozen() -> None:
    mod = _load_mod()
    mod._validate_holdout_constants_match_step29m_v1()


def test_step30a_window_days_constant_is_90() -> None:
    mod = _load_mod()
    assert mod.STEP30A_DATASET_V2_WINDOW_DAYS == 90


def test_wrong_token_rejected() -> None:
    mod = _load_mod()
    with pytest.raises(mod.Step30aDatasetIngestionError, match="confirm_go_token_mismatch"):
        mod.run_step30a_dataset_v2_backward_extension_ingestion_v0(
            confirm_go_token="WRONG",
            skip_network=True,
        )


def test_network_ingestion_forbidden_without_skip_network() -> None:
    mod = _load_mod()
    with pytest.raises(mod.Step30aDatasetIngestionError, match="network_ingestion_forbidden"):
        mod.run_step30a_dataset_v2_backward_extension_ingestion_v0(
            confirm_go_token=_GO_LITERAL,
            skip_network=False,
        )


def test_cli_skip_network_path() -> None:
    proc = _run(
        [
            "--confirm-go-token",
            _GO_LITERAL,
            "--skip-network",
        ]
    )
    assert proc.returncode == 0
    assert "STEP30A_CONFIRM_GO=" in proc.stdout
    assert _GO_LITERAL in proc.stdout
    assert "STEP30A_DATASET_V2_WINDOW_DAYS=90" in proc.stdout
