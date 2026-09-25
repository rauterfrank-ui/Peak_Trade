"""P5.10 productive activation + binding into CURRENT productive cycle."""

from __future__ import annotations

from pathlib import Path

import pytest
from trading.market_state.distinct_market_observation_acceptor_v1 import ObservationCandidateV1
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.p5_10_productive_activation_and_binding_v1 import (
    B5_TEMPORAL_SEMANTICS,
    EXTERNAL_EFFECT_AUTHORIZED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    P5_10_ACTIVATION_READINESS,
    PRODUCTIVE_BIND_SEAM_OWNER,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
)
from src.ops.p5_10b_layered_epoch_remaining_authority_closure_v1 import (
    state_switch_evidence_digest_parity_check_v1,
)
from src.ops.p5_productive_layered_core_authority_seam_v1 import (
    run_p5_layered_core_authority_seam_v1,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import DEFAULT_VENUE

from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _produced_g17_producer,
    _strong_uptrend_closes,
)

_INSTRUMENT = "inst-eth-usdt-perp"
_CYCLE_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py"
)


def _run_cycle(
    *,
    cycle_id: str,
    incoming_cursor: object | None = None,
    mark_px: float,
    event_ts_unix: float = 1_700_000_000.0,
    productive_layered_core_bind_requested: bool = False,
    layered_core_store_root: Path | None = None,
):
    path = _strong_uptrend_closes()
    producer = _produced_g17_producer(instrument_id=_INSTRUMENT)
    return run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=_bound(),
        cycle_id=cycle_id,
        observed_unix=float(event_ts_unix) + 100.0,
        mark_px=float(mark_px),
        index_px=float(mark_px),
        bid_px=float(mark_px) - 0.5,
        ask_px=float(mark_px) + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=path,
        last_finalized_event_ts_unix=float(event_ts_unix),
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        incoming_cursor=incoming_cursor,
        g17_typed_vol_producer=producer,
        productive_layered_core_bind_requested=productive_layered_core_bind_requested,
        layered_core_store_root=layered_core_store_root,
    )


def _init_layered_store(tmp_path: Path, *, mark: float) -> None:
    key = InstrumentObservationKeyV1(
        venue=DEFAULT_VENUE,
        canonical_instrument_id=_INSTRUMENT,
        venue_instrument_id=_INSTRUMENT,
    )
    selected = SelectedFutureInputV1(instrument_id=_INSTRUMENT, instrument_key=key)

    def cand(t: float, m: float) -> ObservationCandidateV1:
        return ObservationCandidateV1(
            venue=key.venue,
            canonical_instrument_id=key.canonical_instrument_id,
            venue_instrument_id=key.venue_instrument_id,
            venue_event_time=t,
            mark_price=m,
        )

    result = run_p5_layered_core_authority_seam_v1(
        store_root=tmp_path,
        selected=selected,
        mark_price_m_t=mark,
        mechanical_step=MechanicalStepSpecV1(mark_price_m_t=mark, proposed_d_t=25.0),
        restore_existing=False,
        initialization_observations=[cand(1.0, mark - 10.0), cand(2.0, mark)],
    )
    assert result.ok is True


def test_activation_guards_and_bind_enabled() -> None:
    assert P5_10_ACTIVATION_READINESS == "READY"
    assert PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is True
    assert B5_TEMPORAL_SEMANTICS == "POST_CANONICAL_NEXT_SIDE_STATE"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_productive_cycle_reachable_bind_seam_without_direct_p5_seam() -> None:
    text = _CYCLE_SOURCE.read_text(encoding="utf-8")
    assert PRODUCTIVE_BIND_SEAM_OWNER.split(".")[-2] in text
    assert "run_p5_layered_core_authority_seam_v1" not in text


def test_bind_requested_without_store_fail_closed() -> None:
    path = _strong_uptrend_closes()
    origin = _run_cycle(cycle_id="bind-no-store-origin", mark_px=float(path[0]))
    result = _run_cycle(
        cycle_id="bind-no-store",
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        productive_layered_core_bind_requested=True,
        layered_core_store_root=None,
    )
    assert result.replay_pass == "false"
    assert "layered_core_store_root_required" in result.provenance


def test_bind_fail_closed_without_existing_scope(tmp_path: Path) -> None:
    _init_layered_store(tmp_path, mark=1640.0)
    path = _strong_uptrend_closes()
    result = _run_cycle(
        cycle_id="bind-no-scope",
        mark_px=float(path[-1]),
        productive_layered_core_bind_requested=True,
        layered_core_store_root=tmp_path,
    )
    assert result.replay_pass == "false"
    assert "layered_bind_requires_existing_scope_carrier" in result.provenance


def test_productive_bind_handoff_post_canonical_next_side_state(tmp_path: Path) -> None:
    _init_layered_store(tmp_path, mark=1640.0)
    path = _strong_uptrend_closes()
    origin = _run_cycle(
        cycle_id="bind-origin",
        mark_px=float(path[0]),
        event_ts_unix=1_700_000_000.0,
    )
    assert origin.outgoing_cursor is not None
    bound = _run_cycle(
        cycle_id="bind-handoff",
        incoming_cursor=origin.outgoing_cursor,
        mark_px=float(path[-1]),
        event_ts_unix=1_700_000_120.0,
        productive_layered_core_bind_requested=True,
        layered_core_store_root=tmp_path,
    )
    assert bound.replay is not None
    assert bound.replay.replay_pass is True
    assert bound.replay.intermediate is not None
    switch = bound.replay.intermediate.state_switch
    assert state_switch_evidence_digest_parity_check_v1(switch) is True
    assert bound.outgoing_cursor is not None


def test_legacy_cycle_without_bind_request_unchanged() -> None:
    path = _strong_uptrend_closes()
    baseline = _run_cycle(cycle_id="legacy-baseline", mark_px=float(path[-1]))
    assert baseline.replay_pass == "true"


def test_n1_and_external_effect_unchanged() -> None:
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert EXTERNAL_EFFECT_AUTHORIZED is False


def test_s7_compose_bootstraps_layered_store_before_c1_extract_second_cycle(
    tmp_path: Path,
) -> None:
    """Regression: scope-bearing cursor without episode snapshot broke T2 after #6764 C1 extract."""
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.addressing_join_v1 import (
        compose_occupied_lane_mv2_dp_durable_cycle_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
        extract_finalized_candle_closes_v1,
    )
    from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
        SNAPSHOT_FILENAME,
    )

    from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
        _lane_g17,
        _market_kwargs,
        _pair,
        _s7_kwargs,
    )

    pairs = {"LANE_1": _pair(tmp_path, "LANE_1")}
    root = Path(pairs["LANE_1"][0].lane_state_root)
    mk = _market_kwargs(cycle_id_prefix="p510-bootstrap")
    mk["g17_typed_vol_producers"] = _lane_g17(pairs)
    s7 = _s7_kwargs(mk)
    first = compose_occupied_lane_mv2_dp_durable_cycle_v1(pairs, **s7)
    assert first["LANE_1"].cycle_result.outgoing_cursor is not None
    assert (root / SNAPSHOT_FILENAME).is_file()

    extracted, last_ts = extract_finalized_candle_closes_v1(mk["candles_payload"])
    assert extracted
    assert last_ts is not None
    lane_s7 = dict(s7)
    lane_s7["cycle_id_prefix"] = "p510-bootstrap:2"
    lane_s7["g17_typed_vol_producers"] = {"LANE_1": _lane_g17(pairs)["LANE_1"]}
    lane_s7["finalized_closes"] = extracted
    lane_s7["last_finalized_event_ts_unix"] = float(last_ts)
    lane_s7["observed_unix"] = float(last_ts) + 1.0
    second = compose_occupied_lane_mv2_dp_durable_cycle_v1(pairs, **lane_s7)
    assert second["LANE_1"].cycle_result.outgoing_cursor is not None
    assert not second["LANE_1"].cycle_result.fail_reasons
