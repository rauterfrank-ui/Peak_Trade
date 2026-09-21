"""Build archive-sibling Risk/Sizing/Capital fields from replay intermediate only.

Maps already-produced CapitalRiskSizingDecisionV1 on IntegratedOfflineReplayIntermediateV1.
Does not call evaluate_capital_risk_sizing_v1 or recompute sizing math.
"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
)
from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.constants_v1 import (
    ERROR_REPLAY_COMMIT_INCOMPLETE,
    ERROR_SIZING_DECISION_ABSENT,
    ERROR_SIZING_STATUS_INCOMPLETE,
)
from src.trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    compute_risk_sizing_decision_ref_v0,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_materializer_v1 import (
    coerce_risk_sizing_capital_fields_mapping_v1,
)


def _enum_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _resolve_sizing_status(decision: CapitalRiskSizingDecisionV1) -> str | None:
    post = decision.post_sizing_risk
    if post is not None:
        return _enum_value(post.status)
    provenance = decision.quantity_provenance
    if provenance is not None:
        return _enum_value(provenance.final_quantity_status)
    # Same fallbacks as capital_risk_sizing_offline_replay_binding_adapter_v0._quantity_status_from_sizing_v0
    if decision.outcome is CapitalRiskSizingOutcome.BLOCKED:
        return "BLOCK"
    return None


def build_risk_sizing_capital_sibling_payload_from_replay_commit_v1(
    *,
    replay_intermediate: object | None,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Map replay-attached sizing decision into sibling export shape (field copy only)."""
    if replay_intermediate is None:
        return None, (ERROR_REPLAY_COMMIT_INCOMPLETE,)

    sizing = getattr(replay_intermediate, "capital_risk_sizing_decision", None)
    if sizing is None or not isinstance(sizing, CapitalRiskSizingDecisionV1):
        return None, (ERROR_SIZING_DECISION_ABSENT,)

    sizing_status = _resolve_sizing_status(sizing)
    if sizing_status is None:
        return None, (ERROR_SIZING_STATUS_INCOMPLETE,)

    risk_status = _enum_value(sizing.pre_sizing_risk.status)
    capital_status = _enum_value(sizing.scope_capital_envelope.status)

    raw_fields: dict[str, Any] = {
        "risk_status": risk_status,
        "sizing_status": sizing_status,
        "capital_status": capital_status,
        "reason_codes": list(sizing.reason_codes),
        "risk_sizing_ref": compute_risk_sizing_decision_ref_v0(sizing),
        "schema_version": "v1",
    }
    qty = sizing.final_quantity
    if isinstance(qty, Decimal) and qty.is_finite() and qty > 0:
        raw_fields["quantity"] = float(qty)

    coerced, errors = coerce_risk_sizing_capital_fields_mapping_v1(raw_fields)
    if coerced is None:
        return None, errors
    return dict(coerced), ()
