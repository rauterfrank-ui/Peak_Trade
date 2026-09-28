"""Read-only reconciliation for UNKNOWN actual-venue POST attempts.

GET-only. Uses FullCoreProductiveReadOnlyGetTransportV1. Never mutates.
Absence on any single endpoint is not promoted to CONFIRMED_NOT_ACCEPTED.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    _assert_no_secrets,
)

ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
ENDPOINT_ORDERS_HISTORY = "/api/v5/trade/orders-history"
ENDPOINT_TRADE_FILLS = "/api/v5/trade/fills"

_RECON_ALLOWLIST = frozenset(
    {
        "ordId",
        "clOrdId",
        "instId",
        "side",
        "sz",
        "fillSz",
        "accFillSz",
        "avgPx",
        "state",
        "cTime",
        "uTime",
        "sCode",
        "sMsg",
        "pos",
        "posSide",
        "code",
        "msg",
    }
)

STILL_UNKNOWN = "STILL_UNKNOWN"
CONFIRMED_ACCEPTED_AND_FILLED = "CONFIRMED_ACCEPTED_AND_FILLED"
CONFIRMED_ACCEPTED_PARTIALLY_FILLED = "CONFIRMED_ACCEPTED_PARTIALLY_FILLED"
CONFIRMED_ACCEPTED_WORKING = "CONFIRMED_ACCEPTED_WORKING"
CONFIRMED_REJECTED = "CONFIRMED_REJECTED"


@dataclass(frozen=True)
class UnknownPostAttemptReadOnlyReconciliationResultV1:
    client_order_id: str
    read_only_requests_performed: int
    order_found: str
    venue_order_id: str
    order_state: str
    reconciliation_result: str
    external_effect_confirmed: str
    correlated_fill_count: int
    exact_order_lookup_performed: bool
    surfaces_summary: tuple[str, ...]


def _rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, Mapping)]


def _sanitize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in _RECON_ALLOWLIST if k in row}


def _match_cl(rows: list[Mapping[str, Any]], cl_ord_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if str(row.get("clOrdId") or "") == cl_ord_id:
            out.append(_sanitize_row(row))
    return out


def reconcile_unknown_post_attempt_read_only_v1(
    *,
    client_order_id: str,
    instrument_id: str,
    inst_type: str,
    read_only_get_transport: FullCoreFreshPretradeGetTransportV1,
    pretrade_decision_id: str,
) -> UnknownPostAttemptReadOnlyReconciliationResultV1:
    cl = str(client_order_id or "").strip()
    inst = str(instrument_id or "").strip()
    itype = str(inst_type or "SWAP").strip()
    if not cl or not inst:
        raise ValueError("CLIENT_ORDER_ID_AND_INSTRUMENT_REQUIRED")

    surfaces: list[str] = []
    requests = 0
    matched: list[dict[str, Any]] = []
    fill_matches: list[dict[str, Any]] = []

    def _get(surface: str, path: str, query: dict[str, str]) -> list[Mapping[str, Any]]:
        nonlocal requests
        endpoint = f"{path}?{urlencode(query)}"
        res = read_only_get_transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=pretrade_decision_id,
        )
        requests += 1
        rows = _rows(res.payload)
        surfaces.append(f"{surface}:http={res.http_status}:rows={len(rows)}")
        return rows

    pending = _get(
        "orders_pending",
        ENDPOINT_ORDERS_PENDING,
        {"instType": itype, "instId": inst},
    )
    matched.extend(_match_cl(pending, cl))

    history = _get(
        "orders_history",
        ENDPOINT_ORDERS_HISTORY,
        {"instType": itype, "instId": inst, "limit": "100"},
    )
    matched.extend(_match_cl(history, cl))

    fills = _get(
        "fills",
        ENDPOINT_TRADE_FILLS,
        {"instType": itype, "instId": inst, "limit": "100"},
    )
    fill_matches = _match_cl(fills, cl)

    _get(
        "positions",
        ENDPOINT_ACCOUNT_POSITIONS,
        {"instType": itype, "instId": inst},
    )

    exact_lookup = False
    exact_rows = _get(
        "exact_order_lookup",
        READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
        {"instId": inst, "clOrdId": cl},
    )
    exact_lookup = True
    matched.extend(_match_cl(exact_rows, cl))

    _assert_no_secrets({"matched": matched, "fills": fill_matches})

    order_found = "false"
    venue_order_id = ""
    order_state = ""
    recon = STILL_UNKNOWN
    external = "false"

    if matched:
        order_found = "true"
        primary = matched[0]
        venue_order_id = str(primary.get("ordId") or "")
        order_state = str(primary.get("state") or "")
        state_lower = order_state.lower()
        if fill_matches and state_lower in {"filled", "partially_filled"}:
            recon = (
                CONFIRMED_ACCEPTED_AND_FILLED
                if state_lower == "filled"
                else CONFIRMED_ACCEPTED_PARTIALLY_FILLED
            )
            external = "true"
        elif state_lower in {"live", "partially_filled"}:
            recon = CONFIRMED_ACCEPTED_WORKING
            external = "true"
        elif str(primary.get("sCode") or "") not in {"", "0"}:
            recon = CONFIRMED_REJECTED
        else:
            recon = STILL_UNKNOWN
    elif fill_matches:
        order_found = "unknown"
        recon = STILL_UNKNOWN

    return UnknownPostAttemptReadOnlyReconciliationResultV1(
        client_order_id=cl,
        read_only_requests_performed=requests,
        order_found=order_found,
        venue_order_id=venue_order_id,
        order_state=order_state,
        reconciliation_result=recon,
        external_effect_confirmed=external,
        correlated_fill_count=len(fill_matches),
        exact_order_lookup_performed=exact_lookup,
        surfaces_summary=tuple(surfaces),
    )


__all__ = [
    "UnknownPostAttemptReadOnlyReconciliationResultV1",
    "reconcile_unknown_post_attempt_read_only_v1",
]
