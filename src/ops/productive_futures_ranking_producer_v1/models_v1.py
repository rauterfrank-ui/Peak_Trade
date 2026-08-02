"""Versioned DTOs for productive futures ranking snapshots (Capability 2.2)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CAPABILITY_ID,
    PRODUCER_VERSION,
    RANKING_POLICY_ID,
    RANKING_POLICY_PROVENANCE,
    RANKING_POLICY_VERSION,
    SCHEMA_VERSION,
    SCORE_COMPONENT_KEYS,
    TOP20_CANDIDATE_CONTEXT_LIMIT,
    VENUE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class RankedCandidateV1:
    rank: int
    canonical_instrument_id: str
    venue_native_id: str
    total_score: float
    score_components: Mapping[str, float]
    data_quality_status: str
    eligibility_status: str
    exclusion_reason_codes: tuple[str, ...]
    tie_break_values: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": int(self.rank),
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_native_id": self.venue_native_id,
            "total_score": float(self.total_score),
            "score_components": {
                str(k): float(self.score_components[k]) for k in SCORE_COMPONENT_KEYS
            },
            "data_quality_status": self.data_quality_status,
            "eligibility_status": self.eligibility_status,
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "tie_break_values": dict(sorted(self.tie_break_values.items())),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "RankedCandidateV1":
        components_raw = dict(payload.get("score_components") or {})
        components = {k: float(components_raw.get(k, 0.0)) for k in SCORE_COMPONENT_KEYS}
        return RankedCandidateV1(
            rank=int(payload["rank"]),
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_native_id=str(payload["venue_native_id"]),
            total_score=float(payload["total_score"]),
            score_components=components,
            data_quality_status=str(payload["data_quality_status"]),
            eligibility_status=str(payload["eligibility_status"]),
            exclusion_reason_codes=tuple(
                str(x) for x in (payload.get("exclusion_reason_codes") or ())
            ),
            tie_break_values={
                str(k): str(v) for k, v in dict(payload.get("tie_break_values") or {}).items()
            },
        )


@dataclass(frozen=True)
class ProductiveFuturesRankingSnapshotV1:
    """Deterministic, versioned ranking snapshot DTO (Top-20 candidate context)."""

    schema_version: str
    capability_id: str
    producer_version: str
    ranking_snapshot_id: str
    universe_snapshot_id: str
    universe_source_digest: str
    universe_payload_digest: str
    ranking_policy_id: str
    ranking_policy_version: str
    repository_sha: str
    config_digest: str
    event_time: str
    produced_at_wall_time: str
    candidate_count_total: int
    eligible_candidate_count: int
    excluded_candidate_count: int
    ranked_candidates: tuple[RankedCandidateV1, ...]
    excluded_candidates: tuple[RankedCandidateV1, ...]
    snapshot_state: str
    integrity_digest: str
    alpha_allowed: bool = False
    top20_candidate_context_limit: int = TOP20_CANDIDATE_CONTEXT_LIMIT
    selection_authority_created: bool = False
    multi_future_authority_created: bool = False
    dashboard_input_used: bool = False
    ranking_policy_provenance: str = RANKING_POLICY_PROVENANCE
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "producer_version": self.producer_version,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "universe_snapshot_id": self.universe_snapshot_id,
            "universe_source_digest": self.universe_source_digest,
            "universe_payload_digest": self.universe_payload_digest,
            "ranking_policy_id": self.ranking_policy_id,
            "ranking_policy_version": self.ranking_policy_version,
            "ranking_policy_provenance": self.ranking_policy_provenance,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "event_time": self.event_time,
            "produced_at_wall_time": self.produced_at_wall_time,
            "candidate_count_total": int(self.candidate_count_total),
            "eligible_candidate_count": int(self.eligible_candidate_count),
            "excluded_candidate_count": int(self.excluded_candidate_count),
            "ranked_candidates": [row.to_dict() for row in self.ranked_candidates],
            "excluded_candidates": [row.to_dict() for row in self.excluded_candidates],
            "snapshot_state": self.snapshot_state,
            "integrity_digest": self.integrity_digest,
            "alpha_allowed": bool(self.alpha_allowed),
            "top20_candidate_context_limit": int(self.top20_candidate_context_limit),
            "selection_authority_created": bool(self.selection_authority_created),
            "multi_future_authority_created": bool(self.multi_future_authority_created),
            "dashboard_input_used": bool(self.dashboard_input_used),
            "authority": dict(self.authority),
            "call_graph": list(self.call_graph),
            "failure_codes": list(self.failure_codes),
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        """Digest payload excludes wall-clock production time.

        Ranking identity is bound to universe input, policy, config, and repository
        SHA — not to the wall clock of a later identical recompute.
        """
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        payload.pop("produced_at_wall_time", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_integrity_digest(self) -> "ProductiveFuturesRankingSnapshotV1":
        digest = self.compute_integrity_digest()
        return ProductiveFuturesRankingSnapshotV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            ranking_snapshot_id=self.ranking_snapshot_id,
            universe_snapshot_id=self.universe_snapshot_id,
            universe_source_digest=self.universe_source_digest,
            universe_payload_digest=self.universe_payload_digest,
            ranking_policy_id=self.ranking_policy_id,
            ranking_policy_version=self.ranking_policy_version,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            event_time=self.event_time,
            produced_at_wall_time=self.produced_at_wall_time,
            candidate_count_total=self.candidate_count_total,
            eligible_candidate_count=self.eligible_candidate_count,
            excluded_candidate_count=self.excluded_candidate_count,
            ranked_candidates=self.ranked_candidates,
            excluded_candidates=self.excluded_candidates,
            snapshot_state=self.snapshot_state,
            integrity_digest=digest,
            alpha_allowed=self.alpha_allowed,
            top20_candidate_context_limit=self.top20_candidate_context_limit,
            selection_authority_created=self.selection_authority_created,
            multi_future_authority_created=self.multi_future_authority_created,
            dashboard_input_used=self.dashboard_input_used,
            ranking_policy_provenance=self.ranking_policy_provenance,
            authority=dict(self.authority),
            call_graph=self.call_graph,
            failure_codes=self.failure_codes,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "ProductiveFuturesRankingSnapshotV1":
        ranked = tuple(
            RankedCandidateV1.from_dict(row) for row in (payload.get("ranked_candidates") or [])
        )
        excluded = tuple(
            RankedCandidateV1.from_dict(row) for row in (payload.get("excluded_candidates") or [])
        )
        return ProductiveFuturesRankingSnapshotV1(
            schema_version=str(payload.get("schema_version") or ""),
            capability_id=str(payload.get("capability_id") or ""),
            producer_version=str(payload.get("producer_version") or ""),
            ranking_snapshot_id=str(payload.get("ranking_snapshot_id") or ""),
            universe_snapshot_id=str(payload.get("universe_snapshot_id") or ""),
            universe_source_digest=str(payload.get("universe_source_digest") or ""),
            universe_payload_digest=str(payload.get("universe_payload_digest") or ""),
            ranking_policy_id=str(payload.get("ranking_policy_id") or ""),
            ranking_policy_version=str(payload.get("ranking_policy_version") or ""),
            repository_sha=str(payload.get("repository_sha") or ""),
            config_digest=str(payload.get("config_digest") or ""),
            event_time=str(payload.get("event_time") or ""),
            produced_at_wall_time=str(payload.get("produced_at_wall_time") or ""),
            candidate_count_total=int(payload.get("candidate_count_total") or 0),
            eligible_candidate_count=int(payload.get("eligible_candidate_count") or 0),
            excluded_candidate_count=int(payload.get("excluded_candidate_count") or 0),
            ranked_candidates=ranked,
            excluded_candidates=excluded,
            snapshot_state=str(payload.get("snapshot_state") or ""),
            integrity_digest=str(payload.get("integrity_digest") or ""),
            alpha_allowed=bool(payload.get("alpha_allowed", False)),
            top20_candidate_context_limit=int(
                payload.get("top20_candidate_context_limit") or TOP20_CANDIDATE_CONTEXT_LIMIT
            ),
            selection_authority_created=bool(payload.get("selection_authority_created", False)),
            multi_future_authority_created=bool(
                payload.get("multi_future_authority_created", False)
            ),
            dashboard_input_used=bool(payload.get("dashboard_input_used", False)),
            ranking_policy_provenance=str(
                payload.get("ranking_policy_provenance") or RANKING_POLICY_PROVENANCE
            ),
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            failure_codes=tuple(str(x) for x in (payload.get("failure_codes") or ())),
        )


@dataclass(frozen=True)
class RankingProduceResultV1:
    snapshot: ProductiveFuturesRankingSnapshotV1
    ok: bool
    hard_stop: bool
    failure_codes: tuple[str, ...]


def authority_block() -> dict[str, Any]:
    return {
        "RANKING_AUTHORITY_OWNER_SINGLE": True,
        "AUTHORITY_OWNER": CAPABILITY_ID,
        "OWNER": "ops.productive_futures_ranking_producer_v1",
        "DASHBOARD_AUTHORITY": False,
        "RANKING_CANDIDATE_CONTEXT_AUTHORITY": True,
        "SELECTION_AUTHORITY_ADDED": False,
        "ALPHA_AUTHORITY_ADDED": False,
        "EXECUTION_AUTHORITY_ADDED": False,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": False,
        "TOP_N_ACTIVE_SET_AUTHORITY": False,
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": True,
        "ALPHA_ALLOWED": ALPHA_ALLOWED_DEFAULT,
        "VENUE": VENUE,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PRODUCER_VERSION": PRODUCER_VERSION,
        "RANKING_POLICY_ID": RANKING_POLICY_ID,
        "RANKING_POLICY_VERSION": RANKING_POLICY_VERSION,
        "TOP20_IS_CONTEXT_ONLY": True,
    }


def compute_config_digest_v1(
    *,
    repository_sha: str,
    max_universe_age_seconds: float,
    top20_limit: int = TOP20_CANDIDATE_CONTEXT_LIMIT,
    venue: str = VENUE,
) -> str:
    payload = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "ranking_policy_id": RANKING_POLICY_ID,
        "ranking_policy_version": RANKING_POLICY_VERSION,
        "score_component_keys": list(SCORE_COMPONENT_KEYS),
        "venue": venue,
        "max_universe_age_seconds": float(max_universe_age_seconds),
        "top20_candidate_context_limit": int(top20_limit),
        "repository_sha": repository_sha,
        "alpha_allowed": ALPHA_ALLOWED_DEFAULT,
        "selection_authority_added": False,
        "multi_future_runtime_authorized": False,
        "dashboard_authority": False,
        "max_positions_effective": 1,
    }
    return sha256_hex(canonical_json_dumps(payload))


def compute_ranking_snapshot_id_v1(
    *,
    universe_snapshot_id: str,
    universe_source_digest: str,
    config_digest: str,
    repository_sha: str,
) -> str:
    material = "|".join(
        [
            CAPABILITY_ID,
            RANKING_POLICY_ID,
            RANKING_POLICY_VERSION,
            PRODUCER_VERSION,
            universe_snapshot_id,
            universe_source_digest,
            config_digest,
            repository_sha,
        ]
    )
    return f"pfr_{sha256_hex(material)[:24]}"
