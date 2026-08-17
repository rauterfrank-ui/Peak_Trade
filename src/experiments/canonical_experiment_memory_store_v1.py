"""Append-only file-backed Canonical Experiment Memory store v1.

Historical records are immutable after successful persist. Identical
canonical replay is idempotent. Divergent content for the same
``experiment_id`` fails closed. This store cannot mutate runtime config,
live overrides, orders, funding, risk, leverage, or promotion authority.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_experiment_memory_v1 import (
    ExperimentMemoryValidationError,
    ExperimentRecordConflictError,
    canonical_record_payload,
    freeze_canonical_experiment_memory_record_v1,
    validate_canonical_experiment_memory_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

RECORD_FILENAME = "canonical_experiment_memory_record_v1.json"
_TMP_PREFIX = ".canonical_experiment_memory_"

_LOGGER = logging.getLogger(__name__)


class CanonicalExperimentMemoryStoreV1:
    """File-backed append-only experiment memory."""

    def __init__(self, store_root: Path | str) -> None:
        root = Path(store_root)
        if root.exists() and not root.is_dir():
            raise ExperimentMemoryValidationError("store_root must be a directory")
        self._root = root

    @property
    def store_root(self) -> Path:
        return self._root

    def append(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        validate_canonical_experiment_memory_record_v1(record)
        payload = canonical_record_payload(record)
        experiment_id = str(payload["experiment_id"])
        dest = self._record_path(experiment_id)
        serialized = _serialize_record(payload)
        if dest.is_file():
            existing = self.get(experiment_id)
            if _serialize_record(canonical_record_payload(existing)) == serialized:
                _LOGGER.info(
                    "canonical_experiment_memory_v1 idempotent append experiment_id=%s",
                    experiment_id,
                )
                return existing
            raise ExperimentRecordConflictError(
                "divergent canonical content for existing experiment_id is forbidden"
            )
        dest_dir = dest.parent
        if dest_dir.exists():
            leftovers = [
                path.name for path in dest_dir.iterdir() if not path.name.startswith(_TMP_PREFIX)
            ]
            if leftovers:
                raise ExperimentMemoryValidationError(
                    "experiment directory exists without a complete immutable record"
                )
        else:
            dest_dir.mkdir(parents=True, exist_ok=False)
        _atomic_create_exclusive(dest, serialized)
        stored = self.get(experiment_id)
        _LOGGER.info(
            "canonical_experiment_memory_v1 appended experiment_id=%s",
            experiment_id,
        )
        return stored

    def get(self, experiment_id: str) -> Mapping[str, Any]:
        path = self._record_path(experiment_id)
        if not path.is_file():
            raise ExperimentMemoryValidationError(f"experiment record not found: {experiment_id}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ExperimentMemoryValidationError(
                f"corrupt experiment record JSON: {experiment_id}"
            ) from exc
        if not isinstance(payload, dict):
            raise ExperimentMemoryValidationError("corrupt experiment record root")
        validate_canonical_experiment_memory_record_v1(payload)
        stored_id = str(payload.get("experiment_id") or "")
        if stored_id != experiment_id:
            raise ExperimentMemoryValidationError(
                "stored experiment_id does not match requested id"
            )
        return freeze_canonical_experiment_memory_record_v1(payload)

    def exists(self, experiment_id: str) -> bool:
        path = self._record_path(experiment_id)
        if not path.exists():
            return False
        self.get(experiment_id)
        return True

    def list_metadata(self) -> list[dict[str, Any]]:
        if not self._root.exists():
            return []
        rows: list[dict[str, Any]] = []
        for child in sorted(self._root.iterdir(), key=lambda item: item.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if not is_valid_sha256_hex(child.name):
                raise ExperimentMemoryValidationError(
                    f"non-canonical directory under experiment memory root: {child.name}"
                )
            record = self.get(child.name)
            rows.append(
                {
                    "candidate_role": record["candidate_role"],
                    "created_at": record["created_at"],
                    "disposition": record["disposition"],
                    "experiment_id": record["experiment_id"],
                    "hypothesis_id": record["hypothesis_id"],
                    "identity_digest": record["experiment_identity"]["identity_digest"],
                    "parent_experiment": record["parent_experiment"],
                }
            )
        return rows

    def _record_path(self, experiment_id: str) -> Path:
        if not isinstance(experiment_id, str) or not is_valid_sha256_hex(experiment_id):
            raise ExperimentMemoryValidationError(
                "experiment_id must be a lowercase sha256 hex digest"
            )
        if ".." in experiment_id or "/" in experiment_id or "\\" in experiment_id:
            raise ExperimentMemoryValidationError("experiment_id path traversal is forbidden")
        root = self._root.resolve()
        dest_dir = (root / experiment_id).resolve()
        try:
            dest_dir.relative_to(root)
        except ValueError as exc:
            raise ExperimentMemoryValidationError(
                "experiment record path escaped store root"
            ) from exc
        dest = dest_dir / RECORD_FILENAME
        dest_resolved = dest.resolve()
        try:
            dest_resolved.relative_to(root)
        except ValueError as exc:
            raise ExperimentMemoryValidationError(
                "experiment record path escaped store root"
            ) from exc
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
                raise ExperimentRecordConflictError(
                    "divergent canonical content for existing experiment_id is forbidden"
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
    "CanonicalExperimentMemoryStoreV1",
    "RECORD_FILENAME",
]
