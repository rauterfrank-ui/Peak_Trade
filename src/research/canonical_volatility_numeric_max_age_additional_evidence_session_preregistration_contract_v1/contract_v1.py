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
    ARTIFACT_RELATIVE_PATH,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    CANDIDATE_SCHEMA_NAME,
    CANDIDATE_SCHEMA_VERSION,
    CANONICAL_INSTRUMENT_ID,
    COVERAGE_REQUIREMENTS,
    EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    EXISTING_EXHAUSTED_SESSION_IDS,
    FORBIDDEN_ARTIFICIAL_FLAGS,
    HARD_STOP,
    MAXIMUM_REQUESTS_PER_CYCLE,
    MINIMUM_ADDITIONAL_PRODUCTIVE_SESSIONS,
    MINIMUM_INTERVAL_SECONDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS,
    MINIMUM_SESSION_DURATION_SECONDS,
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


def build_additional_evidence_session_preregistration_contract_v1() -> (
    AdditionalEvidenceSessionPreregistrationContractV1
):
    payload: dict[str, Any] = {
        "authorization_binding_schema": build_authorization_binding_schema_v1(),
        "authorization_consumption_authorized": AUTHORIZATION_CONSUMPTION_AUTHORIZED,
        "authorization_issuance_authorized": AUTHORIZATION_ISSUANCE_AUTHORIZED,
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "coverage_requirements": dict(COVERAGE_REQUIREMENTS),
        "design_digest": BOUND_DESIGN_DIGEST,
        "exhausted_campaign_id": EXISTING_EXHAUSTED_CAMPAIGN_ID,
        "exhausted_campaign_maximum_session_count": EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
        "exhausted_session_ids": list(EXISTING_EXHAUSTED_SESSION_IDS),
        "forbidden_artificial_controls": _forbidden_artificial_controls(),
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
        "network_access_authorized": NETWORK_ACCESS_AUTHORIZED,
        "numeric_max_age_enforcing": NUMERIC_MAX_AGE_ENFORCING,
        "numeric_max_age_selected": NUMERIC_MAX_AGE_SELECTED,
        "operator_workflow": list(OPERATOR_WORKFLOW),
        "productive_session_execution_authorized": PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
        "ready_for_additional_session_preregistration": (
            READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION
        ),
        "ready_for_authorization_issuance": READY_FOR_AUTHORIZATION_ISSUANCE,
        "ready_for_productive_session_execution": READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
        "recommended_maximum_cycles_per_session": RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION,
        "recommended_maximum_requests_per_session": (RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION),
        "repository_sha": BOUND_REPOSITORY_SHA,
        "required_candidate_fields": list(REQUIRED_CANDIDATE_FIELDS),
        "runbook_digest": BOUND_RUNBOOK_DIGEST,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "session_preregistration_creation_authorized": (
            SESSION_PREREGISTRATION_CREATION_AUTHORIZED
        ),
        "target_age_buckets_seconds": list(TARGET_AGE_BUCKETS_SECONDS),
    }
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
        "instrument": CANONICAL_INSTRUMENT_ID,
        "maximum_cycles_per_session": int(maximum_cycles_per_session),
        "maximum_requests_per_cycle": MAXIMUM_REQUESTS_PER_CYCLE,
        "maximum_requests_per_session": requests,
        "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
        "multiple_market_regimes_required": multiple_market_regimes_required,
        "natural_age_progression_required": natural_age_progression_required,
        "network_authorized": False,
        "network_scope": PUBLIC_MD_NETWORK_SCOPE,
        "post_first_produce_event_span_seconds": int(post_first_produce_event_span_seconds),
        "post_recompute_fresh_observation_required": (post_recompute_fresh_observation_required),
        "recompute_after_age_floor_required": recompute_after_age_floor_required,
        "repository_sha": repository_sha,
        "runbook_digest": runbook_digest,
        "schema_name": CANDIDATE_SCHEMA_NAME,
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "session_id": sid,
        "session_preregistration_creation_authorized": False,
        "session_scope": SESSION_SCOPE,
        "single_use_authorization_required": single_use_authorization_required,
        "target_age_buckets_seconds": list(target_age_buckets_seconds),
        "venue": PUBLIC_MD_VENUE,
    }
    digest = compute_candidate_preregistration_digest_v1(provisional)
    return AdditionalEvidenceSessionCandidateV1(
        campaign_id=cid,
        session_id=sid,
        repository_sha=repository_sha,
        design_digest=design_digest,
        runbook_digest=runbook_digest,
        preregistration_digest=digest,
        venue=PUBLIC_MD_VENUE,
        instrument=CANONICAL_INSTRUMENT_ID,
        network_scope=PUBLIC_MD_NETWORK_SCOPE,
        session_scope=SESSION_SCOPE,
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
        schema_name=CANDIDATE_SCHEMA_NAME,
        schema_version=CANDIDATE_SCHEMA_VERSION,
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
