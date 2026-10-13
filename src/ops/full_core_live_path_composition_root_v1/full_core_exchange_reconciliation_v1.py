"""Full-Core exchange reconciliation (offline-capable, fail-closed).

AUTHORITY_EFFECT=NONE — reconciliation never authorizes POST or re-issues Owner-GO.
UNKNOWN_REMAINS_UNKNOWN until authoritative exchange evidence resolves it.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping, Sequence

CONTRACT_ID = "FULL_CORE_EXCHANGE_RECONCILIATION_V1"
RECONCILIATION_PROVIDER_OFFLINE_STUB = "OFFLINE_STUB"
RECONCILIATION_PROVIDER_PRODUCTION = "PRODUCTION_DISABLED"

OUTCOME_CONFIRMED_OPEN = "CONFIRMED_OPEN"
OUTCOME_CONFIRMED_PARTIALLY_FILLED = "CONFIRMED_PARTIALLY_FILLED"
OUTCOME_CONFIRMED_FILLED = "CONFIRMED_FILLED"
OUTCOME_CONFIRMED_CANCELED = "CONFIRMED_CANCELED"
OUTCOME_CONFIRMED_REJECTED = "CONFIRMED_REJECTED"
OUTCOME_HALTED_UNRESOLVED = "HALTED_UNRESOLVED"

REASON_STALE_EVIDENCE = "STALE_EVIDENCE"
REASON_FRESHNESS_UNPROVEN = "FRESHNESS_UNPROVEN"
REASON_ACCOUNT_MISMATCH = "ACCOUNT_IDENTITY_MISMATCH"
REASON_ENV_MISMATCH = "ENVIRONMENT_MISMATCH"
REASON_INSTRUMENT_MISMATCH = "INSTRUMENT_IDENTITY_MISMATCH"
REASON_WRONG_CLORDID = "WRONG_CLORDID"
REASON_CONFLICTING_ORDID = "CONFLICTING_ORDID"
REASON_ORDER_NOT_FOUND_NOT_PROOF = "ORDER_NOT_FOUND_NOT_PROOF_OF_NO_SUBMIT"
REASON_TRANSPORT_UNKNOWN = "TRANSPORT_UNKNOWN_NO_AUTHORITATIVE_EVIDENCE"
REASON_INCOMPLETE_PAGINATION = "INCOMPLETE_PAGINATION"
REASON_HISTORY_UNAVAILABLE = "ORDER_HISTORY_UNAVAILABLE"
REASON_API_ERROR = "EXCHANGE_API_ERROR"
REASON_RATE_LIMIT = "EXCHANGE_RATE_LIMIT"
REASON_FILL_EXCEEDS_ORDER = "FILLED_QTY_EXCEEDS_ORDER_QTY"
REASON_NEGATIVE_REMAINING = "NEGATIVE_REMAINING_QTY"
REASON_DUPLICATE_FILL_CONFLICT = "DUPLICATE_FILL_CONFLICT"
REASON_ORDER_FILL_CONTRADICTION = "ORDER_FILL_CONTRADICTION"
REASON_POSITION_CONTRADICTION = "POSITION_EXPOSURE_CONTRADICTION"
REASON_UNSUPPORTED_UNITS = "UNSUPPORTED_CONTRACT_UNITS"


class EvidenceLayer(str, Enum):
    LOCAL_INTENT = "LOCAL_INTENT"
    LOCAL_RESERVATION = "LOCAL_RESERVATION"
    SUBMIT_MAY_HAVE_OCCURRED = "SUBMIT_MAY_HAVE_OCCURRED"
    TRANSPORT_ACK = "TRANSPORT_ACK"
    EXCHANGE_ORDER_STATE = "EXCHANGE_ORDER_STATE"
    EXCHANGE_FILL_STATE = "EXCHANGE_FILL_STATE"
    EXCHANGE_POSITION_STATE = "EXCHANGE_POSITION_STATE"
    EXCHANGE_ACCOUNT_STATE = "EXCHANGE_ACCOUNT_STATE"


class LocalSubmitOutcome(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    TRANSPORT_ACK = "TRANSPORT_ACK"
    TRANSPORT_REJECT = "TRANSPORT_REJECT"
    TRANSPORT_TIMEOUT = "TRANSPORT_TIMEOUT"
    TRANSPORT_UNKNOWN = "TRANSPORT_UNKNOWN"


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _dec(value: str | None) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


@dataclass(frozen=True)
class FullCoreExchangeReconciliationIdentityV1:
    canonical_decision_id: str
    decision_outcome: str
    selected_side: str
    instrument_id: str
    native_id: str
    account_identity: str
    execution_environment: str
    venue: str
    venue_plan_identity: str
    venue_plan_digest: str
    envelope_identity: str
    envelope_digest: str
    final_quantity: str
    quantity_unit: str
    order_type: str
    order_price: str
    clordid: str
    exchange_ord_id: str | None
    owner_go: str
    atomic_consumption_key: str
    submit_attempt_id: str
    local_durable_state_version: str

    def identity_digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_decision_id": self.canonical_decision_id,
            "decision_outcome": self.decision_outcome,
            "selected_side": self.selected_side,
            "instrument_id": self.instrument_id,
            "native_id": self.native_id,
            "account_identity": self.account_identity,
            "execution_environment": self.execution_environment,
            "venue": self.venue,
            "venue_plan_identity": self.venue_plan_identity,
            "venue_plan_digest": self.venue_plan_digest,
            "envelope_identity": self.envelope_identity,
            "envelope_digest": self.envelope_digest,
            "final_quantity": self.final_quantity,
            "quantity_unit": self.quantity_unit,
            "order_type": self.order_type,
            "order_price": self.order_price,
            "clordid": self.clordid,
            "exchange_ord_id": self.exchange_ord_id,
            "owner_go": self.owner_go,
            "atomic_consumption_key": self.atomic_consumption_key,
            "submit_attempt_id": self.submit_attempt_id,
            "local_durable_state_version": self.local_durable_state_version,
            "contract_id": CONTRACT_ID,
        }


@dataclass(frozen=True)
class ExchangeEvidenceItemV1:
    layer: EvidenceLayer
    source: str
    account: str
    environment: str
    instrument: str
    observed_at: str
    received_at: str
    freshness_proven: bool
    query_scope: str
    response_status: str
    raw_reference: str
    canonical_identity_digest: str
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.value,
            "source": self.source,
            "account": self.account,
            "environment": self.environment,
            "instrument": self.instrument,
            "observed_at": self.observed_at,
            "received_at": self.received_at,
            "freshness_proven": self.freshness_proven,
            "query_scope": self.query_scope,
            "response_status": self.response_status,
            "raw_reference": self.raw_reference,
            "canonical_identity_digest": self.canonical_identity_digest,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class FullCoreExchangeReconciliationSnapshotV1:
    provider: str
    simulation_mode: str
    identity_digest: str
    evidence_items: tuple[ExchangeEvidenceItemV1, ...]
    incomplete_pagination: bool
    history_unavailable: bool
    snapshot_freshness_proven: bool
    transport_failures: tuple[str, ...]
    api_errors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "simulation_mode": self.simulation_mode,
            "identity_digest": self.identity_digest,
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "incomplete_pagination": self.incomplete_pagination,
            "history_unavailable": self.history_unavailable,
            "snapshot_freshness_proven": self.snapshot_freshness_proven,
            "transport_failures": list(self.transport_failures),
            "api_errors": list(self.api_errors),
            "contract_id": CONTRACT_ID,
        }


@dataclass(frozen=True)
class FullCoreExchangeReconciliationDecisionV1:
    outcome: str
    reasons: tuple[str, ...]
    exposure_retained: bool
    reconciliation_complete: bool
    recommended_atomic_state: str | None
    execution_authority_effect: str
    order_state: str | None
    cumulative_filled_qty: str | None
    remaining_qty: str | None
    venue_ord_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reasons": list(self.reasons),
            "exposure_retained": self.exposure_retained,
            "reconciliation_complete": self.reconciliation_complete,
            "recommended_atomic_state": self.recommended_atomic_state,
            "execution_authority_effect": self.execution_authority_effect,
            "order_state": self.order_state,
            "cumulative_filled_qty": self.cumulative_filled_qty,
            "remaining_qty": self.remaining_qty,
            "venue_ord_id": self.venue_ord_id,
            "contract_id": CONTRACT_ID,
        }


def _halt(*reasons: str) -> FullCoreExchangeReconciliationDecisionV1:
    rs = tuple(r for r in reasons if r)
    return FullCoreExchangeReconciliationDecisionV1(
        outcome=OUTCOME_HALTED_UNRESOLVED,
        reasons=rs or (OUTCOME_HALTED_UNRESOLVED,),
        exposure_retained=True,
        reconciliation_complete=False,
        recommended_atomic_state="HALTED_UNRESOLVED",
        execution_authority_effect="NONE",
        order_state=None,
        cumulative_filled_qty=None,
        remaining_qty=None,
        venue_ord_id=None,
    )


def _verify_evidence_identity(
    identity: FullCoreExchangeReconciliationIdentityV1,
    item: ExchangeEvidenceItemV1,
) -> str | None:
    if item.account.strip() != identity.account_identity.strip():
        return REASON_ACCOUNT_MISMATCH
    if item.environment.strip().upper() != identity.execution_environment.strip().upper():
        return REASON_ENV_MISMATCH
    if item.instrument.strip() != identity.instrument_id.strip():
        return REASON_INSTRUMENT_MISMATCH
    cl = str(item.payload.get("clOrdId") or item.payload.get("clordid") or "")
    if cl and cl != identity.clordid:
        return REASON_WRONG_CLORDID
    ord_id = str(item.payload.get("ordId") or "")
    if identity.exchange_ord_id and ord_id and ord_id != identity.exchange_ord_id:
        return REASON_CONFLICTING_ORDID
    return None


def _collect_order_rows(
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    clordid: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in snapshot.evidence_items:
        if item.layer not in {
            EvidenceLayer.EXCHANGE_ORDER_STATE,
            EvidenceLayer.EXCHANGE_FILL_STATE,
        }:
            continue
        payload = item.payload
        if str(payload.get("clOrdId") or "") == clordid:
            rows.append(dict(payload))
    return rows


def _collect_fill_rows(
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    clordid: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in snapshot.evidence_items:
        if item.layer is not EvidenceLayer.EXCHANGE_FILL_STATE:
            continue
        if str(item.payload.get("clOrdId") or "") == clordid:
            rows.append(dict(item.payload))
    return rows


def _fill_consistency(
    *,
    order_sz: Decimal | None,
    acc_fill: Decimal | None,
    fills: Sequence[Mapping[str, Any]],
) -> str | None:
    if not fills:
        return None
    seen: dict[str, Decimal] = {}
    total = Decimal("0")
    for row in fills:
        fill_id = str(row.get("fillId") or row.get("tradeId") or json.dumps(row, sort_keys=True))
        qty = _dec(str(row.get("fillSz") or row.get("sz") or "0")) or Decimal("0")
        if fill_id in seen and seen[fill_id] != qty:
            return REASON_DUPLICATE_FILL_CONFLICT
        seen[fill_id] = qty
        total += qty
    if order_sz is not None and acc_fill is not None and acc_fill > order_sz:
        return REASON_NEGATIVE_REMAINING
    if order_sz is not None and total > order_sz:
        return REASON_FILL_EXCEEDS_ORDER
    if acc_fill is not None and total != acc_fill:
        return REASON_ORDER_FILL_CONTRADICTION
    return None


def adjudicate_full_core_exchange_reconciliation_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    snapshot: FullCoreExchangeReconciliationSnapshotV1,
    local_submit_outcome: LocalSubmitOutcome,
    proven_never_submitted: bool = False,
) -> FullCoreExchangeReconciliationDecisionV1:
    """Deterministic reconciliation FSM from typed snapshot (no network)."""
    if identity.identity_digest() != snapshot.identity_digest:
        return _halt("IDENTITY_DIGEST_MISMATCH")

    if snapshot.api_errors:
        if any("rate" in e.lower() for e in snapshot.api_errors):
            return _halt(REASON_RATE_LIMIT)
        return _halt(REASON_API_ERROR)

    if snapshot.transport_failures and not snapshot.evidence_items:
        return _halt(*snapshot.transport_failures)

    if not snapshot.snapshot_freshness_proven:
        return _halt(REASON_FRESHNESS_UNPROVEN)

    for item in snapshot.evidence_items:
        if not item.freshness_proven:
            return _halt(REASON_STALE_EVIDENCE)
        err = _verify_evidence_identity(identity, item)
        if err:
            return _halt(err)

    if snapshot.incomplete_pagination:
        return _halt(REASON_INCOMPLETE_PAGINATION)
    if snapshot.history_unavailable:
        return _halt(REASON_HISTORY_UNAVAILABLE)

    if identity.quantity_unit.upper() not in {"CONTRACTS", "CONTRACT"}:
        return _halt(REASON_UNSUPPORTED_UNITS)

    orders = _collect_order_rows(snapshot, identity.clordid)
    fills = _collect_fill_rows(snapshot, identity.clordid)

    if not orders and not fills:
        if local_submit_outcome in {
            LocalSubmitOutcome.TRANSPORT_TIMEOUT,
            LocalSubmitOutcome.TRANSPORT_UNKNOWN,
        }:
            return _halt(REASON_TRANSPORT_UNKNOWN)
        if proven_never_submitted and local_submit_outcome is LocalSubmitOutcome.NOT_SUBMITTED:
            return FullCoreExchangeReconciliationDecisionV1(
                outcome=OUTCOME_CONFIRMED_CANCELED,
                reasons=(),
                exposure_retained=False,
                reconciliation_complete=True,
                recommended_atomic_state="TERMINAL_RECONCILED",
                execution_authority_effect="NONE",
                order_state="never_submitted",
                cumulative_filled_qty="0",
                remaining_qty=identity.final_quantity,
                venue_ord_id=None,
            )
        return _halt(REASON_ORDER_NOT_FOUND_NOT_PROOF)

    primary = orders[0] if orders else fills[0]
    state = str(primary.get("state") or "").lower()
    ord_id = str(primary.get("ordId") or "") or None
    order_sz = _dec(str(primary.get("sz") or identity.final_quantity))
    acc_fill = _dec(str(primary.get("accFillSz") or primary.get("fillSz") or "0"))

    if order_sz is not None and acc_fill is not None and acc_fill > order_sz:
        return _halt(REASON_NEGATIVE_REMAINING)

    fill_err = _fill_consistency(order_sz=order_sz, acc_fill=acc_fill, fills=fills)
    if fill_err:
        return _halt(fill_err)

    if state in {"rejected", "reject"} or str(primary.get("sCode") or "0") not in {"", "0"}:
        return FullCoreExchangeReconciliationDecisionV1(
            outcome=OUTCOME_CONFIRMED_REJECTED,
            reasons=(),
            exposure_retained=False,
            reconciliation_complete=True,
            recommended_atomic_state="TERMINAL_RECONCILED",
            execution_authority_effect="NONE",
            order_state=state or "rejected",
            cumulative_filled_qty=str(acc_fill or Decimal("0")),
            remaining_qty="0",
            venue_ord_id=ord_id,
        )

    if state == "canceled":
        partial = acc_fill is not None and acc_fill > 0
        if partial:
            return FullCoreExchangeReconciliationDecisionV1(
                outcome=OUTCOME_CONFIRMED_PARTIALLY_FILLED,
                reasons=("CANCELED_AFTER_PARTIAL",),
                exposure_retained=True,
                reconciliation_complete=True,
                recommended_atomic_state="TERMINAL_RECONCILED",
                execution_authority_effect="NONE",
                order_state=state,
                cumulative_filled_qty=str(acc_fill),
                remaining_qty=str((order_sz or Decimal("0")) - (acc_fill or Decimal("0"))),
                venue_ord_id=ord_id,
            )
        return FullCoreExchangeReconciliationDecisionV1(
            outcome=OUTCOME_CONFIRMED_CANCELED,
            reasons=(),
            exposure_retained=False,
            reconciliation_complete=True,
            recommended_atomic_state="TERMINAL_RECONCILED",
            execution_authority_effect="NONE",
            order_state=state,
            cumulative_filled_qty=str(acc_fill or Decimal("0")),
            remaining_qty=str(order_sz or Decimal("0")),
            venue_ord_id=ord_id,
        )

    if state == "filled":
        return FullCoreExchangeReconciliationDecisionV1(
            outcome=OUTCOME_CONFIRMED_FILLED,
            reasons=(),
            exposure_retained=True,
            reconciliation_complete=True,
            recommended_atomic_state="TERMINAL_RECONCILED",
            execution_authority_effect="NONE",
            order_state=state,
            cumulative_filled_qty=str(acc_fill or order_sz or Decimal("0")),
            remaining_qty="0",
            venue_ord_id=ord_id,
        )

    if state in {"partially_filled", "partially-filled"} or (
        acc_fill is not None and order_sz is not None and Decimal("0") < acc_fill < order_sz
    ):
        return FullCoreExchangeReconciliationDecisionV1(
            outcome=OUTCOME_CONFIRMED_PARTIALLY_FILLED,
            reasons=(),
            exposure_retained=True,
            reconciliation_complete=False,
            recommended_atomic_state="RECONCILIATION_PENDING",
            execution_authority_effect="NONE",
            order_state=state or "partially_filled",
            cumulative_filled_qty=str(acc_fill or Decimal("0")),
            remaining_qty=str((order_sz or Decimal("0")) - (acc_fill or Decimal("0"))),
            venue_ord_id=ord_id,
        )

    if state in {"live", "open"}:
        return FullCoreExchangeReconciliationDecisionV1(
            outcome=OUTCOME_CONFIRMED_OPEN,
            reasons=(),
            exposure_retained=True,
            reconciliation_complete=False,
            recommended_atomic_state="RECONCILIATION_PENDING",
            execution_authority_effect="NONE",
            order_state=state,
            cumulative_filled_qty=str(acc_fill or Decimal("0")),
            remaining_qty=str((order_sz or Decimal("0")) - (acc_fill or Decimal("0"))),
            venue_ord_id=ord_id,
        )

    return _halt(REASON_ORDER_FILL_CONTRADICTION)


__all__ = [
    "CONTRACT_ID",
    "EvidenceLayer",
    "ExchangeEvidenceItemV1",
    "FullCoreExchangeReconciliationDecisionV1",
    "FullCoreExchangeReconciliationIdentityV1",
    "FullCoreExchangeReconciliationSnapshotV1",
    "LocalSubmitOutcome",
    "OUTCOME_CONFIRMED_CANCELED",
    "OUTCOME_CONFIRMED_FILLED",
    "OUTCOME_CONFIRMED_OPEN",
    "OUTCOME_CONFIRMED_PARTIALLY_FILLED",
    "OUTCOME_CONFIRMED_REJECTED",
    "OUTCOME_HALTED_UNRESOLVED",
    "RECONCILIATION_PROVIDER_OFFLINE_STUB",
    "RECONCILIATION_PROVIDER_PRODUCTION",
    "adjudicate_full_core_exchange_reconciliation_v1",
]
