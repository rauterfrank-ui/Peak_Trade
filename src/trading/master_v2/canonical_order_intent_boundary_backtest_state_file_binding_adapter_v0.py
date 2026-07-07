# src/trading/master_v2/canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0.py
"""
Backtest state-file adapter: binds MV2 research backtest wiring to canonical
order intent semantics via the Surface I offline replay adapter.

Wiring-only parity slice — no runtime authority, no order effects.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.governance.canonical_order_intent_v1 import (
    CONTRACT_VERSION as CANONICAL_ORDER_INTENT_CONTRACT_VERSION,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    CanonicalOrderIntentOfflineReplayBindingResultV0,
    bind_canonical_order_intent_offline_replay_evidence_v0,
    canonical_order_intent_binding_non_authority_boundary_ok_v0,
)
from trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0 import (
    CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
)

CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_LAYER_VERSION = "v0"
CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER = (
    "trading.master_v2.canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0"
)
CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION = (
    "canonical_order_intent_boundary_backtest_state_file_v0"
)

_BLOCKING_INTENT_OUTCOMES = frozenset({"BLOCKED"})


@dataclass(frozen=True)
class CanonicalOrderIntentBacktestStateFileRecordV0:
    """Parsed canonical order intent backtest state-file payload."""

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
    canonical_order_intent_owner_digest_ref: str
    state_file_digest_ref: str
    raw_payload: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0:
    canonical_order_intent_boundary_backtest_state_file_bound: bool
    order_intent_provenance_represented: bool
    order_intent_ref: str
    order_intent_effect: str
    intent_outcome: str
    adapter_compatible: bool
    canonical_order_intent_owner_digest_ref: str
    state_file_digest_ref: str
    runtime_authority: bool
    orders_allowed: bool
    credentials_used: bool
    economic_evaluation: bool
    offline_binding: CanonicalOrderIntentOfflineReplayBindingResultV0
    surface_i_adapter_owner_ref: str


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


def parse_canonical_order_intent_backtest_state_file_v0(
    *,
    path: Path | None = None,
    payload: Mapping[str, Any] | None = None,
    raw_bytes: bytes | None = None,
) -> CanonicalOrderIntentBacktestStateFileRecordV0:
    """Parse backtest canonical order intent state file. Fail-closed on invalid input."""
    if path is None and payload is None and raw_bytes is None:
        raise ValueError("canonical_order_intent_backtest_state_file_input_missing")

    if raw_bytes is None:
        if path is not None:
            if not path.is_file():
                raise ValueError("canonical_order_intent_backtest_state_file_missing")
            raw_bytes = path.read_bytes()
        elif payload is not None:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        else:
            raise ValueError("canonical_order_intent_backtest_state_file_input_missing")

    if not raw_bytes.strip():
        raise ValueError("canonical_order_intent_backtest_state_file_empty")

    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("canonical_order_intent_backtest_state_file_corrupt") from exc

    if not isinstance(decoded, Mapping):
        raise ValueError("canonical_order_intent_backtest_state_file_invalid_shape")

    state_file_digest_ref = compute_backtest_state_file_digest_from_payload_v0(decoded)

    schema_version = decoded.get("schema_version", "")
    if (
        schema_version
        and schema_version != CANONICAL_ORDER_INTENT_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION
    ):
        raise ValueError("canonical_order_intent_backtest_state_file_schema_version_mismatch")

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

    owner_ref = str(decoded.get("canonical_order_intent_owner_digest_ref", "")).strip()
    if not owner_ref:
        raise ValueError("canonical_order_intent_owner_digest_ref_missing")
    if owner_ref != CANONICAL_ORDER_INTENT_CONTRACT_VERSION:
        raise ValueError("canonical_order_intent_owner_digest_ref_mismatch")

    expected_digest = str(decoded.get("state_file_digest_ref", "")).strip()
    if expected_digest and expected_digest != state_file_digest_ref:
        raise ValueError("canonical_order_intent_backtest_state_file_digest_mismatch")

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

    return CanonicalOrderIntentBacktestStateFileRecordV0(
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
        canonical_order_intent_owner_digest_ref=owner_ref,
        state_file_digest_ref=state_file_digest_ref,
        raw_payload=dict(decoded),
    )


def verify_canonical_order_intent_backtest_state_file_digest_v0(
    record: CanonicalOrderIntentBacktestStateFileRecordV0,
    *,
    expected_digest_ref: str,
) -> None:
    """Fail-closed when an expected digest does not match the parsed state file."""
    if not expected_digest_ref.strip():
        raise ValueError("expected_state_file_digest_ref_missing")
    if record.state_file_digest_ref != expected_digest_ref.strip():
        raise ValueError("canonical_order_intent_backtest_state_file_digest_mismatch")


def _capital_context_from_state_file(
    state_file: CanonicalOrderIntentBacktestStateFileRecordV0,
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


def bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0(
    evidence: "CanonicalTradingDecisionEvidenceV1",
    *,
    state_file: CanonicalOrderIntentBacktestStateFileRecordV0,
    sizing_evidence: CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
) -> CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0:
    """Bind backtest state-file order intent through the Surface I offline adapter."""
    if not sizing_evidence.capital_risk_sizing_boundary_backtest_state_file_bound:
        raise ValueError("canonical_order_intent_backtest_state_file_sizing_evidence_missing")

    sized_evidence = sizing_evidence.offline_binding.evidence
    sizing_decision = sizing_evidence.offline_binding.sizing_decision
    offline_binding = bind_canonical_order_intent_offline_replay_evidence_v0(
        sized_evidence,
        sizing_decision=sizing_decision,
        capital_context=_capital_context_from_state_file(state_file),
    )
    if not canonical_order_intent_binding_non_authority_boundary_ok_v0(offline_binding):
        raise ValueError("canonical_order_intent_backtest_state_file_non_authority_boundary_failed")

    intent = offline_binding.canonical_intent
    adapter_compatible = bool(intent.adapter_compatible) if intent is not None else False
    order_intent_provenance_represented = bool(offline_binding.order_intent_ref)
    return CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0(
        canonical_order_intent_boundary_backtest_state_file_bound=True,
        order_intent_provenance_represented=order_intent_provenance_represented,
        order_intent_ref=offline_binding.order_intent_ref,
        order_intent_effect=offline_binding.order_intent_effect,
        intent_outcome=offline_binding.intent_outcome,
        adapter_compatible=adapter_compatible,
        canonical_order_intent_owner_digest_ref=state_file.canonical_order_intent_owner_digest_ref,
        state_file_digest_ref=state_file.state_file_digest_ref,
        runtime_authority=False,
        orders_allowed=False,
        credentials_used=False,
        economic_evaluation=False,
        offline_binding=offline_binding,
        surface_i_adapter_owner_ref=CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    )


def evaluate_backtest_canonical_order_intent_state_file_boundary_only_v0(
    state_file: CanonicalOrderIntentBacktestStateFileRecordV0,
    *,
    sizing_evidence: CapitalRiskSizingBoundaryBacktestStateFileEvidenceV0,
    decision_outcome: str = "enter_long",
) -> CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0:
    """Evaluate boundary evidence fields without mutating decision evidence."""
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        build_scenario_tick_decision_evidence_v0,
    )

    stub = build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-canonical-order-intent-state-file-stub",
        replay_id="backtest-canonical-order-intent-state-file-stub",
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
    _ = stub
    return bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0(
        sizing_evidence.offline_binding.evidence,
        state_file=state_file,
        sizing_evidence=sizing_evidence,
    )


def apply_backtest_canonical_order_intent_exposure_gate_v0(
    position_signal: int,
    *,
    evidence: CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0,
) -> int:
    """Fail-closed backtest exposure representation — no runtime orders."""
    if position_signal == 0:
        return 0
    if not evidence.canonical_order_intent_boundary_backtest_state_file_bound:
        return 0
    if evidence.intent_outcome in _BLOCKING_INTENT_OUTCOMES:
        return 0
    if not evidence.order_intent_ref:
        return 0
    if evidence.adapter_compatible:
        return 0
    if evidence.order_intent_effect != ORDER_INTENT_EFFECT_BOUND_OFFLINE:
        return 0
    return position_signal


def backtest_canonical_order_intent_state_file_binding_non_authority_ok_v0(
    evidence: CanonicalOrderIntentBoundaryBacktestStateFileEvidenceV0,
) -> bool:
    if not evidence.canonical_order_intent_boundary_backtest_state_file_bound:
        return False
    if evidence.runtime_authority or evidence.orders_allowed:
        return False
    if evidence.credentials_used or evidence.economic_evaluation:
        return False
    if evidence.adapter_compatible:
        return False
    return canonical_order_intent_binding_non_authority_boundary_ok_v0(evidence.offline_binding)


def load_canonical_order_intent_backtest_state_file_record_v0(
    path: Path,
    *,
    expected_digest_ref: str = "",
) -> CanonicalOrderIntentBacktestStateFileRecordV0:
    record = parse_canonical_order_intent_backtest_state_file_v0(path=path)
    if expected_digest_ref:
        verify_canonical_order_intent_backtest_state_file_digest_v0(
            record,
            expected_digest_ref=expected_digest_ref,
        )
    return record


from trading.master_v2.canonical_trading_decision_evidence_v1 import (  # noqa: E402
    CanonicalTradingDecisionEvidenceV1,
)
