"""Schema, deterministic writer, parser, and full verifier for campaign authorization."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.constants_v1 import (
    AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_SINGLE_USE_PER_SESSION,
    BOUND_CAMPAIGN_ID,
    BOUND_CONSUMPTION_LEDGER_PATH,
    BOUND_DURABLE_LEDGER_PATH,
    BOUND_INSTRUMENT_ALLOWLIST,
    BOUND_JOIN_PATH,
    BOUND_PREREGISTRATION_ARTIFACT_PATH,
    BOUND_PREREGISTRATION_DIGEST,
    BOUND_PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION,
    BOUND_PRODUCTIVE_DESIGN_ID,
    BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST,
    BOUND_PUBLIC_MD_HOST,
    BOUND_PUBLIC_MD_METHOD_ALLOWLIST,
    BOUND_PUBLIC_MD_VENUE,
    BOUND_QUARANTINE_PATH,
    BOUND_REVOCATION_LEDGER_PATH,
    BOUND_SESSION_IDS,
    CAMPAIGN_AUTHORIZATION_TTL_SECONDS,
    MAXIMUM_SESSION_COUNT,
    REQUIRED_ARTIFACT_FIELDS,
    SCHEMA_VERSION,
    UNKNOWN_FIELD_POLICY,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.expiry_v1 import (
    compute_expires_at_v1,
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
    validate_issuance_window_v1,
)
from research.canonical_volatility_numeric_max_age_campaign_authorization_v1.models_v1 import (
    CampaignAuthorizationArtifactV1,
    CampaignAuthorizationError,
    digest_excluding_keys,
    sha256_hex_text,
)


def canonicalize_session_ids_v1(session_ids: Sequence[str]) -> tuple[str, ...]:
    """Canonical sort shared by writer and verifier (lexicographic, no wildcards)."""
    cleaned = [str(s).strip() for s in session_ids]
    if any(not s for s in cleaned):
        raise CampaignAuthorizationError("session_id_empty")
    if any("*" in s or "?" in s for s in cleaned):
        raise CampaignAuthorizationError("session_id_wildcard_forbidden")
    if len(cleaned) != len(set(cleaned)):
        raise CampaignAuthorizationError("session_ids_not_unique")
    return tuple(sorted(cleaned))


def compute_artifact_digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("artifact_digest",))


def derive_authorization_id_v1(
    *,
    repository_sha: str,
    campaign_id: str,
    session_ids: Sequence[str],
    preregistration_digest: str,
    issued_at: str,
    earliest_start: str,
) -> str:
    material = {
        "campaign_id": campaign_id,
        "earliest_start": earliest_start,
        "issued_at": issued_at,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "scope": AUTHORIZATION_SCOPE,
        "session_ids": list(canonicalize_session_ids_v1(session_ids)),
    }
    digest = sha256_hex_text(
        json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    )
    return f"cv_maxage_campaign_auth_v1_{digest[:16]}"


def build_campaign_authorization_artifact_v1(
    *,
    repository_sha: str,
    campaign_id: str,
    session_ids: Sequence[str],
    preregistration_digest: str,
    issued_at: datetime | str,
    earliest_start: datetime | str,
    authorization_id: Optional[str] = None,
    preregistration_artifact_path: str = BOUND_PREREGISTRATION_ARTIFACT_PATH,
    durable_ledger_path: str = BOUND_DURABLE_LEDGER_PATH,
    join_path: str = BOUND_JOIN_PATH,
    quarantine_path: str = BOUND_QUARANTINE_PATH,
    revocation_ledger_path: str = BOUND_REVOCATION_LEDGER_PATH,
    consumption_ledger_path: str = BOUND_CONSUMPTION_LEDGER_PATH,
) -> CampaignAuthorizationArtifactV1:
    """Deterministic writer. No productive defaults for operator identity fields."""
    repo_sha = str(repository_sha or "").strip()
    if not repo_sha or len(repo_sha) < 7:
        raise CampaignAuthorizationError("repository_sha_required")
    camp = str(campaign_id or "").strip()
    if not camp:
        raise CampaignAuthorizationError("campaign_id_required")
    preg = str(preregistration_digest or "").strip()
    if not preg:
        raise CampaignAuthorizationError("preregistration_digest_required")

    issued, earliest, expires = validate_issuance_window_v1(
        issued_at=parse_aware_utc_datetime_v1(issued_at, field_name="issued_at"),
        earliest_start=parse_aware_utc_datetime_v1(earliest_start, field_name="earliest_start"),
    )
    issued_s = format_aware_utc_datetime_v1(issued)
    earliest_s = format_aware_utc_datetime_v1(earliest)
    expires_s = format_aware_utc_datetime_v1(expires)
    # Defensive: expires must equal issued + TTL.
    if expires != compute_expires_at_v1(issued_at=issued):
        raise CampaignAuthorizationError("expires_at_ttl_mismatch")

    sessions = canonicalize_session_ids_v1(session_ids)
    if len(sessions) != MAXIMUM_SESSION_COUNT:
        raise CampaignAuthorizationError("maximum_session_count_mismatch")
    if camp == BOUND_CAMPAIGN_ID and sessions != canonicalize_session_ids_v1(BOUND_SESSION_IDS):
        raise CampaignAuthorizationError("bound_session_ids_mismatch")
    if camp == BOUND_CAMPAIGN_ID and preg != BOUND_PREREGISTRATION_DIGEST:
        raise CampaignAuthorizationError("bound_preregistration_digest_mismatch")

    auth_id = (
        str(authorization_id).strip()
        if authorization_id
        else derive_authorization_id_v1(
            repository_sha=repo_sha,
            campaign_id=camp,
            session_ids=sessions,
            preregistration_digest=preg,
            issued_at=issued_s,
            earliest_start=earliest_s,
        )
    )
    if not auth_id:
        raise CampaignAuthorizationError("authorization_id_required")

    provisional: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authorization_id": auth_id,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "issued_at": issued_s,
        "earliest_start": earliest_s,
        "expires_at": expires_s,
        "single_use": True,
        "repository_sha": repo_sha,
        "campaign_id": camp,
        "session_ids": list(sessions),
        "maximum_session_count": MAXIMUM_SESSION_COUNT,
        "preregistration_artifact_path": str(preregistration_artifact_path),
        "preregistration_digest": preg,
        "productive_design_id": BOUND_PRODUCTIVE_DESIGN_ID,
        "productive_accumulation_contract_version": (
            BOUND_PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION
        ),
        "public_md_venue": BOUND_PUBLIC_MD_VENUE,
        "public_md_host": BOUND_PUBLIC_MD_HOST,
        "public_md_endpoint_allowlist": list(BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST),
        "public_md_method_allowlist": list(BOUND_PUBLIC_MD_METHOD_ALLOWLIST),
        "instrument_allowlist": list(BOUND_INSTRUMENT_ALLOWLIST),
        "durable_ledger_path": str(durable_ledger_path),
        "join_path": str(join_path),
        "quarantine_path": str(quarantine_path),
        "revocation_ledger_path": str(revocation_ledger_path),
        "consumption_ledger_path": str(consumption_ledger_path),
        "campaign_authorization_ttl_seconds": CAMPAIGN_AUTHORIZATION_TTL_SECONDS,
        "authorization_single_use_per_session": AUTHORIZATION_SINGLE_USE_PER_SESSION,
        "authorization_maximum_total_consumptions": AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS,
    }
    digest = compute_artifact_digest_v1(provisional)
    provisional["artifact_digest"] = digest
    return parse_campaign_authorization_artifact_v1(provisional)


def parse_campaign_authorization_artifact_v1(
    payload: Mapping[str, Any],
) -> CampaignAuthorizationArtifactV1:
    if not isinstance(payload, Mapping):
        raise CampaignAuthorizationError("authorization_payload_not_object")
    keys = set(payload.keys())
    required = set(REQUIRED_ARTIFACT_FIELDS)
    missing = sorted(required - keys)
    if missing:
        raise CampaignAuthorizationError("authorization_field_missing:" + ",".join(missing))
    if UNKNOWN_FIELD_POLICY == "REJECT_UNKNOWN_FIELDS":
        unknown = sorted(keys - required)
        if unknown:
            raise CampaignAuthorizationError("unknown_field:" + ",".join(unknown))

    sessions = canonicalize_session_ids_v1(list(payload["session_ids"] or []))
    # Preserve canonical order in parsed object even if input was unsorted.
    if list(payload["session_ids"]) != list(sessions):
        # Accept unsorted input only when the set matches after canonicalization;
        # digest verification uses canonical session_ids.
        pass

    artifact = CampaignAuthorizationArtifactV1(
        schema_version=str(payload["schema_version"]),
        authorization_id=str(payload["authorization_id"]),
        authorization_scope=str(payload["authorization_scope"]),
        issued_at=str(payload["issued_at"]),
        earliest_start=str(payload["earliest_start"]),
        expires_at=str(payload["expires_at"]),
        single_use=bool(payload["single_use"]),
        repository_sha=str(payload["repository_sha"]),
        campaign_id=str(payload["campaign_id"]),
        session_ids=sessions,
        maximum_session_count=int(payload["maximum_session_count"]),
        preregistration_artifact_path=str(payload["preregistration_artifact_path"]),
        preregistration_digest=str(payload["preregistration_digest"]),
        productive_design_id=str(payload["productive_design_id"]),
        productive_accumulation_contract_version=str(
            payload["productive_accumulation_contract_version"]
        ),
        public_md_venue=str(payload["public_md_venue"]),
        public_md_host=str(payload["public_md_host"]),
        public_md_endpoint_allowlist=tuple(str(x) for x in payload["public_md_endpoint_allowlist"]),
        public_md_method_allowlist=tuple(str(x) for x in payload["public_md_method_allowlist"]),
        instrument_allowlist=tuple(str(x) for x in payload["instrument_allowlist"]),
        durable_ledger_path=str(payload["durable_ledger_path"]),
        join_path=str(payload["join_path"]),
        quarantine_path=str(payload["quarantine_path"]),
        revocation_ledger_path=str(payload["revocation_ledger_path"]),
        consumption_ledger_path=str(payload["consumption_ledger_path"]),
        campaign_authorization_ttl_seconds=int(payload["campaign_authorization_ttl_seconds"]),
        authorization_single_use_per_session=bool(payload["authorization_single_use_per_session"]),
        authorization_maximum_total_consumptions=int(
            payload["authorization_maximum_total_consumptions"]
        ),
        artifact_digest=str(payload["artifact_digest"]),
    )
    return artifact


def verify_campaign_authorization_artifact_v1(
    artifact: CampaignAuthorizationArtifactV1 | Mapping[str, Any],
    *,
    expected_repository_sha: Optional[str] = None,
    expected_campaign_id: Optional[str] = None,
    expected_session_ids: Optional[Sequence[str]] = None,
    expected_preregistration_digest: Optional[str] = None,
    expected_maximum_session_count: int = MAXIMUM_SESSION_COUNT,
) -> CampaignAuthorizationArtifactV1:
    parsed = (
        artifact
        if isinstance(artifact, CampaignAuthorizationArtifactV1)
        else parse_campaign_authorization_artifact_v1(artifact)
    )
    payload = parsed.to_dict()
    # Digest over canonical session order.
    expected_digest = compute_artifact_digest_v1(payload)
    if parsed.artifact_digest != expected_digest:
        raise CampaignAuthorizationError("artifact_digest_mismatch")

    if parsed.schema_version != SCHEMA_VERSION:
        raise CampaignAuthorizationError("schema_version_mismatch")
    if parsed.authorization_scope != AUTHORIZATION_SCOPE:
        raise CampaignAuthorizationError("authorization_scope_mismatch")
    if parsed.single_use is not True:
        raise CampaignAuthorizationError("single_use_required")
    if parsed.authorization_single_use_per_session is not True:
        raise CampaignAuthorizationError("single_use_per_session_required")
    if parsed.authorization_maximum_total_consumptions != AUTHORIZATION_MAXIMUM_TOTAL_CONSUMPTIONS:
        raise CampaignAuthorizationError("maximum_total_consumptions_mismatch")
    if parsed.campaign_authorization_ttl_seconds != CAMPAIGN_AUTHORIZATION_TTL_SECONDS:
        raise CampaignAuthorizationError("ttl_seconds_mismatch")
    if parsed.maximum_session_count != expected_maximum_session_count:
        raise CampaignAuthorizationError("maximum_session_count_mismatch")
    if len(parsed.session_ids) != parsed.maximum_session_count:
        raise CampaignAuthorizationError("session_count_binding_mismatch")

    validate_issuance_window_v1(
        issued_at=parse_aware_utc_datetime_v1(parsed.issued_at, field_name="issued_at"),
        earliest_start=parse_aware_utc_datetime_v1(
            parsed.earliest_start, field_name="earliest_start"
        ),
        expires_at=parse_aware_utc_datetime_v1(parsed.expires_at, field_name="expires_at"),
    )

    if expected_repository_sha is not None and parsed.repository_sha != expected_repository_sha:
        raise CampaignAuthorizationError("repository_sha_binding_mismatch")
    if expected_campaign_id is not None and parsed.campaign_id != expected_campaign_id:
        raise CampaignAuthorizationError("campaign_id_binding_mismatch")
    if expected_preregistration_digest is not None:
        if parsed.preregistration_digest != expected_preregistration_digest:
            raise CampaignAuthorizationError("preregistration_digest_binding_mismatch")
    if expected_session_ids is not None:
        expected = canonicalize_session_ids_v1(expected_session_ids)
        if parsed.session_ids != expected:
            raise CampaignAuthorizationError("session_ids_binding_mismatch")
        if set(parsed.session_ids) - set(expected):
            raise CampaignAuthorizationError("additional_session_id_forbidden")
        if set(expected) - set(parsed.session_ids):
            raise CampaignAuthorizationError("missing_session_id")

    # Productive / design / public-md / path bindings for the bound campaign.
    if parsed.campaign_id == BOUND_CAMPAIGN_ID:
        if parsed.session_ids != canonicalize_session_ids_v1(BOUND_SESSION_IDS):
            raise CampaignAuthorizationError("bound_session_ids_mismatch")
        if parsed.preregistration_digest != BOUND_PREREGISTRATION_DIGEST:
            raise CampaignAuthorizationError("bound_preregistration_digest_mismatch")
        if parsed.preregistration_artifact_path != BOUND_PREREGISTRATION_ARTIFACT_PATH:
            raise CampaignAuthorizationError("preregistration_artifact_path_mismatch")
        if parsed.productive_design_id != BOUND_PRODUCTIVE_DESIGN_ID:
            raise CampaignAuthorizationError("productive_design_id_mismatch")
        if (
            parsed.productive_accumulation_contract_version
            != BOUND_PRODUCTIVE_ACCUMULATION_CONTRACT_VERSION
        ):
            raise CampaignAuthorizationError("productive_accumulation_contract_version_mismatch")
        if parsed.public_md_venue != BOUND_PUBLIC_MD_VENUE:
            raise CampaignAuthorizationError("public_md_venue_mismatch")
        if parsed.public_md_host != BOUND_PUBLIC_MD_HOST:
            raise CampaignAuthorizationError("public_md_host_mismatch")
        if tuple(parsed.public_md_endpoint_allowlist) != BOUND_PUBLIC_MD_ENDPOINT_ALLOWLIST:
            raise CampaignAuthorizationError("public_md_endpoint_allowlist_mismatch")
        if tuple(parsed.public_md_method_allowlist) != BOUND_PUBLIC_MD_METHOD_ALLOWLIST:
            raise CampaignAuthorizationError("public_md_method_allowlist_mismatch")
        if "GET" not in parsed.public_md_method_allowlist:
            raise CampaignAuthorizationError("public_md_method_not_get_only")
        if any(m != "GET" for m in parsed.public_md_method_allowlist):
            raise CampaignAuthorizationError("public_md_non_get_forbidden")
        if tuple(parsed.instrument_allowlist) != BOUND_INSTRUMENT_ALLOWLIST:
            raise CampaignAuthorizationError("instrument_allowlist_mismatch")
        if parsed.durable_ledger_path != BOUND_DURABLE_LEDGER_PATH:
            raise CampaignAuthorizationError("durable_ledger_path_mismatch")
        if parsed.join_path != BOUND_JOIN_PATH:
            raise CampaignAuthorizationError("join_path_mismatch")
        if parsed.quarantine_path != BOUND_QUARANTINE_PATH:
            raise CampaignAuthorizationError("quarantine_path_mismatch")
        if parsed.revocation_ledger_path != BOUND_REVOCATION_LEDGER_PATH:
            raise CampaignAuthorizationError("revocation_ledger_path_mismatch")
        if parsed.consumption_ledger_path != BOUND_CONSUMPTION_LEDGER_PATH:
            raise CampaignAuthorizationError("consumption_ledger_path_mismatch")

    return parsed


def write_campaign_authorization_artifact_v1(
    *,
    output_path: Path,
    artifact: CampaignAuthorizationArtifactV1 | Mapping[str, Any],
) -> CampaignAuthorizationArtifactV1:
    verified = verify_campaign_authorization_artifact_v1(artifact)
    path = Path(output_path)
    if path.exists():
        raise CampaignAuthorizationError("authorization_output_exists_refuse_overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(verified.to_dict(), sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_TRUNC
    fd = os.open(str(tmp), flags, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    loaded = load_campaign_authorization_artifact_v1(path)
    if loaded.artifact_digest != verified.artifact_digest:
        raise CampaignAuthorizationError("authorization_write_verify_failed")
    return loaded


def load_campaign_authorization_artifact_v1(path: Path) -> CampaignAuthorizationArtifactV1:
    p = Path(path)
    if not p.is_file():
        raise CampaignAuthorizationError("authorization_artifact_missing")
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CampaignAuthorizationError("authorization_artifact_parse_error") from exc
    return verify_campaign_authorization_artifact_v1(raw)
