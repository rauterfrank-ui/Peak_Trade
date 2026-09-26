"""Cap 2.2 economic ranking over S_STAR from B05 raw features + Cap 2.1 eligibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.ops.peak_trade_economic_ranking_runtime_v1.constants_v1 import (
    ECONOMIC_RANK_STATE_S_STAR_N0,
    ECONOMIC_RANK_STATE_S_STAR_N1,
    ECONOMIC_RANK_STATE_S_STAR_N_GE_2,
    REASON_INCOMPLETE_FEATURE_CANDIDATE,
    REASON_INVALID_FEATURE_CANDIDATE,
    REASON_NO_COMPLETE_ECONOMIC_CANDIDATES,
    REASON_STRUCTURAL_NOT_ELIGIBLE,
)
from src.ops.peak_trade_economic_ranking_runtime_v1.score_construction_v1 import (
    CandidateEconomicScoreV1,
    build_balanced_movement_scores_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    EconomicSetMembership,
    RankingFeatureValueState,
    RankingFeatureExplainabilityWitnessV1,
    RankingCandidateFeatureBundleV1,
    RawRankingFeatureValueV1,
    NormalizedRankingFeatureValueV1,
    NormalizedTransformId,
    ScoreContributionV1,
    TieBreakWitnessV1,
    TieBreakStage,
    StructuralEligibilityWitnessV1,
    PairwiseOrderWitnessV1,
    build_policy_identity_v1,
    authority_block_v1,
    SCHEMA_VERSION as FEATURE_WITNESS_SCHEMA,
    validate_raw_feature_value_v1,
)
from src.ops.peak_trade_ranking_feature_production_v1.models_v1 import (
    InstrumentRawFeatureProductionV1,
    RankingFeatureProductionSnapshotV1,
)
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    AMPLITUDE_WEIGHT,
    ORDER_PRIMARY,
    ORDER_SECONDARY,
    ORDER_TERTIARY,
    VOLATILITY_POLICY_ID,
    VOLATILITY_WEIGHT,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_EXCLUDED,
    SCORE_COMPONENT_KEYS,
    TOP20_CANDIDATE_CONTEXT_LIMIT,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import RankedCandidateV1
from src.ops.productive_futures_ranking_producer_v1.policy_v1 import (
    classify_exclusion_codes_v1,
    compute_score_components_v1,
    is_ranking_eligible_v1,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1


@dataclass(frozen=True)
class EconomicRankingResultV1:
    ranked: tuple[RankedCandidateV1, ...]
    excluded: tuple[RankedCandidateV1, ...]
    economic_rank_state: str
    s_star_count: int
    explainability: RankingFeatureExplainabilityWitnessV1
    exclusion_counts: Mapping[str, int]


def _raw_feature_map(
    instrument: InstrumentRawFeatureProductionV1,
) -> dict[str, RawRankingFeatureValueV1]:
    return {row.feature_policy_id: row for row in instrument.raw_features}


def _feature_ready_pair(
    instrument: InstrumentRawFeatureProductionV1,
) -> tuple[Optional[float], Optional[float], Optional[str]]:
    by_id = _raw_feature_map(instrument)
    vol = by_id.get(VOLATILITY_POLICY_ID)
    amp = by_id.get(AMPLITUDE_POLICY_ID)
    if vol is None or amp is None:
        return None, None, REASON_INCOMPLETE_FEATURE_CANDIDATE
    for row in (vol, amp):
        validate_raw_feature_value_v1(row)
    if vol.state != RankingFeatureValueState.READY or amp.state != RankingFeatureValueState.READY:
        if RankingFeatureValueState.INCOMPLETE_WARMUP in (vol.state, amp.state) or (
            RankingFeatureValueState.MISSING in (vol.state, amp.state)
        ):
            return None, None, REASON_INCOMPLETE_FEATURE_CANDIDATE
        return None, None, REASON_INVALID_FEATURE_CANDIDATE
    if vol.raw_value is None or amp.raw_value is None:
        return None, None, REASON_INVALID_FEATURE_CANDIDATE
    return float(vol.raw_value), float(amp.raw_value), None


def classify_and_rank_economic_candidates_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    feature_production_snapshot: RankingFeatureProductionSnapshotV1,
    top_n: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
) -> EconomicRankingResultV1:
    features_by_id = {
        row.canonical_instrument_id: row for row in feature_production_snapshot.instruments
    }
    structural_eligible: list[dict[str, Any]] = []
    excluded_rows: list[RankedCandidateV1] = []
    exclusion_counts: dict[str, int] = {}

    for row in universe_snapshot.get("instruments") or ():
        instrument = dict(row)
        components = compute_score_components_v1(instrument)
        native = str(
            instrument.get("venue_native_inst_id") or instrument.get("venue_native_id") or ""
        )
        canonical = str(instrument.get("canonical_instrument_id") or "")
        if not is_ranking_eligible_v1(components):
            codes = classify_exclusion_codes_v1(instrument, components)
            for code in codes:
                exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
            excluded_rows.append(
                RankedCandidateV1(
                    rank=0,
                    canonical_instrument_id=canonical,
                    venue_native_id=native,
                    total_score=float(sum(components.values())),
                    score_components=components,
                    data_quality_status=str(instrument.get("data_quality_status") or ""),
                    eligibility_status=ELIGIBILITY_EXCLUDED,
                    exclusion_reason_codes=codes,
                    tie_break_values={
                        "balanced_movement_score": "",
                        "venue_native_id": native,
                        "canonical_instrument_id": canonical,
                        "economic_set_membership": EconomicSetMembership.EXCLUDED_FROM_S_STAR.value,
                        "exclusion": REASON_STRUCTURAL_NOT_ELIGIBLE,
                    },
                )
            )
            continue
        structural_eligible.append(instrument)

    vol_raw: dict[str, float] = {}
    amp_raw: dict[str, float] = {}
    identities: dict[str, str] = {}
    s_star_feature_rows: dict[str, InstrumentRawFeatureProductionV1] = {}
    structural_components_by_id: dict[str, dict[str, float]] = {}

    for instrument in structural_eligible:
        canonical = str(instrument["canonical_instrument_id"])
        native = str(
            instrument.get("venue_native_inst_id") or instrument.get("venue_native_id") or ""
        )
        components = compute_score_components_v1(instrument)
        structural_components_by_id[canonical] = components
        feature_row = features_by_id.get(canonical)
        if feature_row is None:
            code = REASON_INCOMPLETE_FEATURE_CANDIDATE
            exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
            excluded_rows.append(
                RankedCandidateV1(
                    rank=0,
                    canonical_instrument_id=canonical,
                    venue_native_id=native,
                    total_score=float(sum(components.values())),
                    score_components=components,
                    data_quality_status=str(instrument.get("data_quality_status") or ""),
                    eligibility_status=ELIGIBILITY_EXCLUDED,
                    exclusion_reason_codes=(code,),
                    tie_break_values={
                        "balanced_movement_score": "",
                        "venue_native_id": native,
                        "canonical_instrument_id": canonical,
                        "economic_set_membership": EconomicSetMembership.EXCLUDED_FROM_S_STAR.value,
                        "exclusion": code,
                    },
                )
            )
            continue
        vol, amp, reason = _feature_ready_pair(feature_row)
        if reason is not None or vol is None or amp is None:
            code = reason or REASON_INVALID_FEATURE_CANDIDATE
            exclusion_counts[code] = exclusion_counts.get(code, 0) + 1
            excluded_rows.append(
                RankedCandidateV1(
                    rank=0,
                    canonical_instrument_id=canonical,
                    venue_native_id=native,
                    total_score=float(sum(components.values())),
                    score_components=components,
                    data_quality_status=str(instrument.get("data_quality_status") or ""),
                    eligibility_status=ELIGIBILITY_EXCLUDED,
                    exclusion_reason_codes=(code,),
                    tie_break_values={
                        "balanced_movement_score": "",
                        "venue_native_id": native,
                        "canonical_instrument_id": canonical,
                        "economic_set_membership": EconomicSetMembership.EXCLUDED_FROM_S_STAR.value,
                        "exclusion": code,
                    },
                )
            )
            continue
        vol_raw[canonical] = vol
        amp_raw[canonical] = amp
        identities[canonical] = native
        s_star_feature_rows[canonical] = feature_row

    scores = build_balanced_movement_scores_v1(
        identities=identities,
        volatility_raw_by_id=vol_raw,
        amplitude_raw_by_id=amp_raw,
    )
    n = len(scores)
    if n == 0:
        economic_rank_state = ECONOMIC_RANK_STATE_S_STAR_N0
        exclusion_counts[REASON_NO_COMPLETE_ECONOMIC_CANDIDATES] = (
            exclusion_counts.get(REASON_NO_COMPLETE_ECONOMIC_CANDIDATES, 0) + 1
        )
        exclusion_counts[RankingFailureCodeV1.NO_ELIGIBLE_CANDIDATES.value] = 1
    elif n == 1:
        economic_rank_state = ECONOMIC_RANK_STATE_S_STAR_N1
    else:
        economic_rank_state = ECONOMIC_RANK_STATE_S_STAR_N_GE_2

    ranked: list[RankedCandidateV1] = []
    overflow: list[RankedCandidateV1] = []
    limit = max(0, int(top_n))

    for idx, score in enumerate(scores, start=1):
        components = structural_components_by_id[score.canonical_instrument_id]
        assigned = RankedCandidateV1(
            rank=idx if idx <= limit else 0,
            canonical_instrument_id=score.canonical_instrument_id,
            venue_native_id=score.venue_native_id,
            total_score=float(score.balanced_movement_score),
            score_components=components,
            data_quality_status="PASS",
            eligibility_status=ELIGIBILITY_ELIGIBLE,
            exclusion_reason_codes=(),
            tie_break_values={
                "balanced_movement_score": f"{score.balanced_movement_score:.16e}",
                "volatility_percentile": f"{score.volatility_percentile:.16e}",
                "amplitude_percentile": f"{score.amplitude_percentile:.16e}",
                "venue_native_id": score.venue_native_id,
                "canonical_instrument_id": score.canonical_instrument_id,
                "economic_set_membership": EconomicSetMembership.S_STAR.value,
            },
        )
        if idx <= limit:
            ranked.append(assigned)
        else:
            overflow.append(assigned)

    explainability = _build_explainability_witness_v1(
        feature_production_snapshot=feature_production_snapshot,
        scores=scores,
        s_star_feature_rows=s_star_feature_rows,
        economic_rank_state=economic_rank_state,
        n=n,
    )

    excluded_sorted = sorted(
        excluded_rows + overflow,
        key=lambda c: (c.venue_native_id, c.canonical_instrument_id),
    )
    return EconomicRankingResultV1(
        ranked=tuple(ranked),
        excluded=tuple(excluded_sorted),
        economic_rank_state=economic_rank_state,
        s_star_count=n,
        explainability=explainability,
        exclusion_counts=dict(sorted(exclusion_counts.items())),
    )


def _build_explainability_witness_v1(
    *,
    feature_production_snapshot: RankingFeatureProductionSnapshotV1,
    scores: Sequence[CandidateEconomicScoreV1],
    s_star_feature_rows: Mapping[str, InstrumentRawFeatureProductionV1],
    economic_rank_state: str,
    n: int,
) -> RankingFeatureExplainabilityWitnessV1:
    candidates: list[RankingCandidateFeatureBundleV1] = []
    for idx, score in enumerate(scores, start=1):
        raw_features = s_star_feature_rows[score.canonical_instrument_id].raw_features
        transform = NormalizedTransformId(score.normalized_transform_id)
        norm = (
            NormalizedRankingFeatureValueV1(
                feature_policy_id=VOLATILITY_POLICY_ID,
                state=RankingFeatureValueState.READY,
                cross_section_n=n,
                midrank=score.volatility_midrank,
                percentile=score.volatility_percentile,
                normalized_transform_id=transform,
                direction="HIGHER_IS_BETTER",
                clipping_policy="NONE",
                floor_policy="NONE",
            ),
            NormalizedRankingFeatureValueV1(
                feature_policy_id=AMPLITUDE_POLICY_ID,
                state=RankingFeatureValueState.READY,
                cross_section_n=n,
                midrank=score.amplitude_midrank,
                percentile=score.amplitude_percentile,
                normalized_transform_id=transform,
                direction="HIGHER_IS_BETTER",
                clipping_policy="NONE",
                floor_policy="NONE",
            ),
        )
        contributions = (
            ScoreContributionV1(
                feature_policy_id=VOLATILITY_POLICY_ID,
                weight=VOLATILITY_WEIGHT,
                percentile_used=score.volatility_percentile,
                weighted_contribution=VOLATILITY_WEIGHT * score.volatility_percentile,
                direction="HIGHER_IS_BETTER",
            ),
            ScoreContributionV1(
                feature_policy_id=AMPLITUDE_POLICY_ID,
                weight=AMPLITUDE_WEIGHT,
                percentile_used=score.amplitude_percentile,
                weighted_contribution=AMPLITUDE_WEIGHT * score.amplitude_percentile,
                direction="HIGHER_IS_BETTER",
            ),
        )
        tie = (
            TieBreakWitnessV1(
                stage=TieBreakStage.PRIMARY,
                order_key="balanced_movement_score",
                direction="DESC",
                value=f"{score.balanced_movement_score:.16e}",
                terminal_identity_fallback=False,
            ),
            TieBreakWitnessV1(
                stage=TieBreakStage.SECONDARY,
                order_key="venue_native_id",
                direction="ASC",
                value=score.venue_native_id,
                terminal_identity_fallback=True,
            ),
            TieBreakWitnessV1(
                stage=TieBreakStage.TERTIARY,
                order_key="canonical_instrument_id",
                direction="ASC",
                value=score.canonical_instrument_id,
                terminal_identity_fallback=True,
            ),
        )
        structural = StructuralEligibilityWitnessV1(
            structural_eligibility_pass=True,
            structural_score_component_keys=SCORE_COMPONENT_KEYS,
            exclusion_reason_codes=(),
        )
        candidates.append(
            RankingCandidateFeatureBundleV1(
                canonical_instrument_id=score.canonical_instrument_id,
                venue_native_id=score.venue_native_id,
                structural_witness=structural,
                economic_set_membership=EconomicSetMembership.S_STAR,
                raw_features=raw_features,
                normalized_features=norm,
                score_contributions=contributions,
                balanced_movement_score=score.balanced_movement_score,
                rank_position=idx,
                tie_break_witness=tie,
            )
        )

    pairwise: list[PairwiseOrderWitnessV1] = []
    for left, right in zip(scores, scores[1:]):
        if left.balanced_movement_score != right.balanced_movement_score:
            stage = TieBreakStage.PRIMARY
            explanation = "balanced_movement_score_desc"
        elif left.venue_native_id != right.venue_native_id:
            stage = TieBreakStage.SECONDARY
            explanation = "venue_native_id_asc_fallback"
        else:
            stage = TieBreakStage.TERTIARY
            explanation = "canonical_instrument_id_asc_fallback"
        pairwise.append(
            PairwiseOrderWitnessV1(
                higher_rank_canonical_instrument_id=left.canonical_instrument_id,
                lower_rank_canonical_instrument_id=right.canonical_instrument_id,
                decisive_stage=stage,
                explanation=explanation,
            )
        )

    witness = RankingFeatureExplainabilityWitnessV1(
        schema_version=FEATURE_WITNESS_SCHEMA,
        policy_identity=build_policy_identity_v1(),
        input2_provenance=feature_production_snapshot.input2_provenance,
        s_star_count=n,
        economic_rank_state=economic_rank_state,
        order_primary=ORDER_PRIMARY,
        order_secondary=ORDER_SECONDARY,
        order_tertiary=ORDER_TERTIARY,
        candidates=tuple(candidates),
        pairwise_order_witness=tuple(pairwise),
        integrity_digest="",
        authority={
            **authority_block_v1(),
            "B06_IMPLEMENTED": True,
            "ECONOMIC_RANK_ACTIVATED": True,
            "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED": True,
            "SELECTION_AUTHORITY_CREATED": False,
            "BINDING_EFFECT": False,
        },
    )
    return witness.with_integrity_digest()
