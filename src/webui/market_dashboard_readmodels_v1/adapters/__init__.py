"""Canonical Market Dashboard snapshot adapters (PR-C).

Pure, deterministic, side-effect-free projections from already-produced
canonical sources onto PR-B ReadModel contracts. Adapters never recalculate
trading decisions, Double-Play arbitration, authority, execution permission,
economic metrics, or diagnostics authority.

Adapters accept explicit source objects (or None). They do not discover
"latest" evidence files, call replay/composition evaluate functions, or
perform network/runtime I/O.
"""

from __future__ import annotations

from src.webui.market_dashboard_readmodels_v1.adapters.canonical_decision import (
    adapt_canonical_decision_summary_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.diagnostics import (
    adapt_diagnostics_summary_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.double_play import (
    adapt_double_play_decision_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.economic import (
    adapt_economic_summary_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.execution import (
    adapt_execution_state_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.freshness import (
    adapt_dashboard_freshness_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.market import (
    adapt_market_instrument_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.ranking import (
    adapt_market_ranking_snapshot_v1,
)
from src.webui.market_dashboard_readmodels_v1.adapters.safety_authority import (
    adapt_safety_authority_snapshot_v1,
)

ADAPTER_PACKAGE_ID = "market_dashboard_adapters.v1"
ADAPTER_PACKAGE_VERSION = "1"

__all__ = [
    "ADAPTER_PACKAGE_ID",
    "ADAPTER_PACKAGE_VERSION",
    "adapt_canonical_decision_summary_v1",
    "adapt_dashboard_freshness_snapshot_v1",
    "adapt_diagnostics_summary_snapshot_v1",
    "adapt_double_play_decision_snapshot_v1",
    "adapt_economic_summary_snapshot_v1",
    "adapt_execution_state_snapshot_v1",
    "adapt_market_instrument_snapshot_v1",
    "adapt_market_ranking_snapshot_v1",
    "adapt_safety_authority_snapshot_v1",
]
