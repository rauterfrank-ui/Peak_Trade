"""Productive segment authorization envelopes bound to restart contracts.

Reuses authorization_artifact_v2 + productive confirm-token path. Does not invent a
parallel authorization domain; envelopes add segment/checkpoint bindings only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_artifact_v2 import (
    parse_authorization_artifact_v2,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    ALLOWED_SIDE_EFFECTS,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    FORBIDDEN_SIDE_EFFECTS,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    RUNTIME_MODE,
    SEGMENT_AUTH_ENVELOPE_SCHEMA,
    SEGMENT_POST_PURPOSE,
    SEGMENT_PRE_PURPOSE,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    SEGMENT_ROLES,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.digest_v1 import (
    sha256_canonical_v1,
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.models_v1 import (
    SegmentAuthorizationEnvelopeV1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.authorization_v1 import (
    authorization_digest_v1,
)


class SegmentAuthorizationError(RuntimeError):
    """Fail-closed productive segment authorization error."""


def _purpose_for_role(role: str) -> str:
    if role == SEGMENT_ROLE_PRE:
        return SEGMENT_PRE_PURPOSE
    if role == SEGMENT_ROLE_POST:
        return SEGMENT_POST_PURPOSE
    raise SegmentAuthorizationError(f"invalid_segment_role:{role}")


def build_segment_authorization_envelope_v1(
    *,
    segment_role: str,
    segment_id: str,
    repository_sha: str,
    config_digest: str,
    authorization_id: str,
    restart_campaign_id: str,
    runtime_session_id: str,
    expires_at: float,
    max_segment_duration_seconds: int,
    expected_successor_state: str,
    predecessor_checkpoint_digest: str | None = None,
    session_id: str = TARGET_SESSION_ID,
    instrument_identity: str = CANONICAL_INSTRUMENT_ID,
    revocation_status: str = "ACTIVE",
    productive: bool = True,
    fixture: bool = False,
) -> SegmentAuthorizationEnvelopeV1:
    if segment_role not in SEGMENT_ROLES:
        raise SegmentAuthorizationError(f"invalid_segment_role:{segment_role}")
    if segment_role == SEGMENT_ROLE_PRE and predecessor_checkpoint_digest is not None:
        raise SegmentAuthorizationError("pre_restart_must_not_have_predecessor_checkpoint")
    if segment_role == SEGMENT_ROLE_POST and not predecessor_checkpoint_digest:
        raise SegmentAuthorizationError("post_restart_requires_predecessor_checkpoint")
    if fixture or not productive:
        raise SegmentAuthorizationError("fixture_auth_forbidden_for_productive_envelope")
    if revocation_status != "ACTIVE":
        raise SegmentAuthorizationError(f"revocation_status_not_active:{revocation_status}")

    auth_digest = authorization_digest_v1(
        authorization_id=authorization_id,
        segment_role=segment_role,
        restart_campaign_id=restart_campaign_id,
        runtime_session_id=runtime_session_id,
    )
    provisional = {
        "schema_version": SEGMENT_AUTH_ENVELOPE_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "session_id": session_id,
        "segment_id": segment_id,
        "segment_role": segment_role,
        "segment_purpose": _purpose_for_role(segment_role),
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "runtime_mode": RUNTIME_MODE,
        "instrument_identity": instrument_identity,
        "network_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "allowed_side_effects": list(ALLOWED_SIDE_EFFECTS),
        "forbidden_side_effects": list(FORBIDDEN_SIDE_EFFECTS),
        "max_segment_duration_seconds": int(max_segment_duration_seconds),
        "predecessor_checkpoint_digest": predecessor_checkpoint_digest,
        "expected_successor_state": expected_successor_state,
        "authorization_id": authorization_id,
        "authorization_digest": auth_digest,
        "single_use": True,
        "expires_at": float(expires_at),
        "revocation_status": revocation_status,
        "productive": True,
        "fixture": False,
    }
    digest = sha256_canonical_v1(provisional)
    return SegmentAuthorizationEnvelopeV1(
        schema_version=SEGMENT_AUTH_ENVELOPE_SCHEMA,
        capability_id=CAPABILITY_ID,
        session_id=session_id,
        segment_id=segment_id,
        segment_role=segment_role,
        segment_purpose=_purpose_for_role(segment_role),
        repository_sha=repository_sha,
        config_digest=config_digest,
        runtime_mode=RUNTIME_MODE,
        instrument_identity=instrument_identity,
        network_allowlist=NETWORK_ALLOWLIST,
        http_method_allowlist=HTTP_METHOD_ALLOWLIST,
        allowed_side_effects=ALLOWED_SIDE_EFFECTS,
        forbidden_side_effects=FORBIDDEN_SIDE_EFFECTS,
        max_segment_duration_seconds=int(max_segment_duration_seconds),
        predecessor_checkpoint_digest=predecessor_checkpoint_digest,
        expected_successor_state=expected_successor_state,
        authorization_id=authorization_id,
        authorization_digest=auth_digest,
        single_use=True,
        expires_at=float(expires_at),
        revocation_status=revocation_status,
        productive=True,
        fixture=False,
        envelope_digest=digest,
    )


def write_segment_authorization_envelope_v1(
    *, path: Path, envelope: SegmentAuthorizationEnvelopeV1
) -> None:
    write_json_atomic_v1(path, envelope.to_dict())


def validate_segment_authorization_envelope_v1(
    payload: Mapping[str, Any],
    *,
    expected_segment_role: str,
    expected_session_id: str,
    expected_repository_sha: str,
    expected_config_digest: str,
    expected_predecessor_checkpoint_digest: str | None = None,
    now_unix: float,
    consumed_authorization_ids: set[str] | None = None,
    revoked_authorization_ids: set[str] | None = None,
) -> SegmentAuthorizationEnvelopeV1:
    if not isinstance(payload, Mapping):
        raise SegmentAuthorizationError("envelope_not_mapping")
    required = {
        "schema_version",
        "capability_id",
        "session_id",
        "segment_id",
        "segment_role",
        "segment_purpose",
        "repository_sha",
        "config_digest",
        "runtime_mode",
        "instrument_identity",
        "network_allowlist",
        "http_method_allowlist",
        "allowed_side_effects",
        "forbidden_side_effects",
        "max_segment_duration_seconds",
        "predecessor_checkpoint_digest",
        "expected_successor_state",
        "authorization_id",
        "authorization_digest",
        "single_use",
        "expires_at",
        "revocation_status",
        "productive",
        "fixture",
        "envelope_digest",
    }
    missing = sorted(required - set(payload.keys()))
    if missing:
        raise SegmentAuthorizationError(f"envelope_missing_fields:{','.join(missing)}")

    if str(payload.get("schema_version")) != SEGMENT_AUTH_ENVELOPE_SCHEMA:
        raise SegmentAuthorizationError("envelope_schema_mismatch")
    if str(payload.get("capability_id")) != CAPABILITY_ID:
        raise SegmentAuthorizationError("envelope_capability_mismatch")
    if bool(payload.get("fixture")) or not bool(payload.get("productive")):
        raise SegmentAuthorizationError("fixture_auth_productively_rejected")
    if not bool(payload.get("single_use")):
        raise SegmentAuthorizationError("single_use_required")

    role = str(payload["segment_role"])
    if role != expected_segment_role:
        raise SegmentAuthorizationError("segment_role_mismatch")
    if str(payload["session_id"]) != expected_session_id:
        raise SegmentAuthorizationError("session_id_mismatch")
    if str(payload["repository_sha"]) != expected_repository_sha:
        raise SegmentAuthorizationError("repository_sha_mismatch")
    if str(payload["config_digest"]) != expected_config_digest:
        raise SegmentAuthorizationError("config_digest_mismatch")
    if str(payload["revocation_status"]) != "ACTIVE":
        raise SegmentAuthorizationError("authorization_revoked")
    if float(payload["expires_at"]) <= float(now_unix):
        raise SegmentAuthorizationError("authorization_expired")

    auth_id = str(payload["authorization_id"])
    if consumed_authorization_ids and auth_id in consumed_authorization_ids:
        raise SegmentAuthorizationError("authorization_already_consumed")
    if revoked_authorization_ids and auth_id in revoked_authorization_ids:
        raise SegmentAuthorizationError("authorization_revoked")

    pred = payload.get("predecessor_checkpoint_digest")
    if role == SEGMENT_ROLE_PRE:
        if pred is not None:
            raise SegmentAuthorizationError("pre_restart_must_not_have_predecessor_checkpoint")
    else:
        if not pred:
            raise SegmentAuthorizationError("post_restart_requires_predecessor_checkpoint")
        if expected_predecessor_checkpoint_digest is None:
            raise SegmentAuthorizationError("post_restart_expected_checkpoint_missing")
        if str(pred) != expected_predecessor_checkpoint_digest:
            raise SegmentAuthorizationError("predecessor_checkpoint_digest_mismatch")

    # Recompute envelope digest without trusting caller.
    body = {k: payload[k] for k in payload.keys() if k != "envelope_digest"}
    # Normalize list fields for digest stability.
    body["allowed_side_effects"] = list(body["allowed_side_effects"])
    body["forbidden_side_effects"] = list(body["forbidden_side_effects"])
    recomputed = sha256_canonical_v1(body)
    if recomputed != str(payload["envelope_digest"]):
        raise SegmentAuthorizationError("envelope_digest_mismatch")

    return SegmentAuthorizationEnvelopeV1(
        schema_version=str(payload["schema_version"]),
        capability_id=str(payload["capability_id"]),
        session_id=str(payload["session_id"]),
        segment_id=str(payload["segment_id"]),
        segment_role=role,
        segment_purpose=str(payload["segment_purpose"]),
        repository_sha=str(payload["repository_sha"]),
        config_digest=str(payload["config_digest"]),
        runtime_mode=str(payload["runtime_mode"]),
        instrument_identity=str(payload["instrument_identity"]),
        network_allowlist=str(payload["network_allowlist"]),
        http_method_allowlist=str(payload["http_method_allowlist"]),
        allowed_side_effects=tuple(payload["allowed_side_effects"]),
        forbidden_side_effects=tuple(payload["forbidden_side_effects"]),
        max_segment_duration_seconds=int(payload["max_segment_duration_seconds"]),
        predecessor_checkpoint_digest=None if pred is None else str(pred),
        expected_successor_state=str(payload["expected_successor_state"]),
        authorization_id=auth_id,
        authorization_digest=str(payload["authorization_digest"]),
        single_use=True,
        expires_at=float(payload["expires_at"]),
        revocation_status=str(payload["revocation_status"]),
        productive=True,
        fixture=False,
        envelope_digest=recomputed,
    )


def assert_productive_artifact_not_fixture_v1(artifact_path: Path) -> dict[str, Any]:
    """Reject fixture / legacy authorization artifacts before any side effect."""
    raw = json.loads(artifact_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SegmentAuthorizationError("authorization_artifact_not_object")
    if bool(raw.get("forced_wiring_fixture_mode")):
        raise SegmentAuthorizationError("fixture_auth_productively_rejected")
    if str(raw.get("schema") or "") != "authorization_artifact_v2":
        raise SegmentAuthorizationError("fixture_or_legacy_auth_productively_rejected")
    artifact = parse_authorization_artifact_v2(raw)
    if artifact.forced_wiring_fixture_mode:
        raise SegmentAuthorizationError("fixture_auth_productively_rejected")
    if artifact.state.value in {"CONSUMED", "REVOKED", "EXPIRED"}:
        raise SegmentAuthorizationError(f"authorization_state_rejected:{artifact.state.value}")
    return raw


def load_confirm_token_secure_v1(
    *,
    confirm_token_file: Path | None,
    env_token: str,
    stdin_token: str,
) -> str:
    """Load confirm token from exactly one secure source (file, env, or stdin)."""
    sources = []
    if env_token.strip():
        sources.append("env")
    if confirm_token_file is not None:
        sources.append("file")
    if stdin_token.strip():
        sources.append("stdin")
    if len(sources) == 0:
        raise SegmentAuthorizationError("confirm_token_source_required")
    if len(sources) > 1:
        raise SegmentAuthorizationError("confirm_token_dual_source_forbidden")
    if env_token.strip():
        return env_token.strip()
    if stdin_token.strip():
        return stdin_token.strip()
    assert confirm_token_file is not None
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (  # noqa: E501
        load_confirm_token_from_file_v1,
    )

    return load_confirm_token_from_file_v1(confirm_token_file)
