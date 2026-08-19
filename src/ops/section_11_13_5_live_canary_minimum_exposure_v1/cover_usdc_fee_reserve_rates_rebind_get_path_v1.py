"""§11.13.5.Z2M one-shot authenticated trade-fee GET execution-path ratification.

Seals the later-authorizable read-only request path for FEE_RESERVE_RATES
using the already-sealed §11.13.5.V/Z2L grammar. Does not execute a
productive HTTP GET. Does not freeze taker/maker rates. Does not
instantiate FEE_RESERVE or COVER_USDC. Does not widen
GET_ENDPOINTS_PRIVATE or POST allowlists. Does not authorize Live,
Testnet, orders, funding, conversion, transfer, or Canary execute.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import parse_qsl, urlsplit

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.binding_v1 import (
    normalize_rest_host,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    ENDPOINT_ALLOWLIST_READ,
    FORBIDDEN_HOST_MARKERS,
    FORBIDDEN_HTTP_METHODS_OUTSIDE_GATED_SUBMIT,
    FORBIDDEN_MUTATION_ENDPOINT_MARKERS,
    GET_ENDPOINTS_PRIVATE,
    GET_ENDPOINTS_PUBLIC,
    LIVE_AUTHORIZED,
    POST_ENDPOINTS_GATED,
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_ACCOUNT_SCOPE,
    REUSED_BINDING_REST_HOST,
    TESTNET_AUTHORIZED,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    LiveCanaryTransportV1,
    assert_no_demo_simulation_headers_v1,
    extract_canary_http_response_evidence_v1,
    parse_json_object_v1,
    safe_response_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryEphemeralCredentialHandleV1,
    assert_no_plaintext_in_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.okx_live_canary_signer_v1 import (
    auth_headers_presence_doc_v1,
    build_okx_live_canary_auth_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.secretref_v1 import (
    validate_live_canary_credential_class_v1,
    validate_live_canary_secretref_uri_v1,
)

OWNER_GO = "OWNER_GO_TO_RATIFY_ONE_SHOT_SECTION_11_13_5_AUTHENTICATED_TRADE_FEE_GET_EXECUTION_PATH"
EXECUTE_OWNER_GO = "OWNER_GO_FOR_EXACTLY_ONE_AUTHENTICATED_READ_ONLY_TRADE_FEE_REBIND_GET"
AUTHORIZED_SCOPE = "FEE_RESERVE_RATES_REBIND_GET_EXECUTION_PATH_RATIFICATION_ONLY"
NEXT_CANONICAL_POINTER = (
    "OWNER_GO_REQUIRED_FOR_EXACTLY_ONE_AUTHENTICATED_READ_ONLY_TRADE_FEE_REBIND_GET"
)
SEALED_HOST = REUSED_BINDING_REST_HOST
SEALED_METHOD = "GET"
SEALED_PATH = "/api/v5/account/trade-fee"
SEALED_INST_TYPE = DEFAULT_INST_TYPE
SEALED_INST_FAMILY = "BTC-USD_UM_XPERP"
SEALED_QUERY = f"instType={SEALED_INST_TYPE}&instFamily={SEALED_INST_FAMILY}"
SEALED_QUERY_PAIRS: tuple[tuple[str, str], ...] = (
    ("instType", SEALED_INST_TYPE),
    ("instFamily", SEALED_INST_FAMILY),
)
SEALED_ENDPOINT = f"{SEALED_PATH}?{SEALED_QUERY}"
SEALED_URL = f"https://{SEALED_HOST}{SEALED_ENDPOINT}"
SOURCE_CLASS = "AUTHENTICATED_READ_ONLY_OKX_ACCOUNT_TRADE_FEE_GET"
SECRETREF_URI = REQUIRED_SECRETREF_URI
CREDENTIAL_CLASS = REQUIRED_CREDENTIAL_CLASS
ACCOUNT_BINDING_SCOPE = REUSED_BINDING_ACCOUNT_SCOPE
MAX_REQUEST_COUNT = 1
MAX_RETRIES = 0
FEE_RESERVE_RATES_ADJUDICATION = "UNPROVEN"
COVER_USDC_STATUS = "UNINSTANTIATED"


class CoverUsdcFeeReserveRatesRebindGetPathError(RuntimeError):
    """Fail-closed trade-fee GET execution-path ratification violation."""


def classify_fee_reserve_rates_rebind_get_path_v1() -> dict[str, Any]:
    """Return the sealed execution-path surface. No network. No secrets."""
    return {
        "TERM": "FEE_RESERVE_RATES",
        "SOURCE_CLASS": SOURCE_CLASS,
        "HOST": SEALED_HOST,
        "METHOD": SEALED_METHOD,
        "PATH": SEALED_PATH,
        "QUERY": SEALED_QUERY,
        "ENDPOINT": SEALED_ENDPOINT,
        "URL": SEALED_URL,
        "INST_TYPE": SEALED_INST_TYPE,
        "INST_FAMILY": SEALED_INST_FAMILY,
        "CANARY_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "ACCOUNT_BINDING_SCOPE": ACCOUNT_BINDING_SCOPE,
        "AUTHENTICATION_REQUIREMENT": SOURCE_CLASS,
        "SECRETREF_URI": SECRETREF_URI,
        "CREDENTIAL_CLASS": CREDENTIAL_CLASS,
        "SIGNER": "build_okx_live_canary_auth_headers_v1",
        "TRANSPORT": "UrllibLiveCanaryTransportV1",
        "RUNNER": ("scripts/ops/run_section_11_13_5_z2m_fee_reserve_rates_rebind_get_path_v1.py"),
        "CODE_OWNER": (
            "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/"
            "cover_usdc_fee_reserve_rates_rebind_get_path_v1.py"
        ),
        "READ_ONLY": True,
        "ONE_SHOT_REQUEST_LIMIT": MAX_REQUEST_COUNT,
        "RETRY_COUNT_ALLOWED": MAX_RETRIES,
        "GENERAL_CLIENT_ALLOWLIST_WIDENED": False,
        "GET_ENDPOINTS_PRIVATE_INCLUDES_TRADE_FEE": (SEALED_PATH in GET_ENDPOINTS_PRIVATE),
        "THIS_GO_AUTHORIZES_HTTP_GET": False,
        "LATER_GET_REQUIRES_SEPARATE_OWNER_GO": True,
        "EXECUTE_OWNER_GO": EXECUTE_OWNER_GO,
        "FEE_RESERVE_RATES_ADJUDICATION": FEE_RESERVE_RATES_ADJUDICATION,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "TESTNET_AUTHORIZED": TESTNET_AUTHORIZED,
        "AUTHORIZATION_SCOPE_CANARY": AUTHORIZATION_SCOPE,
        "OWNER_GO_SCOPE": AUTHORIZED_SCOPE,
    }


def ratify_fee_reserve_rates_rebind_get_path_v1(*, owner_go: str) -> dict[str, Any]:
    """Seal the execution path without credentials, transport, or HTTP."""
    if owner_go != OWNER_GO:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(f"OWNER_GO_MISMATCH:{owner_go}")
    _assert_general_canary_allowlists_unwidened()
    request = build_sealed_trade_fee_get_request_v1(
        host=SEALED_HOST,
        method=SEALED_METHOD,
        path=SEALED_PATH,
        query=SEALED_QUERY,
        headers={"User-Agent": USER_AGENT_CANARY, "Accept": "application/json"},
    )
    payload = {
        "ok": True,
        "PATH_RATIFIED": True,
        "EVIDENCE_CALL_EXECUTED": False,
        "EVIDENCE_CALL_COUNT": 0,
        "PRODUCTION_NETWORK_CALL_EXECUTED": False,
        "SECRET_VALUE_EXPOSED": False,
        "classification": classify_fee_reserve_rates_rebind_get_path_v1(),
        "REQUEST_METHOD": request.method,
        "REQUEST_HOST": request.host,
        "REQUEST_PATH": SEALED_PATH,
        "REQUEST_QUERY": SEALED_QUERY,
        "REQUEST_URL": request.url,
        "REQUEST_BODY": request.body_text,
        "MAX_REQUEST_COUNT": MAX_REQUEST_COUNT,
        "MAX_RETRIES": MAX_RETRIES,
        "NEXT_CANONICAL_POINTER": NEXT_CANONICAL_POINTER,
        "FEE_RESERVE_RATES_ADJUDICATION": FEE_RESERVE_RATES_ADJUDICATION,
    }
    assert_no_plaintext_in_payload_v1(payload)
    return payload


def assert_sealed_trade_fee_request_grammar_v1(
    *,
    method: str,
    host: str,
    path: str,
    query: str,
    body_text: str = "",
) -> None:
    """Fail-closed exact grammar. No heuristic reconstruction."""
    method_u = str(method or "").strip().upper()
    if method_u in FORBIDDEN_HTTP_METHODS_OUTSIDE_GATED_SUBMIT:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(f"HTTP_METHOD_HARD_BLOCK:{method_u}")
    if method_u != SEALED_METHOD:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            f"METHOD_NOT_ALLOWLISTED:{method_u or '<empty>'}"
        )
    if str(body_text or ""):
        raise CoverUsdcFeeReserveRatesRebindGetPathError("GET_BODY_FORBIDDEN")
    host_n = normalize_rest_host(str(host or "").strip())
    for marker in FORBIDDEN_HOST_MARKERS:
        if marker in host_n:
            raise CoverUsdcFeeReserveRatesRebindGetPathError(f"FORBIDDEN_HOST_MARKER:{marker}")
    if host_n != SEALED_HOST:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            f"HOST_NOT_ALLOWLISTED:{host_n or '<empty>'}"
        )
    path_n = str(path or "").strip()
    if path_n != SEALED_PATH:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            f"PATH_NOT_ALLOWLISTED:{path_n or '<empty>'}"
        )
    lowered = path_n.lower()
    for marker in FORBIDDEN_MUTATION_ENDPOINT_MARKERS:
        if marker in lowered:
            raise CoverUsdcFeeReserveRatesRebindGetPathError(
                f"MUTATION_ENDPOINT_HARD_BLOCK:{path_n}"
            )
    query_n = str(query or "")
    if query_n != SEALED_QUERY:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            f"QUERY_NOT_ALLOWLISTED:{query_n or '<empty>'}"
        )
    try:
        pairs = tuple(parse_qsl(query_n, keep_blank_values=True, strict_parsing=True))
    except ValueError as exc:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("QUERY_PARSE_FAILED") from exc
    if pairs != SEALED_QUERY_PAIRS:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("QUERY_PAIRS_NOT_ALLOWLISTED")
    keys = [item[0] for item in pairs]
    if "instType" not in keys:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("INSTTYPE_REQUIRED")
    if "instFamily" not in keys:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("INSTFAMILY_REQUIRED")
    if "instId" in keys:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("INSTID_PARAMETER_FORBIDDEN")
    if "ruleType" in keys:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("RULETYPE_PARAMETER_FORBIDDEN")
    if len(pairs) != 2:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("ADDITIONAL_QUERY_PARAMETER_FORBIDDEN")


def build_sealed_trade_fee_get_request_v1(
    *,
    host: str = SEALED_HOST,
    method: str = SEALED_METHOD,
    path: str = SEALED_PATH,
    query: str = SEALED_QUERY,
    headers: Mapping[str, str] | None = None,
    timeout_seconds: float = 10.0,
    body_text: str = "",
) -> LiveCanaryHttpRequestV1:
    """Build exactly the sealed request. Does not send."""
    assert_sealed_trade_fee_request_grammar_v1(
        method=method,
        host=host,
        path=path,
        query=query,
        body_text=body_text,
    )
    hdrs = {str(k): str(v) for k, v in dict(headers or {}).items()}
    if not any(str(k).strip().lower() == "user-agent" for k in hdrs):
        hdrs["User-Agent"] = USER_AGENT_CANARY
    assert_no_demo_simulation_headers_v1(hdrs)
    endpoint = f"{path}?{query}"
    url = f"https://{normalize_rest_host(host)}{endpoint}"
    parsed = urlsplit(url)
    if parsed.scheme != "https":
        raise CoverUsdcFeeReserveRatesRebindGetPathError("SCHEME_NOT_ALLOWLISTED")
    if parsed.hostname != SEALED_HOST:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            f"URL_HOST_NOT_ALLOWLISTED:{parsed.hostname or '<empty>'}"
        )
    if parsed.path != SEALED_PATH:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("URL_PATH_NOT_ALLOWLISTED")
    if parsed.query != SEALED_QUERY:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("URL_QUERY_NOT_ALLOWLISTED")
    if parsed.fragment or parsed.username or parsed.password or parsed.port:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("URL_EXTRA_COMPONENTS_FORBIDDEN")
    return LiveCanaryHttpRequestV1(
        method=SEALED_METHOD,
        url=url,
        host=SEALED_HOST,
        endpoint=endpoint,
        headers=hdrs,
        timeout_seconds=timeout_seconds,
        body_text="",
    )


def _assert_general_canary_allowlists_unwidened() -> None:
    if SEALED_PATH in GET_ENDPOINTS_PRIVATE or SEALED_PATH in GET_ENDPOINTS_PUBLIC:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            "GENERAL_CANARY_GET_ALLOWLIST_MUST_NOT_INCLUDE_TRADE_FEE"
        )
    if SEALED_PATH in ENDPOINT_ALLOWLIST_READ:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            "PREFLIGHT_READ_ALLOWLIST_MUST_NOT_INCLUDE_TRADE_FEE"
        )
    if SEALED_PATH in POST_ENDPOINTS_GATED:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(
            "POST_ALLOWLIST_MUST_NOT_INCLUDE_TRADE_FEE"
        )


def collect_fee_reserve_rates_rebind_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    handle: LiveCanaryEphemeralCredentialHandleV1,
    owner_go: str,
    execute_trade_fee_get: bool,
    secretref_uri: str = SECRETREF_URI,
    credential_class: str = CREDENTIAL_CLASS,
    rest_host: str = SEALED_HOST,
    timeout_seconds: float = 10.0,
) -> tuple[dict[str, Any], LiveCanaryHttpResponseV1]:
    """Later-GO one-shot GET. This ratification GO must not call it on the wire."""
    if not execute_trade_fee_get:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("EXECUTE_FLAG_REQUIRED")
    if owner_go != EXECUTE_OWNER_GO:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(f"EXECUTE_OWNER_GO_MISMATCH:{owner_go}")
    _assert_general_canary_allowlists_unwidened()
    ref = validate_live_canary_secretref_uri_v1(secretref_uri)
    klass = validate_live_canary_credential_class_v1(credential_class)
    if rest_host != SEALED_HOST:
        raise CoverUsdcFeeReserveRatesRebindGetPathError(f"HOST_MISMATCH:{rest_host}")
    unsigned = build_sealed_trade_fee_get_request_v1(
        host=rest_host,
        timeout_seconds=timeout_seconds,
    )
    headers = build_okx_live_canary_auth_headers_v1(
        handle=handle,
        url=unsigned.url,
        method=SEALED_METHOD,
        extra_headers={"User-Agent": USER_AGENT_CANARY, "Accept": "application/json"},
    )
    auth_presence = auth_headers_presence_doc_v1(headers)
    request = build_sealed_trade_fee_get_request_v1(
        host=rest_host,
        headers=headers,
        timeout_seconds=timeout_seconds,
    )
    try:
        response = transport.send(request)
    except LiveCanaryHttpError:
        raise
    finally:
        headers.clear()
    if response.method != "GET":
        raise CoverUsdcFeeReserveRatesRebindGetPathError("TRANSPORT_RETURNED_NON_GET")
    if response.redirect_followed:
        raise CoverUsdcFeeReserveRatesRebindGetPathError("REDIRECT_FOLLOWED_FORBIDDEN")
    redirect_host = ""
    if response.redirect_location:
        redirect_host = str(urlsplit(str(response.redirect_location)).hostname or "")
        if redirect_host and redirect_host != SEALED_HOST:
            raise CoverUsdcFeeReserveRatesRebindGetPathError(
                f"REDIRECT_HOST_NOT_ALLOWLISTED:{redirect_host}"
            )
    http_evidence = extract_canary_http_response_evidence_v1(
        status_code=response.status_code,
        body_bytes=response.body_bytes,
        headers=response.response_headers_safe,
        redirect_followed=response.redirect_followed,
        redirect_status=response.redirect_status,
        redirect_location=response.redirect_location,
    )
    payload = parse_json_object_v1(response.body_bytes)
    snapshot = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2M_FEE_RESERVE_RATES_REBIND_GET_PATH_V1",
        "DOCUMENT_ROLE": "ONE_SHOT_AUTHENTICATED_TRADE_FEE_GET_EVIDENCE_NON_SSOT",
        "OWNER_GO": EXECUTE_OWNER_GO,
        "OWNER_GO_SCOPE": "FEE_RESERVE_RATES_REBIND_GET_ONLY",
        "SECRETREF_URI": ref,
        "CREDENTIAL_CLASS": klass,
        "SECRETREF_HANDLE_DIGEST": handle.material_digest,
        "AUTH_HEADERS_PRESENCE": auth_presence,
        "METHOD": SEALED_METHOD,
        "HOST": rest_host,
        "PATH": SEALED_PATH,
        "QUERY": SEALED_QUERY,
        "ENDPOINT": SEALED_ENDPOINT,
        "GET_REQUEST_COUNT": 1,
        "POST_COUNT": 0,
        "RETRY_COUNT": 0,
        "EVIDENCE_READ_ONLY": True,
        "SECRET_VALUES_INCLUDED": False,
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "FEE_RESERVE_RATES_ADJUDICATION": FEE_RESERVE_RATES_ADJUDICATION,
        "ACCOUNT_BINDING_SCOPE": ACCOUNT_BINDING_SCOPE,
        "CANARY_INSTRUMENT": DEFAULT_INSTRUMENT_ID,
        "http_evidence": http_evidence,
        "response_headers_safe": safe_response_headers_v1(response.response_headers_safe),
        "payload": payload,
    }
    assert_no_plaintext_in_payload_v1(snapshot)
    return snapshot, response
