"""Execute exactly one authenticated GET /api/v5/asset/balances.

Constructs LiveCanaryHttpClientV1 itself. Does not reuse the Z2DF offline
helper, which remains recording/simulated-only. No POST, transfer, order,
or capital movement.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    FundingAccountBalanceObservationError,
    parse_funding_account_balance_observation_v1,
)
from src.ops.offline_funding_balance_read_producer_v1.producer_v1 import (
    observation_without_secrets_v1,
    utc_now_iso_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.constants_v1 import (
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_HOST,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_TRANSFER,
    FORBIDDEN_WITHDRAWAL,
    MAX_NETWORK_REQUEST_COUNT,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_REST_BASE,
    REUSED_REST_HOST,
    REUSED_SECRETREF_URI,
    REUSED_VENUE,
    THIS_SLICE,
)
from src.ops.section_11_13_5_z2dh_single_actual_read_only_funding_balance_get_v1.persist_v1 import (
    persist_z2dh_funding_balance_get_evidence_v1,
)


class Z2DHFundingBalanceGetError(RuntimeError):
    """Fail-closed Z2DH one-shot GET violation."""


def _funding_account_status_v1(
    *,
    observation_class: str,
    row_count: int,
    nonzero_ccys: tuple[str, ...],
) -> str:
    if observation_class != "SUCCESS":
        return "GET_PERFORMED_NOT_SUCCESS"
    if row_count == 0:
        return "OBSERVED_EMPTY_NOT_ZERO"
    if nonzero_ccys:
        return "OBSERVED_NONZERO_ROWS"
    return "OBSERVED_ZERO_ONLY_ROWS"


def _header_presence_v1(headers: dict[str, str]) -> dict[str, Any]:
    keys = {str(k).upper() for k in headers}
    return {
        "AUTH_KEY_HEADER_PRESENT": "OK-ACCESS-KEY" in keys,
        "AUTH_SIGN_HEADER_PRESENT": "OK-ACCESS-SIGN" in keys,
        "AUTH_TIMESTAMP_HEADER_PRESENT": "OK-ACCESS-TIMESTAMP" in keys,
        "AUTH_PASSPHRASE_HEADER_PRESENT": "OK-ACCESS-PASSPHRASE" in keys,
        "SIMULATION_HEADER_PRESENT": any("simul" in str(k).lower() for k in headers),
        "SIGNED_METHOD": "GET",
    }


def _assert_one_get_zero_writes(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise Z2DHFundingBalanceGetError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise Z2DHFundingBalanceGetError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DHFundingBalanceGetError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DHFundingBalanceGetError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise Z2DHFundingBalanceGetError("ORDER_REQUEST_DETECTED")
    if int(counters.get("ENTRY_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DHFundingBalanceGetError("ENTRY_SUBMIT_DETECTED")
    if int(counters.get("FLATTEN_SUBMIT_COUNT", 0) or 0) != 0:
        raise Z2DHFundingBalanceGetError("FLATTEN_SUBMIT_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise Z2DHFundingBalanceGetError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise Z2DHFundingBalanceGetError("NON_GET_METHOD_DETECTED")
    return counters


def execute_single_actual_funding_balance_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    """Perform exactly one allowlisted authenticated GET and persist evidence."""
    owned = str(owner_go or "").strip()
    if owned != OWNER_GO:
        raise Z2DHFundingBalanceGetError("OWNER_GO_MISMATCH")
    bound_sha = str(origin_main_sha or "").strip()
    if bound_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Z2DHFundingBalanceGetError("ORIGIN_MAIN_SHA_MISMATCH")
    if REUSED_REST_HOST != AUTHORIZED_HOST:
        raise Z2DHFundingBalanceGetError("HOST_MISMATCH")
    if "?" in ENDPOINT or ENDPOINT != "/api/v5/asset/balances":
        raise Z2DHFundingBalanceGetError("ENDPOINT_CONTRACT_DRIFT")
    if FORBIDDEN_TRANSFER in ENDPOINT or FORBIDDEN_WITHDRAWAL in ENDPOINT:
        raise Z2DHFundingBalanceGetError("MUTATION_ENDPOINT_FORBIDDEN")

    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise Z2DHFundingBalanceGetError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise Z2DHFundingBalanceGetError("PRODUCTIVE_WIRE_DISABLED")

    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    auth_headers: dict[str, str] = {}
    header_presence: dict[str, Any] = _header_presence_v1({})
    handle = None
    request_time = utc_now_iso_v1()
    http_status: int | None = None
    body_bytes = b""
    get_error: str | None = None
    send_attempted = False
    try:
        url = f"{REUSED_REST_BASE}{ENDPOINT}"
        parsed = urlparse(url)
        if parsed.path != ENDPOINT or parsed.query:
            raise Z2DHFundingBalanceGetError("SIGNED_REQUEST_TARGET_MISMATCH")
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REUSED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REUSED_CREDENTIAL_CLASS,
            )
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        header_presence = _header_presence_v1(auth_headers)
        response = client.get(endpoint=ENDPOINT, headers=auth_headers or None)
        send_attempted = True
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise Z2DHFundingBalanceGetError("NON_GET_RESPONSE")
    except LiveCanaryHttpError as exc:
        send_attempted = True
        get_error = str(exc)
    finally:
        auth_headers.clear()
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    response_time = utc_now_iso_v1()
    counters = client.counters.to_dict()
    if get_error is None:
        counters = _assert_one_get_zero_writes(client)
        wire_count = int(getattr(transport, "http_exchange_count", 0) or 0)
        if productive and wire_count != 1:
            raise Z2DHFundingBalanceGetError("NETWORK_REQUEST_COUNT_NOT_ONE")

    payload: dict[str, Any] | None = None
    parse_error: str | None = None
    if body_bytes:
        try:
            payload = parse_json_object_v1(body_bytes)
        except LiveCanaryHttpError as exc:
            parse_error = str(exc)

    observation_payload: dict[str, Any] | None = None
    observation_class = "NOT_PARSED"
    funding_account_status = "GET_PERFORMED_UNPARSED"
    if get_error is None and parse_error is None:
        try:
            observation = parse_funding_account_balance_observation_v1(
                body_bytes=body_bytes,
                http_status=int(http_status or 0),
                observed_at_utc=response_time,
                venue=REUSED_VENUE,
                rest_host=REUSED_REST_HOST,
                endpoint=ENDPOINT,
                headers={"OK-ACCESS-KEY": "<REDACTED>"}
                if header_presence.get("AUTH_KEY_HEADER_PRESENT")
                else None,
                transport_class=str(getattr(transport, "transport_class", "")),
                get_performed=True,
            )
            observation_payload = observation_without_secrets_v1(observation)
            observation_class = str(observation.observation_class)
            funding_account_status = _funding_account_status_v1(
                observation_class=observation_class,
                row_count=int(observation.row_count),
                nonzero_ccys=observation.nonzero_ccys,
            )
        except FundingAccountBalanceObservationError as exc:
            parse_error = str(exc)
            observation_class = "FAIL_CLOSED"
            funding_account_status = "GET_PERFORMED_NOT_SUCCESS"
    elif get_error is not None:
        observation_class = "NETWORK_OR_CLIENT_FAIL"
        funding_account_status = "GET_FAILED"

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pack = Path(evidence_root) / run_id
    snapshot = {
        "DOCUMENT_CLASS": "Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT",
        "AUTHORITY": "NONE",
        "THIS_ARTIFACT_IS_NOT_CANONICAL": True,
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "AUTHORIZED_ENDPOINT": AUTHORIZED_ENDPOINT,
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HOST": REUSED_REST_HOST,
        "VENUE": REUSED_VENUE,
        "QUERY_PARAMETERS": {},
        "REQUEST_TIME_UTC": request_time,
        "RESPONSE_TIME_UTC": response_time,
        "HTTP_STATUS": http_status,
        "SEND_ATTEMPTED": send_attempted,
        "GET_ERROR": get_error,
        "PARSE_ERROR": parse_error,
        "BODY_BYTES": len(body_bytes),
        "BODY_SHA256": hashlib.sha256(body_bytes).hexdigest() if body_bytes else None,
        "COUNTERS": counters,
        "AUTH_PATH": {
            "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
            "SECRETREF_URI": REUSED_SECRETREF_URI,
            "SIGNER": "build_okx_live_canary_auth_headers_v1",
            "HTTP_CLIENT": "LiveCanaryHttpClientV1",
            "TRANSPORT": type(transport).__name__,
            "HEADER_PRESENCE": header_presence,
        },
        "AUTH_HEADER_SENT": bool(header_presence.get("AUTH_KEY_HEADER_PRESENT")),
        "SECRET_VALUES_INCLUDED": False,
        "observation": observation_payload,
        "OBSERVATION_CLASS": observation_class,
        "FUNDING_ACCOUNT_STATUS": funding_account_status,
        "VENUE_CODE": str((payload or {}).get("code") or "") if payload else None,
        "VENUE_MSG": str((payload or {}).get("msg") or "")[:200] if payload else None,
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "TRANSFER_ALLOWED": False,
        "POST_ALLOWED": False,
        "ORDER_ALLOWED": False,
        "CAPITAL_MOVEMENT_ALLOWED": False,
        "PREREQUISITE_08_CLOSED": False,
        "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY": (
            CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
        ),
    }
    summary = {
        "DOCUMENT_CLASS": "Z2DH_SINGLE_ACTUAL_READ_ONLY_FUNDING_BALANCE_GET_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": owned,
        "THIS_SLICE": THIS_SLICE,
        "BOUND_ORIGIN_MAIN_SHA": bound_sha,
        "ENDPOINT": ENDPOINT,
        "METHOD": "GET",
        "HTTP_STATUS": http_status,
        "GET_REQUEST_COUNT": counters.get("GET_REQUEST_COUNT"),
        "POST_COUNT": 0,
        "WRITE_REQUEST_COUNT": counters.get("WRITE_REQUEST_COUNT"),
        "TRANSFER_REQUEST_COUNT": counters.get("TRANSFER_REQUEST_COUNT"),
        "ORDER_REQUEST_COUNT": counters.get("ORDER_REQUEST_COUNT"),
        "OBSERVATION_CLASS": observation_class,
        "FUNDING_ACCOUNT_STATUS": funding_account_status,
        "ROW_COUNT": None if observation_payload is None else observation_payload.get("row_count"),
        "OBSERVED_CCYS": (
            None if observation_payload is None else observation_payload.get("observed_ccys")
        ),
        "NONZERO_CCYS": (
            None if observation_payload is None else observation_payload.get("nonzero_ccys")
        ),
        "USDC_ROW_STATUS": (
            None if observation_payload is None else observation_payload.get("usdc_row_status")
        ),
        "USD_ROW_STATUS": (
            None if observation_payload is None else observation_payload.get("usd_row_status")
        ),
        "USDC_NUMERIC_STATUS": (
            None if observation_payload is None else observation_payload.get("usdc_numeric_status")
        ),
        "USD_NUMERIC_STATUS": (
            None if observation_payload is None else observation_payload.get("usd_numeric_status")
        ),
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "SECRET_VALUES_INCLUDED": False,
        "PREREQUISITE_08_CLOSED": False,
    }
    verified = persist_z2dh_funding_balance_get_evidence_v1(
        pack=pack,
        origin_main_sha=bound_sha,
        snapshot=snapshot,
        summary=summary,
    )
    if get_error:
        raise Z2DHFundingBalanceGetError(f"FUNDING_BALANCE_GET_FAILED:{get_error}")
    if parse_error:
        raise Z2DHFundingBalanceGetError(f"FUNDING_BALANCE_OBSERVATION_FAIL_CLOSED:{parse_error}")
    return {
        "EVIDENCE_PACK": str(pack),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "summary": summary,
        "observation": observation_payload,
    }
