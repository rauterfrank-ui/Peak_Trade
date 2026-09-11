"""Persisted multi-instrument Economic Market Data Input producer V1.

Owns Public-MD network reads, collection, persistence, schema, and replay
input for Cap 2.2 MVR raw input. Does not rank, select, or execute.
"""

from __future__ import annotations

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
)
from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1
from src.ops.economic_md_input_producer_v1.persistence_v1 import (
    load_and_validate_economic_md_snapshot_v1,
)
from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
    replay_economic_md_snapshot_v1,
    run_economic_md_input_producer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCER_VERSION",
    "SCHEMA_VERSION",
    "EconomicMdInputSnapshotV1",
    "load_and_validate_economic_md_snapshot_v1",
    "produce_economic_md_input_snapshot_v1",
    "replay_economic_md_snapshot_v1",
    "run_economic_md_input_producer_v1",
]
