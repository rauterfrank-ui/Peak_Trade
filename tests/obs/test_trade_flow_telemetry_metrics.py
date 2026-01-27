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


def test_signals_total_increments() -> None:
    from src.obs import trade_flow_telemetry

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    before = (
        _series_value(
            _metrics_text(),
            name="peaktrade_signals_total",
            labels={"strategy_id": "ma_crossover", "symbol": "btc/eur", "signal": "buy"},
        )
        or 0.0
    )

    trade_flow_telemetry.inc_signal(
        strategy_id="MA_Crossover",
        symbol="BTC/EUR",
        signal="buy",
        n=1,
    )

    after = (
        _series_value(
            _metrics_text(),
            name="peaktrade_signals_total",
            labels={"strategy_id": "ma_crossover", "symbol": "btc/eur", "signal": "buy"},
        )
        or 0.0
    )
    assert after == before + 1.0


def test_orders_approved_total_increments() -> None:
    from src.obs import trade_flow_telemetry

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    labels = {
        "strategy_id": "ma_crossover",
        "symbol": "btc/eur",
        "venue": "shadow",
        "order_type": "market",
    }
    before = (
        _series_value(_metrics_text(), name="peaktrade_orders_approved_total", labels=labels) or 0.0
    )

    trade_flow_telemetry.inc_orders_approved(
        strategy_id="MA_Crossover",
        symbol="BTC/EUR",
        venue="shadow",
        order_type="market",
        n=2,
    )

    after = (
        _series_value(_metrics_text(), name="peaktrade_orders_approved_total", labels=labels) or 0.0
    )
    assert after == before + 2.0


def test_orders_blocked_total_increments_with_allowlist_mapping() -> None:
    from src.obs import trade_flow_telemetry

    if not _PROM_AVAILABLE:
        pytest.skip("prometheus_client not installed; counter increment test skipped")

    reason = trade_flow_telemetry.map_block_reason(
        status="blocked_by_risk",
        raw_reason="risk_limits_violated: max_notional",
    )
    assert reason == "limits"

    labels = {"strategy_id": "ma_crossover", "symbol": "btc/eur", "reason": "limits"}
    before = (
        _series_value(_metrics_text(), name="peaktrade_orders_blocked_total", labels=labels) or 0.0
    )

    trade_flow_telemetry.inc_orders_blocked(
        strategy_id="MA_Crossover",
        symbol="BTC/EUR",
        reason=reason,
        n=1,
    )

    after = (
        _series_value(_metrics_text(), name="peaktrade_orders_blocked_total", labels=labels) or 0.0
    )
    assert after == before + 1.0


def test_trade_flow_telemetry_no_crash_without_prometheus_client() -> None:
    """
    Even when prometheus_client is missing, telemetry must stay importable and no-op.
    """
    from src.obs import trade_flow_telemetry

    trade_flow_telemetry.inc_signal(strategy_id="any", symbol="BTC/EUR", signal="buy", n=1)
    trade_flow_telemetry.inc_orders_approved(
        strategy_id="any", symbol="BTC/EUR", venue="shadow", order_type="market", n=1
    )
    trade_flow_telemetry.inc_orders_blocked(
        strategy_id="any", symbol="BTC/EUR", reason="unknown", n=1
    )
