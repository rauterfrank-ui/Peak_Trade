from typing import Any, Dict

from src.observability.nowcast.decision_context_v1 import build_decision_context_v1


class DummyIntent:
    def __init__(self) -> None:
        self.symbol = "BTC/USDT"
        self.side = "buy"
        self.quantity = 1.0
        self.order_type = "market"
        self.session_id = "default"
        self.current_price = 50000.0


def test_build_decision_context_v1_includes_inputs_and_costs() -> None:
    intent = DummyIntent()
    d: Dict[str, Any] = build_decision_context_v1(
        intent=intent,
        env="shadow",
        is_testnet=False,
        current_price=intent.current_price,
        source="test",
    )

    assert "inputs" in d and isinstance(d["inputs"], dict)
    assert d["inputs"]["current_price"] == intent.current_price

    assert "costs" in d and isinstance(d["costs"], dict)
    for k in ["fees_bp", "slippage_bp", "impact_bp", "latency_bp"]:
        assert k in d["costs"]
