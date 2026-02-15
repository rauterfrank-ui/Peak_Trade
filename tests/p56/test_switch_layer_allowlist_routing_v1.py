from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from src.ai.switch_layer.types_v1 import MarketRegimeV1, SwitchDecisionV1
from src.ai.switch_layer.config_v1 import SwitchLayerConfigV1
from src.ai_orchestration.switch_layer_routing_v1 import (
    route_from_switch_decision_v1,
    route_from_switch_decision_with_config_v1,
)


def _mk_decision(regime: MarketRegimeV1) -> SwitchDecisionV1:
    return SwitchDecisionV1(regime=regime, confidence=0.66, evidence={})


def test_routing_deny_by_default_bull() -> None:
    decision = _mk_decision(MarketRegimeV1.BULL)
    out = route_from_switch_decision_v1(decision=decision, allow_bull=None, allow_bear=None)
    assert is_dataclass(out)
    assert out.ai_mode == "disabled"
    assert out.allowed_strategies == ()
    assert out.reason == "deny_by_default"


def test_routing_allowlist_bull_enables_strategies() -> None:
    decision = _mk_decision(MarketRegimeV1.BULL)
    out = route_from_switch_decision_v1(
        decision=decision, allow_bull=["strat_a", "strat_b"], allow_bear=None
    )
    assert out.ai_mode == "shadow"
    assert out.allowed_strategies == ("strat_a", "strat_b")
    assert out.reason == "bull_allowlist"


def test_routing_allowlist_bear_enables_strategies() -> None:
    decision = _mk_decision(MarketRegimeV1.BEAR)
    out = route_from_switch_decision_v1(
        decision=decision, allow_bull=None, allow_bear=["strat_c"]
    )
    assert out.ai_mode == "shadow"
    assert out.allowed_strategies == ("strat_c",)
    assert out.reason == "bear_allowlist"


def test_routing_with_config_deny_by_default() -> None:
    cfg = SwitchLayerConfigV1()
    decision = _mk_decision(MarketRegimeV1.BULL)
    out = route_from_switch_decision_with_config_v1(decision=decision, cfg=cfg)
    assert out.ai_mode == "disabled"
    assert out.allowed_strategies == ()


def test_routing_with_config_allowlist_bull() -> None:
    cfg = SwitchLayerConfigV1(allow_bull_strategies=("s1", "s2"))
    decision = _mk_decision(MarketRegimeV1.BULL)
    out = route_from_switch_decision_with_config_v1(decision=decision, cfg=cfg)
    assert out.ai_mode == "shadow"
    assert out.allowed_strategies == ("s1", "s2")


def test_routing_with_config_allowlist_bear() -> None:
    cfg = SwitchLayerConfigV1(allow_bear_strategies=("s3",))
    decision = _mk_decision(MarketRegimeV1.BEAR)
    out = route_from_switch_decision_with_config_v1(decision=decision, cfg=cfg)
    assert out.ai_mode == "shadow"
    assert out.allowed_strategies == ("s3",)
