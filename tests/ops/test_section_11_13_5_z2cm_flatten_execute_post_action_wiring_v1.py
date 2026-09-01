"""§11.13.5.Z2CM flatten_execute post-action wiring. Synthetic only. No network."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    CategoryCObservationOutcomeV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FLATTEN_EXECUTE_PURPOSE_CANONICAL,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_post_action_binding_v1 import (
    CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE,
    POST_ACTION_READBACK_UNAVAILABLE,
    POST_ACTION_WIRED_IN_FLATTEN_EXECUTE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
    RecordingProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpResponseV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    TARGET_POSITION_NONZERO_PROVEN,
    TARGET_POSITION_NOT_OBSERVED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.runner_v1 import (
    run_section_11_13_5_live_canary_minimum_exposure_v1,
)

OWNER_GO = "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE"
ORIGIN_SHA = "c3614ec0ef5d2c964e2de2f6b0df97db9b7331ab"
Z2CM_DECISION_ID = "z2cm-flatten-pre-send-decision-1"
TARGET = DEFAULT_INSTRUMENT_ID
QUOTE_TS = "1787145055768"
EVAL_TS = "1787145056000"
Z2CM_GO = (
    "PEAK_TRADE_11_13_5_Z2CM_FAIL_CLOSED_POSITION_STATE_PREDICATE_AND_"
    "FLATTEN_EXECUTE_POST_ACTION_WIRING_V1"
)
GATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "flatten_pre_send_gate_v1.py"
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CM_FLATTEN_EXECUTE_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def _positions(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _pending(*rows: Mapping[str, Any]) -> dict[str, Any]:
    return {"code": "0", "data": list(rows)}


def _price(*, side: str = "SELL", pos: str = "1", **overrides: Any) -> FlattenPriceInputV1:
    payload: dict[str, Any] = {
        "flatten_side": side,
        "observed_signed_pos": pos,
        "bid": "64805.6",
        "ask": "64805.7",
        "quote_timestamp_ms": QUOTE_TS,
        "evaluation_timestamp_ms": EVAL_TS,
        "tick_sz": "0.1",
        "freshness_threshold_ms": str(FRESHNESS_THRESHOLD_MS),
    }
    payload.update(overrides)
    return FlattenPriceInputV1(**payload)


def _run(**overrides: Any) -> Any:
    payload: dict[str, Any] = {
        "mode": "flatten_execute",
        "origin_main_sha": ORIGIN_SHA,
        "owner_go": OWNER_GO,
        "live_canary_authorized": True,
        "live_enabled": True,
        "live_armed": True,
        "allow_productive_wire_send": True,
        "flatten_execute_token": FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        "flatten_execute_purpose": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "flatten_execute_owner_go": FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "flatten_execute_bound_origin_main_sha": ORIGIN_SHA,
        "flatten_live_wire_enabled": True,
        "positions_payload": _positions({"instId": TARGET, "pos": "1"}),
        "pending_orders_payload": _pending(),
        "price_input": _price(),
        "transport": RecordingProductiveFlattenTransportV1(),
        "flatten_pre_send_decision_id": Z2CM_DECISION_ID,
        "position_observation_freshness_evidence": PositionObservationFreshnessEvidenceV1(
            response_received_monotonic_ms=0,
            decision_id=Z2CM_DECISION_ID,
            evidence_kind=PRE_SEND_EVIDENCE_KIND,
        ),
        "monotonic_ms_clock": (lambda: 0),
    }
    payload.update(overrides)
    return run_section_11_13_5_live_canary_minimum_exposure_v1(**payload)


def test_standing_safety_and_gate_names_unexpanded() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert "CATEGORY_C" not in GATE_NAMES
    assert CATEGORY_C_SEND_WIRING_IN_PRE_SEND_GATE is False
    flatten_src = GATE_PATH.read_text(encoding="utf-8")
    assert "category_c_open_algo_pending_observer_v1" not in flatten_src
    assert POST_ACTION_WIRED_IN_FLATTEN_EXECUTE is True


def test_this_go_cannot_be_flatten_execute_owner_go() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token=FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL,
        purpose=FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        owner_go=Z2CM_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN" in reasons


def test_send_without_post_readback_cannot_claim_flatten_proof() -> None:
    result = _run()
    assert result.payload.get("send_completed") is True
    assert result.payload.get("POST_ACTION_WIRED_IN_FLATTEN_EXECUTE") is True
    assert result.payload.get("post_action_status") == POST_ACTION_READBACK_UNAVAILABLE
    assert result.payload.get("flatten_position_proven") is False
    assert result.payload.get("LIVE_FLATTEN_PROVABILITY") == "UNPROVEN"
    assert (
        result.payload.get("pre_position_state", {}).get("state") == TARGET_POSITION_NONZERO_PROVEN
    )
    assert result.payload.get("category_c_runtime_status") == "CATEGORY_C_STATE_UNAVAILABLE"
    assert result.payload.get("category_c_universal_absence_proven") is False


def test_recording_transport_cannot_satisfy_choice_b_causal_bind() -> None:
    result = _run(
        post_positions_payload=_positions(),
        post_pending_orders_payload=_pending(),
    )
    assert result.payload.get("send_completed") is True
    verdict = result.payload.get("post_action_verdict") or {}
    assert verdict.get("choice_b_pos_eq_0") is False
    assert verdict.get("offline_contract_satisfied") is False
    assert result.payload.get("flatten_position_proven") is False
    assert "TRANSPORT_FAILURE_BEFORE_WIRE" in (verdict.get("blocking_reasons") or [])


def test_choice_b_missing_post_target_after_wired_send_does_not_prove_no_flip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_open(request: Any) -> LiveCanaryHttpResponseV1:
        return LiveCanaryHttpResponseV1(
            status_code=200,
            body_bytes=b'{"code":"0","data":[{"sCode":"0"}]}',
            elapsed_seconds=0.01,
            endpoint=request.endpoint,
            method="POST",
            send_attempted=True,
            wire_body_sha256="ab",
            wire_body_byte_len=1,
        )

    monkeypatch.setattr(
        "src.ops.section_11_13_5_live_canary_minimum_exposure_v1."
        "flatten_productive_transport_v1.open_productive_flatten_urllib_post_v1",
        _fake_open,
    )
    transport = GatedProductiveFlattenTransportV1()
    transport.network_session_authorized = True
    result = _run(
        transport=transport,
        post_positions_payload=_positions(),
        post_pending_orders_payload=_pending(),
    )
    assert result.payload.get("send_completed") is True
    verdict = result.payload.get("post_action_verdict") or {}
    assert verdict.get("choice_b_pos_eq_0") is True
    assert verdict.get("no_flip") is False
    assert verdict.get("offline_contract_satisfied") is False
    assert result.payload.get("flatten_position_proven") is False
    assert "NO_FLIP_UNPROVEN_TARGET_MISSING" in (verdict.get("blocking_reasons") or [])


def test_explicit_post_zero_row_still_does_not_claim_live_flatten() -> None:
    result = _run(
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
        category_c_runtime_status=CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED.value,
    )
    verdict = result.payload.get("post_action_verdict") or {}
    assert verdict.get("post_pos_zero") is True
    assert result.payload.get("flatten_position_proven") is False
    assert result.payload.get("LIVE_FLATTEN_PROVABILITY") == "UNPROVEN"
    assert result.payload.get("category_c_universal_absence_proven") is False
    assert result.payload.get("category_c_open_algo_present") is False


def test_open_category_c_cannot_complete_pending_empty() -> None:
    result = _run(
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
        category_c_runtime_status=CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_OBSERVED.value,
    )
    assert result.payload.get("category_c_open_algo_present") is True
    assert result.payload.get("pending_empty_completeness") == "UNPROVEN"
    assert result.payload.get("flatten_position_proven") is False


def test_empty_pre_is_not_observed_and_does_not_send() -> None:
    result = _run(positions_payload=_positions(), transport=RecordingProductiveFlattenTransportV1())
    assert result.payload.get("send_completed") is False
    assert result.payload.get("pre_position_state", {}).get("state") == TARGET_POSITION_NOT_OBSERVED
    assert result.payload.get("flatten_position_proven") is False


def test_http_200_path_still_does_not_set_flatten_position_proven() -> None:
    result = _run(
        post_positions_payload=_positions({"instId": TARGET, "pos": "0"}),
        post_pending_orders_payload=_pending(),
    )
    assert result.payload.get("send_completed") is True
    assert result.payload.get("flatten_position_proven") is False
    assert result.payload.get("PRODUCTIVE_VENUE_PROOF") is False
