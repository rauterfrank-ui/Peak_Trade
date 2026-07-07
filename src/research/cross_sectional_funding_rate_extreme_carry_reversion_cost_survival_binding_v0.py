"""Cost survival binding for extreme carry/reversion v0 research scope.

Research-only net-edge survival gate after fees, slippage, spread, and funding drag.
Reuses carry v0 cost execution constants; does not touch master_v2 runtime survival.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from src.research.cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0 import (
    CONSERVATIVE_HALF_SPREAD_BPS,
    EFFECTIVE_ENTRY_COST_BPS,
    EFFECTIVE_EXIT_COST_BPS,
    EXECUTION_MODEL_VERSION,
    FEE_BPS_PER_SIDE,
    FEE_MODEL_VERSION,
    FUNDING_MODEL_VERSION,
    ROUNDTRIP_COST_BPS,
    SLIPPAGE_BPS_PER_SIDE,
    SLIPPAGE_MODEL_VERSION,
    SPREAD_MODEL_VERSION,
    build_cost_execution_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_COST_SURVIVAL_BINDING_V0=true"
)
BINDING_OWNER = "cross_sectional_funding_rate_extreme_carry_reversion_cost_survival_binding_v0"
BINDING_VERSION = "v0"
STRATEGY_ID = "cross_sectional_funding_rate_extreme_carry_reversion"
STRATEGY_VERSION = "v0"

MIN_NET_EDGE_BPS = 0.0
REUSED_COST_EXECUTION_OWNER = "cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0"


class CostSurvivalBindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CostSurvivalBindingResultV0:
    status: CostSurvivalBindingStatus
    reason_code: str
    expected_carry_bps: float | None
    funding_drag_bps: float | None
    roundtrip_cost_bps: float | None
    net_edge_bps: float | None
    min_net_edge_bps: float


def materialize_cost_survival_binding_v0() -> dict[str, object]:
    cost_execution_binding = build_cost_execution_binding_v0()
    return {
        "binding_owner": BINDING_OWNER,
        "binding_version": BINDING_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "feature_kind": "cost_survival",
        "status": "BOUND",
        "cost_execution_binding": cost_execution_binding,
        "survival_semantics": {
            "net_edge_after_fees_slippage_spread_and_funding": True,
            "implicit_zero_cost_forbidden": True,
            "unknown_funding_forbidden": True,
        },
        "thresholds": {
            "min_net_edge_bps": MIN_NET_EDGE_BPS,
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        },
        "reuse_owners": {
            "cost_execution_owner": REUSED_COST_EXECUTION_OWNER,
        },
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "order_effect": "NONE",
    }


def _cost_model_complete(binding: Mapping[str, object]) -> bool:
    cost_execution = binding.get("cost_execution_binding")
    if not isinstance(cost_execution, Mapping):
        return False
    execution = cost_execution.get("execution_model_binding")
    funding = cost_execution.get("funding_model_binding")
    if not isinstance(execution, Mapping) or not isinstance(funding, Mapping):
        return False
    roundtrip = execution.get("roundtrip_cost_bps")
    funding_bound = funding.get("bind")
    return (
        funding_bound is True
        and isinstance(roundtrip, (int, float))
        and math.isfinite(float(roundtrip))
        and float(roundtrip) > 0.0
    )


def evaluate_cost_survival_binding_v0(
    *,
    expected_carry_bps: float | None,
    funding_drag_bps: float | None,
    binding: Mapping[str, object] | None = None,
) -> CostSurvivalBindingResultV0:
    """Fail-closed research cost survival gate for one candidate carry edge."""
    resolved_binding = dict(binding or materialize_cost_survival_binding_v0())
    roundtrip_cost_bps = ROUNDTRIP_COST_BPS

    if not _cost_model_complete(resolved_binding):
        return CostSurvivalBindingResultV0(
            status=CostSurvivalBindingStatus.BLOCKED,
            reason_code="cost_model_incomplete",
            expected_carry_bps=expected_carry_bps,
            funding_drag_bps=funding_drag_bps,
            roundtrip_cost_bps=roundtrip_cost_bps,
            net_edge_bps=None,
            min_net_edge_bps=MIN_NET_EDGE_BPS,
        )

    if expected_carry_bps is None or not math.isfinite(expected_carry_bps):
        return CostSurvivalBindingResultV0(
            status=CostSurvivalBindingStatus.BLOCKED,
            reason_code="expected_carry_unknown",
            expected_carry_bps=expected_carry_bps,
            funding_drag_bps=funding_drag_bps,
            roundtrip_cost_bps=roundtrip_cost_bps,
            net_edge_bps=None,
            min_net_edge_bps=MIN_NET_EDGE_BPS,
        )

    if funding_drag_bps is None or not math.isfinite(funding_drag_bps):
        return CostSurvivalBindingResultV0(
            status=CostSurvivalBindingStatus.BLOCKED,
            reason_code="funding_drag_unknown",
            expected_carry_bps=expected_carry_bps,
            funding_drag_bps=funding_drag_bps,
            roundtrip_cost_bps=roundtrip_cost_bps,
            net_edge_bps=None,
            min_net_edge_bps=MIN_NET_EDGE_BPS,
        )

    net_edge_bps = expected_carry_bps - roundtrip_cost_bps - funding_drag_bps
    if net_edge_bps < MIN_NET_EDGE_BPS:
        return CostSurvivalBindingResultV0(
            status=CostSurvivalBindingStatus.FAIL,
            reason_code="net_edge_insufficient",
            expected_carry_bps=expected_carry_bps,
            funding_drag_bps=funding_drag_bps,
            roundtrip_cost_bps=roundtrip_cost_bps,
            net_edge_bps=net_edge_bps,
            min_net_edge_bps=MIN_NET_EDGE_BPS,
        )

    return CostSurvivalBindingResultV0(
        status=CostSurvivalBindingStatus.PASS,
        reason_code="cost_survival_pass",
        expected_carry_bps=expected_carry_bps,
        funding_drag_bps=funding_drag_bps,
        roundtrip_cost_bps=roundtrip_cost_bps,
        net_edge_bps=net_edge_bps,
        min_net_edge_bps=MIN_NET_EDGE_BPS,
    )


def cost_survival_binding_cost_constants_v0() -> dict[str, float | str]:
    return {
        "fee_model_version": FEE_MODEL_VERSION,
        "fee_bps_per_side": FEE_BPS_PER_SIDE,
        "slippage_model_version": SLIPPAGE_MODEL_VERSION,
        "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
        "funding_model_version": FUNDING_MODEL_VERSION,
        "spread_model_version": SPREAD_MODEL_VERSION,
        "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
        "execution_model_version": EXECUTION_MODEL_VERSION,
        "effective_entry_cost_bps": EFFECTIVE_ENTRY_COST_BPS,
        "effective_exit_cost_bps": EFFECTIVE_EXIT_COST_BPS,
        "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
    }
