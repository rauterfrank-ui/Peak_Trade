"""Account-identity boundary contract for Cap 11.2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_IDENTITY_BOUNDARY_OWNER,
    ACCOUNT_SCOPE_EXPLICIT,
)


class AccountIdentityViolationError(ValueError):
    """Fail-closed account-identity boundary violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class AccountIdentityRecordV1:
    """Explicit account identity bound to venue and credential reference."""

    account_identity: str
    venue: str
    credential_ref_id: str
    account_scope: str
    expected_uid: str

    def digest(self) -> str:
        material = {
            "account_identity": self.account_identity,
            "venue": self.venue,
            "credential_ref_id": self.credential_ref_id,
            "account_scope": self.account_scope,
            "expected_uid": self.expected_uid,
        }
        return hashlib.sha256(_canonical_dumps(material).encode("utf-8")).hexdigest()


def build_account_identity_record_v1(
    *,
    account_identity: str,
    venue: str,
    credential_ref_id: str,
    account_scope: str,
    expected_uid: str,
) -> AccountIdentityRecordV1:
    if not account_identity:
        raise AccountIdentityViolationError("ACCOUNT_IDENTITY_REQUIRED")
    if not venue:
        raise AccountIdentityViolationError("VENUE_REQUIRED")
    if not credential_ref_id:
        raise AccountIdentityViolationError("CREDENTIAL_REF_REQUIRED")
    if not account_scope:
        raise AccountIdentityViolationError("ACCOUNT_SCOPE_REQUIRED")
    if not expected_uid:
        raise AccountIdentityViolationError("EXPECTED_UID_REQUIRED")
    if account_identity != expected_uid:
        raise AccountIdentityViolationError("ACCOUNT_IDENTITY_UID_MISMATCH")
    return AccountIdentityRecordV1(
        account_identity=account_identity,
        venue=venue,
        credential_ref_id=credential_ref_id,
        account_scope=account_scope,
        expected_uid=expected_uid,
    )


def validate_account_identity_v1(
    record: AccountIdentityRecordV1,
    *,
    observed_account_identity: str,
    observed_venue: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    if not observed_account_identity:
        blockers.append("UNKNOWN_ACCOUNT_IDENTITY")
    elif observed_account_identity != record.account_identity:
        blockers.append("ACCOUNT_IDENTITY_MISMATCH")
    if observed_venue != record.venue:
        blockers.append("VENUE_ACCOUNT_SCOPE_MISMATCH")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "ACCOUNT_SCOPE_EXPLICIT": ACCOUNT_SCOPE_EXPLICIT,
        "account_identity": record.account_identity,
        "owner": ACCOUNT_IDENTITY_BOUNDARY_OWNER,
    }


def prove_account_identity_boundary_v1() -> dict[str, Any]:
    record = build_account_identity_record_v1(
        account_identity="acct-uid-demo",
        venue="OKX",
        credential_ref_id="cred-ref-demo",
        account_scope="trading-only",
        expected_uid="acct-uid-demo",
    )
    match = validate_account_identity_v1(
        record,
        observed_account_identity="acct-uid-demo",
        observed_venue="OKX",
    )
    mismatch = validate_account_identity_v1(
        record,
        observed_account_identity="other-acct",
        observed_venue="OKX",
    )
    unknown = validate_account_identity_v1(
        record,
        observed_account_identity="",
        observed_venue="OKX",
    )
    uid_mismatch_blocked = False
    try:
        build_account_identity_record_v1(
            account_identity="acct-a",
            venue="OKX",
            credential_ref_id="cred-ref-demo",
            account_scope="trading-only",
            expected_uid="acct-b",
        )
    except AccountIdentityViolationError:
        uid_mismatch_blocked = True

    ok = all(
        [
            match.get("ok") is True,
            mismatch.get("ok") is False,
            unknown.get("ok") is False,
            "UNKNOWN_ACCOUNT_IDENTITY" in unknown.get("blockers", []),
            uid_mismatch_blocked,
            ACCOUNT_SCOPE_EXPLICIT is True,
        ]
    )
    return {
        "ok": ok,
        "owner": ACCOUNT_IDENTITY_BOUNDARY_OWNER,
        "account_identity_digest": record.digest(),
        "match_ok": match.get("ok") is True,
        "mismatch_fail_closed": mismatch.get("ok") is False,
        "unknown_fail_closed": unknown.get("ok") is False,
        "uid_mismatch_blocked": uid_mismatch_blocked,
        "ACCOUNT_SCOPE_EXPLICIT": ACCOUNT_SCOPE_EXPLICIT,
    }
