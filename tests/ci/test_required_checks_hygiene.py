"""
Tests for Required Checks Hygiene Validator (Phase 5D)

Purpose:
  Validates that the required checks hygiene validator correctly detects
  path-filtered required checks and missing required contexts.

Test Coverage:
  - PASS: Required context produced by always-on workflow
  - FAIL: Required context only produced by path-filtered workflow
  - FAIL: Required context not produced by any workflow

Phase: 5D
Date: 2026-01-12
Owner: ops
"""

import json
import tempfile
from pathlib import Path

import pytest

# Import the validator (adjust import if needed)
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "ci"))
from validate_required_checks_hygiene import RequiredChecksValidator


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "required_checks_hygiene"


def test_pass_when_required_context_produced_without_paths_filter(fixtures_dir):
    """
    Test PASS case: Required context is produced by an always-on workflow.

    Fixture: minimal_good.yml
    - Has pull_request trigger WITHOUT paths filter
    - Produces "test-check" context
    - Should PASS validation
    """
    # Create temporary workflow dir with only the good workflow
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_dir = Path(tmpdir) / "workflows"
        workflows_dir.mkdir()

        # Copy good workflow
        good_wf = fixtures_dir / "minimal_good.yml"
        (workflows_dir / "minimal_good.yml").write_text(good_wf.read_text())

        # Create config expecting "test-check"
        config = fixtures_dir / "test_config_good.json"

        # Run validator
        validator = RequiredChecksValidator(
            config_path=config,
            workflow_dir=workflows_dir,
            strict=False,
        )

        success = validator.validate()

        # Should PASS (no findings)
        assert success is True
        assert len(validator.findings) == 0


def test_fail_when_required_context_only_path_filtered(fixtures_dir):
    """
    Test FAIL case: Required context only produced by path-filtered workflow.

    Fixture: bad_path_filtered_required.yml
    - Has pull_request trigger WITH paths filter
    - Produces "path-filtered-check" context
    - Should FAIL validation (unreliable)
    """
    # Create temporary workflow dir with only the bad workflow
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_dir = Path(tmpdir) / "workflows"
        workflows_dir.mkdir()

        # Copy bad workflow
        bad_wf = fixtures_dir / "bad_path_filtered_required.yml"
        (workflows_dir / "bad_path_filtered_required.yml").write_text(bad_wf.read_text())

        # Create config expecting "path-filtered-check"
        config = fixtures_dir / "test_config_bad_path_filtered.json"

        # Run validator
        validator = RequiredChecksValidator(
            config_path=config,
            workflow_dir=workflows_dir,
            strict=False,
        )

        success = validator.validate()

        # Should FAIL (path-filtered)
        assert success is False
        assert len(validator.findings) == 1

        finding = validator.findings[0]
        assert finding["context"] == "path-filtered-check"
        assert finding["status"] == "FAIL"
        assert "path-filtered" in finding["reason"]


def test_fail_when_required_context_missing(fixtures_dir):
    """
    Test FAIL case: Required context not produced by any workflow.

    Fixture: missing_required.yml
    - Has pull_request trigger
    - Produces "some-other-check" context (NOT the required one)
    - Should FAIL validation (missing)
    """
    # Create temporary workflow dir with workflow that doesn't produce required context
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_dir = Path(tmpdir) / "workflows"
        workflows_dir.mkdir()

        # Copy workflow that produces wrong context
        missing_wf = fixtures_dir / "missing_required.yml"
        (workflows_dir / "missing_required.yml").write_text(missing_wf.read_text())

        # Create config expecting "missing-check-context"
        config = fixtures_dir / "test_config_missing.json"

        # Run validator
        validator = RequiredChecksValidator(
            config_path=config,
            workflow_dir=workflows_dir,
            strict=False,
        )

        success = validator.validate()

        # Should FAIL (not produced)
        assert success is False
        assert len(validator.findings) == 1

        finding = validator.findings[0]
        assert finding["context"] == "missing-check-context"
        assert finding["status"] == "FAIL"
        assert "not produced" in finding["reason"]


def test_pass_when_workflow_has_internal_change_detection(fixtures_dir):
    """
    Test PASS case: Workflow uses internal change detection (dorny/paths-filter).

    Fixture: good_with_internal_filter.yml
    - Has pull_request trigger WITHOUT PR-level paths filter
    - Uses dorny/paths-filter for internal detection
    - Produces "always-on-check" context
    - Should PASS validation (always-on)
    """
    # Create temporary workflow dir with internal filter workflow
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_dir = Path(tmpdir) / "workflows"
        workflows_dir.mkdir()

        # Copy good workflow with internal filter
        good_wf = fixtures_dir / "good_with_internal_filter.yml"
        (workflows_dir / "good_with_internal_filter.yml").write_text(good_wf.read_text())

        # Create config expecting "always-on-check"
        config_path = Path(tmpdir) / "test_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "required_contexts": ["always-on-check"],
                    "ignored_contexts": [],
                    "notes": "Test config",
                }
            )
        )

        # Run validator
        validator = RequiredChecksValidator(
            config_path=config_path,
            workflow_dir=workflows_dir,
            strict=False,
        )

        success = validator.validate()

        # Should PASS (no PR-level paths filter)
        assert success is True
        assert len(validator.findings) == 0


def test_validator_handles_multiple_workflows():
    """
    Test that validator correctly handles multiple workflows.

    Scenario:
    - Two workflows both producing the same required context
    - One is path-filtered, one is always-on
    - Should PASS (at least one always-on match exists)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        workflows_dir = Path(tmpdir) / "workflows"
        workflows_dir.mkdir()

        # Create two workflows producing same context
        # Workflow 1: Always-on
        wf1 = workflows_dir / "always_on.yml"
        wf1.write_text("""
name: Always On Workflow
on:
  pull_request:
jobs:
  my-check:
    name: my-check
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
""")

        # Workflow 2: Path-filtered (should be ignored since we have always-on)
        wf2 = workflows_dir / "path_filtered.yml"
        wf2.write_text("""
name: Path Filtered Workflow
on:
  pull_request:
    paths: [".github/workflows/**"]
jobs:
  my-check:
    name: my-check
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
""")

        # Create config expecting "my-check"
        config_path = Path(tmpdir) / "test_config.json"
        config_path.write_text(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "required_contexts": ["my-check"],
                    "ignored_contexts": [],
                    "notes": "Test config",
                }
            )
        )

        # Run validator
        validator = RequiredChecksValidator(
            config_path=config_path,
            workflow_dir=workflows_dir,
            strict=False,
        )

        success = validator.validate()

        # Should PASS (at least one always-on workflow exists)
        assert success is True
        assert len(validator.findings) == 0
