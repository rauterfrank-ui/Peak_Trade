"""Portfolio-risk binding that consumes R6-S2 contracts.

Can only restrict or block. Cannot create order authority.
"""

from __future__ import annotations

from decimal import Decimal

from src.ops.canonical_r6_s2_portfolio_risk_contracts_v1.verifier_v1 import (
    evaluate_r6_s2_portfolio_risk_contracts_v1,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.constants_v1 import (
    PORTFOLIO_ALLOCATOR_CANNOT_SUBMIT_ORDERS,
    PORTFOLIO_RISK_CONTRACT_OWNER,
)
from src.ops.canonical_r6_s3_multi_future_runtime_architecture_v1.models_v1 import (
    IntentV1,
    R6S3RuntimeArchitectureError,
)


def _reject(message: str) -> None:
    raise R6S3RuntimeArchitectureError(message)


def _qty(value: str) -> Decimal:
    return Decimal(str(value))


def apply_portfolio_risk_v1(
    intents: tuple[IntentV1, ...],
    *,
    authorized: bool,
    reduce_entry_qty_to: str | None = None,
) -> tuple[IntentV1, ...]:
    claims = evaluate_r6_s2_portfolio_risk_contracts_v1()
    if claims["verdict"] != "PASS_R6_S2_PORTFOLIO_RISK_CONTRACTS_V1":
        _reject("s2_portfolio_risk_contract_not_pass")
    if claims["multi_future_runtime_authorized"] is not False:
        _reject("s2_authorized_drift")
    if PORTFOLIO_ALLOCATOR_CANNOT_SUBMIT_ORDERS is not True:
        _reject("allocator_submit_doctrine_missing")
    if authorized is True:
        _reject("portfolio_risk_cannot_honor_authorized_true")
    _ = PORTFOLIO_RISK_CONTRACT_OWNER
    seen: set[str] = set()
    out: list[IntentV1] = []
    for intent in intents:
        if intent.instrument_id in seen:
            _reject(f"portfolio_duplicate_instrument:{intent.instrument_id}")
        seen.add(intent.instrument_id)
        current = intent
        if current.action in {"ENTRY", "REVERSAL"} and not current.blocked:
            if reduce_entry_qty_to is not None:
                reduced = _qty(reduce_entry_qty_to)
                if reduced < _qty(current.qty):
                    current = current.restrict(
                        qty=str(reduced),
                        reason="PORTFOLIO_RISK_REDUCED",
                        source_stage="portfolio_risk",
                    )
            if _qty(current.qty) == 0:
                current = current.restrict(
                    qty="0",
                    reason="PORTFOLIO_RISK_BLOCKED",
                    block=True,
                    source_stage="portfolio_risk",
                )
        if current.blocked is False and current.action in {"ENTRY", "REVERSAL"}:
            # Portfolio risk still cannot mint submit permission.
            current = IntentV1(
                instrument_id=current.instrument_id,
                action=current.action,
                side=current.side,
                qty=current.qty,
                blocked=current.blocked,
                block_reasons=current.block_reasons,
                sequence=current.sequence,
                source_stage="portfolio_risk",
            )
        out.append(current)
    return tuple(sorted(out, key=lambda row: (row.instrument_id, row.sequence)))
