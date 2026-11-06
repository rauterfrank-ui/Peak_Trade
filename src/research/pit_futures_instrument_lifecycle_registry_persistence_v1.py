"""Offline persistence for pit_futures_instrument_lifecycle_registry snapshots v1 — Slice C.

Research-only, non-authorizing. Validator-before-write and validator-after-read.
Atomic replace writes within an explicit root directory. No current-state fallbacks.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    InstrumentLifecycleIntervalV1,
    LifecycleRegistryErrorCode,
    RegistrySnapshotV1,
    SuspensionSubIntervalV1,
    registry_snapshot_to_dict,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)

PACKAGE_MARKER = "PIT_FUTURES_INSTRUMENT_LIFECYCLE_REGISTRY_PERSISTENCE_V1=true"
PERSISTENCE_FORMAT_VERSION = "pit_futures_instrument_lifecycle_registry_persistence.v1"

_SNAPSHOT_TOP_LEVEL_KEYS = frozenset(
    {
        "config_digest",
        "conflict_resolution_policy_version",
        "generated_at",
        "implementation_digest",
        "intervals",
        "policy_version",
        "registry_snapshot_digest",
        "registry_snapshot_version",
        "schema_name",
        "schema_version",
        "source_priority_policy_version",
        "venue_scope",
    }
)
_INTERVAL_KEYS = frozenset(
    {
        "base_asset",
        "contract_expiry",
        "contract_type",
        "correction_provenance_ref",
        "delisting_time",
        "eligible_from",
        "eligible_until",
        "expiry_time",
        "instrument_id",
        "interval_sequence",
        "listing_time",
        "native_instrument_id",
        "quote_asset",
        "record_digest",
        "registry_record_version",
        "settlement_asset",
        "source_digests",
        "source_snapshot_refs",
        "suspension_sub_intervals",
        "superseded_by_version",
        "venue_id",
        "venue_symbol",
    }
)
_SUSPENSION_KEYS = frozenset({"suspension_end", "suspension_start"})


class PersistenceErrorCode(str, Enum):
    VALIDATOR_REJECTED_BEFORE_WRITE = "VALIDATOR_REJECTED_BEFORE_WRITE"
    VALIDATOR_REJECTED_AFTER_READ = "VALIDATOR_REJECTED_AFTER_READ"
    PATH_TRAVERSAL_FORBIDDEN = "PATH_TRAVERSAL_FORBIDDEN"
    PATH_OUTSIDE_ROOT = "PATH_OUTSIDE_ROOT"
    SYMLINK_FORBIDDEN = "SYMLINK_FORBIDDEN"
    TARGET_EXISTS = "TARGET_EXISTS"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    CORRUPT_PERSISTED_FORMAT = "CORRUPT_PERSISTED_FORMAT"
    UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_JSON = "INVALID_JSON"
    TRUNCATED_FILE = "TRUNCATED_FILE"
    IO_ERROR = "IO_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"


class OverwritePolicy(str, Enum):
    FAIL_IF_EXISTS = "FAIL_IF_EXISTS"
    ALLOW_REPLACE = "ALLOW_REPLACE"


@dataclass(frozen=True)
class RegistryPersistenceWriteResultV1:
    success: bool
    path: str | None
    bytes_written: int
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class RegistryPersistenceReadResultV1:
    success: bool
    snapshot: RegistrySnapshotV1 | None
    path: str | None
    error_codes: tuple[str, ...]


def _unknown_keys(data: Mapping[str, Any], allowed: frozenset[str]) -> tuple[str, ...]:
    extras = sorted(set(data.keys()) - allowed)
    return tuple(extras)


def _parse_suspension_sub_interval(data: Mapping[str, Any]) -> SuspensionSubIntervalV1:
    return SuspensionSubIntervalV1(
        suspension_start=str(data["suspension_start"]),
        suspension_end=str(data["suspension_end"]),
    )


def _parse_interval(data: Mapping[str, Any]) -> InstrumentLifecycleIntervalV1:
    suspension_raw = data.get("suspension_sub_intervals", ())
    suspension = tuple(_parse_suspension_sub_interval(item) for item in suspension_raw)
    return InstrumentLifecycleIntervalV1(
        instrument_id=str(data["instrument_id"]),
        venue_id=str(data["venue_id"]),
        contract_type=str(data["contract_type"]),
        base_asset=str(data["base_asset"]),
        quote_asset=str(data["quote_asset"]),
        settlement_asset=str(data["settlement_asset"]),
        listing_time=str(data["listing_time"]),
        eligible_from=str(data["eligible_from"]),
        interval_sequence=int(data["interval_sequence"]),
        registry_record_version=int(data["registry_record_version"]),
        record_digest=str(data["record_digest"]),
        venue_symbol=str(data["venue_symbol"]) if data.get("venue_symbol") is not None else None,
        native_instrument_id=(
            str(data["native_instrument_id"])
            if data.get("native_instrument_id") is not None
            else None
        ),
        contract_expiry=(
            str(data["contract_expiry"]) if data.get("contract_expiry") is not None else None
        ),
        delisting_time=(
            str(data["delisting_time"]) if data.get("delisting_time") is not None else None
        ),
        eligible_until=(
            str(data["eligible_until"]) if data.get("eligible_until") is not None else None
        ),
        expiry_time=str(data["expiry_time"]) if data.get("expiry_time") is not None else None,
        suspension_sub_intervals=suspension,
        source_snapshot_refs=tuple(str(item) for item in data.get("source_snapshot_refs", ())),
        source_digests=tuple(str(item) for item in data.get("source_digests", ())),
        superseded_by_version=(
            int(data["superseded_by_version"])
            if data.get("superseded_by_version") is not None
            else None
        ),
        correction_provenance_ref=(
            str(data["correction_provenance_ref"])
            if data.get("correction_provenance_ref") is not None
            else None
        ),
    )


def parse_registry_snapshot_dict_v1(
    data: Mapping[str, Any],
) -> tuple[RegistrySnapshotV1 | None, tuple[str, ...]]:
    """Fail-closed parse of persisted registry snapshot dict."""
    errors: list[str] = []

    unknown_top = _unknown_keys(data, _SNAPSHOT_TOP_LEVEL_KEYS)
    if unknown_top:
        errors.append(PersistenceErrorCode.UNKNOWN_FIELD.value)
        return None, tuple(errors)

    required_top = (
        "schema_name",
        "schema_version",
        "registry_snapshot_version",
        "policy_version",
        "source_priority_policy_version",
        "conflict_resolution_policy_version",
        "venue_scope",
        "generated_at",
        "intervals",
        "config_digest",
        "implementation_digest",
        "registry_snapshot_digest",
    )
    for field in required_top:
        if field not in data:
            errors.append(PersistenceErrorCode.MISSING_REQUIRED_FIELD.value)
    if errors:
        return None, tuple(sorted(set(errors)))

    schema_version = str(data["schema_version"])
    if schema_version != "v1":
        errors.append(PersistenceErrorCode.UNKNOWN_SCHEMA_VERSION.value)
        return None, tuple(sorted(set(errors)))

    intervals_raw = data["intervals"]
    if not isinstance(intervals_raw, list):
        errors.append(PersistenceErrorCode.CORRUPT_PERSISTED_FORMAT.value)
        return None, tuple(sorted(set(errors)))

    intervals: list[InstrumentLifecycleIntervalV1] = []
    for item in intervals_raw:
        if not isinstance(item, dict):
            errors.append(PersistenceErrorCode.CORRUPT_PERSISTED_FORMAT.value)
            return None, tuple(sorted(set(errors)))
        unknown_interval = _unknown_keys(item, _INTERVAL_KEYS)
        if unknown_interval:
            errors.append(PersistenceErrorCode.UNKNOWN_FIELD.value)
            return None, tuple(sorted(set(errors)))
        for sub in item.get("suspension_sub_intervals", ()):
            if not isinstance(sub, dict):
                errors.append(PersistenceErrorCode.CORRUPT_PERSISTED_FORMAT.value)
                return None, tuple(sorted(set(errors)))
            unknown_sub = _unknown_keys(sub, _SUSPENSION_KEYS)
            if unknown_sub:
                errors.append(PersistenceErrorCode.UNKNOWN_FIELD.value)
                return None, tuple(sorted(set(errors)))
        intervals.append(_parse_interval(item))

    snapshot = RegistrySnapshotV1(
        schema_name=str(data["schema_name"]),
        schema_version=schema_version,
        registry_snapshot_version=int(data["registry_snapshot_version"]),
        policy_version=str(data["policy_version"]),
        source_priority_policy_version=str(data["source_priority_policy_version"]),
        conflict_resolution_policy_version=str(data["conflict_resolution_policy_version"]),
        venue_scope=tuple(str(item) for item in data["venue_scope"]),
        generated_at=str(data["generated_at"]),
        intervals=tuple(intervals),
        config_digest=str(data["config_digest"]),
        implementation_digest=str(data["implementation_digest"]),
        registry_snapshot_digest=str(data["registry_snapshot_digest"]),
    )
    return snapshot, ()


def registry_snapshot_to_canonical_bytes(snapshot: RegistrySnapshotV1) -> bytes:
    payload = registry_snapshot_to_dict(snapshot, include_digest=True)
    return dumps_canonical(payload).encode("utf-8")


def _resolve_bounded_path(
    root_dir: Path, relative_path: Path
) -> tuple[Path | None, tuple[str, ...]]:
    if relative_path.is_absolute():
        return None, (PersistenceErrorCode.PATH_OUTSIDE_ROOT.value,)
    if ".." in relative_path.parts:
        return None, (PersistenceErrorCode.PATH_TRAVERSAL_FORBIDDEN.value,)

    root = root_dir.resolve()
    cursor = root
    for part in relative_path.parts:
        if part == "..":
            return None, (PersistenceErrorCode.PATH_TRAVERSAL_FORBIDDEN.value,)
        next_cursor = cursor / part
        if next_cursor.is_symlink():
            return None, (PersistenceErrorCode.SYMLINK_FORBIDDEN.value,)
        cursor = next_cursor

    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None, (PersistenceErrorCode.PATH_OUTSIDE_ROOT.value,)

    return candidate, ()


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.stem}_",
        suffix=path.suffix or ".json",
    )
    closed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            closed = True
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    except Exception as exc:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise OSError(str(exc)) from exc
    finally:
        if not closed:
            os.close(fd)


def write_registry_snapshot_v1(
    snapshot: RegistrySnapshotV1,
    *,
    root_dir: Path | str,
    relative_path: Path | str,
    overwrite_policy: OverwritePolicy = OverwritePolicy.FAIL_IF_EXISTS,
) -> RegistryPersistenceWriteResultV1:
    """Validate, then atomically persist an accepted registry snapshot."""
    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
    if validation.verdict != ValidationVerdict.ACCEPTED:
        codes = tuple(
            sorted(
                {
                    PersistenceErrorCode.VALIDATOR_REJECTED_BEFORE_WRITE.value,
                    LifecycleRegistryErrorCode.PERSISTENCE_BEFORE_VALIDATION.value,
                    *validation.error_codes,
                }
            )
        )
        return RegistryPersistenceWriteResultV1(False, None, 0, codes)

    root = Path(root_dir)
    rel = Path(relative_path)
    target, path_errors = _resolve_bounded_path(root, rel)
    if target is None:
        return RegistryPersistenceWriteResultV1(False, None, 0, path_errors)

    if target.exists() and overwrite_policy == OverwritePolicy.FAIL_IF_EXISTS:
        return RegistryPersistenceWriteResultV1(
            False,
            str(target),
            0,
            (PersistenceErrorCode.TARGET_EXISTS.value,),
        )

    content = registry_snapshot_to_canonical_bytes(snapshot)
    try:
        _atomic_write_bytes(target, content)
    except OSError:
        return RegistryPersistenceWriteResultV1(
            False,
            str(target),
            0,
            (PersistenceErrorCode.IO_ERROR.value,),
        )

    return RegistryPersistenceWriteResultV1(True, str(target), len(content), ())


def read_registry_snapshot_v1(
    *,
    root_dir: Path | str,
    relative_path: Path | str,
) -> RegistryPersistenceReadResultV1:
    """Read and validator-gate a persisted registry snapshot."""
    root = Path(root_dir)
    rel = Path(relative_path)
    target, path_errors = _resolve_bounded_path(root, rel)
    if target is None:
        return RegistryPersistenceReadResultV1(False, None, None, path_errors)

    if not target.exists():
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.FILE_NOT_FOUND.value,),
        )

    try:
        raw = target.read_bytes()
    except OSError:
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.IO_ERROR.value,),
        )

    if not raw.strip():
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.TRUNCATED_FILE.value,),
        )

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.CORRUPT_PERSISTED_FORMAT.value,),
        )

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.INVALID_JSON.value,),
        )

    if not isinstance(data, dict):
        return RegistryPersistenceReadResultV1(
            False,
            None,
            str(target),
            (PersistenceErrorCode.CORRUPT_PERSISTED_FORMAT.value,),
        )

    snapshot, parse_errors = parse_registry_snapshot_dict_v1(data)
    if snapshot is None:
        return RegistryPersistenceReadResultV1(False, None, str(target), parse_errors)

    validation = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
    if validation.verdict != ValidationVerdict.ACCEPTED:
        codes = tuple(
            sorted(
                {
                    PersistenceErrorCode.VALIDATOR_REJECTED_AFTER_READ.value,
                    *validation.error_codes,
                }
            )
        )
        return RegistryPersistenceReadResultV1(False, None, str(target), codes)

    return RegistryPersistenceReadResultV1(True, snapshot, str(target), ())


__all__ = [
    "OverwritePolicy",
    "PERSISTENCE_FORMAT_VERSION",
    "PersistenceErrorCode",
    "RegistryPersistenceReadResultV1",
    "RegistryPersistenceWriteResultV1",
    "parse_registry_snapshot_dict_v1",
    "read_registry_snapshot_v1",
    "registry_snapshot_to_canonical_bytes",
    "write_registry_snapshot_v1",
]
