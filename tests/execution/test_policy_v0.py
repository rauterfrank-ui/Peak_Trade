from typing import Any, Dict

from src.observability.policy.policy_v0 import decide_policy_v0


class DummyIntent:
    def __init__(self, current_price: float = 1.0) -> None:
        self.symbol = "BTC/USDT"
        self.side = "buy"
        self.quantity = 1.0
        self.order_type = "market"
        self.session_id = "default"
        self.current_price = current_price


def test_policy_v0_is_no_trade_in_live() -> None:
    intent = DummyIntent(current_price=50000.0)
    decision_ctx: Dict[str, Any] = {"inputs": {"current_price": 50000.0}}
    p = decide_policy_v0(decision_ctx=decision_ctx, intent=intent, env="live")
    assert p["action"] == "NO_TRADE"
    assert "ENV_LIVE" in p["reason_codes"]


def test_policy_v0_no_trade_without_price() -> None:
    intent = DummyIntent(current_price=0.0)
    decision_ctx: Dict[str, Any] = {"inputs": {"current_price": None}}
    p = decide_policy_v0(decision_ctx=decision_ctx, intent=intent, env="shadow")
    assert p["action"] == "NO_TRADE"
    assert "MISSING_CURRENT_PRICE" in p["reason_codes"]
