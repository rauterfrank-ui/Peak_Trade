"""Deterministic Live dry-run order-plan builder (pre-submit only; no wire submit)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    DRY_RUN_MARKER,
    EXECUTION_MODE_ALLOWED,
    LIFECYCLE_STATE_ALLOWED,
    LIFECYCLE_STATES_FORBIDDEN,
    LIVE_AUTHORIZED,
    LIVE_RECONCILIATION_PROVEN,
    OWNER,
    SUBMIT_FORBIDDEN,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.mutation_boundary_v1 import (
    LiveDryRunOrderPlanMutationBoundaryError,
    assert_plan_cannot_reach_submit_v1,
    assert_standing_gates_block_execute_v1,
)


class LiveDryRunOrderPlanBuilderError(RuntimeError):
    """Fail-closed order-plan builder violation."""


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _dec(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


@dataclass(frozen=True)
class LiveDryRunOrderPlanRecordV1:
    stage: str
    intent_id: str
    order_plan_id: str
    client_order_id: str
    venue: str
    entity: str
    region: str
    rest_host: str
    account_scope: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    td_mode: str
    reference_price: str | None
    pricing_basis: str
    limit_price: str | None
    stop_risk_parameters: dict[str, Any]
    notional: str | None
    fee_bps_assumption: str
    slippage_bps_assumption: str
    available_equity: str | None
    available_margin: str | None
    portfolio_exposure: dict[str, Any]
    pre_trade_risk_gates: dict[str, Any]
    reconciliation_state: dict[str, Any]
    execution_block_reasons: list[str]
    execution_eligibility: str
    execution_mode: str
    lifecycle_state: str
    canonical_order_plan_digest: str
    venue_native_dry_run_payload: dict[str, Any]
    dry_run_serialization_digest: str
    dry_run_marker: bool = True
    submitted: bool = False
    submit: bool = False
    network_effect: str = "LIVE_DRY_RUN_ORDER_PLAN"
    order_effect: str = "NONE"
    owner: str = OWNER

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "intent_id": self.intent_id,
            "order_plan_id": self.order_plan_id,
            "client_order_id": self.client_order_id,
            "venue": self.venue,
            "entity": self.entity,
            "region": self.region,
            "rest_host": self.rest_host,
            "account_scope": self.account_scope,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "td_mode": self.td_mode,
            "reference_price": self.reference_price,
            "pricing_basis": self.pricing_basis,
            "limit_price": self.limit_price,
            "stop_risk_parameters": dict(self.stop_risk_parameters),
            "notional": self.notional,
            "fee_bps_assumption": self.fee_bps_assumption,
            "slippage_bps_assumption": self.slippage_bps_assumption,
            "available_equity": self.available_equity,
            "available_margin": self.available_margin,
            "portfolio_exposure": dict(self.portfolio_exposure),
            "pre_trade_risk_gates": dict(self.pre_trade_risk_gates),
            "reconciliation_state": dict(self.reconciliation_state),
            "execution_block_reasons": list(self.execution_block_reasons),
            "execution_eligibility": self.execution_eligibility,
            "execution_mode": self.execution_mode,
            "lifecycle_state": self.lifecycle_state,
            "canonical_order_plan_digest": self.canonical_order_plan_digest,
            "venue_native_dry_run_payload": dict(self.venue_native_dry_run_payload),
            "dry_run_serialization_digest": self.dry_run_serialization_digest,
            "dry_run_marker": self.dry_run_marker,
            "submitted": self.submitted,
            "submit": self.submit,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "owner": self.owner,
            "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
            "LIVE_RECONCILIATION_PROVEN": self.reconciliation_state.get(
                "LIVE_RECONCILIATION_PROVEN", LIVE_RECONCILIATION_PROVEN
            ),
            "BLOCKS_NEW_ENTRY": self.reconciliation_state.get("BLOCKS_NEW_ENTRY", True),
        }


def _extract_equity_margin(
    balance_payload: Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    if not isinstance(balance_payload, Mapping):
        return None, None
    data = balance_payload.get("data")
    if isinstance(data, list) and data:
        row = data[0] if isinstance(data[0], Mapping) else {}
    elif isinstance(data, Mapping):
        row = data
    else:
        row = balance_payload
    equity = row.get("totalEq") or row.get("eq") or row.get("adjEq")
    avail = row.get("availEq") or row.get("availBal") or row.get("cashBal")
    return (str(equity) if equity is not None else None, str(avail) if avail is not None else None)


def _extract_exposure(positions_payload: Mapping[str, Any] | None) -> dict[str, Any]:
    positions: list[dict[str, Any]] = []
    if isinstance(positions_payload, Mapping):
        data = positions_payload.get("data")
        if isinstance(data, list):
            for row in data:
                if not isinstance(row, Mapping):
                    continue
                positions.append(
                    {
                        "instId": row.get("instId"),
                        "pos": row.get("pos"),
                        "avgPx": row.get("avgPx"),
                        "markPx": row.get("markPx"),
                        "notionalUsd": row.get("notionalUsd") or row.get("notionalUsd"),
                    }
                )
    return {"open_positions_count": len(positions), "positions": positions}


def build_live_dry_run_order_plan_record_v1(
    *,
    venue: str,
    entity: str,
    region: str,
    rest_host: str,
    account_scope: str,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    td_mode: str,
    fee_bps_assumption: str,
    slippage_bps_assumption: str,
    reference_price: str | None,
    pricing_basis: str,
    balance_payload: Mapping[str, Any] | None,
    positions_payload: Mapping[str, Any] | None,
    reconciliation: Mapping[str, Any],
    intent_id: str,
    order_plan_id: str,
    client_order_id: str,
    min_notional_usdt_assumption: str,
) -> LiveDryRunOrderPlanRecordV1:
    lifecycle_state = LIFECYCLE_STATE_ALLOWED
    if lifecycle_state in LIFECYCLE_STATES_FORBIDDEN:
        raise LiveDryRunOrderPlanBuilderError("LIFECYCLE_STATE_FORBIDDEN")

    blocks_new_entry = bool(reconciliation.get("BLOCKS_NEW_ENTRY", True))
    live_recon_proven = bool(reconciliation.get("LIVE_RECONCILIATION_PROVEN", False))
    unresolved = bool(reconciliation.get("UNRESOLVED_ECONOMIC_DIVERGENCE", True))

    block_reasons = assert_standing_gates_block_execute_v1(
        blocks_new_entry=blocks_new_entry,
        live_reconciliation_proven=live_recon_proven,
    )
    if unresolved:
        block_reasons.append("UNRESOLVED_ECONOMIC_DIVERGENCE=true")
    if LIVE_AUTHORIZED is not False:
        raise LiveDryRunOrderPlanBuilderError("LIVE_AUTHORIZED_CONSTANT_DRIFT")

    equity, avail = _extract_equity_margin(balance_payload)
    exposure = _extract_exposure(positions_payload)

    limit_price = None
    notional = None
    px = _dec(reference_price)
    qty = _dec(quantity)
    if order_type == "LIMIT" and px is not None:
        # Conservative limit: buy below ref, sell above ref by slippage assumption.
        slip = _dec(slippage_bps_assumption) or Decimal("0")
        adj = (slip / Decimal("10000")) if slip else Decimal("0")
        if side == "BUY":
            limit_price = str((px * (Decimal("1") - adj)).quantize(Decimal("0.1")))
        else:
            limit_price = str((px * (Decimal("1") + adj)).quantize(Decimal("0.1")))
        if qty is not None:
            notional = str((qty * Decimal(limit_price)).quantize(Decimal("0.01")))

    pre_trade_risk_gates = {
        "LIVE_AUTHORIZED": False,
        "LIVE_ORDER_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": live_recon_proven,
        "BLOCKS_NEW_ENTRY": blocks_new_entry,
        "UNRESOLVED_ECONOMIC_DIVERGENCE": unresolved,
        "MIN_NOTIONAL_USDT_ASSUMPTION": min_notional_usdt_assumption,
        "SUBMIT_FORBIDDEN": SUBMIT_FORBIDDEN,
        "DRY_RUN_MARKER": DRY_RUN_MARKER,
        "RESULT": "NO_EXECUTE",
    }

    # Eligibility: constructed plan is expected to be blocked under current divergence.
    if block_reasons:
        execution_eligibility = "BLOCKED_NO_EXECUTE"
    else:
        execution_eligibility = "ELIGIBLE_BUT_SUBMIT_STILL_FORBIDDEN_WITHOUT_SEPARATE_GO"

    venue_native = {
        "clOrdId": client_order_id,
        "instId": instrument_id,
        "side": side.lower(),
        "ordType": order_type.lower(),
        "sz": quantity,
        "tdMode": td_mode,
        "px": limit_price,
        "dry_run": True,
        "submit": False,
    }
    canonical_payload = {
        "account_scope": account_scope,
        "client_order_id": client_order_id,
        "entity": entity,
        "execution_mode": EXECUTION_MODE_ALLOWED,
        "instrument_id": instrument_id,
        "intent_id": intent_id,
        "lifecycle_state": lifecycle_state,
        "limit_price": limit_price,
        "order_plan_id": order_plan_id,
        "order_type": order_type,
        "quantity": quantity,
        "reference_price": reference_price,
        "region": region,
        "rest_host": rest_host,
        "side": side,
        "stage": "LIVE_DRY_RUN_ORDER_PLAN",
        "venue": venue,
    }
    record = LiveDryRunOrderPlanRecordV1(
        stage="LIVE_DRY_RUN_ORDER_PLAN",
        intent_id=intent_id,
        order_plan_id=order_plan_id,
        client_order_id=client_order_id,
        venue=venue,
        entity=entity,
        region=region,
        rest_host=rest_host,
        account_scope=account_scope,
        instrument_id=instrument_id,
        side=side,
        order_type=order_type,
        quantity=quantity,
        td_mode=td_mode,
        reference_price=reference_price,
        pricing_basis=pricing_basis,
        limit_price=limit_price,
        stop_risk_parameters={
            "stop_loss": None,
            "take_profit": None,
            "max_loss_budget": None,
            "note": "Stop/risk parameters not Owner-ratified for dry-run plan; left null.",
        },
        notional=notional,
        fee_bps_assumption=fee_bps_assumption,
        slippage_bps_assumption=slippage_bps_assumption,
        available_equity=equity,
        available_margin=avail,
        portfolio_exposure=exposure,
        pre_trade_risk_gates=pre_trade_risk_gates,
        reconciliation_state={
            "LIVE_RECONCILIATION_PROVEN": live_recon_proven,
            "BLOCKS_NEW_ENTRY": blocks_new_entry,
            "UNRESOLVED_ECONOMIC_DIVERGENCE": unresolved,
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
            "ALL_LAYERS_MATCH": reconciliation.get("ALL_LAYERS_MATCH"),
            "layers": reconciliation.get("layers"),
        },
        execution_block_reasons=block_reasons,
        execution_eligibility=execution_eligibility,
        execution_mode=EXECUTION_MODE_ALLOWED,
        lifecycle_state=lifecycle_state,
        canonical_order_plan_digest=hashlib.sha256(
            _canonical_dumps(canonical_payload).encode("utf-8")
        ).hexdigest(),
        venue_native_dry_run_payload=venue_native,
        dry_run_serialization_digest=hashlib.sha256(
            _canonical_dumps(venue_native).encode("utf-8")
        ).hexdigest(),
    )
    try:
        assert_plan_cannot_reach_submit_v1(record.to_dict())
    except LiveDryRunOrderPlanMutationBoundaryError as exc:
        raise LiveDryRunOrderPlanBuilderError(str(exc)) from exc
    return record
