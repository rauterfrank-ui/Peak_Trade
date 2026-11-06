"""Structural negative-control ranking. Reuses Cap-2.1 structural rule only."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    NEGATIVE_CONTROL_CLASS,
    NEGATIVE_CONTROL_POLICY_ID,
    STRUCTURAL_RANKING_POLICY_ID,
)
from src.ops.cap22_offline_mvr_evidence_harness_v1.models_v1 import (
    CandidateUniverseMemberV1,
    NotRankableCandidateV1,
    OfflinePolicyRankingV1,
    make_policy_ranking,
    ranked_from_sorted,
)
from src.ops.productive_futures_ranking_producer_v1.ranking_v1 import (
    classify_and_rank_candidates_v1,
)


def evaluate_negative_control_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    candidate_universe: Sequence[CandidateUniverseMemberV1],
) -> OfflinePolicyRankingV1:
    allowed = {(row.canonical_instrument_id, row.venue_native_id) for row in candidate_universe}
    instruments = [
        dict(row)
        for row in (universe_snapshot.get("instruments") or ())
        if (
            str(row.get("canonical_instrument_id") or ""),
            str(row.get("venue_native_inst_id") or row.get("venue_native_id") or ""),
        )
        in allowed
    ]
    filtered = dict(universe_snapshot)
    filtered["instruments"] = instruments
    ranked, excluded, _counts = classify_and_rank_candidates_v1(
        filtered, top_n=max(len(instruments), 1)
    )
    rows = [
        (
            (
                -cand.total_score,
                cand.venue_native_id,
                cand.canonical_instrument_id,
            ),
            cand.venue_native_id,
            cand.canonical_instrument_id,
            {
                "primary": "structural_total_score_desc",
                "ranking_policy_id": STRUCTURAL_RANKING_POLICY_ID,
                "total_score": f"{cand.total_score:.6f}",
            },
        )
        for cand in ranked
        if (cand.canonical_instrument_id, cand.venue_native_id) in allowed
    ]
    rows.sort(key=lambda item: item[0])
    not_rankable = tuple(
        sorted(
            (
                NotRankableCandidateV1(
                    canonical_instrument_id=cand.canonical_instrument_id,
                    venue_native_id=cand.venue_native_id,
                    reason_code="STRUCTURAL_NEGATIVE_CONTROL_EXCLUDED",
                )
                for cand in excluded
                if (cand.canonical_instrument_id, cand.venue_native_id) in allowed
            ),
            key=lambda item: (item.venue_native_id, item.canonical_instrument_id),
        )
    )
    return make_policy_ranking(
        policy_id=NEGATIVE_CONTROL_POLICY_ID,
        policy_class=NEGATIVE_CONTROL_CLASS,
        ordered=ranked_from_sorted(rows),
        not_rankable=not_rankable,
    )
