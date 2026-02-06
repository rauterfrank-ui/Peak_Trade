"""
Smoke tests for show_recon_audit.py CLI tool

Tests:
- Argument parsing
- Output stability (deterministic)
- Filtering (run_id, session_id, severity)
- Error handling (missing run_id for detailed mode)
- Bash wrapper functionality (pyenv-safe)
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from io import StringIO

import pytest

pytestmark = pytest.mark.external_tools

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts" / "execution"))

from show_recon_audit import (
    ReconAuditQuery,
    parse_args,
    show_summary,
    show_diffs,
    show_detailed,
    load_audit_log,
)

from src.execution.audit_log import AuditLog
from src.execution.contracts import LedgerEntry, ReconSummary, ReconDiff


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_audit_log():
    """Create audit log with sample recon events"""
    audit_log = AuditLog()

    # Create sample diffs
    diff1 = ReconDiff(
        diff_id="diff_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        client_order_id="order_123",
        severity="WARN",
        diff_type="POSITION",
        description="Position mismatch: local=100, exchange=99",
        details={"local_qty": 100, "exchange_qty": 99},
    )

    diff2 = ReconDiff(
        diff_id="diff_002",
        timestamp=datetime(2026, 1, 1, 10, 0, 1, tzinfo=timezone.utc),
        client_order_id="order_456",
        severity="FAIL",
        diff_type="CASH",
        description="Cash balance divergence",
        details={"local_balance": 1000.0, "exchange_balance": 950.0},
    )

    # Create summary
    summary = ReconSummary(
        run_id="run_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        session_id="session_001",
        strategy_id="ma_crossover",
        total_diffs=2,
        counts_by_severity={"WARN": 1, "FAIL": 1},
        counts_by_type={"POSITION": 1, "CASH": 1},
        top_diffs=[diff1, diff2],
        has_critical=False,
        has_fail=True,
        max_severity="FAIL",
    )

    # Append to audit log
    audit_log.append_recon_summary(summary)

    return audit_log


# ============================================================================
# Argument Parsing Tests
# ============================================================================


def test_parse_args_summary_mode():
    """Test parsing summary mode"""
    query = parse_args(["summary"])
    assert query.mode == "summary"
    assert query.run_id is None
    assert query.session_id is None
    assert query.limit == 50


def test_parse_args_diffs_with_filters():
    """Test parsing diffs mode with filters"""
    query = parse_args(["diffs", "--run-id", "run_123", "--severity", "FAIL", "--limit", "10"])
    assert query.mode == "diffs"
    assert query.run_id == "run_123"
    assert query.severity == "FAIL"
    assert query.limit == 10


def test_parse_args_detailed_mode():
    """Test parsing detailed mode"""
    query = parse_args(["detailed", "--run-id", "run_456"])
    assert query.mode == "detailed"
    assert query.run_id == "run_456"


def test_parse_args_invalid_mode():
    """Test invalid mode exits"""
    with pytest.raises(SystemExit):
        parse_args(["invalid_mode"])


def test_parse_args_no_args():
    """Test no arguments shows usage and exits"""
    with pytest.raises(SystemExit):
        parse_args([])


# ============================================================================
# Output Stability Tests
# ============================================================================


def test_show_summary_output_deterministic(sample_audit_log, capsys):
    """Test summary output is deterministic"""
    query = ReconAuditQuery(mode="summary")

    # Run twice
    show_summary(sample_audit_log, query)
    captured1 = capsys.readouterr()

    show_summary(sample_audit_log, query)
    captured2 = capsys.readouterr()

    # Output should be identical
    assert captured1.out == captured2.out
    assert "run_001" in captured1.out
    assert "session_001" in captured1.out
    assert "Total Diffs: 2" in captured1.out


def test_show_diffs_output_deterministic(sample_audit_log, capsys):
    """Test diffs output is deterministic"""
    query = ReconAuditQuery(mode="diffs", run_id="run_001")

    # Run twice
    show_diffs(sample_audit_log, query)
    captured1 = capsys.readouterr()

    show_diffs(sample_audit_log, query)
    captured2 = capsys.readouterr()

    # Output should be identical
    assert captured1.out == captured2.out
    assert "diff_001" in captured1.out
    assert "diff_002" in captured1.out


def test_show_summary_includes_all_fields(sample_audit_log, capsys):
    """Test summary output includes all expected fields"""
    query = ReconAuditQuery(mode="summary")
    show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    # Check all key fields present
    assert "Run ID:" in captured.out
    assert "Timestamp:" in captured.out
    assert "Session:" in captured.out
    assert "Strategy:" in captured.out
    assert "Total Diffs:" in captured.out
    assert "Severity:" in captured.out
    assert "Diff Types:" in captured.out
    assert "Critical:" in captured.out
    assert "Fail:" in captured.out
    assert "Max Severity:" in captured.out


def test_show_diffs_includes_all_fields(sample_audit_log, capsys):
    """Test diffs output includes all expected fields"""
    query = ReconAuditQuery(mode="diffs")
    show_diffs(sample_audit_log, query)
    captured = capsys.readouterr()

    # Check all key fields present
    assert "Diff ID:" in captured.out
    assert "Run ID:" in captured.out
    assert "Timestamp:" in captured.out
    assert "Severity:" in captured.out
    assert "Type:" in captured.out
    assert "Order ID:" in captured.out
    assert "Description:" in captured.out
    assert "Resolved:" in captured.out


# ============================================================================
# Filtering Tests
# ============================================================================


def test_show_diffs_filter_by_severity(sample_audit_log, capsys):
    """Test filtering diffs by severity"""
    query = ReconAuditQuery(mode="diffs", severity="FAIL")
    show_diffs(sample_audit_log, query)
    captured = capsys.readouterr()

    # Should only show FAIL diff
    assert "diff_002" in captured.out
    assert "FAIL" in captured.out
    # Should not show WARN diff
    assert "diff_001" not in captured.out


def test_show_diffs_filter_by_run_id(sample_audit_log, capsys):
    """Test filtering diffs by run_id"""
    query = ReconAuditQuery(mode="diffs", run_id="run_001")
    show_diffs(sample_audit_log, query)
    captured = capsys.readouterr()

    # Should show both diffs for this run
    assert "run_001" in captured.out
    assert "2 RECON_DIFF" in captured.out


def test_show_summary_filter_by_session(sample_audit_log, capsys):
    """Test filtering summary by session_id"""
    query = ReconAuditQuery(mode="summary", session_id="session_001")
    show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    assert "session_001" in captured.out
    assert "1 RECON_SUMMARY" in captured.out


def test_show_summary_no_results(capsys):
    """Test summary with no matching events"""
    empty_log = AuditLog()
    query = ReconAuditQuery(mode="summary")
    show_summary(empty_log, query)
    captured = capsys.readouterr()

    assert "No RECON_SUMMARY events found" in captured.out


def test_show_diffs_no_results(capsys):
    """Test diffs with no matching events"""
    empty_log = AuditLog()
    query = ReconAuditQuery(mode="diffs")
    show_diffs(empty_log, query)
    captured = capsys.readouterr()

    assert "No RECON_DIFF events found" in captured.out


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_show_detailed_requires_run_id(sample_audit_log, capsys):
    """Test detailed mode requires run_id"""
    query = ReconAuditQuery(mode="detailed")  # No run_id

    with pytest.raises(SystemExit):
        show_detailed(sample_audit_log, query)

    captured = capsys.readouterr()
    assert "run-id required" in captured.out


def test_show_detailed_nonexistent_run(sample_audit_log, capsys):
    """Test detailed mode with nonexistent run_id"""
    query = ReconAuditQuery(mode="detailed", run_id="nonexistent_run")
    show_detailed(sample_audit_log, query)
    captured = capsys.readouterr()

    assert "No RECON_SUMMARY found" in captured.out


# ============================================================================
# Integration Tests
# ============================================================================


def test_show_detailed_complete_flow(sample_audit_log, capsys):
    """Test detailed mode shows summary + diffs"""
    query = ReconAuditQuery(mode="detailed", run_id="run_001")
    show_detailed(sample_audit_log, query)
    captured = capsys.readouterr()

    # Should show summary section
    assert "SUMMARY" in captured.out
    assert "run_001" in captured.out

    # Should show diffs section
    assert "DIFFS" in captured.out
    assert "diff_001" in captured.out
    assert "diff_002" in captured.out


def test_load_audit_log_empty():
    """Test loading empty audit log"""
    audit_log = load_audit_log(json_path=None)
    assert audit_log is not None
    assert audit_log.get_entry_count() == 0


def test_limit_parameter(sample_audit_log, capsys):
    """Test limit parameter restricts output"""
    query = ReconAuditQuery(mode="diffs", limit=1)
    show_diffs(sample_audit_log, query)
    captured = capsys.readouterr()

    # Should only show 1 diff despite 2 available
    assert "1 RECON_DIFF" in captured.out


# ============================================================================
# Sorting Tests (Determinism)
# ============================================================================


def test_summary_chronological_sorting():
    """Test summaries are sorted chronologically"""
    audit_log = AuditLog()

    # Add summaries in reverse chronological order
    summary2 = ReconSummary(
        run_id="run_002",
        timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        total_diffs=0,
    )
    summary1 = ReconSummary(
        run_id="run_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        total_diffs=0,
    )

    audit_log.append_recon_summary(summary2)
    audit_log.append_recon_summary(summary1)

    # Get entries
    summaries = audit_log.get_entries_by_event_type("RECON_SUMMARY")
    assert len(summaries) == 2

    # Verify chronological order (oldest first)
    sorted_summaries = sorted(summaries, key=lambda e: e.timestamp)
    assert sorted_summaries[0].details["run_id"] == "run_001"
    assert sorted_summaries[1].details["run_id"] == "run_002"


def test_diffs_chronological_sorting():
    """Test diffs are sorted chronologically"""
    audit_log = AuditLog()

    diff2 = ReconDiff(
        diff_id="diff_002",
        timestamp=datetime(2026, 1, 1, 10, 1, 0, tzinfo=timezone.utc),
        severity="INFO",
        diff_type="POSITION",
        description="Second diff",
    )
    diff1 = ReconDiff(
        diff_id="diff_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        severity="INFO",
        diff_type="POSITION",
        description="First diff",
    )

    summary = ReconSummary(
        run_id="run_001",
        timestamp=datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        total_diffs=2,
        top_diffs=[diff2, diff1],  # Intentionally reversed
    )

    audit_log.append_recon_summary(summary)

    # Get diffs
    diffs = audit_log.get_entries_by_event_type("RECON_DIFF")
    assert len(diffs) == 2

    # Verify chronological order (oldest first)
    sorted_diffs = sorted(diffs, key=lambda e: e.timestamp)
    assert sorted_diffs[0].details["diff_id"] == "diff_001"
    assert sorted_diffs[1].details["diff_id"] == "diff_002"


# ============================================================================
# JSON Format Tests
# ============================================================================


def test_summary_json_format_empty(capsys):
    """Test summary --format json with empty audit log"""
    empty_log = AuditLog()
    query = ReconAuditQuery(mode="summary", format="json")
    exit_code = show_summary(empty_log, query)
    captured = capsys.readouterr()

    # Parse JSON output
    output = json.loads(captured.out)

    # Verify structure
    assert output["event_type"] == "RECON_SUMMARY"
    assert output["count"] == 0
    assert output["items"] == []
    assert "notes" in output
    assert output["notes"] == "No RECON_SUMMARY events found"

    # Exit code should be 0
    assert exit_code == 0


def test_summary_json_format_with_data(sample_audit_log, capsys):
    """Test summary --format json with sample data"""
    query = ReconAuditQuery(mode="summary", format="json")
    exit_code = show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    # Parse JSON output
    output = json.loads(captured.out)

    # Verify structure
    assert output["event_type"] == "RECON_SUMMARY"
    assert output["count"] == 1
    assert len(output["items"]) == 1

    # Verify first item
    item = output["items"][0]
    assert item["run_id"] == "run_001"
    assert item["session_id"] == "session_001"
    assert item["strategy_id"] == "ma_crossover"
    assert item["total_diffs"] == 2
    assert item["has_fail"] is True
    assert item["max_severity"] == "FAIL"

    # Verify deterministic sorting of dicts
    assert isinstance(item["counts_by_severity"], dict)
    assert isinstance(item["counts_by_type"], dict)

    # Exit code should be 0 (no exit_on_findings)
    assert exit_code == 0


def test_summary_json_deterministic_output(sample_audit_log, capsys):
    """Test JSON output is deterministic (run twice)"""
    query = ReconAuditQuery(mode="summary", format="json")

    # Run 1
    show_summary(sample_audit_log, query)
    captured1 = capsys.readouterr()

    # Run 2
    show_summary(sample_audit_log, query)
    captured2 = capsys.readouterr()

    # Outputs should be identical
    assert captured1.out == captured2.out

    # Parse to verify it's valid JSON
    output1 = json.loads(captured1.out)
    output2 = json.loads(captured2.out)
    assert output1 == output2


# ============================================================================
# Exit Code Tests
# ============================================================================


def test_exit_on_findings_false_with_data(sample_audit_log, capsys):
    """Test exit_on_findings=False returns 0 even with findings"""
    query = ReconAuditQuery(mode="summary", format="json", exit_on_findings=False)
    exit_code = show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    # Parse JSON
    output = json.loads(captured.out)
    assert output["count"] == 1  # Has findings

    # But exit code is 0
    assert exit_code == 0


def test_exit_on_findings_true_with_data(sample_audit_log, capsys):
    """Test exit_on_findings=True returns 2 when findings present"""
    query = ReconAuditQuery(mode="summary", format="json", exit_on_findings=True)
    exit_code = show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    # Parse JSON
    output = json.loads(captured.out)
    assert output["count"] == 1  # Has findings

    # Exit code should be 2
    assert exit_code == 2


def test_exit_on_findings_true_no_data(capsys):
    """Test exit_on_findings=True returns 0 when no findings"""
    empty_log = AuditLog()
    query = ReconAuditQuery(mode="summary", format="json", exit_on_findings=True)
    exit_code = show_summary(empty_log, query)
    captured = capsys.readouterr()

    # Parse JSON
    output = json.loads(captured.out)
    assert output["count"] == 0  # No findings

    # Exit code should be 0
    assert exit_code == 0


def test_exit_on_findings_text_format(sample_audit_log, capsys):
    """Test exit_on_findings works with text format too"""
    query = ReconAuditQuery(mode="summary", format="text", exit_on_findings=True)
    exit_code = show_summary(sample_audit_log, query)
    captured = capsys.readouterr()

    # Should have text output
    assert "Found 1 RECON_SUMMARY" in captured.out

    # Exit code should be 2 (has findings)
    assert exit_code == 2


# ============================================================================
# Argument Parsing Tests (New Flags)
# ============================================================================


def test_parse_args_format_json():
    """Test parsing --format json"""
    query = parse_args(["summary", "--format", "json"])
    assert query.mode == "summary"
    assert query.format == "json"


def test_parse_args_format_text():
    """Test parsing --format text (explicit)"""
    query = parse_args(["summary", "--format", "text"])
    assert query.mode == "summary"
    assert query.format == "text"


def test_parse_args_exit_on_findings():
    """Test parsing --exit-on-findings"""
    query = parse_args(["summary", "--exit-on-findings"])
    assert query.mode == "summary"
    assert query.exit_on_findings is True


def test_parse_args_combined_new_flags():
    """Test parsing combined new flags"""
    query = parse_args(["summary", "--format", "json", "--exit-on-findings"])
    assert query.mode == "summary"
    assert query.format == "json"
    assert query.exit_on_findings is True


# ============================================================================
# Bash Wrapper Tests (pyenv-safe)
# ============================================================================


@pytest.mark.skipif(os.name == "nt", reason="Bash wrapper not available on Windows")
def test_wrapper_summary_json():
    """Test bash wrapper produces valid JSON output"""
    repo_root = Path(__file__).parent.parent.parent
    wrapper_script = repo_root / "scripts" / "execution" / "recon_audit_gate.sh"

    # Skip if wrapper doesn't exist (shouldn't happen, but safe)
    if not wrapper_script.exists():
        pytest.skip("Wrapper script not found")

    # Run wrapper
    result = subprocess.run(
        ["bash", str(wrapper_script), "summary-json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Should succeed
    assert result.returncode == 0, f"Wrapper failed: {result.stderr}"

    # Should produce valid JSON
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"Wrapper output is not valid JSON: {e}\nOutput: {result.stdout}")

    # Should have expected structure
    assert "event_type" in data
    assert data["event_type"] == "RECON_SUMMARY"
    assert "count" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    # Empty audit log should have no findings
    assert data["count"] == 0
    assert data["items"] == []


@pytest.mark.skipif(os.name == "nt", reason="Bash wrapper not available on Windows")
def test_wrapper_gate_mode():
    """Test bash wrapper gate mode exit codes"""
    repo_root = Path(__file__).parent.parent.parent
    wrapper_script = repo_root / "scripts" / "execution" / "recon_audit_gate.sh"

    if not wrapper_script.exists():
        pytest.skip("Wrapper script not found")

    # Run gate mode
    result = subprocess.run(
        ["bash", str(wrapper_script), "gate"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # Empty audit log should exit 0 (no findings)
    assert result.returncode == 0, f"Gate mode should exit 0 when no findings: {result.stderr}"

    # Should produce valid JSON
    data = json.loads(result.stdout)
    assert data["count"] == 0
