"""Fail-closed validation for additional evidence session preregistration candidates.

Closed-world candidate schema: unknown top-level and nested fields are rejected.
Exact schema-version and venue/instrument/network/session scope bindings are
required. No normalization, aliases, or best-effort acceptance.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.authorization_binding_v1 import (
    validate_authorization_binding_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    ALLOWED_AUTHORIZATION_BINDING_FIELDS,
    ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS,
    ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS,
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    CANDIDATE_SCHEMA_NAME,
    CANDIDATE_SCHEMA_VERSION,
    EXPECTED_INSTRUMENT,
    EXPECTED_NETWORK_SCOPE,
    EXPECTED_SESSION_SCOPE,
    EXPECTED_VENUE,
    FORBIDDEN_ARTIFICIAL_FLAGS,
    MAXIMUM_REQUESTS_PER_CYCLE,
    MINIMUM_INTERVAL_SECONDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
    MINIMUM_MAXIMUM_REQUESTS_PER_SESSION,
    MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS,
    MINIMUM_SESSION_DURATION_SECONDS,
    REQUIRED_CANDIDATE_FIELDS,
    TARGET_AGE_BUCKETS_SECONDS,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.contract_v1 import (
    compute_candidate_preregistration_digest_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.models_v1 import (
    AdditionalEvidenceSessionPreregistrationContractError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.uniqueness_v1 import (
    assert_campaign_id_not_exhausted_v1,
    assert_session_id_not_exhausted_v1,
    assert_session_id_not_terminal_used_v1,
)

_ALLOWED_TOP_LEVEL = frozenset(ALLOWED_CANDIDATE_TOP_LEVEL_FIELDS)
_ALLOWED_AUTH_BINDING = frozenset(ALLOWED_AUTHORIZATION_BINDING_FIELDS)
_ALLOWED_ARTIFICIAL = frozenset(ALLOWED_FORBIDDEN_ARTIFICIAL_CONTROLS_FIELDS)


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
    raise AdditionalEvidenceSessionPreregistrationContractError(
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
        raise AdditionalEvidenceSessionPreregistrationContractError(error_code)
    value = payload[field]
    if value is None:
        raise AdditionalEvidenceSessionPreregistrationContractError(error_code)
    if not isinstance(value, str):
        raise AdditionalEvidenceSessionPreregistrationContractError(error_code)
    if value == "":
        raise AdditionalEvidenceSessionPreregistrationContractError(error_code)
    # Exact match only — no strip/casefold/alias normalization.
    if value != expected:
        raise AdditionalEvidenceSessionPreregistrationContractError(error_code)
    return value


def _require_bool_true(payload: Mapping[str, Any], field: str) -> None:
    if field not in payload:
        raise AdditionalEvidenceSessionPreregistrationContractError(f"{field}_required_true")
    if payload.get(field) is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(f"{field}_required_true")


def _require_bool_false(payload: Mapping[str, Any], field: str) -> None:
    if field not in payload:
        raise AdditionalEvidenceSessionPreregistrationContractError(f"{field}_required_false")
    if payload.get(field) is not False:
        raise AdditionalEvidenceSessionPreregistrationContractError(f"{field}_required_false")


def _validate_forbidden_artificial_controls(payload: Mapping[str, Any]) -> None:
    controls = payload.get("forbidden_artificial_controls")
    if not isinstance(controls, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "forbidden_artificial_controls_required"
        )
    _reject_unknown_fields(
        present_keys=list(controls.keys()),
        allowed=_ALLOWED_ARTIFICIAL,
        path_prefix="forbidden_artificial_controls",
    )
    for name in FORBIDDEN_ARTIFICIAL_FLAGS:
        if name not in controls:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"artificial_control_missing:{name}"
            )
        value = controls[name]
        if value is True:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"artificial_control_forbidden:{name}"
            )
        if value is not False:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"artificial_control_must_be_false:{name}"
            )


def _validate_authorization_binding_closed_world(binding: Mapping[str, Any]) -> None:
    _reject_unknown_fields(
        present_keys=list(binding.keys()),
        allowed=_ALLOWED_AUTH_BINDING,
        path_prefix="authorization_binding",
    )


def validate_additional_evidence_session_preregistration_candidate_v1(
    payload: Mapping[str, Any],
    *,
    expected_repository_sha: str = BOUND_REPOSITORY_SHA,
    expected_design_digest: str = BOUND_DESIGN_DIGEST,
    expected_runbook_digest: str = BOUND_RUNBOOK_DIGEST,
    terminal_session_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate one additional-session candidate fail-closed."""
    if not isinstance(payload, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractError("candidate_must_be_mapping")

    _reject_unknown_fields(
        present_keys=list(payload.keys()),
        allowed=_ALLOWED_TOP_LEVEL,
    )

    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in payload:
            # Scope / schema bindings use dedicated mismatch codes below.
            if field in {
                "schema_version",
                "venue",
                "instrument",
                "network_scope",
                "session_scope",
            }:
                continue
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"missing_required_field:{field}"
            )

    _require_exact_string_binding(
        payload,
        field="schema_version",
        expected=CANDIDATE_SCHEMA_VERSION,
        error_code="candidate_schema_version_mismatch",
    )
    _require_exact_string_binding(
        payload,
        field="schema_name",
        expected=CANDIDATE_SCHEMA_NAME,
        error_code="candidate_schema_name_mismatch",
    )
    _require_exact_string_binding(
        payload,
        field="venue",
        expected=EXPECTED_VENUE,
        error_code="venue_binding_mismatch",
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
        raise AdditionalEvidenceSessionPreregistrationContractError("campaign_id_required")
    if not isinstance(session_id, str) or not session_id:
        raise AdditionalEvidenceSessionPreregistrationContractError("session_id_required")
    assert_campaign_id_not_exhausted_v1(campaign_id)
    assert_session_id_not_exhausted_v1(session_id)
    assert_session_id_not_terminal_used_v1(
        session_id,
        terminal_session_ids=terminal_session_ids,
    )

    if not isinstance(payload.get("repository_sha"), str):
        raise AdditionalEvidenceSessionPreregistrationContractError("repository_sha_mismatch")
    if payload.get("repository_sha") != expected_repository_sha:
        raise AdditionalEvidenceSessionPreregistrationContractError("repository_sha_mismatch")
    if not isinstance(payload.get("design_digest"), str):
        raise AdditionalEvidenceSessionPreregistrationContractError("design_digest_mismatch")
    if payload.get("design_digest") != expected_design_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError("design_digest_mismatch")
    if not isinstance(payload.get("runbook_digest"), str):
        raise AdditionalEvidenceSessionPreregistrationContractError("runbook_digest_mismatch")
    if payload.get("runbook_digest") != expected_runbook_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError("runbook_digest_mismatch")

    try:
        duration = int(payload["duration_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "duration_seconds_invalid"
        ) from exc
    if duration < MINIMUM_SESSION_DURATION_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractError("duration_below_minimum_10860")

    try:
        post_span = int(payload["post_first_produce_event_span_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "post_first_produce_event_span_seconds_invalid"
        ) from exc
    if post_span < MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "post_first_produce_span_below_minimum_7260"
        )

    try:
        cycles = int(payload["maximum_cycles_per_session"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_cycles_per_session_invalid"
        ) from exc
    if cycles < MINIMUM_MAXIMUM_CYCLES_PER_SESSION:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_cycles_below_minimum_182"
        )

    try:
        requests = int(payload["maximum_requests_per_session"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_requests_per_session_invalid"
        ) from exc
    if requests < MINIMUM_MAXIMUM_REQUESTS_PER_SESSION:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_requests_below_minimum_182"
        )
    if requests < cycles:
        raise AdditionalEvidenceSessionPreregistrationContractError("requests_must_be_gte_cycles")

    try:
        minimum_interval = float(payload["minimum_interval_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "minimum_interval_seconds_invalid"
        ) from exc
    if minimum_interval < float(MINIMUM_INTERVAL_SECONDS):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "minimum_interval_seconds_below_floor"
        )
    try:
        max_per_cycle = int(payload["maximum_requests_per_cycle"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_requests_per_cycle_invalid"
        ) from exc
    if max_per_cycle != int(MAXIMUM_REQUESTS_PER_CYCLE):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_requests_per_cycle_mismatch"
        )

    raw_buckets = payload["target_age_buckets_seconds"]
    if not isinstance(raw_buckets, (list, tuple)):
        raise AdditionalEvidenceSessionPreregistrationContractError("target_age_buckets_mismatch")
    try:
        buckets = tuple(int(x) for x in raw_buckets)
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "target_age_buckets_mismatch"
        ) from exc
    if buckets != TARGET_AGE_BUCKETS_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractError("target_age_buckets_mismatch")
    if 7200 not in buckets:
        raise AdditionalEvidenceSessionPreregistrationContractError("missing_age_7200_bucket")

    _require_bool_true(payload, "first_produce_required")
    _require_bool_true(payload, "natural_age_progression_required")
    _require_bool_true(payload, "age_7200_observation_required")
    _require_bool_true(payload, "recompute_after_age_floor_required")
    _require_bool_true(payload, "post_recompute_fresh_observation_required")
    _require_bool_true(payload, "multiple_market_regimes_required")
    _require_bool_true(payload, "authorization_required")
    _require_bool_true(payload, "single_use_authorization_required")

    _require_bool_false(payload, "session_preregistration_creation_authorized")
    _require_bool_false(payload, "execution_authorized")
    _require_bool_false(payload, "network_authorized")
    _require_bool_false(payload, "evidence_write_authorized")

    binding = payload.get("authorization_binding")
    if not isinstance(binding, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_binding_required"
        )
    _validate_authorization_binding_closed_world(binding)
    validate_authorization_binding_v1(binding)
    if list(binding.get("session_ids") or []) != [session_id]:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_binding_session_mismatch"
        )

    _validate_forbidden_artificial_controls(payload)

    expected_digest = compute_candidate_preregistration_digest_v1(payload)
    stored_digest = payload.get("preregistration_digest")
    if not isinstance(stored_digest, str) or not stored_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "preregistration_digest_required"
        )
    if stored_digest != expected_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "preregistration_digest_mismatch"
        )

    return {
        "valid": True,
        "session_id": session_id,
        "campaign_id": campaign_id,
        "preregistration_digest": stored_digest,
        "repository_sha": expected_repository_sha,
        "schema_version": CANDIDATE_SCHEMA_VERSION,
        "venue": EXPECTED_VENUE,
        "instrument": EXPECTED_INSTRUMENT,
        "network_scope": EXPECTED_NETWORK_SCOPE,
        "session_scope": EXPECTED_SESSION_SCOPE,
    }
