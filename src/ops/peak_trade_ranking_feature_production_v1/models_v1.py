"""Production snapshot DTOs for B05 Cap-2.1 ranking feature production.

Raw B04 feature values only. No rank, score, normalized cross-section, or selection.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    canonical_digest_v1,
)
from src.ops.peak_trade_ranking_feature_contract_v1 import (
    Input2ProvenanceV1,
    RankingPolicyIdentityV1,
    RawRankingFeatureValueV1,
)
from src.ops.peak_trade_ranking_feature_production_v1.constants_v1 import (
    CAPABILITY_ID,
    PRODUCTION_VERSION,
    SCHEMA_VERSION,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class InstrumentMarkWindowProvenanceV1:
    observation_window_id: str
    as_of_event_time: str
    source_class: str
    source_endpoint: str
    mark_count: int
    event_timestamps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "as_of_event_time": self.as_of_event_time,
            "event_timestamps": list(self.event_timestamps),
            "mark_count": int(self.mark_count),
            "observation_window_id": self.observation_window_id,
            "source_class": self.source_class,
            "source_endpoint": self.source_endpoint,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> InstrumentMarkWindowProvenanceV1:
        return InstrumentMarkWindowProvenanceV1(
            observation_window_id=str(payload["observation_window_id"]),
            as_of_event_time=str(payload["as_of_event_time"]),
            source_class=str(payload["source_class"]),
            source_endpoint=str(payload["source_endpoint"]),
            mark_count=int(payload["mark_count"]),
            event_timestamps=tuple(str(x) for x in (payload.get("event_timestamps") or ())),
        )


@dataclass(frozen=True)
class InstrumentRawFeatureProductionV1:
    canonical_instrument_id: str
    venue_native_id: str
    raw_features: tuple[RawRankingFeatureValueV1, ...]
    feature_production_ready: bool
    mark_window_provenance: Optional[InstrumentMarkWindowProvenanceV1]
    exclusion_reason_codes: tuple[str, ...]
    economic_md_raw_input_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "economic_md_raw_input_digest": self.economic_md_raw_input_digest,
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "feature_production_ready": bool(self.feature_production_ready),
            "mark_window_provenance": (
                None
                if self.mark_window_provenance is None
                else self.mark_window_provenance.to_dict()
            ),
            "raw_features": [row.to_dict() for row in self.raw_features],
            "venue_native_id": self.venue_native_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> InstrumentRawFeatureProductionV1:
        provenance_raw = payload.get("mark_window_provenance")
        return InstrumentRawFeatureProductionV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_native_id=str(payload["venue_native_id"]),
            raw_features=tuple(
                RawRankingFeatureValueV1.from_dict(row)
                for row in (payload.get("raw_features") or ())
            ),
            feature_production_ready=bool(payload.get("feature_production_ready", False)),
            mark_window_provenance=(
                None
                if provenance_raw in (None, "")
                else InstrumentMarkWindowProvenanceV1.from_dict(dict(provenance_raw))
            ),
            exclusion_reason_codes=tuple(
                str(x) for x in (payload.get("exclusion_reason_codes") or ())
            ),
            economic_md_raw_input_digest=str(payload.get("economic_md_raw_input_digest") or ""),
        )


@dataclass(frozen=True)
class RankingFeatureProductionSnapshotV1:
    schema_version: str
    production_version: str
    capability_id: str
    production_snapshot_id: str
    policy_identity: RankingPolicyIdentityV1
    input2_provenance: Input2ProvenanceV1
    instruments: tuple[InstrumentRawFeatureProductionV1, ...]
    instrument_count_requested: int
    instrument_count_feature_ready: int
    production_digest: str
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": dict(sorted(self.authority.items())),
            "call_graph": list(self.call_graph),
            "capability_id": self.capability_id,
            "input2_provenance": self.input2_provenance.to_dict(),
            "instrument_count_feature_ready": int(self.instrument_count_feature_ready),
            "instrument_count_requested": int(self.instrument_count_requested),
            "instruments": [row.to_dict() for row in self.instruments],
            "policy_identity": self.policy_identity.to_dict(),
            "production_digest": self.production_digest,
            "production_snapshot_id": self.production_snapshot_id,
            "production_version": self.production_version,
            "schema_version": self.schema_version,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("production_digest", None)
        return payload

    def compute_production_digest(self) -> str:
        return canonical_digest_v1(self.deterministic_payload_for_digest())

    def with_production_digest(self) -> RankingFeatureProductionSnapshotV1:
        return RankingFeatureProductionSnapshotV1(
            schema_version=self.schema_version,
            production_version=self.production_version,
            capability_id=self.capability_id,
            production_snapshot_id=self.production_snapshot_id,
            policy_identity=self.policy_identity,
            input2_provenance=self.input2_provenance,
            instruments=self.instruments,
            instrument_count_requested=self.instrument_count_requested,
            instrument_count_feature_ready=self.instrument_count_feature_ready,
            production_digest=self.compute_production_digest(),
            authority=dict(self.authority),
            call_graph=self.call_graph,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> RankingFeatureProductionSnapshotV1:
        return RankingFeatureProductionSnapshotV1(
            schema_version=str(payload.get("schema_version") or SCHEMA_VERSION),
            production_version=str(payload.get("production_version") or PRODUCTION_VERSION),
            capability_id=str(payload.get("capability_id") or CAPABILITY_ID),
            production_snapshot_id=str(payload.get("production_snapshot_id") or ""),
            policy_identity=RankingPolicyIdentityV1.from_dict(payload["policy_identity"]),
            input2_provenance=Input2ProvenanceV1.from_dict(payload["input2_provenance"]),
            instruments=tuple(
                InstrumentRawFeatureProductionV1.from_dict(row)
                for row in (payload.get("instruments") or ())
            ),
            instrument_count_requested=int(payload.get("instrument_count_requested") or 0),
            instrument_count_feature_ready=int(payload.get("instrument_count_feature_ready") or 0),
            production_digest=str(payload.get("production_digest") or ""),
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
        )


def compute_production_snapshot_id_v1(
    *,
    economic_input_snapshot_id: str,
    economic_input_snapshot_digest: str,
    instrument_feature_digests: Sequence[str],
) -> str:
    material = {
        "capability_id": CAPABILITY_ID,
        "economic_input_snapshot_digest": economic_input_snapshot_digest,
        "economic_input_snapshot_id": economic_input_snapshot_id,
        "instrument_feature_digests": list(instrument_feature_digests),
        "production_version": PRODUCTION_VERSION,
        "schema_version": SCHEMA_VERSION,
    }
    digest = canonical_digest_v1(material)
    return f"rfp_{digest[:24]}"
