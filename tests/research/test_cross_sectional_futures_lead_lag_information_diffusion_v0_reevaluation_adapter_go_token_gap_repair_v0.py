"""Repair contract tests for lead-lag v0 reevaluation adapter GO token gap v0."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops import (
    run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 as runner_module,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN,
    LEGACY_RESEARCH_PATH_MODE,
    REEVALUATION_GO_TOKEN,
    RUNTIME_EFFECT,
    SYSTEM_EVIDENCE_MV2_PATH_MODE,
    resolve_adapter_go_token_for_productive_lane_v0,
    resolve_productive_evaluation_path_mode_v0,
    validate_entry_point_go_token_v0,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    ALLOWED_ADAPTER_GO_TOKENS,
    REASON_GO_TOKEN_INVALID,
    verify_adapter_go_token_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = (
    REPO_ROOT / "scripts/ops/"
    "run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
TARGET_REEVALUATION_GO = REEVALUATION_GO_TOKEN


def test_reevaluation_go_token_in_allowed_adapter_go_tokens() -> None:
    assert TARGET_REEVALUATION_GO in ALLOWED_ADAPTER_GO_TOKENS


def test_full_evaluation_execution_go_token_in_allowed_adapter_go_tokens() -> None:
    assert GO_TOKEN in ALLOWED_ADAPTER_GO_TOKENS


def test_adapter_accepts_reevaluation_go_token() -> None:
    ok, reasons = verify_adapter_go_token_v0(TARGET_REEVALUATION_GO)
    assert ok is True
    assert reasons == ()


def test_adapter_accepts_existing_full_evaluation_go_token() -> None:
    ok, reasons = verify_adapter_go_token_v0(GO_TOKEN)
    assert ok is True
    assert reasons == ()


def test_adapter_rejects_unknown_go_token_fail_closed() -> None:
    ok, reasons = verify_adapter_go_token_v0("GO_UNKNOWN_TOKEN")
    assert ok is False
    assert REASON_GO_TOKEN_INVALID in reasons


def test_adapter_rejects_missing_go_token_fail_closed() -> None:
    ok, reasons = verify_adapter_go_token_v0("")
    assert ok is False
    assert REASON_GO_TOKEN_INVALID in reasons


def test_reevaluation_go_reaches_system_evidence_mv2_path_mode() -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(go_token=TARGET_REEVALUATION_GO)
        == SYSTEM_EVIDENCE_MV2_PATH_MODE
    )


def test_reevaluation_go_legacy_research_path_blocked() -> None:
    assert (
        resolve_productive_evaluation_path_mode_v0(go_token=TARGET_REEVALUATION_GO)
        != LEGACY_RESEARCH_PATH_MODE
    )


def test_reevaluation_go_adapter_resolution_is_identity_alias() -> None:
    assert (
        resolve_adapter_go_token_for_productive_lane_v0(go_token=TARGET_REEVALUATION_GO)
        == TARGET_REEVALUATION_GO
    )


def test_runner_entry_point_accepts_reevaluation_go_token() -> None:
    ok, branch = validate_entry_point_go_token_v0(TARGET_REEVALUATION_GO)
    assert ok is True
    assert branch == "REEVALUATION_V0"


def test_runner_cli_rejects_unknown_go_token_fail_closed() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--confirm",
            "GO_UNKNOWN_TOKEN",
            "--primary-worktree",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "ERR:confirm_go_token_required" in proc.stderr


def test_runner_cli_rejects_missing_go_token_fail_closed() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--primary-worktree",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode != 0


def test_runner_dispatch_only_does_not_execute_evaluation_owner(tmp_path: Path) -> None:
    with patch.object(
        runner_module,
        "run_full_offline_economic_evaluation_v0",
    ) as full_eval:
        with pytest.raises(SystemExit) as exc:
            runner_module.run_bounded_full_evaluation_dispatch_v0(
                confirm=TARGET_REEVALUATION_GO,
                durable_evidence_root=tmp_path,
                primary_worktree=REPO_ROOT,
                staging_root=REPO_ROOT,
            )
        assert exc.value.code == 1
        full_eval.assert_not_called()


def test_adapter_repair_preserves_no_runtime_or_authority_effect() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert AUTHORITY_EFFECT == "NONE"
