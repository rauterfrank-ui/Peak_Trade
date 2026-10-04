"""Bounded observation step — public MD policy via wallclock adapter (offline ticks)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.observation_cycle_adapter_v1 import (
    run_wallclock_observation_cycle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    preflight_wallclock_session_v1,
)


def preflight_public_observation_capability_v1(*, repo_root: Any) -> dict[str, Any]:
    return preflight_wallclock_session_v1(repo_root=repo_root)


def run_bounded_observation_step_v1(
    *,
    ticks: Sequence[ObservationMarketTickV1],
    wall_now_unix: float,
    reference_price: Decimal,
    intended_side: str,
    intended_quantity: Decimal,
) -> dict[str, Any]:
    outcome = run_wallclock_observation_cycle_v1(
        ticks=ticks,
        reference_price=reference_price,
        wall_now_unix=wall_now_unix,
        intended_side=intended_side,
        intended_quantity=intended_quantity,
    )
    return outcome.to_dict()
