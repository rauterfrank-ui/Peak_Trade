from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

# Default path aligned with KillSwitch persistence (see config / pipeline bounded_pilot).
DEFAULT_KILL_SWITCH_STATE_PATH = "data/kill_switch/state.json"

# Env vars for kill-switch state file path (canonical first; legacy alias for older tooling).
KILL_SWITCH_STATE_PATH_ENV_VARS = (
    "PEAK_KILL_SWITCH_STATE_PATH",
    "PEAKTRADE_KILL_SWITCH_STATE_PATH",
)


def kill_switch_state_path_from_env() -> Optional[str]:
    """Return first non-empty path from env, or ``None`` to use the default file path."""
    for key in KILL_SWITCH_STATE_PATH_ENV_VARS:
        raw = os.getenv(key, "").strip()
        if raw:
            return raw
    return None


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


def resolve_kill_switch_limit_from_state_file(
    state_path: Optional[str] = None,
) -> Optional[bool]:
    """
    Map persisted kill-switch state to the ``RiskLimits.kill_switch`` flag.

    Reads ``state`` from JSON (same contract as ``data/kill_switch/state.json``).
    Returns:

    - ``True`` — state is ``KILLED`` or ``RECOVERING`` (trading should be denied).
    - ``False`` — file exists, parsed, and state is not blocking (e.g. ``ACTIVE``).
    - ``None`` — file missing or unreadable; caller should apply env fallback
      (e.g. ``PEAK_KILL_SWITCH``).

    On parse errors after the file was found, returns ``None`` so operators can
    still force a block via env without being silently treated as ACTIVE.
    """
    path = Path(state_path or DEFAULT_KILL_SWITCH_STATE_PATH)
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        state = str(data.get("state", "")).strip().upper()
    except Exception:
        return None
    if state in ("KILLED", "RECOVERING"):
        return True
    return False


def kill_switch_should_block_trading(*, explicit_active: bool = False) -> bool:
    """
    Single source for kill-switch blocking (safety, orchestrator, risk hook).

    - If ``explicit_active`` is True (e.g. orchestrator constructor), block.
    - Else read state via :func:`kill_switch_state_path_from_env` (default path
      if unset) and :func:`resolve_kill_switch_limit_from_state_file`.
    - If resolver returns ``True``, block.
    - If ``None`` (missing/unreadable file), fall back to ``PEAK_KILL_SWITCH``.
    - If ``False`` (file says ACTIVE), do not block.
    """
    if explicit_active:
        return True
    path = kill_switch_state_path_from_env()
    resolved = resolve_kill_switch_limit_from_state_file(path)
    if resolved is True:
        return True
    if resolved is None:
        return os.getenv("PEAK_KILL_SWITCH", "0") == "1"
    return False


def evaluate_risk(limits: RiskLimits, ctx: RiskContext) -> RiskDecision:
    if not limits.enabled:
        return RiskDecision(
            False,
            RiskDenyReason.DISABLED,
            {"enabled": "false", "limits_enabled": str(limits.enabled).lower()},
        )
    if limits.kill_switch:
        return RiskDecision(
            False,
            RiskDenyReason.KILL_SWITCH,
            {
                "kill_switch": "true",
                "limits_kill_switch": str(limits.kill_switch).lower(),
            },
        )

    if (
        limits.max_data_age_seconds > 0
        and ctx.market_data_age_seconds > limits.max_data_age_seconds
    ):
        return RiskDecision(
            False,
            RiskDenyReason.STALE_DATA,
            {
                "age_s": str(ctx.market_data_age_seconds),
                "max_data_age_seconds": str(limits.max_data_age_seconds),
            },
        )

    if limits.max_notional_usd > 0 and ctx.order_notional_usd > limits.max_notional_usd:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_NOTIONAL,
            {
                "notional_usd": str(ctx.order_notional_usd),
                "max_notional_usd": str(limits.max_notional_usd),
            },
        )

    if limits.max_order_size > 0 and abs(ctx.order_size) > limits.max_order_size:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_ORDER_SIZE,
            {
                "order_size": str(ctx.order_size),
                "max_order_size": str(limits.max_order_size),
            },
        )

    if limits.max_position > 0 and abs(ctx.current_position + ctx.order_size) > limits.max_position:
        return RiskDecision(
            False,
            RiskDenyReason.MAX_POSITION,
            {
                "next_pos": str(ctx.current_position + ctx.order_size),
                "max_position": str(limits.max_position),
            },
        )

    if limits.max_session_loss_usd > 0 and ctx.session_pnl_usd < -abs(limits.max_session_loss_usd):
        return RiskDecision(
            False,
            RiskDenyReason.LOSS_LIMIT,
            {
                "session_pnl_usd": str(ctx.session_pnl_usd),
                "max_session_loss_usd": str(limits.max_session_loss_usd),
            },
        )

    return RiskDecision(True, None, {})
