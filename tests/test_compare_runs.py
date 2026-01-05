"""
Tests for compare_runs CLI Tool
================================

Fast, deterministic tests for run comparison.
No network access, <0.5s total.
"""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.experiments.tracking.run_summary import RunSummary

# Import functions from compare_runs script
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "dev"))

from compare_runs import (
    find_summary_files,
    load_summaries,
    format_table,
    format_diff,
)


@pytest.fixture
def sample_summaries(tmp_path):
    """Create sample run summary files."""
    summaries = []

    for i in range(3):
        summary = RunSummary(
            run_id=f"run-{i:03d}",
            started_at_utc=f"2025-01-15T10:{i:02d}:00+00:00",
            finished_at_utc=f"2025-01-15T10:{i:02d}:30+00:00",
            status="FINISHED",
            tags={"experiment": "test", "run_number": str(i)},
            params={"fast_period": 10 + i, "slow_period": 20 + i},
            metrics={
                "sharpe": 1.5 + i * 0.1,
                "total_return": 0.25 + i * 0.05,
            },
            git_sha=f"abc123{i}",
            worktree="test-worktree",
            hostname="test-host",
            tracking_backend="null",
        )

        # Write to tmp_path
        json_path = tmp_path / f"run_summary_{summary.run_id}.json"
        summary.write_json(json_path)

        summaries.append(summary)

    return tmp_path, summaries


def test_find_summary_files(sample_summaries):
    """find_summary_files discovers all summary files."""
    results_dir, expected_summaries = sample_summaries

    files = find_summary_files(results_dir)

    assert len(files) == 3
    assert all(f.name.startswith("run_summary_") for f in files)
    assert all(f.suffix == ".json" for f in files)


def test_find_summary_files_limits_n(sample_summaries):
    """find_summary_files respects n limit."""
    results_dir, _ = sample_summaries

    files = find_summary_files(results_dir, n=2)

    assert len(files) == 2


def test_find_summary_files_empty_dir(tmp_path):
    """find_summary_files returns empty list for empty dir."""
    files = find_summary_files(tmp_path)
    assert files == []


def test_find_summary_files_nonexistent_dir():
    """find_summary_files returns empty list for nonexistent dir."""
    files = find_summary_files(Path("/nonexistent/directory"))
    assert files == []


def test_load_summaries(sample_summaries):
    """load_summaries loads all valid files."""
    results_dir, expected_summaries = sample_summaries

    files = find_summary_files(results_dir)
    summaries = load_summaries(files)

    assert len(summaries) == 3, f"Expected 3 summaries, got {len(summaries)}"

    # Check each summary has expected attributes (duck typing test)
    for i, s in enumerate(summaries):
        assert hasattr(s, 'run_id'), f"Summary {i} missing run_id"
        assert hasattr(s, 'status'), f"Summary {i} missing status"
        assert hasattr(s, 'metrics'), f"Summary {i} missing metrics"

    # Verify IDs match
    loaded_ids = {s.run_id for s in summaries}
    expected_ids = {s.run_id for s in expected_summaries}
    assert loaded_ids == expected_ids


def test_load_summaries_skips_invalid(tmp_path):
    """load_summaries skips files with invalid JSON."""
    # Create valid summary
    valid_summary = RunSummary(
        run_id="valid-run",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
    )
    valid_path = tmp_path / "run_summary_valid.json"
    valid_summary.write_json(valid_path)

    # Create invalid JSON file
    invalid_path = tmp_path / "run_summary_invalid.json"
    invalid_path.write_text("not valid json {")

    # Load should get only the valid one
    files = [valid_path, invalid_path]
    summaries = load_summaries(files)

    assert len(summaries) == 1
    assert summaries[0].run_id == "valid-run"


def test_format_table_empty():
    """format_table handles empty list."""
    result = format_table([])
    assert "No runs found" in result


def test_format_table_contains_expected_rows(sample_summaries):
    """format_table output contains expected data."""
    _, summaries = sample_summaries

    result = format_table(summaries)

    # Should have header
    assert "run_id" in result
    assert "status" in result
    assert "git_sha" in result

    # Should have data rows
    for summary in summaries:
        assert summary.run_id[:8] in result
        assert summary.status in result


def test_format_table_shows_metrics(sample_summaries):
    """format_table displays metric columns."""
    _, summaries = sample_summaries

    result = format_table(summaries, key_metrics=["sharpe", "total_return"])

    # Should have metric headers
    assert "sharpe" in result
    assert "total_return" in result

    # Should have metric values (formatted)
    assert "1.5000" in result or "1.6000" in result  # From sample data


def test_format_diff_shows_changes(sample_summaries):
    """format_diff shows differences between runs."""
    _, summaries = sample_summaries

    baseline = summaries[0]
    candidate = summaries[1]

    result = format_diff(baseline, candidate)

    # Should show run IDs
    assert baseline.run_id in result
    assert candidate.run_id in result

    # Should show changed params
    assert "fast_period" in result or "Parameters" in result

    # Should show metrics
    assert "sharpe" in result or "Metrics" in result


def test_format_diff_shows_metric_deltas(sample_summaries):
    """format_diff calculates metric deltas."""
    _, summaries = sample_summaries

    baseline = summaries[0]
    candidate = summaries[1]

    result = format_diff(baseline, candidate)

    # Should show difference and percentage
    assert "Diff" in result or "%" in result


def test_format_diff_handles_missing_metrics():
    """format_diff handles metrics present in only one run."""
    baseline = RunSummary(
        run_id="baseline",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
        metrics={"sharpe": 1.5},
    )

    candidate = RunSummary(
        run_id="candidate",
        started_at_utc="2025-01-15T11:00:00+00:00",
        finished_at_utc="2025-01-15T11:05:00+00:00",
        status="FINISHED",
        metrics={"sharpe": 1.6, "new_metric": 2.0},
    )

    result = format_diff(baseline, candidate)

    # Should handle both metrics
    assert "sharpe" in result
    assert "new_metric" in result


def test_format_diff_handles_git_changes(sample_summaries):
    """format_diff shows git SHA changes."""
    _, summaries = sample_summaries

    baseline = summaries[0]
    candidate = summaries[1]

    # Ensure different SHAs
    assert baseline.git_sha != candidate.git_sha

    result = format_diff(baseline, candidate)

    # Should show git section
    if baseline.git_sha and candidate.git_sha:
        assert "Git" in result or baseline.git_sha in result


def test_format_diff_handles_status_changes():
    """format_diff shows status changes."""
    baseline = RunSummary(
        run_id="baseline",
        started_at_utc="2025-01-15T10:00:00+00:00",
        finished_at_utc="2025-01-15T10:05:00+00:00",
        status="FINISHED",
    )

    candidate = RunSummary(
        run_id="candidate",
        started_at_utc="2025-01-15T11:00:00+00:00",
        finished_at_utc="2025-01-15T11:05:00+00:00",
        status="FAILED",
    )

    result = format_diff(baseline, candidate)

    # Should show status change
    assert "Status" in result
    assert "FINISHED" in result
    assert "FAILED" in result


def test_comparison_is_fast(sample_summaries):
    """Comparison operations complete quickly."""
    import time

    results_dir, _ = sample_summaries

    start = time.time()

    # Run full comparison workflow
    files = find_summary_files(results_dir)
    summaries = load_summaries(files)
    _ = format_table(summaries)

    elapsed = time.time() - start

    # Should complete in well under 0.5s
    assert elapsed < 0.5, f"Comparison took {elapsed:.3f}s, expected < 0.5s"


def test_comparison_is_deterministic(sample_summaries):
    """Comparison output is deterministic."""
    results_dir, _ = sample_summaries

    # Run comparison twice
    files1 = find_summary_files(results_dir)
    summaries1 = load_summaries(files1)
    result1 = format_table(summaries1)

    files2 = find_summary_files(results_dir)
    summaries2 = load_summaries(files2)
    result2 = format_table(summaries2)

    # Results should be identical
    assert result1 == result2
