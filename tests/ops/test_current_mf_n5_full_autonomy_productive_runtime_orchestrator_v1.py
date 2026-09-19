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
    cycle["g17_typed_vol_producers"] = _g17_for_instruments(
        chain, instrument_rows, target_cardinality
    )
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
    assert "consume_recovered_isolated_lane_topology_v1" in called
    assert "produce_occupied_lane_cap23_n1_selections_v1" in called
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
