"""Auditable productive-flatten submit boundary.

Send is reached only after a full pre-send receipt. Fake transports cannot
masquerade. This slice never opens a network session and never claims
LIVE_FLATTEN_PROVABILITY.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    REUSED_BINDING_REST_HOST,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    LIVE_FLATTEN_PROVABILITY_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    FlattenPreSendGateReceiptV1,
    evaluate_flatten_pre_send_gate_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_productive_transport_v1 import (
    GatedProductiveFlattenTransportV1,
    LiveCanaryFlattenProductiveTransportError,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_submit_transport_v1 import (
    DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED,
    LIVE_FLATTEN_PROVABILITY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    RecordingFakeCanaryTransportV1,
)

DEFAULT_REST_BASE = "https://eea.okx.com"


class LiveCanaryFlattenGatedSubmitError(RuntimeError):
    """Fail-closed productive flatten submit-boundary violation."""


@dataclass(frozen=True)
class FlattenGatedSubmitResultV1:
    """Boundary result. send_completed is not venue proof."""

    allowed: bool
    send_attempted: bool
    send_completed: bool
    reasons: tuple[str, ...]
    receipt: FlattenPreSendGateReceiptV1
    response: LiveCanaryHttpResponseV1 | None
    live_flatten_provability: str
    productive_venue_proof: bool
    transport_class: str
    fake_transport_rejected: bool
    duplicate_blocked: bool
    retry_attempted: bool
    network_used: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "send_attempted": self.send_attempted,
            "send_completed": self.send_completed,
            "reasons": list(self.reasons),
            "live_flatten_provability": self.live_flatten_provability,
            "productive_venue_proof": self.productive_venue_proof,
            "transport_class": self.transport_class,
            "fake_transport_rejected": self.fake_transport_rejected,
            "duplicate_blocked": self.duplicate_blocked,
            "retry_attempted": self.retry_attempted,
            "network_used": self.network_used,
            "DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED": (
                DEDICATED_FLATTEN_TRANSPORT_LIVE_WIRE_ENABLED
            ),
            "LIVE_FLATTEN_PROVABILITY": LIVE_FLATTEN_PROVABILITY,
            "receipt": self.receipt.to_dict(),
        }


@dataclass
class FlattenGatedSubmitBoundaryV1:
    """Single auditable send boundary. One-shot. No retry."""

    rest_base: str = DEFAULT_REST_BASE
    rest_host: str = REUSED_BINDING_REST_HOST
    timeout_seconds: float = 10.0
    _submitted: bool = field(default=False, init=False, repr=False)

    def submit(
        self,
        *,
        gate_input: FlattenPreSendGateInputV1,
        transport: Any,
    ) -> FlattenGatedSubmitResultV1:
        receipt = evaluate_flatten_pre_send_gate_v1(gate_input)
        transport_class = str(getattr(transport, "transport_class", type(transport).__name__))
        fake = isinstance(transport, RecordingFakeCanaryTransportV1) or bool(
            getattr(transport, "is_fake_offline_flatten_transport", False)
        )
        productive = bool(getattr(transport, "is_productive_flatten_transport", False))

        def _denied(
            extra: tuple[str, ...],
            *,
            fake_rejected: bool = False,
            duplicate_blocked: bool = False,
            send_attempted: bool = False,
        ) -> FlattenGatedSubmitResultV1:
            return FlattenGatedSubmitResultV1(
                allowed=False,
                send_attempted=send_attempted,
                send_completed=False,
                reasons=tuple(receipt.reasons) + extra,
                receipt=receipt,
                response=None,
                live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
                productive_venue_proof=False,
                transport_class=transport_class,
                fake_transport_rejected=fake_rejected,
                duplicate_blocked=duplicate_blocked,
                retry_attempted=False,
                network_used=False,
            )

        if fake:
            return _denied(("FAKE_TRANSPORT_CANNOT_MASQUERADE",), fake_rejected=True)
        if not productive:
            return _denied(("NOT_PRODUCTIVE_FLATTEN_TRANSPORT",))
        if not receipt.allowed:
            return _denied(())
        if self._submitted:
            return _denied(("DUPLICATE_POST_FORBIDDEN",), duplicate_blocked=True)
        if not isinstance(receipt.request_body, dict) or not receipt.request_body:
            return _denied(("REQUEST_BODY_MISSING",))
        if str(self.rest_host or "") != REUSED_BINDING_REST_HOST:
            return _denied(("REST_HOST_BINDING_MISMATCH",))
        try:
            transport.attach_pre_send_receipt(receipt)
        except LiveCanaryFlattenProductiveTransportError as exc:
            return _denied((str(exc),))
        body_text = json.dumps(receipt.request_body, separators=(",", ":"), ensure_ascii=True)
        endpoint = ENDPOINT_SUBMIT
        url = f"{self.rest_base.rstrip('/')}{endpoint}"
        request = LiveCanaryHttpRequestV1(
            method="POST",
            url=url,
            host=self.rest_host,
            endpoint=endpoint,
            headers={"User-Agent": "PeakTrade-Section-11-13-5-FlattenWiring/1"},
            timeout_seconds=self.timeout_seconds,
            body_text=body_text,
        )
        self._submitted = True
        try:
            response = transport.send(request)
        except LiveCanaryFlattenProductiveTransportError as exc:
            return FlattenGatedSubmitResultV1(
                allowed=True,
                send_attempted=True,
                send_completed=False,
                reasons=(str(exc),),
                receipt=receipt,
                response=None,
                live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
                productive_venue_proof=False,
                transport_class=transport_class,
                fake_transport_rejected=False,
                duplicate_blocked="DUPLICATE_POST_FORBIDDEN" in str(exc),
                retry_attempted=False,
                network_used=False,
            )
        return FlattenGatedSubmitResultV1(
            allowed=True,
            send_attempted=True,
            send_completed=True,
            reasons=(),
            receipt=receipt,
            response=response,
            live_flatten_provability=LIVE_FLATTEN_PROVABILITY_STATUS,
            productive_venue_proof=False,
            transport_class=transport_class,
            fake_transport_rejected=False,
            duplicate_blocked=False,
            retry_attempted=False,
            network_used=False,
        )


def submit_productive_flatten_v1(
    *,
    gate_input: FlattenPreSendGateInputV1,
    transport: Any,
    rest_base: str = DEFAULT_REST_BASE,
    rest_host: str = REUSED_BINDING_REST_HOST,
) -> FlattenGatedSubmitResultV1:
    """One-shot helper around FlattenGatedSubmitBoundaryV1."""
    boundary = FlattenGatedSubmitBoundaryV1(rest_base=rest_base, rest_host=rest_host)
    return boundary.submit(gate_input=gate_input, transport=transport)


def default_flatten_execute_gate_input_from_runner_v1(
    *,
    live_authorized: bool,
    live_enabled: bool,
    live_armed: bool,
    flatten_live_wire_enabled: bool,
    allow_productive_wire_send: bool,
    flatten_execute_token: str | None,
    flatten_execute_purpose: str | None,
    flatten_execute_owner_go: str | None,
    flatten_execute_bound_origin_main_sha: str | None,
    positions_payload: Mapping[str, Any] | None,
    pending_orders_payload: Mapping[str, Any] | None,
    price_input: Any,
    owner_go: str,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
) -> FlattenPreSendGateInputV1 | None:
    """Build a gate input. Returns None when price_input is absent (do not invent)."""
    if price_input is None:
        return None
    return FlattenPreSendGateInputV1(
        live_authorized=bool(live_authorized),
        live_enabled=bool(live_enabled),
        live_armed=bool(live_armed),
        flatten_live_wire_enabled=bool(flatten_live_wire_enabled),
        allow_productive_wire_send=bool(allow_productive_wire_send),
        flatten_execute_token=flatten_execute_token,
        flatten_execute_purpose=flatten_execute_purpose,
        flatten_execute_owner_go=flatten_execute_owner_go,
        positions_payload=dict(positions_payload or {}),
        pending_orders_payload=pending_orders_payload,
        price_input=price_input,
        owner_go=str(owner_go or ""),
        origin_main_sha=str(origin_main_sha or ""),
        flatten_execute_bound_origin_main_sha=flatten_execute_bound_origin_main_sha,
        instrument_id=instrument_id or DEFAULT_INSTRUMENT_ID,
    )


def default_gated_productive_flatten_transport_v1() -> GatedProductiveFlattenTransportV1:
    """Runner default. Network session remains unauthorized."""
    return GatedProductiveFlattenTransportV1()
