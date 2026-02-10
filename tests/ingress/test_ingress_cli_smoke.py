"""Smoke tests for ingress CLI (A6): module entrypoint, exit code, two path lines. Pointer-only."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cli_empty_input_exits_zero_and_prints_two_paths(tmp_path: Path) -> None:
    """CLI with default/empty input: exit 0, stdout has two lines (feature_view path, capsule path)."""
    base = tmp_path / "ops"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.ingress.cli.ingress_cli",
            "--run-id",
            "smoke1",
            "--base-dir",
            str(base),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert result.returncode == 0
    lines = [s.strip() for s in result.stdout.strip().splitlines() if s.strip()]
    assert len(lines) == 2
    assert lines[0].endswith("smoke1.feature_view.json")
    assert lines[1].endswith("smoke1.capsule.json")
    assert Path(lines[0]).exists()
    assert Path(lines[1]).exists()


def test_cli_with_label_exits_zero(tmp_path: Path) -> None:
    """CLI with --label: exit 0, two path lines."""
    base = tmp_path / "ops"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.ingress.cli.ingress_cli",
            "--run-id",
            "smoke2",
            "--base-dir",
            str(base),
            "--label",
            "env=test",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    assert result.returncode == 0
    lines = [s.strip() for s in result.stdout.strip().splitlines() if s.strip()]
    assert len(lines) == 2
