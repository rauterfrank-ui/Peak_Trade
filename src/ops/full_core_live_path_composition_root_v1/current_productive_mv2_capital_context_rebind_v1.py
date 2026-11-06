"""Live 29P producer equity to MV2/T2 capital_context rebind (v1).

Closes LIVE_29P_TO_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_GAP by binding
CURRENT typed 29P available-for-sizing equity into CanonicalCoreRuntimeCapitalContextV0
together with productive capital/risk limit dimensions derived from that same typed
equity (no historical 25/500/100/10000 fixture literals).

MV2+DP supplies reference_price and protective_stop_price only. Does not POST.
Does not mint permits. RUNTIME_AUTHORIZATION_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal

from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    CanonicalCoreRuntimeCapitalContextV0,
)
from trading.master_v2.capital_risk_sizing_historical_default_deauthorization_v1 import (
    REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    DEFAULT_OFFLINE_BINDING_CONFIG_DIGEST,
    default_offline_replay_capital_context_v0,
)

REBIND_SEAM_ID = "CURRENT_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_SEAM_V1"
PRODUCTIVE_CAPITAL_RISK_LIMITS_FROM_TYPED_29P_EQUITY_LINEAGE_REF_V1 = (
    "current_productive_mv2_capital_context_rebind_v1."
    "resolve_productive_capital_risk_limits_from_29p_producer_v1"
)
CURRENT_PRODUCTIVE_MV2_CAPITAL_CONTEXT_REBIND_V1_CREATED = True


class CurrentProductiveMv2CapitalContextRebindError(RuntimeError):
    """Fail-closed productive MV2 capital context rebind violation."""


@dataclass(frozen=True)
class ProductiveCapitalRiskLimitsV1:
    scope_capital_limit: Decimal
    per_trade_risk_limit: Decimal
    total_capital_limit: Decimal
    daily_loss_remaining_budget: Decimal
    lineage_ref: str


def _productive_config_digest_v1(*, lineage_ref: str) -> str:
    material = f"{REBIND_SEAM_ID}:{lineage_ref}:{CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def resolve_productive_capital_risk_limits_from_29p_producer_v1(
    *,
    typed_account_equity: Decimal,
) -> ProductiveCapitalRiskLimitsV1 | None:
    """Bind productive CRS limit dimensions from typed 29P equity only."""
    if not typed_account_equity.is_finite() or typed_account_equity <= 0:
        return None
    return ProductiveCapitalRiskLimitsV1(
        scope_capital_limit=typed_account_equity,
        per_trade_risk_limit=typed_account_equity,
        total_capital_limit=typed_account_equity,
        daily_loss_remaining_budget=typed_account_equity,
        lineage_ref=PRODUCTIVE_CAPITAL_RISK_LIMITS_FROM_TYPED_29P_EQUITY_LINEAGE_REF_V1,
    )


def build_current_productive_live_account_capital_context_v1(
    *,
    instrument_id: str,
    typed_account_equity: Decimal,
    reference_price: Decimal,
    protective_stop_price: Decimal | None,
    instrument_constraints: InstrumentQuantityConstraintsV1,
) -> CanonicalCoreRuntimeCapitalContextV0:
    """Construct LIVE_ACCOUNT_BOUND capital_context for authoritative sizing."""
    limits = resolve_productive_capital_risk_limits_from_29p_producer_v1(
        typed_account_equity=typed_account_equity,
    )
    if limits is None:
        raise CurrentProductiveMv2CapitalContextRebindError(
            REASON_PRODUCTIVE_CAPITAL_RISK_LIMITS_UNRESOLVED
        )
    if protective_stop_price is None:
        raise CurrentProductiveMv2CapitalContextRebindError(
            "PROTECTIVE_STOP_DERIVATION_FAIL_CLOSED"
        )
    if instrument_constraints.instrument_id != instrument_id:
        raise CurrentProductiveMv2CapitalContextRebindError(
            "INSTRUMENT_METADATA_INSTRUMENT_ID_MISMATCH"
        )
    if not str(instrument_constraints.instrument_metadata_version or "").strip():
        raise CurrentProductiveMv2CapitalContextRebindError("INSTRUMENT_METADATA_VERSION_MISSING")
    ctx = default_offline_replay_capital_context_v0(
        instrument_id=instrument_id,
        reference_price=reference_price,
        protective_stop_price=protective_stop_price,
        account_equity=typed_account_equity,
        scope_capital_limit=limits.scope_capital_limit,
        per_trade_risk_limit=limits.per_trade_risk_limit,
        total_capital_limit=limits.total_capital_limit,
        daily_loss_remaining_budget=limits.daily_loss_remaining_budget,
        instrument=instrument_constraints,
        config_digest=_productive_config_digest_v1(lineage_ref=limits.lineage_ref),
        capital_risk_mode=CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    )
    if ctx.capital_risk_mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
        raise CurrentProductiveMv2CapitalContextRebindError("LIVE_ACCOUNT_BOUND_MODE_NOT_BOUND")
    if ctx.account_equity != typed_account_equity:
        raise CurrentProductiveMv2CapitalContextRebindError("PRODUCER_EQUITY_NOT_BOUND")
    _ = DEFAULT_OFFLINE_BINDING_CONFIG_DIGEST
    return ctx
