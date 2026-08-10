"""Productive Testnet execution port under ACTUAL start authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_ALLOWED_ORDER_TYPES,
    CANONICAL_INSTRUMENT_SCOPE,
    CANONICAL_RUNTIME_MODE,
    CANONICAL_VENUE,
    CONTRACT_VERSION,
    DEPRECATED_INSTRUMENT_BTC_USDT_SWAP,
    OWNER,
    SWAP_RUNTIME_FALLBACK,
    SWAP_WRITE_AUTHORIZATION,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_cancel_body_v1,
    build_venue_native_order_body_v1,
    parse_okx_order_response_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_transport_v1 import (
    StubbedTestnetTransportV1,
    TestnetTransportPortV1,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_venue_host_account_instrument_binding_v1.binding_contract_v1 import (
    assert_order_send_forbidden_v1,
)


class ActualStartPortError(RuntimeError):
    """Fail-closed productive execution port violation."""


@dataclass
class ProductiveTestnetExecutionPortV1:
    """Authorized productive submit surface (separate from terminal ALWAYS_REFUSE port)."""

    PORT_KIND: str = "TESTNET_EXECUTION_PORT_V1_ACTUAL_START_PRODUCTIVE"
    EXECUTION_MODE: str = CANONICAL_RUNTIME_MODE
    CONSTRUCTIBLE: bool = True
    REACHABLE: bool = True
    OWNER: str = OWNER
    CONTRACT_VERSION: str = CONTRACT_VERSION
    venue: str = CANONICAL_VENUE
    instrument_scope: tuple[str, ...] = CANONICAL_INSTRUMENT_SCOPE
    allowed_order_types: tuple[str, ...] = CANONICAL_ALLOWED_ORDER_TYPES
    authorized: bool = False
    stubbed: bool = True
    ephemeral_campaign_write_gate_pass: bool = False
    mutation_wire_intended: bool = False
    transport: TestnetTransportPortV1 | None = None
    submit_attempts: list[dict[str, Any]] = field(default_factory=list)

    def submit_order_v1(
        self,
        *,
        client_order_id: str,
        instrument: str,
        order_type: str,
        side: str,
        quantity: str,
        px: str,
    ) -> dict[str, Any]:
        if not self.authorized:
            raise ActualStartPortError("SUBMIT_FORBIDDEN_WITHOUT_AUTHORIZATION")
        if self.EXECUTION_MODE != "TESTNET":
            raise ActualStartPortError("LIVE_OR_NON_TESTNET_SUBMIT_FORBIDDEN")
        if SWAP_RUNTIME_FALLBACK is not False or SWAP_WRITE_AUTHORIZATION is not False:
            raise ActualStartPortError("SWAP_FALLBACK_OR_WRITE_AUTHORIZATION_FORBIDDEN")
        if instrument == DEPRECATED_INSTRUMENT_BTC_USDT_SWAP:
            raise ActualStartPortError(
                "BTC_USDT_SWAP_PATH_CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY"
            )
        if instrument not in self.instrument_scope:
            raise ActualStartPortError(f"INSTRUMENT_OUT_OF_SCOPE:{instrument}")
        if order_type not in self.allowed_order_types:
            raise ActualStartPortError(f"ORDER_TYPE_FORBIDDEN:{order_type}")
        if self.transport is None:
            raise ActualStartPortError("TRANSPORT_NOT_BOUND")
        # Binding mutation hard-block for intended real wire mutations unless
        # ephemeral write gate passed. Stubbed / boundary-only paths do not mutate.
        if self.mutation_wire_intended:
            assert_order_send_forbidden_v1(
                endpoint="/api/v5/trade/order",
                order_post=True,
                ephemeral_campaign_write_gate_pass=bool(self.ephemeral_campaign_write_gate_pass),
            )
            if not self.ephemeral_campaign_write_gate_pass:
                raise ActualStartPortError("MUTATION_REQUIRES_EPHEMERAL_WRITE_GATE_PASS")

        venue_body = build_venue_native_order_body_v1(
            client_order_id=client_order_id,
            instrument=instrument,
            order_type=order_type,
            side=side,
            quantity=quantity,
            px=px,
        )
        result = self.transport.request(
            method="POST",
            endpoint="/api/v5/trade/order",
            body=venue_body,
        )
        stubbed_result = bool(result.get("stubbed"))
        wire_sent = bool(result.get("wire_sent"))
        boundary_reached = bool(result.get("network_send_boundary_reached"))

        if stubbed_result:
            parsed = {
                "transport_ok": True,
                "http_status": 200,
                "wire_sent": False,
                "body_parsed": True,
                "exchange_code": "0",
                "s_code": "0",
                "s_msg": "stubbed",
                "client_order_id": client_order_id,
                "exchange_order_id": None,
                "exchange_accepted": False,
                "exchange_rejected": False,
                "order_acknowledged": False,
                "fill_observed": False,
                "partial_fill_observed": False,
                "classification": "STUBBED_NO_ACK",
            }
        else:
            mapped = parse_okx_order_response_v1(transport_result=result, wire_sent=wire_sent)
            parsed = mapped.to_dict()

        attempt = {
            "client_order_id": client_order_id,
            "instrument": instrument,
            "order_type": order_type,
            "side": side,
            "quantity": quantity,
            "px": px,
            "venue_native_body": venue_body,
            "stubbed": stubbed_result,
            # submitted means order attempt reached transport; NOT exchange ACK
            "submitted": (wire_sent or stubbed_result) and not stubbed_result,
            "order_attempt": True,
            "wire_sent": wire_sent,
            "network_send_boundary_reached": boundary_reached or stubbed_result or wire_sent,
            "transport_response": bool(
                result.get("http_status") is not None or stubbed_result or wire_sent
            ),
            "order_acknowledged": bool(parsed.get("order_acknowledged")),
            "exchange_accepted": bool(parsed.get("exchange_accepted")),
            "exchange_rejected": bool(parsed.get("exchange_rejected")),
            "exchange_order_id": parsed.get("exchange_order_id"),
            "fill_observed": bool(parsed.get("fill_observed")),
            "partial_fill_observed": bool(parsed.get("partial_fill_observed")),
            "response_classification": parsed.get("classification"),
            "parsed_response": parsed,
            "ephemeral_campaign_write_gate_pass": bool(self.ephemeral_campaign_write_gate_pass),
            "network_effect": (
                "STUBBED"
                if stubbed_result
                else ("TESTNET" if wire_sent else str(result.get("network_effect") or "NONE"))
            ),
            "live_order_effect": "NONE",
        }
        self.submit_attempts.append(attempt)
        return attempt

    def cancel_order_v1(
        self,
        *,
        order_id: str,
        instrument: str | None = None,
    ) -> dict[str, Any]:
        if not self.authorized:
            raise ActualStartPortError("CANCEL_FORBIDDEN_WITHOUT_AUTHORIZATION")
        if self.transport is None:
            raise ActualStartPortError("TRANSPORT_NOT_BOUND")
        inst = (
            str(instrument).strip()
            if instrument is not None and str(instrument).strip()
            else (self.instrument_scope[0] if self.instrument_scope else "")
        )
        if not inst:
            raise ActualStartPortError("CANCEL_INSTID_REQUIRED")
        if SWAP_RUNTIME_FALLBACK is not False or SWAP_WRITE_AUTHORIZATION is not False:
            raise ActualStartPortError("SWAP_FALLBACK_OR_WRITE_AUTHORIZATION_FORBIDDEN")
        if inst == DEPRECATED_INSTRUMENT_BTC_USDT_SWAP:
            raise ActualStartPortError(
                "BTC_USDT_SWAP_PATH_CLOSED_DEPRECATED_HISTORICAL_EVIDENCE_ONLY"
            )
        if inst not in self.instrument_scope:
            raise ActualStartPortError(f"INSTRUMENT_OUT_OF_SCOPE:{inst}")
        if self.mutation_wire_intended:
            assert_order_send_forbidden_v1(
                endpoint="/api/v5/trade/cancel-order",
                order_post=True,
                ephemeral_campaign_write_gate_pass=bool(self.ephemeral_campaign_write_gate_pass),
            )
            if not self.ephemeral_campaign_write_gate_pass:
                raise ActualStartPortError("MUTATION_REQUIRES_EPHEMERAL_WRITE_GATE_PASS")
        body = build_venue_native_cancel_body_v1(order_id=order_id, instrument=inst)
        result = self.transport.request(
            method="POST",
            endpoint="/api/v5/trade/cancel-order",
            body=body,
        )
        stubbed_result = bool(result.get("stubbed"))
        if stubbed_result:
            return {
                "ok": True,
                "stubbed": True,
                "order_acknowledged": True,
                "wire_sent": False,
                "order_id": order_id,
                "inst_id": inst,
                "venue_native_body": dict(body),
            }
        mapped = parse_okx_order_response_v1(
            transport_result=result, wire_sent=bool(result.get("wire_sent"))
        )
        return {
            "ok": bool(mapped.order_acknowledged or mapped.exchange_accepted),
            "stubbed": False,
            "order_acknowledged": mapped.order_acknowledged,
            "exchange_rejected": mapped.exchange_rejected,
            "wire_sent": mapped.wire_sent,
            "order_id": order_id,
            "inst_id": inst,
            "venue_native_body": dict(body),
            "classification": mapped.classification,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "PORT_KIND": self.PORT_KIND,
            "EXECUTION_MODE": self.EXECUTION_MODE,
            "authorized": self.authorized,
            "stubbed": self.stubbed,
            "venue": self.venue,
            "ephemeral_campaign_write_gate_pass": self.ephemeral_campaign_write_gate_pass,
            "mutation_wire_intended": self.mutation_wire_intended,
            "submit_attempt_count": len(self.submit_attempts),
            "OWNER": self.OWNER,
        }


def construct_productive_testnet_execution_port_v1(
    *,
    authorized: bool,
    transport: TestnetTransportPortV1 | None = None,
    stubbed: bool = True,
    ephemeral_campaign_write_gate_pass: bool = False,
    mutation_wire_intended: bool = False,
) -> ProductiveTestnetExecutionPortV1:
    if not authorized:
        raise ActualStartPortError("PORT_CONSTRUCTION_REQUIRES_AUTHORIZATION")
    bound_transport: TestnetTransportPortV1
    if transport is None:
        if not stubbed:
            raise ActualStartPortError("NON_STUBBED_TRANSPORT_REQUIRED")
        bound_transport = StubbedTestnetTransportV1()
    else:
        bound_transport = transport
    return ProductiveTestnetExecutionPortV1(
        authorized=True,
        stubbed=stubbed,
        transport=bound_transport,
        ephemeral_campaign_write_gate_pass=bool(ephemeral_campaign_write_gate_pass),
        mutation_wire_intended=bool(mutation_wire_intended),
    )
