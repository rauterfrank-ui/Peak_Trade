"""CURRENT_PRODUCTIVE exact-object disposition to one-shot flatten POST boundary.

Consumes Owner-GO
OWNER_GO_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_V1.

Grants present-day disposition management for one exact current occupancy only.
Builds a fresh reduce-only flatten plan/envelope. Does not POST. Does not create
or consume a live permit. Does not invent historical Peak_Trade ownership.
Does not import Canary/§11.13.5/§11.14 authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlencode

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM,
    EXTERNAL_EFFECT_AUTHORIZED,
    FOLLOW_ON_SUBMIT_ISOLATED,
    FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    MAX_EXTERNAL_EFFECT_POST_COUNT,
    ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT,
    ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN,
    ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED,
    POST_ALLOWED,
    PRODUCTIVE_WIRE_SEND_REACHABLE,
    REAL_EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    REPLAY_PROTECTION_DURABLE,
    SUBMISSION_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_exact_object_flatten_plan_v1 import (
    ALREADY_FLAT,
    IDENTITY_AMBIGUOUS,
    INCOMPATIBLE_POS_MODE,
    MULTIPLE_POSITIONS,
    OBJECT_MISMATCH,
    PENDING_ORDERS,
    CurrentProductiveExactObjectFlattenPlanError,
    build_exact_object_flatten_plan_and_envelope_v1,
    revalidate_authorized_occupancy_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_TICKER,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ONE_SHOT_REAL_POST_AUTHORITY_REFS,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    ENDPOINT_PUBLIC_INSTRUMENTS,
    ENDPOINT_PUBLIC_PRICE_LIMIT,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    CurrentProductiveFreshCap23Cap24ReadinessError,
    _assert_no_secrets,
    _persist_json,
    _token,
    _utc_now_iso_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)

OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_V1"
)
THIS_SLICE = (
    "11.2.1.DL.FULL_CORE_CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_"
    "FLATTEN_POST_BOUNDARY"
)
EXPECTED_ORIGIN_MAIN_SHA = "7360cb0c6fc229de2835aa68399cc8271ad5c8d0"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_exact_object_disposition_to_one_shot_"
    "flatten_post_boundary_v1/20260915T212400Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
NEXT_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_EXACT_OBJECT_FLATTEN_"
    "ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
GRANTED_INST_ID = "SUI-USD_UM_XPERP-310404"
GRANTED_INST_TYPE = "FUTURES"
GRANTED_POS_ID = "3891385768441942017"
GRANTED_POS = "1"
GRANTED_POS_SIDE = "net"
GRANTED_MGN_MODE = "cross"
ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductiveExactObjectDispositionError(CurrentProductiveFreshCap23Cap24ReadinessError):
    """Fail-closed exact-object disposition / flatten-boundary violation."""


@dataclass(frozen=True)
class CurrentProductiveExactObjectDispositionResultV1:
    store_root: str
    authorized_object_match: str
    flatten_plan_created: str
    flatten_side: str
    flatten_quantity: str
    reduce_only: str
    order_type: str
    limit_price: str
    final_envelope_id: str
    final_envelope_digest: str
    envelope_readiness: str
    permit_created: str
    real_external_effect_authorized: str
    post_count: str
    first_real_blocker: str
    evidence_manifest: str
    manifest_verify_rc: int


def _assert_dl_pins() -> None:
    if (
        CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_CREATED
        is not True
    ):
        raise CurrentProductiveExactObjectDispositionError("DL_ADAPTER_NOT_CREATED")
    if ENVELOPE_BOUND_SINGLE_USE_EXTERNAL_EFFECT_SEAM is not True:
        raise CurrentProductiveExactObjectDispositionError("ENVELOPE_BOUND_SEAM_NOT_TRUE")
    if ONE_SHOT_REAL_POST_TRANSPORT_IMPLEMENTED is not True:
        raise CurrentProductiveExactObjectDispositionError("ONE_SHOT_TRANSPORT_NOT_IMPLEMENTED")
    if ONE_SHOT_REAL_POST_REQUIRES_EXACT_ENVELOPE_BOUND_PERMIT is not True:
        raise CurrentProductiveExactObjectDispositionError("ONE_SHOT_PERMIT_GATE_MISSING")
    if ONE_SHOT_REAL_POST_STANDING_EXTERNAL_EFFECT_FORBIDDEN is not True:
        raise CurrentProductiveExactObjectDispositionError("ONE_SHOT_STANDING_FORBIDDEN_MISSING")
    if FULL_CORE_ACTUAL_HTTP_POST_SEAM_IMPLEMENTED is not True:
        raise CurrentProductiveExactObjectDispositionError("HTTP_POST_SEAM_NOT_IMPLEMENTED")
    if int(MAX_EXTERNAL_EFFECT_POST_COUNT) != 1:
        raise CurrentProductiveExactObjectDispositionError("MAX_POST_COUNT_NOT_ONE")
    if REPLAY_PROTECTION_DURABLE is not True:
        raise CurrentProductiveExactObjectDispositionError("REPLAY_PROTECTION_NOT_DURABLE")
    if FOLLOW_ON_SUBMIT_ISOLATED is not True:
        raise CurrentProductiveExactObjectDispositionError("FOLLOW_ON_NOT_ISOLATED")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise CurrentProductiveExactObjectDispositionError("STANDING_EXTERNAL_EFFECT_TRUE")
    if REAL_EXTERNAL_EFFECT_AUTHORIZED is True:
        raise CurrentProductiveExactObjectDispositionError("REAL_EXTERNAL_EFFECT_TRUE")
    if REAL_VENUE_POST_ALLOWED is True:
        raise CurrentProductiveExactObjectDispositionError("REAL_VENUE_POST_ALLOWED_TRUE")
    if POST_ALLOWED is True:
        raise CurrentProductiveExactObjectDispositionError("POST_ALLOWED_TRUE")
    if LIVE_AUTHORIZED is not True or LIVE_ARMED is not True:
        raise CurrentProductiveExactObjectDispositionError("LIVE_GATES_NOT_TRUE")
    if WIRE_SEND_PERMITTED is not True or SUBMISSION_AUTHORIZED is not True:
        raise CurrentProductiveExactObjectDispositionError("SEND_GATES_NOT_TRUE")
    if PRODUCTIVE_WIRE_SEND_REACHABLE is not True:
        raise CurrentProductiveExactObjectDispositionError("WIRE_SEND_NOT_REACHABLE")
    if int(MAX_POSITIONS_EFFECTIVE) != 1:
        raise CurrentProductiveExactObjectDispositionError("MAX_POSITIONS_NOT_ONE")
    if OWNER_GO in ONE_SHOT_REAL_POST_AUTHORITY_REFS:
        raise CurrentProductiveExactObjectDispositionError("THIS_GO_MUST_NOT_AUTHORIZE_REAL_POST")
    if NEXT_OWNER_GO not in ONE_SHOT_REAL_POST_AUTHORITY_REFS:
        raise CurrentProductiveExactObjectDispositionError("LATER_FLATTEN_POST_GO_NOT_WIRED")


def _get_payload(
    transport: FullCoreProductiveReadOnlyGetTransportV1,
    *,
    path: str,
    query: Mapping[str, str] | None,
    auth_required: bool,
    decision_id: str,
) -> tuple[Any, int, str]:
    endpoint = path if not query else f"{path}?{urlencode(dict(query))}"
    result = transport.get(
        endpoint=endpoint,
        auth_required=auth_required,
        pretrade_decision_id=decision_id,
    )
    status = int(getattr(result, "http_status", 0) or 0)
    if result.get_performed is not True or result.payload is None:
        return None, status, str(result.error_class or "GET_NOT_PERFORMED")
    return result.payload, status, ""


def execute_current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    fresh_get_transport: FullCoreProductiveReadOnlyGetTransportV1 | None = None,
    execute_network: bool = False,
    repository_sha: str | None = None,
) -> CurrentProductiveExactObjectDispositionResultV1:
    del repository_sha
    if str(owner_go or "") != OWNER_GO:
        raise CurrentProductiveExactObjectDispositionError("OWNER_GO_MISMATCH")
    if str(origin_main_sha or "") != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveExactObjectDispositionError("ORIGIN_MAIN_SHA_MISMATCH")
    _assert_dl_pins()

    root = _REPO_ROOT
    package_started = _utc_now_iso_v1()
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)

    handle = None
    transport = fresh_get_transport
    get_status = "NOT_REACHED"
    get_meta: dict[str, Any] = {}
    occupancy: dict[str, str] = {}
    authorized_match = FALSE_TOKEN
    flatten_plan_created = FALSE_TOKEN
    flatten_side = ""
    flatten_qty = ""
    reduce_only = FALSE_TOKEN
    order_type = ""
    limit_price = ""
    envelope_id = ""
    envelope_digest = ""
    envelope_readiness = FALSE_TOKEN
    envelope_fields: dict[str, Any] = {}
    first_blocker = ""
    open_orders_status = "NOT_REACHED"
    already_flat = FALSE_TOKEN

    try:
        if execute_network is True and transport is None:
            resolved_vault = (
                Path(str(vault_file))
                if vault_file is not None and str(vault_file).strip()
                else _fail_closed_credential_unavailable_v1(repo_root=root)
            )
            try:
                backend = _fail_closed_credential_unavailable_v1(vault_file=resolved_vault)
                handle = _fail_closed_credential_unavailable_v1(
                    secret_reference=REQUIRED_SECRETREF_URI,
                    vault_backend=backend,
                    credential_class=REQUIRED_CREDENTIAL_CLASS,
                )
                transport = FullCoreProductiveReadOnlyGetTransportV1(
                    handle=handle, max_request_count=8
                )
            except RuntimeError:
                get_status = "CREDENTIAL_HANDLE_FAIL_CLOSED"
                first_blocker = get_status
        if transport is not None and not first_blocker:
            try:
                config_payload, config_http, config_err = _get_payload(
                    transport,
                    path=ENDPOINT_ACCOUNT_CONFIG,
                    query=None,
                    auth_required=True,
                    decision_id=GRANTED_INST_ID,
                )
                positions_payload, positions_http, positions_err = _get_payload(
                    transport,
                    path=ENDPOINT_ACCOUNT_POSITIONS,
                    query=None,
                    auth_required=True,
                    decision_id=GRANTED_INST_ID,
                )
                pending_payload, pending_http, pending_err = _get_payload(
                    transport,
                    path=ENDPOINT_ORDERS_PENDING,
                    query={"instType": GRANTED_INST_TYPE},
                    auth_required=True,
                    decision_id=GRANTED_INST_ID,
                )
                instruments_payload, instruments_http, instruments_err = _get_payload(
                    transport,
                    path=ENDPOINT_PUBLIC_INSTRUMENTS,
                    query={"instType": GRANTED_INST_TYPE, "instId": GRANTED_INST_ID},
                    auth_required=False,
                    decision_id=GRANTED_INST_ID,
                )
                price_limit_payload, price_http, price_err = _get_payload(
                    transport,
                    path=ENDPOINT_PUBLIC_PRICE_LIMIT,
                    query={"instId": GRANTED_INST_ID},
                    auth_required=False,
                    decision_id=GRANTED_INST_ID,
                )
                ticker_payload, ticker_http, ticker_err = _get_payload(
                    transport,
                    path=ENDPOINT_MARKET_TICKER,
                    query={"instId": GRANTED_INST_ID},
                    auth_required=False,
                    decision_id=GRANTED_INST_ID,
                )
                get_meta = {
                    "CONFIG": {
                        "HTTP_STATUS": str(config_http),
                        "ERROR": config_err,
                    },
                    "POSITIONS": {
                        "HTTP_STATUS": str(positions_http),
                        "ERROR": positions_err,
                    },
                    "PENDING_FUTURES": {
                        "HTTP_STATUS": str(pending_http),
                        "ERROR": pending_err,
                    },
                    "INSTRUMENTS": {
                        "HTTP_STATUS": str(instruments_http),
                        "ERROR": instruments_err,
                    },
                    "PRICE_LIMIT": {"HTTP_STATUS": str(price_http), "ERROR": price_err},
                    "TICKER": {"HTTP_STATUS": str(ticker_http), "ERROR": ticker_err},
                    "METHOD": "GET",
                    "HOST": "eea.okx.com",
                    "GET_REQUEST_COUNT": str(getattr(transport, "request_count", 0)),
                }
                if any(
                    (
                        config_err,
                        positions_err,
                        pending_err,
                        instruments_err,
                        price_err,
                        ticker_err,
                    )
                ):
                    get_status = "FRESH_GET_FAIL_CLOSED"
                    first_blocker = get_status
                else:
                    get_status = "TRUSTED_PRESENT"
                    pending_data = (
                        pending_payload.get("data")
                        if isinstance(pending_payload, Mapping)
                        else None
                    )
                    open_orders_status = (
                        "NONE_OBSERVED"
                        if isinstance(pending_data, list) and len(pending_data) == 0
                        else "UNEXPECTED_PENDING"
                    )
                    try:
                        occupancy = revalidate_authorized_occupancy_v1(
                            positions_payload=positions_payload,
                            pending_payload=pending_payload,
                            config_payload=config_payload,
                            granted_inst_id=GRANTED_INST_ID,
                            granted_inst_type=GRANTED_INST_TYPE,
                            granted_pos_id=GRANTED_POS_ID,
                            granted_pos=GRANTED_POS,
                            granted_pos_side=GRANTED_POS_SIDE,
                            granted_mgn_mode=GRANTED_MGN_MODE,
                        )
                        authorized_match = TRUE_TOKEN
                        plan, envelope, price_source = (
                            build_exact_object_flatten_plan_and_envelope_v1(
                                occupancy=occupancy,
                                instruments_payload=instruments_payload,
                                price_limit_payload=price_limit_payload,
                                ticker_payload=ticker_payload,
                                run_id="current-productive-dl-flatten",
                                session_id="current-productive-dl-session",
                                intent_id=f"exact-object-flatten-{GRANTED_POS_ID[-8:]}",
                                creation_epoch=package_started,
                                td_mode=GRANTED_MGN_MODE,
                            )
                        )
                        del price_source
                        flatten_plan_created = TRUE_TOKEN
                        flatten_side = plan.side
                        flatten_qty = plan.quantity
                        reduce_only = _token(plan.reduce_only is True)
                        order_type = plan.order_type
                        limit_price = envelope.price
                        envelope_id = envelope.envelope_id
                        envelope_digest = envelope.envelope_digest
                        envelope_readiness = TRUE_TOKEN
                        envelope_fields = {
                            "instId": envelope.instrument_id,
                            "side": envelope.side,
                            "ordType": envelope.order_type,
                            "sz": envelope.quantity,
                            "px": envelope.price,
                            "tdMode": envelope.td_mode,
                            "posSide": envelope.pos_side,
                            "reduceOnly": envelope.reduce_only is True,
                            "clOrdId": envelope.client_order_id,
                            "path_kind": envelope.path_kind,
                        }
                        first_blocker = NEXT_OWNER_GO
                    except CurrentProductiveExactObjectFlattenPlanError as exc:
                        code = str(exc)
                        if code == ALREADY_FLAT:
                            already_flat = TRUE_TOKEN
                            first_blocker = ALREADY_FLAT
                            authorized_match = TRUE_TOKEN
                        elif code.startswith(OBJECT_MISMATCH) or code in {
                            MULTIPLE_POSITIONS,
                            PENDING_ORDERS,
                            INCOMPATIBLE_POS_MODE,
                            IDENTITY_AMBIGUOUS,
                        }:
                            first_blocker = code
                            authorized_match = FALSE_TOKEN
                        else:
                            # Occupancy revalidated; plan/envelope construction denied.
                            first_blocker = code
                            if occupancy:
                                authorized_match = TRUE_TOKEN
                            else:
                                authorized_match = FALSE_TOKEN
            except (
                TypeError,
                RuntimeError,
                ValueError,
                FullCoreProductiveReadOnlyGetError,
            ) as exc:
                get_status = f"FRESH_GET_FAIL_CLOSED:{type(exc).__name__}"
                first_blocker = get_status
        elif not first_blocker:
            get_status = "FRESH_GET_TRANSPORT_MISSING"
            first_blocker = get_status
    finally:
        if handle is not None:
            _fail_closed_credential_unavailable_v1(handle)

    send_handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-dl-flatten-readiness-handle", bound=True
    )
    http_transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=send_handle)
    try:
        http_transport.post_trade_order(
            payload={"instId": GRANTED_INST_ID or "MUST_NOT_POST"},
            permit_id="eep-dl-must-not-post",
            envelope_id="env-dl-must-not-post",
            envelope_digest="0" * 64,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveExactObjectDispositionError("HTTP_FORBIDDEN_MISSING") from exc
    else:
        raise CurrentProductiveExactObjectDispositionError("HTTP_MUST_NOT_POST")
    if http_transport.post_count != 0:
        raise CurrentProductiveExactObjectDispositionError("HTTP_TRANSPORT_SIDE_EFFECT")

    package_finished = _utc_now_iso_v1()
    claims = {
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "THIS_SLICE": THIS_SLICE,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "CURRENT_PHASE": THIS_SLICE,
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": package_finished,
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "CURRENT_DISPOSITION_MANAGEMENT_AUTHORITY": "OWNER_GRANTED_EXACT_OBJECT_ONLY",
        "FLATTEN_PREPARATION_AUTHORIZED": TRUE_TOKEN,
        "FLATTEN_POST_AUTHORIZED": FALSE_TOKEN,
        "CANARY_OR_SECTION_11_14_IMPORTED_AS_OWNERSHIP": FALSE_TOKEN,
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "FRESH_POSITION_EVIDENCE": get_status,
        "AUTHORIZED_OBJECT_MATCH": authorized_match,
        "ALREADY_FLAT": already_flat,
        "CURRENT_POSITION_FACTS": occupancy,
        "OPEN_ORDERS_STATUS": open_orders_status,
        "FLATTEN_PLAN_CREATED": flatten_plan_created,
        "FLATTEN_SIDE": flatten_side,
        "FLATTEN_QUANTITY": flatten_qty,
        "REDUCE_ONLY": reduce_only,
        "ORDER_TYPE": order_type,
        "LIMIT_PRICE_IF_APPLICABLE": limit_price,
        "FINAL_ENVELOPE_CREATED": _token(bool(envelope_id)),
        "FINAL_ENVELOPE_ID": envelope_id,
        "FINAL_ENVELOPE_DIGEST": envelope_digest,
        "ENVELOPE_EXECUTION_FIELDS": envelope_fields,
        "EXACT_ENVELOPE_BOUND_PERMIT_READINESS": envelope_readiness,
        "PERMIT_CREATED": FALSE_TOKEN,
        "PERMIT_CONSUMED_DURABLY": FALSE_TOKEN,
        "MAX_POST_COUNT": "1",
        "AUTOMATIC_RETRY_PERFORMED": FALSE_TOKEN,
        "SECOND_SUBMIT_PERFORMED": FALSE_TOKEN,
        "FOLLOW_ON_SUBMIT_ISOLATED": TRUE_TOKEN,
        "REPLAY_PROTECTION_DURABLE": TRUE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "POST_COUNT": "0",
        "TRANSPORT_ATTEMPTED": FALSE_TOKEN,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": "1",
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
        "FIRST_REAL_BLOCKER": first_blocker or NEXT_OWNER_GO,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO,
        "GRANTED_INST_ID": GRANTED_INST_ID,
        "GRANTED_POS_ID": GRANTED_POS_ID,
    }
    _assert_no_secrets(claims)
    summary = {
        "DOCUMENT_CLASS": "CURRENT_PRODUCTIVE_EXACT_OBJECT_DISPOSITION_TO_ONE_SHOT_FLATTEN_POST_BOUNDARY_V1",
        "AUTHORIZED_OBJECT_MATCH": authorized_match,
        "FINAL_ENVELOPE_ID": envelope_id,
        "PERMIT_CREATED": FALSE_TOKEN,
        "POST_COUNT": "0",
        "FIRST_REAL_BLOCKER": first_blocker or NEXT_OWNER_GO,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "CURRENT_DISPOSITION_MANAGEMENT_AUTHORITY": "OWNER_GRANTED_EXACT_OBJECT_ONLY",
        "CANARY_OR_SECTION_11_14_IMPORTED_AS_OWNERSHIP": FALSE_TOKEN,
        "AUTHORITY_CLASS": "OWNER_GRANTED_EXACT_OBJECT_DISPOSITION_PREPARATION_NOT_POST",
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "TOP20_RANKING_SELECTION_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_ENTRY_AUTHORITY_UNCHANGED": TRUE_TOKEN,
        "SINGLE_SELECTED_FUTURE_UNCHANGED": TRUE_TOKEN,
        "MAX_POSITIONS_UNCHANGED_1": TRUE_TOKEN,
    }
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "GET_META.json", payload=get_meta)
    _persist_json(path=store / "POSITIONS_AND_ORDERS.json", payload={"occupancy": occupancy})
    _persist_json(path=store / "FLATTEN_PLAN.json", payload=envelope_fields)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveExactObjectDispositionResultV1(
        store_root=str(store),
        authorized_object_match=authorized_match,
        flatten_plan_created=flatten_plan_created,
        flatten_side=flatten_side,
        flatten_quantity=flatten_qty,
        reduce_only=reduce_only,
        order_type=order_type,
        limit_price=limit_price,
        final_envelope_id=envelope_id,
        final_envelope_digest=envelope_digest,
        envelope_readiness=envelope_readiness,
        permit_created=FALSE_TOKEN,
        real_external_effect_authorized=FALSE_TOKEN,
        post_count="0",
        first_real_blocker=first_blocker or NEXT_OWNER_GO,
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=int(manifest_rc),
    )
