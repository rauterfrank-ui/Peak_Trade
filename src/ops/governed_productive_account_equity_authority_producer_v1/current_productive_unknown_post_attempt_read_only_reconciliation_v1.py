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
    FreshPretradeGetTransportResultV1,
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

_WORKING_STATES = frozenset({"live", "partially_filled"})
_TERMINAL_CANCELED_STATES = frozenset({"canceled", "cancelled"})

_TECHNICAL_ERROR_TRACKED_SURFACES = frozenset(
    {"orders_pending", "orders_history", "fills", "exact_order_lookup"}
)

TRUE_TOKEN = "true"
FALSE_TOKEN = "false"


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
    technical_get_error_present: str
    technical_get_error_classes: tuple[str, ...]


@dataclass(frozen=True)
class _TaggedOrderRow:
    surface: str
    row: dict[str, Any]


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


def _inst_id_consistent(row: Mapping[str, Any], *, expected_inst: str) -> bool:
    observed = str(row.get("instId") or "").strip()
    if not observed:
        return True
    return observed == expected_inst


def _technical_get_failure(res: FreshPretradeGetTransportResultV1) -> bool:
    if res.get_performed is not True:
        return True
    err = str(res.error_class or "").strip()
    return bool(err)


def _technical_error_class(res: FreshPretradeGetTransportResultV1) -> str:
    err = str(res.error_class or "").strip()
    if err:
        return err
    if res.get_performed is not True:
        return "GET_NOT_PERFORMED"
    return ""


def _state_lower(row: Mapping[str, Any]) -> str:
    return str(row.get("state") or "").strip().lower()


def _s_code(row: Mapping[str, Any]) -> str:
    return str(row.get("sCode") or "").strip()


def _ord_id(row: Mapping[str, Any]) -> str:
    return str(row.get("ordId") or "").strip()


def _collect_tagged_order_rows(
    *,
    pending: list[Mapping[str, Any]],
    history: list[Mapping[str, Any]],
    exact_rows: list[Mapping[str, Any]],
    cl: str,
    inst: str,
) -> list[_TaggedOrderRow]:
    tagged: list[_TaggedOrderRow] = []
    for surface, rows in (
        ("orders_pending", pending),
        ("orders_history", history),
        ("exact_order_lookup", exact_rows),
    ):
        for row in _match_cl(rows, cl):
            if not _inst_id_consistent(row, expected_inst=inst):
                continue
            tagged.append(_TaggedOrderRow(surface=surface, row=row))
    return tagged


def _ord_id_groups(tagged: list[_TaggedOrderRow]) -> dict[str, list[_TaggedOrderRow]]:
    groups: dict[str, list[_TaggedOrderRow]] = {}
    for item in tagged:
        key = _ord_id(item.row) or "__MISSING_ORD_ID__"
        groups.setdefault(key, []).append(item)
    return groups


def _states_for_group(items: list[_TaggedOrderRow]) -> set[str]:
    return {_state_lower(it.row) for it in items if _state_lower(it.row)}


def _has_live_canceled_conflict(states: set[str]) -> bool:
    has_live = bool(states & _WORKING_STATES)
    has_canceled = bool(states & _TERMINAL_CANCELED_STATES)
    return has_live and has_canceled


def _pick_primary_row(items: list[_TaggedOrderRow]) -> dict[str, Any]:
    for preferred in ("exact_order_lookup", "orders_pending", "orders_history"):
        for item in items:
            if item.surface == preferred:
                return item.row
    return items[0].row


def _classify_consistent_group(
    *,
    items: list[_TaggedOrderRow],
    fill_matches: list[dict[str, Any]],
) -> tuple[str, str, dict[str, Any]]:
    """Return reconciliation_result, external_effect_confirmed, primary_row."""
    states = _states_for_group(items)
    if _has_live_canceled_conflict(states):
        return STILL_UNKNOWN, FALSE_TOKEN, _pick_primary_row(items)

    primary = _pick_primary_row(items)
    state = _state_lower(primary)

    if fill_matches and state in {"filled", "partially_filled"}:
        if state == "filled":
            return CONFIRMED_ACCEPTED_AND_FILLED, TRUE_TOKEN, primary
        return CONFIRMED_ACCEPTED_PARTIALLY_FILLED, TRUE_TOKEN, primary
    if state in {"live", "partially_filled"}:
        return CONFIRMED_ACCEPTED_WORKING, TRUE_TOKEN, primary
    if _s_code(primary) not in {"", "0"}:
        return CONFIRMED_REJECTED, FALSE_TOKEN, primary
    return STILL_UNKNOWN, FALSE_TOKEN, primary


def _adjudicate_cross_surface_order_evidence_v1(
    *,
    tagged: list[_TaggedOrderRow],
    fill_matches: list[dict[str, Any]],
    technical_blocks_confirmation: bool,
) -> tuple[str, str, str, str, str, dict[str, Any] | None]:
    """Return order_found, venue_order_id, order_state, recon, external, primary_row."""

    if not tagged:
        if fill_matches:
            return "unknown", "", "", STILL_UNKNOWN, FALSE_TOKEN, None
        return FALSE_TOKEN, "", "", STILL_UNKNOWN, FALSE_TOKEN, None

    groups = _ord_id_groups(tagged)
    ord_ids = [k for k in groups if k != "__MISSING_ORD_ID__"]
    if len(set(ord_ids)) > 1:
        primary = _pick_primary_row(tagged)
        return (
            TRUE_TOKEN,
            _ord_id(primary),
            str(primary.get("state") or ""),
            STILL_UNKNOWN,
            FALSE_TOKEN,
            primary,
        )

    if len(groups) > 1 and "__MISSING_ORD_ID__" in groups and len(ord_ids) >= 1:
        primary = _pick_primary_row(tagged)
        return (
            TRUE_TOKEN,
            _ord_id(primary),
            str(primary.get("state") or ""),
            STILL_UNKNOWN,
            FALSE_TOKEN,
            primary,
        )

    if (
        len(groups) == 1
        and "__MISSING_ORD_ID__" in groups
        and len(groups["__MISSING_ORD_ID__"]) > 1
    ):
        states = _states_for_group(groups["__MISSING_ORD_ID__"])
        if _has_live_canceled_conflict(states):
            primary = _pick_primary_row(tagged)
            return (
                TRUE_TOKEN,
                "",
                str(primary.get("state") or ""),
                STILL_UNKNOWN,
                FALSE_TOKEN,
                primary,
            )

    active_key = ord_ids[0] if len(ord_ids) == 1 else next(iter(groups))
    group_items = groups[active_key]
    states = _states_for_group(group_items)
    if _has_live_canceled_conflict(states):
        primary = _pick_primary_row(group_items)
        return (
            TRUE_TOKEN,
            _ord_id(primary),
            str(primary.get("state") or ""),
            STILL_UNKNOWN,
            FALSE_TOKEN,
            primary,
        )

    if technical_blocks_confirmation:
        primary = _pick_primary_row(group_items)
        return (
            TRUE_TOKEN,
            _ord_id(primary),
            str(primary.get("state") or ""),
            STILL_UNKNOWN,
            FALSE_TOKEN,
            primary,
        )

    recon, external, primary = _classify_consistent_group(
        items=group_items,
        fill_matches=fill_matches,
    )
    return (
        TRUE_TOKEN,
        _ord_id(primary),
        str(primary.get("state") or ""),
        recon,
        external,
        primary,
    )


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
    fill_matches: list[dict[str, Any]] = []
    technical_error_classes: list[str] = []
    technical_failed_surfaces: set[str] = set()

    pending_rows: list[Mapping[str, Any]] = []
    history_rows: list[Mapping[str, Any]] = []
    exact_rows: list[Mapping[str, Any]] = []

    def _get(surface: str, path: str, query: dict[str, str]) -> FreshPretradeGetTransportResultV1:
        nonlocal requests
        endpoint = f"{path}?{urlencode(query)}"
        res = read_only_get_transport.get(
            endpoint=endpoint,
            auth_required=True,
            pretrade_decision_id=pretrade_decision_id,
        )
        requests += 1
        rows = _rows(res.payload)
        err_suffix = ""
        if _technical_get_failure(res):
            err_cls = _technical_error_class(res)
            if surface in _TECHNICAL_ERROR_TRACKED_SURFACES:
                technical_failed_surfaces.add(surface)
            if err_cls and err_cls not in technical_error_classes:
                technical_error_classes.append(err_cls)
            err_suffix = f":err={err_cls or 'GET_NOT_PERFORMED'}"
        surfaces.append(f"{surface}:http={res.http_status}:rows={len(rows)}{err_suffix}")
        if surface == "orders_pending":
            pending_rows.extend(rows)
        elif surface == "orders_history":
            history_rows.extend(rows)
        elif surface == "exact_order_lookup":
            exact_rows.extend(rows)
        return res

    _get(
        "orders_pending",
        ENDPOINT_ORDERS_PENDING,
        {"instType": itype, "instId": inst},
    )

    _get(
        "orders_history",
        ENDPOINT_ORDERS_HISTORY,
        {"instType": itype, "instId": inst, "limit": "100"},
    )

    fills_res = _get(
        "fills",
        ENDPOINT_TRADE_FILLS,
        {"instType": itype, "instId": inst, "limit": "100"},
    )
    fill_matches = _match_cl(_rows(fills_res.payload), cl)

    _get(
        "positions",
        ENDPOINT_ACCOUNT_POSITIONS,
        {"instType": itype, "instId": inst},
    )

    exact_lookup = False
    _get(
        "exact_order_lookup",
        READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
        {"instId": inst, "clOrdId": cl},
    )
    exact_lookup = True

    tagged = _collect_tagged_order_rows(
        pending=pending_rows,
        history=history_rows,
        exact_rows=exact_rows,
        cl=cl,
        inst=inst,
    )

    technical_get_error_present = TRUE_TOKEN if technical_failed_surfaces else FALSE_TOKEN
    technical_blocks_confirmation = technical_get_error_present == TRUE_TOKEN

    _assert_no_secrets({"tagged": [t.row for t in tagged], "fills": fill_matches})

    order_found, venue_order_id, order_state, recon, external, _primary = (
        _adjudicate_cross_surface_order_evidence_v1(
            tagged=tagged,
            fill_matches=fill_matches,
            technical_blocks_confirmation=technical_blocks_confirmation,
        )
    )

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
        technical_get_error_present=technical_get_error_present,
        technical_get_error_classes=tuple(sorted(technical_error_classes)),
    )


__all__ = [
    "UnknownPostAttemptReadOnlyReconciliationResultV1",
    "reconcile_unknown_post_attempt_read_only_v1",
]
