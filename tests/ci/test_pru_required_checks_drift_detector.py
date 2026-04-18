"""Tests for required checks drift detector."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_detector_ok(tmp_path: Path) -> None:
    req = tmp_path / "required_status_checks.json"
    req.write_text('{"required_contexts": ["X"]}\n', encoding="utf-8")
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
            "--required-config",
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
    req = tmp_path / "required_status_checks.json"
    req.write_text('{"required_contexts": ["Y"]}\n', encoding="utf-8")
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
            "--required-config",
            str(req),
            "--workflows-dir",
            str(wfd),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2


def test_detector_rejects_legacy_required_list_flag(tmp_path: Path) -> None:
    req = tmp_path / "required_status_checks.json"
    req.write_text('{"required_contexts": ["X"], "ignored_contexts": []}\n', encoding="utf-8")
    required_list = tmp_path / "required_checks.txt"
    required_list.write_text("X\n", encoding="utf-8")
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
            "--required-config",
            str(req),
            "--required-list",
            str(required_list),
            "--workflows-dir",
            str(wfd),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    assert "--required-list" in r.stderr
    assert "unrecognized arguments" in r.stderr


def test_detector_applies_ignored_contexts_from_json(tmp_path: Path) -> None:
    req = tmp_path / "required_status_checks.json"
    req.write_text(
        '{"required_contexts": ["X", "IGNORED_ONLY"], "ignored_contexts": ["IGNORED_ONLY"]}\n',
        encoding="utf-8",
    )
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
            "--required-config",
            str(req),
            "--workflows-dir",
            str(wfd),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    assert "DRIFT_OK" in r.stdout
