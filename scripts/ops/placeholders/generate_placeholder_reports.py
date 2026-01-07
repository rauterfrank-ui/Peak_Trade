#!/usr/bin/env python3
"""
Peak_Trade – Placeholder Inventory Report Generator

Deterministic, stdlib-only script that scans the repository for placeholder
markers (TODO, FIXME, TBD, XXX, etc.) and generates two local report files:

1. TODO_PLACEHOLDER_INVENTORY.md — Summary counts + top files per pattern
2. TODO_PLACEHOLDER_TARGET_MAP.md — Path-prefix breakdowns (docs/, src/, config/, etc.)

Output location: .ops_local/inventory/ (git-ignored)

Usage:
    python scripts/ops/placeholders/generate_placeholder_reports.py

Exit codes:
    0 — Success
    1 — Error (missing repo root, write failure, etc.)

Requirements:
    - Python 3.7+ (stdlib only, no external dependencies)
    - Must be run from within a Git repository
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Patterns to search for (pattern_name, regex)
PATTERNS = [
    ("TODO", r"\bTODO\b"),
    ("FIXME", r"\bFIXME\b"),
    ("TBD", r"\bTBD\b"),
    ("XXX", r"\bXXX\b"),
    ("HACK", r"\bHACK\b"),
    ("QUESTION_MARKS", r"\?\?\?"),
    ("ANGLE_TBD", r"<\s*TBD\s*>"),
    ("BRACKET_TBD", r"\[\s*TBD\s*\]"),
    ("BRACE_TBD", r"\{\s*TBD\s*\}"),
    ("ROADMAP", r"\bROADMAP\b"),
]

# Directories and patterns to skip (relative to repo root)
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".ops_local",  # Don't scan our own output folder!
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
}

# File patterns to skip
SKIP_PATTERNS = [
    r"\.lock$",      # uv.lock, package-lock.json, etc.
    r"\.pyc$",       # Python bytecode
    r"\.so$",        # Shared objects
    r"\.dylib$",     # macOS dynamic libs
    r"\.min\.js$",   # Minified JS
    r"\.map$",       # Source maps
]


def find_repo_root() -> Path:
    """Find the git repository root by walking up from current directory."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError("Not in a git repository. Cannot find .git directory.")


def should_skip(path: Path, repo_root: Path) -> bool:
    """Determine if a file or directory should be skipped."""
    # Check if any parent directory is in SKIP_DIRS
    rel_path = path.relative_to(repo_root)
    for part in rel_path.parts:
        if part in SKIP_DIRS:
            return True

    # Check file patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, path.name):
            return True

    return False


def is_text_file(path: Path) -> bool:
    """Simple heuristic to check if file is likely text (not binary)."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            # Check for null bytes (common in binary files)
            if b"\x00" in chunk:
                return False
        return True
    except Exception:
        return False


def scan_file(path: Path, patterns: List[Tuple[str, str]]) -> Dict[str, int]:
    """
    Scan a single file for all patterns and return counts.

    Returns:
        Dict mapping pattern_name to count of occurrences
    """
    counts = defaultdict(int)
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            for pattern_name, regex in patterns:
                matches = re.findall(regex, content)
                counts[pattern_name] += len(matches)
    except Exception:
        # Silently skip files that can't be read
        pass
    return counts


def scan_repository(repo_root: Path, patterns: List[Tuple[str, str]]) -> Dict[Path, Dict[str, int]]:
    """
    Scan entire repository for patterns.

    Returns:
        Dict mapping file_path to pattern_counts
    """
    results = {}

    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)

        # Skip directories in-place (modifies dirs list to prune walk)
        dirs[:] = [d for d in dirs if not should_skip(root_path / d, repo_root)]

        for filename in files:
            file_path = root_path / filename

            if should_skip(file_path, repo_root):
                continue

            if not is_text_file(file_path):
                continue

            counts = scan_file(file_path, patterns)
            if any(counts.values()):  # Only store if we found something
                results[file_path] = counts

    return results


def categorize_by_prefix(file_path: Path, repo_root: Path) -> str:
    """Categorize file by its top-level directory prefix."""
    rel_path = file_path.relative_to(repo_root)
    parts = rel_path.parts

    if not parts:
        return "other/"

    first_part = parts[0]

    # Standardize common prefixes
    if first_part == "docs":
        return "docs/"
    elif first_part == "src":
        return "src/"
    elif first_part == "config":
        return "config/"
    elif first_part == ".github":
        return ".github/"
    elif first_part == "tests":
        return "tests/"
    elif first_part == "scripts":
        return "scripts/"
    else:
        return "other/"


def generate_inventory_report(results: Dict[Path, Dict[str, int]], repo_root: Path, commit: str) -> str:
    """Generate the TODO_PLACEHOLDER_INVENTORY.md content."""
    lines = []
    lines.append("# TODO/Placeholder Inventory")
    lines.append("")
    lines.append(f"- Repo: {repo_root}")
    lines.append(f"- Commit: {commit}")
    lines.append("- Note: Inventory-only. File is local under .ops_local (do not commit).")
    lines.append("")
    lines.append("## Pattern Summary")
    lines.append("")
    lines.append("| Pattern | Regex | Count |")
    lines.append("|---|---|---:|")

    # Calculate totals per pattern
    pattern_totals = defaultdict(int)
    for file_counts in results.values():
        for pattern_name, count in file_counts.items():
            pattern_totals[pattern_name] += count

    # Stable order: by PATTERNS definition order
    for pattern_name, regex in PATTERNS:
        count = pattern_totals.get(pattern_name, 0)
        # Escape backslashes for markdown
        escaped_regex = regex.replace("\\", "\\\\")
        lines.append(f"| {pattern_name} | `{escaped_regex}` | {count} |")

    lines.append("")
    lines.append("## Top Files by Pattern")
    lines.append("")

    # For each pattern, show top 5 files
    for pattern_name, _ in PATTERNS:
        lines.append(f"### {pattern_name} (top 5)")
        lines.append("```")

        # Collect (count, path) tuples
        file_counts = []
        for file_path, counts in results.items():
            if pattern_name in counts and counts[pattern_name] > 0:
                rel_path = file_path.relative_to(repo_root)
                file_counts.append((counts[pattern_name], str(rel_path)))

        # Sort by count (desc), then path (asc) for determinism
        file_counts.sort(key=lambda x: (-x[0], x[1]))

        for count, path in file_counts[:5]:
            lines.append(f"  {count:3d} {path}")

        if not file_counts:
            lines.append("  (none)")

        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def generate_target_map_report(results: Dict[Path, Dict[str, int]], repo_root: Path) -> str:
    """Generate the TODO_PLACEHOLDER_TARGET_MAP.md content."""
    lines = []
    lines.append("# TODO/Placeholder Target Map (Inventory Addendum)")
    lines.append("")
    lines.append("This file groups placeholder density by path-prefix and lists top files per marker type.")
    lines.append("Inventory-only; local artifact under .ops_local (do not commit).")
    lines.append("")

    for pattern_name, _ in PATTERNS:
        lines.append(f"## Pattern: `{pattern_name}`")
        lines.append("")

        # Top files (top 20)
        lines.append("### Top files (top 20)")
        lines.append("")
        lines.append("```")

        file_counts = []
        for file_path, counts in results.items():
            if pattern_name in counts and counts[pattern_name] > 0:
                rel_path = file_path.relative_to(repo_root)
                file_counts.append((counts[pattern_name], str(rel_path)))

        file_counts.sort(key=lambda x: (-x[0], x[1]))

        for count, path in file_counts[:20]:
            lines.append(f"{path}:{count}")

        if not file_counts:
            lines.append("(none)")

        lines.append("```")
        lines.append("")

        # By path prefix
        lines.append("### By path prefix (docs/src/config/.github/other)")
        lines.append("")
        lines.append("```")

        prefix_totals = defaultdict(int)
        for file_path, counts in results.items():
            if pattern_name in counts and counts[pattern_name] > 0:
                prefix = categorize_by_prefix(file_path, repo_root)
                prefix_totals[prefix] += counts[pattern_name]

        # Sort by count (desc), then prefix (asc)
        sorted_prefixes = sorted(prefix_totals.items(), key=lambda x: (-x[1], x[0]))

        for prefix, count in sorted_prefixes:
            lines.append(f"{prefix}\t{count}")

        if not sorted_prefixes:
            lines.append("(none)")

        lines.append("```")
        lines.append("")

    return "\n".join(lines)


def get_git_commit() -> str:
    """Get current git commit SHA (short)."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "(unknown)"


def main() -> int:
    """Main entry point."""
    try:
        # Find repo root
        repo_root = find_repo_root()
        print(f"📁 Repository root: {repo_root}")

        # Get current commit
        commit = get_git_commit()
        print(f"📌 Commit: {commit}")

        # Scan repository
        print("🔍 Scanning repository for placeholders...")
        results = scan_repository(repo_root, PATTERNS)
        print(f"✅ Scanned {len(results)} files with matches")

        # Prepare output directory
        output_dir = repo_root / ".ops_local" / "inventory"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write inventory report
        inventory_path = output_dir / "TODO_PLACEHOLDER_INVENTORY.md"
        print(f"📝 Generating {inventory_path.name}...")
        inventory_content = generate_inventory_report(results, repo_root, commit)
        inventory_path.write_text(inventory_content, encoding="utf-8")
        print(f"✅ Wrote {inventory_path}")

        # Generate and write target map report
        target_map_path = output_dir / "TODO_PLACEHOLDER_TARGET_MAP.md"
        print(f"📝 Generating {target_map_path.name}...")
        target_map_content = generate_target_map_report(results, repo_root)
        target_map_path.write_text(target_map_content, encoding="utf-8")
        print(f"✅ Wrote {target_map_path}")

        print("")
        print("✨ Report generation complete!")
        print(f"📂 Output location: {output_dir}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
