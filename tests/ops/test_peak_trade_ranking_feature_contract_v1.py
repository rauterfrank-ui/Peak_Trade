"""B04 Peak Trade Ranking Feature Contract V1 typed contract tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.ops import peak_trade_ranking_feature_contract_v1 as b04
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_POLICY_ID,
    INPUT2_MAX_AGE_SECONDS,
    INPUT2_MAX_AGE_SECONDS_RATIFIED,
    ORDER_PRIMARY,
    ORDER_SECONDARY,
    ORDER_TERTIARY,
    POLICY_ID,
    VOLATILITY_POLICY_ID,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    SCORE_COMPONENT_KEYS,
)


def _ready_raw(feature_policy_id: str, value: float) -> b04.RawRankingFeatureValueV1:
    return b04.RawRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=b04.RankingFeatureValueState.READY,
        raw_value=value,
        units=b04.RATIFIED_FEATURE_UNITS[feature_policy_id],
        direction=b04.RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        observation_window_id="61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES",
        raw_feature_normalization=b04.RATIFIED_RAW_NORMALIZATION[feature_policy_id],
        reason_code=None,
    )


def _ready_norm(
    feature_policy_id: str, percentile: float, n: int = 2
) -> b04.NormalizedRankingFeatureValueV1:
    return b04.NormalizedRankingFeatureValueV1(
        feature_policy_id=feature_policy_id,
        state=b04.RankingFeatureValueState.READY,
        cross_section_n=n,
        midrank=1.0,
        percentile=percentile,
        normalized_transform_id=b04.NormalizedTransformId.MIDRANK_PERCENTILE_V1,
        direction=b04.RATIFIED_FEATURE_DIRECTIONS[feature_policy_id],
        clipping_policy="NONE",
        floor_policy="NONE",
    )


def _sample_candidate(
    *,
    cid: str = "okx_eea:BTC-USDT-SWAP",
    vid: str = "BTC-USDT-SWAP",
    vol: float = 0.01,
    amp: float = 0.02,
    score: float = 0.75,
    rank: int = 1,
) -> b04.RankingCandidateFeatureBundleV1:
    structural = b04.StructuralEligibilityWitnessV1(
        structural_eligibility_pass=True,
        structural_score_component_keys=SCORE_COMPONENT_KEYS,
        exclusion_reason_codes=(),
    )
    raw = (
        _ready_raw(VOLATILITY_POLICY_ID, vol),
        _ready_raw(AMPLITUDE_POLICY_ID, amp),
    )
    norm = (
        _ready_norm(VOLATILITY_POLICY_ID, 0.8),
        _ready_norm(AMPLITUDE_POLICY_ID, 0.7),
    )
    contributions = (
        b04.ScoreContributionV1(
            feature_policy_id=VOLATILITY_POLICY_ID,
            weight=0.5,
            percentile_used=0.8,
            weighted_contribution=0.4,
            direction="HIGHER_IS_BETTER",
        ),
        b04.ScoreContributionV1(
            feature_policy_id=AMPLITUDE_POLICY_ID,
            weight=0.5,
            percentile_used=0.7,
            weighted_contribution=0.35,
            direction="HIGHER_IS_BETTER",
        ),
    )
    tie = (
        b04.TieBreakWitnessV1(
            stage=b04.TieBreakStage.PRIMARY,
            order_key="balanced_movement_score",
            direction="DESC",
            value=str(score),
            terminal_identity_fallback=False,
        ),
    )
    return b04.RankingCandidateFeatureBundleV1(
        canonical_instrument_id=cid,
        venue_native_id=vid,
        structural_witness=structural,
        economic_set_membership=b04.EconomicSetMembership.S_STAR,
        raw_features=raw,
        normalized_features=norm,
        score_contributions=contributions,
        balanced_movement_score=score,
        rank_position=rank,
        tie_break_witness=tie,
        profile_observability=(
            b04.ProfileObservabilityFieldV1(
                field_id="display_name",
                observed_value="BTC-USDT-SWAP",
            ),
        ),
    )


def _sample_witness() -> b04.RankingFeatureExplainabilityWitnessV1:
    witness = b04.RankingFeatureExplainabilityWitnessV1(
        schema_version=b04.SCHEMA_VERSION,
        policy_identity=b04.build_policy_identity_v1(),
        input2_provenance=b04.neutral_input2_provenance_v1(
            economic_input_snapshot_id="econ-md-snap-1",
            economic_input_snapshot_digest="abc123",
            collection_cycle_id="cycle-1",
            observed_at_event_time="2026-09-26T00:00:00Z",
            observed_age_seconds=120.0,
            freshness_observation=b04.Input2FreshnessObservation.AGE_OBSERVED,
        ),
        s_star_count=1,
        economic_rank_state="S_STAR_N1",
        order_primary=ORDER_PRIMARY,
        order_secondary=ORDER_SECONDARY,
        order_tertiary=ORDER_TERTIARY,
        candidates=(_sample_candidate(),),
        pairwise_order_witness=(),
        integrity_digest="",
        authority=b04.authority_block_v1(),
    )
    return witness.with_integrity_digest()


def test_contract_versioned_and_classify() -> None:
    summary = b04.classify_peak_trade_ranking_feature_contract_v1()
    assert summary["contract_version"] == b04.CONTRACT_VERSION
    assert summary["b04_implemented"] is True
    assert summary["contract_id"] == b04.CONTRACT_ID
    assert summary["ranking_policy_id"] == POLICY_ID


def test_ratified_features_explicit() -> None:
    assert b04.RATIFIED_ECONOMIC_FEATURE_POLICY_IDS == (
        VOLATILITY_POLICY_ID,
        AMPLITUDE_POLICY_ID,
    )
    payload = b04.build_feature_contract_semantic_payload_v1()
    assert payload["ratified_economic_feature_policy_ids"] == list(
        b04.RATIFIED_ECONOMIC_FEATURE_POLICY_IDS
    )


def test_raw_and_normalized_semantically_separate() -> None:
    candidate = _sample_candidate()
    b04.validate_candidate_bundle_v1(candidate)
    assert candidate.raw_features[0].raw_value == pytest.approx(0.01)
    assert candidate.normalized_features[0].percentile == pytest.approx(0.8)
    assert candidate.raw_features[0].feature_policy_id == VOLATILITY_POLICY_ID


def test_explainability_witness_deterministic_digest() -> None:
    w1 = _sample_witness()
    w2 = _sample_witness()
    assert w1.integrity_digest == w2.integrity_digest
    assert len(w1.integrity_digest) == 64
    b04.validate_explainability_witness_v1(w1)


def test_candidate_identity_unique() -> None:
    witness = _sample_witness()
    dup = b04.RankingFeatureExplainabilityWitnessV1(
        schema_version=witness.schema_version,
        policy_identity=witness.policy_identity,
        input2_provenance=witness.input2_provenance,
        s_star_count=2,
        economic_rank_state=witness.economic_rank_state,
        order_primary=witness.order_primary,
        order_secondary=witness.order_secondary,
        order_tertiary=witness.order_tertiary,
        candidates=(
            _sample_candidate(cid="okx_eea:BTC-USDT-SWAP", rank=1),
            _sample_candidate(cid="okx_eea:BTC-USDT-SWAP", rank=2),
        ),
        pairwise_order_witness=(),
        integrity_digest="",
        authority=witness.authority,
    ).with_integrity_digest()
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="DUPLICATE"):
        b04.validate_explainability_witness_v1(dup)


def test_missing_required_inputs_fail_closed_for_s_star() -> None:
    bad_raw = b04.RawRankingFeatureValueV1(
        feature_policy_id=VOLATILITY_POLICY_ID,
        state=b04.RankingFeatureValueState.MISSING,
        raw_value=None,
        units=b04.RATIFIED_FEATURE_UNITS[VOLATILITY_POLICY_ID],
        direction=b04.RATIFIED_FEATURE_DIRECTIONS[VOLATILITY_POLICY_ID],
        observation_window_id="61_CONTIGUOUS_FINALIZED_PT1M_MARK_PRICES",
        raw_feature_normalization="NONE",
        reason_code="MISSING",
    )
    candidate = _sample_candidate()
    candidate = b04.RankingCandidateFeatureBundleV1(
        canonical_instrument_id=candidate.canonical_instrument_id,
        venue_native_id=candidate.venue_native_id,
        structural_witness=candidate.structural_witness,
        economic_set_membership=b04.EconomicSetMembership.S_STAR,
        raw_features=(bad_raw, candidate.raw_features[1]),
        normalized_features=candidate.normalized_features,
        score_contributions=candidate.score_contributions,
        balanced_movement_score=candidate.balanced_movement_score,
        rank_position=candidate.rank_position,
        tie_break_witness=candidate.tie_break_witness,
    )
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="S_STAR_REQUIRES"):
        b04.validate_candidate_bundle_v1(candidate)


def test_input2_max_age_not_ratified_in_contract() -> None:
    assert INPUT2_MAX_AGE_SECONDS_RATIFIED is False
    assert INPUT2_MAX_AGE_SECONDS == "UNRATIFIED"
    witness = _sample_witness()
    assert witness.input2_provenance.input2_max_age_seconds == "UNRATIFIED"
    bad_prov = b04.Input2ProvenanceV1(
        economic_input_snapshot_id="x",
        economic_input_snapshot_digest="y",
        collection_cycle_id="z",
        observed_at_event_time="t",
        observed_age_seconds=None,
        freshness_observation=b04.Input2FreshnessObservation.NOT_OBSERVED,
        input2_max_age_seconds_ratified=False,
        input2_max_age_seconds="300",
    )
    bad = b04.RankingFeatureExplainabilityWitnessV1(
        schema_version=witness.schema_version,
        policy_identity=witness.policy_identity,
        input2_provenance=bad_prov,
        s_star_count=witness.s_star_count,
        economic_rank_state=witness.economic_rank_state,
        order_primary=witness.order_primary,
        order_secondary=witness.order_secondary,
        order_tertiary=witness.order_tertiary,
        candidates=witness.candidates,
        pairwise_order_witness=witness.pairwise_order_witness,
        integrity_digest=witness.integrity_digest,
        authority=witness.authority,
    )
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="MAX_AGE"):
        b04.validate_explainability_witness_v1(bad)


def test_structural_components_not_economic_features() -> None:
    for key in SCORE_COMPONENT_KEYS:
        with pytest.raises(b04.PeakTradeRankingFeatureContractError):
            b04._assert_ratified_feature_policy_id(key)


def test_profile_fields_no_ranking_authority() -> None:
    field_row = b04.ProfileObservabilityFieldV1(
        field_id="profile_metric",
        observed_value="1.0",
        authority_effect="RANKING",
    )
    candidate = _sample_candidate()
    candidate = b04.RankingCandidateFeatureBundleV1(
        canonical_instrument_id=candidate.canonical_instrument_id,
        venue_native_id=candidate.venue_native_id,
        structural_witness=candidate.structural_witness,
        economic_set_membership=candidate.economic_set_membership,
        raw_features=candidate.raw_features,
        normalized_features=candidate.normalized_features,
        score_contributions=candidate.score_contributions,
        balanced_movement_score=candidate.balanced_movement_score,
        rank_position=candidate.rank_position,
        tie_break_witness=candidate.tie_break_witness,
        profile_observability=(field_row,),
    )
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="PROFILE"):
        b04.validate_candidate_bundle_v1(candidate)


def test_cap23_sole_selection_owner_and_no_activation() -> None:
    auth = b04.authority_block_v1()
    assert auth["CAP23_SOLE_SELECTION_OWNER"] is True
    assert auth["SELECTION_AUTHORITY_CREATED"] is False
    assert auth["PRODUCTIVE_ECONOMIC_RANK_ACTIVATION"] is False
    assert auth["ECONOMIC_RANK_ACTIVATED"] is False
    assert auth["BINDING_EFFECT"] is False


def test_no_binding_effect_on_witness() -> None:
    witness = _sample_witness()
    bad_auth = dict(witness.authority)
    bad_auth["BINDING_EFFECT"] = True
    bad = b04.RankingFeatureExplainabilityWitnessV1(
        schema_version=witness.schema_version,
        policy_identity=witness.policy_identity,
        input2_provenance=witness.input2_provenance,
        s_star_count=witness.s_star_count,
        economic_rank_state=witness.economic_rank_state,
        order_primary=witness.order_primary,
        order_secondary=witness.order_secondary,
        order_tertiary=witness.order_tertiary,
        candidates=witness.candidates,
        pairwise_order_witness=witness.pairwise_order_witness,
        integrity_digest="",
        authority=bad_auth,
    ).with_integrity_digest()
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="BINDING"):
        b04.validate_explainability_witness_v1(bad)


def test_deterministic_serialization_round_trip() -> None:
    witness = _sample_witness()
    b04.round_trip_witness_v1(witness)


def test_contract_config_validates() -> None:
    payload = b04.load_contract_config_v1()
    result = b04.validate_contract_config_v1(payload)
    assert result["valid"] is True
    assert result["feature_contract_digest"] == b04.compute_feature_contract_digest_v1()


def test_contract_config_rejects_fabricated_max_age() -> None:
    payload = dict(b04.load_contract_config_v1())
    payload["input2_max_age_seconds"] = 900
    with pytest.raises(b04.PeakTradeRankingFeatureContractError, match="MAX_AGE"):
        b04.validate_contract_config_v1(payload)


def test_no_runtime_wiring_in_ranking_producer() -> None:
    root = Path(__file__).resolve().parents[2]
    producer = root / "src/ops/productive_futures_ranking_producer_v1/producer_v1.py"
    ranking = root / "src/ops/productive_futures_ranking_producer_v1/ranking_v1.py"
    text = producer.read_text(encoding="utf-8") + ranking.read_text(encoding="utf-8")
    assert "peak_trade_ranking_feature_contract_v1" not in text


def test_module_has_no_network_imports() -> None:
    path = Path(__file__).resolve().parents[2] / "src/ops/peak_trade_ranking_feature_contract_v1.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "requests" not in alias.name
                assert "httpx" not in alias.name
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "requests" not in node.module
            assert "httpx" not in node.module


def test_pairwise_order_witness_round_trip() -> None:
    pair = b04.PairwiseOrderWitnessV1(
        higher_rank_canonical_instrument_id="okx_eea:AAA",
        lower_rank_canonical_instrument_id="okx_eea:BBB",
        decisive_stage=b04.TieBreakStage.SECONDARY,
        explanation="venue_native_id ASC",
    )
    restored = b04.PairwiseOrderWitnessV1.from_dict(pair.to_dict())
    assert json.dumps(restored.to_dict(), sort_keys=True) == json.dumps(
        pair.to_dict(), sort_keys=True
    )
