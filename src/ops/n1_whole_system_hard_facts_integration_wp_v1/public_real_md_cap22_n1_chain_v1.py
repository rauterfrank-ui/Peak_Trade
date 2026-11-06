"""RW-E1 / RW-E3 / RW-PUB-G1 closure: public observation → Cap22 → POLICY_A → N=1 handoff."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    FORBIDDEN_PRODUCTIVE_PUBLIC_REST_HOSTS,
    PRODUCTIVE_ECONOMIC_MD_REST_HOST,
)
from src.ops.economic_md_input_producer_v1.public_md_source_v1 import EconomicMdPublicSourceV1
from src.ops.hard_facts_system_closure_v1.productive_mf_n5_handoff_join_v1 import (
    HardFactsCap22MembershipHandoffRequestV1,
    HardFactsMfN5HandoffResultV1,
    execute_hard_facts_cap22_to_mf_n5_handoff_v1,
)
from src.ops.hard_facts_system_closure_v1.productive_real_b05_cap22_v1 import (
    build_cap22_feature_production_snapshot_from_economic_md_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_runtime_economic_md_adapter_v1 import (
    PublicRuntimeEconomicMdPublicSourceV1,
)
from src.ops.economic_md_input_producer_v1.constants_v1 import PUBLIC_HTTP_HOST
from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.runtime_orchestrator_v1 import (
    PublicMarketDataRuntimeV1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.ws_transport_v1 import PublicWsTransportV1


@dataclass(frozen=True)
class PublicRealMdChainProofV1:
    ok: bool
    public_rest_host: str
    productive_economic_md_host: str
    ws_normalization_applied: bool
    event_sequence_persisted: bool
    cap22_real_b05: bool
    policy_a_n1_handoff: bool
    failure_code: str = ""


def assert_productive_public_host_invariants_v1() -> None:
    if PRODUCTIVE_ECONOMIC_MD_REST_HOST in FORBIDDEN_PRODUCTIVE_PUBLIC_REST_HOSTS:
        raise RuntimeError("PRODUCTIVE_HOST_FORBIDDEN")
    if "www." in PRODUCTIVE_ECONOMIC_MD_REST_HOST:
        raise RuntimeError("WWW_PRODUCTIVE_FORBIDDEN")


def run_public_runtime_ws_normalization_cycle_v1(
    *,
    store_root: Path,
    venue_native_id: str,
    canonical_instrument_id: str,
    ws_messages: list[Mapping[str, Any]],
    rest_fetch_json: Callable[[str, Mapping[str, str]], Mapping[str, Any]],
    captured_at: str = "2026-09-26T00:00:00Z",
) -> PublicMarketDataRuntimeV1:
    """Single observation cycle with durable sequence + canonical fact persistence."""

    msg_iter = iter(ws_messages)

    def _source():
        return iter(list(msg_iter))

    class _Connector:
        def connect(self, ws_base_url: str) -> None:
            _ = ws_base_url

        def subscribe(self, args: list) -> None:
            _ = args

        def disconnect(self) -> None:
            return None

    transport = PublicWsTransportV1.from_ratified_binding(
        connector=_Connector(),
        message_source=_source,
        venue_native_id=venue_native_id,
    )
    transport.connect_and_subscribe()
    runtime = PublicMarketDataRuntimeV1(
        store_root=store_root,
        venue_native_id=venue_native_id,
        canonical_instrument_id=canonical_instrument_id,
        ws_transport=transport,
        rest_fetch_json=rest_fetch_json,
        event_state=EventSequenceStateV1(),
    )
    runtime.bootstrap(captured_at=captured_at)
    runtime.load_durable_event_state()
    runtime.run_observation_cycle(captured_at=captured_at, persist_normalized_facts=True)
    return runtime


def prove_rw_e1_real_economic_md_from_public_source_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    public_md_source: EconomicMdPublicSourceV1,
    collection_started_at_unix: Optional[float] = None,
    collection_completed_at_unix: Optional[float] = None,
) -> bool:
    assert_productive_public_host_invariants_v1()
    started = collection_started_at_unix or time.time()
    completed = collection_completed_at_unix or (started + 1.0)
    feature = build_cap22_feature_production_snapshot_from_economic_md_v1(
        universe_snapshot=universe_snapshot,
        public_md_source=public_md_source,
        collection_started_at_unix=started,
        collection_completed_at_unix=completed,
    )
    return feature.instruments is not None and len(feature.instruments) > 0


def prove_rw_e3_cap22_policy_a_n1_handoff_v1(
    *,
    productive_ranking_snapshot: Mapping[str, Any],
    membership_store_root: Path,
    topology_state_root_base: Path,
    lane_assignment_writer: Any = None,
) -> HardFactsMfN5HandoffResultV1:
    assert_productive_public_host_invariants_v1()
    return execute_hard_facts_cap22_to_mf_n5_handoff_v1(
        HardFactsCap22MembershipHandoffRequestV1(
            ranking_snapshot=dict(productive_ranking_snapshot),
            membership_store_root=membership_store_root,
            topology_state_root_base=topology_state_root_base,
        ),
        lane_assignment_writer=lane_assignment_writer,
    )


def prove_public_real_md_to_cap22_n1_chain_v1(
    *,
    universe_snapshot: Mapping[str, Any],
    public_md_source: EconomicMdPublicSourceV1,
    productive_ranking_snapshot: Mapping[str, Any],
    membership_store_root: Path,
    topology_state_root_base: Path,
    lane_assignment_writer: Any = None,
    ws_normalization_applied: bool = False,
    event_sequence_persisted: bool = False,
    collection_started_at_unix: Optional[float] = None,
    collection_completed_at_unix: Optional[float] = None,
) -> tuple[PublicRealMdChainProofV1, HardFactsMfN5HandoffResultV1 | None]:
    try:
        e1 = prove_rw_e1_real_economic_md_from_public_source_v1(
            universe_snapshot=universe_snapshot,
            public_md_source=public_md_source,
            collection_started_at_unix=collection_started_at_unix,
            collection_completed_at_unix=collection_completed_at_unix,
        )
        handoff = prove_rw_e3_cap22_policy_a_n1_handoff_v1(
            productive_ranking_snapshot=productive_ranking_snapshot,
            membership_store_root=membership_store_root,
            topology_state_root_base=topology_state_root_base,
            lane_assignment_writer=lane_assignment_writer,
        )
        ok = e1 and handoff.membership is not None
        return (
            PublicRealMdChainProofV1(
                ok=ok,
                public_rest_host=str(PUBLIC_HTTP_HOST),
                productive_economic_md_host=PRODUCTIVE_ECONOMIC_MD_REST_HOST,
                ws_normalization_applied=ws_normalization_applied,
                event_sequence_persisted=event_sequence_persisted,
                cap22_real_b05=e1,
                policy_a_n1_handoff=ok,
            ),
            handoff,
        )
    except Exception as exc:
        return (
            PublicRealMdChainProofV1(
                ok=False,
                public_rest_host=str(PUBLIC_HTTP_HOST),
                productive_economic_md_host=PRODUCTIVE_ECONOMIC_MD_REST_HOST,
                ws_normalization_applied=ws_normalization_applied,
                event_sequence_persisted=event_sequence_persisted,
                cap22_real_b05=False,
                policy_a_n1_handoff=False,
                failure_code=str(exc),
            ),
            None,
        )


def economic_md_source_from_public_runtime_store_v1(
    store_root: Path,
) -> PublicRuntimeEconomicMdPublicSourceV1:
    return PublicRuntimeEconomicMdPublicSourceV1(store_root=store_root)
