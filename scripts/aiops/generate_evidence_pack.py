#!/usr/bin/env python3
"""
P5B — Evidence Pack Generator CLI (deterministic, no network)

Creates a pack with manifest.json + index.json. Writes only to out/ops/evidence_packs/.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.aiops.p5b.pack import (
    EvidencePackMeta,
    _iter_files,
    build_manifest,
    build_pack_entries,
    write_json,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_pack_dir(root: Path, pack_id: str) -> Path:
    d = root / pack_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _base_dir_relative_to_manifest(pack_dir: Path, base_dir: Path) -> str:
    """Return base_dir as path relative to pack_dir for portable manifest."""
    pack_res = pack_dir.resolve()
    base_res = base_dir.resolve()
    try:
        rel = pack_res.relative_to(base_res)
        return "/".join([".."] * len(rel.parts)) if rel.parts else "."
    except ValueError:
        try:
            rel = base_res.relative_to(pack_res)
            return rel.as_posix()
        except ValueError:
            return base_res.as_posix()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", type=str, required=True, help="Base dir for relpaths")
    ap.add_argument(
        "--in",
        dest="inputs",
        nargs="+",
        required=True,
        help="Files or dirs to include",
    )
    ap.add_argument(
        "--pack-id",
        type=str,
        default="",
        help="Deterministic pack id (optional)",
    )
    ap.add_argument(
        "--out-root",
        type=str,
        default="out/ops/evidence_packs",
        help="Output root (default out/ops/evidence_packs)",
    )
    ap.add_argument(
        "--deterministic",
        action="store_true",
        help="Use fixed timestamp for reproducible outputs (CI/testing)",
    )
    args = ap.parse_args()

    base_dir = Path(args.base_dir).expanduser().resolve()
    if not base_dir.exists():
        raise FileNotFoundError(base_dir)

    inputs = [Path(x).expanduser().resolve() for x in args.inputs]
    files = _iter_files(inputs)

    pack_id = args.pack_id.strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    out_root = Path(args.out_root).expanduser().resolve()
    pack_dir = ensure_pack_dir(out_root, f"pack_{pack_id}")

    created_at = "2026-02-11T12:00:00Z" if args.deterministic else utc_now_iso()

    entries = build_pack_entries(files, base_dir=base_dir)
    base_dir_rel = _base_dir_relative_to_manifest(pack_dir, base_dir)
    meta = EvidencePackMeta(
        pack_id=f"pack_{pack_id}",
        created_at_utc=created_at,
        base_dir=base_dir_rel,
    )

    manifest = build_manifest(meta, entries)
    write_json(pack_dir / "manifest.json", manifest)

    write_json(
        pack_dir / "index.json",
        {
            "pack_id": meta.pack_id,
            "created_at_utc": meta.created_at_utc,
            "count": len(entries),
        },
    )

    print(str(pack_dir / "manifest.json"))
    print(str(pack_dir / "index.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
