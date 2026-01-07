#!/usr/bin/env python3
"""
Collect Docs Reference Targets Full-Scan Baseline

Performs a full scan of all markdown files in docs/ to identify missing reference targets.
Outputs a deterministic, audit-stable JSON baseline for debt tracking.

Usage:
    python scripts/ops/collect_docs_reference_targets_fullscan.py [--output FILE]

Output Format:
    {
        "generated_at_utc": "2026-01-07T04:00:00Z",
        "git_sha": "abc123...",
        "tool_version": "1.0.0",
        "missing_count": 118,
        "missing_items": [
            {
                "source_file": "docs/example.md",
                "line_number": 42,
                "target": "config/missing.toml",
                "link_text": "optional link text"
            }
        ]
    }

Exit Codes:
    0 = Success
    1 = Error (validation, file access, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Tool version for tracking baseline compatibility
TOOL_VERSION = "1.0.0"


def get_git_sha(repo_root: Path) -> str:
    """Get current git SHA, or 'unknown' if not in git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"


def load_ignore_patterns(repo_root: Path) -> list[str]:
    """Load ignore patterns from DOCS_REFERENCE_TARGETS_IGNORE.txt."""
    ignore_file = repo_root / "docs" / "ops" / "DOCS_REFERENCE_TARGETS_IGNORE.txt"
    patterns = []

    if not ignore_file.exists():
        return patterns

    try:
        for line in ignore_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    except Exception:
        pass

    return patterns


def should_ignore_file(file_path: Path, repo_root: Path, patterns: list[str]) -> bool:
    """Check if a file should be ignored based on patterns."""
    if not patterns:
        return False

    try:
        rel_path = file_path.relative_to(repo_root)
        rel_path_str = str(rel_path)
    except ValueError:
        return False

    import fnmatch

    for pattern in patterns:
        # Handle ** glob patterns
        if "**" in pattern:
            prefix = pattern.replace("/**", "").replace("**", "")
            if rel_path_str.startswith(prefix):
                return True

        # Standard fnmatch
        if fnmatch.fnmatch(rel_path_str, pattern):
            return True

    return False


def is_url(s: str) -> bool:
    """Check if string is a URL."""
    s2 = s.strip()
    return (
        s2.startswith("http://")
        or s2.startswith("https://")
        or s2.startswith("mailto:")
        or "://" in s2
    )


def normalize_target(raw: str) -> str | None:
    """Normalize a target path, filtering out non-file references."""
    t = raw.strip()

    # Strip common wrapping punctuation
    t = t.strip().lstrip("(<\"'").rstrip(")>\"'.,;:]")

    # Ignore anchors-only
    if t.startswith("#"):
        return None

    # Ignore URLs
    if is_url(t):
        return None

    # Strip anchor fragments
    if "#" in t:
        t = t.split("#", 1)[0].strip()

    # Strip query parameters
    if "?" in t:
        t = t.split("?", 1)[0].strip()

    # Ignore empty
    if not t:
        return None

    # Ignore wildcards and globs
    if any(c in t for c in ("*", "?", "[", "]", "<", ">")):
        return None

    # Ignore commands (space-separated)
    if " " in t:
        return None

    # Ignore directory-only references
    if t.endswith("/"):
        return None

    # Normalize leading / for absolute repo paths
    if t.startswith("/"):
        t = t[1:]

    # Filter: only validate repo-relative or relative paths
    is_relative = t.startswith("./") or t.startswith("../")
    roots = ("config/", "docs/", "src/", "scripts/", ".github/")

    if not is_relative and not t.startswith(roots):
        return None

    return t


def resolve_target(target: str, doc_file: Path, repo_root: Path) -> Path | None:
    """Resolve target to absolute path within repo."""
    try:
        if target.startswith("./") or target.startswith("../"):
            # Relative to doc file's directory
            resolved = (doc_file.parent / target).resolve()
        else:
            # Repo-relative
            resolved = (repo_root / target).resolve()

        # Ensure within repo
        if not str(resolved).startswith(str(repo_root)):
            return None

        return resolved
    except Exception:
        return None


def extract_references(
    file_path: Path, repo_root: Path
) -> list[tuple[int, str, str]]:
    """
    Extract references from markdown file.

    Returns:
        List of (line_number, target, link_text) tuples
    """
    # Regex patterns (matching verify_docs_reference_targets.sh logic)
    LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
    CODE_RE = re.compile(r"`([^`]+)`")
    BARE_RE = re.compile(
        r"(?<![\w/.\-])"
        r"(?:(?:config|docs|src|scripts|\.github)/[A-Za-z0-9_\-./]+?\.(?:toml|md|py|yml|yaml|sh|json|txt))"
        r"(?![\w/.\-])"
    )
    IGNORE_MARKER = "<!-- pt:ref-target-ignore -->"

    refs = []

    try:
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return refs

    in_code_block = False

    for i, line in enumerate(lines, start=1):
        # Toggle code block state
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip code blocks and ignored lines
        if in_code_block or IGNORE_MARKER in line:
            continue

        # Extract markdown links [text](target)
        for match in LINK_RE.finditer(line):
            link_text = match.group(1)
            target = normalize_target(match.group(2))
            if target:
                refs.append((i, target, link_text))

        # Extract inline code `target`
        for match in CODE_RE.finditer(line):
            target = normalize_target(match.group(1))
            if target:
                refs.append((i, target, ""))

        # Extract bare paths
        for match in BARE_RE.finditer(line):
            target = normalize_target(match.group(0))
            if target:
                refs.append((i, target, ""))

    return refs


def scan_docs(repo_root: Path) -> dict[str, Any]:
    """
    Perform full scan of docs/ directory.

    Returns:
        Dict with scan results ready for JSON serialization
    """
    docs_root = repo_root / "docs"

    if not docs_root.exists():
        print(f"Error: docs/ directory not found at {docs_root}", file=sys.stderr)
        sys.exit(1)

    # Load ignore patterns
    ignore_patterns = load_ignore_patterns(repo_root)

    # Find all markdown files (tracked by git)
    try:
        result = subprocess.run(
            ["git", "ls-files", "docs"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        md_files = [
            repo_root / line
            for line in result.stdout.splitlines()
            if line.endswith(".md")
        ]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Fallback to find
        md_files = list(docs_root.rglob("*.md"))

    # Scan files
    missing_items = []
    total_refs = 0
    ignored_files = 0

    for md_file in sorted(md_files):
        if not md_file.exists():
            continue

        # Check if file should be ignored
        if should_ignore_file(md_file, repo_root, ignore_patterns):
            ignored_files += 1
            continue

        # Extract references
        refs = extract_references(md_file, repo_root)
        total_refs += len(refs)

        # Check each reference
        for line_no, target, link_text in refs:
            resolved = resolve_target(target, md_file, repo_root)

            if resolved is None or not resolved.exists():
                # Get relative paths for cleaner output
                try:
                    rel_source = str(md_file.relative_to(repo_root))
                except ValueError:
                    rel_source = str(md_file)

                missing_items.append({
                    "source_file": rel_source,
                    "line_number": line_no,
                    "target": target,
                    "link_text": link_text if link_text else None,
                })

    # Sort deterministically: source_file, line_number, target
    missing_items.sort(key=lambda x: (x["source_file"], x["line_number"], x["target"]))

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": get_git_sha(repo_root),
        "tool_version": TOOL_VERSION,
        "scan_stats": {
            "total_markdown_files": len(md_files),
            "ignored_files": ignored_files,
            "scanned_files": len(md_files) - ignored_files,
            "total_references": total_refs,
        },
        "missing_count": len(missing_items),
        "missing_items": missing_items,
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Collect docs reference targets full-scan baseline"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json",
        help="Output JSON file path (default: docs/ops/DOCS_REFERENCE_TARGETS_BASELINE.json)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root (default: auto-detect via git)",
    )

    args = parser.parse_args()

    # Determine repo root
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
            repo_root = Path(result.stdout.strip()).resolve()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            repo_root = Path.cwd()

    print(f"Scanning docs/ in {repo_root}...", file=sys.stderr)

    # Perform scan
    results = scan_docs(repo_root)

    # Determine output path
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = repo_root / output_path

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with deterministic formatting
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=False, ensure_ascii=False)
        f.write("\n")  # Trailing newline for git-friendly diffs

    # Print summary
    print(f"\n✅ Baseline collected:", file=sys.stderr)
    print(f"   Scanned: {results['scan_stats']['scanned_files']} markdown files", file=sys.stderr)
    print(f"   Total references: {results['scan_stats']['total_references']}", file=sys.stderr)
    print(f"   Missing targets: {results['missing_count']}", file=sys.stderr)

    # Show output path (relative if inside repo, absolute otherwise)
    try:
        rel_output = output_path.relative_to(repo_root)
        print(f"   Output: {rel_output}", file=sys.stderr)
    except ValueError:
        print(f"   Output: {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
