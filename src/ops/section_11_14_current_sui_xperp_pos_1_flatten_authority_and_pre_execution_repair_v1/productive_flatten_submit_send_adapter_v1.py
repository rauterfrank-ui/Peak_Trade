"""Send-capable flatten submit adapter. Never invokes inner.send in this WP.

Bridges harness post(endpoint, body) toward inner send(LiveCanaryHttpRequestV1)
without reaching urllib. Distinct from ConstructiveProductiveFlattenSubmitAdapterV1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_SUBMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    CLOSE_POSITION_ENDPOINT,
    FLATTEN_HTTP_ENDPOINT,
    FLATTEN_HTTP_METHOD,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.wrapper_v1 import (
    FlattenWrapperError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


class FlattenProductiveSendAdapterError(RuntimeError):
    """Fail-closed send-capable adapter violation."""


class ProductiveSendInnerV1(Protocol):
    network_session_authorized: bool

    def send(self, request: object) -> object:
        """Must never be invoked by this workpackage."""


@dataclass
class RecordingFakeProductiveSendInnerV1:
    """Offline recording inner. No urllib. send() records and refuses wire I/O."""

    network_session_authorized: bool = False
    send_calls: list[object] = field(default_factory=list)

    def send(self, request: object) -> object:
        self.send_calls.append(request)
        raise AssertionError("INNER_SEND_MUST_NOT_BE_REACHED")


def construct_productive_flatten_submit_send_adapter_v1(
    *,
    inner: ProductiveSendInnerV1 | None = None,
    session_armed: bool = False,
    send_permitted: bool = False,
    wire_send_accepted: bool = False,
    session_accepted: bool = False,
) -> "ProductiveFlattenSubmitSendAdapterV1":
    """Construct send-capable adapter. Never arms. Does not POST."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveSendAdapterError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    resolved: ProductiveSendInnerV1
    if inner is None:
        real = AuthenticatedGatedProductiveFlattenTransportV1()
        if real.network_session_authorized is True:
            raise FlattenProductiveSendAdapterError(
                "PRODUCTIVE_TRANSPORT_MUST_DEFAULT_SESSION_UNAUTHORIZED"
            )
        resolved = real
    else:
        resolved = inner
        if (
            isinstance(resolved, AuthenticatedGatedProductiveFlattenTransportV1)
            and resolved.network_session_authorized is True
        ):
            raise FlattenProductiveSendAdapterError(
                "REAL_INNER_MUST_NOT_BE_ARMED_IN_THIS_IMPLEMENTATION"
            )
    return ProductiveFlattenSubmitSendAdapterV1(
        inner=resolved,
        session_armed=session_armed,
        send_permitted=send_permitted,
        wire_send_accepted=wire_send_accepted,
        session_accepted=session_accepted,
    )


class ProductiveFlattenSubmitSendAdapterV1:
    """Harness post() shape. Prepares request material. Never calls inner.send."""

    def __init__(
        self,
        *,
        inner: ProductiveSendInnerV1,
        session_armed: bool,
        send_permitted: bool,
        wire_send_accepted: bool,
        session_accepted: bool,
    ) -> None:
        self.inner = inner
        self.implemented = True
        self.used = False
        self.calls: list[dict[str, Any]] = []
        self.prepared: dict[str, Any] | None = None
        self.session_armed = session_armed
        self.send_permitted = send_permitted
        self.wire_send_accepted = wire_send_accepted
        self.session_accepted = session_accepted
        self.inner_send_executed = False

    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        path = str(endpoint or "").split("?", 1)[0]
        if path == CLOSE_POSITION_ENDPOINT:
            raise FlattenWrapperError("CLOSE_POSITION_ENDPOINT_REJECTED")
        if path != FLATTEN_HTTP_ENDPOINT:
            raise FlattenProductiveSendAdapterError(f"UNEXPECTED_POST_ENDPOINT:{endpoint}")
        if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
            raise FlattenProductiveSendAdapterError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
        self.used = True
        self.calls.append({"endpoint": endpoint, "body": dict(body)})
        self.prepared = {
            "method": FLATTEN_HTTP_METHOD,
            "host": REUSED_BINDING_REST_HOST,
            "endpoint": path,
            "allowlisted_endpoint": ENDPOINT_SUBMIT,
            "body": dict(body),
            "inner_send_invoked": False,
        }
        if self.wire_send_accepted is not True:
            raise FlattenProductiveSendAdapterError("WIRE_SEND_AUTHORITY_NOT_ACCEPTED")
        if self.session_accepted is not True:
            raise FlattenProductiveSendAdapterError("NETWORK_SESSION_OWNER_AUTHORITY_MISSING")
        if self.session_armed is not True:
            raise FlattenProductiveSendAdapterError("SESSION_NOT_ARMED")
        if self.inner.network_session_authorized is not True:
            raise FlattenProductiveSendAdapterError("PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED")
        if self.send_permitted is not True:
            raise FlattenProductiveSendAdapterError("SEND_PERMITTED_FALSE")
        raise FlattenProductiveSendAdapterError("INNER_SEND_NOT_INVOKED_IN_THIS_IMPLEMENTATION")
