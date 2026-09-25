"""Map CURRENT_PRODUCTIVE common-epoch handoff to enter-live-29p carrier v1.

Values are taken only from the common-epoch compose result and the same
Full-Core fresh-pretrade transport payloads. No fixture defaults.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PInjectedGetV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    FullCoreFreshPretradeGetTransportV1,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    CurrentProductive29PCommonEpochHandoffError,
    CurrentProductive29PCommonEpochHandoffResultV1,
    payload_from_fresh_get_transport_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.available_margin_observation_v1 import (
    account_balance_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_COMMON_EPOCH_TO_ENTER_LIVE_29P_HANDOFF_V1"


class CurrentProductiveCommonEpochToEnterLive29PHandoffError(RuntimeError):
    """Fail-closed common-epoch → enter-live-29p handoff violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_productive_transport_v1(transport: FullCoreFreshPretradeGetTransportV1) -> None:
    transport_class = str(getattr(transport, "transport_class", "") or "")
    if transport_class == TRANSPORT_CLASS_INJECTED_TEST_DOUBLE:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "INJECTED_TEST_DOUBLE_NOT_PRODUCTIVE_CURRENT"
        )
    if transport_class != TRANSPORT_CLASS_PRODUCTIVE_READ_ONLY_GET:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "TRANSPORT_CLASS_NOT_PRODUCTIVE"
        )
    if bool(getattr(transport, "venue_live_contact", False)) is not True:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "VENUE_LIVE_CONTACT_REQUIRED_FOR_PRODUCTIVE_CURRENT"
        )


def build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
    *,
    handoff: CurrentProductive29PCommonEpochHandoffResultV1,
    transport: FullCoreFreshPretradeGetTransportV1,
    expected_account_identity: str = REUSED_BINDING_ACCOUNT_SCOPE,
) -> CurrentProductiveEnterLive29PInjectedGetV1:
    """Build enter-live-29p carrier from common-epoch outputs only."""
    _require_productive_transport_v1(transport)
    epoch = str(handoff.decision_epoch or "").strip()
    if not epoch:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("DECISION_EPOCH_MISSING")
    if handoff.get_status != FreshPretradeGetStatusV1.TRUSTED_PRESENT.value:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "FRESH_PRETRADE_GET_NOT_TRUSTED_PRESENT"
        )
    if handoff.lab_trusted is not True:
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError(
            "LIVE_ACCOUNT_BOUND_NOT_TRUSTED"
        )

    payloads = getattr(transport, "payloads_by_path", None) or {}
    balance_path = account_balance_query_path_v1()
    balance_payload = payloads.get(balance_path) or payloads.get(ENDPOINT_ACCOUNT_BALANCE)
    if balance_payload is None:
        balance_payload = payload_from_fresh_get_transport_v1(
            transport,
            endpoint=balance_path,
            auth_required=True,
            decision_epoch=epoch,
        )
    if not isinstance(balance_payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("BALANCE_PAYLOAD_MISSING")

    instruments_payload = payloads.get(ENDPOINT_PUBLIC_INSTRUMENTS)
    if instruments_payload is None:
        instruments_payload = payload_from_fresh_get_transport_v1(
            transport,
            endpoint=ENDPOINT_PUBLIC_INSTRUMENTS,
            auth_required=False,
            decision_epoch=epoch,
        )
    if not isinstance(instruments_payload, Mapping):
        raise CurrentProductiveCommonEpochToEnterLive29PHandoffError("INSTRUMENTS_PAYLOAD_MISSING")

    body_sha256 = ""
    if handoff.observation is not None:
        body_sha256 = str(handoff.observation.provenance_digest or "").strip()
    if not body_sha256:
        body_sha256 = _sha256_text(_canonical_json(dict(balance_payload)))

    observed_at = epoch
    if handoff.observation is not None:
        observed_at = str(handoff.observation.observed_at_as_of or epoch)

    age_seconds = "1"
    if handoff.observation is not None:
        age_seconds = str(handoff.observation.age_seconds or "1")

    raw_acct_lv = str(handoff.adaptation.raw_token or "").strip()

    return CurrentProductiveEnterLive29PInjectedGetV1(
        payload=dict(balance_payload),
        get_performed=True,
        http_status=200,
        error_class="",
        body_sha256=body_sha256,
        observed_at=observed_at,
        age_seconds=age_seconds,
        live_account_bound_status=str(handoff.lab_status),
        raw_acct_lv=raw_acct_lv,
        expected_account_identity=str(expected_account_identity or REUSED_BINDING_ACCOUNT_SCOPE),
        fresh_pretrade_get_status=str(handoff.get_status),
        instruments_payload=dict(instruments_payload),
    )


__all__ = [
    "JOIN_SEAM_ID",
    "CurrentProductiveCommonEpochToEnterLive29PHandoffError",
    "build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1",
]
