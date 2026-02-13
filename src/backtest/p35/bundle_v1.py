"""P35 — Report artifact bundle v1 (JSON + manifest + integrity)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.backtest.p33.report_artifacts_v1 import ArtifactSchemaError
from src.backtest.p34.json_io_v1 import read_report_json_v1, write_report_json_v1

try:
    from src.backtest.p31.metrics_v1 import summary_kpis as _summary_kpis
except Exception:  # pragma: no cover
    _summary_kpis = None


class BundleIntegrityError(ValueError):
    """Raised when bundle verification fails (tampering, missing file)."""

    pass


@dataclass(frozen=True)
class ManifestFileEntryV1:
    sha256: str
    bytes: int


@dataclass(frozen=True)
class BundleManifestV1:
    version: int
    files: dict[str, ManifestFileEntryV1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "files": {
                k: {"sha256": v.sha256, "bytes": v.bytes} for k, v in sorted(self.files.items())
            },
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BundleManifestV1":
        if not isinstance(d, dict):
            raise BundleIntegrityError("manifest must be a dict")
        if d.get("version") != 1:
            raise BundleIntegrityError(f"unsupported manifest version: {d.get('version')!r}")
        files = d.get("files")
        if not isinstance(files, dict):
            raise BundleIntegrityError("manifest.files must be a dict")
        out: dict[str, ManifestFileEntryV1] = {}
        for name, ent in files.items():
            if not isinstance(name, str) or not isinstance(ent, dict):
                raise BundleIntegrityError("invalid manifest entry")
            sha = ent.get("sha256")
            b = ent.get("bytes")
            if not isinstance(sha, str) or not isinstance(b, int):
                raise BundleIntegrityError("invalid manifest entry fields")
            out[name] = ManifestFileEntryV1(sha256=sha, bytes=b)
        return BundleManifestV1(version=1, files=out)


_MANIFEST_VERSION = 1
_REPORT_JSON = "report.json"
_MANIFEST_JSON = "manifest.json"
_METRICS_JSON = "metrics_summary.json"


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _file_entry(path: Path) -> ManifestFileEntryV1:
    data = path.read_bytes()
    return ManifestFileEntryV1(sha256=_sha256_bytes(data), bytes=len(data))


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    txt = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(txt, encoding="utf-8")


def write_report_bundle_v1(
    dir_path: str | Path,
    report_dict: dict[str, Any],
    *,
    include_metrics_summary: bool = True,
) -> BundleManifestV1:
    d = Path(dir_path)
    d.mkdir(parents=True, exist_ok=True)

    report_path = d / _REPORT_JSON
    write_report_json_v1(report_path, report_dict)

    if include_metrics_summary:
        metrics: dict[str, Any] | None = None
        if isinstance(report_dict.get("metrics"), dict):
            metrics = report_dict["metrics"].copy()
        elif _summary_kpis is not None and isinstance(report_dict.get("equity"), list):
            metrics = _summary_kpis(report_dict["equity"])
        if metrics is not None:
            _write_json_file(d / _METRICS_JSON, metrics)

    # manifest.files excludes manifest.json (avoids fixed-point: manifest cannot hash itself)
    files: dict[str, ManifestFileEntryV1] = {}
    for name in (_REPORT_JSON, _METRICS_JSON):
        p = d / name
        if p.exists():
            files[name] = _file_entry(p)

    manifest = BundleManifestV1(version=_MANIFEST_VERSION, files=files)
    _write_json_file(d / _MANIFEST_JSON, manifest.to_dict())

    return manifest


def verify_report_bundle_v1(dir_path: str | Path) -> BundleManifestV1:
    d = Path(dir_path)
    manifest_path = d / _MANIFEST_JSON
    if not manifest_path.exists():
        raise BundleIntegrityError("missing manifest.json")

    try:
        manifest_raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise BundleIntegrityError(f"invalid manifest json: {e}") from e

    manifest = BundleManifestV1.from_dict(manifest_raw)

    for name, ent in manifest.files.items():
        p = d / name
        if not p.exists():
            raise BundleIntegrityError(f"missing file: {name}")
        actual = _file_entry(p)
        if actual.sha256 != ent.sha256 or actual.bytes != ent.bytes:
            raise BundleIntegrityError(f"integrity mismatch: {name}")

    try:
        read_report_json_v1(d / _REPORT_JSON)
    except ArtifactSchemaError as e:
        raise BundleIntegrityError(f"report schema invalid: {e}") from e

    return manifest


def read_report_bundle_v1(dir_path: str | Path) -> dict[str, Any]:
    d = Path(dir_path)
    verify_report_bundle_v1(d)
    return read_report_json_v1(d / _REPORT_JSON)
