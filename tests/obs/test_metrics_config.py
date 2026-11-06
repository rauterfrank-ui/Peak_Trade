from __future__ import annotations

import pytest

from src.obs.metrics_config import get_metrics_port


def test_metrics_port_uses_canonical_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_METRICSD_PORT", "9123")
    monkeypatch.delenv("PEAKTRADE_METRICS_PORT", raising=False)
    assert get_metrics_port(9111) == 9123


def test_metrics_port_uses_legacy_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_METRICSD_PORT", raising=False)
    monkeypatch.setenv("PEAKTRADE_METRICS_PORT", "9124")
    assert get_metrics_port(9111) == 9124
