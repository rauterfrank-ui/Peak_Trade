"""MV2 offline boundary dynamic price/stop context v1 (non-authorizing).

Separates per-bar mark-price semantics (MV2+DP integrated replay) from digest-pinned
static boundary state-file fields. No runtime, order, or promotion effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping

from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    derive_protective_stop_price_from_adverse_exit_v0,
)

MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1 = (
    "mv2_integrated_replay_bar_mark_price_v1"
)
MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_PRODUCER_LINEAGE_REF_V1 = (
    "integrated_offline_trading_logic_replay_v1.bound_context.mark_price"
)
MV2_OFFLINE_BOUNDARY_DYNAMIC_STOP_PRODUCER_LINEAGE_REF_V1 = (
    "capital_risk_sizing_offline_replay_binding_adapter_v0."
    "derive_protective_stop_price_from_adverse_exit_v0"
)

_DYNAMIC_PRICE_FIELDS = frozenset({"reference_price", "protective_stop_price"})
_DYNAMIC_FORBIDDEN_CURRENT_AUTHORITY_FIELDS = frozenset(
    {
        "daily_loss_remaining_budget",
        "maximum_quantity",
    }
)
CURRENT_DYNAMIC_BOUNDARY_DAILY_LOSS_LINEAGE_REF_V1 = (
    "capital_risk_sizing_boundary_backtest_state_file_v0.per_trade_risk_limit"
    "_when_daily_loss_omitted_on_dynamic_path"
)
CURRENT_DYNAMIC_BOUNDARY_MAX_QUANTITY_LINEAGE_REF_V1 = (
    "instrument_quantity_constraints_v1.maximum_quantity_none"
)


@dataclass(frozen=True)
class MV2OfflineBoundaryDynamicPriceContextV1:
    reference_price: Decimal
    protective_stop_price: Decimal | None
    producer_lineage_ref: str = MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_PRODUCER_LINEAGE_REF_V1
    stop_producer_lineage_ref: str = MV2_OFFLINE_BOUNDARY_DYNAMIC_STOP_PRODUCER_LINEAGE_REF_V1


def dynamic_price_context_binding_ref_from_payload_v0(
    payload: Mapping[str, Any],
) -> str | None:
    raw = payload.get("dynamic_price_context_binding_ref")
    if raw is None:
        return None
    text = str(raw).strip()
    return text or None


def payload_uses_dynamic_price_context_v0(payload: Mapping[str, Any]) -> bool:
    ref = dynamic_price_context_binding_ref_from_payload_v0(payload)
    return ref == MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1


def validate_dynamic_price_context_binding_ref_v0(
    payload: Mapping[str, Any],
) -> None:
    ref = dynamic_price_context_binding_ref_from_payload_v0(payload)
    if ref is None:
        return
    if ref != MV2_OFFLINE_BOUNDARY_DYNAMIC_PRICE_CONTEXT_BINDING_REF_V1:
        raise ValueError("dynamic_price_context_binding_ref_unsupported")
    forbidden = _DYNAMIC_PRICE_FIELDS | _DYNAMIC_FORBIDDEN_CURRENT_AUTHORITY_FIELDS
    for field in forbidden:
        if field in payload and payload[field] not in (None, ""):
            raise ValueError(f"dynamic_boundary_forbidden_static_field:{field}")


def backtest_state_file_digest_stripped_payload_v0(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Canonical digest input: static fields only when dynamic price binding is active."""
    stripped = {k: v for k, v in payload.items() if k != "state_file_digest_ref"}
    if payload_uses_dynamic_price_context_v0(payload):
        for field in _DYNAMIC_PRICE_FIELDS | _DYNAMIC_FORBIDDEN_CURRENT_AUTHORITY_FIELDS:
            stripped.pop(field, None)
    return stripped


def build_mv2_dynamic_boundary_capital_context_v1(
    *,
    state_file: Any,
    dynamic_price_context: MV2OfflineBoundaryDynamicPriceContextV1,
):
    """Boundary + CURRENT eval CRS capital context from digest-pinned state file + dynamic price.

    Omits historical offline-replay fixture scalars (adapter daily_loss=25, max_qty=100).
    When daily_loss is absent on the dynamic state file, daily envelope aligns to
    per_trade_risk_limit from the same file (CRS required Decimal; no tighter daily cap).
    maximum_quantity uses canonical Optional absence (None = no configured max cap).
    """
    from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
        CanonicalCoreRuntimeCapitalContextV0,
    )
    from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
        CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    )

    per_trade = Decimal(str(state_file.per_trade_risk_limit))
    instrument = InstrumentQuantityConstraintsV1(
        instrument_id=str(state_file.instrument_id),
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal(str(state_file.lot_size)),
        minimum_quantity=Decimal(str(state_file.minimum_quantity)),
        maximum_quantity=None,
        minimum_notional=Decimal(str(state_file.minimum_notional)),
        tick_size=Decimal(str(state_file.tick_size)),
        instrument_metadata_version="backtest_state_file_futures_metadata_v0",
    )
    return CanonicalCoreRuntimeCapitalContextV0(
        reference_price=dynamic_price_context.reference_price,
        protective_stop_price=dynamic_price_context.protective_stop_price,
        account_equity=Decimal(str(state_file.account_equity)),
        scope_capital_limit=Decimal(str(state_file.scope_capital_limit)),
        per_trade_risk_limit=per_trade,
        total_capital_limit=Decimal(str(state_file.total_capital_limit)),
        daily_loss_remaining_budget=per_trade,
        current_reconciled_exposure=Decimal(str(state_file.current_reconciled_exposure)),
        instrument=instrument,
        maximum_positions=int(state_file.maximum_positions),
        current_open_positions_count=int(state_file.current_open_positions_count),
        reconciliation_status=str(state_file.reconciliation_status),
        config_digest=str(state_file.state_file_digest_ref),
        capital_risk_mode=CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    )


def build_mv2_dynamic_boundary_capital_context_replay_parity_v1(
    *,
    state_file: Any,
    dynamic_price_context: MV2OfflineBoundaryDynamicPriceContextV1,
):
    """Deprecated alias — use build_mv2_dynamic_boundary_capital_context_v1."""
    return build_mv2_dynamic_boundary_capital_context_v1(
        state_file=state_file,
        dynamic_price_context=dynamic_price_context,
    )


def build_mv2_offline_boundary_dynamic_price_context_v1(
    *,
    mark_price: Decimal | float | str,
    selected_side: str,
    adverse_exit_distance: Decimal | float | str,
) -> MV2OfflineBoundaryDynamicPriceContextV1:
    reference = Decimal(str(mark_price))
    stop = derive_protective_stop_price_from_adverse_exit_v0(
        selected_side=selected_side,
        reference_price=reference,
        adverse_exit_distance=adverse_exit_distance,
    )
    return MV2OfflineBoundaryDynamicPriceContextV1(
        reference_price=reference,
        protective_stop_price=stop,
    )
