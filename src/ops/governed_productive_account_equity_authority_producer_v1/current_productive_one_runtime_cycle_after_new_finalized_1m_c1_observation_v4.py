"""CURRENT_PRODUCTIVE one cycle after a new finalized 1m C1 observation V4.

Consumes Owner-GO
OWNER_GO_CONDITION_GATED_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_C1_BOUNDARY_1789526340_V1.

Phase 1 is a READ-ONLY public candles GET for 0G-USDT-SWAP. A cycle runs only
when a confirm=1 1m candle has venue_event_time > 1789526340.0. Cap-23 is not
forced. Cursor restore remains exact schema/native/instrument/lineage. Does
not POST. Does not mint an external-effect permit. Does not poll. Does not
rewrite the consumed V1/V2/V3 DV standing persist.

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
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CurrentProductiveCursorError,
    load_current_productive_sidestate_confirmation_cursor_v1,
    persist_current_productive_sidestate_confirmation_cursor_v1,
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
    CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_AFTER_NON_EXECUTABLE_DECISION_V3_CREATED,
    CURRENT_PRODUCTIVE_FRESH_RUNTIME_FROM_PERSISTED_CURSOR_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_CREATED,
    CURRENT_PRODUCTIVE_FRESH_RUNTIME_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_CREATED,
    CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V2_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V3_CREATED,
    CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED,
    CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_CREATED,
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
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    map_signal_strength_to_confirmation_assessment_signal_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    _default_policies,
)

OWNER_GO = (
    "OWNER_GO_CONDITION_GATED_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_AFTER_C1_BOUNDARY_1789526340_V1"
)
THIS_SLICE = "11.2.1.DV.FULL_CORE_CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4"
EXPECTED_ORIGIN_MAIN_SHA = "30d8ec5e3779991f9bda145d3cde38241602e5e1"
CANONICAL_PACK_RELPATH = (
    "evidence/ops/full_core_current_productive_one_runtime_cycle_after_new_"
    "finalized_1m_c1_observation_v4/20260916T030300Z"
)
DV_V3_PACK = (
    "evidence/ops/full_core_current_productive_one_runtime_cycle_after_new_"
    "finalized_1m_c1_observation_v3/20260916T024000Z"
)
DV_V2_PACK = (
    "evidence/ops/full_core_current_productive_one_runtime_cycle_after_new_"
    "finalized_1m_c1_observation_v2/20260916T021300Z"
)
DV_V1_PACK = (
    "evidence/ops/full_core_current_productive_one_runtime_cycle_after_new_"
    "finalized_1m_c1_observation_v1/20260916T014000Z"
)
DU_PACK = (
    "evidence/ops/full_core_current_productive_fresh_runtime_from_persisted_"
    "cursor_to_pre_external_effect_applicability_v1/20260916T012200Z"
)
DT_PACK = (
    "evidence/ops/full_core_current_productive_fresh_runtime_to_pre_external_"
    "effect_applicability_v1/20260916T011000Z"
)
PREVIOUS_CYCLE_ID = "dv-0G-USDT-SWAP-2026-09-16T02:40:12Z"
PREVIOUS_C1_VENUE_EVENT_TIME = 1789526340.0
C1_GATE_NATIVE_ID = "0G-USDT-SWAP"
C1_GATE_BAR = "1m"
CURRENT_CURSOR_STORE_RELPATH = (
    "evidence/ops/full_core_current_productive_sidestate_confirmation_cursor_current_v1"
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
    "SEPARATE_OWNER_GO_FOR_NEXT_CURRENT_PRODUCTIVE_RUNTIME_CYCLE_FROM_PERSISTED_CURSOR"
)
OCCUPANCY_NEXT_OWNER_GO = "SEPARATE_OWNER_GO_FOR_CURRENT_OCCUPANCY_DISPOSITION_AFTER_FRESH_REPROOF"
DQ_PACK = (
    "evidence/ops/full_core_current_productive_fresh_runtime_cycle_after_"
    "non_executable_decision_v3/20260915T234800Z"
)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_OCCUPANCY_DECISION_ID = "dv-occupancy-reproof-after-c1-gate-v4"
MAX_GET_REQUEST_COUNT = 24
C1_GATE_MAX_REQUEST_COUNT = 1


class CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
    CurrentProductiveFreshCap23Cap24ReadinessError
):
    """Fail-closed C1-gated one-cycle pre-external-effect boundary violation."""


@dataclass(frozen=True)
class CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationResultV1:
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
    condition_gate: str
    newest_finalized_1m_venue_event_time: str
    runtime_cycle_count: str


def _assert_dv_pins() -> None:
    _assert_standing_pins()
    if CURRENT_PRODUCTIVE_FRESH_RUNTIME_CYCLE_AFTER_NON_EXECUTABLE_DECISION_V3_CREATED is not True:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DQ_ADAPTER_NOT_CREATED"
        )
    if CURRENT_PRODUCTIVE_ONESHOT_SIDESTATE_CONFIRMATION_CURSOR_JOIN_CREATED is not True:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DR_ADAPTER_NOT_CREATED"
        )
    if CURRENT_PRODUCTIVE_HOST_ENTER_29P_INVALID_STOP_PRICE_REPAIR_CREATED is not True:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DS_ADAPTER_NOT_CREATED"
        )
    if CURRENT_PRODUCTIVE_FRESH_RUNTIME_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_CREATED is not True:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DT_ADAPTER_NOT_CREATED"
        )
    if (
        CURRENT_PRODUCTIVE_FRESH_RUNTIME_FROM_PERSISTED_CURSOR_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_CREATED
        is not True
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DU_ADAPTER_NOT_CREATED"
        )
    if (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_CREATED
        is not True
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DV_ADAPTER_NOT_CREATED"
        )
    if (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V2_CREATED
        is not True
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DV_V2_ADAPTER_NOT_CREATED"
        )
    if (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V3_CREATED
        is not True
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DV_V3_ADAPTER_NOT_CREATED"
        )
    if (
        CURRENT_PRODUCTIVE_ONE_RUNTIME_CYCLE_AFTER_NEW_FINALIZED_1M_C1_OBSERVATION_V4_CREATED
        is not True
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "DV_V4_ADAPTER_NOT_CREATED"
        )


def _newest_finalized_1m_identity_v1(payload: Any) -> dict[str, Any]:
    closes, last_ts = extract_finalized_candle_closes_v1(payload)
    newest: dict[str, Any] = {
        "finalized_close_count": len(closes),
        "newest_finalized_venue_event_time": last_ts,
        "confirm": "1" if last_ts is not None else "",
        "close": closes[-1] if closes else None,
    }
    if not isinstance(payload, Mapping):
        return newest
    rows = payload.get("data")
    if not isinstance(rows, list) or last_ts is None:
        return newest
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) < 9:
            continue
        if str(row[8] or "").strip() != "1":
            continue
        try:
            ts = float(row[0]) / 1000.0
        except (TypeError, ValueError):
            continue
        if ts == float(last_ts):
            newest["ts_ms"] = row[0]
            newest["close"] = row[4]
            newest["confirm"] = "1"
            break
    return newest


def _evaluate_c1_gate_v1(
    *,
    payload: Any,
    http_status: int = 0,
    error_class: str = "",
    get_performed: bool = False,
    body_sha256: str = "",
) -> dict[str, str]:
    identity = _newest_finalized_1m_identity_v1(payload)
    last_ts = identity.get("newest_finalized_venue_event_time")
    satisfied = last_ts is not None and float(last_ts) > float(PREVIOUS_C1_VENUE_EVENT_TIME)
    return {
        "CONDITION_GATE": "SATISFIED" if satisfied else "NOT_YET_SATISFIED",
        "PREVIOUS_C1_VENUE_EVENT_TIME": str(PREVIOUS_C1_VENUE_EVENT_TIME),
        "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": "" if last_ts is None else str(last_ts),
        "NEW_C1_EVIDENCE_AVAILABLE": _token(satisfied),
        "C1_GATE_NATIVE_ID": C1_GATE_NATIVE_ID,
        "C1_GATE_BAR": C1_GATE_BAR,
        "CONFIRM": str(identity.get("confirm") or ""),
        "CLOSE": str(identity.get("close") or ""),
        "TS_MS": str(identity.get("ts_ms") or ""),
        "FINALIZED_CLOSE_COUNT": str(identity.get("finalized_close_count") or 0),
        "GET_PERFORMED": _token(get_performed),
        "HTTP_STATUS": str(http_status),
        "ERROR_CLASS": error_class,
        "BODY_SHA256": body_sha256,
        "AUTH_HEADER_SENT": FALSE_TOKEN,
        "POST_COUNT": "0",
        "SELECTION_FORCED": FALSE_TOKEN,
    }


def _signal_class_from_assessment_v1(assessment: object) -> str:
    strength = getattr(assessment, "signal_strength", None)
    if strength is None:
        return ""
    try:
        signal = map_signal_strength_to_confirmation_assessment_signal_v1(
            float(strength),
            _default_policies().directional,
        )
    except (TypeError, ValueError):
        return ""
    return str(getattr(signal, "value", signal) or "")


def _confirmation_transition_class_v1(*, before: str, after: str) -> str:
    before_state = ""
    after_state = ""
    for part in str(before or "").split(";"):
        if part.startswith("bull_state="):
            before_state = part.split("=", 1)[1]
    for part in str(after or "").split(";"):
        if part.startswith("bull_state="):
            after_state = part.split("=", 1)[1]
    if not before_state and not after_state:
        return "NOT_REACHED"
    if before_state == "observe" and after_state == "observe":
        return "OBSERVE_TO_OBSERVE"
    if before_state == "observe" and after_state == "candidate":
        return "OBSERVE_TO_CANDIDATE"
    if before_state == "candidate" and after_state == "observe":
        return "CANDIDATE_TO_RESET"
    if before_state == "candidate" and after_state == "confirmed":
        return "CANDIDATE_TO_CONFIRMED"
    if before_state == "confirmed" and after_state == "observe":
        return "CONFIRMED_TO_RESET"
    if before_state == after_state:
        return "HOLD_" + before_state.upper() if before_state else "UNCHANGED"
    return "BULL_" + before_state.upper() + "_TO_" + after_state.upper()


def _c1_classification_v1(
    *, epoch_before: int, epoch_after: int, event_before: str, event_after: str
) -> str:
    if epoch_after == epoch_before + 1 and event_after and event_after != event_before:
        return "DISTINCT"
    if epoch_after == epoch_before:
        if event_after == event_before:
            return "DUPLICATE_OR_NON_DISTINCT"
        return "NON_DISTINCT_NO_EPOCH_ADVANCE"
    if epoch_after == 0 and epoch_before == 0:
        return "NOT_REACHED"
    return "UNRESOLVED_EPOCH_DELTA"


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


def _cursor_identity_v1(cursor: object) -> str:
    if cursor is None:
        return ""
    if hasattr(cursor, "to_dict"):
        payload = cursor.to_dict()
    elif isinstance(cursor, Mapping):
        payload = dict(cursor)
    else:
        return ""
    confirmation = payload.get("scope_confirmation")
    if not isinstance(confirmation, Mapping):
        confirmation = {}
    return (
        "instrument="
        + str(payload.get("instrument_id") or "")
        + ";native="
        + str(payload.get("venue_native_id") or "")
        + ";lineage="
        + str(payload.get("lineage_id") or "")
        + ";schema="
        + str(payload.get("schema_name") or "")
        + ";side="
        + str(payload.get("side_state") or "")
        + ";epoch="
        + str(payload.get("trading_epoch") or "")
        + ";tick="
        + str(payload.get("now_tick") or "")
        + ";kind="
        + str(confirmation.get("candidate_kind") or "")
        + ";count="
        + str(confirmation.get("candidate_count") or "")
        + ";last="
        + str(confirmation.get("last_evaluated_trading_epoch") or "")
    )


def _confirmation_progress_v1(cursor: object) -> str:
    if cursor is None:
        return ""
    if hasattr(cursor, "to_dict"):
        payload = cursor.to_dict()
    elif isinstance(cursor, Mapping):
        payload = dict(cursor)
    else:
        return ""
    confirmation = payload.get("scope_confirmation")
    if not isinstance(confirmation, Mapping):
        confirmation = {}
    return (
        "kind="
        + str(confirmation.get("candidate_kind") or "")
        + ";count="
        + str(confirmation.get("candidate_count") or "")
        + ";last_evaluated_trading_epoch="
        + str(confirmation.get("last_evaluated_trading_epoch") or "")
        + ";confirmation_epochs="
        + str(payload.get("confirmation_epochs") or "")
        + ";side="
        + str(payload.get("side_state") or "")
    )


def _cursor_mapping_v1(cursor: object) -> dict[str, Any]:
    if cursor is None:
        return {}
    if hasattr(cursor, "to_dict"):
        payload = cursor.to_dict()
        return payload if isinstance(payload, dict) else {}
    if isinstance(cursor, Mapping):
        return dict(cursor)
    return {}


def _cursor_native_id_v1(cursor: object) -> str:
    return str(_cursor_mapping_v1(cursor).get("venue_native_id") or "")


def _cursor_instrument_id_v1(cursor: object) -> str:
    return str(_cursor_mapping_v1(cursor).get("instrument_id") or "")


def _as_int_v1(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _cap61_confirmation_state_v1(cursor: object) -> str:
    payload = _cursor_mapping_v1(cursor)
    if not payload:
        return ""
    cap61 = payload.get("cap61_confirmation_state")
    if not isinstance(cap61, Mapping):
        cap61 = {}
    carrier = cap61.get("confirmation_side_carrier")
    if not isinstance(carrier, Mapping):
        carrier = {}
    bull = carrier.get("bull_confirmation_state")
    bear = carrier.get("bear_confirmation_state")
    if not isinstance(bull, Mapping):
        bull = {}
    if not isinstance(bear, Mapping):
        bear = {}
    return (
        "bull_state="
        + str(bull.get("assessment_state") or "")
        + ";bull_count="
        + str(bull.get("distinct_confirmation_observation_count") or 0)
        + ";bear_state="
        + str(bear.get("assessment_state") or "")
        + ";bear_count="
        + str(bear.get("distinct_confirmation_observation_count") or 0)
        + ";side="
        + str(payload.get("side_state") or "")
        + ";epochs="
        + str(payload.get("confirmation_epochs") or "")
    )


def _confirmation_counts_v1(cursor: object) -> tuple[int, int, str, str]:
    payload = _cursor_mapping_v1(cursor)
    cap61 = payload.get("cap61_confirmation_state")
    if not isinstance(cap61, Mapping):
        cap61 = {}
    carrier = cap61.get("confirmation_side_carrier")
    if not isinstance(carrier, Mapping):
        carrier = {}
    bull = carrier.get("bull_confirmation_state")
    bear = carrier.get("bear_confirmation_state")
    if not isinstance(bull, Mapping):
        bull = {}
    if not isinstance(bear, Mapping):
        bear = {}
    return (
        _as_int_v1(bull.get("distinct_confirmation_observation_count")),
        _as_int_v1(bear.get("distinct_confirmation_observation_count")),
        str(bull.get("assessment_state") or ""),
        str(bear.get("assessment_state") or ""),
    )


def _classify_confirmation_progress_v1(
    *,
    occupancy_blocker: str,
    market_blocker: str,
    cycle_result: object | None,
    cursor_restore_status: str,
    previous_native: str,
    selected_native: str,
    loaded_cursor: object,
    outgoing_cursor: object,
) -> str:
    if occupancy_blocker or market_blocker or cycle_result is None:
        return "D_TECHNICAL_BLOCKER"
    if previous_native and selected_native and previous_native != selected_native:
        return "C_INSTRUMENT_CHANGE"
    if cursor_restore_status == "refused_mismatch":
        return "C_INSTRUMENT_CHANGE"
    if cursor_restore_status == "refused_stale":
        return "B_CONFIRMATION_RESET_OR_INVALIDATED"
    if cursor_restore_status in {
        "fail_closed_corrupt",
        "fail_closed_invalid_sidestate",
        "not_reached",
    }:
        return "D_TECHNICAL_BLOCKER"
    if cursor_restore_status == "missing":
        return "D_TECHNICAL_BLOCKER" if previous_native else "D_TECHNICAL_BLOCKER"
    if cursor_restore_status == "restored":
        before = _confirmation_counts_v1(loaded_cursor)
        after = _confirmation_counts_v1(outgoing_cursor)
        if after[0] < before[0] or after[1] < before[1]:
            return "B_CONFIRMATION_RESET_OR_INVALIDATED"
        if before[2] == "candidate" and after[2] == "observe" and after[0] == 0:
            return "B_CONFIRMATION_RESET_OR_INVALIDATED"
        if before[3] == "candidate" and after[3] == "observe" and after[1] == 0:
            return "B_CONFIRMATION_RESET_OR_INVALIDATED"
        return "A_SAME_CONFIRMATION_CONTINUED"
    return "D_TECHNICAL_BLOCKER"


def execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
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
    incoming_cursor: object | None = None,
    cursor_store_root: Path | None = None,
    c1_gate_payload: Mapping[str, Any] | None = None,
    c1_gate_override: Mapping[str, Any] | None = None,
) -> CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationResultV1:
    if owner_go != OWNER_GO:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "OWNER_GO_MISMATCH"
        )
    if origin_main_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "ORIGIN_MAIN_SHA_MISMATCH"
        )
    if (
        execute_network is not True
        and c1_gate_payload is None
        and c1_gate_override is None
        and acquisition_result is None
        and acquisition_transport is None
    ):
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "EXECUTE_NETWORK_OR_INJECTED_INPUT_REQUIRED"
        )
    _assert_dv_pins()
    del replay
    repo_sha = str(repository_sha or origin_main_sha)
    observed_unix = (
        float(producer_observed_at_unix) if producer_observed_at_unix is not None else time()
    )
    package_started = _utc_now_iso_v1()
    root = _REPO_ROOT
    store = Path(evidence_root) if evidence_root is not None else root / CANONICAL_PACK_RELPATH
    store.mkdir(parents=True, exist_ok=True)
    if cursor_store_root is None:
        cursor_store_root = (
            root / CURRENT_CURSOR_STORE_RELPATH if execute_network is True else store / "cursor"
        )

    gate_payload: Any = c1_gate_payload
    gate_http = 0
    gate_error = ""
    gate_performed = False
    gate_sha = ""
    if c1_gate_override is not None:
        c1_gate = {str(key): str(value) for key, value in dict(c1_gate_override).items()}
        required_gate_keys = (
            "CONDITION_GATE",
            "PREVIOUS_C1_VENUE_EVENT_TIME",
            "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME",
            "NEW_C1_EVIDENCE_AVAILABLE",
        )
        missing = [key for key in required_gate_keys if not str(c1_gate.get(key) or "").strip()]
        if missing:
            raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                "C1_GATE_OVERRIDE_INCOMPLETE"
            )
        if str(c1_gate.get("PREVIOUS_C1_VENUE_EVENT_TIME") or "") != str(
            PREVIOUS_C1_VENUE_EVENT_TIME
        ):
            raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                "C1_GATE_OVERRIDE_PREVIOUS_MISMATCH"
            )
    elif gate_payload is None:
        if execute_network is not True:
            raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                "C1_GATE_PAYLOAD_OR_NETWORK_REQUIRED"
            )
        gate_transport = FullCoreProductiveReadOnlyGetTransportV1(
            handle=None,
            timeout_seconds=20.0,
            max_request_count=C1_GATE_MAX_REQUEST_COUNT,
        )
        gate_endpoint = (
            f"{ENDPOINT_MARKET_CANDLES}?instId={C1_GATE_NATIVE_ID}&bar={C1_GATE_BAR}&limit=100"
        )
        gate_result = gate_transport.get(
            endpoint=gate_endpoint,
            auth_required=False,
            pretrade_decision_id="dv4-c1-gate-0g-usdt-swap",
        )
        gate_payload = gate_result.payload
        gate_http = int(gate_result.http_status)
        gate_error = str(gate_result.error_class or "")
        gate_performed = bool(gate_result.get_performed)
        gate_sha = str(gate_result.body_sha256 or "")
        c1_gate = _evaluate_c1_gate_v1(
            payload=gate_payload,
            http_status=gate_http,
            error_class=gate_error,
            get_performed=gate_performed,
            body_sha256=gate_sha,
        )
    else:
        gate_performed = True
        gate_http = 200
        c1_gate = _evaluate_c1_gate_v1(
            payload=gate_payload,
            http_status=gate_http,
            error_class=gate_error,
            get_performed=gate_performed,
            body_sha256=gate_sha,
        )
    _persist_json(path=store / "c1_gate_v1.json", payload=c1_gate)
    if c1_gate["CONDITION_GATE"] != "SATISFIED":
        claims = {
            "THIS_SLICE": THIS_SLICE,
            "OWNER_GO": OWNER_GO,
            "EXPECTED_ORIGIN_MAIN": origin_main_sha,
            "CONDITION_GATE": c1_gate["CONDITION_GATE"],
            "PREVIOUS_C1_VENUE_EVENT_TIME": c1_gate["PREVIOUS_C1_VENUE_EVENT_TIME"],
            "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": c1_gate["NEWEST_FINALIZED_1M_VENUE_EVENT_TIME"],
            "NEW_C1_EVIDENCE_AVAILABLE": c1_gate["NEW_C1_EVIDENCE_AVAILABLE"],
            "RUNTIME_CYCLE_COUNT_THIS_GO": "0",
            "POST_COUNT": "0",
            "VENUE_MUTATION_PERFORMED": FALSE_TOKEN,
            "EXTERNAL_EFFECT_PERMIT_CREATED": FALSE_TOKEN,
            "HARD_STOP": TRUE_TOKEN,
            "FIRST_REAL_BLOCKER": "CONDITION_GATE_NOT_YET_SATISFIED",
        }
        summary = dict(claims)
        lineage = {
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "DV_V3_PACK": DV_V3_PACK,
            "DV_V3_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
            "DV_V2_PACK": DV_V2_PACK,
            "DV_V2_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
            "DV_V1_PACK": DV_V1_PACK,
            "DV_V1_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
            "DU_PACK": DU_PACK,
            "DU_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
            "DT_PACK": DT_PACK,
            "DT_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
            "CONDITION_GATE": c1_gate["CONDITION_GATE"],
        }
        _persist_json(path=store / "claims.json", payload=claims)
        _persist_json(path=store / "SUMMARY.json", payload=summary)
        _persist_json(path=store / "LINEAGE.json", payload=lineage)
        persist_manifest_sha256_v1(store_root=store)
        manifest_rc = verify_manifest_sha256_v1(store_root=store)
        return CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationResultV1(
            store_root=str(store),
            occupancy_status="NOT_REACHED",
            pending_orders_status="NOT_REACHED",
            cap23_selected_instrument_id="",
            cap23_selection_decision_id="",
            cap23_valid_from="",
            cap23_valid_until="",
            cap24_bound_instrument_id="",
            master_v2_runtime_cycle_id="",
            master_v2_decision_id="",
            master_v2_decision="",
            bull_bear_state="",
            double_play_decision="",
            decision_result="NOT_REACHED",
            decision_provenance="CONDITION_GATE_NOT_YET_SATISFIED",
            decision_execution_eligible=FALSE_TOKEN,
            sizing_result="NOT_REACHED",
            risk_admission_result="NOT_REACHED",
            venue_plan_status="NONE",
            envelope_readiness=FALSE_TOKEN,
            final_envelope_id="",
            final_envelope_digest="",
            order_intent_created=FALSE_TOKEN,
            permit_created=FALSE_TOKEN,
            real_external_effect_authorized=FALSE_TOKEN,
            post_count="0",
            first_real_blocker="CONDITION_GATE_NOT_YET_SATISFIED",
            evidence_manifest=str(store / "MANIFEST.sha256"),
            manifest_verify_rc=manifest_rc,
            condition_gate=c1_gate["CONDITION_GATE"],
            newest_finalized_1m_venue_event_time=c1_gate["NEWEST_FINALIZED_1M_VENUE_EVENT_TIME"],
            runtime_cycle_count="0",
        )
    if execute_network is not True and acquisition_result is None and acquisition_transport is None:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "CYCLE_REQUIRES_INJECTED_ACQUISITION_AFTER_SATISFIED_GATE"
        )

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

    cursor_restore_status = "not_reached"
    cursor_state_before = ""
    cursor_state_after = ""
    confirmation_progress = ""
    confirmation_state_before = ""
    confirmation_state_after = ""
    confirmation_progress_class = ""
    previous_cursor_instrument = ""
    instrument_binding_match = FALSE_TOKEN
    cross_instrument_confirmation_carry = FALSE_TOKEN
    cursor_persisted = FALSE_TOKEN
    loaded_cursor = incoming_cursor
    if loaded_cursor is None and cursor_store_root is not None:
        try:
            loaded_cursor = load_current_productive_sidestate_confirmation_cursor_v1(
                Path(cursor_store_root)
            )
        except CurrentProductiveCursorError:
            loaded_cursor = None
    previous_cursor_instrument = _cursor_native_id_v1(loaded_cursor)
    confirmation_state_before = _cap61_confirmation_state_v1(loaded_cursor)
    cursor_state_before = _cursor_identity_v1(loaded_cursor)
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
                raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                    str(exc)
                ) from exc
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
                selected_native = str(native_id or "")
                if previous_cursor_instrument and selected_native:
                    instrument_binding_match = _token(previous_cursor_instrument == selected_native)
                if not market_blocker:
                    try:
                        cycle_result = run_current_productive_master_v2_runtime_cycle_v1(
                            bound_instrument=bound,
                            cycle_id=f"dv-{native_id}-{package_started}",
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
                            incoming_cursor=loaded_cursor,
                        )
                    except (TypeError, RuntimeError, ValueError) as exc:
                        market_blocker = f"MASTER_V2_RUNTIME_CYCLE_FAIL_CLOSED:{type(exc).__name__}"
                    else:
                        if cycle_result.input_blocker:
                            market_blocker = cycle_result.input_blocker
                        market_payloads["finalized_close_count"] = str(len(closes))
                        market_payloads["mark_px_observed"] = str(mark_px)
                        market_payloads["last_finalized_event_ts"] = str(last_ts)
                        cursor_restore_status = str(cycle_result.cursor_restore_status or "")
                        outgoing_cursor = cycle_result.outgoing_cursor
                        if outgoing_cursor is not None:
                            cursor_state_after = _cursor_identity_v1(outgoing_cursor)
                            confirmation_progress = _confirmation_progress_v1(outgoing_cursor)
                            confirmation_state_after = _cap61_confirmation_state_v1(outgoing_cursor)
                            outgoing_native = _cursor_native_id_v1(outgoing_cursor)
                            selected_native = str(native_id or "")
                            if (
                                previous_cursor_instrument
                                and selected_native
                                and previous_cursor_instrument != selected_native
                                and outgoing_native == previous_cursor_instrument
                            ):
                                raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                                    "CROSS_INSTRUMENT_CONFIRMATION_CARRY"
                                )
                            persist_roots = [store / "cursor"]
                            if cursor_store_root is not None:
                                persist_roots.append(Path(cursor_store_root))
                            for persist_root in persist_roots:
                                persist_current_productive_sidestate_confirmation_cursor_v1(
                                    outgoing_cursor,
                                    store_root=persist_root,
                                )
                            cursor_persisted = TRUE_TOKEN
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
    bull_signal_class = ""
    bear_signal_class = ""
    if cycle_replay is not None and cycle_replay.intermediate is not None:
        bull_signal_class = _signal_class_from_assessment_v1(
            cycle_replay.intermediate.bull_assessment
        )
        bear_signal_class = _signal_class_from_assessment_v1(
            cycle_replay.intermediate.bear_assessment
        )
    incoming_map = _cursor_mapping_v1(loaded_cursor)
    outgoing_map = _cursor_mapping_v1(
        cycle_result.outgoing_cursor if cycle_result is not None else None
    )

    def _obs_epoch(payload: Mapping[str, Any]) -> int:
        cap61 = payload.get("cap61_confirmation_state")
        if not isinstance(cap61, Mapping):
            return 0
        acc = cap61.get("observation_acceptance_state")
        if not isinstance(acc, Mapping):
            return 0
        epoch = acc.get("market_observation_epoch")
        if isinstance(epoch, Mapping):
            return _as_int_v1(epoch.get("value"))
        return 0

    def _obs_event(payload: Mapping[str, Any]) -> str:
        cap61 = payload.get("cap61_confirmation_state")
        if not isinstance(cap61, Mapping):
            return ""
        acc = cap61.get("observation_acceptance_state")
        if not isinstance(acc, Mapping):
            return ""
        ident = acc.get("last_accepted_observation_identity")
        if not isinstance(ident, Mapping):
            return ""
        value = ident.get("venue_event_time")
        return "" if value is None else str(value)

    epoch_before = _obs_epoch(incoming_map)
    epoch_after = _obs_epoch(outgoing_map)
    event_before = _obs_event(incoming_map)
    event_after = _obs_event(outgoing_map)
    c1_classification = _c1_classification_v1(
        epoch_before=epoch_before,
        epoch_after=epoch_after,
        event_before=event_before,
        event_after=event_after,
    )
    confirmation_transition_class = _confirmation_transition_class_v1(
        before=confirmation_state_before,
        after=confirmation_state_after,
    )
    sidestate_before = str(incoming_map.get("side_state") or "")
    sidestate_after = str(outgoing_map.get("side_state") or "")
    cycle_last_ts = str(market_payloads.get("last_finalized_event_ts") or "")

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
            session_id="current-productive-dv-session",
            run_id="current-productive-dv-run",
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

    if sizing_result in {"", "NOT_REACHED"}:
        step_29p_status = "NOT_REACHED"
    elif sizing_result == "MISSING_29P":
        step_29p_status = "NOT_REACHED_HOLD_PATH_MISSING_29P_IS_NOT_A_29P_FINDING"
    else:
        step_29p_status = sizing_result
    selected_native = identities.get("cap23_selected_instrument_id", "")
    if previous_cursor_instrument and selected_native:
        instrument_binding_match = _token(previous_cursor_instrument == selected_native)
    outgoing_for_class = cycle_result.outgoing_cursor if cycle_result is not None else None
    confirmation_progress_class = _classify_confirmation_progress_v1(
        occupancy_blocker=occupancy_blocker,
        market_blocker=market_blocker,
        cycle_result=cycle_result,
        cursor_restore_status=cursor_restore_status,
        previous_native=previous_cursor_instrument,
        selected_native=selected_native,
        loaded_cursor=loaded_cursor,
        outgoing_cursor=outgoing_for_class,
    )
    if confirmation_progress_class == "D_TECHNICAL_BLOCKER":
        hold_class = "D_TECHNICAL_BLOCKER"
    elif confirmation_progress_class == "C_INSTRUMENT_CHANGE":
        hold_class = "C_INSTRUMENT_CHANGE"
    elif confirmation_progress_class == "B_CONFIRMATION_RESET_OR_INVALIDATED":
        hold_class = "B_CONFIRMATION_RESET_OR_INVALIDATED"
    elif decision_result == "EXECUTABLE_VENUE_PLAN_BOUND":
        hold_class = ""
    else:
        hold_class = "A_SAME_CONFIRMATION_CONTINUED"

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
        handle_id="full-core-dv-readiness-handle", bound=True
    )
    http_transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=send_handle)
    try:
        http_transport.post_trade_order(
            payload={"instId": identities.get("cap23_selected_instrument_id") or "MUST_NOT_POST"},
            permit_id="eep-dv-must-not-post",
            envelope_id="env-dv-must-not-post",
            envelope_digest="0" * 64,
        )
    except FullCoreProductiveHttpPostError as exc:
        if "REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE" not in str(exc):
            raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
                "HTTP_FORBIDDEN_MISSING"
            ) from exc
    else:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "HTTP_MUST_NOT_POST"
        )
    if http_transport.post_count != 0:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
            "HTTP_TRANSPORT_SIDE_EFFECT"
        )

    envelope_id = ""
    envelope_digest = ""
    envelope_fields: dict[str, str] = {}
    if plan is not None and envelope_readiness == TRUE_TOKEN:
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref="DV_FRESH_CAP24_AND_CURRENT_PRODUCTIVE_MASTER_V2",
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
    external_effect_applicability = _token(bool(envelope_id))
    envelope_freshness = "CYCLE_BOUND_FRESH" if envelope_id else "NOT_REACHED"
    envelope_status = "BOUND" if envelope_id else "NONE"
    standing_blocker = current_productive_first_real_blocker_v1()
    if standing_blocker != STANDING_SEAM_REMAINDER:
        raise CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationError(
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
        "HOLD_CLASS": hold_class,
        "RUNTIME_CYCLE_COUNT_THIS_GO": "1",
        "CONDITION_GATE": c1_gate["CONDITION_GATE"],
        "PREVIOUS_C1_VENUE_EVENT_TIME": c1_gate["PREVIOUS_C1_VENUE_EVENT_TIME"],
        "NEWEST_FINALIZED_1M_VENUE_EVENT_TIME": c1_gate["NEWEST_FINALIZED_1M_VENUE_EVENT_TIME"],
        "CYCLE_C1_VENUE_EVENT_TIME": event_after or cycle_last_ts,
        "NEW_C1_EVIDENCE_AVAILABLE": c1_gate["NEW_C1_EVIDENCE_AVAILABLE"],
        "C1_CLASSIFICATION": c1_classification,
        "MARKET_OBSERVATION_EPOCH_BEFORE": str(epoch_before),
        "MARKET_OBSERVATION_EPOCH_AFTER": str(epoch_after),
        "BULL_SIGNAL_CLASS": bull_signal_class,
        "BEAR_SIGNAL_CLASS": bear_signal_class,
        "CONFIRMATION_TRANSITION_CLASS": confirmation_transition_class,
        "SIDESTATE_BEFORE": sidestate_before,
        "SIDESTATE_AFTER": sidestate_after,
        "PREVIOUS_CYCLE_ID": PREVIOUS_CYCLE_ID,
        "PREVIOUS_CURSOR_INSTRUMENT": previous_cursor_instrument,
        "SELECTED_INSTRUMENT": identities.get("cap23_selected_instrument_id", ""),
        "INSTRUMENT_BINDING_MATCH": instrument_binding_match,
        "CURSOR_RESTORE_STATUS": cursor_restore_status,
        "CURSOR_STATE_BEFORE": cursor_state_before,
        "CURSOR_STATE_AFTER": cursor_state_after,
        "CONFIRMATION_STATE_BEFORE": confirmation_state_before,
        "CONFIRMATION_STATE_AFTER": confirmation_state_after,
        "CONFIRMATION_PROGRESS": confirmation_progress,
        "CONFIRMATION_PROGRESS_CLASS": confirmation_progress_class,
        "CROSS_INSTRUMENT_CONFIRMATION_CARRY": cross_instrument_confirmation_carry,
        "CURSOR_PERSISTED": cursor_persisted,
        "STEP_29P_STATUS": step_29p_status,
        "SIZING_RESULT": sizing_result,
        "RISK_ADMISSION_RESULT": risk_admission_result,
        "CURRENT_PRODUCTIVE_VENUE_PLAN_STATUS": venue_plan_status,
        "ENVELOPE_READINESS": envelope_readiness,
        "ENVELOPE_STATUS": envelope_status,
        "ENVELOPE_FRESHNESS": envelope_freshness,
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
        "EXTERNAL_EFFECT_APPLICABILITY": external_effect_applicability,
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
        "DQ_PACK": DQ_PACK,
        "DQ_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "DT_PACK": DT_PACK,
        "DT_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "DU_PACK": DU_PACK,
        "DU_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "DV_V3_PACK": DV_V3_PACK,
        "DV_V3_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "DV_V2_PACK": DV_V2_PACK,
        "DV_V2_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "DV_V1_PACK": DV_V1_PACK,
        "DV_V1_PACK_IS_NOT_CURRENT_AUTHORITY": TRUE_TOKEN,
        "PREVIOUS_CYCLE_ID": PREVIOUS_CYCLE_ID,
        "PREVIOUS_CURSOR_INSTRUMENT": previous_cursor_instrument,
        "INSTRUMENT_BINDING_MATCH": instrument_binding_match,
        "CONFIRMATION_PROGRESS_CLASS": confirmation_progress_class,
        "CAP23_SELECTED_INSTRUMENT_ID": identities.get("cap23_selected_instrument_id", ""),
        "CAP24_BOUND_INSTRUMENT_ID": identities.get("cap24_bound_instrument_id", ""),
        "MASTER_V2_RUNTIME_CYCLE_ID": cycle_id,
        "MASTER_V2_DECISION_ID": replay_facts["MASTER_V2_DECISION_ID"],
        "DECISION_PROVENANCE": decision_provenance,
        "OCCUPANCY_STATUS": occupancy_facts.get("OCCUPANCY_STATUS", ""),
        "CURSOR_RESTORE_STATUS": cursor_restore_status,
        "CURSOR_PERSISTED": cursor_persisted,
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
        "HOLD_CLASS": hold_class,
        "CONFIRMATION_PROGRESS_CLASS": confirmation_progress_class,
        "PREVIOUS_CURSOR_INSTRUMENT": previous_cursor_instrument,
        "SELECTED_INSTRUMENT": identities.get("cap23_selected_instrument_id", ""),
        "INSTRUMENT_BINDING_MATCH": instrument_binding_match,
        "CONFIRMATION_STATE_BEFORE": confirmation_state_before,
        "CONFIRMATION_STATE_AFTER": confirmation_state_after,
        "CURSOR_RESTORE_STATUS": cursor_restore_status,
        "CURSOR_PERSISTED": cursor_persisted,
        "CONDITION_GATE": c1_gate["CONDITION_GATE"],
        "C1_CLASSIFICATION": c1_classification,
        "BULL_SIGNAL_CLASS": bull_signal_class,
        "BEAR_SIGNAL_CLASS": bear_signal_class,
        "CONFIRMATION_TRANSITION_CLASS": confirmation_transition_class,
        "SIDESTATE_BEFORE": sidestate_before,
        "SIDESTATE_AFTER": sidestate_after,
        "STEP_29P_STATUS": step_29p_status,
        "ORDER_INTENT_CREATED": replay_facts["ORDER_INTENT_CREATED"],
        "ENVELOPE_READINESS": envelope_readiness,
        "ENVELOPE_STATUS": envelope_status,
        "ENVELOPE_FRESHNESS": envelope_freshness,
        "FINAL_ENVELOPE_ID": envelope_id,
        "PERMIT_CREATED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_PERMIT_CREATED": FALSE_TOKEN,
        "EXTERNAL_EFFECT_APPLICABILITY": external_effect_applicability,
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
    return CurrentProductiveOneRuntimeCycleAfterNewFinalized1mC1ObservationResultV1(
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
        condition_gate=c1_gate["CONDITION_GATE"],
        newest_finalized_1m_venue_event_time=c1_gate["NEWEST_FINALIZED_1M_VENUE_EVENT_TIME"],
        runtime_cycle_count="1",
    )


def main() -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-go", default=OWNER_GO)
    parser.add_argument("--origin-main-sha", default=EXPECTED_ORIGIN_MAIN_SHA)
    parser.add_argument("--execute-network", action="store_true")
    parser.add_argument("--evidence-root", default="")
    parser.add_argument("--vault-file", default="")
    parser.add_argument("--c1-gate-json", default="")
    args = parser.parse_args()
    override = None
    if str(args.c1_gate_json).strip():
        override = json.loads(Path(args.c1_gate_json).read_text(encoding="utf-8"))
    result = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=str(args.owner_go),
        origin_main_sha=str(args.origin_main_sha),
        evidence_root=Path(args.evidence_root) if str(args.evidence_root).strip() else None,
        vault_file=args.vault_file if str(args.vault_file).strip() else None,
        execute_network=bool(args.execute_network),
        c1_gate_override=override,
    )
    print(
        json.dumps(
            {
                "STORE": result.store_root,
                "OCCUPANCY_STATUS": result.occupancy_status,
                "CURRENT_PENDING_ORDERS": result.pending_orders_status,
                "CAP23_SELECTED_INSTRUMENT_ID": result.cap23_selected_instrument_id,
                "CAP23_SELECTION_DECISION_ID": result.cap23_selection_decision_id,
                "CAP24_BOUND_INSTRUMENT_ID": result.cap24_bound_instrument_id,
                "MASTER_V2_RUNTIME_CYCLE_ID": result.master_v2_runtime_cycle_id,
                "MASTER_V2_DECISION_ID": result.master_v2_decision_id,
                "MASTER_V2_DECISION": result.master_v2_decision,
                "BULL_BEAR_STATE": result.bull_bear_state,
                "DOUBLE_PLAY_DECISION": result.double_play_decision,
                "DECISION_RESULT": result.decision_result,
                "DECISION_EXECUTION_ELIGIBLE": result.decision_execution_eligible,
                "ORDER_INTENT_CREATED": result.order_intent_created,
                "ENVELOPE_READINESS": result.envelope_readiness,
                "FINAL_ENVELOPE_ID": result.final_envelope_id,
                "PERMIT_CREATED": result.permit_created,
                "POST_COUNT": result.post_count,
                "FIRST_REAL_BLOCKER": result.first_real_blocker,
                "MANIFEST_VERIFY_RC": result.manifest_verify_rc,
            },
            sort_keys=True,
        )
    )
    return 0 if result.manifest_verify_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
