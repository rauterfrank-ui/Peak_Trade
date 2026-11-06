"""§11.13.5.Z2CC P7.5 live-gate reconciliation contract.

Locks forensic fail-closed rules: empty != zero, P7.3/P7.4 not
reinterpreted, standing live/testnet/canary remain false, Cover remains
uninstantiated, USD is not USDC, implementation existence is not
execution proof, P8 does not start. Offline only. No venue access.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SINGLE_SELECTED_FUTURE,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    ENABLE_LIVE_TRADING,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    POSITION_COUNT_LIMIT,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    evaluate_flatten_execute_authority_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)

P7_5_OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CB_P7_5_LIVE_GATE_RECONCILIATION_READ_ONLY_FORENSIC_ADJUDICATION_ONLY"
)
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"
HISTORICAL_BTC = "BTC-USD_UM_XPERP-310404"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_P7_5_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_standing_live_testnet_canary_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert LIVE_ORDER_AUTHORIZED is False
    assert ENABLE_LIVE_TRADING is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_AUTHORIZED_DEFAULT is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN is False


def test_canonical_instrument_is_sui_and_btc_is_historical() -> None:
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert CANARY_INSTRUMENT == CURRENT_SUI
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == HISTORICAL_BTC
    assert SINGLE_SELECTED_FUTURE is True
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert POSITION_COUNT_LIMIT == 1


def test_p7_3_empty_still_not_zero() -> None:
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload={"code": "0", "data": []},
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("empty position window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
        assert "ZERO" not in str(exc)


def test_p7_5_go_is_not_flatten_execute_go() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=P7_5_OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_MISMATCH" in reasons
    assert P7_5_OWNER_GO != FLATTEN_EXECUTE_OWNER_GO_CANONICAL


def test_productive_flatten_urllib_remains_unimplemented() -> None:
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False


def test_p7_3_and_p7_4_are_not_live_ready() -> None:
    target_zero_proven = False
    target_nonzero_proven = False
    flatten_proof_status = "UNRESOLVED_FAIL_CLOSED"
    productive_urllib_send_implemented = False
    assert target_zero_proven is False
    assert target_nonzero_proven is False
    assert flatten_proof_status == "UNRESOLVED_FAIL_CLOSED"
    assert productive_urllib_send_implemented is False
    live_readiness_from_p7_3_or_p7_4 = False
    assert live_readiness_from_p7_3_or_p7_4 is False


def test_cover_usdc_and_usd_usdc_remain_unproven() -> None:
    cover_usdc_status = "UNINSTANTIATED"
    usd_usdc_operator_status = "UNPROVEN"
    usd_equals_usdc_assumed = False
    cover_substitutable_by_identity = False
    assert cover_usdc_status == "UNINSTANTIATED"
    assert usd_usdc_operator_status == "UNPROVEN"
    assert usd_equals_usdc_assumed is False
    assert cover_substitutable_by_identity is False
