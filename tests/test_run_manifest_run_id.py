"""Deterministische run_id in CLI-Run-Manifesten (_forward_run_manifest)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from _forward_run_manifest import compute_deterministic_run_id  # noqa: E402


def test_compute_deterministic_run_id_stable_for_same_inputs() -> None:
    a = compute_deterministic_run_id(
        script_name="x.py",
        argv=["python", "x.py", "--a", "1"],
        config_path="config.toml",
        git_sha="abc",
    )
    b = compute_deterministic_run_id(
        script_name="x.py",
        argv=["python", "x.py", "--a", "1"],
        config_path="config.toml",
        git_sha="abc",
    )
    assert a == b
    assert len(a) == 64


def test_compute_deterministic_run_id_differs_when_argv_differs() -> None:
    r1 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a", "1"],
        config_path="c.toml",
        git_sha="g",
    )
    r2 = compute_deterministic_run_id(
        script_name="x.py",
        argv=["a", "2"],
        config_path="c.toml",
        git_sha="g",
    )
    assert r1 != r2


def test_compute_deterministic_run_id_none_git_sha_normalized() -> None:
    a = compute_deterministic_run_id(
        script_name="s",
        argv=[],
        config_path="c",
        git_sha=None,
    )
    b = compute_deterministic_run_id(
        script_name="s",
        argv=[],
        config_path="c",
        git_sha=None,
    )
    assert a == b
