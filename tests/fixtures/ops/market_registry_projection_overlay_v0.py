"""Synthetic fixtures for market registry projection overlay tests (non-authorizing)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests.fixtures.ops.generic_evidence_run_registry_v1 import projection_consumer_v0 as pc

PAYLOAD_SCHEMA = "peak_trade.post_closeout_projection_payload.v0"


def write_registry(archive: Path) -> Path:
    pc.write_minimal_paper_run(archive, "paper_run")
    registry = pc.build_registry(archive)
    registry_path = archive.parent / "registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return registry_path


def write_payload(
    dest: Path,
    *,
    registry_path: Path,
    closeout_label: str = "closeout_fixture",
    projection_ready: bool = True,
    market_dashboard_allowed: bool = True,
    blocked_reason: str | None = None,
    schema_version: str = PAYLOAD_SCHEMA,
) -> Path:
    consumers = {
        "notion_projection_allowed": projection_ready and market_dashboard_allowed,
        "market_dashboard_projection_allowed": projection_ready and market_dashboard_allowed,
        "notion_write_allowed": False,
        "dashboard_write_allowed": False,
    }
    payload: dict[str, Any] = {
        "schema_version": schema_version,
        "generated_at_utc": "2026-05-26T12:00:00Z",
        "run_id": "paper_run",
        "projection_ready": projection_ready,
        "projection_blocked_reason": blocked_reason,
        "manifest_verify_rc": 0 if projection_ready else 1,
        "closeout_accepted": True,
        "primary_evidence_finalized": projection_ready,
        "registry_pointer": str(registry_path.resolve()),
        "closeout_pointer": str((registry_path.parent / closeout_label).resolve()),
        "repo_commit": "deadbeef",
        "s3_export_status": "disabled",
        "download_verify_rc": None,
        "authority": {"live_authority": False, "testnet_authority": False},
        "consumers": consumers,
        "source_files": {
            "manifest_sha256": "/secret/MANIFEST.sha256",
            "registry_json": str(registry_path.resolve()),
        },
    }
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def write_ready_bundle(work_dir: Path) -> tuple[Path, Path]:
    work_dir.mkdir(parents=True, exist_ok=True)
    archive = work_dir / "archive"
    registry_path = write_registry(archive)
    payload_path = write_payload(work_dir / "payload.json", registry_path=registry_path)
    return payload_path, registry_path
