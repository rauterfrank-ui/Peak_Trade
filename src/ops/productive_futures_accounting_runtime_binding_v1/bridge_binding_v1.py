"""Bridge-facing productive binding: fill → canonical accounting → portfolio/risk."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
    SimulatedPositionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    AccountingEngineError,
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_STEP,
    DEFAULT_CONTRACT_SIZE,
    DEFAULT_FEE_RATE_BPS,
    DEFAULT_INITIAL_EQUITY,
    DEFAULT_INITIAL_MARGIN_RATE,
    DEFAULT_MAINTENANCE_MARGIN_RATE,
    DEFAULT_MAX_LEVERAGE,
    DEFAULT_MIN_QTY,
    DEFAULT_QUOTE_CURRENCY,
    DEFAULT_SLIPPAGE_BPS,
    DEFAULT_TICK_SIZE,
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    FillModelError,
    build_simulated_fill_v1,
    deterministic_fill_id_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    ContractMetadataV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    load_accounting_session,
    persist_accounting_bundle_atomic_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductiveFuturesAccountingSingleWriterV1,
)


def default_contract_metadata_v1(*, symbol: str) -> ContractMetadataV1:
    return ContractMetadataV1(
        symbol=symbol,
        contract_size=Decimal(DEFAULT_CONTRACT_SIZE),
        tick_size=Decimal(DEFAULT_TICK_SIZE),
        min_qty=Decimal(DEFAULT_MIN_QTY),
        quote_currency=DEFAULT_QUOTE_CURRENCY,
        initial_margin_rate=Decimal(DEFAULT_INITIAL_MARGIN_RATE),
        maintenance_margin_rate=Decimal(DEFAULT_MAINTENANCE_MARGIN_RATE),
        max_leverage=Decimal(DEFAULT_MAX_LEVERAGE),
    )


def ensure_accounting_session_v1(
    *,
    instrument_id: str,
    state_root: Optional[Path],
    contract: Optional[ContractMetadataV1] = None,
    initial_equity: Decimal | str = DEFAULT_INITIAL_EQUITY,
) -> ProductiveFuturesAccountingSessionV1:
    meta = contract or default_contract_metadata_v1(symbol=instrument_id)
    if state_root is not None:
        loaded = load_accounting_session(Path(state_root), require_present=False)
        if loaded is not None:
            return loaded
    return ProductiveFuturesAccountingSessionV1(
        contract=meta,
        initial_equity=Decimal(str(initial_equity)),
        writer_identity=SINGLE_WRITER_IDENTITY,
    )


def sync_portfolio_shell_from_accounting_v1(
    portfolio: SimulatedPortfolioEconomicsModelV1,
    session: ProductiveFuturesAccountingSessionV1,
) -> None:
    """Project canonical accounting results into the analytical portfolio shell."""
    acct = session.portfolio_state()
    portfolio.state.realized_pnl = acct.realized_pnl
    portfolio.state.unrealized_pnl = acct.unrealized_pnl
    portfolio.state.cumulative_fees = acct.cumulative_fees
    portfolio.state.cumulative_slippage = acct.cumulative_slippage
    portfolio.state.fill_count = acct.fill_count
    portfolio.state.equity = acct.equity
    portfolio.state.cash = (
        acct.initial_equity + acct.realized_pnl - acct.cumulative_fees - acct.cumulative_slippage
    )
    portfolio.state.peak_equity = max(portfolio.state.peak_equity, acct.equity)
    portfolio.state.positions.clear()
    for pos in acct.positions:
        signed = pos.quantity if pos.side == "long" else -pos.quantity
        portfolio.state.positions[pos.symbol] = SimulatedPositionV1(
            instrument_id=pos.symbol,
            quantity=signed,
            avg_entry_price=pos.entry_price,
            realized_pnl=pos.realized_pnl,
            unrealized_pnl=pos.unrealized_pnl,
        )


def apply_intended_action_via_canonical_accounting_v1(
    *,
    session: ProductiveFuturesAccountingSessionV1,
    portfolio: SimulatedPortfolioEconomicsModelV1,
    instrument_id: str,
    side: str,
    quantity: Decimal,
    mark_price: Decimal,
    session_id: str,
    cycle_index: int,
    reduce_only: bool = False,
    state_root: Optional[Path] = None,
    persist: bool = False,
    writer_session_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Productive path:
      intended action → simulated fill (fee/slippage) → canonical futures accounting
      → portfolio/risk state projection (and optional atomic persist).
    """
    side_u = str(side or "").strip().upper()
    if side_u in {"", "HOLD", "NONE", "FLAT"}:
        mtm = session.mark_to_market(mark_price)
        sync_portfolio_shell_from_accounting_v1(portfolio, session)
        portfolio.state.intended_action_count += 1
        return {
            "ok": True,
            "fill": None,
            "accounting": mtm.to_dict(),
            "call_graph_step": CALL_GRAPH_STEP,
            "futures_accounting_runtime_bound": FUTURES_ACCOUNTING_RUNTIME_BOUND,
        }

    # Deterministic lot quantization before fill construction (bridge productive path).
    raw_qty = Decimal(str(quantity))
    steps = (raw_qty / session.contract.min_qty).to_integral_value(rounding=ROUND_HALF_EVEN)
    qty = steps * session.contract.min_qty
    if qty <= 0:
        mtm = session.mark_to_market(mark_price)
        sync_portfolio_shell_from_accounting_v1(portfolio, session)
        portfolio.state.intended_action_count += 1
        return {
            "ok": True,
            "fill": None,
            "accounting": mtm.to_dict(),
            "call_graph_step": CALL_GRAPH_STEP,
            "futures_accounting_runtime_bound": FUTURES_ACCOUNTING_RUNTIME_BOUND,
            "notes": ["QUANTITY_QUANTIZED_TO_ZERO_HOLD"],
        }

    fill_id = deterministic_fill_id_v1(
        session_id=session_id,
        cycle_index=cycle_index,
        instrument_id=instrument_id,
        side=side_u,
        quantity=str(qty),
        mark_price=str(mark_price),
    )
    try:
        fill = build_simulated_fill_v1(
            fill_id=fill_id,
            instrument_id=session.contract.symbol,
            side=side_u,
            quantity=qty,
            mark_price=mark_price,
            contract=session.contract,
            fee_rate_bps=portfolio.params.fee_rate_bps
            if portfolio.params.fee_rate_bps is not None
            else DEFAULT_FEE_RATE_BPS,
            slippage_bps=portfolio.params.slippage_bps
            if portfolio.params.slippage_bps is not None
            else DEFAULT_SLIPPAGE_BPS,
            reduce_only=reduce_only,
        )
        result = session.apply_fill(fill)
    except (FillModelError, AccountingEngineError) as exc:
        raise RuntimeError(str(exc)) from exc

    sync_portfolio_shell_from_accounting_v1(portfolio, session)
    portfolio.state.intended_action_count += 1
    portfolio.state.turnover_notional += fill.notional

    persist_result = None
    if persist and state_root is not None:
        writer = ProductiveFuturesAccountingSingleWriterV1(
            state_root=Path(state_root),
            session_id=writer_session_id or session_id,
        )
        try:
            writer.acquire()
            persist_result = persist_accounting_bundle_atomic_v1(
                state_root=Path(state_root),
                session=session,
                writer=writer,
            )
        except ConflictingWriterError as exc:
            raise RuntimeError(str(exc)) from exc
        finally:
            writer.release()

    return {
        "ok": True,
        "fill": fill.to_dict(),
        "accounting": result.to_dict(),
        "persist": persist_result,
        "call_graph_step": CALL_GRAPH_STEP,
        "call_graph_before": list(CALL_GRAPH_BEFORE),
        "call_graph_after": list(CALL_GRAPH_AFTER),
        "futures_accounting_runtime_bound": FUTURES_ACCOUNTING_RUNTIME_BOUND,
        "portfolio_state_digest": session.portfolio_state().digest(),
        "risk_state_digest": session.risk_state().digest(),
    }


def contract_from_mapping_v1(payload: Mapping[str, Any], *, symbol: str) -> ContractMetadataV1:
    return ContractMetadataV1(
        symbol=symbol,
        contract_size=Decimal(str(payload.get("contract_size") or DEFAULT_CONTRACT_SIZE)),
        tick_size=Decimal(str(payload.get("tick_size") or DEFAULT_TICK_SIZE)),
        min_qty=Decimal(str(payload.get("min_qty") or DEFAULT_MIN_QTY)),
        quote_currency=str(payload.get("quote_currency") or DEFAULT_QUOTE_CURRENCY),
        initial_margin_rate=Decimal(
            str(payload.get("initial_margin_rate") or DEFAULT_INITIAL_MARGIN_RATE)
        ),
        maintenance_margin_rate=Decimal(
            str(payload.get("maintenance_margin_rate") or DEFAULT_MAINTENANCE_MARGIN_RATE)
        ),
        max_leverage=Decimal(str(payload.get("max_leverage") or DEFAULT_MAX_LEVERAGE)),
    )
