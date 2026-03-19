"""Tests for scripts/ops/run_bounded_pilot_with_local_secrets.py — Local Bounded Secret Launcher."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_with_local_secrets.py"


def test_script_exists() -> None:
    """Script file exists."""
    assert SCRIPT.is_file()


def test_fail_closed_when_env_file_missing(tmp_path: Path) -> None:
    """Launcher aborts when env file is missing."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(tmp_path / "missing.env"), "--dry-check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode == 2
    assert "FAIL_CLOSED" in r.stderr or "missing" in r.stderr.lower()


def test_fail_closed_when_required_vars_missing(tmp_path: Path) -> None:
    """Launcher aborts when required vars are missing."""
    env_file = tmp_path / "bounded.env"
    env_file.write_text("KRAKEN_API_KEY=abc\n")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file), "--dry-check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode == 2
    assert "FAIL_CLOSED" in r.stderr or "missing" in r.stderr.lower()


def test_fail_closed_for_wrong_mode(tmp_path: Path) -> None:
    """Launcher aborts for unsupported mode (e.g. paper)."""
    env_file = tmp_path / "bounded.env"
    env_file.write_text("KRAKEN_API_KEY=abc\nKRAKEN_API_SECRET=xyz\n")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file), "--mode", "paper", "--dry-check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode == 2
    assert "FAIL_CLOSED" in r.stderr or "unsupported mode" in r.stderr.lower()


def test_dry_check_succeeds_for_bounded_mode(tmp_path: Path) -> None:
    """Dry-check succeeds when env file is complete and mode is bounded_pilot."""
    env_file = tmp_path / "bounded.env"
    env_file.write_text(
        "KRAKEN_API_KEY=abc\n"
        "KRAKEN_API_SECRET=xyz\n"
        "PT_EXEC_EVENTS_ENABLED=true\n"
    )
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file), "--dry-check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode == 0
    assert "LOCAL_BOUNDED_SECRET_SOURCE" in r.stdout
    assert "LOCAL_BOUNDED_SECRET_MODE=bounded_pilot" in r.stdout


def test_dry_check_succeeds_for_acceptance_mode(tmp_path: Path) -> None:
    """Dry-check succeeds when env file is complete and mode is acceptance."""
    env_file = tmp_path / "bounded.env"
    env_file.write_text(
        "KRAKEN_API_KEY=abc\n"
        "KRAKEN_API_SECRET=xyz\n"
        "PT_EXEC_EVENTS_ENABLED=true\n"
    )
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--env-file", str(env_file), "--mode", "acceptance", "--dry-check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode == 0
    assert "LOCAL_BOUNDED_SECRET_MODE=acceptance" in r.stdout
