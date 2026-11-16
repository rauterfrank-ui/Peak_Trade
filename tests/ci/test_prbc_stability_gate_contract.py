import json
import subprocess
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.ci import stability_gate


@pytest.mark.parametrize(
    ("event", "source_id", "mock_step", "reason", "scope"),
    [
        ("schedule", 2, "skipped", "OK", "SCHEDULED"),
        ("workflow_dispatch", 2, "skipped", "OK", "ON_DEMAND"),
        ("workflow_dispatch", 3, "skipped", "PRJ_REPORT_SOURCE_MISMATCH", None),
        ("workflow_dispatch", 2, "success", "MISSING_VERIFIED_WORKFLOW_EVIDENCE", None),
    ],
)
def test_gate_binds_verified_prj_and_prk(
    tmp_path: Path, event, source_id, mock_step, reason, scope
):
    prj_created = "2026-02-24T10:00:00Z"
    prk = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-24T11:00:00Z",
            "event": event,
            "evidence": {
                "report_sha256": {
                    "prj_status_latest.json": "1" * 64,
                    "prj_health_summary.json": "2" * 64,
                },
                "steps": {
                    "Build mock runs JSON": mock_step,
                    "Fetch last 50 PR-J runs (GitHub API)": "success",
                    "Upload report artifact": "success",
                },
                "report": {
                    "runs": [
                        {
                            "id": source_id,
                            "event": event,
                            "status": "completed",
                            "conclusion": "success",
                            "created_at": prj_created,
                        }
                    ]
                },
            },
        }
    ]
    prj = [
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "success",
            "createdAt": prj_created,
            "event": event,
            "evidence": {
                "steps": {
                    "Run PR-J smoke + evidence": "success",
                    "Upload PR-J smoke artifacts": "success",
                }
            },
        }
    ]
    report = prk[0]["evidence"]["report"]
    if event == "schedule":
        report["latest_schedule_success"] = report["runs"][0]
    prk_path = tmp_path / "prk.json"
    prj_path = tmp_path / "prj.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    prk_path.write_text(json.dumps(prk), encoding="utf-8")
    prj_path.write_text(json.dumps(prj), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/stability_gate.py",
            "--out-dir",
            str(outdir),
            "--now",
            "2026-02-24T12:00:00Z",
            "--prk-runs-json",
            str(prk_path),
            "--prj-runs-json",
            str(prj_path),
            "--max-age-hours-prk",
            "36",
            "--max-age-hours-prj",
            "36",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == (0 if scope else 2), r.stderr
    obj = json.loads((outdir / "stability_gate.json").read_text(encoding="utf-8"))
    assert obj["overall_ok"] is bool(scope)
    assert obj["evidence_scope"] == scope
    assert obj["results"][0]["event"] == event
    assert obj["results"][0]["reason"] == reason
    assert obj["prk_report_prj_run_id"] == (2 if scope else None)
    if scope == "SCHEDULED":
        assert obj["scheduled_prj"]["run_id"] == 2
    else:
        assert obj["scheduled_prj"] is None


@pytest.mark.parametrize(
    ("changes", "accepted"),
    [
        ({}, True),
        ({"evidence": {"steps": {}}}, False),
        ({"event": "workflow_dispatch"}, False),
        ({"createdAt": "2026-02-24T09:01:00Z"}, False),
        ({"databaseId": 4}, False),
    ],
)
def test_gate_verifies_the_separate_schedule_source_named_by_prk(changes, accepted):
    now = datetime(2026, 2, 24, 12, tzinfo=timezone.utc)
    planned = {
        "id": 3,
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "created_at": "2026-02-24T09:00:00Z",
    }
    prj = stability_gate.GateResult(
        "PR-J",
        stability_gate.PRJ_WORKFLOW,
        2,
        "2026-02-24T10:00:00Z",
        2.0,
        True,
        "OK",
        "workflow_dispatch",
    )
    prk = stability_gate.GateResult(
        "PR-K",
        stability_gate.PRK_WORKFLOW,
        1,
        "2026-02-24T11:00:00Z",
        1.0,
        True,
        "OK",
        "workflow_dispatch",
        scheduled_prj_source=stability_gate._reported_scheduled_prj(
            {
                "latest_schedule_success": planned,
                "runs": [planned],
            }
        ),
    )
    source = {
        "databaseId": planned["id"],
        "event": "schedule",
        "status": "completed",
        "conclusion": "success",
        "createdAt": planned["created_at"],
        "evidence": {
            "steps": {
                "Run PR-J smoke + evidence": "success",
                "Upload PR-J smoke artifacts": "success",
            }
        },
    }
    proof = stability_gate._bind_scheduled_prj(
        prj,
        prk,
        branch="main",
        now=now,
        limit=60,
        max_age_h=36,
        runs_override=[source | changes, source | {"databaseId": 5}],
    )
    assert proof == (
        {
            "workflow": stability_gate.PRJ_WORKFLOW,
            "run_id": 3,
            "event": "schedule",
            "created_at": planned["created_at"],
        }
        if accepted
        else None
    )


def test_gate_stale(tmp_path: Path):
    prk = [
        {
            "databaseId": 1,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-20T00:00:00Z",
            "event": "schedule",
        }
    ]
    prj = [
        {
            "databaseId": 2,
            "status": "completed",
            "conclusion": "success",
            "createdAt": "2026-02-24T11:00:00Z",
            "event": "schedule",
        }
    ]
    prk_path = tmp_path / "prk.json"
    prj_path = tmp_path / "prj.json"
    outdir = tmp_path / "out"
    outdir.mkdir()
    prk_path.write_text(json.dumps(prk), encoding="utf-8")
    prj_path.write_text(json.dumps(prj), encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/stability_gate.py",
            "--out-dir",
            str(outdir),
            "--now",
            "2026-02-24T12:00:00Z",
            "--prk-runs-json",
            str(prk_path),
            "--prj-runs-json",
            str(prj_path),
            "--max-age-hours-prk",
            "36",
            "--max-age-hours-prj",
            "36",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((outdir / "stability_gate.json").read_text(encoding="utf-8"))
    assert obj["overall_ok"] is False
    assert obj["results"][0]["reason"] == "STALE_SUCCESS"


def test_bound_report_read_from_github_artifact(monkeypatch):
    report_files = {
        "prj_status_latest.json": b'{"runs":[]}',
        "prj_health_summary.json": b'{"status":"NO_SUCCESS"}',
    }
    report_steps = {
        "Build mock runs JSON": "skipped",
        "Fetch last 50 PR-J runs (GitHub API)": "success",
        "Upload report artifact": "success",
    }

    def github_response(command, *, text):
        assert text
        route = command[-1]
        if route.endswith("/jobs?filter=latest"):
            return json.dumps(
                {
                    "jobs": [
                        {
                            "name": "prj-status-report",
                            "conclusion": "success",
                            "steps": [
                                {"name": name, "conclusion": value}
                                for name, value in report_steps.items()
                            ],
                        }
                    ]
                }
            )
        assert route.endswith("/artifacts")
        return json.dumps({"artifacts": [{"name": "prj-status-report", "expired": False}]})

    def download_report(command, *, check):
        assert check
        assert command[:-1] == [
            "gh",
            "run",
            "download",
            "123",
            "--name",
            "prj-status-report",
            "--dir",
        ]
        for name, contents in report_files.items():
            (Path(command[-1]) / name).write_bytes(contents)

    monkeypatch.setattr(stability_gate.subprocess, "check_output", github_response)
    monkeypatch.setattr(stability_gate.subprocess, "run", download_report)
    result = stability_gate._read_workflow_evidence("PR-K", 123)
    assert result["report"] == {"runs": []}
    assert result["report_sha256"] == {
        name: sha256(contents).hexdigest() for name, contents in report_files.items()
    }
