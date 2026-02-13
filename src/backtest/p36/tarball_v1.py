"""P36 — Report bundle tarball v1 (safe extract + verify)."""

from __future__ import annotations

import tarfile
import tempfile
from pathlib import Path

from src.backtest.p35.bundle_v1 import BundleIntegrityError, verify_report_bundle_v1

_ALLOWED = {"report.json", "manifest.json", "metrics_summary.json"}


class TarballBundleError(RuntimeError):
    pass


def _ensure_safe_member(name: str) -> None:
    p = Path(name)
    if p.is_absolute():
        raise TarballBundleError(f"absolute path not allowed: {name}")
    if ".." in p.parts:
        raise TarballBundleError(f"path traversal not allowed: {name}")
    if name not in _ALLOWED:
        raise TarballBundleError(f"unexpected member: {name}")


def write_bundle_tarball_v1(bundle_dir: str | Path, tar_path: str | Path) -> Path:
    bdir = Path(bundle_dir)
    if not bdir.is_dir():
        raise TarballBundleError(f"bundle_dir not a dir: {bdir}")
    out = Path(tar_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    members = [
        n for n in ("report.json", "metrics_summary.json", "manifest.json") if (bdir / n).exists()
    ]
    for n in members:
        _ensure_safe_member(n)

    with tarfile.open(out, "w:gz") as tf:
        for n in members:
            tf.add(bdir / n, arcname=n, recursive=False)

    return out


def read_bundle_tarball_v1(tar_path: str | Path, out_dir: str | Path) -> Path:
    tarp = Path(tar_path)
    if not tarp.is_file():
        raise TarballBundleError(f"tar not found: {tarp}")
    odir = Path(out_dir)
    odir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(tarp, "r:gz") as tf:
        members = tf.getmembers()
        if not members:
            raise TarballBundleError("empty tarball")

        for m in members:
            _ensure_safe_member(m.name)
            if m.isdir():
                raise TarballBundleError(f"directories not allowed in tarball: {m.name}")
            if m.issym() or m.islnk():
                raise TarballBundleError(f"links not allowed in tarball: {m.name}")

        tf.extractall(path=odir)

    return odir


def verify_bundle_tarball_v1(tar_path: str | Path) -> None:
    with tempfile.TemporaryDirectory(prefix="pt_p36_bundle_") as td:
        out_dir = Path(td) / "bundle"
        out_dir.mkdir()
        read_bundle_tarball_v1(tar_path, out_dir)
        try:
            verify_report_bundle_v1(out_dir)
        except BundleIntegrityError as e:
            raise TarballBundleError(f"bundle verify failed: {e}") from e
