"""Append-only file-backed Canonical Reality Gap Store persist v1.

Historical reality-gap records are immutable after successful persist.
Identical canonical replay is idempotent. Divergent content for the same
``reality_gap_record_id`` fails closed. This persist layer cannot mutate
runtime config, live overrides, orders, funding, risk, leverage, or
promotion authority.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.experiments.canonical_reality_gap_store_v1 import (
    RealityGapRecordConflictError,
    RealityGapValidationError,
    canonical_record_payload,
    freeze_canonical_reality_gap_record_v1,
    validate_canonical_reality_gap_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

RECORD_FILENAME = "canonical_reality_gap_record_v1.json"
_TMP_PREFIX = ".canonical_reality_gap_"

_LOGGER = logging.getLogger(__name__)


class CanonicalRealityGapStoreV1:
    """File-backed append-only reality gap store."""

    def __init__(self, store_root: Path | str) -> None:
        root = Path(store_root)
        if root.exists() and not root.is_dir():
            raise RealityGapValidationError("store_root must be a directory")
        self._root = root

    @property
    def store_root(self) -> Path:
        return self._root

    def append(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        validate_canonical_reality_gap_record_v1(record)
        payload = canonical_record_payload(record)
        reality_gap_record_id = str(payload["reality_gap_record_id"])
        dest = self._record_path(reality_gap_record_id)
        serialized = _serialize_record(payload)
        if dest.is_file():
            existing = self.get(reality_gap_record_id)
            if _serialize_record(canonical_record_payload(existing)) == serialized:
                _LOGGER.info(
                    "canonical_reality_gap_store_v1 idempotent append reality_gap_record_id=%s",
                    reality_gap_record_id,
                )
                return existing
            raise RealityGapRecordConflictError(
                "divergent canonical content for existing reality_gap_record_id is forbidden"
            )
        dest_dir = dest.parent
        if dest_dir.exists():
            leftovers = [
                path.name for path in dest_dir.iterdir() if not path.name.startswith(_TMP_PREFIX)
            ]
            if leftovers:
                raise RealityGapValidationError(
                    "reality gap directory exists without a complete immutable record"
                )
        else:
            dest_dir.mkdir(parents=True, exist_ok=False)
        _atomic_create_exclusive(dest, serialized)
        stored = self.get(reality_gap_record_id)
        _LOGGER.info(
            "canonical_reality_gap_store_v1 appended reality_gap_record_id=%s disposition=%s",
            reality_gap_record_id,
            stored["overall_disposition"],
        )
        return stored

    def get(self, reality_gap_record_id: str) -> Mapping[str, Any]:
        path = self._record_path(reality_gap_record_id)
        if not path.is_file():
            raise RealityGapValidationError(
                f"reality gap record not found: {reality_gap_record_id}"
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RealityGapValidationError(
                f"corrupt reality gap record JSON: {reality_gap_record_id}"
            ) from exc
        if not isinstance(payload, dict):
            raise RealityGapValidationError("corrupt reality gap record root")
        validate_canonical_reality_gap_record_v1(payload)
        stored_id = str(payload.get("reality_gap_record_id") or "")
        if stored_id != reality_gap_record_id:
            raise RealityGapValidationError(
                "stored reality_gap_record_id does not match requested id"
            )
        return freeze_canonical_reality_gap_record_v1(payload)

    def exists(self, reality_gap_record_id: str) -> bool:
        path = self._record_path(reality_gap_record_id)
        if not path.exists():
            return False
        self.get(reality_gap_record_id)
        return True

    def list_records(self) -> list[Mapping[str, Any]]:
        if not self._root.exists():
            return []
        rows: list[Mapping[str, Any]] = []
        for child in sorted(self._root.iterdir(), key=lambda item: item.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if not is_valid_sha256_hex(child.name):
                raise RealityGapValidationError(
                    f"non-canonical directory under reality gap store root: {child.name}"
                )
            rows.append(self.get(child.name))
        return rows

    def list_by_experiment_id(self, experiment_id: str) -> list[Mapping[str, Any]]:
        if not isinstance(experiment_id, str) or not is_valid_sha256_hex(experiment_id):
            raise RealityGapValidationError("experiment_id must be a lowercase sha256 hex digest")
        return [
            record for record in self.list_records() if record["experiment_id"] == experiment_id
        ]

    def _record_path(self, reality_gap_record_id: str) -> Path:
        if not isinstance(reality_gap_record_id, str) or not is_valid_sha256_hex(
            reality_gap_record_id
        ):
            raise RealityGapValidationError(
                "reality_gap_record_id must be a lowercase sha256 hex digest"
            )
        if (
            ".." in reality_gap_record_id
            or "/" in reality_gap_record_id
            or "\\" in reality_gap_record_id
        ):
            raise RealityGapValidationError("reality_gap_record_id path traversal is forbidden")
        root = self._root.resolve()
        dest_dir = (root / reality_gap_record_id).resolve()
        try:
            dest_dir.relative_to(root)
        except ValueError as exc:
            raise RealityGapValidationError("reality gap record path escaped store root") from exc
        dest = dest_dir / RECORD_FILENAME
        dest_resolved = dest.resolve()
        try:
            dest_resolved.relative_to(root)
        except ValueError as exc:
            raise RealityGapValidationError("reality gap record path escaped store root") from exc
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
                raise RealityGapRecordConflictError(
                    "divergent canonical content for existing reality_gap_record_id is forbidden"
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
    "CanonicalRealityGapStoreV1",
    "RECORD_FILENAME",
]
