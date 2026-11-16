import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

import pytest


def _stability(prj_age: int) -> dict:
    generated = datetime.now(timezone.utc)
    return {
        "overall_ok": True,
        "generated_at": generated.isoformat(),
        "results": [
            {
                "name": name,
                "created_at": (generated - timedelta(hours=age)).isoformat(),
                "age_hours": 1,
            }
            for name, age in (("PR-K", 1), ("PR-J", prj_age))
        ],
    }


def test_prbd_workflow_accepts_prk_schedule_or_dispatch_events() -> None:
    """PRK/PRBD Option2 B1: PRBD must not filter PRK runs to schedule-only."""
    text = Path(".github/workflows/prbd-live-readiness-scorecard.yml").read_text(encoding="utf-8")
    assert "prk-prj-status-report.yml" in text
    assert '.event=="schedule" or .event=="workflow_dispatch"' in text
    assert 'and .event=="schedule")' not in text


@pytest.mark.parametrize(
    ("age", "policy", "wrong_report", "hard_blocks"),
    [
        (1, "", False, []),
        (37, "", False, ["STABILITY_GATE_STALE"]),
        (1, "NO_TRADE", False, ["PRK_NO_TRADE"]),
        (1, "", True, ["PRK_REPORT_BINDING_MISMATCH"]),
    ],
)
def test_readiness_checks_original_age_and_report_policy(
    tmp_path: Path, age, policy, wrong_report, hard_blocks
):
    stab = _stability(age)
    st = {"dummy": True}
    hs = {"status": "OK", "policy_action": policy}
    (tmp_path / "st.json").write_text(json.dumps(st), encoding="utf-8")
    health_bytes = json.dumps(hs).encode()
    (tmp_path / "h.json").write_bytes(health_bytes)
    stab.update(
        evidence_scope="ON_DEMAND",
        prk_report_prj_run_id=2,
        prk_report_sha256={
            "prj_status_latest.json": sha256((tmp_path / "st.json").read_bytes()).hexdigest(),
            "prj_health_summary.json": "0" * 64
            if wrong_report
            else sha256(health_bytes).hexdigest(),
        },
    )
    for run_id, row in enumerate(stab["results"], 1):
        row.update(run_id=run_id, event="workflow_dispatch", ok=True)
    (tmp_path / "s.json").write_text(json.dumps(stab), encoding="utf-8")
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
    stab = _stability(13)
    st = {"dummy": True}
    hs = {"status": "STALE"}
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
