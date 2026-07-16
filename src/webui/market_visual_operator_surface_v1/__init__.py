"""Market visual operator surface v1 (read-only, non-authorizing SSR display).

This package builds display-only view models for the ``/market`` dashboard's visual
operator zone: a decision funnel, economic observability, AI linear diagnostics, and a
compact operator header. It never invents data, never carries trading/runtime/order
authority, and fails closed when offline evidence bundles are unconfigured or missing.
"""

from __future__ import annotations

from .contracts import (
    ACTIVITY_STATES,
    ActivityState,
    ENV_EVIDENCE_ROOT,
    ENV_LINEAR_DIAGNOSTICS_ROOT,
)
from .runtime_v1 import build_market_visual_operator_surface_context

__all__ = [
    "ACTIVITY_STATES",
    "ActivityState",
    "ENV_EVIDENCE_ROOT",
    "ENV_LINEAR_DIAGNOSTICS_ROOT",
    "build_market_visual_operator_surface_context",
]
