"""Typed models for M9-S1 market session observation accumulation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class M9S1EvidenceAccumulationError(ValueError):
    """Fail-closed M9-S1 evidence accumulation error."""


class ObservationSourceClassV1(str, Enum):
    LIVE_OBSERVED = "LIVE_OBSERVED"
    TESTNET_OBSERVED = "TESTNET_OBSERVED"
    SHADOW_OBSERVED = "SHADOW_OBSERVED"
    REPLAY = "REPLAY"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def digest_excluding_keys(payload: Mapping[str, Any], *, exclude: frozenset[str]) -> str:
    filtered = {k: v for k, v in payload.items() if k not in exclude}
    return sha256_hex(filtered)


@dataclass(frozen=True)
class M9S1MarketSessionObservationV1:
    """Passive observation record; never trading authority."""

    observation_schema_version: str
    workpackage_id: str
    observation_id: str
    session_id: str
    cycle_id: str
    instrument_id: str
    evidence_source_class: str
    reference_market_event_time: Optional[str]
    estimate_as_of_event_time: Optional[str]
    computed_age_seconds: Optional[float]
    volatility_source_digest: Optional[str]
    volatility_value: Optional[float]
    repository_sha: str
    runtime_build_identity: Optional[str]
    market_sample_id: Optional[str]
    join_digest: Optional[str]
    productive_evidence_record_id: Optional[str]
    observation_outcome: str
    missing_invalid_reason: Optional[str]
    ordering_key: Optional[str]
    dedup_identity: str
    synthetic: bool
    fixture: bool
    replay: bool
    record_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "computed_age_seconds": self.computed_age_seconds,
            "cycle_id": self.cycle_id,
            "dedup_identity": self.dedup_identity,
            "estimate_as_of_event_time": self.estimate_as_of_event_time,
            "evidence_source_class": self.evidence_source_class,
            "fixture": self.fixture,
            "instrument_id": self.instrument_id,
            "join_digest": self.join_digest,
            "market_sample_id": self.market_sample_id,
            "missing_invalid_reason": self.missing_invalid_reason,
            "observation_id": self.observation_id,
            "observation_outcome": self.observation_outcome,
            "observation_schema_version": self.observation_schema_version,
            "ordering_key": self.ordering_key,
            "productive_evidence_record_id": self.productive_evidence_record_id,
            "record_digest": self.record_digest,
            "reference_market_event_time": self.reference_market_event_time,
            "replay": self.replay,
            "repository_sha": self.repository_sha,
            "runtime_build_identity": self.runtime_build_identity,
            "session_id": self.session_id,
            "synthetic": self.synthetic,
            "volatility_source_digest": self.volatility_source_digest,
            "volatility_value": self.volatility_value,
            "workpackage_id": self.workpackage_id,
        }
