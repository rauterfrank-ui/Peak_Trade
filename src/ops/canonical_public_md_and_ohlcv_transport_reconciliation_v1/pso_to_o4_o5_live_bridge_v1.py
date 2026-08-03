"""Productive PSO/public-MD → O4 bar producer → O5 durable read-model bridge.

Reuses CanonicalPublicMdBarProducerV1 and O5 projectors exclusively.
No parallel bar authority, no exchange candle fetch, no timestamp fabrication.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    INTERVAL_PT1H,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.durable_read_model_store_v1 import (
    commit_durable_read_model_v1,
    load_durable_read_model_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.read_model_v1 import (
    project_o4_envelopes_to_canonical_dashboard_read_model_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.normalized_market_data_v1 import (
    NormalizedPublicMarketDataV1,
)


@dataclass
class PsoToO4O5LiveBridgeV1:
    """In-process bridge owned by the productive MD consumer (PSO wallclock)."""

    session_id: str
    repository_sha: str
    config_digest: str
    state_root: Path
    selection_bundle_id: str = "o7-live-ohlcv-bundle"
    interval: str = INTERVAL_PT1H
    disconnected: bool = False
    is_stale: bool = False
    producer: CanonicalPublicMdBarProducerV1 = field(init=False)
    last_ingest_result: Optional[dict[str, Any]] = field(default=None, init=False)
    last_read_model: Optional[dict[str, Any]] = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.state_root = Path(self.state_root)
        self.producer = CanonicalPublicMdBarProducerV1(
            session_id=self.session_id,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            interval=self.interval,
        )
        # Reload derived chrome after dashboard restart; bar authority stays in this process.
        self.last_read_model = load_durable_read_model_v1(self.state_root)

    def set_connection_flags(self, *, disconnected: bool = False, is_stale: bool = False) -> None:
        self.disconnected = bool(disconnected)
        self.is_stale = bool(is_stale)

    def ingest_normalized_event(
        self,
        data: NormalizedPublicMarketDataV1,
        *,
        poll_attempt: Optional[int] = None,
        runtime_cycle_index: Optional[int] = None,
        projection_time_unix: Optional[float] = None,
    ) -> dict[str, Any]:
        ingest = self.producer.ingest_normalized_event(
            data,
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
        )
        self.last_ingest_result = ingest

        # Finalize prior bars when event time reaches/exceeds bar_close_time.
        from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
            BAR_STATE_IN_PROGRESS,
        )
        from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
            BarStateContractErrorV1,
        )

        for env in list(self.producer.list_envelopes()):
            if str(env.get("finalization_state") or "") != BAR_STATE_IN_PROGRESS:
                continue
            close_t = float(env["bar_close_time"])
            if float(data.event_ts_unix) >= close_t:
                try:
                    self.producer.finalize_bar(
                        canonical_instrument_id=str(env["canonical_instrument_id"]),
                        bar_open_time=float(env["bar_open_time"]),
                    )
                except (BarStateContractErrorV1, ValueError):
                    # Duplicate finalization / race — fail closed without advancing twice.
                    pass

        proj_t = float(time.time() if projection_time_unix is None else projection_time_unix)
        read_model = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
            self.producer.list_envelopes(),
            selection_bundle_id=self.selection_bundle_id,
            projection_time_unix=proj_t,
            disconnected=self.disconnected,
            is_stale=self.is_stale,
        )
        # Stamp source→ingestion provenance from the latest accepted event when present.
        read_model["market_event_time_unix"] = float(data.event_ts_unix)
        read_model["ingestion_time_unix"] = float(data.receive_ts_unix)
        read_model["bar_projection_time_unix"] = proj_t
        committed = commit_durable_read_model_v1(
            self.state_root,
            read_model,
            commit_time_unix=proj_t,
        )
        self.last_read_model = committed
        return {
            "ingest": ingest,
            "read_model": committed,
            "timestamp_chain": {
                "market_event_time": float(data.event_ts_unix),
                "ingestion_time": float(data.receive_ts_unix),
                "bar_projection_time": proj_t,
                "read_model_commit_time": float(committed["read_model_commit_time_unix"]),
                "http_response_observed_time": None,
                "http_response_observed_time_supported": False,
                "notes": [
                    "HTTP_OBSERVATION_STAMPED_BY_DASHBOARD_HOST_ON_POLL",
                    "NO_TIMESTAMP_FABRICATION",
                ],
            },
            "advance": bool(ingest.get("advance")),
            "accepted": bool(ingest.get("accepted")),
            "classification": ingest.get("classification"),
        }

    def mark_disconnected_and_commit(self, *, projection_time_unix: Optional[float] = None) -> dict:
        self.set_connection_flags(disconnected=True, is_stale=False)
        proj_t = float(time.time() if projection_time_unix is None else projection_time_unix)
        envelopes = self.producer.list_envelopes()
        read_model = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
            envelopes,
            selection_bundle_id=self.selection_bundle_id,
            projection_time_unix=proj_t,
            disconnected=True,
            is_stale=False,
        )
        committed = commit_durable_read_model_v1(
            self.state_root, read_model, commit_time_unix=proj_t
        )
        self.last_read_model = committed
        return committed

    def mark_stale_and_commit(self, *, projection_time_unix: Optional[float] = None) -> dict:
        self.set_connection_flags(disconnected=False, is_stale=True)
        proj_t = float(time.time() if projection_time_unix is None else projection_time_unix)
        envelopes = self.producer.list_envelopes()
        read_model = project_o4_envelopes_to_canonical_dashboard_read_model_v1(
            envelopes,
            selection_bundle_id=self.selection_bundle_id,
            projection_time_unix=proj_t,
            disconnected=False,
            is_stale=True,
        )
        committed = commit_durable_read_model_v1(
            self.state_root, read_model, commit_time_unix=proj_t
        )
        self.last_read_model = committed
        return committed
