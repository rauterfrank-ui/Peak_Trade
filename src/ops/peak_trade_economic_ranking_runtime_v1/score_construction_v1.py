"""B03-ratified midrank-percentile score construction (pure deterministic seam)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from src.ops.peak_trade_economic_ranking_runtime_v1.constants_v1 import (
    AMPLITUDE_POLICY_ID,
    AMPLITUDE_WEIGHT,
    SINGLETON_AMPLITUDE_PERCENTILE,
    SINGLETON_BALANCED_MOVEMENT_SCORE,
    SINGLETON_VOLATILITY_PERCENTILE,
    VOLATILITY_POLICY_ID,
    VOLATILITY_WEIGHT,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import NormalizedTransformId


@dataclass(frozen=True)
class FeatureNormalizationRowV1:
    feature_policy_id: str
    raw_value: float
    midrank: float
    percentile: float
    normalized_transform_id: str


@dataclass(frozen=True)
class CandidateEconomicScoreV1:
    canonical_instrument_id: str
    venue_native_id: str
    volatility_raw: float
    amplitude_raw: float
    volatility_midrank: float
    amplitude_midrank: float
    volatility_percentile: float
    amplitude_percentile: float
    balanced_movement_score: float
    normalized_transform_id: str


def midrank_higher_is_better_v1(values: Sequence[float]) -> tuple[float, ...]:
    """Deterministic average midranks where 1.0 is the highest value."""
    n = len(values)
    if n == 0:
        return ()
    indexed = sorted(enumerate(values), key=lambda item: (-item[1], item[0]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        # Competition ranks i+1 .. j+1 averaged.
        avg = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = float(avg)
        i = j + 1
    return tuple(ranks)


def percentile_from_midrank_v1(*, midrank: float, n: int) -> float:
    if n <= 0:
        raise ValueError("CROSS_SECTION_N_REQUIRED")
    if n == 1:
        return 0.5
    return float(n - midrank) / float(n - 1)


def normalize_feature_cross_section_v1(
    *,
    feature_policy_id: str,
    raw_by_id: Mapping[str, float],
) -> dict[str, FeatureNormalizationRowV1]:
    ids = sorted(raw_by_id)
    values = [float(raw_by_id[cid]) for cid in ids]
    n = len(ids)
    if n == 0:
        return {}
    if n == 1:
        cid = ids[0]
        return {
            cid: FeatureNormalizationRowV1(
                feature_policy_id=feature_policy_id,
                raw_value=values[0],
                midrank=1.0,
                percentile=(
                    SINGLETON_VOLATILITY_PERCENTILE
                    if feature_policy_id == VOLATILITY_POLICY_ID
                    else SINGLETON_AMPLITUDE_PERCENTILE
                ),
                normalized_transform_id=NormalizedTransformId.SINGLETON_NEUTRAL_V1.value,
            )
        }
    midranks = midrank_higher_is_better_v1(values)
    out: dict[str, FeatureNormalizationRowV1] = {}
    for cid, raw, mid in zip(ids, values, midranks):
        out[cid] = FeatureNormalizationRowV1(
            feature_policy_id=feature_policy_id,
            raw_value=float(raw),
            midrank=float(mid),
            percentile=percentile_from_midrank_v1(midrank=float(mid), n=n),
            normalized_transform_id=NormalizedTransformId.MIDRANK_PERCENTILE_V1.value,
        )
    return out


def build_balanced_movement_scores_v1(
    *,
    identities: Mapping[str, str],
    volatility_raw_by_id: Mapping[str, float],
    amplitude_raw_by_id: Mapping[str, float],
) -> tuple[CandidateEconomicScoreV1, ...]:
    """Score only the intersection of provided raw feature maps (S_STAR inputs)."""
    ids = sorted(set(volatility_raw_by_id) & set(amplitude_raw_by_id) & set(identities))
    n = len(ids)
    if n == 0:
        return ()
    vol_norm = normalize_feature_cross_section_v1(
        feature_policy_id=VOLATILITY_POLICY_ID,
        raw_by_id={cid: volatility_raw_by_id[cid] for cid in ids},
    )
    amp_norm = normalize_feature_cross_section_v1(
        feature_policy_id=AMPLITUDE_POLICY_ID,
        raw_by_id={cid: amplitude_raw_by_id[cid] for cid in ids},
    )
    rows: list[CandidateEconomicScoreV1] = []
    for cid in ids:
        vol = vol_norm[cid]
        amp = amp_norm[cid]
        if n == 1:
            score = SINGLETON_BALANCED_MOVEMENT_SCORE
            transform = NormalizedTransformId.SINGLETON_NEUTRAL_V1.value
        else:
            score = (
                float(VOLATILITY_WEIGHT) * vol.percentile + float(AMPLITUDE_WEIGHT) * amp.percentile
            )
            transform = NormalizedTransformId.MIDRANK_PERCENTILE_V1.value
        rows.append(
            CandidateEconomicScoreV1(
                canonical_instrument_id=cid,
                venue_native_id=str(identities[cid]),
                volatility_raw=vol.raw_value,
                amplitude_raw=amp.raw_value,
                volatility_midrank=vol.midrank,
                amplitude_midrank=amp.midrank,
                volatility_percentile=vol.percentile,
                amplitude_percentile=amp.percentile,
                balanced_movement_score=float(score),
                normalized_transform_id=transform,
            )
        )
    rows.sort(
        key=lambda row: (
            -row.balanced_movement_score,
            row.venue_native_id,
            row.canonical_instrument_id,
        )
    )
    return tuple(rows)
