"""Productive MV2 cycle must not auto-wire simulated CRS equity (VARIANT B)."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ops.productive_historical_replay_adapter_v1 import (
    _wire_isolated_offline_simulated_economics_crs_boundary_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.simulated_economics_crs_boundary_binding_v1 import (
    build_simulated_economics_crs_boundary_state_file_v1,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)

REPO = Path(__file__).resolve().parents[2]
MASTER_V2_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)
HISTORICAL_ADAPTER_SRC = REPO / "scripts/ops/productive_historical_replay_adapter_v1.py"
_ENTRY_OUTCOMES = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_REMOVED_PRODUCTIVE_MARKERS = (
    "_wire_simulated_economics_crs_boundary_onto_replay_input_v1",
    "SIMULATED_ECONOMICS_CRS_BOUNDARY_WIRING_OWNER",
    "build_simulated_economics_crs_boundary_state_file_v1",
    "DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY",
    "100000",
    "availEq",
)


def test_productive_cycle_source_has_no_simulated_capital_wire() -> None:
    text = MASTER_V2_SRC.read_text(encoding="utf-8")
    for marker in _REMOVED_PRODUCTIVE_MARKERS:
        assert marker not in text
    assert "treasury" not in text.lower()
    assert "Does not POST" in text
    assert "run_integrated_offline_trading_logic_replay_v1" in text


def test_productive_cycle_leaves_capital_context_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tests.ops.test_current_productive_g17_typed_vol_cmc_bind_v1 import (
        _bound,
        _closes,
    )
    from tests.ops._current_productive_reconciliation_admission_test_helpers_v1 import (
        non_productive_test_master_v2_reconciliation_admission_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
        build_provenance_from_governed_synthetic_close_mark_and_index_v1,
    )
    from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide

    captured: list[IntegratedOfflineReplayInputV1] = []
    original = run_integrated_offline_trading_logic_replay_v1

    def _capture(inp: IntegratedOfflineReplayInputV1):
        captured.append(inp)
        return original(inp)

    monkeypatch.setattr(
        "src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1.run_integrated_offline_trading_logic_replay_v1",
        _capture,
    )
    monkeypatch.setattr(
        "src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1.consumer_wiring_authorized_v1",
        lambda **_kwargs: False,
    )
    closes = _closes()
    last = float(closes[-1])
    index_px = last * 0.995
    bound = _bound()
    result = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="crs-boundary-absent",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=index_px,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        canonical_price_provenance=build_provenance_from_governed_synthetic_close_mark_and_index_v1(
            venue_native_id=str(bound.venue_native_id or bound.instrument_id),
            mark_px=float(last),
            index_px=float(index_px),
        ),
        master_v2_reconciliation_admission=non_productive_test_master_v2_reconciliation_admission_v1(
            bound=bound
        ),
    )
    assert len(captured) == 1
    boundary = captured[0].current_instrument_capital_risk_sizing_boundary_state_file
    assert boundary is None
    assert result.replay is not None
    assert result.decision_outcome not in _ENTRY_OUTCOMES
    intermediate = result.replay.intermediate
    assert intermediate is None or intermediate.canonical_order_intent is None


def test_unresolved_remains_when_replay_input_has_no_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED in replay.evidence.reason_codes
    assert replay.intermediate is not None
    assert replay.intermediate.canonical_order_intent is None
    if replay.evidence.decision_outcome in _ENTRY_OUTCOMES:
        assert replay.intermediate.capital_risk_sizing_decision is None


def test_offline_adapter_preserves_existing_simulated_builder() -> None:
    instrument_id = "BTC-USDT-SWAP-CANON"
    base = _confirmed_replay_input(side="LONG")
    wired = _wire_isolated_offline_simulated_economics_crs_boundary_v1(
        base,
        instrument_id=instrument_id,
    )
    boundary = wired.current_instrument_capital_risk_sizing_boundary_state_file
    assert boundary is not None
    assert isinstance(boundary, CapitalRiskSizingBacktestStateFileRecordV0)
    expected = build_simulated_economics_crs_boundary_state_file_v1(
        instrument_id=instrument_id,
    )
    assert boundary.instrument_id == instrument_id
    assert boundary.account_equity == expected.account_equity == "100000"
    assert boundary.current_reconciled_exposure == "0"
    assert boundary.current_open_positions_count == 0
    assert boundary.maximum_positions == 10
    assert boundary.reconciliation_status == "RECONCILED"
    assert (
        boundary.dynamic_price_context_binding_ref
        == MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1
    )
    assert (
        boundary.capital_risk_sizing_owner_digest_ref
        == expected.capital_risk_sizing_owner_digest_ref
    )
    adapter_text = HISTORICAL_ADAPTER_SRC.read_text(encoding="utf-8")
    assert "_resolve_f1_m9_governed_seam_for_integrated_offline_replay_v1" in adapter_text
    assert "_wire_simulated_economics_crs_boundary_onto_replay_input_v1" not in adapter_text
    assert "build_simulated_economics_crs_boundary_state_file_v1" in adapter_text


def test_offline_adapter_empty_instrument_id_fail_closed() -> None:
    base = _confirmed_replay_input(side="LONG")
    assert (
        _wire_isolated_offline_simulated_economics_crs_boundary_v1(
            base,
            instrument_id="",
        )
        is base
    )


def test_offline_adapter_producer_failure_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom(**_kwargs: object) -> CapitalRiskSizingBacktestStateFileRecordV0:
        raise ValueError("simulated_economics_account_equity_invalid")

    monkeypatch.setattr(
        "src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.simulated_economics_crs_boundary_binding_v1.build_simulated_economics_crs_boundary_state_file_v1",
        _boom,
    )
    base = _confirmed_replay_input(side="LONG")
    wired = _wire_isolated_offline_simulated_economics_crs_boundary_v1(
        base,
        instrument_id="BTC-USDT-SWAP-CANON",
    )
    assert wired.current_instrument_capital_risk_sizing_boundary_state_file is None


def test_no_post_authority_constants_unchanged() -> None:
    from src.governance.current_productive_activation_policy_v1 import (
        REAL_VENUE_POST_ALLOWED_BY_POLICY,
    )

    assert REAL_VENUE_POST_ALLOWED_BY_POLICY is False


_PRODUCTIVE_CYCLE_HOSTS = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_layered_long_mv2_state_advance_for_pre_external_v1.py",
    "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py",
)


def test_productive_hosts_have_no_simulated_capital_fallback() -> None:
    for relative in _PRODUCTIVE_CYCLE_HOSTS:
        text = (REPO / relative).read_text(encoding="utf-8")
        assert "run_current_productive_master_v2_runtime_cycle_v1(" in text
        assert "build_simulated_economics_crs_boundary_state_file_v1" not in text
        assert "DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY" not in text
        assert "_wire_simulated_economics_crs_boundary_onto_replay_input_v1" not in text


def test_changed_files_add_no_execution_authority() -> None:
    cycle = MASTER_V2_SRC.read_text(encoding="utf-8")
    adapter = HISTORICAL_ADAPTER_SRC.read_text(encoding="utf-8")
    for text in (cycle, adapter):
        assert "LIVE_AUTHORIZED = True" not in text
        assert "TESTNET_AUTHORIZED = True" not in text
        assert "submission_authorized=True" not in text
        assert "POST_ALLOWED = True" not in text
