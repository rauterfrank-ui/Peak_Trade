#!/usr/bin/env python3
"""
CI Policy: Enforce Docs Diff Guard section in key ops docs.

Checks that the "Docs Diff Guard (auto beim Merge)" marker is present
in required documentation files when relevant files change.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

MARKER = "Docs Diff Guard (auto beim Merge)"

# Files where the section should exist (at least one anchor doc)
REQUIRED_DOCS = [
    Path("docs/ops/PR_MANAGEMENT_TOOLKIT.md"),
    Path("docs/ops/PR_MANAGEMENT_QUICKSTART.md"),
    Path("docs/ops/README.md"),
]

# If any of these paths change in a PR, enforce presence in REQUIRED_DOCS (that exist)
TRIGGER_PREFIXES = [
    "docs/ops/",
    "scripts/ops/review_and_merge_pr.sh",
    "scripts/ops/docs_diff_guard.sh",
]


def sh(*args: str) -> str:
    """Run shell command and return stdout."""
    return subprocess.check_output(args, text=True).strip()


def main() -> int:
    # Determine diff base for PRs and merge_group
    try:
        base = sh("git", "merge-base", "HEAD", "origin/main")
    except subprocess.CalledProcessError:
        print("⚠️  Could not determine merge-base (running on main?). Skipping.")
        return 0

    changed = sh("git", "diff", "--name-only", f"{base}..HEAD").splitlines()
    changed = [c for c in changed if c.strip()]

    triggered = any(any(c.startswith(p) for p in TRIGGER_PREFIXES) for c in changed)
    if not triggered:
        print("✅ Docs Diff Guard Policy: not applicable (no relevant changes).")
        return 0

    missing = []
    for p in REQUIRED_DOCS:
        if not p.exists():
            continue
        s = p.read_text(encoding="utf-8")
        if MARKER not in s:
            missing.append(str(p))

    if missing:
        print("❌ Docs Diff Guard Policy: section marker missing in required docs.")
        print(f"   Marker: {MARKER}")
        print("   Missing in:")
        for m in missing:
            print(f"    - {m}")
        print("\n   Fix:")
        print(
            "     python3 scripts/ops/insert_docs_diff_guard_section.py --files "
            + ",".join(missing)
        )
        return 1

    print("✅ Docs Diff Guard Policy: OK (marker present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
