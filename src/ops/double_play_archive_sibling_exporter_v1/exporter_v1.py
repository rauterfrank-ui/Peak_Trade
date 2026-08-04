"""Bounded 1:1 Double Play archive sibling exporter V1.

CAPABILITY_ID=CAPABILITY_DOUBLE_PLAY_ARCHIVE_SIBLING_EXPORTER_V1

Loads an already-produced DoublePlayDashboardDisplaySnapshot-compatible JSON
payload from an explicit caller-supplied path and writes it atomically to:

    archive_root/readmodels/double_play_dashboard_display.v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- DOUBLE_PLAY_AUTHORITY_EFFECT=NONE
- no trading / Double Play recomputation / composer imports
- no presentation / dashboard / materializer imports
- no invented display facts, timestamps, or generated_at
- no archive discovery / latest / registry selection
- fail-closed on missing/corrupt/invalid source
- library-only (no automatic productive caller)
"""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
)
from src.ops.double_play_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    DOUBLE_PLAY_AUTHORITY_EFFECT,
    ERROR_DIGEST_MISMATCH,
    ERROR_IDENTICAL_PATHS,
    ERROR_PATH_REQUIRED,
    ERROR_SOURCE_CORRUPT,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_LOAD_FAILED,
    ERROR_SOURCE_MISSING,
    ERROR_TARGET_CONFLICT,
    ERROR_WRITE_FAILED,
    OWNER,
    PANEL_SUMMARY_KEYS,
    READMODELS_DIRNAME,
    REQUIRED_DISPLAY_FIELDS,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)


@dataclass(frozen=True)
class DoublePlayArchiveSiblingExportResultV1:
    """Structured result of a fail-closed archive sibling export attempt."""

    exported: bool
    source_path: str
    target_path: str
    overall_status: str | None = None
    panel_count: int | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    identical_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    double_play_authority_effect: str = DOUBLE_PLAY_AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_path: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> DoublePlayArchiveSiblingExportResultV1:
    return DoublePlayArchiveSiblingExportResultV1(
        exported=False,
        source_path=source_path,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def _require_nonempty_str(value: object) -> str | None:
    if isinstance(value, Enum):
        value = value.value
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _panel_row_from_source(panel: object) -> dict[str, Any] | None:
    """Copy only already-present panel summary fields; no invented keys."""
    if isinstance(panel, Mapping):
        raw = panel
    else:
        extracted: dict[str, Any] = {}
        for key in PANEL_SUMMARY_KEYS:
            if hasattr(panel, key):
                extracted[key] = getattr(panel, key)
        raw = extracted

    name = raw.get("name")
    status = raw.get("status")
    if isinstance(name, Enum):
        name = name.value
    if isinstance(status, Enum):
        status = status.value
    if _require_nonempty_str(name) is None or _require_nonempty_str(status) is None:
        return None

    row: dict[str, Any] = {
        "name": str(name).strip(),
        "status": str(status).strip(),
    }
    if "summary" in raw:
        summary = raw.get("summary")
        if isinstance(summary, Enum):
            summary = summary.value
        if not isinstance(summary, str):
            return None
        row["summary"] = summary
    if "blockers" in raw:
        blockers = raw.get("blockers")
        if blockers is None:
            row["blockers"] = []
        elif isinstance(blockers, (list, tuple)):
            row["blockers"] = [str(code) for code in blockers]
        else:
            return None
    return row


def coerce_double_play_display_export_payload_v1(
    source: object,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate and copy display fields without mutation or recomputation."""
    if source is None:
        return None, ERROR_SOURCE_MISSING
    if not isinstance(source, Mapping):
        return None, ERROR_SOURCE_INVALID

    raw: Mapping[str, Any] = source
    if "display" in raw and isinstance(raw.get("display"), Mapping):
        nested = raw["display"]
        top_status = raw.get("overall_status")
        nested_status = nested.get("overall_status")
        if (
            isinstance(top_status, str)
            and top_status.strip()
            and isinstance(nested_status, str)
            and nested_status.strip()
            and top_status.strip() != nested_status.strip()
        ):
            return None, ERROR_SOURCE_INVALID
        if not all(key in raw for key in REQUIRED_DISPLAY_FIELDS) and not (
            "overall_status" in raw and ("panel_summaries" in raw or "panels" in raw)
        ):
            raw = nested

    display = deepcopy(dict(raw))

    if "panel_summaries" not in display and "panels" in display:
        panels = display.get("panels")
        if isinstance(panels, Mapping):
            return None, ERROR_SOURCE_INVALID
        try:
            rows: list[dict[str, Any]] = []
            for panel in panels or ():
                row = _panel_row_from_source(panel)
                if row is None:
                    return None, ERROR_SOURCE_INVALID
                rows.append(row)
            display["panel_summaries"] = rows
            display.pop("panels", None)
        except TypeError:
            return None, ERROR_SOURCE_INVALID
    elif "panel_summaries" in display and "panels" in display:
        return None, ERROR_SOURCE_INVALID

    missing = [key for key in REQUIRED_DISPLAY_FIELDS if key not in display]
    if missing:
        return None, ERROR_SOURCE_INVALID

    overall_status = _require_nonempty_str(display.get("overall_status"))
    if overall_status is None:
        return None, ERROR_SOURCE_INVALID
    display["overall_status"] = overall_status

    raw_panels = display.get("panel_summaries")
    if isinstance(raw_panels, Mapping):
        return None, ERROR_SOURCE_INVALID
    try:
        panel_summaries: list[dict[str, Any]] = []
        for panel in raw_panels or ():
            row = _panel_row_from_source(panel)
            if row is None:
                return None, ERROR_SOURCE_INVALID
            panel_summaries.append(row)
        display["panel_summaries"] = panel_summaries
    except TypeError:
        return None, ERROR_SOURCE_INVALID

    if "blockers" in display:
        blockers = display.get("blockers")
        if blockers is None:
            display["blockers"] = []
        elif isinstance(blockers, (list, tuple)):
            display["blockers"] = [str(code) for code in blockers]
        else:
            return None, ERROR_SOURCE_INVALID

    if "display_only" in display and not isinstance(display.get("display_only"), bool):
        return None, ERROR_SOURCE_INVALID
    if "live_authorization" in display and not isinstance(display.get("live_authorization"), bool):
        return None, ERROR_SOURCE_INVALID
    if "evidence_digest" in display:
        digest = display.get("evidence_digest")
        if digest is not None and (not isinstance(digest, str) or not digest.strip()):
            return None, ERROR_SOURCE_INVALID
        if isinstance(digest, str):
            display["evidence_digest"] = digest.strip()

    return display, None


def load_double_play_display_export_payload_v1(
    display_source_path: str | Path,
) -> tuple[dict[str, Any] | None, str, str | None]:
    """Load explicit-path display JSON. Never discovers or selects latest."""
    if display_source_path is None or (
        isinstance(display_source_path, str) and not str(display_source_path).strip()
    ):
        return None, "", ERROR_PATH_REQUIRED

    source_path = Path(display_source_path).expanduser().resolve()
    source_str = str(source_path)
    if not source_path.is_file():
        return None, source_str, ERROR_SOURCE_MISSING

    try:
        raw_text = source_path.read_text(encoding="utf-8")
    except OSError:
        return None, source_str, ERROR_SOURCE_LOAD_FAILED

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, source_str, ERROR_SOURCE_CORRUPT

    if not isinstance(payload, dict):
        return None, source_str, ERROR_SOURCE_INVALID

    display, error = coerce_double_play_display_export_payload_v1(payload)
    if display is None:
        return None, source_str, error
    return display, source_str, None


def _serialize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _atomic_write_text(*, destination: Path, body: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=destination.name + ".", dir=str(destination.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, destination)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def export_double_play_display_to_archive_sibling_v1(
    *,
    display_source_path: str | Path,
    archive_root: str | Path,
) -> DoublePlayArchiveSiblingExportResultV1:
    """Export already-produced display snapshot 1:1 into the archive sibling path.

    Does not invent presentation timestamps or recompute Double Play state.
    """
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    display, source_str, load_error = load_double_play_display_export_payload_v1(
        display_source_path
    )
    source_path = Path(source_str).resolve() if source_str else Path()
    if display is None:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=load_error or ERROR_SOURCE_LOAD_FAILED,
            failure_reason=load_error or ERROR_SOURCE_LOAD_FAILED,
        )

    if source_path == target_path:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_IDENTICAL_PATHS,
            failure_reason="source_path and target_path resolve to the same file",
        )

    expected_parent = (archive / READMODELS_DIRNAME).resolve()
    if target_path.parent != expected_parent or target_path.name != TARGET_FILENAME:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="resolved target escaped authorized sibling path",
        )

    try:
        source_digest = canonical_digest_v1(display)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_SOURCE_INVALID,
            failure_reason=str(exc),
        )

    replaced_existing = target_path.is_file()
    if replaced_existing:
        try:
            existing_raw = target_path.read_text(encoding="utf-8")
            existing_payload = json.loads(existing_raw)
        except (OSError, json.JSONDecodeError):
            return _fail(
                source_path=source_str,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is corrupt or unreadable",
                replaced_existing=True,
            )
        if not isinstance(existing_payload, dict):
            return _fail(
                source_path=source_str,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is not a JSON object",
                replaced_existing=True,
            )
        try:
            existing_digest = canonical_digest_v1(existing_payload)
        except CanonicalJsonErrorV1:
            return _fail(
                source_path=source_str,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is not canonically digestible",
                replaced_existing=True,
            )
        if existing_digest == source_digest:
            return DoublePlayArchiveSiblingExportResultV1(
                exported=True,
                source_path=source_str,
                target_path=str(target_path),
                overall_status=str(display.get("overall_status") or ""),
                panel_count=len(display.get("panel_summaries") or ()),
                source_payload_digest=source_digest,
                target_payload_digest=existing_digest,
                bytes_written=0,
                replaced_existing=False,
                identical_existing=True,
                error_code=None,
                failure_reason=None,
            )

    body = _serialize_payload(display)

    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if not target_path.is_file():
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="target missing after atomic write",
            replaced_existing=replaced_existing,
        )

    try:
        written_raw = target_path.read_text(encoding="utf-8")
        written_payload = json.loads(written_raw)
    except (OSError, json.JSONDecodeError) as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=f"post-write verify failed: {exc}",
            replaced_existing=replaced_existing,
        )

    if not isinstance(written_payload, dict):
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="post-write payload is not a JSON object",
            replaced_existing=replaced_existing,
        )

    try:
        target_digest = canonical_digest_v1(written_payload)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if target_digest != source_digest:
        return _fail(
            source_path=source_str,
            target_path=str(target_path),
            error_code=ERROR_DIGEST_MISMATCH,
            failure_reason=f"{source_digest}!={target_digest}",
            replaced_existing=replaced_existing,
        )

    return DoublePlayArchiveSiblingExportResultV1(
        exported=True,
        source_path=source_str,
        target_path=str(target_path),
        overall_status=str(display.get("overall_status") or ""),
        panel_count=len(display.get("panel_summaries") or ()),
        source_payload_digest=source_digest,
        target_payload_digest=target_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        identical_existing=False,
        error_code=None,
        failure_reason=None,
    )
