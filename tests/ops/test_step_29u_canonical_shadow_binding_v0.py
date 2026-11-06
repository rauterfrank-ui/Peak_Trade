"""Focused tests: Step 29U canonical Shadow no-order binding capability v0."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    run_okx_futures_shadow_no_order_cycle_v0,
)
from src.ops.shadow_preparation_readiness_gate_v0 import (
    evaluate_shadow_preparation_readiness_gate_v0,
)
from src.ops.step_29u_canonical_shadow_binding_v0 import (
    BINDING_OWNER,
    CANONICAL_STEP_29U_EVIDENCE_RELPATH,
    PACKAGE_MARKER,
    observe_canonical_step_29u_bound_v0,
    verify_canonical_step_29u_binding_evidence_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_EVIDENCE = REPO_ROOT / CANONICAL_STEP_29U_EVIDENCE_RELPATH


def test_step_29u_bound_pass_full_chain_hold_presence_truthful() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repo_root=REPO_ROOT,
    )
    assert result.terminal_status == "PASS"
    assert result.direction == "HOLD"
    assert result.decision_result == "hold"
    assert result.risk_sizing_result
    assert result.execution_intent_result
    assert result.reconciliation_audit_result
    assert result.step_29u_bound is True
    assert result.step_29u_present is True
    assert result.step_29u_evidence_verified is True
    assert result.canonical_step_29u_absent is False
    assert result.step_29u_capability_result == "STEP_29U_OFFLINE_CAPABILITY_PASS"
    assert result.step_29u_binding_owner == BINDING_OWNER
    assert result.real_order_submission is False
    assert result.order_capable_client_instantiated is False
    assert result.exchange_order_submission is False
    assert result.live_activation is False
    assert result.scheduler is False
    assert PACKAGE_MARKER.startswith("STEP_29U_CANONICAL_SHADOW_BINDING")


def test_step_29u_missing_fail_closed_no_fallback_pass(tmp_path: Path) -> None:
    empty = REPO_ROOT / "out" / "tmp_step29u_binding_missing_evidence"
    if empty.exists():
        shutil.rmtree(empty)
    empty.mkdir(parents=True)
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repo_root=REPO_ROOT,
        evidence_dir=empty,
    )
    assert result.terminal_status == "FAIL_CLOSED"
    assert result.step_29u_bound is False
    assert result.canonical_step_29u_absent is True
    assert "STEP_29U_BINDING_FAIL_CLOSED" in result.blockers
    assert any("MISSING" in b for b in result.blockers)
    assert result.real_order_submission is False
    assert result.order_capable_client_instantiated is False


def test_step_29u_invalid_or_contradictory_fail_closed(tmp_path: Path) -> None:
    bad = REPO_ROOT / "out" / "tmp_step29u_binding_bad_evidence"
    if bad.exists():
        shutil.rmtree(bad)
    shutil.copytree(CANONICAL_EVIDENCE, bad)
    payload_path = bad / "capability_result.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    payload["schema_id"] = "ops.not_step_29u"
    payload["step_29u_activated"] = True
    payload_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    # Manifest digests will also mismatch after rewrite.
    ok, reasons, _ = verify_canonical_step_29u_binding_evidence_v0(
        repo_root=REPO_ROOT,
        evidence_dir=bad,
    )
    assert ok is False
    assert any(
        "SCHEMA" in r or "ACTIVATION" in r or "DIGEST" in r or "MANIFEST" in r for r in reasons
    )

    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        repo_root=REPO_ROOT,
        evidence_dir=bad,
    )
    assert result.terminal_status == "FAIL_CLOSED"
    assert result.step_29u_bound is False
    assert result.live_activation is False
    assert result.real_order_submission is False


def test_no_order_contract_zero_orders_zero_network() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        repo_root=REPO_ROOT,
    )
    assert result.terminal_status == "PASS"
    assert result.real_order_submission is False
    assert result.order_capable_client_instantiated is False
    assert result.exchange_order_submission is False
    assert result.testnet_order_submission is False
    assert result.live_activation is False
    assert result.scheduler is False


def test_architecture_boundaries_sole_owner_no_dashboard_btc_spot() -> None:
    src = (REPO_ROOT / "src/ops/step_29u_canonical_shadow_binding_v0.py").read_text(
        encoding="utf-8"
    )
    assert "src.webui" not in src
    assert "kraken" not in src.lower()
    assert BINDING_OWNER == "ops.step_29u_canonical_shadow_binding_v0"
    btc = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id="BTC-USD_UM_XPERP-310404",
        repo_root=REPO_ROOT,
    )
    assert btc.terminal_status == "FAIL_CLOSED"
    assert "btc_instrument_forbidden" in btc.blockers
    spot = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id="ETH/USDT",
        repo_root=REPO_ROOT,
    )
    assert spot.terminal_status == "FAIL_CLOSED"
    assert "spot_instrument_forbidden" in spot.blockers


def test_readiness_gate_stops_emitting_absent_when_bound() -> None:
    bound, reasons = observe_canonical_step_29u_bound_v0(repo_root=REPO_ROOT)
    assert bound is True
    assert reasons == ()
    result = evaluate_shadow_preparation_readiness_gate_v0(repo_root=REPO_ROOT)
    assert result.canonical_step_29u_bound is True
    assert result.step_29u_implemented is True
    assert "CANONICAL_STEP_29U_ABSENT" not in result.blockers
    assert result.shadow_activation_authorized is False
    assert result.orders_authorized is False
    assert result.runtime_activation_authorized is False
    assert result.shadow_activatable is False
    assert result.not_step_29u_implementation is True
