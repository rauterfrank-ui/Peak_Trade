"""Append-only durable store for MI offline evidence envelopes (offline; AUTHORITY=NONE)."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    MiOfflineDurableEvidenceValidationError,
    validate_mi_offline_durable_evidence_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import deterministic_json_dumps

RECORD_FILENAME = "mi_offline_durable_evidence_record_v1.json"
_TMP_PREFIX = ".mi_offline_durable_"
_LOGGER = logging.getLogger(__name__)


class MiOfflineDurableEvidenceStoreV1:
    """File-backed append-only MI offline durable evidence store."""

    def __init__(self, store_root: Path | str) -> None:
        root = Path(store_root)
        if root.exists() and not root.is_dir():
            raise MiOfflineDurableEvidenceValidationError("store_root must be a directory")
        self._root = root

    @property
    def store_root(self) -> Path:
        return self._root

    def append(self, record: Mapping[str, Any]) -> Mapping[str, Any]:
        validated = validate_mi_offline_durable_evidence_record_v1(record)
        payload = dict(validated)
        record_id = str(payload["durable_evidence_id"])
        dest = self._record_path(record_id)
        serialized = _serialize_record(payload)
        if dest.is_file():
            existing = self.get(record_id)
            if _serialize_record(dict(existing)) == serialized:
                _LOGGER.info(
                    "mi_offline_durable_evidence_v1 idempotent append durable_evidence_id=%s",
                    record_id,
                )
                return existing
            raise MiOfflineDurableEvidenceValidationError(
                "divergent canonical content for existing durable_evidence_id is forbidden"
            )
        dest.parent.mkdir(parents=True, exist_ok=True)
        _atomic_create_exclusive(dest, serialized)
        return self.get(record_id)

    def get(self, durable_evidence_id: str) -> Mapping[str, Any]:
        path = self._record_path(durable_evidence_id)
        if not path.is_file():
            raise MiOfflineDurableEvidenceValidationError("MI_OFFLINE_DURABLE_EVIDENCE_NOT_FOUND")
        data = json.loads(path.read_text(encoding="utf-8"))
        return validate_mi_offline_durable_evidence_record_v1(data)

    def get_by_forecast_evidence_id(self, forecast_evidence_id: str) -> Mapping[str, Any] | None:
        matches = [
            record
            for record in self.list_records()
            if str(record.get("forecast_evidence_id")) == forecast_evidence_id
        ]
        if not matches:
            return None
        if len(matches) > 1:
            raise MiOfflineDurableEvidenceValidationError(
                "MULTIPLE_DURABLE_RECORDS_FOR_FORECAST_EVIDENCE_ID"
            )
        return matches[0]

    def list_records(self) -> list[Mapping[str, Any]]:
        if not self._root.is_dir():
            return []
        records: list[Mapping[str, Any]] = []
        for child in sorted(self._root.iterdir()):
            if not child.is_dir():
                continue
            record_path = child / RECORD_FILENAME
            if record_path.is_file():
                records.append(
                    validate_mi_offline_durable_evidence_record_v1(
                        json.loads(record_path.read_text(encoding="utf-8"))
                    )
                )
        return records

    def _record_path(self, durable_evidence_id: str) -> Path:
        safe = durable_evidence_id.replace("/", "_")
        return self._root / safe / RECORD_FILENAME


def _serialize_record(payload: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(dict(payload))


def _atomic_create_exclusive(dest: Path, content: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=_TMP_PREFIX, dir=dest.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, dest)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
