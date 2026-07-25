"""Focused contract tests for OKX Futures Shadow no-order entrypoint v0."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.okx_futures_shadow_no_order_entrypoint_v0 import (
    CLI_RELPATH,
    PACKAGE_MARKER,
    run_okx_futures_shadow_no_order_cycle_v0,
    serialize_okx_futures_shadow_no_order_cycle_result_v0,
    validate_shadow_no_order_request_v0,
)
from src.shadow_no_order_proof import adapter_contract_v0

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / CLI_RELPATH


def test_a_valid_canonical_non_btc_okx_futures_shadow_cycle_passes() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert result.terminal_status == "PASS"
    assert result.venue == "okx_europe"
    assert result.instrument == PRODUCTION_INSTRUMENT_ID
    assert result.futures_only is True
    assert result.btc_excluded is True
    assert result.spot_excluded is True
    assert result.decision_result == "hold"
    assert result.direction == "HOLD"
    assert result.real_order_submission is False
    assert result.order_capable_client_instantiated is False
    assert result.exchange_order_submission is False
    assert result.testnet_order_submission is False
    assert result.live_activation is False
    assert result.scheduler is False
    assert result.background_process_left_running is False
    assert result.reconciliation_audit_result
    assert PACKAGE_MARKER in result.package_marker
    assert result.step_29u_bound is True
    assert result.step_29u_present is True
    assert result.canonical_step_29u_absent is False


def test_b_btc_instrument_fails_closed() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id="BTC-USD_UM_XPERP-310404",
    )
    assert result.terminal_status == "FAIL_CLOSED"
    assert "btc_instrument_forbidden" in result.blockers


def test_c_spot_instrument_fails_closed() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id="ETH/USDT",
    )
    assert result.terminal_status == "FAIL_CLOSED"
    assert "spot_instrument_forbidden" in result.blockers


def test_d_live_or_order_capable_config_fails_closed() -> None:
    live = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        live_enabled=True,
    )
    assert live.terminal_status == "FAIL_CLOSED"
    assert "live_enabled_forbidden" in live.blockers

    orders = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        order_submission_enabled=True,
    )
    assert orders.terminal_status == "FAIL_CLOSED"
    assert "order_submission_forbidden" in orders.blockers

    testnet = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
        testnet_order_submission_enabled=True,
    )
    assert testnet.terminal_status == "FAIL_CLOSED"
    assert "testnet_order_submission_forbidden" in testnet.blockers


def test_e_missing_or_invalid_canonical_input_fails_closed() -> None:
    missing_mode = validate_shadow_no_order_request_v0(
        mode="",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert "mode_must_be_shadow" in missing_mode

    wrong_inst = run_okx_futures_shadow_no_order_cycle_v0(
        mode="shadow",
        instrument_id="ETH-PERP",
    )
    assert wrong_inst.terminal_status == "FAIL_CLOSED"
    assert "instrument_must_match_canonical_okx_europe_xperp_binding" in wrong_inst.blockers

    paper_mode = run_okx_futures_shadow_no_order_cycle_v0(
        mode="paper",
        instrument_id=PRODUCTION_INSTRUMENT_ID,
    )
    assert paper_mode.terminal_status == "FAIL_CLOSED"
    assert "mode_must_be_shadow" in paper_mode.blockers


def test_f_authentic_hold_result_is_observable_success() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(mode="shadow")
    assert result.terminal_status == "PASS"
    assert result.decision_result == "hold"
    assert result.direction == "HOLD"
    assert "shadow_no_order_mode" in result.reason_codes or result.reason_codes
    payload = serialize_okx_futures_shadow_no_order_cycle_result_v0(result)
    assert payload["real_order_submission"] is False
    assert payload["reconciliation_audit_result"]


def test_g_no_order_submission_adapter_client_called() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(mode="shadow")
    assert result.order_capable_client_instantiated is False
    assert result.exchange_order_submission is False
    assert result.real_order_submission is False
    # Intent projection may be NOT_APPLICABLE/NONE for HOLD — never a live submit.
    assert "SUBMIT" not in result.execution_intent_result.upper()
    assert "PLACE" not in result.execution_intent_result.upper()


def test_h_structured_reconciliation_audit_output_emitted() -> None:
    result = run_okx_futures_shadow_no_order_cycle_v0(mode="shadow")
    assert result.reconciliation_audit_result
    assert result.risk_sizing_result
    assert result.safety_result
    assert result.execution_intent_result
    assert result.input_provenance.startswith("src.ops.bounded_futures_testnet_venue_binding_v0")


def test_i_cli_exits_clean_and_leaves_no_background_process() -> None:
    assert CLI.is_file()
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--mode",
            "shadow",
            "--instrument-id",
            PRODUCTION_INSTRUMENT_ID,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "TERMINAL_STATUS=PASS" in proc.stdout
    assert "REAL_ORDER_SUBMISSION=false" in proc.stdout
    assert "BACKGROUND_PROCESS_LEFT_RUNNING=false" in proc.stdout
    # CompletedProcess implies the child exited; no background persistence.


def test_cli_fail_closed_on_forbidden_flags() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--mode",
            "shadow",
            "--live-enabled",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert proc.returncode == 2
    assert "TERMINAL_STATUS=FAIL_CLOSED" in proc.stdout


def test_proof_package_points_at_new_entrypoint() -> None:
    assert (
        adapter_contract_v0.EXTERNAL_PROVEN_EXECUTABLE_SHADOW_NO_ORDER_ENTRYPOINT_RELPATH
        == CLI_RELPATH
    )
    assert (
        adapter_contract_v0.EXTERNAL_PROVEN_EXECUTABLE_SHADOW_NO_ORDER_ENTRYPOINT_MODULE
        == "src.ops.okx_futures_shadow_no_order_entrypoint_v0"
    )
    # Declarative package itself remains non-executable / non-approving.
    assert adapter_contract_v0.PROVEN_SHADOW_NO_ORDER_ENTRYPOINT_FOUND is False
    assert adapter_contract_v0.EXECUTABLE_COMMAND_CREATED is False
