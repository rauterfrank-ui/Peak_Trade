"""Send-capable productive transport bind. Distinct from NO_SEND bind.

send-capable means this bind may represent a future send path. It does not
mean send is currently allowed. send_permitted stays false unless a later
explicit gate sets it. No constructor I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    PRODUCTIVE_TRANSPORT_BIND_KIND_SEND_CAPABLE,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.network_session_authority_v1 import (
    verify_owner_network_session_authority_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_flatten_submit_send_adapter_v1 import (
    ProductiveFlattenSubmitSendAdapterV1,
    ProductiveSendInnerV1,
    construct_productive_flatten_submit_send_adapter_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.productive_wire_send_authority_v1 import (
    verify_owner_productive_wire_send_authority_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenProductiveSendCapableBindError(RuntimeError):
    """Fail-closed send-capable bind violation."""


@dataclass(frozen=True)
class ProductiveTransportBindSendCapableV1:
    """Inspectable send-capable bind. send_permitted is not implied by issued."""

    kind: Literal["PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE"]
    adapter: ProductiveFlattenSubmitSendAdapterV1
    send_permitted: bool
    network_session_authorized: bool
    origin_main_sha: str
    instrument_id: str
    exact_envelope_id: str
    wire_send_verdict: Mapping[str, Any]
    session_verdict: Mapping[str, Any]


def prepare_productive_transport_bind_send_capable_v1(
    *,
    origin_main_sha: str,
    instrument_id: str,
    exact_envelope_id: str,
    wire_send: Mapping[str, Any] | None,
    network_session: Mapping[str, Any] | None,
    session_armed: bool = False,
    inner: ProductiveSendInnerV1 | None = None,
) -> ProductiveTransportBindSendCapableV1:
    """Construct send-capable bind. Offline only. send_permitted remains false."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveSendCapableBindError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    wire_verdict = verify_owner_productive_wire_send_authority_v1(
        issuance=wire_send,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    session_verdict = verify_owner_network_session_authority_v1(
        issuance=network_session,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        exact_envelope_id=exact_envelope_id,
    )
    adapter = construct_productive_flatten_submit_send_adapter_v1(
        inner=inner,
        session_armed=session_armed,
        send_permitted=False,
        wire_send_accepted=wire_verdict.get("accepted") is True,
        session_accepted=session_verdict.get("accepted") is True,
    )
    if adapter.inner.network_session_authorized is True and inner is None:
        raise FlattenProductiveSendCapableBindError(
            "PRODUCTIVE_TRANSPORT_MUST_DEFAULT_SESSION_UNAUTHORIZED"
        )
    bind = ProductiveTransportBindSendCapableV1(
        kind=PRODUCTIVE_TRANSPORT_BIND_KIND_SEND_CAPABLE,
        adapter=adapter,
        send_permitted=False,
        network_session_authorized=False,
        origin_main_sha=str(origin_main_sha).strip().lower(),
        instrument_id=str(instrument_id),
        exact_envelope_id=str(exact_envelope_id),
        wire_send_verdict=wire_verdict,
        session_verdict=session_verdict,
    )
    reasons = assert_productive_transport_bind_send_capable_v1(bind)
    if reasons:
        raise FlattenProductiveSendCapableBindError(",".join(reasons))
    return bind


def assert_productive_transport_bind_send_capable_v1(
    bind: ProductiveTransportBindSendCapableV1 | None,
) -> list[str]:
    """Return deny reasons. Does not post. Does not invoke inner.send."""
    if bind is None:
        return ["PRODUCTIVE_TRANSPORT_BIND_SEND_CAPABLE_MISSING"]
    reasons: list[str] = []
    if bind.kind != PRODUCTIVE_TRANSPORT_BIND_KIND_SEND_CAPABLE:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_KIND_NOT_SEND_CAPABLE")
    if bind.send_permitted is True:
        reasons.append("SEND_PERMITTED_MUST_NOT_AUTO_PROMOTE")
    if bind.network_session_authorized is True:
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_MUST_NOT_AUTHORIZE_SESSION")
    if not isinstance(bind.adapter, ProductiveFlattenSubmitSendAdapterV1):
        reasons.append("PRODUCTIVE_TRANSPORT_BIND_ADAPTER_TYPE_MISMATCH")
        return reasons
    if bind.adapter.inner_send_executed is True:
        reasons.append("INNER_SEND_MUST_REMAIN_UNEXECUTED")
    if bind.adapter.send_permitted is True:
        reasons.append("SEND_PERMITTED_MUST_NOT_AUTO_PROMOTE")
    return reasons
