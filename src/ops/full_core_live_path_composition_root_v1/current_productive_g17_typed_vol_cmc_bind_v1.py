"""CURRENT_PRODUCTIVE thin join: JOIN-2 G17 producer -> existing CMC typed bind.

Owner lock for this S2-BIND MS2 slice only (prospective, not historical rewrite):
ESTIMATE_ABSENT_CMC_POLICY=BIND_ONLY_WHEN_PRODUCED
INGEST_SAMPLE=false
PRESENCE_GATE_IN_THIS_WP=false

Reuses the JOIN-2 producer object and
``bind_typed_canonical_volatility_estimate_into_market_context_v1``.
Does not ingest, create, restore, wrap a second persistence owner, mutate
the presence gate, or own HardeningSession.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass

from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
    TypedRuntimeProducerOutcomeV1,
)

PACKAGE_MARKER = "FULL_CORE_G17_TYPED_VOL_CMC_BIND_V1=true"
BIND_OWNER = (
    "ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1"
)
ESTIMATE_ABSENT_CMC_POLICY = "BIND_ONLY_WHEN_PRODUCED"
INGEST_SAMPLE = False
PRESENCE_GATE_IN_THIS_WP = False
CMC_BINDING_PERFORMED = True
PRESENCE_GATE_MUTATED = False
HARDENING_SESSION_OWNER = False
SIDESTATE_CURSOR_OWNER = False
ECONOMIC_MD_OWNER = False
GLOBAL_SINGLETON = False
JOIN_1_REWRITTEN = False
JOIN_2_REWRITTEN = False


class CurrentProductiveG17CmcBindError(ValueError):
    """Fail-closed CURRENT_PRODUCTIVE G17 CMC bind violation."""

    def __init__(self, reason_code: str, detail: str = "") -> None:
        self.reason_code = reason_code
        self.detail = detail
        super().__init__(f"{reason_code}:{detail}" if detail else reason_code)


@dataclass(frozen=True)
class CurrentProductiveG17CmcBindResultV1:
    context: CanonicalMarketContextV1
    bind_performed: bool
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1 | None
    outcome: str
    estimate_present: bool


def apply_current_productive_g17_typed_vol_cmc_bind_v1(
    context: CanonicalMarketContextV1,
    *,
    producer: CanonicalVolatilityTypedRuntimeProducerScaffoldV1 | None,
) -> CurrentProductiveG17CmcBindResultV1:
    """Bind typed G17 estimate into CMC only when this-cycle outcome is PRODUCED.

    Absent estimate returns the same context object unchanged.
    """
    if producer is None:
        return CurrentProductiveG17CmcBindResultV1(
            context=context,
            bind_performed=False,
            producer=None,
            outcome="",
            estimate_present=False,
        )
    if not isinstance(producer, CanonicalVolatilityTypedRuntimeProducerScaffoldV1):
        raise CurrentProductiveG17CmcBindError(
            "G17_CMC_BIND_PRODUCER_TYPE_INVALID",
            type(producer).__name__,
        )
    port = producer.output_port_v1()
    outcome = str(port.outcome.value)
    estimate_present = port.estimate is not None
    if (
        port.outcome is not TypedRuntimeProducerOutcomeV1.PRODUCED
        or port.estimate is None
        or port.ready_for_binding_handoff is not True
    ):
        return CurrentProductiveG17CmcBindResultV1(
            context=context,
            bind_performed=False,
            producer=producer,
            outcome=outcome,
            estimate_present=estimate_present,
        )
    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        context,
        port.estimate,
    )
    return CurrentProductiveG17CmcBindResultV1(
        context=bound,
        bind_performed=True,
        producer=producer,
        outcome=outcome,
        estimate_present=True,
    )


__all__ = [
    "BIND_OWNER",
    "CMC_BINDING_PERFORMED",
    "CurrentProductiveG17CmcBindError",
    "CurrentProductiveG17CmcBindResultV1",
    "ECONOMIC_MD_OWNER",
    "ESTIMATE_ABSENT_CMC_POLICY",
    "GLOBAL_SINGLETON",
    "HARDENING_SESSION_OWNER",
    "INGEST_SAMPLE",
    "JOIN_1_REWRITTEN",
    "JOIN_2_REWRITTEN",
    "PACKAGE_MARKER",
    "PRESENCE_GATE_IN_THIS_WP",
    "PRESENCE_GATE_MUTATED",
    "SIDESTATE_CURSOR_OWNER",
    "apply_current_productive_g17_typed_vol_cmc_bind_v1",
]
