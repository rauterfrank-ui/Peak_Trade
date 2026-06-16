"""Tests for readiness ledger / preflight mirror v0."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "report_readiness_ledger_preflight_mirror_v0.py"
FIXTURES = ROOT / "tests" / "fixtures" / "ops" / "readiness_ledger_preflight_mirror_v0"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

LEDGER_PASS = "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE"
MIRROR_PASS = "READINESS_LEDGER_PREFLIGHT_MIRROR_PASS_BLOCKED_SAFE"
MIRROR_FAIL = "READINESS_LEDGER_PREFLIGHT_MIRROR_FAIL_CLOSED"
MIRROR_REVIEW = "READINESS_LEDGER_PREFLIGHT_MIRROR_REVIEW_REQUIRED"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "report_readiness_ledger_preflight_mirror_v0", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["report_readiness_ledger_preflight_mirror_v0"] = mod
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
        "shadow_runtime_authorized": False,
        "scheduler_execution_authorized": False,
        "testnet_authorized": False,
        "live_authorized": False,
        "dry_activation_readiness": {"ready": False},
        "hold_context_v0": {
            "current_state": "HOLD_NO_PAPER_RUN",
            "go_live_next_step": "blocked",
            "progression_authorization": {
                "testnet_authorized": False,
                "live_authorized": False,
            },
        },
    }
    base.update(overrides)
    return base


def _write_pair(
    tmp_path: Path, ledger: dict | None, preflight: dict | str | None
) -> tuple[Path, Path]:
    ledger_path = tmp_path / "ledger.json"
    preflight_path = tmp_path / "preflight.json"
    if ledger is not None:
        ledger_path.write_text(json.dumps(ledger) + "\n", encoding="utf-8")
    if isinstance(preflight, str):
        preflight_path.write_text(preflight + "\n", encoding="utf-8")
    elif preflight is not None:
        preflight_path.write_text(json.dumps(preflight) + "\n", encoding="utf-8")
    return ledger_path, preflight_path


@pytest.fixture
def mod():
    return _load_module()


def test_complete_safe_fixture_pass_blocked_safe(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(tmp_path, _safe_ledger(), _safe_preflight())
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    payload = mod.build_mirror(ctx)
    assert payload["verdict"] == MIRROR_PASS
    assert payload["mirror"]["mirror_check_pass"] is True


def test_ledger_live_allowed_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path,
        _safe_ledger(governance={"live_allowed": True}),
        _safe_preflight(),
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_ledger_secret_values_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path,
        _safe_ledger(governance={"secret_values_included": True}),
        _safe_preflight(),
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_ledger_governance_not_blocked_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path,
        _safe_ledger(governance={"governance_blocked": False}),
        _safe_preflight(),
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_preflight_status_ready_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path, _safe_ledger(), _safe_preflight(status="READY")
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_preflight_live_authorized_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path, _safe_ledger(), _safe_preflight(live_authorized=True)
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_preflight_testnet_authorized_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path, _safe_ledger(), _safe_preflight(testnet_authorized=True)
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_preflight_dry_ready_fail_closed(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(
        tmp_path,
        _safe_ledger(),
        _safe_preflight(dry_activation_readiness={"ready": True}),
    )
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_FAIL


def test_missing_ledger_review_required(mod, tmp_path: Path) -> None:
    _, preflight_path = _write_pair(tmp_path, None, _safe_preflight())
    ctx = mod.MirrorContext(ledger_path=tmp_path / "missing.json", preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_REVIEW


def test_invalid_preflight_review_required(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(tmp_path, _safe_ledger(), "{not-json")
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    assert mod.build_mirror(ctx)["verdict"] == MIRROR_REVIEW


def test_cli_json_only_stdout(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(tmp_path, _safe_ledger(), _safe_preflight())
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--ledger-json",
            str(ledger_path),
            "--preflight-json",
            str(preflight_path),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["schema"] == mod.SCHEMA
    assert payload["generated_at_utc"] == "2026-05-21T00:00:00Z"


def test_deterministic_timestamp(mod, tmp_path: Path, monkeypatch) -> None:
    ledger_path, preflight_path = _write_pair(tmp_path, _safe_ledger(), _safe_preflight())
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-05-21T12:00:00Z")
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    payload = mod.build_mirror(ctx)
    assert payload["generated_at_utc"] == "2026-05-21T12:00:00Z"


def test_schema_stable(mod, tmp_path: Path) -> None:
    ledger_path, preflight_path = _write_pair(tmp_path, _safe_ledger(), _safe_preflight())
    ctx = mod.MirrorContext(ledger_path=ledger_path, preflight_path=preflight_path)
    payload = mod.build_mirror(ctx)
    assert set(payload) == {
        "schema",
        "generated_at_utc",
        "ledger",
        "preflight",
        "mirror",
        "blockers",
        "verdict",
        "issues",
    }


def test_fixtures_dir_exists() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    assert FIXTURES.is_dir()


@pytest.mark.skipif(not ARCHIVE_ROOT.is_dir(), reason="operator archive not present")
def test_real_smoke_pass_blocked_safe(tmp_path: Path) -> None:
    ledger_path = tmp_path / "ledger_real.json"
    preflight_path = tmp_path / "preflight_real.json"
    mirror_path = tmp_path / "mirror_real.json"

    ledger_proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/ops/build_readiness_evidence_ledger_v0.py"),
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
    ledger_path.write_text(ledger_proc.stdout, encoding="utf-8")
    preflight_proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/ops/report_paper_shadow_247_preflight_status.py"),
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    preflight_path.write_text(preflight_proc.stdout, encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--ledger-json",
            str(ledger_path),
            "--preflight-json",
            str(preflight_path),
            "--fixed-generated-at-utc",
            "2026-05-21T00:00:00Z",
            "--json",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    mirror_path.write_text(proc.stdout, encoding="utf-8")
    payload = json.loads(proc.stdout)
    assert payload["verdict"] == MIRROR_PASS
