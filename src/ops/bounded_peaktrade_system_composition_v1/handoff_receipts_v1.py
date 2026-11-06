"""Immutable coordination receipts, never a second financial state owner.

Recovery only compares verified original-owner readback. This module cannot
apply, roll back, release, resend or clear a safety barrier.
"""

from dataclasses import asdict, dataclass
import fcntl
import json
import os
from pathlib import Path

from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from .session_v1 import _write


def _sha(value):
    if (
        type(value) is not str
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
    ):
        raise ValueError("HANDOFF_DIGEST_REQUIRED")


@dataclass(frozen=True)
class HandoffRequestV1:
    session_manifest_digest: str
    transition_id: str
    source_owner: str
    target_owner: str
    original_input_digest: str
    expected_original_output_digest: str
    original_output_reference: str

    def validate_v1(self):
        for value in (
            self.session_manifest_digest,
            self.original_input_digest,
            self.expected_original_output_digest,
        ):
            _sha(value)
        if self.target_owner not in {
            "original_exit",
            "original_cursor",
            "original_budget",
            "original_accounting_source",
        }:
            raise ValueError("HANDOFF_OWNER_NOT_ALLOWLISTED")
        for value in (self.transition_id, self.source_owner, self.original_output_reference):
            if type(value) is not str or not value or value != value.strip():
                raise ValueError("HANDOFF_EXACT_REFERENCE_REQUIRED")


class OfflineHandoffJournalV1:
    def __init__(self, *, root, session_manifest_digest):
        _sha(session_manifest_digest)
        self.root = Path(root)
        if not self.root.is_absolute() or self.root != self.root.resolve():
            raise ValueError("HANDOFF_CANONICAL_ROOT_REQUIRED")
        self.scope = session_manifest_digest
        self.fd = None

    def __enter__(self):
        if self.fd is not None:
            raise ValueError("HANDOFF_ALREADY_OPEN")
        self.root.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.root / "writer.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            path = self.root / "scope.json"
            value = {"schema": "offline_handoff_scope.v1", "session_manifest_digest": self.scope}
            if path.exists():
                if json.loads(path.read_text()) != value:
                    raise ValueError("HANDOFF_FOREIGN_SESSION")
            else:
                _write(path, value)
        except BaseException:
            os.close(self.fd)
            self.fd = None
            raise
        return self

    def __exit__(self, *_):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def _path(self, request):
        if self.fd is None or type(request) is not HandoffRequestV1:
            raise ValueError("HANDOFF_OPEN_TYPED_REQUEST_REQUIRED")
        request.validate_v1()
        if request.session_manifest_digest != self.scope:
            raise ValueError("HANDOFF_FOREIGN_SESSION")
        if json.loads((self.root / "scope.json").read_text()) != {
            "schema": "offline_handoff_scope.v1",
            "session_manifest_digest": self.scope,
        }:
            raise ValueError("HANDOFF_SCOPE_CHANGED")
        # Same transition label cannot acquire a new identity by changing values.
        return self.root / digest({"session": self.scope, "transition": request.transition_id})

    def prepare_v1(self, request):
        path = self._path(request)
        payload = {
            "schema": "offline_handoff_prepared.v1",
            "request": asdict(request),
            "request_digest": digest(asdict(request)),
        }
        if path.exists():
            if json.loads(path.read_text()) != payload:
                raise ValueError("HANDOFF_PREPARED_CONFLICT")
        else:
            _write(path, payload)
        return payload["request_digest"]

    def inspect_original_readback_v1(self, request, *, verified_original_output_digest):
        path = self._path(request)
        expected = {
            "schema": "offline_handoff_prepared.v1",
            "request": asdict(request),
            "request_digest": digest(asdict(request)),
        }
        if not path.is_file() or json.loads(path.read_text()) != expected:
            raise ValueError("HANDOFF_PREPARED_MISSING_OR_CORRUPT")
        _sha(verified_original_output_digest)
        ack = path.with_suffix(".ack.json")
        value = {
            "schema": "offline_handoff_ack.v1",
            "prepared_digest": digest(expected),
            "verified_original_output_digest": request.expected_original_output_digest,
        }
        if ack.exists() and json.loads(ack.read_text()) != value:
            raise ValueError("HANDOFF_ACK_CORRUPT")
        if verified_original_output_digest != request.expected_original_output_digest:
            return {
                "status": "RECOVERY_REQUIRED",
                "automatic_owner_action": False,
                "resend_allowed": False,
            }
        if not ack.exists():
            _write(ack, value)
        return {"status": "ACKNOWLEDGED", "automatic_owner_action": False, "resend_allowed": False}

    def require_original_reservation_ack_v1(self, *, reservation_id, original_input_digest):
        path = self.root / digest(
            {"session": self.scope, "transition": "risk-reserve:" + str(reservation_id)}
        )
        if not path.is_file():
            raise ValueError("HANDOFF_PREPARED_MISSING_OR_CORRUPT")
        prepared = json.loads(path.read_text())
        if not isinstance(prepared, dict) or set(prepared) != {
            "schema",
            "request",
            "request_digest",
        }:
            raise ValueError("HANDOFF_PREPARED_MISSING_OR_CORRUPT")
        request = HandoffRequestV1(**prepared["request"])
        if (
            self._path(request) != path
            or request.target_owner != "original_budget"
            or request.original_input_digest != original_input_digest
            or request.original_output_reference != "portfolio-reservation:" + str(reservation_id)
        ):
            raise ValueError("HANDOFF_ORIGINAL_RESERVATION_UNPROVEN")
        if prepared != {
            "schema": "offline_handoff_prepared.v1",
            "request": asdict(request),
            "request_digest": digest(asdict(request)),
        }:
            raise ValueError("HANDOFF_PREPARED_MISSING_OR_CORRUPT")
        ack = path.with_suffix(".ack.json")
        expected = {
            "schema": "offline_handoff_ack.v1",
            "prepared_digest": digest(prepared),
            "verified_original_output_digest": request.expected_original_output_digest,
        }
        if not ack.is_file() or json.loads(ack.read_text()) != expected:
            raise ValueError("HANDOFF_ORIGINAL_READBACK_ACK_REQUIRED")
        return expected
