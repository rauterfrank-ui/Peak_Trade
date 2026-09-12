"""Append-only T-indexed PIT archive for Cap-2.1 and Economic-MD snapshots.

Reuses existing snapshot DTOs, digest helpers, and manifest primitives.
Does not fetch venue data, does not schedule, does not rank, and does not
replace latest-state persistence.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.cap22_append_only_15m_pit_persistence_v1.anchor_v1 import (
    Cap22AppendOnlyPitPersistenceError,
    canonical_path_key_for_anchor,
    parse_canonical_15m_anchor_utc,
    require_anchor_equals,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.constants_v1 import (
    CAP21_MANIFEST_FILENAME,
    CAP21_SNAPSHOT_FILENAME,
    CAP21_UNIVERSE_AT_T_DIRNAME,
    ECONOMIC_MD_AT_T_DIRNAME,
    ECONOMIC_MD_MANIFEST_FILENAME,
    ECONOMIC_MD_SNAPSHOT_FILENAME,
    SCHEMA_VERSION,
)
from src.ops.cap22_append_only_15m_pit_persistence_v1.reason_codes_v1 import (
    Cap22AppendOnlyPitPersistenceFailureCodeV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    CAPABILITY_ID as ECONOMIC_MD_CAPABILITY_ID,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    PRODUCER_VERSION as ECONOMIC_MD_PRODUCER_VERSION,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import (
    SCHEMA_VERSION as ECONOMIC_MD_SCHEMA_VERSION,
)
from src.ops.economic_md_input_producer_v1.models_v1 import EconomicMdInputSnapshotV1
from src.ops.economic_md_input_producer_v1.persistence_v1 import (
    validate_snapshot_bindings_v1 as validate_economic_md_snapshot_bindings_v1,
)
from src.ops.economic_md_input_producer_v1.persistence_v1 import (
    verify_manifest as verify_economic_md_manifest,
)
from src.ops.economic_md_input_producer_v1.persistence_v1 import (
    write_manifest as write_economic_md_manifest,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    CAPABILITY_ID as CAP21_CAPABILITY_ID,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    PRODUCER_VERSION as CAP21_PRODUCER_VERSION,
)
from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    SCHEMA_VERSION as CAP21_SCHEMA_VERSION,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    validate_snapshot_bindings_v1 as validate_cap21_snapshot_bindings_v1,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    verify_manifest as verify_cap21_manifest,
)
from src.ops.governed_futures_universe_producer_v1.persistence_v1 import (
    write_manifest as write_cap21_manifest,
)

Code = Cap22AppendOnlyPitPersistenceFailureCodeV1


def _fail(code: Cap22AppendOnlyPitPersistenceFailureCodeV1, detail: str = "") -> None:
    raise Cap22AppendOnlyPitPersistenceError(code.value, detail)


def cap21_slot_dir(archive_root: Path, anchor: str) -> Path:
    return Path(archive_root) / CAP21_UNIVERSE_AT_T_DIRNAME / canonical_path_key_for_anchor(anchor)


def economic_md_slot_dir(archive_root: Path, anchor: str) -> Path:
    return Path(archive_root) / ECONOMIC_MD_AT_T_DIRNAME / canonical_path_key_for_anchor(anchor)


def canonical_cap21_path(archive_root: Path, anchor: str) -> Path:
    return cap21_slot_dir(archive_root, anchor) / CAP21_SNAPSHOT_FILENAME


def canonical_economic_md_path(archive_root: Path, anchor: str) -> Path:
    return economic_md_slot_dir(archive_root, anchor) / ECONOMIC_MD_SNAPSHOT_FILENAME


def _atomic_replace_dir(*, staging: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.rename(str(staging), str(dest))
    except OSError as exc:
        if dest.exists():
            raise FileExistsError(str(dest)) from exc
        raise


def _write_json_file(path: Path, payload: Mapping[str, Any]) -> None:
    text = json.dumps(dict(payload), sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _validate_cap21_snapshot(snapshot: GovernedFuturesUniverseSnapshotV1) -> None:
    loaded = validate_cap21_snapshot_bindings_v1(snapshot)
    if not loaded.ok:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, ",".join(loaded.failure_codes))
    if snapshot.schema_version != CAP21_SCHEMA_VERSION:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "CAP21_SCHEMA")
    if snapshot.capability_id != CAP21_CAPABILITY_ID:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "CAP21_CAPABILITY")
    if snapshot.producer_version != CAP21_PRODUCER_VERSION:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "CAP21_PRODUCER")
    if not str(snapshot.snapshot_id or "").strip():
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "CAP21_SNAPSHOT_ID_MISSING")
    if not str(snapshot.generated_at_event_time or "").strip():
        _fail(Code.EVENT_TIME_MISSING, "generated_at_event_time")
    if not str(snapshot.generated_at_wall_time or "").strip():
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "generated_at_wall_time")
    for row in snapshot.instruments:
        if not str(row.source_event_time or "").strip():
            _fail(Code.EVENT_TIME_MISSING, row.canonical_instrument_id)


def _validate_economic_md_snapshot(snapshot: EconomicMdInputSnapshotV1) -> None:
    loaded = validate_economic_md_snapshot_bindings_v1(snapshot)
    if not loaded.ok:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, ",".join(loaded.failure_codes))
    if snapshot.schema_version != ECONOMIC_MD_SCHEMA_VERSION:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "ECONOMIC_MD_SCHEMA")
    if snapshot.capability_id != ECONOMIC_MD_CAPABILITY_ID:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "ECONOMIC_MD_CAPABILITY")
    if snapshot.producer_version != ECONOMIC_MD_PRODUCER_VERSION:
        _fail(Code.DIGEST_OR_SCHEMA_ERROR, "ECONOMIC_MD_PRODUCER")
    if not str(snapshot.economic_input_snapshot_id or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "economic_input_snapshot_id")
    reference = dict(snapshot.universe_snapshot_reference or {})
    if not str(reference.get("snapshot_id") or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "universe_snapshot_id")
    if not str(reference.get("payload_digest") or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "universe_payload_digest")
    if not str(snapshot.collection_cycle_identity or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "collection_cycle_identity")
    if not str(snapshot.collection_started_at or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "collection_started_at")
    if not str(snapshot.collection_completed_at or "").strip():
        _fail(Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT, "collection_completed_at")


def _as_cap21(
    snapshot: GovernedFuturesUniverseSnapshotV1 | Mapping[str, Any],
) -> GovernedFuturesUniverseSnapshotV1:
    if isinstance(snapshot, GovernedFuturesUniverseSnapshotV1):
        parsed = snapshot
    else:
        try:
            parsed = GovernedFuturesUniverseSnapshotV1.from_dict(snapshot)
        except Exception as exc:  # noqa: BLE001
            raise Cap22AppendOnlyPitPersistenceError(
                Code.DIGEST_OR_SCHEMA_ERROR.value, f"CAP21_PARSE:{exc}"
            ) from exc
    _validate_cap21_snapshot(parsed)
    return parsed


def _as_economic_md(
    snapshot: EconomicMdInputSnapshotV1 | Mapping[str, Any],
) -> EconomicMdInputSnapshotV1:
    if isinstance(snapshot, EconomicMdInputSnapshotV1):
        parsed = snapshot
    else:
        try:
            parsed = EconomicMdInputSnapshotV1.from_dict(snapshot)
        except Exception as exc:  # noqa: BLE001
            raise Cap22AppendOnlyPitPersistenceError(
                Code.INCOMPLETE_ECONOMIC_MD_SNAPSHOT.value, f"PARSE:{exc}"
            ) from exc
    _validate_economic_md_snapshot(parsed)
    return parsed


@dataclass(frozen=True)
class AppendOnlyPersistResultV1:
    ok: bool
    idempotent: bool
    anchor: str
    path: str
    payload_digest: str
    snapshot_id: str
    schema_version: str
    archive_schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor": self.anchor,
            "archive_schema_version": self.archive_schema_version,
            "idempotent": self.idempotent,
            "ok": self.ok,
            "path": self.path,
            "payload_digest": self.payload_digest,
            "snapshot_id": self.snapshot_id,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class ExactTBindingV1:
    anchor: str
    cap21_snapshot_id: str
    cap21_payload_digest: str
    economic_md_snapshot_id: str
    economic_md_payload_digest: str
    cap21_path: str
    economic_md_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "anchor": self.anchor,
            "cap21_path": self.cap21_path,
            "cap21_payload_digest": self.cap21_payload_digest,
            "cap21_snapshot_id": self.cap21_snapshot_id,
            "economic_md_path": self.economic_md_path,
            "economic_md_payload_digest": self.economic_md_payload_digest,
            "economic_md_snapshot_id": self.economic_md_snapshot_id,
        }


def _load_cap21_from_slot(slot: Path) -> GovernedFuturesUniverseSnapshotV1:
    path = slot / CAP21_SNAPSHOT_FILENAME
    if not path.is_file():
        _fail(Code.SNAPSHOT_MISSING, str(path))
    try:
        verify_cap21_manifest(slot)
    except Exception as exc:  # noqa: BLE001
        raise Cap22AppendOnlyPitPersistenceError(
            Code.CORRUPT_PERSISTED_SNAPSHOT.value, f"CAP21_MANIFEST:{exc}"
        ) from exc
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        snapshot = GovernedFuturesUniverseSnapshotV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise Cap22AppendOnlyPitPersistenceError(
            Code.CORRUPT_PERSISTED_SNAPSHOT.value, f"CAP21_LOAD:{exc}"
        ) from exc
    _validate_cap21_snapshot(snapshot)
    return snapshot


def _load_economic_md_from_slot(slot: Path) -> EconomicMdInputSnapshotV1:
    path = slot / ECONOMIC_MD_SNAPSHOT_FILENAME
    if not path.is_file():
        _fail(Code.SNAPSHOT_MISSING, str(path))
    try:
        verify_economic_md_manifest(slot)
    except Exception as exc:  # noqa: BLE001
        raise Cap22AppendOnlyPitPersistenceError(
            Code.CORRUPT_PERSISTED_SNAPSHOT.value, f"ECONOMIC_MD_MANIFEST:{exc}"
        ) from exc
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        snapshot = EconomicMdInputSnapshotV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raise Cap22AppendOnlyPitPersistenceError(
            Code.CORRUPT_PERSISTED_SNAPSHOT.value, f"ECONOMIC_MD_LOAD:{exc}"
        ) from exc
    _validate_economic_md_snapshot(snapshot)
    return snapshot


def load_cap21_universe_at_t_v1(
    archive_root: Path,
    *,
    anchor: str,
) -> GovernedFuturesUniverseSnapshotV1:
    canonical = parse_canonical_15m_anchor_utc(anchor)
    slot = cap21_slot_dir(archive_root, canonical)
    if not slot.is_dir():
        _fail(Code.MISSING_CAP21_BINDING, canonical)
    snapshot = _load_cap21_from_slot(slot)
    require_anchor_equals(
        expected=canonical,
        actual=snapshot.generated_at_event_time,
        field="generated_at_event_time",
    )
    return snapshot


def load_economic_md_at_t_v1(
    archive_root: Path,
    *,
    anchor: str,
) -> EconomicMdInputSnapshotV1:
    canonical = parse_canonical_15m_anchor_utc(anchor)
    slot = economic_md_slot_dir(archive_root, canonical)
    if not slot.is_dir():
        _fail(Code.SNAPSHOT_MISSING, canonical)
    return _load_economic_md_from_slot(slot)


def persist_cap21_universe_at_t_v1(
    *,
    archive_root: Path,
    anchor: str,
    snapshot: GovernedFuturesUniverseSnapshotV1 | Mapping[str, Any],
) -> AppendOnlyPersistResultV1:
    canonical = parse_canonical_15m_anchor_utc(anchor)
    parsed = _as_cap21(snapshot)
    require_anchor_equals(
        expected=canonical,
        actual=parsed.generated_at_event_time,
        field="generated_at_event_time",
    )
    dest = cap21_slot_dir(archive_root, canonical)
    dest_file = dest / CAP21_SNAPSHOT_FILENAME
    if dest.is_dir():
        existing = _load_cap21_from_slot(dest)
        if existing.payload_digest == parsed.payload_digest:
            return AppendOnlyPersistResultV1(
                ok=True,
                idempotent=True,
                anchor=canonical,
                path=str(dest_file),
                payload_digest=existing.payload_digest,
                snapshot_id=existing.snapshot_id,
                schema_version=existing.schema_version,
            )
        _fail(
            Code.CONFLICTING_DUPLICATE,
            f"{canonical}:{existing.payload_digest}!={parsed.payload_digest}",
        )
    staging = dest.parent / f".cap21_at_t_staging_{uuid.uuid4().hex}"
    try:
        staging.mkdir(parents=True, exist_ok=False)
        _write_json_file(staging / CAP21_SNAPSHOT_FILENAME, parsed.to_dict())
        write_cap21_manifest(staging, (CAP21_SNAPSHOT_FILENAME,))
        try:
            _atomic_replace_dir(staging=staging, dest=dest)
        except FileExistsError:
            existing = _load_cap21_from_slot(dest)
            if existing.payload_digest == parsed.payload_digest:
                return AppendOnlyPersistResultV1(
                    ok=True,
                    idempotent=True,
                    anchor=canonical,
                    path=str(dest_file),
                    payload_digest=existing.payload_digest,
                    snapshot_id=existing.snapshot_id,
                    schema_version=existing.schema_version,
                )
            _fail(Code.OVERWRITE_FORBIDDEN, canonical)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    reloaded = _load_cap21_from_slot(dest)
    if reloaded.payload_digest != parsed.payload_digest:
        _fail(Code.CORRUPT_PERSISTED_SNAPSHOT, "CAP21_POST_DIGEST_MISMATCH")
    return AppendOnlyPersistResultV1(
        ok=True,
        idempotent=False,
        anchor=canonical,
        path=str(dest_file),
        payload_digest=reloaded.payload_digest,
        snapshot_id=reloaded.snapshot_id,
        schema_version=reloaded.schema_version,
    )


def _assert_exact_t_binding(
    *,
    anchor: str,
    cap21: GovernedFuturesUniverseSnapshotV1,
    economic_md: EconomicMdInputSnapshotV1,
) -> None:
    require_anchor_equals(
        expected=anchor,
        actual=cap21.generated_at_event_time,
        field="generated_at_event_time",
    )
    reference = dict(economic_md.universe_snapshot_reference or {})
    if str(reference.get("snapshot_id") or "") != cap21.snapshot_id:
        _fail(Code.CAP21_BINDING_MISMATCH, "snapshot_id")
    if str(reference.get("payload_digest") or "") != cap21.payload_digest:
        _fail(Code.CAP21_BINDING_MISMATCH, "payload_digest")


def persist_economic_md_at_t_v1(
    *,
    archive_root: Path,
    anchor: str,
    snapshot: EconomicMdInputSnapshotV1 | Mapping[str, Any],
) -> AppendOnlyPersistResultV1:
    canonical = parse_canonical_15m_anchor_utc(anchor)
    parsed = _as_economic_md(snapshot)
    try:
        cap21 = load_cap21_universe_at_t_v1(archive_root, anchor=canonical)
    except Cap22AppendOnlyPitPersistenceError as exc:
        if exc.failure_code == Code.MISSING_CAP21_BINDING.value:
            raise
        if exc.failure_code == Code.SNAPSHOT_MISSING.value:
            _fail(Code.MISSING_CAP21_BINDING, canonical)
        raise
    _assert_exact_t_binding(anchor=canonical, cap21=cap21, economic_md=parsed)
    dest = economic_md_slot_dir(archive_root, canonical)
    dest_file = dest / ECONOMIC_MD_SNAPSHOT_FILENAME
    if dest.is_dir():
        existing = _load_economic_md_from_slot(dest)
        if existing.payload_digest == parsed.payload_digest:
            return AppendOnlyPersistResultV1(
                ok=True,
                idempotent=True,
                anchor=canonical,
                path=str(dest_file),
                payload_digest=existing.payload_digest,
                snapshot_id=existing.economic_input_snapshot_id,
                schema_version=existing.schema_version,
            )
        _fail(
            Code.CONFLICTING_DUPLICATE,
            f"{canonical}:{existing.payload_digest}!={parsed.payload_digest}",
        )
    staging = dest.parent / f".economic_md_at_t_staging_{uuid.uuid4().hex}"
    try:
        staging.mkdir(parents=True, exist_ok=False)
        _write_json_file(staging / ECONOMIC_MD_SNAPSHOT_FILENAME, parsed.to_dict())
        write_economic_md_manifest(staging, (ECONOMIC_MD_SNAPSHOT_FILENAME,))
        try:
            _atomic_replace_dir(staging=staging, dest=dest)
        except FileExistsError:
            existing = _load_economic_md_from_slot(dest)
            if existing.payload_digest == parsed.payload_digest:
                return AppendOnlyPersistResultV1(
                    ok=True,
                    idempotent=True,
                    anchor=canonical,
                    path=str(dest_file),
                    payload_digest=existing.payload_digest,
                    snapshot_id=existing.economic_input_snapshot_id,
                    schema_version=existing.schema_version,
                )
            _fail(Code.OVERWRITE_FORBIDDEN, canonical)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    reloaded = _load_economic_md_from_slot(dest)
    if reloaded.payload_digest != parsed.payload_digest:
        _fail(Code.CORRUPT_PERSISTED_SNAPSHOT, "ECONOMIC_MD_POST_DIGEST_MISMATCH")
    return AppendOnlyPersistResultV1(
        ok=True,
        idempotent=False,
        anchor=canonical,
        path=str(dest_file),
        payload_digest=reloaded.payload_digest,
        snapshot_id=reloaded.economic_input_snapshot_id,
        schema_version=reloaded.schema_version,
    )


def bind_economic_md_to_cap21_at_exact_t_v1(
    archive_root: Path,
    *,
    anchor: str,
    economic_md: Optional[EconomicMdInputSnapshotV1 | Mapping[str, Any]] = None,
    cap21: Optional[GovernedFuturesUniverseSnapshotV1 | Mapping[str, Any]] = None,
) -> ExactTBindingV1:
    canonical = parse_canonical_15m_anchor_utc(anchor)
    loaded_cap21 = (
        cap21 if cap21 is not None else load_cap21_universe_at_t_v1(archive_root, anchor=canonical)
    )
    parsed_cap21 = _as_cap21(loaded_cap21)
    loaded_md = (
        economic_md
        if economic_md is not None
        else load_economic_md_at_t_v1(archive_root, anchor=canonical)
    )
    parsed_md = _as_economic_md(loaded_md)
    _assert_exact_t_binding(anchor=canonical, cap21=parsed_cap21, economic_md=parsed_md)
    return ExactTBindingV1(
        anchor=canonical,
        cap21_snapshot_id=parsed_cap21.snapshot_id,
        cap21_payload_digest=parsed_cap21.payload_digest,
        economic_md_snapshot_id=parsed_md.economic_input_snapshot_id,
        economic_md_payload_digest=parsed_md.payload_digest,
        cap21_path=str(canonical_cap21_path(archive_root, canonical)),
        economic_md_path=str(canonical_economic_md_path(archive_root, canonical)),
    )
