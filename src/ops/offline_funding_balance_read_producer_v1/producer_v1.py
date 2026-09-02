"""Read-only Funding Account observation producer.

Reuses LiveCanaryHttpClientV1 and RecordingFakeCanaryTransportV1.
Does not create a second HTTP client, signer, or SecretRef owner.
Does not enable productive wire send. Does not transfer capital.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from src.ops.offline_funding_balance_read_producer_v1.constants_v1 import (
    DEFAULT_MAX_REQUEST_COUNT,
    DEFAULT_MAX_RETRIES,
    FORBIDDEN_TRANSFER_ENDPOINT,
    FORBIDDEN_WITHDRAWAL_ENDPOINT,
    FUNDING_BALANCE_ENDPOINT,
    FUNDING_BALANCE_ENDPOINT_METHOD,
    PRODUCTIVE_NETWORK_REACHABILITY,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_VENUE,
)
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    FundingAccountBalanceObservationError,
    FundingAccountBalanceObservationV1,
    parse_funding_account_balance_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
)


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def build_offline_funding_balance_read_client_v1(
    *,
    transport: LiveCanaryTransportV1,
) -> LiveCanaryHttpClientV1:
    """Build the existing canary GET client for this exact funding GET.

    Productive urllib wire send is refused here. A future Owner-GO may
    construct LiveCanaryHttpClientV1 itself; this helper stays offline.
    """
    if transport is None:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_TRANSPORT_REQUIRED")
    if isinstance(transport, UrllibLiveCanaryTransportV1):
        raise FundingAccountBalanceObservationError(
            "FUNDING_BALANCE_PRODUCTIVE_TRANSPORT_FORBIDDEN"
        )
    wire_enabled = bool(getattr(transport, "wire_send_enabled", False))
    if wire_enabled or PRODUCTIVE_NETWORK_REACHABILITY:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_PRODUCTIVE_WIRE_FORBIDDEN")
    return LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=DEFAULT_MAX_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
    )


def observe_funding_account_balances_v1(
    *,
    client: LiveCanaryHttpClientV1,
    headers: Mapping[str, str] | None = None,
    observed_at_utc: str | None = None,
    endpoint: str = FUNDING_BALANCE_ENDPOINT,
) -> FundingAccountBalanceObservationV1:
    """Execute exactly one allowlisted GET through the existing client.

    Observation terminates after the read. No transfer, deposit, conversion,
    or capital-path recommendation is emitted.
    """
    ep = str(endpoint or "").strip()
    if "?" in ep:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_QUERY_FORBIDDEN")
    if ep != FUNDING_BALANCE_ENDPOINT:
        raise FundingAccountBalanceObservationError(f"FUNDING_BALANCE_ENDPOINT_MISMATCH:{endpoint}")
    if FORBIDDEN_TRANSFER_ENDPOINT in ep or FORBIDDEN_WITHDRAWAL_ENDPOINT in ep:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_MUTATION_ENDPOINT_FORBIDDEN")
    if getattr(client.transport, "wire_send_enabled", False):
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_PRODUCTIVE_WIRE_FORBIDDEN")
    if isinstance(client.transport, UrllibLiveCanaryTransportV1):
        raise FundingAccountBalanceObservationError(
            "FUNDING_BALANCE_PRODUCTIVE_TRANSPORT_FORBIDDEN"
        )
    try:
        response = client.get(endpoint=ep, headers=headers)
    except LiveCanaryHttpError as exc:
        raise FundingAccountBalanceObservationError(str(exc)) from exc
    if response.method != FUNDING_BALANCE_ENDPOINT_METHOD:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_NON_GET_RESPONSE")
    counters = client.counters.to_dict()
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_ORDER_REQUEST_DETECTED")
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_GET_COUNT_NOT_ONE")
    used = list(client.counters.endpoints_used)
    if used != [FUNDING_BALANCE_ENDPOINT]:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_ENDPOINT_SET_MISMATCH")
    return parse_funding_account_balance_observation_v1(
        body_bytes=response.body_bytes,
        http_status=int(response.status_code),
        observed_at_utc=str(observed_at_utc or utc_now_iso_v1()),
        venue=REUSED_VENUE,
        rest_host=client.rest_host,
        endpoint=ep,
        headers=headers,
        transport_class=str(getattr(client.transport, "transport_class", "")),
        get_performed=bool(response.send_attempted),
    )


def assert_transfer_unreachable_through_reader_v1(client: LiveCanaryHttpClientV1) -> None:
    """Negative proof: transfer POST cannot be issued by this reader."""
    try:
        client.post(endpoint=FORBIDDEN_TRANSFER_ENDPOINT)
    except LiveCanaryHttpError as exc:
        text = str(exc)
        if "UNGATED_POST_FORBIDDEN" in text or "POST_ENDPOINT_NOT_ALLOWLISTED" in text:
            return
        raise FundingAccountBalanceObservationError(
            f"FUNDING_BALANCE_TRANSFER_NOT_HARD_BLOCKED:{exc}"
        ) from exc
    raise FundingAccountBalanceObservationError("FUNDING_BALANCE_TRANSFER_REACHED_WIRE")


def observation_without_secrets_v1(
    observation: FundingAccountBalanceObservationV1,
    *,
    forbidden_values: tuple[str, ...] = (),
) -> dict[str, Any]:
    payload = observation.to_dict()
    rendered = str(payload)
    lowered = rendered.lower()
    if "ok-access-" in lowered or "passphrase" in lowered:
        raise FundingAccountBalanceObservationError("FUNDING_BALANCE_SECRET_IN_EVIDENCE")
    for value in forbidden_values:
        if value and value in rendered:
            raise FundingAccountBalanceObservationError("FUNDING_BALANCE_SECRET_IN_EVIDENCE")
    return payload
