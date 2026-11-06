"""CRS boundary state-file binding for wallclock simulated-economics bridge (v1).

Wires digest-pinned dynamic-price boundary metadata into integrated offline replay
so Cap 7.1 / simulated economics receives CanonicalCoreRuntimeCapitalContextV0
without changing integrated replay fail-closed when no boundary is supplied.

RUNTIME_AUTHORIZATION_EFFECT=NONE — offline algebra only.
"""

from __future__ import annotations

from decimal import Decimal

from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBacktestStateFileRecordV0,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_DAILY_LOSS_REMAINING_BUDGET,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_PER_TRADE_RISK_LIMIT,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_SCOPE_CAPITAL_LIMIT,
    ISOLATED_OFFLINE_REPLAY_FIXTURE_TOTAL_CAPITAL_LIMIT,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    default_offline_replay_instrument_v0,
)
from trading.master_v2.mv2_offline_boundary_dynamic_price_context_v1 import (
    MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
)

SIMULATED_ECONOMICS_CRS_BOUNDARY_LINEAGE_REF_V1 = (
    "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1."
    "simulated_economics_crs_boundary_binding_v1.build_simulated_economics_crs_boundary_state_file_v1"
)
DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY = Decimal("100000")


def build_simulated_economics_crs_boundary_state_file_v1(
    *,
    instrument_id: str,
    account_equity: Decimal | None = None,
) -> CapitalRiskSizingBacktestStateFileRecordV0:
    """Build in-memory CRS boundary record for integrated simulated economics.

    Static limit scalars follow isolated offline replay fixture ratios scaled to
    the simulated portfolio initial equity (default 100000). Mark/stop come from
    per-cycle dynamic price context inside integrated replay.
    """
    eq = (
        account_equity if account_equity is not None else DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY
    )
    if not eq.is_finite() or eq <= 0:
        raise ValueError("simulated_economics_account_equity_invalid")
    scale = eq / ISOLATED_OFFLINE_REPLAY_FIXTURE_ACCOUNT_EQUITY
    inst = default_offline_replay_instrument_v0(instrument_id)
    return CapitalRiskSizingBacktestStateFileRecordV0(
        instrument_id=instrument_id,
        reference_price="",
        protective_stop_price="",
        account_equity=str(eq),
        scope_capital_limit=str(ISOLATED_OFFLINE_REPLAY_FIXTURE_SCOPE_CAPITAL_LIMIT * scale),
        per_trade_risk_limit=str(ISOLATED_OFFLINE_REPLAY_FIXTURE_PER_TRADE_RISK_LIMIT * scale),
        total_capital_limit=str(ISOLATED_OFFLINE_REPLAY_FIXTURE_TOTAL_CAPITAL_LIMIT * scale),
        daily_loss_remaining_budget=str(
            ISOLATED_OFFLINE_REPLAY_FIXTURE_DAILY_LOSS_REMAINING_BUDGET * scale
        ),
        current_reconciled_exposure="0",
        lot_size=str(inst.lot_size),
        minimum_quantity=str(inst.minimum_quantity),
        maximum_quantity="",
        minimum_notional=str(inst.minimum_notional),
        tick_size=str(inst.tick_size),
        maximum_positions=10,
        current_open_positions_count=0,
        reconciliation_status="RECONCILED",
        capital_risk_sizing_owner_digest_ref=CAPITAL_RISK_SIZING_CONTRACT_VERSION,
        state_file_digest_ref="0" * 64,
        dynamic_price_context_binding_ref=MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1,
    )


__all__ = [
    "DEFAULT_SIMULATED_ECONOMICS_ACCOUNT_EQUITY",
    "SIMULATED_ECONOMICS_CRS_BOUNDARY_LINEAGE_REF_V1",
    "build_simulated_economics_crs_boundary_state_file_v1",
]
