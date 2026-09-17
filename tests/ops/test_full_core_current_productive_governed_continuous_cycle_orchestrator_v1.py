"""CURRENT_PRODUCTIVE governed continuous-cycle sequencer. No POST. No network."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    AUTONOMY_CAN_CHANGE_TRADING_LOGIC,
    AUTONOMY_CAN_FORCE_ENTER,
    AUTONOMY_CAN_MINT_PERMIT,
    AUTONOMY_CAN_POST,
    AUTONOMY_CAN_RESELECT_DOWNSTREAM,
    BOUNDS_CLASS,
    CONTINUOUS_RUN_AUTHORIZED,
    CONTINUOUS_RUN_EXECUTED,
    DEFAULT_MAX_CYCLES_PER_RUN,
    DEFAULT_MAX_RUN_DURATION_SECONDS,
    DISPOSITION_CANCELLED,
    DISPOSITION_FAIL_CLOSED,
    DISPOSITION_HOLD_CONTINUE,
    DISPOSITION_MAX_CYCLES,
    DISPOSITION_MAX_DURATION,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
    DISPOSITION_PRESENT,
    DISPOSITION_STALL,
    FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY,
    HARD_CAP_MAX_CYCLES_PER_RUN,
    HARD_CAP_MAX_RUN_DURATION_SECONDS,
    JOIN_SEAM_ID,
    OWNER_GO,
    POST_COMPOSED_INTO_CONTINUOUS_GO,
    REASON_CONSUME_INSTANCE_REUSE,
    REASON_EXCEEDS_HARD_CAP,
    REASON_INJECTED_SOURCE_REQUIRED,
    REASON_NETWORK_NOT_AUTHORIZED,
    REASON_OWNER_GO_MISMATCH,
    REASON_PARTIAL_NOT_RESUMABLE,
    REASON_PERSIST_GO_NOT_RUNTIME_LICENSE,
    REASON_POST_GO_IN_CONTINUOUS_AUTHORIZATION,
    REASON_REPLAY,
    REASON_S5_GO_IS_NOT_CONTINUOUS_GO,
    REASON_STALE_OR_EQUAL_C1,
    REASON_UNBOUNDED_OR_INVALID_BOUND,
    RUNTIME_OWNER_GO,
    RUNTIME_OWNER_GO_STATUS,
    S6_V5_EXECUTE_NETWORK,
    THIS_SLICE,
    CurrentProductiveGovernedContinuousCycleOrchestratorError,
    CurrentProductiveGovernedContinuousCycleRunAuthorizationV1,
    InjectedContinuousObservationV1,
    ScriptedContinuousObservationSourceV1,
    bind_s6_governed_continuous_cycle_orchestrator_offline_v1,
    mint_continuous_run_id_v1,
    mint_s5_cycle_consume_instance_id_v1,
    run_current_productive_governed_continuous_cycle_run_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD as S5_DISPOSITION_HOLD,
    OWNER_GO as S5_PERSIST_GO,
    RUNTIME_OWNER_GO as S5_RUNTIME_OWNER_GO,
    S5_V5_EXECUTE_NETWORK,
    run_current_productive_governed_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_CREATED,
    CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    _eg_stub,
    _occupancy_absent,
    _occupancy_present,
    _t2_enter,
    _t2_hold,
)
from tests.ops.test_full_core_current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    _seed_cursor,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    _candles,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
OWNER_MODULE = (
    REPO_ROOT
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_governed_continuous_cycle_orchestrator_v1.py"
)
S5_MODULE = (
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
EH_S6_HEADING = "### 11.2.1.EH S6 GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_OFFLINE_BIND"
CURSOR_FLOOR = 1789667940.0
C1_A = 1789668000.0
C1_B = 1789668060.0
C1_C = 1789668120.0
NATIVE_ID = "0G-USDT-SWAP"
ORIGIN_SHA = "e93495de691455d8f27a269452ca0833e9fd6724"


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(float(seconds))
        self.now += float(seconds)


def _auth(**overrides: object) -> CurrentProductiveGovernedContinuousCycleRunAuthorizationV1:
    payload = {
        "continuous_owner_go": RUNTIME_OWNER_GO,
        "native_id": NATIVE_ID,
        "bar": "1m",
        "expected_cursor_floor": CURSOR_FLOOR,
        "max_cycles_per_run": 2,
        "max_run_duration_seconds": 90.0,
        "wait_interval_seconds": 1.0,
        "max_wait_for_next_c1_seconds": 30.0,
        "stall_seconds": 30.0,
    }
    payload.update(overrides)
    return CurrentProductiveGovernedContinuousCycleRunAuthorizationV1(**payload)  # type: ignore[arg-type]


def _obs(
    event_time: float, occupancy: dict[str, object] | None = None
) -> InjectedContinuousObservationV1:
    return InjectedContinuousObservationV1(
        candles_payload=_candles(last_ts_ms=int(event_time * 1000)),
        occupancy_payloads=occupancy if occupancy is not None else _occupancy_absent(),
    )


def _source(
    *steps: InjectedContinuousObservationV1 | None,
) -> ScriptedContinuousObservationSourceV1:
    return ScriptedContinuousObservationSourceV1(steps)


def _run(tmp_path: Path, **kwargs):
    cursor_store = kwargs.pop("cursor_store_root", None)
    if cursor_store is None:
        cursor_store = _seed_cursor(tmp_path, event_time=CURSOR_FLOOR)
    clock = kwargs.pop("clock", None)
    if clock is None:
        clock = _FakeClock()
    return run_current_productive_governed_continuous_cycle_run_v1(
        authorization=kwargs.pop("authorization", _auth()),
        origin_main_sha=kwargs.pop("origin_main_sha", ORIGIN_SHA),
        cursor_store_root=cursor_store,
        lock_root=kwargs.pop("lock_root", tmp_path / "lock"),
        evidence_root=kwargs.pop("evidence_root", tmp_path / "evidence"),
        observation_source=kwargs.pop("observation_source", _source(_obs(C1_A))),
        execute_network=kwargs.pop("execute_network", False),
        perform_get=kwargs.pop("perform_get", False),
        eg_cycle_dispatch=kwargs.pop("eg_cycle_dispatch", _eg_stub),
        t2_cycle_dispatch=kwargs.pop("t2_cycle_dispatch", _t2_hold),
        s5_runner=kwargs.pop("s5_runner", run_current_productive_governed_cycle_v1),
        time_fn=clock.time,
        sleep_fn=clock.sleep,
        cancel_requested=kwargs.pop("cancel_requested", None),
    )


def _assert_zero_effect(result) -> None:
    assert result.post_count == 0
    assert result.external_effect_count == 0
    assert result.permit_created is False


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
    assert CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_CREATED is True
    assert CURRENT_PRODUCTIVE_GOVERNED_CYCLE_ORCHESTRATOR_CREATED is True
    assert FULL_CORE_AUTONOMY_AUTHORITY_BOUNDARY == (
        "BOUNDED_CONTINUOUS_SEQUENCING_TO_PRE_EXTERNAL_EFFECT_ONLY"
    )
    assert AUTONOMY_CAN_CHANGE_TRADING_LOGIC is False
    assert AUTONOMY_CAN_RESELECT_DOWNSTREAM is False
    assert AUTONOMY_CAN_MINT_PERMIT is False
    assert AUTONOMY_CAN_POST is False
    assert AUTONOMY_CAN_FORCE_ENTER is False
    assert POST_COMPOSED_INTO_CONTINUOUS_GO is False
    assert CONTINUOUS_RUN_AUTHORIZED is False
    assert CONTINUOUS_RUN_EXECUTED is False
    assert S6_V5_EXECUTE_NETWORK is False
    assert S5_V5_EXECUTE_NETWORK is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert RUNTIME_OWNER_GO != OWNER_GO
    assert RUNTIME_OWNER_GO != S5_RUNTIME_OWNER_GO
    assert RUNTIME_OWNER_GO != S5_PERSIST_GO
    assert RUNTIME_OWNER_GO != POST_NEXT_OWNER_GO
    assert RUNTIME_OWNER_GO_STATUS == "DEFINED_NOT_CONSUMED"
    assert JOIN_SEAM_ID == "CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_SEAM_V1"
    assert DEFAULT_MAX_CYCLES_PER_RUN == 2
    assert HARD_CAP_MAX_CYCLES_PER_RUN == 4
    assert DEFAULT_MAX_RUN_DURATION_SECONDS == 90.0
    assert HARD_CAP_MAX_RUN_DURATION_SECONDS == 180.0
    assert BOUNDS_CLASS == "VALIDATION_DEFAULTS_NOT_PRODUCTIVE_POLICY"
    bound = bind_s6_governed_continuous_cycle_orchestrator_offline_v1(owner_go=OWNER_GO)
    assert bound["disposition"] == DISPOSITION_PRESENT
    assert bound["runtime_owner_go"] == RUNTIME_OWNER_GO
    assert bound["continuous_run_authorized"] == "false"
    assert (
        bind_s6_governed_continuous_cycle_orchestrator_offline_v1(owner_go=RUNTIME_OWNER_GO)[
            "reason_code"
        ]
        == REASON_OWNER_GO_MISMATCH
    )
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    source = OWNER_MODULE.read_text(encoding="utf-8")
    s5_source = S5_MODULE.read_text(encoding="utf-8")
    assert EH_S6_HEADING in runbook
    assert THIS_SLICE in runbook
    assert "FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR" in mot
    assert "docs_token:" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_ORCHESTRATOR_V1" in spec
    )
    assert JOIN_SEAM_ID in atlas
    assert "current_productive_governed_continuous_cycle_orchestrator_v1.py" in atlas
    assert "test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1.py" in atlas
    assert "run_current_productive_governed_cycle_v1" in source
    assert "urlopen" not in source
    assert (
        "execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1"
        not in source
    )
    assert RUNTIME_OWNER_GO not in s5_source
    assert inspect.isfunction(run_current_productive_governed_cycle_v1)
    for path in PROTECTED_ALGORITHM_FILES:
        assert (REPO_ROOT / path).is_file()
    _assert_post_guard()


def test_hold_then_next_fresh_c1_allowed(tmp_path: Path) -> None:
    t2_calls = {"n": 0}

    def _t2(**kwargs: object) -> SimpleNamespace:
        t2_calls["n"] += 1
        return _t2_hold(**kwargs)

    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), None, _obs(C1_B)),
        t2_cycle_dispatch=_t2,
        authorization=_auth(max_cycles_per_run=2),
    )
    assert result.disposition == DISPOSITION_MAX_CYCLES
    assert result.cycles_completed == 2
    assert result.s5_invoke_count == 2
    assert t2_calls["n"] == 2
    assert result.cycle_records[0].c1_venue_event_time == C1_A
    assert result.cycle_records[1].c1_venue_event_time == C1_B
    assert result.cycle_records[0].s5_disposition == S5_DISPOSITION_HOLD
    assert result.cycle_records[1].s5_disposition == S5_DISPOSITION_HOLD
    assert result.cursor_floor_after == C1_B
    assert result.cursor_floor_after > result.cursor_floor_before
    _assert_zero_effect(result)


def test_multiple_holds_use_distinct_consume_instances(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), None, _obs(C1_B)),
        authorization=_auth(max_cycles_per_run=2),
    )
    ids = result.consume_instance_ids
    assert len(ids) == 2
    assert ids[0] != ids[1]
    assert result.cycle_records[0].evidence_root != result.cycle_records[1].evidence_root
    assert result.cycle_records[0].sequencing_owner_go == S5_RUNTIME_OWNER_GO
    assert result.cycle_records[1].get_owner_go == result.cycle_records[0].get_owner_go


def test_consumed_s5_instance_never_reused(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), None, _obs(C1_B)),
        authorization=_auth(max_cycles_per_run=2),
    )
    assert len(result.consume_instance_ids) == 2
    assert len(set(result.consume_instance_ids)) == 2
    roots = [record.evidence_root for record in result.cycle_records]
    assert len(set(roots)) == 2
    _assert_zero_effect(result)


def test_second_cycle_reuse_of_consumed_instance_stops(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ids = {"n": 0}

    def _mint(*, run_id: str, cycle_index: int, c1_venue_event_time: float) -> str:
        ids["n"] += 1
        if ids["n"] == 1:
            return mint_s5_cycle_consume_instance_id_v1(
                run_id=run_id,
                cycle_index=cycle_index,
                c1_venue_event_time=c1_venue_event_time,
            )
        return mint_s5_cycle_consume_instance_id_v1(
            run_id=run_id,
            cycle_index=1,
            c1_venue_event_time=C1_A,
        )

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1.mint_s5_cycle_consume_instance_id_v1",
        _mint,
    )
    s5_calls = {"n": 0}

    def _runner(**kwargs: object):
        s5_calls["n"] += 1
        return run_current_productive_governed_cycle_v1(**kwargs)

    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), None, _obs(C1_B)),
        s5_runner=_runner,
        authorization=_auth(max_cycles_per_run=2),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.reason_code == REASON_CONSUME_INSTANCE_REUSE
    assert s5_calls["n"] == 1
    _assert_zero_effect(result)


def test_stale_or_equal_c1_rejected_without_s5(tmp_path: Path) -> None:
    s5_calls = {"n": 0}

    def _runner(**kwargs: object):
        s5_calls["n"] += 1
        return run_current_productive_governed_cycle_v1(**kwargs)

    result = _run(
        tmp_path,
        observation_source=_source(_obs(CURSOR_FLOOR)),
        s5_runner=_runner,
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.reason_code == REASON_STALE_OR_EQUAL_C1
    assert result.s5_invoke_count == 0
    assert s5_calls["n"] == 0
    _assert_zero_effect(result)


def test_enter_stops_at_pre_external_effect_and_no_subsequent_cycle(tmp_path: Path) -> None:
    t2_calls = {"n": 0}

    def _t2(**kwargs: object) -> SimpleNamespace:
        t2_calls["n"] += 1
        return _t2_enter(**kwargs)

    source = _source(_obs(C1_A), _obs(C1_B), _obs(C1_C))
    result = _run(
        tmp_path,
        observation_source=source,
        t2_cycle_dispatch=_t2,
        authorization=_auth(max_cycles_per_run=3),
    )
    assert result.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
    assert result.terminal_class == "PRE_EXTERNAL_EFFECT"
    assert result.cycles_completed == 1
    assert result.s5_invoke_count == 1
    assert t2_calls["n"] == 1
    assert POST_NEXT_OWNER_GO in result.next_required_owner_decision
    assert "does not compose" in result.next_required_owner_decision
    assert source.poll_count == 1
    _assert_zero_effect(result)
    _assert_post_guard()


def test_failure_stops_run(tmp_path: Path) -> None:
    def _boom(**_kwargs: object) -> SimpleNamespace:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
            CurrentProductiveGovernedCycleOrchestratorError,
        )

        raise CurrentProductiveGovernedCycleOrchestratorError("T2_HOST_FAIL_CLOSED")

    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), _obs(C1_B)),
        t2_cycle_dispatch=_boom,
        authorization=_auth(max_cycles_per_run=2),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.cycles_completed == 1
    assert result.s5_invoke_count == 1
    assert result.reason_code == "T2_HOST_FAIL_CLOSED"
    _assert_zero_effect(result)


def test_occupancy_blocker_stops_run(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A, occupancy=_occupancy_present()), _obs(C1_B)),
        authorization=_auth(max_cycles_per_run=2),
    )
    assert result.disposition == DISPOSITION_FAIL_CLOSED
    assert result.terminal_class == "OCCUPANCY_FAILURE"
    assert result.cycles_completed == 1
    assert result.s5_invoke_count == 1
    _assert_zero_effect(result)


def test_partial_cycle_cannot_resume(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    first = _run(
        tmp_path,
        evidence_root=evidence,
        observation_source=_source(_obs(C1_A, occupancy=_occupancy_present())),
    )
    assert first.disposition == DISPOSITION_FAIL_CLOSED
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_PARTIAL_NOT_RESUMABLE,
    ):
        _run(
            tmp_path,
            evidence_root=evidence,
            cursor_store_root=_seed_cursor(tmp_path / "cursor2", event_time=CURSOR_FLOOR),
            observation_source=_source(_obs(C1_B)),
        )


def test_replay_rejected(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    first = _run(
        tmp_path,
        evidence_root=evidence,
        observation_source=_source(_obs(C1_A)),
        authorization=_auth(max_cycles_per_run=1),
    )
    assert first.disposition == DISPOSITION_MAX_CYCLES
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_REPLAY,
    ):
        _run(
            tmp_path,
            evidence_root=evidence,
            observation_source=_source(_obs(C1_B)),
            authorization=_auth(max_cycles_per_run=1),
        )


def test_max_cycle_bound_stops(tmp_path: Path) -> None:
    t2_calls = {"n": 0}

    def _t2(**kwargs: object) -> SimpleNamespace:
        t2_calls["n"] += 1
        return _t2_hold(**kwargs)

    result = _run(
        tmp_path,
        observation_source=_source(_obs(C1_A), _obs(C1_B), _obs(C1_C)),
        t2_cycle_dispatch=_t2,
        authorization=_auth(max_cycles_per_run=1),
    )
    assert result.disposition == DISPOSITION_MAX_CYCLES
    assert result.cycles_completed == 1
    assert t2_calls["n"] == 1
    _assert_zero_effect(result)


def test_max_duration_and_stall_bounds_stop(tmp_path: Path) -> None:
    duration = _run(
        tmp_path,
        observation_source=_source(None, None, None, None, None),
        authorization=_auth(
            max_run_duration_seconds=3.0,
            stall_seconds=60.0,
            max_wait_for_next_c1_seconds=60.0,
            wait_interval_seconds=1.0,
        ),
    )
    assert duration.disposition == DISPOSITION_MAX_DURATION
    assert duration.s5_invoke_count == 0
    stall = _run(
        tmp_path,
        evidence_root=tmp_path / "stall",
        cursor_store_root=_seed_cursor(tmp_path / "stall_cursor", event_time=CURSOR_FLOOR),
        observation_source=_source(None, None, None, None, None),
        authorization=_auth(
            max_run_duration_seconds=90.0,
            stall_seconds=2.0,
            max_wait_for_next_c1_seconds=60.0,
            wait_interval_seconds=1.0,
        ),
    )
    assert stall.disposition == DISPOSITION_STALL
    assert stall.s5_invoke_count == 0
    _assert_zero_effect(duration)
    _assert_zero_effect(stall)


def test_cancellation_is_terminal_and_auditable(tmp_path: Path) -> None:
    evidence = tmp_path / "cancel"
    result = _run(
        tmp_path,
        evidence_root=evidence,
        observation_source=_source(_obs(C1_A), None, _obs(C1_B)),
        cancel_requested=lambda: True,
        authorization=_auth(max_cycles_per_run=2),
    )
    assert result.disposition == DISPOSITION_CANCELLED
    assert result.ledger_state == "CANCELLED_STOP"
    ledger = json.loads((evidence / "governed_continuous_cycle_run_ledger_v1.json").read_text())
    assert ledger["state"] == "CANCELLED_STOP"
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_REPLAY,
    ):
        _run(
            tmp_path,
            evidence_root=evidence,
            observation_source=_source(_obs(C1_B)),
        )
    _assert_zero_effect(result)


def test_post_go_rejected_as_continuous_go(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_POST_GO_IN_CONTINUOUS_AUTHORIZATION,
    ):
        _run(tmp_path, authorization=_auth(continuous_owner_go=POST_NEXT_OWNER_GO))
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_S5_GO_IS_NOT_CONTINUOUS_GO,
    ):
        _run(tmp_path, authorization=_auth(continuous_owner_go=S5_RUNTIME_OWNER_GO))
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_PERSIST_GO_NOT_RUNTIME_LICENSE,
    ):
        _run(tmp_path, authorization=_auth(continuous_owner_go=OWNER_GO))
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_OWNER_GO_MISMATCH,
    ):
        _run(tmp_path, authorization=_auth(continuous_owner_go="OWNER_GO_WRONG"))


def test_post_permit_and_network_pins(tmp_path: Path) -> None:
    result = _run(
        tmp_path, observation_source=_source(_obs(C1_A)), authorization=_auth(max_cycles_per_run=1)
    )
    _assert_zero_effect(result)
    assert result.post_count == 0
    assert result.permit_created is False
    assert result.external_effect_count == 0
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_NETWORK_NOT_AUTHORIZED,
    ):
        _run(tmp_path, execute_network=True)
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_NETWORK_NOT_AUTHORIZED,
    ):
        _run(tmp_path, perform_get=True)
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_INJECTED_SOURCE_REQUIRED,
    ):
        _run(tmp_path, observation_source=None)
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_UNBOUNDED_OR_INVALID_BOUND,
    ):
        _run(tmp_path, authorization=_auth(max_cycles_per_run=0))
    with pytest.raises(
        CurrentProductiveGovernedContinuousCycleOrchestratorError,
        match=REASON_EXCEEDS_HARD_CAP,
    ):
        _run(tmp_path, authorization=_auth(max_cycles_per_run=HARD_CAP_MAX_CYCLES_PER_RUN + 1))
    _assert_post_guard()


def test_no_busy_loop_sleeps_on_empty_poll(tmp_path: Path) -> None:
    clock = _FakeClock()
    _run(
        tmp_path,
        clock=clock,
        observation_source=_source(None, None, _obs(C1_A)),
        authorization=_auth(
            max_cycles_per_run=1, stall_seconds=60.0, max_run_duration_seconds=90.0
        ),
    )
    assert clock.sleeps
    assert all(pause > 0 for pause in clock.sleeps)


def test_protected_trading_surfaces_unmodified_by_this_module() -> None:
    source = OWNER_MODULE.read_text(encoding="utf-8")
    assert "double_play_state" not in source
    assert "double_play_entry_exit_policy" not in source
    assert "learning_loop" not in source
    assert DISPOSITION_HOLD_CONTINUE
    _assert_post_guard()
