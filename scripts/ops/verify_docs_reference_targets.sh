#!/usr/bin/env bash
set -euo pipefail

# Defaults (can be overridden via args)
REPO_ROOT=""
DOCS_ROOT=""
WARN_ONLY=0
CHANGED_ONLY=0
BASE_REF="origin/main"

usage() {
  cat <<'EOF'
verify_docs_reference_targets.sh

Scans Markdown docs for referenced repo-relative paths and verifies that the targets exist.

Exit codes:
  0 = OK / not applicable
  1 = FAIL (missing targets)
  2 = WARN (missing targets in --warn-only)

Usage:
  scripts/ops/verify_docs_reference_targets.sh [OPTIONS]

Options:
  --docs-root <path>   Directory to scan for *.md files (default: <repo-root>/docs)
  --repo-root <path>   Repository root for target existence checks (default: git rev-parse --show-toplevel)
  --changed            Scan only changed *.md files against merge-base with --base (default: origin/main)
  --base <ref>         Base ref for --changed mode (e.g. origin/main or origin/<base_branch>)
  --warn-only          Do not fail; instead return exit 2 if missing targets are found (for ops doctor)
  -h, --help           Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docs-root) DOCS_ROOT="${2:-}"; [[ -n "$DOCS_ROOT" ]] || { echo "Missing value for --docs-root"; exit 1; }; shift 2 ;;
    --repo-root) REPO_ROOT="${2:-}"; [[ -n "$REPO_ROOT" ]] || { echo "Missing value for --repo-root"; exit 1; }; shift 2 ;;
    --warn-only) WARN_ONLY=1; shift ;;
    --changed) CHANGED_ONLY=1; shift ;;
    --base) BASE_REF="${2:-}"; [[ -n "$BASE_REF" ]] || { echo "Missing value for --base"; exit 1; }; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 1 ;;
  esac
done

# Apply defaults if not provided
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

if [[ -z "$DOCS_ROOT" ]]; then
  DOCS_ROOT="$REPO_ROOT/docs"
fi

cd "$REPO_ROOT"

# Determine markdown files to scan
md_files=()

if [[ "$CHANGED_ONLY" == "1" ]]; then
  # Ensure base ref exists locally; best-effort fetch
  git fetch --quiet --prune origin >/dev/null 2>&1 || true

  # Use triple-dot to diff against merge-base
  # Exclude test fixtures (tests/fixtures/) to avoid false positives
  while IFS= read -r f; do
    [[ -n "$f" ]] && [[ "$f" != tests/fixtures/* ]] && md_files+=("$f")
  done < <(git diff --name-only "${BASE_REF}...HEAD" -- '*.md' || true)
else
  # Determine docs_root relative to repo_root for git ls-files
  docs_root_abs="$(cd "$DOCS_ROOT" 2>/dev/null && pwd || echo "$DOCS_ROOT")"
  repo_root_abs="$(pwd)"

  # Check if docs_root is under repo_root and git is available
  if [[ "$docs_root_abs" == "$repo_root_abs"* ]] && git rev-parse --git-dir >/dev/null 2>&1; then
    # Calculate relative path from repo root to docs root
    docs_root_rel="${docs_root_abs#$repo_root_abs/}"
    [[ "$docs_root_rel" == "$docs_root_abs" ]] && docs_root_rel="."

    # Use git ls-files for tracked files
    while IFS= read -r f; do
      [[ -n "$f" ]] && md_files+=("$f")
    done < <(git ls-files "$docs_root_rel" 2>/dev/null | grep -E '\.md$' | sort || true)
  else
    # Fallback to find
    while IFS= read -r f; do
      [[ -n "$f" ]] && md_files+=("$f")
    done < <(find "$DOCS_ROOT" -type f -name '*.md' 2>/dev/null | sort || true)
  fi
fi

if [[ ${#md_files[@]} -eq 0 ]]; then
  echo "Docs Reference Targets: not applicable (no markdown files to scan)."
  exit 0
fi

# Feed file list to python for robust parsing + line numbers
python3 - "$REPO_ROOT" "$WARN_ONLY" <<'PY' "${md_files[@]}"
from __future__ import annotations
import os, re, sys
from pathlib import Path
from typing import Optional

root = Path(sys.argv[1]).resolve()
warn_only = int(sys.argv[2])

files = [Path(p) for p in sys.argv[3:]]

# Patterns:
#  - Markdown links: [text](relative/path.ext)
#  - Inline code blocks: `relative/path.ext`
#  - Bare paths: config/.../x.toml (etc.)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BARE_RE = re.compile(
    r"(?<![\w/.\-])"
    r"(?:(?:config|docs|src|scripts|\.github)/[A-Za-z0-9_\-./]+?\.(?:toml|md|py|yml|yaml|sh|json|txt))"
    r"(?![\w/.\-])"
)

def is_url(s: str) -> bool:
    s2 = s.strip()
    return (
        s2.startswith("http://") or s2.startswith("https://")
        or s2.startswith("mailto:")
        or "://" in s2
    )

def normalize_target(raw: str) -> str | None:
    t = raw.strip()

    # drop surrounding angle brackets used in some markdown: (<path>)
    if t.startswith("<") and t.endswith(">"):
        t = t[1:-1].strip()

    # ignore anchors-only
    if t.startswith("#"):
        return None

    # ignore URLs
    if is_url(t):
        return None

    # strip trailing punctuation that commonly clings to paths
    t = t.strip().rstrip(").,;:]\"'")

    # strip anchor fragments: file.md#section
    if "#" in t:
        t = t.split("#", 1)[0].strip()

    # ignore empty
    if not t:
        return None

    # normalize leading ./ and leading /
    if t.startswith("./"):
        t = t[2:]
    if t.startswith("/"):
        t = t[1:]

    # ignore wildcards and globs (*, ?, [, ], <>)
    if any(c in t for c in ("*", "?", "[", "]", "<", ">")):
        return None

    # ignore if it looks like a command (ends with subcommand after space)
    # e.g. "scripts/ops/ops_center.sh doctor"
    if " " in t:
        return None

    # ignore directory-only references (trailing slash)
    if t.endswith("/"):
        return None

    # quick filter: we only validate repo-ish paths (not e.g. "foo/bar" without known roots)
    roots = ("config/", "docs/", "src/", "scripts/", ".github/")
    if not t.startswith(roots):
        return None

    return t

def safe_is_within(p: Path, root: Path) -> bool:
    try:
        rp = p.resolve()
        return str(rp).startswith(str(root))
    except Exception:
        return False

refs = []  # (doc_file, line_no, target)
for f in files:
    if not f.exists():
        continue
    try:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        continue

    # Track if we're inside a code block
    in_code_block = False

    for i, line in enumerate(lines, start=1):
        # Toggle code block state on fence markers
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        # Skip lines inside code blocks
        if in_code_block:
            continue

        # markdown links
        for raw in LINK_RE.findall(line):
            t = normalize_target(raw)
            if t:
                refs.append((str(f), i, t))
        # inline code
        for raw in CODE_RE.findall(line):
            t = normalize_target(raw)
            if t:
                refs.append((str(f), i, t))
        # bare paths
        for raw in BARE_RE.findall(line):
            t = normalize_target(raw)
            if t:
                refs.append((str(f), i, t))

# Deduplicate by (doc,line,target) but keep stable order
seen = set()
deduped = []
for r in refs:
    if r not in seen:
        seen.add(r)
        deduped.append(r)

missing = []
for doc, line_no, target in deduped:
    p = (root / target)
    # don't allow escaping repo root
    if not safe_is_within(p, root):
        missing.append((doc, line_no, target))
        continue
    if not p.exists() or not p.is_file():
        missing.append((doc, line_no, target))

print(f"Docs Reference Targets: scanned {len(files)} md file(s), found {len(deduped)} reference(s).")

if missing:
    print(f"Missing targets: {len(missing)}")
    for doc, line_no, target in missing:
        print(f"  - {doc}:{line_no}: {target}")
    sys.exit(2 if warn_only else 1)

print("All referenced targets exist.")
sys.exit(0)
PY
