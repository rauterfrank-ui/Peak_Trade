"""Authorization-binding schema for future per-session authorizations.

Schema only. This capability never issues or consumes authorization.
"""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.constants_v1 import (
    CAPABILITY_ID,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1.models_v1 import (
    AdditionalEvidenceSessionPreregistrationContractError,
)


def build_authorization_binding_schema_v1() -> dict[str, Any]:
    return {
        "schema": (
            "canonical_volatility_numeric_max_age_additional_evidence_"
            "session_authorization_binding/v1"
        ),
        "authorization_per_session_required": True,
        "single_use_authorization_required": True,
        "authorization_optional_forbidden": True,
        "authorization_reusable_forbidden": True,
        "s01_s02_authorization_reuse_forbidden": True,
        "maximum_session_count_per_authorization": 1,
        "required_fields": [
            "authorization_id",
            "campaign_id",
            "session_id",
            "repository_sha",
            "preregistration_digest",
            "design_digest",
            "runbook_digest",
            "single_use",
            "authorization_single_use_per_session",
            "maximum_session_count",
            "session_ids",
        ],
        "required_field_values": {
            "single_use": True,
            "authorization_single_use_per_session": True,
            "maximum_session_count": 1,
        },
        "notes": [
            "Exactly one session_id per authorization artifact.",
            "Consumption is single-use and session-bound.",
            "Existing s01/s02 campaign authorizations are not reusable.",
            f"Owned by {CAPABILITY_ID} as schema only; issuance is a later step.",
        ],
    }


def build_candidate_authorization_binding_v1(
    *,
    campaign_id: str,
    session_id: str,
    repository_sha: str,
    design_digest: str,
    runbook_digest: str,
) -> dict[str, Any]:
    """Planned binding descriptor embedded in a candidate (not an issued auth).

    Omits preregistration_digest so candidate digests remain acyclic; the
    candidate top-level preregistration_digest is the binding digest authority.
    """
    return {
        "authorization_required": True,
        "single_use_authorization_required": True,
        "authorization_issuance_authorized": False,
        "authorization_consumption_authorized": False,
        "maximum_session_count": 1,
        "session_ids": [session_id],
        "campaign_id": campaign_id,
        "repository_sha": repository_sha,
        "design_digest": design_digest,
        "runbook_digest": runbook_digest,
        "s01_s02_authorization_reuse_forbidden": True,
    }


def validate_authorization_binding_v1(binding: Mapping[str, Any]) -> None:
    schema = build_authorization_binding_schema_v1()
    if binding.get("authorization_required") is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_required_must_be_true"
        )
    if binding.get("single_use_authorization_required") is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "single_use_authorization_required_must_be_true"
        )
    if binding.get("authorization_optional") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_optional_forbidden"
        )
    if binding.get("authorization_reusable") is True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_reusable_forbidden"
        )
    if int(binding.get("maximum_session_count", -1)) != 1:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_must_bind_exactly_one_session"
        )
    session_ids = binding.get("session_ids")
    if not isinstance(session_ids, list) or len(session_ids) != 1:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_session_ids_must_be_singleton"
        )
    if schema["authorization_per_session_required"] is not True:
        raise AdditionalEvidenceSessionPreregistrationContractError(
            "authorization_binding_schema_drift"
        )
