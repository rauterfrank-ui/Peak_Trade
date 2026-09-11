"""Offline MVR evidence-harness output records. Diagnostic only."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Optional

from src.ops.cap22_offline_mvr_evidence_harness_v1.constants_v1 import (
    POLICY_VERSION,
    TOP20_DIAGNOSTIC_LIMIT,
    TOP20_IS_AUTHORITATIVE,
)
from src.ops.economic_md_input_producer_v1.models_v1 import canonical_json_dumps, sha256_hex


def authority_block() -> dict[str, Any]:
    from src.ops.cap22_offline_mvr_evidence_harness_v1 import constants_v1 as c

    return {
        "ACTIVE_SET_SEMANTICS_CREATED": c.ACTIVE_SET_SEMANTICS_CREATED,
        "AUTHORITY_EFFECT": c.AUTHORITY_EFFECT,
        "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED": c.CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
        "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED": (
            c.ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
        ),
        "ECONOMIC_RANK_ACTIVATED": c.ECONOMIC_RANK_ACTIVATED,
        "FORWARD_LABEL_METRICS_PRESENT": c.FORWARD_LABEL_METRICS_PRESENT,
        "HARNESS_NETWORK_READ_REQUIRED": c.HARNESS_NETWORK_READ_REQUIRED,
        "HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT": (
            c.HISTORICAL_PIT_WALK_FORWARD_EVIDENCE_PRESENT
        ),
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": c.MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "PDF_STEP_5_STATUS": c.PDF_STEP_5_STATUS,
        "PDF_STEP_7_STATUS": c.PDF_STEP_7_STATUS,
        "POLICY_B_THRESHOLD_SET_RATIFIED": c.POLICY_B_THRESHOLD_SET_RATIFIED,
        "POLICY_RATIFICATION_JUSTIFIED": c.POLICY_RATIFICATION_JUSTIFIED,
        "POLICY_WINNER_OUTPUT_PRESENT": c.POLICY_WINNER_OUTPUT_PRESENT,
        "PRODUCTIVE_MF_HOST_JOIN": c.PRODUCTIVE_MF_HOST_JOIN,
        "RUNTIME_AUTHORITY_GRANTED": c.RUNTIME_AUTHORITY_GRANTED,
        "TOP20_DIAGNOSTIC_ONLY": c.TOP20_DIAGNOSTIC_ONLY,
        "TOP20_IS_AUTHORITATIVE": c.TOP20_IS_AUTHORITATIVE,
    }


@dataclass(frozen=True)
class CandidateUniverseMemberV1:
    canonical_instrument_id: str
    venue_native_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_native_id": self.venue_native_id,
        }


@dataclass(frozen=True)
class RankedOfflineCandidateV1:
    rank: int
    canonical_instrument_id: str
    venue_native_id: str
    sort_keys: Mapping[str, str]
    residual_tie_break: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "rank": self.rank,
            "residual_tie_break": dict(self.residual_tie_break),
            "sort_keys": dict(self.sort_keys),
            "venue_native_id": self.venue_native_id,
        }


@dataclass(frozen=True)
class NotRankableCandidateV1:
    canonical_instrument_id: str
    venue_native_id: str
    reason_code: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "reason_code": self.reason_code,
            "venue_native_id": self.venue_native_id,
        }


@dataclass(frozen=True)
class OfflinePolicyRankingV1:
    policy_id: str
    policy_version: str
    policy_class: str
    threshold_set_id: Optional[str]
    threshold_id: Optional[str]
    threshold_value: Optional[str]
    ordered_ranking: tuple[RankedOfflineCandidateV1, ...]
    not_rankable: tuple[NotRankableCandidateV1, ...]
    gate_pass_count: Optional[int]
    exact_zero_not_rankable_count: Optional[int]
    ranking_output_digest: str
    top20_diagnostic: tuple[RankedOfflineCandidateV1, ...]
    top20_authoritative: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "exact_zero_not_rankable_count": self.exact_zero_not_rankable_count,
            "gate_pass_count": self.gate_pass_count,
            "not_rankable": [row.to_dict() for row in self.not_rankable],
            "ordered_ranking": [row.to_dict() for row in self.ordered_ranking],
            "policy_class": self.policy_class,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "ranking_output_digest": self.ranking_output_digest,
            "threshold_id": self.threshold_id,
            "threshold_set_id": self.threshold_set_id,
            "threshold_value": self.threshold_value,
            "top20_authoritative": self.top20_authoritative,
            "top20_diagnostic": [row.to_dict() for row in self.top20_diagnostic],
            "top20_diagnostic_only": True,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("ranking_output_digest", None)
        payload.pop("top20_diagnostic", None)
        payload.pop("top20_authoritative", None)
        payload.pop("top20_diagnostic_only", None)
        return payload


def attach_ranking_digest(ranking: OfflinePolicyRankingV1) -> OfflinePolicyRankingV1:
    digest = sha256_hex(canonical_json_dumps(ranking.deterministic_payload_for_digest()))
    return OfflinePolicyRankingV1(
        policy_id=ranking.policy_id,
        policy_version=ranking.policy_version,
        policy_class=ranking.policy_class,
        threshold_set_id=ranking.threshold_set_id,
        threshold_id=ranking.threshold_id,
        threshold_value=ranking.threshold_value,
        ordered_ranking=ranking.ordered_ranking,
        not_rankable=ranking.not_rankable,
        gate_pass_count=ranking.gate_pass_count,
        exact_zero_not_rankable_count=ranking.exact_zero_not_rankable_count,
        ranking_output_digest=digest,
        top20_diagnostic=ranking.top20_diagnostic,
        top20_authoritative=ranking.top20_authoritative,
    )


def top20_diagnostic_from(
    ordered: tuple[RankedOfflineCandidateV1, ...],
) -> tuple[RankedOfflineCandidateV1, ...]:
    return ordered[:TOP20_DIAGNOSTIC_LIMIT]


def residual_tie_break(venue_native_id: str, canonical_instrument_id: str) -> dict[str, str]:
    return {
        "canonical_instrument_id": canonical_instrument_id,
        "venue_native_id": venue_native_id,
    }


def ranked_from_sorted(
    rows: list[tuple[tuple[Any, ...], str, str, Mapping[str, str]]],
) -> tuple[RankedOfflineCandidateV1, ...]:
    ranked: list[RankedOfflineCandidateV1] = []
    for index, (_sort_tuple, venue, canonical, sort_keys) in enumerate(rows, start=1):
        ranked.append(
            RankedOfflineCandidateV1(
                rank=index,
                canonical_instrument_id=canonical,
                venue_native_id=venue,
                sort_keys=dict(sort_keys),
                residual_tie_break=residual_tie_break(venue, canonical),
            )
        )
    return tuple(ranked)


def make_policy_ranking(
    *,
    policy_id: str,
    policy_class: str,
    ordered: tuple[RankedOfflineCandidateV1, ...],
    not_rankable: tuple[NotRankableCandidateV1, ...] = (),
    threshold_set_id: Optional[str] = None,
    threshold_id: Optional[str] = None,
    threshold_value: Optional[str] = None,
    gate_pass_count: Optional[int] = None,
    exact_zero_not_rankable_count: Optional[int] = None,
) -> OfflinePolicyRankingV1:
    return attach_ranking_digest(
        OfflinePolicyRankingV1(
            policy_id=policy_id,
            policy_version=POLICY_VERSION,
            policy_class=policy_class,
            threshold_set_id=threshold_set_id,
            threshold_id=threshold_id,
            threshold_value=threshold_value,
            ordered_ranking=ordered,
            not_rankable=not_rankable,
            gate_pass_count=gate_pass_count,
            exact_zero_not_rankable_count=exact_zero_not_rankable_count,
            ranking_output_digest="",
            top20_diagnostic=top20_diagnostic_from(ordered),
            top20_authoritative=TOP20_IS_AUTHORITATIVE,
        )
    )


def overlap_and_displacement_v1(
    left: OfflinePolicyRankingV1,
    right: OfflinePolicyRankingV1,
) -> dict[str, Any]:
    left_ranks = {row.canonical_instrument_id: row.rank for row in left.ordered_ranking}
    right_ranks = {row.canonical_instrument_id: row.rank for row in right.ordered_ranking}
    left_ids = set(left_ranks)
    right_ids = set(right_ranks)
    intersection = sorted(left_ids & right_ids)
    union = left_ids | right_ids
    jaccard = Decimal(len(intersection)) / Decimal(len(union)) if union else Decimal(1)
    displacements = {
        instrument_id: left_ranks[instrument_id] - right_ranks[instrument_id]
        for instrument_id in intersection
    }
    return {
        "jaccard_overlap": format(jaccard, "f"),
        "left_policy_id": left.policy_id,
        "overlap_count": len(intersection),
        "rank_displacement_left_minus_right": displacements,
        "right_policy_id": right.policy_id,
        "union_count": len(union),
    }
