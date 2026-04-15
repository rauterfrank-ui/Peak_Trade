"""Contract tests for p99 ops loop CLI integer env defaults."""

from __future__ import annotations

import pytest

from src.ops.p99.ops_loop_cli_v1 import main


def test_main_invalid_max_age_sec_env_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_AGE_SEC", "not-an-int")
    with pytest.raises(ValueError, match="MAX_AGE_SEC must be a decimal integer"):
        main([])


def test_main_invalid_min_ticks_env_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIN_TICKS", "bogus")
    with pytest.raises(ValueError, match="MIN_TICKS must be a decimal integer"):
        main([])
