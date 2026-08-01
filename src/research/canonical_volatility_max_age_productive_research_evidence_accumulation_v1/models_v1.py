"""Typed models for productive max-age research evidence accumulation v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence


class ProductiveEvidenceAccumulationError(ValueError):
    """Fail-closed productive evidence accumulation error."""


class ResearchRegimeLabelV1(str, Enum):
    UP_DIRECTIONAL = "UP_DIRECTIONAL"
    DOWN_DIRECTIONAL = "DOWN_DIRECTIONAL"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    CHOP_OR_RANGE = "CHOP_OR_RANGE"
    STRESS_OR_GAP = "STRESS_OR_GAP"
    UNCLASSIFIED = "UNCLASSIFIED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ValidationStatusV1(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    QUARANTINED = "QUARANTINED"


class DuplicateStatusV1(str, Enum):
    UNIQUE = "UNIQUE"
    DUPLICATE_IDEMPOTENT = "DUPLICATE_IDEMPOTENT"
    DUPLICATE_CONFLICT = "DUPLICATE_CONFLICT"
    UNRESOLVED = "UNRESOLVED"


class SessionLifecycleStateV1(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sha256_hex_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProductiveResearchEvidenceRecordV1:
    """One productive, non-enforcing research evidence observation."""

    evidence_schema_version: str
    evidence_record_id: str
    session_id: str
    session_start_event_time: str
    session_end_event_time: Optional[str]
    observation_event_time: str
    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    repository_sha: str
    strategy_contract_digest: str
    volatility_contract_digest: str
    preregistration_digest: str
    market_event_time: str
    receive_time: Optional[str]
    as_of_event_time: str
    volatility_value: float
    volatility_unit: str
    volatility_horizon_seconds: float
    volatility_estimator: str
    volatility_observation_count: int
    volatility_source_digest: str
    fallback_used: bool
    age_seconds: float
    age_reference_clock: str
    age_formula_version: str
    source_estimate_id: str
    estimate_created_event_time: str
    estimate_reused: bool
    reuse_count: int
    restart_generation: int
    regime_label: str
    regime_source: str
    regime_confidence: str
    decision_context_digest: str
    counterfactual_eligible: bool
    data_trust_state: str
    clock_trust_state: str
    duplicate_status: str
    validation_status: str
    rejection_reasons: tuple[str, ...]
    record_digest: str
    # Join-facing identity (research execution compatibility).
    cycle_id: str
    reuse_status: str
    restart_status: str
    estimate_present: bool
    decision_outcome: Optional[str]
    selected_side: Optional[str]
    economic_metrics: Optional[Mapping[str, Any]]
    campaign_id: Optional[str] = None
    market_sample_id: Optional[str] = None
    productive_input_authority: Optional[str] = None
    source_is_authoritative_bridge_cycle: bool = False
    synthetic: bool = False
    fixture: bool = False
    test_data: bool = False
    # Numeric productive-accumulation enrichment (diagnostic / join-facing).
    estimate_age_seconds: Optional[float] = None
    volatility_regime: Optional[str] = None
    config_digest: Optional[str] = None
    code_sha: Optional[str] = None
    exit_path_preservation: bool = True
    productive_preregistration_digest: Optional[str] = None
    estimator_observation_count: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_formula_version": self.age_formula_version,
            "age_reference_clock": self.age_reference_clock,
            "age_seconds": self.age_seconds,
            "as_of_event_time": self.as_of_event_time,
            "campaign_id": self.campaign_id,
            "canonical_instrument_id": self.canonical_instrument_id,
            "clock_trust_state": self.clock_trust_state,
            "code_sha": self.code_sha,
            "config_digest": self.config_digest,
            "counterfactual_eligible": self.counterfactual_eligible,
            "cycle_id": self.cycle_id,
            "data_trust_state": self.data_trust_state,
            "decision_context_digest": self.decision_context_digest,
            "decision_outcome": self.decision_outcome,
            "duplicate_status": self.duplicate_status,
            "economic_metrics": (
                None if self.economic_metrics is None else dict(self.economic_metrics)
            ),
            "estimate_age_seconds": (
                self.age_seconds if self.estimate_age_seconds is None else self.estimate_age_seconds
            ),
            "estimate_created_event_time": self.estimate_created_event_time,
            "estimate_present": self.estimate_present,
            "estimate_reused": self.estimate_reused,
            "estimator_observation_count": (
                self.volatility_observation_count
                if self.estimator_observation_count is None
                else self.estimator_observation_count
            ),
            "evidence_record_id": self.evidence_record_id,
            "evidence_schema_version": self.evidence_schema_version,
            "exit_path_preservation": self.exit_path_preservation,
            "fallback_used": self.fallback_used,
            "fixture": self.fixture,
            "market_event_time": self.market_event_time,
            "market_sample_id": self.market_sample_id,
            "observation_event_time": self.observation_event_time,
            "preregistration_digest": self.preregistration_digest,
            "productive_input_authority": self.productive_input_authority,
            "productive_preregistration_digest": self.productive_preregistration_digest,
            "receive_time": self.receive_time,
            "record_digest": self.record_digest,
            "regime_confidence": self.regime_confidence,
            "regime_label": self.regime_label,
            "regime_source": self.regime_source,
            "rejection_reasons": list(self.rejection_reasons),
            "repository_sha": self.repository_sha,
            "restart_generation": self.restart_generation,
            "restart_status": self.restart_status,
            "reuse_count": self.reuse_count,
            "reuse_status": self.reuse_status,
            "selected_side": self.selected_side,
            "session_end_event_time": self.session_end_event_time,
            "session_id": self.session_id,
            "session_start_event_time": self.session_start_event_time,
            "source_estimate_id": self.source_estimate_id,
            "source_is_authoritative_bridge_cycle": self.source_is_authoritative_bridge_cycle,
            "strategy_contract_digest": self.strategy_contract_digest,
            "synthetic": self.synthetic,
            "test_data": self.test_data,
            "validation_status": self.validation_status,
            "venue": self.venue,
            "venue_instrument_id": self.venue_instrument_id,
            "volatility_contract_digest": self.volatility_contract_digest,
            "volatility_estimator": self.volatility_estimator,
            "volatility_horizon_seconds": self.volatility_horizon_seconds,
            "volatility_observation_count": self.volatility_observation_count,
            "volatility_regime": self.volatility_regime,
            "volatility_source_digest": self.volatility_source_digest,
            "volatility_unit": self.volatility_unit,
            "volatility_value": self.volatility_value,
        }

    def semantic_identity_v1(self) -> tuple[str, ...]:
        return (
            self.evidence_schema_version,
            self.session_id,
            self.cycle_id,
            self.canonical_instrument_id,
            self.venue,
            self.source_estimate_id,
            self.market_event_time,
            self.as_of_event_time,
            self.volatility_source_digest,
        )

    def business_join_identity_v1(self) -> tuple[str, str, str, str]:
        return (
            self.session_id,
            self.cycle_id,
            self.canonical_instrument_id,
            self.regime_label,
        )


@dataclass(frozen=True)
class ProductiveEvidenceSessionV1:
    session_contract_version: str
    session_id: str
    lifecycle_state: str
    session_start_event_time: str
    session_end_event_time: Optional[str]
    repository_sha: str
    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    restart_generation: int
    resume_token: str
    observation_count: int
    session_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "lifecycle_state": self.lifecycle_state,
            "observation_count": self.observation_count,
            "repository_sha": self.repository_sha,
            "restart_generation": self.restart_generation,
            "resume_token": self.resume_token,
            "session_contract_version": self.session_contract_version,
            "session_digest": self.session_digest,
            "session_end_event_time": self.session_end_event_time,
            "session_id": self.session_id,
            "session_start_event_time": self.session_start_event_time,
            "venue": self.venue,
            "venue_instrument_id": self.venue_instrument_id,
        }


@dataclass(frozen=True)
class ProductiveLedgerEnvelopeV1:
    ledger_schema_version: str
    ledger_record_sequence: int
    prev_ledger_chain_digest: str
    ledger_chain_digest: str
    record_kind: str
    productive_evidence: Mapping[str, Any]
    research_join: Optional[Mapping[str, Any]]
    quarantine_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_chain_digest": self.ledger_chain_digest,
            "ledger_record_sequence": self.ledger_record_sequence,
            "ledger_schema_version": self.ledger_schema_version,
            "prev_ledger_chain_digest": self.prev_ledger_chain_digest,
            "productive_evidence": dict(self.productive_evidence),
            "quarantine_reasons": list(self.quarantine_reasons),
            "record_kind": self.record_kind,
            "research_join": None if self.research_join is None else dict(self.research_join),
        }


@dataclass(frozen=True)
class CoverageReadinessReportV1:
    coverage_schema_version: str
    valid_evidence_count: int
    invalid_evidence_count: int
    quarantined_evidence_count: int
    duplicate_evidence_count: int
    session_count: int
    completed_session_count: int
    regime_count: int
    observations_per_session: Mapping[str, int]
    observations_per_regime: Mapping[str, int]
    event_time_span_seconds: Optional[float]
    first_event_time: Optional[str]
    last_event_time: Optional[str]
    restart_count: int
    reused_estimate_count: int
    fresh_estimate_count: int
    fallback_record_count: int
    trusted_record_count: int
    untrusted_record_count: int
    multi_session_coverage: bool
    multi_regime_coverage: bool
    coverage_gaps: tuple[str, ...]
    ready_for_research_execution: bool
    readiness_authority: str
    threshold_status: str
    enforcement_applied: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed_session_count": self.completed_session_count,
            "coverage_gaps": list(self.coverage_gaps),
            "coverage_schema_version": self.coverage_schema_version,
            "duplicate_evidence_count": self.duplicate_evidence_count,
            "enforcement_applied": self.enforcement_applied,
            "event_time_span_seconds": self.event_time_span_seconds,
            "fallback_record_count": self.fallback_record_count,
            "first_event_time": self.first_event_time,
            "fresh_estimate_count": self.fresh_estimate_count,
            "invalid_evidence_count": self.invalid_evidence_count,
            "last_event_time": self.last_event_time,
            "multi_regime_coverage": self.multi_regime_coverage,
            "multi_session_coverage": self.multi_session_coverage,
            "observations_per_regime": dict(self.observations_per_regime),
            "observations_per_session": dict(self.observations_per_session),
            "quarantined_evidence_count": self.quarantined_evidence_count,
            "readiness_authority": self.readiness_authority,
            "ready_for_research_execution": self.ready_for_research_execution,
            "regime_count": self.regime_count,
            "restart_count": self.restart_count,
            "reused_estimate_count": self.reused_estimate_count,
            "session_count": self.session_count,
            "threshold_status": self.threshold_status,
            "trusted_record_count": self.trusted_record_count,
            "untrusted_record_count": self.untrusted_record_count,
            "valid_evidence_count": self.valid_evidence_count,
        }


def require_nonempty(value: Any, *, field_name: str) -> str:
    if value is None:
        raise ProductiveEvidenceAccumulationError(f"{field_name}_required")
    text = str(value).strip()
    if not text:
        raise ProductiveEvidenceAccumulationError(f"{field_name}_must_be_nonempty")
    return text


def optional_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_float(value: Any, *, field_name: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise ProductiveEvidenceAccumulationError(f"{field_name}_not_numeric") from exc
    if out != out or out in (float("inf"), float("-inf")):  # noqa: PLR0124
        raise ProductiveEvidenceAccumulationError(f"{field_name}_not_finite")
    return out


def as_int(value: Any, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ProductiveEvidenceAccumulationError(f"{field_name}_not_integer") from exc


def as_bool(value: Any, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ProductiveEvidenceAccumulationError(f"{field_name}_not_bool")


def digest_excluding_keys(payload: Mapping[str, Any], *, exclude: Sequence[str]) -> str:
    body = {k: v for k, v in payload.items() if k not in set(exclude)}
    return sha256_hex(body)
