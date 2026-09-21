"""Bounded 1:1 Economic Summary archive sibling exporter V1.

CAPABILITY_ID=CAPABILITY_ECONOMIC_SUMMARY_ARCHIVE_SIBLING_EXPORTER_V1

Writes already-mapped Economic Summary field dicts atomically to:

    archive_root/readmodels/economic_summary.v1.json

Invariants:
- AUTHORITY_EFFECT=NONE
- no economic viability evaluators / metric recomputation
- no presentation / dashboard imports at module top level
- no registry/latest/filesystem discovery
- fail-closed on missing/corrupt/invalid explicit bundle reference
"""

from __future__ import annotations

import json
import os
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
)
from src.ops.economic_summary_archive_sibling_exporter_v1.constants_v1 import (
    AUTHORITY_EFFECT,
    CAPABILITY_ID,
    ECONOMIC_AUTHORITY_EFFECT,
    ERROR_BUNDLE_PATH_REQUIRED,
    ERROR_DIGEST_MISMATCH,
    ERROR_IDENTICAL_PATHS,
    ERROR_SOURCE_INVALID,
    ERROR_SOURCE_MISSING,
    ERROR_WRITE_FAILED,
    OWNER,
    READMODELS_DIRNAME,
    TARGET_FILENAME,
    TARGET_RELATIVE_PATH,
)


@dataclass(frozen=True)
class EconomicSummaryArchiveSiblingExportResultV1:
    exported: bool
    source_path: str
    target_path: str
    economic_status: str | None = None
    source_payload_digest: str | None = None
    target_payload_digest: str | None = None
    bytes_written: int = 0
    replaced_existing: bool = False
    error_code: str | None = None
    failure_reason: str | None = None
    capability_id: str = CAPABILITY_ID
    authority_effect: str = AUTHORITY_EFFECT
    economic_authority_effect: str = ECONOMIC_AUTHORITY_EFFECT
    owner: str = OWNER


def _fail(
    *,
    source_path: str,
    target_path: str,
    error_code: str,
    failure_reason: str = "",
    replaced_existing: bool = False,
) -> EconomicSummaryArchiveSiblingExportResultV1:
    return EconomicSummaryArchiveSiblingExportResultV1(
        exported=False,
        source_path=source_path,
        target_path=target_path,
        error_code=error_code,
        failure_reason=failure_reason or error_code,
        replaced_existing=replaced_existing,
    )


def coerce_economic_summary_fields_export_payload_v1(
    source: object,
) -> tuple[dict[str, Any] | None, str | None]:
    """Validate export fields via the materializer-owned coerce contract (lazy bind)."""
    from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1 import (
        coerce_economic_summary_fields_mapping_v1,
    )

    coerced, errors = coerce_economic_summary_fields_mapping_v1(source)
    if coerced is None:
        code = errors[0] if errors else ERROR_SOURCE_INVALID
        return None, code
    return deepcopy(dict(coerced)), None


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


def export_economic_summary_fields_payload_to_archive_sibling_v1(
    *,
    fields_payload: Mapping[str, Any],
    archive_root: str | Path,
    source_label: str = "in_memory_fields_payload",
) -> EconomicSummaryArchiveSiblingExportResultV1:
    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()
    label = source_label.strip() or "in_memory_fields_payload"

    fields, error = coerce_economic_summary_fields_export_payload_v1(fields_payload)
    if fields is None:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=error or ERROR_SOURCE_INVALID,
            failure_reason=error or ERROR_SOURCE_INVALID,
        )

    try:
        source_digest = canonical_digest_v1(fields)
    except CanonicalJsonErrorV1 as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_SOURCE_INVALID,
            failure_reason=str(exc),
        )

    replaced_existing = target_path.is_file()
    body = _serialize_payload(fields)
    try:
        _atomic_write_text(destination=target_path, body=body)
    except OSError as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    try:
        written_payload = json.loads(target_path.read_text(encoding="utf-8"))
        target_digest = canonical_digest_v1(written_payload)
    except (OSError, json.JSONDecodeError, CanonicalJsonErrorV1) as exc:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=str(exc),
            replaced_existing=replaced_existing,
        )

    if target_digest != source_digest:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_DIGEST_MISMATCH,
            failure_reason=f"{source_digest}!={target_digest}",
            replaced_existing=replaced_existing,
        )

    from src.ops.archive_sibling_export_contract_v1.manifest_finalize_v1 import (
        finalize_manifest_for_sibling_target_v1,
    )

    manifest_ok, manifest_msg = finalize_manifest_for_sibling_target_v1(target_path)
    if not manifest_ok:
        return _fail(
            source_path=label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason=f"manifest_finalize_failed:{manifest_msg}",
            replaced_existing=replaced_existing,
        )

    return EconomicSummaryArchiveSiblingExportResultV1(
        exported=True,
        source_path=label,
        target_path=str(target_path),
        economic_status=str(fields.get("status") or ""),
        source_payload_digest=source_digest,
        target_payload_digest=target_digest,
        bytes_written=len(body.encode("utf-8")),
        replaced_existing=replaced_existing,
        error_code=None,
        failure_reason=None,
    )


def export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
    *,
    archive_root: str | Path,
    economic_viability_evidence_bundle_path: str | Path | None,
    source_label: str = "explicit_step29m_bundle",
) -> EconomicSummaryArchiveSiblingExportResultV1:
    from src.ops.economic_summary_archive_sibling_exporter_v1.explicit_bundle_source_v1 import (
        build_economic_summary_sibling_payload_from_explicit_bundle_v1,
    )

    archive = Path(archive_root).expanduser().resolve()
    target_path = (archive / TARGET_RELATIVE_PATH).resolve()

    if economic_viability_evidence_bundle_path is None or (
        isinstance(economic_viability_evidence_bundle_path, str)
        and not str(economic_viability_evidence_bundle_path).strip()
    ):
        return _fail(
            source_path="",
            target_path=str(target_path),
            error_code=ERROR_BUNDLE_PATH_REQUIRED,
            failure_reason=ERROR_BUNDLE_PATH_REQUIRED,
        )

    bundle_path = Path(economic_viability_evidence_bundle_path).expanduser().resolve()
    label = source_label.strip() or "explicit_step29m_bundle"
    bundle_label = f"{label}:{bundle_path}"

    if bundle_path == target_path or bundle_path.is_file() and bundle_path == target_path:
        return _fail(
            source_path=bundle_label,
            target_path=str(target_path),
            error_code=ERROR_IDENTICAL_PATHS,
            failure_reason="bundle path must not equal archive sibling target",
        )

    expected_parent = (archive / READMODELS_DIRNAME).resolve()
    if target_path.parent != expected_parent or target_path.name != TARGET_FILENAME:
        return _fail(
            source_path=bundle_label,
            target_path=str(target_path),
            error_code=ERROR_WRITE_FAILED,
            failure_reason="resolved target escaped authorized sibling path",
        )

    payload, build_errors = build_economic_summary_sibling_payload_from_explicit_bundle_v1(
        economic_viability_evidence_bundle_path=bundle_path,
    )
    if payload is None:
        code = build_errors[0] if build_errors else ERROR_SOURCE_INVALID
        detail = build_errors[1] if len(build_errors) > 1 else code
        return _fail(
            source_path=bundle_label,
            target_path=str(target_path),
            error_code=code,
            failure_reason=str(detail),
        )

    return export_economic_summary_fields_payload_to_archive_sibling_v1(
        fields_payload=payload,
        archive_root=archive,
        source_label=bundle_label,
    )
