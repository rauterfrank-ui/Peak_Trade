"""P37 — Bundle index v1 (deterministic registry over P35/P36 artifacts)."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from src.backtest.p33.report_artifacts_v1 import ArtifactSchemaError
from src.backtest.p34.json_io_v1 import read_report_json_v1
from src.backtest.p35.bundle_v1 import BundleIntegrityError, verify_report_bundle_v1
from src.backtest.p36.tarball_v1 import (
    TarballBundleError,
    read_bundle_tarball_v1,
    verify_bundle_tarball_v1,
)

Kind = Literal["dir_bundle", "tarball"]

_REPORT_JSON = "report.json"
_MANIFEST_JSON = "manifest.json"


class IndexIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class BundleIndexEntryV1:
    kind: Kind
    relpath: str
    sha256: str
    bytes: int
    report_schema_version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "relpath": self.relpath,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "report_schema_version": self.report_schema_version,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BundleIndexEntryV1":
        if not isinstance(d, dict):
            raise IndexIntegrityError("entry must be a dict")
        kind = d.get("kind")
        relpath = d.get("relpath")
        sha256 = d.get("sha256")
        b = d.get("bytes")
        rsv = d.get("report_schema_version")
        if kind not in ("dir_bundle", "tarball"):
            raise IndexIntegrityError(f"invalid kind: {kind!r}")
        if not isinstance(relpath, str) or not relpath:
            raise IndexIntegrityError("relpath must be a non-empty string")
        if not isinstance(sha256, str) or len(sha256) != 64:
            raise IndexIntegrityError("sha256 must be a 64-hex string")
        if not isinstance(b, int) or b < 0:
            raise IndexIntegrityError("bytes must be a non-negative int")
        if not isinstance(rsv, int) or rsv <= 0:
            raise IndexIntegrityError("report_schema_version must be positive int")
        return BundleIndexEntryV1(
            kind=kind,
            relpath=relpath,
            sha256=sha256,
            bytes=b,
            report_schema_version=rsv,
        )


@dataclass(frozen=True)
class BundleIndexV1:
    version: int
    entries: list[BundleIndexEntryV1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "entries": [e.to_dict() for e in sorted(self.entries, key=lambda x: x.relpath)],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BundleIndexV1":
        if not isinstance(d, dict):
            raise IndexIntegrityError("index must be a dict")
        if d.get("version") != 1:
            raise IndexIntegrityError(f"unsupported index version: {d.get('version')!r}")
        ents = d.get("entries")
        if not isinstance(ents, list):
            raise IndexIntegrityError("entries must be a list")
        return BundleIndexV1(
            version=1,
            entries=[BundleIndexEntryV1.from_dict(x) for x in ents],
        )


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _file_meta(p: Path) -> tuple[str, int]:
    b = p.read_bytes()
    return _sha256_bytes(b), len(b)


def _stable_relpath(p: Path, base_dir: Path | None) -> str:
    pp = p.resolve()
    if base_dir is None:
        return str(p)
    bb = base_dir.resolve()
    try:
        rel = pp.relative_to(bb)
        return rel.as_posix()
    except ValueError:
        return str(pp)


def _report_schema_version_from_report_json(report_path: Path) -> int:
    d = read_report_json_v1(report_path)
    v = d.get("schema_version")
    if not isinstance(v, int) or v <= 0:
        raise IndexIntegrityError(f"invalid report schema_version: {v!r}")
    return v


def _index_dir_bundle(dir_path: Path, relpath: str) -> BundleIndexEntryV1:
    try:
        verify_report_bundle_v1(dir_path)
    except BundleIntegrityError as e:
        raise IndexIntegrityError(f"invalid dir bundle: {dir_path}: {e}") from e

    manifest_path = dir_path / _MANIFEST_JSON
    if not manifest_path.exists():
        raise IndexIntegrityError(f"missing manifest.json in dir bundle: {dir_path}")
    sha, nbytes = _file_meta(manifest_path)

    rsv = _report_schema_version_from_report_json(dir_path / _REPORT_JSON)
    return BundleIndexEntryV1(
        kind="dir_bundle",
        relpath=relpath,
        sha256=sha,
        bytes=nbytes,
        report_schema_version=rsv,
    )


def _index_tarball(tgz_path: Path, relpath: str) -> BundleIndexEntryV1:
    if not tgz_path.exists():
        raise IndexIntegrityError(f"missing tarball: {tgz_path}")
    sha, nbytes = _file_meta(tgz_path)

    try:
        verify_bundle_tarball_v1(tgz_path)
    except TarballBundleError as e:
        raise IndexIntegrityError(f"invalid tarball bundle: {tgz_path}: {e}") from e

    with tempfile.TemporaryDirectory(prefix="p37_tarball_") as td:
        out_dir = Path(td) / "extract"
        out_dir.mkdir()
        read_bundle_tarball_v1(tgz_path, out_dir)
        report_path = out_dir / _REPORT_JSON
        if not report_path.exists():
            raise IndexIntegrityError(f"tarball missing report.json: {tgz_path}")

        try:
            rsv = _report_schema_version_from_report_json(report_path)
        except ArtifactSchemaError as e:
            raise IndexIntegrityError(f"tarball report schema invalid: {tgz_path}: {e}") from e

    return BundleIndexEntryV1(
        kind="tarball",
        relpath=relpath,
        sha256=sha,
        bytes=nbytes,
        report_schema_version=rsv,
    )


def write_bundle_index_v1(path: str | Path, index: BundleIndexV1) -> None:
    p = Path(path)
    txt = json.dumps(index.to_dict(), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    p.write_text(txt, encoding="utf-8")


def read_bundle_index_v1(path: str | Path) -> BundleIndexV1:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    return BundleIndexV1.from_dict(d)


def index_bundles_v1(
    paths: list[str | Path], *, base_dir: str | Path | None = None
) -> BundleIndexV1:
    bb = Path(base_dir).resolve() if base_dir is not None else None
    entries: list[BundleIndexEntryV1] = []

    for raw in paths:
        p = Path(raw).resolve()
        rel = _stable_relpath(p, bb)

        if p.is_dir():
            if not (p / _REPORT_JSON).exists():
                raise IndexIntegrityError(f"dir bundle missing report.json: {p}")
            if not (p / _MANIFEST_JSON).exists():
                raise IndexIntegrityError(f"dir bundle missing manifest.json: {p}")
            entries.append(_index_dir_bundle(p, rel))
            continue

        if p.is_file() and (p.suffix in (".tgz", ".gz") or p.name.endswith(".tgz")):
            entries.append(_index_tarball(p, rel))
            continue

        raise IndexIntegrityError(f"unsupported bundle path: {p}")

    rels = [e.relpath for e in entries]
    if len(set(rels)) != len(rels):
        raise IndexIntegrityError("duplicate relpath entries in index")
    return BundleIndexV1(version=1, entries=sorted(entries, key=lambda e: e.relpath))


def verify_bundle_index_v1(index: BundleIndexV1, *, base_dir: str | Path | None = None) -> None:
    if index.version != 1:
        raise IndexIntegrityError(f"unsupported index version: {index.version!r}")

    bb = Path(base_dir).resolve() if base_dir is not None else None

    seen: set[str] = set()
    for e in index.entries:
        if e.relpath in seen:
            raise IndexIntegrityError(f"duplicate relpath: {e.relpath}")
        seen.add(e.relpath)

        p = Path(e.relpath)
        if bb is not None:
            if not p.is_absolute():
                p = (bb / p).resolve()
            else:
                p = p.resolve()

        if e.kind == "dir_bundle":
            manifest = p / _MANIFEST_JSON
            if not manifest.exists():
                raise IndexIntegrityError(f"missing manifest.json for {e.relpath}")
            sha, nbytes = _file_meta(manifest)
        else:
            if not p.exists():
                raise IndexIntegrityError(f"missing tarball for {e.relpath}")
            sha, nbytes = _file_meta(p)

        if sha != e.sha256 or nbytes != e.bytes:
            raise IndexIntegrityError(f"sha/bytes mismatch for {e.relpath}")
