"""Genesis D4 bootstrap from one fresh GET /api/v5/account/config.

Reuses LiveCanaryHttpClientV1, UrllibLiveCanaryTransportV1, the existing
GET signer, and SecretRef. Does not mint from env, credential contents,
defaults, fixtures, or historical evidence. Does not POST.
Does not reconstruct the legacy D4 chain.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    CONTINUE_OWNER_GO,
    UID_RECAPTURE_OWNER_GO,
    D4D5GenesisRebaselineContractError,
    build_d4_d5_genesis_rebaseline_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.sample_schema_v1 import (
    REQUIRED_SETTLEMENT_CURRENCY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_REST_HOST,
    REUSED_BINDING_VENUE,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
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

ENDPOINT = "/api/v5/account/config"
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
MAX_NETWORK_REQUEST_COUNT = 1
DEFAULT_MAX_RETRIES = 0
DEFAULT_TIMEOUT_SECONDS = 10.0
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/balance",
    "/api/v5/account/subtypes",
    "/api/v5/account/bills",
    "/api/v5/account/bills-archive",
    "/api/v5/asset/balances",
    "/api/v5/account/positions",
    "/api/v5/asset/transfer",
    "/api/v5/trade/order",
)
VENUE_IDENTITY_SOURCE = "CANONICAL_REUSED_GET_PATH_VENUE_IDENTITY"
SETTLEMENT_SOURCE_OBSERVED = "FRESH_ACCOUNT_CONFIG_SETTLE_CCY"
SETTLEMENT_SOURCE_OWNER_PIN = "OWNER_PACKAGE_REQUIRED_SETTLEMENT_CURRENCY"
TD_MODE_SOURCE_OBSERVED = "FRESH_ACCOUNT_CONFIG_TD_MODE"
ACCOUNT_IDENTITY_SOURCE = "FRESH_AUTHENTICATED_ACCOUNT_CONFIG_UID"
FRESH_ACCOUNT_CONFIG_UID_ABSENT = "FRESH_ACCOUNT_CONFIG_UID_ABSENT"


class D4GenesisFreshAccountConfigBootstrapError(ValueError):
    """Fail-closed genesis account-config bootstrap violation."""


@dataclass(frozen=True)
class ObservedAccountConfigIdentityFactsV1:
    observed_uid: str
    observed_main_uid: str
    observed_td_mode: str
    observed_settle_ccy: str
    observed_field_names: tuple[str, ...]


@dataclass(frozen=True)
class GenesisD4MemberResolutionV1:
    bound_account_identity: str
    bound_venue_identity: str
    bound_td_mode: str
    settlement_currency: str
    bound_account_identity_source: str
    bound_venue_identity_source: str
    bound_td_mode_source: str
    settlement_currency_source: str
    uid_freshly_observed: str


def _optional_account_config_field(row: Mapping[str, Any], field: str) -> str:
    raw = row.get(field)
    if raw is None:
        return ""
    if isinstance(raw, bool) or not isinstance(raw, (str, int)):
        raise D4GenesisFreshAccountConfigBootstrapError(f"D4_GENESIS_FIELD_NOT_STRING:{field}")
    text = str(raw).strip()
    if text == "":
        return ""
    return text


def _extract_account_config_row_v1(
    payload: Mapping[str, Any],
) -> tuple[Mapping[str, Any], tuple[str, ...]]:
    if not isinstance(payload, Mapping):
        raise D4GenesisFreshAccountConfigBootstrapError("ACCOUNT_CONFIG_PAYLOAD_NOT_OBJECT")
    code = str(payload.get("code") or "").strip()
    if code != "0":
        raise D4GenesisFreshAccountConfigBootstrapError(
            f"ACCOUNT_CONFIG_VENUE_CODE_NOT_ZERO:{code}"
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise D4GenesisFreshAccountConfigBootstrapError("ACCOUNT_CONFIG_DATA_MISSING")
    if len(data) != 1 or not isinstance(data[0], Mapping):
        raise D4GenesisFreshAccountConfigBootstrapError("ACCOUNT_CONFIG_DATA_NOT_SINGLE_OBJECT")
    row = data[0]
    names = tuple(sorted(str(key) for key in row.keys()))
    return row, names


def extract_observed_account_config_identity_facts_v1(
    payload: Mapping[str, Any],
) -> ObservedAccountConfigIdentityFactsV1:
    row, names = _extract_account_config_row_v1(payload)
    uid = _optional_account_config_field(row, "uid")
    if uid == "":
        raise D4GenesisFreshAccountConfigBootstrapError("D4_GENESIS_FIELD_FAIL_CLOSED:uid")
    return ObservedAccountConfigIdentityFactsV1(
        observed_uid=uid,
        observed_main_uid=_optional_account_config_field(row, "mainUid"),
        observed_td_mode=_optional_account_config_field(row, "tdMode"),
        observed_settle_ccy=_optional_account_config_field(row, "settleCcy"),
        observed_field_names=names,
    )


def extract_account_config_uid_recapture_facts_v1(
    payload: Mapping[str, Any],
) -> ObservedAccountConfigIdentityFactsV1:
    row, names = _extract_account_config_row_v1(payload)
    return ObservedAccountConfigIdentityFactsV1(
        observed_uid=_optional_account_config_field(row, "uid"),
        observed_main_uid=_optional_account_config_field(row, "mainUid"),
        observed_td_mode=_optional_account_config_field(row, "tdMode"),
        observed_settle_ccy=_optional_account_config_field(row, "settleCcy"),
        observed_field_names=names,
    )


def resolve_genesis_d4_members_v1(
    *,
    observed: ObservedAccountConfigIdentityFactsV1,
) -> GenesisD4MemberResolutionV1:
    if observed.observed_uid == "":
        raise D4GenesisFreshAccountConfigBootstrapError(
            "D4_GENESIS_FIELD_FAIL_CLOSED:bound_account_identity"
        )
    if REUSED_BINDING_VENUE != "OKX":
        raise D4GenesisFreshAccountConfigBootstrapError(
            "D4_GENESIS_FIELD_FAIL_CLOSED:bound_venue_identity"
        )
    if observed.observed_td_mode == "":
        raise D4GenesisFreshAccountConfigBootstrapError(
            "D4_GENESIS_FIELD_FAIL_CLOSED:bound_td_mode"
        )
    settle = observed.observed_settle_ccy
    settle_source = SETTLEMENT_SOURCE_OBSERVED
    if settle == "":
        if REQUIRED_SETTLEMENT_CURRENCY != "USDC":
            raise D4GenesisFreshAccountConfigBootstrapError(
                "D4_GENESIS_FIELD_FAIL_CLOSED:settlement_currency"
            )
        settle = REQUIRED_SETTLEMENT_CURRENCY
        settle_source = SETTLEMENT_SOURCE_OWNER_PIN
    return GenesisD4MemberResolutionV1(
        bound_account_identity=observed.observed_uid,
        bound_venue_identity=REUSED_BINDING_VENUE,
        bound_td_mode=observed.observed_td_mode,
        settlement_currency=settle,
        bound_account_identity_source="FRESH_AUTHENTICATED_ACCOUNT_CONFIG_UID",
        bound_venue_identity_source=VENUE_IDENTITY_SOURCE,
        bound_td_mode_source=TD_MODE_SOURCE_OBSERVED,
        settlement_currency_source=settle_source,
        uid_freshly_observed="true",
    )


def _assert_one_get_zero_writes(client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 1:
        raise D4GenesisFreshAccountConfigBootstrapError("GET_COUNT_NOT_ONE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 1:
        raise D4GenesisFreshAccountConfigBootstrapError("REQUEST_COUNT_NOT_ONE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshAccountConfigBootstrapError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshAccountConfigBootstrapError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise D4GenesisFreshAccountConfigBootstrapError("ORDER_REQUEST_DETECTED")
    if list(client.counters.endpoints_used) != [ENDPOINT]:
        raise D4GenesisFreshAccountConfigBootstrapError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"]:
        raise D4GenesisFreshAccountConfigBootstrapError("NON_GET_METHOD_DETECTED")
    return counters


def _execute_account_config_http_get_v1(
    *,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> tuple[int, dict[str, Any], bytes]:
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise D4GenesisFreshAccountConfigBootstrapError("HOST_MISMATCH")
    if ENDPOINT in FORBIDDEN_ENDPOINTS:
        raise D4GenesisFreshAccountConfigBootstrapError("MUTATION_ENDPOINT_FORBIDDEN")
    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise D4GenesisFreshAccountConfigBootstrapError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise D4GenesisFreshAccountConfigBootstrapError("PRODUCTIVE_WIRE_DISABLED")
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
        url = f"{REUSED_REST_BASE}{ENDPOINT}"
        parsed = urlparse(url)
        if parsed.path != ENDPOINT or parsed.query:
            raise D4GenesisFreshAccountConfigBootstrapError("SIGNED_REQUEST_TARGET_MISMATCH")
        if parsed.hostname != AUTHORIZED_HOST:
            raise D4GenesisFreshAccountConfigBootstrapError("HOST_MISMATCH")
        if productive:
            backend = build_file_secretref_vault_backend_v1(vault_file=vault_file)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
            auth_headers = build_okx_live_canary_auth_headers_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        response = client.get(endpoint=ENDPOINT, headers=auth_headers or None)
        http_status = int(response.status_code)
        body_bytes = bytes(response.body_bytes)
        if response.method != "GET":
            raise D4GenesisFreshAccountConfigBootstrapError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            raise D4GenesisFreshAccountConfigBootstrapError("REDIRECT_FOLLOWED")
    except LiveCanaryHttpError as exc:
        raise D4GenesisFreshAccountConfigBootstrapError(f"GENESIS_GET_FAILED:{exc}") from exc
    finally:
        auth_headers.clear()
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
    counters = _assert_one_get_zero_writes(client)
    if http_status is None:
        raise D4GenesisFreshAccountConfigBootstrapError("GENESIS_GET_FAILED:HTTP_STATUS_ABSENT")
    return http_status, counters, body_bytes


def execute_genesis_account_config_get_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    genesis_id: str,
    genesis_as_of: str,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    try:
        build_d4_d5_genesis_rebaseline_contract_v1(
            genesis_id=genesis_id,
            genesis_as_of=genesis_as_of,
            owner_go=owner_go,
            bound_origin_main_sha=origin_main_sha,
            continue_owner_go=CONTINUE_OWNER_GO,
        )
    except D4D5GenesisRebaselineContractError as exc:
        raise D4GenesisFreshAccountConfigBootstrapError(str(exc)) from exc
    http_status, counters, body_bytes = _execute_account_config_http_get_v1(
        vault_file=vault_file,
        transport=transport,
    )
    payload = parse_json_object_v1(body_bytes)
    observed = extract_observed_account_config_identity_facts_v1(payload)
    members = resolve_genesis_d4_members_v1(observed=observed)
    return {
        "http_status": http_status,
        "get_error": None,
        "counters": counters,
        "observed": observed,
        "members": members,
        "network_get_count": 1,
        "network_post_count": 0,
        "d4_genesis_bootstrap_source": "FRESH_AUTHENTICATED_ACCOUNT_CONFIG",
    }


def execute_genesis_account_config_uid_recapture_get_v1(
    *,
    owner_go: str,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
) -> dict[str, Any]:
    if owner_go != UID_RECAPTURE_OWNER_GO:
        raise D4GenesisFreshAccountConfigBootstrapError("UID_RECAPTURE_OWNER_GO_MISMATCH")
    http_status, counters, body_bytes = _execute_account_config_http_get_v1(
        vault_file=vault_file,
        transport=transport,
    )
    payload = parse_json_object_v1(body_bytes)
    observed = extract_account_config_uid_recapture_facts_v1(payload)
    return {
        "http_status": http_status,
        "get_error": None,
        "counters": counters,
        "observed": observed,
        "bound_account_identity": observed.observed_uid,
        "bound_account_identity_source": ACCOUNT_IDENTITY_SOURCE,
        "network_get_count": 1,
        "network_post_count": 0,
        "d4_genesis_bootstrap_source": "FRESH_AUTHENTICATED_ACCOUNT_CONFIG",
    }
