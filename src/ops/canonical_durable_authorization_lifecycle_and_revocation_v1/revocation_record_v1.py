"""Durable append-only authorization revocation records."""

from __future__ import annotations

import secrets
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    append_only_create_json,
    canonical_json_dumps,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    REASON_CONFIRM_TOKEN_EXPOSED,
    REVOCATION_DIRNAME,
    REVOCATION_SCHEMA,
    REVOCATION_SCHEMA_VERSION,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    integrity_digest_v1,
    stamp_integrity_digest,
    verify_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)

_KNOWN_FIELDS = frozenset(
    {
        "schema",
        "schema_version",
        "revocation_id",
        "authorization_id",
        "authorization_digest",
        "preregistration_id",
        "preregistration_digest",
        "capability",
        "repository_sha",
        "reason_code",
        "reason_detail_redacted",
        "created_at",
        "operator_authority_reference",
        "previous_state",
        "resulting_state",
        "single_use_consumption_blocked",
        "replay_blocked",
        "integrity_digest",
        "digest_scope",
        "legacy_classification",
        "notes",
    }
)


class RevocationRecordError(ValueError):
    """Fail-closed revocation record error."""


@dataclass(frozen=True)
class AuthorizationRevocationRecordV1:
    schema: str
    schema_version: str
    revocation_id: str
    authorization_id: str
    authorization_digest: str
    preregistration_id: str
    preregistration_digest: str
    capability: str
    repository_sha: str
    reason_code: str
    reason_detail_redacted: str
    created_at: float
    operator_authority_reference: str
    previous_state: str
    resulting_state: str
    single_use_consumption_blocked: bool
    replay_blocked: bool
    integrity_digest: str = ""
    digest_scope: str = ""
    legacy_classification: str = ""
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        return payload


@dataclass
class RevocationWriteResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    path: str = ""
    record: Optional[AuthorizationRevocationRecordV1] = None
    idempotent_reuse: bool = False
    notes: list[str] = field(default_factory=list)


def parse_revocation_record_v1(raw: Mapping[str, Any]) -> AuthorizationRevocationRecordV1:
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise RevocationRecordError("REVOCATION_UNKNOWN_FIELDS:" + ",".join(unknown))
    if raw.get("schema") != REVOCATION_SCHEMA:
        raise RevocationRecordError(f"REVOCATION_SCHEMA_UNSUPPORTED:{raw.get('schema')}")
    if raw.get("schema_version") != REVOCATION_SCHEMA_VERSION:
        raise RevocationRecordError(
            f"REVOCATION_SCHEMA_VERSION_UNSUPPORTED:{raw.get('schema_version')}"
        )
    if raw.get("resulting_state") != AuthorizationStateV2.REVOKED.value:
        raise RevocationRecordError("REVOCATION_RESULTING_STATE_MUST_BE_REVOKED")
    if raw.get("single_use_consumption_blocked") is not True:
        raise RevocationRecordError("REVOCATION_MUST_BLOCK_CONSUMPTION")
    if raw.get("replay_blocked") is not True:
        raise RevocationRecordError("REVOCATION_MUST_BLOCK_REPLAY")
    notes_raw = raw.get("notes", ())
    notes = tuple(str(x) for x in notes_raw) if isinstance(notes_raw, (list, tuple)) else ()
    record = AuthorizationRevocationRecordV1(
        schema=str(raw["schema"]),
        schema_version=str(raw["schema_version"]),
        revocation_id=str(raw["revocation_id"]),
        authorization_id=str(raw["authorization_id"]),
        authorization_digest=str(raw["authorization_digest"]),
        preregistration_id=str(raw["preregistration_id"]),
        preregistration_digest=str(raw["preregistration_digest"]),
        capability=str(raw["capability"]),
        repository_sha=str(raw["repository_sha"]),
        reason_code=str(raw["reason_code"]),
        reason_detail_redacted=str(raw.get("reason_detail_redacted") or ""),
        created_at=float(raw["created_at"]),
        operator_authority_reference=str(raw.get("operator_authority_reference") or ""),
        previous_state=str(raw.get("previous_state") or ""),
        resulting_state=AuthorizationStateV2.REVOKED.value,
        single_use_consumption_blocked=True,
        replay_blocked=True,
        integrity_digest=str(raw.get("integrity_digest") or ""),
        digest_scope=str(raw.get("digest_scope") or ""),
        legacy_classification=str(raw.get("legacy_classification") or ""),
        notes=notes,
    )
    if record.integrity_digest:
        verify_integrity_digest(record.to_dict())
    return record


def build_revocation_record_dict_v1(
    *,
    authorization_id: str,
    authorization_digest: str,
    preregistration_id: str,
    preregistration_digest: str,
    repository_sha: str,
    reason_code: str,
    previous_state: str,
    capability: str = TARGET_RUNTIME_CAPABILITY,
    reason_detail_redacted: str = "",
    operator_authority_reference: str = "OPERATOR_EXPLICIT_TOKEN_EXPOSURE_REVOCATION",
    legacy_classification: str = "",
    now_unix: Optional[float] = None,
    revocation_id: Optional[str] = None,
) -> dict[str, Any]:
    now = float(time.time() if now_unix is None else now_unix)
    rid = revocation_id or f"rev_{secrets.token_hex(12)}"
    provisional = {
        "schema": REVOCATION_SCHEMA,
        "schema_version": REVOCATION_SCHEMA_VERSION,
        "revocation_id": rid,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "preregistration_id": preregistration_id,
        "preregistration_digest": preregistration_digest,
        "capability": capability,
        "repository_sha": repository_sha,
        "reason_code": reason_code,
        "reason_detail_redacted": reason_detail_redacted,
        "created_at": now,
        "operator_authority_reference": operator_authority_reference,
        "previous_state": previous_state,
        "resulting_state": AuthorizationStateV2.REVOKED.value,
        "single_use_consumption_blocked": True,
        "replay_blocked": True,
        "legacy_classification": legacy_classification,
        "notes": [
            "APPEND_ONLY_REVOCATION",
            "NO_PRIMARY_AUTHORIZATION_MUTATION",
            "NO_PLAINTEXT_TOKEN",
            "CONSUMPTION_BLOCKED",
        ],
    }
    return stamp_integrity_digest(provisional)


def revocation_store_dir(evidence_root: Path) -> Path:
    return Path(evidence_root) / REVOCATION_DIRNAME


def revocation_record_path(*, evidence_root: Path, revocation_id: str) -> Path:
    return revocation_store_dir(evidence_root) / f"{revocation_id}.json"


def _semantic_core(record: Mapping[str, Any]) -> str:
    """Identity for idempotent duplicate detection (exclude ids/timestamps/digests)."""
    keys = (
        "schema",
        "schema_version",
        "authorization_id",
        "authorization_digest",
        "preregistration_id",
        "preregistration_digest",
        "capability",
        "repository_sha",
        "reason_code",
        "resulting_state",
        "single_use_consumption_blocked",
        "replay_blocked",
        "legacy_classification",
    )
    core = {k: record.get(k) for k in keys}
    return canonical_json_dumps(core)


def write_revocation_record_v1(
    *,
    evidence_root: Path,
    record_dict: Mapping[str, Any],
    allow_idempotent_duplicate: bool = True,
) -> RevocationWriteResultV1:
    notes = ["DURABLE_APPEND_ONLY_REVOCATION_WRITE"]
    try:
        record = parse_revocation_record_v1(record_dict)
    except Exception as exc:  # noqa: BLE001
        return RevocationWriteResultV1(ok=False, blockers=[f"REVOCATION_PARSE_FAILED:{exc}"])

    store = revocation_store_dir(evidence_root)
    store.mkdir(parents=True, exist_ok=True)
    path = revocation_record_path(evidence_root=evidence_root, revocation_id=record.revocation_id)

    # Idempotent / conflict scan against existing records for same authorization_id.
    existing_for_auth: list[tuple[Path, dict[str, Any]]] = []
    for existing in sorted(store.glob("*.json")):
        try:
            import json

            raw = json.loads(existing.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return RevocationWriteResultV1(
                ok=False,
                blockers=[f"REVOCATION_STORE_CORRUPT:{existing.name}:{exc}"],
                notes=notes,
            )
        if not isinstance(raw, dict):
            return RevocationWriteResultV1(
                ok=False,
                blockers=[f"REVOCATION_STORE_CORRUPT_NOT_OBJECT:{existing.name}"],
                notes=notes,
            )
        try:
            parse_revocation_record_v1(raw)
            verify_integrity_digest(raw)
        except Exception as exc:  # noqa: BLE001
            return RevocationWriteResultV1(
                ok=False,
                blockers=[f"REVOCATION_STORE_INTEGRITY_FAIL:{existing.name}:{exc}"],
                notes=notes,
            )
        if raw.get("authorization_id") == record.authorization_id:
            existing_for_auth.append((existing, raw))

    new_core = _semantic_core(record.to_dict())
    for existing_path, raw in existing_for_auth:
        if raw.get("authorization_digest") != record.authorization_digest:
            return RevocationWriteResultV1(
                ok=False,
                blockers=["CONFLICTING_REVOCATION_DIGEST_FOR_AUTHORIZATION_ID"],
                notes=notes,
            )
        if _semantic_core(raw) == new_core:
            if allow_idempotent_duplicate:
                existing_record = parse_revocation_record_v1(raw)
                return RevocationWriteResultV1(
                    ok=True,
                    path=str(existing_path),
                    record=existing_record,
                    idempotent_reuse=True,
                    notes=notes + ["IDEMPOTENT_DUPLICATE_REVOCATION_REUSED"],
                )
            return RevocationWriteResultV1(
                ok=False,
                blockers=["DUPLICATE_IDENTICAL_REVOCATION_FORBIDDEN"],
                notes=notes,
            )
        if raw.get("reason_code") != record.reason_code:
            return RevocationWriteResultV1(
                ok=False,
                blockers=["CONFLICTING_REVOCATION_REASON_FOR_AUTHORIZATION_ID"],
                notes=notes,
            )

    try:
        append_only_create_json(path=path, payload=record.to_dict())
    except FileExistsError:
        # Same revocation_id collision
        import json

        existing = json.loads(path.read_text(encoding="utf-8"))
        if _semantic_core(existing) == new_core and allow_idempotent_duplicate:
            return RevocationWriteResultV1(
                ok=True,
                path=str(path),
                record=parse_revocation_record_v1(existing),
                idempotent_reuse=True,
                notes=notes + ["IDEMPOTENT_SAME_REVOCATION_ID"],
            )
        return RevocationWriteResultV1(
            ok=False,
            blockers=["REVOCATION_ID_COLLISION"],
            notes=notes,
        )
    except OSError as exc:
        return RevocationWriteResultV1(ok=False, blockers=[f"REVOCATION_WRITE_FAILED:{exc}"])

    return RevocationWriteResultV1(
        ok=True,
        path=str(path),
        record=record,
        notes=notes + ["REVOCATION_WRITTEN"],
    )


def issue_token_exposure_revocation_v1(
    *,
    evidence_root: Path,
    authorization_id: str,
    authorization_digest: str,
    preregistration_id: str,
    preregistration_digest: str,
    repository_sha: str,
    previous_state: str,
    capability: str = TARGET_RUNTIME_CAPABILITY,
    legacy_classification: str = "",
    now_unix: Optional[float] = None,
) -> RevocationWriteResultV1:
    payload = build_revocation_record_dict_v1(
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        repository_sha=repository_sha,
        reason_code=REASON_CONFIRM_TOKEN_EXPOSED,
        previous_state=previous_state,
        capability=capability,
        reason_detail_redacted=(
            "Confirm-token plaintext was disclosed outside the single operator delivery channel."
        ),
        legacy_classification=legacy_classification,
        now_unix=now_unix,
    )
    return write_revocation_record_v1(evidence_root=evidence_root, record_dict=payload)
