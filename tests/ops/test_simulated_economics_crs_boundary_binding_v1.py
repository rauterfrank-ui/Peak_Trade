"""Contract: simulated-economics bridge binds CRS boundary for integrated replay."""

from __future__ import annotations

from decimal import Decimal

from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.simulated_economics_crs_boundary_binding_v1 import (
    DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY,
    build_simulated_economics_crs_boundary_state_file_v1,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    build_mv2_dynamic_boundary_capital_context_v1,
    build_mv2_offline_boundary_dynamic_price_context_v1,
)


def test_simulated_economics_boundary_enables_dynamic_capital_context() -> None:
    instrument_id = "ETH-USD_UM_XPERP-310404"
    record = build_simulated_economics_crs_boundary_state_file_v1(instrument_id=instrument_id)
    assert record.dynamic_price_context_binding_ref == (
        MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1
    )
    assert Decimal(record.account_equity) == DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY
    dynamic = build_mv2_offline_boundary_dynamic_price_context_v1(
        mark_price=Decimal("3200"),
        selected_side="SHORT",
        adverse_exit_distance=Decimal("50"),
    )
    ctx = build_mv2_dynamic_boundary_capital_context_v1(
        state_file=record,
        dynamic_price_context=dynamic,
    )
    assert ctx.reference_price == dynamic.reference_price
    assert ctx.protective_stop_price == dynamic.protective_stop_price
    assert ctx.account_equity == DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY
