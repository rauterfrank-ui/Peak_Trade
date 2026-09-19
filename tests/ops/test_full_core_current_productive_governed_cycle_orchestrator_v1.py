"""CURRENT_PRODUCTIVE governed one-cycle orchestrator. No POST."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_CHANGE_TRADING_LOGIC,
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    AUTONOMY_CAN_RESELECT_DOWNSTREAM,
    DISPOSITION_COMPLETED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    DISPOSITION_PRESENT,
    EG_OWNER_GO,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
    GET_OWNER_GO,
    JOIN_SEAM_ID,
    OWNER_GO,
    REASON_GO_IDENTITY_COLLAPSE,
    REASON_INJECTED_C1_REQUIRED,
    REASON_NETWORK_NOT_AUTHORIZED,
    REASON_OWNER_GO_MISMATCH,
    REASON_PARTIAL_NOT_RESUMABLE,
    REASON_PERSIST_GO_NOT_RUNTIME_LICENSE,
    REASON_POST_GO_IN_CYCLE_AUTHORIZATION,
    REASON_REMAINDER_IS_NOT_CONSUME_LICENSE,
    REASON_REPLAY,
    REASON_SUBORDINATE_GO_MISMATCH,
    REMAINDER_OWNER_GO,
    RUNTIME_OWNER_GO,
    RUNTIME_OWNER_GO_STATUS,
    S5_V5_EXECUTE_NETWORK,
    THIS_SLICE,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
    CurrentProductiveGovernedCycleOrchestratorError,
    bind_s5_governed_cycle_orchestrator_offline_v1,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    OCCUPANCY_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
    CURSOR_LINEAGE_ID,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_CREATED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    _seed_cursor,
)
from tests.ops.current_productive_c1_cycle_test_fixtures_v1 import (
    _candles,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs" / "FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
OWNER_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_cycle_orchestrator_v1.py"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
CURSOR_FLOOR = 1789664700.0
NEW_C1 = 1789664760.0
NATIVE_ID = "0G-USDT-SWAP"
ORIGIN_SHA = "f9bbd1d8c77a571b9c3f8cd238bacf21f200877d"


def _auth(**overrides: object) -> CurrentProductiveGovernedCycleAuthorizationV1:
    payload = {
        "cycle_owner_go": RUNTIME_OWNER_GO,
        "get_owner_go": GET_OWNER_GO,
        "eg_owner_go": EG_OWNER_GO,
        "occupancy_owner_go": OCCUPANCY_OWNER_GO,
        "t2_owner_go": T2_RUNTIME_OWNER_GO,
        "native_id": NATIVE_ID,
        "bar": "1m",
        "expected_cursor_floor": CURSOR_FLOOR,
    }
    payload.update(overrides)
    return CurrentProductiveGovernedCycleAuthorizationV1(**payload)  # type: ignore[arg-type]


def _occupancy_absent() -> dict[str, object]:
    return {
        "POSITIONS": {"code": "0", "data": []},
        "PENDING": {"code": "0", "data": []},
        "CONFIG": {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]},
    }


def _occupancy_present() -> dict[str, object]:
    absent = _occupancy_absent()
    absent["POSITIONS"] = {"code": "0", "data": [{"instId": NATIVE_ID, "pos": "1"}]}
    return absent


def _eg_stub(**_kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(permit_created="false", post_count="0")


def _t2_hold(**_kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(
        runtime_cycle_count="1",
        decision_result="OBSERVE_HOLD",
        decision_execution_eligible="false",
        master_v2_decision="observe",
        venue_plan_status="DENY",
        final_envelope_id="",
        final_envelope_digest="",
        permit_created="false",
        post_count="0",
        first_real_blocker="HOLD",
    )


def _t2_enter(**_kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(
        runtime_cycle_count="1",
        decision_result="EXECUTABLE_VENUE_PLAN_BOUND",
        decision_execution_eligible="true",
        master_v2_decision="enter",
        venue_plan_status="BOUND",
        final_envelope_id="env-fixture",
        final_envelope_digest="0" * 64,
        permit_created="false",
        post_count="0",
        first_real_blocker=POST_NEXT_OWNER_GO,
    )


def _run(tmp_path: Path, **kwargs):
    cursor_store = kwargs.pop("cursor_store_root", None)
    if cursor_store is None:
        cursor_store = _seed_cursor(tmp_path, event_time=CURSOR_FLOOR)
    return run_current_productive_governed_cycle_v1(
        authorization=kwargs.pop("authorization", _auth()),
        origin_main_sha=kwargs.pop("origin_main_sha", ORIGIN_SHA),
        cursor_store_root=cursor_store,
        lock_root=kwargs.pop("lock_root", tmp_path / "lock"),
        evidence_root=kwargs.pop("evidence_root", tmp_path / "evidence"),
        candles_payload=kwargs.pop("candles_payload", _candles(last_ts_ms=int(NEW_C1 * 1000))),
        occupancy_payloads=kwargs.pop("occupancy_payloads", _occupancy_absent()),
        execute_network=kwargs.pop("execute_network", False),
        perform_get=kwargs.pop("perform_get", False),
        eg_cycle_dispatch=kwargs.pop("eg_cycle_dispatch", _eg_stub),
        t2_cycle_dispatch=kwargs.pop("t2_cycle_dispatch", _t2_hold),
    )


def _assert_zero_effect(result) -> None:
    assert result.post_count == 0
    assert result.external_effect_count == 0
    assert result.permit_created is False
    assert result.cursor_persisted is False


def _assert_post_guard() -> None:
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0


def test_created_flag_pins_and_docs() -> None:
    assert CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_CREATED is True
    assert FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY == (
        "ONE_CYCLE_ORCHESTRATION_TO_PRE_EXTERNAL_EFFECT_ONLY"
    )
    assert AUTONOMY_CAN_CHANGE_TRADING_LOGIC is False
    assert AUTONOMY_CAN_RESELECT_DOWNSTREAM is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert S5_V5_EXECUTE_NETWORK is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert RUNTIME_OWNER_GO != OWNER_GO
    assert RUNTIME_OWNER_GO != GET_OWNER_GO
    assert RUNTIME_OWNER_GO != EG_OWNER_GO
    assert RUNTIME_OWNER_GO != OCCUPANCY_OWNER_GO
    assert RUNTIME_OWNER_GO != T2_RUNTIME_OWNER_GO
    assert RUNTIME_OWNER_GO != POST_NEXT_OWNER_GO
    assert RUNTIME_OWNER_GO != REMAINDER_OWNER_GO
    assert (
        len({RUNTIME_OWNER_GO, GET_OWNER_GO, EG_OWNER_GO, OCCUPANCY_OWNER_GO, T2_RUNTIME_OWNER_GO})
        == 5
    )
    assert RUNTIME_OWNER_GO_STATUS == "DEFINED_NOT_CONSUMED"
    assert JOIN_SEAM_ID == "CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_SEAM_V1"
    bound = bind_s5_governed_cycle_orchestrator_offline_v1(owner_go=OWNER_GO)
    assert bound["disposition"] == DISPOSITION_PRESENT
    assert bound["runtime_owner_go"] == RUNTIME_OWNER_GO
    assert bound["remainder_is_consume_license"] == "false"
    assert (
        bind_s5_governed_cycle_orchestrator_offline_v1(owner_go=RUNTIME_OWNER_GO)["reason_code"]
        == REASON_OWNER_GO_MISMATCH
    )
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    source = OWNER_MODULE.read_text(encoding="utf-8")
    assert "EH.S5" in runbook
    assert THIS_SLICE in source
    assert "current_productive_governed_cycle_orchestrator_v1.py" in mot
    assert "docs_token:" in spec
    assert "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_V1" in spec
    assert JOIN_SEAM_ID in atlas
    assert "current_productive_governed_cycle_orchestrator_v1.py" in atlas
    assert "test_full_core_current_productive_governed_cycle_orchestrator_v1.py" in atlas
    assert (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1"
        not in source
    )
    assert "urlopen" not in source
    for path in PROTECTED_ALGORITHM_FILES:
        assert (REPO_ROOT / path).is_file()
    _assert_post_guard()


def test_persist_go_is_not_runtime_license(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_PERSIST_GO_NOT_RUNTIME_LICENSE,
    ):
        _run(tmp_path, authorization=_auth(cycle_owner_go=OWNER_GO))


def test_remainder_is_not_consume_license(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_REMAINDER_IS_NOT_CONSUME_LICENSE,
    ):
        _run(tmp_path, authorization=_auth(cycle_owner_go=REMAINDER_OWNER_GO))


def test_post_go_cannot_be_cycle_authorization(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_POST_GO_IN_CYCLE_AUTHORIZATION,
    ):
        _run(tmp_path, authorization=_auth(cycle_owner_go=POST_NEXT_OWNER_GO))


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_OWNER_GO_MISMATCH,
    ):
        _run(tmp_path, authorization=_auth(cycle_owner_go="OWNER_GO_WRONG"))


def test_identity_collapse_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_GO_IDENTITY_COLLAPSE,
    ):
        _run(tmp_path, authorization=_auth(get_owner_go=RUNTIME_OWNER_GO))


def test_subordinate_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_SUBORDINATE_GO_MISMATCH,
    ):
        _run(tmp_path, authorization=_auth(get_owner_go="OWNER_GO_WRONG_GET"))


def test_network_and_missing_injected_c1_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_NETWORK_NOT_AUTHORIZED,
    ):
        _run(tmp_path, execute_network=True)
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_NETWORK_NOT_AUTHORIZED,
    ):
        _run(tmp_path, perform_get=True)
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_INJECTED_C1_REQUIRED,
    ):
        _run(tmp_path, candles_payload=None)


def test_freshness_failure_does_not_consume_eg_occupancy_t2(tmp_path: Path) -> None:
    result = _run(tmp_path, candles_payload=_candles(last_ts_ms=int(CURSOR_FLOOR * 1000)))
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.terminal_class == "FRESHNESS_FAILURE"
    assert result.get_consumed is True
    assert result.eg_consumed is False
    assert result.occupancy_consumed is False
    assert result.t2_consumed is False
    assert result.eg_dispatch_count == 0
    assert result.t2_consume_count == 0
    _assert_zero_effect(result)
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_PARTIAL_NOT_RESUMABLE,
    ):
        _run(tmp_path, evidence_root=tmp_path / "evidence")


def test_occupancy_failure_does_not_consume_t2(tmp_path: Path) -> None:
    result = _run(tmp_path, occupancy_payloads=_occupancy_present())
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.terminal_class == "OCCUPANCY_FAILURE"
    assert result.get_consumed is True
    assert result.eg_consumed is True
    assert result.eg_dispatch_count == 1
    assert result.occupancy_consumed is True
    assert result.occupancy_disposition == "OCCUPANCY_PRESENT"
    assert result.t2_consumed is False
    assert result.t2_consume_count == 0
    _assert_zero_effect(result)


def test_t2_failure_is_partial_not_resumable(tmp_path: Path) -> None:
    def _boom(**_kwargs: object) -> SimpleNamespace:
        raise CurrentProductiveGovernedCycleOrchestratorError("T2_HOST_FAIL_CLOSED")

    result = _run(tmp_path, t2_cycle_dispatch=_boom)
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.terminal_class == "T2_FAILURE"
    assert result.eg_dispatch_count == 1
    assert result.occupancy_consumed is True
    assert result.t2_consumed is False
    _assert_zero_effect(result)
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_PARTIAL_NOT_RESUMABLE,
    ):
        _run(tmp_path, evidence_root=tmp_path / "evidence")


def test_hold_path_is_success_terminal_and_exactly_once(tmp_path: Path) -> None:
    eg_calls = {"n": 0}
    t2_calls = {"n": 0}

    def _eg(**kwargs: object) -> SimpleNamespace:
        eg_calls["n"] += 1
        return _eg_stub(**kwargs)

    def _t2(**kwargs: object) -> SimpleNamespace:
        t2_calls["n"] += 1
        return _t2_hold(**kwargs)

    result = _run(tmp_path, eg_cycle_dispatch=_eg, t2_cycle_dispatch=_t2)
    assert result.disposition == DISPOSITION_HOLD
    assert result.terminal_class == "MARKET_STATE_REQUIRED"
    assert result.get_consume_count == 1
    assert result.eg_dispatch_count == 1
    assert result.t2_consume_count == 1
    assert result.runtime_cycle_count == 1
    assert result.occupancy_disposition == "OCCUPANCY_ABSENT"
    assert result.cycle_go_status_after == "CONSUMED_THIS_CYCLE_ONLY"
    assert REMAINDER_OWNER_GO in result.next_required_owner_decision
    assert (
        POST_NEXT_OWNER_GO not in result.next_required_owner_decision
        or "not a consume" in result.next_required_owner_decision.lower()
    )
    assert "POST unauthorized" in result.next_required_owner_decision
    _assert_zero_effect(result)
    assert eg_calls["n"] == 1
    assert t2_calls["n"] == 1
    trans = (
        (tmp_path / "evidence" / "transitions.jsonl")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert trans
    with pytest.raises(
        CurrentProductiveGovernedCycleOrchestratorError,
        match=REASON_REPLAY,
    ):
        _run(
            tmp_path,
            evidence_root=tmp_path / "evidence",
            eg_cycle_dispatch=_eg,
            t2_cycle_dispatch=_t2,
        )
    assert eg_calls["n"] == 1
    assert t2_calls["n"] == 1


def test_natural_executable_stops_at_pre_external_effect(tmp_path: Path) -> None:
    result = _run(tmp_path, t2_cycle_dispatch=_t2_enter)
    assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.terminal_class == "PRE_EXTERNAL_EFFECT"
    assert result.t2_consume_count == 1
    assert result.envelope_created is True
    assert POST_NEXT_OWNER_GO in result.next_required_owner_decision
    assert "does not compose POST" in result.next_required_owner_decision
    _assert_zero_effect(result)
    _assert_post_guard()


def test_default_t2_dispatch_is_not_direct_v5(tmp_path: Path) -> None:
    result = _run(tmp_path, t2_cycle_dispatch=None)
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.terminal_class == "T2_FAILURE"
    assert result.reason_code == "T2_CYCLE_DISPATCH_REQUIRED_OFFLINE_NO_DIRECT_V5"
    assert result.t2_consumed is False
    _assert_zero_effect(result)


def test_cursor_filename_and_zero_post_pins(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert CURSOR_FILENAME
    assert CURSOR_LINEAGE_ID
    assert result.ledger_state == "COMPLETED"
    assert DISPOSITION_COMPLETED != DISPOSITION_FAIL_CLOSED
    assert inspect.isfunction(run_current_productive_governed_cycle_v1)
    _assert_zero_effect(result)
    _assert_post_guard()
