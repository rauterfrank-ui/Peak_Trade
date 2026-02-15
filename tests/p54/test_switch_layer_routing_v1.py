from src.ai.switch_layer.types_v1 import MarketRegimeV1, SwitchDecisionV1
from src.ai_orchestration.switch_layer_routing_v1 import route_from_switch_decision_v1


def test_routing_deny_by_default_bull():
    d = SwitchDecisionV1(regime=MarketRegimeV1.BULL, confidence=0.9, evidence={"n": 100})
    r = route_from_switch_decision_v1(decision=d)
    assert r.allowed_strategies == ()
    assert r.ai_mode == "disabled"


def test_routing_allowlist_bull_shadow():
    d = SwitchDecisionV1(regime=MarketRegimeV1.BULL, confidence=0.9, evidence={"n": 100})
    r = route_from_switch_decision_v1(decision=d, allow_bull=["s1", "s2"])
    assert r.allowed_strategies == ("s1", "s2")
    assert r.ai_mode == "shadow"
