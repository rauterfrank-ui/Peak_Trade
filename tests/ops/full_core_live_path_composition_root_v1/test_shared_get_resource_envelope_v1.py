"""Actual polling/pretrade call costs against the original transport fuse.

All network, signing and acquisition clocks are local test doubles. This tests
charged attempts, not live operation or a full G17/Core/host reconstruction.
"""

import pytest

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import (
    ENDPOINT_PUBLIC_MARK_PRICE,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_get_budget_contract_v1 import (
    compute_max_canonical_continuous_poll_iterations_v1,
    compute_worst_case_legitimate_shared_transport_charged_gets_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_live_fresh_c1_continuous_observation_source_v1 import (
    LiveFreshC1ContinuousObservationSourceV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_INDEX_TICKERS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetError,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_index_tickers_payload_v1,
    okx_public_mark_price_payload_v1,
)
from tests.ops.test_current_productive_s6_live_fresh_c1_mark_attachment_v1 import CANDLES
from tests.ops.test_full_core_current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1 import (
    _seed_cursor,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _bound,
    _identity_payloads,
)
from tests.ops.test_pretrade_acquisition_freshness_v1 import local_wire  # noqa: F401
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    compose_current_productive_29p_common_epoch_handoff_v1,
)

NATIVE = "0G-USDT-SWAP"


def _routes(state, *, embedded_index):
    state["payloads"] = _identity_payloads(instrument_id=NATIVE)
    state["payloads"][GET_PATH] = CANDLES
    mark = okx_public_mark_price_payload_v1(native_id=NATIVE, mark_px=3500, index_px=3490)
    if not embedded_index:
        del mark["data"][0]["idxPx"]
    state["payloads"][ENDPOINT_PUBLIC_MARK_PRICE] = mark
    state["payloads"][f"{ENDPOINT_MARKET_INDEX_TICKERS}#instId=0G-USDT"] = (
        okx_index_tickers_payload_v1(index_inst_id="0G-USDT", index_px=3490)
    )


def _source(tmp_path, transport, *, warm=True):
    cursor = _seed_cursor(tmp_path, event_time=0.0) if warm else tmp_path / "cold"
    return LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=tmp_path / "evidence",
        run_id=tmp_path.name,
        native_id=NATIVE,
        transport=transport,
    )


@pytest.mark.parametrize("embedded_index,cost", [(True, 2), (False, 3)])
def test_actual_poll_cost_includes_conditional_fresh_index(
    tmp_path, local_wire, embedded_index, cost
):
    state, transport = local_wire
    _routes(state, embedded_index=embedded_index)
    source = _source(tmp_path, transport)
    assert source.poll() is not None
    assert source.poll() is not None
    assert transport.request_count == len(state["calls"]) == 2 * cost
    index_calls = [url for url in state["calls"] if "index-tickers" in url]
    assert len(index_calls) == (0 if embedded_index else 2)


@pytest.mark.parametrize("cycles,duration", [(4, 180.0), (12, 900.0)])
def test_derived_fuse_covers_actual_cold_polls_and_fresh_decisions(
    tmp_path, local_wire, monkeypatch, cycles, duration
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )

    state, transport = local_wire
    _routes(state, embedded_index=False)
    cap = compute_worst_case_legitimate_shared_transport_charged_gets_v1(
        max_run_duration_seconds=duration, wait_interval_seconds=5.0, max_cycles_per_run=cycles
    )
    transport.max_request_count = cap
    polls = compute_max_canonical_continuous_poll_iterations_v1(
        max_run_duration_seconds=duration, wait_interval_seconds=5.0, max_cycles_per_run=cycles
    )
    # The pre-existing finite margin must also charge an unsuccessful wire attempt.
    original_opener = wire.build_opener

    class TimedOut:
        def open(self, *args, **kwargs):
            raise TimeoutError()

    monkeypatch.setattr(wire, "build_opener", lambda *args: TimedOut())
    failure = transport.get(
        endpoint=GET_PATH,
        auth_required=False,
        pretrade_decision_id="failed-attempt",
        get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    )
    assert not failure.get_performed and failure.error_class == "TIMEOUT"
    assert transport.request_count == 1
    monkeypatch.setattr(wire, "build_opener", original_opener)

    # The original launcher makes one G17 history acquisition. Its downstream
    # volatility computation is outside this charged-request test.
    state["payloads"]["/api/v5/market/history-mark-price-candles"] = CANDLES
    transport.get(
        endpoint="/api/v5/market/history-mark-price-candles?instId=0G-USDT-SWAP",
        auth_required=False,
        pretrade_decision_id="g17-history",
    )
    assert _source(tmp_path / "bootstrap", transport, warm=False).poll() is not None
    source = _source(tmp_path / "continuous", transport)
    for _ in range(polls):
        assert source.poll() is not None
    for index in range(cycles):
        handoff = compose_current_productive_29p_common_epoch_handoff_v1(
            decision_epoch="2026-11-07T12:00:00Z",
            bound_instrument=_bound(instrument_id=NATIVE),
            fresh_get_transport=transport,
            pretrade_cycle_id=f"original-cycle-{index}",
        )
        assert handoff.evaluator_29p is True
    assert transport.request_count == 1 + len(state["calls"]) == cap
    with pytest.raises(FullCoreProductiveReadOnlyGetError, match="MAX_REQUEST_COUNT_EXCEEDED"):
        transport.get(
            endpoint=GET_PATH,
            auth_required=False,
            pretrade_decision_id="over-limit",
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )
    assert transport.request_count == cap
    assert set(transport.methods_used) == {"GET"}


def test_existing_duration_gate_rechecks_after_blocking_source_before_s5(tmp_path):
    from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
        _FakeClock,
        _auth,
        _run,
    )

    clock = _FakeClock()

    class SlowSource:
        def poll(self):
            clock.now += 6.0
            return None

    result = _run(
        tmp_path,
        clock=clock,
        authorization=_auth(max_run_duration_seconds=3.0),
        observation_source=SlowSource(),
    )
    assert result.reason_code == "MAX_RUN_DURATION"
    assert result.s5_invoke_count == 0
    # The original duration owner gates continuation after the foreign call;
    # it does not preempt an in-flight transport operation at second three.
    assert result.sequencer_elapsed_monotonic_seconds == 6.0
