"""OKX EEA read-only reconciliation snapshot adapter (injected GET transport only).

Uses FullCoreFreshPretradeGetTransportV1 / FullCoreProductiveReadOnlyGetTransportV1.
No standalone HTTP client. No credentials. No productive wiring without Owner-GO.

PRODUCTION_PROVIDER_WIRING remains NOT_AUTHORIZED at integration boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    FullCoreFreshPretradeGetTransportV1,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET,
    EvidenceLayer,
    ExchangeEvidenceItemV1,
    FullCoreExchangeReconciliationIdentityV1,
    FullCoreExchangeReconciliationSnapshotV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)

CONTRACT_ID = "FULL_CORE_EXCHANGE_RECONCILIATION_OKX_READ_ONLY_PROVIDER_V1"
SIMULATION_OKX_TRANSPORT_INJECTED = "OKX_TRANSPORT_INJECTED"
PRODUCTION_PROVIDER_WIRING = "NOT_AUTHORIZED"

ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
ENDPOINT_ORDERS_HISTORY = "/api/v5/trade/orders-history"
ENDPOINT_TRADE_FILLS = "/api/v5/trade/fills"

DEFAULT_HISTORY_LIMIT = 100
DEFAULT_FILLS_LIMIT = 100

_OKX_RATE_LIMIT_CODES = frozenset({"50011", "50061"})


class OkxReadOnlyReconciliationProviderError(RuntimeError):
    """Fail-closed OKX read-only reconciliation adapter violation."""


@dataclass(frozen=True)
class OkxReadOnlyReconciliationQueryOptionsV1:
    inst_type: str = "SWAP"
    history_limit: int = DEFAULT_HISTORY_LIMIT
    fills_limit: int = DEFAULT_FILLS_LIMIT


def _rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _api_code(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    return str(payload.get("code") or "")


def _freshness_proven_from_get_v1(result: FreshPretradeGetTransportResultV1) -> bool:
    if not result.get_performed:
        return False
    if result.historical_reuse:
        return False
    if str(result.error_class or "").strip():
        return False
    if int(result.http_status) != 200:
        return False
    code = _api_code(result.payload)
    if code and code != "0":
        return False
    return True


def _response_status_from_get_v1(result: FreshPretradeGetTransportResultV1) -> str:
    if result.error_class:
        return str(result.error_class)
    return str(int(result.http_status))


def _collect_api_error_v1(result: FreshPretradeGetTransportResultV1, *, surface: str) -> str | None:
    if result.error_class:
        if result.error_class == "TIMEOUT":
            return f"TRANSPORT_TIMEOUT:{surface}"
        return f"TRANSPORT_FAILURE:{surface}:{result.error_class}"
    if int(result.http_status) == 429:
        return f"EXCHANGE_RATE_LIMIT:{surface}"
    code = _api_code(result.payload)
    if code and code != "0":
        msg = ""
        if isinstance(result.payload, Mapping):
            msg = str(result.payload.get("msg") or "")
        if code in _OKX_RATE_LIMIT_CODES or "rate" in msg.lower():
            return f"EXCHANGE_RATE_LIMIT:{surface}"
        return f"EXCHANGE_API_ERROR:{surface}:code={code}"
    if not result.get_performed:
        return f"TRANSPORT_AMBIGUOUS:{surface}"
    return None


def _item_from_row(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    layer: EvidenceLayer,
    source: str,
    query_scope: str,
    row: Mapping[str, Any],
    freshness_proven: bool,
    response_status: str,
    received_at: str,
) -> ExchangeEvidenceItemV1:
    return ExchangeEvidenceItemV1(
        layer=layer,
        source=source,
        account=identity.account_identity,
        environment=identity.execution_environment,
        instrument=identity.instrument_id,
        observed_at=str(row.get("uTime") or row.get("cTime") or "0"),
        received_at=received_at,
        freshness_proven=freshness_proven,
        query_scope=query_scope,
        response_status=response_status,
        raw_reference=f"{source}:{query_scope}",
        canonical_identity_digest=identity.identity_digest(),
        payload=dict(row),
    )


def _record_order_row_identity_conflicts_v1(
    *,
    rows: list[dict[str, Any]],
    cl: str,
    identity: FullCoreExchangeReconciliationIdentityV1,
    source: str,
    identity_conflicts: list[str],
) -> list[dict[str, Any]]:
    """Return rows safe to ingest; record conflicts for relevant contradictory identity."""
    matching = [row for row in rows if str(row.get("clOrdId") or "") == cl]
    if not matching:
        return []
    ord_ids = {str(r.get("ordId") or "") for r in matching if str(r.get("ordId") or "")}
    if len(ord_ids) > 1:
        identity_conflicts.append(f"CONFLICTING_ORDID:{source}")
        return []
    safe: list[dict[str, Any]] = []
    for row in matching:
        row_cl = str(row.get("clOrdId") or "")
        if row_cl != cl:
            identity_conflicts.append(f"CLORDID_IDENTITY_MISMATCH:{source}")
            continue
        row_inst = str(row.get("instId") or "").strip()
        if row_inst and row_inst != identity.instrument_id.strip():
            identity_conflicts.append(f"INSTRUMENT_IDENTITY_MISMATCH:{source}:instId={row_inst}")
            continue
        if identity.exchange_ord_id:
            row_ord = str(row.get("ordId") or "")
            if row_ord and row_ord != identity.exchange_ord_id:
                identity_conflicts.append(
                    f"CONFLICTING_ORDID:{source}:expected={identity.exchange_ord_id}:observed={row_ord}"
                )
                continue
        safe.append(row)
    return safe


def _record_fill_row_identity_conflicts_v1(
    *,
    rows: list[dict[str, Any]],
    cl: str,
    identity: FullCoreExchangeReconciliationIdentityV1,
    identity_conflicts: list[str],
) -> list[dict[str, Any]]:
    matching = [row for row in rows if str(row.get("clOrdId") or "") == cl]
    if not matching:
        return []
    ord_ids = {str(r.get("ordId") or "") for r in matching if str(r.get("ordId") or "")}
    if len(ord_ids) > 1:
        identity_conflicts.append("CONFLICTING_ORDID:fills")
        return []
    safe: list[dict[str, Any]] = []
    for row in matching:
        row_inst = str(row.get("instId") or "").strip()
        if row_inst and row_inst != identity.instrument_id.strip():
            identity_conflicts.append(f"INSTRUMENT_IDENTITY_MISMATCH:fills:instId={row_inst}")
            continue
        if identity.exchange_ord_id:
            row_ord = str(row.get("ordId") or "")
            if row_ord and row_ord != identity.exchange_ord_id:
                identity_conflicts.append(
                    f"CONFLICTING_ORDID:fills:expected={identity.exchange_ord_id}:observed={row_ord}"
                )
                continue
        safe.append(row)
    return safe


def fetch_okx_read_only_reconciliation_snapshot_v1(
    *,
    identity: FullCoreExchangeReconciliationIdentityV1,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1,
    pretrade_decision_id: str,
    options: OkxReadOnlyReconciliationQueryOptionsV1 | None = None,
    received_at: str = "injected_transport",
) -> FullCoreExchangeReconciliationSnapshotV1:
    """Issue bounded OKX read-only GET set and map into Full-Core reconciliation snapshot."""
    opts = options or OkxReadOnlyReconciliationQueryOptionsV1()
    cl = identity.clordid.strip()
    inst = identity.instrument_id.strip()
    itype = opts.inst_type.strip() or "SWAP"
    if not cl or not inst:
        raise OkxReadOnlyReconciliationProviderError("CLORDID_AND_INSTRUMENT_REQUIRED")

    items: list[ExchangeEvidenceItemV1] = []
    api_errors: list[str] = []
    identity_conflicts: list[str] = []
    incomplete_pagination = False
    history_unavailable = False
    snapshot_freshness_flags: list[bool] = []

    def _get(surface: str, path: str, query: dict[str, str]) -> FreshPretradeGetTransportResultV1:
        endpoint = f"{path}?{urlencode(query)}"
        return read_only_get_transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=pretrade_decision_id,
            get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
        )

    def _ingest_order_rows(
        *,
        result: FreshPretradeGetTransportResultV1,
        source: str,
        query_scope: str,
        rows: list[dict[str, Any]],
    ) -> None:
        fresh = _freshness_proven_from_get_v1(result)
        snapshot_freshness_flags.append(fresh)
        status = _response_status_from_get_v1(result)
        err = _collect_api_error_v1(result, surface=source)
        if err:
            api_errors.append(err)
            return
        safe_rows = _record_order_row_identity_conflicts_v1(
            rows=rows,
            cl=cl,
            identity=identity,
            source=source,
            identity_conflicts=identity_conflicts,
        )
        for row in safe_rows:
            items.append(
                _item_from_row(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_ORDER_STATE,
                    source=source,
                    query_scope=query_scope,
                    row=row,
                    freshness_proven=fresh,
                    response_status=status,
                    received_at=received_at,
                )
            )

    def _ingest_fill_rows(
        *,
        result: FreshPretradeGetTransportResultV1,
        rows: list[dict[str, Any]],
    ) -> None:
        fresh = _freshness_proven_from_get_v1(result)
        snapshot_freshness_flags.append(fresh)
        status = _response_status_from_get_v1(result)
        err = _collect_api_error_v1(result, surface="fills")
        if err:
            api_errors.append(err)
            return
        safe_rows = _record_fill_row_identity_conflicts_v1(
            rows=rows,
            cl=cl,
            identity=identity,
            identity_conflicts=identity_conflicts,
        )
        for row in safe_rows:
            items.append(
                _item_from_row(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_FILL_STATE,
                    source="fills",
                    query_scope="fills",
                    row=row,
                    freshness_proven=fresh,
                    response_status=status,
                    received_at=received_at,
                )
            )

    pending_res = _get(
        "orders_pending",
        ENDPOINT_ORDERS_PENDING,
        {"instType": itype, "instId": inst},
    )
    pending_rows = _rows(pending_res.payload)
    _ingest_order_rows(
        result=pending_res,
        source="orders-pending",
        query_scope="instId",
        rows=pending_rows,
    )

    history_res = _get(
        "orders_history",
        ENDPOINT_ORDERS_HISTORY,
        {
            "instType": itype,
            "instId": inst,
            "limit": str(opts.history_limit),
        },
    )
    history_rows = _rows(history_res.payload)
    if len(history_rows) >= opts.history_limit:
        incomplete_pagination = True
    hist_err = _collect_api_error_v1(history_res, surface="orders_history")
    if hist_err:
        history_unavailable = True
        api_errors.append(hist_err)
    else:
        _ingest_order_rows(
            result=history_res,
            source="orders-history",
            query_scope="history",
            rows=history_rows,
        )

    fills_res = _get(
        "fills",
        ENDPOINT_TRADE_FILLS,
        {"instType": itype, "instId": inst, "limit": str(opts.fills_limit)},
    )
    fills_rows = _rows(fills_res.payload)
    if len(fills_rows) >= opts.fills_limit:
        incomplete_pagination = True
    _ingest_fill_rows(result=fills_res, rows=fills_rows)

    pos_res = _get(
        "positions",
        ENDPOINT_ACCOUNT_POSITIONS,
        {"instType": itype, "instId": inst},
    )
    pos_fresh = _freshness_proven_from_get_v1(pos_res)
    snapshot_freshness_flags.append(pos_fresh)
    pos_err = _collect_api_error_v1(pos_res, surface="positions")
    if pos_err:
        api_errors.append(pos_err)
    else:
        status = _response_status_from_get_v1(pos_res)
        for row in _rows(pos_res.payload):
            if str(row.get("instId") or "") != inst:
                continue
            items.append(
                _item_from_row(
                    identity=identity,
                    layer=EvidenceLayer.EXCHANGE_POSITION_STATE,
                    source="positions",
                    query_scope="positions",
                    row=row,
                    freshness_proven=pos_fresh,
                    response_status=status,
                    received_at=received_at,
                )
            )

    exact_res = _get(
        "exact_order_lookup",
        READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
        {"instId": inst, "clOrdId": cl},
    )
    exact_rows = _rows(exact_res.payload)
    _ingest_order_rows(
        result=exact_res,
        source="exact-order-lookup",
        query_scope="clOrdId",
        rows=exact_rows,
    )

    snapshot_freshness_proven = bool(snapshot_freshness_flags) and all(snapshot_freshness_flags)

    return FullCoreExchangeReconciliationSnapshotV1(
        provider=RECONCILIATION_PROVIDER_OKX_EEA_READ_ONLY_GET,
        simulation_mode=SIMULATION_OKX_TRANSPORT_INJECTED,
        identity_digest=identity.identity_digest(),
        evidence_items=tuple(items),
        incomplete_pagination=incomplete_pagination,
        history_unavailable=history_unavailable,
        snapshot_freshness_proven=snapshot_freshness_proven,
        transport_failures=(),
        api_errors=tuple(api_errors),
        identity_conflicts=tuple(identity_conflicts),
    )


__all__ = [
    "CONTRACT_ID",
    "DEFAULT_FILLS_LIMIT",
    "DEFAULT_HISTORY_LIMIT",
    "OkxReadOnlyReconciliationProviderError",
    "OkxReadOnlyReconciliationQueryOptionsV1",
    "PRODUCTION_PROVIDER_WIRING",
    "SIMULATION_OKX_TRANSPORT_INJECTED",
    "fetch_okx_read_only_reconciliation_snapshot_v1",
]
