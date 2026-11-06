"""Smoke tests for scripts/ops/reference_drift_report_v1.py (read-only visibility layer)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "reference_drift_report_v1.py"

REQUIRED_TOP_LEVEL_FIELDS = (
    "total_violations",
    "affected_files",
    "classification_counts",
    "legacy_list",
    "broken_list",
    "timestamp",
    "git_head",
)


def _git_porcelain(root: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


@pytest.fixture(scope="module")
def repo_porcelain_before() -> str:
    return _git_porcelain(ROOT)


def test_script_runs_and_writes_json(tmp_path: Path, repo_porcelain_before: str) -> None:
    out_path = tmp_path / "reference_drift_v1.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert out_path.is_file(), "expected JSON report file"


def test_report_has_required_fields(tmp_path: Path) -> None:
    out_path = tmp_path / "reference_drift_v1.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        assert field in payload, f"missing field: {field}"

    counts = payload["classification_counts"]
    assert set(counts) >= {"LEGACY", "BROKEN", "UNKNOWN"}
    assert payload["total_violations"] == sum(counts.values())
    assert isinstance(payload["affected_files"], list)
    assert isinstance(payload["legacy_list"], list)
    assert isinstance(payload["broken_list"], list)
    assert payload["git_head"]
    assert payload["timestamp"].endswith("Z")


def test_script_does_not_modify_repo(tmp_path: Path, repo_porcelain_before: str) -> None:
    out_path = tmp_path / "reference_drift_v1.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out_path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert _git_porcelain(ROOT) == repo_porcelain_before
