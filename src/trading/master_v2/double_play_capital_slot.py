# src/trading/master_v2/double_play_capital_slot.py
"""
Pure Double Play capital slot model: ratchet, release, loss-following base.

Data-only; no I/O, allocation, execution, exchange, or Live authority.
Aligned with docs/ops/specs/MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

DOUBLE_PLAY_CAPITAL_SLOT_LAYER_VERSION = "v0"

_SPLIT_EPS = 1e-9


class CapitalSlotStatus(str, Enum):
    """Per-future capital slot lifecycle (model labels only, non-authority)."""

    ACTIVE = "active"
    RELEASED = "released"


class CapitalSlotReleaseReason(str, Enum):
    INACTIVITY = "inactivity"
    OPPORTUNITY_COST = "opportunity_cost"


class CapitalSlotBlockReason(str, Enum):
    """Why ratchet pre-authorization is blocked; fail closed."""

    CONFIG_LIVE_AUTHORIZATION_CONTRADICTION = "config_live_authorization_contradiction"
    INVALID_CASHFLOW_SPLIT = "invalid_cashflow_split"
    SURVIVAL_NOT_ALLOWED = "survival_not_allowed"
    MISSING_REALIZED_SETTLED_BASIS = "missing_realized_settled_basis"


@dataclass(frozen=True)
class CapitalSlotConfig:
    profit_step_pct: float
    cashflow_lock_fraction: float
    reinvest_fraction: float
    allow_auto_top_up: bool
    live_authorization: bool
    min_realized_volatility: float
    min_atr_or_range: float
    max_time_without_cashflow_step: int
    min_opportunity_score: float


@dataclass(frozen=True)
class CapitalSlotState:
    selected_future: str
    initial_slot_base: float
    active_slot_base: float
    """Realized or settled slot equity; None = unknown -> ratchet fail closed."""
    realized_or_settled_slot_equity: Optional[float]
    unrealized_pnl: float
    locked_cashflow: float
    time_without_cashflow_step: int
    realized_volatility: float
    atr_or_range: float
    opportunity_score: float
    survival_allows_slot: bool


@dataclass(frozen=True)
class CapitalSlotRatchetDecision:
    status: CapitalSlotStatus
    ratchet_target: float
    can_ratchet: bool
    block_reasons: Tuple[CapitalSlotBlockReason, ...]
    reason: str
    live_authorization: bool
    new_active_slot_base: Optional[float] = None


@dataclass(frozen=True)
class CapitalSlotReleaseDecision:
    status: CapitalSlotStatus
    released: bool
    release_reason: Optional[CapitalSlotReleaseReason]
    block_reasons: Tuple[CapitalSlotBlockReason, ...]
    reason: str
    live_authorization: bool
    authorizes_new_future_selection: bool
    authorizes_new_trade: bool


def calculate_ratchet_target(
    active_slot_base: float, profit_step_pct: float, *, locked_cashflow: float = 0.0
) -> float:
    base = max(0.0, active_slot_base - locked_cashflow)
    return base * (1.0 + profit_step_pct)


def cashflow_split_valid(
    lock_fraction: float, reinvest_fraction: float, *, eps: float = _SPLIT_EPS
) -> bool:
    if lock_fraction < 0 or reinvest_fraction < 0 or lock_fraction > 1.0 or reinvest_fraction > 1.0:
        return False
    return abs(lock_fraction + reinvest_fraction - 1.0) <= eps


def apply_loss_following_base(prior_active: float, realized_settled_slot_equity: float) -> float:
    """
    After realized loss, the active slot base follows realized/settled equity downward.

    This does not top up from reserve or toward ``initial_slot_base``.
    """
    return min(prior_active, realized_settled_slot_equity)


def evaluate_capital_slot_ratchet(
    config: CapitalSlotConfig, state: CapitalSlotState
) -> CapitalSlotRatchetDecision:
    """
    Ratchet: target = effective_base * (1 + profit_step_pct) with
    effective_base = max(0, active_slot_base - locked_cashflow).

    - Eligibility for stepping uses **only** ``realized_or_settled_slot_equity`` vs target;
      ``unrealized_pnl`` is not used for the comparison (v0 contract).
    - Survival disallows pre-authorization when ``survival_allows_slot`` is False.
    - Invalid lock/reinvest split blocks ratchet.
    - This layer never pulls missing equity from a reserve: ``new_active_slot_base`` is
      always the observed settled slot equity when a step is allowed, independent of
      ``allow_auto_top_up`` (v0: field reserved for later governance; no reserve top-up).
    - Output ``live_authorization`` is always false.
    """
    if config.live_authorization:
        return CapitalSlotRatchetDecision(
            status=CapitalSlotStatus.ACTIVE,
            ratchet_target=0.0,
            can_ratchet=False,
            block_reasons=(CapitalSlotBlockReason.CONFIG_LIVE_AUTHORIZATION_CONTRADICTION,),
            reason="live_authorization in config is never accepted in this model; fail closed.",
            live_authorization=False,
        )
    if not cashflow_split_valid(config.cashflow_lock_fraction, config.reinvest_fraction):
        return CapitalSlotRatchetDecision(
            status=CapitalSlotStatus.ACTIVE,
            ratchet_target=0.0,
            can_ratchet=False,
            block_reasons=(CapitalSlotBlockReason.INVALID_CASHFLOW_SPLIT,),
            reason="Lock/reinvest split must be explicit, in [0,1], and sum to 1.",
            live_authorization=False,
        )
    t = calculate_ratchet_target(
        state.active_slot_base, config.profit_step_pct, locked_cashflow=state.locked_cashflow
    )
    if not state.survival_allows_slot:
        return CapitalSlotRatchetDecision(
            status=CapitalSlotStatus.ACTIVE,
            ratchet_target=t,
            can_ratchet=False,
            block_reasons=(CapitalSlotBlockReason.SURVIVAL_NOT_ALLOWED,),
            reason="Survival envelope disallows slot pre-authorization / ratchet.",
            live_authorization=False,
        )
    if state.realized_or_settled_slot_equity is None:
        return CapitalSlotRatchetDecision(
            status=CapitalSlotStatus.ACTIVE,
            ratchet_target=t,
            can_ratchet=False,
            block_reasons=(CapitalSlotBlockReason.MISSING_REALIZED_SETTLED_BASIS,),
            reason="Realized/settled slot equity is unknown; fail closed.",
            live_authorization=False,
        )
    r = state.realized_or_settled_slot_equity
    if r + 1e-12 < t:
        return CapitalSlotRatchetDecision(
            status=CapitalSlotStatus.ACTIVE,
            ratchet_target=t,
            can_ratchet=False,
            block_reasons=(),
            reason="Realized/settled slot equity has not reached ratchet target (unrealized PnL ignored for this check).",
            live_authorization=False,
        )
    return CapitalSlotRatchetDecision(
        status=CapitalSlotStatus.ACTIVE,
        ratchet_target=t,
        can_ratchet=True,
        block_reasons=(),
        reason="Settled slot equity meets ratchet target; new active base follows settled equity (data-only, no reserve top-up).",
        live_authorization=False,
        new_active_slot_base=r,
    )


def evaluate_capital_slot_release(
    config: CapitalSlotConfig, state: CapitalSlotState
) -> CapitalSlotReleaseDecision:
    """
    Data-only inactivity or opportunity-cost release. Does not select a new future or trade.
    """
    if config.live_authorization:
        return CapitalSlotReleaseDecision(
            status=CapitalSlotStatus.ACTIVE,
            released=False,
            release_reason=None,
            block_reasons=(CapitalSlotBlockReason.CONFIG_LIVE_AUTHORIZATION_CONTRADICTION,),
            reason="Config live_authorization is invalid for this model.",
            live_authorization=False,
            authorizes_new_future_selection=False,
            authorizes_new_trade=False,
        )
    tmax = config.max_time_without_cashflow_step
    time_breach = tmax > 0 and state.time_without_cashflow_step > tmax
    low_movement = (
        state.realized_volatility < config.min_realized_volatility
        and state.atr_or_range < config.min_atr_or_range
    )
    inactivity = time_breach or low_movement
    if inactivity:
        return CapitalSlotReleaseDecision(
            status=CapitalSlotStatus.RELEASED,
            released=True,
            release_reason=CapitalSlotReleaseReason.INACTIVITY,
            block_reasons=(),
            reason="Inactivity / low movement or stale cashflow step (data-only).",
            live_authorization=False,
            authorizes_new_future_selection=False,
            authorizes_new_trade=False,
        )
    if state.opportunity_score < config.min_opportunity_score:
        return CapitalSlotReleaseDecision(
            status=CapitalSlotStatus.RELEASED,
            released=True,
            release_reason=CapitalSlotReleaseReason.OPPORTUNITY_COST,
            block_reasons=(),
            reason="Opportunity score below threshold (data-only).",
            live_authorization=False,
            authorizes_new_future_selection=False,
            authorizes_new_trade=False,
        )
    return CapitalSlotReleaseDecision(
        status=CapitalSlotStatus.ACTIVE,
        released=False,
        release_reason=None,
        block_reasons=(),
        reason="No inactivity or opportunity release conditions met.",
        live_authorization=False,
        authorizes_new_future_selection=False,
        authorizes_new_trade=False,
    )
