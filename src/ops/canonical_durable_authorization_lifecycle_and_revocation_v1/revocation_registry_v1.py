"""Revocation registry lookup and consumability assertions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    LEGACY_FORMAL_AUTHORIZATION_CLASS,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    verify_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_record_v1 import (
    parse_revocation_record_v1,
    revocation_store_dir,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)


class RevocationRegistryError(ValueError):
    """Fail-closed registry error."""


@dataclass
class EffectiveAuthorizationStateV1:
    ok: bool
    effective_state: str
    blockers: list[str] = field(default_factory=list)
    revoked: bool = False
    invalidated: bool = False
    consumable: bool = False
    revocation_paths: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "effective_state": self.effective_state,
            "blockers": list(self.blockers),
            "revoked": self.revoked,
            "invalidated": self.invalidated,
            "consumable": self.consumable,
            "revocation_paths": list(self.revocation_paths),
            "notes": list(self.notes),
        }


def load_revocation_records_for_authorization_v1(
    *,
    evidence_root: Path,
    authorization_id: str,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Return (records, paths, blockers)."""
    store = revocation_store_dir(evidence_root)
    if not store.is_dir():
        return [], [], []
    records: list[dict[str, Any]] = []
    paths: list[str] = []
    blockers: list[str] = []
    for path in sorted(store.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"REVOCATION_RECORD_DAMAGED:{path.name}:{exc}")
            continue
        if not isinstance(raw, dict):
            blockers.append(f"REVOCATION_RECORD_NOT_OBJECT:{path.name}")
            continue
        try:
            parse_revocation_record_v1(raw)
            verify_integrity_digest(raw)
        except Exception as exc:  # noqa: BLE001
            blockers.append(f"REVOCATION_RECORD_INTEGRITY_FAIL:{path.name}:{exc}")
            continue
        if raw.get("authorization_id") == authorization_id:
            records.append(raw)
            paths.append(str(path))
    return records, paths, blockers


def is_authorization_revoked_v1(
    *,
    evidence_root: Path,
    authorization_id: str,
    authorization_digest: str,
) -> EffectiveAuthorizationStateV1:
    records, paths, blockers = load_revocation_records_for_authorization_v1(
        evidence_root=evidence_root, authorization_id=authorization_id
    )
    if blockers:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=blockers,
            consumable=False,
            notes=["FAIL_CLOSED_DAMAGED_OR_INVALID_REVOCATION_STORE"],
        )
    if not records:
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
            revoked=False,
            consumable=True,
            notes=["NO_REVOCATION_RECORDS"],
        )
    digests = {str(r.get("authorization_digest")) for r in records}
    if authorization_digest not in digests:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=["REVOCATION_DIGEST_MISMATCH"],
            revoked=True,
            consumable=False,
            revocation_paths=paths,
        )
    if len(digests) > 1:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=["CONFLICTING_REVOCATION_RECORDS"],
            revoked=True,
            consumable=False,
            revocation_paths=paths,
        )
    reasons = {str(r.get("reason_code")) for r in records}
    if len(reasons) > 1:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=["CONFLICTING_REVOCATION_REASON_CODES"],
            revoked=True,
            consumable=False,
            revocation_paths=paths,
        )
    return EffectiveAuthorizationStateV1(
        ok=True,
        effective_state=AuthorizationStateV2.REVOKED.value,
        revoked=True,
        consumable=False,
        revocation_paths=paths,
        notes=["REVOCATION_RECORD_PRESENT"],
    )


def resolve_authorization_effective_state_v1(
    *,
    evidence_root: Path,
    authorization_id: str,
    authorization_digest: str,
    declared_state: str,
    legacy_classification: str = "",
) -> EffectiveAuthorizationStateV1:
    if legacy_classification == LEGACY_FORMAL_AUTHORIZATION_CLASS:
        # Legacy never consumable; revocation still elevates effective state.
        rev = is_authorization_revoked_v1(
            evidence_root=evidence_root,
            authorization_id=authorization_id,
            authorization_digest=authorization_digest,
        )
        if rev.blockers:
            return EffectiveAuthorizationStateV1(
                ok=False,
                effective_state="UNKNOWN",
                blockers=list(rev.blockers) + ["LEGACY_NOT_CONSUMABLE"],
                consumable=False,
                revocation_paths=list(rev.revocation_paths),
            )
        if rev.revoked:
            return EffectiveAuthorizationStateV1(
                ok=True,
                effective_state=AuthorizationStateV2.REVOKED.value,
                revoked=True,
                consumable=False,
                revocation_paths=list(rev.revocation_paths),
                notes=["LEGACY_REVOKED"],
            )
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state="LEGACY_NOT_CONSUMABLE",
            consumable=False,
            notes=["LEGACY_FORMAL_AUTHORIZATION_V1_NEVER_CONSUMABLE"],
        )

    try:
        declared = AuthorizationStateV2(str(declared_state))
    except ValueError:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=[f"UNKNOWN_AUTHORIZATION_STATE:{declared_state}"],
            consumable=False,
        )

    rev = is_authorization_revoked_v1(
        evidence_root=evidence_root,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
    )
    if rev.blockers:
        return EffectiveAuthorizationStateV1(
            ok=False,
            effective_state="UNKNOWN",
            blockers=list(rev.blockers),
            consumable=False,
            revocation_paths=list(rev.revocation_paths),
        )
    if rev.revoked:
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state=AuthorizationStateV2.REVOKED.value,
            revoked=True,
            consumable=False,
            revocation_paths=list(rev.revocation_paths),
            notes=["REVOCATION_OVERRIDES_DECLARED_STATE"],
        )
    if declared is AuthorizationStateV2.INVALIDATED:
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state=AuthorizationStateV2.INVALIDATED.value,
            invalidated=True,
            consumable=False,
        )
    if declared is AuthorizationStateV2.CONSUMED:
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state=AuthorizationStateV2.CONSUMED.value,
            consumable=False,
            notes=["ALREADY_CONSUMED"],
        )
    if declared is AuthorizationStateV2.CREATED_UNCONSUMED:
        return EffectiveAuthorizationStateV1(
            ok=True,
            effective_state=AuthorizationStateV2.CREATED_UNCONSUMED.value,
            consumable=True,
        )
    return EffectiveAuthorizationStateV1(
        ok=False,
        effective_state="UNKNOWN",
        blockers=[f"UNHANDLED_STATE:{declared.value}"],
        consumable=False,
    )


def assert_authorization_consumable_v1(
    *,
    evidence_root: Path,
    authorization_id: str,
    authorization_digest: str,
    declared_state: str,
    preregistration_id: str,
    preregistration_digest: str,
    capability: str,
    repository_sha: str,
    expected_repository_sha: str,
    expected_preregistration_id: str,
    expected_preregistration_digest: str,
    expected_capability: str = TARGET_RUNTIME_CAPABILITY,
    legacy_classification: str = "",
    config_digests_match: bool = True,
    runbook_sha_match: bool = True,
    active_session_found: bool = False,
    resumable_session_found: bool = False,
    stale_session_lock_found: bool = False,
) -> EffectiveAuthorizationStateV1:
    blockers: list[str] = []
    if repository_sha != expected_repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if preregistration_id != expected_preregistration_id:
        blockers.append("PREREGISTRATION_ID_MISMATCH")
    if preregistration_digest != expected_preregistration_digest:
        blockers.append("PREREGISTRATION_DIGEST_MISMATCH")
    if capability != expected_capability:
        blockers.append("CAPABILITY_MISMATCH")
    if not config_digests_match:
        blockers.append("CONFIG_DRIFT")
    if not runbook_sha_match:
        blockers.append("RUNBOOK_SHA_MISMATCH")
    if active_session_found:
        blockers.append("ACTIVE_SESSION_FOUND")
    if resumable_session_found:
        blockers.append("RESUMABLE_SESSION_FOUND")
    if stale_session_lock_found:
        blockers.append("STALE_SESSION_LOCK_FOUND")
    if legacy_classification == LEGACY_FORMAL_AUTHORIZATION_CLASS:
        blockers.append("LEGACY_AUTHORIZATION_NOT_CONSUMABLE")

    effective = resolve_authorization_effective_state_v1(
        evidence_root=evidence_root,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        declared_state=declared_state,
        legacy_classification=legacy_classification,
    )
    blockers.extend(effective.blockers)
    if effective.revoked:
        blockers.append("AUTHORIZATION_REVOKED")
    if effective.invalidated:
        blockers.append("AUTHORIZATION_INVALIDATED")
    if not effective.consumable:
        blockers.append("AUTHORIZATION_NOT_CONSUMABLE")
    unique = sorted(set(blockers))
    return EffectiveAuthorizationStateV1(
        ok=not unique and effective.consumable,
        effective_state=effective.effective_state,
        blockers=unique,
        revoked=effective.revoked,
        invalidated=effective.invalidated,
        consumable=not unique and effective.consumable,
        revocation_paths=list(effective.revocation_paths),
        notes=list(effective.notes),
    )
