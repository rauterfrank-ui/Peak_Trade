"""OFFLINE_STUB reconciliation snapshot provider (no GET, no credentials)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    RECONCILIATION_PROVIDER_OFFLINE_STUB,
    EvidenceLayer,
    ExchangeEvidenceItemV1,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
)

CONTRACT_ID = "FULL_CORE_EXCHANGE_RECONCILIATION_OFFLINE_PROVIDER_V1"
SIMULATION_OFFLINE = "OFFLINE_SIMULATED"


@dataclass(frozen=True)
class OfflineExchangeFixtureV1:
    """Fixture buckets mirroring OKX read surfaces (stub payloads only)."""

    pending_orders: Mapping[str, Any] | None = None
    order_history: Mapping[str, Any] | None = None
    fills: Mapping[str, Any] | None = None
    positions: Mapping[str, Any] | None = None
    account_context: Mapping[str, Any] | None = None
    instrument_metadata: Mapping[str, Any] | None = None
    incomplete_pagination: bool = False
    history_unavailable: bool = False
    snapshot_freshness_proven: bool = True
    item_freshness_proven: bool = True
    transport_failures: tuple[str, ...] = ()
    api_errors: tuple[str, ...] = ()
    response_status: str = "200"


def _rows(payload: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if payload is None:
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _item(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    layer: EvidenceLayer,
    source: str,
    query_scope: str,
    row: Mapping[str, Any],
    freshness_proven: bool,
    response_status: str,
) -> ExchangeEvidenceItemV1:
    return ExchangeEvidenceItemV1(
        layer=layer,
        source=source,
        account=identity.account_identity,
        environment=identity.execution_environment,
        instrument=identity.instrument_id,
        observed_at=str(row.get("uTime") or row.get("cTime") or "0"),
        received_at="offline_fixture",
        freshness_proven=freshness_proven,
        query_scope=query_scope,
        response_status=response_status,
        raw_reference=f"{source}:{query_scope}",
        canonical_identity_digest=identity.identity_digest(),
        payload=dict(row),
    )


def build_offline_exchange_reconciliation_snapshot_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    fixture: OfflineExchangeFixtureV1,
) -> FullCoreExchangeReconciliationSnapshotV1:
    items: list[ExchangeEvidenceItemV1] = []
    cl = identity.clordid
    status = fixture.response_status

    for row in _rows(fixture.pending_orders):
        if str(row.get("clOrdId") or "") == cl:
            items.append(
                _item(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_ORDER_STATE,
                    source="orders-pending",
                    query_scope="instId",
                    row=row,
                    freshness_proven=fixture.item_freshness_proven,
                    response_status=status,
                )
            )
    for row in _rows(fixture.order_history):
        if str(row.get("clOrdId") or "") == cl:
            items.append(
                _item(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_ORDER_STATE,
                    source="orders-history",
                    query_scope="history",
                    row=row,
                    freshness_proven=fixture.item_freshness_proven,
                    response_status=status,
                )
            )
    for row in _rows(fixture.fills):
        if str(row.get("clOrdId") or "") == cl:
            items.append(
                _item(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_FILL_STATE,
                    source="fills",
                    query_scope="fills",
                    row=row,
                    freshness_proven=fixture.item_freshness_proven,
                    response_status=status,
                )
            )
    for row in _rows(fixture.positions):
        if str(row.get("instId") or "") == identity.instrument_id:
            items.append(
                _item(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_POSITION_STATE,
                    source="positions",
                    query_scope="positions",
                    row=row,
                    freshness_proven=fixture.item_freshness_proven,
                    response_status=status,
                )
            )
    if fixture.account_context:
        items.append(
            ExchangeEvidenceItemV1(
                layer=EvidenceLayer.EXCHANGE_ACCOUNT_STATE,
                source="account",
                account=identity.account_identity,
                environment=identity.execution_environment,
                instrument=identity.instrument_id,
                observed_at="0",
                received_at="offline_fixture",
                freshness_proven=fixture.item_freshness_proven,
                query_scope="account",
                response_status=status,
                raw_reference="account:config",
                canonical_identity_digest=identity.identity_digest(),
                payload=dict(fixture.account_context),
            )
        )

    return FullCoreExchangeReconciliationSnapshotV1(
        provider=RECONCILIATION_PROVIDER_OFFLINE_STUB,
        simulation_mode=SIMULATION_OFFLINE,
        identity_digest=identity.identity_digest(),
        evidence_items=tuple(items),
        incomplete_pagination=fixture.incomplete_pagination,
        history_unavailable=fixture.history_unavailable,
        snapshot_freshness_proven=fixture.snapshot_freshness_proven,
        transport_failures=tuple(fixture.transport_failures),
        api_errors=tuple(fixture.api_errors),
    )


def fetch_offline_reconciliation_snapshot_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    fixture: OfflineExchangeFixtureV1,
) -> FullCoreExchangeReconciliationSnapshotV1:
    return build_offline_exchange_reconciliation_snapshot_v1(identity=identity, fixture=fixture)


__all__ = [
    "CONTRACT_ID",
    "OfflineExchangeFixtureV1",
    "SIMULATION_OFFLINE",
    "build_offline_exchange_reconciliation_snapshot_v1",
    "fetch_offline_reconciliation_snapshot_v1",
]
