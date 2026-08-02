"""Atomic persistence + load/validate for productive ranking snapshots."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.productive_futures_ranking_producer_v1.constants_v1 import (
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SNAPSHOT_FILENAME,
    STAGING_DIRNAME_PREFIX,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
    canonical_json_dumps,
    sha256_hex,
)
from src.ops.productive_futures_ranking_producer_v1.reason_codes_v1 import RankingFailureCodeV1
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    DuplicateRankingWriterError,
    ProductiveRankingSingleWriterV1,
)


class RankingPersistenceError(RuntimeError):
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
        raise RankingPersistenceError(
            RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value, "MANIFEST_MISSING"
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
        raise RankingPersistenceError(
            RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,
            ";".join(errors),
        )
    return {"ok": True, "manifest_path": str(manifest)}


@dataclass(frozen=True)
class RankingLoadResultV1:
    ok: bool
    snapshot: Optional[ProductiveFuturesRankingSnapshotV1]
    failure_codes: tuple[str, ...]
    detail: str = ""


def validate_ranking_snapshot_bindings_v1(
    snapshot: ProductiveFuturesRankingSnapshotV1,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    expected_schema_version: str = SCHEMA_VERSION,
) -> RankingLoadResultV1:
    failures: list[str] = []
    if snapshot.schema_version != expected_schema_version:
        failures.append(RankingFailureCodeV1.SCHEMA_MISMATCH.value)
    if snapshot.capability_id != CAPABILITY_ID:
        failures.append(RankingFailureCodeV1.SCHEMA_MISMATCH.value)
    if snapshot.producer_version != PRODUCER_VERSION:
        failures.append(RankingFailureCodeV1.SCHEMA_MISMATCH.value)
    recomputed = snapshot.compute_integrity_digest()
    if not snapshot.integrity_digest or snapshot.integrity_digest != recomputed:
        failures.append(RankingFailureCodeV1.INTEGRITY_FAILURE.value)
        failures.append(RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value)
    if expected_repository_sha is not None and snapshot.repository_sha != expected_repository_sha:
        failures.append(RankingFailureCodeV1.REPOSITORY_SHA_MISMATCH.value)
    if expected_config_digest is not None and snapshot.config_digest != expected_config_digest:
        failures.append(RankingFailureCodeV1.CONFIG_DIGEST_MISMATCH.value)
    if snapshot.selection_authority_created:
        failures.append(RankingFailureCodeV1.SCHEMA_MISMATCH.value)
    if snapshot.dashboard_input_used:
        failures.append(RankingFailureCodeV1.DASHBOARD_INPUT_FORBIDDEN.value)
    ranks = [c.rank for c in snapshot.ranked_candidates]
    if ranks and ranks != list(range(1, len(ranks) + 1)):
        failures.append(RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value)
    if failures:
        return RankingLoadResultV1(False, snapshot, tuple(sorted(set(failures))), "VALIDATE_FAIL")
    return RankingLoadResultV1(True, snapshot, (), "VALIDATE_OK")


def load_and_validate_ranking_snapshot_v1(
    state_root: Path,
    *,
    expected_repository_sha: str | None = None,
    expected_config_digest: str | None = None,
    require_manifest: bool = True,
) -> RankingLoadResultV1:
    root = Path(state_root)
    path = root / SNAPSHOT_FILENAME
    if not path.is_file():
        return RankingLoadResultV1(
            False,
            None,
            (RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            "SNAPSHOT_MISSING",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return RankingLoadResultV1(
            False,
            None,
            (RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            f"UNREADABLE:{exc}",
        )
    if not isinstance(payload, Mapping):
        return RankingLoadResultV1(
            False,
            None,
            (RankingFailureCodeV1.UNIVERSE_SNAPSHOT_INVALID.value,),
            "SNAPSHOT_NOT_OBJECT",
        )
    try:
        snapshot = ProductiveFuturesRankingSnapshotV1.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        return RankingLoadResultV1(
            False,
            None,
            (RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,),
            f"PARSE:{exc}",
        )
    if require_manifest:
        try:
            verify_manifest(root)
        except RankingPersistenceError as exc:
            return RankingLoadResultV1(False, snapshot, (exc.failure_code,), str(exc))
    return validate_ranking_snapshot_bindings_v1(
        snapshot,
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )


def _existing_snapshot_conflict_v1(
    root: Path,
    snapshot: ProductiveFuturesRankingSnapshotV1,
) -> Optional[str]:
    path = root / SNAPSHOT_FILENAME
    if not path.is_file():
        return None
    try:
        existing = ProductiveFuturesRankingSnapshotV1.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except Exception:  # noqa: BLE001
        return RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value
    if existing.ranking_snapshot_id != snapshot.ranking_snapshot_id:
        return None
    # Semantic identity: integrity digest excludes wall-clock production time.
    if existing.integrity_digest == snapshot.integrity_digest:
        return None  # idempotent identical ranking content
    return RankingFailureCodeV1.SNAPSHOT_ID_CONTENT_CONFLICT.value


def persist_ranking_bundle_atomic_v1(
    *,
    state_root: Path,
    writer: ProductiveRankingSingleWriterV1,
    snapshot: ProductiveFuturesRankingSnapshotV1,
    evidence: Mapping[str, Any],
    simulate_partial_write: bool = False,
    simulate_write_failure: bool = False,
    simulate_crash_after_persist_before_confirm: bool = False,
) -> dict[str, Any]:
    """Atomically stage→publish snapshot + evidence + manifest, then verify."""
    try:
        writer.assert_held()
    except DuplicateRankingWriterError as exc:
        raise RankingPersistenceError(exc.failure_code, str(exc)) from exc

    if simulate_write_failure:
        raise RankingPersistenceError(
            RankingFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value,
            "SIMULATED",
        )

    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)

    conflict = _existing_snapshot_conflict_v1(root, snapshot)
    if conflict == RankingFailureCodeV1.SNAPSHOT_ID_CONTENT_CONFLICT.value:
        raise RankingPersistenceError(conflict, snapshot.ranking_snapshot_id)
    if conflict is None and (root / SNAPSHOT_FILENAME).is_file():
        # Identical content path: still rewrite atomically for restart safety.
        pass

    staging = root / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"
    staging.mkdir(parents=True, exist_ok=False)
    try:
        snapshot_text = json.dumps(snapshot.to_dict(), sort_keys=True, indent=2) + "\n"
        evidence_text = json.dumps(dict(evidence), sort_keys=True, indent=2) + "\n"
        (staging / SNAPSHOT_FILENAME).write_text(snapshot_text, encoding="utf-8")
        (staging / EVIDENCE_FILENAME).write_text(evidence_text, encoding="utf-8")
        write_manifest(staging, (SNAPSHOT_FILENAME, EVIDENCE_FILENAME))

        if simulate_partial_write:
            _atomic_write_text(root / SNAPSHOT_FILENAME, snapshot_text)
            raise RankingPersistenceError(
                RankingFailureCodeV1.PARTIAL_WRITE.value,
                "SIMULATED_PARTIAL",
            )

        for name in (SNAPSHOT_FILENAME, EVIDENCE_FILENAME, MANIFEST_FILENAME):
            src = staging / name
            _atomic_write_text(root / name, src.read_text(encoding="utf-8"))

        if simulate_crash_after_persist_before_confirm:
            raise RankingPersistenceError(
                RankingFailureCodeV1.PERSISTENCE_WRITE_FAILURE.value,
                "SIMULATED_CRASH_AFTER_PERSIST_BEFORE_CONFIRM",
            )

        verification = verify_manifest(root)
        loaded = load_and_validate_ranking_snapshot_v1(
            root,
            expected_repository_sha=snapshot.repository_sha,
            expected_config_digest=snapshot.config_digest,
        )
        if not loaded.ok or loaded.snapshot is None:
            raise RankingPersistenceError(
                RankingFailureCodeV1.CORRUPT_PERSISTED_SNAPSHOT.value,
                f"POST_LOAD:{loaded.failure_codes}:{loaded.detail}",
            )
        if loaded.snapshot.integrity_digest != snapshot.integrity_digest:
            raise RankingPersistenceError(
                RankingFailureCodeV1.INTEGRITY_FAILURE.value,
                "POST_DIGEST_MISMATCH",
            )
        return {
            "ok": True,
            "verification": verification,
            "ranking_snapshot_id": snapshot.ranking_snapshot_id,
            "integrity_digest": snapshot.integrity_digest,
            "persistence_path": str(root / SNAPSHOT_FILENAME),
            "reloaded_digest": loaded.snapshot.integrity_digest,
            "idempotent_identical": True,
        }
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def evidence_digest_v1(evidence: Mapping[str, Any]) -> str:
    return sha256_hex(canonical_json_dumps(dict(evidence)))
