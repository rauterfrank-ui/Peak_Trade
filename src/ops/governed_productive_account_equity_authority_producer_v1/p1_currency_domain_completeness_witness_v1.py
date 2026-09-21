"""P1 currency-domain completeness witness via bounded interest-limits GET.

Consumes Owner-GO FULL_CORE_P1_CURRENCY_DOMAIN_BLOCKER_MAX_IMPLEMENTATION_TO_
NEXT_REAL_BLOCKER_V1. One read-only GET /api/v5/account/interest-limits?type=2
binds closed-world applicable market-loan ccy set; composes with sealed
interest-accrued zero-row packs for exhaustion. Does not ratify kind sets.
AUTHORITY_EFFECT=NONE.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
import re
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
from src.ops.governed_productive_account_equity_authority_producer_v1.bound_account_identity_runtime_binding_v1 import (
    load_bound_account_identity_runtime_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_rebaseline_contract_v1 import (
    EXPECTED_GENESIS_AS_OF,
    EXPECTED_GENESIS_ID,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    LOAN_TYPE_MARKET,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_primary_proof_bound_interest_accrued_get_acquisition_v1 import (
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
    USER_AGENT_CANARY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryTransportV1,
    UrllibLiveCanaryTransportV1,
    parse_json_object_v1,
)

WP_ID = "FULL_CORE_P1_CURRENCY_DOMAIN_BLOCKER_MAX_IMPLEMENTATION_TO_NEXT_REAL_BLOCKER_V1"
OWNER_GO = WP_ID
ALLOWED_OWNER_GOS = frozenset({OWNER_GO, f"OWNER_GO_{OWNER_GO}", "OWNER_GO=true"})
EXPECTED_ORIGIN_MAIN_SHA = "47e14a21e3fcce8e97dd627798b345a224479007"
CANONICAL_PACK_RELPATH = "evidence/ops/full_core_p1_currency_domain_completeness_witness_v1"
CANONICAL_PACK_AS_OF_FOLDER = "2026-09-21T031500Z"
SCHEMA_CLASS = "P1_CURRENCY_DOMAIN_COMPLETENESS_WITNESS_V1"
CONTRACT_VERSION = "v1"
AUTHORITY_EFFECT = "NONE"
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NONE_TOKEN = "NONE"
HTTP_METHOD = "GET"
AUTHORIZED_HOST = "eea.okx.com"
AUTHORIZED_PATH = "/api/v5/account/interest-limits"
AUTHORIZED_QUERY = f"type={LOAN_TYPE_MARKET}"
AUTHORIZED_ENDPOINT = f"{AUTHORIZED_PATH}?{AUTHORIZED_QUERY}"
AUTHORIZED_URL = f"https://{AUTHORIZED_HOST}{AUTHORIZED_ENDPOINT}"
REQUEST_SURFACE = "GET_/api/v5/account/interest-limits"
MAX_AUTHORIZED_GET_COUNT = 1
RETRY_COUNT = 0
TIMEOUT_SECONDS = 15.0
INTEREST_ACCRUED_TYPE_QUERY = f"type={LOAN_TYPE_MARKET}"
_CCY_TOKEN = re.compile(r"^[A-Z0-9]{2,16}$")
_REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_CAMPAIGN_PACK = (
    "evidence/ops/full_core_p1_max_evidence_campaign_to_next_real_blocker_v1/2026-09-21T020000Z"
)


class P1CurrencyDomainCompletenessWitnessError(ValueError):
    """Fail-closed P1 currency-domain completeness witness violation."""


@dataclass(frozen=True)
class P1CurrencyDomainCompletenessWitnessResultV1:
    wp_id: str
    origin_main_sha: str
    persist_as_of: str
    store_root: str
    authorized_get_count: str
    actual_get_count: str
    network_used: str
    get_surfaces: str
    raw_evidence_persisted: str
    applicable_market_loan_ccy_count: str
    p1_currency_domain_completeness_proven: str
    p1_status_after: str
    first_real_blocker: str
    blocker_class: str
    missing_fact_or_authority: str
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
        raise P1CurrencyDomainCompletenessWitnessError(f"JSON_NOT_OBJECT:{path.name}")
    return payload


def _as_bool_token(value: object) -> bool:
    return str(value or "").lower() == TRUE_TOKEN


def _rows_from_interest_accrued_body(*, body: Mapping[str, Any]) -> int:
    data = body.get("data")
    if not isinstance(data, list):
        return 0
    return sum(1 for item in data if isinstance(item, Mapping))


def build_venue_closed_world_binding_v1() -> dict[str, Any]:
    """Pinned EEA venue semantics for closed-world market-loan ccy enumeration."""
    return {
        "layer": "VENUE_SPECIFICATION",
        "venue_host": AUTHORIZED_HOST,
        "venue_authority_source": "EEA_OKX_V5_OFFICIAL_REST_DOCUMENTATION_PINNED",
        "loan_type_market": LOAN_TYPE_MARKET,
        "interest_accrued_type_alignment": (
            "interest-accrued type=2 and interest-limits type=2 both denote Market loans"
        ),
        "excerpts": [
            {
                "excerpt_id": "INTEREST_ACCRUED_LOAN_TYPE",
                "text": (
                    "type Loan type 2: Market loans Default is 2. ccy Loan currency "
                    "Only applicable to Market loans Only applicable to MARGIN."
                ),
            },
            {
                "excerpt_id": "INTEREST_LIMITS_SURFACE",
                "text": (
                    "Get borrow interest and limit. GET /api/v5/account/interest-limits. "
                    "type Loan type 2: Market loans. ccy Loan currency optional filter."
                ),
            },
            {
                "excerpt_id": "INTEREST_LIMITS_RECORDS_ARRAY",
                "text": (
                    "interest-limits response data[] includes records[]: per-currency loan "
                    "records with ccy field. Omitting ccy on type=2 query returns the "
                    "account-applicable market-loan currency record set in one response."
                ),
            },
            {
                "excerpt_id": "INTEREST_ACCRUED_UNSCOPED_COVERAGE",
                "text": (
                    "interest-accrued without ccy returns interest-accrued rows across "
                    "loan currencies for the bound Market-loan query class (type=2)."
                ),
            },
        ],
        "closed_world_rule": (
            "APPLICABLE_MARKET_LOAN_CCY_SET := sorted unique records[].ccy from "
            "GET /api/v5/account/interest-limits?type=2 without ccy filter, bound to "
            "D4 account at acquisition time; not inferred from settlement currency, "
            "USDC filter alone, or interest-accrued row observation alone."
        ),
    }


def extract_applicable_market_loan_ccy_set_v1(*, body: Mapping[str, Any]) -> tuple[str, ...]:
    if str(body.get("code") or "") != "0":
        raise P1CurrencyDomainCompletenessWitnessError("VENUE_CODE_NON_ZERO")
    data = body.get("data")
    if not isinstance(data, list) or not data:
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_DATA_EMPTY")
    block = data[0]
    if not isinstance(block, Mapping):
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_BLOCK_NOT_OBJECT")
    records = block.get("records")
    if not isinstance(records, list) or not records:
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_RECORDS_EMPTY")
    seen: set[str] = set()
    ordered: list[str] = []
    for row in records:
        if not isinstance(row, Mapping):
            raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_RECORD_MALFORMED")
        ccy = str(row.get("ccy") or "").strip().upper()
        if not ccy or not _CCY_TOKEN.match(ccy):
            raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_CCY_INVALID")
        if ccy not in seen:
            seen.add(ccy)
            ordered.append(ccy)
    if not ordered:
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_CCY_SET_EMPTY")
    return tuple(ordered)


def build_p1_currency_domain_witness_adjudication_v1(
    *,
    applicable_market_loan_ccy_set: Sequence[str],
    cd_row_count: int,
    usdc_row_count: int,
    campaign_row_count: int,
    settlement_ccy: str,
) -> dict[str, Any]:
    """Offline fail-closed adjudication for currency-domain completeness."""
    ccy_set = tuple(applicable_market_loan_ccy_set)
    enumeration_proven = len(ccy_set) > 0
    enumeration_missing = NONE_TOKEN
    if not enumeration_proven:
        enumeration_missing = "CLOSED_WORLD_APPLICABLE_MARKET_LOAN_CCY_SET_EMPTY"

    combined_interest_accrued_rows = cd_row_count + usdc_row_count + campaign_row_count
    exhaustion_proven = False
    exhaustion_missing = (
        "INTEREST_ACCRUED_ROW_OBSERVATION_WITHOUT_CLOSED_WORLD_ENUMERATION_OR_NONZERO_ROWS"
    )

    if enumeration_proven and combined_interest_accrued_rows == 0:
        exhaustion_proven = True
        exhaustion_missing = NONE_TOKEN
    elif enumeration_proven and combined_interest_accrued_rows > 0:
        exhaustion_missing = (
            "NONZERO_INTEREST_ACCRUED_ROWS_REQUIRE_PER_CCY_TRAVERSAL_WITNESS_NOT_IN_THIS_WP"
        )
    elif settlement_ccy == "USDC" and usdc_row_count == 0 and not enumeration_proven:
        exhaustion_missing = "USDC_SCOPED_ZERO_ROWS_ALONE_DO_NOT_PROVE_DOMAIN_EXHAUSTION"
    elif combined_interest_accrued_rows == 0 and not enumeration_proven:
        exhaustion_missing = (
            "ZERO_ROWS_ACROSS_SEALED_INTEREST_ACCRUED_GETS_CANNOT_PROVE_APPLICABLE_CCY_DOMAIN"
        )

    completeness_proven = enumeration_proven and exhaustion_proven
    missing_fact = NONE_TOKEN
    if not enumeration_proven:
        missing_fact = enumeration_missing
    elif not exhaustion_proven:
        missing_fact = exhaustion_missing

    return {
        "layer": "CANONICAL_AUTHORITY",
        "WP_ID": WP_ID,
        "SCHEMA_CLASS": SCHEMA_CLASS,
        "CLOSED_WORLD_ENUMERATION_PROVEN": TRUE_TOKEN if enumeration_proven else FALSE_TOKEN,
        "CLOSED_WORLD_SOURCE_SURFACE": REQUEST_SURFACE,
        "CLOSED_WORLD_SOURCE_QUERY": AUTHORIZED_QUERY,
        "APPLICABLE_MARKET_LOAN_CCY_SET": list(ccy_set),
        "APPLICABLE_MARKET_LOAN_CCY_COUNT": str(len(ccy_set)),
        "INTEREST_ACCRUED_TYPE_ALIGNMENT": INTEREST_ACCRUED_TYPE_QUERY,
        "APPLICABLE_LOAN_CURRENCY_DOMAIN_EXHAUSTION_PROVEN": (
            TRUE_TOKEN if exhaustion_proven else FALSE_TOKEN
        ),
        "P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN": (
            TRUE_TOKEN if completeness_proven else FALSE_TOKEN
        ),
        "CURRENCY_DOMAIN_MISSING_FACT": missing_fact,
        "SEALED_CD_ROW_COUNT": str(cd_row_count),
        "SEALED_USDC_ROW_COUNT": str(usdc_row_count),
        "SEALED_CAMPAIGN_ROW_COUNT": str(campaign_row_count),
        "SETTLEMENT_CCY_NON_AUTHORITY": TRUE_TOKEN,
        "USDC_FILTER_NON_AUTHORITY": TRUE_TOKEN,
        "ZERO_ROWS_NON_AUTHORITY_WITHOUT_ENUMERATION": TRUE_TOKEN,
    }


def _one_bounded_interest_limits_get_v1(
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
        "error_class": NONE_TOKEN,
    }


def execute_p1_currency_domain_completeness_witness_v1(
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
    interest_limits_body: Mapping[str, Any] | None = None,
) -> P1CurrencyDomainCompletenessWitnessResultV1:
    if owner_go not in ALLOWED_OWNER_GOS:
        raise P1CurrencyDomainCompletenessWitnessError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise P1CurrencyDomainCompletenessWitnessError("ORIGIN_MAIN_SHA_MISMATCH")

    repo = Path(repo_root) if repo_root is not None else _REPO_ROOT
    cd_pack = repo / CANONICAL_CD_PACK_RELPATH
    usdc_pack = repo / CANONICAL_USDC_P1_PACK_RELPATH / "2026-09-20T233000Z"
    campaign_pack = repo / CANONICAL_CAMPAIGN_PACK
    for pack in (cd_pack, usdc_pack, campaign_pack):
        if verify_manifest_sha256_v1(store_root=pack) != 0:
            raise P1CurrencyDomainCompletenessWitnessError(
                f"SEALED_PACK_MANIFEST_MISMATCH:{pack.name}"
            )

    cd_body = _load_json_object(path=cd_pack / "raw_interest_accrued_response_body.json")
    usdc_body = _load_json_object(path=usdc_pack / "raw_interest_accrued_response_body.json")
    campaign_body_path = campaign_pack / "raw_interest_accrued_response_body.json"
    campaign_body: Mapping[str, Any] = {}
    if campaign_body_path.is_file():
        campaign_body = _load_json_object(path=campaign_body_path)
    cd_rows = _rows_from_interest_accrued_body(body=cd_body)
    usdc_rows = _rows_from_interest_accrued_body(body=usdc_body)
    campaign_rows = _rows_from_interest_accrued_body(body=campaign_body)

    genesis_root = (
        Path(genesis_store_root)
        if genesis_store_root is not None
        else resolve_canonical_d4_d5_genesis_runtime_store_root_v1(repo_root=repo)
    )
    if genesis_root is None:
        raise P1CurrencyDomainCompletenessWitnessError("GENESIS_STORE_ABSENT")
    d4 = load_bound_account_identity_runtime_binding_v1(store_root=genesis_root)
    if d4.identity_digest != "00c354f2d247f5a64e33efb31f8be155b8557e847868335ccb15cd4f7ca9d7c4":
        raise P1CurrencyDomainCompletenessWitnessError("D4_IDENTITY_DIGEST_DRIFT")

    as_of = persist_as_of or _utc_now_z()
    store = Path(evidence_root) / _folder_from_as_of(as_of)
    canonical = repo / CANONICAL_PACK_RELPATH / CANONICAL_PACK_AS_OF_FOLDER
    if store.resolve() != canonical.resolve():
        raise P1CurrencyDomainCompletenessWitnessError("WITNESS_STORE_NOT_CANONICAL_PATH")
    store.mkdir(parents=True, exist_ok=True)

    network_used = FALSE_TOKEN
    actual_get_count = 0
    raw_persisted = FALSE_TOKEN
    raw_sha = ""
    parsed_limits: Mapping[str, Any]

    if interest_limits_body is not None:
        parsed_limits = interest_limits_body
    elif not skip_network:
        default_vault = repo / (
            ".ops_local/section_11_13_5_live_canary_minimum_exposure/secrets/secretref_vault.json"
        )
        resolved_vault = Path(vault_file) if vault_file else default_vault
        if not resolved_vault.is_file():
            raise P1CurrencyDomainCompletenessWitnessError("VAULT_FILE_REQUIRED")
        secretref_identity_without_values_v1(vault_file=resolved_vault)
        key, secret, phrase = _ephemeral_vault_fields_v1(vault_file=resolved_vault)
        handle: FullCoreK1BoundVenueAuthHandleV1 | None = (
            bind_already_held_k1_venue_auth_session_v1(
                api_key=key, api_secret=secret, passphrase=phrase
            )
        )
        opened: LiveCanaryTransportV1 = (
            transport
            if transport is not None
            else UrllibLiveCanaryTransportV1(wire_send_enabled=True)
        )
        try:
            capture = _one_bounded_interest_limits_get_v1(transport=opened, handle=handle)
            actual_get_count = 1
            network_used = TRUE_TOKEN
            body_bytes = bytes(capture["body_bytes"])
            raw_sha = _sha256_bytes(body_bytes)
            _persist_raw_bytes(
                path=store / "raw_interest_limits_response_body.json", body=body_bytes
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
                    "request_utc": capture["request_utc"],
                    "response_utc": capture["response_utc"],
                    "http_status": capture["http_status"],
                    "raw_body_sha256": raw_sha,
                    "account_identity_digest": d4.identity_digest,
                },
            )
            raw_persisted = TRUE_TOKEN
            parsed_limits = parse_json_object_v1(body_bytes)
        finally:
            if handle is not None:
                release_k1_venue_auth_session_v1(handle)
    elif skip_network:
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_BODY_REQUIRED")
    else:
        raise P1CurrencyDomainCompletenessWitnessError("INTEREST_LIMITS_BODY_REQUIRED")

    ccy_set = extract_applicable_market_loan_ccy_set_v1(body=parsed_limits)
    venue_binding = build_venue_closed_world_binding_v1()
    adjudication = build_p1_currency_domain_witness_adjudication_v1(
        applicable_market_loan_ccy_set=ccy_set,
        cd_row_count=cd_rows,
        usdc_row_count=usdc_rows,
        campaign_row_count=campaign_rows,
        settlement_ccy=str(d4.settlement_currency or ""),
    )
    _persist_json(path=store / "venue_closed_world_binding_v1.json", payload=venue_binding)
    _persist_json(
        path=store / "p1_currency_domain_witness_adjudication_v1.json", payload=adjudication
    )
    _persist_json(
        path=store / "currency_domain_surface_binding_v1.json",
        payload={
            "layer": "CANONICAL_AUTHORITY",
            "HTTP_METHOD": HTTP_METHOD,
            "AUTHORIZED_QUERY": AUTHORIZED_QUERY,
            "MAX_AUTHORIZED_GET_COUNT": str(MAX_AUTHORIZED_GET_COUNT),
            "RETRY_COUNT": str(RETRY_COUNT),
            "ACCOUNT_IDENTITY_DIGEST": d4.identity_digest,
            "VENUE": d4.bound_venue_identity,
            "SETTLEMENT_CCY": str(d4.settlement_currency or ""),
            "GET_SURFACE": REQUEST_SURFACE,
            "INTEREST_ACCRUED_TYPE_ALIGNMENT": INTEREST_ACCRUED_TYPE_QUERY,
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
            "APPLICABLE_MARKET_LOAN_CCY_COUNT": str(len(ccy_set)),
            "CD_PACK_CONSUMED": str(cd_pack.relative_to(repo)),
            "USDC_P1_PACK_CONSUMED": str(usdc_pack.relative_to(repo)),
            "CAMPAIGN_PACK_CONSUMED": str(campaign_pack.relative_to(repo)),
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

    _persist_json(
        path=store / "p1_currency_domain_closeout_report_v1.json",
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
                ROOT_LIABILITY_EVENT_CLASS: root_by_id_v1(
                    bundle, ROOT_LIABILITY_EVENT_CLASS
                ).complete,
                ROOT_PAGINATION: root_by_id_v1(bundle, ROOT_PAGINATION).complete,
                ROOT_EVENT_ORDERING: root_by_id_v1(bundle, ROOT_EVENT_ORDERING).complete,
                ROOT_OBSERVATION_FRESHNESS: root_by_id_v1(
                    bundle, ROOT_OBSERVATION_FRESHNESS
                ).complete,
                ROOT_RESTART_DURABILITY: root_by_id_v1(bundle, ROOT_RESTART_DURABILITY).complete,
                DERIVED_TIME_DOMAIN: bundle.time_domain.complete,
                DERIVED_PROVENANCE: bundle.provenance.complete,
            },
        },
    )

    persist_manifest_sha256_v1(store_root=store)
    if verify_manifest_sha256_v1(store_root=store) != 0:
        raise P1CurrencyDomainCompletenessWitnessError("MANIFEST_PERSIST_FAIL")

    return P1CurrencyDomainCompletenessWitnessResultV1(
        wp_id=WP_ID,
        origin_main_sha=origin_main_sha,
        persist_as_of=as_of,
        store_root=str(store),
        authorized_get_count=str(MAX_AUTHORIZED_GET_COUNT),
        actual_get_count=str(actual_get_count),
        network_used=network_used,
        get_surfaces=REQUEST_SURFACE,
        raw_evidence_persisted=raw_persisted,
        applicable_market_loan_ccy_count=str(len(ccy_set)),
        p1_currency_domain_completeness_proven=str(
            adjudication["P1_CURRENCY_DOMAIN_COMPLETENESS_PROVEN"]
        ),
        p1_status_after=closeout.p1_status_after,
        first_real_blocker=blocker_id,
        blocker_class=blocker_class,
        missing_fact_or_authority=missing,
        closeout_decision=closeout.closeout_decision,
    )


def _ephemeral_vault_fields_v1(*, vault_file: Path) -> tuple[str, str, str]:
    payload = json.loads(vault_file.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise P1CurrencyDomainCompletenessWitnessError("VAULT_NOT_OBJECT")
    if REQUIRED_SECRETREF_URI not in payload:
        raise P1CurrencyDomainCompletenessWitnessError("SECRETREF_URI_UNBOUND")
    raw = payload[REQUIRED_SECRETREF_URI]
    material = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(material, Mapping):
        raise P1CurrencyDomainCompletenessWitnessError("SECRETREF_MATERIAL_NOT_OBJECT")
    key = str(material.get("api_key") or "").strip()
    secret = str(material.get("api_secret") or "").strip()
    phrase = str(material.get("passphrase") or "").strip()
    if not key or not secret or not phrase:
        raise P1CurrencyDomainCompletenessWitnessError("CREDENTIAL_FIELDS_INCOMPLETE")
    return key, secret, phrase


__all__ = [
    "ALLOWED_OWNER_GOS",
    "AUTHORITY_EFFECT",
    "AUTHORIZED_QUERY",
    "AUTHORIZED_URL",
    "CANONICAL_PACK_AS_OF_FOLDER",
    "CANONICAL_PACK_RELPATH",
    "EXPECTED_ORIGIN_MAIN_SHA",
    "MAX_AUTHORIZED_GET_COUNT",
    "OWNER_GO",
    "P1CurrencyDomainCompletenessWitnessError",
    "P1CurrencyDomainCompletenessWitnessResultV1",
    "REQUEST_SURFACE",
    "SCHEMA_CLASS",
    "WP_ID",
    "build_p1_currency_domain_witness_adjudication_v1",
    "build_venue_closed_world_binding_v1",
    "execute_p1_currency_domain_completeness_witness_v1",
    "extract_applicable_market_loan_ccy_set_v1",
]
