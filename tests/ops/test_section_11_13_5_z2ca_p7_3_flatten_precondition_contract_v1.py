"""§11.13.5 P7.3 flatten-precondition contract.

Locks the empty/absent/zero distinctions after the fresh SUI
position-state GET. Prevents empty-data-as-zero, BTC-as-SUI proof,
Category-C-as-zero, and P7.3-to-P7.4 promotion. Offline only. No
venue access.
"""

from __future__ import annotations

from decimal import Decimal

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    GET_ENDPOINTS_PRIVATE,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POSITION_COUNT_LIMIT,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_fee_reserve_rates_rebind_get_path_v1 import (
    COVER_USDC_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    MULTI_FUTURE_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)

HISTORICAL_BTC = "BTC-USD_UM_XPERP-310404"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"
POSITIONS_ENDPOINT = "/api/v5/account/positions"


def test_current_identity_is_sui_and_positions_path_is_allowlisted() -> None:
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert CANARY_INSTRUMENT == CURRENT_SUI
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == HISTORICAL_BTC
    assert POSITIONS_ENDPOINT in GET_ENDPOINTS_PRIVATE


def test_empty_payload_is_not_observed_not_zero() -> None:
    empty_positions = {"code": "0", "data": []}
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=empty_positions,
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("empty position window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
        assert "ZERO" not in str(exc)


def test_explicit_zero_row_is_distinct_from_absent_row() -> None:
    zero_row = {
        "code": "0",
        "data": [{"instId": CURRENT_SUI, "pos": "0"}],
    }
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=zero_row,
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("explicit zero row must not become a flatten candidate")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "ZERO_POSITION_NO_FLATTEN_ORDER"
        assert str(exc) != "TARGET_INSTRUMENT_NOT_OBSERVED"
    signed = Decimal(str(zero_row["data"][0]["pos"]))
    assert signed == Decimal("0")


def test_btc_empty_window_is_not_sui_position_proof() -> None:
    empty_positions = {"code": "0", "data": []}
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=empty_positions,
            instrument_id=HISTORICAL_BTC,
        )
        raise AssertionError("BTC empty window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
    assert HISTORICAL_BTC != DEFAULT_INSTRUMENT_ID


def test_p7_3_does_not_unlock_flatten_live_or_cover() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert CANARY_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert MULTI_FUTURE_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert POSITION_COUNT_LIMIT == 1
    assert COVER_USDC_STATUS == "UNINSTANTIATED"
    assert LIVE_FLATTEN_PROVABILITY_STATUS == "UNPROVEN"
