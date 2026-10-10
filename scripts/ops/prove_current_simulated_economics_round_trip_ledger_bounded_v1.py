#!/usr/bin/env python3
"""Bounded proof for CURRENT simulated economic round-trip ledger v1."""

from __future__ import annotations

import json
import sys
import time
from decimal import Decimal
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.integrated_paper_shadow_observation_session_v1.simulated_economics_round_trip_ledger_v1 import (
    ROUND_TRIP_LEDGER_SCHEMA_ID,
    SimulatedEconomicsObservabilityContextV1,
    SimulatedRoundTripLedgerCollectorV1,
    ledger_content_digest_v1,
    ledger_document_from_collector_v1,
    ledger_totals_v1,
    reconcile_ledger_against_portfolio_v1,
)

INSTRUMENT = "ETH-USD_UM_XPERP-310404"
FIXTURE_ID = "bounded_round_trip_ledger_fixture_v1"
EVIDENCE_REL = (
    "evidence/ops/integrated_offline_economic_evidence_v1/"
    "current_simulated_economics_round_trip_ledger_bounded_proof_v1"
)


def _ctx(epoch: str, decision: str = "") -> SimulatedEconomicsObservabilityContextV1:
    return SimulatedEconomicsObservabilityContextV1(
        epoch_id=f"bounded-epoch-{epoch}",
        timestamp=f"2022-12-19T00:{epoch}:00+00:00",
        entry_decision=decision,
        terminal_decision=decision,
    )


def _apply(
    portfolio: SimulatedPortfolioEconomicsModelV1,
    *,
    side: str,
    qty: str,
    mark: str,
    ctx: SimulatedEconomicsObservabilityContextV1,
) -> None:
    portfolio.apply_intended_action(
        instrument_id=INSTRUMENT,
        side=side,
        quantity=Decimal(qty),
        mark_price=Decimal(mark),
        observability_context=ctx,
    )


def run_bounded_proof_v1(*, repo_root: Path) -> dict:
    t0 = time.monotonic()
    ledger = SimulatedRoundTripLedgerCollectorV1()
    portfolio = SimulatedPortfolioEconomicsModelV1(round_trip_ledger=ledger)
    baseline = SimulatedPortfolioEconomicsModelV1(round_trip_ledger=None)

    steps = [
        ("SELL", "3", "3500", _ctx("01", "enter_short")),
        ("BUY", "1", "3480", _ctx("02", "reduce")),
        ("BUY", "2", "3470", _ctx("03", "exit_flat")),
    ]
    for side, qty, mark, ctx in steps:
        _apply(portfolio, side=side, qty=qty, mark=mark, ctx=ctx)
        baseline.apply_intended_action(
            instrument_id=INSTRUMENT,
            side=side,
            quantity=Decimal(qty),
            mark_price=Decimal(mark),
        )

    open_eco = portfolio.open_lifecycle_economics_v1()
    reconcile_ok, blockers = reconcile_ledger_against_portfolio_v1(
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
    parity_ok = portfolio.snapshot()["state"] == baseline.snapshot()["state"]
    totals = ledger_totals_v1(ledger)
    doc = ledger_document_from_collector_v1(
        ledger,
        bindings={
            "fixture_id": FIXTURE_ID,
            "schema_id": ROUND_TRIP_LEDGER_SCHEMA_ID,
            "proof_class": "BOUNDED_OBSERVABILITY_PROOF_V1",
        },
        open_position_economics=ledger.open_position_economics_snapshot(
            portfolio_state=portfolio.state.to_dict()
        ),
    )
    digest = ledger_content_digest_v1(doc)
    evidence_root = repo_root / EVIDENCE_REL
    evidence_root.mkdir(parents=True, exist_ok=True)
    artifact = evidence_root / "CURRENT_SIMULATED_ECONOMIC_ROUND_TRIP_LEDGER_V1.json"
    artifact.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    runtime = time.monotonic() - t0
    return {
        "bounded_proof_complete": reconcile_ok and parity_ok and len(ledger.rows) > 0,
        "accounting_reconciliation_pass": reconcile_ok,
        "trading_outcome_parity_pass": parity_ok,
        "reconciliation_blockers": blockers,
        "ledger_rows": len(ledger.rows),
        "ledger_totals": totals,
        "ledger_digest": digest,
        "ledger_artifact_path": str(artifact.relative_to(repo_root)),
        "bounded_proof_runtime_seconds": runtime,
        "fixture_id": FIXTURE_ID,
    }


def main() -> int:
    result = run_bounded_proof_v1(repo_root=_REPO)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["bounded_proof_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
