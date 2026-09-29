"""S6 continuous-run observation source: public readonly Fresh-C1 GET (S4A authority).

GET occurs inside poll(); S6 execute_network/perform_get remain false.
No credentials on public candles GET (auth_required=false).

RUNTIME_AUTHORIZATION_EFFECT=PUBLIC_READONLY_FRESH_C1_GET_FOR_CONTINUOUS_POLL_ONLY
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol

from src.ops.full_core_live_path_composition_root_v1.current_productive_bounded_continuous_run_owner_go_wiring_v1 import (
    append_fresh_c1_get_owner_go_consumption_v1,
    validate_bounded_continuous_run_owner_go_decision_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_continuous_cycle_orchestrator_v1 import (
    ContinuousObservationSourceV1,
    InjectedContinuousObservationV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    productive_auth_free_flat_occupancy_payloads_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_scoped_one_shot_c1_observation_source_v1 import (
    GET_BAR,
    GET_LIMIT,
    GET_PATH,
    REASON_CURSOR_MISSING,
    S4A_FRESH_C1_GET_OWNER_GO,
    bind_s4a_fresh_c1_get_runtime_authority_v1,
    load_current_productive_c1_cursor_or_reason_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_s6_fresh_c1_mark_index_evidence_join_v1 import (
    CurrentProductiveS6C1MarkIndexEvidenceError,
    collect_current_productive_s6_c1_poll_mark_index_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)

OWNER = (
    "full_core_live_path_composition_root_v1."
    "current_productive_s6_live_fresh_c1_continuous_observation_source_v1"
)
DISPOSITION_PRESENT = "PRESENT"


class LiveFreshC1GetTransportV1(Protocol):
    def get(
        self,
        *,
        endpoint: str,
        auth_required: bool,
        pretrade_decision_id: str,
    ) -> Any: ...


@dataclass
class LiveFreshC1ContinuousObservationSourceV1:
    """Poll-driven Fresh-C1 source for S6 wait loops."""

    cursor_store_root: Path
    evidence_root: Path
    run_id: str
    native_id: str
    transport: LiveFreshC1GetTransportV1
    poll_count: int = field(default=0, init=False)
    get_count: int = field(default=0, init=False)

    def _cold_lane_bootstrap_endpoint_v1(self) -> str | None:
        """Cap24-bound native id when sidestate cursor is not yet persisted (S7 bootstrap)."""
        if self.poll_count != 0 or not str(self.native_id or "").strip():
            return None
        _cursor, reason = load_current_productive_c1_cursor_or_reason_v1(
            Path(self.cursor_store_root)
        )
        if reason != REASON_CURSOR_MISSING:
            return None
        return f"{GET_PATH}?instId={self.native_id}&bar={GET_BAR}&limit={GET_LIMIT}"

    def poll(self) -> InjectedContinuousObservationV1 | None:
        ok, reasons = validate_bounded_continuous_run_owner_go_decision_v1()
        if not ok:
            raise ValueError(f"FRESH_C1_OWNER_GO_DENIED:{','.join(reasons)}")
        auth = bind_s4a_fresh_c1_get_runtime_authority_v1(
            owner_go=S4A_FRESH_C1_GET_OWNER_GO,
            cursor_store_root=self.cursor_store_root,
        )
        endpoint: str | None
        if auth.disposition == DISPOSITION_PRESENT:
            endpoint = f"{auth.path}?instId={self.native_id}&bar={auth.bar}&limit={auth.limit}"
        else:
            endpoint = self._cold_lane_bootstrap_endpoint_v1()
            if endpoint is None:
                return None
        poll_index = self.poll_count
        self.poll_count += 1
        result = self.transport.get(
            endpoint=endpoint,
            auth_required=False,
            pretrade_decision_id=f"continuous-run-{self.run_id}-poll-{poll_index}",
        )
        get_performed = bool(getattr(result, "get_performed", False))
        append_fresh_c1_get_owner_go_consumption_v1(
            evidence_root=self.evidence_root,
            run_id=self.run_id,
            poll_index=poll_index,
            endpoint=endpoint.split("?", 1)[0],
            get_performed=get_performed,
        )
        if not get_performed:
            return None
        payload = getattr(result, "payload", None)
        if not isinstance(payload, dict):
            return None
        self.get_count += 1
        candles_payload: Mapping[str, Any] = payload
        if "data" not in candles_payload:
            return None
        try:
            mark_index = collect_current_productive_s6_c1_poll_mark_index_evidence_v1(
                transport=self.transport,
                venue_native_id=str(self.native_id or ""),
                pretrade_decision_id=f"continuous-run-{self.run_id}-poll-{poll_index}",
            )
        except CurrentProductiveS6C1MarkIndexEvidenceError as exc:
            raise ValueError(f"C1_MARK_INDEX_ENRICHMENT_FAIL_CLOSED:{exc}") from exc
        return InjectedContinuousObservationV1(
            candles_payload=candles_payload,
            occupancy_payloads=productive_auth_free_flat_occupancy_payloads_v1(),
            mark_price_payload=mark_index.mark_price_payload,
            index_tickers_payload=mark_index.index_tickers_payload,
        )


def build_default_read_only_get_transport_v1() -> FullCoreProductiveReadOnlyGetTransportV1:
    return FullCoreProductiveReadOnlyGetTransportV1(max_request_count=1)


__all__ = [
    "OWNER",
    "LiveFreshC1ContinuousObservationSourceV1",
    "LiveFreshC1GetTransportV1",
    "build_default_read_only_get_transport_v1",
]
