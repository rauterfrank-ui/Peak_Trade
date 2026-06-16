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

REGISTRY_PASS = "GENERIC_EVIDENCE_RUN_REGISTRY_PASS_BLOCKED_SAFE"
REGISTRY_REVIEW = "GENERIC_EVIDENCE_RUN_REGISTRY_REVIEW_REQUIRED"
REGISTRY_FAIL = "GENERIC_EVIDENCE_RUN_REGISTRY_FAIL_CLOSED"


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


def _safe_registry(**overrides: object) -> dict:
    base = {
        "schema": "peak_trade.generic_evidence_run_registry.v1",
        "verdict": REGISTRY_PASS,
        "summaries": {
            "total_runs": 3,
            "verified_runs": 3,
            "runs_by_lane": {"paper": 1, "shadow": 1, "testnet": 1},
            "scheduler_boundary_gap_acknowledged": True,
            "live_authority_present": False,
            "broker_exchange_authority_present": False,
        },
        "authority": {
            "live_allowed": False,
            "broker_exchange_allowed": False,
            "secret_values_included": False,
        },
        "blockers": ["LIVE_NOT_AUTHORIZED"],
        "issues": [],
    }
    if "summaries" in overrides and isinstance(overrides["summaries"], dict):
        base["summaries"].update(overrides.pop("summaries"))  # type: ignore[arg-type]
    if "authority" in overrides and isinstance(overrides["authority"], dict):
        base["authority"].update(overrides.pop("authority"))  # type: ignore[arg-type]
    base.update(overrides)
    return base


def _patch_safe_stack(monkeypatch, mod, *, registry: dict | None = None) -> None:
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
    if registry is not None:
        monkeypatch.setattr(
            "scripts.ops.build_generic_evidence_run_registry_v1.build_registry",
            lambda ctx: registry,
        )


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


def test_pass_blocked_safe_triple_lane_is_review_input_only_not_approval(mod, monkeypatch) -> None:
    """GLB-015 / §2a.1: gate snapshot PASS_BLOCKED_SAFE does not clear preflight or grant authority."""
    ledger = _safe_ledger(
        evidence={"triple_lane_primary_evidence": True},
        governance={
            "governance_blocked": True,
            "live_allowed": False,
            "broker_exchange_allowed": False,
            "preflight_ready": False,
            "glb_015_cleared": False,
            "go_decision_granted": False,
            "hold_no_paper_run_cleared": False,
        },
        blockers=["PREFLIGHT_BLOCKED", "HOLD_NO_PAPER_RUN_NOT_CLEARED"],
    )
    monkeypatch.setattr(
        "scripts.ops.build_readiness_evidence_ledger_v0.build_ledger",
        lambda ctx: ledger,
    )
    monkeypatch.setattr(
        "scripts.ops.report_paper_shadow_247_preflight_status.build_paper_shadow_247_preflight_status",
        lambda **kwargs: _safe_preflight(status="BLOCKED", activation_authorized=False),
    )
    monkeypatch.setattr(
        "scripts.ops.report_readiness_ledger_preflight_mirror_v0.build_mirror_from_payloads",
        lambda *a, **k: _safe_mirror(),
    )

    payload = mod.build_readiness_gate_snapshot(Path("/tmp/archive"))
    assert payload["verdict"] == GATE_PASS
    assert payload["ledger"]["triple_lane_primary_evidence"] is True
    assert payload["preflight"]["status"] == "BLOCKED"
    assert payload["preflight"]["activation_authorized"] is False
    assert payload["governance"]["governance_blocked"] is True
    assert payload["governance"]["preflight_ready"] is False
    assert payload["governance"]["hold_no_paper_run_cleared"] is False
    assert "PREFLIGHT_BLOCKED" in payload["blockers"]
    assert "HOLD_NO_PAPER_RUN_NOT_CLEARED" in payload["blockers"]


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
    assert "registry" not in payload


def test_default_output_has_no_registry_key(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod)
    payload = mod.build_readiness_gate_snapshot(Path("/tmp/archive"))
    assert "registry" not in payload


def test_include_registry_adds_summary_section(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry())
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    reg = payload["registry"]
    assert reg["included"] is True
    assert reg["schema"] == "peak_trade.generic_evidence_run_registry.v1"
    assert reg["total_runs"] == 3
    assert reg["verified_runs"] == 3
    assert reg["runs_by_lane"] == {"paper": 1, "shadow": 1, "testnet": 1}


def test_registry_non_authorizing_flag(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry())
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["registry"]["non_authorizing"] is True


def test_registry_pass_does_not_change_gate_verdict(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry())
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_PASS


def test_registry_review_required_escalates_gate_from_pass(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry(verdict=REGISTRY_REVIEW))
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_REVIEW


def test_registry_fail_closed_escalates_gate(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry(verdict=REGISTRY_FAIL))
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_FAIL


def test_registry_live_authority_present_fail_closed(mod, monkeypatch) -> None:
    _patch_safe_stack(
        monkeypatch,
        mod,
        registry=_safe_registry(
            summaries={"live_authority_present": True},
        ),
    )
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_FAIL
    assert any(
        i.get("code") == "REGISTRY_SECTION_UNSAFE_AUTHORITY_SIGNAL" for i in payload["issues"]
    )


def test_registry_broker_exchange_authority_present_fail_closed(mod, monkeypatch) -> None:
    _patch_safe_stack(
        monkeypatch,
        mod,
        registry=_safe_registry(
            summaries={"broker_exchange_authority_present": True},
        ),
    )
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_FAIL


def test_registry_build_failure_review_required(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod)

    def _boom(ctx):
        raise RuntimeError("registry build failed")

    monkeypatch.setattr(
        "scripts.ops.build_generic_evidence_run_registry_v1.build_registry",
        _boom,
    )
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
    assert payload["verdict"] == GATE_REVIEW
    assert payload["registry"]["included"] is False
    assert any(i.get("code") == "REGISTRY_SECTION_BUILD_FAILED" for i in payload["issues"])


def test_include_registry_schema_stable(mod, monkeypatch) -> None:
    _patch_safe_stack(monkeypatch, mod, registry=_safe_registry())
    payload = mod.build_readiness_gate_snapshot(
        Path("/tmp/archive"),
        include_registry=True,
    )
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
        "registry",
    }


def test_cli_include_registry_json_prints_json_only(tmp_path: Path) -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(tmp_path / "missing"),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--include-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stderr.strip() == ""
    payload = json.loads(proc.stdout)
    assert "registry" in payload


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
    assert "registry" not in payload


@pytest.mark.skipif(not ARCHIVE_ROOT.is_dir(), reason="operator archive not present")
def test_real_smoke_include_registry_pass_blocked_safe() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--archive-root",
            str(ARCHIVE_ROOT),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--include-registry",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == GATE_PASS
    assert payload["registry"]["included"] is True
    assert payload["registry"]["non_authorizing"] is True
    assert payload["registry"]["verdict"] == REGISTRY_PASS
    assert payload["governance"]["live_allowed"] is False
    assert payload["governance"]["broker_exchange_allowed"] is False
    assert payload["governance"]["secret_values_included"] is False
    assert payload["registry"]["issues_count"] == 0
