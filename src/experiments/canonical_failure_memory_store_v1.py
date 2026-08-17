"""Append-only file-backed Canonical Failure Memory store v1.

Historical failure records are immutable after successful persist. Identical
canonical replay is idempotent. Divergent content for the same
``failure_record_id`` fails closed. Duplicate hypothesis fingerprints are
queryable; they never authorize an automatic research ban or runtime
mutation.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_failure_memory_v1 import (
    FailureMemoryValidationError,
    FailureRecordConflictError,
    assess_duplicate_hypothesis_v1,
    canonical_record_payload,
    freeze_canonical_failure_memory_record_v1,
    validate_canonical_failure_memory_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

RECORD_FILENAME = "canonical_failure_memory_record_v1.json"
_TMP_PREFIX = ".canonical_failure_memory_"

_LOGGER = logging.getLogger(__name__)


class CanonicalFailureMemoryStoreV1:
    """File-backed append-only failure memory."""

    def __init__(self, store_root: Path | str) -> None:
        root = Path(store_root)
        if root.exists() and not root.is_dir():
            raise FailureMemoryValidationError("store_root must be a directory")
        self._root = root

    @property
    def store_root(self) -> Path:
        return self._root

    def append(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        validate_canonical_failure_memory_record_v1(record)
        payload = canonical_record_payload(record)
        failure_record_id = str(payload["failure_record_id"])
        dest = self._record_path(failure_record_id)
        serialized = _serialize_record(payload)
        if dest.is_file():
            existing = self.get(failure_record_id)
            if _serialize_record(canonical_record_payload(existing)) == serialized:
                _LOGGER.info(
                    "canonical_failure_memory_v1 idempotent append failure_record_id=%s",
                    failure_record_id,
                )
                return existing
            raise FailureRecordConflictError(
                "divergent canonical content for existing failure_record_id is forbidden"
            )
        dest_dir = dest.parent
        if dest_dir.exists():
            leftovers = [
                path.name for path in dest_dir.iterdir() if not path.name.startswith(_TMP_PREFIX)
            ]
            if leftovers:
                raise FailureMemoryValidationError(
                    "failure directory exists without a complete immutable record"
                )
        else:
            dest_dir.mkdir(parents=True, exist_ok=False)
        _atomic_create_exclusive(dest, serialized)
        stored = self.get(failure_record_id)
        _LOGGER.info(
            "canonical_failure_memory_v1 appended failure_record_id=%s fingerprint=%s",
            failure_record_id,
            stored["hypothesis_fingerprint"],
        )
        return stored

    def get(self, failure_record_id: str) -> Mapping[str, Any]:
        path = self._record_path(failure_record_id)
        if not path.is_file():
            raise FailureMemoryValidationError(f"failure record not found: {failure_record_id}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise FailureMemoryValidationError(
                f"corrupt failure record JSON: {failure_record_id}"
            ) from exc
        if not isinstance(payload, dict):
            raise FailureMemoryValidationError("corrupt failure record root")
        validate_canonical_failure_memory_record_v1(payload)
        stored_id = str(payload.get("failure_record_id") or "")
        if stored_id != failure_record_id:
            raise FailureMemoryValidationError(
                "stored failure_record_id does not match requested id"
            )
        return freeze_canonical_failure_memory_record_v1(payload)

    def exists(self, failure_record_id: str) -> bool:
        path = self._record_path(failure_record_id)
        if not path.exists():
            return False
        self.get(failure_record_id)
        return True

    def list_records(self) -> list[Mapping[str, Any]]:
        if not self._root.exists():
            return []
        rows: list[Mapping[str, Any]] = []
        for child in sorted(self._root.iterdir(), key=lambda item: item.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if not is_valid_sha256_hex(child.name):
                raise FailureMemoryValidationError(
                    f"non-canonical directory under failure memory root: {child.name}"
                )
            rows.append(self.get(child.name))
        return rows

    def list_by_hypothesis_fingerprint(
        self, hypothesis_fingerprint: str
    ) -> list[Mapping[str, Any]]:
        if not isinstance(hypothesis_fingerprint, str) or not is_valid_sha256_hex(
            hypothesis_fingerprint
        ):
            raise FailureMemoryValidationError(
                "hypothesis_fingerprint must be a lowercase sha256 hex digest"
            )
        return [
            record
            for record in self.list_records()
            if record["hypothesis_fingerprint"] == hypothesis_fingerprint
        ]

    def assess_duplicate(
        self,
        *,
        hypothesis_fingerprint: str,
        failure_class: str | None = None,
        parameter_region: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        return assess_duplicate_hypothesis_v1(
            self.list_records(),
            hypothesis_fingerprint=hypothesis_fingerprint,
            failure_class=failure_class,
            parameter_region=parameter_region,
        )

    def _record_path(self, failure_record_id: str) -> Path:
        if not isinstance(failure_record_id, str) or not is_valid_sha256_hex(failure_record_id):
            raise FailureMemoryValidationError(
                "failure_record_id must be a lowercase sha256 hex digest"
            )
        if ".." in failure_record_id or "/" in failure_record_id or "\\" in failure_record_id:
            raise FailureMemoryValidationError("failure_record_id path traversal is forbidden")
        root = self._root.resolve()
        dest_dir = (root / failure_record_id).resolve()
        try:
            dest_dir.relative_to(root)
        except ValueError as exc:
            raise FailureMemoryValidationError("failure record path escaped store root") from exc
        dest = dest_dir / RECORD_FILENAME
        dest_resolved = dest.resolve()
        try:
            dest_resolved.relative_to(root)
        except ValueError as exc:
            raise FailureMemoryValidationError("failure record path escaped store root") from exc
        return dest


def _serialize_record(payload: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(payload) + "\n"


def _atomic_create_exclusive(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=_TMP_PREFIX,
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp_name, path)
        except FileExistsError as exc:
            existing = Path(path).read_text(encoding="utf-8")
            if existing != content:
                raise FailureRecordConflictError(
                    "divergent canonical content for existing failure_record_id is forbidden"
                ) from exc
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    else:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


__all__ = [
    "CanonicalFailureMemoryStoreV1",
    "RECORD_FILENAME",
]
