from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_bounded_final_research_fleet_runner_exists() -> None:
    assert Path(
        "scripts/research/bounded_final_research_fleet_offline_economic_evaluation_v0.py"
    ).exists()


def test_bounded_final_research_fleet_runner_help() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/bounded_final_research_fleet_offline_economic_evaluation_v0.py",
            "--help",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0
    assert "--fleet" in result.stdout
    assert "--offline-only" in result.stdout
    assert "--no-runtime" in result.stdout


def test_bounded_final_research_fleet_runner_fail_closed_on_wrong_fleet(tmp_path: Path) -> None:
    out = tmp_path / "evidence"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/bounded_final_research_fleet_offline_economic_evaluation_v0.py",
            "--repo-root",
            ".",
            "--output-dir",
            str(out),
            "--operator",
            "Frank Rauter",
            "--go-token",
            "GO_IMPLEMENT_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_RUNNER_V0",
            "--fleet",
            "trend_following",
            "--futures-only",
            "--offline-only",
            "--no-runtime",
            "--no-orders",
            "--require-full-canonical-chain-wired",
            "--require-backtest-runtime-decision-parity-pass",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(
        (out / "bounded_final_research_fleet_offline_economic_evaluation_v0.json").read_text()
    )
    assert payload["status"] == "FAIL_CLOSED"
    assert "FINAL_RESEARCH_FLEET_MISMATCH" in payload["reason_codes"]
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["runtime_rewire_admissible"] is False
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"


def test_bounded_final_research_fleet_runner_passes_or_fail_closed_with_manifest(
    tmp_path: Path,
) -> None:
    out = tmp_path / "evidence"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/bounded_final_research_fleet_offline_economic_evaluation_v0.py",
            "--repo-root",
            ".",
            "--output-dir",
            str(out),
            "--operator",
            "Frank Rauter",
            "--go-token",
            "GO_IMPLEMENT_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_RUNNER_V0",
            "--fleet",
            "trend_following,bollinger_bands,momentum_1h",
            "--futures-only",
            "--offline-only",
            "--no-runtime",
            "--no-orders",
            "--require-full-canonical-chain-wired",
            "--require-backtest-runtime-decision-parity-pass",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode in {0, 1}
    assert (out / "bounded_final_research_fleet_offline_economic_evaluation_v0.json").exists()
    assert (out / "final_report.txt").exists()
    assert (out / "MANIFEST.sha256").exists()
    assert (out / "MANIFEST.verify.rc").read_text().strip() == "0"
    payload = json.loads(
        (out / "bounded_final_research_fleet_offline_economic_evaluation_v0.json").read_text()
    )
    assert payload["final_research_fleet"] == ["trend_following", "bollinger_bands", "momentum_1h"]
    assert payload["futures_only"] is True
    assert payload["bitcoin_direction_allowed"] is False
    assert payload["offline_only"] is True
    assert payload["no_runtime"] is True
    assert payload["no_orders"] is True
    assert payload["system_economic_evidence_admissible"] is False
    assert payload["runtime_rewire_admissible"] is False
