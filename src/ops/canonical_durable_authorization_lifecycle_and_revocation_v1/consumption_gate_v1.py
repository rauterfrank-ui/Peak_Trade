"""Atomic consumption gate with mandatory revocation check under lifecycle lock."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    AuthorizationArtifactV2,
    parse_authorization_artifact_v2,
    validate_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    stamp_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.legacy_formal_authorization_v1 import (
    classify_legacy_formal_authorization_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.lifecycle_lock_v1 import (
    AuthorizationLifecycleLockV1,
    LifecycleLockError,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.revocation_registry_v1 import (
    assert_authorization_consumable_v1,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
    assert_transition_allowed_v2,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    sha256_text,
)


class ConsumptionGateError(ValueError):
    """Fail-closed consumption gate error."""


@dataclass
class ConsumptionGateResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    consumption_id: str = ""
    consumed_artifact_path: str = ""
    consumption_record_path: str = ""
    effective_state: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "consumption_id": self.consumption_id,
            "consumed_artifact_path": self.consumed_artifact_path,
            "consumption_record_path": self.consumption_record_path,
            "effective_state": self.effective_state,
            "notes": list(self.notes),
            "session_started": False,
        }


def _token_matches(artifact: AuthorizationArtifactV2, confirm_token: str) -> bool:
    fp = fingerprint_confirm_token(confirm_token)
    digest = f"sha256:{sha256_text(confirm_token)}"
    return fp == artifact.confirm_token_fingerprint and digest == artifact.confirm_token_digest


def classify_authorization_payload_v1(raw: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Return (kind, blockers). kind in {v2, legacy, unknown}."""
    if raw.get("schema") == "authorization_artifact_v2":
        return "v2", []
    legacy = classify_legacy_formal_authorization_v1(raw)
    if legacy.classification == "LEGACY_FORMAL_AUTHORIZATION_V1" or legacy.ok:
        return "legacy", ["LEGACY_AUTHORIZATION_NOT_CONSUMABLE"]
    return "unknown", ["AUTHORIZATION_SCHEMA_UNSUPPORTED"]


def consume_authorization_artifact_v2(
    *,
    evidence_root: Path,
    artifact_path: Path,
    confirm_token: str,
    expected_repository_sha: str,
    expected_preregistration_id: str,
    expected_preregistration_digest: str,
    expected_runbook_sha256: str,
    expected_capability: str = TARGET_RUNTIME_CAPABILITY,
    now_unix: Optional[float] = None,
    active_session_found: bool = False,
    resumable_session_found: bool = False,
    stale_session_lock_found: bool = False,
    config_digests_live: Optional[Mapping[str, str]] = None,
) -> ConsumptionGateResultV1:
    """Revocation-checked, lock-held, atomic single-use consumption for v2 artifacts.

    Does not start a session and does not open network transport.
    """
    notes = [
        "REVOCATION_CHECK_BEFORE_CONSUMPTION",
        "CONSUMPTION_ATOMIC",
        "CONSUMPTION_SINGLE_USE",
        "NO_SESSION_START",
    ]
    now = float(time.time() if now_unix is None else now_unix)
    blockers: list[str] = []

    if not artifact_path.is_file():
        return ConsumptionGateResultV1(ok=False, blockers=["AUTHORIZATION_ARTIFACT_MISSING"])

    import json

    raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    kind, kind_blockers = classify_authorization_payload_v1(raw)
    if kind != "v2":
        return ConsumptionGateResultV1(
            ok=False,
            blockers=kind_blockers or ["AUTHORIZATION_NOT_V2"],
            notes=notes + [f"CLASSIFIED:{kind}"],
        )

    try:
        artifact = parse_authorization_artifact_v2(raw)
    except Exception as exc:  # noqa: BLE001
        return ConsumptionGateResultV1(ok=False, blockers=[f"AUTHORIZATION_PARSE_FAILED:{exc}"])

    lock = AuthorizationLifecycleLockV1.for_evidence_root(
        evidence_root=evidence_root,
        authorization_id=artifact.authorization_id,
        owner="consume_authorization_artifact_v2",
    )
    try:
        lock.acquire()
    except LifecycleLockError as exc:
        return ConsumptionGateResultV1(ok=False, blockers=[str(exc)], notes=notes)

    try:
        lock.assert_held()
        # Re-read under lock (TOCTOU).
        raw2 = json.loads(artifact_path.read_text(encoding="utf-8"))
        artifact = parse_authorization_artifact_v2(raw2)

        config_match = True
        if config_digests_live is not None:
            config_match = dict(sorted(config_digests_live.items())) == dict(
                sorted(artifact.config_digests.items())
            )

        consumable = assert_authorization_consumable_v1(
            evidence_root=evidence_root,
            authorization_id=artifact.authorization_id,
            authorization_digest=artifact.integrity_digest,
            declared_state=artifact.state.value,
            preregistration_id=artifact.preregistration_id,
            preregistration_digest=artifact.preregistration_digest,
            capability=artifact.capability,
            repository_sha=artifact.repository_sha,
            expected_repository_sha=expected_repository_sha,
            expected_preregistration_id=expected_preregistration_id,
            expected_preregistration_digest=expected_preregistration_digest,
            expected_capability=expected_capability,
            config_digests_match=config_match,
            runbook_sha_match=artifact.runbook_sha256 == expected_runbook_sha256,
            active_session_found=active_session_found,
            resumable_session_found=resumable_session_found,
            stale_session_lock_found=stale_session_lock_found,
        )
        blockers.extend(consumable.blockers)

        validated = validate_authorization_artifact_v2(
            artifact,
            expected_repository_sha=expected_repository_sha,
            expected_runbook_sha256=expected_runbook_sha256,
            expected_preregistration_id=expected_preregistration_id,
            expected_preregistration_digest=expected_preregistration_digest,
            now_unix=now,
        )
        blockers.extend(validated.blockers)

        if not _token_matches(artifact, confirm_token):
            blockers.append("CONFIRM_TOKEN_MISMATCH")

        unique = sorted(set(blockers))
        if unique:
            return ConsumptionGateResultV1(
                ok=False,
                blockers=unique,
                effective_state=consumable.effective_state,
                notes=notes,
            )

        assert_transition_allowed_v2(
            from_state=artifact.state, to_state=AuthorizationStateV2.CONSUMED
        )
        consumption_id = f"cons_{secrets.token_hex(12)}"
        consumed_dict = artifact.to_dict()
        consumed_dict["state"] = AuthorizationStateV2.CONSUMED.value
        consumed_dict["state_version"] = int(artifact.state_version) + 1
        consumed_dict["consumed_at"] = now
        consumed_dict["consumption_id"] = consumption_id
        consumed_dict["session_start_authorized"] = False
        consumed_dict["notes"] = list(artifact.notes) + [
            "CONSUMED_CONTRACT_ONLY_NO_SESSION",
            "REVOCATION_CHECKED_BEFORE_CONSUMPTION",
        ]
        consumed_dict.pop("integrity_digest", None)
        consumed_dict.pop("digest_scope", None)
        stamped = stamp_integrity_digest(consumed_dict)
        consumed_artifact = parse_authorization_artifact_v2(stamped)

        # Atomic replace of artifact + append-only consumption record.
        record = {
            "schema": "authorization_consumption_record_v1",
            "schema_version": "v1",
            "consumption_id": consumption_id,
            "authorization_id": artifact.authorization_id,
            "authorization_digest_before": artifact.integrity_digest,
            "authorization_digest_after": consumed_artifact.integrity_digest,
            "preregistration_id": artifact.preregistration_id,
            "preregistration_digest": artifact.preregistration_digest,
            "repository_sha": artifact.repository_sha,
            "consumed_at": now,
            "confirm_token_fingerprint": artifact.confirm_token_fingerprint,
            "session_started": False,
            "notes": ["ATOMIC_CONSUMPTION", "NO_SESSION_START"],
        }
        record = stamp_integrity_digest(record)
        record_path = (
            Path(evidence_root) / "authorization_consumptions_v1" / f"{consumption_id}.json"
        )
        atomic_write_json(path=artifact_path, payload=consumed_artifact.to_dict())
        atomic_write_json(path=record_path, payload=record)

        return ConsumptionGateResultV1(
            ok=True,
            consumption_id=consumption_id,
            consumed_artifact_path=str(artifact_path),
            consumption_record_path=str(record_path),
            effective_state=AuthorizationStateV2.CONSUMED.value,
            notes=notes + ["CONSUMPTION_COMPLETE"],
        )
    finally:
        lock.release()
