"""Tests for scripts/ops/run_with_timeout.py — stdlib subprocess timeout wrapper."""

from __future__ import annotations

import importlib.util
import sys
from io import StringIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_with_timeout.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("run_with_timeout", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def test_fast_command_exits_zero() -> None:
    mod = _load_mod()
    argv = [
        "run_with_timeout.py",
        "--timeout-seconds",
        "30",
        "--",
        sys.executable,
        "-c",
        "raise SystemExit(0)",
    ]
    assert mod.main(argv) == 0


def test_child_nonzero_exit_preserved() -> None:
    mod = _load_mod()
    argv = [
        "run_with_timeout.py",
        "--timeout-seconds",
        "30",
        "--",
        sys.executable,
        "-c",
        "raise SystemExit(19)",
    ]
    assert mod.main(argv) == 19


def test_timeout_returns_124_and_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    argv = [
        "run_with_timeout.py",
        "--timeout-seconds",
        "0.25",
        "--",
        sys.executable,
        "-c",
        "import time; time.sleep(10)",
    ]
    assert mod.main(argv) == mod.TIMEOUT_EXIT == 124
    assert "exceeded" in err.getvalue().lower()
    assert "timeout-seconds" in err.getvalue().lower()


@pytest.mark.parametrize("bad_timeout", ("0", "-1", "0.0"))
def test_non_positive_timeout_fails(bad_timeout: str, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    argv = [
        "run_with_timeout.py",
        "--timeout-seconds",
        bad_timeout,
        "--",
        sys.executable,
        "-c",
        "pass",
    ]
    assert mod.main(argv) == mod.USAGE_EXIT
    assert "timeout-seconds" in err.getvalue().lower()


def test_missing_command_after_separator(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    argv = ["run_with_timeout.py", "--timeout-seconds", "10", "--"]
    assert mod.main(argv) == mod.USAGE_EXIT
    assert "no command" in err.getvalue().lower()


def test_missing_separator(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    argv = ["run_with_timeout.py", "--timeout-seconds", "10", sys.executable, "-c", "pass"]
    assert mod.main(argv) == mod.USAGE_EXIT
    assert "missing" in err.getvalue().lower() and "--" in err.getvalue()


def test_invalid_args_no_timeout_key(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_mod()
    err = StringIO()
    monkeypatch.setattr(sys, "stderr", err)
    argv = ["run_with_timeout.py", "--", sys.executable, "-c", "pass"]
    assert mod.main(argv) == mod.USAGE_EXIT
