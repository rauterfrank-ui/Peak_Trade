#!/usr/bin/env python3
"""
Docs Drift Guard — Slice A (deterministic, PR-local).

Compares changed files against a base ref (default: origin/main). If a sensitive
path changed but none of the mapped required_docs changed, exit 1.

Exit codes:
  0 — OK (no violation, or no sensitive changes)
  1 — Drift: sensitive change without required doc update
  2 — Configuration or git error
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


def _load_mapping(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required (pip install pyyaml).")
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError("Mapping root must be a mapping.")
    return data


def _path_matches_sensitive(repo_rel: str, pattern: str) -> bool:
    """Return True if repo-relative path matches a sensitive pattern."""
    p = repo_rel.replace("\\", "/").strip()
    if not p:
        return False
    if pattern.endswith("/"):
        return p.startswith(pattern)
    return p == pattern


def _any_sensitive_triggered(
    changed: frozenset[str],
    sensitive_patterns: list[str],
) -> bool:
    for pat in sensitive_patterns:
        for ch in changed:
            if _path_matches_sensitive(ch, pat):
                return True
    return False


def _any_required_present(
    changed: frozenset[str],
    required_docs: list[str],
) -> bool:
    req = {r.replace("\\", "/") for r in required_docs}
    ch = {c.replace("\\", "/") for c in changed}
    return bool(ch & req)


def _git_changed_files(repo_root: Path, base: str) -> list[str]:
    """Paths changed on HEAD vs merge-base(base, HEAD) ... HEAD (three-dot)."""
    cmd = ["git", "-C", str(repo_root), "diff", "--name-only", f"{base}...HEAD"]
    cp = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if cp.returncode != 0:
        raise RuntimeError(
            f"git diff failed (exit {cp.returncode}).\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stderr: {cp.stderr.strip() or '(empty)'}"
        )
    lines = [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]
    return lines


def evaluate(
    changed_files: list[str],
    mapping: dict[str, Any],
) -> list[tuple[str, list[str], list[str]]]:
    """
    Return list of violations: (rule_id, triggered_sensitive, required_docs).
    """
    changed = frozenset(changed_files)
    rules = mapping.get("rules")
    if not isinstance(rules, list):
        return []

    violations: list[tuple[str, list[str], list[str]]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rid = str(rule.get("id", "unknown"))
        sens = rule.get("sensitive")
        req = rule.get("required_docs")
        if not isinstance(sens, list) or not isinstance(req, list):
            continue
        sensitive_patterns = [str(x) for x in sens]
        required_docs = [str(x) for x in req]

        triggered: list[str] = []
        for pat in sensitive_patterns:
            for ch in changed:
                if _path_matches_sensitive(ch, pat):
                    triggered.append(ch)

        if not triggered:
            continue

        if _any_required_present(changed, required_docs):
            continue

        violations.append((rid, sorted(set(triggered)), required_docs))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Docs drift guard: sensitive changes require canonical doc updates.",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Git base ref for three-dot diff (default: origin/main).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=_REPO_ROOT,
        help="Repository root (default: auto).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_REPO_ROOT / "config" / "ops" / "docs_truth_map.yaml",
        help="Path to docs_truth_map.yaml.",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    cfg_path = args.config.resolve()

    if not cfg_path.is_file():
        print(f"ERR: config not found: {cfg_path}", file=sys.stderr)
        return 2

    try:
        mapping = _load_mapping(cfg_path)
    except Exception as e:
        print(f"ERR: failed to load mapping: {e}", file=sys.stderr)
        return 2

    try:
        changed = _git_changed_files(repo_root, args.base)
    except Exception as e:
        print(f"ERR: {e}", file=sys.stderr)
        print(
            "Hint: ensure the base ref exists (e.g. git fetch origin).",
            file=sys.stderr,
        )
        return 2

    violations = evaluate(changed, mapping)

    if not violations:
        print("docs_drift_guard: OK (no sensitive changes without required doc updates).")
        print(f"  base={args.base!r}  changed_files={len(changed)}")
        return 0

    print("docs_drift_guard: FAIL — sensitive area changed but no required canonical doc in diff.\n", file=sys.stderr)
    for rid, triggered, required_docs in violations:
        print(f"  Rule: {rid}", file=sys.stderr)
        print("  Sensitive paths touched:", file=sys.stderr)
        for t in triggered:
            print(f"    - {t}", file=sys.stderr)
        print("  At least one of these docs should have been updated in the same diff:", file=sys.stderr)
        for r in required_docs:
            print(f"    - {r}", file=sys.stderr)
        print(file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
