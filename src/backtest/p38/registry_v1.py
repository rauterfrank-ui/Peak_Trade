"""P38 — Bundle registry v1 (index_all primitive)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from src.backtest.p35.bundle_v1 import BundleIntegrityError, verify_report_bundle_v1
from src.backtest.p36.tarball_v1 import TarballBundleError, verify_bundle_tarball_v1
from src.backtest.p37.bundle_index_v1 import (
    IndexIntegrityError,
    read_bundle_index_v1,
    verify_bundle_index_v1,
)

SCHEMA_VERSION_V1 = 1


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class RegistryEntryV1:
    bundle_id: str
    kind: str  # "dir_bundle" | "tarball" | "bundle_index"
    ref_path: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "kind": self.kind,
            "ref_path": self.ref_path,
            "sha256": self.sha256,
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "RegistryEntryV1":
        for k in ("bundle_id", "kind", "ref_path", "sha256"):
            if k not in d:
                raise RegistryError(f"missing key: {k}")
        if not all(isinstance(d[k], str) for k in ("bundle_id", "kind", "ref_path", "sha256")):
            raise RegistryError("invalid entry field types")
        return RegistryEntryV1(
            bundle_id=d["bundle_id"],
            kind=d["kind"],
            ref_path=d["ref_path"],
            sha256=d["sha256"],
        )


@dataclass(frozen=True)
class BundleRegistryV1:
    schema_version: int
    entries: list[RegistryEntryV1]

    def to_dict(self) -> dict[str, Any]:
        ents = sorted(self.entries, key=lambda e: (e.bundle_id, e.kind, e.ref_path))
        return {
            "schema_version": self.schema_version,
            "entries": [e.to_dict() for e in ents],
        }

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "BundleRegistryV1":
        if d.get("schema_version") != SCHEMA_VERSION_V1:
            raise RegistryError(f"unsupported schema_version: {d.get('schema_version')!r}")
        ents = d.get("entries")
        if not isinstance(ents, list):
            raise RegistryError("entries must be a list")
        out: list[RegistryEntryV1] = []
        for e in ents:
            if not isinstance(e, dict):
                raise RegistryError("entry must be dict")
            out.append(RegistryEntryV1.from_dict(e))
        return BundleRegistryV1(schema_version=SCHEMA_VERSION_V1, entries=out)


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    txt = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    path.write_text(txt, encoding="utf-8")


def _iter_inputs(inputs: Iterable[str | Path]) -> list[Path]:
    out: list[Path] = []
    for p in inputs:
        pp = Path(p)
        if not pp.exists():
            raise RegistryError(f"input not found: {pp}")
        out.append(pp)
    return out


def build_registry_v1(inputs: list[str | Path]) -> BundleRegistryV1:
    paths = _iter_inputs(inputs)
    entries: list[RegistryEntryV1] = []

    for p in paths:
        # P37 index file
        if p.is_file() and p.name.endswith(".json"):
            try:
                idx = read_bundle_index_v1(p)
                verify_bundle_index_v1(idx, base_dir=p.parent)
                sha = _sha256_file(p)
                bundle_id = p.stem
                entries.append(
                    RegistryEntryV1(
                        bundle_id=bundle_id,
                        kind="bundle_index",
                        ref_path=str(p),
                        sha256=sha,
                    )
                )
                for ent in idx.entries:
                    bid = Path(ent.relpath).stem or ent.relpath
                    entries.append(
                        RegistryEntryV1(
                            bundle_id=bid,
                            kind=ent.kind,
                            ref_path=ent.relpath,
                            sha256=ent.sha256,
                        )
                    )
                continue
            except IndexIntegrityError:
                pass

        # P36 tarball
        if p.is_file() and (p.suffix in {".tgz", ".gz"} or p.name.endswith(".tgz")):
            try:
                verify_bundle_tarball_v1(p)
                sha = _sha256_file(p)
                entries.append(
                    RegistryEntryV1(
                        bundle_id=p.stem,
                        kind="tarball",
                        ref_path=str(p),
                        sha256=sha,
                    )
                )
                continue
            except TarballBundleError:
                pass

        # P35 dir bundle
        if p.is_dir() and (p / "manifest.json").exists():
            try:
                verify_report_bundle_v1(p)
                sha = _sha256_file(p / "manifest.json")
                entries.append(
                    RegistryEntryV1(
                        bundle_id=p.name,
                        kind="dir_bundle",
                        ref_path=str(p),
                        sha256=sha,
                    )
                )
                continue
            except BundleIntegrityError:
                pass

        raise RegistryError(f"unsupported input: {p}")

    uniq: dict[tuple[str, str, str], RegistryEntryV1] = {}
    for e in entries:
        uniq[(e.bundle_id, e.kind, e.ref_path)] = e
    out = list(uniq.values())
    return BundleRegistryV1(schema_version=SCHEMA_VERSION_V1, entries=out)


def write_registry_v1(path: str | Path, registry: BundleRegistryV1) -> None:
    p = Path(path)
    _write_json(p, registry.to_dict())


def read_registry_v1(path: str | Path) -> BundleRegistryV1:
    p = Path(path)
    d = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(d, dict):
        raise RegistryError("registry json must be object")
    return BundleRegistryV1.from_dict(d)


def verify_registry_v1(path: str | Path) -> BundleRegistryV1:
    reg = read_registry_v1(path)
    # Check that entries are in deterministic order (as stored in file)
    ordered = sorted(reg.entries, key=lambda e: (e.bundle_id, e.kind, e.ref_path))
    if reg.entries != ordered:
        raise RegistryError("registry not deterministically ordered")
    seen: set[tuple[str, str, str]] = set()
    for e in reg.entries:
        k = (e.bundle_id, e.kind, e.ref_path)
        if k in seen:
            raise RegistryError(f"duplicate entry: {k}")
        seen.add(k)
    return reg
