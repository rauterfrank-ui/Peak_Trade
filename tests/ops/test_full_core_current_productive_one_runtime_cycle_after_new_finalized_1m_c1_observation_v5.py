"""C1-gated CURRENT_PRODUCTIVE one-cycle owner V5. No venue POST."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V5_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v4 import (
    EXPECTED_ORIGIN_MAIN_SHA as V4_EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO as V4_OWNER_GO,
    PREVIOUS_C1_VENUE_EVENT_TIME as V4_PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    CLI_ORIGIN_MAIN_SHA_DEFAULT,
    CONSUMED_V4_OWNER_GO,
    CURRENT_CURSOR_STORE_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    PREVIOUS_C1_VENUE_EVENT_TIME,
    STANDING_SEAM_REMAINDER,
    CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
    execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 import (
    _eligible_transport,
    _fresh_get_transport,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKED_CURSOR = (
    REPO_ROOT
    / "evidence/ops/full_core_current_productive_sidestate_confirmation_cursor_current_v1"
    / "current_productive_sidestate_confirmation_cursor_v1.json"
)
V4_HOST = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v4.py"
)
SATISFIED_TS_MS = 1_789_527_840_000
FLOOR_TS_MS = 1_789_527_780_000
V4_SATISFIED_TS_MS = 1_789_527_600_000


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


def _execute(**kwargs):
    kwargs.setdefault("actual_checkout_sha", EXPECTED_ORIGIN_MAIN_SHA)
    return execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        **kwargs
    )


def test_created_flag_standing_pins_and_c1_floor() -> None:
    assert (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V5_CREATED
        is True
    )
    assert POST_ALLOWED is False
    assert REAL_EXTERNAL_EFFECT_AUTHORIZED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert EXPECTED_ORIGIN_MAIN_SHA == "cd96b853dc8905757caaa6881cdc5145a430087a"
    assert PREVIOUS_C1_VENUE_EVENT_TIME == 1789527780.0
    assert PREVIOUS_C1_VENUE_EVENT_TIME != 1789526340.0
    assert current_productive_first_real_blocker_v1() == STANDING_SEAM_REMAINDER
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert CLI_ORIGIN_MAIN_SHA_DEFAULT == ""
    assert CLI_ORIGIN_MAIN_SHA_DEFAULT != EXPECTED_ORIGIN_MAIN_SHA


def test_v4_host_unchanged() -> None:
    assert (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED
        is True
    )
    assert V4_OWNER_GO == CONSUMED_V4_OWNER_GO
    assert V4_PREVIOUS_C1_VENUE_EVENT_TIME == 1789526340.0
    assert V4_EXPECTED_ORIGIN_MAIN_SHA == "30d8ec5e3779991f9bda145d3cde38241602e5e1"
    text = V4_HOST.read_text(encoding="utf-8")
    assert "1789527780.0" not in text
    assert OWNER_GO not in text
    assert "CHECKOUT_HEAD_MISMATCH" not in text


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="OWNER_GO_MISMATCH",
    ):
        _execute(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_consumed_v4_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="OWNER_GO_MISMATCH",
    ):
        _execute(
            owner_go=CONSUMED_V4_OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_origin_main_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        _execute(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_checkout_head_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="CHECKOUT_HEAD_MISMATCH",
    ):
        _execute(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            actual_checkout_sha="0" * 40,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_default_argument_cannot_self_confirm_wrong_head(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5."
        "resolve_repository_sha_from_git_head_v1",
        lambda repo_root: "0" * 40,
    )
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="CHECKOUT_HEAD_MISMATCH",
    ):
        execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_empty_origin_main_sha_argument_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="ORIGIN_MAIN_SHA_ARGUMENT_MISSING",
    ):
        _execute(
            owner_go=OWNER_GO,
            origin_main_sha=CLI_ORIGIN_MAIN_SHA_DEFAULT,
            evidence_root=tmp_path / "store",
            c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        )


def test_gate_equal_to_floor_does_not_run_cycle(tmp_path: Path) -> None:
    result = _execute(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        c1_gate_payload=_candles(last_ts_ms=FLOOR_TS_MS),
    )
    assert result.condition_gate == "NOT_YET_SATISFIED"
    assert result.runtime_cycle_count == "0"
    assert result.master_v2_runtime_cycle_id == ""
    assert result.post_count == "0"
    assert result.permit_created == "false"
    assert result.first_real_blocker == "CONDITION_GATE_NOT_YET_SATISFIED"


def test_v4_satisfied_timestamp_does_not_satisfy_v5_floor(tmp_path: Path) -> None:
    result = _execute(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        c1_gate_payload=_candles(last_ts_ms=V4_SATISFIED_TS_MS),
    )
    assert result.condition_gate == "NOT_YET_SATISFIED"
    assert result.runtime_cycle_count == "0"


def test_gate_override_previous_must_be_v5_floor(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError,
        match="C1_GATE_OVERRIDE_PREVIOUS_MISMATCH",
    ):
        _execute(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "store",
            c1_gate_override={
                "CONDITION_GATE": "NOT_YET_SATISFIED",
                "PREVIOUS_C1_VENUE_EVENT_TIME": "1789526340.0",
                "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": "1789526340.0",
                "NEW_C1_EVIDENCE_AVAILABLE": "false",
            },
        )


def test_gate_override_not_satisfied_does_not_run_cycle(tmp_path: Path) -> None:
    result = _execute(
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
    assert result.post_count == "0"
    assert result.permit_created == "false"


def test_tracked_n1_cursor_identity_unchanged() -> None:
    payload = json.loads(TRACKED_CURSOR.read_text(encoding="utf-8"))
    assert payload["venue_native_id"] == "0G-USDT-SWAP"
    assert payload["side_state"] == "neutral_observe"
    cap61 = payload["cap61_confirmation_state"]["observation_acceptance_state"]
    assert cap61["last_accepted_observation_identity"]["venue_event_time"] == 1789527780.0
    assert cap61["market_observation_epoch"]["value"] == 6
    assert CURRENT_CURSOR_STORE_RELPATH.endswith(
        "full_core_current_productive_sidestate_confirmation_cursor_current_v1"
    )


def test_cursor_instrument_mismatch_fail_closed(tmp_path: Path) -> None:
    incoming = json.loads(TRACKED_CURSOR.read_text(encoding="utf-8"))
    result = _execute(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "store",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        incoming_cursor=incoming,
        producer_observed_at_unix=1_700_000_100.0,
    )
    claims = json.loads((tmp_path / "store" / "claims.json").read_text(encoding="utf-8"))
    assert result.post_count == "0"
    assert result.permit_created == "false"
    assert claims["CURSOR_RESTORE_STATUS"] == "refused_mismatch"
    assert claims["CROSS_INSTRUMENT_CONFIRMATION_CARRY"] == "false"
    assert claims["PREVIOUS_CURSOR_INSTRUMENT"] == "0G-USDT-SWAP"
    assert claims["SELECTED_INSTRUMENT"] != "0G-USDT-SWAP"
    assert claims["VENUE_MUTATION_PERFORMED"] == "false"


def test_satisfied_gate_hold_deny_without_post(tmp_path: Path) -> None:
    result = _execute(
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
    assert result.venue_plan_status == "DENY"
    assert "HOLD" in result.decision_provenance or result.first_real_blocker == "HOLD"
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0
