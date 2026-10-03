"""MV2 simulated-economics CRS boundary propagation (WIRING_ONLY)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    SIMULATED_ECONOMICS_CRS_BOUNDARY_WIRING_OWNER,
    _wire_simulated_economics_crs_boundary_onto_replay_input_v1,
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
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayInputV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
)

REPO = Path(__file__).resolve().parents[2]
MASTER_V2_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)


def test_wire_helper_attaches_canonical_boundary_record() -> None:
    instrument_id = "BTC-USDT-SWAP-CANON"
    base = _confirmed_replay_input(side="LONG")
    wired = _wire_simulated_economics_crs_boundary_onto_replay_input_v1(
        base,
        instrument_id=instrument_id,
    )
    boundary = wired.current_instrument_capital_risk_sizing_boundary_state_file
    assert boundary is not None
    assert isinstance(boundary, CapitalRiskSizingBacktestStateFileRecordV0)
    assert boundary.instrument_id == instrument_id
    assert (
        boundary.dynamic_price_context_binding_ref
        == MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1
    )
    expected = build_simulated_economics_crs_boundary_state_file_v1(
        instrument_id=instrument_id,
    )
    assert boundary.account_equity == expected.account_equity
    assert (
        boundary.capital_risk_sizing_owner_digest_ref
        == expected.capital_risk_sizing_owner_digest_ref
    )


def test_wire_helper_empty_instrument_id_fail_closed() -> None:
    base = _confirmed_replay_input(side="LONG")
    assert (
        _wire_simulated_economics_crs_boundary_onto_replay_input_v1(
            base,
            instrument_id="",
        )
        is base
    )


def test_wire_helper_producer_failure_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 as mv2_mod

    def _boom(**_kwargs: object) -> CapitalRiskSizingBacktestStateFileRecordV0:
        raise ValueError("simulated_economics_account_equity_invalid")

    monkeypatch.setattr(
        "src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.simulated_economics_crs_boundary_binding_v1.build_simulated_economics_crs_boundary_state_file_v1",
        _boom,
    )
    base = _confirmed_replay_input(side="LONG")
    wired = mv2_mod._wire_simulated_economics_crs_boundary_onto_replay_input_v1(
        base,
        instrument_id="BTC-USDT-SWAP-CANON",
    )
    assert wired.current_instrument_capital_risk_sizing_boundary_state_file is None


def test_master_v2_cycle_passes_boundary_into_integrated_replay(
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
    closes = _closes()
    last = float(closes[-1])
    index_px = last * 0.995
    bound = _bound()
    run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=bound,
        cycle_id="crs-boundary-capture",
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
    assert boundary is not None
    assert boundary.instrument_id == bound.instrument_id


def test_wiring_owner_is_mv2_host_only() -> None:
    text = MASTER_V2_SRC.read_text(encoding="utf-8")
    assert "_wire_simulated_economics_crs_boundary_onto_replay_input_v1" in text
    assert SIMULATED_ECONOMICS_CRS_BOUNDARY_WIRING_OWNER.endswith(
        "_wire_simulated_economics_crs_boundary_onto_replay_input_v1"
    )
    assert "build_simulated_economics_crs_boundary_state_file_v1" in text
    assert "current_instrument_capital_risk_sizing_boundary_state_file" in text


def test_unresolved_remains_when_replay_input_has_no_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED in replay.evidence.reason_codes


def test_no_post_authority_constants_unchanged() -> None:
    from src.governance.current_productive_activation_policy_v1 import (
        REAL_VENUE_POST_ALLOWED_BY_POLICY,
    )

    assert REAL_VENUE_POST_ALLOWED_BY_POLICY is False
