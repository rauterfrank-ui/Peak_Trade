"""Transactional state history owned by the existing portfolio budget owner.

No capital authority, no DDO storage reuse and no automatic migration. Local
single-writer process recovery only; no host/power-loss proof is claimed.
"""

import fcntl
from contextlib import closing
from hashlib import sha256
import json
import os
from pathlib import Path
import sqlite3

SCHEMA = "portfolio_reservation_state.v1"
OWNER = "portfolio_capital_reservation_budget_owner_v1"


class DurableBudgetStoreError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def _read_revision(connection, account, sequence, expected_digest):
    if type(sequence) is not int or sequence <= 0:
        raise DurableBudgetStoreError("DURABLE_BUDGET_REVISION_INVALID")
    row = connection.execute(
        "SELECT previous, digest, payload FROM states WHERE seq = ?", (sequence,)
    ).fetchone()
    if row is None:
        raise DurableBudgetStoreError("DURABLE_BUDGET_REVISION_MISSING")
    prior, checksum, body = row
    payload = json.loads(body)
    if (
        checksum != digest({"seq": sequence, "previous": prior, "state": payload})
        or (expected_digest is not None and checksum != expected_digest)
        or payload.get("schema") != SCHEMA
        or payload.get("account_identity") != account
    ):
        raise DurableBudgetStoreError("DURABLE_BUDGET_REVISION_UNPROVEN")
    return {"sequence": sequence, "digest": checksum, "previous": prior, "state": payload}


def read_budget_revision_read_only_v1(root: Path, *, account_identity, sequence, expected_digest):
    """Read a digest-pinned original revision without acquiring the writer lock."""
    database = root / "reservations.sqlite3"
    if (
        not root.is_absolute()
        or root.resolve() != root
        or database.is_symlink()
        or not database.is_file()
        or not expected_digest
    ):
        raise DurableBudgetStoreError("DURABLE_BUDGET_READ_SCOPE_UNPROVEN")
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=0)) as db:
        if db.execute("PRAGMA journal_mode").fetchone() != ("delete",):
            raise DurableBudgetStoreError("DURABLE_BUDGET_JOURNAL_MODE_MISMATCH")
        if db.execute("SELECT * FROM metadata").fetchall() != [(SCHEMA, OWNER, account_identity)]:
            raise DurableBudgetStoreError("DURABLE_BUDGET_IDENTITY_MISMATCH")
        return _read_revision(db, account_identity, sequence, expected_digest)


class DurableBudgetStoreV1:
    def __init__(self, root: Path, *, account_identity: str, mode: str):
        self.root = Path(root).resolve()
        self.connection = None
        self.lock_fd = None
        self.sequence = 0
        self.head = ""
        if (
            not account_identity
            or account_identity != account_identity.strip()
            or mode not in {"create", "recover"}
        ):
            raise DurableBudgetStoreError("DURABLE_BUDGET_SCOPE_INVALID")
        self.account = account_identity
        path = self.root / "reservations.sqlite3"
        if mode == "recover" and not path.is_file():
            raise DurableBudgetStoreError("DURABLE_BUDGET_STATE_MISSING")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            self.lock_fd = os.open(self.root / "writer.lock", os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if mode == "create" and path.exists():
                raise DurableBudgetStoreError("DURABLE_BUDGET_ALREADY_EXISTS")
            self.connection = sqlite3.connect(
                path, timeout=0, isolation_level=None, check_same_thread=False
            )
            if mode == "create":
                path.chmod(0o600)
                self.connection.execute("PRAGMA journal_mode=DELETE")
                self.connection.execute("PRAGMA synchronous=FULL")
                self.connection.execute("BEGIN IMMEDIATE")
                self.connection.execute(
                    "CREATE TABLE metadata (schema TEXT, owner TEXT, account TEXT)"
                )
                self.connection.execute(
                    "CREATE TABLE states (seq INTEGER PRIMARY KEY, previous TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL)"
                )
                self.connection.execute(
                    "INSERT INTO metadata VALUES (?, ?, ?)", (SCHEMA, OWNER, self.account)
                )
                self.connection.commit()
            else:
                self.connection.execute("PRAGMA synchronous=FULL")
                if self.connection.execute("PRAGMA journal_mode").fetchone() != ("delete",):
                    raise DurableBudgetStoreError("DURABLE_BUDGET_JOURNAL_MODE_MISMATCH")
            self._verify()
        except Exception as exc:
            self.close()
            if isinstance(exc, DurableBudgetStoreError):
                raise
            raise DurableBudgetStoreError("DURABLE_BUDGET_OPEN_UNPROVEN") from exc

    def _verify(self):
        if self.connection is None or self.lock_fd is None:
            raise DurableBudgetStoreError("DURABLE_BUDGET_CLOSED")
        if self.connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise DurableBudgetStoreError("DURABLE_BUDGET_DATABASE_CORRUPT")
        if self.connection.execute("SELECT * FROM metadata").fetchall() != [
            (SCHEMA, OWNER, self.account)
        ]:
            raise DurableBudgetStoreError("DURABLE_BUDGET_IDENTITY_MISMATCH")
        previous, sequence, latest = "", 0, None
        for seq, prior, checksum, body in self.connection.execute(
            "SELECT seq, previous, digest, payload FROM states ORDER BY seq"
        ):
            payload = json.loads(body)
            if (
                seq != sequence + 1
                or prior != previous
                or checksum != digest({"seq": seq, "previous": prior, "state": payload})
            ):
                raise DurableBudgetStoreError("DURABLE_BUDGET_HISTORY_UNPROVEN")
            if payload.get("schema") != SCHEMA or payload.get("account_identity") != self.account:
                raise DurableBudgetStoreError("DURABLE_BUDGET_PAYLOAD_SCOPE_MISMATCH")
            previous, sequence, latest = checksum, seq, payload
        self.head, self.sequence = previous, sequence
        return latest

    def load(self):
        try:
            state = self._verify()
        except Exception as exc:
            if isinstance(exc, DurableBudgetStoreError):
                raise
            raise DurableBudgetStoreError("DURABLE_BUDGET_HISTORY_UNPROVEN") from exc
        if state is None:
            raise DurableBudgetStoreError("DURABLE_BUDGET_EMPTY_RECOVERY")
        return state

    def save(self, state):
        if self.connection is None:
            raise DurableBudgetStoreError("DURABLE_BUDGET_CLOSED")
        if state.get("schema") != SCHEMA or state.get("account_identity") != self.account:
            raise DurableBudgetStoreError("DURABLE_BUDGET_PAYLOAD_SCOPE_MISMATCH")
        seq = self.sequence + 1
        checksum = digest({"seq": seq, "previous": self.head, "state": state})
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            row = self.connection.execute(
                "SELECT seq, digest FROM states ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            if row != ((self.sequence, self.head) if self.sequence else None):
                raise DurableBudgetStoreError("DURABLE_BUDGET_WRITER_EPOCH_CHANGED")
            self.connection.execute(
                "INSERT INTO states VALUES (?, ?, ?, ?)",
                (seq, self.head, checksum, canonical(state)),
            )
            self.connection.commit()
            self.sequence, self.head = seq, checksum
        except Exception as exc:
            if self.connection.in_transaction:
                self.connection.rollback()
            raise DurableBudgetStoreError("DURABLE_BUDGET_COMMIT_UNPROVEN") from exc

    def read_revision_v1(self, sequence, expected_digest=None):
        """Read an exact owned history revision without moving the writer cursor."""
        if self.connection is None:
            raise DurableBudgetStoreError("DURABLE_BUDGET_REVISION_INVALID")
        return _read_revision(self.connection, self.account, sequence, expected_digest)

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            self.lock_fd = None
