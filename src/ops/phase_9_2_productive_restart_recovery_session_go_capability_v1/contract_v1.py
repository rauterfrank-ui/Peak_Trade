"""Fail-closed Session-GO authority contract parse/validate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUSES,
    ACTIVATION_STATUS_ACTIVE,
    CAPABILITY_ID,
    DEFAULT_MAX_SESSION_DURATION_SECONDS,
    KNOWN_FIELDS,
    REQUIRED_FIELDS,
    RESTART_RECOVERY_SCOPE,
    SCHEMA_VERSION,
    TARGET_ENTRYPOINT_ID,
    TARGET_ENTRYPOINT_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.models_v1 import (
    SessionGoAuthorityV1,
)


class SessionGoContractError(ValueError):
    """Fail-closed Session-GO contract error."""


def _req(raw: Mapping[str, Any], name: str) -> Any:
    if name not in raw:
        raise SessionGoContractError(f"SESSION_GO_FIELD_MISSING:{name}")
    return raw[name]


def load_session_go_dict_v1(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SessionGoContractError("SESSION_GO_ARTIFACT_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SessionGoContractError(f"SESSION_GO_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise SessionGoContractError("SESSION_GO_NOT_OBJECT")
    unknown = sorted(set(raw) - KNOWN_FIELDS)
    if unknown:
        raise SessionGoContractError("SESSION_GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    return raw


def parse_session_go_authority_v1(raw: Mapping[str, Any]) -> SessionGoAuthorityV1:
    unknown = sorted(set(raw) - KNOWN_FIELDS)
    if unknown:
        raise SessionGoContractError("SESSION_GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    for name in REQUIRED_FIELDS:
        _req(raw, name)

    schema = str(raw["schema_version"]).strip()
    if schema != SCHEMA_VERSION:
        raise SessionGoContractError(f"SESSION_GO_SCHEMA_MISMATCH:{schema}")

    capability_id = str(raw["capability_id"]).strip()
    if capability_id != CAPABILITY_ID:
        raise SessionGoContractError(f"SESSION_GO_CAPABILITY_MISMATCH:{capability_id}")

    activation_status = str(raw["activation_status"]).strip()
    if activation_status not in ACTIVATION_STATUSES:
        raise SessionGoContractError(f"SESSION_GO_ACTIVATION_STATUS_INVALID:{activation_status}")

    max_duration = int(raw["max_session_duration_seconds"])
    if max_duration <= 0 or max_duration > DEFAULT_MAX_SESSION_DURATION_SECONDS:
        raise SessionGoContractError(f"SESSION_GO_MAX_DURATION_INVALID:{max_duration}")

    if not bool(raw["public_md_only"]):
        raise SessionGoContractError("SESSION_GO_PUBLIC_MD_ONLY_REQUIRED")
    if not bool(raw["http_get_only"]):
        raise SessionGoContractError("SESSION_GO_HTTP_GET_ONLY_REQUIRED")
    if str(raw["restart_recovery_scope"]).strip() != RESTART_RECOVERY_SCOPE:
        raise SessionGoContractError("SESSION_GO_RESTART_SCOPE_MISMATCH")
    if not bool(raw["owner_go_required"]):
        raise SessionGoContractError("SESSION_GO_OWNER_GO_REQUIRED_MUST_BE_TRUE")
    if not bool(raw["owner_session_go_required"]):
        raise SessionGoContractError("SESSION_GO_OWNER_SESSION_GO_REQUIRED_MUST_BE_TRUE")
    if not bool(raw["single_use_authorization_required"]):
        raise SessionGoContractError("SESSION_GO_SINGLE_USE_AUTH_REQUIRED_MUST_BE_TRUE")
    if not bool(raw["confirm_token_required"]):
        raise SessionGoContractError("SESSION_GO_CONFIRM_TOKEN_REQUIRED_MUST_BE_TRUE")

    issued_at = float(raw["issued_at"])
    not_before = float(raw["not_before"])
    expires_at = float(raw["expires_at"])
    if not_before < issued_at:
        raise SessionGoContractError("SESSION_GO_NOT_BEFORE_BEFORE_ISSUED")
    if expires_at <= not_before:
        raise SessionGoContractError("SESSION_GO_EXPIRES_NOT_AFTER_NOT_BEFORE")

    notes_raw = raw.get("notes", ())
    notes = tuple(str(x) for x in notes_raw) if isinstance(notes_raw, (list, tuple)) else ()

    provisional = {
        "schema_version": schema,
        "capability_id": capability_id,
        "session_go_id": str(raw["session_go_id"]).strip(),
        "session_id": str(raw["session_id"]).strip(),
        "expected_repository_sha": str(raw["expected_repository_sha"]).strip(),
        "expected_config_digest": str(raw["expected_config_digest"]).strip(),
        "entrypoint_id": str(raw["entrypoint_id"]).strip(),
        "entrypoint_path": str(raw["entrypoint_path"]).strip(),
        "public_md_only": True,
        "http_get_only": True,
        "max_session_duration_seconds": max_duration,
        "restart_recovery_scope": RESTART_RECOVERY_SCOPE,
        "issued_at": issued_at,
        "not_before": not_before,
        "expires_at": expires_at,
        "activation_status": activation_status,
        "owner_go_required": True,
        "owner_session_go_required": True,
        "single_use_authorization_required": True,
        "confirm_token_required": True,
        "network_session_execution_authorized_by_this_go": bool(
            raw["network_session_execution_authorized_by_this_go"]
        ),
        "fixture_non_authoritative": bool(raw["fixture_non_authoritative"]),
        "notes": list(notes),
    }
    digest = sha256_canonical_v1(provisional)
    provided = str(raw.get("session_go_digest") or "").strip()
    if provided and provided != digest:
        raise SessionGoContractError("SESSION_GO_DIGEST_MISMATCH")

    return SessionGoAuthorityV1(
        schema_version=schema,
        capability_id=capability_id,
        session_go_id=provisional["session_go_id"],
        session_id=provisional["session_id"],
        expected_repository_sha=provisional["expected_repository_sha"],
        expected_config_digest=provisional["expected_config_digest"],
        entrypoint_id=provisional["entrypoint_id"],
        entrypoint_path=provisional["entrypoint_path"],
        public_md_only=True,
        http_get_only=True,
        max_session_duration_seconds=max_duration,
        restart_recovery_scope=RESTART_RECOVERY_SCOPE,
        issued_at=issued_at,
        not_before=not_before,
        expires_at=expires_at,
        activation_status=activation_status,
        owner_go_required=True,
        owner_session_go_required=True,
        single_use_authorization_required=True,
        confirm_token_required=True,
        network_session_execution_authorized_by_this_go=bool(
            raw["network_session_execution_authorized_by_this_go"]
        ),
        fixture_non_authoritative=bool(raw["fixture_non_authoritative"]),
        session_go_digest=digest,
        notes=notes,
    )


def build_session_go_authority_v1(
    *,
    session_go_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    issued_at: float,
    not_before: float,
    expires_at: float,
    activation_status: str = ACTIVATION_STATUS_ACTIVE,
    session_id: str = TARGET_SESSION_ID,
    entrypoint_id: str = TARGET_ENTRYPOINT_ID,
    entrypoint_path: str = TARGET_ENTRYPOINT_PATH,
    max_session_duration_seconds: int = DEFAULT_MAX_SESSION_DURATION_SECONDS,
    network_session_execution_authorized_by_this_go: bool = True,
    fixture_non_authoritative: bool = False,
    notes: tuple[str, ...] = (),
) -> SessionGoAuthorityV1:
    return parse_session_go_authority_v1(
        {
            "schema_version": SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "session_go_id": session_go_id,
            "session_id": session_id,
            "expected_repository_sha": expected_repository_sha,
            "expected_config_digest": expected_config_digest,
            "entrypoint_id": entrypoint_id,
            "entrypoint_path": entrypoint_path,
            "public_md_only": True,
            "http_get_only": True,
            "max_session_duration_seconds": max_session_duration_seconds,
            "restart_recovery_scope": RESTART_RECOVERY_SCOPE,
            "issued_at": issued_at,
            "not_before": not_before,
            "expires_at": expires_at,
            "activation_status": activation_status,
            "owner_go_required": True,
            "owner_session_go_required": True,
            "single_use_authorization_required": True,
            "confirm_token_required": True,
            "network_session_execution_authorized_by_this_go": (
                network_session_execution_authorized_by_this_go
            ),
            "fixture_non_authoritative": fixture_non_authoritative,
            "notes": list(notes),
        }
    )


def load_session_go_authority_v1(path: Path) -> SessionGoAuthorityV1:
    return parse_session_go_authority_v1(load_session_go_dict_v1(path))
