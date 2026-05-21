"""Tests for readiness gate snapshot v0."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "report_readiness_gate_snapshot_v0.py"
FIXTURES = ROOT / "tests" / "fixtures" / "ops" / "readiness_gate_snapshot_v0"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

GATE_PASS = "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE"
GATE_FAIL = "READINESS_GATE_SNAPSHOT_FAIL_CLOSED"
GATE_REVIEW = "READINESS_GATE_SNAPSHOT_REVIEW_REQUIRED"

LEDGER_PASS = "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"
LEDGER_FAIL = "READINESS_EVIDENCE_LEDGER_FAIL_CLOSED"
LEDGER_REVIEW = "READINESS_EVIDENCE_LEDGER_REVIEW_REQUIRED"

MIRROR_PASS = "READINESS_LEDGER_PREFLIGHT_MIRROR_PASS_BLOCKED_SAFE"
MIRROR_FAIL = "READINESS_LEDGER_PREFLIGHT_MIRROR_FAIL_CLOSED"


def _load_module():
    spec = importlib.util.spec_from_file_location("report_readiness_gate_snapshot_v0", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["report_readiness_gate_snapshot_v0"] = mod
    spec.loader.exec_module(mod)
    return mod


def _safe_ledger(**overrides: object) -> dict:
    base = {
        "schema": "peak_trade.readiness_evidence_ledger.v0",
        "verdict": LEDGER_PASS,
        "evidence": {"triple_lane_primary_evidence": True},
        "planning": {"planning_chain_present": True},
        "governance": {
            "governance_blocked": True,
            "live_allowed": False,
            "broker_exchange_allowed": False,
            "secret_values_included": False,
            "go_decision_granted": False,
            "preflight_ready": False,
            "hold_no_paper_run_cleared": False,
            "glb_014_cleared": False,
            "glb_015_cleared": False,
        },
        "blockers": ["PREFLIGHT_BLOCKED"],
        "issues": [],
    }
    if "governance" in overrides and isinstance(overrides["governance"], dict):
        base["governance"].update(overrides.pop("governance"))  # type: ignore[arg-type]
    base.update(overrides)
    return base


def _safe_preflight(**overrides: object) -> dict:
    base = {
        "status": "BLOCKED",
        "activation_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "dry_activation_readiness": {"ready": False},
        "hold_context_v0": {
            "current_state": "HOLD_NO_PAPER_RUN",
            "go_live_next_step": "blocked",
        },
        "blockers": [],
    }
    base.update(overrides)
    return base


def _safe_mirror(**overrides: object) -> dict:
    base = {
        "schema": "peak_trade.readiness_ledger_preflight_mirror.v0",
        "verdict": MIRROR_PASS,
        "mirror": {
            "mirror_check_pass": True,
            "ledger_pass_blocked_safe": True,
            "preflight_blocked": True,
            "authorization_flags_false": True,
            "governance_blocked_consistent": True,
        },
        "blockers": ["PREFLIGHT_BLOCKED"],
        "issues": [],
    }
    base.update(overrides)
    return base


@pytest.fixture
def mod():
    return _load_module()


def test_complete_safe_fixture_pass_blocked_safe(mod, monkeypatch) -> None:
    ledger = _safe_ledger()
    preflight = _safe_preflight()
    mirror = _safe_mirror()

    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: ledger,
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: preflight,
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: mirror,
    )

    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        fixed_generated_at_utc="2026-05-21T00:00:00Z",
    )
    assert payload["verdict"] == GATE_PASS
    assert payload["ledger"]["verdict"] == LEDGER_PASS
    assert payload["mirror"]["verdict"] == MIRROR_PASS
    assert payload["preflight"]["status"] == "BLOCKED"
    assert payload["governance"]["governance_blocked"] is True
    assert payload["governance"]["live_allowed"] is False
    assert len(payload["issues"]) == 0


def test_ledger_fail_closed_propagates(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(verdict=LEDGER_FAIL),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(verdict=MIRROR_FAIL),
    )

    assert mod.build_readiness_gate_snapshot(Path("/tmp/archive"))["verdict"] == GATE_FAIL


def test_mirror_fail_closed_propagates(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(verdict=MIRROR_FAIL),
    )

    assert mod.build_readiness_gate_snapshot(Path("/tmp/archive"))["verdict"] == GATE_FAIL


def test_preflight_ready_fail_closed(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(status="READY"),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )

    assert mod.build_readiness_gate_snapshot(Path("/tmp/archive"))["verdict"] == GATE_FAIL


def test_live_allowed_fail_closed(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(governance={"live_allowed": True}),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )

    assert mod.build_readiness_gate_snapshot(Path("/tmp/archive"))["verdict"] == GATE_FAIL


def test_secret_values_fail_closed(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(governance={"secret_values_included": True}),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )

    assert mod.build_readiness_gate_snapshot(Path("/tmp/archive"))["verdict"] == GATE_FAIL


def test_missing_archive_root_review_required(mod, tmp_path: Path) -> None:
    missing = tmp_path / "missing_archive"
    payload = mod.build_readiness_gate_snapshot(missing)
    assert payload["verdict"] == GATE_REVIEW
    assert payload["ledger"]["verdict"] == LEDGER_REVIEW


def test_cli_json_prints_json_only(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(tmp_path / "missing"),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stderr.strip() == ""
    payload = json.loads(proc.stdout)
    assert payload["schema"] == "peak_trade.readiness_gate_snapshot.v0"
    assert payload["generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_deterministic_timestamp_via_env(mod, monkeypatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-05-21T12:00:00Z")
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )
    payload = mod.build_readiness_gate_snapshot(Path("/tmp/archive"))
    assert payload["generated_at_utc"] == "2026-05-21T12:00:00Z"


def test_schema_stable(mod, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: _safe_ledger(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )
    payload = mod.build_readiness_gate_snapshot(Path("/tmp/archive"))
    assert set(payload) == {
        "schema",
        "generated_at_utc",
        "archive_root",
        "ledger",
        "preflight",
        "mirror",
        "governance",
        "blockers",
        "verdict",
        "issues",
    }


def test_no_subprocess_or_network_in_module_source() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "urllib" not in source
    assert "requests" not in source
    assert "socket" not in source


def test_fixtures_dir_exists() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    assert FIXTURES.is_dir()


@pytest.mark.skipif(not ARCHIVE_ROOT.is_dir(), reason="operator archive not present")
def test_real_smoke_pass_blocked_safe() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(ARCHIVE_ROOT),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == GATE_PASS
    assert payload["ledger"]["issues_count"] == 0
    assert payload["mirror"]["issues_count"] == 0
