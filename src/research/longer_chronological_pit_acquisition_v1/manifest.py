"""Acquisition manifest — deterministic serialization."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.longer_chronological_pit_acquisition_v1 import (
    DATASET_ID,
    MANIFEST_SCHEMA_VERSION,
)
from src.research.longer_chronological_pit_acquisition_v1.archive_root import (
    ArchiveRootError,
    archive_layout,
    assert_path_under_archive,
)
from src.research.longer_chronological_pit_acquisition_v1.source_discovery import (
    discover_sources_for_partition,
)

REQUIRED_FIELDS = (
    "dataset_id",
    "schema_version",
    "source_id",
    "venue",
    "market_type",
    "instrument_id",
    "normalized_symbol",
    "period_start",
    "period_end",
    "frequency",
    "source_locator",
    "expected_artifact_path",
    "status",
    "checksum",
    "byte_size",
    "acquired_at",
    "validation_status",
    "retry_count",
    "provenance",
    "error_code",
    "partition_id",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def expected_artifact_relpath(partition: Mapping[str, Any]) -> str:
    kind = str(partition.get("kind") or "ohlcv_pt1h")
    inst = str(partition["native_instrument_id"]).replace(":", "_")
    yyyymm = str(partition["period_start"])[0:7].replace("-", "")
    return f"raw/{kind}/{inst}/{yyyymm}/{partition['partition_id']}.json"


def build_partition_manifest_row(
    partition: Mapping[str, Any],
    *,
    status: str = "PLANNED",
    checksum: str | None = None,
    byte_size: int | None = None,
    acquired_at: str | None = None,
    validation_status: str = "NOT_RUN",
    retry_count: int = 0,
    error_code: str | None = None,
    provenance: str = "plan_only_scaffold_v1",
) -> dict[str, Any]:
    discovered = discover_sources_for_partition(partition)
    row = {
        "partition_id": partition["partition_id"],
        "dataset_id": partition.get("dataset_id", DATASET_ID),
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "source_id": discovered["source_id"],
        "venue": discovered["venue"],
        "market_type": discovered["market_type"],
        "instrument_id": partition["instrument_id"],
        "normalized_symbol": partition.get("normalized_symbol", partition["native_instrument_id"]),
        "period_start": partition["period_start"],
        "period_end": partition["period_end"],
        "frequency": partition.get("frequency", discovered["frequency"]),
        "source_locator": discovered["source_locator"],
        "expected_artifact_path": expected_artifact_relpath(partition),
        "status": status,
        "checksum": checksum,
        "byte_size": byte_size,
        "acquired_at": acquired_at,
        "validation_status": validation_status,
        "retry_count": int(retry_count),
        "provenance": provenance,
        "error_code": error_code,
        "coverage_certainty": discovered["coverage_certainty"],
        "kind": partition.get("kind", "ohlcv_pt1h"),
    }
    for key in REQUIRED_FIELDS:
        if key not in row:
            raise ValueError(f"MISSING_MANIFEST_FIELD:{key}")
    return row


def build_acquisition_manifest(
    partitions: Sequence[Mapping[str, Any]],
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    rows = [build_partition_manifest_row(p) for p in partitions]
    rows.sort(key=lambda r: (r["period_start"], r["instrument_id"], r["partition_id"]))
    body = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "dataset_id": DATASET_ID,
        "created_at": created_at or _utc_now(),
        "partition_count": len(rows),
        "partitions": rows,
        "economic_gate_opened": False,
        "promotion_eligible": False,
        "download_default": False,
        "network_default": False,
    }
    digest = hashlib.sha256(dumps_canonical(body).encode("utf-8")).hexdigest()
    body["manifest_digest"] = digest
    return body


def manifest_digest(manifest: Mapping[str, Any]) -> str:
    payload = {k: v for k, v in manifest.items() if k != "manifest_digest"}
    return hashlib.sha256(dumps_canonical(payload).encode("utf-8")).hexdigest()


def write_manifest_atomic(
    manifest: Mapping[str, Any],
    *,
    archive_root: Path,
    filename: str = "acquisition_manifest.json",
) -> Path:
    layout = archive_layout(archive_root)
    layout["manifests"].mkdir(parents=True, exist_ok=True)
    target = assert_path_under_archive(layout["manifests"] / filename, archive_root)
    if target.exists():
        raise ArchiveRootError("IMMUTABLE_MANIFEST_EXISTS_NO_OVERWRITE")
    tmp = target.with_suffix(target.suffix + ".tmp")
    data = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(target)
    return target
