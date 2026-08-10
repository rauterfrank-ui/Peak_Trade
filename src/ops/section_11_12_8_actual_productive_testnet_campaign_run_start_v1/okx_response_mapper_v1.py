"""OKX Testnet response mapper — wire_sent is never treated as ACK."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


class OkxResponseMapperError(RuntimeError):
    """Fail-closed OKX response mapping violation."""


@dataclass(frozen=True)
class OkxOrderResponseV1:
    transport_ok: bool
    http_status: int | None
    wire_sent: bool
    body_parsed: bool
    exchange_code: str | None
    msg: str | None
    s_code: str | None
    s_msg: str | None
    client_order_id: str | None
    exchange_order_id: str | None
    exchange_accepted: bool
    exchange_rejected: bool
    order_acknowledged: bool
    fill_observed: bool
    partial_fill_observed: bool
    classification: str
    raw_keys: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "transport_ok": self.transport_ok,
            "http_status": self.http_status,
            "wire_sent": self.wire_sent,
            "body_parsed": self.body_parsed,
            "exchange_code": self.exchange_code,
            "msg": self.msg,
            "s_code": self.s_code,
            "s_msg": self.s_msg,
            "client_order_id": self.client_order_id,
            "exchange_order_id": self.exchange_order_id,
            "exchange_accepted": self.exchange_accepted,
            "exchange_rejected": self.exchange_rejected,
            "order_acknowledged": self.order_acknowledged,
            "fill_observed": self.fill_observed,
            "partial_fill_observed": self.partial_fill_observed,
            "classification": self.classification,
            "raw_keys": list(self.raw_keys),
        }


# OKX Place Order: Conditional px required for these ordType values.
_OKX_ORD_TYPES_REQUIRING_PX: frozenset[str] = frozenset(
    {
        "limit",
        "post_only",
        "fok",
        "ioc",
        "optimal_limit_ioc",
        "mmp",
        "mmp_and_post_only",
        "op_fok",
        "op_ioc",
    }
)


def build_venue_native_order_body_v1(
    *,
    client_order_id: str,
    instrument: str,
    order_type: str,
    side: str,
    quantity: str,
    td_mode: str = "cross",
    px: str | None = None,
) -> dict[str, Any]:
    """Cap 11.4 venue-native field mapping (productive; dry_run omitted).

    For LIMIT-class ordType, OKX Conditional ``px`` MUST be present in the
    final request body. Missing/blank px fails closed before wire.
    """
    ord_type = order_type.lower()
    body: dict[str, Any] = {
        "clOrdId": client_order_id,
        "instId": instrument,
        "side": side.lower(),
        "ordType": ord_type,
        "sz": quantity,
        "tdMode": td_mode,
    }
    if ord_type in _OKX_ORD_TYPES_REQUIRING_PX:
        px_text = "" if px is None else str(px).strip()
        if not px_text:
            raise OkxResponseMapperError("LIMIT_ORDER_PX_REQUIRED_BEFORE_WIRE")
        body["px"] = px_text
    return body


def build_venue_native_cancel_body_v1(
    *,
    order_id: str,
    instrument: str,
) -> dict[str, Any]:
    """OKX cancel-order venue-native body for §11.12.8 Demo XPerp path.

    OKX requires ``instId`` together with ``ordId`` (or ``clOrdId``). Historical
    residual defect omitted ``instId`` and left live Demo orders after ACK.
    """
    oid = str(order_id or "").strip()
    inst = str(instrument or "").strip()
    if not oid:
        raise OkxResponseMapperError("CANCEL_ORDER_ID_REQUIRED_BEFORE_WIRE")
    if not inst:
        raise OkxResponseMapperError("CANCEL_INSTID_REQUIRED_BEFORE_WIRE")
    return {"instId": inst, "ordId": oid}


def parse_okx_order_response_v1(
    *,
    transport_result: dict[str, Any],
    wire_sent: bool,
) -> OkxOrderResponseV1:
    http_status = transport_result.get("http_status")
    status_i = int(http_status) if http_status is not None else None
    transport_ok = bool(transport_result.get("ok")) and (status_i is None or 200 <= status_i < 300)
    raw_body = transport_result.get("response_body")
    body_obj: dict[str, Any] | None = None
    body_parsed = False
    # HTTP client may store a non-JSON wire body as a sentinel dict. That must
    # NOT count as a parsed OKX exchange body (forensic classification precision).
    raw_unparsed_sentinel = isinstance(raw_body, dict) and bool(raw_body.get("_raw_unparsed"))
    if isinstance(raw_body, dict) and not raw_unparsed_sentinel:
        body_obj = raw_body
        body_parsed = True
    elif isinstance(raw_body, (bytes, bytearray, str)):
        try:
            text = (
                raw_body.decode("utf-8") if isinstance(raw_body, (bytes, bytearray)) else raw_body
            )
            loaded = json.loads(text)
            if isinstance(loaded, dict):
                body_obj = loaded
                body_parsed = True
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise OkxResponseMapperError(f"INVALID_OKX_RESPONSE_JSON:{type(exc).__name__}") from exc

    if wire_sent and (not body_parsed or raw_unparsed_sentinel):
        # Wire without parseable OKX JSON body cannot be ACK or exchange REJECT.
        raw_keys: tuple[str, ...]
        if raw_unparsed_sentinel and isinstance(raw_body, dict):
            raw_keys = tuple(sorted(str(k) for k in raw_body.keys()))
        else:
            raw_keys = tuple(sorted(str(k) for k in transport_result.keys()))
        return OkxOrderResponseV1(
            transport_ok=transport_ok,
            http_status=status_i,
            wire_sent=True,
            body_parsed=False,
            exchange_code=None,
            msg=None,
            s_code=None,
            s_msg=None,
            client_order_id=None,
            exchange_order_id=None,
            exchange_accepted=False,
            exchange_rejected=False,
            order_acknowledged=False,
            fill_observed=False,
            partial_fill_observed=False,
            classification="TRANSPORT_RESPONSE_UNPARSED",
            raw_keys=raw_keys,
        )

    if not wire_sent:
        return OkxOrderResponseV1(
            transport_ok=transport_ok,
            http_status=status_i,
            wire_sent=False,
            body_parsed=body_parsed,
            exchange_code=None,
            msg=None,
            s_code=None,
            s_msg=None,
            client_order_id=None,
            exchange_order_id=None,
            exchange_accepted=False,
            exchange_rejected=False,
            order_acknowledged=False,
            fill_observed=False,
            partial_fill_observed=False,
            classification="WIRE_NOT_SENT",
            raw_keys=tuple(sorted(str(k) for k in transport_result.keys())),
        )

    assert body_obj is not None
    exchange_code = str(body_obj.get("code")) if body_obj.get("code") is not None else None
    # Top-level OKX msg must be retained for forensic reject diagnosis (e.g. 50124).
    top_msg = body_obj.get("msg")
    msg = str(top_msg) if top_msg is not None and str(top_msg) != "" else None
    data = body_obj.get("data")
    item: dict[str, Any] = {}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        item = data[0]
    s_code = str(item.get("sCode")) if item.get("sCode") is not None else None
    s_msg = str(item.get("sMsg")) if item.get("sMsg") is not None else None
    cl_ord = str(item.get("clOrdId") or "") or None
    ord_id = str(item.get("ordId") or "") or None
    fill_px = item.get("fillPx")
    acc_fill = item.get("accFillSz")
    fill_observed = bool(fill_px) and str(acc_fill or "") not in {"", "0"}
    partial = bool(acc_fill) and str(acc_fill) not in {"", "0"} and not fill_observed

    top_ok = exchange_code == "0"
    item_ok = s_code == "0"
    accepted = bool(wire_sent and body_parsed and top_ok and item_ok and ord_id)
    rejected = bool(
        wire_sent
        and body_parsed
        and (exchange_code not in {None, "0"} or (s_code is not None and s_code != "0"))
    )
    if accepted and rejected:
        raise OkxResponseMapperError("ACK_AND_REJECT_MUTUALLY_EXCLUSIVE")
    if accepted:
        classification = "EXCHANGE_ACCEPTED_ACK"
    elif rejected:
        classification = "EXCHANGE_REJECTED"
    else:
        classification = "EXCHANGE_RESPONSE_INCONCLUSIVE"

    return OkxOrderResponseV1(
        transport_ok=transport_ok,
        http_status=status_i,
        wire_sent=True,
        body_parsed=True,
        exchange_code=exchange_code,
        msg=msg,
        s_code=s_code,
        s_msg=s_msg,
        client_order_id=cl_ord,
        exchange_order_id=ord_id,
        exchange_accepted=accepted,
        exchange_rejected=rejected,
        order_acknowledged=accepted,
        fill_observed=fill_observed if accepted else False,
        partial_fill_observed=partial if accepted else False,
        classification=classification,
        raw_keys=tuple(sorted(str(k) for k in body_obj.keys())),
    )
