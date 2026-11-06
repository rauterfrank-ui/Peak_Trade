"""Build and verify additional-evidence session preregistration contract v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.authorization_binding_v2 import (
    build_authorization_binding_schema_v2,
    build_candidate_authorization_binding_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    ALLOWED_AUTHORIZATION_BINDING_FIELDS,
    ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS,
    ALLOWED_CONTRACT_TOP_LEVEL_FIELDS,
    ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS,
    ARTIFACT_RELATIVE_PATH,
    AUTHORITY_NEGATIVE_CONTRACT,
    AUTHORIZATION_CONSUMPTION_AUTHORIZED,
    AUTHORIZATION_ISSUANCE_AUTHORIZED,
    BINDING_VALUE_NORMALIZATION_FORBIDDEN,
    BOUND_DESIGN_DIGEST,
    BOUND_RUNBOOK_DIGEST,
    CANDIDATE_SCHEMA_CLOSED_WORLD,
    CANDIDATE_SCHEMA_NAME,
    CANDIDATE_SCHEMA_VERSION,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    COVERAGE_REQUIREMENTS,
    CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
    DEFAULT_CODE_BASELINE_SHA,
    EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
    EXISTING_EXHAUSTED_CAMPAIGN_ID,
    EXISTING_EXHAUSTED_SESSION_IDS,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_ARTIFICIAL_FLAGS,
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
    PREREGISTRATION_RELATIVE_PATH,
    PRODUCTIVE_SESSION_EXECUTION_AUTHORIZED,
    PUBLIC_MD_NETWORK_SCOPE,
    PUBLIC_MD_VENUE,
    READY_FOR_ADDITIONAL_SESSION_PREREGISTRATION,
    READY_FOR_AUTHORIZATION_ISSUANCE,
    READY_FOR_PRODUCTIVE_SESSION_EXECUTION,
    RECOMMENDED_MAXIMUM_CYCLES_PER_SESSION,
    RECOMMENDED_MAXIMUM_REQUESTS_PER_SESSION,
    REPOSITORY_BINDING_MODE,
    REPOSITORY_SHA_FIELD_STATUS,
    REQUIRED_CANDIDATE_FIELDS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SELF_COMMIT_SHA_EMBEDDING_REQUIRED,
    SESSION_PREREGISTRATION_CREATION_AUTHORIZED,
    SESSION_SCOPE,
    SUPERSEDED_PR_5629,
    TARGET_AGE_BUCKETS_SECONDS,
    TIP_OF_MAIN_EQUALITY_REQUIRED,
    UNKNOWN_AUTHORITY_FIELDS_REJECTED,
    UNKNOWN_FIELDS_REJECTED,
    V1_NEW_AUTHORIZATION_READINESS_ALLOWED,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.critical_surface_v2 import (
    compute_critical_surface_manifest_digest_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.git_binding_v2 import (
    assert_full_git_sha_v2,
    resolve_artifact_creation_sha_from_git_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionCandidateV2,
    AdditionalEvidenceSessionPreregistrationContractV2,
    AdditionalEvidenceSessionPreregistrationContractV2Error,
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.uniqueness_v2 import (
    deterministic_additional_campaign_id_v2,
    deterministic_additional_session_id_v2,
)


def _forbidden_artificial_controls() -> dict[str, bool]:
    return {name: False for name in FORBIDDEN_ARTIFICIAL_FLAGS}


def compute_candidate_preregistration_digest_v2(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(dict(payload), exclude=("preregistration_digest",))


def _contract_payload_without_digest(
    *,
    code_baseline_sha: str,
    artifact_creation_sha: str,
    critical_surface_manifest_digest: str,
) -> dict[str, Any]:
    return {
        "age_7200_observation_required": True,
        "allowed_authorization_binding_fields": list(ALLOWED_AUTHORIZATION_BINDING_FIELDS),
        "allowed_candidate_top_level_fields": list(ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS),
        "allowed_forbidden_artificial_controls_fields": list(
            ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS
        ),
        "artifact_creation_sha": artifact_creation_sha,
        "authority_negative_contract": dict(AUTHORITY_NEGATIVE_CONTRACT),
        "authorization_binding_schema": build_authorization_binding_schema_v2(),
        "authorization_consumption_authorized": AUTHORIZATION_CONSUMPTION_AUTHORIZED,
        "authorization_issuance_authorized": AUTHORIZATION_ISSUANCE_AUTHORIZED,
        "authorization_per_session_required": True,
        "binding_value_normalization_forbidden": BINDING_VALUE_NORMALIZATION_FORBIDDEN,
        "candidate_schema_closed_world": CANDIDATE_SCHEMA_CLOSED_WORLD,
        "candidate_schema_name": CANDIDATE_SCHEMA_NAME,
        "candidate_schema_version": CANDIDATE_SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "code_baseline_sha": code_baseline_sha,
        "coverage_requirements": dict(COVERAGE_REQUIREMENTS),
        "critical_surface_manifest_digest": critical_surface_manifest_digest,
        "critical_surface_manifest_path": CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
        "design_digest": BOUND_DESIGN_DIGEST,
        "exhausted_campaign_id": EXISTING_EXHAUSTED_CAMPAIGN_ID,
        "exhausted_campaign_maximum_session_count": EXISTING_CAMPAIGN_MAXIMUM_SESSION_COUNT,
        "exhausted_session_ids": list(EXISTING_EXHAUSTED_SESSION_IDS),
        "expected_instrument": EXPECTED_INSTRUMENT,
        "expected_network_scope": EXPECTED_NETWORK_SCOPE,
        "expected_session_scope": EXPECTED_SESSION_SCOPE,
        "expected_venue": EXPECTED_VENUE,
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
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "repository_sha_field_status": REPOSITORY_SHA_FIELD_STATUS,
        "required_candidate_fields": list(REQUIRED_CANDIDATE_FIELDS),
        "runbook_digest": BOUND_RUNBOOK_DIGEST,
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "self_commit_sha_embedding_required": SELF_COMMIT_SHA_EMBEDDING_REQUIRED,
        "session_preregistration_creation_authorized": (
            SESSION_PREREGISTRATION_CREATION_AUTHORIZED
        ),
        "single_use_authorization_required": True,
        "superseded_pr_5629": SUPERSEDED_PR_5629,
        "target_age_buckets_seconds": list(TARGET_AGE_BUCKETS_SECONDS),
        "tip_of_main_equality_required": TIP_OF_MAIN_EQUALITY_REQUIRED,
        "unknown_authority_fields_rejected": UNKNOWN_AUTHORITY_FIELDS_REJECTED,
        "unknown_fields_rejected": UNKNOWN_FIELDS_REJECTED,
        "v1_new_authorization_readiness_allowed": V1_NEW_AUTHORIZATION_READINESS_ALLOWED,
    }


def build_additional_evidence_session_preregistration_contract_v2(
    *,
    repo_root: Path | None = None,
    code_baseline_sha: str | None = None,
    artifact_creation_sha: str | None = None,
    critical_surface_manifest_digest: str | None = None,
) -> AdditionalEvidenceSessionPreregistrationContractV2:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    baseline = assert_full_git_sha_v2(
        code_baseline_sha or DEFAULT_CODE_BASELINE_SHA,
        field="code_baseline_sha",
    )
    creation = (
        assert_full_git_sha_v2(artifact_creation_sha, field="artifact_creation_sha")
        if artifact_creation_sha is not None
        else resolve_artifact_creation_sha_from_git_v2(repo_root=root)
    )
    digest = (
        critical_surface_manifest_digest
        if critical_surface_manifest_digest is not None
        else compute_critical_surface_manifest_digest_v2(repo_root=root)
    )
    payload = _contract_payload_without_digest(
        code_baseline_sha=baseline,
        artifact_creation_sha=creation,
        critical_surface_manifest_digest=digest,
    )
    contract_digest = digest_excluding_keys(payload, exclude=("contract_digest",))
    return AdditionalEvidenceSessionPreregistrationContractV2(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        contract_digest=contract_digest,
        code_baseline_sha=baseline,
        artifact_creation_sha=creation,
        critical_surface_manifest_digest=digest,
        repository_binding_mode=REPOSITORY_BINDING_MODE,
        tip_of_main_equality_required=TIP_OF_MAIN_EQUALITY_REQUIRED,
        self_commit_sha_embedding_required=SELF_COMMIT_SHA_EMBEDDING_REQUIRED,
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
        authorization_binding_schema=build_authorization_binding_schema_v2(),
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
        v1_new_authorization_readiness_allowed=V1_NEW_AUTHORIZATION_READINESS_ALLOWED,
        repository_sha_field_status=REPOSITORY_SHA_FIELD_STATUS,
        critical_surface_manifest_path=CRITICAL_SURFACE_MANIFEST_RELATIVE_PATH,
        superseded_pr_5629=SUPERSEDED_PR_5629,
    )


def render_additional_evidence_session_preregistration_contract_v2(
    *,
    repo_root: Path | None = None,
    code_baseline_sha: str | None = None,
    artifact_creation_sha: str | None = None,
    critical_surface_manifest_digest: str | None = None,
) -> dict[str, Any]:
    return build_additional_evidence_session_preregistration_contract_v2(
        repo_root=repo_root,
        code_baseline_sha=code_baseline_sha,
        artifact_creation_sha=artifact_creation_sha,
        critical_surface_manifest_digest=critical_surface_manifest_digest,
    ).to_dict()


def verify_additional_evidence_session_preregistration_contract_artifact_v2(
    *,
    artifact_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = artifact_path or (root / ARTIFACT_RELATIVE_PATH)
    payload = json.loads(path.read_text(encoding="utf-8"))
    unknown = sorted(set(payload) - set(ALLOWED_CONTRACT_TOP_LEVEL_FIELDS))
    if unknown:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            f"unknown_contract_fields:{','.join(unknown)}"
        )
    expected = build_additional_evidence_session_preregistration_contract_v2(
        repo_root=root,
        code_baseline_sha=str(payload.get("code_baseline_sha")),
        artifact_creation_sha=str(payload.get("artifact_creation_sha")),
        critical_surface_manifest_digest=str(payload.get("critical_surface_manifest_digest")),
    ).to_dict()
    if payload.get("contract_digest") != expected["contract_digest"]:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("contract_digest_mismatch")
    for key, value in expected.items():
        if key == "contract_digest":
            continue
        if payload.get(key) != value:
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                f"contract_field_drift:{key}"
            )
    if payload.get("tip_of_main_equality_required") is not False:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "tip_of_main_equality_must_be_false"
        )
    if payload.get("v1_new_authorization_readiness_allowed") is not False:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "v1_new_authorization_readiness_must_be_false"
        )
    return payload


def build_example_additional_session_candidate_v2(
    *,
    repo_root: Path | None = None,
    session_index: int = 1,
    duration_seconds: int = MINIMUM_SESSION_DURATION_SECONDS,
    post_first_produce_event_span_seconds: int = (MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS),
    maximum_cycles_per_session: int = MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    maximum_requests_per_session: int | None = None,
    code_baseline_sha: str | None = None,
    artifact_creation_sha: str | None = None,
    critical_surface_manifest_digest: str | None = None,
    design_digest: str = BOUND_DESIGN_DIGEST,
    runbook_digest: str = BOUND_RUNBOOK_DIGEST,
    target_age_buckets_seconds: tuple[int, ...] = TARGET_AGE_BUCKETS_SECONDS,
    campaign_id: str | None = None,
    session_id: str | None = None,
    venue: str = PUBLIC_MD_VENUE,
    instrument: str = CANONICAL_INSTRUMENT_ID,
    network_scope: str = PUBLIC_MD_NETWORK_SCOPE,
    session_scope: str = SESSION_SCOPE,
    schema_name: str = CANDIDATE_SCHEMA_NAME,
    schema_version: str = CANDIDATE_SCHEMA_VERSION,
    repository_binding_mode: str = REPOSITORY_BINDING_MODE,
) -> AdditionalEvidenceSessionCandidateV2:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    baseline = assert_full_git_sha_v2(
        code_baseline_sha or DEFAULT_CODE_BASELINE_SHA,
        field="code_baseline_sha",
    )
    creation = (
        assert_full_git_sha_v2(artifact_creation_sha, field="artifact_creation_sha")
        if artifact_creation_sha is not None
        else resolve_artifact_creation_sha_from_git_v2(repo_root=root)
    )
    surface_digest = (
        critical_surface_manifest_digest
        if critical_surface_manifest_digest is not None
        else compute_critical_surface_manifest_digest_v2(repo_root=root)
    )
    cid = campaign_id or deterministic_additional_campaign_id_v2(code_baseline_sha=baseline)
    sid = session_id or deterministic_additional_session_id_v2(
        campaign_id=cid,
        session_index=session_index,
    )
    requests = (
        int(maximum_requests_per_session)
        if maximum_requests_per_session is not None
        else int(maximum_cycles_per_session)
    )
    auth_binding = build_candidate_authorization_binding_v2(
        campaign_id=cid,
        session_id=sid,
        code_baseline_sha=baseline,
        critical_surface_manifest_digest=surface_digest,
        design_digest=design_digest,
        runbook_digest=runbook_digest,
    )
    provisional: dict[str, Any] = {
        "age_7200_observation_required": True,
        "artifact_creation_sha": creation,
        "authorization_binding": auth_binding,
        "authorization_required": True,
        "campaign_id": cid,
        "code_baseline_sha": baseline,
        "critical_surface_manifest_digest": surface_digest,
        "design_digest": design_digest,
        "duration_seconds": int(duration_seconds),
        "evidence_write_authorized": False,
        "execution_authorized": False,
        "first_produce_required": True,
        "forbidden_artificial_controls": _forbidden_artificial_controls(),
        "instrument": instrument,
        "maximum_cycles_per_session": int(maximum_cycles_per_session),
        "maximum_requests_per_cycle": MAXIMUM_REQUESTS_PER_CYCLE,
        "maximum_requests_per_session": requests,
        "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
        "multiple_market_regimes_required": True,
        "natural_age_progression_required": True,
        "network_authorized": False,
        "network_scope": network_scope,
        "post_first_produce_event_span_seconds": int(post_first_produce_event_span_seconds),
        "post_recompute_fresh_observation_required": True,
        "recompute_after_age_floor_required": True,
        "repository_binding_mode": repository_binding_mode,
        "runbook_digest": runbook_digest,
        "schema_name": schema_name,
        "schema_version": schema_version,
        "session_id": sid,
        "session_preregistration_creation_authorized": False,
        "session_scope": session_scope,
        "single_use_authorization_required": True,
        "target_age_buckets_seconds": list(target_age_buckets_seconds),
        "venue": venue,
    }
    digest = compute_candidate_preregistration_digest_v2(provisional)
    return AdditionalEvidenceSessionCandidateV2(
        campaign_id=cid,
        session_id=sid,
        code_baseline_sha=baseline,
        artifact_creation_sha=creation,
        critical_surface_manifest_digest=surface_digest,
        repository_binding_mode=repository_binding_mode,
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
        first_produce_required=True,
        natural_age_progression_required=True,
        age_7200_observation_required=True,
        recompute_after_age_floor_required=True,
        post_recompute_fresh_observation_required=True,
        multiple_market_regimes_required=True,
        authorization_required=True,
        single_use_authorization_required=True,
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


def build_active_additional_evidence_session_preregistration_v2(
    *,
    repo_root: Path | None = None,
    code_baseline_sha: str | None = None,
    artifact_creation_sha: str | None = None,
    critical_surface_manifest_digest: str | None = None,
) -> dict[str, Any]:
    """Build exactly one active v2 preregistration payload (no v1)."""
    candidate = build_example_additional_session_candidate_v2(
        repo_root=repo_root,
        session_index=1,
        code_baseline_sha=code_baseline_sha,
        artifact_creation_sha=artifact_creation_sha,
        critical_surface_manifest_digest=critical_surface_manifest_digest,
    )
    return candidate.to_dict()


def render_canonical_json_bytes_v2(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def count_active_v2_preregistrations(*, repo_root: Path) -> int:
    path = Path(repo_root) / PREREGISTRATION_RELATIVE_PATH
    if not path.is_file():
        return 0
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != CANDIDATE_SCHEMA_VERSION:
        return 0
    return 1
