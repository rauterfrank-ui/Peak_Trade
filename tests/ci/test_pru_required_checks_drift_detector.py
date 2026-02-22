"""Tests for required checks drift detector."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_detector_ok(tmp_path: Path) -> None:
    req = tmp_path / "req.txt"
    req.write_text("X\n", encoding="utf-8")
    wfd = tmp_path / "wfs"
    wfd.mkdir()
    (wfd / "a.yml").write_text(
        "name: X\non: {workflow_dispatch:{}}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps: []\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/required_checks_drift_detector.py",
            "--required-list",
            str(req),
            "--workflows-dir",
            str(wfd),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0


def test_detector_missing(tmp_path: Path) -> None:
    req = tmp_path / "req.txt"
    req.write_text("Y\n", encoding="utf-8")
    wfd = tmp_path / "wfs"
    wfd.mkdir()
    (wfd / "a.yml").write_text(
        "name: X\non: {workflow_dispatch:{}}\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps: []\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/required_checks_drift_detector.py",
            "--required-list",
            str(req),
            "--workflows-dir",
            str(wfd),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
