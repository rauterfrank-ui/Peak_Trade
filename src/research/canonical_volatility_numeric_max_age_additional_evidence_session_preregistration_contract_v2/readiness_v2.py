"""Authorization-/execution-readiness for additional evidence contract v2.

Strict separation of:

* HEAD_EQUALS_ORIGIN_MAIN — operational checkout gate only
* CODE_BASELINE_IS_ANCESTOR_OF_EXECUTION_SHA — required readiness check
* CRITICAL_SURFACE_DIGEST_MATCH — required readiness check

Tip-of-main equality is never required for readiness PASS.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    CANDIDATE_SCHEMA_VERSION,
    REPOSITORY_BINDING_MODE,
    V1_CANDIDATE_SCHEMA_VERSION,
    V1_CONTRACT_VERSION,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.critical_surface_v2 import (
    assert_critical_surface_digest_match_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.git_binding_v2 import (
    assert_baseline_not_after_artifact_creation_v2,
    assert_full_git_sha_v2,
    assert_is_ancestor_v2,
    head_equals_origin_main_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.validate_v2 import (
    reject_v1_for_new_authorization_readiness_v2,
    validate_additional_evidence_session_preregistration_candidate_v2,
)


def evaluate_authorization_readiness_v2(
    payload: Mapping[str, Any],
    *,
    execution_repository_sha: str,
    repo_root: Path,
    require_head_equals_origin_main: bool = False,
    path_content_overrides: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    """Evaluate new-authorization readiness for a v2 preregistration candidate.

    execution_repository_sha is a dynamic readiness input and must not be
    embedded into the candidate as a self-referential tip SHA.
    """
    if not isinstance(payload, Mapping):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("candidate_must_be_mapping")

    schema_version = payload.get("schema_version")
    if schema_version in {V1_CANDIDATE_SCHEMA_VERSION, V1_CONTRACT_VERSION, "v1"}:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "v1_new_authorization_readiness_unsupported"
        )
    if schema_version != CANDIDATE_SCHEMA_VERSION:
        reject_v1_for_new_authorization_readiness_v2(payload)
        raise AdditionalEvidenceSessionPreregistrationContractV2Error("unknown_contract_version")

    root = Path(repo_root)
    execution_sha = assert_full_git_sha_v2(
        execution_repository_sha, field="execution_repository_sha"
    )

    validated = validate_additional_evidence_session_preregistration_candidate_v2(
        payload,
        repo_root=root,
        verify_baseline_artifact_ordering=True,
    )

    code_baseline_sha = validated["code_baseline_sha"]
    artifact_creation_sha = validated["artifact_creation_sha"]

    assert_baseline_not_after_artifact_creation_v2(
        code_baseline_sha=code_baseline_sha,
        artifact_creation_sha=artifact_creation_sha,
        repo_root=root,
    )
    assert_is_ancestor_v2(
        ancestor_sha=code_baseline_sha,
        descendant_sha=execution_sha,
        repo_root=root,
    )
    ancestor_ok = True

    critical_ok_digest = assert_critical_surface_digest_match_v2(
        expected_digest=str(validated["critical_surface_manifest_digest"]),
        repo_root=root,
        at_sha=None if path_content_overrides is not None else execution_sha,
        path_content_overrides=path_content_overrides,
    )

    head_equals_main = head_equals_origin_main_v2(repo_root=root)
    if require_head_equals_origin_main and not head_equals_main:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "head_equals_origin_main_required_operational_gate_failed"
        )

    # Tip equality is informational / optional operational — never readiness authority.
    tip_equality_required = False
    tip_equality_satisfied = execution_sha == (
        # compare against origin/main only as info
        execution_sha if not head_equals_main else execution_sha
    )

    return {
        "ready": True,
        "authorization_readiness": "PASS",
        "repository_binding_mode": REPOSITORY_BINDING_MODE,
        "code_baseline_sha": code_baseline_sha,
        "artifact_creation_sha": artifact_creation_sha,
        "execution_repository_sha": execution_sha,
        "critical_surface_manifest_digest": critical_ok_digest,
        "CODE_BASELINE_IS_ANCESTOR_OF_EXECUTION_SHA": ancestor_ok,
        "CRITICAL_SURFACE_DIGEST_MATCH": True,
        "HEAD_EQUALS_ORIGIN_MAIN": head_equals_main,
        "TIP_OF_MAIN_EQUALITY_REQUIRED": tip_equality_required,
        "TIP_OF_MAIN_EQUALITY_SATISFIED": bool(head_equals_main),
        "SELF_COMMIT_SHA_EMBEDDING_REQUIRED": False,
        "V1_NEW_AUTHORIZATION_READINESS_ALLOWED": False,
        "session_id": validated["session_id"],
        "campaign_id": validated["campaign_id"],
        "preregistration_digest": validated["preregistration_digest"],
        "tip_equality_note": (
            "Tip-of-main equality is not required for authorization readiness; "
            "it remains an optional operational checkout gate only."
        ),
        "unused_tip_equality_satisfied_flag": tip_equality_satisfied,
    }
