"""Exact S03 scope binding validation (fail-closed, closed-world)."""

from __future__ import annotations

from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    BOUND_CAMPAIGN_ID,
    BOUND_CONTRACT_DIGEST,
    BOUND_DURATION_SECONDS,
    BOUND_INSTRUMENT,
    BOUND_NETWORK_SCOPE,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_PREREGISTRATION_ID,
    BOUND_RUNBOOK_DIGEST_V1,
    BOUND_SESSION_ID,
    BOUND_SESSION_LABEL,
    BOUND_SESSION_SCOPE,
    BOUND_VENUE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
    S03ScopeBindingsV1,
)

REQUIRED_BINDING_FIELDS: tuple[str, ...] = (
    "campaign_id",
    "session_label",
    "session_id",
    "preregistration_id",
    "preregistration_digest",
    "contract_digest",
    "runbook_digest",
    "authorization_id",
    "authorization_digest",
    "repository_sha",
    "venue",
    "instrument",
    "network_scope",
    "session_scope",
    "duration_seconds",
)


def validate_s03_scope_bindings_v1(payload: Mapping[str, Any]) -> S03ScopeBindingsV1:
    unknown = sorted(set(payload.keys()) - set(REQUIRED_BINDING_FIELDS))
    if unknown:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"unknown_authority_fields:{','.join(unknown)}"
        )
    missing = [k for k in REQUIRED_BINDING_FIELDS if k not in payload]
    if missing:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            f"missing_required_fields:{','.join(missing)}"
        )

    checks = {
        "campaign_id": BOUND_CAMPAIGN_ID,
        "session_label": BOUND_SESSION_LABEL,
        "session_id": BOUND_SESSION_ID,
        "preregistration_id": BOUND_PREREGISTRATION_ID,
        "preregistration_digest": BOUND_PREREGISTRATION_DIGEST,
        "contract_digest": BOUND_CONTRACT_DIGEST,
        "runbook_digest": BOUND_RUNBOOK_DIGEST_V1,
        "venue": BOUND_VENUE,
        "instrument": BOUND_INSTRUMENT,
        "network_scope": BOUND_NETWORK_SCOPE,
        "session_scope": BOUND_SESSION_SCOPE,
    }
    for key, expected in checks.items():
        if payload[key] != expected:
            raise AdditionalEvidenceS03SessionExecutionOwnerError(f"{key}_mismatch")

    duration = int(payload["duration_seconds"])
    if duration != BOUND_DURATION_SECONDS:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("duration_seconds_mismatch")
    if duration > BOUND_DURATION_SECONDS:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("duration_exceeds_authorized_maximum")

    auth_id = str(payload["authorization_id"]).strip()
    auth_digest = str(payload["authorization_digest"]).strip()
    repo_sha = str(payload["repository_sha"]).strip()
    if not auth_id or not auth_digest or len(repo_sha) != 40:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("identity_binding_invalid")

    return S03ScopeBindingsV1(
        campaign_id=BOUND_CAMPAIGN_ID,
        session_label=BOUND_SESSION_LABEL,
        session_id=BOUND_SESSION_ID,
        preregistration_id=BOUND_PREREGISTRATION_ID,
        preregistration_digest=BOUND_PREREGISTRATION_DIGEST,
        contract_digest=BOUND_CONTRACT_DIGEST,
        runbook_digest=BOUND_RUNBOOK_DIGEST_V1,
        authorization_id=auth_id,
        authorization_digest=auth_digest,
        repository_sha=repo_sha,
        venue=BOUND_VENUE,
        instrument=BOUND_INSTRUMENT,
        network_scope=BOUND_NETWORK_SCOPE,
        session_scope=BOUND_SESSION_SCOPE,
        duration_seconds=BOUND_DURATION_SECONDS,
    )
