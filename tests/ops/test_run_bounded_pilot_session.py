"""Tests for scripts/ops/run_bounded_pilot_session.py — Bounded Pilot Entry Gate."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "run_bounded_pilot_session.py"


def _load_session_module():
    spec = importlib.util.spec_from_file_location("run_bounded_pilot_session", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _green_readiness_bundle() -> dict:
    return {
        "contract": "bounded_pilot_readiness_v1",
        "ok": True,
        "blocked_at": None,
        "message": "ok",
        "go_no_go": {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    }


def _green_operator_packet() -> dict:
    return {
        "contract": "bounded_pilot_operator_preflight_packet_v1",
        "summary": {
            "readiness_ok": True,
            "stop_snapshot_ok": True,
            "packet_ok": True,
            "blocked": [],
            "notes": [],
        },
    }


def test_script_exists() -> None:
    """Script file exists."""
    assert SCRIPT.is_file()


def test_script_runs_with_repo_root() -> None:
    """Script runs with --repo-root and produces output."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--no-invoke"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1, 2), f"stderr: {r.stderr}"
    assert (
        "Bounded pilot" in r.stdout
        or "GATES_RED" in r.stderr
        or "entry_permitted" in r.stdout
        or "Gates GREEN" in r.stdout
        or "operator preflight packet GREEN" in r.stdout
    )


def test_script_json_output() -> None:
    """Script --json produces valid JSON with contract and entry_permitted."""
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(ROOT), "--json", "--no-invoke"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert r.returncode in (0, 1)
    data = json.loads(r.stdout)
    assert data["contract"] == "run_bounded_pilot_session"
    assert "entry_permitted" in data
    assert "verdict" in data
    assert "bounded_pilot_readiness" in data
    br = data["bounded_pilot_readiness"]
    assert br.get("contract") == "bounded_pilot_readiness_v1"
    if data["entry_permitted"]:
        assert data["go_no_go"]["contract"] == "pilot_go_no_go_eval_v1"
        assert "operator_preflight_packet" in data
        assert data["operator_preflight_packet"].get("contract") == (
            "bounded_pilot_operator_preflight_packet_v1"
        )
    else:
        assert data.get("blocked_at") == br.get("blocked_at")
        if br.get("go_no_go"):
            assert br["go_no_go"]["contract"] == "pilot_go_no_go_eval_v1"


def test_main_importable() -> None:
    """main() can be imported and returns int."""
    mod = _load_session_module()
    assert hasattr(mod, "main")
    assert callable(mod.main)


def test_no_invoke_returns_0_when_operator_preflight_packet_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )
    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: (_green_operator_packet(), 0),
    )

    def _no_subprocess(*a, **k):
        raise AssertionError("subprocess.run must not be called for --no-invoke")

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_bounded_pilot_session", "--repo-root", str(ROOT), "--no-invoke"],
    )
    assert mod.main() == 0


def test_no_invoke_returns_1_when_operator_preflight_packet_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )

    def _bad(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "readiness_ok": True,
                    "stop_snapshot_ok": False,
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot.kill_switch_file: error (bad)"],
                    "notes": [],
                },
            },
            1,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _bad,
    )

    def _no_sub(*a, **k):
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(subprocess, "run", _no_sub)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_bounded_pilot_session", "--repo-root", str(ROOT), "--no-invoke"],
    )
    assert mod.main() == 1


def test_no_invoke_returns_2_when_operator_preflight_orchestrator_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )

    def _broken(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {"packet_ok": False, "blocked": ["x"]},
            },
            2,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _broken,
    )

    def _no_sub(*a, **k):
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(subprocess, "run", _no_sub)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_bounded_pilot_session", "--repo-root", str(ROOT), "--no-invoke"],
    )
    assert mod.main() == 2


def test_no_invoke_json_includes_operator_preflight_packet_when_ok(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )
    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: (_green_operator_packet(), 0),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_bounded_pilot_session",
            "--repo-root",
            str(ROOT),
            "--json",
            "--no-invoke",
        ],
    )
    assert mod.main() == 0
    data = json.loads(capsys.readouterr().out.strip())
    assert data["entry_permitted"] is True
    assert data["operator_preflight_packet"]["summary"]["packet_ok"] is True


def test_invoke_skips_subprocess_when_operator_preflight_packet_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )

    def _bad_packet(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "readiness_ok": True,
                    "stop_snapshot_ok": False,
                    "packet_ok": False,
                    "blocked": [
                        "stop_signal_snapshot.kill_switch_file: error (invalid json)",
                    ],
                    "notes": [],
                },
            },
            1,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _bad_packet,
    )

    def _no_subprocess(*a, **k):
        raise AssertionError("subprocess.run must not be called when packet blocks")

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    monkeypatch.setattr(sys, "argv", ["run_bounded_pilot_session", "--repo-root", str(ROOT)])
    assert mod.main() == 1


def test_invoke_runs_subprocess_when_operator_preflight_packet_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )
    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: (_green_operator_packet(), 0),
    )
    calls: list = []

    def _fake_run(*a, **k):
        calls.append(1)
        return subprocess.CompletedProcess(args=a[0] if a else [], returncode=0)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["run_bounded_pilot_session", "--repo-root", str(ROOT)])
    assert mod.main() == 0
    assert calls == [1]


def test_invoke_returns_2_when_operator_preflight_packet_orchestrator_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )

    def _broken_packet(*a, **k):
        return (
            {
                "contract": "bounded_pilot_operator_preflight_packet_v1",
                "summary": {
                    "readiness_ok": True,
                    "stop_snapshot_ok": False,
                    "packet_ok": False,
                    "blocked": ["stop_signal_snapshot: exception (boom)"],
                    "notes": [],
                },
                "stop_signal_snapshot": {"orchestrator_error": "boom"},
            },
            2,
        )

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        _broken_packet,
    )

    def _no_subprocess(*a, **k):
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    monkeypatch.setattr(sys, "argv", ["run_bounded_pilot_session", "--repo-root", str(ROOT)])
    assert mod.main() == 2


def test_invoke_json_shows_operator_preflight_packet_when_blocked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    mod = _load_session_module()
    monkeypatch.setattr(
        "scripts.ops.check_bounded_pilot_readiness.run_bounded_pilot_readiness",
        lambda *a, **k: (True, _green_readiness_bundle()),
    )
    bad = {
        "contract": "bounded_pilot_operator_preflight_packet_v1",
        "summary": {
            "readiness_ok": True,
            "stop_snapshot_ok": False,
            "packet_ok": False,
            "blocked": ["stop_signal_snapshot.incident_stop_artifact: error (e)"],
            "notes": [],
        },
    }

    monkeypatch.setattr(
        "scripts.ops.bounded_pilot_operator_preflight_packet.build_operator_preflight_packet",
        lambda *a, **k: (bad, 1),
    )

    def _no_subprocess(*a, **k):
        raise AssertionError("subprocess.run must not be called")

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_bounded_pilot_session", "--repo-root", str(ROOT), "--json"],
    )
    assert mod.main() == 1
    data = json.loads(capsys.readouterr().out.strip())
    assert data["entry_permitted"] is False
    assert data["blocked_at"] == "operator_preflight_packet"
    blocked_txt = " ".join(data["operator_preflight_packet"]["summary"]["blocked"])
    assert "incident_stop_artifact" in blocked_txt
