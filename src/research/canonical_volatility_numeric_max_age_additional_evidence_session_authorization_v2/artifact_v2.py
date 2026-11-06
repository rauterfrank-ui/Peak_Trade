"""Builder, parser, verifier, and durable writer for authorization v2."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.confirm_token_v2 import (
    assert_authorization_payload_token_safe_v2,
    bind_confirm_token_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TTL_SECONDS,
    AUTHORIZATION_VERSION,
    CAMPAIGN_AUTHORIZATION_SCHEMA_PREFIX,
    CONSUMPTION_STATE_UNCONSUMED,
    FULL_GIT_SHA_LENGTH,
    ISSUED_BY_AUTHORITY,
    KNOWN_CONSUMPTION_STATES,
    KNOWN_REVOCATION_STATES,
    REQUIRED_AUTHORIZATION_FIELDS,
    REQUIRED_DURATION_SECONDS,
    REQUIRED_INSTRUMENT,
    REQUIRED_NETWORK_SCOPE,
    REQUIRED_SESSION_SCOPE,
    REQUIRED_VENUE,
    REVOCATION_STATE_ACTIVE,
    UNKNOWN_FIELD_POLICY,
    WALLCLOCK_AUTHORIZATION_SCHEMA,
    WALLCLOCK_DURATION_SECONDS,
    WALLCLOCK_NETWORK_SCOPE,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2,
    AdditionalEvidenceSessionAuthorizationV2Error,
    digest_excluding_keys,
    sha256_hex_text,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.critical_surface_v2 import (
    assert_critical_surface_digest_match_v2,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.git_binding_v2 import (
    assert_full_git_sha_v2,
    assert_is_ancestor_v2,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _parse_utc_z(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not _ISO_Z_RE.fullmatch(value):
        raise AdditionalEvidenceSessionAuthorizationV2Error(f"{field}_invalid_utc_z")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def format_utc_z(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AdditionalEvidenceSessionAuthorizationV2Error("datetime_naive_forbidden")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_authorization_digest_v2(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("authorization_digest",))


def derive_authorization_id_v2(
    *,
    preregistration_id: str,
    preregistration_digest: str,
    execution_sha: str,
    issued_at: str,
    earliest_start: str,
) -> str:
    material = {
        "authorization_version": AUTHORIZATION_VERSION,
        "earliest_start": earliest_start,
        "execution_sha": execution_sha,
        "issued_at": issued_at,
        "preregistration_digest": preregistration_digest,
        "preregistration_id": preregistration_id,
        "scope": AUTHORIZATION_SCOPE,
    }
    digest = sha256_hex_text(json.dumps(material, sort_keys=True, separators=(",", ":")))
    return f"cv_maxage_additional_evidence_auth_v2_{digest[:16]}"


def reject_foreign_authorization_payload_v2(payload: Mapping[str, Any]) -> None:
    version = (
        payload.get("authorization_version")
        or payload.get("schema")
        or payload.get("schema_version")
    )
    if version == WALLCLOCK_AUTHORIZATION_SCHEMA or payload.get("schema") == (
        WALLCLOCK_AUTHORIZATION_SCHEMA
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "cross_authority_wallclock_artifact_rejected"
        )
    if isinstance(version, str) and version.startswith(CAMPAIGN_AUTHORIZATION_SCHEMA_PREFIX):
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "cross_authority_campaign_v1_artifact_rejected"
        )
    if (
        payload.get("network_scope") == WALLCLOCK_NETWORK_SCOPE
        and payload.get("duration_seconds") == WALLCLOCK_DURATION_SECONDS
    ):
        # Wallclock-shaped payload without our version.
        if version != AUTHORIZATION_VERSION:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                "cross_authority_wallclock_shaped_artifact_rejected"
            )


def parse_additional_evidence_session_authorization_v2(
    payload: Mapping[str, Any],
) -> AdditionalEvidenceSessionAuthorizationV2:
    if not isinstance(payload, Mapping):
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_must_be_mapping")
    assert_authorization_payload_token_safe_v2(payload)
    reject_foreign_authorization_payload_v2(payload)

    keys = set(payload.keys())
    required = set(REQUIRED_AUTHORIZATION_FIELDS)
    missing = sorted(required - keys)
    if missing:
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "missing_required_field:" + ",".join(missing)
        )
    if UNKNOWN_FIELD_POLICY == "REJECT_UNKNOWN_FIELDS":
        unknown = sorted(keys - required)
        if unknown:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                "unknown_authorization_fields:" + ",".join(unknown)
            )

    version = payload.get("authorization_version")
    if version != AUTHORIZATION_VERSION:
        if version in {None, "", "v1"} or (isinstance(version, str) and version.endswith("/v1")):
            raise AdditionalEvidenceSessionAuthorizationV2Error("unknown_authorization_version")
        raise AdditionalEvidenceSessionAuthorizationV2Error("unknown_authorization_version")

    for field in (
        "authorization_id",
        "preregistration_id",
        "preregistration_digest",
        "preregistration_contract_version",
        "preregistration_contract_digest",
        "critical_surface_digest",
        "runbook_digest",
        "campaign_id",
        "confirm_token_fingerprint",
        "confirm_token_digest",
        "confirm_token_binding_sha256",
        "revocation_ledger_path",
        "consumption_ledger_path",
        "issued_by_authority",
    ):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise AdditionalEvidenceSessionAuthorizationV2Error(f"{field}_empty")

    if payload.get("issued_by_authority") != ISSUED_BY_AUTHORITY:
        raise AdditionalEvidenceSessionAuthorizationV2Error("issued_by_authority_mismatch")
    if payload.get("authorization_scope") != AUTHORIZATION_SCOPE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_scope_mismatch")
    if payload.get("single_use") is not True:
        raise AdditionalEvidenceSessionAuthorizationV2Error("single_use_required_true")
    if payload.get("venue") != REQUIRED_VENUE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("venue_binding_mismatch")
    if payload.get("instrument") != REQUIRED_INSTRUMENT:
        raise AdditionalEvidenceSessionAuthorizationV2Error("instrument_binding_mismatch")
    if payload.get("network_scope") != REQUIRED_NETWORK_SCOPE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("network_scope_binding_mismatch")
    if payload.get("session_scope") != REQUIRED_SESSION_SCOPE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("session_scope_binding_mismatch")
    try:
        duration = int(payload["duration_seconds"])
    except (TypeError, ValueError) as exc:
        raise AdditionalEvidenceSessionAuthorizationV2Error("duration_seconds_invalid") from exc
    if duration != REQUIRED_DURATION_SECONDS:
        raise AdditionalEvidenceSessionAuthorizationV2Error("duration_seconds_mismatch")
    if duration == WALLCLOCK_DURATION_SECONDS:
        raise AdditionalEvidenceSessionAuthorizationV2Error("duration_seconds_mismatch")

    for sha_field in ("code_baseline_sha", "execution_sha"):
        raw = payload.get(sha_field)
        if not isinstance(raw, str) or not _SHA_RE.fullmatch(raw):
            raise AdditionalEvidenceSessionAuthorizationV2Error(f"{sha_field}_invalid_format")
        if len(raw) != FULL_GIT_SHA_LENGTH:
            raise AdditionalEvidenceSessionAuthorizationV2Error(f"{sha_field}_invalid_length")

    for digest_field in (
        "preregistration_digest",
        "preregistration_contract_digest",
        "critical_surface_digest",
        "runbook_digest",
        "confirm_token_fingerprint",
        "confirm_token_binding_sha256",
    ):
        raw = payload.get(digest_field)
        if not isinstance(raw, str) or len(raw) != 64 or not re.fullmatch(r"[0-9a-f]{64}", raw):
            raise AdditionalEvidenceSessionAuthorizationV2Error(f"{digest_field}_invalid")

    token_digest = payload.get("confirm_token_digest")
    if not isinstance(token_digest, str) or not token_digest.startswith("sha256:"):
        raise AdditionalEvidenceSessionAuthorizationV2Error("confirm_token_digest_invalid")

    consumption_state = payload.get("consumption_state")
    if consumption_state not in KNOWN_CONSUMPTION_STATES:
        raise AdditionalEvidenceSessionAuthorizationV2Error("consumption_state_invalid")
    revocation_state = payload.get("revocation_state")
    if revocation_state not in KNOWN_REVOCATION_STATES:
        raise AdditionalEvidenceSessionAuthorizationV2Error("revocation_state_invalid")

    issued_at = _parse_utc_z(str(payload["issued_at"]), field="issued_at")
    earliest = _parse_utc_z(str(payload["earliest_start"]), field="earliest_start")
    expires = _parse_utc_z(str(payload["expires_at"]), field="expires_at")
    if earliest > expires:
        raise AdditionalEvidenceSessionAuthorizationV2Error("earliest_start_after_expires_at")
    if issued_at > expires:
        raise AdditionalEvidenceSessionAuthorizationV2Error("issued_at_after_expires_at")

    provisional = dict(payload)
    claimed = provisional.get("authorization_digest")
    recomputed = compute_authorization_digest_v2(provisional)
    if not isinstance(claimed, str) or claimed != recomputed:
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_digest_mismatch")

    return AdditionalEvidenceSessionAuthorizationV2(
        authorization_version=str(payload["authorization_version"]),
        authorization_id=str(payload["authorization_id"]),
        authorization_digest=str(claimed),
        authorization_scope=str(payload["authorization_scope"]),
        preregistration_id=str(payload["preregistration_id"]),
        preregistration_digest=str(payload["preregistration_digest"]),
        preregistration_contract_version=str(payload["preregistration_contract_version"]),
        preregistration_contract_digest=str(payload["preregistration_contract_digest"]),
        code_baseline_sha=str(payload["code_baseline_sha"]),
        execution_sha=str(payload["execution_sha"]),
        critical_surface_digest=str(payload["critical_surface_digest"]),
        runbook_digest=str(payload["runbook_digest"]),
        venue=str(payload["venue"]),
        instrument=str(payload["instrument"]),
        network_scope=str(payload["network_scope"]),
        session_scope=str(payload["session_scope"]),
        duration_seconds=duration,
        earliest_start=str(payload["earliest_start"]),
        expires_at=str(payload["expires_at"]),
        single_use=True,
        issued_at=str(payload["issued_at"]),
        issued_by_authority=str(payload["issued_by_authority"]),
        campaign_id=str(payload["campaign_id"]),
        confirm_token_fingerprint=str(payload["confirm_token_fingerprint"]),
        confirm_token_digest=str(payload["confirm_token_digest"]),
        confirm_token_binding_sha256=str(payload["confirm_token_binding_sha256"]),
        revocation_ledger_path=str(payload["revocation_ledger_path"]),
        consumption_ledger_path=str(payload["consumption_ledger_path"]),
        consumption_state=str(consumption_state),
        revocation_state=str(revocation_state),
    )


def verify_additional_evidence_session_authorization_v2(
    artifact: AdditionalEvidenceSessionAuthorizationV2,
    *,
    repo_root: Path,
    now_utc: Optional[datetime] = None,
    expected_preregistration_id: Optional[str] = None,
    expected_preregistration_digest: Optional[str] = None,
    expected_code_baseline_sha: Optional[str] = None,
    expected_execution_sha: Optional[str] = None,
    expected_critical_surface_digest: Optional[str] = None,
    expected_runbook_digest: Optional[str] = None,
    expected_contract_version: Optional[str] = None,
    expected_contract_digest: Optional[str] = None,
    require_unconsumed: bool = False,
    require_unrevoked: bool = False,
) -> AdditionalEvidenceSessionAuthorizationV2:
    root = Path(repo_root)
    parsed = parse_additional_evidence_session_authorization_v2(artifact.to_dict())
    try:
        assert_full_git_sha_v2(parsed.code_baseline_sha, field="code_baseline_sha")
        assert_full_git_sha_v2(parsed.execution_sha, field="execution_sha")
        assert_is_ancestor_v2(
            ancestor_sha=parsed.code_baseline_sha,
            descendant_sha=parsed.execution_sha,
            repo_root=root,
        )
        assert_critical_surface_digest_match_v2(
            expected_digest=parsed.critical_surface_digest,
            repo_root=root,
            at_sha=parsed.execution_sha,
        )
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, AdditionalEvidenceSessionAuthorizationV2Error):
            raise
        msg = str(exc)
        if "not_ancestor" in msg or "code_baseline_not_ancestor" in msg:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                "code_baseline_not_ancestor_of_execution_sha"
            ) from exc
        if "unknown_commit" in msg:
            raise AdditionalEvidenceSessionAuthorizationV2Error("git_sha_unknown_commit") from exc
        if "critical_surface" in msg:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                "critical_surface_digest_mismatch"
            ) from exc
        raise AdditionalEvidenceSessionAuthorizationV2Error(f"git_binding_failed:{exc}") from exc
    if expected_preregistration_id is not None and (
        parsed.preregistration_id != expected_preregistration_id
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("preregistration_id_mismatch")
    if expected_preregistration_digest is not None and (
        parsed.preregistration_digest != expected_preregistration_digest
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("preregistration_digest_mismatch")
    if expected_code_baseline_sha is not None and (
        parsed.code_baseline_sha != expected_code_baseline_sha
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("code_baseline_sha_mismatch")
    if expected_execution_sha is not None and parsed.execution_sha != expected_execution_sha:
        raise AdditionalEvidenceSessionAuthorizationV2Error("execution_sha_mismatch")
    if expected_critical_surface_digest is not None and (
        parsed.critical_surface_digest != expected_critical_surface_digest
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("critical_surface_digest_mismatch")
    if expected_runbook_digest is not None and parsed.runbook_digest != expected_runbook_digest:
        raise AdditionalEvidenceSessionAuthorizationV2Error("runbook_digest_mismatch")
    if expected_contract_version is not None and (
        parsed.preregistration_contract_version != expected_contract_version
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "preregistration_contract_version_mismatch"
        )
    if expected_contract_digest is not None and (
        parsed.preregistration_contract_digest != expected_contract_digest
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "preregistration_contract_digest_mismatch"
        )
    now = now_utc or datetime.now(timezone.utc)
    expires = _parse_utc_z(parsed.expires_at, field="expires_at")
    if now > expires:
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_expired")
    if require_unconsumed and parsed.consumption_state != CONSUMPTION_STATE_UNCONSUMED:
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_already_consumed")
    if require_unrevoked and parsed.revocation_state != REVOCATION_STATE_ACTIVE:
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_revoked")
    return parsed


def build_additional_evidence_session_authorization_v2(
    *,
    preregistration_id: str,
    preregistration_digest: str,
    preregistration_contract_version: str,
    preregistration_contract_digest: str,
    code_baseline_sha: str,
    execution_sha: str,
    critical_surface_digest: str,
    runbook_digest: str,
    venue: str,
    instrument: str,
    network_scope: str,
    session_scope: str,
    duration_seconds: int,
    campaign_id: str,
    confirm_token: str,
    revocation_ledger_path: str,
    consumption_ledger_path: str,
    issued_at: Optional[datetime] = None,
    earliest_start: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
    authorization_id: Optional[str] = None,
) -> AdditionalEvidenceSessionAuthorizationV2:
    issued = issued_at or datetime.now(timezone.utc)
    earliest = earliest_start or issued
    expires = expires_at or (issued + timedelta(seconds=AUTHORIZATION_TTL_SECONDS))
    issued_s = format_utc_z(issued)
    earliest_s = format_utc_z(earliest)
    expires_s = format_utc_z(expires)
    auth_id = authorization_id or derive_authorization_id_v2(
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        execution_sha=execution_sha,
        issued_at=issued_s,
        earliest_start=earliest_s,
    )
    token_fields = bind_confirm_token_v2(
        confirm_token=confirm_token,
        authorization_id=auth_id,
        preregistration_id=preregistration_id,
        preregistration_digest=preregistration_digest,
        execution_sha=execution_sha,
    )
    provisional: dict[str, Any] = {
        "authorization_id": auth_id,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorization_version": AUTHORIZATION_VERSION,
        "campaign_id": campaign_id,
        "code_baseline_sha": code_baseline_sha,
        "confirm_token_binding_sha256": token_fields["confirm_token_binding_sha256"],
        "confirm_token_digest": token_fields["confirm_token_digest"],
        "confirm_token_fingerprint": token_fields["confirm_token_fingerprint"],
        "consumption_ledger_path": consumption_ledger_path,
        "consumption_state": CONSUMPTION_STATE_UNCONSUMED,
        "critical_surface_digest": critical_surface_digest,
        "duration_seconds": int(duration_seconds),
        "earliest_start": earliest_s,
        "execution_sha": execution_sha,
        "expires_at": expires_s,
        "instrument": instrument,
        "issued_at": issued_s,
        "issued_by_authority": ISSUED_BY_AUTHORITY,
        "network_scope": network_scope,
        "preregistration_contract_digest": preregistration_contract_digest,
        "preregistration_contract_version": preregistration_contract_version,
        "preregistration_digest": preregistration_digest,
        "preregistration_id": preregistration_id,
        "revocation_ledger_path": revocation_ledger_path,
        "revocation_state": REVOCATION_STATE_ACTIVE,
        "runbook_digest": runbook_digest,
        "session_scope": session_scope,
        "single_use": True,
        "venue": venue,
    }
    provisional["authorization_digest"] = compute_authorization_digest_v2(provisional)
    return parse_additional_evidence_session_authorization_v2(provisional)


def load_additional_evidence_session_authorization_v2(
    path: Path,
) -> AdditionalEvidenceSessionAuthorizationV2:
    path = Path(path)
    if not path.is_file():
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_artifact_missing")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            f"authorization_parse_error:{exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_not_object")
    return parse_additional_evidence_session_authorization_v2(raw)


def write_additional_evidence_session_authorization_v2(
    *,
    output_path: Path,
    artifact: AdditionalEvidenceSessionAuthorizationV2,
) -> Path:
    """Atomic durable write with cleanup on failure and post-write reload."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = artifact.to_dict()
    assert_authorization_payload_token_safe_v2(payload)
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        # Pre-replace structural validation.
        parse_additional_evidence_session_authorization_v2(
            json.loads(tmp.read_text(encoding="utf-8"))
        )
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise
    loaded = load_additional_evidence_session_authorization_v2(path)
    if loaded.authorization_digest != artifact.authorization_digest:
        raise AdditionalEvidenceSessionAuthorizationV2Error(
            "authorization_post_write_digest_mismatch"
        )
    return path
