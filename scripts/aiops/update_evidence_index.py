#!/usr/bin/env python3
"""
P5B — Evidence Index updater (deterministic)

Scans evidence packs, produces consolidated index_all.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        o = json.load(f)
    if not isinstance(o, dict):
        raise TypeError(f"expected dict json: {p}")
    return o


def write_json(p: Path, o: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--root",
        type=str,
        default="out/ops/evidence_packs",
        help="Evidence packs root",
    )
    ap.add_argument(
        "--out",
        type=str,
        default="out/ops/evidence_packs/index_all.json",
        help="Consolidated index output",
    )
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()

    packs: List[Dict[str, Any]] = []
    if root.is_dir():
        for idx_path in sorted(root.rglob("index.json"), key=lambda x: x.as_posix()):
            try:
                idx = load_json(idx_path)
            except Exception:
                continue
            pack_dir = idx_path.parent
            manifest_path = pack_dir / "manifest.json"
            manifest = load_json(manifest_path) if manifest_path.is_file() else {}
            meta = (manifest.get("meta") or {}) if isinstance(manifest, dict) else {}
            packs.append(
                {
                    "pack_id": str(idx.get("pack_id", "")),
                    "created_at_utc": str(idx.get("created_at_utc", "")),
                    "count": int(idx.get("count", 0) or 0),
                    "pack_dir": pack_dir.as_posix(),
                    "schema_version": str(meta.get("schema_version", "")),
                }
            )

    # stable ordering: newest first by created_at_utc, then pack_id
    packs_sorted = sorted(
        packs,
        key=lambda p: (p.get("created_at_utc", ""), p.get("pack_id", "")),
        reverse=True,
    )

    write_json(
        out,
        {"root": root.as_posix(), "packs": packs_sorted, "count": len(packs_sorted)},
    )
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
