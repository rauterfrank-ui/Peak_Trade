"""Atomic persistence for residency store, admission snapshots, and metrics."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.top20_opportunity_evaluation_residency_v1.constants_v1 import (
    ADMISSION_SNAPSHOTS_DIR,
    EVENTS_FILENAME,
    MANIFEST_FILENAME,
    METRICS_FILENAME,
    STATE_FILENAME,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import (
    ResidencyMetricsV1,
    ResidencyRecordV1,
    ResidencyStoreSnapshotV1,
    canonical_json_dumps,
    sha256_hex,
)


class ResidencyPersistenceError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code


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


def admission_snapshot_path(state_root: Path, ranking_snapshot_id: str) -> Path:
    safe = ranking_snapshot_id.replace("/", "_")
    return state_root / ADMISSION_SNAPSHOTS_DIR / f"{safe}.json"


def persist_admission_snapshot_v1(
    state_root: Path,
    snapshot: Mapping[str, Any],
) -> str:
    ranking_snapshot_id = str(snapshot.get("ranking_snapshot_id") or "")
    if not ranking_snapshot_id:
        raise ResidencyPersistenceError("MISSING_RANKING_SNAPSHOT_ID")
    path = admission_snapshot_path(state_root, ranking_snapshot_id)
    if path.is_file():
        return str(path.relative_to(state_root))
    _atomic_write_text(path, canonical_json_dumps(dict(snapshot)) + "\n")
    return str(path.relative_to(state_root))


def load_admission_snapshot_v1(state_root: Path, ref: str) -> dict[str, Any]:
    path = state_root / ref
    if not path.is_file():
        raise ResidencyPersistenceError("ADMISSION_SNAPSHOT_MISSING", ref)
    return json.loads(path.read_text(encoding="utf-8"))


def load_store_v1(state_root: Path) -> ResidencyStoreSnapshotV1:
    path = state_root / STATE_FILENAME
    if not path.is_file():
        return ResidencyStoreSnapshotV1.empty()
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = tuple(ResidencyRecordV1.from_dict(row) for row in (payload.get("records") or ()))
    return ResidencyStoreSnapshotV1(
        schema_version=str(payload.get("schema_version") or ""),
        next_first_admission_sequence=int(payload.get("next_first_admission_sequence") or 1),
        records=records,
        last_observed_clock_unix=float(payload.get("last_observed_clock_unix") or 0.0),
    )


def load_metrics_v1(state_root: Path) -> ResidencyMetricsV1:
    path = state_root / METRICS_FILENAME
    if not path.is_file():
        return ResidencyMetricsV1()
    return ResidencyMetricsV1.from_dict(json.loads(path.read_text(encoding="utf-8")))


def persist_bundle_v1(
    state_root: Path,
    *,
    store: ResidencyStoreSnapshotV1,
    metrics: ResidencyMetricsV1,
    event_line: Optional[str] = None,
) -> None:
    state_root.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        state_root / STATE_FILENAME,
        canonical_json_dumps(store.to_dict()) + "\n",
    )
    _atomic_write_text(
        state_root / METRICS_FILENAME,
        canonical_json_dumps(metrics.to_dict()) + "\n",
    )
    if event_line:
        events = state_root / EVENTS_FILENAME
        with events.open("a", encoding="utf-8") as fh:
            fh.write(event_line.rstrip() + "\n")
            fh.flush()
            os.fsync(fh.fileno())
    rel_files = (STATE_FILENAME, METRICS_FILENAME)
    lines = []
    for rel in rel_files:
        digest = sha256_hex((state_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    _atomic_write_text(state_root / MANIFEST_FILENAME, "\n".join(lines) + "\n")
