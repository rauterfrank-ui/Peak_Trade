"""CURRENT instrument MV2 offline boundary dynamic price context + materialization v1."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.backtest.current_instrument_mv2_offline_boundary_materialization_v1 import (
    materialize_current_instrument_crs_coi_boundary_state_files_v1,
)
from src.backtest.mv2_research_wiring_v1 import (
    STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1,
    _ensure_supported_instrument,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    parse_capital_risk_sizing_backtest_state_file_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_capital_context_v0,
    default_offline_replay_instrument_v0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    build_mv2_dynamic_boundary_capital_context_v1,
    build_mv2_offline_boundary_dynamic_price_context_v1,
    validate_dynamic_price_context_binding_ref_v0,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)


def test_current_admission_accepts_okx_eea_identity() -> None:
    _ensure_supported_instrument(
        "okx_eea:linear_perpetual:0G:USDT:USDT:0g-usdt-swap",
        admission_mode=STEP29L_INSTRUMENT_ADMISSION_CURRENT_SELECTED_INSTRUMENT_V1,
    )


def test_dynamic_price_context_matches_integrated_replay_semantics() -> None:
    ctx = build_mv2_offline_boundary_dynamic_price_context_v1(
        mark_price=Decimal("123.45"),
        selected_side="LONG",
        adverse_exit_distance=Decimal("2.5"),
    )
    assert ctx.reference_price == Decimal("123.45")
    assert ctx.protective_stop_price == Decimal("120.95")


def test_materialized_state_file_uses_dynamic_binding_without_static_prices(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "instrument_id": "okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
                "instrument_metadata": {
                    "lotSz": "0.1",
                    "tickSz": "0.001",
                    "minSz": "0.1",
                },
            }
        ),
        encoding="utf-8",
    )
    result = materialize_current_instrument_crs_coi_boundary_state_files_v1(
        canonical_instrument_id="okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
        dataset_manifest_path=manifest,
        output_dir=tmp_path / "boundary",
        account_equity="10000",
    )
    crs = json.loads(result.capital_risk_sizing_path.read_text(encoding="utf-8"))
    assert crs["dynamic_price_context_binding_ref"] == (
        MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1
    )
    assert "reference_price" not in crs
    assert "protective_stop_price" not in crs
    assert "daily_loss_remaining_budget" not in crs
    assert "maximum_quantity" not in crs
    record = parse_capital_risk_sizing_backtest_state_file_v0(path=result.capital_risk_sizing_path)
    assert record.dynamic_price_context_binding_ref == (
        MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1
    )


def test_dynamic_payload_forbids_digest_pinned_daily_loss_and_max_quantity() -> None:
    payload = {
        "dynamic_price_context_binding_ref": MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
        "daily_loss_remaining_budget": "25",
    }
    with pytest.raises(ValueError, match="dynamic_boundary_forbidden_static_field:daily_loss"):
        validate_dynamic_price_context_binding_ref_v0(payload)


def test_current_dynamic_boundary_excludes_offline_adapter_fixture_scalars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 as crs_adapter

    monkeypatch.setattr(crs_adapter, "_DEFAULT_DAILY_LOSS_BUDGET", Decimal("999"))

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
        capital_risk_sizing_owner_digest_ref=CAPITAL_RISK_SIZING_CONTRACT_VERSION,
        state_file_digest_ref="0" * 64,
        dynamic_price_context_binding_ref=MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    )
    dynamic = build_mv2_offline_boundary_dynamic_price_context_v1(
        mark_price=Decimal("100"),
        selected_side="LONG",
        adverse_exit_distance=Decimal("1"),
    )
    ctx = build_mv2_dynamic_boundary_capital_context_v1(
        state_file=state,
        dynamic_price_context=dynamic,
    )
    assert ctx.daily_loss_remaining_budget == Decimal("40")
    assert ctx.daily_loss_remaining_budget != Decimal("999")
    assert ctx.instrument.maximum_quantity is None

    replay_fixture = default_offline_replay_capital_context_v0(
        instrument_id="okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
        reference_price=Decimal("100"),
        protective_stop_price=Decimal("99"),
    )
    assert replay_fixture.daily_loss_remaining_budget == Decimal("999")
    assert replay_fixture.instrument.maximum_quantity == Decimal("100")


def test_materialization_fail_closed_on_manifest_identity_mismatch(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"instrument_id": "okx_eea:linear_perpetual:OTHER:USDT:USDT:other-swap"}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="dataset_manifest_instrument_identity_mismatch"):
        materialize_current_instrument_crs_coi_boundary_state_files_v1(
            canonical_instrument_id="okx_eea:linear_perpetual:TEST:USDT:USDT:test-usdt-swap",
            dataset_manifest_path=manifest,
            output_dir=tmp_path / "boundary",
            account_equity="10000",
        )
