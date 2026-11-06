"""Regression: historical capital/risk sizing defaults must not imply CURRENT authority."""

from __future__ import annotations

from decimal import Decimal

import pytest

from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_LINEAGE_REF_V1,
    REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED,
    REASON_DAILY_LOSS_REMAINING_BUDGET_UNRESOLVED,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    default_offline_replay_instrument_v0,
    isolated_offline_replay_fixture_capital_context_v0,
    isolated_offline_replay_fixture_instrument_v0,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    build_mv2_dynamic_boundary_capital_context_v1,
    build_mv2_offline_boundary_dynamic_price_context_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_ADVERSE_EXIT_DISTANCE,
)
from src.backtest.current_instrument_mv2_offline_boundary_materialization_v1 import (
    CurrentInstrumentBoundaryMaterializationError,
    materialize_current_instrument_crs_coi_boundary_state_files_v1,
)


def test_bind_without_capital_context_fail_closed() -> None:
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    evidence = build_scenario_tick_decision_evidence_v0(
        decision_id="d1",
        replay_id="r1",
        instrument_id="ETH-USDT-SWAP",
        trading_epoch=1,
        composition_result_id="c1",
        entry_exit_policy_ref="p1",
        selected_side="LONG",
        decision_outcome="enter_long",
        reason_codes=(),
        decision_precedence_trace=(),
        config_digest="0" * 64,
        implementation_digest="1" * 64,
    )
    binding = bind_capital_risk_sizing_offline_replay_evidence_v0(evidence, capital_context=None)
    assert binding.binding_applied is False
    assert REASON_CAPITAL_RISK_CONTEXT_UNRESOLVED in binding.evidence.reason_codes


def test_default_instrument_has_no_historical_max_quantity() -> None:
    inst = default_offline_replay_instrument_v0("ETH-USDT-SWAP")
    assert inst.maximum_quantity is None
    fixture = isolated_offline_replay_fixture_instrument_v0("ETH-USDT-SWAP")
    assert fixture.maximum_quantity == Decimal("100")


def test_dynamic_boundary_daily_loss_alias_removed() -> None:
    state = CapitalRiskSizingBacktestStateFileRecordV0(
        instrument_id="okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
        reference_price="",
        protective_stop_price="",
        account_equity="10000",
        scope_capital_limit="500",
        per_trade_risk_limit="40",
        total_capital_limit="500",
        daily_loss_remaining_budget="",
        current_reconciled_exposure="0",
        lot_size="1",
        minimum_quantity="1",
        maximum_quantity="",
        minimum_notional="5",
        tick_size="0.0001",
        maximum_positions=1,
        current_open_positions_count=0,
        reconciliation_status="RECONCILED",
        capital_risk_sizing_owner_digest_ref="v1",
        state_file_digest_ref="0" * 64,
        dynamic_price_context_binding_ref=MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    )
    dynamic = build_mv2_offline_boundary_dynamic_price_context_v1(
        mark_price=Decimal("100"),
        selected_side="LONG",
        adverse_exit_distance=Decimal("1"),
    )
    with pytest.raises(ValueError, match=REASON_DAILY_LOSS_REMAINING_BUDGET_UNRESOLVED):
        build_mv2_dynamic_boundary_capital_context_v1(
            state_file=state,
            dynamic_price_context=dynamic,
        )


def test_materialization_fail_closed_without_limits(tmp_path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"instrument_id":"okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap"}',
        encoding="utf-8",
    )
    with pytest.raises(
        CurrentInstrumentBoundaryMaterializationError,
        match="CAPITAL_RISK_STATIC_LIMITS_UNRESOLVED",
    ):
        materialize_current_instrument_crs_coi_boundary_state_files_v1(
            canonical_instrument_id="okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
            dataset_manifest_path=manifest,
            output_dir=tmp_path / "out",
            account_equity="10000",
        )


def test_fixture_context_retains_isolated_literals_only() -> None:
    ctx = isolated_offline_replay_fixture_capital_context_v0(
        instrument_id="ETH-USDT-SWAP",
        reference_price=Decimal("100"),
        protective_stop_price=Decimal("99"),
    )
    assert ctx.account_equity == ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY


def test_adverse_exit_distance_unchanged() -> None:
    assert float(CANONICAL_ADVERSE_EXIT_DISTANCE) == 80.0


def test_fixture_lineage_ref_stable() -> None:
    assert "isolated_offline_replay_fixture_capital_context_v0" in (
        ISOLATED_OFFLINE_REPLAY_FIXTURE_LINEAGE_REF_V1
    )
