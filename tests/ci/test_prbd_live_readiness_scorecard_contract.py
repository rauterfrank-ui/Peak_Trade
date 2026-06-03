import json
import subprocess
import sys
from pathlib import Path


def test_prbd_workflow_accepts_prk_schedule_or_dispatch_events() -> None:
    """PRK/PRBD Option2 B1: PRBD must not filter PRK runs to schedule-only."""
    text = Path(".github/workflows/prbd-live-readiness-scorecard.yml").read_text(encoding="utf-8")
    assert "prk-prj-status-report.yml" in text
    assert '.event=="schedule" or .event=="workflow_dispatch"' in text
    assert 'and .event=="schedule")' not in text


def test_go(tmp_path: Path):
    stab = {
        "overall_ok": True,
        "results": [
            {"name": "PR-K", "age_hours": 1.0},
            {"name": "PR-J", "age_hours": 1.0},
        ],
    }
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
            "--go-threshold",
            "85",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    assert r.returncode == 0
    obj = json.loads((out / "live_readiness_scorecard.json").read_text(encoding="utf-8"))
    assert obj["decision"] == "GO"


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
