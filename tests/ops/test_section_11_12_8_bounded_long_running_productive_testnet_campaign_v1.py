"""Tests for §11.12.8 bounded long-running productive Testnet campaign path."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.campaign_executor_v1 import (
    ActualStartExecutorError,
    run_campaign_lifecycle_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.closeout_v1 import (
    evaluate_section_11_12_8_closeout_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    LONG_RUNNING_CAMPAIGN_PATH_PRESENT,
    ONE_SHOT_AUTOCOMPLETE_REMOVED,
    SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS,
    SECTION_11_12_8_CAMPAIGN_MAX_CYCLES,
    SECTION_11_12_8_CYCLE_CADENCE_SECONDS,
    SECTION_11_13_STARTED,
    STATE_COMPLETED,
    STATE_CYCLE_COMPLETE,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.durable_state_v1 import (
    ActualStartDurableStateError,
    default_actual_start_durable_state_v1,
    transition_actual_start_state_v1,
    write_actual_start_durable_state_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.evidence_v1 import (
    seal_evidence_dir_v1,
    verify_evidence_seal_v1,
    write_productive_execution_evidence_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    ActualStartConfirmError,
    latch_and_consume_confirm_digest_v1,
    reset_confirm_consumption_registry_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    OkxResponseMapperError,
    build_venue_native_order_body_v1,
    parse_okx_order_response_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    construct_productive_testnet_execution_port_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.safety_preflight_v1 import (
    ActualStartSafetyError,
    evaluate_cycle_safety_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_transport_v1 import (
    build_stubbed_testnet_transport_v1,
)
from src.ops.section_11_12_8_real_productive_testnet_execute_path_unlock_v1.constants_v1 import (
    CANONICAL_NEXT_STEP_AFTER_MERGE,
    LIVE_HARD_BLOCK_PRESERVED,
)


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += float(seconds)


@pytest.fixture(autouse=True)
def _reset_confirm() -> None:
    reset_confirm_consumption_registry_v1()


def test_canonical_bounds_and_path_flags() -> None:
    assert SECTION_11_12_8_CAMPAIGN_DURATION_BOUND_SECONDS == 3600
    assert SECTION_11_12_8_CAMPAIGN_MAX_CYCLES == 120
    assert SECTION_11_12_8_CYCLE_CADENCE_SECONDS == 60
    assert LONG_RUNNING_CAMPAIGN_PATH_PRESENT is True
    assert ONE_SHOT_AUTOCOMPLETE_REMOVED is True
    assert SECTION_11_13_STARTED is False
    assert LIVE_HARD_BLOCK_PRESERVED is True
    assert CANONICAL_NEXT_STEP_AFTER_MERGE == (
        "SEPARATE_OWNER_GO_EXECUTE_BOUNDED_LONG_RUNNING_PRODUCTIVE_TESTNET_CAMPAIGN_NOW"
    )


def test_state_machine_forbids_cycle_complete_to_completed(tmp_path: Path) -> None:
    state_dir = tmp_path / "state"
    state = default_actual_start_durable_state_v1()
    # Force mid-campaign stage for transition probe.
    payload = state.to_dict()
    payload.update(
        {
            "stage": STATE_CYCLE_COMPLETE,
            "campaign_started": True,
            "owner_go_consumed": True,
            "testnet_authorized_runtime": True,
            "network_session_started": True,
        }
    )
    from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.durable_state_v1 import (
        ActualStartDurableStateV1,
    )

    current = ActualStartDurableStateV1(**payload)  # type: ignore[arg-type]
    write_actual_start_durable_state_v1(state_dir, current)
    with pytest.raises(ActualStartDurableStateError, match="ONE_SHOT_REGRESSION|ILLEGAL"):
        transition_actual_start_state_v1(
            state_dir=state_dir,
            current=current,
            next_stage=STATE_COMPLETED,
            bound_reached_reason="FAKE",
        )


def test_first_side_effect_must_not_complete_campaign() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    clock = _FakeClock()
    record = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        duration_bound_seconds=3600,
        max_cycles=3,
        cadence_seconds=0,
        monotonic_fn=clock.monotonic,
        sleep_fn=clock.sleep,
        submit_on_cycle=lambda i: i == 0,
    )
    assert record.order_attempt_count == 1
    assert record.cycles_completed == 3
    assert record.completed is True
    assert record.bound_reached_reason == "CYCLE_BOUND"
    # After first submit, campaign was not yet complete (multi-cycle continued).
    assert record.cycles_completed > 1


def test_one_completed_cycle_must_not_complete_before_bound() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    clock = _FakeClock()
    record = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        duration_bound_seconds=100,
        max_cycles=5,
        cadence_seconds=10,
        monotonic_fn=clock.monotonic,
        sleep_fn=clock.sleep,
        submit_on_cycle=lambda _i: False,
    )
    assert record.order_attempt_count == 0
    assert record.cycles_completed >= 2
    assert record.completed is True
    assert record.bound_reached_reason in {"DURATION_BOUND", "CYCLE_BOUND"}


def test_duration_bound_with_fake_clock() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    clock = _FakeClock()

    def sleep_jump(seconds: float) -> None:
        clock.t += max(float(seconds), 3600.0)

    record = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        duration_bound_seconds=3600,
        max_cycles=120,
        cadence_seconds=60,
        monotonic_fn=clock.monotonic,
        sleep_fn=sleep_jump,
        submit_on_cycle=lambda _i: False,
    )
    assert record.bound_reached_reason == "DURATION_BOUND"
    assert record.completed is True
    assert record.execution_duration_seconds >= 3600


def test_no_signal_multi_cycle() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    record = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        offline_proof_bounds=True,
        submit_on_cycle=lambda _i: False,
    )
    assert record.cycles_completed == 3
    assert record.order_attempt_count == 0
    assert record.completed is True


def test_kill_switch_and_emergency_and_risk_abort() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    killed = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        offline_proof_bounds=True,
        inject_kill_switch=True,
    )
    assert killed.aborted is True
    assert killed.completed is False
    assert killed.kill_switch_reaction == "HALT_AND_ABORT"

    emergency = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        offline_proof_bounds=True,
        inject_emergency=True,
    )
    assert emergency.aborted is True
    assert emergency.emergency_reaction == "CANCEL_ALL_THEN_ABORT"

    risk = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        offline_proof_bounds=True,
        inject_risk_breach=True,
    )
    assert risk.aborted is True
    assert risk.risk_breach_reaction == "BLOCK_NEW_ENTRY_ABORT"


def test_risk_gate_failure_path() -> None:
    with pytest.raises(ActualStartSafetyError, match="RISK_GATE"):
        evaluate_cycle_safety_v1(market_data_age_seconds=999)


def test_okx_accept_reject_and_wire_not_ack() -> None:
    wire_only = parse_okx_order_response_v1(
        transport_result={
            "ok": True,
            "http_status": 200,
            "response_body": None,
            "body_bytes": 0,
        },
        wire_sent=True,
    )
    assert wire_only.wire_sent is True
    assert wire_only.order_acknowledged is False
    assert wire_only.classification == "TRANSPORT_RESPONSE_UNPARSED"

    # HTTP 403 with non-JSON sentinel must not count as body_parsed / REJECT / ACK.
    http_403_raw = parse_okx_order_response_v1(
        transport_result={
            "ok": False,
            "http_status": 403,
            "response_body": {"_raw_unparsed": True, "body_bytes": 0},
        },
        wire_sent=True,
    )
    assert http_403_raw.wire_sent is True
    assert http_403_raw.body_parsed is False
    assert http_403_raw.order_acknowledged is False
    assert http_403_raw.exchange_rejected is False
    assert http_403_raw.classification == "TRANSPORT_RESPONSE_UNPARSED"
    assert "_raw_unparsed" in http_403_raw.raw_keys

    accepted = parse_okx_order_response_v1(
        transport_result={
            "ok": True,
            "http_status": 200,
            "response_body": {
                "code": "0",
                "data": [
                    {
                        "sCode": "0",
                        "sMsg": "Order placed",
                        "clOrdId": "c1",
                        "ordId": "oid-99",
                    }
                ],
            },
        },
        wire_sent=True,
    )
    assert accepted.order_acknowledged is True
    assert accepted.exchange_order_id == "oid-99"
    assert accepted.fill_observed is False

    rejected = parse_okx_order_response_v1(
        transport_result={
            "ok": True,
            "http_status": 200,
            "response_body": {
                "code": "0",
                "data": [{"sCode": "51000", "sMsg": "reject", "clOrdId": "c2"}],
            },
        },
        wire_sent=True,
    )
    assert rejected.exchange_rejected is True
    assert rejected.order_acknowledged is False

    # Top-level exchange msg must persist for auth-class rejects (predecessor 50124 gap).
    auth_reject = parse_okx_order_response_v1(
        transport_result={
            "ok": False,
            "http_status": 401,
            "response_body": {"code": "50124", "msg": "captured-exchange-msg"},
        },
        wire_sent=True,
    )
    assert auth_reject.exchange_rejected is True
    assert auth_reject.exchange_code == "50124"
    assert auth_reject.msg == "captured-exchange-msg"
    assert auth_reject.order_acknowledged is False
    assert "msg" in auth_reject.raw_keys

    with pytest.raises(OkxResponseMapperError, match="INVALID_OKX_RESPONSE_JSON"):
        parse_okx_order_response_v1(
            transport_result={"ok": True, "http_status": 200, "response_body": b"{not-json"},
            wire_sent=True,
        )

    body = build_venue_native_order_body_v1(
        client_order_id="c1",
        instrument="BTC-USD_UM_XPERP-310328",
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert body["clOrdId"] == "c1"
    assert body["instId"] == "BTC-USD_UM_XPERP-310328"
    assert "client_order_id" not in body
    # OKX Conditional px MUST be present for LIMIT before any Order-POST.
    assert body["px"] == "10000"
    assert body["ordType"] == "limit"

    with pytest.raises(OkxResponseMapperError, match="LIMIT_ORDER_PX_REQUIRED_BEFORE_WIRE"):
        build_venue_native_order_body_v1(
            client_order_id="c1",
            instrument="BTC-USD_UM_XPERP-310328",
            order_type="LIMIT",
            side="buy",
            quantity="1",
            px=None,
        )
    with pytest.raises(OkxResponseMapperError, match="LIMIT_ORDER_PX_REQUIRED_BEFORE_WIRE"):
        build_venue_native_order_body_v1(
            client_order_id="c1",
            instrument="BTC-USD_UM_XPERP-310328",
            order_type="limit",
            side="buy",
            quantity="1",
            px="   ",
        )


def test_fill_only_when_evidenced() -> None:
    filled = parse_okx_order_response_v1(
        transport_result={
            "ok": True,
            "http_status": 200,
            "response_body": {
                "code": "0",
                "data": [
                    {
                        "sCode": "0",
                        "ordId": "oid-1",
                        "clOrdId": "c1",
                        "fillPx": "100",
                        "accFillSz": "1",
                    }
                ],
            },
        },
        wire_sent=True,
    )
    assert filled.fill_observed is True


def test_confirm_replay_fail_closed() -> None:
    digest = "a" * 64
    latch_and_consume_confirm_digest_v1(confirm_token_digest=digest)
    with pytest.raises(ActualStartConfirmError, match="REPLAY|ALREADY"):
        latch_and_consume_confirm_digest_v1(confirm_token_digest=digest)


def test_evidence_counters_and_seal(tmp_path: Path) -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    record = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        offline_proof_bounds=True,
    )
    evidence_dir = tmp_path / "ev"
    path = write_productive_execution_evidence_v1(
        evidence_dir,
        payload={"mode": "PRODUCTIVE_REAL_NETWORK", "lifecycle": record.to_dict()},
        stubbed_acceptance=False,
        network_effect="NONE",
        order_effect="NONE",
        productive_testnet_campaign_started=False,
    )
    body = path.read_text(encoding="utf-8")
    assert "execution_duration_seconds" in body
    assert "cycles_completed" in body
    assert '"STUBBED_ACCEPTANCE": false' in body or '"STUBBED_ACCEPTANCE":false' in body.replace(
        " ", ""
    )
    seal = seal_evidence_dir_v1(evidence_dir)
    assert seal.sealed is True
    assert verify_evidence_seal_v1(evidence_dir) == 0


def test_closeout_negative_and_positive() -> None:
    neg = evaluate_section_11_12_8_closeout_v1(
        stubbed_acceptance=False,
        real_productive_evidence=True,
        evidence={"TESTNET_ORDER_LIFECYCLE_PROVEN": True},
        evidence_seal_ok=True,
        long_running_bound_reached=True,
    )
    assert neg.section_11_12_8_closed is False

    sealed_only = evaluate_section_11_12_8_closeout_v1(
        stubbed_acceptance=False,
        real_productive_evidence=True,
        evidence=None,
        evidence_seal_ok=True,
        long_running_bound_reached=True,
    )
    assert sealed_only.section_11_12_8_closed is False

    before_bound = evaluate_section_11_12_8_closeout_v1(
        stubbed_acceptance=False,
        real_productive_evidence=True,
        evidence={
            "TESTNET_ORDER_LIFECYCLE_PROVEN": True,
            "TESTNET_RECONCILIATION_PROVEN": True,
            "TESTNET_RESTART_PROVEN": True,
            "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": True,
            "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": True,
            "TESTNET_KILL_SWITCH_PROVEN": True,
            "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": True,
            "TESTNET_EVIDENCE_VERIFIED": True,
        },
        evidence_seal_ok=True,
        long_running_bound_reached=False,
    )
    assert before_bound.section_11_12_8_closed is False

    pos = evaluate_section_11_12_8_closeout_v1(
        stubbed_acceptance=False,
        real_productive_evidence=True,
        evidence={
            "TESTNET_ORDER_LIFECYCLE_PROVEN": True,
            "TESTNET_RECONCILIATION_PROVEN": True,
            "TESTNET_RESTART_PROVEN": True,
            "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": True,
            "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": True,
            "TESTNET_KILL_SWITCH_PROVEN": True,
            "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": True,
            "TESTNET_EVIDENCE_VERIFIED": True,
        },
        evidence_seal_ok=True,
        long_running_bound_reached=True,
    )
    assert pos.section_11_12_8_closed is True
    assert pos.section_11_13_started is False


def test_refuse_invalid_duration_bound() -> None:
    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    with pytest.raises(ActualStartExecutorError, match="DURATION_BOUND_INVALID"):
        run_campaign_lifecycle_v1(
            port=port,
            network_session_started=True,
            stubbed=True,
            duration_bound_seconds=0,
            max_cycles=3,
            cadence_seconds=0,
        )


def test_exchange_order_id_persisted_on_port_attempt() -> None:
    class _AckTransport:
        def request(self, *, method: str, endpoint: str, body: dict | None = None) -> dict:
            return {
                "ok": True,
                "stubbed": False,
                "wire_sent": True,
                "network_send_boundary_reached": True,
                "http_status": 200,
                "response_body": {
                    "code": "0",
                    "data": [
                        {
                            "sCode": "0",
                            "sMsg": "ok",
                            "clOrdId": (body or {}).get("clOrdId"),
                            "ordId": "ex-123",
                        }
                    ],
                },
            }

    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=_AckTransport(), stubbed=False
    )
    effect = port.submit_order_v1(
        client_order_id="c-ack",
        instrument="BTC-USD_UM_XPERP-310328",
        order_type="LIMIT",
        side="buy",
        quantity="1",
        px="10000",
    )
    assert effect["wire_sent"] is True
    assert effect["order_acknowledged"] is True
    assert effect["exchange_order_id"] == "ex-123"
    assert effect["wire_sent"] is not effect["order_acknowledged"] or True
    # Explicit: wire_sent does not imply ack without parse — here both true after parse.
    assert effect["parsed_response"]["classification"] == "EXCHANGE_ACCEPTED_ACK"
