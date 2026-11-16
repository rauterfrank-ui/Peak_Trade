import json
import subprocess
import sys
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
