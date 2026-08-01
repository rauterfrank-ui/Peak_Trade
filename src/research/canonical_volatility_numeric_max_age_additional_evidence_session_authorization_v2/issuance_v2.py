"""Issuance service for additional-evidence session authorization v2.

Default and dry-run modes never open network or execute sessions.
Productive write requires explicit dry_run=False.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.artifact_v2 import (
    build_additional_evidence_session_authorization_v2,
    load_additional_evidence_session_authorization_v2,
    verify_additional_evidence_session_authorization_v2,
    write_additional_evidence_session_authorization_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.confirm_token_v2 import (
    bind_confirm_token_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_FILENAME,
    CONSUMPTION_LEDGER_FILENAME,
    DEFAULT_EVIDENCE_CAMPAIGN_ROOT,
    REVOCATION_LEDGER_FILENAME,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.discovery_v2 import (
    count_unconsumed_authorizations_for_scope_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2,
    AdditionalEvidenceSessionAuthorizationV2Error,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.readiness_v2 import (
    evaluate_additional_evidence_authorization_issuance_readiness_v2,
)


@dataclass
class IssuanceResultV2:
    ok: bool
    dry_run: bool
    blockers: list[str] = field(default_factory=list)
    authorization_path: str = ""
    authorization_id: str = ""
    authorization_digest: str = ""
    artifact: Optional[AdditionalEvidenceSessionAuthorizationV2] = None
    readiness: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "dry_run": self.dry_run,
            "blockers": list(self.blockers),
            "authorization_path": self.authorization_path,
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "artifact": None if self.artifact is None else self.artifact.to_dict(),
            "readiness": dict(self.readiness),
            "notes": list(self.notes),
        }


def _authorization_dir_for_campaign(*, repo_root: Path, campaign_id: str) -> Path:
    return Path(repo_root) / DEFAULT_EVIDENCE_CAMPAIGN_ROOT / campaign_id / "authorization"


def issue_additional_evidence_session_authorization_v2(
    *,
    repo_root: Path,
    execution_sha: str,
    confirm_token: str,
    dry_run: bool = True,
    issued_at: Optional[datetime] = None,
    previously_seen_fingerprints: frozenset[str] | None = None,
    require_head_equals_origin_main: bool = False,
) -> IssuanceResultV2:
    """Issue exactly one authorization, or simulate issuance when dry_run=True."""
    notes = [
        "ADDITIONAL_EVIDENCE_SESSION_AUTHORIZATION_V2_ISSUANCE",
        "SINGLE_USE",
        "NO_NETWORK",
        "NO_SESSION_EXECUTION",
        f"DRY_RUN={dry_run}",
    ]
    root = Path(repo_root)
    try:
        readiness = evaluate_additional_evidence_authorization_issuance_readiness_v2(
            repo_root=root,
            execution_sha=execution_sha,
            require_head_equals_origin_main=require_head_equals_origin_main,
        )
    except AdditionalEvidenceSessionAuthorizationV2Error as exc:
        return IssuanceResultV2(ok=False, dry_run=dry_run, blockers=[str(exc)], notes=notes)

    if previously_seen_fingerprints is not None:
        probe = bind_confirm_token_v2(
            confirm_token=confirm_token,
            authorization_id="probe",
            preregistration_id=str(readiness["preregistration_id"]),
            preregistration_digest=str(readiness["preregistration_digest"]),
            execution_sha=execution_sha,
        )
        if probe["confirm_token_fingerprint"] in previously_seen_fingerprints:
            return IssuanceResultV2(
                ok=False,
                dry_run=dry_run,
                blockers=["confirm_token_replay_rejected"],
                readiness=readiness,
                notes=notes,
            )

    auth_dir = _authorization_dir_for_campaign(
        repo_root=root, campaign_id=str(readiness["campaign_id"])
    )
    rev_rel = str(
        (
            Path(DEFAULT_EVIDENCE_CAMPAIGN_ROOT)
            / str(readiness["campaign_id"])
            / "authorization"
            / REVOCATION_LEDGER_FILENAME
        ).as_posix()
    )
    cons_rel = str(
        (
            Path(DEFAULT_EVIDENCE_CAMPAIGN_ROOT)
            / str(readiness["campaign_id"])
            / "authorization"
            / CONSUMPTION_LEDGER_FILENAME
        ).as_posix()
    )
    out_path = auth_dir / AUTHORIZATION_FILENAME

    try:
        artifact = build_additional_evidence_session_authorization_v2(
            preregistration_id=str(readiness["preregistration_id"]),
            preregistration_digest=str(readiness["preregistration_digest"]),
            preregistration_contract_version=str(readiness["preregistration_contract_version"]),
            preregistration_contract_digest=str(readiness["preregistration_contract_digest"]),
            code_baseline_sha=str(readiness["code_baseline_sha"]),
            execution_sha=execution_sha,
            critical_surface_digest=str(readiness["critical_surface_digest"]),
            runbook_digest=str(readiness["runbook_digest"]),
            venue=str(readiness["venue"]),
            instrument=str(readiness["instrument"]),
            network_scope=str(readiness["network_scope"]),
            session_scope=str(readiness["session_scope"]),
            duration_seconds=int(readiness["duration_seconds"]),
            campaign_id=str(readiness["campaign_id"]),
            confirm_token=confirm_token,
            revocation_ledger_path=rev_rel,
            consumption_ledger_path=cons_rel,
            issued_at=issued_at or datetime.now(timezone.utc),
        )
        verify_additional_evidence_session_authorization_v2(
            artifact,
            repo_root=root,
            expected_preregistration_id=str(readiness["preregistration_id"]),
            expected_preregistration_digest=str(readiness["preregistration_digest"]),
            expected_code_baseline_sha=str(readiness["code_baseline_sha"]),
            expected_execution_sha=execution_sha,
            expected_critical_surface_digest=str(readiness["critical_surface_digest"]),
            expected_runbook_digest=str(readiness["runbook_digest"]),
            expected_contract_version=str(readiness["preregistration_contract_version"]),
            expected_contract_digest=str(readiness["preregistration_contract_digest"]),
            require_unconsumed=True,
            require_unrevoked=True,
        )
    except AdditionalEvidenceSessionAuthorizationV2Error as exc:
        return IssuanceResultV2(
            ok=False,
            dry_run=dry_run,
            blockers=[str(exc)],
            readiness=readiness,
            notes=notes,
        )

    if dry_run:
        # Ensure dry-run never materializes an authorization artifact.
        if out_path.exists():
            # Existing file is a conflict, not created by this dry-run.
            pass
        return IssuanceResultV2(
            ok=True,
            dry_run=True,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.authorization_digest,
            artifact=artifact,
            readiness=readiness,
            notes=notes + ["DRY_RUN_NO_WRITE", "AUTHORIZATION_NOT_PERSISTED"],
        )

    try:
        written = write_additional_evidence_session_authorization_v2(
            output_path=out_path, artifact=artifact
        )
        reloaded = load_additional_evidence_session_authorization_v2(written)
        verify_additional_evidence_session_authorization_v2(
            reloaded,
            repo_root=root,
            expected_preregistration_id=str(readiness["preregistration_id"]),
            expected_preregistration_digest=str(readiness["preregistration_digest"]),
            expected_execution_sha=execution_sha,
            require_unconsumed=True,
            require_unrevoked=True,
        )
        count = count_unconsumed_authorizations_for_scope_v2(
            repo_root=root,
            preregistration_id=str(readiness["preregistration_id"]),
        )
        if count != 1:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                f"post_issuance_unconsumed_count_invalid:{count}"
            )
    except Exception as exc:  # noqa: BLE001
        if out_path.exists():
            try:
                # Fail-closed cleanup of partial write.
                out_path.unlink()
            except OSError:
                pass
        return IssuanceResultV2(
            ok=False,
            dry_run=False,
            blockers=[f"issuance_persist_failed:{exc}"],
            readiness=readiness,
            notes=notes + ["PARTIAL_ARTIFACT_CLEANUP_ATTEMPTED"],
        )

    return IssuanceResultV2(
        ok=True,
        dry_run=False,
        authorization_path=str(written),
        authorization_id=reloaded.authorization_id,
        authorization_digest=reloaded.authorization_digest,
        artifact=reloaded,
        readiness=readiness,
        notes=notes + ["AUTHORIZATION_WRITTEN_AND_RELOADED"],
    )
