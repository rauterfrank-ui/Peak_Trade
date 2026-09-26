"""Peak Trade Ranking Feature Contract V1 (B04).

Typed contract/DTO seam for B03-ratified Cap 2.2 economic ranking features.
Schema and validation only: no feature production (B05), no productive
economic rank activation (B06), no selection/binding authority, no live or
external effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    canonical_digest_v1,
)
from src.ops.peak_trade_ranking_matrix_policy_v1 import (
    AMPLITUDE_DIRECTION,
    AMPLITUDE_POLICY_ID,
    AMPLITUDE_RAW_FEATURE_NORMALIZATION,
    AMPLITUDE_UNITS,
    AMPLITUDE_WEIGHT,
    INPUT2_MAX_AGE_SECONDS,
    INPUT2_MAX_AGE_SECONDS_RATIFIED,
    ORDER_PRIMARY,
    ORDER_SECONDARY,
    ORDER_TERTIARY,
    POLICY_ID,
    POLICY_VERSION,
    PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
    ECONOMIC_RANK_ACTIVATED,
    SCORE_CONSTRUCTION,
    SOLE_PRODUCTIVE_SELECTION_OWNER,
    CROSS_UNIVERSE_AUTHORITY,
    VOLATILITY_DIRECTION,
    VOLATILITY_POLICY_ID,
    VOLATILITY_RAW_FEATURE_NORMALIZATION,
    VOLATILITY_UNITS,
    VOLATILITY_WEIGHT,
    compute_ranking_matrix_policy_digest_v1,
)
from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    SCORE_COMPONENT_KEYS as STRUCTURAL_SCORE_COMPONENT_KEYS,
)

PACKAGE_MARKER = "PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1=true"
CONTRACT_ID = "PEAK_TRADE_RANKING_FEATURE_CONTRACT_V1"
CONTRACT_VERSION = "peak_trade_ranking_feature_contract/v1"
SCHEMA_VERSION = "peak_trade_ranking_feature_witness.v1"
OWNER_GO_THIS_SLICE = "PEAK_TRADE_B04_RANKING_FEATURE_CONTRACT_V1"
BOUND_ORIGIN_MAIN_SHA = "9117b02e6c1ba93732c3efa17d1bba47f77294ae"
CONTRACT_CONFIG_REL_PATH = "config/governance/peak_trade_ranking_feature_contract_v1.json"
CANONICAL_SERIALIZATION_VERSION = "peak_trade_ranking_feature_contract_canonical_json_v1"

CAPABILITY_ID_CAP22 = "CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1"
PRODUCTIVE_SELECTION_OWNER = "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1"

B04_IMPLEMENTED = True
AUTHORITY_EFFECT = "NONE"
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
SELECTION_AUTHORITY_CREATED = False
BINDING_EFFECT = False
RUNTIME_WIRING_ADDED = False

RATIFIED_ECONOMIC_FEATURE_POLICY_IDS: tuple[str, ...] = (
    VOLATILITY_POLICY_ID,
    AMPLITUDE_POLICY_ID,
)

RATIFIED_FEATURE_WEIGHTS: Mapping[str, float] = {
    VOLATILITY_POLICY_ID: VOLATILITY_WEIGHT,
    AMPLITUDE_POLICY_ID: AMPLITUDE_WEIGHT,
}

RATIFIED_FEATURE_UNITS: Mapping[str, str] = {
    VOLATILITY_POLICY_ID: VOLATILITY_UNITS,
    AMPLITUDE_POLICY_ID: AMPLITUDE_UNITS,
}

RATIFIED_FEATURE_DIRECTIONS: Mapping[str, str] = {
    VOLATILITY_POLICY_ID: VOLATILITY_DIRECTION,
    AMPLITUDE_POLICY_ID: AMPLITUDE_DIRECTION,
}

RATIFIED_RAW_NORMALIZATION: Mapping[str, str] = {
    VOLATILITY_POLICY_ID: VOLATILITY_RAW_FEATURE_NORMALIZATION,
    AMPLITUDE_POLICY_ID: AMPLITUDE_RAW_FEATURE_NORMALIZATION,
}

PROFILE_OBSERVABILITY_AUTHORITY = "NONE"
STRUCTURAL_ELIGIBILITY_RANKING_AUTHORITY = False


class PeakTradeRankingFeatureContractError(ValueError):
    """Fail-closed ranking feature contract error."""


class RankingFeatureValueState(str, Enum):
    READY = "READY"
    MISSING = "MISSING"
    INVALID = "INVALID"
    INCOMPLETE_WARMUP = "INCOMPLETE_WARMUP"
    NOT_READY = "NOT_READY"


class EconomicSetMembership(str, Enum):
    S_STAR = "S_STAR"
    EXCLUDED_FROM_S_STAR = "EXCLUDED_FROM_S_STAR"


class Input2FreshnessObservation(str, Enum):
    """Neutral transport only; no ratified max-age threshold in B04."""

    NOT_OBSERVED = "NOT_OBSERVED"
    AGE_OBSERVED = "AGE_OBSERVED"
    READINESS_DECLARED = "READINESS_DECLARED"


class NormalizedTransformId(str, Enum):
    MIDRANK_PERCENTILE_V1 = "MIDRANK_PERCENTILE_V1"
    SINGLETON_NEUTRAL_V1 = "SINGLETON_NEUTRAL_V1"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TieBreakStage(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    TERTIARY = "TERTIARY"


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class RankingPolicyIdentityV1:
    ranking_policy_id: str
    ranking_policy_version: str
    ranking_policy_digest: str
    feature_contract_id: str
    feature_contract_version: str
    feature_contract_digest: str
    score_construction_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranking_policy_id": self.ranking_policy_id,
            "ranking_policy_version": self.ranking_policy_version,
            "ranking_policy_digest": self.ranking_policy_digest,
            "feature_contract_id": self.feature_contract_id,
            "feature_contract_version": self.feature_contract_version,
            "feature_contract_digest": self.feature_contract_digest,
            "score_construction_id": self.score_construction_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> RankingPolicyIdentityV1:
        return RankingPolicyIdentityV1(
            ranking_policy_id=str(payload["ranking_policy_id"]),
            ranking_policy_version=str(payload["ranking_policy_version"]),
            ranking_policy_digest=str(payload["ranking_policy_digest"]),
            feature_contract_id=str(payload["feature_contract_id"]),
            feature_contract_version=str(payload["feature_contract_version"]),
            feature_contract_digest=str(payload["feature_contract_digest"]),
            score_construction_id=str(payload["score_construction_id"]),
        )


@dataclass(frozen=True)
class Input2ProvenanceV1:
    economic_input_snapshot_id: str
    economic_input_snapshot_digest: str
    collection_cycle_id: str
    observed_at_event_time: str
    observed_age_seconds: Optional[float]
    freshness_observation: Input2FreshnessObservation
    input2_max_age_seconds_ratified: bool
    input2_max_age_seconds: str

    def to_dict(self) -> dict[str, Any]:
        age: Any = None
        if self.observed_age_seconds is not None:
            age = float(self.observed_age_seconds)
        return {
            "economic_input_snapshot_id": self.economic_input_snapshot_id,
            "economic_input_snapshot_digest": self.economic_input_snapshot_digest,
            "collection_cycle_id": self.collection_cycle_id,
            "observed_at_event_time": self.observed_at_event_time,
            "observed_age_seconds": age,
            "freshness_observation": self.freshness_observation.value,
            "input2_max_age_seconds_ratified": bool(self.input2_max_age_seconds_ratified),
            "input2_max_age_seconds": self.input2_max_age_seconds,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> Input2ProvenanceV1:
        raw_age = payload.get("observed_age_seconds")
        age = None if raw_age is None else float(raw_age)
        return Input2ProvenanceV1(
            economic_input_snapshot_id=str(payload["economic_input_snapshot_id"]),
            economic_input_snapshot_digest=str(payload["economic_input_snapshot_digest"]),
            collection_cycle_id=str(payload["collection_cycle_id"]),
            observed_at_event_time=str(payload["observed_at_event_time"]),
            observed_age_seconds=age,
            freshness_observation=Input2FreshnessObservation(str(payload["freshness_observation"])),
            input2_max_age_seconds_ratified=bool(payload["input2_max_age_seconds_ratified"]),
            input2_max_age_seconds=str(payload["input2_max_age_seconds"]),
        )


@dataclass(frozen=True)
class StructuralEligibilityWitnessV1:
    """Cap 2.1 structural/readiness facts — not economic ranking inputs."""

    structural_eligibility_pass: bool
    structural_score_component_keys: tuple[str, ...]
    exclusion_reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "structural_eligibility_pass": bool(self.structural_eligibility_pass),
            "structural_score_component_keys": list(self.structural_score_component_keys),
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "economic_ranking_authority": False,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> StructuralEligibilityWitnessV1:
        return StructuralEligibilityWitnessV1(
            structural_eligibility_pass=bool(payload["structural_eligibility_pass"]),
            structural_score_component_keys=tuple(
                str(x) for x in (payload.get("structural_score_component_keys") or ())
            ),
            exclusion_reason_codes=tuple(
                str(x) for x in (payload.get("exclusion_reason_codes") or ())
            ),
        )


@dataclass(frozen=True)
class ProfileObservabilityFieldV1:
    field_id: str
    observed_value: str
    authority_effect: str = PROFILE_OBSERVABILITY_AUTHORITY

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "observed_value": self.observed_value,
            "ranking_input_authority": False,
            "authority_effect": self.authority_effect,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> ProfileObservabilityFieldV1:
        return ProfileObservabilityFieldV1(
            field_id=str(payload["field_id"]),
            observed_value=str(payload["observed_value"]),
            authority_effect=str(
                payload.get("authority_effect") or PROFILE_OBSERVABILITY_AUTHORITY
            ),
        )


@dataclass(frozen=True)
class RawRankingFeatureValueV1:
    feature_policy_id: str
    state: RankingFeatureValueState
    raw_value: Optional[float]
    units: str
    direction: str
    observation_window_id: str
    raw_feature_normalization: str
    reason_code: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        raw: Any = None
        if self.raw_value is not None:
            raw = float(self.raw_value)
        return {
            "feature_policy_id": self.feature_policy_id,
            "state": self.state.value,
            "raw_value": raw,
            "units": self.units,
            "direction": self.direction,
            "observation_window_id": self.observation_window_id,
            "raw_feature_normalization": self.raw_feature_normalization,
            "reason_code": self.reason_code,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> RawRankingFeatureValueV1:
        raw_val = payload.get("raw_value")
        value = None if raw_val is None else float(raw_val)
        reason = payload.get("reason_code")
        return RawRankingFeatureValueV1(
            feature_policy_id=str(payload["feature_policy_id"]),
            state=RankingFeatureValueState(str(payload["state"])),
            raw_value=value,
            units=str(payload["units"]),
            direction=str(payload["direction"]),
            observation_window_id=str(payload["observation_window_id"]),
            raw_feature_normalization=str(payload["raw_feature_normalization"]),
            reason_code=None if reason is None else str(reason),
        )


@dataclass(frozen=True)
class NormalizedRankingFeatureValueV1:
    feature_policy_id: str
    state: RankingFeatureValueState
    cross_section_n: int
    midrank: Optional[float]
    percentile: Optional[float]
    normalized_transform_id: NormalizedTransformId
    direction: str
    clipping_policy: str
    floor_policy: str

    def to_dict(self) -> dict[str, Any]:
        mid: Any = None
        if self.midrank is not None:
            mid = float(self.midrank)
        pct: Any = None
        if self.percentile is not None:
            pct = float(self.percentile)
        return {
            "feature_policy_id": self.feature_policy_id,
            "state": self.state.value,
            "cross_section_n": int(self.cross_section_n),
            "midrank": mid,
            "percentile": pct,
            "normalized_transform_id": self.normalized_transform_id.value,
            "direction": self.direction,
            "clipping_policy": self.clipping_policy,
            "floor_policy": self.floor_policy,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> NormalizedRankingFeatureValueV1:
        mid_raw = payload.get("midrank")
        pct_raw = payload.get("percentile")
        return NormalizedRankingFeatureValueV1(
            feature_policy_id=str(payload["feature_policy_id"]),
            state=RankingFeatureValueState(str(payload["state"])),
            cross_section_n=int(payload["cross_section_n"]),
            midrank=None if mid_raw is None else float(mid_raw),
            percentile=None if pct_raw is None else float(pct_raw),
            normalized_transform_id=NormalizedTransformId(str(payload["normalized_transform_id"])),
            direction=str(payload["direction"]),
            clipping_policy=str(payload["clipping_policy"]),
            floor_policy=str(payload["floor_policy"]),
        )


@dataclass(frozen=True)
class ScoreContributionV1:
    feature_policy_id: str
    weight: float
    percentile_used: Optional[float]
    weighted_contribution: Optional[float]
    direction: str

    def to_dict(self) -> dict[str, Any]:
        pct: Any = None
        if self.percentile_used is not None:
            pct = float(self.percentile_used)
        contrib: Any = None
        if self.weighted_contribution is not None:
            contrib = float(self.weighted_contribution)
        return {
            "feature_policy_id": self.feature_policy_id,
            "weight": float(self.weight),
            "percentile_used": pct,
            "weighted_contribution": contrib,
            "direction": self.direction,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> ScoreContributionV1:
        pct_raw = payload.get("percentile_used")
        contrib_raw = payload.get("weighted_contribution")
        return ScoreContributionV1(
            feature_policy_id=str(payload["feature_policy_id"]),
            weight=float(payload["weight"]),
            percentile_used=None if pct_raw is None else float(pct_raw),
            weighted_contribution=None if contrib_raw is None else float(contrib_raw),
            direction=str(payload["direction"]),
        )


@dataclass(frozen=True)
class TieBreakWitnessV1:
    stage: TieBreakStage
    order_key: str
    direction: str
    value: str
    terminal_identity_fallback: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "order_key": self.order_key,
            "direction": self.direction,
            "value": self.value,
            "terminal_identity_fallback": bool(self.terminal_identity_fallback),
            "market_attractiveness_semantics": False,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> TieBreakWitnessV1:
        return TieBreakWitnessV1(
            stage=TieBreakStage(str(payload["stage"])),
            order_key=str(payload["order_key"]),
            direction=str(payload["direction"]),
            value=str(payload["value"]),
            terminal_identity_fallback=bool(payload["terminal_identity_fallback"]),
        )


@dataclass(frozen=True)
class RankingCandidateFeatureBundleV1:
    canonical_instrument_id: str
    venue_native_id: str
    structural_witness: StructuralEligibilityWitnessV1
    economic_set_membership: EconomicSetMembership
    raw_features: tuple[RawRankingFeatureValueV1, ...]
    normalized_features: tuple[NormalizedRankingFeatureValueV1, ...]
    score_contributions: tuple[ScoreContributionV1, ...]
    balanced_movement_score: Optional[float]
    rank_position: Optional[int]
    tie_break_witness: tuple[TieBreakWitnessV1, ...]
    profile_observability: tuple[ProfileObservabilityFieldV1, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        score: Any = None
        if self.balanced_movement_score is not None:
            score = float(self.balanced_movement_score)
        rank: Any = None
        if self.rank_position is not None:
            rank = int(self.rank_position)
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_native_id": self.venue_native_id,
            "structural_witness": self.structural_witness.to_dict(),
            "economic_set_membership": self.economic_set_membership.value,
            "raw_features": [row.to_dict() for row in self.raw_features],
            "normalized_features": [row.to_dict() for row in self.normalized_features],
            "score_contributions": [row.to_dict() for row in self.score_contributions],
            "balanced_movement_score": score,
            "rank_position": rank,
            "tie_break_witness": [row.to_dict() for row in self.tie_break_witness],
            "profile_observability": [row.to_dict() for row in self.profile_observability],
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> RankingCandidateFeatureBundleV1:
        score_raw = payload.get("balanced_movement_score")
        rank_raw = payload.get("rank_position")
        return RankingCandidateFeatureBundleV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_native_id=str(payload["venue_native_id"]),
            structural_witness=StructuralEligibilityWitnessV1.from_dict(
                payload["structural_witness"]
            ),
            economic_set_membership=EconomicSetMembership(str(payload["economic_set_membership"])),
            raw_features=tuple(
                RawRankingFeatureValueV1.from_dict(row)
                for row in (payload.get("raw_features") or ())
            ),
            normalized_features=tuple(
                NormalizedRankingFeatureValueV1.from_dict(row)
                for row in (payload.get("normalized_features") or ())
            ),
            score_contributions=tuple(
                ScoreContributionV1.from_dict(row)
                for row in (payload.get("score_contributions") or ())
            ),
            balanced_movement_score=None if score_raw is None else float(score_raw),
            rank_position=None if rank_raw is None else int(rank_raw),
            tie_break_witness=tuple(
                TieBreakWitnessV1.from_dict(row) for row in (payload.get("tie_break_witness") or ())
            ),
            profile_observability=tuple(
                ProfileObservabilityFieldV1.from_dict(row)
                for row in (payload.get("profile_observability") or ())
            ),
        )


@dataclass(frozen=True)
class PairwiseOrderWitnessV1:
    higher_rank_canonical_instrument_id: str
    lower_rank_canonical_instrument_id: str
    decisive_stage: TieBreakStage
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "higher_rank_canonical_instrument_id": self.higher_rank_canonical_instrument_id,
            "lower_rank_canonical_instrument_id": self.lower_rank_canonical_instrument_id,
            "decisive_stage": self.decisive_stage.value,
            "explanation": self.explanation,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> PairwiseOrderWitnessV1:
        return PairwiseOrderWitnessV1(
            higher_rank_canonical_instrument_id=str(payload["higher_rank_canonical_instrument_id"]),
            lower_rank_canonical_instrument_id=str(payload["lower_rank_canonical_instrument_id"]),
            decisive_stage=TieBreakStage(str(payload["decisive_stage"])),
            explanation=str(payload["explanation"]),
        )


@dataclass(frozen=True)
class RankingFeatureExplainabilityWitnessV1:
    schema_version: str
    policy_identity: RankingPolicyIdentityV1
    input2_provenance: Input2ProvenanceV1
    s_star_count: int
    economic_rank_state: str
    order_primary: str
    order_secondary: str
    order_tertiary: str
    candidates: tuple[RankingCandidateFeatureBundleV1, ...]
    pairwise_order_witness: tuple[PairwiseOrderWitnessV1, ...]
    integrity_digest: str
    authority: Mapping[str, Any] = field(default_factory=dict)

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return canonical_digest_v1(self.deterministic_payload_for_digest())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "policy_identity": self.policy_identity.to_dict(),
            "input2_provenance": self.input2_provenance.to_dict(),
            "s_star_count": int(self.s_star_count),
            "economic_rank_state": self.economic_rank_state,
            "order_primary": self.order_primary,
            "order_secondary": self.order_secondary,
            "order_tertiary": self.order_tertiary,
            "candidates": [row.to_dict() for row in self.candidates],
            "pairwise_order_witness": [row.to_dict() for row in self.pairwise_order_witness],
            "integrity_digest": self.integrity_digest,
            "authority": dict(sorted(self.authority.items())),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> RankingFeatureExplainabilityWitnessV1:
        return RankingFeatureExplainabilityWitnessV1(
            schema_version=str(payload["schema_version"]),
            policy_identity=RankingPolicyIdentityV1.from_dict(payload["policy_identity"]),
            input2_provenance=Input2ProvenanceV1.from_dict(payload["input2_provenance"]),
            s_star_count=int(payload["s_star_count"]),
            economic_rank_state=str(payload["economic_rank_state"]),
            order_primary=str(payload["order_primary"]),
            order_secondary=str(payload["order_secondary"]),
            order_tertiary=str(payload["order_tertiary"]),
            candidates=tuple(
                RankingCandidateFeatureBundleV1.from_dict(row)
                for row in (payload.get("candidates") or ())
            ),
            pairwise_order_witness=tuple(
                PairwiseOrderWitnessV1.from_dict(row)
                for row in (payload.get("pairwise_order_witness") or ())
            ),
            integrity_digest=str(payload.get("integrity_digest") or ""),
            authority=dict(payload.get("authority") or {}),
        )

    def with_integrity_digest(self) -> RankingFeatureExplainabilityWitnessV1:
        digest = self.compute_integrity_digest()
        return RankingFeatureExplainabilityWitnessV1(
            schema_version=self.schema_version,
            policy_identity=self.policy_identity,
            input2_provenance=self.input2_provenance,
            s_star_count=self.s_star_count,
            economic_rank_state=self.economic_rank_state,
            order_primary=self.order_primary,
            order_secondary=self.order_secondary,
            order_tertiary=self.order_tertiary,
            candidates=self.candidates,
            pairwise_order_witness=self.pairwise_order_witness,
            integrity_digest=digest,
            authority=dict(self.authority),
        )


def build_feature_contract_semantic_payload_v1() -> dict[str, Any]:
    return {
        "b04_implemented": B04_IMPLEMENTED,
        "binding_effect": BINDING_EFFECT,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "economic_rank_activated": ECONOMIC_RANK_ACTIVATED,
        "input2_max_age_seconds": INPUT2_MAX_AGE_SECONDS,
        "input2_max_age_seconds_ratified": INPUT2_MAX_AGE_SECONDS_RATIFIED,
        "productive_economic_rank_activation": PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
        "ratified_economic_feature_policy_ids": list(RATIFIED_ECONOMIC_FEATURE_POLICY_IDS),
        "ranking_policy_id": POLICY_ID,
        "ranking_policy_version": POLICY_VERSION,
        "schema_version": SCHEMA_VERSION,
        "score_construction_id": SCORE_CONSTRUCTION,
        "selection_authority_created": SELECTION_AUTHORITY_CREATED,
        "structural_eligibility_ranking_authority": STRUCTURAL_ELIGIBILITY_RANKING_AUTHORITY,
    }


def compute_feature_contract_digest_v1() -> str:
    return canonical_digest_v1(build_feature_contract_semantic_payload_v1())


def build_policy_identity_v1() -> RankingPolicyIdentityV1:
    return RankingPolicyIdentityV1(
        ranking_policy_id=POLICY_ID,
        ranking_policy_version=POLICY_VERSION,
        ranking_policy_digest=compute_ranking_matrix_policy_digest_v1(),
        feature_contract_id=CONTRACT_ID,
        feature_contract_version=CONTRACT_VERSION,
        feature_contract_digest=compute_feature_contract_digest_v1(),
        score_construction_id=SCORE_CONSTRUCTION,
    )


def neutral_input2_provenance_v1(
    *,
    economic_input_snapshot_id: str,
    economic_input_snapshot_digest: str,
    collection_cycle_id: str,
    observed_at_event_time: str,
    observed_age_seconds: Optional[float] = None,
    freshness_observation: Input2FreshnessObservation = Input2FreshnessObservation.NOT_OBSERVED,
) -> Input2ProvenanceV1:
    return Input2ProvenanceV1(
        economic_input_snapshot_id=economic_input_snapshot_id,
        economic_input_snapshot_digest=economic_input_snapshot_digest,
        collection_cycle_id=collection_cycle_id,
        observed_at_event_time=observed_at_event_time,
        observed_age_seconds=observed_age_seconds,
        freshness_observation=freshness_observation,
        input2_max_age_seconds_ratified=INPUT2_MAX_AGE_SECONDS_RATIFIED,
        input2_max_age_seconds=INPUT2_MAX_AGE_SECONDS,
    )


def authority_block_v1() -> dict[str, Any]:
    return {
        "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
        "BINDING_EFFECT": BINDING_EFFECT,
        "B04_IMPLEMENTED": B04_IMPLEMENTED,
        "CAP22_RANKING_CONTEXT_ONLY": True,
        "CAP23_SOLE_SELECTION_OWNER": SOLE_PRODUCTIVE_SELECTION_OWNER,
        "CROSS_UNIVERSE_AUTHORITY": CROSS_UNIVERSE_AUTHORITY,
        "ECONOMIC_RANK_ACTIVATED": ECONOMIC_RANK_ACTIVATED,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "PRODUCTIVE_ECONOMIC_RANK_ACTIVATION": PRODUCTIVE_ECONOMIC_RANK_ACTIVATION,
        "PRODUCTIVE_SELECTION_OWNER": PRODUCTIVE_SELECTION_OWNER,
        "RUNTIME_AUTHORIZATION_EFFECT": RUNTIME_AUTHORIZATION_EFFECT,
        "RUNTIME_WIRING_ADDED": RUNTIME_WIRING_ADDED,
        "SELECTION_AUTHORITY_CREATED": SELECTION_AUTHORITY_CREATED,
        "STRUCTURAL_ELIGIBILITY_RANKING_AUTHORITY": STRUCTURAL_ELIGIBILITY_RANKING_AUTHORITY,
    }


def _assert_ratified_feature_policy_id(feature_policy_id: str) -> None:
    if feature_policy_id not in RATIFIED_ECONOMIC_FEATURE_POLICY_IDS:
        raise PeakTradeRankingFeatureContractError("UNRATIFIED_ECONOMIC_FEATURE", feature_policy_id)
    if feature_policy_id in STRUCTURAL_SCORE_COMPONENT_KEYS:
        raise PeakTradeRankingFeatureContractError(
            "STRUCTURAL_COMPONENT_NOT_ECONOMIC_FEATURE",
            feature_policy_id,
        )


def validate_raw_feature_value_v1(raw: RawRankingFeatureValueV1) -> None:
    _assert_ratified_feature_policy_id(raw.feature_policy_id)
    expected_units = RATIFIED_FEATURE_UNITS[raw.feature_policy_id]
    expected_direction = RATIFIED_FEATURE_DIRECTIONS[raw.feature_policy_id]
    expected_norm = RATIFIED_RAW_NORMALIZATION[raw.feature_policy_id]
    if raw.units != expected_units:
        raise PeakTradeRankingFeatureContractError("FEATURE_UNITS_MISMATCH", raw.feature_policy_id)
    if raw.direction != expected_direction:
        raise PeakTradeRankingFeatureContractError(
            "FEATURE_DIRECTION_MISMATCH",
            raw.feature_policy_id,
        )
    if raw.raw_feature_normalization != expected_norm:
        raise PeakTradeRankingFeatureContractError(
            "RAW_NORMALIZATION_MISMATCH",
            raw.feature_policy_id,
        )
    if raw.state == RankingFeatureValueState.READY:
        if raw.raw_value is None:
            raise PeakTradeRankingFeatureContractError(
                "READY_REQUIRES_RAW_VALUE", raw.feature_policy_id
            )
    elif raw.raw_value is not None:
        raise PeakTradeRankingFeatureContractError(
            "NON_READY_FORBIDS_RAW_VALUE", raw.feature_policy_id
        )


def validate_candidate_bundle_v1(candidate: RankingCandidateFeatureBundleV1) -> None:
    if not candidate.canonical_instrument_id:
        raise PeakTradeRankingFeatureContractError("CANDIDATE_IDENTITY_REQUIRED")
    raw_ids = [row.feature_policy_id for row in candidate.raw_features]
    if tuple(raw_ids) != RATIFIED_ECONOMIC_FEATURE_POLICY_IDS:
        raise PeakTradeRankingFeatureContractError("RATIFIED_RAW_FEATURE_SET_ORDER_MISMATCH")
    norm_ids = [row.feature_policy_id for row in candidate.normalized_features]
    if tuple(norm_ids) != RATIFIED_ECONOMIC_FEATURE_POLICY_IDS:
        raise PeakTradeRankingFeatureContractError("RATIFIED_NORMALIZED_FEATURE_SET_ORDER_MISMATCH")
    for row in candidate.raw_features:
        validate_raw_feature_value_v1(row)
    for row in candidate.normalized_features:
        _assert_ratified_feature_policy_id(row.feature_policy_id)
    for row in candidate.profile_observability:
        if row.authority_effect != PROFILE_OBSERVABILITY_AUTHORITY:
            raise PeakTradeRankingFeatureContractError("PROFILE_FIELD_AUTHORITY_FORBIDDEN")
    if candidate.economic_set_membership == EconomicSetMembership.S_STAR:
        for row in candidate.raw_features:
            if row.state != RankingFeatureValueState.READY:
                raise PeakTradeRankingFeatureContractError(
                    "S_STAR_REQUIRES_READY_RAW_FEATURES",
                    candidate.canonical_instrument_id,
                )
        for row in candidate.normalized_features:
            if row.state != RankingFeatureValueState.READY:
                raise PeakTradeRankingFeatureContractError(
                    "S_STAR_REQUIRES_READY_NORMALIZED_FEATURES",
                    candidate.canonical_instrument_id,
                )
        if candidate.balanced_movement_score is None:
            raise PeakTradeRankingFeatureContractError(
                "S_STAR_REQUIRES_BALANCED_SCORE",
                candidate.canonical_instrument_id,
            )


def validate_explainability_witness_v1(
    witness: RankingFeatureExplainabilityWitnessV1,
    *,
    require_integrity_digest: bool = True,
) -> None:
    if witness.schema_version != SCHEMA_VERSION:
        raise PeakTradeRankingFeatureContractError("SCHEMA_VERSION_MISMATCH")
    if witness.policy_identity.ranking_policy_id != POLICY_ID:
        raise PeakTradeRankingFeatureContractError("POLICY_ID_MISMATCH")
    if witness.policy_identity.feature_contract_id != CONTRACT_ID:
        raise PeakTradeRankingFeatureContractError("FEATURE_CONTRACT_ID_MISMATCH")
    if witness.input2_provenance.input2_max_age_seconds != INPUT2_MAX_AGE_SECONDS:
        raise PeakTradeRankingFeatureContractError("INPUT2_MAX_AGE_MUST_REMAIN_UNRATIFIED")
    if witness.input2_provenance.input2_max_age_seconds_ratified is not False:
        raise PeakTradeRankingFeatureContractError("INPUT2_MAX_AGE_RATIFICATION_FORBIDDEN")
    expected_policy_digest = compute_ranking_matrix_policy_digest_v1()
    if witness.policy_identity.ranking_policy_digest != expected_policy_digest:
        raise PeakTradeRankingFeatureContractError("POLICY_DIGEST_MISMATCH")
    expected_contract_digest = compute_feature_contract_digest_v1()
    if witness.policy_identity.feature_contract_digest != expected_contract_digest:
        raise PeakTradeRankingFeatureContractError("FEATURE_CONTRACT_DIGEST_MISMATCH")
    if require_integrity_digest:
        if witness.integrity_digest != witness.compute_integrity_digest():
            raise PeakTradeRankingFeatureContractError("INTEGRITY_DIGEST_MISMATCH")
    seen_ids: set[str] = set()
    for candidate in witness.candidates:
        if candidate.canonical_instrument_id in seen_ids:
            raise PeakTradeRankingFeatureContractError("DUPLICATE_CANDIDATE_IDENTITY")
        seen_ids.add(candidate.canonical_instrument_id)
        validate_candidate_bundle_v1(candidate)
    s_star = sum(
        1 for c in witness.candidates if c.economic_set_membership == EconomicSetMembership.S_STAR
    )
    if s_star != witness.s_star_count:
        raise PeakTradeRankingFeatureContractError("S_STAR_COUNT_MISMATCH")
    auth = witness.authority or authority_block_v1()
    if auth.get("SELECTION_AUTHORITY_CREATED"):
        raise PeakTradeRankingFeatureContractError("SELECTION_AUTHORITY_FORBIDDEN")
    if auth.get("BINDING_EFFECT"):
        raise PeakTradeRankingFeatureContractError("BINDING_EFFECT_FORBIDDEN")
    if auth.get("PRODUCTIVE_ECONOMIC_RANK_ACTIVATION"):
        raise PeakTradeRankingFeatureContractError("PRODUCTIVE_ACTIVATION_FORBIDDEN")
    if auth.get("ECONOMIC_RANK_ACTIVATED"):
        raise PeakTradeRankingFeatureContractError("ECONOMIC_RANK_ACTIVATED_FORBIDDEN")


def load_contract_config_v1() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    path = root / CONTRACT_CONFIG_REL_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract_config_v1(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise PeakTradeRankingFeatureContractError("CONTRACT_CONFIG_NOT_A_MAPPING")
    expected = build_feature_contract_semantic_payload_v1()
    for key in (
        "contract_id",
        "contract_version",
        "ranking_policy_id",
        "ranking_policy_version",
        "schema_version",
        "score_construction_id",
    ):
        if payload.get(key) != expected[key]:
            raise PeakTradeRankingFeatureContractError("CONTRACT_CONFIG_DRIFT", key)
    if payload.get("input2_max_age_seconds") != INPUT2_MAX_AGE_SECONDS:
        raise PeakTradeRankingFeatureContractError("CONTRACT_CONFIG_MAX_AGE_FABRICATION")
    if payload.get("ratified_economic_feature_policy_ids") != list(
        RATIFIED_ECONOMIC_FEATURE_POLICY_IDS
    ):
        raise PeakTradeRankingFeatureContractError("RATIFIED_FEATURE_SET_MISMATCH")
    digest = compute_feature_contract_digest_v1()
    declared = payload.get("feature_contract_digest")
    if declared is not None and declared != digest:
        raise PeakTradeRankingFeatureContractError("FEATURE_CONTRACT_DIGEST_MISMATCH")
    return {"valid": True, "feature_contract_digest": digest}


def round_trip_witness_v1(witness: RankingFeatureExplainabilityWitnessV1) -> None:
    serialized = canonical_json_dumps(witness.to_dict())
    restored = RankingFeatureExplainabilityWitnessV1.from_dict(json.loads(serialized))
    if canonical_json_dumps(restored.to_dict()) != serialized:
        raise PeakTradeRankingFeatureContractError("ROUND_TRIP_CANONICAL_JSON_MISMATCH")
    validate_explainability_witness_v1(restored, require_integrity_digest=True)


def classify_peak_trade_ranking_feature_contract_v1() -> dict[str, Any]:
    return {
        **authority_block_v1(),
        "b04_implemented": B04_IMPLEMENTED,
        "capability_id_cap22": CAPABILITY_ID_CAP22,
        "contract_id": CONTRACT_ID,
        "contract_version": CONTRACT_VERSION,
        "feature_contract_digest": compute_feature_contract_digest_v1(),
        "owner_go_this_slice": OWNER_GO_THIS_SLICE,
        "ranking_policy_digest": compute_ranking_matrix_policy_digest_v1(),
        "ranking_policy_id": POLICY_ID,
        "ratified_economic_feature_policy_ids": list(RATIFIED_ECONOMIC_FEATURE_POLICY_IDS),
        "schema_version": SCHEMA_VERSION,
    }
