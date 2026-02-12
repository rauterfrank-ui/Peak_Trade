#!/usr/bin/env python3
"""Tracked MA CLI: next | finalize | package | verify | list | journal-verify | dedupe."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def sh(
    cmd: list[str], check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture,
    )


def newest_run_id(root: Path) -> str:
    l4 = root / "out" / "ai" / "l4"
    files = sorted([p.name for p in l4.glob("*_critic_decision.md")])
    if not files:
        raise SystemExit("no L4 scaffolds found under out/ai/l4")
    return files[-1].replace("_critic_decision.md", "")


def ensure_out_ops(root: Path, name: str) -> Path:
    p = root / "out" / "ops" / name
    if not p.is_file():
        raise SystemExit(f"missing local helper: {p}")
    return p


def run_local(root: Path, *args: str) -> None:
    p = ensure_out_ops(root, args[0])
    sh([str(p), *args[1:]])


def archive_tracked(root: Path, run_id: str) -> None:
    p = root / "scripts" / "ops" / "cursor_ma_archive_run.sh"
    if not p.is_file():
        raise SystemExit(f"missing tracked archive helper: {p}")
    sh([str(p), run_id])


def manifest_path(root: Path) -> Path:
    return root / "out" / "ai" / "audit" / "manifest.ndjson"


def journal_path(root: Path) -> Path:
    return root / "out" / "ai" / "audit" / "journal.ndjson"


def read_ndjson(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            raise SystemExit(f"NDJSON_PARSE_FAIL {path} line={i} err={e}") from e
    return rows


def cmd_next(args: argparse.Namespace) -> None:
    root = root_dir()
    run_id = args.run_id or newest_run_id(root)
    run_local(root, "cursor_ma_context_file.sh", run_id)
    ctx = root / "out" / "ai" / "context" / f"{run_id}_cursor_context.txt"
    print(f"NEW_RUN_ID={run_id}")
    print(f"CONTEXT_FILE={ctx}")
    if ctx.is_file():
        print(ctx.read_text(encoding="utf-8").rstrip())


def cmd_list(args: argparse.Namespace) -> None:
    root = root_dir()
    n = str(args.n)
    run_local(root, "cursor_ma_runs.sh", n)


def cmd_verify(args: argparse.Namespace) -> None:
    root = root_dir()
    run_local(root, "cursor_ma_manifest_verify.sh")


def cmd_journal_verify(_: argparse.Namespace) -> None:
    root = root_dir()
    jp = journal_path(root)
    rows = read_ndjson(jp)
    print(f"JOURNAL_OK total_lines={len(rows)} path={jp}")


def cmd_package(args: argparse.Namespace) -> None:
    root = root_dir()
    run_id = args.run_id
    run_local(root, "cursor_ma_promote_run.sh", run_id)
    run_local(root, "cursor_ma_bundle_snapshot.sh", run_id)
    archive_tracked(root, run_id)
    run_local(root, "cursor_ma_manifest_verify.sh")
    run_local(root, "cursor_ma_runs.sh", "20")


def cmd_finalize(args: argparse.Namespace) -> None:
    root = root_dir()
    run_id = args.run_id
    finalize = root / "out" / "ops" / "cursor_ma_finalize.sh"
    if not finalize.is_file():
        raise SystemExit(f"missing local helper: {finalize}")
    cmd = [str(finalize), run_id]
    if args.force:
        cmd.append("--force")
    sh(cmd)
    run_local(root, "cursor_ma_manifest_verify.sh")
    run_local(root, "cursor_ma_runs.sh", "20")


def cmd_dedupe(_: argparse.Namespace) -> None:
    root = root_dir()
    run_local(root, "cursor_ma_manifest_dedupe.sh")
    run_local(root, "cursor_ma_manifest_verify.sh")


def main() -> None:
    p = argparse.ArgumentParser(prog="ma", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("next", help="create/print Cursor context for newest (or given) run")
    sp.add_argument("--run-id", dest="run_id", default=None)
    sp.set_defaults(func=cmd_next)

    sp = sub.add_parser("finalize", help="closeout+package; respects local finalize semantics")
    sp.add_argument("run_id")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_finalize)

    sp = sub.add_parser("package", help="promote+bundle+archive (no closeout)")
    sp.add_argument("run_id")
    sp.set_defaults(func=cmd_package)

    sp = sub.add_parser("verify", help="verify manifest index integrity")
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("journal-verify", help="parse-check journal.ndjson (append-only)")
    sp.set_defaults(func=cmd_journal_verify)

    sp = sub.add_parser("list", help="list last N runs")
    sp.add_argument("n", nargs="?", type=int, default=20)
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("dedupe", help="dedupe manifest to latest-per-run (index)")
    sp.set_defaults(func=cmd_dedupe)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
