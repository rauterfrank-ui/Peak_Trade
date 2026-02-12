from __future__ import annotations

from src.aiops.p4c.regime_rules_v0 import compute_outlook_v0


def test_fixture_rules_expectation() -> None:
    features = {
        "volatility_14d": {"BTC/USDT": 0.55, "ETH/USDT": 0.62},
        "trend_7d": {"BTC/USDT": 0.12, "ETH/USDT": -0.04},
    }
    o = compute_outlook_v0(features)
    # mean_tr = (0.12 + -0.04)/2 = 0.04 => NEUTRAL
    # mean_vol = (0.55 + 0.62)/2 = 0.585 => not high
    assert o.regime == "NEUTRAL"
    assert o.no_trade is False
    assert o.no_trade_reasons == []


def test_missing_features_triggers_no_trade() -> None:
    o = compute_outlook_v0({"volatility_14d": {"BTC/USDT": 0.5}})
    assert o.no_trade is True
    assert "MISSING_FEATURES" in o.no_trade_reasons


def test_extreme_vol_triggers_no_trade() -> None:
    features = {"volatility_14d": {"BTC/USDT": 0.95}, "trend_7d": {"BTC/USDT": 0.2}}
    o = compute_outlook_v0(features)
    assert o.regime == "HIGH_VOL"
    assert o.no_trade is True
    assert "VOL_EXTREME" in o.no_trade_reasons
