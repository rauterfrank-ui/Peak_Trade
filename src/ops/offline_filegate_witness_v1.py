"""Separate signed FILEGATE head for the isolated recovery profile."""

from hashlib import sha256
import hmac
import json
import os
from pathlib import Path

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    atomic_write_json,
    canonical_json_dumps,
    canonical_json_text,
)
from src.ops.offline_public_feed_recovery_v1 import OfflinePublicFeedRecoveryError

_SCHEMA = "offline_filegate_witness.v1"


class OfflineFilegateWitnessV1:
    """Keep the latest signed generation outside the local runtime/diagnostic root.

    All operations run under the isolated Safety writer lock. The witness directory
    must be supplied by the deployment and kept outside the runtime's rollback set.
    """

    def __init__(self, *, directory: Path, state_path: Path, key: bytes):
        self.directory = directory
        self.state_path = state_path
        if type(key) is not bytes or len(key) < 32:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_KEY_REQUIRED")
        self._key = key
        self.path = directory / f"{sha256(str(state_path).encode()).hexdigest()}.json"

    def _require_scope(self):
        directory = self.directory
        runtime_root = self.state_path.parent
        if (
            not directory.is_absolute()
            or directory.resolve() != directory
            or not directory.is_dir()
            or directory.stat().st_uid != os.getuid()
            or directory.stat().st_mode & 0o077
            or directory.is_relative_to(runtime_root)
            or runtime_root.is_relative_to(directory)
            or any(
                path.resolve() != path or (path.exists() and not path.is_file())
                for path in (self.path, self.path.with_suffix(".json.tmp"))
            )
        ):
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_SCOPE_UNPROVEN")

    def _sign(self, body):
        return hmac.digest(self._key, canonical_json_dumps(body).encode(), "sha256").hex()

    def read_v1(self):
        self._require_scope()
        try:
            envelope = json.loads(self.path.read_bytes())
            body = envelope["body"]
            if (
                set(envelope) == {"body", "signature"}
                and body["schema"] == _SCHEMA
                and body["state_path"] == str(self.state_path)
                and type(body["generation"]) is int
                and body["generation"] > 0
                and body["state"] in {"KILLED", "ACTIVE"}
                and len(bytes.fromhex(body["filegate_sha256"])) == 32
                and hmac.compare_digest(envelope["signature"], self._sign(body))
            ):
                return body
        except (OSError, KeyError, TypeError, ValueError):
            pass
        raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_HEAD_UNPROVEN")

    def bootstrap_v1(self, raw: bytes):
        self._require_scope()
        if self.path.exists() or self.path.with_suffix(".json.tmp").exists():
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_ALREADY_INITIALIZED")
        self._write(raw, state="KILLED", previous=None)

    def publish_v1(self, payload: dict):
        previous = self.read_v1()
        self._write(
            canonical_json_text(payload).encode(), state=payload["state"], previous=previous
        )

    def _write(self, raw, *, state, previous):
        if json.loads(raw)["state"] != state or state not in {"KILLED", "ACTIVE"}:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_INVALID_STATE")
        body = {
            "schema": _SCHEMA,
            "state_path": str(self.state_path),
            "generation": 1 if previous is None else previous["generation"] + 1,
            "previous_head": None if previous is None else self._sign(previous),
            "state": state,
            "filegate_sha256": sha256(raw).hexdigest(),
        }
        atomic_write_json(path=self.path, payload={"body": body, "signature": self._sign(body)})
        if self.read_v1() != body:
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_READBACK_UNPROVEN")

    def require_match_v1(self, raw: bytes, *, state: str):
        head = self.read_v1()
        if head["state"] != state or head["filegate_sha256"] != sha256(raw).hexdigest():
            raise OfflinePublicFeedRecoveryError("FILEGATE_WITNESS_STATE_MISMATCH")
        return head
