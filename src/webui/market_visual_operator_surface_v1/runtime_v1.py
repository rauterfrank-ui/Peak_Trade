"""Runtime orchestration for the market visual operator surface v1 (SSR-only).

Composes the individual display view models and computes the overall AI activity state.
Read-only and non-authorizing: no request-time market data, no runtime/order authority.
"""

from __future__ import annotations

from typing import Any

from .ai_linear_diagnostics_display_v1 import build_ai_linear_diagnostics_display_v1
from .contracts import (
    ENV_EVIDENCE_ROOT,
    ActivityState,
    compute_ai_activity_state,
    resolved_dir_or_none,
)
from .decision_funnel_display_v1 import build_decision_funnel_display_v1
from .economic_observability_display_v1 import build_economic_observability_display_v1
from .operator_header_display_v1 import build_operator_header_display_v1


def build_market_visual_operator_surface_context(
    *,
    source: str = "futures",
    futures_ohlcv: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full visual operator surface context for GET /market (display-only)."""
    decision_funnel = build_decision_funnel_display_v1()
    economic = build_economic_observability_display_v1()
    linear_diagnostics = build_ai_linear_diagnostics_display_v1()

    evidence_root_set = resolved_dir_or_none(ENV_EVIDENCE_ROOT) is not None
    ai_activity_state = compute_ai_activity_state(
        funnel_loaded=decision_funnel["activity_state"] == ActivityState.PROCESSED,
        funnel_failed=decision_funnel["activity_state"] == ActivityState.FAILED,
        evidence_root_set=evidence_root_set,
        trade_count_computed=bool(decision_funnel.get("trade_count_computed")),
        bar_count=decision_funnel.get("bar_count"),
        zero_trade_degeneration_explicit=bool(
            decision_funnel.get("zero_trade_degeneration_explicit")
        ),
    )

    operator_header = build_operator_header_display_v1(
        source=source,
        futures_ohlcv=futures_ohlcv,
        economic_vm=economic,
        ai_activity_state=ai_activity_state,
    )

    return {
        "visual_operator_header": operator_header,
        "decision_funnel_visual": decision_funnel,
        "economic_observability_visual": economic,
        "ai_linear_diagnostics_visual": linear_diagnostics,
        "ai_activity_state": ai_activity_state,
    }


__all__ = ["build_market_visual_operator_surface_context"]
