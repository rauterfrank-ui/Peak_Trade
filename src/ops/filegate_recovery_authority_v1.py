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


def require_filegate_execution_incidents_v1(stop):
    """Return every incident that must be resolved for the current R04 stop."""
    incidents = stop.get("execution_incident_ids")
    if (
        "R04" not in stop["causes"]
        or type(incidents) is not list
        or not incidents
        or not all(is_digest_v1(incident) for incident in incidents)
        or incidents != sorted(set(incidents))
    ):
        raise FilegateAuthorityError("FILEGATE_EXECUTION_INCIDENT_BINDING_UNPROVEN")
    return tuple(incidents)


def require_filegate_loss_violation_v1(violation, *, scope):
    if (
        type(violation) is not dict
        or set(violation) != {"rule", "scope", "policy_sha256", "observation_sha256"}
        or violation["rule"] != "RISK_GATE_SESSION_LOSS_LIMIT_V1"
        or violation["scope"] != scope
        or not is_digest_v1(violation["policy_sha256"])
        or not is_digest_v1(violation["observation_sha256"])
    ):
        raise FilegateAuthorityError("FILEGATE_RISK_VIOLATION_BINDING_UNPROVEN")
    return violation


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
    issued_at, expires_at = body.get("observed_at"), body.get("expires_at")
    if not (
        all(
            type(value) in {float, int} and math.isfinite(value)
            for value in (issued_at, now, expires_at)
        )
        and issued_at <= now < expires_at
    ):
        raise FilegateAuthorityError("FILEGATE_AUTHORITY_EXPIRED_OR_NOT_YET_VALID")


def attest_filegate_owner_evidence_v1(
    *, role, stop, evidence_sha256, observed_at, expires_at, key, cause=None
):
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
    if cause is not None:
        if role != "CAUSE" or cause not in RECOVERABLE_CAUSES or cause not in stop["causes"]:
            raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_INVALID")
        body["cause"] = cause
    _current(body, observed_at)
    return _signed(body, key)


def requires_cause_proof_set_v1(stop, cause_keys):
    return len(stop["causes"]) != 1 or stop["causes"][0] in cause_keys


def verify_filegate_owner_proof_v1(*, proof, key, role, stop, now, cause=None, require_cause=False):
    body = _verify(proof, key)
    _current(body, now)
    if (
        body.get("schema") != "filegate_owner_evidence.v1"
        or body.get("role") != role
        or body.get("stop") != stop
        or body["observed_at"] < stop["killed_at"]
        or not is_digest_v1(body.get("evidence_sha256"))
        or ("cause" in body and (cause is None or body["cause"] != cause))
        or (require_cause and "cause" not in body)
    ):
        raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_BINDING_CHANGED")
    return body["expires_at"]


def _release_body(*, stop, evidence, trust, now):
    causes = set(stop["causes"])
    if not causes or not causes <= set(trust["recoverable_causes"]):
        raise FilegateAuthorityError("FILEGATE_CAUSE_REQUIRES_SEPARATE_AUTHORITY")
    if "R04" in causes:
        require_filegate_execution_incidents_v1(stop)
    if "R05" in causes:
        require_filegate_loss_violation_v1(stop.get("risk_violation"), scope=stop["scope"])
    owners = trust["owners"]
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_ROLES:
        raise FilegateAuthorityError("FILEGATE_OWNER_EVIDENCE_COVERAGE_UNPROVEN")
    signatures = {}
    expirations = []
    for role in ("ACCOUNT", "HOST"):
        proof = evidence[role]
        expirations.append(
            verify_filegate_owner_proof_v1(
                proof=proof, key=owners[role], role=role, stop=stop, now=now
            )
        )
        signatures[role] = proof["signature"]

    cause_keys = trust.get("cause_keys", {})
    cause_proof = evidence["CAUSE"]
    if requires_cause_proof_set_v1(stop, cause_keys):
        if (
            not isinstance(cause_proof, dict)
            or set(cause_proof) != causes
            or not causes <= cause_keys.keys()
        ):
            raise FilegateAuthorityError("FILEGATE_CAUSE_EVIDENCE_COVERAGE_UNPROVEN")
        signatures["CAUSE"] = {}
        for cause in stop["causes"]:
            proof = cause_proof[cause]
            expirations.append(
                verify_filegate_owner_proof_v1(
                    proof=proof,
                    key=cause_keys[cause],
                    role="CAUSE",
                    stop=stop,
                    now=now,
                    cause=cause,
                    require_cause=True,
                )
            )
            signatures["CAUSE"][cause] = proof["signature"]
    else:
        expirations.append(
            verify_filegate_owner_proof_v1(
                proof=cause_proof,
                key=owners["CAUSE"],
                role="CAUSE",
                stop=stop,
                now=now,
                cause=stop["causes"][0],
            )
        )
        signatures["CAUSE"] = cause_proof["signature"]
    return {
        "schema": "filegate_release.v1",
        "stop": stop,
        "observed_at": now,
        "expires_at": min(expirations),
        "owner_signatures": signatures,
    }


def issue_filegate_release_v1(*, stop, evidence, trust, issuer_key, now):
    """Issue only with fresh evidence from every responsible owner."""
    if not isinstance(issuer_key, SigningKey) or (
        bytes(issuer_key.verify_key).hex() != trust["issuer"]
    ):
        raise FilegateAuthorityError("FILEGATE_ISSUER_UNPROVEN")
    return _signed(_release_body(stop=stop, evidence=evidence, trust=trust, now=now), issuer_key)


def verify_filegate_release_v1(*, release, stop, evidence, trust, now):
    body = _verify(release, trust["issuer"])
    _current(body, now)
    if body.get("stop") != stop:
        raise FilegateAuthorityError("FILEGATE_RELEASE_BINDING_CHANGED")
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
