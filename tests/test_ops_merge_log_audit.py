"""
Unit tests for ops merge log audit tool.

Tests report generation (JSON and Markdown) and violation detection.
"""

import json
import tempfile
from pathlib import Path
import pytest

# Import from the audit script
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "audit"))
from check_ops_merge_logs import (
    Violation,
    check_merge_log,
    generate_json_report,
    generate_markdown_report,
)


class TestViolationClass:
    """Test the Violation data class."""

    def test_violation_creation(self):
        v = Violation("TEST_CODE", "Test message", "error")
        assert v.code == "TEST_CODE"
        assert v.message == "Test message"
        assert v.severity == "error"

    def test_violation_to_dict(self):
        v = Violation("TEST_CODE", "Test message", "warning")
        d = v.to_dict()
        assert d == {
            "code": "TEST_CODE",
            "message": "Test message",
            "severity": "warning",
        }

    def test_violation_str_error(self):
        v = Violation("TEST_CODE", "Test message", "error")
        s = str(v)
        assert "❌" in s
        assert "Test message" in s

    def test_violation_str_warning(self):
        v = Violation("TEST_CODE", "Test message", "warning")
        s = str(v)
        assert "⚠️" in s
        assert "Test message" in s


class TestCheckMergeLog:
    """Test merge log validation."""

    def test_valid_merge_log(self, tmp_path):
        """Test a fully compliant merge log."""
        log_file = tmp_path / "PR_999_MERGE_LOG.md"
        log_file.write_text(
            """# PR #999 — Post-Merge Log
**Title:** Test PR
**PR:** #999
**Merged:** 2025-12-21
**Merge Commit:** abc1234
**Branch:** test-branch (deleted)
**Change Type:** additive

## Summary
This is a test PR.

## Motivation
Testing the audit tool.

## Changes
- Added test

## Files Changed
- test.py

## Verification
- CI: pass

## Risk Assessment
Risk: low
"""
        )

        is_valid, violations = check_merge_log(log_file)
        assert is_valid
        assert len(violations) == 0

    def test_missing_headers(self, tmp_path):
        """Test detection of missing headers."""
        log_file = tmp_path / "PR_999_MERGE_LOG.md"
        log_file.write_text(
            """# PR #999
**Title:** Test

## Summary
Test

## Motivation
Test

## Changes
Test

## Files Changed
Test

## Verification
Test

## Risk Assessment
Test
"""
        )

        is_valid, violations = check_merge_log(log_file)
        assert not is_valid
        assert len(violations) > 0

        # Check that specific headers are flagged as missing
        missing_codes = [v.code for v in violations]
        assert "MISSING_HEADER" in missing_codes

    def test_missing_sections(self, tmp_path):
        """Test detection of missing sections."""
        log_file = tmp_path / "PR_999_MERGE_LOG.md"
        log_file.write_text(
            """# PR #999
**Title:** Test
**PR:** #999
**Merged:** 2025-12-21
**Merge Commit:** abc1234
**Branch:** test
**Change Type:** additive

## Summary
Test
"""
        )

        is_valid, violations = check_merge_log(log_file)
        assert not is_valid

        missing_codes = [v.code for v in violations]
        assert "MISSING_SECTION" in missing_codes

    def test_length_warning(self, tmp_path):
        """Test that long files trigger a warning."""
        log_file = tmp_path / "PR_999_MERGE_LOG.md"
        content = (
            """**Title:** Test
**PR:** #999
**Merged:** 2025-12-21
**Merge Commit:** abc1234
**Branch:** test
**Change Type:** additive

## Summary
Test

## Motivation
Test

## Changes
Test

## Files Changed
Test

## Verification
Test

## Risk Assessment
Test

"""
            + "\n" * 200
        )  # Make it long
        log_file.write_text(content)

        is_valid, violations = check_merge_log(log_file)
        assert not is_valid

        codes = [v.code for v in violations]
        assert "LENGTH_WARNING" in codes

        # Length warnings should be warnings, not errors
        length_violations = [v for v in violations if v.code == "LENGTH_WARNING"]
        assert all(v.severity == "warning" for v in length_violations)


class TestReportGeneration:
    """Test JSON and Markdown report generation."""

    def test_json_report_generation(self, tmp_path):
        """Test JSON report structure and content."""
        violations = {
            "PR_999_MERGE_LOG.md": [
                Violation("MISSING_HEADER", "Missing Title", "error"),
                Violation("MISSING_SECTION", "Missing Summary", "error"),
            ],
            "PR_998_MERGE_LOG.md": [
                Violation("LENGTH_WARNING", "Too long", "warning"),
            ],
        }

        output_path = tmp_path / "report.json"
        generate_json_report(violations, 10, 8, output_path)

        assert output_path.exists()

        data = json.loads(output_path.read_text())

        # Check required keys
        assert "timestamp" in data
        assert "summary" in data
        assert "violations" in data

        # Check summary
        assert data["summary"]["total_checked"] == 10
        assert data["summary"]["total_passed"] == 8
        assert data["summary"]["total_failed"] == 2

        # Check violations structure
        assert "PR_999_MERGE_LOG.md" in data["violations"]
        assert len(data["violations"]["PR_999_MERGE_LOG.md"]) == 2

        # Check violation details
        v = data["violations"]["PR_999_MERGE_LOG.md"][0]
        assert "code" in v
        assert "message" in v
        assert "severity" in v

    def test_markdown_report_generation(self, tmp_path):
        """Test Markdown report structure and content."""
        violations = {
            "PR_999_MERGE_LOG.md": [
                Violation("MISSING_HEADER", "Missing Title", "error"),
                Violation("MISSING_SECTION", "Missing Summary", "error"),
            ],
            "PR_998_MERGE_LOG.md": [
                Violation("LENGTH_WARNING", "Too long", "warning"),
            ],
        }

        output_path = tmp_path / "report.md"
        generate_markdown_report(violations, 10, 8, output_path)

        assert output_path.exists()

        content = output_path.read_text()

        # Check required sections
        assert "# Ops Merge Log Violations Report" in content
        assert "## Summary" in content
        assert "## Violations by File" in content
        assert "## Detailed Violations" in content
        assert "## Migration Checklist" in content
        assert "## Recommendations" in content
        assert "## Standard Requirements" in content

        # Check file paths are present
        assert "PR_999_MERGE_LOG.md" in content
        assert "PR_998_MERGE_LOG.md" in content

        # Check violation counts
        assert "2 file(s) with violations" in content

    def test_markdown_report_no_violations(self, tmp_path):
        """Test Markdown report when there are no violations."""
        violations = {}

        output_path = tmp_path / "report.md"
        generate_markdown_report(violations, 10, 10, output_path)

        assert output_path.exists()

        content = output_path.read_text()

        assert "All merge logs are compliant" in content
        assert "## Migration Checklist" not in content  # No checklist needed

    def test_json_report_no_violations(self, tmp_path):
        """Test JSON report when there are no violations."""
        violations = {}

        output_path = tmp_path / "report.json"
        generate_json_report(violations, 10, 10, output_path)

        assert output_path.exists()

        data = json.loads(output_path.read_text())

        assert data["summary"]["total_failed"] == 0
        assert len(data["violations"]) == 0


class TestReportIdempotency:
    """Test that report generation is deterministic/idempotent."""

    def test_json_report_deterministic(self, tmp_path):
        """Test that generating the same report twice produces same structure."""
        violations = {
            "PR_999_MERGE_LOG.md": [
                Violation("MISSING_HEADER", "Missing Title", "error"),
            ],
        }

        output1 = tmp_path / "report1.json"
        output2 = tmp_path / "report2.json"

        generate_json_report(violations, 10, 9, output1)
        generate_json_report(violations, 10, 9, output2)

        data1 = json.loads(output1.read_text())
        data2 = json.loads(output2.read_text())

        # Timestamps will differ, but structure should be same
        del data1["timestamp"]
        del data2["timestamp"]

        assert data1 == data2

    def test_markdown_report_has_consistent_structure(self, tmp_path):
        """Test that Markdown report has consistent structure."""
        violations = {
            "PR_999_MERGE_LOG.md": [
                Violation("MISSING_HEADER", "Missing Title", "error"),
            ],
            "PR_998_MERGE_LOG.md": [
                Violation("MISSING_HEADER", "Missing Title", "error"),
            ],
        }

        output1 = tmp_path / "report1.md"
        output2 = tmp_path / "report2.md"

        generate_markdown_report(violations, 10, 8, output1)
        generate_markdown_report(violations, 10, 8, output2)

        content1 = output1.read_text()
        content2 = output2.read_text()

        # Split into lines and filter out timestamp line
        lines1 = [l for l in content1.split("\n") if not l.startswith("**Generated:**")]
        lines2 = [l for l in content2.split("\n") if not l.startswith("**Generated:**")]

        # Structure should be identical
        assert lines1 == lines2
