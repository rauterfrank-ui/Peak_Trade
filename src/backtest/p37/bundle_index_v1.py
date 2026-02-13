"""P37 — Bundle index v1 (deterministic registry over P35/P36 artifacts)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Kind = Literal["dir_bundle", "tarball"]


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
        return BundleIndexEntryV1(
            kind=d["kind"],
            relpath=d["relpath"],
            sha256=d["sha256"],
            bytes=int(d["bytes"]),
            report_schema_version=int(d["report_schema_version"]),
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
    """Placeholder: implement next (scan P35/P36 formats)."""
    del paths, base_dir
    return BundleIndexV1(version=1, entries=[])


def verify_bundle_index_v1(index: BundleIndexV1, *, base_dir: str | Path | None = None) -> None:
    """Placeholder: implement next (existence + sha/bytes + duplicates)."""
    del index, base_dir
