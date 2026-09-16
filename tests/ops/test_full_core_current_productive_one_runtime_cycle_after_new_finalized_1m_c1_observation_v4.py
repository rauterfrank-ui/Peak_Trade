"""C1-gated CURRENT_PRODUCTIVE one-cycle owner V4. No venue POST."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    POST_ALLOWED,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v4 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREVIOUS_C1_VENUE_EVENT_TIME,
    STANDING_SEAM_REMAINDER,
    CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
    execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 import (
    _eligible_transport,
    _fresh_get_transport,
)

SATISFIED_TS_MS = 1_789_527_600_000


def _candles(*, last_ts_ms: int, confirm: str = "1", count: int = 8) -> dict[str, object]:
    rows: list[list[str]] = []
    close = 0.188
    for index in range(count):
        ts = str(last_ts_ms - (count - 1 - index) * 60_000)
        px = f"{close:.4f}"
        rows.append(
            [ts, px, px, px, px, "10", "100", "USDT", confirm if index == count - 1 else "1"]
        )
    return {"code": "0", "data": rows}


def test_created_flag_and_standing_post_forbidden() -> None:
    assert (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED
        is True
    )
    assert POST_ALLOWED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "30d8ec5e3779991f9bda145d3cde38241602e5e1"
    assert PREVIOUS_C1_VENUE_EVENT_TIME == 1789526340.0
    assert current_productive_first_real_blocker_v1() == STANDING_SEAM_REMAINDER


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_origin_main_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_gate_not_satisfied_does_not_run_cycle(tmp_path: Path) -> None:
    result = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        c1_gate_payload=_candles(last_ts_ms=int(PREVIOUS_C1_VENUE_EVENT_TIME * 1000)),
    )
    assert result.condition_gate == "NOT_YET_SATISFIED"
    assert result.runtime_cycle_count == "0"
    assert result.master_v2_runtime_cycle_id == ""
    assert result.post_count == "0"
    assert result.first_real_blocker == "CONDITION_GATE_NOT_YET_SATISFIED"
    assert (tmp_path / "store" / "c1_gate_v1.json").is_file()


def test_gate_override_not_satisfied_does_not_run_cycle(tmp_path: Path) -> None:
    result = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        c1_gate_override={
            "CONDITION_GATE": "NOT_YET_SATISFIED",
            "PREVIOUS_C1_VENUE_EVENT_TIME": str(PREVIOUS_C1_VENUE_EVENT_TIME),
            "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": str(PREVIOUS_C1_VENUE_EVENT_TIME),
            "NEW_C1_EVIDENCE_AVAILABLE": "false",
        },
    )
    assert result.condition_gate == "NOT_YET_SATISFIED"
    assert result.runtime_cycle_count == "0"
    assert result.master_v2_runtime_cycle_id == ""
    assert result.post_count == "0"


def test_satisfied_gate_runs_one_injected_cycle_without_post(tmp_path: Path) -> None:
    result = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        producer_observed_at_unix=1_700_000_100.0,
    )
    assert result.condition_gate == "SATISFIED"
    assert result.runtime_cycle_count == "1"
    assert result.post_count == "0"
    assert result.permit_created == "false"
    assert result.master_v2_runtime_cycle_id
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0
