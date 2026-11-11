"""Signed, scope-bound evidence and releases for the managed FILEGATE writer."""

from dataclasses import dataclass
from hashlib import sha256
import math
import re

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
    canonical_json_text,
)

EVIDENCE_ROLES = frozenset({"CAUSE", "ACCOUNT", "HOST"})
RECOVERABLE_CAUSES = frozenset({"R01", "R02", "R03", "R04", "R05", "R06"})


class FilegateAuthorityError(ValueError):
    pass


@dataclass(frozen=True)
class FilegateRecoveryScopeV1:
    account: str
    environment: str
    host: str
    instruments: tuple[str, ...]
    original_stores_sha256: str

    def binding_v1(self):
        if (
            self.environment not in {"LIVE", "SHADOW", "INTERNAL_SIMULATED_EXECUTION"}
            or not self.instruments
            or tuple(sorted(set(self.instruments))) != self.instruments
            or not all(
                type(value) is str and value and value == value.strip()
                for value in (self.account, self.host, *self.instruments)
            )
            or not is_digest_v1(self.original_stores_sha256)
        ):
            raise FilegateAuthorityError("FILEGATE_RECOVERY_SCOPE_INVALID")
        return {
            "account": self.account,
            "environment": self.environment,
            "host": self.host,
            "instruments": list(self.instruments),
            "original_stores_sha256": self.original_stores_sha256,
        }


def is_digest_v1(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def public_key_hex_v1(key):
    if type(key) is not bytes or len(key) != 32:
        raise FilegateAuthorityError("FILEGATE_AUTHORITY_KEY_INVALID")
    return key.hex()


def _signed(body, key):
    if not isinstance(key, SigningKey):
        raise FilegateAuthorityError("FILEGATE_SIGNING_KEY_REQUIRED")
    signature = key.sign(canonical_json_dumps(body).encode()).signature.hex()
    return {"body": body, "signature": signature}


def _verify(envelope, key):
    try:
        body = envelope["body"]
        if set(envelope) == {"body", "signature"} and type(body) is dict:
            public_key = VerifyKey(bytes.fromhex(key))
            public_key.verify(
                canonical_json_dumps(body).encode(), bytes.fromhex(envelope["signature"])
            )
            return body
    except (BadSignatureError, KeyError, TypeError, ValueError):
        pass
    raise FilegateAuthorityError("FILEGATE_SIGNATURE_UNPROVEN")


def _current(body, now):
    issued_at, expires_at = body["observed_at"], body["expires_at"]
    if not (
        all(
            type(value) in {float, int} and math.isfinite(value)
            for value in (issued_at, now, expires_at)
        )
        and issued_at <= now < expires_at
    ):
        raise FilegateAuthorityError("FILEGATE_AUTHORITY_EXPIRED_OR_NOT_YET_VALID")


def attest_filegate_owner_evidence_v1(*, role, stop, evidence_sha256, observed_at, expires_at, key):
    """Called by the responsible owner after it has independently verified its result."""
    if role not in EVIDENCE_ROLES or not is_digest_v1(evidence_sha256):
        raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_INVALID")
    body = {
        "schema": "filegate_owner_evidence.v1",
        "role": role,
        "stop": stop,
        "evidence_sha256": evidence_sha256,
        "observed_at": observed_at,
        "expires_at": expires_at,
    }
    _current(body, observed_at)
    return _signed(body, key)


def verify_filegate_owner_evidence_v1(*, evidence, stop, owner_keys, now):
    if set(evidence) != EVIDENCE_ROLES or set(owner_keys) != EVIDENCE_ROLES:
        raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_COVERAGE_UNPROVEN")
    proofs = {}
    for role in sorted(EVIDENCE_ROLES):
        body = _verify(evidence[role], owner_keys[role])
        _current(body, now)
        if (
            body["schema"] != "filegate_owner_evidence.v1"
            or body["role"] != role
            or body["stop"] != stop
            or body["observed_at"] < stop["killed_at"]
            or not is_digest_v1(body["evidence_sha256"])
        ):
            raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_BINDING_CHANGED")
        proofs[role] = body
    return proofs


def _release_body(*, stop, evidence, trust, now):
    if not set(stop["causes"]) <= set(trust["recoverable_causes"]):
        raise FilegateAuthorityError("FILEGATE_CAUSE_REQUIRES_SEPARATE_AUTHORITY")
    proofs = verify_filegate_owner_evidence_v1(
        evidence=evidence, stop=stop, owner_keys=trust["owners"], now=now
    )
    return {
        "schema": "filegate_release.v1",
        "stop": stop,
        "observed_at": now,
        "expires_at": min(proof["expires_at"] for proof in proofs.values()),
        "owner_signatures": {role: evidence[role]["signature"] for role in sorted(proofs)},
    }


def issue_filegate_release_v1(*, stop, evidence, trust, issuer_key, now):
    """Issue only for a ratified cause with all three independent, fresh owner proofs."""
    if not isinstance(issuer_key, SigningKey) or (
        bytes(issuer_key.verify_key).hex() != trust["issuer"]
    ):
        raise FilegateAuthorityError("FILEGATE_ISSUER_UNPROVEN")
    return _signed(_release_body(stop=stop, evidence=evidence, trust=trust, now=now), issuer_key)


def verify_filegate_release_v1(*, release, stop, evidence, trust, now):
    body = _verify(release, trust["issuer"])
    _current(body, now)
    expected = _release_body(
        stop=stop,
        evidence=evidence,
        trust=trust,
        now=body["observed_at"],
    )
    if body != expected:
        raise FilegateAuthorityError("FILEGATE_RELEASE_BINDING_CHANGED")
    return body


def sign_filegate_revocation_v1(*, release, issuer_key):
    return _signed(
        {
            "schema": "filegate_release_revocation.v1",
            "release_sha256": sha256(canonical_json_text(release).encode()).hexdigest(),
        },
        issuer_key,
    )


def verify_filegate_revocation_v1(revocation, issuer_public_key):
    body = _verify(revocation, issuer_public_key)
    if body.get("schema") != "filegate_release_revocation.v1" or not is_digest_v1(
        body.get("release_sha256")
    ):
        raise FilegateAuthorityError("FILEGATE_REVOCATION_UNPROVEN")
    return body["release_sha256"]


def sign_filegate_protection_v1(
    *,
    stop,
    permit_id,
    approved_body_sha256,
    observed_at,
    expires_at,
    key,
):
    """An existing protection owner authorizes one exact reduce-only body."""
    if not is_digest_v1(permit_id) or not is_digest_v1(approved_body_sha256):
        raise FilegateAuthorityError("FILEGATE_PROTECTION_BINDING_INVALID")
    body = {
        "schema": "filegate_reduce_only_permit.v1",
        "stop": stop,
        "permit_id": permit_id,
        "approved_body_sha256": approved_body_sha256,
        "observed_at": observed_at,
        "expires_at": expires_at,
    }
    _current(body, observed_at)
    return _signed(body, key)


def verify_filegate_protection_v1(*, permit, stop, approved_body_sha256, public_key, now):
    body = _verify(permit, public_key)
    _current(body, now)
    if (
        body["schema"] != "filegate_reduce_only_permit.v1"
        or body["stop"] != stop
        or body["approved_body_sha256"] != approved_body_sha256
        or not is_digest_v1(body["permit_id"])
    ):
        raise FilegateAuthorityError("FILEGATE_PROTECTION_BINDING_INVALID")
    return body
