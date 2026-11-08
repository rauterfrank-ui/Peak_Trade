"""Full-Core productive trade-order HTTP POST transport.

The urllib POST path is host-bound to eea.okx.com /api/v5/trade/order.
Standing REAL_VENUE_POST_ALLOWED remains false. The socket opens only when
one_shot_real_post=true is passed from an exact envelope-bound permit whose
authority_ref is a later actual-POST Owner-GO. This readiness slice never
passes that flag. Canary/§11.14 submit paths are not imported.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import OpenerDirector, ProxyHandler, Request, build_opener

from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    CurrentPostSafetyContextV1,
    CurrentPostSafetyVetoError,
)
from .current_productive_post_venue_quantity_v1 import (
    CurrentPostVenueQuantityError,
    inspect_current_post_venue_quantity_v1,
)
from .current_productive_post_pending_observation_v1 import (
    CurrentPostPendingObservationError,
    inspect_current_post_pending_v1,
)
from .current_productive_post_budget_admission_v1 import (
    CurrentPostBudgetAdmissionError,
    inspect_current_post_budget_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    FullCoreExternalEffectDurableConsumeError,
    OriginalPermitTransportAttemptV1,
)

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_canonical_okx_post_body_serialize_v1 import (
    serialize_canonical_okx_post_body_v1,
)
from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    build_k1_okx_venue_auth_headers_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_outcome_v1 import (
    HTTP_RESPONSE_RECEIVED,
    NOT_ATTEMPTED,
    RESPONSE_RECEIVED_PARSE_FAILED,
    SEND_INITIATED,
    TRANSPORT_FAILURE_BEFORE_RESPONSE,
    UNKNOWN_EXTERNAL_STATE,
    VENUE_RESPONSE_PARSED,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    AUTHORIZED_HOST,
    FullCoreSendCredentialHandleV1,
)

USER_AGENT = "PeakTrade-FullCore-DJ-EnvelopeBound-Productive-POST/1"
REST_BASE = f"https://{AUTHORIZED_HOST}"
TRANSPORT_CLASS_NON_NETWORKING_TEST = "FULL_CORE_NON_NETWORKING_TEST_POST_V1"
TRANSPORT_CLASS_PRODUCTIVE_HTTP = "FULL_CORE_PRODUCTIVE_HTTP_TRADE_ORDER_POST_V1"
DEFAULT_TIMEOUT_SECONDS = 20.0
CONNECT_TIMEOUT_SECONDS = 10.0


class FullCoreProductiveHttpPostError(RuntimeError):
    """Fail-closed productive HTTP POST transport violation."""


class FullCoreCurrentPostSafetyVetoError(FullCoreProductiveHttpPostError):
    """Actual current safety-reader denial, distinct from caller error text."""


class FullCoreCurrentPostQuantityVetoError(FullCoreProductiveHttpPostError):
    """Actual current native-quantity consumer denial."""


class FullCoreCurrentPostPendingVetoError(FullCoreProductiveHttpPostError):
    """Actual original observation session/pending denial."""


class FullCoreCurrentPostBudgetVetoError(FullCoreProductiveHttpPostError):
    """Actual original budget-owner/current-attempt readback denial."""


@dataclass(frozen=True)
class FullCoreTradeOrderPostResultV1:
    post_attempted: bool
    venue_live_contact: bool
    method: str
    endpoint: str
    http_status: int
    payload: Mapping[str, Any]
    transport_class: str
    unknown_outcome: bool = False
    outcome_phase: str = NOT_ATTEMPTED
    transport_error_class: str = ""


class FullCoreProductiveTradeOrderPostTransportV1(Protocol):
    """Injected Full-Core trade-order POST port."""

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1: ...


@dataclass
class FullCoreNonNetworkingTestPostTransportV1:
    """Test double. Records exactly the injected POST call. Never networks."""

    post_count: int = 0
    last_payload: Optional[dict[str, Any]] = None
    methods_used: list[str] = field(default_factory=list)
    transport_class: str = TRANSPORT_CLASS_NON_NETWORKING_TEST
    venue_live_contact: bool = False

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1:
        del permit_id, envelope_id, envelope_digest, one_shot_real_post
        if self.venue_live_contact is True:
            raise FullCoreProductiveHttpPostError("TEST_TRANSPORT_LIVE_CONTACT_FORBIDDEN")
        self.post_count += 1
        self.methods_used.append("POST")
        self.last_payload = dict(payload)
        return FullCoreTradeOrderPostResultV1(
            post_attempted=True,
            venue_live_contact=False,
            method="POST",
            endpoint=TRADE_ORDER_PATH,
            http_status=0,
            payload={"mocked": True, "code": "0"},
            transport_class=self.transport_class,
            unknown_outcome=False,
        )


class FullCoreProductiveHttpTradeOrderTransportV1:
    """Send-capable urllib POST transport. Socket stays closed unless one-shot."""

    def __init__(
        self,
        *,
        handle: Optional[FullCoreSendCredentialHandleV1] = None,
        signing_handle: Any | None = None,
        opener_factory: Callable[[], OpenerDirector] | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        post_safety_context: CurrentPostSafetyContextV1 | None = None,
        transport_attempt: OriginalPermitTransportAttemptV1 | None = None,
        post_quantity_context=None,
        post_pending_context=None,
        post_budget_context=None,
    ) -> None:
        self._handle = handle
        self._signing_handle = signing_handle
        self._opener_factory = opener_factory
        self._post_safety_context = post_safety_context
        self._transport_attempt = transport_attempt
        self._post_quantity_context = post_quantity_context
        self._post_pending_context = post_pending_context
        self._post_budget_context = post_budget_context
        self.timeout_seconds = float(timeout_seconds)
        self.post_count = 0
        self.methods_used: list[str] = []
        self.transport_class = TRANSPORT_CLASS_PRODUCTIVE_HTTP
        self.venue_live_contact = False

    def post_trade_order(
        self,
        *,
        payload: Mapping[str, Any],
        permit_id: str,
        envelope_id: str,
        envelope_digest: str,
        one_shot_real_post: bool = False,
    ) -> FullCoreTradeOrderPostResultV1:
        if self._handle is None or self._handle.bound is not True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_HANDLE_MISSING")
        if self._handle.material_loaded is True:
            raise FullCoreProductiveHttpPostError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
        if REAL_VENUE_POST_ALLOWED is True:
            raise FullCoreProductiveHttpPostError("STANDING_REAL_VENUE_POST_FORBIDDEN")
        if one_shot_real_post is not True:
            raise FullCoreProductiveHttpPostError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
        self._check_current_safety_v1(
            payload=payload,
            stage="HTTP_ORDER_IDENTITY",
            envelope_id=envelope_id,
            envelope_digest=envelope_digest,
        )
        self._check_original_transport_v1(
            permit_id=permit_id, envelope_id=envelope_id, envelope_digest=envelope_digest
        )
        return self._perform_http_post_v1(payload=payload)

    def _check_current_safety_v1(self, *, payload, stage, **identity):
        if type(self._post_safety_context) is not CurrentPostSafetyContextV1:
            raise FullCoreProductiveHttpPostError("POST_SAFETY_CONTEXT_REQUIRED")
        try:
            self._post_safety_context.inspect_wire_v1(payload=payload, stage=stage, **identity)
        except CurrentPostSafetyVetoError as exc:
            raise FullCoreCurrentPostSafetyVetoError(str(exc)) from exc

    def _check_original_transport_v1(self, **identity):
        if type(self._transport_attempt) is not OriginalPermitTransportAttemptV1:
            raise FullCoreProductiveHttpPostError("ORIGINAL_TRANSPORT_CLAIM_REQUIRED")
        try:
            self._transport_attempt.inspect_v1(**identity)
            self._transport_attempt.inspect_v1(
                envelope_id=self._post_safety_context.envelope.envelope_id,
                envelope_digest=self._post_safety_context.envelope.envelope_digest,
            )
        except FullCoreExternalEffectDurableConsumeError as exc:
            raise FullCoreProductiveHttpPostError(str(exc)) from exc
        try:
            inspect_current_post_venue_quantity_v1(
                self._post_quantity_context,
                envelope=self._post_safety_context.envelope,
                stage="HTTP_QUANTITY",
            )
        except CurrentPostVenueQuantityError as exc:
            raise FullCoreCurrentPostQuantityVetoError(str(exc)) from exc
        try:
            inspect_current_post_pending_v1(
                self._post_pending_context,
                envelope=self._post_safety_context.envelope,
                stage="HTTP_PENDING",
            )
        except CurrentPostPendingObservationError as exc:
            raise FullCoreCurrentPostPendingVetoError(str(exc)) from exc
        self._check_current_budget_v1(stage="HTTP_BUDGET")

    def _check_current_budget_v1(self, *, stage):
        try:
            inspect_current_post_budget_admission_v1(
                self._post_budget_context,
                envelope=self._post_safety_context.envelope,
                transport_attempt=self._transport_attempt,
                stage=stage,
            )
        except CurrentPostBudgetAdmissionError as exc:
            raise FullCoreCurrentPostBudgetVetoError(str(exc)) from exc

    def _perform_http_post_v1(
        self, *, payload: Mapping[str, Any]
    ) -> FullCoreTradeOrderPostResultV1:
        if REAL_VENUE_POST_ALLOWED is True:
            raise FullCoreProductiveHttpPostError("STANDING_REAL_VENUE_POST_FORBIDDEN")
        if self._signing_handle is None:
            raise FullCoreProductiveHttpPostError("SIGNING_HANDLE_MISSING")
        self._check_current_safety_v1(payload=payload, stage="BEFORE_HTTP_SIGNING")
        self._check_original_transport_v1()
        url = f"{REST_BASE}{TRADE_ORDER_PATH}"
        parsed = urlparse(url)
        if parsed.scheme != "https" or str(parsed.hostname or "") != AUTHORIZED_HOST:
            raise FullCoreProductiveHttpPostError("HOST_NOT_EEA_OKX")
        if "www.okx.com" in str(parsed.hostname or ""):
            raise FullCoreProductiveHttpPostError("WWW_OKX_FORBIDDEN")
        body = serialize_canonical_okx_post_body_v1(payload)
        headers = build_k1_okx_venue_auth_headers_v1(
            handle=self._signing_handle,
            url=url,
            method="POST",
            body=body,
        )
        headers["User-Agent"] = USER_AGENT
        req = Request(url, data=body.encode("utf-8"), method="POST", headers=headers)
        factory = self._opener_factory or (lambda: build_opener(ProxyHandler({})))
        opener = factory()
        raw = b""
        status = 0
        transport_error_class = ""
        outcome_phase = NOT_ATTEMPTED
        try:
            socket.setdefaulttimeout(CONNECT_TIMEOUT_SECONDS)
            self._check_current_safety_v1(payload=payload, stage="BEFORE_SOCKET")
            try:
                inspect_current_post_venue_quantity_v1(
                    self._post_quantity_context,
                    envelope=self._post_safety_context.envelope,
                    stage="BEFORE_SOCKET",
                )
            except CurrentPostVenueQuantityError as exc:
                raise FullCoreCurrentPostQuantityVetoError(str(exc)) from exc
            try:
                inspect_current_post_pending_v1(
                    self._post_pending_context,
                    envelope=self._post_safety_context.envelope,
                    stage="BEFORE_SOCKET",
                )
            except CurrentPostPendingObservationError as exc:
                raise FullCoreCurrentPostPendingVetoError(str(exc)) from exc
            self._check_current_budget_v1(stage="BEFORE_SOCKET")
            try:
                self._transport_attempt.mark_socket_boundary_v1()
            except FullCoreExternalEffectDurableConsumeError as exc:
                raise FullCoreProductiveHttpPostError(str(exc)) from exc
            self.post_count += 1
            self.methods_used.append("POST")
            outcome_phase = SEND_INITIATED
            with opener.open(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                status = int(getattr(resp, "status", 200))
                raw = bytes(resp.read() or b"")
                loc_host = str(urlparse(str(getattr(resp, "url", url) or url)).hostname or "")
                if loc_host and loc_host != AUTHORIZED_HOST:
                    raise FullCoreProductiveHttpPostError("REDIRECT_OFF_HOST_FORBIDDEN")
            self.venue_live_contact = True
            outcome_phase = HTTP_RESPONSE_RECEIVED
        except FullCoreProductiveHttpPostError:
            raise
        except TimeoutError:
            transport_error_class = "TimeoutError"
            return FullCoreTradeOrderPostResultV1(
                post_attempted=True,
                venue_live_contact=False,
                method="POST",
                endpoint=TRADE_ORDER_PATH,
                http_status=0,
                payload={},
                transport_class=self.transport_class,
                unknown_outcome=True,
                outcome_phase=TRANSPORT_FAILURE_BEFORE_RESPONSE,
                transport_error_class=transport_error_class,
            )
        except HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            raw = bytes(exc.read() or b"") if hasattr(exc, "read") else b""
            transport_error_class = "HTTPError"
            self.venue_live_contact = True
            outcome_phase = HTTP_RESPONSE_RECEIVED
        except (URLError, OSError, socket.timeout) as exc:
            transport_error_class = type(exc).__name__
            return FullCoreTradeOrderPostResultV1(
                post_attempted=True,
                venue_live_contact=False,
                method="POST",
                endpoint=TRADE_ORDER_PATH,
                http_status=0,
                payload={},
                transport_class=self.transport_class,
                unknown_outcome=True,
                outcome_phase=TRANSPORT_FAILURE_BEFORE_RESPONSE,
                transport_error_class=transport_error_class,
            )
        finally:
            socket.setdefaulttimeout(None)
        parsed_payload: Mapping[str, Any]
        parse_failed = False
        try:
            loaded = json.loads(raw.decode("utf-8") or "{}")
            parsed_payload = loaded if isinstance(loaded, dict) else {"raw": True}
            if outcome_phase == HTTP_RESPONSE_RECEIVED:
                outcome_phase = VENUE_RESPONSE_PARSED
        except (ValueError, UnicodeDecodeError):
            parsed_payload = {}
            parse_failed = True
            outcome_phase = RESPONSE_RECEIVED_PARSE_FAILED
        if parse_failed:
            return FullCoreTradeOrderPostResultV1(
                post_attempted=True,
                venue_live_contact=True,
                method="POST",
                endpoint=TRADE_ORDER_PATH,
                http_status=status,
                payload=parsed_payload,
                transport_class=self.transport_class,
                unknown_outcome=True,
                outcome_phase=outcome_phase,
                transport_error_class=transport_error_class or "PARSE_FAILURE",
            )
        from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
            classify_full_core_post_result_v1,
        )

        classification = classify_full_core_post_result_v1(
            result=FullCoreTradeOrderPostResultV1(
                post_attempted=True,
                venue_live_contact=True,
                method="POST",
                endpoint=TRADE_ORDER_PATH,
                http_status=status,
                payload=parsed_payload,
                transport_class=self.transport_class,
                unknown_outcome=False,
                outcome_phase=outcome_phase,
            ),
            sent_clordid=str(payload.get("clOrdId") or ""),
            submit_count=1,
        )
        typed = str(classification.get("classification") or "")
        unknown = typed == "UNKNOWN"
        if unknown:
            outcome_phase = UNKNOWN_EXTERNAL_STATE
        return FullCoreTradeOrderPostResultV1(
            post_attempted=True,
            venue_live_contact=True,
            method="POST",
            endpoint=TRADE_ORDER_PATH,
            http_status=status,
            payload=parsed_payload,
            transport_class=self.transport_class,
            unknown_outcome=unknown,
            outcome_phase=outcome_phase,
            transport_error_class=transport_error_class,
        )
