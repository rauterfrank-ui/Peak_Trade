"""Deterministic Top-20 candidate-context ranking from Cap 2.1 instruments."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_EXCLUDED,
    TOP20_CANDIDATE_CONTEXT_LIMIT,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import RankedCandidateV1
from src.ops.productive_futures_ranking_producer_v1.policy_v1 import (
    classify_exclusion_codes_v1,
    compute_score_components_v1,
    is_ranking_eligible_v1,
    total_score_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1


def _instrument_rows(universe_snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = universe_snapshot.get("instruments") or ()
    return [dict(row) for row in rows]


def classify_and_rank_candidates_v1(
    universe_snapshot: Mapping[str, Any],
    *,
    top_n: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
) -> tuple[tuple[RankedCandidateV1, ...], tuple[RankedCandidateV1, ...], dict[str, int]]:
    """Return (ranked_top_n, excluded_or_non_top, counts).

    Ranking order: total_score DESC, venue_native_id ASC, canonical_instrument_id ASC.
    Only eligible candidates receive ranks 1..min(N, eligible_count).
    """
    eligible_rows: list[RankedCandidateV1] = []
    excluded_rows: list[RankedCandidateV1] = []
    exclusion_counts: dict[str, int] = {}

    for row in _instrument_rows(universe_snapshot):
        components = compute_score_components_v1(row)
        score = total_score_v1(components)
        native = str(row.get("venue_native_inst_id") or row.get("venue_native_id") or "")
        canonical = str(row.get("canonical_instrument_id") or "")
        tie_break = {
            "total_score": f"{score:.6f}",
            "venue_native_id": native,
            "canonical_instrument_id": canonical,
        }
        if is_ranking_eligible_v1(components):
            eligible_rows.append(
                RankedCandidateV1(
                    rank=0,  # assigned after sort
                    canonical_instrument_id=canonical,
                    venue_native_id=native,
                    total_score=score,
                    score_components=components,
                    data_quality_status=str(row.get("data_quality_status") or ""),
                    eligibility_status=ELIGIBILITY_ELIGIBLE,
                    exclusion_reason_codes=(),
                    tie_break_values=tie_break,
                )
            )
        else:
            codes = classify_exclusion_codes_v1(row, components)
            for code in codes:
                exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
            excluded_rows.append(
                RankedCandidateV1(
                    rank=0,
                    canonical_instrument_id=canonical,
                    venue_native_id=native,
                    total_score=score,
                    score_components=components,
                    data_quality_status=str(row.get("data_quality_status") or ""),
                    eligibility_status=ELIGIBILITY_EXCLUDED,
                    exclusion_reason_codes=codes,
                    tie_break_values=tie_break,
                )
            )

    eligible_rows.sort(
        key=lambda c: (
            -c.total_score,
            c.venue_native_id,
            c.canonical_instrument_id,
        )
    )

    ranked: list[RankedCandidateV1] = []
    overflow: list[RankedCandidateV1] = []
    limit = max(0, int(top_n))
    for idx, cand in enumerate(eligible_rows, start=1):
        assigned = RankedCandidateV1(
            rank=idx if idx <= limit else 0,
            canonical_instrument_id=cand.canonical_instrument_id,
            venue_native_id=cand.venue_native_id,
            total_score=cand.total_score,
            score_components=cand.score_components,
            data_quality_status=cand.data_quality_status,
            eligibility_status=cand.eligibility_status,
            exclusion_reason_codes=cand.exclusion_reason_codes,
            tie_break_values=cand.tie_break_values,
        )
        if idx <= limit:
            ranked.append(assigned)
        else:
            overflow.append(assigned)

    excluded_sorted = sorted(
        excluded_rows,
        key=lambda c: (c.venue_native_id, c.canonical_instrument_id),
    )
    all_excluded = tuple(excluded_sorted + overflow)
    if not ranked and not exclusion_counts:
        exclusion_counts[RankingFailureCodeV1.NO_ELIGIBLE_CANDIDATES.value] = 1
    return tuple(ranked), all_excluded, dict(sorted(exclusion_counts.items()))


def assert_no_reintroduced_excluded_instruments_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    ranked: Sequence[RankedCandidateV1],
) -> tuple[str, ...]:
    """Fail-closed if ranked set includes instruments not present in universe snapshot."""
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
