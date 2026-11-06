"""Offline Z2AP flatten construction + gate binding.

Composes observation, account-wide cap, price policy, and request
serialization. Never POSTs, never enables live wire, and never claims
LIVE_FLATTEN_PROVABILITY=PROVEN.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    ORDER_COUNT_LIMIT,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    FlattenPricePermitV1,
    LIVE_FLATTEN_PROVABILITY_STATUS,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_orchestration_contract_v1 import (
    evaluate_canary_flatten_orchestration_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_post_submit_evidence_state_v1 import (
    STATE_NOT_SUBMITTED,
    evaluate_canary_flatten_post_submit_evidence_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LiveCanaryFlattenSubmitTransportError,
    build_canary_flatten_submit_request_v1,
)


class LiveCanaryFlattenOfflinePipelineError(RuntimeError):
    """Fail-closed offline flatten construction/gate binding."""


@dataclass(frozen=True)
class OfflineFlattenConstructionVerdictV1:
    """Construction/gate result. Submit remains unattempted."""

    submit_eligible: bool
    request_body: dict[str, Any] | None
    evidence_state: str
    live_flatten_provability: str
    live_wire_enabled: bool
    live_authorized: bool
    order_count_limit: int
    freshness_threshold_ms: int
    blocking_reasons: tuple[str, ...]
    audit_class: str
    productive_venue_proof: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "submit_eligible": self.submit_eligible,
            "request_body": self.request_body,
            "evidence_state": self.evidence_state,
            "live_flatten_provability": self.live_flatten_provability,
            "live_wire_enabled": self.live_wire_enabled,
            "live_authorized": self.live_authorized,
            "order_count_limit": self.order_count_limit,
            "freshness_threshold_ms": self.freshness_threshold_ms,
            "blocking_reasons": list(self.blocking_reasons),
            "audit_class": self.audit_class,
            "productive_venue_proof": self.productive_venue_proof,
        }


def _denied(reasons: tuple[str, ...]) -> OfflineFlattenConstructionVerdictV1:
    return OfflineFlattenConstructionVerdictV1(
        submit_eligible=False,
        request_body=None,
        evidence_state=STATE_NOT_SUBMITTED,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        live_wire_enabled=False,
        live_authorized=False,
        order_count_limit=ORDER_COUNT_LIMIT,
        freshness_threshold_ms=FRESHNESS_THRESHOLD_MS,
        blocking_reasons=reasons,
        audit_class="offline_intent_construction",
        productive_venue_proof=False,
    )


def evaluate_offline_flatten_construction_and_gates_v1(
    *,
    positions_payload: Mapping[str, Any],
    price_input: FlattenPriceInputV1,
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    requested_qty: str | None = None,
    confirm_token: str | None = None,
    price_permit: FlattenPricePermitV1 | None = None,
) -> OfflineFlattenConstructionVerdictV1:
    """Build a flatten LIMIT body through existing gates. Never POSTs."""
    del confirm_token  # flatten has no confirm-token authority; absence does not unlock
    if LIVE_AUTHORIZED or LIVE_ENABLED or LIVE_ARMED:
        return _denied(("LIVE_DISABLED_DEFAULT",))
    if DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED:
        raise LiveCanaryFlattenOfflinePipelineError("FLATTEN_LIVE_WIRE_MUST_REMAIN_DISABLED")
    if ORDER_COUNT_LIMIT != 1:
        return _denied(("ORDER_COUNT_LIMIT_MUST_REMAIN_1",))
    target = str(instrument_id or "").strip()
    if target != DEFAULT_INSTRUMENT_ID:
        return _denied(("INSTRUMENT_BINDING_MISMATCH",))

    orch = evaluate_canary_flatten_orchestration_contract_v1(
        positions_payload=positions_payload,
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        instrument_id=target,
    )
    if not orch.permit_issued or orch.permit is None or orch.flatten_plan is None:
        return _denied(tuple(orch.blocking_reasons) or ("FLATTEN_ORCHESTRATION_DENIED",))
    if orch.submit_reachable is not False:
        return _denied(("FLATTEN_SUBMIT_REACHABLE_FORBIDDEN",))

    decision = evaluate_canary_flatten_limit_price_contract_v1(price_input)
    issued = price_permit if price_permit is not None else decision.permit
    if issued is None:
        return _denied(tuple(decision.reject_reasons) or ("FLATTEN_PRICE_PERMIT_MISSING",))

    try:
        body = build_canary_flatten_submit_request_v1(
            permit=orch.permit,
            plan=orch.flatten_plan,
            price_permit=issued,
            positions_payload=positions_payload,
            instrument_id=target,
            requested_qty=requested_qty,
        )
    except LiveCanaryFlattenSubmitTransportError as exc:
        return _denied((str(exc),))

    evidence = evaluate_canary_flatten_post_submit_evidence_state_v1(
        submit_attempted=False,
        send_attempted=False,
        instrument_id=target,
    )
    return OfflineFlattenConstructionVerdictV1(
        submit_eligible=True,
        request_body=body,
        evidence_state=evidence.evidence_state,
        live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
        live_wire_enabled=False,
        live_authorized=False,
        order_count_limit=ORDER_COUNT_LIMIT,
        freshness_threshold_ms=FRESHNESS_THRESHOLD_MS,
        blocking_reasons=(),
        audit_class="submit_eligible_state_not_posted",
        productive_venue_proof=False,
    )
