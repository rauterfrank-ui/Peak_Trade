"""Offline-safe Treasury intent store. File-backed test double. No network."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasuryPersistenceError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import TreasuryIntentRecordV1
from src.ops.treasury_phase_1_offline_contracts_v1.serialization_v1 import (
    deserialize_intent_record_v1,
    serialize_intent_record_v1,
)


class TreasuryIntentStoreV1(Protocol):
    def get(self, intent_id: str) -> TreasuryIntentRecordV1 | None: ...

    def put(self, record: TreasuryIntentRecordV1) -> None: ...

    def list_all(self) -> tuple[TreasuryIntentRecordV1, ...]: ...

    def next_sequence(self) -> int: ...


class InMemoryTreasuryIntentStoreV1:
    def __init__(self) -> None:
        self._records: dict[str, TreasuryIntentRecordV1] = {}
        self._sequence = 0

    def get(self, intent_id: str) -> TreasuryIntentRecordV1 | None:
        return self._records.get(intent_id)

    def put(self, record: TreasuryIntentRecordV1) -> None:
        existing = self._records.get(record.intent_id)
        if existing is not None and existing.sequence > record.sequence:
            raise TreasuryPersistenceError("MONOTONIC_SEQUENCE_VIOLATION")
        self._records[record.intent_id] = record
        self._sequence = max(self._sequence, record.sequence)

    def list_all(self) -> tuple[TreasuryIntentRecordV1, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence


class FileBackedTreasuryIntentStoreV1:
    """Crash-consistent JSONL test double. Not a productive persistence architecture."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._memory = InMemoryTreasuryIntentStoreV1()
        if path.exists():
            self._load()

    def _load(self) -> None:
        text = self._path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if line.strip() == "":
                continue
            try:
                record = deserialize_intent_record_v1(line)
            except Exception as exc:
                raise TreasuryPersistenceError(f"CORRUPTED_LINE:{line_no}") from exc
            self._memory.put(record)

    def _rewrite(self) -> None:
        payload = "\n".join(
            serialize_intent_record_v1(record) for record in self._memory.list_all()
        )
        if payload:
            payload += "\n"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = os.open(str(tmp), flags, 0o644)
        try:
            os.write(fd, payload.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, self._path)
        try:
            dir_fd = os.open(str(self._path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass

    def get(self, intent_id: str) -> TreasuryIntentRecordV1 | None:
        return self._memory.get(intent_id)

    def put(self, record: TreasuryIntentRecordV1) -> None:
        self._memory.put(record)
        self._rewrite()

    def list_all(self) -> tuple[TreasuryIntentRecordV1, ...]:
        return self._memory.list_all()

    def next_sequence(self) -> int:
        return self._memory.next_sequence()


def restore_store_from_bytes_v1(path: Path) -> FileBackedTreasuryIntentStoreV1:
    if not path.exists():
        raise TreasuryPersistenceError("STORE_MISSING")
    return FileBackedTreasuryIntentStoreV1(path)


def recover_record_without_second_effect_v1(
    store: TreasuryIntentStoreV1, record: TreasuryIntentRecordV1
) -> TreasuryIntentRecordV1:
    existing = store.get(record.intent_id)
    if existing is None:
        store.put(record)
        restored = store.get(record.intent_id)
        if restored is None:
            raise TreasuryPersistenceError("RECOVERY_PUT_FAILED")
        return restored
    if existing.intent_id != record.intent_id:
        raise TreasuryPersistenceError("RECOVERY_IDENTITY_MISMATCH")
    return existing
