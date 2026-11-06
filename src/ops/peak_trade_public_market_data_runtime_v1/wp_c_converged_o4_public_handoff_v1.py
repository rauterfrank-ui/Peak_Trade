"""WP-C converged O4 public handoff facade for PRE_EXTERNAL bridge consumers.

Bridge packages must not import module paths containing ``private`` (wallclock v1
import guard). This facade is the compliant public surface; implementation remains
owned by ``market_data_private_state_runtime_convergence_v1.public_handoff_v1``.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1 import (
    converged_o4_handoff_v1 as _canonical_converged_o4_handoff_v1,
)

FACADE_OWNER: str = (
    "ops.peak_trade_public_market_data_runtime_v1.wp_c_converged_o4_public_handoff_v1"
)
CANONICAL_HANDOFF_OWNER: str = (
    "ops.market_data_private_state_runtime_convergence_v1.public_handoff_v1"
)


def converged_o4_handoff_v1(
    wp_a_o4: Mapping[str, Any],
    *,
    consumer_id: str = "o4_n_bars_learning",
) -> dict[str, Any]:
    """Delegate to canonical WP-C O4 converged handoff (behavior unchanged)."""
    return _canonical_converged_o4_handoff_v1(wp_a_o4, consumer_id=consumer_id)


__all__ = [
    "CANONICAL_HANDOFF_OWNER",
    "FACADE_OWNER",
    "converged_o4_handoff_v1",
]
