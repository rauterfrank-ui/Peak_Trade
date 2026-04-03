"""
Smoke tests for scripts/run_study_optuna_placeholder.py (J2 minimal slice).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import importlib.util

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "scripts" / "run_study_optuna_placeholder.py"
)

OPTUNA_AVAILABLE = importlib.util.find_spec("optuna") is not None


def test_script_exists():
    assert SCRIPT_PATH.is_file()


def test_help_exits_zero():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "--study-name" in out
    assert "--trials" in out
    assert "--direction" in out
    assert "--dry-run" in out or "dry-run" in out or "no-dry-run" in out
    assert "NO-LIVE" in out
    assert "order execution" in out.lower()


def test_default_is_dry_run_no_optuna_needed():
    """Ohne Argumente: Dry-Run, Exit 0, auch ohne Optuna."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "DRY-RUN" in result.stdout or "Dry" in result.stdout
    assert "Toy-Objective" in result.stdout or "toy" in result.stdout.lower()


def test_trials_invalid_exits_nonzero():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--trials", "0", "--no-dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="optuna not installed")
def test_no_dry_run_runs_deterministic_toy_study():
    """Mit Optuna: --no-dry-run führt deterministische Demo aus."""
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--no-dry-run",
        "--trials",
        "5",
        "--seed",
        "42",
        "--study-name",
        "pytest_j2_toy",
        "--direction",
        "minimize",
    ]
    r1 = subprocess.run(cmd, capture_output=True, text=True, check=False)
    r2 = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert r1.returncode == 0
    assert r2.returncode == 0
    assert "best_value" in r1.stdout
    assert "best_params" in r1.stdout
    # Gleiche Seeds → gleiche Optuna-Ergebnisse
    assert r1.stdout == r2.stdout


@pytest.mark.skipif(not OPTUNA_AVAILABLE, reason="optuna not installed")
def test_no_dry_run_maximize():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--no-dry-run",
            "--trials",
            "3",
            "--seed",
            "7",
            "--direction",
            "maximize",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "best_value" in result.stdout


def test_import_module_functions():
    """Direkter Import (sys.path scripts) für parse_args."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_study_optuna_placeholder",
        SCRIPT_PATH,
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ns = mod.parse_args(["--trials", "2", "--study-name", "x"])
    assert ns.trials == 2
    assert ns.study_name == "x"
    assert ns.dry_run is True

    ns2 = mod.parse_args(["--no-dry-run"])
    assert ns2.dry_run is False
