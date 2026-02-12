from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_report_file(p: Path) -> bool:
    if not p.is_file():
        return False
    name = p.name
    # avoid indexing self-generated files
    if name in {"index.json", "validation.json"}:
        return False
    return p.suffix.lower() in {".json", ".jsonl", ".md", ".html", ".txt", ".csv"}


def build_index(
    root: Path,
    *,
    run_date: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    root = root.resolve()
    entries: List[Dict[str, Any]] = []

    for p in sorted(root.rglob("*")):
        if not _is_report_file(p):
            continue
        st = p.stat()
        entries.append(
            {
                "path": _relpath(p, root),
                "bytes": int(st.st_size),
                "sha256": _sha256(p),
            }
        )

    idx: Dict[str, Any] = {
        "schema_version": "stage1_index.v1",
        "root": str(root),
        "run_date": run_date,
        "entries": entries,
    }
    if generated_at:
        idx["generated_at"] = generated_at
    return idx


def write_index(out_path: Path, index_obj: Dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(index_obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Build deterministic Stage1 report index.json.")
    ap.add_argument(
        "--root", required=True, help="Root directory to index (e.g. reports/obs/stage1)"
    )
    ap.add_argument("--out", required=True, help="Output index.json path")
    ap.add_argument("--run-date", default=None, help="Run date (YYYY-MM-DD)")
    ap.add_argument("--generated-at", default=None, help="ISO timestamp (optional)")
    args = ap.parse_args(argv)

    gen = args.generated_at
    if gen is None:
        gen = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    idx = build_index(Path(args.root), run_date=args.run_date, generated_at=gen)
    write_index(Path(args.out), idx)
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
