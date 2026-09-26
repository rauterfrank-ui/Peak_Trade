"""Restart/recovery lifecycle for OKX EEA private account state runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.okx_eea_private_account_state_runtime_v1.consumer_adapters_v1 import (
    balance_equity_observation_adapter_v1,
    operator_readmodel_from_private_state_v1,
    wp_b_to_fresh_pretrade_observation_hint_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.durable_store_v1 import (
    append_private_state_v1,
    default_private_store_paths_v1,
    load_all_private_state_v1,
    load_known_fill_trade_ids_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.event_pipeline_v1 import (
    PrivateEventSequenceStateV1,
    process_private_ws_events_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.reconciliation_v1 import (
    reconcile_rest_baseline_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.rest_baseline_v1 import (
    RestGetJson,
    collect_rest_baseline_v1,
)
from src.ops.okx_eea_private_account_state_runtime_v1.ws_transport_v1 import PrivateWsTransportV1


@dataclass
class OkxEeaPrivateAccountStateRuntimeV1:
    store_root: Path
    rest_fetch_json: RestGetJson
    ws_transport: Optional[PrivateWsTransportV1] = None
    event_state: PrivateEventSequenceStateV1 = field(default_factory=PrivateEventSequenceStateV1)
    lifecycle_events: list[dict[str, Any]] = field(default_factory=list)
    trusted_current: bool = False

    def restore_durable_state_v1(self) -> list[Mapping[str, Any]]:
        paths = default_private_store_paths_v1(self.store_root)
        restored = load_all_private_state_v1(paths)
        self.lifecycle_events.append({"phase": "durable_restore", "count": len(restored)})
        self.trusted_current = False
        return restored

    def run_rest_baseline_v1(self, *, captured_at: str, recovery: bool = False) -> dict[str, Any]:
        snap = collect_rest_baseline_v1(
            self.rest_fetch_json, captured_at=captured_at, recovery=recovery
        )
        self.lifecycle_events.append(
            {
                "phase": "rest_baseline",
                "endpoints": list(snap.endpoints_called),
                "recovery": recovery,
            }
        )
        return {"host": snap.host, "snapshot": snap}

    def reconcile_after_restore_or_ws_v1(
        self,
        *,
        reconciliation_id: str,
        rest_snapshot: Any,
        ws_positions: list[Mapping[str, str]] | None = None,
        ws_orders: list[Mapping[str, str]] | None = None,
        restored_from_durable: bool = False,
    ) -> dict[str, Any]:
        result = reconcile_rest_baseline_v1(
            reconciliation_id=reconciliation_id,
            rest_baseline=rest_snapshot,
            ws_positions=ws_positions,
            ws_orders=ws_orders,
            restored_from_durable=restored_from_durable,
        )
        self.trusted_current = result.trusted
        paths = default_private_store_paths_v1(self.store_root)
        append_private_state_v1(paths, result.snapshot.to_dict())
        self.lifecycle_events.append(
            {
                "phase": "reconciliation",
                "trusted": result.trusted,
                "quality": result.snapshot.quality.state,
            }
        )
        return result.snapshot.to_dict()

    def persist_normalized_facts_v1(self, facts: list[Mapping[str, Any]]) -> int:
        paths = default_private_store_paths_v1(self.store_root)
        known_fills = load_known_fill_trade_ids_v1(paths)
        written = 0
        for fact in facts:
            if fact.get("fact_kind") == "FillFactV1":
                tid = str(fact.get("tradeId") or "")
                if tid and tid in known_fills:
                    continue
            append_private_state_v1(paths, fact)
            written += 1
        return written

    def run_observation_cycle_v1(self) -> dict[str, Any]:
        if self.ws_transport is None:
            return {"events": [], "reconciliation_required": False}
        msgs = self.ws_transport.poll_messages()
        envelopes, self.event_state, recon = process_private_ws_events_v1(
            events=msgs, state=self.event_state
        )
        if recon:
            self.trusted_current = False
        return {
            "events": [e.payload for e in envelopes],
            "reconciliation_required": recon,
            "envelope_count": len(envelopes),
        }

    def publish_consumer_surfaces_v1(self, *, balance: Any | None = None) -> dict[str, Any]:
        restored = load_all_private_state_v1(default_private_store_paths_v1(self.store_root))
        return {
            "trusted_current": self.trusted_current,
            "fresh_pretrade_hint": wp_b_to_fresh_pretrade_observation_hint_v1(
                endpoint_path="/api/v5/account/leverage-info"
            ),
            "balance_equity_observation": balance_equity_observation_adapter_v1(balance),
            "operator_readmodel": operator_readmodel_from_private_state_v1(restored),
        }

    def restart_sequence_v1(self, *, captured_at: str) -> dict[str, Any]:
        restored = self.restore_durable_state_v1()
        baseline = self.run_rest_baseline_v1(captured_at=captured_at, recovery=True)
        recon = self.reconcile_after_restore_or_ws_v1(
            reconciliation_id="restart_v1",
            rest_snapshot=baseline["snapshot"],
            restored_from_durable=bool(restored),
        )
        if self.ws_transport is not None:
            self.ws_transport.connect_login_subscribe()
        return {
            "restored_count": len(restored),
            "reconciliation": recon,
            "trusted_current": self.trusted_current,
        }
