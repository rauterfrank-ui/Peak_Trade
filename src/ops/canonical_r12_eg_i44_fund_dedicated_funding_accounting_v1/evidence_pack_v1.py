"""Future G16 evidence-pack chain (read-only status, not a closeout)."""

from __future__ import annotations

from src.ops.canonical_r12_eg_i44_fund_dedicated_funding_accounting_v1.models_v1 import (
    ContractItemStatus,
    ContractRowV1,
    R12EgI44FundError,
)

_CB = ContractItemStatus.CLOSED_BOUNDARY
_INP = ContractItemStatus.IMPLEMENTED_NOT_PROVEN
_PART = ContractItemStatus.PARTIAL
_MISS = ContractItemStatus.MISSING
_NRA = ContractItemStatus.NOT_REQUIRED_UNTIL_ACTIVATION

REQUIRED_EVIDENCE_STEP_IDS = (
    "funding_observation",
    "applicable_position_snapshot",
    "expected_payment_calculation",
    "actual_venue_account_funding_event",
    "accounting_application",
    "persisted_state",
    "reconciliation",
    "restart_reload",
    "independent_reconstruction",
    "verifier_pass",
)


def _row(
    item_id: str,
    *,
    status: ContractItemStatus,
    current_binding: str,
) -> ContractRowV1:
    return ContractRowV1(
        item_id=item_id,
        family="G16_EVIDENCE_PACK",
        status=status,
        current_binding=current_binding,
        owner="future_dedicated_funding_accounting_pack",
        g16_relevance="required_for_g16_closeout",
        later_requirement="activation_go_plus_productive_evidence",
    )


EVIDENCE_PACK_CHAIN: tuple[ContractRowV1, ...] = (
    _row(
        "funding_observation",
        status=_PART,
        current_binding="research/CMC observation exists; not bound as accounting input; hardcoded 0.0001 is not source of truth",
    ),
    _row(
        "applicable_position_snapshot",
        status=_CB,
        current_binding="Cap3.1 position snapshot exists; settlement-aligned funding snapshot not produced",
    ),
    _row(
        "expected_payment_calculation",
        status=_INP,
        current_binding="funding_payment_quote + backtest funding_model_v1 exist as helpers",
    ),
    _row(
        "actual_venue_account_funding_event",
        status=_MISS,
        current_binding="no productive venue/account funding event ingest",
    ),
    _row(
        "accounting_application",
        status=_INP,
        current_binding="apply_funding_payment helper exists; Cap3.1 does not call it; I17 shadow has a distinct local helper",
    ),
    _row(
        "persisted_state",
        status=_CB,
        current_binding="funding_pnl field persists; typically 0; field≠application",
    ),
    _row(
        "reconciliation",
        status=_NRA,
        current_binding="Cap1.1 has no funding recon against venue truth",
    ),
    _row(
        "restart_reload",
        status=_CB,
        current_binding="field roundtrip exists; payment-event reconstruction unproven",
    ),
    _row(
        "independent_reconstruction",
        status=_MISS,
        current_binding="no independent funding reconstruction verifier",
    ),
    _row(
        "verifier_pass",
        status=_NRA,
        current_binding="productive G16 verifier absent; this overlay is structural only and must not PASS G16",
    ),
)


def require_evidence_step(item_id: str) -> ContractRowV1:
    for row in EVIDENCE_PACK_CHAIN:
        if row.item_id == item_id:
            return row
    raise R12EgI44FundError(f"unknown_evidence_step:{item_id}")
