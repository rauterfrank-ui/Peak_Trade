"""Passive C1/cycle join for elementary direction — no replay/trading-core feed."""

from __future__ import annotations

import ast
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.market_state.elementary_direction_v1 import (
    ElementaryDirectionStatusV1,
    ElementaryDirectionV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

_CYCLE_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)
_REPLAY_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
)
_ENTRY_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
)
_COMPOSITION_PATH = (
    Path(__file__).resolve().parents[2]
    / "src/trading/master_v2/double_play_composition_matrix_v1.py"
)
_STATE_PATH = Path(__file__).resolve().parents[2] / "src/trading/master_v2/double_play_state.py"


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def test_cycle_computes_elementary_direction_but_does_not_feed_replay() -> None:
    source = _CYCLE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    replay_builder_kwargs: set[str] = set()
    replay_run_kwargs: set[str] = set()
    join_called = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        keywords = {kw.arg for kw in node.keywords if kw.arg is not None}
        if name == "evaluate_elementary_direction_from_observation_acceptance_v1":
            join_called = True
            assert "current_mark" in keywords
            assert "bound_instrument_key" in keywords
        if name == "build_integrated_offline_replay_input_v1":
            replay_builder_kwargs = keywords
        if name == "run_integrated_offline_trading_logic_replay_v1":
            replay_run_kwargs = keywords
    assert join_called is True
    assert "elementary_direction" not in replay_builder_kwargs
    assert "elementary_direction" not in replay_run_kwargs
    assert "evaluate_elementary_direction_from_observation_acceptance_v1" in source
    assert "elementary_direction=elementary_direction" in source


def test_trading_core_owners_do_not_import_elementary_direction() -> None:
    forbidden = "elementary_direction"
    for path in (_REPLAY_PATH, _ENTRY_PATH, _COMPOSITION_PATH, _STATE_PATH):
        text = path.read_text(encoding="utf-8")
        assert forbidden not in text
        assert "ElementaryDirectionV1" not in text
        assert "evaluate_elementary_direction_v1" not in text


def test_first_cycle_exposes_neutral_without_changing_entry_owner() -> None:
    closes = (100.0, 101.0, 102.0)
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=BoundInstrumentV1(
            instrument_id="ETH-USD-SWAP-CANON",
            venue_native_id="ETH-USD-SWAP",
            ranking_snapshot_id="rank-elem-dir",
            ranking_integrity_digest="rank-elem-dir-digest",
            universe_snapshot_id="uni-elem-dir",
            selection_id="sel-elem-dir",
            selection_integrity_digest="sel-elem-dir-digest",
            selection_state="SELECTED",
        ),
        cycle_id="elementary-direction-first-cycle",
        observed_unix=1_700_000_100.0,
        mark_px=102.0,
        index_px=102.0,
        bid_px=101.5,
        ask_px=102.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
    )
    assert result.elementary_direction is not None
    assert result.elementary_direction.status is ElementaryDirectionStatusV1.EVALUATED
    assert result.elementary_direction.direction is ElementaryDirectionV1.NEUTRAL
    assert result.elementary_direction.previous_mark is None
    assert result.elementary_direction.current_mark == 102.0
    if result.replay is not None:
        assert getattr(result.replay.evidence, "elementary_direction", None) is None
