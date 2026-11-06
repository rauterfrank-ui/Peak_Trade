"""Bounded active-set representation. Ranking cannot create runtime authority."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping

from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    RANKING_CANNOT_CREATE_RUNTIME_AUTHORITY,
    TOP_N_ACTIVE_SET_AUTHORITY,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    Phase82GraphRequestV1,
    R6S3RuntimeArchitectureError,
    RankingCandidateV1,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def _sorted_candidates(
    candidates: tuple[RankingCandidateV1, ...],
) -> tuple[RankingCandidateV1, ...]:
    return tuple(sorted(candidates, key=lambda row: (int(row.rank), row.instrument_id)))


def resolve_active_set_v1(
    request: Phase82GraphRequestV1,
    *,
    authorized: bool,
) -> Mapping[str, Any]:
    if TOP_N_ACTIVE_SET_AUTHORITY is True:
        _reject("top_n_active_set_authority_must_remain_false")
    if RANKING_CANNOT_CREATE_RUNTIME_AUTHORITY is not True:
        _reject("ranking_authority_doctrine_missing")
    selected = str(request.selected_future_id or "").strip()
    if not selected:
        _reject("selected_future_id_missing")
    candidates = _sorted_candidates(request.ranking_candidates)
    candidate_ids = tuple(row.instrument_id for row in candidates)
    if authorized is True:
        _reject("authorized_active_set_forbidden_in_s3")
    effective = (selected,)
    if len(effective) > MAX_POSITIONS_EFFECTIVE:
        _reject("effective_active_count_exceeds_max_positions")
    return MappingProxyType(
        {
            "candidate_ids": candidate_ids,
            "effective_active_ids": effective,
            "effective_active_count": len(effective),
            "max_positions_effective": MAX_POSITIONS_EFFECTIVE,
            "top_n_active_set_authority": False,
            "ranking_created_runtime_authority": False,
        }
    )
