"""Canonical authorization_artifact_v2 schema (parser + model)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    AUTHORIZATION_SCHEMA_VERSION,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    integrity_digest_v1,
    stamp_integrity_digest,
    verify_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateError,
    AuthorizationStateV2,
    parse_authorization_state_v2,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
)

_KNOWN_FIELDS = frozenset(
    {
        "schema",
        "schema_version",
        "authorization_id",
        "capability",
        "preregistration_id",
        "preregistration_digest",
        "repository_sha",
        "runbook_sha256",
        "session_duration_seconds",
        "config_digests",
        "safety_boundaries",
        "confirm_token_fingerprint",
        "confirm_token_digest",
        "confirm_token_binding_sha256",
        "created_at",
        "expires_at",
        "single_use",
        "state",
        "state_version",
        "consumed_at",
        "consumption_id",
        "revocation_required_lookup",
        "atomic_consumption_required",
        "replay_blocked",
        "audit_trail_required",
        "forced_wiring_fixture_mode",
        "no_implicit_resume",
        "orders_authorized",
        "testnet_authorized",
        "live_authorized",
        "credentials_authorized",
        "paper_execution_authorized",
        "promotion_authority",
        "economic_validity_changed",
        "session_start_authorized",
        "notes",
        "integrity_digest",
        "digest_scope",
    }
)


class AuthorizationArtifactV2Error(ValueError):
    """Fail-closed authorization_artifact_v2 error."""


@dataclass(frozen=True)
class AuthorizationArtifactV2:
    schema: str
    schema_version: str
    authorization_id: str
    capability: str
    preregistration_id: str
    preregistration_digest: str
    repository_sha: str
    runbook_sha256: str
    session_duration_seconds: int
    config_digests: dict[str, str]
    safety_boundaries: dict[str, bool]
    confirm_token_fingerprint: str
    confirm_token_digest: str
    confirm_token_binding_sha256: str
    created_at: float
    expires_at: float
    single_use: bool
    state: AuthorizationStateV2
    state_version: int
    consumed_at: Optional[float]
    consumption_id: Optional[str]
    revocation_required_lookup: bool
    atomic_consumption_required: bool
    replay_blocked: bool
    audit_trail_required: bool
    forced_wiring_fixture_mode: bool
    no_implicit_resume: bool
    orders_authorized: bool
    testnet_authorized: bool
    live_authorized: bool
    credentials_authorized: bool
    paper_execution_authorized: bool
    promotion_authority: bool
    economic_validity_changed: bool
    session_start_authorized: bool
    notes: tuple[str, ...] = ()
    integrity_digest: str = ""
    digest_scope: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["notes"] = list(self.notes)
        payload["consumed_at"] = self.consumed_at
        payload["consumption_id"] = self.consumption_id
        return payload

    def with_integrity(self) -> "AuthorizationArtifactV2":
        stamped = stamp_integrity_digest(self.to_dict())
        return parse_authorization_artifact_v2(stamped)


@dataclass
class AuthorizationParseResultV2:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    artifact: Optional[AuthorizationArtifactV2] = None


def load_authorization_artifact_dict_v2(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AuthorizationArtifactV2Error("AUTHORIZATION_ARTIFACT_MISSING")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthorizationArtifactV2Error(f"AUTHORIZATION_PARSE_ERROR:{exc}") from exc
    if not isinstance(raw, dict):
        raise AuthorizationArtifactV2Error("AUTHORIZATION_NOT_OBJECT")
    assert_no_plaintext_token_fields(raw)
    return raw


def parse_authorization_artifact_v2(raw: Mapping[str, Any]) -> AuthorizationArtifactV2:
    assert_no_plaintext_token_fields(raw)
    unknown = sorted(set(raw) - _KNOWN_FIELDS)
    if unknown:
        raise AuthorizationArtifactV2Error("AUTH_UNKNOWN_FIELDS:" + ",".join(unknown))
    missing = sorted(
        {
            "schema",
            "schema_version",
            "authorization_id",
            "capability",
            "preregistration_id",
            "preregistration_digest",
            "repository_sha",
            "runbook_sha256",
            "session_duration_seconds",
            "config_digests",
            "safety_boundaries",
            "confirm_token_fingerprint",
            "confirm_token_digest",
            "created_at",
            "single_use",
            "state",
            "state_version",
            "revocation_required_lookup",
        }
        - set(raw)
    )
    if missing:
        raise AuthorizationArtifactV2Error("AUTH_FIELD_MISSING:" + ",".join(missing))
    if raw["schema"] != AUTHORIZATION_SCHEMA:
        raise AuthorizationArtifactV2Error(f"AUTH_SCHEMA_UNSUPPORTED:{raw['schema']}")
    if raw["schema_version"] != AUTHORIZATION_SCHEMA_VERSION:
        raise AuthorizationArtifactV2Error(
            f"AUTH_SCHEMA_VERSION_UNSUPPORTED:{raw['schema_version']}"
        )
    try:
        state = parse_authorization_state_v2(raw["state"])
    except AuthorizationStateError as exc:
        raise AuthorizationArtifactV2Error(str(exc)) from exc
    cfg = raw["config_digests"]
    if not isinstance(cfg, dict) or not cfg:
        raise AuthorizationArtifactV2Error("CONFIG_DIGESTS_INCOMPLETE")
    if any(
        not isinstance(k, str) or not isinstance(v, str) or len(v) != 64 for k, v in cfg.items()
    ):
        raise AuthorizationArtifactV2Error("CONFIG_DIGESTS_INVALID")
    safety = raw["safety_boundaries"]
    if not isinstance(safety, dict) or not safety:
        raise AuthorizationArtifactV2Error("SAFETY_BOUNDARIES_INCOMPLETE")
    duration = int(raw["session_duration_seconds"])
    if duration <= 0:
        raise AuthorizationArtifactV2Error("SESSION_DURATION_INVALID")
    if raw.get("single_use") is not True:
        raise AuthorizationArtifactV2Error("SINGLE_USE_REQUIRED")
    if raw.get("revocation_required_lookup") is not True:
        raise AuthorizationArtifactV2Error("REVOCATION_LOOKUP_REQUIRED")
    notes_raw = raw.get("notes", ())
    notes = tuple(str(x) for x in notes_raw) if isinstance(notes_raw, (list, tuple)) else ()
    artifact = AuthorizationArtifactV2(
        schema=str(raw["schema"]),
        schema_version=str(raw["schema_version"]),
        authorization_id=str(raw["authorization_id"]),
        capability=str(raw["capability"]),
        preregistration_id=str(raw["preregistration_id"]),
        preregistration_digest=str(raw["preregistration_digest"]),
        repository_sha=str(raw["repository_sha"]),
        runbook_sha256=str(raw["runbook_sha256"]),
        session_duration_seconds=duration,
        config_digests={str(k): str(v) for k, v in sorted(cfg.items())},
        safety_boundaries={str(k): bool(v) for k, v in safety.items()},
        confirm_token_fingerprint=str(raw["confirm_token_fingerprint"]),
        confirm_token_digest=str(raw["confirm_token_digest"]),
        confirm_token_binding_sha256=str(raw.get("confirm_token_binding_sha256") or ""),
        created_at=float(raw["created_at"]),
        expires_at=float(raw.get("expires_at") or raw["created_at"]),
        single_use=True,
        state=state,
        state_version=int(raw["state_version"]),
        consumed_at=None if raw.get("consumed_at") is None else float(raw["consumed_at"]),
        consumption_id=None
        if raw.get("consumption_id") in (None, "")
        else str(raw.get("consumption_id")),
        revocation_required_lookup=True,
        atomic_consumption_required=bool(raw.get("atomic_consumption_required", True)),
        replay_blocked=bool(raw.get("replay_blocked", True)),
        audit_trail_required=bool(raw.get("audit_trail_required", True)),
        forced_wiring_fixture_mode=bool(raw.get("forced_wiring_fixture_mode", False)),
        no_implicit_resume=bool(raw.get("no_implicit_resume", True)),
        orders_authorized=bool(raw.get("orders_authorized", False)),
        testnet_authorized=bool(raw.get("testnet_authorized", False)),
        live_authorized=bool(raw.get("live_authorized", False)),
        credentials_authorized=bool(raw.get("credentials_authorized", False)),
        paper_execution_authorized=bool(raw.get("paper_execution_authorized", False)),
        promotion_authority=bool(raw.get("promotion_authority", False)),
        economic_validity_changed=bool(raw.get("economic_validity_changed", False)),
        session_start_authorized=bool(raw.get("session_start_authorized", False)),
        notes=notes,
        integrity_digest=str(raw.get("integrity_digest") or ""),
        digest_scope=str(raw.get("digest_scope") or ""),
    )
    if artifact.integrity_digest:
        verify_integrity_digest(artifact.to_dict())
    if artifact.capability not in {
        TARGET_RUNTIME_CAPABILITY,
        "CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1",
    } and not str(artifact.capability).startswith("WALLCLOCK_"):
        # Allow TARGET runtime capability primarily; reject empty.
        if not artifact.capability.strip():
            raise AuthorizationArtifactV2Error("CAPABILITY_REQUIRED")
    return artifact


def validate_authorization_artifact_v2(
    artifact: AuthorizationArtifactV2,
    *,
    expected_repository_sha: Optional[str] = None,
    expected_runbook_sha256: Optional[str] = None,
    expected_preregistration_id: Optional[str] = None,
    expected_preregistration_digest: Optional[str] = None,
    now_unix: Optional[float] = None,
) -> AuthorizationParseResultV2:
    blockers: list[str] = []
    try:
        verify_integrity_digest(artifact.to_dict())
    except ValueError as exc:
        blockers.append(str(exc))
    if expected_repository_sha and artifact.repository_sha != expected_repository_sha:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if expected_runbook_sha256 and artifact.runbook_sha256 != expected_runbook_sha256:
        blockers.append("RUNBOOK_SHA_MISMATCH")
    if expected_preregistration_id and artifact.preregistration_id != expected_preregistration_id:
        blockers.append("PREREGISTRATION_ID_MISMATCH")
    if (
        expected_preregistration_digest
        and artifact.preregistration_digest != expected_preregistration_digest
    ):
        blockers.append("PREREGISTRATION_DIGEST_MISMATCH")
    if artifact.orders_authorized or artifact.testnet_authorized or artifact.live_authorized:
        blockers.append("AUTHORITY_FLAGS_MUST_BE_FALSE")
    if artifact.forced_wiring_fixture_mode:
        blockers.append("FORCED_WIRING_FIXTURE_MODE_FORBIDDEN")
    if now_unix is not None and now_unix > artifact.expires_at:
        blockers.append("AUTHORIZATION_EXPIRED")
    if artifact.state is AuthorizationStateV2.CONSUMED:
        blockers.append("ALREADY_CONSUMED")
    if artifact.state is AuthorizationStateV2.REVOKED:
        blockers.append("REVOKED")
    if artifact.state is AuthorizationStateV2.INVALIDATED:
        blockers.append("INVALIDATED")
    return AuthorizationParseResultV2(
        ok=not blockers, blockers=sorted(set(blockers)), artifact=artifact
    )


def recompute_authorization_integrity_digest(artifact: AuthorizationArtifactV2) -> str:
    return integrity_digest_v1(artifact.to_dict())
