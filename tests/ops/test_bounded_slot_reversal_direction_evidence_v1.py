"""Offline comparison of first-entry and running-reversal direction evidence."""

from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    current_core_entry_assessment_frame_v1 as frames,
    current_productive_sidestate_confirmation_cursor_v1 as cursors,
)
from src.ops.p5_productive_layered_core_authority_seam_v1 import (
    run_p5_layered_core_authority_seam_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import core_confirmation_source_v1 as c3
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from tests.ops._wp03_supervisor_golden_harness_v1 import _run_layered_entry_supervisor_v1
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.master_v2.layered_core_authority_seal_v1 import validate_layered_core_authority_seal_v1
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.contracts_v1 import (
    SelectedFutureInputV1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.durable_state_v1 import (
    restore_episode_from_store_v1,
)
from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.orchestrator_v1 import (
    MechanicalStepSpecV1,
)


@pytest.mark.parametrize(
    "opening_side,target_side,prior_regime,target_regime,move",
    [("LONG", "SHORT", "bull", "bear", -1), ("SHORT", "LONG", "bear", "bull", 1)],
)
def test_original_scope_switch_does_not_need_new_c3_to_prove_direction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    opening_side: str,
    target_side: str,
    prior_regime: str,
    target_regime: str,
    move: int,
):
    bind = PortfolioCapitalReservationBudgetOwnerV1.bind_execution_plan_v1
    first_entry = []

    def capture_plan(owner, reservation_id, envelope, **kwargs):
        plan = bind(owner, reservation_id, envelope, **kwargs)
        proof = owner.inspect_current_core_cursor_v1(reservation_id, envelope)
        assert proof["confirmation"]["confirmation_status"] == "confirmed"
        assert proof["original_intent_side"] == opening_side
        source = plan["plan_origin"]["core_cursor_source"]
        assert kwargs["entry_frame_required"] is True
        first_entry.append(source)
        return plan

    monkeypatch.setattr(
        PortfolioCapitalReservationBudgetOwnerV1, "bind_execution_plan_v1", capture_plan
    )
    result = _run_layered_entry_supervisor_v1(tmp_path, short=opening_side == "SHORT")
    assert result.ok and result.trace.post_count == 0
    (source,) = first_entry
    root = Path(source["cursor_root"])
    raw = cursors.load_current_productive_sidestate_confirmation_cursor_v1(root)
    cursor = cursors.parse_current_productive_sidestate_confirmation_cursor_v1(raw)
    initial = restore_episode_from_store_v1(root, expected_instrument_id=cursor.instrument_id)
    assert initial.regime.value == prior_regime

    selected = SelectedFutureInputV1(
        instrument_id=cursor.instrument_id,
        instrument_key=InstrumentObservationKeyV1(
            venue="okx_eea",
            canonical_instrument_id=cursor.instrument_id,
            venue_instrument_id=cursor.venue_native_id,
        ),
    )
    reference = initial.running_reference.reference_price_r_t
    distance = 2.0
    for distance_fraction in (0.5, 1.5):
        mark = reference + move * distance * distance_fraction
        native = run_p5_layered_core_authority_seam_v1(
            store_root=root,
            selected=selected,
            mark_price_m_t=mark,
            mechanical_step=MechanicalStepSpecV1(mark_price_m_t=mark, proposed_d_t=distance),
        )
        assert native.ok and native.seal is not None, native.failure_codes
        seal = native.seal
        assert validate_layered_core_authority_seal_v1(seal, instrument_id=cursor.instrument_id).ok
        restored = restore_episode_from_store_v1(root, expected_instrument_id=cursor.instrument_id)
        assert restored.snapshot_id == seal.episode_snapshot_id
        assert restored.regime.value == seal.regime_post
        if distance_fraction < 1:
            assert seal.regime_post == prior_regime
            assert not seal.switch_condition_met
        else:
            assert (seal.regime_pre, seal.regime_post) == (prior_regime, target_regime)
            assert seal.switch_condition_met and seal.cm_t >= seal.d_t and seal.r_t == mark
            assert not validate_layered_core_authority_seal_v1(seal, instrument_id="foreign").ok
            assert not validate_layered_core_authority_seal_v1(
                replace(seal, regime_post=prior_regime), instrument_id=cursor.instrument_id
            ).ok

    # The mechanical steps leave the original C3 observation history intact.
    assert cursors.load_current_productive_sidestate_confirmation_cursor_v1(root) == raw
    with pytest.raises(ValueError, match="CURRENT_CORE_C3_SELECTED_SIDE_NOT_CONFIRMED"):
        c3.inspect_current_core_confirmation_v1(
            source["confirmation_lineage"], cursor=cursor, raw=raw, intent_side=target_side
        )
    with pytest.raises(ValueError, match="CURRENT_CORE_ASSESSMENT_ENTRY_NOT_ADMITTED"):
        frames.inspect_current_core_entry_assessment_v1(
            cursor=cursor,
            intent_side=target_side,
            original_strategy=source["entry_frame_reference"]["selected_strategy"],
        )
