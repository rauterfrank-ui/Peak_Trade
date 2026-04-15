"""Contract tests for execution watch metrics env flag (read-only helper)."""

from __future__ import annotations

import pytest

from src.webui.execution_watch_api_v0_2 import _enabled_exec_watch_metrics

_ENV = "PEAK_TRADE_EXECUTION_WATCH_METRICS_ENABLED"


@pytest.mark.parametrize(
    ("raw", "expect_enabled"),
    [
        (None, False),
        ("0", False),
        ("1", True),
        ("true", False),
        ("1 ", False),
        (" 1", False),
    ],
)
def test_peak_trade_execution_watch_metrics_enabled_strict_literal_one(
    monkeypatch: pytest.MonkeyPatch,
    raw: str | None,
    expect_enabled: bool,
) -> None:
    """``os.getenv(..., '0') == '1'`` — no strip; only exact ``1`` enables (current contract)."""
    if raw is None:
        monkeypatch.delenv(_ENV, raising=False)
    else:
        monkeypatch.setenv(_ENV, raw)
    assert _enabled_exec_watch_metrics() is expect_enabled
