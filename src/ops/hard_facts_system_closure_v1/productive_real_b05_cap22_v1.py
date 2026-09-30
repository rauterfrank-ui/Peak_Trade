"""Productive Cap-2.2 B05 from Economic-MD Input-2 (no synthetic ranking path)."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.economic_md_input_producer_v1.producer_v1 import (
    produce_economic_md_input_snapshot_v1,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import (
    EconomicMdPublicSourceV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    RankingFeatureProductionSnapshotV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.producer_v1 import (
    produce_ranking_feature_production_snapshot_v1,
)


class ProductiveRealB05Cap22Error(RuntimeError):
    pass


def build_cap22_feature_production_snapshot_from_economic_md_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    public_md_source: EconomicMdPublicSourceV1,
    collection_started_at_unix: float,
    collection_completed_at_unix: float,
) -> RankingFeatureProductionSnapshotV1:
    """Cap21-scheduled collection → Input-2 snapshot → real B05 production snapshot."""

    produced = produce_economic_md_input_snapshot_v1(
        universe_snapshot=universe_snapshot,
        public_md_source=public_md_source,
        collection_started_at_unix=collection_started_at_unix,
        collection_completed_at_unix=collection_completed_at_unix,
    )
    if produced.ok is not True or produced.snapshot is None:
        codes = ",".join(produced.failure_codes or ())
        raise ProductiveRealB05Cap22Error(f"ECONOMIC_MD_INPUT_FAIL_CLOSED:{codes}")
    return produce_ranking_feature_production_snapshot_v1(produced.snapshot)
