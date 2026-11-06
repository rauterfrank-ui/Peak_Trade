#!/usr/bin/env python3
"""
Tests for docs graph analysis tools (_docs_graph.py, docs_graph_snapshot.py, docs_orphan_detector.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts/ops to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "ops"))

from _docs_graph import (
    build_graph,
    collect_anchors,
    extract_links,
    find_orphans,
    github_slugify,
    strip_code_fences,
    suggest_link_points,
)


class TestGitHubSlugify:
    """Test GitHub heading slugification."""

    def test_basic_heading(self):
        assert github_slugify("Introduction") == "introduction"

    def test_heading_with_spaces(self):
        assert github_slugify("Getting Started") == "getting-started"

    def test_heading_with_punctuation(self):
        assert github_slugify("What's Next?") == "whats-next"

    def test_heading_with_backticks(self):
        assert github_slugify("`config.toml` Setup") == "configtoml-setup"

    def test_heading_with_multiple_hyphens(self):
        assert github_slugify("Pre---Flight---Check") == "pre-flight-check"

    def test_heading_with_numbers(self):
        assert github_slugify("Phase 1: Setup") == "phase-1-setup"

    def test_empty_heading(self):
        assert github_slugify("") == ""


class TestStripCodeFences:
    """Test code fence stripping."""

    def test_no_code_fences(self):
        md = "# Heading\n\nSome text\n"
        assert strip_code_fences(md) == "# Heading\n\nSome text"

    def test_single_code_fence(self):
        md = "# Heading\n\n```python\ncode here\n```\n\nMore text"
        assert strip_code_fences(md) == "# Heading\n\n\nMore text"

    def test_multiple_code_fences(self):
        md = "Text\n```\ncode1\n```\nMiddle\n```\ncode2\n```\nEnd"
        assert strip_code_fences(md) == "Text\nMiddle\nEnd"


class TestCollectAnchors:
    """Test anchor collection from headings."""

    def test_single_heading(self):
        md = "# Introduction\n\nSome text"
        anchors = collect_anchors(md)
        assert "introduction" in anchors

    def test_multiple_headings(self):
        md = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
        anchors = collect_anchors(md)
        assert "heading-1" in anchors
        assert "heading-2" in anchors
        assert "heading-3" in anchors

    def test_duplicate_headings(self):
        md = "# Setup\n\n## Setup\n\n### Setup"
        anchors = collect_anchors(md)
        assert "setup" in anchors
        assert "setup-1" in anchors
        assert "setup-2" in anchors

    def test_heading_with_formatting(self):
        md = "# **Bold** and `code`"
        anchors = collect_anchors(md)
        assert "bold-and-code" in anchors


class TestExtractLinks:
    """Test link extraction from markdown."""

    def test_simple_link(self):
        md = "[Link text](docs/README.md)"
        links = extract_links(md)
        assert len(links) == 1
        assert links[0].target == "docs/README.md"
        assert links[0].anchor is None

    def test_link_with_anchor(self):
        md = "[Link](docs/README.md#introduction)"
        links = extract_links(md)
        assert len(links) == 1
        assert links[0].target == "docs/README.md"
        assert links[0].anchor == "introduction"

    def test_multiple_links(self):
        md = "[Link 1](file1.md) and [Link 2](file2.md)"
        links = extract_links(md)
        assert len(links) == 2
        assert links[0].target == "file1.md"
        assert links[1].target == "file2.md"

    def test_ignore_external_links(self):
        md = "[External](https://example.com) and [Internal](docs/README.md)"
        links = extract_links(md)
        assert len(links) == 1
        assert links[0].target == "docs/README.md"

    def test_ignore_images(self):
        md = "![Image](image.png) and [Link](docs/README.md)"
        links = extract_links(md)
        assert len(links) == 1
        assert links[0].target == "docs/README.md"

    def test_ignore_anchor_only_links(self):
        md = "[Anchor](#section) and [Link](docs/README.md)"
        links = extract_links(md)
        assert len(links) == 1
        assert links[0].target == "docs/README.md"


class TestBuildGraphWithFixtures:
    """Test graph building with test fixtures."""

    @pytest.fixture
    def fixture_root(self):
        return Path(__file__).parent.parent / "fixtures" / "docs_graph"

    def test_build_graph_basic(self, fixture_root):
        """Test basic graph building with fixtures."""
        nodes, edges, broken_targets, broken_anchors = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        # Check nodes exist
        assert "README.md" in nodes
        assert "WORKFLOW.md" in nodes
        assert "docs/README.md" in nodes
        assert "docs/sub/page.md" in nodes

        # Check orphan exists
        assert "docs/orphan.md" in nodes

        # Check edges exist
        edge_pairs = [(e.src, e.dst) for e in edges]
        assert ("README.md", "WORKFLOW.md") in edge_pairs
        assert ("README.md", "docs/README.md") in edge_pairs

        # Check broken target
        broken_target_pairs = [(b.src, b.target) for b in broken_targets]
        assert any("missing.md" in target for _, target in broken_target_pairs)

    def test_build_graph_with_anchors(self, fixture_root):
        """Test anchor validation."""
        nodes, edges, broken_targets, broken_anchors = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        # Check valid anchor edge exists
        anchor_edges = [e for e in edges if e.anchor == "section-one"]
        assert len(anchor_edges) >= 1

    def test_deterministic_ordering(self, fixture_root):
        """Test that output is deterministic (sorted)."""
        nodes1, edges1, bt1, ba1 = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        nodes2, edges2, bt2, ba2 = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        # Check nodes are in same order
        assert list(nodes1.keys()) == list(nodes2.keys())

        # Check edges are in same order
        assert [(e.src, e.dst, e.anchor) for e in edges1] == [
            (e.src, e.dst, e.anchor) for e in edges2
        ]


class TestFindOrphans:
    """Test orphan detection."""

    @pytest.fixture
    def fixture_root(self):
        return Path(__file__).parent.parent / "fixtures" / "docs_graph"

    def test_find_orphans(self, fixture_root):
        """Test orphan detection."""
        nodes, edges, broken_targets, broken_anchors = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        orphans = find_orphans(nodes=nodes, roots=["README.md"])

        # Check orphan.md is detected as orphan
        assert "docs/orphan.md" in orphans

        # Check connected files are NOT orphans
        assert "WORKFLOW.md" not in orphans
        assert "docs/README.md" not in orphans
        assert "docs/sub/page.md" not in orphans

    def test_suggest_link_points(self, fixture_root):
        """Test link point suggestions."""
        nodes, edges, broken_targets, broken_anchors = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        suggestions = suggest_link_points("docs/orphan.md", nodes)

        # Should suggest docs/README.md (same directory)
        assert "docs/README.md" in suggestions


class TestArchiveExclusion:
    """Test archive directory exclusion."""

    @pytest.fixture
    def fixture_root(self):
        return Path(__file__).parent.parent / "fixtures" / "docs_graph"

    def test_exclude_archives_false(self, fixture_root):
        """Test that archives are excluded when include_archives=False."""
        nodes, _, _, _ = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=False,
        )

        # Archive file should NOT be in nodes
        assert "docs/archive/old.md" not in nodes

    def test_include_archives_true(self, fixture_root):
        """Test that archives are included when include_archives=True."""
        nodes, _, _, _ = build_graph(
            repo_root=fixture_root,
            roots=["README.md"],
            include_archives=True,
        )

        # Archive file SHOULD be in nodes
        assert "docs/archive/old.md" in nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
