"""Bounded archive sibling exporter for regime_bull_bear_switch.v1.json.

CAPABILITY_ID=CAPABILITY_REGIME_BULL_BEAR_SWITCH_ARCHIVE_SIBLING_EXPORTER_V1

Writes already-produced replay commit facts atomically to:

    archive_root/readmodels/regime_bull_bear_switch.v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- no transition_state / SideState recomputation
- no evidence readmodel relabel or load-as-source
- no presentation / dashboard imports beyond coerce contract reuse
- fail-closed on missing/invalid replay commit facts
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_MISSING,
    ERROR_TARGET_CONFLICT,
    ERROR_WRITE_FAILED,
    OWNER,
    READMODELS_DIRNAME,
    REGIME_AUTHORITY_EFFECT,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.replay_commit_source_v1 import (
    build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1,
)


@dataclass(frozen=True)
class RegimeBullBearSwitchArchiveSiblingExportResultV1:
    """Structured result of a fail-closed archive sibling export attempt."""

    exported: bool
    source_label: str
    target_path: str
    side_state: str | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    identical_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    regime_authority_effect: str = REGIME_AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_label: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> RegimeBullBearSwitchArchiveSiblingExportResultV1:
    return RegimeBullBearSwitchArchiveSiblingExportResultV1(
        exported=False,
        source_label=source_label,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def _serialize_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


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


def export_regime_bull_bear_switch_to_archive_sibling_v1(
    *,
    archive_root: str | Path,
    regime_id: str,
    regime_status: str,
    replay_intermediate: object | None,
    source_label: str = "integrated_replay_commit",
) -> RegimeBullBearSwitchArchiveSiblingExportResultV1:
    """Export replay-produced regime facts into the authorized archive sibling path."""
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()
    label = source_label.strip() or "integrated_replay_commit"

    payload, build_errors = build_regime_bull_bear_switch_sibling_payload_from_replay_commit_v1(
        regime_id=regime_id,
        regime_status=regime_status,
        replay_intermediate=replay_intermediate,
    )
    if payload is None:
        code = build_errors[0] if build_errors else ERROR_SOURCE_MISSING
        return _fail(
            source_label=label,
            target_path=str(target_path),
            error_code=code,
            failure_reason=",".join(build_errors) if build_errors else code,
        )

    expected_parent = (archive / READMODELS_DIRNAME).resolve()
    if target_path.parent != expected_parent or target_path.name != TARGET_FILENAME:
        return _fail(
            source_label=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="resolved target escaped authorized sibling path",
        )

    try:
        source_digest = canonical_digest_v1(payload)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_label=label,
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
                source_label=label,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is corrupt or unreadable",
                replaced_existing=True,
            )
        if not isinstance(existing_payload, dict):
            return _fail(
                source_label=label,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is not a JSON object",
                replaced_existing=True,
            )
        try:
            existing_digest = canonical_digest_v1(existing_payload)
        except CanonicalJsonErrorV1:
            return _fail(
                source_label=label,
                target_path=str(target_path),
                error_code=ERROR_TARGET_CONFLICT,
                failure_reason="existing target is not canonically digestible",
                replaced_existing=True,
            )
        if existing_digest == source_digest:
            side = str(payload.get("side_state") or "")
            return RegimeBullBearSwitchArchiveSiblingExportResultV1(
                exported=True,
                source_label=label,
                target_path=str(target_path),
                side_state=side or None,
                source_payload_digest=source_digest,
                target_payload_digest=existing_digest,
                replaced_existing=True,
                identical_existing=True,
            )

    body = _serialize_payload(payload)
    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_label=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=type(exc).__name__,
            replaced_existing=replaced_existing,
        )

    from src.ops.archive_sibling_export_contract_v1.manifest_finalize_v1 import (
        finalize_manifest_for_sibling_target_v1,
    )

    manifest_ok, manifest_msg = finalize_manifest_for_sibling_target_v1(target_path)
    if not manifest_ok:
        return _fail(
            source_label=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=f"manifest_finalize_failed:{manifest_msg}",
            replaced_existing=replaced_existing,
        )

    side = str(payload.get("side_state") or "")
    return RegimeBullBearSwitchArchiveSiblingExportResultV1(
        exported=True,
        source_label=label,
        target_path=str(target_path),
        side_state=side or None,
        source_payload_digest=source_digest,
        target_payload_digest=source_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        identical_existing=False,
    )
