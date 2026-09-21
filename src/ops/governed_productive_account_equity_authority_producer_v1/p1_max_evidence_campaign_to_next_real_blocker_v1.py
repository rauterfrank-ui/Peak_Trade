"""P1 max evidence campaign: bounded read-only GET + offline witness adjudication.

Consumes Owner-GO FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1.
Reuses #6666 witness foundation and re-evaluates #6665 closeout. One fresh
unscoped interest-accrued GET maximum; zero retries; no pagination expansion.
Does not ratify kind sets. AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.full_core_live_path_composition_root_v1.checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1BoundVenueAuthHandleV1,
    bind_already_held_k1_venue_auth_session_v1,
    build_k1_okx_venue_auth_headers_v1,
    release_k1_venue_auth_session_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY as DAG_PIN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.checkpoint_observation_window_binding_contract_v1 import (
    load_checkpoint_observation_window_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    AUTHORIZED_PRODUCTIVE_EVENT_SOURCE_SEAM_PRESENT,
    C17_CREATED,
    COMPLETE_EVENT_STREAM_PROVEN,
    D6_FULLY_CLOSED,
    D7_AUTHORIZED,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    KIND_SET_RESOLVED,
    MS2_AUTHORIZED,
    OBSERVATION_NETWORK_GET_AUTHORIZED,
    PAGINATION_EXHAUSTION_PROVES_COMPLETENESS,
    PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED,
    RAW_EQ_SOURCE_AUTHORITY,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_affecting_event_taxonomy_contract_v1 import (
    RATIFIED_CLASSIFIED_KIND_SET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_completeness_witness_foundation_v1 import (
    DERIVED_PROVENANCE,
    DERIVED_TIME_DOMAIN,
    ROOT_CURRENCY_DOMAIN,
    ROOT_EVENT_ORDERING,
    ROOT_LIABILITY_EVENT_CLASS,
    ROOT_OBSERVATION_FRESHNESS,
    ROOT_PAGINATION,
    ROOT_RESTART_DURABILITY,
    evaluate_sealed_p1_completeness_witness_bundle_v1,
    first_real_blocker_from_bundle_v1,
    root_by_id_v1,
    witness_bundle_to_mapping_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p1_negative_completeness_closeout_contract_v1 import (
    evaluate_sealed_interest_accrued_p1_closeout_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_observation_s0_runtime_binding_gate_v1 import (
    resolve_canonical_d4_d5_genesis_runtime_store_root_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.p01_overlap_with_u04_u05_contract_v1 import (
    P01_U05_OVERLAP_RESOLVED_STATUS,
    P01_U05_OVERLAP_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    SELECTED_ENDPOINT_PATH,
    SELECTED_SURFACE_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
    AUTHORIZED_QUERY as CD_AUTHORIZED_QUERY,
    CANONICAL_PACK_RELPATH as CANONICAL_CD_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_p1_futures_bound_interest_accrued_usdc_scoped_get_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_USDC_P1_PACK_RELPATH,
)
from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.execute_v1 import (
    secretref_identity_without_values_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpError,
    LiveCanaryHttpRequestV1,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)

WP_ID = "FULL_CORE_P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1"
OWNER_GO = WP_ID
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})
EXPECTED_ORIGIN_MAIN_SHA = "2d90c4b88555c1a19dd41176dec08f18a0a50e35"
CANONICAL_PACK_RELPATH = "evidence/ops/full_core_p1_max_evidence_campaign_to_next_real_blocker_v1"
SCHEMA_CLASS = "P1_MAX_EVIDENCE_CAMPAIGN_TO_NEXT_REAL_BLOCKER_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
HTTP_METHOD = "GET"
AUTHORIZED_HOST = "eea.okx.com"
AUTHORIZED_PATH = SELECTED_ENDPOINT_PATH
AUTHORIZED_QUERY = CD_AUTHORIZED_QUERY
AUTHORIZED_ENDPOINT = f"{AUTHORIZED_PATH}?{AUTHORIZED_QUERY}"
AUTHORIZED_URL = f"https://{AUTHORIZED_HOST}{AUTHORIZED_ENDPOINT}"
REQUEST_SURFACE = SELECTED_SURFACE_ID
MAX_AUTHORIZED_GET_COUNT = 1
MAX_PAGES = 1
RETRY_COUNT = 0
TIMEOUT_SECONDS = 15.0
QUERY_LIMIT = "100"
PAGINATION_MODEL = "limit_only_no_cursor_in_binding"
DEFAULT_VAULT_RELATIVE = (
    ".ops_local/section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
)
_REPO_ROOT = Path(__file__).resolve().parents[3]


class P1MaxEvidenceCampaignError(ValueError):
    """Fail-closed P1 max evidence campaign violation."""


@dataclass(frozen=True)
class P1MaxEvidenceCampaignResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    authorized_get_count: str
    actual_get_count: str
    network_used: str
    get_surfaces: str
    raw_evidence_persisted: str
    witness_bundle_digest: str
    p1_status_after: str
    max_campaign_closeout_reached: str
    first_real_blocker: str
    blocker_class: str
    missing_fact_or_authority: str
    governance_required_next: str
    network_required_next: str
    runtime_required_next: str
    restart_required_next: str
    closeout_decision: str


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


def _persist_raw_bytes(*, path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(body)
    tmp.replace(path)


def _load_json_object(*, path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise P1MaxEvidenceCampaignError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def _assert_standing_pins() -> None:
    if U05_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise P1MaxEvidenceCampaignError("U05_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if U06_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise P1MaxEvidenceCampaignError("U06_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if RESIDUAL_KIND_DECISION != DECISION_REMAIN_UNKNOWN:
        raise P1MaxEvidenceCampaignError("RESIDUAL_KIND_DECISION_NOT_REMAIN_UNKNOWN")
    if KIND_SET_RESOLVED is not False:
        raise P1MaxEvidenceCampaignError("KIND_SET_RESOLVED_NOT_FALSE")
    if RATIFIED_CLASSIFIED_KIND_SET:
        raise P1MaxEvidenceCampaignError("KIND_SET_MUST_REMAIN_EMPTY")
    if PAGINATION_EXHAUSTION_PROVES_QUERY_TRAVERSAL_COMPLETED is not True:
        raise P1MaxEvidenceCampaignError("PAGINATION_TRAVERSAL_PIN_DRIFT")
    if PAGINATION_EXHAUSTION_PROVES_COMPLETENESS is not False:
        raise P1MaxEvidenceCampaignError("PAGINATION_COMPLETENESS_LAW_DRIFT")
    if DAG_PIN != "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING":
        raise P1MaxEvidenceCampaignError("DAG_PIN_DRIFT")
    if P01_U05_OVERLAP_STATE != "UNRESOLVED":
        raise P1MaxEvidenceCampaignError("P01_U05_OVERLAP_STATE_DRIFT")
    if P01_U05_OVERLAP_RESOLVED_STATUS != FALSE_TOKEN:
        raise P1MaxEvidenceCampaignError("P01_U05_OVERLAP_MUST_REMAIN_UNRESOLVED")
    if EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is not False:
        raise P1MaxEvidenceCampaignError("STANDING_EVENT_GET_UNAUTHORIZED")
    if OBSERVATION_NETWORK_GET_AUTHORIZED is not False:
        raise P1MaxEvidenceCampaignError("STANDING_OBSERVATION_GET_UNAUTHORIZED")


def _rows_from_body(*, body: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    data = body.get("data")
    if not isinstance(data, list):
        return []
    rows: list[Mapping[str, Any]] = []
    for item in data:
        if isinstance(item, Mapping):
            rows.append(item)
    return rows


def _distinct_loan_ccy(rows: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for row in rows:
        ccy = str(row.get("ccy") or "").strip()
        if ccy and ccy not in seen:
            seen.add(ccy)
            ordered.append(ccy)
    return tuple(ordered)


def build_p1_campaign_witness_adjudication_v1(
    *,
    cd_row_count: int,
    usdc_row_count: int,
    fresh_row_count: int,
    fresh_request_utc: str,
    d5_window_start: str,
    d5_window_end: str,
    d5_event_completeness_from_window: str,
) -> dict[str, Any]:
    """Offline witness adjudication for campaign pack (fail-closed)."""
    combined_rows = cd_row_count + usdc_row_count + fresh_row_count
    limit = int(QUERY_LIMIT)

    currency_exhaustion = FALSE_TOKEN
    currency_missing = (
        "CLOSED_WORLD_APPLICABLE_MARKET_LOAN_CCY_SET_NOT_BOUND;"
        "OPTIONAL_CCY_FILTER_WITHOUT_POSITIVE_DOMAIN_COVERAGE"
    )
    if fresh_row_count > 0 and fresh_row_count < limit:
        currency_missing = (
            "PARTIAL_ROW_CCY_OBSERVED_BUT_APPLICABLE_DOMAIN_NOT_CLOSED;"
            "REQUIRES_VENUE_CONTRACT_ENUM_OR_SCOPED_CCY_EXHAUSTION"
        )
    elif combined_rows == 0:
        currency_missing = (
            "ZERO_ROWS_ACROSS_SEALED_AND_CAMPAIGN_GET;CANNOT_EXHAUST_APPLICABLE_LOAN_CCY_DOMAIN"
        )

    pagination_traversal = FALSE_TOKEN
    pagination_detail = "zero_rows_not_exhaustion_proof"
    if fresh_row_count > 0 and fresh_row_count < limit:
        pagination_traversal = TRUE_TOKEN
        pagination_detail = "limit_only_single_page_row_count_below_limit"
    elif fresh_row_count >= limit:
        pagination_detail = "limit_saturated_cursor_not_in_binding_cannot_prove_exhaustion"

    ordering_proven = FALSE_TOKEN
    ordering_detail = "venue_ordering_semantics_not_bound_for_interest_accrued"
    if fresh_row_count >= 2:
        ordering_detail = "multiple_rows_without_ratified_ordering_witness"

    freshness_proven = FALSE_TOKEN
    freshness_detail = "d5_checkpoint_freshness_witness_not_materialized"
    if fresh_request_utc and d5_window_start and d5_window_end:
        if d5_window_start == d5_window_end:
            freshness_detail = "genesis_point_window_not_freshness_complete"
        elif d5_event_completeness_from_window == TRUE_TOKEN:
            freshness_detail = "event_completeness_from_window_must_remain_false"
        else:
            freshness_detail = "observation_outside_or_unbound_to_d5_checkpoint_window"

    time_domain_proven = FALSE_TOKEN
    if _as_bool_token(pagination_traversal) and fresh_row_count > 0:
        time_domain_proven = FALSE_TOKEN
    time_detail = "venue_default_past_year_not_traversed_without_exhaustion"

    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_PROVEN": currency_exhaustion,
        "CURRENCY_DOMAIN_MISSING_FACT": currency_missing,
        "PAGINATION_QUERY_TRAVERSAL_EXHAUSTION_PROVEN": pagination_traversal,
        "PAGINATION_COMPLETENESS_PROVEN": FALSE_TOKEN,
        "PAGINATION_DETAIL": pagination_detail,
        "PAGINATION_MODEL": PAGINATION_MODEL,
        "EVENT_ORDERING_COMPLETENESS_PROVEN": ordering_proven,
        "EVENT_ORDERING_DETAIL": ordering_detail,
        "D5_CHECKPOINT_FRESHNESS_PROVEN": freshness_proven,
        "D5_FRESHNESS_DETAIL": freshness_detail,
        "TIME_DOMAIN_EXHAUSTION_PROVEN": time_domain_proven,
        "TIME_DOMAIN_DETAIL": time_detail,
        "GOVERNANCE_REQUIRED_FOR_LIABILITY_CLASS": TRUE_TOKEN,
        "RESTART_DURABILITY_PROVEN": FALSE_TOKEN,
        "SEALED_CD_ROW_COUNT": str(cd_row_count),
        "SEALED_USDC_ROW_COUNT": str(usdc_row_count),
        "CAMPAIGN_FRESH_ROW_COUNT": str(fresh_row_count),
        "CAMPAIGN_FRESH_REQUEST_UTC": fresh_request_utc,
    }


def _one_bounded_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    handle: Any | None,
) -> dict[str, Any]:
    request_utc = _utc_now_z()
    url = AUTHORIZED_URL
    headers = {"User-Agent": USER_AGENT_CANARY}
    if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
        headers = build_k1_okx_venue_auth_headers_v1(handle=handle, url=url, method=HTTP_METHOD)
        headers["User-Agent"] = USER_AGENT_CANARY
    request = LiveCanaryHttpRequestV1(
        method=HTTP_METHOD,
        url=url,
        host=AUTHORIZED_HOST,
        endpoint=AUTHORIZED_ENDPOINT,
        headers=headers,
        timeout_seconds=TIMEOUT_SECONDS,
        body_text="",
    )
    response = transport.send(request)
    body_bytes = bytes(response.body_bytes or b"")
    return {
        "request_utc": request_utc,
        "response_utc": _utc_now_z(),
        "http_status": str(int(response.status_code)),
        "body_bytes": body_bytes,
        "venue_code": "",
        "error_class": NONE_TOKEN,
    }


def execute_p1_max_evidence_campaign_to_next_real_blocker_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | str,
    repo_root: Path | str | None = None,
    genesis_store_root: Path | str | None = None,
    vault_file: Path | str | None = None,
    transport: LiveCanaryTransportV1 | None = None,
    persist_as_of: str | None = None,
    skip_network: bool = False,
) -> P1MaxEvidenceCampaignResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise P1MaxEvidenceCampaignError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P1MaxEvidenceCampaignError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_standing_pins()
    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cd_pack = repo / CANONICAL_CD_PACK_RELPATH
    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH / "2026-09-20T233000Z"
    if verify_manifest_sha256_v1(store_root=cd_pack) != 0:
        raise P1MaxEvidenceCampaignError("CD_MANIFEST_MISMATCH")
    if verify_manifest_sha256_v1(store_root=usdc_pack) != 0:
        raise P1MaxEvidenceCampaignError("USDC_P1_MANIFEST_MISMATCH")
    cd_claims = _load_json_object(path=cd_pack / "claims.json")
    usdc_claims = _load_json_object(path=usdc_pack / "claims.json")
    cd_body = _load_json_object(path=cd_pack / "raw_interest_accrued_response_body.json")
    usdc_body = _load_json_object(path=usdc_pack / "raw_interest_accrued_response_body.json")
    cd_rows = len(_rows_from_body(body=cd_body))
    usdc_rows = len(_rows_from_body(body=usdc_body))

    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise P1MaxEvidenceCampaignError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    d5 = load_checkpoint_observation_window_binding_v1(store_root=genesis_root)
    if d4.identity_digest != "00c354f2d247f5a64e33efb31f8be155b8557e847868335ccb15cd4f7ca9d7c4":
        raise P1MaxEvidenceCampaignError("D4_IDENTITY_DIGEST_DRIFT")
    if d5.binding_id != "WIND4D5GENESIS8d3f573ffc0c59b4":
        raise P1MaxEvidenceCampaignError("D5_BINDING_ID_DRIFT")

    as_of = persist_as_of or _utc_now_z()
    store = Path(evidence_root) / _folder_from_as_of(as_of)
    canonical = repo / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    if store.resolve() != canonical.resolve():
        raise P1MaxEvidenceCampaignError("CAMPAIGN_STORE_NOT_CANONICAL_PATH")
    store.mkdir(parents=True, exist_ok=True)

    network_used = FALSE_TOKEN
    actual_get_count = 0
    fresh_row_count = 0
    fresh_request_utc = ""
    raw_persisted = FALSE_TOKEN
    raw_sha = ""

    if not skip_network:
        resolved_vault: Path | None = (
            Path(vault_file) if vault_file else repo / DEFAULT_VAULT_RELATIVE
        )
        productive = transport is None
        handle: Any | None = None
        opened: LiveCanaryTransportV1
        if productive:
            if resolved_vault is None or not resolved_vault.is_file():
                raise P1MaxEvidenceCampaignError("VAULT_FILE_REQUIRED")
            secretref_identity_without_values_v1(vault_file=resolved_vault)
            opened = UrllibLiveCanaryTransportV1(wire_send_enabled=True)
            key, secret, phrase = _ephemeral_vault_fields_v1(vault_file=resolved_vault)
            handle = bind_already_held_k1_venue_auth_session_v1(
                api_key=key, api_secret=secret, passphrase=phrase
            )
        else:
            opened = transport  # type: ignore[assignment]
        try:
            if actual_get_count >= MAX_AUTHORIZED_GET_COUNT:
                raise P1MaxEvidenceCampaignError("GET_BUDGET_EXCEEDED")
            capture = _one_bounded_get_v1(transport=opened, handle=handle)
            actual_get_count = 1
            network_used = TRUE_TOKEN
            fresh_request_utc = str(capture["request_utc"])
            body_bytes = bytes(capture["body_bytes"])
            raw_sha = _sha256_bytes(body_bytes)
            _persist_raw_bytes(
                path=store / "raw_interest_accrued_response_body.json", body=body_bytes
            )
            _persist_json(
                path=store / "raw_http_capture_v1.json",
                payload={
                    "layer": "FORENSIC_RAW_EVIDENCE",
                    "method": HTTP_METHOD,
                    "host": AUTHORIZED_HOST,
                    "endpoint": AUTHORIZED_PATH,
                    "query": AUTHORIZED_QUERY,
                    "url": AUTHORIZED_URL,
                    "request_surface": REQUEST_SURFACE,
                    "request_utc": fresh_request_utc,
                    "response_utc": capture["response_utc"],
                    "http_status": capture["http_status"],
                    "raw_body_sha256": raw_sha,
                    "account_identity_digest": d4.identity_digest,
                },
            )
            raw_persisted = TRUE_TOKEN
            parsed = parse_json_object_v1(body_bytes)
            fresh_row_count = len(_rows_from_body(body=parsed))
            if str(parsed.get("code") or "") != "0":
                raise P1MaxEvidenceCampaignError("VENUE_CODE_NON_ZERO")
        finally:
            if isinstance(handle, FullCoreK1BoundVenueAuthHandleV1):
                release_k1_venue_auth_session_v1(handle)

    witness_adjudication = build_p1_campaign_witness_adjudication_v1(
        cd_row_count=cd_rows,
        usdc_row_count=usdc_rows,
        fresh_row_count=fresh_row_count,
        fresh_request_utc=fresh_request_utc,
        d5_window_start=str(d5.checkpoint_window_start or ""),
        d5_window_end=str(d5.checkpoint_window_end or ""),
        d5_event_completeness_from_window=str(d5.event_completeness_from_window or FALSE_TOKEN),
    )
    _persist_json(
        path=store / "p1_campaign_witness_adjudication_v1.json", payload=witness_adjudication
    )
    _persist_json(
        path=store / "campaign_surface_binding_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "HTTP_METHOD": HTTP_METHOD,
            "AUTHORIZED_QUERY": AUTHORIZED_QUERY,
            "MAX_AUTHORIZED_GET_COUNT": str(MAX_AUTHORIZED_GET_COUNT),
            "MAX_PAGES": str(MAX_PAGES),
            "RETRY_COUNT": str(RETRY_COUNT),
            "ACCOUNT_IDENTITY_DIGEST": d4.identity_digest,
            "VENUE": d4.bound_venue_identity,
            "SETTLEMENT_CCY": str(d4.settlement_currency or ""),
            "GET_SURFACE": REQUEST_SURFACE,
        },
    )
    _persist_json(
        path=store / "claims.json",
        payload={
            "SCHEMA_CLASS": SCHEMA_CLASS,
            "CONTRACT_VERSION": CONTRACT_VERSION,
            "WP_ID": WP_ID,
            "AUTHORITY_EFFECT": AUTHORITY_EFFECT,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "PERSIST_AS_OF": as_of,
            "NETWORK_USED": network_used,
            "AUTHORIZED_GET_COUNT": str(MAX_AUTHORIZED_GET_COUNT),
            "ACTUAL_GET_COUNT": str(actual_get_count),
            "RAW_EVIDENCE_PERSISTED": raw_persisted,
            "RAW_EVIDENCE_SHA256": raw_sha,
            "CD_PACK_CONSUMED": str(cd_pack.relative_to(repo)),
            "USDC_P1_PACK_CONSUMED": str(usdc_pack.relative_to(repo)),
            "GENESIS_ID": EXPECTED_GENESIS_ID,
            "GENESIS_AS_OF": EXPECTED_GENESIS_AS_OF,
        },
    )
    persist_manifest_sha256_v1(store_root=store)

    bundle = evaluate_sealed_p1_completeness_witness_bundle_v1(
        repo_root=repo, bound_origin_main_sha=origin_main_sha
    )
    closeout = evaluate_sealed_interest_accrued_p1_closeout_v1(repo_root=repo)
    blocker_id, blocker_class, missing = first_real_blocker_from_bundle_v1(bundle)
    currency = root_by_id_v1(bundle, ROOT_CURRENCY_DOMAIN)
    liability = root_by_id_v1(bundle, ROOT_LIABILITY_EVENT_CLASS)
    pagination = root_by_id_v1(bundle, ROOT_PAGINATION)
    ordering = root_by_id_v1(bundle, ROOT_EVENT_ORDERING)
    freshness = root_by_id_v1(bundle, ROOT_OBSERVATION_FRESHNESS)
    restart = root_by_id_v1(bundle, ROOT_RESTART_DURABILITY)

    _persist_json(
        path=store / "p1_campaign_closeout_report_v1.json",
        payload={
            "WP_ID": WP_ID,
            "ORIGIN_MAIN_SHA": origin_main_sha,
            "WITNESS_BUNDLE": witness_bundle_to_mapping_v1(bundle),
            "CLOSEOUT_DECISION": closeout.closeout_decision,
            "P1_STATUS_AFTER": closeout.p1_status_after,
            "FIRST_REAL_BLOCKER": blocker_id,
            "BLOCKER_CLASS": blocker_class,
            "MISSING_FACT_OR_AUTHORITY": missing,
            "ROOTS_PROVEN": {
                ROOT_CURRENCY_DOMAIN: currency.complete,
                ROOT_LIABILITY_EVENT_CLASS: liability.complete,
                ROOT_PAGINATION: pagination.complete,
                ROOT_EVENT_ORDERING: ordering.complete,
                ROOT_OBSERVATION_FRESHNESS: freshness.complete,
                ROOT_RESTART_DURABILITY: restart.complete,
                DERIVED_TIME_DOMAIN: bundle.time_domain.complete,
                DERIVED_PROVENANCE: bundle.provenance.complete,
            },
        },
    )

    persist_manifest_sha256_v1(store_root=store)
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise P1MaxEvidenceCampaignError("MANIFEST_PERSIST_FAIL")

    return P1MaxEvidenceCampaignResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=as_of,
        store_root=str(store),
        authorized_get_count=str(MAX_AUTHORIZED_GET_COUNT),
        actual_get_count=str(actual_get_count),
        network_used=network_used,
        get_surfaces=REQUEST_SURFACE,
        raw_evidence_persisted=raw_persisted,
        witness_bundle_digest=witness_bundle_to_mapping_v1(bundle).get("WITNESS_BUNDLE_DIGEST", ""),
        p1_status_after=closeout.p1_status_after,
        max_campaign_closeout_reached=TRUE_TOKEN,
        first_real_blocker=blocker_id,
        blocker_class=blocker_class,
        missing_fact_or_authority=missing,
        governance_required_next=TRUE_TOKEN if liability.governance_required else FALSE_TOKEN,
        network_required_next=TRUE_TOKEN if currency.network_required else FALSE_TOKEN,
        runtime_required_next=TRUE_TOKEN if freshness.runtime_required else FALSE_TOKEN,
        restart_required_next=TRUE_TOKEN if restart.restart_required else FALSE_TOKEN,
        closeout_decision=closeout.closeout_decision,
    )


def _ephemeral_vault_fields_v1(*, vault_file: Path) -> tuple[str, str, str]:
    payload = json.loads(vault_file.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise P1MaxEvidenceCampaignError("VAULT_NOT_OBJECT")
    if REQUIRED_SECRETREF_URI not in payload:
        raise P1MaxEvidenceCampaignError("SECRETREF_URI_UNBOUND")
    raw = payload[REQUIRED_SECRETREF_URI]
    material = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(material, Mapping):
        raise P1MaxEvidenceCampaignError("SECRETREF_MATERIAL_NOT_OBJECT")
    key = str(material.get("api_key") or "").strip()
    secret = str(material.get("api_secret") or "").strip()
    phrase = str(material.get("passphrase") or "").strip()
    if not key or not secret or not phrase:
        raise P1MaxEvidenceCampaignError("CREDENTIAL_FIELDS_INCOMPLETE")
    return key, secret, phrase


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORITY_EFFECT",
    "CANONICAL_PACK_RELPATH",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "MAX_AUTHORIZED_GET_COUNT",
    "OWNER_GO",
    "P1MaxEvidenceCampaignError",
    "P1MaxEvidenceCampaignResultV1",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_campaign_witness_adjudication_v1",
    "execute_p1_max_evidence_campaign_to_next_real_blocker_v1",
]

CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T020000Z"
