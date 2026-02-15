from __future__ import annotations

import pytest

from src.ai.regimes.regime_switch_v1 import Regime, regime_switch_v1


def test_regime_switch_v1_up() -> None:
    d = regime_switch_v1(score=0.2, neutral_band=0.1)
    assert d.regime == Regime.UP


def test_regime_switch_v1_down() -> None:
    d = regime_switch_v1(score=-0.2, neutral_band=0.1)
    assert d.regime == Regime.DOWN


def test_regime_switch_v1_neutral() -> None:
    d = regime_switch_v1(score=0.05, neutral_band=0.1)
    assert d.regime == Regime.NEUTRAL


def test_regime_switch_v1_bad_band() -> None:
    with pytest.raises(ValueError):
        regime_switch_v1(score=0.0, neutral_band=-1.0)
