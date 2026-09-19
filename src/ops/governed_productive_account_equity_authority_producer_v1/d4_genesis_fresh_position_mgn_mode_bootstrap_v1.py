"""Genesis D4 tdMode resolution from one fresh GET /api/v5/account/positions.

Reuses the existing canary HTTP client, signer, SecretRef, and the
canonical positions query grammar. Binds bound_td_mode only from a
unique fresh mgnMode on the currently bound single-selected future.
Does not mint from default cross, history, fixtures, env, credential,
account-config ctIsoMode, leverage-info, or max-size. Does not POST.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
    TD_MODE_RESOLUTION_OWNER_GO,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.account_positions_query_grammar_v1 import (
    POSITION_STATE_ENDPOINT,
    build_account_positions_query_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    USER_AGENT_CANARY,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpClientV1,
    LiveCanaryHttpError,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)


def _fail_closed_credential_unavailable_v1(*_a, **_k):
    raise RuntimeError("CREDENTIAL_HANDLE_FAIL_CLOSED")


AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
MAX_NETWORK_REQUEST_COUNT = 1
DEFAULT_MAX_RETRIES = 0
DEFAULT_TIMEOUT_SECONDS = 10.0
ALLOWED_MGN_MODES: frozenset[str] = frozenset({"cross", "isolated"})
TD_MODE_SOURCE = "FRESH_AUTHENTICATED_POSITION_MGN_MODE"
TD_MODE_DERIVATION = "OKX_FUTURES_SWAP_MGN_MODE_TO_TD_MODE_IDENTITY_MAPPING"
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/config",
    "/api/v5/account/balance",
    "/api/v5/account/subtypes",
    "/api/v5/account/bills",
    "/api/v5/account/bills-archive",
    "/api/v5/asset/balances",
    "/api/v5/account/positions-history",
    "/api/v5/account/leverage-info",
    "/api/v5/account/max-size",
    "/api/v5/asset/transfer",
    "/api/v5/trade/order",
)


class D4GenesisFreshPositionMgnModeBootstrapError(ValueError):
    """Fail-closed genesis positions mgnMode bootstrap violation."""


@dataclass(frozen=True)
class FreshPositionMgnModeResolutionV1:
    query_instrument: str
    query_inst_type: str
    query_path: str
    position_match_count: int
    fresh_mgn_mode_observed: str
    bound_td_mode: str
    bound_td_mode_source: str
    bound_td_mode_derivation: str
    observed_field_names: tuple[str, ...]
    observed_uid: str
    http_status: int
    network_get_count: int
    network_post_count: int


def _optional_str(row: Mapping[str, Any], field: str) -> str:
    raw = row.get(field)
    if raw is None:
        return ""
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise D4GenesisFreshPositionMgnModeBootstrapError(
            f"D4_GENESIS_POSITION_FIELD_NOT_STRING:{field}"
        )
    return str(raw).strip()


def resolve_fresh_position_mgn_mode_v1(
    *,
    payload: Mapping[str, Any],
    bound_instrument_id: str,
) -> tuple[str, int, tuple[str, ...], str]:
    if not isinstance(payload, Mapping):
        raise D4GenesisFreshPositionMgnModeBootstrapError("POSITIONS_PAYLOAD_NOT_OBJECT")
    code = str(payload.get("code") or "").strip()
    if code != "0":
        raise D4GenesisFreshPositionMgnModeBootstrapError(f"POSITIONS_VENUE_CODE_NOT_ZERO:{code}")
    data = payload.get("data")
    if not isinstance(data, list):
        raise D4GenesisFreshPositionMgnModeBootstrapError("POSITIONS_DATA_NOT_LIST")
    if not data:
        raise D4GenesisFreshPositionMgnModeBootstrapError("POSITIONS_EMPTY")
    names: set[str] = set()
    mgn_modes: list[str] = []
    uids: set[str] = set()
    match_count = 0
    for item in data:
        if not isinstance(item, Mapping):
            raise D4GenesisFreshPositionMgnModeBootstrapError("POSITIONS_ROW_NOT_OBJECT")
        names.update(str(key) for key in item.keys())
        inst_id = _optional_str(item, "instId")
        if inst_id != bound_instrument_id:
            continue
        match_count += 1
        mgn_mode = _optional_str(item, "mgnMode")
        if mgn_mode == "":
            raise D4GenesisFreshPositionMgnModeBootstrapError(
                "D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode:MGN_MODE_EMPTY"
            )
        if mgn_mode not in ALLOWED_MGN_MODES:
            raise D4GenesisFreshPositionMgnModeBootstrapError(
                f"D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode:MGN_MODE_NOT_ALLOWED:{mgn_mode}"
            )
        mgn_modes.append(mgn_mode)
        uid = _optional_str(item, "uid")
        if uid:
            uids.add(uid)
    if match_count == 0:
        raise D4GenesisFreshPositionMgnModeBootstrapError("POSITION_MATCH_COUNT_ZERO")
    unique_modes = set(mgn_modes)
    if len(unique_modes) != 1:
        raise D4GenesisFreshPositionMgnModeBootstrapError(
            "D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode:CONFLICTING_MGN_MODE"
        )
    observed_uid = ""
    if len(uids) == 1:
        observed_uid = next(iter(uids))
    elif len(uids) > 1:
        raise D4GenesisFreshPositionMgnModeBootstrapError(
            "D4_GENESIS_FIELD_FAIL_CLOSED:bound_account_identity:CONFLICTING_UID"
        )
    return next(iter(unique_modes)), match_count, tuple(sorted(names)), observed_uid


def _assert_one_get_zero_writes(
    client: LiveCanaryHttpClientV1, *, expected_endpoint: str
) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise D4GenesisFreshPositionMgnModeBootstrapError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise D4GenesisFreshPositionMgnModeBootstrapError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshPositionMgnModeBootstrapError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshPositionMgnModeBootstrapError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshPositionMgnModeBootstrapError("ORDER_REQUEST_DETECTED")
    if list(client.counters.endpoints_used) != [expected_endpoint]:
        raise D4GenesisFreshPositionMgnModeBootstrapError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise D4GenesisFreshPositionMgnModeBootstrapError("NON_GET_METHOD_DETECTED")
    return counters


def execute_genesis_position_mgn_mode_get_v1(
    *,
    owner_go: str,
    genesis_id: str,
    genesis_as_of: str,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> FreshPositionMgnModeResolutionV1:
    if owner_go != TD_MODE_RESOLUTION_OWNER_GO:
        raise D4GenesisFreshPositionMgnModeBootstrapError("TD_MODE_RESOLUTION_OWNER_GO_MISMATCH")
    if genesis_id != EXPECTED_GENESIS_ID:
        raise D4GenesisFreshPositionMgnModeBootstrapError("GENESIS_ID_MUST_REMAIN_BOUND")
    if genesis_as_of != EXPECTED_GENESIS_AS_OF:
        raise D4GenesisFreshPositionMgnModeBootstrapError("GENESIS_AS_OF_MUST_REMAIN_BOUND")
    assert_live_canary_instrument_binding_v1(
        instrument_id=DEFAULT_INSTRUMENT_ID, inst_type=DEFAULT_INST_TYPE
    )
    query = build_account_positions_query_v1(
        inst_type=DEFAULT_INST_TYPE, inst_id=DEFAULT_INSTRUMENT_ID
    )
    endpoint = query.path_with_query()
    if query.endpoint != POSITION_STATE_ENDPOINT:
        raise D4GenesisFreshPositionMgnModeBootstrapError("POSITIONS_ENDPOINT_DRIFT")
    if POSITION_STATE_ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise D4GenesisFreshPositionMgnModeBootstrapError("MUTATION_ENDPOINT_FORBIDDEN")
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise D4GenesisFreshPositionMgnModeBootstrapError("HOST_MISMATCH")
    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise D4GenesisFreshPositionMgnModeBootstrapError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise D4GenesisFreshPositionMgnModeBootstrapError("PRODUCTIVE_WIRE_DISABLED")
    client = LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    auth_headers: dict[str, str] = {}
    handle = None
    http_status: int | None = None
    body_bytes = b""
    try:
        url = f"{REUSED_REST_BASE}{endpoint}"
        parsed = urlparse(url)
        if parsed.path != POSITION_STATE_ENDPOINT:
            raise D4GenesisFreshPositionMgnModeBootstrapError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise D4GenesisFreshPositionMgnModeBootstrapError("HOST_MISMATCH")
        if productive:
            backend = _fail_closed_credential_unavailable_v1(vault_file=vault_file)
            handle = _fail_closed_credential_unavailable_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
            auth_headers = _fail_closed_credential_unavailable_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        response = client.get(endpoint=endpoint, headers=auth_headers or None)
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise D4GenesisFreshPositionMgnModeBootstrapError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            raise D4GenesisFreshPositionMgnModeBootstrapError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        raise D4GenesisFreshPositionMgnModeBootstrapError(
            f"GENESIS_POSITIONS_GET_FAILED:{exc}"
        ) from exc
    finally:
        auth_headers.clear()
        if handle is not None:
            _fail_closed_credential_unavailable_v1(handle)
    _assert_one_get_zero_writes(client, expected_endpoint=endpoint)
    payload = parse_json_object_v1(body_bytes)
    mgn_mode, match_count, field_names, observed_uid = resolve_fresh_position_mgn_mode_v1(
        payload=payload, bound_instrument_id=DEFAULT_INSTRUMENT_ID
    )
    return FreshPositionMgnModeResolutionV1(
        query_instrument=DEFAULT_INSTRUMENT_ID,
        query_inst_type=DEFAULT_INST_TYPE,
        query_path=endpoint,
        position_match_count=match_count,
        fresh_mgn_mode_observed=mgn_mode,
        bound_td_mode=mgn_mode,
        bound_td_mode_source=TD_MODE_SOURCE,
        bound_td_mode_derivation=TD_MODE_DERIVATION,
        observed_field_names=field_names,
        observed_uid=observed_uid,
        http_status=int(http_status or 0),
        network_get_count=1,
        network_post_count=0,
    )
