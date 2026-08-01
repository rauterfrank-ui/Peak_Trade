"""Fail-closed validation for additional evidence session preregistration candidates."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.authorization_binding_v1 import (
    validate_authorization_binding_v1,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    BOUND_DESIGN_DIGEST,
    BOUND_REPOSITORY_SHA,
    BOUND_RUNBOOK_DIGEST,
    FORBIDDEN_ARTIFICIAL_FLAGS,
    MAXIMUM_REQUESTS_PER_CYCLE,
    MINIMUM_INTERVAL_SECONDS,
    MINIMUM_MAXIMUM_CYCLES_PER_SESSION,
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


def _require_bool_true(payload: Mapping[str, Any], field: str) -> None:
    if payload.get(field) is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(f"{field}_required_true")


def _validate_forbidden_artificial_controls(payload: Mapping[str, Any]) -> None:
    controls = payload.get("forbidden_artificial_controls")
    if not isinstance(controls, Mapping):
        # Also accept top-level flags.
        controls = {name: payload.get(name) for name in FORBIDDEN_ARTIFICIAL_FLAGS}
    for name in FORBIDDEN_ARTIFICIAL_FLAGS:
        value = controls.get(name, payload.get(name))
        if value is True:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"artificial_control_forbidden:{name}"
            )
        if value is not False and value is not None:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"artificial_control_must_be_false:{name}"
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
    for field in REQUIRED_CANDIDATE_FIELDS:
        if field not in payload:
            raise AdditionalEvidenceSessionPreregistrationContractError(
                f"missing_required_field:{field}"
            )

    campaign_id = str(payload["campaign_id"])
    session_id = str(payload["session_id"])
    assert_campaign_id_not_exhausted_v1(campaign_id)
    assert_session_id_not_exhausted_v1(session_id)
    assert_session_id_not_terminal_used_v1(
        session_id,
        terminal_session_ids=terminal_session_ids,
    )

    if str(payload.get("repository_sha")) != expected_repository_sha:
        raise AdditionalEvidenceSessionPreregistrationContractError("repository_sha_mismatch")
    if str(payload.get("design_digest")) != expected_design_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError("design_digest_mismatch")
    if str(payload.get("runbook_digest")) != expected_runbook_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError("runbook_digest_mismatch")

    duration = int(payload["duration_seconds"])
    if duration < MINIMUM_SESSION_DURATION_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractError("duration_below_minimum_10860")

    post_span = int(
        payload.get(
            "post_first_produce_event_span_seconds",
            payload.get("minimum_post_first_produce_event_span_seconds", -1),
        )
    )
    if post_span < MINIMUM_POST_FIRST_PRODUCE_EVENT_SPAN_SECONDS:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "post_first_produce_span_below_minimum_7260"
        )

    cycles = int(payload["maximum_cycles_per_session"])
    if cycles < MINIMUM_MAXIMUM_CYCLES_PER_SESSION:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_cycles_below_minimum_182"
        )

    requests = int(payload["maximum_requests_per_session"])
    if requests < cycles:
        raise AdditionalEvidenceSessionPreregistrationContractError("requests_must_be_gte_cycles")

    if float(payload["minimum_interval_seconds"]) < float(MINIMUM_INTERVAL_SECONDS):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "minimum_interval_seconds_below_floor"
        )
    if int(payload["maximum_requests_per_cycle"]) != int(MAXIMUM_REQUESTS_PER_CYCLE):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "maximum_requests_per_cycle_mismatch"
        )

    buckets = tuple(int(x) for x in payload["target_age_buckets_seconds"])
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

    if payload.get("authorization_optional") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_optional_forbidden"
        )
    if payload.get("authorization_reusable") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_reusable_forbidden"
        )

    binding = payload.get("authorization_binding")
    if not isinstance(binding, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_binding_required"
        )
    validate_authorization_binding_v1(binding)
    if list(binding.get("session_ids") or []) != [session_id]:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_binding_session_mismatch"
        )

    _validate_forbidden_artificial_controls(payload)

    expected_digest = compute_candidate_preregistration_digest_v1(payload)
    stored_digest = str(payload.get("preregistration_digest") or "")
    if not stored_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "preregistration_digest_required"
        )
    if stored_digest != expected_digest:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "preregistration_digest_mismatch"
        )

    # This capability never authorizes creation/execution of the candidate.
    if payload.get("session_preregistration_creation_authorized") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "candidate_must_not_authorize_creation_in_contract_capability"
        )
    if payload.get("execution_authorized") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "candidate_must_not_authorize_execution"
        )
    if payload.get("network_authorized") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "candidate_must_not_authorize_network"
        )

    return {
        "valid": True,
        "session_id": session_id,
        "campaign_id": campaign_id,
        "preregistration_digest": stored_digest,
        "repository_sha": expected_repository_sha,
    }
