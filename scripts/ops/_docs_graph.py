#!/usr/bin/env python3
"""
Shared utilities for docs graph analysis (snapshot + orphan detection).

Provides:
- Markdown link parsing
- Graph building from markdown files
- Anchor validation (GitHub-style heading slugs)
- Deterministic traversal and output
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Regex patterns
LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")  # ignore images ![alt](...)
CODE_FENCE_RE = re.compile(r"^```")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class Link:
    """Represents a parsed markdown link."""

    target: str
    anchor: str | None
    line: int


@dataclass
class GraphNode:
    """Represents a markdown file node in the graph."""

    path: str
    inbound: list[str] = field(default_factory=list)
    outbound: list[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """Represents an edge in the docs graph."""

    src: str
    dst: str
    anchor: str | None
    raw: str | None = None  # Raw link text from markdown


@dataclass
class BrokenTarget:
    """Represents a broken link target."""

    src: str
    target: str
    reason: str = "file not found"


@dataclass
class BrokenAnchor:
    """Represents a broken anchor reference."""

    src: str
    target: str
    anchor: str


def github_slugify(text: str) -> str:
    """
    Approximate GitHub anchor slug rules for headings.
    - lowercase
    - remove punctuation (keep spaces and hyphens)
    - collapse whitespace to '-'
    - collapse multiple '-' to one
    - strip leading/trailing '-'
    """
    s = text.strip().lower()
    # remove inline markdown formatting
    s = re.sub(r"[`*_~]+", "", s)
    # remove punctuation except spaces/hyphens
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def strip_code_fences(md: str) -> str:
    """Remove fenced code blocks to avoid matching links inside code."""
    out: list[str] = []
    in_fence = False
    for line in md.splitlines():
        if CODE_FENCE_RE.match(line.strip()):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def collect_anchors(md: str) -> set[str]:
    """
    Collect possible anchors from headings.
    GitHub duplicates: first=slug, second=slug-1, third=slug-2, etc.
    """
    counts: dict[str, int] = {}
    anchors: set[str] = set()

    for line in md.splitlines():
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        heading_text = m.group(2).strip()
        slug = github_slugify(heading_text)
        if not slug:
            continue

        n = counts.get(slug, 0)
        counts[slug] = n + 1

        anchored = slug if n == 0 else f"{slug}-{n}"
        anchors.add(anchored)

    return anchors


def parse_link_target(raw: str) -> str:
    """Strip surrounding <...> and optional title part."""
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()

    # Split on whitespace to drop optional title
    parts = raw.split()
    return parts[0].strip() if parts else ""


def extract_links(md: str) -> list[Link]:
    """Extract all internal links from markdown content."""
    links: list[Link] = []
    stripped = strip_code_fences(md)

    for line_num, line in enumerate(stripped.splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            raw_target = match.group(1)
            target = parse_link_target(raw_target)

            # Skip empty, external, or mailto links
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue

            # Skip anchor-only links
            if target.startswith("#"):
                continue

            # Split anchor
            anchor = None
            if "#" in target:
                target, anchor = target.split("#", 1)

            if target:  # Skip if target is empty after anchor split
                links.append(Link(target=target, anchor=anchor, line=line_num))

    return links


def resolve_link(source_file: Path, target: str, repo_root: Path) -> str | None:
    """
    Resolve a link target to a canonical repo-relative path.
    Returns None if target is outside repo.
    """
    if target.startswith("/"):
        # Absolute path from repo root
        target_path = target.lstrip("/")
    else:
        # Relative path from source file
        target_file = (source_file.parent / target).resolve()
        repo_root_resolved = repo_root.resolve()
        try:
            target_path = str(target_file.relative_to(repo_root_resolved))
        except ValueError:
            # Target is outside repo
            return None

    return target_path


def should_exclude_file(file_path: Path, repo_root: Path, include_archives: bool) -> bool:
    """Check if a file should be excluded from analysis."""
    try:
        rel_path = str(file_path.relative_to(repo_root))
    except ValueError:
        return True

    # Always exclude docs/_generated/**
    if rel_path.startswith("docs/_generated/"):
        return True

    # Optionally exclude archive directories
    if not include_archives:
        # Exclude docs/ops/_archive/** (production)
        if rel_path.startswith("docs/ops/_archive/"):
            return True
        # Exclude docs/archive/** (test fixtures)
        if rel_path.startswith("docs/archive/"):
            return True

    return False


def build_graph(
    repo_root: Path,
    roots: list[str],
    include_archives: bool = True,
    docs_dir: str = "docs",
) -> tuple[dict[str, GraphNode], list[GraphEdge], list[BrokenTarget], list[BrokenAnchor]]:
    """
    Build docs graph from markdown files.

    Returns:
        - nodes: dict of path -> GraphNode
        - edges: list of GraphEdge
        - broken_targets: list of BrokenTarget
        - broken_anchors: list of BrokenAnchor
    """
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    broken_targets: list[BrokenTarget] = []
    broken_anchors: list[BrokenAnchor] = []

    # Collect all markdown files (docs/ + root-level docs)
    md_files: list[Path] = []

    # Scan docs directory
    docs_path = repo_root / docs_dir
    if docs_path.exists():
        md_files.extend(
            f
            for f in docs_path.rglob("*.md")
            if not should_exclude_file(f, repo_root, include_archives)
        )

    # Scan root-level markdown files
    for md_file in repo_root.glob("*.md"):
        if md_file.is_file():
            md_files.append(md_file)

    # Remove duplicates and sort
    md_files = sorted(set(md_files))

    # First pass: create nodes and collect available anchors
    file_anchors: dict[str, set[str]] = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        rel_path = str(md_file.relative_to(repo_root))
        nodes[rel_path] = GraphNode(path=rel_path)
        file_anchors[rel_path] = collect_anchors(content)

    # Second pass: parse links and build edges
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        src_path = str(md_file.relative_to(repo_root))
        links = extract_links(content)

        for link in links:
            # Resolve target path
            resolved = resolve_link(md_file, link.target, repo_root)
            if not resolved:
                broken_targets.append(
                    BrokenTarget(src=src_path, target=link.target, reason="outside repo")
                )
                continue

            # Check if target file exists in graph
            if resolved not in nodes:
                broken_targets.append(
                    BrokenTarget(src=src_path, target=link.target, reason="file not found")
                )
                continue

            # Check anchor if specified
            if link.anchor:
                available_anchors = file_anchors.get(resolved, set())
                if link.anchor not in available_anchors:
                    broken_anchors.append(
                        BrokenAnchor(src=src_path, target=resolved, anchor=link.anchor)
                    )
                    continue

            # Add edge and update node connections
            raw_link = f"{link.target}#{link.anchor}" if link.anchor else link.target
            edges.append(GraphEdge(src=src_path, dst=resolved, anchor=link.anchor, raw=raw_link))
            nodes[src_path].outbound.append(resolved)
            nodes[resolved].inbound.append(src_path)

    # Sort node connections for determinism
    for node in nodes.values():
        node.inbound.sort()
        node.outbound.sort()

    # Sort edges and broken items for determinism
    edges.sort(key=lambda e: (e.src, e.dst, e.anchor or ""))
    broken_targets.sort(key=lambda b: (b.src, b.target))
    broken_anchors.sort(key=lambda b: (b.src, b.target, b.anchor))

    return nodes, edges, broken_targets, broken_anchors


def find_orphans(
    nodes: dict[str, GraphNode],
    roots: list[str],
) -> list[str]:
    """
    Find orphaned files (not reachable from roots via BFS).

    Returns:
        Sorted list of orphaned file paths.
    """
    visited: set[str] = set()
    to_visit: list[str] = list(roots)

    # BFS from roots
    while to_visit:
        current = to_visit.pop(0)
        if current in visited or current not in nodes:
            continue
        visited.add(current)

        # Add all outbound links to visit queue
        for target in nodes[current].outbound:
            if target not in visited:
                to_visit.append(target)

    # Find orphans: nodes not visited and not in roots
    orphans = sorted(path for path in nodes if path not in visited and path not in roots)

    return orphans


def suggest_link_points(orphan_path: str, nodes: dict[str, GraphNode]) -> list[str]:
    """
    Suggest 1-3 link insertion candidates for an orphaned file.

    Heuristics:
    1. Same directory README.md
    2. Parent directory README.md
    3. Root documentation files (WORKFLOW_FRONTDOOR, ops/README, etc.)
    """
    suggestions: list[str] = []
    orphan_parts = Path(orphan_path).parts

    # Suggestion 1: Same directory README
    if len(orphan_parts) > 1:
        same_dir_readme = str(Path(*orphan_parts[:-1]) / "README.md")
        if same_dir_readme in nodes and same_dir_readme != orphan_path:
            suggestions.append(same_dir_readme)

    # Suggestion 2: Parent directory README
    if len(orphan_parts) > 2:
        parent_readme = str(Path(*orphan_parts[:-2]) / "README.md")
        if parent_readme in nodes and parent_readme not in suggestions:
            suggestions.append(parent_readme)

    # Suggestion 3: Root documentation files
    root_docs = [
        "docs/WORKFLOW_FRONTDOOR.md",
        "docs/ops/README.md",
        "WORKFLOW_RUNBOOK_OVERVIEW_2026-01-12.md",
        "README.md",
    ]
    for root_doc in root_docs:
        if root_doc in nodes and root_doc not in suggestions:
            suggestions.append(root_doc)
            if len(suggestions) >= 3:
                break

    return suggestions[:3]
