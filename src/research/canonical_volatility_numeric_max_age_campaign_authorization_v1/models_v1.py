"""Typed models and errors for campaign authorization v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence


class CampaignAuthorizationError(ValueError):
    """Fail-closed campaign authorization error."""


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sha256_hex_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_excluding_keys(payload: Mapping[str, Any], *, exclude: Sequence[str]) -> str:
    body = {k: v for k, v in payload.items() if k not in set(exclude)}
    return sha256_hex(body)


def require_aware_utc(value: datetime, *, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise CampaignAuthorizationError(f"{field_name}_not_datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise CampaignAuthorizationError(f"{field_name}_naive_datetime_forbidden")
    return value.astimezone(tz=value.tzinfo).astimezone()


@dataclass(frozen=True)
class CampaignAuthorizationArtifactV1:
    schema_version: str
    authorization_id: str
    authorization_scope: str
    issued_at: str
    earliest_start: str
    expires_at: str
    single_use: bool
    repository_sha: str
    campaign_id: str
    session_ids: tuple[str, ...]
    maximum_session_count: int
    preregistration_artifact_path: str
    preregistration_digest: str
    productive_design_id: str
    productive_accumulation_contract_version: str
    public_md_venue: str
    public_md_host: str
    public_md_endpoint_allowlist: tuple[str, ...]
    public_md_method_allowlist: tuple[str, ...]
    instrument_allowlist: tuple[str, ...]
    durable_ledger_path: str
    join_path: str
    quarantine_path: str
    revocation_ledger_path: str
    consumption_ledger_path: str
    campaign_authorization_ttl_seconds: int
    authorization_single_use_per_session: bool
    authorization_maximum_total_consumptions: int
    artifact_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "authorization_id": self.authorization_id,
            "authorization_scope": self.authorization_scope,
            "issued_at": self.issued_at,
            "earliest_start": self.earliest_start,
            "expires_at": self.expires_at,
            "single_use": self.single_use,
            "repository_sha": self.repository_sha,
            "campaign_id": self.campaign_id,
            "session_ids": list(self.session_ids),
            "maximum_session_count": self.maximum_session_count,
            "preregistration_artifact_path": self.preregistration_artifact_path,
            "preregistration_digest": self.preregistration_digest,
            "productive_design_id": self.productive_design_id,
            "productive_accumulation_contract_version": (
                self.productive_accumulation_contract_version
            ),
            "public_md_venue": self.public_md_venue,
            "public_md_host": self.public_md_host,
            "public_md_endpoint_allowlist": list(self.public_md_endpoint_allowlist),
            "public_md_method_allowlist": list(self.public_md_method_allowlist),
            "instrument_allowlist": list(self.instrument_allowlist),
            "durable_ledger_path": self.durable_ledger_path,
            "join_path": self.join_path,
            "quarantine_path": self.quarantine_path,
            "revocation_ledger_path": self.revocation_ledger_path,
            "consumption_ledger_path": self.consumption_ledger_path,
            "campaign_authorization_ttl_seconds": self.campaign_authorization_ttl_seconds,
            "authorization_single_use_per_session": self.authorization_single_use_per_session,
            "authorization_maximum_total_consumptions": (
                self.authorization_maximum_total_consumptions
            ),
            "artifact_digest": self.artifact_digest,
        }


@dataclass(frozen=True)
class RuntimeReleaseV1:
    """Authority token returned only after atomic consumption verification."""

    authorization_id: str
    authorization_digest: str
    campaign_id: str
    session_id: str
    repository_sha: str
    consumption_record_digest: str
    consumption_index: int
    released_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_id": self.authorization_id,
            "authorization_digest": self.authorization_digest,
            "campaign_id": self.campaign_id,
            "session_id": self.session_id,
            "repository_sha": self.repository_sha,
            "consumption_record_digest": self.consumption_record_digest,
            "consumption_index": self.consumption_index,
            "released_at": self.released_at,
            "runtime_side_effects_authorized": True,
            "authority_kind": "CAMPAIGN_AUTHORIZATION_SESSION_CONSUMPTION_V1",
        }
