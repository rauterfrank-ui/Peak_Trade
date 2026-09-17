"""CURRENT_PRODUCTIVE next-C1 trigger and exactly-one cycle orchestration. No POST."""

from __future__ import annotations

import inspect
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_NOT_CALLED_HOLD,
    STATUS_PASS,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    AUTONOMY_CAN_CHANGE_TRADING_LOGIC,
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    AUTONOMY_CAN_RESELECT_DOWNSTREAM,
    CYCLE_EXCLUSION_LOCK_NAME,
    DISPOSITION_DISPATCHED,
    DISPOSITION_FAILED_STOP,
    DISPOSITION_NO_DISPATCH,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
    JOIN_SEAM_ID,
    OWNER_GO,
    REASON_CONCURRENT_CYCLE,
    REASON_CURSOR_MISSING,
    REASON_CYCLE_EXCEPTION,
    REASON_DISPATCHED,
    REASON_DUPLICATE_C1,
    REASON_LINEAGE_MISMATCH,
    REASON_OWNER_GO_MISMATCH,
    REASON_PERSIST_GO_NOT_TRIGGER_LICENSE,
    REASON_STALE_C1,
    REASON_UNFINALIZED_C1,
    RUNTIME_TRIGGER_OWNER_GO,
    STATE_CYCLE_COMPLETED,
    STATE_CYCLE_IN_PROGRESS,
    STATE_FAILED_STOP,
    STATE_IDLE,
    STATE_NEW_C1_ACCEPTED,
    THIS_SLICE,
    CurrentProductiveC1ObservationV1,
    CurrentProductiveGovernedNextC1OrchestrationError,
    trigger_current_productive_next_c1_and_exactly_one_cycle_v1,
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
    CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V5_CREATED,
)
from src.ops.single_selected_future_policy_v1.constants_v1 import (
    WRITER_LOCK_FILENAME as CAP23_WRITER_LOCK_FILENAME,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    DISTINCTIVE_EQUITY,
    _balance_payload,
    _injected,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 import (
    _eligible_transport,
    _fresh_get_transport,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    TRACKED_CURSOR,
    _candles,
    _declared_checkout_sha,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
OWNER_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1.py"
)
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
SEALED_CORE_MEMBERS = (
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
CURSOR_C1_FLOOR = 1789527780.0
NEW_C1 = 1789527840.0
EG_HEADING = (
    "### 11.2.1.EG FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_"
    "AND_EXACTLY_ONE_CYCLE_ORCHESTRATION"
)


def _seed_cursor(tmp_path: Path, *, event_time: float = CURSOR_C1_FLOOR) -> Path:
    payload = json.loads(TRACKED_CURSOR.read_text(encoding="utf-8"))
    payload["lineage_id"] = CURSOR_LINEAGE_ID
    payload["venue_native_id"] = "0G-USDT-SWAP"
    payload["schema_name"] = "current_productive_sidestate_confirmation_cursor.v1"
    payload["cap61_confirmation_state"]["observation_acceptance_state"][
        "last_accepted_observation_identity"
    ]["venue_event_time"] = event_time
    store = tmp_path / "cursor"
    store.mkdir(parents=True, exist_ok=True)
    (store / CURSOR_FILENAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return store


def _observation(
    *,
    venue_event_time: float = NEW_C1,
    confirm: str = "1",
    native_id: str = "0G-USDT-SWAP",
    bar: str = "1m",
    payload: dict[str, object] | None = None,
) -> CurrentProductiveC1ObservationV1:
    if payload is None:
        payload = _candles(last_ts_ms=int(venue_event_time * 1000))
    return CurrentProductiveC1ObservationV1(
        venue_event_time=venue_event_time,
        confirm=confirm,
        native_id=native_id,
        bar=bar,
        payload=payload,
    )


def _stub_result() -> SimpleNamespace:
    return SimpleNamespace(
        permit_created="false",
        post_count="0",
        master_v2_decision="observe",
        venue_plan_status="DENY",
        final_envelope_id="",
        runtime_cycle_count="1",
    )


def _trigger(tmp_path: Path, observation, **kwargs):
    cursor_store = kwargs.pop("cursor_store_root", None)
    if cursor_store is None:
        cursor_store = _seed_cursor(tmp_path)
    return trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=kwargs.pop("owner_go", RUNTIME_TRIGGER_OWNER_GO),
        origin_main_sha=kwargs.pop("origin_main_sha", _declared_checkout_sha()),
        observation=observation,
        cursor_store_root=cursor_store,
        lock_root=kwargs.pop("lock_root", tmp_path / "lock"),
        evidence_root=kwargs.pop("evidence_root", tmp_path / "evidence"),
        cycle_dispatch=kwargs.pop("cycle_dispatch", None),
        v5_kwargs=kwargs.pop("v5_kwargs", None),
    )


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
    assert (
        CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_CREATED
        is True
    )
    assert (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V5_CREATED
        is True
    )
    assert FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY == (
        "NEXT_C1_TRIGGER_AND_SINGLE_CYCLE_ORCHESTRATION_ONLY"
    )
    assert AUTONOMY_CAN_CHANGE_TRADING_LOGIC is False
    assert AUTONOMY_CAN_RESELECT_DOWNSTREAM is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert RUNTIME_TRIGGER_OWNER_GO != OWNER_GO
    assert JOIN_SEAM_ID == (
        "CURRENT_PRODUCTIVE_NEXT_C1_TRIGGER_AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_SEAM_V1"
    )
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert EG_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER" in mot
    assert "docs_token:" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_NEXT_C1_TRIGGER_"
        "AND_EXACTLY_ONE_CYCLE_ORCHESTRATION_V1"
    ) in spec
    assert JOIN_SEAM_ID in atlas
    for path in (*PROTECTED_ALGORITHM_FILES, *SEALED_CORE_MEMBERS):
        assert (REPO_ROOT / path).is_file()


def test_persist_go_is_not_runtime_trigger_license(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedNextC1OrchestrationError,
        match=REASON_PERSIST_GO_NOT_TRIGGER_LICENSE,
    ):
        _trigger(tmp_path, _observation(), owner_go=OWNER_GO)


def test_owner_go_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedNextC1OrchestrationError,
        match=REASON_OWNER_GO_MISMATCH,
    ):
        _trigger(tmp_path, _observation(), owner_go="WRONG")


def test_new_c1_single_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        assert kwargs["execute_network"] is False
        assert kwargs["incoming_cursor"] is not None
        transport = kwargs.get("acquisition_transport")
        assert transport is not None
        assert type(transport).__name__ == "UrllibEeaPublicUniverseGetTransportV1"
        assert getattr(transport, "request_count", 0) == 0
        return _stub_result()

    result = _trigger(tmp_path, _observation(), cycle_dispatch=_dispatch)
    assert result.disposition == DISPOSITION_DISPATCHED
    assert result.reason_code == REASON_DISPATCHED
    assert result.dispatch_count == 1
    assert len(calls) == 1
    assert STATE_NEW_C1_ACCEPTED in result.transitions
    assert STATE_CYCLE_IN_PROGRESS in result.transitions
    assert STATE_CYCLE_COMPLETED in result.transitions
    assert result.transitions[-1] == STATE_IDLE
    assert result.lock_released == "true"
    assert result.permit_created == "false"
    assert result.post_count == "0"


def test_duplicate_c1_no_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        return _stub_result()

    result = _trigger(
        tmp_path,
        _observation(venue_event_time=CURSOR_C1_FLOOR),
        cycle_dispatch=_dispatch,
    )
    assert result.disposition == DISPOSITION_NO_DISPATCH
    assert result.reason_code == REASON_DUPLICATE_C1
    assert result.dispatch_count == 0
    assert calls == []


def test_stale_c1_no_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        return _stub_result()

    result = _trigger(
        tmp_path,
        _observation(venue_event_time=CURSOR_C1_FLOOR - 60.0),
        cycle_dispatch=_dispatch,
    )
    assert result.disposition == DISPOSITION_NO_DISPATCH
    assert result.reason_code == REASON_STALE_C1
    assert result.dispatch_count == 0
    assert calls == []


def test_unfinalized_c1_no_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        return _stub_result()

    result = _trigger(
        tmp_path,
        _observation(confirm="0"),
        cycle_dispatch=_dispatch,
    )
    assert result.disposition == DISPOSITION_NO_DISPATCH
    assert result.reason_code == REASON_UNFINALIZED_C1
    assert result.dispatch_count == 0
    assert calls == []


def test_concurrent_trigger_exactly_one_accepted(tmp_path: Path) -> None:
    started = threading.Event()
    release = threading.Event()
    calls: list[str] = []
    lock_root = tmp_path / "lock"
    cursor_store = _seed_cursor(tmp_path)

    def _dispatch(**kwargs):
        calls.append("dispatch")
        started.set()
        assert release.wait(timeout=2.0) is True
        return _stub_result()

    first: dict[str, object] = {}
    second: dict[str, object] = {}

    def _run_first() -> None:
        first["result"] = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
            owner_go=RUNTIME_TRIGGER_OWNER_GO,
            origin_main_sha=_declared_checkout_sha(),
            observation=_observation(),
            cursor_store_root=cursor_store,
            lock_root=lock_root,
            evidence_root=tmp_path / "first",
            cycle_dispatch=_dispatch,
        )

    worker = threading.Thread(target=_run_first)
    worker.start()
    assert started.wait(timeout=2.0) is True
    second["result"] = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(),
        cursor_store_root=cursor_store,
        lock_root=lock_root,
        evidence_root=tmp_path / "second",
        cycle_dispatch=_dispatch,
    )
    release.set()
    worker.join(timeout=2.0)
    accepted = first["result"]
    rejected = second["result"]
    assert accepted.dispatch_count == 1
    assert accepted.disposition == DISPOSITION_DISPATCHED
    assert rejected.dispatch_count == 0
    assert rejected.reason_code == REASON_CONCURRENT_CYCLE
    assert rejected.disposition == DISPOSITION_NO_DISPATCH
    assert calls == ["dispatch"]


def test_cycle_exception_no_retry_cursor_not_advanced(tmp_path: Path) -> None:
    cursor_store = _seed_cursor(tmp_path)
    before = (cursor_store / CURSOR_FILENAME).read_text(encoding="utf-8")
    lock_root = tmp_path / "lock"

    def _boom(**kwargs):
        raise RuntimeError("injected-cycle-failure")

    failed = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(),
        cursor_store_root=cursor_store,
        lock_root=lock_root,
        evidence_root=tmp_path / "failed",
        cycle_dispatch=_boom,
    )
    assert failed.disposition == DISPOSITION_FAILED_STOP
    assert failed.reason_code == REASON_CYCLE_EXCEPTION
    assert failed.state == STATE_FAILED_STOP
    assert failed.lock_released == "false"
    assert (lock_root / CYCLE_EXCLUSION_LOCK_NAME).is_file()
    after = (cursor_store / CURSOR_FILENAME).read_text(encoding="utf-8")
    assert after == before
    retry_calls: list[object] = []

    def _retry(**kwargs):
        retry_calls.append(kwargs)
        return _stub_result()

    blocked = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(venue_event_time=NEW_C1 + 60.0),
        cursor_store_root=cursor_store,
        lock_root=lock_root,
        evidence_root=tmp_path / "retry",
        cycle_dispatch=_retry,
    )
    assert blocked.reason_code == REASON_CONCURRENT_CYCLE
    assert blocked.dispatch_count == 0
    assert retry_calls == []


def test_lineage_mismatch_no_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        return _stub_result()

    result = _trigger(
        tmp_path,
        _observation(native_id="BTC-USDT-SWAP"),
        cycle_dispatch=_dispatch,
    )
    assert result.disposition == DISPOSITION_NO_DISPATCH
    assert result.reason_code == REASON_LINEAGE_MISMATCH
    assert result.dispatch_count == 0
    assert calls == []


def test_cursor_missing_no_dispatch(tmp_path: Path) -> None:
    calls: list[object] = []

    def _dispatch(**kwargs):
        calls.append(kwargs)
        return _stub_result()

    empty = tmp_path / "empty-cursor"
    empty.mkdir()
    result = _trigger(
        tmp_path,
        _observation(),
        cursor_store_root=empty,
        cycle_dispatch=_dispatch,
    )
    assert result.reason_code == REASON_CURSOR_MISSING
    assert result.dispatch_count == 0
    assert calls == []


def _v5_join_kwargs(tmp_path: Path, **extra: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "incoming_cursor": None,
        "cursor_store_root": tmp_path / "v5-empty-cursor",
        "acquisition_transport": _eligible_transport(),
        "fresh_get_transport": _fresh_get_transport(),
        "producer_observed_at_unix": 1_700_000_100.0,
    }
    kwargs.update(extra)
    return kwargs


def test_hold_cycle_skips_29p_reaches_pre_external_effect(tmp_path: Path) -> None:
    cursor_store = _seed_cursor(tmp_path)
    result = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(),
        cursor_store_root=cursor_store,
        lock_root=tmp_path / "lock",
        evidence_root=tmp_path / "hold",
        v5_kwargs=_v5_join_kwargs(tmp_path / "hold-v5"),
    )
    assert result.disposition == DISPOSITION_DISPATCHED
    assert result.dispatch_count == 1
    cycle = result.cycle_result
    assert cycle is not None
    claims = json.loads((Path(cycle.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert claims["STEP_29P_GET_COUNT"] == "0"
    assert claims["STEP_29P_JOIN_STATUS"] == STATUS_NOT_CALLED_HOLD
    assert claims["LIVE_29P_GET_CONSUMED"] == "false"
    assert claims["PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED"] == "true"
    assert cycle.post_count == "0"
    assert cycle.permit_created == "false"
    assert cycle.final_envelope_id == ""
    assert result.permit_created == "false"
    assert result.post_count == "0"
    _assert_post_guard()


def test_enter_live_29p_guard_and_fail_closes_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, cycle_b, _path = _host_enter_cycle()
    monkeypatch.setattr(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5."
        "run_current_productive_master_v2_runtime_cycle_v1",
        lambda **_kwargs: cycle_b,
    )
    missing_cursor = _seed_cursor(tmp_path / "missing-cursor-root")
    missing = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(),
        cursor_store_root=missing_cursor,
        lock_root=tmp_path / "lock-missing",
        evidence_root=tmp_path / "enter-missing",
        v5_kwargs=_v5_join_kwargs(tmp_path / "enter-missing-v5"),
    )
    missing_cycle = missing.cycle_result
    assert missing_cycle is not None
    missing_claims = json.loads(
        (Path(missing_cycle.store_root) / "claims.json").read_text(encoding="utf-8")
    )
    assert missing_claims["STEP_29P_JOIN_STATUS"] != STATUS_PASS
    assert missing_claims["USED_OFFLINE_DEFAULT_EQUITY"] == "false"
    assert missing_cycle.venue_plan_status == "DENY"
    assert missing_cycle.envelope_readiness == "false"
    assert missing_cycle.final_envelope_id == ""
    assert missing_cycle.post_count == "0"
    assert missing_cycle.permit_created == "false"

    passed_cursor = _seed_cursor(tmp_path / "pass-cursor-root")
    passed = trigger_current_productive_next_c1_and_exactly_one_cycle_v1(
        owner_go=RUNTIME_TRIGGER_OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        observation=_observation(),
        cursor_store_root=passed_cursor,
        lock_root=tmp_path / "lock-pass",
        evidence_root=tmp_path / "enter-pass",
        v5_kwargs=_v5_join_kwargs(
            tmp_path / "enter-pass-v5",
            enter_live_29p_injected=_injected(payload=_balance_payload()),
        ),
    )
    passed_cycle = passed.cycle_result
    assert passed_cycle is not None
    pass_claims = json.loads(
        (Path(passed_cycle.store_root) / "claims.json").read_text(encoding="utf-8")
    )
    assert pass_claims["STEP_29P_GET_COUNT"] == "1"
    assert pass_claims["LIVE_29P_GET_CONSUMED"] == "true"
    assert pass_claims["STEP_29P_JOIN_STATUS"] == STATUS_PASS
    assert pass_claims["LIVE_29P_PRODUCER_OUTPUT_VALUE"] == DISTINCTIVE_EQUITY
    assert pass_claims["USED_OFFLINE_DEFAULT_EQUITY"] == "false"
    assert passed_cycle.post_count == "0"
    assert passed_cycle.permit_created == "false"
    _assert_post_guard()


def test_authority_guard_cannot_mint_permit_or_post() -> None:
    source = OWNER_MODULE.read_text(encoding="utf-8")
    assert "issue_external_effect_permit_v1" not in source
    assert "post_trade_order" not in source
    assert "while True" not in source
    assert "time.sleep" not in source
    assert 'execute_network": True' not in source
    assert "execute_network = True" not in source
    assert CAP23_WRITER_LOCK_FILENAME not in source
    assert CYCLE_EXCLUSION_LOCK_NAME in source
    assert "AuthorizationLifecycleLockV1" in source
    inspected = inspect.getsource(trigger_current_productive_next_c1_and_exactly_one_cycle_v1)
    assert "issue_external_effect_permit_v1" not in inspected
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    _assert_post_guard()
