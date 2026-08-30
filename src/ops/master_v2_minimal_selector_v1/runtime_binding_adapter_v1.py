"""Narrowed runtime-binding adapter for Master V2 minimal selector V1.

OWNER_POLICY_VERSION=V1
HISTORICAL_CLAIM=false

Does not modify Cap 2.4 in place. Does not require ranking snapshots or
cadence-derived valid_until. Preserves fail-closed NO_SELECTION, native
identity, source integrity, override rejection, and non-activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.discovery_v1 import (
    discover_okx_eea_instruments_v1,
)
from src.ops.governed_futures_universe_producer_v1.models_v1 import compute_source_digest_v1
from src.ops.master_v2_minimal_selector_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    REASON_NO_SELECTION_OVERRIDE_REJECTED,
    RUNTIME_ACTIVATION_ALLOWED,
    STATUS_NO_SELECTION,
    STATUS_SELECTED,
    VENUE_DISCOVERY,
)
from src.ops.master_v2_minimal_selector_v1.models_v1 import MasterV2SelectionDecisionV1


@dataclass(frozen=True)
class MasterV2RuntimeBindingAdapterResultV1:
    ok: bool
    bound_native_instrument_id: Optional[str]
    decision_status: str
    decision_reason: str
    activation_allowed: bool
    live_authorized: bool
    orders_authorized: bool
    ranking_required: bool
    valid_until_required: bool
    failure_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "bound_native_instrument_id": self.bound_native_instrument_id,
            "decision_status": self.decision_status,
            "decision_reason": self.decision_reason,
            "activation_allowed": self.activation_allowed,
            "live_authorized": self.live_authorized,
            "orders_authorized": self.orders_authorized,
            "ranking_required": self.ranking_required,
            "valid_until_required": self.valid_until_required,
            "failure_codes": list(self.failure_codes),
        }


def _fail(
    *,
    decision: MasterV2SelectionDecisionV1,
    codes: Sequence[str],
) -> MasterV2RuntimeBindingAdapterResultV1:
    return MasterV2RuntimeBindingAdapterResultV1(
        ok=False,
        bound_native_instrument_id=None,
        decision_status=decision.decision_status,
        decision_reason=decision.decision_reason,
        activation_allowed=False,
        live_authorized=False,
        orders_authorized=False,
        ranking_required=False,
        valid_until_required=False,
        failure_codes=tuple(sorted(set(str(c) for c in codes))),
    )


def adapt_master_v2_selection_to_runtime_binding_v1(
    decision: MasterV2SelectionDecisionV1,
    *,
    source_payload: Mapping[str, Any] | None = None,
    mark_price_payload: Mapping[str, Any] | Sequence[str] | None = None,
    source_event_time: str | None = None,
    dashboard_selected_instrument: str | None = None,
    direct_instrument_override: str | None = None,
    ranking_snapshot: Mapping[str, Any] | None = None,
) -> MasterV2RuntimeBindingAdapterResultV1:
    """Bind a Master V2 selector decision without Cap 2.4 ranking/cadence gates."""
    _ = ranking_snapshot

    if LIVE_AUTHORIZED or ORDERS_AUTHORIZED or RUNTIME_ACTIVATION_ALLOWED:
        raise RuntimeError("INVARIANT_VIOLATION_AUTHORITY_FLAGS")

    if direct_instrument_override:
        return _fail(
            decision=decision,
            codes=("DIRECT_INSTRUMENT_OVERRIDE_REJECTED", REASON_NO_SELECTION_OVERRIDE_REJECTED),
        )

    if dashboard_selected_instrument:
        wanted = str(dashboard_selected_instrument)
        selected = decision.selected_native_instrument_id or ""
        if wanted not in {selected, ""}:
            return _fail(
                decision=decision,
                codes=("DASHBOARD_OVERRIDE_REJECTED", REASON_NO_SELECTION_OVERRIDE_REJECTED),
            )

    if (
        decision.decision_status == STATUS_NO_SELECTION
        or not decision.selected_native_instrument_id
    ):
        return _fail(decision=decision, codes=("NO_SELECTION",))

    if not decision.source_snapshot_digest or not decision.identity_digest:
        return _fail(decision=decision, codes=("NO_SELECTION_INCOMPLETE_SOURCE",))

    recomputed = decision.compute_identity_digest()
    if recomputed != decision.identity_digest:
        return _fail(decision=decision, codes=("IDENTITY_DIGEST_MISMATCH",))

    if source_payload is not None:
        discovery = discover_okx_eea_instruments_v1(
            source_payload=source_payload,
            mark_price_payload=mark_price_payload,
            source_event_time=source_event_time or decision.source_event_time,
            venue=VENUE_DISCOVERY,
            source_kind="okx_eea_public_instruments",
        )
        if not discovery.ok:
            return _fail(decision=decision, codes=("NO_SELECTION_STALE_OR_INVALID_SOURCE",))
        digest = compute_source_digest_v1(
            instruments=discovery.instruments,
            mark_price_supported_ids=sorted(discovery.mark_price_supported_ids),
            source_event_time=str(discovery.source_event_time or decision.source_event_time),
            venue=discovery.venue,
        )
        if digest != decision.source_snapshot_digest:
            return _fail(decision=decision, codes=("SOURCE_DIGEST_MISMATCH",))
        natives = {str(row.get("instId") or "") for row in discovery.instruments}
        if decision.selected_native_instrument_id not in natives:
            return _fail(decision=decision, codes=("NATIVE_VENUE_ID_MISMATCH",))

    if decision.decision_status != STATUS_SELECTED:
        return _fail(decision=decision, codes=("NO_SELECTION",))

    return MasterV2RuntimeBindingAdapterResultV1(
        ok=True,
        bound_native_instrument_id=decision.selected_native_instrument_id,
        decision_status=decision.decision_status,
        decision_reason=decision.decision_reason,
        activation_allowed=False,
        live_authorized=False,
        orders_authorized=False,
        ranking_required=False,
        valid_until_required=False,
        failure_codes=(),
    )
