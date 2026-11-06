"""§11.13.5.Z2CF next-pointer adjudication contract.

Locks that this docs persist does not flip standing live/testnet/canary
flags, does not change consumer empty-vs-zero semantics, and does not
enable flatten send. Offline only. No venue access.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED,
    LIVE_ENABLED,
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

Z2CF_PERSIST_OWNER_GO = (
    "SECTION_11_13_5_POST_Z2CE_POST_6058_NORMAL_SYSTEM_NEXT_POINTER_ADJUDICATION_PERSIST_ONLY"
)
CURRENT_SUI = "SUI-USD_UM_XPERP-310404"


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("NETWORK_FORBIDDEN_IN_Z2CF_CONTRACT_TESTS")

    monkeypatch.setattr("urllib.request.urlopen", _blocked)
    monkeypatch.setattr("socket.create_connection", _blocked)


def test_standing_live_testnet_canary_remain_false() -> None:
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert TESTNET_AUTHORIZED is False
    assert SUBMIT_UNLOCKED is False
    assert LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED is False
    assert DEFAULT_INSTRUMENT_ID == CURRENT_SUI
    assert CANARY_INSTRUMENT == CURRENT_SUI


def test_empty_payload_is_still_not_zero() -> None:
    try:
        observe_target_position_flatten_candidate_v1(
            positions_payload={"code": "0", "data": []},
            instrument_id=CURRENT_SUI,
        )
        raise AssertionError("empty position window must not become zero")
    except LiveCanaryPositionObservationError as exc:
        assert str(exc) == "TARGET_INSTRUMENT_NOT_OBSERVED"
        assert "ZERO" not in str(exc)


def test_z2cf_persist_go_is_not_flatten_execute_go() -> None:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token="I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE",
        purpose="SECTION_11_13_5_FLATTEN_EXECUTE",
        owner_go=Z2CF_PERSIST_OWNER_GO,
    )
    assert accepted is False
    assert "FLATTEN_EXECUTE_OWNER_GO_MISMATCH" in reasons
    assert Z2CF_PERSIST_OWNER_GO != FLATTEN_EXECUTE_OWNER_GO_CANONICAL


def test_productive_flatten_urllib_remains_unimplemented() -> None:
    assert DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED is False
    transport = GatedProductiveFlattenTransportV1()
    assert transport.network_session_authorized is False
