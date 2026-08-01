"""Discovery of active unconsumed additional-evidence authorizations v2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    load_additional_evidence_session_authorization_v2,
    parse_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_FILENAME,
    AUTHORIZATION_VERSION,
    CONSUMPTION_STATE_UNCONSUMED,
    DEFAULT_EVIDENCE_CAMPAIGN_ROOT,
    REVOCATION_STATE_ACTIVE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.ledgers_v2 import (
    authorization_is_consumed_v2,
    authorization_is_revoked_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2,
    AdditionalEvidenceSessionAuthorizationV2Error,
)


def discover_unconsumed_additional_evidence_authorizations_v2(
    *,
    repo_root: Path,
    evidence_campaign_root: str | None = None,
    preregistration_id: str | None = None,
    session_scope: str | None = None,
    network_scope: str | None = None,
    instrument: str | None = None,
) -> list[AdditionalEvidenceSessionAuthorizationV2]:
    root = Path(repo_root)
    campaign_root = root / (evidence_campaign_root or DEFAULT_EVIDENCE_CAMPAIGN_ROOT)
    if not campaign_root.exists():
        return []
    found: list[AdditionalEvidenceSessionAuthorizationV2] = []
    for path in sorted(campaign_root.rglob(AUTHORIZATION_FILENAME)):
        try:
            artifact = load_additional_evidence_session_authorization_v2(path)
        except AdditionalEvidenceSessionAuthorizationV2Error:
            continue
        if artifact.authorization_version != AUTHORIZATION_VERSION:
            continue
        if artifact.consumption_state != CONSUMPTION_STATE_UNCONSUMED:
            continue
        if artifact.revocation_state != REVOCATION_STATE_ACTIVE:
            continue
        rev_path = root / artifact.revocation_ledger_path
        cons_path = root / artifact.consumption_ledger_path
        if authorization_is_revoked_v2(
            revocation_ledger_path=rev_path, authorization_id=artifact.authorization_id
        ):
            continue
        if authorization_is_consumed_v2(
            consumption_ledger_path=cons_path, authorization_id=artifact.authorization_id
        ):
            continue
        if preregistration_id is not None and artifact.preregistration_id != preregistration_id:
            continue
        if session_scope is not None and artifact.session_scope != session_scope:
            continue
        if network_scope is not None and artifact.network_scope != network_scope:
            continue
        if instrument is not None and artifact.instrument != instrument:
            continue
        found.append(artifact)
    return found


def assert_no_unconsumed_scope_conflict_v2(
    *,
    repo_root: Path,
    preregistration_id: str,
    session_scope: str,
    network_scope: str,
    instrument: str,
) -> None:
    existing = discover_unconsumed_additional_evidence_authorizations_v2(
        repo_root=repo_root,
        preregistration_id=preregistration_id,
        session_scope=session_scope,
        network_scope=network_scope,
        instrument=instrument,
    )
    if existing:
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "duplicate_unconsumed_authorization_for_scope"
        )


def count_unconsumed_authorizations_for_scope_v2(
    *,
    repo_root: Path,
    preregistration_id: str,
) -> int:
    return len(
        discover_unconsumed_additional_evidence_authorizations_v2(
            repo_root=repo_root,
            preregistration_id=preregistration_id,
        )
    )


def reject_foreign_discovery_payload_v2(payload: dict[str, Any]) -> None:
    parse_additional_evidence_session_authorization_v2(payload)
