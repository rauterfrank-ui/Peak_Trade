# src/orders/__init__.py
"""
Peak_Trade: Order-Layer (Sandbox & Order-Routing)
=================================================

Dieser Layer definiert:
- Order-Datenstrukturen (OrderRequest, OrderFill, OrderExecutionResult)
- OrderExecutor-Interface (Protocol)
- PaperOrderExecutor (Simulation/Sandbox, keine echten Orders)
- ShadowOrderExecutor (Shadow-/Dry-Run-Modus, Phase 24)
- TestnetOrderExecutor (Dry-Run, Phase 17)
- LiveOrderExecutor (Stub, nicht implementiert)
- ExchangeOrderExecutor (Unified mit SafetyGuard)
- Mapping-Helpers (von LiveOrderRequest/CSV auf OrderRequest)

WICHTIG: In Phase 24 werden KEINE echten Orders an Boersen gesendet.
         Testnet/Live sind nur als Architektur vorbereitet (Dry-Run/Stubs).
         ShadowOrderExecutor ist zu 100% simulativ.

HINWEIS: Exchange-Module (Testnet/Live Executors) werden lazy importiert,
         um zirkulaere Abhaengigkeiten zu vermeiden. Direkter Import:
         >>> from src.orders.exchange import TestnetOrderExecutor
         >>> from src.orders.shadow import ShadowOrderExecutor
"""
from __future__ import annotations

from .base import (
    OrderSide,
    OrderType,
    OrderStatus,
    OrderRequest,
    OrderFill,
    OrderExecutionResult,
    OrderExecutor,
)
from .paper import PaperMarketContext, PaperOrderExecutor
from .shadow import (
    ShadowOrderExecutor,
    ShadowMarketContext,
    ShadowOrderLog,
    create_shadow_executor,
    EXECUTION_MODE_SHADOW,
    EXECUTION_MODE_SHADOW_RUN,
)

# Exchange-Module werden NICHT hier importiert um zirkulaere Imports zu vermeiden.
# Direkter Import: from src.orders.exchange import TestnetOrderExecutor, ...

from .mappers import (
    from_live_order_request,
    from_orders_csv_row,
    to_order_requests,
)

# Constants are safe to define here
EXECUTION_MODE_DRY_RUN = "dry_run"
EXECUTION_MODE_TESTNET_DRY_RUN = "testnet_dry_run"
EXECUTION_MODE_LIVE_BLOCKED = "live_blocked"
EXECUTION_MODE_SIMULATED = "simulated"


def __getattr__(name: str):
    """Lazy-Loading fuer Exchange-Module, um zirkulaere Imports zu vermeiden."""
    _exchange_exports = {
        "TestnetOrderExecutor",
        "LiveOrderExecutor",
        "ExchangeOrderExecutor",
        "DryRunOrderLog",
    }
    if name in _exchange_exports:
        from . import exchange
        return getattr(exchange, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Types
    "OrderSide",
    "OrderType",
    "OrderStatus",
    # Dataclasses
    "OrderRequest",
    "OrderFill",
    "OrderExecutionResult",
    # Executor Interface
    "OrderExecutor",
    # Paper/Sandbox
    "PaperMarketContext",
    "PaperOrderExecutor",
    # Shadow Executor (Phase 24)
    "ShadowOrderExecutor",
    "ShadowMarketContext",
    "ShadowOrderLog",
    "create_shadow_executor",
    # Mappers
    "from_live_order_request",
    "from_orders_csv_row",
    "to_order_requests",
    # Exchange Executors (Phase 17: Dry-Run/Stubs) - lazy loaded
    "TestnetOrderExecutor",
    "LiveOrderExecutor",
    "ExchangeOrderExecutor",
    "DryRunOrderLog",
    # Execution Mode Constants
    "EXECUTION_MODE_DRY_RUN",
    "EXECUTION_MODE_TESTNET_DRY_RUN",
    "EXECUTION_MODE_LIVE_BLOCKED",
    "EXECUTION_MODE_SIMULATED",
    "EXECUTION_MODE_SHADOW",
    "EXECUTION_MODE_SHADOW_RUN",
]
