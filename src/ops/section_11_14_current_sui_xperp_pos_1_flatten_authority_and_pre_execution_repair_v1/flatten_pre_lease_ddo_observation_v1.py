"""Host-side DDO observation adapter for §11.14 pre-lease flatten send intent.

Called from AuthenticatedGatedProductiveFlattenTransportV1.send after local
pre-wire denies and immediately before `_consume_receipt_lease`. Fail-open:
capture exceptions never change the productive send result, never consume
the lease, and never enable urllib. Does not bind a durable ledger_path.
Does not unlock the blocked `venue_execution` seam.

DDO_TRADING_AUTHORITY=NONE
DDO_EXECUTION_AUTHORITY=NONE
DDO_PERMISSION_AUTHORITY=NONE
DDO_LIVE_AUTHORITY=NONE
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping

from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT,
    current_capture_binding_v0,
    observe_producer_result_v0,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.authenticated_productive_transport_v1 import (
    construct_okx_signing_input_v1,
    signing_input_digest_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.hmac_signed_network_session_bind_v1 import (
    BIND_ATTR,
)

SEAM_CORRELATION_ID = "ddo.corr.s1114.prelease"
EVENT_TYPE = "flatten_pre_lease_send_intent_observed"


def _flag(value: Any) -> str:
    return "true" if value is True else "false"


def _header_lookup(headers: Mapping[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    return {str(key).strip().upper(): str(value) for key, value in headers.items()}


def _sha256_or_unknown(value: Any) -> str:
    token = str(value or "").strip().lower()
    if len(token) == 64 and all(ch in "0123456789abcdef" for ch in token):
        return token
    return UNKNOWN


def _text_or_unknown(value: Any) -> str:
    token = str(value or "").strip()
    return token if token else UNKNOWN


def _body_sha256(body_text: str) -> str:
    raw = str(body_text or "").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _signing_input_digest(*, request: Any) -> str:
    lookup = _header_lookup(getattr(request, "headers", None))
    timestamp = str(lookup.get("OK-ACCESS-TIMESTAMP") or "").strip()
    if not timestamp:
        return UNKNOWN
    try:
        signing_input = construct_okx_signing_input_v1(
            timestamp=timestamp,
            method=str(getattr(request, "method", "") or ""),
            url=str(getattr(request, "url", "") or ""),
            body=str(getattr(request, "body_text", "") or ""),
        )
        return signing_input_digest_v1(signing_input)
    except Exception:  # noqa: BLE001
        return UNKNOWN


def _bind_record(transport: Any) -> Mapping[str, Any]:
    record = getattr(transport, BIND_ATTR, None)
    if isinstance(record, Mapping):
        return record
    return {}


def build_flatten_pre_lease_observation_view_v1(
    *,
    transport: Any,
    request: Any,
    receipt: Any,
    capture_repository_sha: str | None = None,
) -> dict[str, Any]:
    bind = _bind_record(transport)
    approved = _sha256_or_unknown(getattr(receipt, "approved_request_identity", None))
    hmac_request = _sha256_or_unknown(bind.get("request_identity"))
    return {
        "event_type": EVENT_TYPE,
        "observation_only": True,
        "host": _text_or_unknown(getattr(request, "host", None)),
        "endpoint": _text_or_unknown(getattr(request, "endpoint", None)),
        "method": _text_or_unknown(getattr(request, "method", None)),
        "approved_request_identity": approved,
        "hmac_bind_request_identity": hmac_request,
        "hmac_signing_input_digest": _signing_input_digest(request=request),
        "hmac_bind_exact_envelope_id": _sha256_or_unknown(bind.get("exact_envelope_id")),
        "hmac_bind_origin_main_sha": _text_or_unknown(bind.get("origin_main_sha")),
        "capture_repository_sha": _text_or_unknown(capture_repository_sha),
        "network_session_authority_id": _text_or_unknown(bind.get("authority_id")),
        "network_session_authorized": _flag(
            getattr(transport, "network_session_authorized", False)
        ),
        "lease_consumed": _flag(getattr(getattr(receipt, "send_lease", None), "consumed", False)),
        "last_wire_attempted": _flag(getattr(transport, "last_wire_attempted", False)),
        "sent_flag": _flag(getattr(transport, "_sent", False)),
        "gate_digest": _sha256_or_unknown(getattr(receipt, "gate_digest", None)),
        "request_body_sha256": _body_sha256(str(getattr(request, "body_text", "") or "")),
        "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha": "UNPROVEN",
    }


def observe_flatten_pre_lease_send_intent_v1(
    *,
    transport: Any,
    request: Any,
    receipt: Any,
) -> None:
    """Fail-open observation. Never raises into the send producer."""
    binding = current_capture_binding_v0()
    if binding is None or not binding.enabled:
        return
    try:
        view = build_flatten_pre_lease_observation_view_v1(
            transport=transport,
            request=request,
            receipt=receipt,
            capture_repository_sha=binding.capture_repository_sha,
        )
        event_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        observe_producer_result_v0(
            binding,
            seam_id=SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT,
            result=view,
            event_time_utc=event_time,
            correlation_id=SEAM_CORRELATION_ID,
            repository_sha=binding.capture_repository_sha,
        )
    except Exception as exc:  # noqa: BLE001
        binding.last_error = f"{type(exc).__name__}:{exc}"
        binding.last_result = {
            "ok": False,
            "error": binding.last_error,
            "decision_unchanged": True,
            "capture_failure_changes_current_decision": False,
            "seam_id": SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT,
            "capture_failure_may_enable_send": False,
            "capture_failure_may_disable_an_otherwise_allowed_send": False,
        }
