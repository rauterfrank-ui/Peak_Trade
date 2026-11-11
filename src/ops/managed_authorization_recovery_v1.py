"""Verify replacement authority through the existing durable lifecycle and revocation registry."""

from pathlib import Path

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    load_authorization_artifact_dict_v2,
    parse_authorization_artifact_v2,
    validate_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_registry_v1 import (
    resolve_authorization_effective_state_v1,
)
from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    attest_filegate_owner_evidence_v1,
)


def attest_managed_replacement_authority_v1(
    *,
    stop,
    artifact_path: Path,
    evidence_root: Path,
    prior_authorization_id,
    repository_sha,
    runbook_sha256,
    preregistration_id,
    preregistration_digest,
    original_session_config_digest,
    now,
    key,
):
    """Observe a freshly issued original artifact without creating or consuming it."""
    if (
        stop["causes"] != ["R06"]
        or not evidence_root.is_absolute()
        or evidence_root.resolve() != evidence_root
        or artifact_path.resolve() != artifact_path
        or not artifact_path.is_relative_to(evidence_root)
        or not all(
            (
                prior_authorization_id,
                repository_sha,
                runbook_sha256,
                preregistration_id,
                preregistration_digest,
                original_session_config_digest,
            )
        )
    ):
        raise FilegateAuthorityError("FAULT_AUTHORIZATION_SCOPE_UNPROVEN")
    artifact = parse_authorization_artifact_v2(load_authorization_artifact_dict_v2(artifact_path))
    validity = validate_authorization_artifact_v2(
        artifact,
        expected_repository_sha=repository_sha,
        expected_runbook_sha256=runbook_sha256,
        expected_preregistration_id=preregistration_id,
        expected_preregistration_digest=preregistration_digest,
        now_unix=now,
    )
    state = resolve_authorization_effective_state_v1(
        evidence_root=evidence_root,
        authorization_id=artifact.authorization_id,
        authorization_digest=artifact.integrity_digest,
        declared_state=artifact.state.value,
    )
    if (
        not validity.ok
        or not state.ok
        or not state.consumable
        or artifact.authorization_id == prior_authorization_id
        or artifact.session_config_digest != original_session_config_digest
        or not stop["killed_at"] <= artifact.created_at <= now < artifact.expires_at
    ):
        raise FilegateAuthorityError("FAULT_REPLACEMENT_AUTHORIZATION_UNPROVEN")
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        stop=stop,
        evidence_sha256=artifact.integrity_digest,
        observed_at=now,
        expires_at=artifact.expires_at,
        key=key,
    )
