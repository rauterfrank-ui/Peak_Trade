"""PACKAGE_1 Observation S1-S5 execution.

Reuses LiveCanaryHttpClientV1, the existing GET signer, and SecretRef.
Exactly five authorized GET surfaces. Does not mint D4 identity.
Does not POST. Does not classify kinds. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_genesis_fresh_account_config_bootstrap_v1 import (
    D4GenesisFreshAccountConfigBootstrapError,
    extract_account_config_uid_recapture_facts_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    assert_package_1_observation_s0_runtime_payloads_present_v1,
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.path_b_class_c_package_1_trading_account_observation_rules_contract_v1 import (
    BALANCE_ALLOWED_OBSERVATION_FIELDS,
    PathBClassCPackage1TradingAccountObservationRulesContractError,
    corroborate_d4_identity_from_account_config_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_BILLS,
    ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_SUBTYPES,
    REUSED_BINDING_REST_HOST,
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


def _fail_closed_credential_unavailable_v1(*_a, **_k):
    raise RuntimeError("CREDENTIAL_HANDLE_FAIL_CLOSED")


OWNER_GO = "OWNER_GO_D6_PATH_B_CLASS_C_PACKAGE_1_OBSERVATION_EXECUTION_WORKPACKAGE_V1"
EXPECTED_ORIGIN_MAIN_SHA = "e3ba0c516113f600a3634da73ae09359d85e0618"
AUTHORIZED_HOST = "eea.okx.com"
REUSED_REST_BASE = f"https://{REUSED_BINDING_REST_HOST}"
AUTHORIZED_ENDPOINTS: tuple[str, ...] = (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_BALANCE,
    ENDPOINT_ACCOUNT_SUBTYPES,
    ENDPOINT_ACCOUNT_BILLS,
    ENDPOINT_ACCOUNT_BILLS_ARCHIVE,
)
FORBIDDEN_ENDPOINTS: tuple[str, ...] = (
    "/api/v5/account/positions",
    "/api/v5/asset/balances",
    "/api/v5/asset/transfer",
    "/api/v5/trade/order",
)
MAX_NETWORK_REQUEST_COUNT = 5
DEFAULT_MAX_RETRIES = 0
DEFAULT_TIMEOUT_SECONDS = 10.0
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
OKX_BILLS_DEFAULT_PAGE_LIMIT = 100
RETENTION_COVERAGE_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
ORDERING_COMPLETENESS_FAIL_CLOSED = "FAIL_CLOSED_NOT_PROVEN"
D4_CORROBORATED = "D4_RUNTIME_EVIDENCE_CORROBORATED_IDENTITY_NOT_MINTED"


class Package1ObservationExecutionError(ValueError):
    """Fail-closed PACKAGE_1 Observation S1-S5 violation."""


@dataclass(frozen=True)
class Package1ObservationExecutionResultV1:
    genesis_id: str
    genesis_as_of: str
    observation_as_of: str
    store_root: str
    s1_account_config_get: str
    s2_account_balance_get: str
    s3_account_subtypes_get: str
    s4_account_bills_get: str
    s4_account_bills_archive_get: str
    authorized_get_surface_count: str
    unauthorized_get_surface_count: str
    network_post_performed: str
    d4_corroboration_result: str
    d4_identity_minted: str
    raw_eq_source_authority: str
    bills_archive_overlap_status: str
    retention_coverage_status: str
    ordering_completeness_status: str
    raw_evidence_sealed: str
    evidence_manifest: str
    kind_set_resolved: str
    mapping_persisted: str
    mapping_s6_executed: str
    ms2_authorized: str
    d6_fully_closed: str
    d7_authorized: str


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _folder_from_as_of(as_of: str) -> str:
    return as_of.replace(":", "")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _persist_json(*, path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(payload) + "\n", encoding="utf-8")
    tmp.replace(path)


def _require_owner_go(owner_go: str) -> None:
    if owner_go != OWNER_GO:
        raise Package1ObservationExecutionError("PACKAGE_1_OBSERVATION_OWNER_GO_MISMATCH")


def _verify_genesis_manifest(*, store_root: Path) -> None:
    manifest = store_root / "MANIFEST.sha256"
    if not manifest.is_file():
        raise Package1ObservationExecutionError("GENESIS_MANIFEST_ABSENT")
    expected: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual_names = {
        p.name for p in store_root.iterdir() if p.is_file() and p.name != "MANIFEST.sha256"
    }
    if set(expected) != actual_names:
        raise Package1ObservationExecutionError("GENESIS_MANIFEST_FILESET_DRIFT")
    for name, digest in expected.items():
        actual = _sha256_bytes((store_root / name).read_bytes())
        if actual != digest:
            raise Package1ObservationExecutionError(f"GENESIS_MANIFEST_DIGEST_MISMATCH:{name}")


def _load_genesis_claims(*, store_root: Path) -> dict[str, str]:
    claims_path = store_root / "claims.json"
    payload = json.loads(claims_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Package1ObservationExecutionError("GENESIS_CLAIMS_NOT_OBJECT")
    return {str(k): str(v) for k, v in payload.items()}


def preflight_package_1_observation_s0_v1(
    *,
    origin_main_sha: str,
    genesis_store_root: Path | str | None = None,
) -> Path:
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise Package1ObservationExecutionError("ORIGIN_MAIN_SHA_MISMATCH")
    root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1()
    )
    if root is None:
        raise Package1ObservationExecutionError("GENESIS_RUNTIME_STORE_ABSENT")
    assert_package_1_observation_s0_runtime_payloads_present_v1(store_root=root)
    _verify_genesis_manifest(store_root=root)
    claims = _load_genesis_claims(store_root=root)
    if claims.get("GENESIS_ID") != EXPECTED_GENESIS_ID:
        raise Package1ObservationExecutionError("GENESIS_ID_DRIFT")
    if claims.get("GENESIS_AS_OF") != EXPECTED_GENESIS_AS_OF:
        raise Package1ObservationExecutionError("GENESIS_AS_OF_DRIFT")
    if claims.get("D4_RUNTIME_INSTANCE_PRESENT") != TRUE_TOKEN:
        raise Package1ObservationExecutionError("D4_RUNTIME_INSTANCE_ABSENT")
    if claims.get("D5_RUNTIME_INSTANCE_PRESENT") != TRUE_TOKEN:
        raise Package1ObservationExecutionError("D5_RUNTIME_INSTANCE_ABSENT")
    if claims.get("OBSERVATION_S0_PREREQUISITES_SATISFIED") != TRUE_TOKEN:
        raise Package1ObservationExecutionError("OBSERVATION_S0_PREREQUISITES_NOT_SATISFIED")
    if claims.get("BOUND_ACCOUNT_IDENTITY_RESOLVED") != TRUE_TOKEN:
        raise Package1ObservationExecutionError("BOUND_ACCOUNT_IDENTITY_NOT_RESOLVED")
    if claims.get("NETWORK_POST_PERFORMED") != FALSE_TOKEN:
        raise Package1ObservationExecutionError("GENESIS_NETWORK_POST_NOT_FALSE")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=root)
    if d4.bound_td_mode != "cross":
        raise Package1ObservationExecutionError("BOUND_TD_MODE_NOT_CROSS")
    if d4.bound_venue_identity != "OKX":
        raise Package1ObservationExecutionError("BOUND_VENUE_IDENTITY_DRIFT")
    if d4.settlement_currency != "USDC":
        raise Package1ObservationExecutionError("SETTLEMENT_CURRENCY_DRIFT")
    if d5.observed_at_as_of != EXPECTED_GENESIS_AS_OF:
        raise Package1ObservationExecutionError("D5_WINDOW_AS_OF_DRIFT")
    return root


def _extract_rows(payload: Mapping[str, Any]) -> list[Any]:
    data = payload.get("data")
    if data is None:
        return []
    if not isinstance(data, list):
        raise Package1ObservationExecutionError("VENUE_DATA_NOT_LIST")
    return list(data)


def _optional_str(row: Mapping[str, Any], field: str) -> str:
    raw = row.get(field)
    if raw is None:
        return ""
    if isinstance(raw, bool):
        return ""
    return str(raw).strip()


def _bill_ids(rows: list[Any]) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        bill_id = _optional_str(row, "billId")
        if bill_id:
            ids.add(bill_id)
    return ids


def _overlap_status(*, bills_ids: set[str], archive_ids: set[str]) -> str:
    if not bills_ids and not archive_ids:
        return "BOTH_EMPTY_QUERY_RETURNED_NO_ROWS"
    if not bills_ids or not archive_ids:
        return "ONE_SIDE_EMPTY_QUERY_RETURNED_NO_ROWS"
    if bills_ids == archive_ids:
        return "IDENTICAL_BILL_ID_SET"
    if bills_ids & archive_ids:
        return "PARTIAL_BILL_ID_OVERLAP"
    return "DISJOINT_BILL_ID_SET"


def _pagination_status(*, row_count: int) -> str:
    if row_count >= OKX_BILLS_DEFAULT_PAGE_LIMIT:
        return "SINGLE_PAGE_NOT_EXHAUSTED"
    return "SINGLE_PAGE_NO_CONTINUATION_OBSERVED"


def _balance_reconciliation_fields(rows: list[Any]) -> list[dict[str, str]]:
    observed: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        details = row.get("details")
        nested = details if isinstance(details, list) else [row]
        for item in nested:
            if not isinstance(item, Mapping):
                continue
            record = {
                field: _optional_str(item, field) for field in BALANCE_ALLOWED_OBSERVATION_FIELDS
            }
            record["ccy"] = _optional_str(item, "ccy")
            observed.append(record)
    return observed


def _surface_record(
    *,
    surface: str,
    observed_at: str,
    http_status: int,
    body_bytes: bytes,
    payload: Mapping[str, Any],
    genesis_id: str,
    genesis_as_of: str,
    d4_identity_digest: str,
    d4_instance_digest: str,
    d5_binding_id: str,
) -> dict[str, Any]:
    rows = _extract_rows(payload)
    return {
        "request_surface": surface,
        "observed_at": observed_at,
        "http_status": str(http_status),
        "venue_code": str(payload.get("code") or ""),
        "venue_msg": str(payload.get("msg") or ""),
        "payload_digest": _sha256_bytes(body_bytes),
        "row_count": str(len(rows)),
        "empty_result_means_query_returned_no_rows_only": TRUE_TOKEN,
        "empty_result_proves_zero_events": FALSE_TOKEN,
        "pagination_exhaustion_proves_completeness": FALSE_TOKEN,
        "pagination_status": _pagination_status(row_count=len(rows)),
        "page_cursor_after": "",
        "page_cursor_before": "",
        "provenance": "FRESH_AUTHENTICATED_PACKAGE_1_OBSERVATION",
        "genesis_id": genesis_id,
        "genesis_as_of": genesis_as_of,
        "d4_identity_digest": d4_identity_digest,
        "d4_instance_digest": d4_instance_digest,
        "d5_binding_id": d5_binding_id,
        "raw_eq_source_authority": FALSE_TOKEN,
        "authority_effect": "NONE",
        "rows": rows,
    }


def _build_client_v1(*, transport: LiveCanaryTransportV1) -> LiveCanaryHttpClientV1:
    return LiveCanaryHttpClientV1(
        rest_base=REUSED_REST_BASE,
        rest_host=REUSED_BINDING_REST_HOST,
        transport=transport,
        max_request_count=MAX_NETWORK_REQUEST_COUNT,
        max_retries=DEFAULT_MAX_RETRIES,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )


def _one_authorized_get_v1(
    *,
    client: LiveCanaryHttpClientV1,
    handle: Any,
    endpoint: str,
) -> dict[str, Any]:
    if endpoint not in AUTHORIZED_ENDPOINTS:
        raise Package1ObservationExecutionError(f"UNAUTHORIZED_GET_SURFACE:{endpoint}")
    if endpoint in FORBIDDEN_ENDPOINTS:
        raise Package1ObservationExecutionError("MUTATION_ENDPOINT_FORBIDDEN")
    url = f"{REUSED_REST_BASE}{endpoint}"
    parsed = urlparse(url)
    if parsed.path != endpoint or parsed.query:
        raise Package1ObservationExecutionError("SIGNED_REQUEST_TARGET_MISMATCH")
    if parsed.hostname != AUTHORIZED_HOST:
        raise Package1ObservationExecutionError("HOST_MISMATCH")
    auth_headers: dict[str, str] = {}
    try:
        if handle is not None:
            auth_headers = _fail_closed_credential_unavailable_v1(
                handle=handle, url=url, method="GET"
            )
            auth_headers["User-Agent"] = USER_AGENT_CANARY
        observed_at = _utc_now_z()
        try:
            response = client.get(endpoint=endpoint, headers=auth_headers or None)
        except LiveCanaryHttpError as exc:
            raise Package1ObservationExecutionError(
                f"PACKAGE_1_GET_FAILED:{endpoint}:{exc}"
            ) from exc
        if response.method != "GET":
            raise Package1ObservationExecutionError("NON_GET_RESPONSE")
        if bool(response.redirect_followed):
            raise Package1ObservationExecutionError("REDIRECT_FOLLOWED")
        return {
            "endpoint": endpoint,
            "observed_at": observed_at,
            "http_status": int(response.status_code),
            "body_bytes": bytes(response.body_bytes),
        }
    finally:
        auth_headers.clear()


def _parse_payload_v1(*, body_bytes: bytes, require_json: bool) -> tuple[dict[str, Any], str]:
    try:
        return parse_json_object_v1(body_bytes), "JSON_OBJECT"
    except LiveCanaryHttpError as exc:
        if require_json:
            raise Package1ObservationExecutionError(str(exc)) from exc
        return {}, "MALFORMED_NON_JSON"


def _assert_get_counters_v1(*, client: LiveCanaryHttpClientV1) -> dict[str, Any]:
    counters = client.counters.to_dict()
    if int(counters.get("GET_REQUEST_COUNT", 0) or 0) != 5:
        raise Package1ObservationExecutionError("GET_COUNT_NOT_FIVE")
    if int(counters.get("REQUEST_COUNT", 0) or 0) != 5:
        raise Package1ObservationExecutionError("REQUEST_COUNT_NOT_FIVE")
    if int(counters.get("WRITE_REQUEST_COUNT", 0) or 0) != 0:
        raise Package1ObservationExecutionError("WRITE_REQUEST_DETECTED")
    if int(counters.get("TRANSFER_REQUEST_COUNT", 0) or 0) != 0:
        raise Package1ObservationExecutionError("TRANSFER_REQUEST_DETECTED")
    if int(counters.get("ORDER_REQUEST_COUNT", 0) or 0) != 0:
        raise Package1ObservationExecutionError("ORDER_REQUEST_DETECTED")
    if list(client.counters.endpoints_used) != list(AUTHORIZED_ENDPOINTS):
        raise Package1ObservationExecutionError("ENDPOINT_SET_MISMATCH")
    if list(client.counters.methods_used) != ["GET"] * 5:
        raise Package1ObservationExecutionError("NON_GET_METHOD_DETECTED")
    return counters


def _open_transport_v1(
    *,
    vault_file: Path | str | None,
    transport: LiveCanaryTransportV1 | None,
) -> tuple[LiveCanaryTransportV1, Any, bool]:
    if REUSED_BINDING_REST_HOST != AUTHORIZED_HOST:
        raise Package1ObservationExecutionError("HOST_MISMATCH")
    productive = transport is None
    if productive:
        if vault_file is None or not str(vault_file).strip():
            raise Package1ObservationExecutionError("VAULT_FILE_REQUIRED")
        transport = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
    if isinstance(transport, UrllibLiveCanaryTransportV1) and not bool(
        getattr(transport, "wire_send_enabled", False)
    ):
        raise Package1ObservationExecutionError("PRODUCTIVE_WIRE_DISABLED")
    handle = None
    if productive:
        backend = _fail_closed_credential_unavailable_v1(vault_file=vault_file)
        handle = _fail_closed_credential_unavailable_v1(
            secret_reference=REQUIRED_SECRETREF_URI,
            vault_backend=backend,
            credential_class=REQUIRED_CREDENTIAL_CLASS,
        )
    if transport is None:
        raise Package1ObservationExecutionError("TRANSPORT_ABSENT")
    return transport, handle, productive


def execute_package_1_observation_s1_s5_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    genesis_store_root: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    observation_as_of: str | None = None,
) -> Package1ObservationExecutionResultV1:
    _require_owner_go(owner_go)
    genesis_root = preflight_package_1_observation_s0_v1(
        origin_main_sha=origin_main_sha,
        genesis_store_root=genesis_store_root,
    )
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    as_of = observation_as_of or _utc_now_z()
    opened_transport, handle, _productive = _open_transport_v1(
        vault_file=vault_file, transport=transport
    )
    client = _build_client_v1(transport=opened_transport)
    captures: list[dict[str, Any]] = []
    try:
        config_cap = _one_authorized_get_v1(
            client=client, handle=handle, endpoint=ENDPOINT_ACCOUNT_CONFIG
        )
        captures.append(config_cap)
        if int(config_cap["http_status"]) != 200:
            raise Package1ObservationExecutionError(
                f"S1_HTTP_STATUS_NOT_200:{config_cap['http_status']}"
            )
        config_payload, _parse_status = _parse_payload_v1(
            body_bytes=bytes(config_cap["body_bytes"]), require_json=True
        )
        try:
            observed = extract_account_config_uid_recapture_facts_v1(config_payload)
        except D4GenesisFreshAccountConfigBootstrapError as exc:
            raise Package1ObservationExecutionError(str(exc)) from exc
        if observed.observed_uid == "":
            raise Package1ObservationExecutionError("S1_UID_ABSENT")
        account_mode = ""
        config_rows = _extract_rows(config_payload)
        if config_rows and isinstance(config_rows[0], Mapping):
            account_mode = _optional_str(config_rows[0], "acctLv") or _optional_str(
                config_rows[0], "type"
            )
        if account_mode == "":
            raise Package1ObservationExecutionError("S1_ACCOUNT_MODE_ABSENT")
        if observed.observed_settle_ccy == "":
            raise Package1ObservationExecutionError("S1_SETTLE_CCY_ABSENT")
        if observed.observed_main_uid == "":
            raise Package1ObservationExecutionError("S1_MAIN_UID_ABSENT")
        try:
            corroboration = corroborate_d4_identity_from_account_config_observation_v1(
                bound_account_identity=d4.bound_account_identity,
                bound_settlement_currency=d4.settlement_currency,
                observed_uid=observed.observed_uid,
                observed_main_uid=observed.observed_main_uid,
                observed_settle_ccy=observed.observed_settle_ccy,
                observed_account_mode=account_mode,
                identity_provenance_class=d4.identity_provenance_class,
            )
        except PathBClassCPackage1TradingAccountObservationRulesContractError as exc:
            raise Package1ObservationExecutionError(str(exc)) from exc
        if corroboration != D4_CORROBORATED:
            raise Package1ObservationExecutionError("D4_CORROBORATION_FAILED")
        for endpoint in AUTHORIZED_ENDPOINTS[1:]:
            captures.append(_one_authorized_get_v1(client=client, handle=handle, endpoint=endpoint))
        _assert_get_counters_v1(client=client)
    finally:
        if handle is not None:
            _fail_closed_credential_unavailable_v1(handle)
    by_endpoint = {str(item["endpoint"]): item for item in captures}
    surfaces: dict[str, dict[str, Any]] = {}
    for endpoint in AUTHORIZED_ENDPOINTS:
        cap = by_endpoint[endpoint]
        payload, parse_status = _parse_payload_v1(
            body_bytes=bytes(cap["body_bytes"]),
            require_json=endpoint == ENDPOINT_ACCOUNT_CONFIG,
        )
        record = _surface_record(
            surface=f"GET_{endpoint}",
            observed_at=str(cap["observed_at"]),
            http_status=int(cap["http_status"]),
            body_bytes=bytes(cap["body_bytes"]),
            payload=payload,
            genesis_id=EXPECTED_GENESIS_ID,
            genesis_as_of=EXPECTED_GENESIS_AS_OF,
            d4_identity_digest=d4.identity_digest,
            d4_instance_digest=d4.instance_digest,
            d5_binding_id=d5.binding_id,
        )
        record["parse_status"] = parse_status
        surfaces[endpoint] = record
    bills_ids = _bill_ids(list(surfaces[ENDPOINT_ACCOUNT_BILLS]["rows"]))
    archive_ids = _bill_ids(list(surfaces[ENDPOINT_ACCOUNT_BILLS_ARCHIVE]["rows"]))
    overlap_status = _overlap_status(bills_ids=bills_ids, archive_ids=archive_ids)
    balance_fields = _balance_reconciliation_fields(
        list(surfaces[ENDPOINT_ACCOUNT_BALANCE]["rows"])
    )
    pack_root = Path(evidence_root) / _folder_from_as_of(as_of)
    pack_root.mkdir(parents=True, exist_ok=True)
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "GENESIS_ID": EXPECTED_GENESIS_ID,
        "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        "OBSERVATION_AS_OF": as_of,
        "S1_ACCOUNT_CONFIG_GET": TRUE_TOKEN,
        "S2_ACCOUNT_BALANCE_GET": TRUE_TOKEN,
        "S3_ACCOUNT_SUBTYPES_GET": TRUE_TOKEN,
        "S4_ACCOUNT_BILLS_GET": TRUE_TOKEN,
        "S4_ACCOUNT_BILLS_ARCHIVE_GET": TRUE_TOKEN,
        "AUTHORIZED_GET_SURFACE_COUNT": "5",
        "UNAUTHORIZED_GET_SURFACE_COUNT": "0",
        "NETWORK_POST_PERFORMED": FALSE_TOKEN,
        "D4_CORROBORATION_RESULT": corroboration,
        "D4_IDENTITY_MINTED": FALSE_TOKEN,
        "RAW_EQ_SOURCE_AUTHORITY": FALSE_TOKEN,
        "BILLS_ARCHIVE_OVERLAP_STATUS": overlap_status,
        "BILLS_BILL_ID_COUNT": str(len(bills_ids)),
        "BILLS_ARCHIVE_BILL_ID_COUNT": str(len(archive_ids)),
        "BILLS_ARCHIVE_OVERLAP_COUNT": str(len(bills_ids & archive_ids)),
        "RETENTION_COVERAGE_STATUS": RETENTION_COVERAGE_FAIL_CLOSED,
        "ORDERING_COMPLETENESS_STATUS": ORDERING_COMPLETENESS_FAIL_CLOSED,
        "EMPTY_RESULT_MEANS_QUERY_RETURNED_NO_ROWS_ONLY": TRUE_TOKEN,
        "EMPTY_RESULT_PROVES_ZERO_EVENTS": FALSE_TOKEN,
        "PAGINATION_EXHAUSTION_PROVES_COMPLETENESS": FALSE_TOKEN,
        "F12_STATUS": "UNKNOWN",
        "F13_STATUS": "UNKNOWN",
        "F16_STATUS": "UNKNOWN",
        "F17_STATUS": "UNKNOWN",
        "F18_STATUS": "UNKNOWN",
        "KIND_SET_RESOLVED": FALSE_TOKEN,
        "MAPPING_PERSISTED": FALSE_TOKEN,
        "S6_EXECUTED": FALSE_TOKEN,
        "MS2_AUTHORIZED": FALSE_TOKEN,
        "D6_FULLY_CLOSED": FALSE_TOKEN,
        "D7_AUTHORIZED": FALSE_TOKEN,
        "RAW_EVIDENCE_SEALED": TRUE_TOKEN,
        "ATLAS_AUTHORITY": "NONE",
        "AUTHORITY_EFFECT": "NONE",
        "BOUND_TD_MODE": d4.bound_td_mode,
        "D4_IDENTITY_DIGEST": d4.identity_digest,
        "D4_INSTANCE_DIGEST": d4.instance_digest,
        "D5_BINDING_ID": d5.binding_id,
        "D4_RUNTIME_INSTANCE_PERSISTED": TRUE_TOKEN,
        "D5_RUNTIME_INSTANCE_PERSISTED": TRUE_TOKEN,
        "OBSERVATION_S0_PREREQUISITES_SATISFIED": TRUE_TOKEN,
    }
    _persist_json(path=pack_root / "claims.json", payload=claims)
    _persist_json(
        path=pack_root / "s1_account_config_observation_v1.json",
        payload={
            **surfaces[ENDPOINT_ACCOUNT_CONFIG],
            "observed_uid": observed.observed_uid,
            "observed_main_uid": observed.observed_main_uid,
            "observed_uid_present": TRUE_TOKEN,
            "observed_main_uid_present": TRUE_TOKEN,
            "observed_account_mode": account_mode,
            "observed_settle_ccy": observed.observed_settle_ccy,
            "d4_corroboration_result": corroboration,
            "d4_identity_minted": FALSE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "s2_account_balance_observation_v1.json",
        payload={
            **surfaces[ENDPOINT_ACCOUNT_BALANCE],
            "reconciliation_or_embedding_fields": balance_fields,
            "raw_eq_source_authority": FALSE_TOKEN,
            "c01_rehabilitation": "FORBIDDEN",
        },
    )
    _persist_json(
        path=pack_root / "s3_account_subtypes_observation_v1.json",
        payload=surfaces[ENDPOINT_ACCOUNT_SUBTYPES],
    )
    _persist_json(
        path=pack_root / "s4_account_bills_observation_v1.json",
        payload=surfaces[ENDPOINT_ACCOUNT_BILLS],
    )
    _persist_json(
        path=pack_root / "s4_account_bills_archive_observation_v1.json",
        payload=surfaces[ENDPOINT_ACCOUNT_BILLS_ARCHIVE],
    )
    _persist_json(
        path=pack_root / "s4_bills_pair_overlap_v1.json",
        payload={
            "bills_archive_overlap_status": overlap_status,
            "bills_bill_id_count": str(len(bills_ids)),
            "bills_archive_bill_id_count": str(len(archive_ids)),
            "overlap_count": str(len(bills_ids & archive_ids)),
            "retention_coverage_status": RETENTION_COVERAGE_FAIL_CLOSED,
            "ordering_completeness_status": ORDERING_COMPLETENESS_FAIL_CLOSED,
            "pagination_exhaustion_proves_completeness": FALSE_TOKEN,
            "empty_result_proves_zero_events": FALSE_TOKEN,
            "account_bills_atlas_authority": "NONE",
            "account_bills_remains_current_noncanonical": TRUE_TOKEN,
        },
    )
    _persist_json(
        path=pack_root / "s5_raw_evidence_seal_v1.json",
        payload={
            "raw_evidence_sealed": TRUE_TOKEN,
            "authorized_get_surface_count": "5",
            "unauthorized_get_surface_count": "0",
            "network_post_performed": FALSE_TOKEN,
            "genesis_id": EXPECTED_GENESIS_ID,
            "genesis_as_of": EXPECTED_GENESIS_AS_OF,
            "d4_identity_digest": d4.identity_digest,
            "d4_instance_digest": d4.instance_digest,
            "d5_binding_id": d5.binding_id,
            "payload_digests": {
                endpoint: surfaces[endpoint]["payload_digest"] for endpoint in AUTHORIZED_ENDPOINTS
            },
        },
    )
    manifest = persist_manifest_sha256_v1(store_root=pack_root)
    return Package1ObservationExecutionResultV1(
        genesis_id=EXPECTED_GENESIS_ID,
        genesis_as_of=EXPECTED_GENESIS_AS_OF,
        observation_as_of=as_of,
        store_root=str(pack_root),
        s1_account_config_get=TRUE_TOKEN,
        s2_account_balance_get=TRUE_TOKEN,
        s3_account_subtypes_get=TRUE_TOKEN,
        s4_account_bills_get=TRUE_TOKEN,
        s4_account_bills_archive_get=TRUE_TOKEN,
        authorized_get_surface_count="5",
        unauthorized_get_surface_count="0",
        network_post_performed=FALSE_TOKEN,
        d4_corroboration_result=corroboration,
        d4_identity_minted=FALSE_TOKEN,
        raw_eq_source_authority=FALSE_TOKEN,
        bills_archive_overlap_status=overlap_status,
        retention_coverage_status=RETENTION_COVERAGE_FAIL_CLOSED,
        ordering_completeness_status=ORDERING_COMPLETENESS_FAIL_CLOSED,
        raw_evidence_sealed=TRUE_TOKEN,
        evidence_manifest=str(manifest),
        kind_set_resolved=FALSE_TOKEN,
        mapping_persisted=FALSE_TOKEN,
        mapping_s6_executed=FALSE_TOKEN,
        ms2_authorized=FALSE_TOKEN,
        d6_fully_closed=FALSE_TOKEN,
        d7_authorized=FALSE_TOKEN,
    )
