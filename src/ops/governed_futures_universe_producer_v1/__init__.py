"""Governed Futures Universe Producer V1 (Capability 2.1).

Produces the canonical OKX-EEA futures-only universe snapshot truth for the
Phase-1 trading path. Does not grant ranking, selection, alpha, execution,
or runtime activation authority. Dashboard/readmodel inputs are rejected.
"""

from __future__ import annotations

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    GovernedUniverseInstrumentV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    load_and_validate_universe_snapshot_v1,
)
from src.ops.governed_futures_universe_producer_v1.producer_v1 import (
    produce_governed_futures_universe_v1,
    run_governed_futures_universe_producer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "GovernedFuturesUniverseSnapshotV1",
    "GovernedUniverseInstrumentV1",
    "load_and_validate_universe_snapshot_v1",
    "produce_governed_futures_universe_v1",
    "run_governed_futures_universe_producer_v1",
]
