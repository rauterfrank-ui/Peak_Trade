"""Typed models for additional evidence session preregistration contract v2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class AdditionalEvidenceSessionPreregistrationContractV2Error(ValueError):
    """Fail-closed contract / candidate / readiness validation error."""


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sha256_hex_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_hex_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_excluding_keys(
    payload: Mapping[str, Any],
    *,
    exclude: Sequence[str],
) -> str:
    filtered = {k: payload[k] for k in sorted(payload) if k not in set(exclude)}
    return sha256_hex(filtered)


@dataclass(frozen=True)
class AdditionalEvidenceSessionCandidateV2:
    """In-memory v2 candidate preregistration (immutable SHA semantics)."""

    campaign_id: str
    session_id: str
    code_baseline_sha: str
    artifact_creation_sha: str
    critical_surface_manifest_digest: str
    repository_binding_mode: str
    design_digest: str
    runbook_digest: str
    preregistration_digest: str
    venue: str
    instrument: str
    network_scope: str
    session_scope: str
    duration_seconds: int
    maximum_cycles_per_session: int
    maximum_requests_per_session: int
    minimum_interval_seconds: float
    maximum_requests_per_cycle: int
    target_age_buckets_seconds: tuple[int, ...]
    first_produce_required: bool
    natural_age_progression_required: bool
    age_7200_observation_required: bool
    recompute_after_age_floor_required: bool
    post_recompute_fresh_observation_required: bool
    multiple_market_regimes_required: bool
    authorization_required: bool
    single_use_authorization_required: bool
    post_first_produce_event_span_seconds: int
    schema_name: str
    schema_version: str
    authorization_binding: Mapping[str, Any]
    forbidden_artificial_controls: Mapping[str, bool]
    session_preregistration_creation_authorized: bool
    execution_authorized: bool
    network_authorized: bool
    evidence_write_authorized: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_7200_observation_required": self.age_7200_observation_required,
            "artifact_creation_sha": self.artifact_creation_sha,
            "authorization_binding": dict(self.authorization_binding),
            "authorization_required": self.authorization_required,
            "campaign_id": self.campaign_id,
            "code_baseline_sha": self.code_baseline_sha,
            "critical_surface_manifest_digest": self.critical_surface_manifest_digest,
            "design_digest": self.design_digest,
            "duration_seconds": self.duration_seconds,
            "evidence_write_authorized": self.evidence_write_authorized,
            "execution_authorized": self.execution_authorized,
            "first_produce_required": self.first_produce_required,
            "forbidden_artificial_controls": dict(self.forbidden_artificial_controls),
            "instrument": self.instrument,
            "maximum_cycles_per_session": self.maximum_cycles_per_session,
            "maximum_requests_per_cycle": self.maximum_requests_per_cycle,
            "maximum_requests_per_session": self.maximum_requests_per_session,
            "minimum_interval_seconds": self.minimum_interval_seconds,
            "multiple_market_regimes_required": self.multiple_market_regimes_required,
            "natural_age_progression_required": self.natural_age_progression_required,
            "network_authorized": self.network_authorized,
            "network_scope": self.network_scope,
            "post_first_produce_event_span_seconds": self.post_first_produce_event_span_seconds,
            "post_recompute_fresh_observation_required": (
                self.post_recompute_fresh_observation_required
            ),
            "preregistration_digest": self.preregistration_digest,
            "recompute_after_age_floor_required": self.recompute_after_age_floor_required,
            "repository_binding_mode": self.repository_binding_mode,
            "runbook_digest": self.runbook_digest,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "session_preregistration_creation_authorized": (
                self.session_preregistration_creation_authorized
            ),
            "session_scope": self.session_scope,
            "single_use_authorization_required": self.single_use_authorization_required,
            "target_age_buckets_seconds": list(self.target_age_buckets_seconds),
            "venue": self.venue,
        }


@dataclass(frozen=True)
class AdditionalEvidenceSessionPreregistrationContractV2:
    """Versioned v2 contract with immutable ancestor SHA binding."""

    schema_name: str
    schema_version: str
    capability_id: str
    capability_version: str
    contract_digest: str
    code_baseline_sha: str
    artifact_creation_sha: str
    critical_surface_manifest_digest: str
    repository_binding_mode: str
    tip_of_main_equality_required: bool
    self_commit_sha_embedding_required: bool
    design_digest: str
    runbook_digest: str
    target_age_buckets_seconds: tuple[int, ...]
    minimum_additional_productive_sessions: int
    minimum_session_duration_seconds: int
    minimum_post_first_produce_event_span_seconds: int
    minimum_maximum_cycles_per_session: int
    recommended_maximum_cycles_per_session: int
    minimum_maximum_requests_per_session: int
    recommended_maximum_requests_per_session: int
    minimum_interval_seconds: float
    maximum_requests_per_cycle: int
    coverage_requirements: Mapping[str, Any]
    exhausted_campaign_id: str
    exhausted_session_ids: tuple[str, ...]
    exhausted_campaign_maximum_session_count: int
    forbidden_artificial_controls: Mapping[str, bool]
    operator_workflow: tuple[str, ...]
    authorization_binding_schema: Mapping[str, Any]
    required_candidate_fields: tuple[str, ...]
    session_preregistration_creation_authorized: bool
    authorization_issuance_authorized: bool
    authorization_consumption_authorized: bool
    network_access_authorized: bool
    productive_session_execution_authorized: bool
    numeric_max_age_selected: bool
    numeric_max_age_enforcing: bool
    hard_stop: bool
    ready_for_additional_session_preregistration: bool
    ready_for_authorization_issuance: bool
    ready_for_productive_session_execution: bool
    candidate_schema_name: str
    candidate_schema_version: str
    expected_venue: str
    expected_instrument: str
    expected_network_scope: str
    expected_session_scope: str
    candidate_schema_closed_world: bool
    nested_objects_present: bool
    unknown_fields_rejected: bool
    unknown_authority_fields_rejected: bool
    binding_value_normalization_forbidden: bool
    allowed_candidate_top_level_fields: tuple[str, ...]
    allowed_authorization_binding_fields: tuple[str, ...]
    allowed_forbidden_artificial_controls_fields: tuple[str, ...]
    authority_negative_contract: Mapping[str, Any]
    age_7200_observation_required: bool
    recompute_after_age_floor_required: bool
    post_recompute_fresh_required: bool
    authorization_per_session_required: bool
    single_use_authorization_required: bool
    v1_new_authorization_readiness_allowed: bool
    repository_sha_field_status: str
    critical_surface_manifest_path: str
    superseded_pr_5629: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_7200_observation_required": self.age_7200_observation_required,
            "allowed_authorization_binding_fields": list(self.allowed_authorization_binding_fields),
            "allowed_candidate_top_level_fields": list(self.allowed_candidate_top_level_fields),
            "allowed_forbidden_artificial_controls_fields": list(
                self.allowed_forbidden_artificial_controls_fields
            ),
            "artifact_creation_sha": self.artifact_creation_sha,
            "authority_negative_contract": dict(self.authority_negative_contract),
            "authorization_binding_schema": dict(self.authorization_binding_schema),
            "authorization_consumption_authorized": self.authorization_consumption_authorized,
            "authorization_issuance_authorized": self.authorization_issuance_authorized,
            "authorization_per_session_required": self.authorization_per_session_required,
            "binding_value_normalization_forbidden": self.binding_value_normalization_forbidden,
            "candidate_schema_closed_world": self.candidate_schema_closed_world,
            "candidate_schema_name": self.candidate_schema_name,
            "candidate_schema_version": self.candidate_schema_version,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "code_baseline_sha": self.code_baseline_sha,
            "contract_digest": self.contract_digest,
            "coverage_requirements": dict(self.coverage_requirements),
            "critical_surface_manifest_digest": self.critical_surface_manifest_digest,
            "critical_surface_manifest_path": self.critical_surface_manifest_path,
            "design_digest": self.design_digest,
            "exhausted_campaign_id": self.exhausted_campaign_id,
            "exhausted_campaign_maximum_session_count": (
                self.exhausted_campaign_maximum_session_count
            ),
            "exhausted_session_ids": list(self.exhausted_session_ids),
            "expected_instrument": self.expected_instrument,
            "expected_network_scope": self.expected_network_scope,
            "expected_session_scope": self.expected_session_scope,
            "expected_venue": self.expected_venue,
            "forbidden_artificial_controls": dict(self.forbidden_artificial_controls),
            "hard_stop": self.hard_stop,
            "maximum_requests_per_cycle": self.maximum_requests_per_cycle,
            "minimum_additional_productive_sessions": self.minimum_additional_productive_sessions,
            "minimum_interval_seconds": self.minimum_interval_seconds,
            "minimum_maximum_cycles_per_session": self.minimum_maximum_cycles_per_session,
            "minimum_maximum_requests_per_session": self.minimum_maximum_requests_per_session,
            "minimum_post_first_produce_event_span_seconds": (
                self.minimum_post_first_produce_event_span_seconds
            ),
            "minimum_session_duration_seconds": self.minimum_session_duration_seconds,
            "nested_objects_present": self.nested_objects_present,
            "network_access_authorized": self.network_access_authorized,
            "numeric_max_age_enforcing": self.numeric_max_age_enforcing,
            "numeric_max_age_selected": self.numeric_max_age_selected,
            "operator_workflow": list(self.operator_workflow),
            "post_recompute_fresh_required": self.post_recompute_fresh_required,
            "productive_session_execution_authorized": (
                self.productive_session_execution_authorized
            ),
            "ready_for_additional_session_preregistration": (
                self.ready_for_additional_session_preregistration
            ),
            "ready_for_authorization_issuance": self.ready_for_authorization_issuance,
            "ready_for_productive_session_execution": self.ready_for_productive_session_execution,
            "recompute_after_age_floor_required": self.recompute_after_age_floor_required,
            "recommended_maximum_cycles_per_session": self.recommended_maximum_cycles_per_session,
            "recommended_maximum_requests_per_session": (
                self.recommended_maximum_requests_per_session
            ),
            "repository_binding_mode": self.repository_binding_mode,
            "repository_sha_field_status": self.repository_sha_field_status,
            "required_candidate_fields": list(self.required_candidate_fields),
            "runbook_digest": self.runbook_digest,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "self_commit_sha_embedding_required": self.self_commit_sha_embedding_required,
            "session_preregistration_creation_authorized": (
                self.session_preregistration_creation_authorized
            ),
            "single_use_authorization_required": self.single_use_authorization_required,
            "superseded_pr_5629": self.superseded_pr_5629,
            "target_age_buckets_seconds": list(self.target_age_buckets_seconds),
            "tip_of_main_equality_required": self.tip_of_main_equality_required,
            "unknown_authority_fields_rejected": self.unknown_authority_fields_rejected,
            "unknown_fields_rejected": self.unknown_fields_rejected,
            "v1_new_authorization_readiness_allowed": self.v1_new_authorization_readiness_allowed,
        }
