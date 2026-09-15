"""CURRENT_PRODUCTIVE fresh runtime cycle after flatten occupancy-absent.

Consumes Owner-GO
OWNER_GO_FOR_FRESH_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT_V1.

Re-proves occupancy/pending/config via READ-ONLY GETs, binds Cap-23/24 to
this cycle through the current Cap-2.1–2.4 producers, and runs one current
Master-V2 cycle. Does not fabricate ENTER. Does not POST. Does not create
or consume a live permit.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from time import time
from typing import Any, Mapping, Optional
from urllib.parse import urlencode

from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    EeaUniverseAcquisitionResultV1,
    acquire_eea_universe_inventory_v1,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.transport_v1 import (
    EeaPublicUniverseGetPortV1,
    EeaUniverseAcquisitionError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ENDPOINT_MARKET_CANDLES,
    ENDPOINT_MARKET_TICKER,
    ENDPOINT_PUBLIC_FUNDING_RATE,
    ENDPOINT_PUBLIC_OPEN_INTEREST,
    extract_finalized_candle_closes_v1,
    extract_funding_rate_v1,
    extract_mark_and_index_from_payload_v1,
    extract_open_interest_v1,
    extract_position_truth_v1,
    extract_ticker_fields_v1,
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT,
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_CONFIG,
    ENDPOINT_ACCOUNT_POSITIONS,
    FullCoreFreshPretradeGetTransportV1,
    collect_fresh_pretrade_runtime_get_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    FullCoreProductiveReadOnlyGetError,
    FullCoreProductiveReadOnlyGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    current_productive_first_real_blocker_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1 import (
    CurrentProductiveFreshCap23Cap24ReadinessError,
    _assert_no_secrets,
    _assert_standing_pins,
    _persist_json,
    _run_cap21_to_cap24_v1,
    _token,
    _utc_now_iso_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.d4_d5_genesis_runtime_orchestrator_v1 import (
    persist_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REQUIRED_CREDENTIAL_CLASS,
    REQUIRED_SECRETREF_URI,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.credential_presence_v1 import (
    default_vault_path_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)

OWNER_GO = "OWNER_GO_FOR_FRESH_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT_V1"
THIS_SLICE = (
    "11.2.1.DN.FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT"
)
EXPECTED_ORIGIN_MAIN_SHA = "5b58f5432fed3ade2b51fff52a52028d5bde5178"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_fresh_runtime_cycle_after_"
    "flatten_occupancy_absent_v1/20260916T003500Z"
)
FALSE_TOKEN = "false"
TRUE_TOKEN = "true"
ENDPOINT_ORDERS_PENDING = "/api/v5/trade/orders-pending"
ENDPOINT_MARKET_INDEX_TICKERS = "/api/v5/market/index-tickers"
STANDING_SEAM_REMAINDER = (
    "OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT"
)
POST_NEXT_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
NON_EXECUTABLE_NEXT_OWNER_GO = (
    "SEPARATE_OWNER_GO_FOR_NEXT_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_NON_EXECUTABLE_DECISION"
)
OCCUPANCY_NEXT_OWNER_GO = "SEPARATE_OWNER_GO_FOR_CURRENT_OCCUPANCY_DISPOSITION_AFTER_FRESH_REPROOF"
DM_PACK = (
    "evidence/ops/full_core_post_flatten_evidence_adjudication_and_canonical_"
    "state_advance_v1/20260916T001500Z"
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_OCCUPANCY_DECISION_ID = "dn-occupancy-reproof-after-flatten-v1"
MAX_GET_REQUEST_COUNT = 24


class CurrentProductiveFreshRuntimeCycleAfterFlattenError(
    CurrentProductiveFreshCap23Cap24ReadinessError
):
    """Fail-closed occupancy-absent runtime-cycle boundary violation."""


@dataclass(frozen=True)
class CurrentProductiveFreshRuntimeCycleAfterFlattenResultV1:
    store_root: str
    occupancy_status: str
    pending_orders_status: str
    cap23_selected_instrument_id: str
    cap23_selection_decision_id: str
    cap23_valid_from: str
    cap23_valid_until: str
    cap24_bound_instrument_id: str
    master_v2_runtime_cycle_id: str
    master_v2_decision_id: str
    master_v2_decision: str
    bull_bear_state: str
    double_play_decision: str
    decision_result: str
    decision_provenance: str
    decision_execution_eligible: str
    sizing_result: str
    risk_admission_result: str
    venue_plan_status: str
    envelope_readiness: str
    final_envelope_id: str
    final_envelope_digest: str
    order_intent_created: str
    permit_created: str
    real_external_effect_authorized: str
    post_count: str
    first_real_blocker: str
    evidence_manifest: str
    manifest_verify_rc: int


def _assert_dn_pins() -> None:
    _assert_standing_pins()
    if CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_AFTER_FLATTEN_OCCUPANCY_ABSENT_CREATED is not True:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError("DN_ADAPTER_NOT_CREATED")


def _transport_payload(
    transport: FullCoreFreshPretradeGetTransportV1,
    *,
    path: str,
    query: Mapping[str, str],
    auth_required: bool,
    native_id: str,
) -> tuple[Any, str]:
    endpoint = f"{path}?{urlencode(dict(query))}" if query else path
    result = transport.get(
        endpoint=endpoint,
        auth_required=auth_required,
        pretrade_decision_id=native_id,
    )
    if result.get_performed is not True or result.payload is None:
        return None, str(result.error_class or "GET_NOT_PERFORMED")
    return result.payload, ""


def _data_rows(payload: Any) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("data")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, Mapping)]


def _open_nonzero_position_rows(payload: Any) -> list[Mapping[str, Any]]:
    open_rows: list[Mapping[str, Any]] = []
    for row in _data_rows(payload):
        text = str(row.get("pos") or "").strip()
        if not text:
            continue
        try:
            if Decimal(text) == 0:
                continue
        except Exception:
            continue
        open_rows.append(row)
    return open_rows


def _enum_token(value: object) -> str:
    if value is None:
        return ""
    raw = getattr(value, "value", value)
    return str(raw)


def _index_ticker_inst_id_v1(native_id: str) -> str:
    text = str(native_id or "").strip()
    if text.endswith("-SWAP"):
        return text[: -len("-SWAP")]
    return text


def _extract_idx_px_v1(payload: Any, *, wanted: str) -> float | None:
    target = str(wanted or "").strip()
    for row in _data_rows(payload):
        inst = str(row.get("instId") or "").strip()
        if inst not in {"", target}:
            continue
        try:
            number = float(row.get("idxPx"))
        except (TypeError, ValueError):
            continue
        if number != number or number in (float("inf"), float("-inf")) or number <= 0:
            continue
        return number
    return None


def _classify_occupancy_v1(
    *,
    positions_payload: Any,
    pending_payload: Any,
    config_payload: Any,
    positions_error: str,
    pending_error: str,
    config_error: str,
) -> dict[str, str]:
    config_rows = _data_rows(config_payload)
    config_row = config_rows[0] if config_rows else {}
    facts = {
        "POSITIONS_GET_ERROR": positions_error,
        "PENDING_GET_ERROR": pending_error,
        "CONFIG_GET_ERROR": config_error,
        "POSITIONS_CODE": str(positions_payload.get("code") or "")
        if isinstance(positions_payload, Mapping)
        else "",
        "PENDING_CODE": str(pending_payload.get("code") or "")
        if isinstance(pending_payload, Mapping)
        else "",
        "CONFIG_CODE": str(config_payload.get("code") or "")
        if isinstance(config_payload, Mapping)
        else "",
        "POSITION_ROW_COUNT": str(len(_data_rows(positions_payload))),
        "OPEN_POSITION_COUNT": "0",
        "PENDING_ROW_COUNT": str(len(_data_rows(pending_payload))),
        "OCCUPANCY_STATUS": "UNKNOWN",
        "PENDING_ORDERS_STATUS": "UNKNOWN",
        "CONFIG_ACCTLV": str(config_row.get("acctLv") or ""),
        "CONFIG_POS_MODE": str(config_row.get("posMode") or ""),
        "OPEN_POSITION_INST_IDS": "",
        "PENDING_INST_IDS": "",
        "OCCUPANCY_ABSENT": FALSE_TOKEN,
    }
    if positions_error or not isinstance(positions_payload, Mapping):
        facts["OCCUPANCY_STATUS"] = f"POSITIONS_GET_FAIL_CLOSED:{positions_error or 'MISSING'}"
        return facts
    if pending_error or not isinstance(pending_payload, Mapping):
        facts["PENDING_ORDERS_STATUS"] = f"PENDING_GET_FAIL_CLOSED:{pending_error or 'MISSING'}"
        facts["OCCUPANCY_STATUS"] = facts["PENDING_ORDERS_STATUS"]
        return facts
    if config_error or not isinstance(config_payload, Mapping):
        facts["OCCUPANCY_STATUS"] = f"CONFIG_GET_FAIL_CLOSED:{config_error or 'MISSING'}"
        return facts
    open_rows = _open_nonzero_position_rows(positions_payload)
    pending_rows = _data_rows(pending_payload)
    facts["OPEN_POSITION_COUNT"] = str(len(open_rows))
    facts["OPEN_POSITION_INST_IDS"] = ",".join(
        str(row.get("instId") or "") for row in open_rows if str(row.get("instId") or "")
    )
    facts["PENDING_INST_IDS"] = ",".join(
        str(row.get("instId") or "") for row in pending_rows if str(row.get("instId") or "")
    )
    if open_rows:
        facts["OCCUPANCY_STATUS"] = "OCCUPANCY_PRESENT"
        facts["OCCUPANCY_ABSENT"] = FALSE_TOKEN
    else:
        facts["OCCUPANCY_STATUS"] = "OCCUPANCY_ABSENT"
        facts["OCCUPANCY_ABSENT"] = TRUE_TOKEN
    facts["PENDING_ORDERS_STATUS"] = "PENDING_ORDERS_PRESENT" if pending_rows else "NONE_OBSERVED"
    return facts


def _replay_consumed_facts_v1(replay: Optional[IntegratedOfflineReplayResultV1]) -> dict[str, str]:
    empty = {
        "MASTER_V2_DECISION_ID": "",
        "MASTER_V2_DECISION": "",
        "BULL_BEAR_STATE": "",
        "DOUBLE_PLAY_DECISION": "",
        "DECISION_TRACE": "",
        "EXECUTION_ELIGIBLE": FALSE_TOKEN,
        "ORDER_INTENT_CREATED": FALSE_TOKEN,
        "SELECTED_SIDE": "",
        "STATE_SWITCH_PREVIOUS": "",
        "STATE_SWITCH_NEXT": "",
        "COMPOSITION_STATUS": "",
        "ENTRY_EXIT_OUTCOME": "",
    }
    if replay is None or replay.evidence is None:
        return empty
    evidence = replay.evidence
    empty["MASTER_V2_DECISION_ID"] = str(evidence.decision_id or "")
    empty["MASTER_V2_DECISION"] = str(evidence.decision_outcome or "")
    empty["BULL_BEAR_STATE"] = str(evidence.next_direction_state or "")
    empty["SELECTED_SIDE"] = str(evidence.selected_side or "")
    empty["DECISION_TRACE"] = ",".join(str(x) for x in (evidence.decision_precedence_trace or ()))
    empty["EXECUTION_ELIGIBLE"] = _token(bool(evidence.execution_eligible))
    intermediate = replay.intermediate
    if intermediate is None:
        empty["DOUBLE_PLAY_DECISION"] = empty["SELECTED_SIDE"]
        return empty
    composition = intermediate.composition_result
    entry = intermediate.entry_exit_decision
    switch = intermediate.state_switch
    empty["COMPOSITION_STATUS"] = _enum_token(getattr(composition, "composition_status", ""))
    empty["DOUBLE_PLAY_DECISION"] = _enum_token(getattr(composition, "selected_side", ""))
    empty["ENTRY_EXIT_OUTCOME"] = _enum_token(getattr(entry, "decision_outcome", ""))
    empty["STATE_SWITCH_PREVIOUS"] = str(getattr(switch, "previous_side_state", "") or "")
    empty["STATE_SWITCH_NEXT"] = str(getattr(switch, "next_side_state", "") or "")
    if empty["BULL_BEAR_STATE"] == "" and empty["STATE_SWITCH_NEXT"]:
        empty["BULL_BEAR_STATE"] = empty["STATE_SWITCH_NEXT"]
    empty["ORDER_INTENT_CREATED"] = _token(intermediate.canonical_order_intent is not None)
    return empty


def execute_current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    evidence_root: Path | None = None,
    vault_file: Path | str | None = None,
    acquisition_transport: EeaPublicUniverseGetPortV1 | None = None,
    acquisition_result: EeaUniverseAcquisitionResultV1 | None = None,
    fresh_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    replay: Optional[IntegratedOfflineReplayResultV1] = None,
    execute_network: bool = False,
    repository_sha: str | None = None,
    producer_observed_at_unix: float | None = None,
) -> CurrentProductiveFreshRuntimeCycleAfterFlattenResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError("OWNER_GO_MISMATCH")
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError("ORIGIN_MAIN_SHA_MISMATCH")
    if execute_network is not True and acquisition_result is None and acquisition_transport is None:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError(
            "EXECUTE_NETWORK_OR_INJECTED_INPUT_REQUIRED"
        )
    _assert_dn_pins()
    del replay
    repo_sha = str(repository_sha or origin_main_sha)
    observed_unix = (
        float(producer_observed_at_unix) if producer_observed_at_unix is not None else time()
    )
    package_started = _utc_now_iso_v1()
    root = _REPO_ROOT
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)

    handle = None
    get_status = "NOT_REACHED"
    if execute_network is True and fresh_get_transport is None:
        resolved_vault = (
            Path(str(vault_file))
            if vault_file is not None and str(vault_file).strip()
            else default_vault_path_v1(repo_root=root)
        )
        try:
            backend = build_file_secretref_vault_backend_v1(vault_file=resolved_vault)
            handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
                secret_reference=REQUIRED_SECRETREF_URI,
                vault_backend=backend,
                credential_class=REQUIRED_CREDENTIAL_CLASS,
            )
            fresh_get_transport = FullCoreProductiveReadOnlyGetTransportV1(
                handle=handle,
                max_request_count=MAX_GET_REQUEST_COUNT,
            )
        except LiveCanaryCredentialError:
            get_status = "CREDENTIAL_HANDLE_FAIL_CLOSED"

    occupancy_facts = {
        "OCCUPANCY_STATUS": "NOT_REACHED",
        "PENDING_ORDERS_STATUS": "NOT_REACHED",
        "OCCUPANCY_ABSENT": FALSE_TOKEN,
        "OPEN_POSITION_COUNT": "",
        "PENDING_ROW_COUNT": "",
        "CONFIG_ACCTLV": "",
        "CONFIG_POS_MODE": "",
        "OPEN_POSITION_INST_IDS": "",
        "PENDING_INST_IDS": "",
        "POSITIONS_GET_ERROR": "",
        "PENDING_GET_ERROR": "",
        "CONFIG_GET_ERROR": "",
        "POSITIONS_CODE": "",
        "PENDING_CODE": "",
        "CONFIG_CODE": "",
        "POSITION_ROW_COUNT": "",
    }
    occupancy_blocker = ""
    if get_status == "CREDENTIAL_HANDLE_FAIL_CLOSED":
        occupancy_blocker = get_status
        occupancy_facts["OCCUPANCY_STATUS"] = get_status
    elif fresh_get_transport is None:
        occupancy_blocker = "FRESH_GET_TRANSPORT_MISSING"
        occupancy_facts["OCCUPANCY_STATUS"] = occupancy_blocker
    else:
        try:
            positions_payload, positions_err = _transport_payload(
                fresh_get_transport,
                path=ENDPOINT_ACCOUNT_POSITIONS,
                query={},
                auth_required=True,
                native_id=_OCCUPANCY_DECISION_ID,
            )
            pending_payload, pending_err = _transport_payload(
                fresh_get_transport,
                path=ENDPOINT_ORDERS_PENDING,
                query={},
                auth_required=True,
                native_id=_OCCUPANCY_DECISION_ID,
            )
            config_payload, config_err = _transport_payload(
                fresh_get_transport,
                path=ENDPOINT_ACCOUNT_CONFIG,
                query={},
                auth_required=True,
                native_id=_OCCUPANCY_DECISION_ID,
            )
            occupancy_facts = _classify_occupancy_v1(
                positions_payload=positions_payload,
                pending_payload=pending_payload,
                config_payload=config_payload,
                positions_error=positions_err,
                pending_error=pending_err,
                config_error=config_err,
            )
        except (
            TypeError,
            RuntimeError,
            ValueError,
            FullCoreProductiveReadOnlyGetError,
        ) as exc:
            occupancy_blocker = f"OCCUPANCY_GET_FAIL_CLOSED:{type(exc).__name__}"
            occupancy_facts["OCCUPANCY_STATUS"] = occupancy_blocker
        else:
            if occupancy_facts["OCCUPANCY_STATUS"] != "OCCUPANCY_ABSENT":
                occupancy_blocker = occupancy_facts["OCCUPANCY_STATUS"]
            elif occupancy_facts["PENDING_ORDERS_STATUS"] != "NONE_OBSERVED":
                occupancy_blocker = occupancy_facts["PENDING_ORDERS_STATUS"]

    identities: dict[str, str] = {}
    bound = None
    cap_status = "NOT_REACHED"
    first_blocker = occupancy_blocker
    if occupancy_blocker:
        if acquisition_result is None:
            acquisition_result = EeaUniverseAcquisitionResultV1(
                ok=False,
                host="",
                venue="",
                source_kind="",
                source_event_time="",
                instruments_payload={},
                mark_price_payload={},
                endpoints_used=(),
                methods_used=(),
                post_count="0",
                request_count=0,
                venue_live_contact=False,
                failure_codes=(occupancy_blocker,),
                provenance={"SKIPPED": "OCCUPANCY_BLOCKER"},
            )
    else:
        if acquisition_result is None:
            try:
                acquisition_result = acquire_eea_universe_inventory_v1(
                    transport=acquisition_transport,
                    observed_at=package_started,
                )
            except EeaUniverseAcquisitionError as exc:
                raise CurrentProductiveFreshRuntimeCycleAfterFlattenError(str(exc)) from exc
        if acquisition_result.ok is not True:
            first_blocker = "EEA_UNIVERSE_ACQUISITION_FAIL_CLOSED"
            cap_status = first_blocker
        else:
            cap_status, identities, bound, _selection = _run_cap21_to_cap24_v1(
                acquisition=acquisition_result,
                store=store,
                repo_sha=repo_sha,
                observed_unix=observed_unix,
            )
            first_blocker = cap_status if cap_status != "PASS" else ""

    positions_payload: Any = None
    if bound is not None and fresh_get_transport is not None:
        try:
            evidence = collect_fresh_pretrade_runtime_get_v1(
                transport=fresh_get_transport,
                pretrade_decision_id=str(bound.venue_native_id),
                instrument_id=str(bound.venue_native_id),
                td_mode="cross",
                limit_px="",
                inst_type="SWAP",
                require_collection=True,
            )
            get_status = str(evidence.evidence_status or "FAIL_CLOSED")
            positions_payload = getattr(fresh_get_transport, "payloads_by_path", {}).get(
                ENDPOINT_ACCOUNT_POSITIONS
            )
        except (
            TypeError,
            RuntimeError,
            ValueError,
            FullCoreProductiveReadOnlyGetError,
        ) as exc:
            get_status = f"FRESH_PRETRADE_GET_FAIL_CLOSED:{type(exc).__name__}"
    elif bound is not None and get_status == "NOT_REACHED":
        get_status = "FRESH_GET_TRANSPORT_MISSING"

    native_id = str(identities.get("cap23_selected_instrument_id") or "")
    cycle_result = None
    market_blocker = ""
    market_payloads: dict[str, Any] = {}
    position_status = occupancy_facts.get("OCCUPANCY_STATUS") or ""
    venue_flat = occupancy_facts.get("OCCUPANCY_ABSENT") == TRUE_TOKEN
    existing_side = ExistingPositionSide.NONE
    if bound is not None and get_status == FreshPretradeGetStatusV1.TRUSTED_PRESENT.value:
        if fresh_get_transport is None:
            market_blocker = "FRESH_GET_TRANSPORT_MISSING"
        else:
            pos_status, venue_flat, existing_side = extract_position_truth_v1(
                positions_payload, native_id=native_id
            )
            position_status = pos_status
            if pos_status == "FOREIGN_OPEN_POSITION_MAX_POSITIONS_1":
                market_blocker = pos_status
            ticker_payload = candles_payload = oi_payload = funding_payload = None
            ticker_err = candles_err = oi_err = funding_err = ""
            if not market_blocker:
                try:
                    ticker_payload, ticker_err = _transport_payload(
                        fresh_get_transport,
                        path=ENDPOINT_MARKET_TICKER,
                        query={"instId": native_id},
                        auth_required=False,
                        native_id=native_id,
                    )
                    candles_payload, candles_err = _transport_payload(
                        fresh_get_transport,
                        path=ENDPOINT_MARKET_CANDLES,
                        query={"instId": native_id, "bar": "1m", "limit": "100"},
                        auth_required=False,
                        native_id=native_id,
                    )
                    oi_payload, oi_err = _transport_payload(
                        fresh_get_transport,
                        path=ENDPOINT_PUBLIC_OPEN_INTEREST,
                        query={"instId": native_id},
                        auth_required=False,
                        native_id=native_id,
                    )
                    funding_payload, funding_err = _transport_payload(
                        fresh_get_transport,
                        path=ENDPOINT_PUBLIC_FUNDING_RATE,
                        query={"instId": native_id},
                        auth_required=False,
                        native_id=native_id,
                    )
                except (
                    TypeError,
                    RuntimeError,
                    ValueError,
                    FullCoreProductiveReadOnlyGetError,
                ) as exc:
                    market_blocker = (
                        market_blocker or f"MARKET_GET_FAIL_CLOSED:{type(exc).__name__}"
                    )
                    ticker_payload = candles_payload = oi_payload = funding_payload = None
                    ticker_err = candles_err = oi_err = funding_err = type(exc).__name__
            market_payloads = {
                "ticker_error": ticker_err,
                "candles_error": candles_err,
                "oi_error": oi_err,
                "funding_error": funding_err,
            }
            mark_px, index_from_mark = extract_mark_and_index_from_payload_v1(
                acquisition_result.mark_price_payload, native_id=native_id
            )
            bid, ask, volume, index_from_ticker = extract_ticker_fields_v1(
                ticker_payload, native_id=native_id
            )
            index_px = index_from_mark if index_from_mark is not None else index_from_ticker
            if index_px is None and not market_blocker:
                index_inst = _index_ticker_inst_id_v1(native_id)
                index_payload, index_ticker_err = _transport_payload(
                    fresh_get_transport,
                    path=ENDPOINT_MARKET_INDEX_TICKERS,
                    query={"instId": index_inst},
                    auth_required=False,
                    native_id=native_id,
                )
                market_payloads["index_tickers_error"] = index_ticker_err
                market_payloads["index_tickers_inst_id"] = index_inst
                index_px = _extract_idx_px_v1(index_payload, wanted=index_inst)
            oi = extract_open_interest_v1(oi_payload, native_id=native_id)
            funding = extract_funding_rate_v1(funding_payload, native_id=native_id)
            closes, last_ts = extract_finalized_candle_closes_v1(candles_payload)
            missing = []
            if mark_px is None:
                missing.append("MARK_PX")
            if index_px is None:
                missing.append("INDEX_PX")
            if bid is None or ask is None:
                missing.append("BID_ASK")
            if volume is None:
                missing.append("VOLUME")
            if oi is None:
                missing.append("OPEN_INTEREST")
            if funding is None:
                missing.append("FUNDING_RATE")
            if not closes or last_ts is None:
                missing.append("FINALIZED_CANDLES")
            if ticker_err or candles_err or oi_err or funding_err:
                missing.append("MARKET_GET_ERROR")
            if missing and not market_blocker:
                market_blocker = "MASTER_V2_REQUIRED_GET_INCOMPLETE:" + ",".join(missing)
            elif not market_blocker:
                try:
                    cycle_result = run_current_productive_master_v2_runtime_cycle_v1(
                        bound_instrument=bound,
                        cycle_id=f"dn-{native_id}-{package_started}",
                        observed_unix=observed_unix,
                        mark_px=float(mark_px),
                        index_px=float(index_px),
                        bid_px=float(bid),
                        ask_px=float(ask),
                        volume=float(volume),
                        open_interest=float(oi),
                        funding_rate=float(funding),
                        finalized_closes=closes,
                        last_finalized_event_ts_unix=float(last_ts),
                        venue_flat=venue_flat,
                        existing_position_side=existing_side,
                    )
                except (TypeError, RuntimeError, ValueError) as exc:
                    market_blocker = f"MASTER_V2_RUNTIME_CYCLE_FAIL_CLOSED:{type(exc).__name__}"
                else:
                    if cycle_result.input_blocker:
                        market_blocker = cycle_result.input_blocker
                    market_payloads["finalized_close_count"] = str(len(closes))
                    market_payloads["mark_px_observed"] = str(mark_px)
    if handle is not None:
        release_live_canary_ephemeral_material_v1(handle)

    cycle_replay = None
    cycle_id = ""
    cycle_provenance = CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    if cycle_result is not None and cycle_result.replay is not None:
        cycle_replay = cycle_result.replay
        cycle_id = cycle_result.cycle_id
        cycle_provenance = cycle_result.provenance
    elif occupancy_blocker:
        cycle_provenance = occupancy_blocker
    elif market_blocker:
        cycle_provenance = market_blocker
    elif bound is None:
        cycle_provenance = first_blocker or CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
    replay_facts = _replay_consumed_facts_v1(cycle_replay)

    decision_result = "NO_EXECUTABLE_DECISION"
    decision_provenance = cycle_provenance
    venue_plan_status = "NONE"
    envelope_readiness = FALSE_TOKEN
    plan = None
    sizing_result = "NOT_REACHED"
    risk_admission_result = "NOT_REACHED"
    if occupancy_blocker or market_blocker:
        venue_plan_status = "DENY"
        risk_admission_result = "DENY"
        decision_provenance = occupancy_blocker or market_blocker
    if bound is not None and not occupancy_blocker and not market_blocker:
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=cycle_replay,
            bound_instrument=bound,
            session_id="current-productive-dn-session",
            run_id="current-productive-dn-run",
            composed_epoch=package_started,
        )
        decision_provenance = ",".join(reasons) if reasons else cycle_provenance
        if status is CompositionStatusV1.PASS and plan is not None:
            decision_result = "EXECUTABLE_VENUE_PLAN_BOUND"
            venue_plan_status = "PASS"
            envelope_readiness = TRUE_TOKEN
            risk_admission_result = "PASS"
        else:
            decision_result = "NO_EXECUTABLE_DECISION"
            venue_plan_status = status.value if hasattr(status, "value") else str(status)
            risk_admission_result = venue_plan_status
    if cycle_replay is not None and cycle_replay.intermediate is not None:
        sizing = cycle_replay.intermediate.capital_risk_sizing_decision
        if sizing is not None:
            sizing_result = str(getattr(sizing.outcome, "value", sizing.outcome))
        else:
            sizing_result = "MISSING_29P"

    trusted_get = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value
    next_owner_go = NON_EXECUTABLE_NEXT_OWNER_GO
    if occupancy_blocker:
        first_blocker = occupancy_blocker
        next_owner_go = OCCUPANCY_NEXT_OWNER_GO
    elif cap_status != "PASS":
        first_blocker = cap_status
        next_owner_go = NON_EXECUTABLE_NEXT_OWNER_GO
    elif get_status != trusted_get:
        first_blocker = f"FRESH_PRE_SUBMIT_EVIDENCE_FAIL_CLOSED:{get_status}"
        next_owner_go = NON_EXECUTABLE_NEXT_OWNER_GO
    elif market_blocker:
        first_blocker = market_blocker
        next_owner_go = NON_EXECUTABLE_NEXT_OWNER_GO
    elif decision_result != "EXECUTABLE_VENUE_PLAN_BOUND":
        first_blocker = decision_provenance or CURRENT_MASTER_V2_RUNTIME_CYCLE_ABSENT
        next_owner_go = NON_EXECUTABLE_NEXT_OWNER_GO
    else:
        first_blocker = POST_NEXT_OWNER_GO
        next_owner_go = POST_NEXT_OWNER_GO

    send_handle = FullCoreSendCredentialHandleV1(
        handle_id="full-core-dn-readiness-handle", bound=True
    )
    http_transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=send_handle)
    try:
        http_transport.post_trade_order(
            payload={"instId": identities.get("cap23_selected_instrument_id") or "MUST_NOT_POST"},
            permit_id="eep-dn-must-not-post",
            envelope_id="env-dn-must-not-post",
            envelope_digest="0" * 64,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveFreshRuntimeCycleAfterFlattenError(
                "HTTP_FORBIDDEN_MISSING"
            ) from exc
    else:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError("HTTP_MUST_NOT_POST")
    if http_transport.post_count != 0:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError("HTTP_TRANSPORT_SIDE_EFFECT")

    envelope_id = ""
    envelope_digest = ""
    envelope_fields: dict[str, str] = {}
    if plan is not None and envelope_readiness == TRUE_TOKEN:
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref="DN_FRESH_CAP24_AND_CURRENT_PRODUCTIVE_MASTER_V2",
            provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
            creation_epoch=package_started,
        )
        envelope_id = envelope.envelope_id
        envelope_digest = envelope.envelope_digest
        envelope_fields = {
            "instrument_id": envelope.instrument_id,
            "side": envelope.side,
            "quantity": envelope.quantity,
            "order_type": envelope.order_type,
            "td_mode": envelope.td_mode,
        }
    standing_blocker = current_productive_first_real_blocker_v1()
    if standing_blocker != STANDING_SEAM_REMAINDER:
        raise CurrentProductiveFreshRuntimeCycleAfterFlattenError(
            f"BLOCKER_DRIFT:{standing_blocker}"
        )

    decision_eligible = (
        TRUE_TOKEN if decision_result == "EXECUTABLE_VENUE_PLAN_BOUND" else FALSE_TOKEN
    )
    cap23_status = "BOUND" if identities.get("cap23_selected_instrument_id") else "NOT_BOUND"
    cap24_status = "BOUND" if identities.get("cap24_bound_instrument_id") else "NOT_BOUND"
    if occupancy_blocker:
        cap23_status = "NOT_REACHED"
        cap24_status = "NOT_REACHED"
    elif cap_status != "PASS" and cap_status != "NOT_REACHED":
        cap23_status = cap_status if cap_status.startswith("CAP23") else cap23_status
        cap24_status = cap_status if cap_status.startswith("CAP24") else cap24_status
    claims = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GO": OWNER_GO,
        "EXPECTED_ORIGIN_MAIN": origin_main_sha,
        "RESELECTION_AUTHORIZED_BY_THIS_GO": TRUE_TOKEN,
        "RESELECTION_PERFORMED": _token(bound is not None),
        "CANARY_INSTRUMENT_AUTHORITY_IMPORTED": FALSE_TOKEN,
        "HISTORICAL_POSITION_OWNERSHIP": "UNKNOWN_NOT_PROVEN",
        "OCCUPANCY_STATUS": occupancy_facts.get("OCCUPANCY_STATUS", ""),
        "OCCUPANCY_ABSENT": occupancy_facts.get("OCCUPANCY_ABSENT", FALSE_TOKEN),
        "CURRENT_POSITION_STATE": occupancy_facts.get("OCCUPANCY_STATUS", ""),
        "CURRENT_PENDING_ORDERS": occupancy_facts.get("PENDING_ORDERS_STATUS", ""),
        "OPEN_POSITION_COUNT": occupancy_facts.get("OPEN_POSITION_COUNT", ""),
        "PENDING_ROW_COUNT": occupancy_facts.get("PENDING_ROW_COUNT", ""),
        "CONFIG_ACCTLV": occupancy_facts.get("CONFIG_ACCTLV", ""),
        "CONFIG_POS_MODE": occupancy_facts.get("CONFIG_POS_MODE", ""),
        "CAP21_SNAPSHOT_ID": identities.get("cap21_snapshot_id", ""),
        "CAP21_EVENT_TIME": identities.get("cap21_event_time", ""),
        "CAP21_UNIVERSE_SIZE": identities.get("cap21_universe_size", ""),
        "CAP22_RANKING_ID": identities.get("cap22_ranking_id", ""),
        "CAP22_RANKING_EPOCH": identities.get("cap22_ranking_epoch", ""),
        "CAP23_BINDING_STATUS": cap23_status,
        "CAP23_SELECTION_DECISION_ID": identities.get("cap23_selection_decision_id", ""),
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP23_VALID_FROM": identities.get("cap23_valid_from", ""),
        "CAP23_VALID_UNTIL": identities.get("cap23_valid_until", ""),
        "CAP23_INPUTS": (
            "CAP21_SNAPSHOT="
            + identities.get("cap21_snapshot_id", "")
            + ";CAP22_RANKING="
            + identities.get("cap22_ranking_id", "")
        ),
        "CAP23_OUTPUT": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BINDING_STATUS": cap24_status,
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "CAP24_INPUTS": (
            "CAP23_SELECTION="
            + identities.get("cap23_selection_decision_id", "")
            + ";OCCUPANCY="
            + occupancy_facts.get("OCCUPANCY_STATUS", "")
        ),
        "CAP24_OUTPUT": identities.get("cap24_bound_instrument_id", ""),
        "CAP23_SELECTION_PROVENANCE": "CURRENT_CAP21_CAP22_CAP23_PRODUCERS",
        "MASTER_V2_RUNTIME_CYCLE_ID": cycle_id,
        "MASTER_V2_RUNTIME_CYCLE_PROVENANCE": (
            cycle_result.provenance if cycle_result is not None else cycle_provenance
        ),
        "MASTER_V2_DECISION_ID": replay_facts["MASTER_V2_DECISION_ID"],
        "MASTER_V2_DECISION": replay_facts["MASTER_V2_DECISION"],
        "BULL_BEAR_STATE": replay_facts["BULL_BEAR_STATE"],
        "DOUBLE_PLAY_DECISION": replay_facts["DOUBLE_PLAY_DECISION"],
        "DECISION_TRACE": replay_facts["DECISION_TRACE"],
        "CURRENT_PRODUCTIVE_DECISION_RESULT": decision_result,
        "CURRENT_PRODUCTIVE_DECISION_PROVENANCE": decision_provenance,
        "DECISION_EXECUTION_ELIGIBLE": decision_eligible,
        "SIZING_RESULT": sizing_result,
        "RISK_ADMISSION_RESULT": risk_admission_result,
        "CURRENT_PRODUCTIVE_VENUE_PLAN_STATUS": venue_plan_status,
        "ENVELOPE_READINESS": envelope_readiness,
        "FINAL_ENVELOPE_CREATED": _token(bool(envelope_id)),
        "FINAL_ENVELOPE_ID": envelope_id,
        "FINAL_ENVELOPE_DIGEST": envelope_digest,
        "ENVELOPE_EXECUTION_FIELDS": ",".join(
            f"{key}={value}" for key, value in envelope_fields.items()
        ),
        "ORDER_INTENT_CREATED": replay_facts["ORDER_INTENT_CREATED"],
        "FRESH_PRE_SUBMIT_EVIDENCE": get_status,
        "POSITION_TRUTH_STATUS": position_status,
        "ONE_SHOT_REAL_POST_SEAM_IMPLEMENTED": TRUE_TOKEN,
        "EXACT_ENVELOPE_BOUND_PERMIT_READINESS": _token(bool(envelope_id)),
        "PERMIT_CREATED": FALSE_TOKEN,
        "PERMIT_CONSUMED_DURABLY": FALSE_TOKEN,
        "EXTERNAL_EFFECT_PERMIT_CREATED": FALSE_TOKEN,
        "LIVE_AUTHORIZED": TRUE_TOKEN,
        "LIVE_ARMED": TRUE_TOKEN,
        "WIRE_SEND_PERMITTED": TRUE_TOKEN,
        "SUBMISSION_AUTHORIZED": TRUE_TOKEN,
        "EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "REAL_VENUE_POST_ALLOWED": FALSE_TOKEN,
        "POST_ALLOWED": FALSE_TOKEN,
        "STEP_29Q_STATUS": STEP_29Q_PLAN_ONLY,
        "MAX_POST_COUNT": "1",
        "POST_COUNT": "0",
        "TRANSPORT_ATTEMPTED": FALSE_TOKEN,
        "ACTUAL_ORDER_SUBMIT_PERFORMED": FALSE_TOKEN,
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "MAX_POSITIONS_EFFECTIVE": "1",
        "STANDING_SEAM_REMAINDER": STANDING_SEAM_REMAINDER,
        "STANDING_SEAM_REMAINDER_CLASS": (
            "CURRENT_PRODUCTIVE_NEXT_BLOCKER"
            if decision_result == "EXECUTABLE_VENUE_PLAN_BOUND"
            else "LEGACY_NON_BLOCKING_UNTIL_EXECUTABLE_VENUE_PLAN"
        ),
        "FIRST_REAL_BLOCKER": first_blocker,
        "NEXT_OWNER_GO_REQUIRED": next_owner_go,
        "PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED": TRUE_TOKEN,
        "TRADING_LOGIC_CHANGES_FOUND": FALSE_TOKEN,
        "RANKING_ALGORITHM_CHANGED": FALSE_TOKEN,
        "SELECTION_ALGORITHM_CHANGED": FALSE_TOKEN,
        "UNIVERSE_SEMANTICS_CHANGED": FALSE_TOKEN,
        "LEARNING_LOGIC_CHANGED": FALSE_TOKEN,
        "SAFETY_AUTHORITY_WEAKENED": FALSE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_CHANGED": FALSE_TOKEN,
        "PROTECTED_SURFACES_CHANGED": FALSE_TOKEN,
        "SECTION_11_14_REWRITTEN": FALSE_TOKEN,
        "RUNTIME_AUTHORIZATION_EFFECT": "NONE",
        "PACKAGE_STARTED_UTC": package_started,
        "PACKAGE_FINISHED_UTC": _utc_now_iso_v1(),
    }
    lineage = {
        "OWNER_GO": OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "DM_PACK": DM_PACK,
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "MASTER_V2_RUNTIME_CYCLE_ID": cycle_id,
        "MASTER_V2_DECISION_ID": replay_facts["MASTER_V2_DECISION_ID"],
        "DECISION_PROVENANCE": decision_provenance,
        "OCCUPANCY_STATUS": occupancy_facts.get("OCCUPANCY_STATUS", ""),
    }
    protected = {
        "MASTER_V2_UNCHANGED": TRUE_TOKEN,
        "DOUBLE_PLAY_UNCHANGED": TRUE_TOKEN,
        "UNIVERSE_MEMBERSHIP_SEMANTICS_UNCHANGED": TRUE_TOKEN,
        "RANKING_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "SELECTION_ALGORITHM_UNCHANGED": TRUE_TOKEN,
        "LEARNING_UNCHANGED": TRUE_TOKEN,
        "FULL_CORE_SAFETY_ADMISSION_AUTHORITY_UNCHANGED": TRUE_TOKEN,
        "CANARY_FULL_CORE_BOUNDARY_UNCHANGED": TRUE_TOKEN,
        "STEP_29Q_UNCHANGED_PLAN_ONLY": TRUE_TOKEN,
        "EXTERNAL_EFFECT_STANDING_UNCHANGED_FALSE": TRUE_TOKEN,
        "MAX_POSITIONS_UNCHANGED_1": TRUE_TOKEN,
        "SECTION_11_14_UNCHANGED": TRUE_TOKEN,
    }
    summary = {
        "FIRST_REAL_BLOCKER": first_blocker,
        "OCCUPANCY_STATUS": occupancy_facts.get("OCCUPANCY_STATUS", ""),
        "CURRENT_PENDING_ORDERS": occupancy_facts.get("PENDING_ORDERS_STATUS", ""),
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "MASTER_V2_RUNTIME_CYCLE_ID": cycle_id,
        "MASTER_V2_DECISION_ID": replay_facts["MASTER_V2_DECISION_ID"],
        "MASTER_V2_DECISION": replay_facts["MASTER_V2_DECISION"],
        "BULL_BEAR_STATE": replay_facts["BULL_BEAR_STATE"],
        "DOUBLE_PLAY_DECISION": replay_facts["DOUBLE_PLAY_DECISION"],
        "CURRENT_PRODUCTIVE_DECISION_RESULT": decision_result,
        "DECISION_EXECUTION_ELIGIBLE": decision_eligible,
        "ORDER_INTENT_CREATED": replay_facts["ORDER_INTENT_CREATED"],
        "ENVELOPE_READINESS": envelope_readiness,
        "FINAL_ENVELOPE_ID": envelope_id,
        "PERMIT_CREATED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_PERMIT_CREATED": FALSE_TOKEN,
        "REAL_EXTERNAL_EFFECT_AUTHORIZED": FALSE_TOKEN,
        "POST_COUNT": "0",
        "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
        "PRE_EXTERNAL_EFFECT_BOUNDARY_REACHED": TRUE_TOKEN,
        "HARD_STOP": TRUE_TOKEN,
    }
    bound_payload = {"BOUND_INSTRUMENT": bound.to_dict() if bound is not None else {}}
    acquisition_payload = {
        "HOST": acquisition_result.host,
        "ENDPOINTS": list(acquisition_result.endpoints_used),
        "METHODS": list(acquisition_result.methods_used),
        "POST_COUNT": "0",
        "PROVENANCE": dict(acquisition_result.provenance),
        "OK": acquisition_result.ok,
    }
    cycle_payload = {
        "CYCLE_ID": cycle_id,
        "PROVENANCE": cycle_result.provenance if cycle_result is not None else cycle_provenance,
        "DECISION_OUTCOME": cycle_result.decision_outcome if cycle_result is not None else "",
        "REPLAY_PASS": cycle_result.replay_pass if cycle_result is not None else FALSE_TOKEN,
        "FAIL_REASONS": list(cycle_result.fail_reasons) if cycle_result is not None else [],
        "INPUT_DIGEST": cycle_result.input_digest if cycle_result is not None else "",
        "INPUT_BLOCKER": cycle_result.input_blocker if cycle_result is not None else market_blocker,
        "MARKET": {key: str(value) for key, value in market_payloads.items()},
        "CONSUMED": replay_facts,
    }
    occupancy_payload = dict(occupancy_facts)
    for payload in (
        claims,
        lineage,
        protected,
        summary,
        bound_payload,
        acquisition_payload,
        cycle_payload,
        occupancy_payload,
    ):
        _assert_no_secrets(payload)
    _persist_json(path=store / "claims.json", payload=claims)
    _persist_json(path=store / "SUMMARY.json", payload=summary)
    _persist_json(path=store / "LINEAGE.json", payload=lineage)
    _persist_json(path=store / "protected_surfaces_v1.json", payload=protected)
    _persist_json(path=store / "bound_instrument_v1.json", payload=bound_payload)
    _persist_json(path=store / "acquisition_v1.json", payload=acquisition_payload)
    _persist_json(path=store / "master_v2_runtime_cycle_v1.json", payload=cycle_payload)
    _persist_json(path=store / "occupancy_v1.json", payload=occupancy_payload)
    persist_manifest_sha256_v1(store_root=store)
    manifest_rc = verify_manifest_sha256_v1(store_root=store)
    return CurrentProductiveFreshRuntimeCycleAfterFlattenResultV1(
        store_root=str(store),
        occupancy_status=occupancy_facts.get("OCCUPANCY_STATUS", ""),
        pending_orders_status=occupancy_facts.get("PENDING_ORDERS_STATUS", ""),
        cap23_selected_instrument_id=identities.get("cap23_selected_instrument_id", ""),
        cap23_selection_decision_id=identities.get("cap23_selection_decision_id", ""),
        cap23_valid_from=identities.get("cap23_valid_from", ""),
        cap23_valid_until=identities.get("cap23_valid_until", ""),
        cap24_bound_instrument_id=identities.get("cap24_bound_instrument_id", ""),
        master_v2_runtime_cycle_id=cycle_id,
        master_v2_decision_id=replay_facts["MASTER_V2_DECISION_ID"],
        master_v2_decision=replay_facts["MASTER_V2_DECISION"],
        bull_bear_state=replay_facts["BULL_BEAR_STATE"],
        double_play_decision=replay_facts["DOUBLE_PLAY_DECISION"],
        decision_result=decision_result,
        decision_provenance=decision_provenance,
        decision_execution_eligible=decision_eligible,
        sizing_result=sizing_result,
        risk_admission_result=risk_admission_result,
        venue_plan_status=venue_plan_status,
        envelope_readiness=envelope_readiness,
        final_envelope_id=envelope_id,
        final_envelope_digest=envelope_digest,
        order_intent_created=replay_facts["ORDER_INTENT_CREATED"],
        permit_created=FALSE_TOKEN,
        real_external_effect_authorized=FALSE_TOKEN,
        post_count="0",
        first_real_blocker=first_blocker,
        evidence_manifest=str(store / "MANIFEST.sha256"),
        manifest_verify_rc=manifest_rc,
    )
