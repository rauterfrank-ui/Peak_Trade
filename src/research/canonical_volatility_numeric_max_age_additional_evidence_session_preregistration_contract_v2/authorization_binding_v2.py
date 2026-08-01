"""Authorization-binding schema for future per-session authorizations (v2).

Schema only. This capability never issues or consumes authorization.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    CAPABILITY_ID,
    REPOSITORY_BINDING_MODE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
)


def build_authorization_binding_schema_v2() -> dict[str, Any]:
    return {
        "schema": (
            "canonical_volatility_numeric_max_age_additional_evidence_"
            "session_authorization_binding/v2"
        ),
        "authorization_per_session_required": True,
        "single_use_authorization_required": True,
        "authorization_optional_forbidden": True,
        "authorization_reusable_forbidden": True,
        "s01_s02_authorization_reuse_forbidden": True,
        "maximum_session_count_per_authorization": 1,
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "required_fields": [
            "authorization_id",
            "campaign_id",
            "session_id",
            "code_baseline_sha",
            "critical_surface_manifest_digest",
            "preregistration_digest",
            "design_digest",
            "runbook_digest",
            "single_use",
            "authorization_single_use_per_session",
            "maximum_session_count",
            "session_ids",
            "repository_binding_mode",
        ],
        "required_field_values": {
            "single_use": True,
            "authorization_single_use_per_session": True,
            "maximum_session_count": 1,
            "repository_binding_mode": REPOSITORY_BINDING_MODE,
        },
        "notes": [
            "Exactly one session_id per authorization artifact.",
            "Consumption is single-use and session-bound.",
            "Existing s01/s02 campaign authorizations are not reusable.",
            "code_baseline_sha is an immutable ancestor baseline, not tip-of-main.",
            f"Owned by {CAPABILITY_ID} as schema only; issuance is a later step.",
        ],
    }


def build_candidate_authorization_binding_v2(
    *,
    campaign_id: str,
    session_id: str,
    code_baseline_sha: str,
    critical_surface_manifest_digest: str,
    design_digest: str,
    runbook_digest: str,
) -> dict[str, Any]:
    return {
        "authorization_required": True,
        "single_use_authorization_required": True,
        "authorization_issuance_authorized": False,
        "authorization_consumption_authorized": False,
        "maximum_session_count": 1,
        "session_ids": [session_id],
        "campaign_id": campaign_id,
        "code_baseline_sha": code_baseline_sha,
        "critical_surface_manifest_digest": critical_surface_manifest_digest,
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "design_digest": design_digest,
        "runbook_digest": runbook_digest,
        "s01_s02_authorization_reuse_forbidden": True,
    }


def validate_authorization_binding_v2(binding: Mapping[str, Any]) -> None:
    schema = build_authorization_binding_schema_v2()
    if binding.get("authorization_required") is not True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_required_must_be_true"
        )
    if binding.get("single_use_authorization_required") is not True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "single_use_authorization_required_must_be_true"
        )
    if binding.get("authorization_optional") is True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_optional_forbidden"
        )
    if binding.get("authorization_reusable") is True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_reusable_forbidden"
        )
    if int(binding.get("maximum_session_count", -1)) != 1:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_must_bind_exactly_one_session"
        )
    session_ids = binding.get("session_ids")
    if not isinstance(session_ids, list) or len(session_ids) != 1:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_session_ids_must_be_singleton"
        )
    if binding.get("repository_binding_mode") != REPOSITORY_BINDING_MODE:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_binding_mode_mismatch"
        )
    if schema["authorization_per_session_required"] is not True:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "authorization_binding_schema_drift"
        )
