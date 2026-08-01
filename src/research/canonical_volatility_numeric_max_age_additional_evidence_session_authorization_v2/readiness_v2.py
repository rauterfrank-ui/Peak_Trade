"""Authorization-issuance readiness for additional-evidence session auth v2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    DEFAULT_PREREGISTRATION_PATH,
    REQUIRED_DURATION_SECONDS,
    REQUIRED_INSTRUMENT,
    REQUIRED_NETWORK_SCOPE,
    REQUIRED_SESSION_SCOPE,
    REQUIRED_VENUE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.discovery_v2 import (
    assert_no_unconsumed_scope_conflict_v2,
    count_unconsumed_authorizations_for_scope_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    ARTIFACT_RELATIVE_PATH as PREREG_CONTRACT_PATH,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.contract_v2 import (
    count_active_v2_preregistrations,
    verify_additional_evidence_session_preregistration_contract_artifact_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.readiness_v2 import (
    evaluate_authorization_readiness_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    validate_additional_evidence_session_preregistration_candidate_v2,
)


def evaluate_additional_evidence_authorization_issuance_readiness_v2(
    *,
    repo_root: Path,
    execution_sha: str,
    preregistration_path: str | None = None,
    require_head_equals_origin_main: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root)
    if count_active_v2_preregistrations(repo_root=root) != 1:
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "active_v2_preregistration_count_invalid"
        )
    active_v1 = (
        root
        / "config/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_v1.json"
    )
    if active_v1.exists():
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "active_v1_preregistration_overlapping_scope"
        )

    preg_path = root / (preregistration_path or DEFAULT_PREREGISTRATION_PATH)
    if not preg_path.is_file():
        raise AdditionalEvidenceSessionAuthorizationV2Error("preregistration_missing")
    prereg = json.loads(preg_path.read_text(encoding="utf-8"))
    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        prereg,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )
    if validated["network_scope"] != REQUIRED_NETWORK_SCOPE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("network_scope_binding_mismatch")
    if int(prereg["duration_seconds"]) != REQUIRED_DURATION_SECONDS:
        raise AdditionalEvidenceSessionAuthorizationV2Error("duration_seconds_mismatch")
    if validated["venue"] != REQUIRED_VENUE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("venue_binding_mismatch")
    if validated["instrument"] != REQUIRED_INSTRUMENT:
        raise AdditionalEvidenceSessionAuthorizationV2Error("instrument_binding_mismatch")
    if validated["session_scope"] != REQUIRED_SESSION_SCOPE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("session_scope_binding_mismatch")

    contract = verify_additional_evidence_session_preregistration_contract_artifact_v2(
        repo_root=root
    )
    prereg_ready = evaluate_authorization_readiness_v2(
        prereg,
        execution_repository_sha=execution_sha,
        repo_root=root,
        require_head_equals_origin_main=require_head_equals_origin_main,
    )
    if not prereg_ready.get("ready"):
        raise AdditionalEvidenceSessionAuthorizationV2Error("preregistration_readiness_not_pass")

    assert_no_unconsumed_scope_conflict_v2(
        repo_root=root,
        preregistration_id=str(validated["session_id"]),
        session_scope=str(validated["session_scope"]),
        network_scope=str(validated["network_scope"]),
        instrument=str(validated["instrument"]),
    )
    unconsumed = count_unconsumed_authorizations_for_scope_v2(
        repo_root=root,
        preregistration_id=str(validated["session_id"]),
    )
    return {
        "ready": True,
        "authorization_issuance_readiness": "PASS",
        "preregistration_id": validated["session_id"],
        "preregistration_digest": validated["preregistration_digest"],
        "preregistration_contract_version": contract["capability_version"],
        "preregistration_contract_digest": contract["contract_digest"],
        "preregistration_contract_path": PREREG_CONTRACT_PATH,
        "code_baseline_sha": validated["code_baseline_sha"],
        "execution_sha": execution_sha,
        "critical_surface_digest": validated["critical_surface_manifest_digest"],
        "runbook_digest": str(prereg["runbook_digest"]),
        "venue": validated["venue"],
        "instrument": validated["instrument"],
        "network_scope": validated["network_scope"],
        "session_scope": validated["session_scope"],
        "duration_seconds": int(prereg["duration_seconds"]),
        "campaign_id": validated["campaign_id"],
        "unconsumed_authorization_count": unconsumed,
        "HEAD_EQUALS_ORIGIN_MAIN": prereg_ready.get("HEAD_EQUALS_ORIGIN_MAIN"),
        "preregistration_readiness": prereg_ready.get("authorization_readiness"),
    }
