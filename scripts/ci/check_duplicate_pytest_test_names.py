#!/usr/bin/env python3
"""Fail when the same test function name is defined twice in one test_*.py file.

AST-only: does not import test modules, does not run pytest, no network.

Allowlist (see config/ci/duplicate_test_names_allowlist.json) tolerates known legacy
duplicate names until cleaned up.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _rel_posix(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as e:
        raise SystemExit(f"path outside repo root {repo_root}: {path}") from e


def _collect_files_from_roots(repo_root: Path, roots: list[Path]) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for r in roots:
        base = (repo_root / r).resolve() if not r.is_absolute() else r.resolve()
        if base.is_file():
            if base.suffix == ".py" and base.name.startswith("test_"):
                if base not in seen:
                    seen.add(base)
                    out.append(base)
            continue
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("test_*.py")):
            if path not in seen:
                seen.add(path)
                out.append(path)
    return sorted(out)


def _default_scan_roots(repo_root: Path) -> list[Path]:
    return [repo_root / "tests"]


def find_duplicate_test_names(path: Path) -> dict[str, list[int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: dict[str, list[int]] = defaultdict(list)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith(
            "test_"
        ):
            names[node.name].append(node.lineno)
    return {k: sorted(v) for k, v in names.items() if len(v) > 1}


def load_allowlist(path: Path | None, *, no_allowlist: bool) -> dict[str, Any]:
    if no_allowlist or path is None:
        return {"version": 1, "allowed": {}}
    if not path.is_file():
        raise ValueError(f"allowlist file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("allowlist root must be a JSON object")
    ver = data.get("version")
    if ver != 1:
        raise ValueError(f"unsupported allowlist version: {ver!r}")
    allowed = data.get("allowed")
    if allowed is None:
        allowed = {}
    if not isinstance(allowed, dict):
        raise ValueError("allowlist 'allowed' must be an object")
    for rel, entry in allowed.items():
        if not isinstance(rel, str):
            raise ValueError(f"allowlist key must be string path: {rel!r}")
        if not isinstance(entry, dict):
            raise ValueError(f"allowlist entry for {rel!r} must be an object")
        names = entry.get("names")
        if not isinstance(names, list) or not all(isinstance(x, str) for x in names):
            raise ValueError(f"allowlist.names for {rel!r} must be a string array")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (defaults to Peak_Trade checkout)",
    )
    parser.add_argument(
        "--paths",
        nargs="*",
        default=None,
        help="Optional paths (files or dirs) under repo root to scan for test_*.py",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=None,
        help="JSON allowlist path (default: config/ci/duplicate_test_names_allowlist.json)",
    )
    parser.add_argument(
        "--no-allowlist",
        action="store_true",
        help="Ignore allowlist (report every duplicate)",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    allowlist_path = args.allowlist
    if allowlist_path is None and not args.no_allowlist:
        allowlist_path = repo_root / "config" / "ci" / "duplicate_test_names_allowlist.json"

    try:
        allow_doc = load_allowlist(allowlist_path, no_allowlist=args.no_allowlist)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"allowlist error: {e}", file=sys.stderr)
        return 2

    allowed_map_raw = allow_doc.get("allowed") or {}
    allowed_sets: dict[str, set[str]] = {}
    for rel, entry in allowed_map_raw.items():
        names = entry.get("names") or []
        allowed_sets[str(rel).replace("\\", "/")] = set(names)

    if args.paths:
        roots = [Path(p) for p in args.paths]
    else:
        roots = _default_scan_roots(repo_root)
    files = _collect_files_from_roots(repo_root, roots)

    violations: list[str] = []
    for path in files:
        rel = _rel_posix(path, repo_root)
        dups = find_duplicate_test_names(path)
        if not dups:
            continue
        permitted = allowed_sets.get(rel, set())
        for name, lines in sorted(dups.items()):
            if name not in permitted:
                violations.append(f"{rel}: duplicate {name!r} at lines {lines}")

    if violations:
        print("duplicate pytest test names (same file, unallowlisted):", file=sys.stderr)
        for line in violations:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
