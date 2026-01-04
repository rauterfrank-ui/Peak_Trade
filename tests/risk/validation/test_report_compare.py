"""
Tests for VaR Backtest Suite Run Comparison Tool.

Phase 8D: Report Index + Compare + HTML Summary
"""

import json
import pytest
from pathlib import Path

from src.risk.validation.report_compare import (
    load_run,
    compare_runs,
    render_compare_json,
    render_compare_md,
    render_compare_html,
    write_compare,
    RunSummary,
)


@pytest.fixture
def fixtures_root():
    """Path to test fixtures."""
    return Path(__file__).parent.parent.parent / "fixtures" / "var_suite_reports"


@pytest.fixture
def baseline_dir(fixtures_root):
    """Baseline run directory (CI green path, no regressions)."""
    return fixtures_root / "run_baseline"


@pytest.fixture
def candidate_dir(fixtures_root):
    """Candidate run directory (CI green path, no regressions)."""
    return fixtures_root / "run_candidate"


@pytest.fixture
def known_regressions_baseline_dir(fixtures_root):
    """Baseline with clean data (for negative testing)."""
    return fixtures_root / "run_known_regressions_baseline"


@pytest.fixture
def known_regressions_candidate_dir(fixtures_root):
    """Candidate with known regressions (for negative testing)."""
    return fixtures_root / "run_known_regressions_candidate"


def test_load_run(baseline_dir):
    """Test loading run summary from JSON."""
    summary = load_run(baseline_dir)

    assert summary.run_id == "run_baseline"
    assert summary.observations == 250
    assert summary.breaches == 3  # Updated: run_baseline now uses clean pass_all data
    assert summary.confidence_level == 0.95
    assert summary.overall_result == "PASS"
    assert summary.kupiec_pof_result == "PASS"
    assert summary.basel_traffic_light == "GREEN"


def test_load_run_not_found(tmp_path):
    """Test loading from non-existent directory."""
    with pytest.raises(FileNotFoundError):
        load_run(tmp_path / "nonexistent")


def test_compare_runs(baseline_dir, candidate_dir):
    """Test run comparison with CI green-path fixtures (no regressions)."""
    comparison = compare_runs(baseline_dir, candidate_dir)

    # Check structure
    assert comparison["schema_version"] == "1.0"
    assert "baseline" in comparison
    assert "candidate" in comparison
    assert "diff" in comparison
    assert "regressions" in comparison
    assert "improvements" in comparison

    # Check baseline/candidate (both clean)
    assert comparison["baseline"]["run_id"] == "run_baseline"
    assert comparison["baseline"]["overall_result"] == "PASS"
    assert comparison["candidate"]["run_id"] == "run_candidate"
    assert comparison["candidate"]["overall_result"] == "PASS"

    # No regressions expected (CI green path)
    assert len(comparison["regressions"]) == 0


def test_compare_runs_no_regressions(fixtures_root):
    """Test comparison with no regressions."""
    baseline_dir = fixtures_root / "run_baseline"
    pass_all_dir = fixtures_root / "run_pass_all"

    comparison = compare_runs(baseline_dir, pass_all_dir)

    # Both PASS -> no overall regression
    assert comparison["baseline"]["overall_result"] == "PASS"
    assert comparison["candidate"]["overall_result"] == "PASS"

    # No regressions
    assert len(comparison["regressions"]) == 0


def test_compare_runs_with_known_regressions(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test run comparison with known regressions (negative testing)."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )

    # Check structure
    assert comparison["schema_version"] == "1.0"
    assert "baseline" in comparison
    assert "candidate" in comparison
    assert "diff" in comparison
    assert "regressions" in comparison
    assert "improvements" in comparison

    # Check baseline/candidate
    assert comparison["baseline"]["run_id"] == "run_known_regressions_baseline"
    assert comparison["baseline"]["overall_result"] == "PASS"
    assert comparison["candidate"]["run_id"] == "run_known_regressions_candidate"
    assert comparison["candidate"]["overall_result"] == "FAIL"

    # Check diffs
    assert comparison["diff"]["breaches"]["baseline"] == 5
    assert comparison["diff"]["breaches"]["candidate"] == 8
    assert comparison["diff"]["breaches"]["delta"] == 3

    # Check regressions (should detect 4 known regressions)
    assert len(comparison["regressions"]) == 4

    # Verify all 4 known regressions are detected
    regression_types = {r["type"] for r in comparison["regressions"]}
    assert "overall_result" in regression_types
    assert "basel_traffic_light" in regression_types
    assert "christoffersen_cc" in regression_types
    assert "christoffersen_ind" in regression_types

    # Overall result regression should be HIGH severity
    overall_reg = next(
        (r for r in comparison["regressions"] if r["type"] == "overall_result"), None
    )
    assert overall_reg is not None
    assert overall_reg["severity"] == "HIGH"


def test_render_compare_json(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test JSON rendering with known regressions."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )
    json_output = render_compare_json(comparison)

    # Should be valid JSON
    parsed = json.loads(json_output)
    assert parsed["schema_version"] == "1.0"
    assert len(parsed["regressions"]) > 0

    # Check determinism (keys sorted)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_render_compare_md(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test Markdown rendering with known regressions."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )
    md_output = render_compare_md(comparison)

    # Check structure
    assert "# VaR Backtest Suite Run Comparison" in md_output
    assert "## Summary" in md_output
    assert "## ⚠️ Regressions" in md_output
    assert "## Detailed Metrics" in md_output

    # Check content
    assert "run_known_regressions_baseline" in md_output
    assert "run_known_regressions_candidate" in md_output
    assert "PASS" in md_output
    assert "FAIL" in md_output


def test_render_compare_html(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test HTML rendering with known regressions."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )
    html_output = render_compare_html(comparison)

    # Check structure
    assert "<!DOCTYPE html>" in html_output
    assert "<title>VaR Suite Run Comparison</title>" in html_output
    assert "<h1>VaR Backtest Suite Run Comparison</h1>" in html_output

    # Check content
    assert "run_known_regressions" in html_output

    # Check CSS
    assert "<style>" in html_output
    assert "regression" in html_output


def test_write_compare_all_formats(
    tmp_path, known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test writing comparison in all formats with known regressions."""
    out_dir = tmp_path / "compare"

    created_files = write_compare(
        out_dir=out_dir,
        baseline_dir=known_regressions_baseline_dir,
        candidate_dir=known_regressions_candidate_dir,
        formats=("json", "md", "html"),
    )

    assert len(created_files) == 3
    assert (out_dir / "compare.json").exists()
    assert (out_dir / "compare.md").exists()
    assert (out_dir / "compare.html").exists()

    # Verify content
    with open(out_dir / "compare.json") as f:
        data = json.load(f)
        assert data["schema_version"] == "1.0"
        assert len(data["regressions"]) > 0


def test_write_compare_json_only(tmp_path, baseline_dir, candidate_dir):
    """Test writing comparison with JSON format only (CI green path)."""
    out_dir = tmp_path / "compare"

    created_files = write_compare(
        out_dir=out_dir,
        baseline_dir=baseline_dir,
        candidate_dir=candidate_dir,
        formats=("json",),
    )

    assert len(created_files) == 1
    assert (out_dir / "compare.json").exists()
    assert not (out_dir / "compare.md").exists()
    assert not (out_dir / "compare.html").exists()

    # Verify no regressions (CI green path)
    with open(out_dir / "compare.json") as f:
        data = json.load(f)
        assert data["schema_version"] == "1.0"
        assert len(data["regressions"]) == 0


def test_deterministic_output(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test that comparison output is deterministic."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )

    # Generate output twice
    json_output_1 = render_compare_json(comparison)
    json_output_2 = render_compare_json(comparison)

    # Should be identical
    assert json_output_1 == json_output_2

    # Markdown should also be deterministic
    md_output_1 = render_compare_md(comparison)
    md_output_2 = render_compare_md(comparison)
    assert md_output_1 == md_output_2


def test_regression_severity_ordering(
    known_regressions_baseline_dir, known_regressions_candidate_dir
):
    """Test that regressions are ordered by severity."""
    comparison = compare_runs(
        known_regressions_baseline_dir, known_regressions_candidate_dir
    )
    regressions = comparison["regressions"]

    # Should be sorted by severity (HIGH before MEDIUM)
    severities = [r["severity"] for r in regressions]
    assert severities == sorted(severities, key=lambda s: (s != "HIGH", s != "MEDIUM"))


def test_improvements_ordering(fixtures_root):
    """Test that improvements are ordered alphabetically."""
    # Create scenario where candidate improves over baseline
    # Swap: use known_regressions_candidate as baseline (worse)
    # and known_regressions_baseline as candidate (better)
    baseline_dir = fixtures_root / "run_known_regressions_candidate"
    candidate_dir = fixtures_root / "run_known_regressions_baseline"

    comparison = compare_runs(baseline_dir, candidate_dir)
    improvements = comparison["improvements"]

    # Should be sorted by type
    if len(improvements) > 1:
        types = [i["type"] for i in improvements]
        assert types == sorted(types)
