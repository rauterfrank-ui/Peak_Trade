"""Source manifest generation and verification for cross-sectional panel staging v1.

Deterministic MANIFEST.sha256 for staging, panel, and lifecycle roots.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

PACKAGE_MARKER = "CROSS_SECTIONAL_PANEL_STAGING_SOURCE_MANIFEST_V1=true"
MANIFEST_VERSION = "cross_sectional_panel_staging_source_manifest.v1"
MANIFEST_FILENAME = "MANIFEST.sha256"

REASON_MISSING_PANEL_DIR = "MISSING_PANEL_DIR"
REASON_MISSING_LIFECYCLE_DIR = "MISSING_LIFECYCLE_DIR"
REASON_MANIFEST_VERIFY_FAILED = "MANIFEST_VERIFY_FAILED"


class SourceManifestStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class SubdirectoryManifestResultV1:
    root_name: str
    root_path: str
    manifest_written: bool
    manifest_verify_rc: int
    file_count: int


@dataclass(frozen=True)
class SourceManifestMaterializationResultV1:
    status: SourceManifestStatus
    staging_root: str
    staging_manifest: SubdirectoryManifestResultV1
    panel_manifest: SubdirectoryManifestResultV1
    lifecycle_manifest: SubdirectoryManifestResultV1
    combined_verify_rc: int
    reason_codes: tuple[str, ...]


def _write_manifest_sha256(root: Path) -> int:
    lines: list[str] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.name == MANIFEST_FILENAME:
            continue
        rel = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel}")
    manifest = root / MANIFEST_FILENAME
    manifest.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return len(lines)


def verify_manifest_sha256(root: Path) -> tuple[bool, str]:
    manifest = root / MANIFEST_FILENAME
    if not manifest.is_file():
        return False, "MANIFEST.sha256 missing"
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            return False, f"invalid manifest line: {line!r}"
        digest, rel = parts
        path = root / rel
        if not path.is_file():
            return False, f"missing manifest entry: {rel}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            return False, f"checksum mismatch: {rel}"
    return True, ""


def materialize_subdirectory_manifest_v1(
    root: Path, *, root_name: str
) -> SubdirectoryManifestResultV1:
    file_count = _write_manifest_sha256(root)
    verify_ok, _ = verify_manifest_sha256(root)
    return SubdirectoryManifestResultV1(
        root_name=root_name,
        root_path=str(root),
        manifest_written=True,
        manifest_verify_rc=0 if verify_ok else 1,
        file_count=file_count,
    )


def materialize_panel_staging_source_manifests_v1(
    staging_root: Path,
) -> SourceManifestMaterializationResultV1:
    """Write and verify MANIFEST.sha256 for staging, panel, and lifecycle roots."""
    staging_root = staging_root.resolve()
    reasons: list[str] = []
    panel_dir = staging_root / "panel"
    lifecycle_dir = staging_root / "lifecycle"

    if not panel_dir.is_dir():
        reasons.append(REASON_MISSING_PANEL_DIR)
    if not lifecycle_dir.is_dir():
        reasons.append(REASON_MISSING_LIFECYCLE_DIR)

    if reasons:
        empty = SubdirectoryManifestResultV1(
            root_name="",
            root_path="",
            manifest_written=False,
            manifest_verify_rc=1,
            file_count=0,
        )
        return SourceManifestMaterializationResultV1(
            status=SourceManifestStatus.FAIL_CLOSED,
            staging_root=str(staging_root),
            staging_manifest=empty,
            panel_manifest=empty,
            lifecycle_manifest=empty,
            combined_verify_rc=1,
            reason_codes=tuple(reasons),
        )

    panel_result = materialize_subdirectory_manifest_v1(panel_dir, root_name="panel")
    lifecycle_result = materialize_subdirectory_manifest_v1(lifecycle_dir, root_name="lifecycle")
    staging_result = materialize_subdirectory_manifest_v1(staging_root, root_name="staging")

    verify_results = (
        panel_result.manifest_verify_rc,
        lifecycle_result.manifest_verify_rc,
        staging_result.manifest_verify_rc,
    )
    if any(rc != 0 for rc in verify_results):
        reasons.append(REASON_MANIFEST_VERIFY_FAILED)

    combined_rc = 0 if not reasons else 1
    return SourceManifestMaterializationResultV1(
        status=SourceManifestStatus.VERIFIED
        if combined_rc == 0
        else SourceManifestStatus.FAIL_CLOSED,
        staging_root=str(staging_root),
        staging_manifest=staging_result,
        panel_manifest=panel_result,
        lifecycle_manifest=lifecycle_result,
        combined_verify_rc=combined_rc,
        reason_codes=tuple(reasons),
    )


def verify_panel_staging_source_manifests_v1(
    staging_root: Path,
) -> tuple[bool, int, tuple[str, ...]]:
    """Verify existing manifests without rewriting. Returns (ok, rc, reason_codes)."""
    staging_root = staging_root.resolve()
    reasons: list[str] = []
    for subdir in ("panel", "lifecycle"):
        path = staging_root / subdir
        if not path.is_dir():
            reasons.append(f"MISSING_{subdir.upper()}_DIR")
            continue
        ok, msg = verify_manifest_sha256(path)
        if not ok:
            reasons.append(f"{subdir}:{msg}")

    ok_staging, msg_staging = verify_manifest_sha256(staging_root)
    if not ok_staging:
        reasons.append(f"staging:{msg_staging}")

    rc = 0 if not reasons else 1
    return rc == 0, rc, tuple(reasons)


def source_manifest_result_to_dict(
    result: SourceManifestMaterializationResultV1,
) -> dict[str, object]:
    def _sub(item: SubdirectoryManifestResultV1) -> dict[str, object]:
        return {
            "root_name": item.root_name,
            "root_path": item.root_path,
            "manifest_written": item.manifest_written,
            "manifest_verify_rc": item.manifest_verify_rc,
            "file_count": item.file_count,
        }

    return {
        "manifest_version": MANIFEST_VERSION,
        "status": result.status.value,
        "staging_root": result.staging_root,
        "staging_manifest": _sub(result.staging_manifest),
        "panel_manifest": _sub(result.panel_manifest),
        "lifecycle_manifest": _sub(result.lifecycle_manifest),
        "combined_verify_rc": result.combined_verify_rc,
        "reason_codes": list(result.reason_codes),
    }
