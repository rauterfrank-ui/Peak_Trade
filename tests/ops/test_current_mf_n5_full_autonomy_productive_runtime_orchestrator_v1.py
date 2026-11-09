"""Productive Full-Autonomy N=5 runtime orchestrator tests."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    AUTONOMY_ORCHESTRATOR_STATUS,
    AUTONOMY_TRADING_DECISION_AUTHORITY,
    CONTRACT_ID,
    ENTRYPOINT_SYMBOL,
    OWNER,
    PORTFOLIO_RESTART_STATUS,
    PRODUCTIVE_ENTRYPOINT,
    ProductiveFullAutonomyCap24BindContextV1,
    ProductiveFullAutonomyN5RuntimeOrchestratorError,
    run_productive_full_autonomy_n5_runtime_orchestrator_v1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    N_GT_1_ENABLED,
    POST_ALLOWED,
    TERMINAL_BOUNDARY_PRE_EXTERNAL,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_HOLD,
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from tests.ops.test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import (
    OBSERVED_UNIX,
    REPO_SHA,
    _cid,
    _empty_portfolio,
    _five_rows,
    _held_writer,
    _membership,
    _persist_universe_and_ranking,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    ORIGIN_SHA,
    _market_kwargs,
    _memory_g17_producer,
    _mv2_aligned_candles,
)

PACKAGE_DIR = Path(__file__).resolve().parents[2] / (
    "src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1"
)
ORCH_SOURCE = (PACKAGE_DIR / "orchestrator_v1.py").read_text(encoding="utf-8")
CONSTANTS_SOURCE = (PACKAGE_DIR / "constants_v1.py").read_text(encoding="utf-8")


def _called_names(source: str) -> set[str]:
    called: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


def _g17_for_instruments(
    chain: dict,
    instrument_rows: list[str],
    target_cardinality: int,
) -> dict[str, object]:
    producers: dict[str, object] = {}
    for idx, native in enumerate(instrument_rows[:target_cardinality]):
        lane_id = LANE_IDS[idx]
        producers[lane_id] = _memory_g17_producer(
            instrument_id=_cid(chain["ranking"], native),
            venue_native_id=native,
        )
    return producers


def _run_orchestrator(
    tmp_path: Path,
    *,
    instrument_rows: list[str],
    target_cardinality: int,
    portfolio_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None,
    include_host_completion_rollup: bool = False,
    host_budget_recovery=None,
) -> object:
    chain = _persist_universe_and_ranking(tmp_path, _five_rows())
    topology_root = tmp_path / "topology"
    topology_root.mkdir()
    instruments = [_cid(chain["ranking"], native) for native in instrument_rows]
    membership = _membership(chain["ranking"], instruments)
    writer = _held_writer(topology_root)
    cap24 = ProductiveFullAutonomyCap24BindContextV1(
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=_empty_portfolio(),
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        session_id="fa-orchestrator",
        now_unix=OBSERVED_UNIX,
    )
    cycle = _market_kwargs(cycle_id_prefix="fa-orch")
    cycle.pop("origin_main_sha", None)
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_explicit_test_fixture_price_provenance_v1,
    )

    cycle.pop("canonical_price_provenance", None)
    cycle["canonical_price_provenance_by_lane"] = {
        LANE_IDS[i]: build_explicit_test_fixture_price_provenance_v1(
            venue_native_id=native,
            mark_px=float(chain["mark_price_by_native_id"][native]),
            index_px=float(cycle["index_px"]),
        )
        for i, native in enumerate(instrument_rows[:target_cardinality])
    }
    cycle["g17_typed_vol_producers"] = _g17_for_instruments(
        chain, instrument_rows, target_cardinality
    )
    # Supply the existing 100-bar readiness contract explicitly in this offline
    # fixture. The old convenience materializer supplies only eight bars.
    cycle["candles_payload_by_lane"] = {
        LANE_IDS[index]: {
            **_mv2_aligned_candles(
                last_ts_ms=int(cycle["candles_payload"]["data"][-1][0]),
                mark_px=float(chain["mark_price_by_native_id"][native]),
            ),
            "instId": native,
        }
        for index, native in enumerate(instrument_rows[:target_cardinality])
    }
    if host_budget_recovery is not None:
        cycle["host_budget_recovery"] = host_budget_recovery
    try:
        return run_productive_full_autonomy_n5_runtime_orchestrator_v1(
            membership=membership,
            ranking_snapshot=chain["ranking"],
            topology_state_root_base=topology_root,
            lane_assignment_writer=writer,
            cap24_bind=cap24,
            repository_sha=REPO_SHA,
            producer_observed_at_unix=OBSERVED_UNIX,
            origin_main_sha=ORIGIN_SHA,
            target_cardinality=target_cardinality,
            portfolio_budget_owner=portfolio_owner,
            include_host_completion_rollup=include_host_completion_rollup,
            **cycle,
        )
    finally:
        writer.release()


def test_productive_entrypoint_and_authority_pins() -> None:
    assert CONTRACT_ID == "CURRENT_MF_N5_FULL_AUTONOMY_PRODUCTIVE_RUNTIME_ORCHESTRATOR_CONTRACT_V1"
    assert OWNER == "ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1"
    assert ENTRYPOINT_SYMBOL == "run_productive_full_autonomy_n5_runtime_orchestrator_v1"
    assert PRODUCTIVE_ENTRYPOINT.endswith(ENTRYPOINT_SYMBOL)
    assert AUTONOMY_ORCHESTRATOR_STATUS == "PRODUCTIVE_COMPOSE_IMPLEMENTED"
    assert AUTONOMY_TRADING_DECISION_AUTHORITY is False
    assert PORTFOLIO_RESTART_STATUS == "FAIL_CLOSED_NO_UNPROVEN_RESTORE"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert N_GT_1_ENABLED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False


def test_orchestrator_composes_canonical_join_chain() -> None:
    called = _called_names(ORCH_SOURCE)
    assert "publish_checked_lane_selections_v1" in called
    assert "consume_recovered_isolated_lane_topology_v1" not in called
    assert "bind_occupied_lane_cap24_n1_instruments_v1" in called
    assert "admit_occupied_lane_bound_instruments_v1" in called
    assert "compose_occupied_lane_mv2_dp_handoff_v1" in called
    assert "compose_occupied_lane_n1_host_join_readiness_v1" in called
    assert "run_current_productive_master_v2_runtime_cycle_v1" not in called
    assert "produce_occupied_lane_cap23_n1_selections_v1" not in CONSTANTS_SOURCE


def test_target_cardinality_one_end_to_end(tmp_path: Path) -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    result = _run_orchestrator(
        tmp_path,
        instrument_rows=["SOL-USDT-SWAP"],
        target_cardinality=1,
        portfolio_owner=owner,
    )
    assert result.target_cardinality == 1
    assert result.terminal_boundary == TERMINAL_BOUNDARY_PRE_EXTERNAL
    assert len(result.occupied_lane_ids) == 1
    assert result.external_effect_authorized is False
    assert result.post_allowed is False
    rollup = result.lane_rollups[0]
    assert rollup.disposition in {
        DISPOSITION_PRE_EXTERNAL_EFFECT,
        DISPOSITION_HOLD,
    }
    assert rollup.post_count == 0
    assert rollup.permit_created is False


def test_two_lanes_isolated_roots_and_sequential_rollups(tmp_path: Path) -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    result = _run_orchestrator(
        tmp_path,
        instrument_rows=["SOL-USDT-SWAP", "ETH-USDT-SWAP"],
        target_cardinality=2,
        portfolio_owner=owner,
    )
    assert result.target_cardinality == 2
    assert len(result.lane_rollups) == 2
    roots = [r.cursor_store_root for r in result.lane_rollups]
    assert len(set(roots)) == 2
    locks = [r.lock_root for r in result.lane_rollups]
    assert len(set(locks)) == 2


def test_cardinality_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ProductiveFullAutonomyN5RuntimeOrchestratorError) as exc:
        _run_orchestrator(
            tmp_path,
            instrument_rows=["SOL-USDT-SWAP"],
            target_cardinality=2,
        )
    assert "CARDINALITY" in exc.value.failure_code


@pytest.mark.parametrize("target", (3, 5))
def test_architectural_multi_lane_cardinality_without_productive_n_gt_1(
    tmp_path: Path, target: int
) -> None:
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    result = _run_orchestrator(
        tmp_path,
        instrument_rows=natives,
        target_cardinality=target,
        portfolio_owner=owner,
    )
    assert result.target_cardinality == target
    assert len(result.lane_rollups) == target
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert result.external_effect_authorized is False


def test_harness_joins_remain_distinct_from_productive_entrypoint() -> None:
    harness = Path(
        "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1"
        "/invoke_join_v1.py"
    ).read_text(encoding="utf-8")
    assert "run_productive_full_autonomy_n5_runtime_orchestrator_v1" not in harness
    sig = inspect.signature(run_productive_full_autonomy_n5_runtime_orchestrator_v1)
    assert "membership" in sig.parameters
    assert "target_cardinality" in sig.parameters


@pytest.mark.parametrize("target", [1, 5])
def test_optional_completion_uses_same_cycle_results_without_advancing_them(
    tmp_path: Path, monkeypatch, target: int
) -> None:
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        orchestrator_v1 as orchestrator,
    )
    from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1 import (
        completion_join_v1 as completion,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
        CURSOR_FILENAME,
    )

    real_readiness = orchestrator.compose_occupied_lane_n1_host_join_readiness_v1
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    calls, cursor_bytes, consumed = [], {}, {}

    def measured_readiness(*args, **kwargs):
        calls.append(kwargs.get("portfolio_budget_owner"))
        consumed.update(args=args, kwargs=kwargs)
        result = real_readiness(*args, **kwargs)
        for lane, projection in result.items():
            cursor_bytes[lane] = (Path(projection.cursor_store_root) / CURSOR_FILENAME).read_bytes()
        return result

    monkeypatch.setattr(
        orchestrator, "compose_occupied_lane_n1_host_join_readiness_v1", measured_readiness
    )
    monkeypatch.setattr(
        completion, "compose_occupied_lane_n1_host_join_readiness_v1", measured_readiness
    )
    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    result = _run_orchestrator(
        tmp_path,
        instrument_rows=natives[:target],
        target_cardinality=target,
        portfolio_owner=owner,
        include_host_completion_rollup=True,
    )
    assert calls == [owner]
    assert result.completion_result is not None
    assert result.completion_result.productive_runtime_cardinality == f"{target}_JOINED"
    for lane, projection in result.readiness_projections.items():
        joined = result.completion_result.joined_lanes[lane]
        assert joined.disposition == projection.disposition
        assert joined.instrument_id == projection.instrument_id
        assert joined.origin_main_sha == projection.origin_main_sha
        assert (Path(projection.cursor_store_root) / CURSOR_FILENAME).read_bytes() == cursor_bytes[
            lane
        ]
    assert result.completion_result.post_count == 0
    assert result.completion_result.permit_created is False
    # Reusing the consumed cycle remains forbidden. Completion did not clear or
    # mint authorization, and cannot turn the same C1 into another decision.
    with pytest.raises(ValueError, match="CYCLE_AUTHORIZATION_REPLAY"):
        real_readiness(*consumed["args"], **consumed["kwargs"])
    for lane, projection in result.readiness_projections.items():
        assert (Path(projection.cursor_store_root) / CURSOR_FILENAME).read_bytes() == cursor_bytes[
            lane
        ]


@pytest.mark.parametrize("fault", ["lane", "revision", "disposition", "consumer_effect"])
def test_completion_rejects_projection_that_disagrees_with_original_consumer(
    tmp_path: Path, monkeypatch, fault: str
) -> None:
    from dataclasses import replace
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        orchestrator_v1 as orchestrator,
    )
    from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1 import (
        completion_join_v1 as completion,
    )

    original = orchestrator.compose_occupied_lane_n1_host_join_readiness_v1
    seen = {}

    def capture(pairs, **kwargs):
        projections = original(pairs, **kwargs)
        seen.update(pairs=pairs, projections=projections, kwargs=kwargs)
        return projections

    monkeypatch.setattr(orchestrator, "compose_occupied_lane_n1_host_join_readiness_v1", capture)
    _run_orchestrator(tmp_path, instrument_rows=["SOL-USDT-SWAP"], target_cardinality=1)
    projection = seen["projections"]["LANE_1"]
    if fault == "lane":
        changed = replace(projection, lane_id="LANE_2")
    elif fault == "revision":
        changed = replace(projection, origin_main_sha="f" * 40)
    elif fault == "disposition":
        changed = replace(projection, disposition="COMPLETED")
    else:
        consumer = projection.n1_consumer_result
        changed = replace(
            projection,
            n1_consumer_result=replace(
                consumer,
                governed_cycle_result=replace(consumer.governed_cycle_result, post_count=1),
            ),
        )
    before = {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    with pytest.raises(ValueError):
        completion.complete_occupied_lane_runtime_n5_from_readiness_v1(
            seen["pairs"],
            {"LANE_1": changed},
            target_cardinality=1,
            origin_main_sha=ORIGIN_SHA,
            cycle_id_prefix=seen["kwargs"]["cycle_id_prefix"],
        )
    after = {
        str(p.relative_to(tmp_path)): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()
    }
    assert after == before


def test_shared_durable_recovery_context_reaches_actual_t2_and_29p_without_hold_admission(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.ops.test_portfolio_budget_host_v1 import _host
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        invoke_join_v1 as consumer,
    )

    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP"]
    (tmp_path / "prepared").mkdir()
    (tmp_path / "consumer").mkdir()
    prepared = _run_orchestrator(
        tmp_path / "prepared", instrument_rows=natives, target_cardinality=2
    )
    bindings = {lane: p.bound_instrument for lane, p in prepared.readiness_projections.items()}
    host = _host(tmp_path / "private", clock=lambda: OBSERVED_UNIX)
    dispatch_calls, capital_calls = [], []
    original_dispatch = consumer._t2_from_s7
    original_join = consumer.join_current_productive_enter_live_29p_before_venue_plan_v1

    def dispatch(**kwargs):
        dispatch_calls.append(kwargs)
        return original_dispatch(**kwargs)

    def join(**kwargs):
        capital_calls.append(kwargs)
        return original_join(**kwargs)

    monkeypatch.setattr(consumer, "_t2_from_s7", dispatch)
    monkeypatch.setattr(
        consumer, "join_current_productive_enter_live_29p_before_venue_plan_v1", join
    )
    try:
        context = host.observe_v1(bindings)
        result = _run_orchestrator(
            tmp_path / "consumer",
            instrument_rows=natives,
            target_cardinality=2,
            portfolio_owner=host.owner,
            host_budget_recovery=context,
            include_host_completion_rollup=True,
        )
        assert {
            lane: p.bound_instrument for lane, p in result.readiness_projections.items()
        } == bindings
        assert len(dispatch_calls) == len(capital_calls) == 2
        for call in [*dispatch_calls, *capital_calls]:
            assert call["host_budget_recovery"] is context
            assert call["portfolio_budget_owner"] is host.owner
        # HOLD does not grant fresh-capital/recovery admission. This test proves
        # transport through the real owners, not an executed ENTER or reconciliation.
        assert all(p.disposition == DISPOSITION_HOLD for p in result.readiness_projections.values())
        assert host.owner.budget_state_v1().recovery_required
        assert not result.portfolio_admitted
        assert result.portfolio_active_sum == 0
    finally:
        host.close()


@pytest.mark.parametrize("target", [1, 5])
def test_standalone_completion_retains_full_valid_native_cycle_path(
    tmp_path: Path, monkeypatch, target: int
) -> None:
    from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
        orchestrator_v1 as orchestrator,
    )
    from src.ops.current_mf_n5_full_autonomy_runtime_n5_completion_v1 import (
        completion_join_v1 as completion,
    )

    class InputsPrepared(Exception):
        pass

    inputs = {}

    def stop_before_any_cycle(pairs, **kwargs):
        inputs.update(pairs=pairs, kwargs=kwargs)
        raise InputsPrepared

    monkeypatch.setattr(
        orchestrator, "compose_occupied_lane_n1_host_join_readiness_v1", stop_before_any_cycle
    )
    natives = ["SOL-USDT-SWAP", "ETH-USDT-SWAP", "ADA-USDT-SWAP", "LINK-USDT-SWAP", "APT-USDT-SWAP"]
    with pytest.raises(InputsPrepared):
        _run_orchestrator(tmp_path, instrument_rows=natives[:target], target_cardinality=target)
    # Real Cap23/24 inputs prepared above; the standalone entry now performs the
    # first actual readiness/cycle calls and the original no-order host joins.
    result = completion.run_occupied_lane_runtime_n5_completion_v1(
        inputs["pairs"], target_cardinality=target, **inputs["kwargs"]
    )
    assert result.productive_runtime_cardinality == f"{target}_JOINED"
    assert len(result.joined_lanes) == target
    assert result.post_count == 0 and result.permit_created is False
    for lane, joined in result.joined_lanes.items():
        assert joined.native_id == inputs["pairs"][lane][1].venue_native_id
        assert joined.host_join_invoked and not joined.host_live_execution_port_present
