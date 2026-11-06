"""Authenticated GET-only REST baseline/recovery orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    BASELINE_REST_GET_ALLOWLIST,
    BASELINE_REST_RECOVERY_ALLOWLIST,
    EEA_REST_HOST,
    FRESH_PRETRADE_ONLY_GET_PATHS,
)
from src.ops.okx_eea_private_account_state_runtime_v1.state_contracts_v1 import (
    AccountConfigStateV1,
    BalanceSnapshotV1,
    FillFactV1,
    OrderSnapshotV1,
    PositionStateV1,
    PrivateStateProvenanceV1,
    PrivateStateQualityV1,
    body_digest,
)
from src.ops.okx_eea_private_account_state_runtime_v1.constants_v1 import (
    CREDENTIAL_CLASS,
    QUALITY_CURRENT,
)


class PrivateRestBaselineError(RuntimeError):
    pass


RestGetJson = Callable[[str, Mapping[str, str]], Mapping[str, Any]]


@dataclass
class RestBaselineSnapshotV1:
    host: str
    endpoints_called: tuple[str, ...] = field(default_factory=tuple)
    account_config: AccountConfigStateV1 | None = None
    balance: BalanceSnapshotV1 | None = None
    positions: tuple[PositionStateV1, ...] = field(default_factory=tuple)
    orders: tuple[OrderSnapshotV1, ...] = field(default_factory=tuple)
    fills: tuple[FillFactV1, ...] = field(default_factory=tuple)


def assert_get_path_allowlisted_v1(path: str, *, recovery: bool = False) -> None:
    allow = BASELINE_REST_RECOVERY_ALLOWLIST if recovery else BASELINE_REST_GET_ALLOWLIST
    if path not in allow:
        raise PrivateRestBaselineError(f"REST_GET_NOT_ALLOWLISTED:{path}")


def assert_no_rest_post_v1(method: str) -> None:
    if method.upper() != "GET":
        raise PrivateRestBaselineError("REST_POST_FORBIDDEN_IN_WP_B")


def _provenance(
    path: str, payload: Mapping[str, Any], captured_at: str
) -> PrivateStateProvenanceV1:
    return PrivateStateProvenanceV1(
        observation_source_class="OKX_EEA_PRIVATE_OBSERVATION_READ_V1",
        transport="rest",
        endpoint_or_channel=path,
        venue_host_family=EEA_REST_HOST,
        instrument=None,
        venue_timestamp_ms=None,
        captured_at=captured_at,
        session_identity="rest_baseline_v1",
        body_digest=body_digest(payload),
        credential_class=CREDENTIAL_CLASS,
    )


def _quality_current() -> PrivateStateQualityV1:
    return PrivateStateQualityV1(state=QUALITY_CURRENT, reconciliation_required=False)


def _rows(payload: Mapping[str, Any], kind: str, *, singleton: bool = False) -> list:
    if not isinstance(payload, Mapping):
        raise PrivateRestBaselineError(f"{kind}_MALFORMED")
    data = payload.get("data")
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise PrivateRestBaselineError(f"{kind}_MALFORMED")
    if singleton and len(data) != 1:
        raise PrivateRestBaselineError(f"{kind}_MALFORMED")
    return data


def _number(value: Any, kind: str, *, positive: bool = False) -> str:
    try:
        if value is None or isinstance(value, bool) or not str(value).strip():
            raise ValueError()
        numeric = Decimal(str(value))
        if not numeric.is_finite() or (positive and numeric <= 0):
            raise ValueError()
    except (ValueError, InvalidOperation) as exc:
        raise PrivateRestBaselineError(f"{kind}_NUMERIC_UNPROVEN") from exc
    return str(value)


def normalize_account_config_v1(
    path: str, payload: Mapping[str, Any], *, captured_at: str
) -> AccountConfigStateV1:
    row = _rows(payload, "ACCOUNT_CONFIG", singleton=True)[0]
    if not row.get("acctLv") or not row.get("posMode"):
        raise PrivateRestBaselineError("ACCOUNT_CONFIG_MALFORMED")
    return AccountConfigStateV1(
        acct_lv=str(row.get("acctLv")) if row.get("acctLv") is not None else None,
        pos_mode=str(row.get("posMode")) if row.get("posMode") is not None else None,
        quality=_quality_current(),
        provenance=_provenance(path, payload, captured_at),
    )


def normalize_balance_v1(
    path: str, payload: Mapping[str, Any], *, captured_at: str
) -> BalanceSnapshotV1:
    row = _rows(payload, "BALANCE", singleton=True)[0]
    details = row.get("details")
    ccy = None
    avail = None
    if isinstance(details, list) and details:
        d0 = details[0]
        if isinstance(d0, dict):
            ccy = str(d0.get("ccy")) if d0.get("ccy") is not None else None
            avail = str(d0.get("availEq")) if d0.get("availEq") is not None else None
    if not ccy:
        raise PrivateRestBaselineError("BALANCE_CURRENCY_UNPROVEN")
    _number(row.get("totalEq"), "BALANCE_TOTAL_EQ")
    _number(avail, "BALANCE_AVAIL_EQ")
    return BalanceSnapshotV1(
        total_eq=str(row.get("totalEq")) if row.get("totalEq") is not None else None,
        avail_eq=avail,
        ccy=ccy,
        quality=_quality_current(),
        provenance=_provenance(path, payload, captured_at),
    )


def normalize_positions_v1(
    path: str, payload: Mapping[str, Any], *, captured_at: str
) -> tuple[PositionStateV1, ...]:
    data = _rows(payload, "POSITIONS")
    out: list[PositionStateV1] = []
    for row in data:
        inst = str(row.get("instId") or "")
        if not inst:
            raise PrivateRestBaselineError("POSITION_UNKNOWN_INSTRUMENT")
        out.append(
            PositionStateV1(
                inst_id=inst,
                pos_side=str(row.get("posSide")) if row.get("posSide") is not None else None,
                pos=_number(row.get("pos"), "POSITION_QUANTITY"),
                avg_px=str(row.get("avgPx")) if row.get("avgPx") is not None else None,
                quality=_quality_current(),
                provenance=_provenance(path, payload, captured_at),
            )
        )
    return tuple(out)


def _map_order_state(raw: str) -> str:
    mapping = {
        "live": "accepted/live",
        "partially_filled": "partial",
        "filled": "filled",
        "canceled": "canceled",
        "cancelled": "canceled",
        "mmp_canceled": "canceled",
    }
    return mapping.get(raw, raw or "unknown")


def normalize_orders_v1(
    path: str, payload: Mapping[str, Any], *, captured_at: str
) -> tuple[OrderSnapshotV1, ...]:
    data = _rows(payload, "ORDERS")
    out: list[OrderSnapshotV1] = []
    for row in data:
        inst = str(row.get("instId") or "")
        if not inst:
            raise PrivateRestBaselineError("ORDER_UNKNOWN_INSTRUMENT")
        if not (row.get("ordId") or row.get("clOrdId")):
            raise PrivateRestBaselineError("ORDER_IDENTITY_INCOMPLETE")
        if _map_order_state(str(row.get("state") or "")) not in {
            "accepted/live",
            "partial",
            "filled",
            "canceled",
            "rejected",
        }:
            raise PrivateRestBaselineError("ORDER_STATE_UNPROVEN")
        out.append(
            OrderSnapshotV1(
                inst_id=inst,
                cl_ord_id=str(row.get("clOrdId")) if row.get("clOrdId") is not None else None,
                ord_id=str(row.get("ordId")) if row.get("ordId") is not None else None,
                state=_map_order_state(str(row.get("state") or "")),
                quality=_quality_current(),
                provenance=_provenance(path, payload, captured_at),
            )
        )
    return tuple(out)


def normalize_fills_v1(
    path: str, payload: Mapping[str, Any], *, captured_at: str
) -> tuple[FillFactV1, ...]:
    data = _rows(payload, "FILLS")
    out: list[FillFactV1] = []
    for row in data:
        inst = str(row.get("instId") or "")
        trade_id = str(row.get("tradeId") or "")
        if not inst or not trade_id:
            raise PrivateRestBaselineError("FILL_IDENTITY_INCOMPLETE")
        out.append(
            FillFactV1(
                inst_id=inst,
                trade_id=trade_id,
                ord_id=str(row.get("ordId")) if row.get("ordId") is not None else None,
                cl_ord_id=str(row.get("clOrdId")) if row.get("clOrdId") is not None else None,
                fill_sz=_number(row.get("fillSz"), "FILL_SIZE", positive=True),
                fill_px=_number(row.get("fillPx"), "FILL_PRICE", positive=True),
                quality=_quality_current(),
                provenance=_provenance(path, payload, captured_at),
            )
        )
    return tuple(out)


def collect_rest_baseline_v1(
    fetch_json: RestGetJson,
    *,
    captured_at: str,
    inst_id: str = "ETH-USDT-SWAP",
    recovery: bool = False,
) -> RestBaselineSnapshotV1:
    called: list[str] = []
    snap = RestBaselineSnapshotV1(host=EEA_REST_HOST)

    def _get(path: str, params: Mapping[str, str] | None = None) -> Mapping[str, Any]:
        assert_get_path_allowlisted_v1(path, recovery=recovery)
        assert_no_rest_post_v1("GET")
        called.append(path)
        payload = fetch_json(path, dict(params or {}))
        if not isinstance(payload, Mapping) or str(payload.get("code")) not in ("0", "0.0"):
            raise PrivateRestBaselineError("REST_AUTH_OR_VENUE_FAILURE")
        _rows(payload, "REST_DATA")
        return payload

    cfg = _get("/api/v5/account/config")
    snap.account_config = normalize_account_config_v1(
        "/api/v5/account/config", cfg, captured_at=captured_at
    )

    bal = _get("/api/v5/account/balance")
    snap.balance = normalize_balance_v1("/api/v5/account/balance", bal, captured_at=captured_at)

    pos = _get("/api/v5/account/positions", {"instType": "SWAP"})
    snap.positions = normalize_positions_v1(
        "/api/v5/account/positions", pos, captured_at=captured_at
    )

    pending = _get("/api/v5/trade/orders-pending", {"instType": "SWAP", "instId": inst_id})
    snap.orders = normalize_orders_v1(
        "/api/v5/trade/orders-pending", pending, captured_at=captured_at
    )

    hist = _get("/api/v5/trade/orders-history", {"instType": "SWAP", "instId": inst_id})
    snap.orders = snap.orders + normalize_orders_v1(
        "/api/v5/trade/orders-history", hist, captured_at=captured_at
    )

    fills = _get("/api/v5/trade/fills", {"instType": "SWAP", "instId": inst_id})
    snap.fills = normalize_fills_v1("/api/v5/trade/fills", fills, captured_at=captured_at)

    if not recovery:
        for path in FRESH_PRETRADE_ONLY_GET_PATHS:
            if path in ("/api/v5/account/config",):
                continue
            params: dict[str, str] = {"instId": inst_id, "tdMode": "cross"}
            if path == "/api/v5/account/leverage-info":
                params["mgnMode"] = "cross"
            _get(path, params)

    snap.endpoints_called = tuple(called)
    return snap


def cached_state_may_not_substitute_fresh_pretrade_get_v1(path: str) -> bool:
    return path in FRESH_PRETRADE_ONLY_GET_PATHS
