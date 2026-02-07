from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class RiskDenyReason(str, Enum):
    DISABLED = "disabled"
    STALE_DATA = "stale_data"
    MAX_NOTIONAL = "max_notional"
    MAX_ORDER_SIZE = "max_order_size"
    MAX_POSITION = "max_position"
    LOSS_LIMIT = "loss_limit"
    KILL_SWITCH = "kill_switch"
    INVALID_CONFIG = "invalid_config"


@dataclass(frozen=True)
class RiskLimits:
    enabled: bool = True
    kill_switch: bool = False
    max_notional_usd: float = 0.0
    max_order_size: float = 0.0
    max_position: float = 0.0
    max_session_loss_usd: float = 0.0
    max_data_age_seconds: int = 0


@dataclass(frozen=True)
class RiskContext:
    # values should be precomputed by caller; RiskGate stays pure
    now_epoch: int
    market_data_age_seconds: int
    session_pnl_usd: float
    current_position: float  # in base units
    order_size: float  # in base units
    order_notional_usd: float


@dataclass(frozen=True)
class RiskDecision:
    allow: bool
    reason: Optional[RiskDenyReason]
    details: Dict[str, str]


def evaluate_risk(limits: RiskLimits, ctx: RiskContext) -> RiskDecision:
    if not limits.enabled:
        return RiskDecision(False, RiskDenyReason.DISABLED, {"enabled": "false"})
    if limits.kill_switch:
        return RiskDecision(False, RiskDenyReason.KILL_SWITCH, {"kill_switch": "true"})

    if (
        limits.max_data_age_seconds > 0
        and ctx.market_data_age_seconds > limits.max_data_age_seconds
    ):
        return RiskDecision(
            False,
            RiskDenyReason.STALE_DATA,
            {"age_s": str(ctx.market_data_age_seconds)},
        )

    if limits.max_notional_usd > 0 and ctx.order_notional_usd > limits.max_notional_usd:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_NOTIONAL,
            {"notional_usd": str(ctx.order_notional_usd)},
        )

    if limits.max_order_size > 0 and abs(ctx.order_size) > limits.max_order_size:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_ORDER_SIZE,
            {"order_size": str(ctx.order_size)},
        )

    if limits.max_position > 0 and abs(ctx.current_position + ctx.order_size) > limits.max_position:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_POSITION,
            {"next_pos": str(ctx.current_position + ctx.order_size)},
        )

    if limits.max_session_loss_usd > 0 and ctx.session_pnl_usd < -abs(limits.max_session_loss_usd):
        return RiskDecision(
            False,
            RiskDenyReason.LOSS_LIMIT,
            {"session_pnl_usd": str(ctx.session_pnl_usd)},
        )

    return RiskDecision(True, None, {})
