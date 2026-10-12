"""Read-only Full-Core reconciliation stub (NO_PRIVATE_GET, AUTHORITY=NONE)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

CONTRACT_ID = "FULL_CORE_CAPITAL_GUARD_RECONCILIATION_STUB_V1"

OUTCOME_ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
OUTCOME_PARTIAL_FILL = "PARTIAL_FILL"
OUTCOME_ORDER_REJECTED = "ORDER_REJECTED"
OUTCOME_HALTED_UNRESOLVED = "HALTED_UNRESOLVED"
OUTCOME_TERMINAL_RECONCILED = "TERMINAL_RECONCILED"


@dataclass(frozen=True)
class FullCoreReconciliationEvidenceV1:
    account_scope: str
    environment: str
    instrument_id: str
    clordid: str
    evidence_fresh: bool
    reconciliation_complete: bool
    order_exists: bool | None
    order_state: str | None
    partial_fill_qty: str | None
    position_exposure: str | None
    pending_unknown_submission: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_scope": self.account_scope,
            "environment": self.environment,
            "instrument_id": self.instrument_id,
            "clordid": self.clordid,
            "evidence_fresh": self.evidence_fresh,
            "reconciliation_complete": self.reconciliation_complete,
            "order_exists": self.order_exists,
            "order_state": self.order_state,
            "partial_fill_qty": self.partial_fill_qty,
            "position_exposure": self.position_exposure,
            "pending_unknown_submission": self.pending_unknown_submission,
            "contract_id": CONTRACT_ID,
        }


@dataclass(frozen=True)
class FullCoreReconciliationAdjudicationV1:
    outcome: str
    reconciliation_complete: bool
    exposure_retained: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reconciliation_complete": self.reconciliation_complete,
            "exposure_retained": self.exposure_retained,
            "reasons": list(self.reasons),
            "contract_id": CONTRACT_ID,
        }


def adjudicate_full_core_entry_recovery_stub_v1(
    *,
    evidence: FullCoreReconciliationEvidenceV1,
    stub_orders: Mapping[str, Any] | None = None,
    stub_history: Mapping[str, Any] | None = None,
    stub_positions: Mapping[str, Any] | None = None,
) -> FullCoreReconciliationAdjudicationV1:
    """Offline stub adjudication only — never proves absence of submission."""
    reasons: list[str] = []
    if not evidence.evidence_fresh:
        reasons.append("STALE_EVIDENCE")
    if evidence.pending_unknown_submission:
        reasons.append("PENDING_UNKNOWN_SUBMISSION")
    if reasons:
        return FullCoreReconciliationAdjudicationV1(
            outcome=OUTCOME_HALTED_UNRESOLVED,
            reconciliation_complete=False,
            exposure_retained=True,
            reasons=tuple(reasons),
        )

    cl = evidence.clordid
    orders = stub_orders or {"data": []}
    history = stub_history or {"data": []}
    positions = stub_positions or {"data": []}

    for row in history.get("data") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("clOrdId") or "") != cl:
            continue
        state = str(row.get("state") or "")
        if state in {"canceled", "rejected"}:
            return FullCoreReconciliationAdjudicationV1(
                outcome=OUTCOME_ORDER_REJECTED,
                reconciliation_complete=True,
                exposure_retained=False,
                reasons=(),
            )

    for row in orders.get("data") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("clOrdId") or "") != cl:
            continue
        state = str(row.get("state") or "")
        if state == "partially_filled":
            return FullCoreReconciliationAdjudicationV1(
                outcome=OUTCOME_PARTIAL_FILL,
                reconciliation_complete=False,
                exposure_retained=True,
                reasons=(),
            )
        if state in {"live", "filled"}:
            return FullCoreReconciliationAdjudicationV1(
                outcome=OUTCOME_TERMINAL_RECONCILED,
                reconciliation_complete=True,
                exposure_retained=state != "filled",
                reasons=(),
            )

    _ = positions
    return FullCoreReconciliationAdjudicationV1(
        outcome=OUTCOME_ORDER_NOT_FOUND,
        reconciliation_complete=False,
        exposure_retained=False,
        reasons=("ORDER_NOT_FOUND_NOT_PROOF_OF_NO_SUBMIT",),
    )
