"""Build and verify the versioned additional-evidence session preregistration contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.authorization_binding_v1 import (
    build_authorization_binding_schema_v1,
    build_candidate_authorization_binding_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ALLOWED_AUTHORIZATION_BINDING_FIELDS,
    ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS,
    ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS,
    ARTIFACT_RELATIVE_PATH,
    AUTHORITY_NEGATIVE_CONTRACT,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    BINDING_VALUE_NORMALIZATION_FORBIDDEN,
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    CANDIDATE_SCHEMA_CLOSED_WORLD,
    CANDIDATE_SCHEMA_NAME,
    CANDIDATE_SCHEMA_VERSION,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    COVERAGE_REQUIREMENTS,
    EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    EXISTING_EXHAUSTED_SESSION_IDS,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_ARTIFICIAL_FLAGS,
    HARDENING_CAPABILITY_ID,
    HARD_STOP,
    MAXIMUM_REQUESTS_PER_CYCLE,
    MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS,
    MINIMUM_INTERVAL_SECONDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS,
    MINIMUM_SESSION_DURATION_SECONDS,
    NESTED_OBJECTS_PRESENT,
    NETWORK_ACCESS_AUTHORIZED,
    NUMERIC_MAX_AGE_ENFORCING,
    NUMERIC_MAX_AGE_SELECTED,
    OPERATOR_WORKFLOW,
    PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
    PUBLIC_MD_NETWORK_SCOPE,
    PUBLIC_MD_VENUE,
    READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION,
    READY_FOR_AUTHORIZATION_ISSUANCE,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION,
    RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION,
    REQUIRED_CANDIDATE_FIELDS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SESSION_PREREGISTRATION_CREATION_AUTHORIZED,
    SESSION_SCOPE,
    TARGET_AGE_BUCKETS_SECONDS,
    UNKNOWN_AUTHORITY_FIELDS_REJECTED,
    UNKNOWN_FIELDS_REJECTED,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.models_v1 import (
    AdditionalEvidenceSessionCandidateV1,
    AdditionalEvidenceSessionPreregistrationContractError,
    AdditionalEvidenceSessionPreregistrationContractV1,
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.uniqueness_v1 import (
    deterministic_additional_campaign_id_v1,
    deterministic_additional_session_id_v1,
)


def _forbidden_artificial_controls() -> dict[str, bool]:
    return {name: False for name in FORBIDDEN_ARTIFICIAL_FLAGS}


def _contract_payload_without_digest() -> dict[str, Any]:
    return {
        "age_7200_observation_required": True,
        "allowed_authorization_binding_fields": list(ALLOWED_AUTHORIZATION_BINDING_FIELDS),
        "allowed_candidate_top_level_fields": list(ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS),
        "allowed_forbidden_artificial_controls_fields": list(
            ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS
        ),
        "authority_negative_contract": dict(AUTHORITY_NEGATIVE_CONTRACT),
        "authorization_binding_schema": build_authorization_binding_schema_v1(),
        "authorization_consumption_authorized": AUTHORIZATION_CONSUMPTION_AUTHORIZED,
        "authorization_issuance_authorized": AUTHORIZATION_ISSUANCE_AUTHORIZED,
        "authorization_per_session_required": True,
        "binding_value_normalization_forbidden": BINDING_VALUE_NORMALIZATION_FORBIDDEN,
        "candidate_schema_closed_world": CANDIDATE_SCHEMA_CLOSED_WORLD,
        "candidate_schema_name": CANDIDATE_SCHEMA_NAME,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "coverage_requirements": dict(COVERAGE_REQUIREMENTS),
        "design_digest": BOUND_DESIGN_DIGEST,
        "exhausted_campaign_id": EXISTING_EXHAUSTED_CAMPAIGN_ID,
        "exhausted_campaign_maximum_session_count": EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
        "exhausted_session_ids": list(EXISTING_EXHAUSTED_SESSION_IDS),
        "expected_instrument": EXPECTED_INSTRUMENT,
        "expected_network_scope": EXPECTED_NETWORK_SCOPE,
        "expected_session_scope": EXPECTED_SESSION_SCOPE,
        "expected_venue": EXPECTED_VENUE,
        "forbidden_artificial_controls": _forbidden_artificial_controls(),
        "hardening_capability_id": HARDENING_CAPABILITY_ID,
        "hard_stop": HARD_STOP,
        "maximum_requests_per_cycle": MAXIMUM_REQUESTS_PER_CYCLE,
        "minimum_additional_productive_sessions": MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS,
        "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
        "minimum_maximum_cycles_per_session": MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
        "minimum_maximum_requests_per_session": MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
        "minimum_post_first_produce_event_span_seconds": (
            MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS
        ),
        "minimum_session_duration_seconds": MINIMUM_SESSION_DURATION_SECONDS,
        "nested_objects_present": NESTED_OBJECTS_PRESENT,
        "network_access_authorized": NETWORK_ACCESS_AUTHORIZED,
        "numeric_max_age_enforcing": NUMERIC_MAX_AGE_ENFORCING,
        "numeric_max_age_selected": NUMERIC_MAX_AGE_SELECTED,
        "operator_workflow": list(OPERATOR_WORKFLOW),
        "post_recompute_fresh_required": True,
        "productive_session_execution_authorized": PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
        "ready_for_additional_session_preregistration": (
            READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION
        ),
        "ready_for_authorization_issuance": READY_FOR_AUTHORIZATION_ISSUANCE,
        "ready_for_productive_session_execution": READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
        "recompute_after_age_floor_required": True,
        "recommended_maximum_cycles_per_session": RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION,
        "recommended_maximum_requests_per_session": RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION,
        "repository_sha": BOUND_REPOSITORY_SHA,
        "required_candidate_fields": list(REQUIRED_CANDIDATE_FIELDS),
        "runbook_digest": BOUND_RUNBOOK_DIGEST,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "session_preregistration_creation_authorized": (
            SESSION_PREREGISTRATION_CREATION_AUTHORIZED
        ),
        "single_use_authorization_required": True,
        "target_age_buckets_seconds": list(TARGET_AGE_BUCKETS_SECONDS),
        "unknown_authority_fields_rejected": UNKNOWN_AUTHORITY_FIELDS_REJECTED,
        "unknown_fields_rejected": UNKNOWN_FIELDS_REJECTED,
    }


def build_additional_evidence_session_preregistration_contract_v1() -> (
    AdditionalEvidenceSessionPreregistrationContractV1
):
    payload = _contract_payload_without_digest()
    digest = digest_excluding_keys(payload, exclude=("contract_digest",))
    return AdditionalEvidenceSessionPreregistrationContractV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        contract_digest=digest,
        repository_sha=BOUND_REPOSITORY_SHA,
        design_digest=BOUND_DESIGN_DIGEST,
        runbook_digest=BOUND_RUNBOOK_DIGEST,
        target_age_buckets_seconds=TARGET_AGE_BUCKETS_SECONDS,
        minimum_additional_productive_sessions=MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS,
        minimum_session_duration_seconds=MINIMUM_SESSION_DURATION_SECONDS,
        minimum_post_first_produce_event_span_seconds=(
            MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS
        ),
        minimum_maximum_cycles_per_session=MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
        recommended_maximum_cycles_per_session=RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION,
        minimum_maximum_requests_per_session=MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
        recommended_maximum_requests_per_session=RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION,
        minimum_interval_seconds=MINIMUM_INTERVAL_SECONDS,
        maximum_requests_per_cycle=MAXIMUM_REQUESTS_PER_CYCLE,
        coverage_requirements=dict(COVERAGE_REQUIREMENTS),
        exhausted_campaign_id=EXISTING_EXHAUSTED_CAMPAIGN_ID,
        exhausted_session_ids=EXISTING_EXHAUSTED_SESSION_IDS,
        exhausted_campaign_maximum_session_count=EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
        forbidden_artificial_controls=_forbidden_artificial_controls(),
        operator_workflow=OPERATOR_WORKFLOW,
        authorization_binding_schema=build_authorization_binding_schema_v1(),
        required_candidate_fields=REQUIRED_CANDIDATE_FIELDS,
        session_preregistration_creation_authorized=SESSION_PREREGISTRATION_CREATION_AUTHORIZED,
        authorization_issuance_authorized=AUTHORIZATION_ISSUANCE_AUTHORIZED,
        authorization_consumption_authorized=AUTHORIZATION_CONSUMPTION_AUTHORIZED,
        network_access_authorized=NETWORK_ACCESS_AUTHORIZED,
        productive_session_execution_authorized=PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
        numeric_max_age_selected=NUMERIC_MAX_AGE_SELECTED,
        numeric_max_age_enforcing=NUMERIC_MAX_AGE_ENFORCING,
        hard_stop=HARD_STOP,
        ready_for_additional_session_preregistration=(READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION),
        ready_for_authorization_issuance=READY_FOR_AUTHORIZATION_ISSUANCE,
        ready_for_productive_session_execution=READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
        hardening_capability_id=HARDENING_CAPABILITY_ID,
        candidate_schema_name=CANDIDATE_SCHEMA_NAME,
        candidate_schema_version=CANDIDATE_SCHEMA_VERSION,
        expected_venue=EXPECTED_VENUE,
        expected_instrument=EXPECTED_INSTRUMENT,
        expected_network_scope=EXPECTED_NETWORK_SCOPE,
        expected_session_scope=EXPECTED_SESSION_SCOPE,
        candidate_schema_closed_world=CANDIDATE_SCHEMA_CLOSED_WORLD,
        nested_objects_present=NESTED_OBJECTS_PRESENT,
        unknown_fields_rejected=UNKNOWN_FIELDS_REJECTED,
        unknown_authority_fields_rejected=UNKNOWN_AUTHORITY_FIELDS_REJECTED,
        binding_value_normalization_forbidden=BINDING_VALUE_NORMALIZATION_FORBIDDEN,
        allowed_candidate_top_level_fields=ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS,
        allowed_authorization_binding_fields=ALLOWED_AUTHORIZATION_BINDING_FIELDS,
        allowed_forbidden_artificial_controls_fields=(ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS),
        authority_negative_contract=dict(AUTHORITY_NEGATIVE_CONTRACT),
        age_7200_observation_required=True,
        recompute_after_age_floor_required=True,
        post_recompute_fresh_required=True,
        authorization_per_session_required=True,
        single_use_authorization_required=True,
    )


def render_additional_evidence_session_preregistration_contract_v1() -> dict[str, Any]:
    return build_additional_evidence_session_preregistration_contract_v1().to_dict()


def verify_additional_evidence_session_preregistration_contract_artifact_v1(
    *,
    artifact_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = artifact_path or (root / ARTIFACT_RELATIVE_PATH)
    expected = build_additional_evidence_session_preregistration_contract_v1().to_dict()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("contract_digest") != expected["contract_digest"]:
        raise AdditionalEvidenceSessionPreregistrationContractError("contract_digest_mismatch")
    for key, value in expected.items():
        if key == "contract_digest":
            continue
        if payload.get(key) != value:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"contract_field_drift:{key}"
            )
    if payload.get("session_preregistration_creation_authorized") is not False:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "contract_must_not_authorize_preregistration_creation"
        )
    if payload.get("authorization_issuance_authorized") is not False:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "contract_must_not_authorize_issuance"
        )
    if payload.get("productive_session_execution_authorized") is not False:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "contract_must_not_authorize_session_execution"
        )
    if payload.get("candidate_schema_closed_world") is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "contract_must_declare_closed_world_candidate_schema"
        )
    if payload.get("candidate_schema_version") != CANDIDATE_SCHEMA_VERSION:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "contract_candidate_schema_version_mismatch"
        )
    return payload


def compute_candidate_preregistration_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(dict(payload), exclude=("preregistration_digest",))


def build_example_additional_session_candidate_v1(
    *,
    session_index: int = 1,
    duration_seconds: int = MINIMUM_SESSION_DURATION_SECONDS,
    post_first_produce_event_span_seconds: int = (MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS),
    maximum_cycles_per_session: int = MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    maximum_requests_per_session: int | None = None,
    repository_sha: str = BOUND_REPOSITORY_SHA,
    design_digest: str = BOUND_DESIGN_DIGEST,
    runbook_digest: str = BOUND_RUNBOOK_DIGEST,
    target_age_buckets_seconds: tuple[int, ...] = TARGET_AGE_BUCKETS_SECONDS,
    first_produce_required: bool = True,
    natural_age_progression_required: bool = True,
    age_7200_observation_required: bool = True,
    recompute_after_age_floor_required: bool = True,
    post_recompute_fresh_observation_required: bool = True,
    multiple_market_regimes_required: bool = True,
    authorization_required: bool = True,
    single_use_authorization_required: bool = True,
    campaign_id: str | None = None,
    session_id: str | None = None,
    venue: str = PUBLIC_MD_VENUE,
    instrument: str = CANONICAL_INSTRUMENT_ID,
    network_scope: str = PUBLIC_MD_NETWORK_SCOPE,
    session_scope: str = SESSION_SCOPE,
    schema_name: str = CANDIDATE_SCHEMA_NAME,
    schema_version: str = CANDIDATE_SCHEMA_VERSION,
) -> AdditionalEvidenceSessionCandidateV1:
    """Build an in-memory candidate for validation tests.

    Does not write artifacts, authorize creation, or execute a session.
    """
    cid = campaign_id or deterministic_additional_campaign_id_v1(repository_sha=repository_sha)
    sid = session_id or deterministic_additional_session_id_v1(
        campaign_id=cid,
        session_index=session_index,
    )
    requests = (
        int(maximum_requests_per_session)
        if maximum_requests_per_session is not None
        else int(maximum_cycles_per_session)
    )
    auth_binding = build_candidate_authorization_binding_v1(
        campaign_id=cid,
        session_id=sid,
        repository_sha=repository_sha,
        design_digest=design_digest,
        runbook_digest=runbook_digest,
    )
    provisional: dict[str, Any] = {
        "age_7200_observation_required": age_7200_observation_required,
        "authorization_binding": auth_binding,
        "authorization_required": authorization_required,
        "campaign_id": cid,
        "design_digest": design_digest,
        "duration_seconds": int(duration_seconds),
        "evidence_write_authorized": False,
        "execution_authorized": False,
        "first_produce_required": first_produce_required,
        "forbidden_artificial_controls": _forbidden_artificial_controls(),
        "instrument": instrument,
        "maximum_cycles_per_session": int(maximum_cycles_per_session),
        "maximum_requests_per_cycle": MAXIMUM_REQUESTS_PER_CYCLE,
        "maximum_requests_per_session": requests,
        "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
        "multiple_market_regimes_required": multiple_market_regimes_required,
        "natural_age_progression_required": natural_age_progression_required,
        "network_authorized": False,
        "network_scope": network_scope,
        "post_first_produce_event_span_seconds": int(post_first_produce_event_span_seconds),
        "post_recompute_fresh_observation_required": (post_recompute_fresh_observation_required),
        "recompute_after_age_floor_required": recompute_after_age_floor_required,
        "repository_sha": repository_sha,
        "runbook_digest": runbook_digest,
        "schema_name": schema_name,
        "schema_version": schema_version,
        "session_id": sid,
        "session_preregistration_creation_authorized": False,
        "session_scope": session_scope,
        "single_use_authorization_required": single_use_authorization_required,
        "target_age_buckets_seconds": list(target_age_buckets_seconds),
        "venue": venue,
    }
    digest = compute_candidate_preregistration_digest_v1(provisional)
    return AdditionalEvidenceSessionCandidateV1(
        campaign_id=cid,
        session_id=sid,
        repository_sha=repository_sha,
        design_digest=design_digest,
        runbook_digest=runbook_digest,
        preregistration_digest=digest,
        venue=venue,
        instrument=instrument,
        network_scope=network_scope,
        session_scope=session_scope,
        duration_seconds=int(duration_seconds),
        maximum_cycles_per_session=int(maximum_cycles_per_session),
        maximum_requests_per_session=requests,
        minimum_interval_seconds=MINIMUM_INTERVAL_SECONDS,
        maximum_requests_per_cycle=MAXIMUM_REQUESTS_PER_CYCLE,
        target_age_buckets_seconds=tuple(int(x) for x in target_age_buckets_seconds),
        first_produce_required=first_produce_required,
        natural_age_progression_required=natural_age_progression_required,
        age_7200_observation_required=age_7200_observation_required,
        recompute_after_age_floor_required=recompute_after_age_floor_required,
        post_recompute_fresh_observation_required=(post_recompute_fresh_observation_required),
        multiple_market_regimes_required=multiple_market_regimes_required,
        authorization_required=authorization_required,
        single_use_authorization_required=single_use_authorization_required,
        post_first_produce_event_span_seconds=int(post_first_produce_event_span_seconds),
        schema_name=schema_name,
        schema_version=schema_version,
        authorization_binding=auth_binding,
        forbidden_artificial_controls=_forbidden_artificial_controls(),
        session_preregistration_creation_authorized=False,
        execution_authorized=False,
        network_authorized=False,
        evidence_write_authorized=False,
    )


def build_example_additional_session_candidate_pair_v1() -> tuple[
    AdditionalEvidenceSessionCandidateV1,
    AdditionalEvidenceSessionCandidateV1,
]:
    first = build_example_additional_session_candidate_v1(session_index=1)
    second = build_example_additional_session_candidate_v1(
        session_index=2,
        campaign_id=first.campaign_id,
    )
    return first, second
