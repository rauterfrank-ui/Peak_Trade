#!/usr/bin/env python3
"""
Peak_Trade – Placeholder Inventory Report Generator

Deterministic, stdlib-only script that scans the repository for placeholder
markers (TODO, FIXME, TBD, XXX, etc.) and generates two local report files:

1. TODO_PLACEHOLDER_INVENTORY.md — Summary counts + top files per pattern
2. TODO_PLACEHOLDER_TARGET_MAP.md — Path-prefix breakdowns (docs/, src/, config/, etc.),
   plus per-pattern triage slices (default: `src/` and `scripts/` so code hotspots are visible
   when the global top-20 is dominated by `docs/`). With ``--prefix``, triage slices follow the
   given prefixes only.

Output location: .ops_local/inventory/ (git-ignored)

NO-LIVE: local inventory / triage only — no brokers, orders, or execution.

Large or noisy trees (e.g. ``out/``, ``.venv*/``, ``.cursor/``) are skipped by default;
see ``SKIP_DIRS`` and ``_skip_path_component`` in this file.

Usage:
    python3 scripts/ops/placeholders/generate_placeholder_reports.py
    python3 scripts/ops/placeholders/generate_placeholder_reports.py --prefix src/
    python3 scripts/ops/placeholders/generate_placeholder_reports.py --prefix src/ --prefix scripts/
    python3 scripts/ops/placeholders/generate_placeholder_reports.py --output-dir /path/to/dir

Exit codes:
    0 — Success
    1 — Error (invalid --output-dir, missing repo root, write failure, etc.)

Requirements:
    - Python 3.7+ (stdlib only, no external dependencies)
    - Must be run from within a Git repository
"""

import argparse
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

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
    "out",  # generated ops / audit trees (high noise for triage)
    ".cursor",
}


def _skip_path_component(part: str) -> bool:
    """True if a single path segment should be excluded from the walk."""
    if part in SKIP_DIRS:
        return True
    # CI/local venv clones: .venv_ci_lint, .venv_obs, …
    if part.startswith(".venv"):
        return True
    return False


# File patterns to skip
SKIP_PATTERNS = [
    r"\.lock$",  # uv.lock, package-lock.json, etc.
    r"\.pyc$",  # Python bytecode
    r"\.so$",  # Shared objects
    r"\.dylib$",  # macOS dynamic libs
    r"\.min\.js$",  # Minified JS
    r"\.map$",  # Source maps
]


def find_repo_root() -> Path:
    """Find the git repository root by walking up from current directory."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError("Not in a git repository. Cannot find .git directory.")


def normalize_path_prefix(raw: str) -> str:
    """
    Normalize a repo-relative path prefix for directory-style matching.

    Leading ``./`` is stripped; backslashes become ``/``. A non-empty prefix
    always ends with ``/`` (e.g. ``src`` → ``src/``, ``docs/ops`` → ``docs/ops/``).
    """
    p = raw.strip().replace("\\", "/").strip("./")
    if not p:
        raise ValueError("empty prefix")
    if not p.endswith("/"):
        p = p + "/"
    return p


def rel_path_matches_prefixes(rel: Path, prefixes: Sequence[str]) -> bool:
    """True if ``rel`` (repo-relative) is under at least one normalized prefix."""
    rel_s = rel.as_posix()
    if rel_s == ".":
        return False
    for pre in prefixes:
        base = pre.rstrip("/")
        if rel_s == base or rel_s.startswith(base + "/"):
            return True
    return False


def should_skip(path: Path, repo_root: Path) -> bool:
    """Determine if a file or directory should be skipped."""
    rel_path = path.relative_to(repo_root)
    for part in rel_path.parts:
        if _skip_path_component(part):
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


def scan_repository(
    repo_root: Path,
    patterns: List[Tuple[str, str]],
    path_prefixes: Optional[Sequence[str]] = None,
) -> Dict[Path, Dict[str, int]]:
    """
    Scan entire repository for patterns.

    If ``path_prefixes`` is set, only files whose repo-relative path falls under
    at least one normalized prefix are included.

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

            rel = file_path.relative_to(repo_root)
            if path_prefixes is not None and not rel_path_matches_prefixes(
                rel, path_prefixes
            ):
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


def generate_inventory_report(
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    commit: str,
    scope_note: Optional[str] = None,
) -> str:
    """Generate the TODO_PLACEHOLDER_INVENTORY.md content."""
    lines = []
    lines.append("# TODO/Placeholder Inventory")
    lines.append("")
    lines.append(f"- Repo: {repo_root}")
    lines.append(f"- Commit: {commit}")
    lines.append("- Note: Inventory-only. File is local under .ops_local (do not commit).")
    lines.append(
        "- Scan excludes: `out/`, `.cursor/`, `.venv*/`, and other dirs in SKIP_DIRS "
        "(see `generate_placeholder_reports.py`)."
    )
    if scope_note:
        lines.append(f"- Scan scope: {scope_note}")
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


# Max lines for prefix-scoped "top files" lists (src/, scripts/) per pattern.
TOP_FILES_PER_PREFIX_LIMIT = 10


def _top_files_for_category(
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    pattern_name: str,
    category: str,
) -> List[Tuple[int, str]]:
    """
    Return (count, rel_path) for files in a single categorize_by_prefix bucket, sorted.

    category is e.g. 'src/' or 'scripts/' (must match categorize_by_prefix output).
    """
    file_counts: List[Tuple[int, str]] = []
    for file_path, counts in results.items():
        if pattern_name not in counts or counts[pattern_name] <= 0:
            continue
        if categorize_by_prefix(file_path, repo_root) != category:
            continue
        rel_path = file_path.relative_to(repo_root)
        file_counts.append((counts[pattern_name], str(rel_path)))
    file_counts.sort(key=lambda x: (-x[0], x[1]))
    return file_counts


def _top_files_under_arbitrary_prefix(
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    pattern_name: str,
    prefix_norm: str,
) -> List[Tuple[int, str]]:
    """
    Like ``_top_files_for_category`` but for any normalized repo-relative prefix
    (e.g. ``docs/ops/``), not only single-segment buckets from ``categorize_by_prefix``.
    """
    pfx = prefix_norm.rstrip("/")
    file_counts: List[Tuple[int, str]] = []
    for file_path, counts in results.items():
        if pattern_name not in counts or counts[pattern_name] <= 0:
            continue
        rel = file_path.relative_to(repo_root).as_posix()
        if pfx == "":
            ok = True
        elif rel == pfx:
            ok = True
        else:
            ok = rel.startswith(pfx + "/")
        if not ok:
            continue
        file_counts.append((counts[pattern_name], rel))
    file_counts.sort(key=lambda x: (-x[0], x[1]))
    return file_counts


def _append_top_files_for_prefix_section(
    lines: List[str],
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    pattern_name: str,
    heading: str,
    category: str,
) -> None:
    """Append a fenced block of path:count lines for one prefix category."""
    lines.append(heading)
    lines.append("")
    lines.append("```")
    scoped = _top_files_for_category(results, repo_root, pattern_name, category)
    for count, path in scoped[:TOP_FILES_PER_PREFIX_LIMIT]:
        lines.append(f"{path}:{count}")
    if not scoped:
        lines.append("(none)")
    lines.append("```")
    lines.append("")


def _append_top_files_for_arbitrary_prefix(
    lines: List[str],
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    pattern_name: str,
    heading: str,
    prefix_norm: str,
) -> None:
    """Append a fenced block for files under an arbitrary path prefix."""
    lines.append(heading)
    lines.append("")
    lines.append("```")
    scoped = _top_files_under_arbitrary_prefix(
        results, repo_root, pattern_name, prefix_norm
    )
    for count, path in scoped[:TOP_FILES_PER_PREFIX_LIMIT]:
        lines.append(f"{path}:{count}")
    if not scoped:
        lines.append("(none)")
    lines.append("```")
    lines.append("")


def generate_target_map_report(
    results: Dict[Path, Dict[str, int]],
    repo_root: Path,
    triage_prefixes: Optional[Sequence[str]] = None,
) -> str:
    """Generate the TODO_PLACEHOLDER_TARGET_MAP.md content."""
    lines = []
    lines.append("# TODO/Placeholder Target Map (Inventory Addendum)")
    lines.append("")
    lines.append(
        "This file groups placeholder density by path-prefix and lists top files per marker type."
    )
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

        # Prefix-scoped tops: global top-20 is often docs-only; surface code paths explicitly.
        if triage_prefixes is None:
            _append_top_files_for_prefix_section(
                lines,
                results,
                repo_root,
                pattern_name,
                f"### Top files under `src/` (top {TOP_FILES_PER_PREFIX_LIMIT}; triage slice)",
                "src/",
            )
            _append_top_files_for_prefix_section(
                lines,
                results,
                repo_root,
                pattern_name,
                f"### Top files under `scripts/` (top {TOP_FILES_PER_PREFIX_LIMIT}; triage slice)",
                "scripts/",
            )
        else:
            for prefix_norm in triage_prefixes:
                label = prefix_norm.rstrip("/")
                display = f"{label}/" if label else "/"
                _append_top_files_for_arbitrary_prefix(
                    lines,
                    results,
                    repo_root,
                    pattern_name,
                    f"### Top files under `{display}` (top {TOP_FILES_PER_PREFIX_LIMIT}; triage slice)",
                    prefix_norm,
                )

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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Scan the repository for placeholder markers and write inventory reports "
            "(stdlib only; default output: .ops_local/inventory/).\n\n"
            "NO-LIVE: local triage tooling only — no exchanges, no orders, no execution."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Scope (NO-LIVE):
  Operator-facing inventory only. Does not connect to brokers, place orders, or run
  live or paper execution. Output is Markdown under --output-dir or
  <repo>/.ops_local/inventory/ (gitignored by default). Not a CI gate.
        """.strip(),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Directory for TODO_PLACEHOLDER_*.md (default: <repo>/.ops_local/inventory). "
            "Use an absolute path or a path relative to the current working directory. "
            "Must not be an existing file."
        ),
    )
    parser.add_argument(
        "--prefix",
        action="append",
        dest="prefixes",
        default=None,
        metavar="PATH",
        help=(
            "Repo-relative path prefix to scan (repeatable). Only files under at least one "
            "prefix are included (e.g. `src/`, `scripts/`, `docs/ops`). "
            "Default: scan the whole tree (subject to SKIP_DIRS)."
        ),
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    try:
        args = _build_arg_parser().parse_args(argv)

        resolved_output: Optional[Path] = None
        if args.output_dir is not None:
            resolved_output = Path(args.output_dir).expanduser().resolve()
            if resolved_output.exists() and resolved_output.is_file():
                print(
                    f"❌ Error: --output-dir must be a directory, not a file: {resolved_output}",
                    file=sys.stderr,
                )
                return 1

        # Find repo root
        repo_root = find_repo_root()
        print(f"📁 Repository root: {repo_root}")

        # Get current commit
        commit = get_git_commit()
        print(f"📌 Commit: {commit}")

        normalized_prefixes: Optional[List[str]] = None
        scope_note: Optional[str] = None
        if args.prefixes:
            normalized_prefixes = []
            for raw in args.prefixes:
                np = normalize_path_prefix(raw)
                if np not in normalized_prefixes:
                    normalized_prefixes.append(np)
            scope_note = " ".join(f"`{p}`" for p in normalized_prefixes)
            print(f"🔎 Path prefix filter: {', '.join(normalized_prefixes)}")

        # Scan repository
        print("🔍 Scanning repository for placeholders...")
        results = scan_repository(repo_root, PATTERNS, path_prefixes=normalized_prefixes)
        print(f"✅ Scanned {len(results)} files with matches")

        # Prepare output directory
        if resolved_output is not None:
            output_dir = resolved_output
        else:
            output_dir = repo_root / ".ops_local" / "inventory"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate and write inventory report
        inventory_path = output_dir / "TODO_PLACEHOLDER_INVENTORY.md"
        print(f"📝 Generating {inventory_path.name}...")
        inventory_content = generate_inventory_report(
            results, repo_root, commit, scope_note=scope_note
        )
        inventory_path.write_text(inventory_content, encoding="utf-8")
        print(f"✅ Wrote {inventory_path}")

        # Generate and write target map report
        target_map_path = output_dir / "TODO_PLACEHOLDER_TARGET_MAP.md"
        print(f"📝 Generating {target_map_path.name}...")
        target_map_content = generate_target_map_report(
            results,
            repo_root,
            triage_prefixes=normalized_prefixes,
        )
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
