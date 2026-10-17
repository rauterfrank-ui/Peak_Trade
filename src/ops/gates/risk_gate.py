from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

# Default path aligned with KillSwitch persistence (see config / pipeline bounded_pilot).
# Relative to the repository root of this checkout, never to the process CWD.
DEFAULT_KILL_SWITCH_STATE_PATH = "data/kill_switch/state.json"

# Env vars for kill-switch state file path (canonical first; legacy alias for older tooling).
# Never honored as a redirect: a set override is rejected fail-closed in every process.
KILL_SWITCH_STATE_PATH_ENV_VARS = (
    "PEAK_KILL_SWITCH_STATE_PATH",
    "PEAKTRADE_KILL_SWITCH_STATE_PATH",
)

_KILL_SWITCH_STATE_ROOT = Path(__file__).resolve().parents[3]
_KILL_SWITCH_BLOCKING_STATES = frozenset({"KILLED", "RECOVERING"})
_KILL_SWITCH_NON_BLOCKING_STATES = frozenset({"ACTIVE", "DISABLED"})


def kill_switch_state_path_from_env() -> Optional[str]:
    """Return first non-empty path from env, or ``None`` to use the default file path."""
    for key in KILL_SWITCH_STATE_PATH_ENV_VARS:
        raw = os.getenv(key, "").strip()
        if raw:
            return raw
    return None


def kill_switch_env_override_rejected() -> bool:
    """True when an env path override is set (fail-closed signal; it never redirects)."""
    return kill_switch_state_path_from_env() is not None


def _anchor_kill_switch_path(raw: str) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = _KILL_SWITCH_STATE_ROOT / candidate
    return candidate.resolve()


def canonical_kill_switch_state_path() -> str:
    """Single absolute persist/read path shared by the KillSwitch writer and every reader.

    Anchored at the repository root of this checkout. Independent of the process
    CWD, the environment and imported modules.
    """
    return str(_anchor_kill_switch_path(DEFAULT_KILL_SWITCH_STATE_PATH))


def legacy_cwd_kill_switch_state_paths() -> tuple[str, ...]:
    """CWD-relative legacy location when it differs from the canonical path (deny-only)."""
    resolved = str(Path(DEFAULT_KILL_SWITCH_STATE_PATH).resolve())
    return () if resolved == canonical_kill_switch_state_path() else (resolved,)


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
    - ``False`` — file exists, parsed, and state is a valid non-blocking enum
      (``ACTIVE`` or ``DISABLED``).
    - ``None`` — file missing, unreadable, or semantically invalid. Callers that
      treat the path as configured/expected must fail-closed rather than treat
      this as ACTIVE.
    """
    path = Path(state_path or canonical_kill_switch_state_path())
    if not path.is_file():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        state = str(data.get("state", "")).strip().upper()
    except Exception:
        return None
    if state in _KILL_SWITCH_BLOCKING_STATES:
        return True
    if state in _KILL_SWITCH_NON_BLOCKING_STATES:
        return False
    return None


def kill_switch_should_block_trading(*, explicit_active: bool = False) -> bool:
    """
    Canonical execution-side kill-switch block reader.

    - If ``explicit_active`` is True (e.g. orchestrator constructor), block.
    - Else read state via :func:`canonical_kill_switch_state_path` and
      :func:`resolve_kill_switch_limit_from_state_file`.
    - ``KILLED`` / ``RECOVERING`` block.
    - Valid ``ACTIVE`` / ``DISABLED`` do not block from the file.
    - Configured path missing, or an existing file that is unreadable or
      semantically invalid, fail-closed (block).
    - When no state path is configured and the default file is absent,
      ``PEAK_KILL_SWITCH=1`` remains an explicit operator deny overlay.
      It is not a second persisted kill-state machine.
    - A set env path override blocks (never redirects).
    - A CWD-relative legacy state file that is not a valid non-blocking state blocks.
    """
    if explicit_active:
        return True
    if kill_switch_env_override_rejected():
        return True
    for legacy in legacy_cwd_kill_switch_state_paths():
        if (
            Path(legacy).is_file()
            and resolve_kill_switch_limit_from_state_file(legacy) is not False
        ):
            return True
    path = canonical_kill_switch_state_path()
    resolved = resolve_kill_switch_limit_from_state_file(path)
    if resolved is True:
        return True
    if resolved is False:
        return False
    if Path(path).is_file():
        return True
    return os.getenv("PEAK_KILL_SWITCH", "0") == "1"


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
