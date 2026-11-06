"""Round-trip economic ledger contract tests (observability only)."""

from __future__ import annotations

from decimal import Decimal

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.simulated_economics_round_trip_ledger_v1 import (
    SimulatedEconomicsObservabilityContextV1,
    SimulatedRoundTripLedgerCollectorV1,
    ledger_content_digest_v1,
    ledger_document_from_collector_v1,
    reconcile_ledger_against_portfolio_v1,
)

INSTRUMENT = "ETH-USD_UM_XPERP-310404"


def _ctx(
    epoch: str,
    *,
    decision: str = "",
    terminal: str = "",
    reason: str = "",
) -> SimulatedEconomicsObservabilityContextV1:
    return SimulatedEconomicsObservabilityContextV1(
        epoch_id=f"epoch-{epoch}",
        timestamp=f"2024-01-01T00:{epoch}:00+00:00",
        entry_decision=decision,
        terminal_decision=terminal,
        terminal_reason=reason,
    )


def _apply(
    portfolio: SimulatedPortfolioEconomicsModelV1,
    *,
    side: str,
    quantity: str,
    mark: str = "3500",
    ctx: SimulatedEconomicsObservabilityContextV1 | None = None,
) -> None:
    portfolio.apply_intended_action(
        instrument_id=INSTRUMENT,
        side=side,
        quantity=Decimal(quantity),
        mark_price=Decimal(mark),
        observability_context=ctx,
    )


def _portfolio_with_ledger() -> tuple[
    SimulatedPortfolioEconomicsModelV1, SimulatedRoundTripLedgerCollectorV1
]:
    ledger = SimulatedRoundTripLedgerCollectorV1()
    return SimulatedPortfolioEconomicsModelV1(round_trip_ledger=ledger), ledger


def _reconcile_ok(
    portfolio: SimulatedPortfolioEconomicsModelV1, ledger: SimulatedRoundTripLedgerCollectorV1
) -> bool:
    open_eco = portfolio.open_lifecycle_economics_v1()
    ok, _ = reconcile_ledger_against_portfolio_v1(
        collector=ledger,
        portfolio_completed_trade_count=portfolio.completed_trade_count,
        portfolio_realized_pnl=portfolio.state.realized_pnl,
        portfolio_cumulative_fees=portfolio.state.cumulative_fees,
        portfolio_cumulative_slippage=portfolio.state.cumulative_slippage,
        portfolio_cumulative_funding=portfolio.state.cumulative_funding,
        portfolio_has_open_exposure=any(
            p.quantity != 0 for p in portfolio.state.positions.values()
        ),
        open_lifecycle_fees=Decimal(open_eco["fees"]) if open_eco else Decimal("0"),
        open_lifecycle_slippage=Decimal(open_eco["slippage"]) if open_eco else Decimal("0"),
        open_lifecycle_funding=Decimal(open_eco["funding"]) if open_eco else Decimal("0"),
        open_lifecycle_gross=Decimal(open_eco["gross_realized_pnl"]) if open_eco else Decimal("0"),
    )
    return ok


def test_a_flat_long_flat_one_round_trip() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="BUY", quantity="1", ctx=_ctx("01", decision="enter_long"))
    _apply(p, side="SELL", quantity="1", mark="3600", ctx=_ctx("02", terminal="exit"))
    assert p.completed_trade_count == 1
    assert len(ledger.rows) == 1
    assert ledger.rows[0]["direction"] == "LONG"


def test_b_flat_short_flat_one_round_trip() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="SELL", quantity="2", ctx=_ctx("01", decision="enter_short"))
    _apply(p, side="BUY", quantity="2", ctx=_ctx("02", terminal="exit"))
    assert len(ledger.rows) == 1
    assert ledger.rows[0]["direction"] == "SHORT"


def test_c_partial_reduce_then_flat_one_trip_reduction_count() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="SELL", quantity="2", ctx=_ctx("01", decision="enter_short"))
    _apply(p, side="BUY", quantity="1", ctx=_ctx("02", decision="reduce"))
    _apply(p, side="BUY", quantity="1", ctx=_ctx("03", terminal="exit"))
    assert p.completed_trade_count == 1
    assert ledger.rows[0]["reduction_count"] == 1


def test_d_multiple_partial_reductions_one_trip() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="SELL", quantity="4", ctx=_ctx("01"))
    _apply(p, side="BUY", quantity="1", ctx=_ctx("02"))
    _apply(p, side="BUY", quantity="1", ctx=_ctx("03"))
    _apply(p, side="BUY", quantity="2", ctx=_ctx("04"))
    assert p.completed_trade_count == 1
    assert ledger.rows[0]["reduction_count"] == 2


def test_e_open_position_zero_completed_open_economics() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="BUY", quantity="1", ctx=_ctx("01"))
    assert p.completed_trade_count == 0
    assert len(ledger.rows) == 0
    open_doc = ledger.open_position_economics_snapshot(portfolio_state=p.state.to_dict())
    assert open_doc is not None
    assert open_doc["economics_class"] == "OPEN_POSITION_ECONOMICS"


def test_f_two_lifecycles_two_rows() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="BUY", quantity="1", ctx=_ctx("01"))
    _apply(p, side="SELL", quantity="1", ctx=_ctx("02"))
    _apply(p, side="SELL", quantity="1", ctx=_ctx("03"))
    _apply(p, side="BUY", quantity="1", ctx=_ctx("04"))
    assert p.completed_trade_count == 2
    assert len(ledger.rows) == 2
    assert ledger.rows[0]["round_trip_id"] == 1
    assert ledger.rows[1]["round_trip_id"] == 2


def test_g_reversal_close_then_open_semantics() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="SELL", quantity="2", ctx=_ctx("01", decision="enter_short"))
    _apply(p, side="BUY", quantity="3", ctx=_ctx("02", decision="reversal"))
    assert p.completed_trade_count == 1
    assert len(ledger.rows) == 1
    pos = p.state.positions[INSTRUMENT]
    assert pos.quantity > 0


def test_h_ledger_reconciles_with_portfolio_when_flat() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(p, side="SELL", quantity="3", ctx=_ctx("01"))
    _apply(p, side="BUY", quantity="1", mark="3400", ctx=_ctx("02"))
    _apply(p, side="BUY", quantity="2", mark="3450", ctx=_ctx("03"))
    assert _reconcile_ok(p, ledger)


def test_i_identical_input_identical_ledger_digest() -> None:
    def _run() -> str:
        p, ledger = _portfolio_with_ledger()
        _apply(p, side="SELL", quantity="2", ctx=_ctx("01", decision="enter_short"))
        _apply(p, side="BUY", quantity="1", ctx=_ctx("02", decision="reduce"))
        _apply(p, side="BUY", quantity="1", ctx=_ctx("03", terminal="exit"))
        doc = ledger_document_from_collector_v1(
            ledger,
            bindings={"fixture_id": "ledger_determinism_v1"},
            open_position_economics=None,
        )
        return ledger_content_digest_v1(doc)

    assert _run() == _run()


def test_j_ledger_disabled_economic_outcomes_unchanged() -> None:
    actions = [
        ("SELL", "2"),
        ("BUY", "1"),
        ("BUY", "1"),
    ]

    def _run(with_ledger: bool) -> dict:
        ledger = SimulatedRoundTripLedgerCollectorV1() if with_ledger else None
        p = SimulatedPortfolioEconomicsModelV1(round_trip_ledger=ledger)
        for side, qty in actions:
            _apply(p, side=side, quantity=qty)
        return p.snapshot()

    assert _run(False) == _run(False)
    base = _run(False)
    with_ledger = _run(True)
    assert base["state"] == with_ledger["state"]
    assert base["economic_metrics"] == with_ledger["economic_metrics"]


def test_ledger_row_fields_present() -> None:
    p, ledger = _portfolio_with_ledger()
    _apply(
        p,
        side="BUY",
        quantity="1",
        ctx=_ctx("01", decision="enter_long", reason="signal"),
    )
    _apply(p, side="SELL", quantity="1", ctx=_ctx("02", terminal="exit", reason="flat"))
    row = ledger.rows[0]
    for key in (
        "round_trip_id",
        "entry_epoch_id",
        "exit_epoch_id",
        "direction",
        "entry_price",
        "exit_price",
        "gross_realized_pnl",
        "fees",
        "slippage",
        "funding",
        "net_pnl",
        "fill_count",
        "reduction_count",
    ):
        assert key in row
