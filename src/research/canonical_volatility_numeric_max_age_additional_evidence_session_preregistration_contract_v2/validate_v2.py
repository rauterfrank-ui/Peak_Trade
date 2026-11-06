"""Fail-closed validation for additional evidence session preregistration v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.authorization_binding_v2 import (
    validate_authorization_binding_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    ALLOWED_AUTHORIZATION_BINDING_FIELDS,
    ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS,
    ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS,
    BOUND_DESIGN_DIGEST,
    BOUND_RUNBOOK_DIGEST,
    CANDIDATE_SCHEMA_NAME,
    CANDIDATE_SCHEMA_VERSION,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_ARTIFICIAL_FLAGS,
    FORBIDDEN_AUTHORITY_FIELD_NAMES,
    KNOWN_REPOSITORY_BINDING_MODES,
    MAXIMUM_REQUESTS_PER_CYCLE,
    MINIMUM_INTERVAL_SECONDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS,
    MINIMUM_SESSION_DURATION_SECONDS,
    REPOSITORY_BINDING_MODE,
    REQUIRED_CANDIDATE_FIELDS,
    TARGET_AGE_BUCKETS_SECONDS,
    V1_CANDIDATE_SCHEMA_VERSION,
    V1_CONTRACT_VERSION,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.git_binding_v2 import (
    assert_baseline_not_after_artifact_creation_v2,
    assert_full_git_sha_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.uniqueness_v2 import (
    assert_campaign_id_not_exhausted_v2,
    assert_session_id_not_exhausted_v2,
    assert_session_id_not_terminal_used_v2,
)

_ALLOWED_TOP_LEVEL = frozenset(ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS)
_ALLOWED_AUTH_BINDING = frozenset(ALLOWED_AUTHORIZATION_BINDING_FIELDS)
_ALLOWED_ARTIFICIAL = frozenset(ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS)
_FORBIDDEN_AUTHORITY = frozenset(FORBIDDEN_AUTHORITY_FIELD_NAMES)


def _reject_unknown_fields(
    *,
    present_keys: Sequence[str],
    allowed: frozenset[str],
    path_prefix: str = "",
) -> None:
    unknown = sorted(set(present_keys) - allowed)
    if not unknown:
        return
    if path_prefix:
        rendered = ",".join(f"{path_prefix}.{key}" for key in unknown)
    else:
        rendered = ",".join(unknown)
    # Distinguish authority fields for clearer fail-closed codes.
    authority_hits = [k for k in unknown if k in _FORBIDDEN_AUTHORITY or k.endswith("_authority")]
    if authority_hits and not path_prefix:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            f"unknown_authority_fields:{','.join(sorted(authority_hits))}"
        )
    raise AdditionalEvidenceSessionPreregistrationContractV2Error(
        f"unknown_candidate_fields:{rendered}"
    )


def _require_exact_string_binding(
    payload: Mapping[str, Any],
    *,
    field: str,
    expected: str,
    error_code: str,
) -> str:
    if field not in payload:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(error_code)
    value = payload[field]
    if not isinstance(value, str) or value == "" or value != expected:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(error_code)
    return value


def _require_bool_true(payload: Mapping[str, Any], field: str) -> None:
    if payload.get(field) is not True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_required_true")


def _require_bool_false(payload: Mapping[str, Any], field: str) -> None:
    if payload.get(field) is not False:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_required_false")


def _validate_forbidden_artificial_controls(payload: Mapping[str, Any]) -> None:
    controls = payload.get("forbidden_artificial_controls")
    if not isinstance(controls, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "forbidden_artificial_controls_required"
        )
    _reject_unknown_fields(
        present_keys=list(controls.keys()),
        allowed=_ALLOWED_ARTIFICIAL,
        path_prefix="forbidden_artificial_controls",
    )
    for name in FORBIDDEN_ARTIFICIAL_FLAGS:
        if name not in controls:
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                f"artificial_control_missing:{name}"
            )
        if controls[name] is not False:
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                f"artificial_control_must_be_false:{name}"
            )


def reject_v1_for_new_authorization_readiness_v2(payload: Mapping[str, Any]) -> None:
    """V1 remains parseable elsewhere but cannot obtain new authorization readiness."""
    version = payload.get("schema_version") or payload.get("capability_version")
    if version in {V1_CANDIDATE_SCHEMA_VERSION, V1_CONTRACT_VERSION, "v1"}:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "v1_new_authorization_readiness_unsupported"
        )


def validate_additional_evidence_session_preregistration_candidate_v2(
    payload: Mapping[str, Any],
    *,
    expected_design_digest: str = BOUND_DESIGN_DIGEST,
    expected_runbook_digest: str = BOUND_RUNBOOK_DIGEST,
    terminal_session_ids: Sequence[str] | None = None,
    repo_root: Path | None = None,
    verify_baseline_artifact_ordering: bool = False,
) -> dict[str, Any]:
    """Validate one additional-session v2 candidate fail-closed.

    Structural/SHA-format validation does not require git. Optional
    verify_baseline_artifact_ordering enables local ancestor ordering check.
    """
    if not isinstance(payload, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("candidate_must_be_mapping")

    reject_v1_for_new_authorization_readiness_v2(payload)

    _reject_unknown_fields(present_keys=list(payload.keys()), allowed=_ALLOWED_TOP_LEVEL)

    # Explicit reject of removed tip-equality field.
    if "repository_sha" in payload:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "unknown_candidate_fields:repository_sha"
        )

    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in payload:
            if field in {
                "schema_version",
                "venue",
                "instrument",
                "network_scope",
                "session_scope",
                "repository_binding_mode",
            }:
                continue
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                f"missing_required_field:{field}"
            )

    schema_version = payload.get("schema_version")
    if schema_version != CANDIDATE_SCHEMA_VERSION:
        if schema_version == V1_CANDIDATE_SCHEMA_VERSION:
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                "v1_new_authorization_readiness_unsupported"
            )
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("unknown_contract_version")

    _require_exact_string_binding(
        payload,
        field="schema_name",
        expected=CANDIDATE_SCHEMA_NAME,
        error_code="candidate_schema_name_mismatch",
    )
    binding_mode = payload.get("repository_binding_mode")
    if not isinstance(binding_mode, str) or binding_mode not in KNOWN_REPOSITORY_BINDING_MODES:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("unknown_binding_mode")
    if binding_mode != REPOSITORY_BINDING_MODE:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("unknown_binding_mode")

    _require_exact_string_binding(
        payload, field="venue", expected=EXPECTED_VENUE, error_code="venue_binding_mismatch"
    )
    _require_exact_string_binding(
        payload,
        field="instrument",
        expected=EXPECTED_INSTRUMENT,
        error_code="instrument_binding_mismatch",
    )
    _require_exact_string_binding(
        payload,
        field="network_scope",
        expected=EXPECTED_NETWORK_SCOPE,
        error_code="network_scope_binding_mismatch",
    )
    _require_exact_string_binding(
        payload,
        field="session_scope",
        expected=EXPECTED_SESSION_SCOPE,
        error_code="session_scope_binding_mismatch",
    )

    campaign_id = payload["campaign_id"]
    session_id = payload["session_id"]
    if not isinstance(campaign_id, str) or not campaign_id:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("campaign_id_required")
    if not isinstance(session_id, str) or not session_id:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("session_id_required")
    assert_campaign_id_not_exhausted_v2(campaign_id)
    assert_session_id_not_exhausted_v2(session_id)
    assert_session_id_not_terminal_used_v2(session_id, terminal_session_ids=terminal_session_ids)

    code_baseline_sha = assert_full_git_sha_v2(
        payload.get("code_baseline_sha"), field="code_baseline_sha"
    )
    artifact_creation_sha = assert_full_git_sha_v2(
        payload.get("artifact_creation_sha"), field="artifact_creation_sha"
    )
    critical_digest = payload.get("critical_surface_manifest_digest")
    if not isinstance(critical_digest, str) or len(critical_digest) != 64:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "critical_surface_manifest_digest_invalid"
        )

    if payload.get("design_digest") != expected_design_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("design_digest_mismatch")
    if payload.get("runbook_digest") != expected_runbook_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("runbook_digest_mismatch")

    try:
        duration = int(payload["duration_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "duration_seconds_invalid"
        ) from exc
    if duration < MINIMUM_SESSION_DURATION_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "duration_below_minimum_10860"
        )

    try:
        post_span = int(payload["post_first_produce_event_span_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "post_first_produce_event_span_seconds_invalid"
        ) from exc
    if post_span < MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "post_first_produce_span_below_minimum_7260"
        )

    try:
        cycles = int(payload["maximum_cycles_per_session"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_cycles_per_session_invalid"
        ) from exc
    if cycles < MINIMUM_MAXIMUM_CYCLES_PER_SESSION:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_cycles_below_minimum_182"
        )

    try:
        requests = int(payload["maximum_requests_per_session"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_requests_per_session_invalid"
        ) from exc
    if requests < MINIMUM_MAXIMUM_REQUESTS_PER_SESSION:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_requests_below_minimum_182"
        )
    if requests < cycles:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("requests_must_be_gte_cycles")

    try:
        minimum_interval = float(payload["minimum_interval_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "minimum_interval_seconds_invalid"
        ) from exc
    if minimum_interval < float(MINIMUM_INTERVAL_SECONDS):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "minimum_interval_seconds_below_floor"
        )
    try:
        max_per_cycle = int(payload["maximum_requests_per_cycle"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_requests_per_cycle_invalid"
        ) from exc
    if max_per_cycle != int(MAXIMUM_REQUESTS_PER_CYCLE):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "maximum_requests_per_cycle_mismatch"
        )

    raw_buckets = payload["target_age_buckets_seconds"]
    if not isinstance(raw_buckets, (list, tuple)):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("target_age_buckets_mismatch")
    try:
        buckets = tuple(int(x) for x in raw_buckets)
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "target_age_buckets_mismatch"
        ) from exc
    if buckets != TARGET_AGE_BUCKETS_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("target_age_buckets_mismatch")

    for flag in (
        "first_produce_required",
        "natural_age_progression_required",
        "age_7200_observation_required",
        "recompute_after_age_floor_required",
        "post_recompute_fresh_observation_required",
        "multiple_market_regimes_required",
        "authorization_required",
        "single_use_authorization_required",
    ):
        _require_bool_true(payload, flag)
    for flag in (
        "session_preregistration_creation_authorized",
        "execution_authorized",
        "network_authorized",
        "evidence_write_authorized",
    ):
        _require_bool_false(payload, flag)

    binding = payload.get("authorization_binding")
    if not isinstance(binding, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_binding_required"
        )
    _reject_unknown_fields(
        present_keys=list(binding.keys()),
        allowed=_ALLOWED_AUTH_BINDING,
        path_prefix="authorization_binding",
    )
    validate_authorization_binding_v2(binding)
    if list(binding.get("session_ids") or []) != [session_id]:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_binding_session_mismatch"
        )
    if binding.get("code_baseline_sha") != code_baseline_sha:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_binding_code_baseline_mismatch"
        )

    _validate_forbidden_artificial_controls(payload)

    expected_digest = digest_excluding_keys(dict(payload), exclude=("preregistration_digest",))
    stored_digest = payload.get("preregistration_digest")
    if not isinstance(stored_digest, str) or not stored_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "preregistration_digest_required"
        )
    if stored_digest != expected_digest:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "preregistration_digest_mismatch"
        )

    if verify_baseline_artifact_ordering:
        if repo_root is None:
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                "repo_root_required_for_ancestor_ordering"
            )
        assert_baseline_not_after_artifact_creation_v2(
            code_baseline_sha=code_baseline_sha,
            artifact_creation_sha=artifact_creation_sha,
            repo_root=Path(repo_root),
        )

    return {
        "valid": True,
        "session_id": session_id,
        "campaign_id": campaign_id,
        "preregistration_digest": stored_digest,
        "code_baseline_sha": code_baseline_sha,
        "artifact_creation_sha": artifact_creation_sha,
        "critical_surface_manifest_digest": critical_digest,
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "venue": EXPECTED_VENUE,
        "instrument": EXPECTED_INSTRUMENT,
        "network_scope": EXPECTED_NETWORK_SCOPE,
        "session_scope": EXPECTED_SESSION_SCOPE,
        "tip_of_main_equality_required": False,
    }
