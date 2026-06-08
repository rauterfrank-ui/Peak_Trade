"""Closeout-only producer helper for universe_selection_readmodel.v1 (Slice 2 — no runtime I/O)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .universe_selection_contract_v1 import (
    MISSING_TRUTH_FUTURE_DETAIL,
    MISSING_TRUTH_PNL,
    MISSING_TRUTH_RANKING,
    MISSING_TRUTH_SELECTED,
    MISSING_TRUTH_UNIVERSE,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    STORAGE_RELATIVE_PATH,
    UniverseSelectionContractError,
    contract_to_json_dict,
    validate_universe_selection_payload,
)

PRODUCER_CONTRACT = "universe_selection_producer.v1"
READMODELS_DIRNAME = "readmodels"
READMODEL_FILENAME = "universe_selection_readmodel.v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"


class ProducerWriteError(ValueError):
    """Raised when a universe selection readmodel write cannot complete safely."""


@dataclass(frozen=True)
class ProducerWriteResult:
    archive_root: str
    readmodels_dir: str
    readmodel_path: str
    manifest_path: str
    manifest_verify_ok: bool
    manifest_verify_message: str
    manifest_verify_rc: int
    dry_run: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _import_manifest_helpers() -> tuple[Any, Any, Any]:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import (
        require_durable_archive_root,
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    return require_durable_archive_root, write_manifest_sha256, verify_manifest_sha256


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _readmodels_dir(archive_root: Path) -> Path:
    return archive_root.expanduser().resolve() / READMODELS_DIRNAME


def _readmodel_path(archive_root: Path) -> Path:
    return _readmodels_dir(archive_root) / READMODEL_FILENAME


def _build_evidence_links(
    *,
    run_bundle_path: str | None,
    run_bundle_uri: str | None,
    extra_links: tuple[str, ...] | None,
) -> list[str]:
    links: list[str] = []
    if run_bundle_path and run_bundle_path.strip():
        links.append(run_bundle_path.strip())
    if run_bundle_uri and run_bundle_uri.strip():
        uri = run_bundle_uri.strip()
        if uri not in links:
            links.append(uri)
    if extra_links:
        for item in extra_links:
            text = str(item).strip()
            if text and text not in links:
                links.append(text)
    return links


def build_missing_truth_universe_selection_readmodel(
    *,
    source_run_id: str,
    source_stage: str,
    generated_at: str | None = None,
    run_bundle_path: str | None = None,
    run_bundle_uri: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build a Mode-B missing-truth payload that validates against Slice 1 schema."""
    links = _build_evidence_links(
        run_bundle_path=run_bundle_path,
        run_bundle_uri=run_bundle_uri,
        extra_links=evidence_links,
    )
    payload: dict[str, Any] = {
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at or _now_iso(),
        "source_run_id": source_run_id.strip(),
        "source_stage": source_stage.strip().lower(),
        "non_authorizing": True,
        "universe": [],
        "ranking": [],
        "selected_future": {"truth_status": "NOT_PERSISTED"},
        "market_snapshot": {
            "truth_status": "NOT_PERSISTED",
            "source_kind": "NOT_PERSISTED",
            "snapshot_id": None,
            "exchange": None,
            "captured_at": None,
        },
        "evidence": {
            "producer_contract": PRODUCER_CONTRACT,
            "storage_target": STORAGE_RELATIVE_PATH,
            "manifest_verify_rc_expected": 0,
            "links": links,
        },
        "missing_truth": {
            "universe": MISSING_TRUTH_UNIVERSE,
            "ranking": MISSING_TRUTH_RANKING,
            "selected_future": MISSING_TRUTH_SELECTED,
            "future_detail": MISSING_TRUTH_FUTURE_DETAIL,
            "orders_fills_pnl": MISSING_TRUTH_PNL,
        },
    }
    contract = validate_universe_selection_payload(payload)
    return contract_to_json_dict(contract)


def write_universe_selection_readmodel(
    archive_root: str | Path,
    payload: dict[str, Any],
    *,
    dry_run: bool = False,
) -> ProducerWriteResult:
    """Validate and atomically persist universe_selection_readmodel.v1 under archive readmodels/."""
    require_durable_archive_root, write_manifest_sha256, verify_manifest_sha256 = (
        _import_manifest_helpers()
    )

    root = Path(archive_root).expanduser().resolve()
    ok, msg = require_durable_archive_root(root)
    if not ok:
        raise ProducerWriteError(msg)

    try:
        contract = validate_universe_selection_payload(payload)
    except UniverseSelectionContractError as exc:
        raise ProducerWriteError(str(exc)) from exc

    serialized = contract_to_json_dict(contract)
    readmodels_dir = _readmodels_dir(root)
    final_path = readmodels_dir / READMODEL_FILENAME
    manifest_path = readmodels_dir / MANIFEST_FILENAME

    if dry_run:
        return ProducerWriteResult(
            archive_root=str(root),
            readmodels_dir=str(readmodels_dir),
            readmodel_path=str(final_path),
            manifest_path=str(manifest_path),
            manifest_verify_ok=True,
            manifest_verify_message="dry_run",
            manifest_verify_rc=0,
            dry_run=True,
        )

    readmodels_dir.mkdir(parents=True, exist_ok=True)
    body = json.dumps(serialized, indent=2, sort_keys=True) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{READMODEL_FILENAME}.",
        suffix=".tmp",
        dir=readmodels_dir,
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, final_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    write_manifest_sha256(readmodels_dir)
    verify_ok, verify_msg = verify_manifest_sha256(readmodels_dir)
    return ProducerWriteResult(
        archive_root=str(root),
        readmodels_dir=str(readmodels_dir),
        readmodel_path=str(final_path),
        manifest_path=str(manifest_path),
        manifest_verify_ok=verify_ok,
        manifest_verify_message=verify_msg,
        manifest_verify_rc=0 if verify_ok else 1,
        dry_run=False,
    )


def write_missing_truth_universe_selection_readmodel(
    archive_root: str | Path,
    *,
    source_run_id: str,
    source_stage: str,
    generated_at: str | None = None,
    run_bundle_path: str | None = None,
    run_bundle_uri: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
    dry_run: bool = False,
) -> ProducerWriteResult:
    """Build and write explicit Mode-B missing-truth readmodel for a closeout bundle."""
    payload = build_missing_truth_universe_selection_readmodel(
        source_run_id=source_run_id,
        source_stage=source_stage,
        generated_at=generated_at,
        run_bundle_path=run_bundle_path,
        run_bundle_uri=run_bundle_uri,
        evidence_links=evidence_links,
    )
    return write_universe_selection_readmodel(archive_root, payload, dry_run=dry_run)
