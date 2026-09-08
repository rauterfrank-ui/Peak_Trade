"""Constructive adapter of authenticated productive flatten transport.

Reuses AuthenticatedGatedProductiveFlattenTransportV1. Does not set
network_session_authorized. Does not open urllib. Does not POST.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    AuthenticatedGatedProductiveFlattenTransportV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    CLOSE_POSITION_ENDPOINT,
    FLATTEN_HTTP_ENDPOINT,
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


class FlattenProductiveTransportAdapterError(RuntimeError):
    """Fail-closed productive-transport adapter violation."""


def construct_productive_flatten_submit_adapter_v1() -> (
    "ConstructiveProductiveFlattenSubmitAdapterV1"
):
    """Prove the productive class is constructible. Never arms a network session."""
    if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
        raise FlattenProductiveTransportAdapterError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    inner = AuthenticatedGatedProductiveFlattenTransportV1()
    if inner.network_session_authorized is True:
        raise FlattenProductiveTransportAdapterError(
            "PRODUCTIVE_TRANSPORT_MUST_DEFAULT_SESSION_UNAUTHORIZED"
        )
    return ConstructiveProductiveFlattenSubmitAdapterV1(inner=inner)


class ConstructiveProductiveFlattenSubmitAdapterV1:
    """FlattenSubmitTransportV1-shaped adapter. Wire send remains unauthorized."""

    def __init__(self, *, inner: AuthenticatedGatedProductiveFlattenTransportV1) -> None:
        self.inner = inner
        self.implemented = True
        self.used = False
        self.calls: list[dict[str, Any]] = []

    def post(self, *, endpoint: str, body: Mapping[str, Any]) -> Mapping[str, Any]:
        path = str(endpoint or "").split("?", 1)[0]
        if path == CLOSE_POSITION_ENDPOINT:
            raise FlattenWrapperError("CLOSE_POSITION_ENDPOINT_REJECTED")
        if path != FLATTEN_HTTP_ENDPOINT:
            raise FlattenProductiveTransportAdapterError(f"UNEXPECTED_POST_ENDPOINT:{endpoint}")
        if LIVE_ENABLED or LIVE_ARMED or CANARY_AUTHORIZED or POST_ALLOWED:
            raise FlattenProductiveTransportAdapterError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
        if self.inner.network_session_authorized is True:
            raise FlattenProductiveTransportAdapterError(
                "ADAPTER_MUST_NOT_INHERIT_ARMED_NETWORK_SESSION"
            )
        raise FlattenProductiveTransportAdapterError("PRODUCTIVE_NETWORK_SESSION_NOT_AUTHORIZED")
