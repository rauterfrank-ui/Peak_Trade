"""
Tests for docs_graph_triage.py

Verifies:
- Deterministic output ordering
- Token policy compliance (path escaping)
- Correct categorization of broken targets and orphans
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# Import the triage functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "ops"))

from docs_graph_triage import (
    categorize_broken_targets,
    categorize_orphans,
    generate_broken_targets_md,
    generate_orphans_md,
    safe_escape_path,
)


# Minimal test fixture
MINIMAL_SNAPSHOT = {
    "metadata": {
        "timestamp": "2026-01-13T12:00:00Z",
        "nodes": 10,
        "edges": 8,
    },
    "broken_targets": [
        {
            "src": "docs/guide.md",
            "raw": "missing_file.md",
            "resolved": "missing_file.md",
            "reason": "file not found",
        },
        {
            "src": "README.md",
            "raw": "../../../outside.md",
            "resolved": "../../../outside.md",
            "reason": "outside repo",
        },
        {
            "src": "docs/ops/runbook.md",
            "raw": "another_missing.md",
            "resolved": "another_missing.md",
            "reason": "file not found",
        },
    ],
    "broken_anchors": [
        {
            "src": "docs/index.md",
            "dst": "docs/guide.md",
            "anchor": "missing-section",
            "reason": "anchor not found: #missing-section",
        }
    ],
    "orphans": [
        {
            "path": "PHASE1_SUMMARY.md"
        },
        {
            "path": "docs/ops/old_guide.md"
        },
        {
            "path": "docs/ops/runbooks/unused_runbook.md"
        },
        {
            "path": "docs/architecture.md"
        },
        {
            "path": "PHASE2_SUMMARY.md"
        },
    ],
    "nodes": [
        {"path": "README.md", "is_root": True},
        {"path": "docs/guide.md", "is_root": False},
        {"path": "docs/ops/runbook.md", "is_root": False},
    ],
    "edges": [
        {"src": "README.md", "dst": "docs/guide.md", "kind": "md", "anchor": None, "raw": "docs/guide.md"},
    ],
}


class TestSafeEscapePath:
    """Test path escaping for Token Policy compliance."""

    def test_escape_forward_slash(self):
        """Forward slashes should be escaped as &#47;"""
        assert safe_escape_path("docs/ops/README.md") == "docs&#47;ops&#47;README.md"

    def test_no_slash_unchanged(self):
        """Strings without slashes should remain unchanged."""
        assert safe_escape_path("README.md") == "README.md"

    def test_multiple_slashes(self):
        """All forward slashes should be escaped."""
        assert safe_escape_path("a/b/c/d.md") == "a&#47;b&#47;c&#47;d.md"

    def test_empty_string(self):
        """Empty strings should be handled gracefully."""
        assert safe_escape_path("") == ""


class TestCategorizeBrokenTargets:
    """Test categorization of broken targets by reason."""

    def test_categorize_by_reason(self):
        """Broken targets should be grouped by reason."""
        broken = MINIMAL_SNAPSHOT["broken_targets"]
        categorized = categorize_broken_targets(broken)

        assert "file not found" in categorized
        assert "outside repo" in categorized
        assert len(categorized["file not found"]) == 2
        assert len(categorized["outside repo"]) == 1

    def test_empty_list(self):
        """Empty list should return empty dict."""
        assert categorize_broken_targets([]) == {}


class TestCategorizeOrphans:
    """Test categorization of orphans by doc area."""

    def test_categorize_by_area(self):
        """Orphans should be grouped by doc area."""
        orphans = MINIMAL_SNAPSHOT["orphans"]
        categorized = categorize_orphans(orphans)

        assert "root" in categorized
        assert "docs/ops" in categorized
        assert "docs/ops/runbooks" in categorized
        assert "docs" in categorized

        # Check counts
        assert len(categorized["root"]) == 2  # PHASE1, PHASE2
        assert len(categorized["docs/ops"]) == 1  # old_guide
        assert len(categorized["docs/ops/runbooks"]) == 1  # unused_runbook
        assert len(categorized["docs"]) == 1  # architecture

    def test_deterministic_categorization(self):
        """Same input should produce same categorization."""
        orphans = MINIMAL_SNAPSHOT["orphans"]
        cat1 = categorize_orphans(orphans)
        cat2 = categorize_orphans(orphans)

        assert cat1.keys() == cat2.keys()
        for key in cat1:
            assert cat1[key] == cat2[key]


class TestGenerateBrokenTargetsMd:
    """Test broken targets markdown generation."""

    def test_generate_output_file(self):
        """Should generate a valid markdown file."""
        broken = MINIMAL_SNAPSHOT["broken_targets"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "broken_targets.md"
            generate_broken_targets_md(
                broken_targets=broken,
                out_path=out_path,
                snapshot_path="test/snapshot.json",
            )

            assert out_path.exists()
            content = out_path.read_text()

            # Check structure
            assert "# Broken Targets Report" in content
            assert "Total Broken Targets:" in content
            assert "file not found" in content.lower()
            assert "outside repo" in content.lower()

    def test_path_escaping_in_output(self):
        """Paths in output should be escaped per Token Policy."""
        broken = MINIMAL_SNAPSHOT["broken_targets"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "broken_targets.md"
            generate_broken_targets_md(
                broken_targets=broken,
                out_path=out_path,
                snapshot_path="test/snapshot.json",
            )

            content = out_path.read_text()

            # Check that paths are escaped
            assert "docs&#47;guide.md" in content
            assert "docs&#47;ops&#47;runbook.md" in content

            # Should NOT contain unescaped paths in inline code
            # Note: This is a heuristic check - we look for backticked paths with unescaped slashes
            import re
            # Find all backticked content
            backticked = re.findall(r"`([^`]+)`", content)
            for item in backticked:
                if "/" in item and "snapshot" not in item.lower():
                    # If it contains a slash and looks like a path (not the snapshot reference),
                    # it should be escaped
                    pytest.fail(f"Found unescaped path in inline code: {item}")


class TestGenerateOrphansMd:
    """Test orphans markdown generation."""

    def test_generate_output_file(self):
        """Should generate a valid markdown file."""
        orphans = MINIMAL_SNAPSHOT["orphans"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "orphans.md"
            generate_orphans_md(
                orphans=orphans,
                out_path=out_path,
                snapshot_path="test/snapshot.json",
            )

            assert out_path.exists()
            content = out_path.read_text()

            # Check structure
            assert "# Orphaned Pages Report" in content
            assert "Total Orphans:" in content
            assert "root" in content.lower()
            assert "docs/ops" in content.lower()

    def test_deterministic_ordering(self):
        """Output should be deterministic (same input → same output)."""
        orphans = MINIMAL_SNAPSHOT["orphans"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path1 = Path(tmpdir) / "orphans1.md"
            out_path2 = Path(tmpdir) / "orphans2.md"

            generate_orphans_md(orphans, out_path1, "test/snapshot.json")
            generate_orphans_md(orphans, out_path2, "test/snapshot.json")

            assert out_path1.read_text() == out_path2.read_text()

    def test_path_escaping_in_output(self):
        """Paths in output should be escaped per Token Policy."""
        orphans = MINIMAL_SNAPSHOT["orphans"]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "orphans.md"
            generate_orphans_md(
                orphans=orphans,
                out_path=out_path,
                snapshot_path="test/snapshot.json",
            )

            content = out_path.read_text()

            # Check that paths are escaped
            assert "docs&#47;ops&#47;old_guide.md" in content
            assert "docs&#47;ops&#47;runbooks&#47;unused_runbook.md" in content
            assert "docs&#47;architecture.md" in content


class TestIntegration:
    """Integration tests for the full triage workflow."""

    def test_full_workflow_with_fixture(self):
        """Test complete workflow: load snapshot → generate reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Write fixture snapshot
            snapshot_path = tmpdir_path / "snapshot.json"
            snapshot_path.write_text(json.dumps(MINIMAL_SNAPSHOT, indent=2))

            # Generate reports
            broken_path = tmpdir_path / "broken_targets.md"
            orphans_path = tmpdir_path / "orphans.md"

            generate_broken_targets_md(
                broken_targets=MINIMAL_SNAPSHOT["broken_targets"],
                out_path=broken_path,
                snapshot_path=str(snapshot_path),
            )

            generate_orphans_md(
                orphans=MINIMAL_SNAPSHOT["orphans"],
                out_path=orphans_path,
                snapshot_path=str(snapshot_path),
            )

            # Verify outputs exist and are non-empty
            assert broken_path.exists()
            assert orphans_path.exists()
            assert len(broken_path.read_text()) > 100
            assert len(orphans_path.read_text()) > 100

            # Verify structure
            broken_content = broken_path.read_text()
            orphans_content = orphans_path.read_text()

            assert "# Broken Targets Report" in broken_content
            assert "# Orphaned Pages Report" in orphans_content

            # Verify counts (with markdown bold formatting)
            assert "**Total Broken Targets:** 3" in broken_content
            assert "**Total Orphans:** 5" in orphans_content
