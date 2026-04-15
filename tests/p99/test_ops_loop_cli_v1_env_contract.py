"""Contract tests for p99 ops loop CLI integer env defaults and early validation."""

from __future__ import annotations

import pytest

from src.ops.p99.ops_loop_cli_v1 import main


def test_main_invalid_max_age_sec_env_returns_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MAX_AGE_SEC", "not-an-int")
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "MAX_AGE_SEC must be a decimal integer" in err


def test_main_invalid_min_ticks_env_returns_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("MIN_TICKS", "bogus")
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "MIN_TICKS must be a decimal integer" in err


def test_main_empty_max_age_sec_env_returns_2(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Set-but-empty env is not a valid integer (missing effective value)."""
    monkeypatch.setenv("MAX_AGE_SEC", "")
    assert main([]) == 2
    err = capsys.readouterr().err
    assert "MAX_AGE_SEC must be a decimal integer" in err


def test_main_max_age_sec_zero_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--max-age-sec", "0"]) == 2
    assert "positive integer" in capsys.readouterr().err


def test_main_min_ticks_zero_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--min-ticks", "0"]) == 2
    assert "positive integer" in capsys.readouterr().err


def test_main_invalid_mode_returns_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--mode", "live"]) == 2
    assert "paper|shadow" in capsys.readouterr().err
