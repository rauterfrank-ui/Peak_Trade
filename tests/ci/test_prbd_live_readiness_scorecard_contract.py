import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest

from scripts.ci.stability_gate import PRJ_WORKFLOW, read_scheduled_prj_age


def _stability_and_report(
    prj_age: int,
    scheduled_age: int | None,
) -> tuple[dict, dict]:
    now = datetime.now(timezone.utc)
    generated = now - timedelta(hours=2) if scheduled_age == 37 else now
    receipt = {
        "overall_ok": True,
        "branch": "main",
        "generated_at": generated.isoformat(),
        "evidence_scope": "ON_DEMAND",
        "prk_report_prj_run_id": 2,
        "results": [
            {
                "name": name,
                "run_id": run_id,
                "event": "workflow_dispatch",
                "ok": True,
                "created_at": (generated - timedelta(hours=age)).isoformat(),
                "age_hours": 1,
            }
            for name, run_id, age in (("PR-K", 1, 1), ("PR-J", 2, prj_age))
        ],
    }
    report = {}
    if scheduled_age is not None:
        created_at = (now - timedelta(hours=scheduled_age, minutes=1)).isoformat()
        row = {
            "id": 3,
            "event": "schedule",
            "status": "completed",
            "conclusion": "success",
            "created_at": created_at,
        }
        receipt["scheduled_prj"] = {
            "workflow": PRJ_WORKFLOW,
            "run_id": 3,
            "event": "schedule",
            "created_at": created_at,
        }
        report = {"runs": [row], "latest_schedule_success": row}
    return receipt, report


def _write_inputs(tmp_path: Path, receipt: dict, report: dict, health: dict, wrong_report=False):
    status_bytes = json.dumps(report).encode()
    health_bytes = json.dumps(health).encode()
    receipt["prk_report_sha256"] = {
        "prj_status_latest.json": sha256(status_bytes).hexdigest(),
        "prj_health_summary.json": "0" * 64 if wrong_report else sha256(health_bytes).hexdigest(),
    }
    (tmp_path / "st.json").write_bytes(status_bytes)
    (tmp_path / "h.json").write_bytes(health_bytes)
    (tmp_path / "s.json").write_text(json.dumps(receipt), encoding="utf-8")


def test_prbd_workflow_accepts_prk_schedule_or_dispatch_events() -> None:
    """PRK/PRBD Option2 B1: PRBD must not filter PRK runs to schedule-only."""
    text = Path(".github/workflows/prbd-live-readiness-scorecard.yml").read_text(encoding="utf-8")
    assert "prk-prj-status-report.yml" in text
    assert '.event=="schedule" or .event=="workflow_dispatch"' in text
    assert 'and .event=="schedule")' not in text


@pytest.mark.parametrize(
    ("age", "scheduled_age", "policy", "wrong_report", "hard_blocks"),
    [
        (1, 2, "", False, []),
        (37, 2, "", False, ["STABILITY_GATE_STALE"]),
        (1, 2, "NO_TRADE", False, ["PRK_NO_TRADE"]),
        (1, 2, "", True, ["PRK_REPORT_BINDING_MISMATCH"]),
        (1, None, "", False, ["MISSING_VERIFIED_SCHEDULED_PRJ"]),
        (1, 37, "", False, ["SCHEDULED_PRJ_STALE"]),
    ],
)
def test_readiness_checks_original_age_and_report_policy(
    tmp_path: Path, age, scheduled_age, policy, wrong_report, hard_blocks
):
    stab, report = _stability_and_report(age, scheduled_age)
    _write_inputs(tmp_path, stab, report, {"status": "OK", "policy_action": policy}, wrong_report)
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/live_readiness_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "s.json"),
            "--status",
            str(tmp_path / "st.json"),
            "--health",
            str(tmp_path / "h.json"),
            "--go-threshold",
            "85",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == (2 if hard_blocks else 0)
    obj = json.loads((out / "live_readiness_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == ("NO_GO" if hard_blocks else "GO")
    assert obj["hard_blocks"] == hard_blocks
    assert obj["scheduled_prj"] == (None if hard_blocks else stab["scheduled_prj"])


def test_no_go_on_stability_fail(tmp_path: Path):
    stab = {"overall_ok": False, "results": []}
    st = {"dummy": True}
    hs = {"status": "OK"}
    (tmp_path / "s.json").write_text(json.dumps(stab), encoding="utf-8")
    (tmp_path / "st.json").write_text(json.dumps(st), encoding="utf-8")
    (tmp_path / "h.json").write_text(json.dumps(hs), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/live_readiness_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "s.json"),
            "--status",
            str(tmp_path / "st.json"),
            "--health",
            str(tmp_path / "h.json"),
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2


def test_no_go_on_soft_penalties_only(tmp_path: Path):
    stab, report = _stability_and_report(1, 13)
    _write_inputs(tmp_path, stab, report, {"status": "STALE"})
    out = tmp_path / "out"
    out.mkdir()
    r = subprocess.run(
        [
            sys.executable,
            "scripts/ci/live_readiness_scorecard.py",
            "--out-dir",
            str(out),
            "--stability",
            str(tmp_path / "s.json"),
            "--status",
            str(tmp_path / "st.json"),
            "--health",
            str(tmp_path / "h.json"),
            "--go-threshold",
            "85",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 2
    obj = json.loads((out / "live_readiness_scorecard.json").read_text(encoding="utf-8"))
    assert obj["score"] == 75
    assert obj["decision"] == "NO_GO"
    assert obj["hard_blocks"] == []
    assert set(obj["warnings"]) == {"PRJ_AGE_GT_12H", "HEALTH_STALE"}


def test_source_binding_and_expiry_use_the_scheduled_timestamp():
    receipt, report = _stability_and_report(1, 2)
    source_time = datetime.fromisoformat(receipt["scheduled_prj"]["created_at"])
    expires_at = source_time + timedelta(hours=36)
    assert read_scheduled_prj_age(receipt, report, now=expires_at) == 36
    assert (
        read_scheduled_prj_age(
            receipt,
            report,
            now=expires_at + timedelta(microseconds=1),
        )
        == "SCHEDULED_PRJ_STALE"
    )
    receipt["scheduled_prj"]["run_id"] = 2
    assert (
        read_scheduled_prj_age(
            receipt,
            report,
            now=expires_at,
        )
        == "SCHEDULED_PRJ_BINDING_MISMATCH"
    )
