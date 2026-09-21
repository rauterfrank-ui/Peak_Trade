"""Productive funding balance GET via FullCoreProductiveReadOnlyGetTransportV1."""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    FUNDING_BALANCE_ENDPOINT,
    REUSED_REST_HOST,
    REUSED_VENUE,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    FundingAccountBalanceObservationV1,
    parse_funding_account_balance_observation_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import utc_now_iso_v1
from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    NE_TF_001_ENDPOINT_PATH,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.constants_v1 import (
    FUNDING_GET_ENDPOINT,
    PRODUCTIVE_TRANSPORT_CLASS,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.errors_v1 import (
    TreasuryProductiveReadOnlyVenueObservationError,
)


def _payload_to_body_bytes_v1(payload: Any) -> bytes:
    if payload is None:
        return b""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def observe_funding_balance_via_productive_transport_v1(
    *,
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    pretrade_decision_id: str,
    observed_at_utc: str | None = None,
) -> tuple[FundingAccountBalanceObservationV1, FreshPretradeGetTransportResultV1]:
    if transport is None:
        raise TreasuryProductiveReadOnlyVenueObservationError("TRANSPORT_REQUIRED")
    if str(getattr(transport, "transport_class", "")) != PRODUCTIVE_TRANSPORT_CLASS:
        raise TreasuryProductiveReadOnlyVenueObservationError("TRANSPORT_CLASS_MISMATCH")
    result = transport.get(
        endpoint=FUNDING_GET_ENDPOINT,
        auth_required=True,
        pretrade_decision_id=str(pretrade_decision_id),
    )
    if str(result.endpoint or "").split("?", 1)[0] != FUNDING_BALANCE_ENDPOINT:
        raise TreasuryProductiveReadOnlyVenueObservationError("FUNDING_ENDPOINT_DRIFT")
    if str(result.method or "").upper() != "GET":
        raise TreasuryProductiveReadOnlyVenueObservationError("FUNDING_NON_GET")
    body = _payload_to_body_bytes_v1(result.payload)
    observation = parse_funding_account_balance_observation_v1(
        body_bytes=body,
        http_status=int(result.http_status),
        observed_at_utc=str(observed_at_utc or utc_now_iso_v1()),
        venue=REUSED_VENUE,
        rest_host=REUSED_REST_HOST,
        endpoint=FUNDING_BALANCE_ENDPOINT,
        headers={},
        transport_class=str(result.transport_class or PRODUCTIVE_TRANSPORT_CLASS),
        get_performed=bool(result.get_performed),
    )
    return observation, result


def resolve_account_identity_uid_from_config_get_v1(
    *,
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    pretrade_decision_id: str,
) -> str:
    result = transport.get(
        endpoint=NE_TF_001_ENDPOINT_PATH,
        auth_required=True,
        pretrade_decision_id=str(pretrade_decision_id),
    )
    if not result.get_performed:
        raise TreasuryProductiveReadOnlyVenueObservationError("ACCOUNT_CONFIG_GET_NOT_PERFORMED")
    payload = result.payload
    if not isinstance(payload, Mapping):
        raise TreasuryProductiveReadOnlyVenueObservationError("ACCOUNT_CONFIG_PAYLOAD_INVALID")
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], Mapping):
        raise TreasuryProductiveReadOnlyVenueObservationError("ACCOUNT_CONFIG_UID_MISSING")
    uid = str(data[0].get("uid") or "").strip()
    if not uid:
        raise TreasuryProductiveReadOnlyVenueObservationError("ACCOUNT_CONFIG_UID_EMPTY")
    return uid
