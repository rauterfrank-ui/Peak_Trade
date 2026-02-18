from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class DecisionContextV0:
    """
    Minimal deterministic observer/nowcast context builder.
    Phase v0: no market data feeds; uses only intent + env flags.
    Output is JSON-serializable via to_dict().
    """

    ts: str
    source: str
    symbol: str
    side: Optional[str]
    qty: float
    order_type: Optional[str]
    session_id: str
    env: str
    is_testnet: bool

    policy_action: str = "UNSPECIFIED"

    def to_dict(self) -> Dict[str, Any]:
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
            "policy": {"action": self.policy_action, "reason_codes": []},
            # v0 placeholders (stable keys)
            "micro": {
                "data_quality": "v0_no_feed",
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
            "costs": {
                "fees_bp": None,
                "slippage_bp": None,
                "impact_bp": None,
                "latency_bp": None,
            },
            "regime": {"state": "unknown", "confidence": None},
        }


def build_decision_context_v0(
    *,
    intent: Any,
    env: str,
    is_testnet: bool,
    source: str = "observability.nowcast.v0",
    ts: Optional[str] = None,
) -> Dict[str, Any]:
    _ts = ts or utc_ts()
    ctx = DecisionContextV0(
        ts=_ts,
        source=source,
        symbol=getattr(intent, "symbol", None) or "",
        side=getattr(intent, "side", None),
        qty=float(getattr(intent, "quantity", 0.0) or 0.0),
        order_type=getattr(intent, "order_type", None),
        session_id=getattr(intent, "session_id", "default"),
        env=env,
        is_testnet=bool(is_testnet),
    )
    return ctx.to_dict()
