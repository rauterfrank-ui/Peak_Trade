# src/trading/master_v2/capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
capital/risk/sizing semantics via the Surface H offline replay adapter.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import (
    CONTRACT_VERSION as CAPITAL_RISK_SIZING_CONTRACT_VERSION,
    CapitalRiskSizingOutcome,
    InstrumentQuantityConstraintsV1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    CapitalRiskSizingOfflineReplayBindingResultV0,
    bind_capital_risk_sizing_offline_replay_evidence_v0,
    capital_risk_sizing_binding_non_authority_boundary_ok_v0,
)

CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0"
)
CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "capital_risk_sizing_boundary_backtest_state_file_v0"
)

_BLOCKING_QUANTITY_STATUSES = frozenset({"BLOCK", "NOT_BOUND"})


@dataclass(frozen=True)
class CapitalRiskSizingBacktestStateFileRecordV0:
    """Parsed capital/risk/sizing backtest state-file payload."""

    instrument_id: str
    reference_price: str
    protective_stop_price: str
    account_equity: str
    scope_capital_limit: str
    per_trade_risk_limit: str
    total_capital_limit: str
    daily_loss_remaining_budget: str
    current_reconciled_exposure: str
    lot_size: str
    minimum_quantity: str
    maximum_quantity: str
    minimum_notional: str
    tick_size: str
    maximum_positions: int
    current_open_positions_count: int
    reconciliation_status: str
    capital_risk_sizing_owner_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0:
    capital_risk_sizing_boundary_backtest_state_file_bound: bool
    quantity_provenance_represented: bool
    risk_limits_represented: bool
    quantity_provenance_ref: str
    risk_sizing_ref: str
    quantity_status: str
    sizing_outcome: str
    order_intent_boundary_not_adapter_compatible: bool
    capital_risk_sizing_owner_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: CapitalRiskSizingOfflineReplayBindingResultV0
    surface_h_adapter_owner_ref: str


def _canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    stripped = {k: v for k, v in payload.items() if k != "state_file_digest_ref"}
    return json.dumps(stripped, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_backtest_state_file_digest_v0(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compute_backtest_state_file_digest_from_payload_v0(payload: Mapping[str, Any]) -> str:
    return compute_backtest_state_file_digest_v0(_canonical_payload_bytes(payload))


def _parse_positive_decimal(raw: object, *, field_name: str) -> Decimal:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ValueError(f"{field_name}_missing")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name}_invalid") from exc
    if value <= 0:
        raise ValueError(f"{field_name}_invalid")
    return value


def _parse_non_negative_decimal(raw: object, *, field_name: str) -> Decimal:
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        raise ValueError(f"{field_name}_missing")
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name}_invalid") from exc
    if value < 0:
        raise ValueError(f"{field_name}_invalid")
    return value


def _parse_required_str(raw: object, *, field_name: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{field_name}_missing")
    return raw.strip()


def parse_capital_risk_sizing_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> CapitalRiskSizingBacktestStateFileRecordV0:
    """Parse backtest capital/risk/sizing state file. Fail-closed on missing or invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("capital_risk_sizing_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("capital_risk_sizing_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("capital_risk_sizing_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("capital_risk_sizing_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("capital_risk_sizing_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("capital_risk_sizing_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != CAPITAL_RISK_SIZING_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("capital_risk_sizing_backtest_state_file_schema_version_mismatch")

    instrument_id = _parse_required_str(decoded.get("instrument_id"), field_name="instrument_id")
    _parse_positive_decimal(decoded.get("reference_price"), field_name="reference_price")
    _parse_positive_decimal(decoded.get("account_equity"), field_name="account_equity")
    _parse_positive_decimal(decoded.get("scope_capital_limit"), field_name="scope_capital_limit")
    _parse_positive_decimal(decoded.get("per_trade_risk_limit"), field_name="per_trade_risk_limit")
    _parse_positive_decimal(decoded.get("total_capital_limit"), field_name="total_capital_limit")
    _parse_non_negative_decimal(
        decoded.get("daily_loss_remaining_budget"),
        field_name="daily_loss_remaining_budget",
    )
    _parse_non_negative_decimal(
        decoded.get("current_reconciled_exposure"),
        field_name="current_reconciled_exposure",
    )
    _parse_positive_decimal(decoded.get("lot_size"), field_name="lot_size")
    _parse_positive_decimal(decoded.get("minimum_quantity"), field_name="minimum_quantity")
    _parse_positive_decimal(decoded.get("maximum_quantity"), field_name="maximum_quantity")
    _parse_positive_decimal(decoded.get("minimum_notional"), field_name="minimum_notional")
    _parse_positive_decimal(decoded.get("tick_size"), field_name="tick_size")

    owner_ref = str(decoded.get("capital_risk_sizing_owner_digest_ref", "")).strip()
    if not owner_ref:
        raise ValueError("capital_risk_sizing_owner_digest_ref_missing")
    if owner_ref != CAPITAL_RISK_SIZING_CONTRACT_VERSION:
        raise ValueError("capital_risk_sizing_owner_digest_ref_mismatch")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("capital_risk_sizing_backtest_state_file_digest_mismatch")

    protective_stop = decoded.get("protective_stop_price")
    if protective_stop is None or (
        isinstance(protective_stop, str) and not protective_stop.strip()
    ):
        raise ValueError("protective_stop_price_missing")

    maximum_positions = int(decoded.get("maximum_positions", 1))
    if maximum_positions <= 0:
        raise ValueError("maximum_positions_invalid")
    current_open_positions_count = int(decoded.get("current_open_positions_count", 0))
    if current_open_positions_count < 0:
        raise ValueError("current_open_positions_count_invalid")

    return CapitalRiskSizingBacktestStateFileRecordV0(
        instrument_id=instrument_id,
        reference_price=str(decoded["reference_price"]),
        protective_stop_price=str(protective_stop),
        account_equity=str(decoded["account_equity"]),
        scope_capital_limit=str(decoded["scope_capital_limit"]),
        per_trade_risk_limit=str(decoded["per_trade_risk_limit"]),
        total_capital_limit=str(decoded["total_capital_limit"]),
        daily_loss_remaining_budget=str(decoded["daily_loss_remaining_budget"]),
        current_reconciled_exposure=str(decoded["current_reconciled_exposure"]),
        lot_size=str(decoded["lot_size"]),
        minimum_quantity=str(decoded["minimum_quantity"]),
        maximum_quantity=str(decoded["maximum_quantity"]),
        minimum_notional=str(decoded["minimum_notional"]),
        tick_size=str(decoded["tick_size"]),
        maximum_positions=maximum_positions,
        current_open_positions_count=current_open_positions_count,
        reconciliation_status=str(decoded.get("reconciliation_status", "RECONCILED")).strip()
        or "RECONCILED",
        capital_risk_sizing_owner_digest_ref=owner_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_capital_risk_sizing_backtest_state_file_digest_v0(
    record: CapitalRiskSizingBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("capital_risk_sizing_backtest_state_file_digest_mismatch")


def _capital_context_from_state_file(
    state_file: CapitalRiskSizingBacktestStateFileRecordV0,
):
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        CanonicalCoreRuntimeCapitalContextV0,
    )

    instrument = InstrumentQuantityConstraintsV1(
        instrument_id=state_file.instrument_id,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal(state_file.lot_size),
        minimum_quantity=Decimal(state_file.minimum_quantity),
        maximum_quantity=Decimal(state_file.maximum_quantity),
        minimum_notional=Decimal(state_file.minimum_notional),
        tick_size=Decimal(state_file.tick_size),
        instrument_metadata_version="backtest_state_file_futures_metadata_v0",
    )
    return CanonicalCoreRuntimeCapitalContextV0(
        reference_price=Decimal(state_file.reference_price),
        protective_stop_price=Decimal(state_file.protective_stop_price),
        account_equity=Decimal(state_file.account_equity),
        scope_capital_limit=Decimal(state_file.scope_capital_limit),
        per_trade_risk_limit=Decimal(state_file.per_trade_risk_limit),
        total_capital_limit=Decimal(state_file.total_capital_limit),
        daily_loss_remaining_budget=Decimal(state_file.daily_loss_remaining_budget),
        current_reconciled_exposure=Decimal(state_file.current_reconciled_exposure),
        instrument=instrument,
        maximum_positions=state_file.maximum_positions,
        current_open_positions_count=state_file.current_open_positions_count,
        reconciliation_status=state_file.reconciliation_status,
        config_digest=state_file.state_file_digest_ref,
    )


def bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: CapitalRiskSizingBacktestStateFileRecordV0,
) -> CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file capital/risk/sizing through the Surface H offline adapter."""
    offline_binding = bind_capital_risk_sizing_offline_replay_evidence_v0(
        evidence,
        capital_context=_capital_context_from_state_file(state_file),
    )
    if not capital_risk_sizing_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("capital_risk_sizing_backtest_state_file_non_authority_boundary_failed")

    sizing_decision = offline_binding.sizing_decision
    sizing_outcome = sizing_decision.outcome.value if sizing_decision is not None else ""
    quantity_provenance_represented = bool(offline_binding.quantity_provenance_ref)
    risk_limits_represented = all(
        (
            state_file.scope_capital_limit,
            state_file.per_trade_risk_limit,
            state_file.total_capital_limit,
            state_file.daily_loss_remaining_budget,
        )
    )
    return CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0(
        capital_risk_sizing_boundary_backtest_state_file_bound=True,
        quantity_provenance_represented=quantity_provenance_represented,
        risk_limits_represented=risk_limits_represented,
        quantity_provenance_ref=offline_binding.quantity_provenance_ref,
        risk_sizing_ref=offline_binding.risk_sizing_ref,
        quantity_status=offline_binding.quantity_status,
        sizing_outcome=sizing_outcome,
        order_intent_boundary_not_adapter_compatible=True,
        capital_risk_sizing_owner_digest_ref=state_file.capital_risk_sizing_owner_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_h_adapter_owner_ref=CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_capital_risk_sizing_state_file_boundary_only_v0(
    state_file: CapitalRiskSizingBacktestStateFileRecordV0,
    *,
    decision_outcome: str = "enter_long",
) -> CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-capital-risk-sizing-state-file-stub",
        replay_id="backtest-capital-risk-sizing-state-file-stub",
        instrument_id=state_file.instrument_id,
        trading_epoch=0,
        composition_result_id="stub",
        entry_exit_policy_ref="stub",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("stub",),
        decision_precedence_trace=("stub",),
        config_digest="stub",
        implementation_digest="stub",
    )
    return bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0(
        stub,
        state_file=state_file,
    )


def apply_backtest_capital_risk_sizing_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Fail-closed backtest exposure representation — no runtime orders."""
    if position_signal == 0:
        return 0
    if not evidence.capital_risk_sizing_boundary_backtest_state_file_bound:
        return 0

    binding = evidence.offline_binding
    if binding.quantity_status in _BLOCKING_QUANTITY_STATUSES:
        return 0
    if not binding.quantity_provenance_ref:
        return 0
    if binding.sizing_decision is not None:
        if binding.sizing_decision.outcome is CapitalRiskSizingOutcome.BLOCKED:
            return 0
        position_sizing = binding.sizing_decision.canonical_position_sizing
        if position_sizing is not None:
            if position_sizing.rounded_quantity <= Decimal("0"):
                return 0
            if position_sizing.rounded_quantity > position_sizing.bounded_quantity_before_rounding:
                return 0
    return position_signal


def backtest_capital_risk_sizing_state_file_binding_non_authority_ok_v0(
    evidence: CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.capital_risk_sizing_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    if not evidence.order_intent_boundary_not_adapter_compatible:
        return False
    return capital_risk_sizing_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_capital_risk_sizing_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> CapitalRiskSizingBacktestStateFileRecordV0:
    record = parse_capital_risk_sizing_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_capital_risk_sizing_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
