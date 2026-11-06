"""Offline/stub authoritative recovery adjudication for canary atomic one-shot (read-only).

Does not perform network I/O. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    STATE_HALTED_UNRESOLVED,
    STATE_RECONCILIATION_PENDING,
    STATE_TERMINAL_RECONCILED,
)

RECOVERY_CONTRACT_ID = "CANARY_ATOMIC_RECOVERY_ADJUDICATE_V1"

OUTCOME_ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
OUTCOME_ORDER_ACCEPTED_OPEN = "ORDER_ACCEPTED_OPEN"
OUTCOME_ORDER_REJECTED = "ORDER_REJECTED"
OUTCOME_PARTIAL_FILL = "PARTIAL_FILL"
OUTCOME_FILLED = "FILLED"
OUTCOME_CONTRADICTION = "RECONCILIATION_CONTRADICTION"
OUTCOME_PROVEN_NEVER_SUBMITTED = "PROVEN_NEVER_SUBMITTED"


@dataclass(frozen=True)
class CanaryRecoveryAdjudicationV1:
    outcome: str
    recommended_state: str
    exposure_retained: bool
    reconciliation_complete: bool
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "recommended_state": self.recommended_state,
            "exposure_retained": self.exposure_retained,
            "reconciliation_complete": self.reconciliation_complete,
            "evidence": dict(self.evidence),
            "contract_id": RECOVERY_CONTRACT_ID,
        }


def _find_clordid_rows(payload: Mapping[str, Any] | None, clordid: str) -> list[dict[str, Any]]:
    if payload is None:
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    rows: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        if str(row.get("clOrdId") or "") == clordid:
            rows.append(row)
    return rows


def adjudicate_canary_entry_recovery_offline_v1(
    *,
    clordid: str,
    pending_orders_payload: Mapping[str, Any] | None,
    history_payload: Mapping[str, Any] | None,
    positions_payload: Mapping[str, Any] | None,
    instrument_id: str,
    proven_never_submitted_evidence: Mapping[str, Any] | None = None,
) -> CanaryRecoveryAdjudicationV1:
    """Classify recovery from stubbed exchange payloads (fail-closed on contradiction)."""
    pending = _find_clordid_rows(pending_orders_payload, clordid)
    history = _find_clordid_rows(history_payload, clordid)
    if pending and history:
        p_state = str(pending[0].get("state") or "")
        h_state = str(history[0].get("state") or "")
        if p_state and h_state and p_state != h_state:
            return CanaryRecoveryAdjudicationV1(
                outcome=OUTCOME_CONTRADICTION,
                recommended_state=STATE_HALTED_UNRESOLVED,
                exposure_retained=True,
                reconciliation_complete=False,
                evidence={
                    "pending_state": p_state,
                    "history_state": h_state,
                    "clordid": clordid,
                },
            )
    rows = pending or history
    if not rows:
        if proven_never_submitted_evidence is not None:
            return CanaryRecoveryAdjudicationV1(
                outcome=OUTCOME_PROVEN_NEVER_SUBMITTED,
                recommended_state=STATE_TERMINAL_RECONCILED,
                exposure_retained=False,
                reconciliation_complete=True,
                evidence={"clordid": clordid, "proof": dict(proven_never_submitted_evidence)},
            )
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_ORDER_NOT_FOUND,
            recommended_state=STATE_RECONCILIATION_PENDING,
            exposure_retained=True,
            reconciliation_complete=False,
            evidence={
                "clordid": clordid,
                "note": "ORDER_NOT_FOUND_NOT_PROVEN_NEVER_SUBMITTED",
            },
        )
    row = rows[0]
    state = str(row.get("state") or "")
    fill_sz = str(row.get("fillSz") or "0")
    acc_fill = str(row.get("accFillSz") or fill_sz)
    exposure = acc_fill not in {"", "0", "0.0"}
    if state in {"filled", "Filled"}:
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_FILLED,
            recommended_state=STATE_TERMINAL_RECONCILED,
            exposure_retained=False,
            reconciliation_complete=True,
            evidence={"clordid": clordid, "row": dict(row)},
        )
    if exposure and state not in {"canceled", "cancelled"}:
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_PARTIAL_FILL,
            recommended_state=STATE_RECONCILIATION_PENDING,
            exposure_retained=True,
            reconciliation_complete=False,
            evidence={"clordid": clordid, "row": dict(row)},
        )
    if state in {"live", "partially_filled"}:
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_ORDER_ACCEPTED_OPEN,
            recommended_state=STATE_RECONCILIATION_PENDING,
            exposure_retained=exposure,
            reconciliation_complete=False,
            evidence={"clordid": clordid, "row": dict(row)},
        )
    s_code = str(row.get("sCode") or "")
    if s_code and s_code != "0":
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_ORDER_REJECTED,
            recommended_state=STATE_TERMINAL_RECONCILED,
            exposure_retained=False,
            reconciliation_complete=True,
            evidence={"clordid": clordid, "row": dict(row)},
        )
    pos_exposure = False
    if positions_payload is not None:
        data = positions_payload.get("data")
        if isinstance(data, list):
            for pos in data:
                if not isinstance(pos, dict):
                    continue
                if str(pos.get("instId") or "") != instrument_id:
                    continue
                if str(pos.get("pos") or "0") not in {"", "0", "0.0"}:
                    pos_exposure = True
    if pos_exposure:
        return CanaryRecoveryAdjudicationV1(
            outcome=OUTCOME_PARTIAL_FILL,
            recommended_state=STATE_RECONCILIATION_PENDING,
            exposure_retained=True,
            reconciliation_complete=False,
            evidence={"clordid": clordid, "position_exposure": True},
        )
    return CanaryRecoveryAdjudicationV1(
        outcome=OUTCOME_ORDER_NOT_FOUND,
        recommended_state=STATE_RECONCILIATION_PENDING,
        exposure_retained=True,
        reconciliation_complete=False,
        evidence={"clordid": clordid, "row": dict(row)},
    )
