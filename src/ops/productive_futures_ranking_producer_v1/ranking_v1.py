"""Deterministic Top-20 Cap 2.2 ranking: B03 economic order over Cap 2.1-eligible S_STAR."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    RankingFeatureProductionSnapshotV1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    TOP20_CANDIDATE_CONTEXT_LIMIT,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import RankedCandidateV1


def classify_and_rank_candidates_v1(
    universe_snapshot: Mapping[str, Any],
    *,
    feature_production_snapshot: RankingFeatureProductionSnapshotV1,
    top_n: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
):
    """Rank Cap-2.1-eligible candidates by B03 economic score using B05 features.

    Ordering: balanced_movement_score DESC, venue_native_id ASC, canonical_id ASC.
    Venue-native id is final deterministic fallback only after economic ties.
    Missing/invalid required economic features exclude from S_STAR (fail closed).
    """
    # Lazy import avoids circular load:
    # feature_contract → productive.__init__ → producer → ranking → economic → feature_contract
    from src.ops.peak_trade_economic_ranking_runtime_v1.economic_rank_v1 import (
        classify_and_rank_economic_candidates_v1,
    )

    return classify_and_rank_economic_candidates_v1(
        universe_snapshot=universe_snapshot,
        feature_production_snapshot=feature_production_snapshot,
        top_n=top_n,
    )


def assert_no_reintroduced_excluded_instruments_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    ranked: Sequence[RankedCandidateV1],
) -> tuple[str, ...]:
    """Fail-closed if ranked set includes instruments not present in universe snapshot."""
    from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import (
        RankingFailureCodeV1,
    )

    universe_ids = {
        str(row.get("canonical_instrument_id") or "")
        for row in (universe_snapshot.get("instruments") or ())
    }
    failures: list[str] = []
    for cand in ranked:
        if cand.canonical_instrument_id not in universe_ids:
            failures.append(RankingFailureCodeV1.FORBIDDEN_INSTRUMENT_REINTRODUCTION.value)
            break
    return tuple(failures)
