"""GHV + synthetic enter_short: Live-29P protective-stop side resolution (fail-closed preserved)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    STATUS_FAIL,
    STATUS_PASS,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
    resolve_protective_stop_sizing_side_for_live_29p_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_synthetic_enter_forensic_v1 import (
    bind_synthetic_enter_forensic_session_v1,
    build_synthetic_enter_forensic_session_v1,
    maybe_apply_synthetic_enter_forensic_overlay_v1,
    reset_synthetic_enter_forensic_session_v1,
)
from tests.ops.test_current_productive_synthetic_enter_forensic_v1 import (
    _observe_replay_from_enter_fixture,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    DISTINCTIVE_EQUITY,
    EPOCH,
    _balance_payload,
    _bound,
    _injected,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    derive_protective_stop_price_from_adverse_exit_v0,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)


def test_ghv_synthetic_enter_short_resolves_protective_stop_sizing_side(
    tmp_path: Path,
) -> None:
    observe_replay = _observe_replay_from_enter_fixture()
    observe_only = replace(
        observe_replay,
        evidence=replace(
            observe_replay.evidence,
            decision_outcome="observe",
            selected_side="none",
        ),
    )
    assert resolve_protective_stop_sizing_side_for_live_29p_join_v1(observe_only) is None

    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="ghv-regression",
    )
    session_reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(session_reset)

    assert overlay.applied is True
    assert str(overlay.replay.evidence.decision_outcome) == "enter_short"
    assert overlay.replay.evidence.selected_side == "short"
    assert resolve_protective_stop_sizing_side_for_live_29p_join_v1(overlay.replay) == "SHORT"


def test_synthetic_enter_short_live_29p_join_passes_protective_stop_derivation(
    tmp_path: Path,
) -> None:
    """GHV forensic path: synthetic enter_short must not fail PROTECTIVE_STOP_DERIVATION_FAIL_CLOSED."""
    observe_replay = _observe_replay_from_enter_fixture()
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_short",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="ghv-ps-regression",
    )
    session_reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        result = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=overlay.replay,
            bound_instrument=_bound(),
            injected=_injected(payload=_balance_payload()),
            decision_epoch=EPOCH,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(session_reset)

    assert result.called is True
    assert result.first_blocker != "PROTECTIVE_STOP_DERIVATION_FAIL_CLOSED"
    assert result.status == STATUS_PASS
    assert result.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert result.producer_output_value == DISTINCTIVE_EQUITY
    assert result.post_count == "0"


def test_protective_stop_derivation_fail_closed_when_sizing_side_unresolved() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    replay = cycle_b.replay
    assert replay is not None
    evidence = replace(
        replay.evidence,
        decision_outcome="observe",
        selected_side="none",
    )
    hold_replay = replace(replay, evidence=evidence)
    assert resolve_protective_stop_sizing_side_for_live_29p_join_v1(hold_replay) is None
    assert (
        derive_protective_stop_price_from_adverse_exit_v0(
            selected_side="",
            reference_price=Decimal("3.18"),
            adverse_exit_distance=80,
        )
        is None
    )


def test_protective_stop_fail_closed_when_derived_stop_invalid(
    tmp_path: Path,
) -> None:
    observe_replay = _observe_replay_from_enter_fixture()
    session = build_synthetic_enter_forensic_session_v1(
        enabled=True,
        synthetic_side="enter_long",
        inject_cycle_index=1,
        product_evidence_root=tmp_path,
        continuous_run_id="ghv-ps-neg-long",
    )
    session_reset = bind_synthetic_enter_forensic_session_v1(session)
    try:
        overlay = maybe_apply_synthetic_enter_forensic_overlay_v1(
            observe_replay,
            cycle_index=1,
        )
        # Mark below CANONICAL_ADVERSE_EXIT_DISTANCE (80) → LONG stop non-positive → fail-closed.
        broken: IntegratedOfflineReplayResultV1 = replace(
            overlay.replay,
            intermediate=replace(
                overlay.replay.intermediate,
                market_context=replace(
                    overlay.replay.intermediate.market_context,
                    mark_price=Decimal("3.18"),
                ),
            ),
        )
        result = join_current_productive_enter_live_29p_before_venue_plan_v1(
            replay=broken,
            bound_instrument=_bound(),
            injected=_injected(payload=_balance_payload()),
            decision_epoch=EPOCH,
        )
    finally:
        reset_synthetic_enter_forensic_session_v1(session_reset)

    assert result.called is True
    assert result.status == STATUS_FAIL
    assert result.first_blocker == "PROTECTIVE_STOP_DERIVATION_FAIL_CLOSED"
