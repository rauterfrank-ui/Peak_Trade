"""Tests for scripts/ops/check_bounded_pilot_readiness.py — canonical bounded-pilot preflight."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = ROOT / "scripts" / "ops" / "check_bounded_pilot_readiness.py"


def test_script_exists() -> None:
    assert SCRIPT.is_file()


def _passing_readiness_report() -> object:
    from scripts.check_live_readiness import CheckResult, ReadinessReport

    return ReadinessReport(
        stage="live",
        checks=[CheckResult("stub", True, "ok")],
        warnings=[],
    )


def test_run_bounded_pilot_readiness_green(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {"repo_root": str(ROOT)},
    )

    def _go(payload: dict) -> dict:
        return {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [{"row": 1, "area": "Safety Gates", "status": "PASS"}],
        }

    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        _go,
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is True
    assert bundle["contract"] == mod.CONTRACT_ID
    assert bundle["go_no_go"]["verdict"] == "GO_FOR_NEXT_PHASE_ONLY"
    assert bundle["live_readiness"]["all_passed"] is True


def test_run_bounded_pilot_readiness_blocks_on_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod
    from scripts.check_live_readiness import CheckResult, ReadinessReport

    bad = ReadinessReport(
        stage="live",
        checks=[
            CheckResult("API-Credentials", False, "Live-API-Keys fehlen"),
        ],
        warnings=[],
    )
    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: bad,
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["blocked_at"] == "live_readiness"
    assert "go_no_go" not in bundle


def test_run_bounded_pilot_readiness_blocks_on_go_no_go(monkeypatch: pytest.MonkeyPatch) -> None:
    import scripts.ops.check_bounded_pilot_readiness as mod

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "NO_GO",
            "rows": [{"row": 6, "area": "Treasury Separation", "status": "FAIL"}],
        },
    )

    ok, bundle = mod.run_bounded_pilot_readiness(
        ROOT, ROOT / "config" / "config.toml", run_tests=False
    )
    assert ok is False
    assert bundle["blocked_at"] == "go_no_go"
    assert bundle["go_no_go"]["verdict"] == "NO_GO"


def test_main_json_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_bounded_pilot_readiness", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    monkeypatch.setattr(
        "scripts.check_live_readiness.run_readiness_checks",
        lambda **kw: _passing_readiness_report(),
    )
    monkeypatch.setattr(
        "src.webui.ops_cockpit.build_ops_cockpit_payload",
        lambda **kw: {},
    )
    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "GO_FOR_NEXT_PHASE_ONLY",
            "rows": [],
        },
    )

    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(ROOT)])
    assert mod.main() == 0
    out = capsys.readouterr().out
    data = json.loads(out.strip())
    assert data["ok"] is True

    monkeypatch.setattr(
        "scripts.ops.pilot_go_no_go_eval_v1.evaluate",
        lambda payload: {
            "contract": "pilot_go_no_go_eval_v1",
            "verdict": "CONDITIONAL",
            "rows": [{"row": 1, "area": "Safety Gates", "status": "UNKNOWN"}],
        },
    )
    monkeypatch.setattr(sys, "argv", ["x", "--json", "--repo-root", str(ROOT)])
    assert mod.main() == 1
