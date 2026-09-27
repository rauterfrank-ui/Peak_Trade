"""PRE_EXTERNAL order-independence: repeated ENTER closure in one pytest process."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    execute_current_productive_full_core_pre_external_closure_v1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _TEST_INST,
    _bound,
    _origin_main_sha,
    _productive_transport,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_wp2_composition_v1 import (
    OWNER_GO,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


def _run_layered_enter_pre_external_once_v1(*, tmp_path: Path, cycle_id_prefix: str) -> None:
    origin_sha = _origin_main_sha()
    integrity = MockCurrentProductive29PIntegrityBackendV1(
        origin_main=origin_sha,
        head=origin_sha,
    )
    bound = _bound()
    lanes_root = tmp_path / "lanes"
    _arm, enter_closes, mark_px, event_ts, g17 = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=object(),
            lane_state_root=lanes_root,
        )
    )
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    cap24_root = write_cap21_productivity_root_for_inst_v1(tmp_path, venue_native_id=_TEST_INST)
    result = execute_current_productive_full_core_pre_external_closure_v1(
        owner_go=OWNER_GO,
        origin_main_sha=origin_sha,
        bound_instrument=bound,
        lane_state_root=lanes_root,
        fresh_get_transport=_productive_transport(),
        execute_network=False,
        evidence_root=tmp_path / "evidence",
        candles_payload=candles,
        cap24_productivity_root=cap24_root,
        market_kwargs={
            "cycle_id_prefix": cycle_id_prefix,
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "existing_position_side": ExistingPositionSide.NONE,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
        },
        g17_typed_vol_producers={"LANE_1": g17},
        execution_integrity_backend=integrity,
    )
    assert result.wp2_status == "PASS"
    assert result.terminal_disposition == DISPOSITION_PRE_EXTERNAL_EFFECT


def test_layered_enter_pre_external_closure_with_process_isolation_contract_v1(
    tmp_path: Path,
) -> None:
    """ENTER→PRE_EXTERNAL closure under ops conftest F1/G17 isolation (single bounded proof)."""
    _run_layered_enter_pre_external_once_v1(
        tmp_path=tmp_path,
        cycle_id_prefix="order-indep-single",
    )
