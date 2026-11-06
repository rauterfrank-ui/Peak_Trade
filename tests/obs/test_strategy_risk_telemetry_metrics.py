from typing import Optional

import pytest

try:
    import prometheus_client  # type: ignore
    from prometheus_client.core import REGISTRY  # type: ignore
    from prometheus_client.exposition import generate_latest  # type: ignore

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover
    prometheus_client = None  # type: ignore
    REGISTRY = None  # type: ignore
    generate_latest = None  # type: ignore
    _PROM_AVAILABLE = False


def _metrics_text() -> str:
    assert _PROM_AVAILABLE and generate_latest is not None and REGISTRY is not None
    return generate_latest(REGISTRY).decode("utf-8")


def _parse_labels(raw: str) -> dict[str, str]:
    raw = raw.strip()
    if not raw:
        return {}
    out: dict[str, str] = {}
    for part in raw.split(","):
        k, v = part.split("=", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        out[k] = v
    return out


def _series_value(
    text: str, *, name: str, labels: Optional[dict[str, str]] = None
) -> Optional[float]:
    labels = labels or {}
    for ln in text.splitlines():
        if not ln or ln.startswith("#"):
            continue
        if not ln.startswith(name):
            continue
        if "{" in ln:
            prefix, rest = ln.split("{", 1)
            if prefix != name:
                continue
            label_str, value_str = rest.split("}", 1)
            got = _parse_labels(label_str)
            if got != labels:
                continue
            return float(value_str.strip().split()[0])
        if labels:
            continue
        parts = ln.split()
        if parts and parts[0] == name and len(parts) >= 2:
            return float(parts[1])
    return None


def test_strategy_signals_total_increments() -> None:
    from src.obs import strategy_risk_telemetry as srt

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    labels = {"strategy_id": "ma_crossover", "signal": "long"}
    before = (
        _series_value(_metrics_text(), name="peaktrade_strategy_signals_total", labels=labels)
        or 0.0
    )

    srt.inc_strategy_signal(strategy_id="MA_Crossover", signal="long", n=1)

    after = (
        _series_value(_metrics_text(), name="peaktrade_strategy_signals_total", labels=labels)
        or 0.0
    )
    assert after == before + 1.0


def test_strategy_decisions_total_increments() -> None:
    from src.obs import strategy_risk_telemetry as srt

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    labels = {"strategy_id": "ma_crossover", "decision": "entry_long"}
    before = (
        _series_value(_metrics_text(), name="peaktrade_strategy_decisions_total", labels=labels)
        or 0.0
    )

    srt.inc_strategy_decision(strategy_id="MA_Crossover", decision="entry_long", n=2)

    after = (
        _series_value(_metrics_text(), name="peaktrade_strategy_decisions_total", labels=labels)
        or 0.0
    )
    assert after == before + 2.0


def test_risk_checks_total_and_blocks_total_increment() -> None:
    from src.obs import strategy_risk_telemetry as srt

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    labels = {"check": "runtime_risk.evaluate_pre_order", "result": "block"}
    before = (
        _series_value(_metrics_text(), name="peaktrade_risk_checks_total", labels=labels) or 0.0
    )
    srt.inc_risk_check(check="runtime_risk.evaluate_pre_order", result="block", n=1)
    after = _series_value(_metrics_text(), name="peaktrade_risk_checks_total", labels=labels) or 0.0
    assert after == before + 1.0

    block_labels = {"reason": "runtime:reject"}
    before_b = (
        _series_value(_metrics_text(), name="peaktrade_risk_blocks_total", labels=block_labels)
        or 0.0
    )
    srt.inc_risk_block(reason="runtime:reject", n=1)
    after_b = (
        _series_value(_metrics_text(), name="peaktrade_risk_blocks_total", labels=block_labels)
        or 0.0
    )
    assert after_b == before_b + 1.0


def test_strategy_risk_telemetry_no_crash_without_prometheus_client() -> None:
    """
    Even when prometheus_client is missing, telemetry must stay importable and no-op.
    """
    from src.obs import strategy_risk_telemetry as srt

    srt.inc_strategy_signal(strategy_id="any", signal="long", n=1)
    srt.inc_strategy_decision(strategy_id="any", decision="entry_long", n=1)
    srt.set_strategy_position_gross_exposure(strategy_id="any", ccy="EUR", exposure=123.0)
    srt.inc_risk_check(check="live_limits.check_orders", result="allow", n=1)
    srt.set_risk_limit_utilization(limit_id="max_total_exposure", utilization_0_1=0.5)
    srt.inc_risk_block(reason="limit:max_total_exposure", n=1)
