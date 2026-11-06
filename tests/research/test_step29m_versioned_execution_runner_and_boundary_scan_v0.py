from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts/research/run_step29m_offline_economic_evaluation_execution_v0.py"


def test_step29m_versioned_execution_runner_exists_and_is_authority_neutral() -> None:
    text = RUNNER.read_text(encoding="utf-8")
    assert "AUTHORITY_EFFECT" in text
    assert "RUNTIME_EFFECT" in text
    assert "ORDERS_ALLOWED" in text
    assert "SCHEDULER_RUNTIME_ALLOWED" in text
    assert "LIVE_AUTHORIZED" in text
    assert "send_order(" not in text
    assert "cancel_order(" not in text
    assert "create_order(" not in text


def test_step29m_runner_emits_manifested_fail_closed_evidence(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(RUNNER), "--out", str(tmp_path)],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr

    result_path = tmp_path / "step29m_execution_result_v0.json"
    report_path = tmp_path / "final_report.txt"
    manifest_path = tmp_path / "MANIFEST.sha256"
    verify_path = tmp_path / "manifest_verify.txt"

    assert result_path.exists()
    assert report_path.exists()
    assert manifest_path.exists()
    assert verify_path.exists()

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    assert payload["authority"]["AUTHORITY_EFFECT"] == "NONE"
    assert payload["authority"]["RUNTIME_EFFECT"] == "NONE"
    assert payload["authority"]["ORDERS_ALLOWED"] is False
    assert payload["authority"]["SCHEDULER_RUNTIME_ALLOWED"] is False
    assert payload["authority"]["LIVE_AUTHORIZED"] is False
    assert payload["execution_chain"]["offline_backtest_executed"] is False
    assert payload["execution_chain"]["walk_forward_executed"] is False
    assert payload["execution_chain"]["monte_carlo_executed"] is False
    assert payload["execution_chain"]["stress_executed"] is False
    assert "MANIFEST_VERIFY_RC=0" in verify_path.read_text(encoding="utf-8")


def test_step29m_scoped_boundary_scan_ignores_legacy_inventory_false_positives() -> None:
    scan_paths = [
        REPO_ROOT / "scripts/research/run_step29m_offline_economic_evaluation_execution_v0.py",
        REPO_ROOT
        / "docs/research/step29m_offline_economic_evaluation_execution_plan_separate_operator_go_required_v0.json",
        REPO_ROOT
        / "docs/research/STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED_V0.md",
    ]

    forbidden = [
        "ORDERS_ALLOWED=true",
        "LIVE_AUTHORIZED=true",
        "SCHEDULER_RUNTIME_ALLOWED=true",
        "send_order(",
        "cancel_order(",
        "create_order(",
    ]

    hits: list[str] = []
    for path in scan_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{token}")

    assert hits == []
