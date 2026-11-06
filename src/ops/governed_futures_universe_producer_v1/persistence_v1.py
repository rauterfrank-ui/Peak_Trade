"""Atomic persistence + load/validate for governed universe snapshots."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SNAPSHOT_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import (
    GovernedFuturesUniverseSnapshotV1,
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import UniverseFailureCodeV1
from src.ops.governed_futures_universe_producer_v1.single_writer_v1 import (
    DuplicateUniverseWriterError,
    GovernedUniverseSingleWriterV1,
)


class UniversePersistenceError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _atomic_write_text(path: Path, text: str) -> None:
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


def write_manifest(root: Path, relative_files: tuple[str, ...]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    body = "\n".join(lines) + "\n"
    _atomic_write_text(root / MANIFEST_FILENAME, body)
    return sha256_hex(body)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = Path(root) / MANIFEST_FILENAME
    if not manifest.is_file():
        raise UniversePersistenceError(
            UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value, "MANIFEST_MISSING"
        )
    errors: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, rel = line.split(None, 1)
        path = Path(root) / rel
        if not path.is_file():
            errors.append(f"MISSING:{rel}")
            continue
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            errors.append(f"DIGEST_MISMATCH:{rel}")
    if errors:
        raise UniversePersistenceError(
            UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,
            ";".join(errors),
        )
    return {"ok": True, "manifest_path": str(manifest)}


@dataclass(frozen=True)
class UniverseLoadResultV1:
    ok: bool
    snapshot: Optional[GovernedFuturesUniverseSnapshotV1]
    failure_codes: tuple[str, ...]
    detail: str = ""


def validate_snapshot_bindings_v1(
    snapshot: GovernedFuturesUniverseSnapshotV1,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    expected_schema_version: str = SCHEMA_VERSION,
) -> UniverseLoadResultV1:
    failures: list[str] = []
    if snapshot.schema_version != expected_schema_version:
        failures.append(UniverseFailureCodeV1.SCHEMA_MISMATCH.value)
    if snapshot.capability_id != CAPABILITY_ID:
        failures.append(UniverseFailureCodeV1.SCHEMA_MISMATCH.value)
    if snapshot.producer_version != PRODUCER_VERSION:
        failures.append(UniverseFailureCodeV1.SCHEMA_MISMATCH.value)
    recomputed = snapshot.compute_payload_digest()
    if not snapshot.payload_digest or snapshot.payload_digest != recomputed:
        failures.append(UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value)
    if expected_repository_sha is not None and snapshot.repository_sha != expected_repository_sha:
        failures.append(UniverseFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    if expected_config_digest is not None and snapshot.config_digest != expected_config_digest:
        failures.append(UniverseFailureCodeV1.CONFIG_DIGEST_MISMATCH.value)
    # Instrument order must remain deterministic.
    ids = [row.canonical_instrument_id for row in snapshot.instruments]
    if ids != sorted(ids):
        failures.append(UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value)
    if failures:
        return UniverseLoadResultV1(False, snapshot, tuple(sorted(set(failures))), "VALIDATE_FAIL")
    return UniverseLoadResultV1(True, snapshot, (), "VALIDATE_OK")


def load_and_validate_universe_snapshot_v1(
    state_root: Path,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    require_manifest: bool = True,
) -> UniverseLoadResultV1:
    root = Path(state_root)
    path = root / SNAPSHOT_FILENAME
    if not path.is_file():
        return UniverseLoadResultV1(
            False,
            None,
            (UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            "SNAPSHOT_MISSING",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return UniverseLoadResultV1(
            False,
            None,
            (UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            f"UNREADABLE:{exc}",
        )
    if not isinstance(payload, Mapping):
        return UniverseLoadResultV1(
            False,
            None,
            (UniverseFailureCodeV1.MALFORMED_SOURCE_PAYLOAD.value,),
            "SNAPSHOT_NOT_OBJECT",
        )
    try:
        snapshot = GovernedFuturesUniverseSnapshotV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        return UniverseLoadResultV1(
            False,
            None,
            (UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            f"PARSE:{exc}",
        )
    if require_manifest:
        try:
            verify_manifest(root)
        except UniversePersistenceError as exc:
            return UniverseLoadResultV1(False, snapshot, (exc.failure_code,), str(exc))
    return validate_snapshot_bindings_v1(
        snapshot,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )


def persist_universe_bundle_atomic_v1(
    *,
    state_root: Path,
    writer: GovernedUniverseSingleWriterV1,
    snapshot: GovernedFuturesUniverseSnapshotV1,
    evidence: Mapping[str, Any],
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
) -> dict[str, Any]:
    """Atomically stage→publish snapshot + evidence + manifest, then verify."""
    try:
        writer.assert_held()
    except DuplicateUniverseWriterError as exc:
        raise UniversePersistenceError(exc.failure_code, str(exc)) from exc

    if simulate_write_failure:
        raise UniversePersistenceError(
            UniverseFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value,
            "SIMULATED",
        )

    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)
    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        snapshot_text = json.dumps(snapshot.to_dict(), sort_keys=True, indent=2) + "\n"
        evidence_text = json.dumps(dict(evidence), sort_keys=True, indent=2) + "\n"
        (staging / SNAPSHOT_FILENAME).write_text(snapshot_text, encoding="utf-8")
        (staging / EVIDENCE_FILENAME).write_text(evidence_text, encoding="utf-8")
        write_manifest(staging, (SNAPSHOT_FILENAME, EVIDENCE_FILENAME))

        if simulate_partial_write:
            # Publish only snapshot — omit evidence/manifest → partial write.
            _atomic_write_text(root / SNAPSHOT_FILENAME, snapshot_text)
            raise UniversePersistenceError(
                UniverseFailureCodeV1.PARTIAL_WRITE.value,
                "SIMULATED_PARTIAL",
            )

        for name in (SNAPSHOT_FILENAME, EVIDENCE_FILENAME, MANIFEST_FILENAME):
            src = staging / name
            _atomic_write_text(root / name, src.read_text(encoding="utf-8"))

        verification = verify_manifest(root)
        loaded = load_and_validate_universe_snapshot_v1(
            root,
            expected_repository_sha=snapshot.repository_sha,
            expected_config_digest=snapshot.config_digest,
        )
        if not loaded.ok or loaded.snapshot is None:
            raise UniversePersistenceError(
                UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,
                f"POST_LOAD:{loaded.failure_codes}:{loaded.detail}",
            )
        if loaded.snapshot.payload_digest != snapshot.payload_digest:
            raise UniversePersistenceError(
                UniverseFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,
                "POST_DIGEST_MISMATCH",
            )
        return {
            "ok": True,
            "verification": verification,
            "snapshot_id": snapshot.snapshot_id,
            "payload_digest": snapshot.payload_digest,
            "persistence_path": str(root / SNAPSHOT_FILENAME),
            "reloaded_digest": loaded.snapshot.payload_digest,
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def evidence_digest_v1(evidence: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_dumps(dict(evidence)))
