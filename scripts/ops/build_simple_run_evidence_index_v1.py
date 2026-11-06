#!/usr/bin/env python3
"""Build owner-facing simple run evidence index (JSONL). Non-authorizing."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.simple_run_evidence_retention_v1.index_v1 import (
    build_index_entries,
    load_index_entries_jsonl,
    merge_index_entries,
    utc_now_iso,
)
from src.ops.simple_run_evidence_retention_v1.storage_v1 import (
    default_owner_index_path,
    resolve_owner_run_evidence_root,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build simple run evidence index v1")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_repo_root(),
        help="Peak_Trade repository root (canary discovery under evidence/ops)",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        default=None,
        help=(
            "Optional read-only discovery source for paper/shadow/testnet archive runs. "
            "Does not select owner index output location."
        ),
    )
    parser.add_argument(
        "--owner-root",
        type=Path,
        default=None,
        help=(
            "Optional owner evidence root override (else PEAK_TRADE_OWNER_RUN_EVIDENCE_ROOT "
            "or $HOME/Peak_Trade_Run_Evidence)"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSONL path (default: $HOME/Peak_Trade_Run_Evidence/index/runs.jsonl)",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge with existing index at --out instead of replacing",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    owner_root = resolve_owner_run_evidence_root(
        env=os.environ,
        explicit=args.owner_root,
    )
    out_path = (
        args.out.resolve()
        if args.out is not None
        else default_owner_index_path(env=os.environ, explicit=args.owner_root)
    )

    archive_root: Path | None = None
    if args.archive_root is not None:
        archive_root = args.archive_root.resolve()

    fresh = build_index_entries(repo_root=repo_root, archive_root=archive_root)
    if args.merge and out_path.is_file():
        entries = merge_index_entries(load_index_entries_jsonl(out_path), fresh)
    else:
        entries = fresh

    header = {
        "schema": "peak_trade.simple_run_evidence_index_build.v1",
        "generated_at_utc": utc_now_iso(),
        "repo_root": str(repo_root),
        "owner_run_evidence_root": str(owner_root),
        "archive_discovery_root": str(archive_root) if archive_root else None,
        "entry_count": len(entries),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(header, sort_keys=True) + "\n")
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")

    print(f"SIMPLE_RUN_EVIDENCE_INDEX_BUILT=true path={out_path} entries={len(entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
