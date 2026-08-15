"""Structural dedicated funding-accounting contract rows (read-only).

Numerics are not invented. Activation remains unauthorized. G16 stays open.
"""

from __future__ import annotations

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    ContractRowV1,
    R12EgI44FundError,
)

_CP = ContractItemStatus.CLOSED_PROVEN
_CB = ContractItemStatus.CLOSED_BOUNDARY
_NRA = ContractItemStatus.NOT_REQUIRED_UNTIL_ACTIVATION

REQUIRED_CONTRACT_ITEM_IDS = (
    "instrument_identity",
    "venue",
    "funding_timestamp_settlement_interval",
    "funding_rate_source",
    "position_quantity_exposure_at_settlement",
    "direction_sign_convention",
    "payment_formula",
    "quote_base_currency_semantics",
    "actual_vs_estimated_funding",
    "deduplication_idempotency",
    "missing_payment_handling",
    "duplicate_payment_handling",
    "late_out_of_order_funding_events",
    "reconciliation_against_venue_account_truth",
    "restart_persistence_reconstruction",
    "realized_pnl_interaction",
    "fee_separation",
    "account_portfolio_aggregation",
    "evidence_identity_lineage",
    "verifier_semantics",
    "fail_closed_behavior",
)


def _row(
    item_id: str,
    *,
    family: str,
    status: ContractItemStatus,
    current_binding: str,
    owner: str,
    g16_relevance: str,
    later_requirement: str,
) -> ContractRowV1:
    return ContractRowV1(
        item_id=item_id,
        family=family,
        status=status,
        current_binding=current_binding,
        owner=owner,
        g16_relevance=g16_relevance,
        later_requirement=later_requirement,
    )


STRUCTURAL_CONTRACT: tuple[ContractRowV1, ...] = (
    _row(
        "instrument_identity",
        family="IDENTITY",
        status=_CP,
        current_binding="single selected future identity via Cap2.3/2.4; Package-N SHA256 join already CLOSED_PROVEN",
        owner="Cap2.4 + EG-I82-JOIN",
        g16_relevance="required_input",
        later_requirement="same identity plane on funding events when activated",
    ),
    _row(
        "venue",
        family="IDENTITY",
        status=_CB,
        current_binding="OKX Europe XPerp is productive venue binding; funding venue-event ingest absent",
        owner="ops.bounded_futures_testnet_venue_binding_v0",
        g16_relevance="required_input",
        later_requirement="venue funding event identity when activated",
    ),
    _row(
        "funding_timestamp_settlement_interval",
        family="TIME",
        status=_CB,
        current_binding="backtest funding_model_v1 DEFAULT_PAYMENT_INTERVAL_HOURS=8 is research/backtest; not productive grant",
        owner="S2_contract_not_numeric_grant",
        g16_relevance="required_when_activated",
        later_requirement="venue settlement clock; no invented interval as SSOT",
    ),
    _row(
        "funding_rate_source",
        family="INPUT",
        status=_CB,
        current_binding="research/CMC observation only; productive accounting must not silently use hardcoded 0.0001",
        owner="FUNDING_OBSERVATION_OWNER_NON_AUTHORITY",
        g16_relevance="required_when_activated",
        later_requirement="explicit venue rate source + lineage",
    ),
    _row(
        "position_quantity_exposure_at_settlement",
        family="POSITION",
        status=_CB,
        current_binding="Cap3.1 position snapshot exists; settlement-aligned quantity not applied for funding",
        owner="ops.productive_futures_accounting_runtime_binding_v1",
        g16_relevance="required_when_activated",
        later_requirement="snapshot at applicable settlement, not fill-time only",
    ),
    _row(
        "direction_sign_convention",
        family="FORMULA",
        status=_CP,
        current_binding="kernel: funding_rate>0 means long pays short; backtest LONG_SHORT_SIGN_SEMANTICS=long_pays_positive_rate; I17 shadow longs pay positive — helpers only",
        owner="src.execution.paper.futures_accounting.funding_payment_quote",
        g16_relevance="reuse_candidate_must_remain_single_convention",
        later_requirement="do not fork sign convention across Cap3.1 / I17 / backtest",
    ),
    _row(
        "payment_formula",
        family="FORMULA",
        status=_CB,
        current_binding="quote payment = +/- rate * notional in funding_payment_quote; Cap3.1 does not call it",
        owner="src.execution.paper.futures_accounting",
        g16_relevance="reuse_candidate",
        later_requirement="wire behind activation GO; no second formula owner",
    ),
    _row(
        "quote_base_currency_semantics",
        family="CURRENCY",
        status=_CB,
        current_binding="kernel pays in quote currency; EG-EV-CURRENCY remains a separate evidence gap and is not G16 proof",
        owner="FuturesInstrumentSpec.quote_currency",
        g16_relevance="required_when_activated",
        later_requirement="currency lineage on funding evidence; do not invent FX",
    ),
    _row(
        "actual_vs_estimated_funding",
        family="TRUTH",
        status=_CP,
        current_binding="estimated=helper/backtest; actual=venue/account event; actual currently MISSING; estimate must not be claimed as actual",
        owner="S2_contract",
        g16_relevance="core_g16_distinction",
        later_requirement="both legs required for G16 closeout",
    ),
    _row(
        "deduplication_idempotency",
        family="EVENTS",
        status=_CB,
        current_binding="backtest model has DUPLICATE_FUNDING_EVENT reason; productive path has no funding event log",
        owner="src.backtest.funding_model_v1 as REUSE_CANDIDATE_NON_AUTHORITY",
        g16_relevance="required_when_activated",
        later_requirement="idempotent apply on Cap3.1 writer only",
    ),
    _row(
        "missing_payment_handling",
        family="EVENTS",
        status=_CP,
        current_binding="authority contract=fail-closed; implicit zero funding forbidden; backtest MISSING_FUNDING_RATE already fail-closed",
        owner="S2_contract + backtest.funding_model_v1",
        g16_relevance="required_when_activated",
        later_requirement="must remain fail-closed; no silent 0",
    ),
    _row(
        "duplicate_payment_handling",
        family="EVENTS",
        status=_CB,
        current_binding="backtest DUPLICATE_FUNDING_EVENT; productive none",
        owner="reuse_candidate_non_authority",
        g16_relevance="required_when_activated",
        later_requirement="reject or idempotent-skip with evidence; never double-apply",
    ),
    _row(
        "late_out_of_order_funding_events",
        family="EVENTS",
        status=_CB,
        current_binding="backtest OUT_OF_ORDER_FUNDING_EVENT; productive none",
        owner="reuse_candidate_non_authority",
        g16_relevance="required_when_activated",
        later_requirement="fail-closed or governed reorder with evidence",
    ),
    _row(
        "reconciliation_against_venue_account_truth",
        family="RECON",
        status=_NRA,
        current_binding="Cap1.1 recon has no funding fields; funding recon owner=NONE_PRODUCTIVE",
        owner="NONE_PRODUCTIVE",
        g16_relevance="required_for_g16_closeout",
        later_requirement="extend Cap1.1 derived recon; no second recon writer",
    ),
    _row(
        "restart_persistence_reconstruction",
        family="RESTART",
        status=_CB,
        current_binding="Cap3.1 persists funding_pnl field and reloads it; application path absent so reconstruction of payments is not proven",
        owner="ops.productive_futures_accounting_runtime_binding_v1",
        g16_relevance="field_roundtrip_not_payment_proof",
        later_requirement="persist applied funding events then reconstruct",
    ),
    _row(
        "realized_pnl_interaction",
        family="PNL",
        status=_CP,
        current_binding="kernel keeps realized_pnl and funding_pnl as separate fields; apply_funding_payment does not mutate realized_pnl or fees_paid",
        owner="src.execution.paper.futures_accounting",
        g16_relevance="must_preserve_separation",
        later_requirement="do not fold funding into realized silently",
    ),
    _row(
        "fee_separation",
        family="PNL",
        status=_CP,
        current_binding="fees_paid is a distinct field; Cap3.1 applies fees on fills; funding must remain separate",
        owner="Cap3.1 + kernel",
        g16_relevance="must_preserve_separation",
        later_requirement="preserve at activation",
    ),
    _row(
        "account_portfolio_aggregation",
        family="AGGREGATE",
        status=_CB,
        current_binding="Cap3.1 single writer aggregates position state; funding_pnl copied; derived unless explicit; N=1",
        owner="productive_futures_accounting_portfolio_writer_v1",
        g16_relevance="derived_only",
        later_requirement="no second accounting writer for funding",
    ),
    _row(
        "evidence_identity_lineage",
        family="EVIDENCE",
        status=_CP,
        current_binding="this overlay + Package-N join; comparison-gates G16 is distinct identity",
        owner="ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1",
        g16_relevance="contract_identity_not_proof",
        later_requirement="funding event lineage on future pack",
    ),
    _row(
        "verifier_semantics",
        family="EVIDENCE",
        status=_CP,
        current_binding="this overlay fail-closed rejects G16_CLOSED=true, activation, live-proof, MF, canary, numeric invention",
        owner="verifier_v1",
        g16_relevance="structural_only",
        later_requirement="separate productive G16 verifier after activation evidence",
    ),
    _row(
        "fail_closed_behavior",
        family="SAFETY",
        status=_CP,
        current_binding="OD-I44 keep gap; claims false; implicit zero forbidden; research≠proof; OUT_OF_SCOPE_FOREVER=false",
        owner="Master G16 + OD-I44",
        g16_relevance="current_gate",
        later_requirement="remain fail-closed until dedicated pack + Owner activation GO",
    ),
)


def require_contract_item(item_id: str) -> ContractRowV1:
    for row in STRUCTURAL_CONTRACT:
        if row.item_id == item_id:
            return row
    raise R12EgI44FundError(f"unknown_structural_item:{item_id}")
