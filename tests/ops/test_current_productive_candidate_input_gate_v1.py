"""Candidate rejection must happen before GGE, with no wait/entry dependency."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_master_v2_runtime_cycle_v1 as host,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_candidate_input_gate_v1 import (
    CANDIDATE_REJECTED,
    REQUIRED_CANDIDATE_FINALIZED_CLOSES,
    finalized_candidate_candle_history_rejection_codes_v1,
)
from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import _cycle_kwargs
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _cycle,
    _produced_g17_producer,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide


@pytest.mark.parametrize(
    "field",
    [
        "mark_px",
        "index_px",
        "bid_px",
        "ask_px",
        "volume",
        "open_interest",
        "funding_rate",
        "observed_unix",
        "last_finalized_event_ts_unix",
        "finalized_closes",
        "bound_instrument",
        "canonical_price_provenance",
        "master_v2_reconciliation_admission",
    ],
)
def test_missing_required_input_discards_before_gge(monkeypatch, field):
    gge = Mock(side_effect=AssertionError("rejected candidate reached GGE"))
    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", gge
    )
    kwargs = _cycle_kwargs("missing-input")
    kwargs[field] = None
    result = host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    assert result.provenance == CANDIDATE_REJECTED
    assert field in result.input_blocker
    assert result.replay is None
    assert result.outgoing_cursor is None
    gge.assert_not_called()


@pytest.mark.parametrize(
    "changes",
    [
        {"funding_rate": float("nan")},
        {"open_interest": float("inf")},
        {"finalized_closes": [1.0, None]},
        {"mark_px": True},
        {"bid_px": -1.0},
    ],
)
def test_invalid_required_data_never_reaches_gge(monkeypatch, changes):
    gge = Mock(side_effect=AssertionError("invalid candidate reached GGE"))
    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", gge
    )
    kwargs = _cycle_kwargs("invalid-input")
    kwargs["g17_typed_vol_producer"] = _produced_g17_producer(
        instrument_id=kwargs["bound_instrument"].instrument_id,
    )
    kwargs.update(changes)
    result = host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    assert result.input_blocker
    assert result.replay is None
    gge.assert_not_called()


def test_missing_required_typed_volatility_discards_before_gge(monkeypatch):
    gge = Mock(side_effect=AssertionError("missing typed volatility reached GGE"))
    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", gge
    )
    result = host.run_current_productive_master_v2_runtime_cycle_v1(**_cycle_kwargs("missing-g17"))
    assert result.provenance == CANDIDATE_REJECTED
    assert "TYPED_VOLATILITY_ESTIMATE_MISSING" in result.fail_reasons
    gge.assert_not_called()


def test_invalid_g17_handle_discards_without_binding_or_fetch(monkeypatch):
    bind = Mock(side_effect=AssertionError("invalid handle reached typed bind"))
    monkeypatch.setattr(host, "apply_current_productive_g17_typed_vol_cmc_bind_v1", bind)
    kwargs = _cycle_kwargs("invalid-g17", producer=object())
    result = host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    assert result.provenance == CANDIDATE_REJECTED
    assert "g17_typed_vol_producer_invalid" in result.input_blocker
    bind.assert_not_called()


class ReachedGge(Exception):
    pass


def test_complete_valid_candidate_handed_to_gge_without_entry_or_wait(monkeypatch):
    kwargs = _cycle_kwargs("valid-candidate")
    kwargs["g17_typed_vol_producer"] = _produced_g17_producer(
        instrument_id=kwargs["bound_instrument"].instrument_id,
    )
    kwargs.update(volume=0.0, open_interest=0.0, funding_rate=-0.001)

    def at_gge(context):
        assert context.instrument_id == kwargs["bound_instrument"].instrument_id
        assert context.mark_price == kwargs["mark_px"]
        assert context.canonical_volatility_estimate is not None
        raise ReachedGge

    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", at_gge
    )
    with pytest.raises(ReachedGge):
        host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)


def test_existing_position_is_not_discarded_by_candidate_gate(monkeypatch):
    kwargs = _cycle_kwargs("occupied-position")
    origin = _cycle(
        cycle_id="occupied-position-origin", bound_instrument=kwargs["bound_instrument"]
    )
    assert origin.outgoing_cursor is not None
    kwargs["incoming_cursor"] = origin.outgoing_cursor
    kwargs.update(venue_flat=False, existing_position_side=ExistingPositionSide.LONG)
    kwargs["finalized_closes"] = kwargs["finalized_closes"][:64]
    gge = Mock(side_effect=ReachedGge)
    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", gge
    )
    gate = Mock(side_effect=AssertionError("candidate gate applied to open position"))
    monkeypatch.setattr(host, "candidate_market_context_rejection_codes_v1", gate)
    with pytest.raises(ReachedGge):
        host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    gate.assert_not_called()


def test_passed_candidate_leaves_double_play_results_and_cursor_unchanged(monkeypatch):
    """Compare the same cold/warm cycles with inspection active vs bypassed.

    This bypass exists only in this test process. Production has no bypass flag.
    Equality covers the replay, input digest, confirmation, scope, SideState and
    outgoing persisted-cursor payload, not just a final decision label.
    """
    actual_cursor = baseline_cursor = None
    for step in range(3):
        cycle_id = f"candidate-noninterference-{step}"
        event_time = 1_700_000_000.0 + step * 60.0
        actual = _cycle(
            cycle_id=cycle_id,
            incoming_cursor=actual_cursor,
            event_ts_unix=event_time,
        )
        with monkeypatch.context() as patch:
            patch.setattr(host, "invalid_candidate_cycle_input_codes_v1", lambda **_: ())
            patch.setattr(host, "candidate_market_context_rejection_codes_v1", lambda _: ())
            baseline = _cycle(
                cycle_id=cycle_id,
                incoming_cursor=baseline_cursor,
                event_ts_unix=event_time,
            )
        assert actual.replay is not None
        assert actual == baseline
        actual_cursor = actual.outgoing_cursor
        baseline_cursor = baseline.outgoing_cursor
        assert actual_cursor is not None


@pytest.mark.parametrize("count", [1, 3, 64, 99])
def test_incomplete_history_rejected_before_gge_and_confirmation(monkeypatch, count):
    forbidden = Mock(side_effect=AssertionError("incomplete history entered evaluation"))
    monkeypatch.setattr(host, "_bind_cap61_confirmation_v1", forbidden)
    monkeypatch.setattr(
        host, "resolve_layer_c_event_distances_from_canonical_market_context_v1", forbidden
    )
    kwargs = _cycle_kwargs("history-not-ready")
    kwargs["finalized_closes"] = tuple(float(1000 + i) for i in range(count))
    result = host.run_current_productive_master_v2_runtime_cycle_v1(**kwargs)
    assert result.provenance == CANDIDATE_REJECTED
    assert "finalized_history_not_ready" in result.input_blocker
    assert result.replay is None
    assert result.outgoing_cursor is None
    forbidden.assert_not_called()


def _history_payload(count=100):
    return {
        "data": [
            [str(1700000000000 + 60000 * i), "1", "1", "1", str(1000 + i), "1", "1", "1", "1"]
            for i in range(count)
        ]
    }


def test_full_history_with_unfinished_current_candle_ready_immediately_and_unchanged():
    import copy
    from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
        GET_LIMIT,
    )

    payload = _history_payload()
    current = _history_payload(101)["data"][-1]
    current[8] = "0"
    payload["data"].insert(0, current)
    before = copy.deepcopy(payload)
    assert REQUIRED_CANDIDATE_FINALIZED_CLOSES == 100
    assert int(GET_LIMIT) == 101
    assert finalized_candidate_candle_history_rejection_codes_v1(payload) == ()
    assert payload == before


@pytest.mark.parametrize(
    "defect,code",
    [
        ("unfinished", "finalized_history_not_ready"),
        ("duplicate", "finalized_history_duplicate"),
        ("gap", "finalized_history_gap"),
        ("nonfinite", "finalized_history_invalid"),
    ],
)
def test_history_must_already_be_complete_and_valid(defect, code):
    payload = _history_payload()
    rows = payload["data"]
    if defect == "unfinished":
        rows[-1][8] = "0"
    elif defect == "duplicate":
        rows[-1][0] = rows[-2][0]
    elif defect == "gap":
        rows[-1][0] = str(int(rows[-1][0]) + 60000)
    else:
        rows[-1][4] = "nan"
    assert finalized_candidate_candle_history_rejection_codes_v1(payload) == (code,)


def test_persistent_handoff_rejects_short_history_before_market_processing():
    from src.ops.full_core_live_path_composition_root_v1.current_productive_persistent_natural_enter_convergence_v1 import (
        PersistentNaturalEnterConvergenceError,
        _market_kwargs_from_observation_v1,
    )

    with pytest.raises(PersistentNaturalEnterConvergenceError, match="finalized_history_not_ready"):
        _market_kwargs_from_observation_v1(
            candles_payload=_history_payload(99),
            mark_price_payload={},
            venue_native_id="inst-eth-usdt-perp",
            cycle_id_prefix="not-ready",
            origin_main_sha="offline",
            g17_producers={},
        )
