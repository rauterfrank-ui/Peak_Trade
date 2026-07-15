"""Ops contract tests for lead-lag offline economic evaluation infrastructure materializer v0."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.ops import (
    materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_infrastructure_v0 as materializer_module,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    INFRASTRUCTURE_GO_TOKEN,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER_SCRIPT = (
    REPO_ROOT / "scripts/ops/"
    "materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
    "economic_evaluation_execution_infrastructure_v0.py"
)


def test_materializer_script_present() -> None:
    assert MATERIALIZER_SCRIPT.is_file()


def test_materializer_rejects_invalid_go_token() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        with pytest.raises(SystemExit) as exc:
            materializer_module.run_materialization(
                confirm="GO_INVALID",
                durable_evidence_root=Path(tmp),
                primary_worktree=REPO_ROOT,
                staging_root=REPO_ROOT,
            )
        assert exc.value.code == 2


def test_materializer_cli_rejects_invalid_go_token() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(MATERIALIZER_SCRIPT),
            "--confirm",
            "GO_INVALID",
            "--primary-worktree",
            str(REPO_ROOT),
            "--durable-evidence-root",
            tempfile.mkdtemp(prefix="cs_lead_lag_mat_cli_"),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "ERR:confirm_go_token_required" in proc.stderr


def test_materializer_infra_go_produces_manifest_bundle(tmp_path: Path) -> None:
    if not materializer_module.DEFAULT_STAGING_ROOT.is_dir():
        pytest.skip("default staging root not present")
    result = materializer_module.run_materialization(
        confirm=INFRASTRUCTURE_GO_TOKEN,
        durable_evidence_root=tmp_path,
        primary_worktree=REPO_ROOT,
        staging_root=materializer_module.DEFAULT_STAGING_ROOT,
    )
    assert result["economic_evaluation_executed"] is False
    assert result["manifest_verify_rc"] == 0
    bundle_dir = Path(result["durable_evidence_path"])
    assert (bundle_dir / "MANIFEST.sha256").is_file()
    assert (bundle_dir / "MANIFEST_VERIFY.log").is_file()
    assert (bundle_dir / "ECONOMIC_EVALUATION_EXECUTED.txt").read_text(
        encoding="utf-8"
    ).strip() == "ECONOMIC_EVALUATION_EXECUTED=false"
    execution_result = json.loads(
        (bundle_dir / "EXECUTION_RESULT.json").read_text(encoding="utf-8")
    )
    assert execution_result["economic_evaluation_executed"] is False
