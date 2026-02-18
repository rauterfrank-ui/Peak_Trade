from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class CostModelV1:
    # static, conservative defaults (basis points)
    fees_bp: float = 8.0
    slippage_bp: float = 10.0
    impact_bp: float = 0.0
    latency_bp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fees_bp": self.fees_bp,
            "slippage_bp": self.slippage_bp,
            "impact_bp": self.impact_bp,
            "latency_bp": self.latency_bp,
        }


@dataclass(frozen=True)
class DecisionContextV1:
    ts: str
    source: str
    symbol: str
    side: Optional[str]
    qty: float
    order_type: Optional[str]
    session_id: str
    env: str
    is_testnet: bool
    current_price: Optional[float]

    cost_model: CostModelV1

    def to_dict(self) -> Dict[str, Any]:
        # v1: still no feed, but now we pass through current_price and costs
        return {
            "ts": self.ts,
            "source": self.source,
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "order_type": self.order_type,
            "session_id": self.session_id,
            "env": self.env,
            "is_testnet": bool(self.is_testnet),
            "policy": {"action": "UNSPECIFIED", "reason_codes": []},
            "micro": {
                "data_quality": "v1_intent_only",
                "spread_bp": None,
                "book_thin": None,
                "jump_flag": None,
            },
            "forecast": {
                "horizon_s": None,
                "p_up": None,
                "p_down": None,
                "mu_bp": None,
                "sigma_bp": None,
                "calib": None,
            },
            "costs": self.cost_model.to_dict(),
            "regime": {"state": "unknown", "confidence": None},
            "inputs": {"current_price": self.current_price},
        }


def build_decision_context_v1(
    *,
    intent: Any,
    env: str,
    is_testnet: bool,
    current_price: Optional[float] = None,
    source: str = "observability.nowcast.v1",
    ts: Optional[str] = None,
    cost_model: Optional[CostModelV1] = None,
) -> Dict[str, Any]:
    _ts = ts or utc_ts()
    cm = cost_model or CostModelV1()
    ctx = DecisionContextV1(
        ts=_ts,
        source=source,
        symbol=getattr(intent, "symbol", None) or "",
        side=getattr(intent, "side", None),
        qty=float(getattr(intent, "quantity", 0.0) or 0.0),
        order_type=getattr(intent, "order_type", None),
        session_id=getattr(intent, "session_id", "default"),
        env=env,
        is_testnet=bool(is_testnet),
        current_price=float(current_price) if current_price is not None else None,
        cost_model=cm,
    )
    return ctx.to_dict()
