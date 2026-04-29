"""Tests for scripts/ops/report_class_a_spot_paper_snapshot_v0.py (read-only)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path("scripts/ops/report_class_a_spot_paper_snapshot_v0.py")

from scripts.ops.report_class_a_spot_paper_snapshot_v0 import (  # noqa: E402
    build_json_payload,
    coerce_run_list,
    fetch_runs_via_gh,
    render_markdown,
    summarize_runs,
)


def _sample_runs() -> list[dict[str, object]]:
    return [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "event": "schedule",
            "createdAt": "2026-04-29T18:00:00Z",
            "updatedAt": "2026-04-29T18:05:00Z",
            "headBranch": "main",
            "headSha": "abc",
            "url": "https://example.com/1",
        },
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "skipped",
            "event": "schedule",
            "createdAt": "2026-04-28T12:00:00Z",
            "updatedAt": "2026-04-28T12:01:00Z",
            "headBranch": "main",
            "headSha": "def",
            "url": "https://example.com/2",
        },
    ]


def test_summarize_runs_counts_skipped_separately() -> None:
    summary = summarize_runs(_sample_runs())
    assert summary["run_count"] == 2
    assert summary["completed_success"] == 1
    assert summary["completed_skipped"] == 1
    assert summary["schedule_event_rows"] == 2
    assert any(
        "skipped" in c.lower() for c in summary["caveats"]
    ), "expected explicit skipped caveat"


def test_coerce_run_list_rejects_non_list() -> None:
    with pytest.raises(ValueError, match="array"):
        coerce_run_list({})


def test_coerce_run_list_rejects_non_object_elements() -> None:
    with pytest.raises(ValueError, match="index 0"):
        coerce_run_list([1])


def test_build_json_payload_has_contract_and_non_authorizing() -> None:
    runs = _sample_runs()
    summary = summarize_runs(runs)
    payload = build_json_payload(
        workflow="class-a-shadow-paper-scheduled-probe-v1.yml",
        runs=runs,
        summary=summary,
    )
    assert payload["contract"] == "class_a_spot_paper_snapshot_report_v0"
    assert payload["non_authorizing"] is True
    assert payload["read_only"] is True
    assert len(payload["runs"]) == 2


def test_render_markdown_includes_boundary_language() -> None:
    runs = _sample_runs()
    summary = summarize_runs(runs)
    md = render_markdown(
        workflow="class-a-shadow-paper-scheduled-probe-v1.yml",
        runs=runs,
        summary=summary,
    )
    lowered = md.lower()
    assert "infrastructure-smoke" in lowered
    assert "not futures" in lowered or "futures" in md.lower()
    assert "251" not in md  # no hard-coded real run ids in fixture


def test_cli_stdin_json_markdown_rc0() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--stdin-json"],
        input=json.dumps(_sample_runs()),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "Class-A Spot/Paper" in proc.stdout
    assert proc.stderr == ""


def test_cli_stdin_json_emit_json() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--stdin-json", "--json"],
        input=json.dumps(_sample_runs()),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["summary"]["completed_skipped"] == 1


def test_cli_input_file(tmp_path: Path) -> None:
    p = tmp_path / "runs.json"
    p.write_text(json.dumps(_sample_runs()), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--input-file", str(p), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["summary"]["run_count"] == 2


def test_fetch_runs_via_gh_parses_stdout() -> None:
    with patch.object(subprocess, "run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(_sample_runs()),
            stderr="",
        )
        runs = fetch_runs_via_gh(
            workflow="class-a-shadow-paper-scheduled-probe-v1.yml",
            limit=5,
        )
    assert len(runs) == 2
    assert m.call_args is not None
    cmd = m.call_args[0][0]
    assert cmd[0] == "gh"
    assert "--limit" in cmd
    assert "5" in cmd


def test_fetch_runs_via_gh_nonzero_raises() -> None:
    with patch.object(subprocess, "run") as m:
        m.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="auth failed",
        )
        with pytest.raises(RuntimeError, match="gh run list failed"):
            fetch_runs_via_gh(workflow="wf.yml", limit=1)