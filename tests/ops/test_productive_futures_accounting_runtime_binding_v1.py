"""Capability 3.1 — productive futures accounting runtime binding tests."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution.paper import futures_accounting as fa
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    AccountingEngineError,
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.authority_inventory_v1 import (
    inventory_accounting_authority_surfaces_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    apply_intended_action_via_canonical_accounting_v1,
    ensure_accounting_session_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_AFTER,
    CALL_GRAPH_BEFORE,
    CALL_GRAPH_STEP,
    CANONICAL_KERNEL_PATH,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
    PACKAGE_MARKER,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    FillModelError,
    build_simulated_fill_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.models_v1 import (
    ContractMetadataV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.persistence_v1 import (
    PersistenceInterruptionError,
    load_accounting_session,
    persist_accounting_bundle_atomic_v1,
    verify_manifest,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.reason_codes_v1 import (
    AccountingFailureCodeV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductiveFuturesAccountingSingleWriterV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    CALL_GRAPH_V1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.full_economic_reconstruction_verifier_v1 import (
    REQUIRED_CALL_GRAPH,
)

REPO_SHA = "9f294a2d459812a54f376180494e25eeebed8fa0"


def _contract(
    symbol: str = "ETH-USDT-SWAP",
    *,
    contract_size: str = "0.01",
    tick: str = "0.01",
    min_qty: str = "1",
) -> ContractMetadataV1:
    return ContractMetadataV1(
        symbol=symbol,
        contract_size=Decimal(contract_size),
        tick_size=Decimal(tick),
        min_qty=Decimal(min_qty),
        quote_currency="USDT",
        initial_margin_rate=Decimal("0.10"),
        maintenance_margin_rate=Decimal("0.05"),
        max_leverage=Decimal("10"),
    )


def _session(**kwargs) -> ProductiveFuturesAccountingSessionV1:
    return ProductiveFuturesAccountingSessionV1(contract=_contract(**kwargs))


def _fill(
    session: ProductiveFuturesAccountingSessionV1,
    *,
    fill_id: str,
    side: str,
    qty: str,
    mark: str,
    reduce_only: bool = False,
):
    return build_simulated_fill_v1(
        fill_id=fill_id,
        instrument_id=session.contract.symbol,
        side=side,
        quantity=Decimal(qty),
        mark_price=Decimal(mark),
        contract=session.contract,
        reduce_only=reduce_only,
    )


def test_constants_and_call_graph_bound() -> None:
    assert CAPABILITY_ID == "CAPABILITY_3_1_PRODUCTIVE_FUTURES_ACCOUNTING_RUNTIME_BINDING_V1"
    assert FUTURES_ACCOUNTING_RUNTIME_BOUND is True
    assert CORE_LOGIC_CHANGE is False
    assert PACKAGE_MARKER.endswith("=true")
    assert CALL_GRAPH_STEP in CALL_GRAPH_AFTER
    assert CALL_GRAPH_STEP in CALL_GRAPH_V1
    assert CALL_GRAPH_V1 == REQUIRED_CALL_GRAPH
    assert CALL_GRAPH_AFTER.index("canonical_futures_accounting") > CALL_GRAPH_AFTER.index(
        "simulated_fill_fee_slippage"
    )
    assert CALL_GRAPH_AFTER.index("session_persistent_portfolio") > CALL_GRAPH_AFTER.index(
        "canonical_futures_accounting"
    )
    assert "canonical_futures_accounting" not in CALL_GRAPH_BEFORE


def test_canonical_kernel_reused_not_duplicated() -> None:
    inv = inventory_accounting_authority_surfaces_v1()
    assert inv["canonical_kernel_reused"] is True
    assert inv["second_accounting_kernel_created"] is False
    assert inv["canonical_kernel_path"] == CANONICAL_KERNEL_PATH
    assert Path(CANONICAL_KERNEL_PATH).is_file()
    assert hasattr(fa, "reduce_position")
    assert hasattr(fa, "unrealized_pnl")
    assert hasattr(fa, "realize_pnl_on_close")


def test_long_open_close_realized_unrealized_contract_multiplier() -> None:
    session = _session(contract_size="0.01")
    open_fill = build_simulated_fill_v1(
        fill_id="f1",
        instrument_id=session.contract.symbol,
        side="BUY",
        quantity=Decimal("10"),
        mark_price=Decimal("100"),
        contract=session.contract,
        slippage_bps=Decimal("0"),
        fee_rate_bps=Decimal("0"),
    )
    open_r = session.apply_fill(open_fill)
    assert open_r.ok
    assert open_r.action_code == "LONG_OPEN"
    assert session.position is not None
    assert session.position.qty == Decimal("10")
    # Unrealized: (101-100)*10*0.01 = 0.1 with zero-slip entry
    mtm = session.mark_to_market(Decimal("101"))
    assert mtm.portfolio_state.unrealized_pnl == Decimal("0.1")
    assert mtm.risk_state.notional == Decimal("10") * Decimal("101") * Decimal("0.01")
    close_fill = build_simulated_fill_v1(
        fill_id="f2",
        instrument_id=session.contract.symbol,
        side="SELL",
        quantity=Decimal("10"),
        mark_price=Decimal("102"),
        contract=session.contract,
        slippage_bps=Decimal("0"),
        fee_rate_bps=Decimal("2"),
    )
    close_r = session.apply_fill(close_fill)
    assert close_r.action_code == "LONG_CLOSE"
    assert session.position is None
    assert session.realized_pnl > 0
    assert close_r.portfolio_state.cumulative_fees > 0


def test_short_open_close() -> None:
    session = _session()
    session.apply_fill(_fill(session, fill_id="s1", side="SELL", qty="5", mark="200"))
    assert session.position is not None
    assert session.position.side.value == "short"
    session.apply_fill(_fill(session, fill_id="s2", side="BUY", qty="5", mark="190"))
    assert session.position is None
    assert session.realized_pnl > 0


def test_partial_reduce_fees_slippage() -> None:
    session = _session()
    session.apply_fill(_fill(session, fill_id="p1", side="BUY", qty="10", mark="50"))
    r = session.apply_fill(_fill(session, fill_id="p2", side="SELL", qty="4", mark="55"))
    assert r.action_code == "LONG_REDUCE"
    assert session.position is not None
    assert session.position.qty == Decimal("6")
    assert r.portfolio_state.cumulative_fees > 0
    assert r.portfolio_state.cumulative_slippage > 0


def test_mark_price_movement_unrealized() -> None:
    session = _session(contract_size="1")
    session.apply_fill(_fill(session, fill_id="m1", side="BUY", qty="1", mark="100"))
    u1 = session.mark_to_market(Decimal("100")).portfolio_state.unrealized_pnl
    u2 = session.mark_to_market(Decimal("110")).portfolio_state.unrealized_pnl
    assert u1 == Decimal("0") or abs(u1) < Decimal("1")  # slippage on entry may skew entry
    assert u2 > u1


def test_idempotency_and_duplicate_fill() -> None:
    session = _session()
    f = _fill(session, fill_id="dup1", side="BUY", qty="2", mark="10")
    r1 = session.apply_fill(f)
    r2 = session.apply_fill(f)
    assert r1.ok and r2.ok
    assert r2.idempotent_replay is True
    assert r2.action_code == "IDEMPOTENT_REPLAY"
    assert session.position is not None
    assert session.position.qty == Decimal("2")
    assert len(session.fill_order) == 1


def test_restart_semantics(tmp_path: Path) -> None:
    session = _session()
    session.apply_fill(_fill(session, fill_id="r1", side="BUY", qty="3", mark="20"))
    before = session.portfolio_state().digest()
    writer = ProductiveFuturesAccountingSingleWriterV1(state_root=tmp_path, session_id="s1")
    writer.acquire()
    persist_accounting_bundle_atomic_v1(state_root=tmp_path, session=session, writer=writer)
    writer.release()
    verify_manifest(tmp_path)
    reloaded = load_accounting_session(tmp_path, require_present=True)
    assert reloaded is not None
    assert reloaded.portfolio_state().digest() == before
    # Idempotent replay after restart
    again = reloaded.apply_fill(_fill(reloaded, fill_id="r1", side="BUY", qty="3", mark="20"))
    assert again.idempotent_replay is True


def test_zero_quantity_invalid_contract_missing_mark() -> None:
    session = _session()
    with pytest.raises(FillModelError) as z:
        build_simulated_fill_v1(
            fill_id="z",
            instrument_id=session.contract.symbol,
            side="BUY",
            quantity=Decimal("0"),
            mark_price=Decimal("1"),
            contract=session.contract,
        )
    assert z.value.code == AccountingFailureCodeV1.ZERO_QUANTITY

    with pytest.raises(FillModelError) as m:
        build_simulated_fill_v1(
            fill_id="m",
            instrument_id=session.contract.symbol,
            side="BUY",
            quantity=Decimal("1"),
            mark_price=None,
            contract=session.contract,
        )
    assert m.value.code == AccountingFailureCodeV1.MISSING_MARK_PRICE

    with pytest.raises(AccountingEngineError) as c:
        ProductiveFuturesAccountingSessionV1(
            contract=ContractMetadataV1(
                symbol="",
                contract_size=Decimal("1"),
                tick_size=Decimal("0.01"),
                min_qty=Decimal("1"),
                quote_currency="USDT",
                initial_margin_rate=Decimal("0.10"),
                maintenance_margin_rate=Decimal("0.05"),
                max_leverage=Decimal("10"),
            )
        )
    assert c.value.code == AccountingFailureCodeV1.INVALID_CONTRACT_METADATA


def test_reduce_only_over_reduce_flip_blocked() -> None:
    session = _session()
    session.apply_fill(_fill(session, fill_id="x1", side="BUY", qty="5", mark="10"))
    with pytest.raises(AccountingEngineError) as ro:
        session.apply_fill(
            _fill(session, fill_id="x2", side="BUY", qty="1", mark="10", reduce_only=True)
        )
    assert ro.value.code == AccountingFailureCodeV1.REDUCE_ONLY_VIOLATION

    with pytest.raises(AccountingEngineError) as ov:
        session.apply_fill(_fill(session, fill_id="x3", side="SELL", qty="9", mark="10"))
    assert ov.value.code == AccountingFailureCodeV1.OVER_REDUCE

    # Exact close then reopen; oversize opposite fill is over-reduce / flip-blocked.
    session.apply_fill(_fill(session, fill_id="x4", side="SELL", qty="5", mark="10"))
    assert session.position is None
    session.apply_fill(_fill(session, fill_id="x5", side="BUY", qty="2", mark="10"))
    with pytest.raises(AccountingEngineError) as fl:
        session.apply_fill(_fill(session, fill_id="x6", side="SELL", qty="3", mark="10"))
    assert fl.value.code in {
        AccountingFailureCodeV1.OVER_REDUCE,
        AccountingFailureCodeV1.POSITION_FLIP_BLOCKED,
    }


def test_rounding_edge_case_tick_quantize() -> None:
    session = _session(tick="0.01", min_qty="1")
    f = build_simulated_fill_v1(
        fill_id="tick1",
        instrument_id=session.contract.symbol,
        side="BUY",
        quantity=Decimal("1"),
        mark_price=Decimal("100.004"),
        contract=session.contract,
        slippage_bps=Decimal("0"),
    )
    # fill price quantized to tick
    assert f.fill_price == Decimal("100.00") or f.fill_price == Decimal("100.00")


def test_non_representable_quantity() -> None:
    session = _session(min_qty="1")
    with pytest.raises(FillModelError) as e:
        build_simulated_fill_v1(
            fill_id="nr",
            instrument_id=session.contract.symbol,
            side="BUY",
            quantity=Decimal("1.5"),
            mark_price=Decimal("10"),
            contract=session.contract,
        )
    assert e.value.code == AccountingFailureCodeV1.NON_REPRESENTABLE_QUANTITY


def test_conflicting_writer_and_persistence_interruption(tmp_path: Path) -> None:
    session = _session()
    session.apply_fill(_fill(session, fill_id="w1", side="BUY", qty="1", mark="10"))
    w1 = ProductiveFuturesAccountingSingleWriterV1(state_root=tmp_path, session_id="a")
    w1.acquire()
    w2 = ProductiveFuturesAccountingSingleWriterV1(state_root=tmp_path, session_id="b")
    with pytest.raises(ConflictingWriterError):
        w2.acquire()
    with pytest.raises(PersistenceInterruptionError):
        persist_accounting_bundle_atomic_v1(
            state_root=tmp_path,
            session=session,
            writer=w1,
            interrupt_after_fill_before_accounting=True,
        )
    # Successful persist after interruption flag cleared
    out = persist_accounting_bundle_atomic_v1(state_root=tmp_path, session=session, writer=w1)
    assert out["ok"] is True
    w1.release()


def test_bridge_binding_applies_kernel_and_projects_portfolio() -> None:
    session = ensure_accounting_session_v1(
        instrument_id="ETH-USDT-SWAP",
        state_root=None,
        contract=_contract("ETH-USDT-SWAP"),
    )
    portfolio = SimulatedPortfolioEconomicsModelV1()
    applied = apply_intended_action_via_canonical_accounting_v1(
        session=session,
        portfolio=portfolio,
        instrument_id="ETH-USDT-SWAP",
        side="BUY",
        quantity=Decimal("2"),
        mark_price=Decimal("100"),
        session_id="bridge",
        cycle_index=1,
        persist=False,
    )
    assert applied["ok"] is True
    assert applied["fill"] is not None
    assert applied["call_graph_step"] == CALL_GRAPH_STEP
    assert portfolio.state.fill_count == 1
    assert "ETH-USDT-SWAP" in portfolio.state.positions
    assert SINGLE_WRITER_IDENTITY


def test_cap24_entrypoint_call_graph_includes_accounting() -> None:
    """Runtime reachability marker: Cap 2.4 productive call graph hosts Cap 3.1 step."""
    from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import CALL_GRAPH

    assert "canonical_futures_accounting" in CALL_GRAPH
    assert CALL_GRAPH.index("canonical_futures_accounting") > CALL_GRAPH.index(
        "simulated_fill_fee_slippage"
    )
