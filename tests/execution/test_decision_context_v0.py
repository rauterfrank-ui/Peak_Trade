from typing import Any, Dict

from src.observability.nowcast.decision_context_v0 import build_decision_context_v0


class DummyIntent:
    def __init__(self) -> None:
        self.symbol = "BTC/USDT"
        self.side = "buy"
        self.quantity = 1.0
        self.order_type = "market"
        self.session_id = "default"
        self.current_price = 50000.0


def test_build_decision_context_v0_has_stable_keys() -> None:
    intent = DummyIntent()
    d: Dict[str, Any] = build_decision_context_v0(intent=intent, env="shadow", is_testnet=False)

    for k in [
        "ts",
        "source",
        "symbol",
        "side",
        "qty",
        "order_type",
        "session_id",
        "env",
        "is_testnet",
    ]:
        assert k in d

    for k in ["policy", "micro", "forecast", "costs", "regime"]:
        assert k in d
        assert isinstance(d[k], dict)
