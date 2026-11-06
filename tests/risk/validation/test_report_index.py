"""
Tests for VaR Backtest Suite Report Index Generator.

Phase 8D: Report Index + Compare + HTML Summary
"""

import json
import pytest
from pathlib import Path

from src.risk.validation.report_index import (
    discover_runs,
    build_index_payload,
    render_index_json,
    render_index_md,
    render_index_html,
    write_index,
)


@pytest.fixture
def fixtures_root():
    """Path to test fixtures."""
    return Path(__file__).parent.parent.parent / "fixtures" / "var_suite_reports"


def test_discover_runs(fixtures_root):
    """Test run discovery from report root."""
    runs = discover_runs(fixtures_root)

    # Should find 5 runs (sorted by run_id)
    assert len(runs) == 5
    assert runs[0].run_id == "run_baseline"
    assert runs[1].run_id == "run_candidate"
    assert runs[2].run_id == "run_known_regressions_baseline"
    assert runs[3].run_id == "run_known_regressions_candidate"
    assert runs[4].run_id == "run_pass_all"

    # Check metrics extraction (run_baseline now has clean data)
    baseline = runs[0]
    assert baseline.metrics["observations"] == 250
    assert baseline.metrics["breaches"] == 3
    assert baseline.metrics["overall_result"] == "PASS"
    assert baseline.metrics["basel_traffic_light"] == "GREEN"


def test_discover_runs_empty_dir(tmp_path):
    """Test discovery on empty directory."""
    runs = discover_runs(tmp_path)
    assert len(runs) == 0


def test_discover_runs_nonexistent_dir():
    """Test discovery on non-existent directory."""
    runs = discover_runs(Path("/nonexistent/path"))
    assert len(runs) == 0


def test_build_index_payload(fixtures_root):
    """Test index payload construction."""
    runs = discover_runs(fixtures_root)
    payload = build_index_payload(runs)

    assert payload["schema_version"] == "1.0"
    assert len(payload["runs"]) == 5

    # Check deterministic key ordering
    first_run = payload["runs"][0]
    assert list(first_run.keys()) == ["run_id", "path", "primary_json", "primary_md", "metrics"]

    # Metrics should be sorted
    metrics_keys = list(first_run["metrics"].keys())
    assert metrics_keys == sorted(metrics_keys)


def test_render_index_json(fixtures_root):
    """Test JSON rendering."""
    runs = discover_runs(fixtures_root)
    payload = build_index_payload(runs)
    json_output = render_index_json(payload)

    # Should be valid JSON
    parsed = json.loads(json_output)
    assert parsed["schema_version"] == "1.0"
    assert len(parsed["runs"]) == 5

    # Check determinism (keys should be sorted)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_render_index_md(fixtures_root):
    """Test Markdown rendering."""
    runs = discover_runs(fixtures_root)
    payload = build_index_payload(runs)
    md_output = render_index_md(payload)

    # Check structure
    assert "# VaR Backtest Suite Report Index" in md_output
    assert "**Total Runs:** 5" in md_output
    assert "| Run ID |" in md_output

    # Check run entries
    assert "run_baseline" in md_output
    assert "run_candidate" in md_output
    assert "run_pass_all" in md_output

    # Check results
    assert "PASS" in md_output
    assert "FAIL" in md_output


def test_render_index_html(fixtures_root):
    """Test HTML rendering."""
    runs = discover_runs(fixtures_root)
    payload = build_index_payload(runs)
    html_output = render_index_html(payload)

    # Check structure
    assert "<!DOCTYPE html>" in html_output
    assert "<title>VaR Backtest Suite Report Index</title>" in html_output
    assert "<h1>VaR Backtest Suite Report Index</h1>" in html_output

    # Check run entries
    assert "run_baseline" in html_output
    assert "run_candidate" in html_output

    # Check CSS
    assert "<style>" in html_output
    assert "font-family:" in html_output


def test_write_index_all_formats(tmp_path, fixtures_root):
    """Test writing index in all formats."""
    # Create test report root with fixture data
    test_root = tmp_path / "test_reports"
    test_root.mkdir()

    # Copy fixtures
    for run_dir in fixtures_root.glob("run_*"):
        dest = test_root / run_dir.name
        dest.mkdir()
        (dest / "suite_report.json").write_text((run_dir / "suite_report.json").read_text())
        (dest / "suite_report.md").write_text((run_dir / "suite_report.md").read_text())

    # Write index
    created_files = write_index(test_root, formats=("json", "md", "html"))

    assert len(created_files) == 3
    assert (test_root / "index.json").exists()
    assert (test_root / "index.md").exists()
    assert (test_root / "index.html").exists()

    # Verify content
    with open(test_root / "index.json") as f:
        data = json.load(f)
        assert data["schema_version"] == "1.0"
        assert len(data["runs"]) == 5


def test_write_index_json_only(tmp_path, fixtures_root):
    """Test writing index with JSON format only."""
    test_root = tmp_path / "test_reports"
    test_root.mkdir()

    # Copy fixtures
    for run_dir in fixtures_root.glob("run_*"):
        dest = test_root / run_dir.name
        dest.mkdir()
        (dest / "suite_report.json").write_text((run_dir / "suite_report.json").read_text())

    # Write index (JSON only)
    created_files = write_index(test_root, formats=("json",))

    assert len(created_files) == 1
    assert (test_root / "index.json").exists()
    assert not (test_root / "index.md").exists()
    assert not (test_root / "index.html").exists()


def test_deterministic_output(fixtures_root):
    """Test that output is deterministic across multiple runs."""
    runs = discover_runs(fixtures_root)
    payload = build_index_payload(runs)

    # Generate output twice
    json_output_1 = render_index_json(payload)
    json_output_2 = render_index_json(payload)

    # Should be identical
    assert json_output_1 == json_output_2

    # Markdown should also be deterministic
    md_output_1 = render_index_md(payload)
    md_output_2 = render_index_md(payload)
    assert md_output_1 == md_output_2
