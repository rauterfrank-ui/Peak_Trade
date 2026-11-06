"""Canonical authorization_artifact_v2 writer (no plaintext tokens)."""

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
    recompute_authorization_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    AUTHORIZATION_SCHEMA,
    AUTHORIZATION_SCHEMA_VERSION,
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.integrity_v1 import (
    stamp_integrity_digest,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.states_v1 import (
    AuthorizationStateV2,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    EFFECTIVE_SESSION_CONFIG_DIGEST_KEY,
    MANDATORY_SAFETY_BOUNDARIES,
    REQUIRED_SESSION_DURATION_SECONDS,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.effective_session_config_digest_v1 import (
    compute_effective_session_config_digest_v1,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.mandatory_bindings_v1 import (
    validate_mandatory_network_scope_v1,
    validate_mandatory_safety_boundaries_v1,
    validate_mandatory_venue_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    assert_no_plaintext_token_fields,
    fingerprint_confirm_token,
    sha256_text,
)


class AuthorizationWriterV2Error(ValueError):
    """Fail-closed writer error."""


@dataclass
class AuthorizationWriteResultV2:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    path: str = ""
    integrity_digest: str = ""
    artifact: Optional[AuthorizationArtifactV2] = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "path": self.path,
            "integrity_digest": self.integrity_digest,
            "notes": list(self.notes),
            "artifact": None if self.artifact is None else self.artifact.to_dict(),
        }


def build_authorization_artifact_dict_v2(
    *,
    authorization_id: str,
    preregistration_id: str,
    preregistration_digest: str,
    repository_sha: str,
    runbook_sha256: str,
    session_duration_seconds: int = REQUIRED_SESSION_DURATION_SECONDS,
    config_digests: Optional[Mapping[str, str]] = None,
    safety_boundaries: Optional[Mapping[str, bool]] = None,
    confirm_token: str,
    confirm_token_binding_sha256: str = "",
    capability: str = TARGET_RUNTIME_CAPABILITY,
    created_at: Optional[float] = None,
    expires_at: Optional[float] = None,
    session_config_digest: Optional[str] = None,
    runtime_overrides: Optional[Mapping[str, Any]] = None,
    cli_overrides: Optional[Mapping[str, Any]] = None,
    env_overrides: Optional[Mapping[str, Any]] = None,
    defaults: Optional[Mapping[str, Any]] = None,
    notes: Optional[list[str]] = None,
    venue: Optional[str] = None,
    network_scope: Optional[str] = None,
) -> dict[str, Any]:
    now = float(time.time() if created_at is None else created_at)
    exp = float(expires_at) if expires_at is not None else now + 86400.0
    fp = fingerprint_confirm_token(confirm_token)
    digest = f"sha256:{sha256_text(confirm_token)}"
    # Venue/network_scope must be provided explicitly (no implicit OKX default).
    venue_bound = validate_mandatory_venue_v1(venue)
    network_bound = validate_mandatory_network_scope_v1(network_scope)
    merged_safety = dict(MANDATORY_SAFETY_BOUNDARIES)
    if safety_boundaries:
        merged_safety.update({str(k): v for k, v in safety_boundaries.items()})
    safety = validate_mandatory_safety_boundaries_v1(merged_safety)
    file_digests = {str(k): str(v) for k, v in sorted((config_digests or {}).items())}
    file_digests.pop(EFFECTIVE_SESSION_CONFIG_DIGEST_KEY, None)
    effective = session_config_digest or compute_effective_session_config_digest_v1(
        capability=capability,
        session_duration_seconds=int(session_duration_seconds),
        safety_boundaries=safety,
        runtime_overrides=runtime_overrides,
        cli_overrides=cli_overrides,
        env_overrides=env_overrides,
        defaults=defaults,
        config_files=file_digests,
        venue=venue_bound,
        network_scope=network_bound,
    )
    cfg = dict(sorted(file_digests.items()))
    cfg[EFFECTIVE_SESSION_CONFIG_DIGEST_KEY] = effective
    provisional = {
        "schema": AUTHORIZATION_SCHEMA,
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "authorization_id": authorization_id,
        "capability": capability,
        "preregistration_id": preregistration_id,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "runbook_sha256": runbook_sha256,
        "session_duration_seconds": int(session_duration_seconds),
        "session_config_digest": effective,
        "config_digests": cfg,
        "safety_boundaries": safety,
        "venue": venue_bound,
        "network_scope": network_bound,
        "confirm_token_fingerprint": fp,
        "confirm_token_digest": digest,
        "confirm_token_binding_sha256": confirm_token_binding_sha256,
        "created_at": now,
        "expires_at": exp,
        "single_use": True,
        "state": AuthorizationStateV2.CREATED_UNCONSUMED.value,
        "state_version": 1,
        "consumed_at": None,
        "consumption_id": None,
        "revocation_required_lookup": True,
        "atomic_consumption_required": True,
        "replay_blocked": True,
        "audit_trail_required": True,
        "forced_wiring_fixture_mode": False,
        "no_implicit_resume": True,
        "orders_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "credentials_authorized": False,
        "paper_execution_authorized": False,
        "promotion_authority": False,
        "economic_validity_changed": False,
        "session_start_authorized": False,
        "notes": list(notes or [])
        + [
            "AUTHORIZATION_ARTIFACT_V2",
            "NO_PLAINTEXT_TOKEN",
            "REVOCATION_LOOKUP_REQUIRED",
            "SINGLE_USE",
            "MANDATORY_SAFETY_BINDINGS",
            f"VENUE={AUTHORIZED_VENUE}",
            f"NETWORK_SCOPE={AUTHORIZED_NETWORK_SCOPE}",
        ],
    }
    assert_no_plaintext_token_fields(provisional)
    return stamp_integrity_digest(provisional)


def write_authorization_artifact_v2(
    *,
    output_path: Path,
    artifact_dict: Mapping[str, Any],
) -> AuthorizationWriteResultV2:
    notes = ["CANONICAL_AUTHORIZATION_ARTIFACT_V2_WRITE"]
    blockers: list[str] = []
    try:
        assert_no_plaintext_token_fields(artifact_dict)
        artifact = parse_authorization_artifact_v2(artifact_dict)
    except Exception as exc:  # noqa: BLE001
        return AuthorizationWriteResultV2(
            ok=False, blockers=[f"AUTHORIZATION_WRITE_PARSE_FAILED:{exc}"], notes=notes
        )
    if artifact.state is not AuthorizationStateV2.CREATED_UNCONSUMED:
        blockers.append("WRITER_MUST_EMIT_CREATED_UNCONSUMED")
    if blockers:
        return AuthorizationWriteResultV2(ok=False, blockers=blockers, notes=notes)

    payload = artifact.to_dict()
    try:
        atomic_write_json(path=output_path, payload=payload)
    except OSError as exc:
        return AuthorizationWriteResultV2(
            ok=False, blockers=[f"AUTHORIZATION_WRITE_FAILED:{exc}"], notes=notes
        )

    # Roundtrip verify
    loaded = parse_authorization_artifact_v2(
        __import__("json").loads(output_path.read_text(encoding="utf-8"))
    )
    if recompute_authorization_integrity_digest(loaded) != artifact.integrity_digest:
        return AuthorizationWriteResultV2(
            ok=False, blockers=["AUTHORIZATION_ROUNDTRIP_DIGEST_MISMATCH"], notes=notes
        )
    return AuthorizationWriteResultV2(
        ok=True,
        path=str(output_path),
        integrity_digest=artifact.integrity_digest,
        artifact=loaded,
        notes=notes + ["AUTHORIZATION_WRITTEN_AND_ROUNDTRIP_VERIFIED"],
    )


def new_authorization_id_v2() -> str:
    return f"auth_v2_{secrets.token_hex(16)}"
