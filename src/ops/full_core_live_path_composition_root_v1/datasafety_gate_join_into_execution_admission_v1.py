"""Typed DataSafetyGate join into Full-Core execution admission.

Predicate producer only. Not an admission owner. Not activation, POST, or wire.

Invoked on FreshPretradeGetTransportResultV1 immediately after transport.get
and S2B bind, before A1/A2/A3 unwrap. Uses DataSafetyGate.check only.
Never ensure_allowed. Never infers LIVE_TRADE; only the S2B-bound
DataSafetyContext(REAL, LIVE_TRADE) may reach the gate.

UNBOUND / missing context: no gate call, fail-closed.
allowed=false: DENY.
Unexpected bind/check/context error: typed ERROR, no escaped bypass.

AUTHORITY_EFFECT=NONE
DATASAFETYGATE_JOIN=CONJUNCT_NOT_OWNER
RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from src.data.safety import (
    DataSafetyContext,
    DataSafetyGate,
    DataSourceKind,
    DataUsageContextKind,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import OWNER
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DataSafetyAdmissionStatusV1,
)

JOIN_SEAM_ID = "FULL_CORE_DATASAFETY_GATE_JOIN_INTO_EXECUTION_ADMISSION_SEAM_V1"
JOIN_AUTHORITY = OWNER
DATASAFETYGATE_JOIN_CLASS = "CONJUNCT_NOT_OWNER"

_STATUS_RANK = {
    DataSafetyAdmissionStatusV1.ERROR.value: 0,
    DataSafetyAdmissionStatusV1.DENIED.value: 1,
    DataSafetyAdmissionStatusV1.UNBOUND.value: 2,
    DataSafetyAdmissionStatusV1.MISSING.value: 3,
    DataSafetyAdmissionStatusV1.SATISFIED.value: 4,
}


def _is_bound_real_live_trade_context(context: object) -> bool:
    return (
        isinstance(context, DataSafetyContext)
        and context.source_kind is DataSourceKind.REAL
        and context.usage is DataUsageContextKind.LIVE_TRADE
    )


def aggregate_datasafety_admission_status_v1(statuses: tuple[str, ...]) -> str:
    """All-must-pass aggregate. Empty set is MISSING (fail-closed)."""
    if not statuses:
        return DataSafetyAdmissionStatusV1.MISSING.value
    return min(
        statuses,
        key=lambda item: _STATUS_RANK.get(item, -1),
    )


def evaluate_datasafety_admission_for_transport_result_v1(result: object) -> str:
    """Bind then check one transport result. Never ensure_allowed.

    Binder import is function-local to avoid a collect/binder import cycle.
    """
    from src.ops.full_core_live_path_composition_root_v1.datasafety_context_bind_from_fresh_pretrade_get_transport_result_v1 import (
        DISPOSITION_BOUND,
        bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1,
    )

    try:
        bound = bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(
            result  # type: ignore[arg-type]
        )
    except Exception:
        return DataSafetyAdmissionStatusV1.ERROR.value
    if bound.disposition != DISPOSITION_BOUND or bound.context is None:
        return DataSafetyAdmissionStatusV1.UNBOUND.value
    if not _is_bound_real_live_trade_context(bound.context):
        return DataSafetyAdmissionStatusV1.ERROR.value
    try:
        gate_result = DataSafetyGate.check(bound.context)
    except Exception:
        return DataSafetyAdmissionStatusV1.ERROR.value
    if gate_result.allowed is True:
        return DataSafetyAdmissionStatusV1.SATISFIED.value
    return DataSafetyAdmissionStatusV1.DENIED.value
