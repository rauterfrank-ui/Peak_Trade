#!/usr/bin/env python3
"""List/show simple run evidence index entries (owner navigation; non-authorizing)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.simple_run_evidence_retention_v1.storage_v1 import default_owner_index_path


def _repo_root() -> Path:
    return _REPO_ROOT


def _load_rows(index_path: Path) -> list[dict]:
    rows: list[dict] = []
    if not index_path.is_file():
        return rows
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict) and payload.get("schema", "").endswith("_entry.v1"):
            rows.append(payload)
    return rows


def cmd_list(args: argparse.Namespace) -> int:
    rows = _load_rows(args.index)
    if args.run_class:
        rows = [r for r in rows if r.get("run_class") == args.run_class]
    rows = sorted(rows, key=lambda r: r.get("started_at") or "", reverse=True)
    if args.limit is not None:
        rows = rows[: args.limit]
    for row in rows:
        print(
            "\t".join(
                [
                    str(row.get("started_at") or ""),
                    str(row.get("run_class") or ""),
                    str(row.get("status") or ""),
                    str(row.get("run_id") or ""),
                    str(row.get("retention_class") or ""),
                    str(row.get("evidence_location") or ""),
                ]
            )
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    rows = _load_rows(args.index)
    matches = [r for r in rows if r.get("run_id") == args.run_id]
    if args.run_class:
        matches = [r for r in matches if r.get("run_class") == args.run_class]
    if not matches:
        print(f"RUN_NOT_FOUND run_id={args.run_id}", file=sys.stderr)
        return 2
    print(json.dumps(matches[0], indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Simple run evidence index reader v1")
    parser.add_argument(
        "--index",
        type=Path,
        default=None,
        help="Index JSONL path",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List recent runs")
    list_p.add_argument("--run-class", choices=("paper", "shadow", "testnet", "canary"))
    list_p.add_argument("--limit", type=int, default=20)
    list_p.set_defaults(func=cmd_list)

    show_p = sub.add_parser("show", help="Show one run by run_id")
    show_p.add_argument("run_id")
    show_p.add_argument("--run-class", choices=("paper", "shadow", "testnet", "canary"))
    show_p.set_defaults(func=cmd_show)

    args = parser.parse_args(argv)
    if args.index is None:
        args.index = default_owner_index_path()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
