"""DTOs for Cap 3.1 productive futures accounting runtime binding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Optional

from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CANONICAL_KERNEL_OWNER,
    CANONICAL_KERNEL_PATH,
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SINGLE_WRITER_IDENTITY,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dec_str(value: Decimal | str | int | float | None) -> Optional[str]:
    if value is None:
        return None
    return str(value)


@dataclass(frozen=True)
class ContractMetadataV1:
    symbol: str
    contract_size: Decimal
    tick_size: Decimal
    min_qty: Decimal
    quote_currency: str
    initial_margin_rate: Decimal
    maintenance_margin_rate: Decimal
    max_leverage: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "contract_size": str(self.contract_size),
            "tick_size": str(self.tick_size),
            "min_qty": str(self.min_qty),
            "quote_currency": self.quote_currency,
            "initial_margin_rate": str(self.initial_margin_rate),
            "maintenance_margin_rate": str(self.maintenance_margin_rate),
            "max_leverage": str(self.max_leverage),
        }

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class SimulatedFillInputV1:
    fill_id: str
    instrument_id: str
    side: str  # BUY|SELL
    quantity: Decimal
    mark_price: Decimal
    fill_price: Decimal
    fee: Decimal
    slippage_cost: Decimal
    notional: Decimal
    reduce_only: bool = False
    event_time_unix: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": str(self.quantity),
            "mark_price": str(self.mark_price),
            "fill_price": str(self.fill_price),
            "fee": str(self.fee),
            "slippage_cost": str(self.slippage_cost),
            "notional": str(self.notional),
            "reduce_only": bool(self.reduce_only),
            "event_time_unix": self.event_time_unix,
        }

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class AccountingPositionStateV1:
    symbol: str
    side: Optional[str]
    quantity: Decimal
    entry_price: Decimal
    mark_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    fees_paid: Decimal
    funding_pnl: Decimal = Decimal("0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": str(self.quantity),
            "entry_price": str(self.entry_price),
            "mark_price": str(self.mark_price),
            "realized_pnl": str(self.realized_pnl),
            "unrealized_pnl": str(self.unrealized_pnl),
            "fees_paid": str(self.fees_paid),
            "funding_pnl": str(self.funding_pnl),
        }


@dataclass(frozen=True)
class AccountingPortfolioStateV1:
    equity: Decimal
    initial_equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    cumulative_fees: Decimal
    cumulative_slippage: Decimal
    positions: tuple[AccountingPositionStateV1, ...]
    fill_count: int
    applied_fill_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "equity": str(self.equity),
            "initial_equity": str(self.initial_equity),
            "realized_pnl": str(self.realized_pnl),
            "unrealized_pnl": str(self.unrealized_pnl),
            "cumulative_fees": str(self.cumulative_fees),
            "cumulative_slippage": str(self.cumulative_slippage),
            "fill_count": int(self.fill_count),
            "applied_fill_ids": list(self.applied_fill_ids),
            "positions": [p.to_dict() for p in self.positions],
            "authority_owner": AUTHORITY_OWNER,
            "canonical_kernel_owner": CANONICAL_KERNEL_OWNER,
            "single_writer_identity": SINGLE_WRITER_IDENTITY,
        }

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class AccountingRiskStateV1:
    notional: Decimal
    initial_margin_required: Decimal
    maintenance_margin_required: Decimal
    liquidation_proximity: Optional[str]
    mark_price: Decimal
    contract_size: Decimal

    def to_dict(self) -> dict[str, Any]:
        return {
            "notional": str(self.notional),
            "initial_margin_required": str(self.initial_margin_required),
            "maintenance_margin_required": str(self.maintenance_margin_required),
            "liquidation_proximity": self.liquidation_proximity,
            "mark_price": str(self.mark_price),
            "contract_size": str(self.contract_size),
            "source": "canonical_futures_accounting",
        }

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class AccountingApplyResultV1:
    ok: bool
    action_code: str
    fill_input_digest: str
    accounting_output_digest: str
    portfolio_state: AccountingPortfolioStateV1
    risk_state: AccountingRiskStateV1
    idempotent_replay: bool = False
    failure_code: Optional[str] = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "action_code": self.action_code,
            "fill_input_digest": self.fill_input_digest,
            "accounting_output_digest": self.accounting_output_digest,
            "portfolio_state": self.portfolio_state.to_dict(),
            "risk_state": self.risk_state.to_dict(),
            "idempotent_replay": bool(self.idempotent_replay),
            "failure_code": self.failure_code,
            "notes": list(self.notes),
            "portfolio_state_digest": self.portfolio_state.digest(),
            "risk_state_digest": self.risk_state.digest(),
        }


@dataclass(frozen=True)
class ProductiveFuturesAccountingEvidenceV1:
    capability_id: str = CAPABILITY_ID
    schema_version: str = SCHEMA_VERSION
    producer_version: str = PRODUCER_VERSION
    owner: str = OWNER
    repository_sha: str = ""
    config_digest: str = ""
    call_graph_before: tuple[str, ...] = ()
    call_graph_after: tuple[str, ...] = ()
    accounting_authority_before: str = (
        "ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1"
    )
    accounting_authority_after: str = AUTHORITY_OWNER
    canonical_kernel_path: str = CANONICAL_KERNEL_PATH
    canonical_kernel_reused: bool = True
    futures_accounting_runtime_bound: bool = FUTURES_ACCOUNTING_RUNTIME_BOUND
    core_logic_change: bool = CORE_LOGIC_CHANGE
    single_writer_identity: str = SINGLE_WRITER_IDENTITY
    contract_metadata_digest: str = ""
    fill_input_digests: tuple[str, ...] = ()
    accounting_output_digests: tuple[str, ...] = ()
    portfolio_state_digest_before: str = ""
    portfolio_state_digest_after: str = ""
    risk_state_digest: str = ""
    restart_idempotency_proven: bool = False
    failure_injection_results: Mapping[str, Any] = field(default_factory=dict)
    legacy_authority_check: Mapping[str, Any] = field(default_factory=dict)
    verification_result: Mapping[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "schema_version": self.schema_version,
            "producer_version": self.producer_version,
            "owner": self.owner,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "call_graph_before": list(self.call_graph_before),
            "call_graph_after": list(self.call_graph_after),
            "accounting_authority_before": self.accounting_authority_before,
            "accounting_authority_after": self.accounting_authority_after,
            "canonical_kernel_path": self.canonical_kernel_path,
            "canonical_kernel_reused": bool(self.canonical_kernel_reused),
            "futures_accounting_runtime_bound": bool(self.futures_accounting_runtime_bound),
            "core_logic_change": bool(self.core_logic_change),
            "single_writer_identity": self.single_writer_identity,
            "contract_metadata_digest": self.contract_metadata_digest,
            "fill_input_digests": list(self.fill_input_digests),
            "accounting_output_digests": list(self.accounting_output_digests),
            "portfolio_state_digest_before": self.portfolio_state_digest_before,
            "portfolio_state_digest_after": self.portfolio_state_digest_after,
            "risk_state_digest": self.risk_state_digest,
            "restart_idempotency_proven": bool(self.restart_idempotency_proven),
            "failure_injection_results": dict(self.failure_injection_results),
            "legacy_authority_check": dict(self.legacy_authority_check),
            "verification_result": dict(self.verification_result),
            "notes": list(self.notes),
        }
