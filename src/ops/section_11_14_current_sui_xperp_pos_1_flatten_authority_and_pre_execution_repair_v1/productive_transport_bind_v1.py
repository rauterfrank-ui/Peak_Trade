"""Productive transport bind distinct from send. Does not POST.

Bind prepares the constructive productive adapter. It does not authorize a
network session, does not call post(), and does not mutate standing Live flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_transport_adapter_v1 import (
    ConstructiveProductiveFlattenSubmitAdapterV1,
    construct_productive_flatten_submit_adapter_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenProductiveTransportBindError(RuntimeError):
    """Fail-closed productive-transport bind violation."""


@dataclass(frozen=True)
class ProductiveTransportBindV1:
    """Inspectable bind handle. send_permitted is never true in this repair."""

    kind: Literal["PRODUCTIVE_TRANSPORT_BIND_NO_SEND"]
    adapter: ConstructiveProductiveFlattenSubmitAdapterV1
    send_permitted: bool
    network_session_authorized: bool


def prepare_productive_flatten_transport_bind_v1() -> ProductiveTransportBindV1:
    """Construct and bind the productive adapter without send permission."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveTransportBindError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    adapter = construct_productive_flatten_submit_adapter_v1()
    if adapter.inner.network_session_authorized is True:
        raise FlattenProductiveTransportBindError(
            "PRODUCTIVE_TRANSPORT_MUST_DEFAULT_SESSION_UNAUTHORIZED"
        )
    bind = ProductiveTransportBindV1(
        kind=PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND,
        adapter=adapter,
        send_permitted=False,
        network_session_authorized=False,
    )
    reasons = assert_productive_transport_bind_no_send_v1(bind)
    if reasons:
        raise FlattenProductiveTransportBindError(",".join(reasons))
    return bind


def assert_productive_transport_bind_no_send_v1(
    bind: ProductiveTransportBindV1 | None,
) -> list[str]:
    """Return deny reasons. Does not post. Does not mint session authority."""
    if bind is None:
        return ["PRODUCTIVE_TRANSPORT_BIND_MISSING"]
    reasons: list[str] = []
    if bind.kind != PRODUCTIVE_TRANSPORT_BIND_KIND_NO_SEND:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_KIND_NOT_NO_SEND")
    if bind.send_permitted is not False:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_SEND_MUST_REMAIN_FALSE")
    if bind.network_session_authorized is True:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_MUST_NOT_AUTHORIZE_SESSION")
    if not isinstance(bind.adapter, ConstructiveProductiveFlattenSubmitAdapterV1):
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_ADAPTER_TYPE_MISMATCH")
        return reasons
    if bind.adapter.inner.network_session_authorized is True:
        reasons.append("PRODUCTIVE_TRANSPORT_MUST_DEFAULT_SESSION_UNAUTHORIZED")
    if bind.adapter.used is True or bind.adapter.calls:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_MUST_REMAIN_UNUSED")
    return reasons
