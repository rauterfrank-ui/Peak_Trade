"""Credential reference metadata contract (no plaintext, Cap 11.2 boundary only)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_SCOPE_EXPLICIT,
    CREDENTIAL_FAILURE_FAILS_CLOSED,
    CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2,
    CREDENTIAL_PLAINTEXT_LOADED,
    CREDENTIAL_REFERENCE_METADATA_OWNER,
    EXCHANGE_CREDENTIAL_ACCESS_REACHABLE,
    FORBIDDEN_IN_EVIDENCE,
    FORBIDDEN_IN_LOGS,
    FORBIDDEN_IN_PROCESS_ARGUMENTS,
    FORBIDDEN_TO_PERSIST,
    INSTRUMENT_SCOPE_EXPLICIT,
    IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED,
    LEAST_PRIVILEGE,
    OWNER,
    PLAINTEXT_SECRET_NEVER_PERSISTED,
    REVOCATION_DETECTED,
    ROTATION_SUPPORTED,
    SECRET_REFERENCE_ONLY_IN_CONFIG,
    VENUE_SCOPE_EXPLICIT,
    WITHDRAWAL_PERMISSION,
)


class CredentialContractViolationError(ValueError):
    """Fail-closed credential boundary violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class CredentialReferenceMetadataV1:
    """Durable credential *reference* metadata — never plaintext secrets."""

    credential_ref_id: str
    secret_reference: str
    venue: str
    account_identity: str
    instrument_scope: tuple[str, ...]
    least_privilege: bool = True
    withdrawal_permission: bool = False
    ip_or_host_restriction_declared: bool = True
    rotation_supported: bool = True
    revocation_detected: bool = False
    plaintext_present: bool = False

    def digest(self) -> str:
        material = {
            "credential_ref_id": self.credential_ref_id,
            "secret_reference": self.secret_reference,
            "venue": self.venue,
            "account_identity": self.account_identity,
            "instrument_scope": list(self.instrument_scope),
            "least_privilege": self.least_privilege,
            "withdrawal_permission": self.withdrawal_permission,
            "ip_or_host_restriction_declared": self.ip_or_host_restriction_declared,
            "rotation_supported": self.rotation_supported,
            "revocation_detected": self.revocation_detected,
            "plaintext_present": self.plaintext_present,
        }
        return hashlib.sha256(_canonical_dumps(material).encode("utf-8")).hexdigest()


def build_credential_reference_metadata_v1(
    *,
    credential_ref_id: str,
    secret_reference: str,
    venue: str,
    account_identity: str,
    instrument_scope: tuple[str, ...] | list[str],
    least_privilege: bool = True,
    withdrawal_permission: bool = False,
    ip_or_host_restriction_declared: bool = True,
    rotation_supported: bool = True,
    revocation_detected: bool = False,
    plaintext_present: bool = False,
    plaintext_secret: str | None = None,
) -> CredentialReferenceMetadataV1:
    """Build reference metadata; reject any plaintext secret material."""
    if plaintext_secret is not None or plaintext_present:
        raise CredentialContractViolationError("PLAINTEXT_SECRET_FORBIDDEN")
    if not credential_ref_id or not secret_reference:
        raise CredentialContractViolationError("CREDENTIAL_REFERENCE_REQUIRED")
    if secret_reference.startswith("plaintext:") or secret_reference.startswith("sk-"):
        raise CredentialContractViolationError("SECRET_MUST_BE_REFERENCE_ONLY")
    if not venue:
        raise CredentialContractViolationError("VENUE_SCOPE_REQUIRED")
    if not account_identity:
        raise CredentialContractViolationError("ACCOUNT_IDENTITY_REQUIRED")
    scope = tuple(str(x) for x in instrument_scope)
    if not scope:
        raise CredentialContractViolationError("INSTRUMENT_SCOPE_REQUIRED")
    if not least_privilege:
        raise CredentialContractViolationError("LEAST_PRIVILEGE_REQUIRED")
    if withdrawal_permission:
        raise CredentialContractViolationError("WITHDRAWAL_PERMISSION_FORBIDDEN")
    return CredentialReferenceMetadataV1(
        credential_ref_id=credential_ref_id,
        secret_reference=secret_reference,
        venue=venue,
        account_identity=account_identity,
        instrument_scope=scope,
        least_privilege=least_privilege,
        withdrawal_permission=withdrawal_permission,
        ip_or_host_restriction_declared=ip_or_host_restriction_declared,
        rotation_supported=rotation_supported,
        revocation_detected=revocation_detected,
        plaintext_present=False,
    )


def refuse_plaintext_secret_persistence_v1(
    *,
    candidate: str | None,
    surface: str,
) -> dict[str, Any]:
    """Fail-closed refusal for plaintext secrets on any persistence surface."""
    if candidate:
        raise CredentialContractViolationError(f"PLAINTEXT_SECRET_FORBIDDEN_ON_{surface.upper()}")
    return {
        "ok": True,
        "surface": surface,
        "FORBIDDEN_TO_PERSIST": FORBIDDEN_TO_PERSIST,
        "FORBIDDEN_IN_LOGS": FORBIDDEN_IN_LOGS,
        "FORBIDDEN_IN_PROCESS_ARGUMENTS": FORBIDDEN_IN_PROCESS_ARGUMENTS,
        "FORBIDDEN_IN_EVIDENCE": FORBIDDEN_IN_EVIDENCE,
        "PLAINTEXT_SECRET_NEVER_PERSISTED": PLAINTEXT_SECRET_NEVER_PERSISTED,
    }


def prove_credential_contract_v1() -> dict[str, Any]:
    meta = build_credential_reference_metadata_v1(
        credential_ref_id="cred-ref-demo",
        secret_reference="secretref://vault/peak-trade/demo",
        venue="OKX",
        account_identity="acct-uid-demo",
        instrument_scope=("BTC-USDT-SWAP",),
    )
    plaintext_blocked = False
    try:
        build_credential_reference_metadata_v1(
            credential_ref_id="cred-ref-bad",
            secret_reference="secretref://vault/peak-trade/demo",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            plaintext_secret="super-secret",
        )
    except CredentialContractViolationError:
        plaintext_blocked = True

    withdrawal_blocked = False
    try:
        build_credential_reference_metadata_v1(
            credential_ref_id="cred-ref-wd",
            secret_reference="secretref://vault/peak-trade/demo",
            venue="OKX",
            account_identity="acct-uid-demo",
            instrument_scope=("BTC-USDT-SWAP",),
            withdrawal_permission=True,
        )
    except CredentialContractViolationError:
        withdrawal_blocked = True

    persist_ok = refuse_plaintext_secret_persistence_v1(candidate=None, surface="evidence")
    persist_blocked = False
    try:
        refuse_plaintext_secret_persistence_v1(candidate="leak", surface="logs")
    except CredentialContractViolationError:
        persist_blocked = True

    ok = all(
        [
            meta.plaintext_present is False,
            plaintext_blocked,
            withdrawal_blocked,
            persist_ok.get("ok") is True,
            persist_blocked,
            LEAST_PRIVILEGE is True,
            WITHDRAWAL_PERMISSION is False,
            ACCOUNT_SCOPE_EXPLICIT is True,
            VENUE_SCOPE_EXPLICIT is True,
            INSTRUMENT_SCOPE_EXPLICIT is True,
            IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED is True,
            SECRET_REFERENCE_ONLY_IN_CONFIG is True,
            PLAINTEXT_SECRET_NEVER_PERSISTED is True,
            ROTATION_SUPPORTED is True,
            REVOCATION_DETECTED is True,
            CREDENTIAL_FAILURE_FAILS_CLOSED is True,
            EXCHANGE_CREDENTIAL_ACCESS_REACHABLE is False,
            CREDENTIAL_PLAINTEXT_LOADED is False,
            CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2 is False,
        ]
    )
    return {
        "ok": ok,
        "owner": CREDENTIAL_REFERENCE_METADATA_OWNER,
        "credential_ref_digest": meta.digest(),
        "LEAST_PRIVILEGE": LEAST_PRIVILEGE,
        "WITHDRAWAL_PERMISSION": WITHDRAWAL_PERMISSION,
        "ACCOUNT_SCOPE_EXPLICIT": ACCOUNT_SCOPE_EXPLICIT,
        "VENUE_SCOPE_EXPLICIT": VENUE_SCOPE_EXPLICIT,
        "INSTRUMENT_SCOPE_EXPLICIT": INSTRUMENT_SCOPE_EXPLICIT,
        "IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED": IP_OR_HOST_RESTRICTION_WHERE_SUPPORTED,
        "SECRET_REFERENCE_ONLY_IN_CONFIG": SECRET_REFERENCE_ONLY_IN_CONFIG,
        "PLAINTEXT_SECRET_NEVER_PERSISTED": PLAINTEXT_SECRET_NEVER_PERSISTED,
        "ROTATION_SUPPORTED": ROTATION_SUPPORTED,
        "REVOCATION_DETECTED": REVOCATION_DETECTED,
        "CREDENTIAL_FAILURE_FAILS_CLOSED": CREDENTIAL_FAILURE_FAILS_CLOSED,
        "FORBIDDEN_TO_PERSIST": FORBIDDEN_TO_PERSIST,
        "FORBIDDEN_IN_LOGS": FORBIDDEN_IN_LOGS,
        "FORBIDDEN_IN_PROCESS_ARGUMENTS": FORBIDDEN_IN_PROCESS_ARGUMENTS,
        "FORBIDDEN_IN_EVIDENCE": FORBIDDEN_IN_EVIDENCE,
        "EXCHANGE_CREDENTIAL_ACCESS_REACHABLE": False,
        "CREDENTIAL_PLAINTEXT_LOADED": False,
        "CREDENTIAL_LOAD_PERFORMED_IN_CAPABILITY_11_2": False,
        "plaintext_blocked": plaintext_blocked,
        "withdrawal_blocked": withdrawal_blocked,
        "persist_blocked": persist_blocked,
        "CAPABILITY_OWNER": OWNER,
    }
