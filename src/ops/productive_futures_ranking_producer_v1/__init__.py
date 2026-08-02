"""Productive Futures Ranking Producer V1 (Capability 2.2).

Consumes Cap 2.1 governed universe snapshots and produces a deterministic,
persistable Top-20 candidate-context ranking snapshot. Does not grant
selection, alpha, execution, multi-future, or runtime activation authority.
Dashboard/UI/legacy ranker inputs are rejected.
"""

from __future__ import annotations

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    PACKAGE_MARKER,
    PRODUCER_VERSION,
    RANKING_POLICY_ID,
    RANKING_POLICY_VERSION,
    SCHEMA_VERSION,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    RankedCandidateV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    load_and_validate_ranking_snapshot_v1,
)
from src.ops.productive_futures_ranking_producer_v1.producer_v1 import (
    produce_productive_futures_ranking_v1,
    run_productive_futures_ranking_producer_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "OWNER",
    "PACKAGE_MARKER",
    "PRODUCER_VERSION",
    "RANKING_POLICY_ID",
    "RANKING_POLICY_VERSION",
    "SCHEMA_VERSION",
    "ProductiveFuturesRankingSnapshotV1",
    "RankedCandidateV1",
    "load_and_validate_ranking_snapshot_v1",
    "produce_productive_futures_ranking_v1",
    "run_productive_futures_ranking_producer_v1",
]
