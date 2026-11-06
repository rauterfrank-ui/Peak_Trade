"""Typed models for additional-evidence session authorization v2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


class AdditionalEvidenceSessionAuthorizationV2Error(ValueError):
    """Fail-closed authorization v2 error."""


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256_hex(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def sha256_hex_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_excluding_keys(payload: Mapping[str, Any], *, exclude: Sequence[str]) -> str:
    body = {k: payload[k] for k in sorted(payload) if k not in set(exclude)}
    return sha256_hex(body)


@dataclass(frozen=True)
class AdditionalEvidenceSessionAuthorizationV2:
    authorization_version: str
    authorization_id: str
    authorization_digest: str
    authorization_scope: str
    preregistration_id: str
    preregistration_digest: str
    preregistration_contract_version: str
    preregistration_contract_digest: str
    code_baseline_sha: str
    execution_sha: str
    critical_surface_digest: str
    runbook_digest: str
    venue: str
    instrument: str
    network_scope: str
    session_scope: str
    duration_seconds: int
    earliest_start: str
    expires_at: str
    single_use: bool
    issued_at: str
    issued_by_authority: str
    campaign_id: str
    confirm_token_fingerprint: str
    confirm_token_digest: str
    confirm_token_binding_sha256: str
    revocation_ledger_path: str
    consumption_ledger_path: str
    consumption_state: str
    revocation_state: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorization_digest": self.authorization_digest,
            "authorization_id": self.authorization_id,
            "authorization_scope": self.authorization_scope,
            "authorization_version": self.authorization_version,
            "campaign_id": self.campaign_id,
            "code_baseline_sha": self.code_baseline_sha,
            "confirm_token_binding_sha256": self.confirm_token_binding_sha256,
            "confirm_token_digest": self.confirm_token_digest,
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "consumption_ledger_path": self.consumption_ledger_path,
            "consumption_state": self.consumption_state,
            "critical_surface_digest": self.critical_surface_digest,
            "duration_seconds": self.duration_seconds,
            "earliest_start": self.earliest_start,
            "execution_sha": self.execution_sha,
            "expires_at": self.expires_at,
            "instrument": self.instrument,
            "issued_at": self.issued_at,
            "issued_by_authority": self.issued_by_authority,
            "network_scope": self.network_scope,
            "preregistration_contract_digest": self.preregistration_contract_digest,
            "preregistration_contract_version": self.preregistration_contract_version,
            "preregistration_digest": self.preregistration_digest,
            "preregistration_id": self.preregistration_id,
            "revocation_ledger_path": self.revocation_ledger_path,
            "revocation_state": self.revocation_state,
            "runbook_digest": self.runbook_digest,
            "session_scope": self.session_scope,
            "single_use": self.single_use,
            "venue": self.venue,
        }
