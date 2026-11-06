"""Step-5 Session-GO authority contract and gate (owned by this binding capability)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_INACTIVE,
    ACTIVATION_STATUS_REVOKED,
    ACTIVATION_STATUSES,
    AUTHORITY_OWNER,
    CAPABILITY_ID,
    DEFAULT_WALLCLOCK_DURATION_SECONDS,
    MAX_WALLCLOCK_DURATION_SECONDS,
    MIN_WALLCLOCK_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_ID,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SESSION_GO_KNOWN_FIELDS,
    SESSION_GO_REQUIRED_FIELDS,
    SESSION_GO_SCHEMA_VERSION,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.models_v1 import (
    SessionGoAuthorityV1,
)
from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (
    validate_planned_duration_v1,
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
    unknown = sorted(set(raw) - SESSION_GO_KNOWN_FIELDS)
    if unknown:
        raise SessionGoContractError("SESSION_GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    return raw


def parse_session_go_authority_v1(raw: Mapping[str, Any]) -> SessionGoAuthorityV1:
    unknown = sorted(set(raw) - SESSION_GO_KNOWN_FIELDS)
    if unknown:
        raise SessionGoContractError("SESSION_GO_UNKNOWN_FIELDS:" + ",".join(unknown))
    for name in SESSION_GO_REQUIRED_FIELDS:
        _req(raw, name)

    schema = str(raw["schema_version"]).strip()
    if schema != SESSION_GO_SCHEMA_VERSION:
        raise SessionGoContractError(f"SESSION_GO_SCHEMA_MISMATCH:{schema}")

    capability_id = str(raw["capability_id"]).strip()
    if capability_id != CAPABILITY_ID:
        raise SessionGoContractError(f"SESSION_GO_CAPABILITY_MISMATCH:{capability_id}")

    activation_status = str(raw["activation_status"]).strip()
    if activation_status not in ACTIVATION_STATUSES:
        raise SessionGoContractError(f"SESSION_GO_ACTIVATION_STATUS_INVALID:{activation_status}")

    min_duration = int(raw["min_session_duration_seconds"])
    max_duration = int(raw["max_session_duration_seconds"])
    planned = int(raw["planned_session_duration_seconds"])
    if min_duration != MIN_WALLCLOCK_DURATION_SECONDS:
        raise SessionGoContractError(f"SESSION_GO_MIN_DURATION_INVALID:{min_duration}")
    if max_duration != MAX_WALLCLOCK_DURATION_SECONDS:
        raise SessionGoContractError(f"SESSION_GO_MAX_DURATION_INVALID:{max_duration}")
    duration_gaps = validate_planned_duration_v1(planned)
    if duration_gaps:
        raise SessionGoContractError(
            "SESSION_GO_PLANNED_DURATION_INVALID:" + ",".join(duration_gaps)
        )
    if not (min_duration <= planned <= max_duration):
        raise SessionGoContractError("SESSION_GO_PLANNED_DURATION_OUT_OF_BOUNDS")

    if not bool(raw["public_md_only"]):
        raise SessionGoContractError("SESSION_GO_PUBLIC_MD_ONLY_REQUIRED")
    if not bool(raw["http_get_only"]):
        raise SessionGoContractError("SESSION_GO_HTTP_GET_ONLY_REQUIRED")
    if str(raw["session_scope"]).strip() != SESSION_SCOPE:
        raise SessionGoContractError("SESSION_GO_SESSION_SCOPE_MISMATCH")
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
        "min_session_duration_seconds": min_duration,
        "planned_session_duration_seconds": planned,
        "session_scope": SESSION_SCOPE,
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
        min_session_duration_seconds=min_duration,
        planned_session_duration_seconds=planned,
        session_scope=SESSION_SCOPE,
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
    entrypoint_id: str = PRODUCTIVE_ENTRYPOINT_ID,
    entrypoint_path: str = PRODUCTIVE_ENTRYPOINT_PATH,
    min_session_duration_seconds: int = MIN_WALLCLOCK_DURATION_SECONDS,
    max_session_duration_seconds: int = MAX_WALLCLOCK_DURATION_SECONDS,
    planned_session_duration_seconds: int = DEFAULT_WALLCLOCK_DURATION_SECONDS,
    network_session_execution_authorized_by_this_go: bool = True,
    fixture_non_authoritative: bool = False,
    notes: tuple[str, ...] = (),
) -> SessionGoAuthorityV1:
    return parse_session_go_authority_v1(
        {
            "schema_version": SESSION_GO_SCHEMA_VERSION,
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
            "min_session_duration_seconds": min_session_duration_seconds,
            "planned_session_duration_seconds": planned_session_duration_seconds,
            "session_scope": SESSION_SCOPE,
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


def evaluate_session_go_gate_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_session_id: str = TARGET_SESSION_ID,
    expected_entrypoint_id: str = PRODUCTIVE_ENTRYPOINT_ID,
    expected_entrypoint_path: str = PRODUCTIVE_ENTRYPOINT_PATH,
    now_unix: float,
    owner_go: bool,
    owner_session_go: bool,
    session_go_path: Path | None = None,
    session_go_payload: Mapping[str, Any] | SessionGoAuthorityV1 | None = None,
    authorization_present: bool = False,
    confirm_token_present: bool = False,
) -> dict[str, Any]:
    notes = [
        f"SESSION_GO_AUTHORITY_OWNER={AUTHORITY_OWNER}",
        "SESSION_GO_EVALUATION_BEFORE_AUTHORIZATION=true",
        "SESSION_GO_EVALUATION_BEFORE_LOCK=true",
        "SESSION_GO_EVALUATION_BEFORE_NETWORK=true",
        "SESSION_GO_EVALUATION_BEFORE_SESSION_START=true",
        "NO_SIDE_EFFECTS_IN_SESSION_GO_GATE=true",
        "STEP4_AUTHORIZATION_REUSE_FORBIDDEN=true",
        "STEP4_CONFIRM_TOKEN_REUSE_FORBIDDEN=true",
    ]
    blockers: list[str] = []
    authority: Optional[SessionGoAuthorityV1] = None

    if session_go_path is None and session_go_payload is None:
        return {
            "ok": False,
            "blockers": ["SESSION_GO_MISSING"],
            "notes": notes + ["MISSING_SESSION_GO_FAILS_CLOSED=true"],
            "session_go_authority_satisfied": False,
            "productive_session_execution_permitted": False,
            "network_may_proceed": False,
            "authorization_may_proceed": False,
            "authority": None,
        }

    try:
        if session_go_payload is not None:
            if isinstance(session_go_payload, SessionGoAuthorityV1):
                authority = session_go_payload
            else:
                authority = parse_session_go_authority_v1(session_go_payload)
        else:
            assert session_go_path is not None
            authority = load_session_go_authority_v1(session_go_path)
    except SessionGoContractError as exc:
        return {
            "ok": False,
            "blockers": [str(exc)],
            "notes": notes + ["SESSION_GO_PARSE_OR_SCHEMA_FAIL_CLOSED=true"],
            "session_go_authority_satisfied": False,
            "productive_session_execution_permitted": False,
            "network_may_proceed": False,
            "authorization_may_proceed": False,
            "authority": None,
        }

    if authority.fixture_non_authoritative:
        blockers.append("SESSION_GO_FIXTURE_NON_AUTHORITATIVE")
    if authority.activation_status == ACTIVATION_STATUS_INACTIVE:
        blockers.append("SESSION_GO_INACTIVE")
    if authority.activation_status == ACTIVATION_STATUS_REVOKED:
        blockers.append("SESSION_GO_REVOKED")
    if authority.activation_status == ACTIVATION_STATUS_EXPIRED or float(now_unix) >= float(
        authority.expires_at
    ):
        blockers.append("SESSION_GO_EXPIRED")
    if float(now_unix) < float(authority.not_before):
        blockers.append("SESSION_GO_NOT_YET_VALID")
    if (
        authority.activation_status != ACTIVATION_STATUS_ACTIVE
        and "SESSION_GO_EXPIRED" not in blockers
        and authority.activation_status
        not in {ACTIVATION_STATUS_INACTIVE, ACTIVATION_STATUS_REVOKED}
    ):
        blockers.append("SESSION_GO_NOT_ACTIVE")

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not owner_session_go:
        blockers.append("OWNER_SESSION_GO_REQUIRED")
    if authority.session_id != expected_session_id:
        blockers.append("SESSION_GO_SESSION_ID_MISMATCH")
    if authority.entrypoint_id != expected_entrypoint_id:
        blockers.append("SESSION_GO_ENTRYPOINT_ID_MISMATCH")
    if authority.entrypoint_path != expected_entrypoint_path:
        blockers.append("SESSION_GO_ENTRYPOINT_PATH_MISMATCH")
    if authority.expected_repository_sha != expected_repository_sha:
        blockers.append("SESSION_GO_REPOSITORY_SHA_MISMATCH")
    if authority.expected_config_digest != expected_config_digest:
        blockers.append("SESSION_GO_CONFIG_DIGEST_MISMATCH")
    if not authorization_present:
        blockers.append("AUTHORIZATION_REQUIRED")
    if not confirm_token_present:
        blockers.append("CONFIRM_TOKEN_REQUIRED")

    ok = not blockers
    network_may = ok and bool(authority.network_session_execution_authorized_by_this_go)
    return {
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "notes": notes,
        "session_go_authority_satisfied": ok,
        "productive_session_execution_permitted": ok,
        "network_may_proceed": network_may,
        "authorization_may_proceed": ok,
        "authority": authority,
    }
