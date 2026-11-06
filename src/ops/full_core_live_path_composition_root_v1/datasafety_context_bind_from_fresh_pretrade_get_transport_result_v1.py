"""Full-Core DataSafetyContext bind from FreshPretradeGetTransportResultV1.

Owner-ratified binder: ops.full_core_live_path_composition_root_v1.
Boundary: FreshPretradeGetTransportResultV1 immediately after transport.get,
before A1/A2/A3 stamp-loss points.

Composes DataSafetyContext from:
  source_kind <- result.data_safety_source_kind (S1 stamp only; exact REAL value)
  usage       <- DataUsageContextKind.LIVE_TRADE (binder-supplied; not inferred)

LIVE_TRADE classifies intended CURRENT productive live-trade data usage only.
It grants no admission, activation, POST, wire-send, credentials, capital,
continuous-run, execution, selection, or trading authority.

FAIL_CLOSED: source_kind None or non-exact-REAL => no DataSafetyContext.
Does not invoke the data-safety gate. Does not remap foreign vocabularies.
Does not derive usage from admission-context tokens, master mode tokens,
standing live predicates, or from the REAL stamp itself.

AUTHORITY_EFFECT=RATIFIED_CONTEXT_BINDER_IMPLEMENTATION_ONLY
RUNTIME_AUTHORIZATION_EFFECT=NONE
DATASAFETYGATE_JOIN=false
"""

from __future__ import annotations

from dataclasses import dataclass

from src.data.safety import DataSafetyContext, DataSourceKind, DataUsageContextKind
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)

JOIN_SEAM_ID = "FULL_CORE_DATASAFETY_CONTEXT_BIND_FROM_FRESH_PRETRADE_GET_TRANSPORT_RESULT_SEAM_V1"
BINDING_BOUNDARY_TYPE = "FreshPretradeGetTransportResultV1"
BINDING_BOUNDARY_MOMENT = "IMMEDIATELY_AFTER_TRANSPORT_GET_BEFORE_A1_A2_A3_UNWRAP"
BINDER_OWNER = OWNER
BINDER_CAPABILITY_ID = CAPABILITY_ID
BOUND_USAGE = DataUsageContextKind.LIVE_TRADE

DISPOSITION_BOUND = "BOUND"
DISPOSITION_UNBOUND_FAIL_CLOSED = "UNBOUND_FAIL_CLOSED"

REASON_BOUND_LIVE_TRADE = "FULL_CORE_DATASAFETY_CONTEXT_BOUND_LIVE_TRADE"
REASON_SOURCE_KIND_UNBOUND = "DATA_SAFETY_SOURCE_KIND_UNBOUND"
REASON_SOURCE_KIND_NOT_EXACT_REAL = "DATA_SAFETY_SOURCE_KIND_NOT_EXACT_REAL"


@dataclass(frozen=True)
class FullCoreDataSafetyContextBindResultV1:
    """Typed bind outcome for later S2C consumption. No gate evaluation."""

    disposition: str
    context: DataSafetyContext | None
    reason_code: str
    binder_owner: str
    binder_capability_id: str
    binding_boundary_type: str
    binding_boundary_moment: str
    join_seam_id: str = JOIN_SEAM_ID
    authority_effect: str = "RATIFIED_CONTEXT_BINDER_IMPLEMENTATION_ONLY"
    datasafetygate_join: bool = False


def _unbound(*, reason_code: str) -> FullCoreDataSafetyContextBindResultV1:
    return FullCoreDataSafetyContextBindResultV1(
        disposition=DISPOSITION_UNBOUND_FAIL_CLOSED,
        context=None,
        reason_code=reason_code,
        binder_owner=BINDER_OWNER,
        binder_capability_id=BINDER_CAPABILITY_ID,
        binding_boundary_type=BINDING_BOUNDARY_TYPE,
        binding_boundary_moment=BINDING_BOUNDARY_MOMENT,
    )


def bind_full_core_datasafety_context_from_fresh_pretrade_get_transport_result_v1(
    result: FreshPretradeGetTransportResultV1,
) -> FullCoreDataSafetyContextBindResultV1:
    """Bind DataSafetyContext at the S2A carrier boundary. No gate call.

    LIVE_TRADE is supplied only by this ratified Full-Core binder function.
    Callers cannot pass usage. Standing live predicates are not consulted.
    """
    stamp = result.data_safety_source_kind
    if stamp is None:
        return _unbound(reason_code=REASON_SOURCE_KIND_UNBOUND)
    # Exact productive REAL stamp only. No remap, inheritance, or foreign vocab.
    if stamp != DataSourceKind.REAL.value:
        return _unbound(reason_code=REASON_SOURCE_KIND_NOT_EXACT_REAL)
    return FullCoreDataSafetyContextBindResultV1(
        disposition=DISPOSITION_BOUND,
        context=DataSafetyContext(
            source_kind=DataSourceKind.REAL,
            usage=BOUND_USAGE,
        ),
        reason_code=REASON_BOUND_LIVE_TRADE,
        binder_owner=BINDER_OWNER,
        binder_capability_id=BINDER_CAPABILITY_ID,
        binding_boundary_type=BINDING_BOUNDARY_TYPE,
        binding_boundary_moment=BINDING_BOUNDARY_MOMENT,
    )
