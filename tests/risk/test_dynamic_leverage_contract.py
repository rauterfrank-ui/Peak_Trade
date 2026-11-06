from __future__ import annotations

import math
import pytest

from src.risk.dynamic_leverage import DynamicLeverageConfig, compute_dynamic_leverage


def test_hard_cap_and_bounds():
    cfg = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=2.0)
    assert compute_dynamic_leverage(strength=0.0, cfg=cfg) == pytest.approx(1.0)
    assert compute_dynamic_leverage(strength=1.0, cfg=cfg) == pytest.approx(50.0)
    assert compute_dynamic_leverage(strength=2.0, cfg=cfg) == pytest.approx(50.0)  # clamp strength
    assert compute_dynamic_leverage(strength=-1.0, cfg=cfg) == pytest.approx(1.0)  # clamp strength


def test_monotonic_in_strength():
    cfg = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=3.0)
    prev = -math.inf
    for i in range(0, 101):
        s = i / 100.0
        lv = compute_dynamic_leverage(strength=s, cfg=cfg)
        assert lv >= prev
        prev = lv


def test_gamma_changes_curve_but_respects_caps():
    cfg1 = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=1.0)
    cfg2 = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=4.0)
    lv1 = compute_dynamic_leverage(strength=0.5, cfg=cfg1)
    lv2 = compute_dynamic_leverage(strength=0.5, cfg=cfg2)
    assert lv2 <= lv1  # higher gamma => more conservative mid-strength
    assert 1.0 <= lv1 <= 50.0
    assert 1.0 <= lv2 <= 50.0


def test_fail_closed_on_invalid_config():
    with pytest.raises(ValueError):
        compute_dynamic_leverage(
            strength=0.5, cfg=DynamicLeverageConfig(min_leverage=-1.0, max_leverage=50.0, gamma=2.0)
        )
    with pytest.raises(ValueError):
        compute_dynamic_leverage(
            strength=0.5, cfg=DynamicLeverageConfig(min_leverage=10.0, max_leverage=5.0, gamma=2.0)
        )
    with pytest.raises(ValueError):
        compute_dynamic_leverage(
            strength=0.5, cfg=DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=0.5)
        )


def test_fail_closed_on_nan_strength():
    cfg = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=2.0)
    with pytest.raises(ValueError):
        compute_dynamic_leverage(strength=float("nan"), cfg=cfg)
