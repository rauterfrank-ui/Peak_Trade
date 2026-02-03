from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_index(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if obj.get("schema_version") != "stage1_index.v1":
        raise ValueError(f"unsupported schema_version: {obj.get('schema_version')!r}")
    if not isinstance(obj.get("entries"), list):
        raise ValueError("entries must be a list")
    return obj


def validate_index(
    root: Path,
    index_obj: Dict[str, Any],
    *,
    required_paths: Optional[List[str]] = None,
) -> Dict[str, Any]:
    errors: List[str] = []
    checked = 0
    required_paths = required_paths or []

    # required artifacts (index missing path -> "in index"; disk missing file -> "on disk")
    present = {e.get("path") for e in index_obj.get("entries", []) if isinstance(e, dict)}
    for rp in required_paths:
        if rp not in present:
            errors.append(f"missing required artifact in index: {rp}")

    # integrity (bytes/sha256 per entry)
    for e in index_obj.get("entries", []):
        if not isinstance(e, dict):
            errors.append("entry must be an object")
            continue
        rp = e.get("path")
        if not isinstance(rp, str) or not rp:
            errors.append("entry.path must be non-empty string")
            continue

        p = (root / rp).resolve()
        if not p.exists():
            errors.append(f"missing file on disk: {rp}")
            continue

        st = p.stat()
        try:
            exp_bytes = int(e.get("bytes", -1))
        except Exception:
            exp_bytes = -1
        if exp_bytes != int(st.st_size):
            errors.append(f"bytes mismatch for {rp}: index={exp_bytes} disk={st.st_size}")

        exp_sha = str(e.get("sha256", ""))
        act_sha = _sha256(p)
        if exp_sha != act_sha:
            errors.append(f"sha256 mismatch for {rp}: index={exp_sha} disk={act_sha}")

        checked += 1

    return {
        "schema_version": "stage1_validation.v1",
        "index_schema_version": index_obj.get("schema_version"),
        "run_date": index_obj.get("run_date"),
        "checked_entries": checked,
        "ok": len(errors) == 0,
        "errors": errors,
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Validate Stage1 index.json against disk artifacts.")
    ap.add_argument(
        "--root", required=True, help="Stage1 report root directory (e.g. reports/obs/stage1)"
    )
    ap.add_argument("--index", required=True, help="Path to index.json")
    ap.add_argument("--out", required=True, help="Path to validation.json output")
    ap.add_argument(
        "--require",
        action="append",
        default=[],
        help="Required relative artifact path (repeatable)",
    )
    args = ap.parse_args(argv)

    root = Path(args.root)
    index_path = Path(args.index)
    out_path = Path(args.out)

    try:
        idx = _load_index(index_path)
        rep = validate_index(root, idx, required_paths=list(args.require))
    except Exception as e:
        rep = {
            "schema_version": "stage1_validation.v1",
            "ok": False,
            "errors": [str(e)],
        }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(rep, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not rep.get("ok", False):
        print("[FAIL] stage1 validation failed", file=sys.stderr)
        return 2
    print("[OK] stage1 validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
