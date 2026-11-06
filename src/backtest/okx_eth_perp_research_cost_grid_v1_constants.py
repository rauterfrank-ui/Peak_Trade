"""SSOT for okx_eth_perp_research_cost_grid_v1 (Step29M/31F economic evaluation bindings).

Research calibration grid only — not productive defaults or live config authority.
"""

from __future__ import annotations

from typing import Final

GRID_ID: Final[str] = "okx_eth_perp_research_cost_grid_v1"
GRID_VERSION: Final[str] = "v1"
PARAMETER_NAMES: Final[tuple[str, ...]] = ("fee_bps", "slippage_bps")
OPERATOR_BOUND_FEE_BPS: Final[tuple[float, ...]] = (8.0, 10.0, 12.0)
OPERATOR_BOUND_SLIPPAGE_BPS: Final[tuple[float, ...]] = (4.0, 5.0, 6.0)
BASELINE_FEE_BPS: Final[float] = 10.0
BASELINE_SLIPPAGE_BPS: Final[float] = 5.0
SEARCH_SPACE_BOUNDS: Final[dict[str, dict[str, float]]] = {
    "fee_bps": {"min": 8.0, "max": 12.0},
    "slippage_bps": {"min": 4.0, "max": 6.0},
}
GRID_SEED: Final[int] = 42
SOURCE_STEP29M_CONFIG: Final[str] = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_economic_evaluation_v1.json"
)
