"""Durable POST authority shared by the explicit ENTER and L10-Close paths."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    canonical_json_dumps,
)

_SCHEMA = "peaktrade.post_owner_authority.v1"
_HEX_DIGEST = re.compile(r"[0-9a-f]{64}")


class SharedPostOwnerAuthorityError(ValueError):
    """The shared grant, its scope, or its durable transition is unproven."""


def _identifier(value: object) -> bool:
    return type(value) is str and bool(value) and value == value.strip()


def _digest(payload: bytes) -> str:
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class PostOwnerGrantV1:
    store_id: str
    store_binding_digest: str
    issuer_id: str
    grant_id: str
    account: str
    action: str
    envelope_digest: str
    issued_at_unix: int
    expires_at_unix: int
    signature: bytes = field(repr=False)
    environment: str = "LIVE"
    venue: str = "OKX_EEA"

    def signing_bytes_v1(self) -> bytes:
        return canonical_json_dumps(
            {
                "schema": "peaktrade.post_owner_grant.v1",
                "store_id": self.store_id,
                "store_binding_digest": self.store_binding_digest,
                "issuer_id": self.issuer_id,
                "grant_id": self.grant_id,
                "account": self.account,
                "action": self.action,
                "envelope_digest": self.envelope_digest,
                "issued_at_unix": self.issued_at_unix,
                "expires_at_unix": self.expires_at_unix,
                "environment": self.environment,
                "venue": self.venue,
            }
        ).encode()


@dataclass(frozen=True)
class PostOwnerAuthorityStoreV1:
    """Owner-provisioned path and trust anchor, supplied independently of the grant."""

    path: Path
    store_id: str
    issuer_id: str
    verify_key: bytes

    def _metadata(self) -> tuple[str, str, str, str, str]:
        if (
            not isinstance(self.path, Path)
            or not self.path.is_absolute()
            or self.path.resolve() != self.path
            or not _identifier(self.store_id)
            or not _identifier(self.issuer_id)
            or type(self.verify_key) is not bytes
            or len(self.verify_key) != 32
        ):
            raise SharedPostOwnerAuthorityError("POST_AUTHORITY_STORE_BINDING_INVALID")
        return _SCHEMA, str(self.path), self.store_id, self.issuer_id, self.verify_key.hex()

    def provision_v1(self) -> None:
        """Explicit bootstrap by the store owner. Consumers always open in read/write mode."""
        metadata = self._metadata()
        try:
            with os.fdopen(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "wb"):
                pass
            with self._transaction(provision=True) as (db, _):
                db.execute(
                    "CREATE TABLE authority (schema TEXT, path TEXT, store_id TEXT, "
                    "issuer_id TEXT, verify_key TEXT, generation TEXT NOT NULL)"
                )
                db.execute(
                    "INSERT INTO authority VALUES (?, ?, ?, ?, ?, ?)",
                    (*metadata, secrets.token_hex(32)),
                )
                db.execute(
                    "CREATE TABLE claims (grant_id TEXT PRIMARY KEY NOT NULL, grant_digest TEXT NOT NULL, "
                    "claim_digest TEXT NOT NULL, consumed_at REAL NOT NULL, dispatch_started_at REAL)"
                )
                db.execute(
                    "CREATE TABLE revocations (grant_id TEXT PRIMARY KEY NOT NULL, "
                    "record_digest TEXT NOT NULL, revoked_at REAL NOT NULL)"
                )
            directory_fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as exc:
            raise SharedPostOwnerAuthorityError("POST_AUTHORITY_STORE_PROVISION_FAILED") from exc

    @contextmanager
    def _transaction(self, *, provision: bool = False):
        metadata = self._metadata()
        db = None
        try:
            db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, isolation_level=None)
            if db.execute("PRAGMA journal_mode").fetchone() != ("delete",):
                raise SharedPostOwnerAuthorityError("POST_AUTHORITY_JOURNAL_MODE_INVALID")
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            binding = ""
            if not provision:
                rows = db.execute("SELECT * FROM authority").fetchall()
                if (
                    len(rows) != 1
                    or rows[0][:-1] != metadata
                    or type(rows[0][-1]) is not str
                    or not _HEX_DIGEST.fullmatch(rows[0][-1])
                ):
                    raise SharedPostOwnerAuthorityError("POST_AUTHORITY_STORE_IDENTITY_MISMATCH")
                binding = _digest(canonical_json_dumps({"authority": rows[0]}).encode())
            yield db, binding
            db.commit()
        except sqlite3.Error as exc:
            raise SharedPostOwnerAuthorityError("POST_AUTHORITY_STORE_UNPROVEN") from exc
        finally:
            if db is not None:
                db.close()

    def _verify(self, body: bytes, signature: bytes) -> None:
        try:
            VerifyKey(self.verify_key).verify(body, signature)
        except (BadSignatureError, TypeError, ValueError) as exc:
            raise SharedPostOwnerAuthorityError("POST_GRANT_SIGNATURE_UNPROVEN") from exc

    def binding_digest_v1(self) -> str:
        """Read the signing binding of the current provisioned store generation."""
        with self._transaction() as (_, binding):
            return binding

    def _revocation_body(self, grant_id: str, binding: str) -> bytes:
        if not _identifier(grant_id):
            raise SharedPostOwnerAuthorityError("POST_GRANT_ID_INVALID")
        return canonical_json_dumps(
            {
                "schema": "peaktrade.post_owner_revocation.v1",
                "store_id": self.store_id,
                "store_binding_digest": binding,
                "issuer_id": self.issuer_id,
                "grant_id": grant_id,
            }
        ).encode()

    def revocation_signing_bytes_v1(self, grant_id: str) -> bytes:
        return self._revocation_body(grant_id, self.binding_digest_v1())

    def revoke_v1(self, grant_id: str, signature: bytes) -> None:
        with self._transaction() as (db, binding):
            body = self._revocation_body(grant_id, binding)
            self._verify(body, signature)
            db.execute(
                "INSERT INTO revocations VALUES (?, ?, ?) ON CONFLICT(grant_id) DO NOTHING",
                (grant_id, _digest(body), time.time()),
            )


@dataclass(frozen=True)
class SharedPostOwnerAuthorizationV1:
    authority: PostOwnerAuthorityStoreV1
    grant: PostOwnerGrantV1

    def consume_v1(
        self, *, account: str, action: str, envelope_digest: str, attempt_root: Path
    ) -> SharedPostOwnerClaimV1:
        grant = self.grant
        if (
            type(self.authority) is not PostOwnerAuthorityStoreV1
            or type(grant) is not PostOwnerGrantV1
            or not _identifier(grant.grant_id)
            or not _identifier(grant.account)
            or type(grant.issued_at_unix) is not int
            or type(grant.expires_at_unix) is not int
        ):
            raise SharedPostOwnerAuthorityError("POST_GRANT_INVALID")
        if grant.issuer_id != self.authority.issuer_id or grant.store_id != self.authority.store_id:
            raise SharedPostOwnerAuthorityError("POST_GRANT_ISSUER_OR_STORE_MISMATCH")
        if (
            grant.account != account
            or grant.action != action
            or action not in {"ENTER", "L10_CLOSE"}
            or grant.environment != "LIVE"
            or grant.venue != "OKX_EEA"
            or grant.envelope_digest != envelope_digest
            or type(envelope_digest) is not str
            or not _HEX_DIGEST.fullmatch(envelope_digest)
        ):
            raise SharedPostOwnerAuthorityError("POST_GRANT_SCOPE_MISMATCH")
        body = grant.signing_bytes_v1()
        self.authority._verify(body, grant.signature)
        claim = SharedPostOwnerClaimV1(
            self.authority, grant, _digest(body), attempt_root.resolve(), secrets.token_hex(32)
        )
        with self.authority._transaction() as (db, binding):
            if grant.store_binding_digest != binding:
                raise SharedPostOwnerAuthorityError("POST_GRANT_STORE_BINDING_MISMATCH")
            now = _require_current(db, grant)
            if (
                db.execute("SELECT 1 FROM claims WHERE grant_id=?", (grant.grant_id,)).fetchone()
                is not None
            ):
                raise SharedPostOwnerAuthorityError("POST_GRANT_ALREADY_CONSUMED")
            db.execute(
                "INSERT INTO claims VALUES (?, ?, ?, ?, NULL)",
                (grant.grant_id, claim.grant_digest, claim.receipt_digest_v1(), now),
            )
        return claim


def _require_current(db: sqlite3.Connection, grant: PostOwnerGrantV1) -> float:
    now = time.time()
    if not grant.issued_at_unix <= now < grant.expires_at_unix:
        raise SharedPostOwnerAuthorityError("POST_GRANT_OUTSIDE_VALIDITY")
    if db.execute("SELECT 1 FROM revocations WHERE grant_id=?", (grant.grant_id,)).fetchone():
        raise SharedPostOwnerAuthorityError("POST_GRANT_REVOKED")
    return now


@dataclass(frozen=True)
class SharedPostOwnerClaimV1:
    authority: PostOwnerAuthorityStoreV1
    grant: PostOwnerGrantV1
    grant_digest: str
    attempt_root: Path
    nonce: str = field(repr=False)

    def receipt_digest_v1(self) -> str:
        return _digest(
            canonical_json_dumps(
                {
                    "grant_digest": self.grant_digest,
                    "attempt_root": str(self.attempt_root),
                    "nonce": self.nonce,
                }
            ).encode()
        )

    def inspect_v1(
        self, *, envelope_digest: str, attempt_root: Path, account: str, action: str
    ) -> None:
        if (
            self.attempt_root != attempt_root.resolve()
            or self.grant.envelope_digest != envelope_digest
            or self.grant.account != account
            or self.grant.action != action
        ):
            raise SharedPostOwnerAuthorityError("POST_GRANT_CLAIM_SCOPE_MISMATCH")
        self.recheck_v1()

    def _require_unstarted_claim(self, db: sqlite3.Connection, binding: str) -> float:
        if (
            self.grant.store_binding_digest != binding
            or _digest(self.grant.signing_bytes_v1()) != self.grant_digest
        ):
            raise SharedPostOwnerAuthorityError("POST_GRANT_CLAIM_UNPROVEN")
        now = _require_current(db, self.grant)
        row = db.execute(
            "SELECT grant_digest, claim_digest, dispatch_started_at FROM claims WHERE grant_id=?",
            (self.grant.grant_id,),
        ).fetchone()
        if not row or row[:2] != (self.grant_digest, self.receipt_digest_v1()):
            raise SharedPostOwnerAuthorityError("POST_GRANT_CLAIM_UNPROVEN")
        if row[2] is not None:
            raise SharedPostOwnerAuthorityError("POST_GRANT_DISPATCH_ALREADY_STARTED")
        return now

    def recheck_v1(self) -> None:
        with self.authority._transaction() as (db, binding):
            self._require_unstarted_claim(db, binding)

    def start_dispatch_v1(self) -> None:
        with self.authority._transaction() as (db, binding):
            now = self._require_unstarted_claim(db, binding)
            db.execute(
                "UPDATE claims SET dispatch_started_at=? WHERE grant_id=?",
                (now, self.grant.grant_id),
            )
