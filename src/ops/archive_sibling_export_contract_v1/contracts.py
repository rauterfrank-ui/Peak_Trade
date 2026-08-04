"""Public export API for CAPABILITY_ARCHIVE_SIBLING_EXPORT_CONTRACT_V1.

Semantics-free infrastructure only:
- no trading / presentation / materializer imports
- no archive discovery, latest selection, or env authority
- default dry_run=True; write requires dry_run=False and write_authorized=True
"""

from __future__ import annotations

import json
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

from src.ops.archive_sibling_export_contract_v1.atomic_write import (
    AtomicWriteErrorV1,
    atomic_write_text_v1,
)
from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
    canonical_json_file_body_v1,
)
from src.ops.archive_sibling_export_contract_v1.path_guard import (
    ArchiveSiblingPathErrorV1,
    resolve_archive_sibling_target_v1,
)
from src.ops.archive_sibling_export_contract_v1.result_types import (
    ArchiveSiblingExportEffectV1,
    ArchiveSiblingExportResultV1,
)

CONTRACT_ID = "archive_sibling_export_contract_v1"
CAPABILITY_ID = "CAPABILITY_ARCHIVE_SIBLING_EXPORT_CONTRACT_V1"
AUTHORITY_EFFECT = "NONE"

BLOCK_WRITE_NOT_AUTHORIZED = "ARCHIVE_SIBLING_EXPORT_WRITE_NOT_AUTHORIZED"
BLOCK_PAYLOAD_NOT_OBJECT = "ARCHIVE_SIBLING_EXPORT_PAYLOAD_NOT_OBJECT"
BLOCK_PAYLOAD_NOT_SERIALIZABLE = "ARCHIVE_SIBLING_EXPORT_PAYLOAD_NOT_SERIALIZABLE"
BLOCK_REQUIRED_FIELD_MISSING = "ARCHIVE_SIBLING_EXPORT_REQUIRED_FIELD_MISSING"
BLOCK_PATH_INVALID = "ARCHIVE_SIBLING_EXPORT_PATH_INVALID"
BLOCK_TARGET_NOT_FILE = "ARCHIVE_SIBLING_EXPORT_TARGET_NOT_FILE"
BLOCK_TARGET_INVALID_JSON = "ARCHIVE_SIBLING_EXPORT_TARGET_INVALID_JSON"
BLOCK_TARGET_NOT_OBJECT = "ARCHIVE_SIBLING_EXPORT_TARGET_NOT_OBJECT"
BLOCK_WRITE_FAILED = "ARCHIVE_SIBLING_EXPORT_WRITE_FAILED"
BLOCK_POST_WRITE_VERIFY_FAILED = "ARCHIVE_SIBLING_EXPORT_POST_WRITE_VERIFY_FAILED"
BLOCK_CONTRACT_NAME_EMPTY = "ARCHIVE_SIBLING_EXPORT_CONTRACT_NAME_EMPTY"


def _blocked(
    *,
    dry_run: bool,
    contract_name: str,
    reason: str,
    target_path: str | None = None,
    source_digest: str | None = None,
    target_digest_before: str | None = None,
    expected_target_digest: str | None = None,
    schema_name: str | None = None,
) -> ArchiveSiblingExportResultV1:
    return ArchiveSiblingExportResultV1(
        effect=ArchiveSiblingExportEffectV1.BLOCKED,
        write_performed=False,
        dry_run=dry_run,
        contract_name=contract_name,
        target_path=target_path,
        source_digest=source_digest,
        target_digest_before=target_digest_before,
        target_digest_after=None,
        expected_target_digest=expected_target_digest,
        block_reason=reason,
        schema_name=schema_name,
    )


def _inspect_existing_target(
    target_path: Path,
) -> tuple[str | None, str | None]:
    """Return (digest_before, block_reason). block_reason None means usable."""
    if not target_path.exists():
        return None, None
    if not target_path.is_file():
        return None, BLOCK_TARGET_NOT_FILE
    try:
        raw = target_path.read_text(encoding="utf-8")
        parsed: Any = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, BLOCK_TARGET_INVALID_JSON
    if not isinstance(parsed, dict):
        return None, BLOCK_TARGET_NOT_OBJECT
    try:
        return canonical_digest_v1(parsed), None
    except CanonicalJsonErrorV1:
        return None, BLOCK_TARGET_INVALID_JSON


def export_archive_sibling_json_v1(
    *,
    payload: Mapping[str, object],
    archive_root: Path | str,
    target_relative_path: Path | str,
    contract_name: str,
    required_fields: Collection[str] = (),
    dry_run: bool = True,
    write_authorized: bool = False,
) -> ArchiveSiblingExportResultV1:
    """Validate and optionally atomically persist a JSON-object archive sibling.

    Write occurs only when ``dry_run is False`` and ``write_authorized is True``.
    All other combinations never mutate the filesystem.
    """
    name = str(contract_name or "").strip()
    schema_name = name or None
    effective_dry_run = bool(dry_run)

    if not name:
        return _blocked(
            dry_run=effective_dry_run,
            contract_name="",
            reason=BLOCK_CONTRACT_NAME_EMPTY,
            schema_name=None,
        )

    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes, bytearray)):
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=BLOCK_PAYLOAD_NOT_OBJECT,
            schema_name=schema_name,
        )

    # Plain dict snapshot only (no field invention / coercion / rounding).
    try:
        object_payload = dict(payload)
    except Exception:  # noqa: BLE001 — fail-closed for hostile/unreadable mappings
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=BLOCK_PAYLOAD_NOT_OBJECT,
            schema_name=schema_name,
        )

    missing = [str(field) for field in required_fields if field not in object_payload]
    if missing:
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=f"{BLOCK_REQUIRED_FIELD_MISSING}:{','.join(missing)}",
            schema_name=schema_name,
        )

    try:
        source_digest = canonical_digest_v1(object_payload)
        body = canonical_json_file_body_v1(object_payload)
    except CanonicalJsonErrorV1:
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=BLOCK_PAYLOAD_NOT_SERIALIZABLE,
            schema_name=schema_name,
        )

    try:
        resolved = resolve_archive_sibling_target_v1(
            archive_root=archive_root,
            target_relative_path=target_relative_path,
        )
    except ArchiveSiblingPathErrorV1 as exc:
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=f"{BLOCK_PATH_INVALID}:{exc}",
            source_digest=source_digest,
            expected_target_digest=source_digest,
            schema_name=schema_name,
        )

    target_path = resolved.target_path
    target_str = str(target_path)

    digest_before, target_block = _inspect_existing_target(target_path)
    if target_block is not None:
        return _blocked(
            dry_run=effective_dry_run,
            contract_name=name,
            reason=target_block,
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            expected_target_digest=source_digest,
            schema_name=schema_name,
        )

    if digest_before is None:
        effect = ArchiveSiblingExportEffectV1.CREATE
    elif digest_before == source_digest:
        effect = ArchiveSiblingExportEffectV1.NO_CHANGE
    else:
        effect = ArchiveSiblingExportEffectV1.REPLACE

    if effect == ArchiveSiblingExportEffectV1.NO_CHANGE:
        return ArchiveSiblingExportResultV1(
            effect=effect,
            write_performed=False,
            dry_run=effective_dry_run,
            contract_name=name,
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            target_digest_after=digest_before,
            expected_target_digest=source_digest,
            block_reason=None,
            schema_name=schema_name,
        )

    if effective_dry_run:
        return ArchiveSiblingExportResultV1(
            effect=effect,
            write_performed=False,
            dry_run=True,
            contract_name=name,
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            target_digest_after=None,
            expected_target_digest=source_digest,
            block_reason=None,
            schema_name=schema_name,
        )

    if not write_authorized:
        return _blocked(
            dry_run=False,
            contract_name=name,
            reason=BLOCK_WRITE_NOT_AUTHORIZED,
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            expected_target_digest=source_digest,
            schema_name=schema_name,
        )

    # Authorized write path — validation is complete before any temp/mkdir/replace.
    try:
        atomic_write_text_v1(destination=target_path, body=body)
    except AtomicWriteErrorV1 as exc:
        return _blocked(
            dry_run=False,
            contract_name=name,
            reason=f"{BLOCK_WRITE_FAILED}:{exc}",
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            expected_target_digest=source_digest,
            schema_name=schema_name,
        )

    after_digest, after_block = _inspect_existing_target(target_path)
    if after_block is not None or after_digest != source_digest:
        return _blocked(
            dry_run=False,
            contract_name=name,
            reason=BLOCK_POST_WRITE_VERIFY_FAILED,
            target_path=target_str,
            source_digest=source_digest,
            target_digest_before=digest_before,
            expected_target_digest=source_digest,
            schema_name=schema_name,
        )

    return ArchiveSiblingExportResultV1(
        effect=effect,
        write_performed=True,
        dry_run=False,
        contract_name=name,
        target_path=target_str,
        source_digest=source_digest,
        target_digest_before=digest_before,
        target_digest_after=after_digest,
        expected_target_digest=source_digest,
        block_reason=None,
        schema_name=schema_name,
    )
