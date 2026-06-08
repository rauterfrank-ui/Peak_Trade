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
    ALLOWED_SOURCE_STAGES,
    FORBIDDEN_SOURCE_STAGES,
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

ENV_PRODUCER_V1_ENABLED = "PEAK_TRADE_UNIVERSE_SELECTION_PRODUCER_V1_ENABLED"
ENV_UPSTREAM_FIXTURE_PATH = "PEAK_TRADE_UNIVERSE_SELECTION_UPSTREAM_FIXTURE_PATH"
ENV_REAL_METADATA_LOADER_V1_ENABLED = (
    "PEAK_TRADE_UNIVERSE_SELECTION_REAL_METADATA_LOADER_V1_ENABLED"
)
ENV_REAL_METADATA_SOURCE_PATH = "PEAK_TRADE_UNIVERSE_SELECTION_REAL_METADATA_SOURCE_PATH"

REASON_UPSTREAM_FIXTURE_PATH_FORBIDDEN = "UPSTREAM_FIXTURE_PATH_FORBIDDEN"
REASON_UPSTREAM_FIXTURE_PATH_INVALID = "UPSTREAM_FIXTURE_PATH_INVALID"
REASON_REAL_METADATA_LOADER_PATH_FORBIDDEN = "REAL_METADATA_LOADER_PATH_FORBIDDEN"
REASON_REAL_METADATA_LOADER_PATH_INVALID = "REAL_METADATA_LOADER_PATH_INVALID"
REASON_UPSTREAM_SOURCE_PATH_CONFLICT = "UPSTREAM_SOURCE_PATH_CONFLICT"

PRODUCER_CONTRACT = "universe_selection_producer.v1"
READMODELS_DIRNAME = "readmodels"
READMODEL_FILENAME = "universe_selection_readmodel.v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
MANIFEST_VERIFY_LOG_FILENAME = "MANIFEST_VERIFY.log"

OPTIONAL_PERSISTED_MARKER_FIELDS = (
    "real_metadata_source_marked",
    "observability_truth_allowed",
)


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


@dataclass(frozen=True)
class CloseoutHookResult:
    """Non-throwing result for env-gated closeout adapter hooks (Slice 2b)."""

    enabled: bool
    skipped: bool
    written: bool
    reason: str
    archive_root: str
    readmodel_path: str | None
    manifest_verify_rc: int | None
    error: str | None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _import_manifest_helpers() -> tuple[Any, Any, Any, Any]:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import (
        parse_manifest_verify_log_rc,
        require_durable_archive_root,
        verify_manifest_sha256,
        write_manifest_sha256,
    )

    return (
        require_durable_archive_root,
        write_manifest_sha256,
        verify_manifest_sha256,
        parse_manifest_verify_log_rc,
    )


def _write_manifest_verify_log(readmodels_dir: Path, *, verify_ok: bool, verify_msg: str) -> None:
    """Persist MANIFEST_VERIFY.log under readmodels/ (Slice 4 evidence path)."""
    rc = 0 if verify_ok else 1
    status = "OK" if verify_ok else "FAILED"
    body = (
        f"verify_ok={str(verify_ok).lower()}\n"
        f"message={verify_msg}\n"
        f"MANIFEST_VERIFY_RC={rc}\n"
        f"STATUS={status}\n"
    )
    (readmodels_dir / MANIFEST_VERIFY_LOG_FILENAME).write_text(body, encoding="utf-8")


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


def _merge_optional_persisted_markers(
    serialized: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(serialized)
    for key in OPTIONAL_PERSISTED_MARKER_FIELDS:
        if key in payload:
            merged[key] = payload[key]
    return merged


def write_universe_selection_readmodel(
    archive_root: str | Path,
    payload: dict[str, Any],
    *,
    dry_run: bool = False,
) -> ProducerWriteResult:
    """Validate and atomically persist universe_selection_readmodel.v1 under archive readmodels/."""
    (
        require_durable_archive_root,
        write_manifest_sha256,
        verify_manifest_sha256,
        parse_manifest_verify_log_rc,
    ) = _import_manifest_helpers()

    root = Path(archive_root).expanduser().resolve()
    ok, msg = require_durable_archive_root(root)
    if not ok:
        raise ProducerWriteError(msg)

    try:
        contract = validate_universe_selection_payload(payload)
    except UniverseSelectionContractError as exc:
        raise ProducerWriteError(str(exc)) from exc

    serialized = _merge_optional_persisted_markers(contract_to_json_dict(contract), payload)
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
    _write_manifest_verify_log(readmodels_dir, verify_ok=verify_ok, verify_msg=verify_msg)
    write_manifest_sha256(readmodels_dir)
    final_ok, final_msg = verify_manifest_sha256(readmodels_dir)
    parsed_rc, _, _ = parse_manifest_verify_log_rc(readmodels_dir)
    manifest_verify_rc = (
        parsed_rc if parsed_rc is not None else (0 if final_ok and verify_ok else 1)
    )
    manifest_verify_ok = verify_ok and final_ok and manifest_verify_rc == 0
    return ProducerWriteResult(
        archive_root=str(root),
        readmodels_dir=str(readmodels_dir),
        readmodel_path=str(final_path),
        manifest_path=str(manifest_path),
        manifest_verify_ok=manifest_verify_ok,
        manifest_verify_message=final_msg if not final_ok else verify_msg,
        manifest_verify_rc=manifest_verify_rc,
        dry_run=False,
    )


def _producer_v1_enabled() -> bool:
    return (os.environ.get(ENV_PRODUCER_V1_ENABLED) or "").strip() == "1"


def _real_metadata_loader_v1_enabled() -> bool:
    return (os.environ.get(ENV_REAL_METADATA_LOADER_V1_ENABLED) or "").strip() == "1"


def _resolve_upstream_fixture_path_status() -> tuple[Path | None, str | None]:
    raw = (os.environ.get(ENV_UPSTREAM_FIXTURE_PATH) or "").strip()
    if not raw:
        return None, None
    path = Path(raw).expanduser()
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return None, f"{REASON_UPSTREAM_FIXTURE_PATH_INVALID}: fixture path not found"
    if not resolved.is_file():
        return None, f"{REASON_UPSTREAM_FIXTURE_PATH_INVALID}: fixture path not found"
    fixtures_root = (_repo_root() / "tests" / "fixtures").resolve()
    try:
        resolved.relative_to(fixtures_root)
    except ValueError:
        return None, f"{REASON_UPSTREAM_FIXTURE_PATH_FORBIDDEN}: path must be under tests/fixtures"
    return resolved, None


def _resolve_real_metadata_source_path_status(
    archive_root: Path,
) -> tuple[Path | None, str | None]:
    raw = (os.environ.get(ENV_REAL_METADATA_SOURCE_PATH) or "").strip()
    if not raw:
        return None, None
    path = Path(raw).expanduser()
    if not path.is_absolute():
        return None, f"{REASON_REAL_METADATA_LOADER_PATH_INVALID}: path must be absolute"
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return None, f"{REASON_REAL_METADATA_LOADER_PATH_INVALID}: governed bundle path not found"
    if not resolved.is_file():
        return None, f"{REASON_REAL_METADATA_LOADER_PATH_INVALID}: governed bundle path not found"
    root = archive_root.expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return (
            None,
            f"{REASON_REAL_METADATA_LOADER_PATH_FORBIDDEN}: path must be under archive root",
        )
    fixtures_root = (_repo_root() / "tests" / "fixtures").resolve()
    try:
        resolved.relative_to(fixtures_root)
        return (
            None,
            f"{REASON_REAL_METADATA_LOADER_PATH_FORBIDDEN}: repo fixture paths forbidden for U2b",
        )
    except ValueError:
        pass
    return resolved, None


def build_real_metadata_mapped_universe_selection_readmodel(
    *,
    archive_root: str | Path,
    governed_bundle_path: str | Path,
    run_bundle_path: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build readmodel payload from U2b governed bundle → U1 adapter (dry-verification only)."""
    from .futures_producer_packet_real_metadata_source_v1 import (
        assert_governed_not_observability_truth,
        bundle_to_upstream_input,
        load_futures_producer_packet_governed,
    )
    from .futures_universe_upstream_adapter_v1 import (
        map_futures_packets_to_universe_selection_readmodel,
    )

    root = Path(archive_root).expanduser().resolve()
    path = Path(governed_bundle_path).expanduser().resolve()

    bundle = load_futures_producer_packet_governed(path, archive_root=root)
    assert_governed_not_observability_truth(bundle)
    upstream = bundle_to_upstream_input(bundle)
    adapter_result = map_futures_packets_to_universe_selection_readmodel(upstream)
    payload = dict(adapter_result.payload)

    payload["fixture_marked"] = False
    payload["observability_truth_allowed"] = False
    payload["real_metadata_source_marked"] = True
    payload["non_authorizing"] = True

    links = _build_evidence_links(
        run_bundle_path=run_bundle_path,
        run_bundle_uri=None,
        extra_links=evidence_links,
    )
    for link in bundle.evidence_links:
        if link not in links:
            links.append(link)
    bundle_link = str(path)
    if bundle_link not in links:
        links.append(bundle_link)
    if bundle.metadata_table_ref not in links:
        links.append(bundle.metadata_table_ref)

    evidence = dict(payload.get("evidence") or {})
    evidence["links"] = links
    evidence["real_metadata_loader"] = "futures_producer_packet_real_metadata_source.v1"
    evidence["metadata_table_ref"] = bundle.metadata_table_ref
    evidence["metadata_refresh_utc"] = bundle.metadata_refresh_utc
    payload["evidence"] = evidence

    contract = validate_universe_selection_payload(payload)
    serialized = contract_to_json_dict(contract)
    serialized["fixture_marked"] = False
    serialized["observability_truth_allowed"] = False
    serialized["real_metadata_source_marked"] = True
    serialized["non_authorizing"] = True
    return serialized


def write_real_metadata_mapped_universe_selection_readmodel(
    archive_root: str | Path,
    *,
    governed_bundle_path: str | Path,
    run_bundle_path: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
    dry_run: bool = False,
) -> ProducerWriteResult:
    """Validate and persist U2b→U1 mapped readmodel (non-authorizing, not observability truth)."""
    payload = build_real_metadata_mapped_universe_selection_readmodel(
        archive_root=archive_root,
        governed_bundle_path=governed_bundle_path,
        run_bundle_path=run_bundle_path,
        evidence_links=evidence_links,
    )
    return write_universe_selection_readmodel(archive_root, payload, dry_run=dry_run)


def build_upstream_mapped_universe_selection_readmodel(
    *,
    fixture_path: str | Path,
    run_bundle_path: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build readmodel payload from U2a fixture → U1 adapter (dry-verification only)."""
    from .futures_producer_packet_fixture_source_v1 import (
        bundle_to_upstream_input,
        load_futures_producer_packet_fixture,
    )
    from .futures_universe_upstream_adapter_v1 import (
        map_futures_packets_to_universe_selection_readmodel,
    )

    path = Path(fixture_path).expanduser().resolve()
    fixtures_root = (_repo_root() / "tests" / "fixtures").resolve()
    try:
        path.relative_to(fixtures_root)
    except ValueError as exc:
        msg = f"{REASON_UPSTREAM_FIXTURE_PATH_FORBIDDEN}: path must be under tests/fixtures"
        raise ProducerWriteError(msg) from exc
    if not path.is_file():
        msg = f"{REASON_UPSTREAM_FIXTURE_PATH_INVALID}: fixture file not found"
        raise ProducerWriteError(msg)

    bundle = load_futures_producer_packet_fixture(path)
    upstream = bundle_to_upstream_input(bundle)
    adapter_result = map_futures_packets_to_universe_selection_readmodel(upstream)
    payload = dict(adapter_result.payload)

    links = _build_evidence_links(
        run_bundle_path=run_bundle_path,
        run_bundle_uri=None,
        extra_links=evidence_links,
    )
    fixture_link = str(path)
    if fixture_link not in links:
        links.append(fixture_link)
    evidence = dict(payload.get("evidence") or {})
    evidence["links"] = links
    payload["evidence"] = evidence

    contract = validate_universe_selection_payload(payload)
    return contract_to_json_dict(contract)


def write_upstream_mapped_universe_selection_readmodel(
    archive_root: str | Path,
    *,
    fixture_path: str | Path,
    run_bundle_path: str | None = None,
    evidence_links: tuple[str, ...] | None = None,
    dry_run: bool = False,
) -> ProducerWriteResult:
    """Validate and persist U2a→U1 mapped readmodel (fixture_marked, non-authorizing)."""
    payload = build_upstream_mapped_universe_selection_readmodel(
        fixture_path=fixture_path,
        run_bundle_path=run_bundle_path,
        evidence_links=evidence_links,
    )
    return write_universe_selection_readmodel(archive_root, payload, dry_run=dry_run)


def emit_universe_selection_closeout_machine_lines(result: CloseoutHookResult) -> None:
    """Emit deterministic machine lines for bounded adapter closeout hooks."""
    print(f"UNIVERSE_SELECTION_PRODUCER_V1_ENABLED={'true' if result.enabled else 'false'}")
    print(f"UNIVERSE_SELECTION_READMODEL_WRITTEN={'true' if result.written else 'false'}")
    if result.readmodel_path:
        print(f"UNIVERSE_SELECTION_READMODEL_PATH={result.readmodel_path}")
    else:
        print("UNIVERSE_SELECTION_READMODEL_PATH=NOT_WRITTEN")
    if result.manifest_verify_rc is not None:
        print(f"UNIVERSE_SELECTION_READMODEL_MANIFEST_VERIFY_RC={result.manifest_verify_rc}")
    else:
        print("UNIVERSE_SELECTION_READMODEL_MANIFEST_VERIFY_RC=NOT_RUN")
    if result.error:
        print(f"UNIVERSE_SELECTION_READMODEL_ERROR={result.error}")
    else:
        print("UNIVERSE_SELECTION_READMODEL_ERROR=")


def maybe_write_missing_truth_after_bounded_closeout(
    *,
    archive_root: str | Path,
    run_bundle_path: str | Path,
    source_run_id: str,
    source_stage: str,
) -> CloseoutHookResult:
    """Env-gated closeout hook: write Mode-B missing truth when enabled (default off)."""
    root = Path(archive_root).expanduser().resolve()
    if not _producer_v1_enabled():
        return CloseoutHookResult(
            enabled=False,
            skipped=True,
            written=False,
            reason="DISABLED",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=None,
        )

    stage = source_stage.strip().lower()
    if stage in FORBIDDEN_SOURCE_STAGES or stage not in ALLOWED_SOURCE_STAGES:
        return CloseoutHookResult(
            enabled=True,
            skipped=True,
            written=False,
            reason="INVALID_STAGE",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=f"source_stage unsupported: {stage}",
        )

    fixture_path, fixture_path_error = _resolve_upstream_fixture_path_status()
    real_metadata_path, real_metadata_path_error = _resolve_real_metadata_source_path_status(root)
    real_metadata_enabled = _real_metadata_loader_v1_enabled()

    if fixture_path is not None and real_metadata_path is not None:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=(
                f"{REASON_UPSTREAM_SOURCE_PATH_CONFLICT}: "
                "fixture path and real metadata path are mutually exclusive"
            ),
        )

    if real_metadata_enabled and fixture_path is not None:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=(
                f"{REASON_UPSTREAM_SOURCE_PATH_CONFLICT}: "
                "real metadata loader enabled while fixture path is set"
            ),
        )

    if fixture_path_error is not None:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=fixture_path_error,
        )

    if real_metadata_path_error is not None:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=real_metadata_path_error,
        )

    if real_metadata_enabled and real_metadata_path is None:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=(
                f"{REASON_REAL_METADATA_LOADER_PATH_INVALID}: "
                "real metadata source path required when loader enabled"
            ),
        )

    try:
        if real_metadata_enabled and real_metadata_path is not None:
            write_result = write_real_metadata_mapped_universe_selection_readmodel(
                root,
                governed_bundle_path=real_metadata_path,
                run_bundle_path=str(run_bundle_path),
            )
        elif fixture_path is not None:
            write_result = write_upstream_mapped_universe_selection_readmodel(
                root,
                fixture_path=fixture_path,
                run_bundle_path=str(run_bundle_path),
            )
        else:
            write_result = write_missing_truth_universe_selection_readmodel(
                root,
                source_run_id=source_run_id,
                source_stage=stage,
                run_bundle_path=str(run_bundle_path),
            )
    except (ProducerWriteError, UniverseSelectionContractError, OSError, ValueError) as exc:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="ERROR",
            archive_root=str(root),
            readmodel_path=None,
            manifest_verify_rc=None,
            error=str(exc),
        )

    if not write_result.manifest_verify_ok:
        return CloseoutHookResult(
            enabled=True,
            skipped=False,
            written=False,
            reason="VERIFY_FAILED",
            archive_root=write_result.archive_root,
            readmodel_path=write_result.readmodel_path,
            manifest_verify_rc=write_result.manifest_verify_rc,
            error=write_result.manifest_verify_message,
        )

    return CloseoutHookResult(
        enabled=True,
        skipped=False,
        written=True,
        reason="OK",
        archive_root=write_result.archive_root,
        readmodel_path=write_result.readmodel_path,
        manifest_verify_rc=write_result.manifest_verify_rc,
        error=None,
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
