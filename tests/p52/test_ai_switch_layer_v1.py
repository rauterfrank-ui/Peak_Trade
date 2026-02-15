from __future__ import annotations

from src.ai.switch_layer import MarketRegimeV1, SwitchLayerConfigV1, decide_regime_v1


def test_switch_layer_insufficient_samples_neutral():
    cfg = SwitchLayerConfigV1(require_min_samples=10, slow_window=10, fast_window=5)
    dec = decide_regime_v1([0.001] * 9, cfg=cfg)
    assert dec.regime == MarketRegimeV1.NEUTRAL
    assert dec.confidence >= cfg.min_confidence
    assert dec.evidence["reason"] == "insufficient_samples"


def test_switch_layer_bull():
    cfg = SwitchLayerConfigV1(
        require_min_samples=60,
        slow_window=50,
        fast_window=20,
        bull_threshold=0.001,
        bear_threshold=-0.001,
    )
    rets = [0.002] * 80
    dec = decide_regime_v1(rets, cfg=cfg)
    assert dec.regime == MarketRegimeV1.BULL
    assert 0.55 <= dec.confidence <= 0.95


def test_switch_layer_bear():
    cfg = SwitchLayerConfigV1(
        require_min_samples=60,
        slow_window=50,
        fast_window=20,
        bull_threshold=0.001,
        bear_threshold=-0.001,
    )
    rets = [-0.002] * 80
    dec = decide_regime_v1(rets, cfg=cfg)
    assert dec.regime == MarketRegimeV1.BEAR
    assert 0.55 <= dec.confidence <= 0.95


def test_switch_layer_deterministic_same_input_same_output():
    cfg = SwitchLayerConfigV1(
        require_min_samples=60,
        slow_window=50,
        fast_window=20,
        bull_threshold=0.001,
        bear_threshold=-0.001,
    )
    rets = [0.0] * 30 + [0.0015] * 60
    a = decide_regime_v1(rets, cfg=cfg)
    b = decide_regime_v1(rets, cfg=cfg)
    assert a.regime == b.regime
    assert a.confidence == b.confidence
    assert a.evidence == b.evidence
