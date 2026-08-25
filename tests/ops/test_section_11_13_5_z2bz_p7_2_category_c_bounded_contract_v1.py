"""§11.13.5 P7.2 Category-C bounded contract.

Locks the live-relevant Category-C statement after the Z2BY SUI identity
rebind. Prevents empty-window universal-absence, NOT_OBSERVED-as-zero,
BTC-window-as-SUI-proof, and Category-C-closure promotions into flatten,
live, cover, or risk. Offline only. No venue access.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    CANARY_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.category_c_open_algo_pending_observer_v1 import (
    CATEGORY_C_ORD_TYPE_VARIANTS,
    CategoryCObservationOutcomeV1,
    observe_category_c_open_algo_pending_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_ORDERS_ALGO_PENDING,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    GATE_NAMES,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    RecordingFakeCanaryTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    MULTI_FUTURE_AUTHORIZED,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPositionObservationError,
    observe_target_position_flatten_candidate_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OBSERVER_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "category_c_open_algo_pending_observer_v1.py"
)
FLATTEN_GATE_PATH = (
    REPO_ROOT
    / "src"
    / "ops"
    / "section_11_13_5_live_canary_minimum_exposure_v1"
    / "flatten_pre_send_gate_v1.py"
)
HISTORICAL_BTC = "BTC-USD_UM_XPERP-310404"
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


def _ok_body() -> bytes:
    return json.dumps({"code": "0", "data": []}).encode()


def _client(transport: RecordingFakeCanaryTransportV1) -> LiveCanaryHttpClientV1:
    return LiveCanaryHttpClientV1(
        rest_base="https://eea.okx.com",
        rest_host="eea.okx.com",
        transport=transport,
        max_request_count=64,
    )


def test_current_identity_is_sui_and_historical_btc_is_not_current_scope() -> None:
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert CANARY_INSTRUMENT == CURRENT_SUI
    assert HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID == HISTORICAL_BTC
    assert HISTORICAL_BTC != DEFAULT_INSTRUMENT_ID


def test_empty_window_is_not_observed_not_universal_absence() -> None:
    transport = RecordingFakeCanaryTransportV1(body=_ok_body())
    result = observe_category_c_open_algo_pending_v1(
        client=_client(transport),
        instrument_id=DEFAULT_INSTRUMENT_ID,
    )
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert result.target_instrument_id == CURRENT_SUI
    assert result.target_rows == ()
    names = {member.name for member in CategoryCObservationOutcomeV1}
    assert "UNIVERSAL_ABSENCE" not in names
    assert "UNIVERSAL_CATEGORY_C_ABSENCE" not in names
    assert "POSITION_ZERO" not in names
    assert result.outcome.value != "UNIVERSAL_ABSENCE"
    assert "universal" not in result.outcome.value.lower()
    assert "zero" not in result.outcome.value.lower()


def test_btc_empty_window_is_not_sui_absence_proof() -> None:
    transport = RecordingFakeCanaryTransportV1(body=_ok_body())
    btc = observe_category_c_open_algo_pending_v1(
        client=_client(transport),
        instrument_id=HISTORICAL_BTC,
    )
    assert btc.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert btc.target_instrument_id == HISTORICAL_BTC
    queries = [parse_qs(urlparse(call.endpoint).query) for call in transport.calls]
    assert all(query["instId"] == [HISTORICAL_BTC] for query in queries)
    assert all(query["instId"] != [CURRENT_SUI] for query in queries)
    assert btc.target_instrument_id != DEFAULT_INSTRUMENT_ID
    assert CATEGORY_C_ORD_TYPE_VARIANTS == (
        "conditional,oco",
        "trigger",
        "move_order_stop",
    )


def test_not_observed_is_not_position_zero() -> None:
    transport = RecordingFakeCanaryTransportV1(body=_ok_body())
    result = observe_category_c_open_algo_pending_v1(
        client=_client(transport),
        instrument_id=DEFAULT_INSTRUMENT_ID,
    )
    assert result.outcome is CategoryCObservationOutcomeV1.TARGET_CATEGORY_C_NOT_OBSERVED
    assert not hasattr(result, "signed_pos")
    assert "position" not in inspect.signature(observe_category_c_open_algo_pending_v1).parameters
    empty_positions = {"code": "0", "data": []}
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload=empty_positions,
            instrument_id=DEFAULT_INSTRUMENT_ID,
        )
        raise AssertionError("empty position window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
        assert "ZERO" not in str(exc)


def test_category_c_closure_does_not_complete_flatten_live_or_cover() -> None:
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
    assert "CATEGORY_C" not in GATE_NAMES
    flatten_src = FLATTEN_GATE_PATH.read_text(encoding="utf-8")
    assert "category_c_open_algo_pending_observer_v1" not in flatten_src
    assert ENDPOINT_ORDERS_ALGO_PENDING not in flatten_src
    observer_src = OBSERVER_PATH.read_text(encoding="utf-8")
    assert "LIVE_AUTHORIZED = True" not in observer_src
    assert "COVER_USDC" not in observer_src
    assert "RISK_ENVELOPE" not in observer_src
