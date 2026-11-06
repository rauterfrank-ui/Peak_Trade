from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


def write_current_state_contract_trace_v3(path: Path) -> None:
    trace = {
        "CURRENT_C1_OBSERVATION_OWNER": "trading.market_state.distinct_market_observation_acceptor_v1.evaluate_distinct_market_observation_v1",
        "CURRENT_CONFIRMATION_CARRIER_OWNER": "trading.master_v2.directional_assessment_confirmation_integration_v1.DirectionalConfirmationSideStateCarrierV1",
        "CURRENT_CONFIRMATION_EPOCH_OWNER": "trading.market_state.directional_confirmation_progress_v1.evaluate_confirmation_progress_v1",
        "CURRENT_CONFIRMATION_STATE_OWNER": "trading.master_v2.directional_assessment_confirmation_integration_v1.apply_single_lane_confirmation_lifecycle_v1",
        "CURRENT_SCOPE_STATE_OWNER": "trading.master_v2.double_play_state.RuntimeScopeState",
        "CURRENT_SIDE_STATE_OWNER": "trading.master_v2.double_play_state.transition_state",
        "CURRENT_MULTI_CYCLE_STATE_TRANSPORT_OWNER": "run_integrated_offline_trading_logic_replay_v1 caller-owned inp fields + intermediate outputs",
        "C1": {
            "INITIALIZATION": "initial_observation_acceptance_state_v1(bound_instrument_key=...)",
            "INPUT": "ObservationAcceptanceResultV1 per cycle via inp.observation_acceptance_result",
            "OUTPUT": "commit_observation_acceptance_v1 state_after in result",
            "PERSISTENCE_BOUNDARY": "caller persists c1_acceptance_state between cycles",
            "FAIL_CLOSED": "non-DISTINCT → non_advancing path if not injected",
        },
        "C3_CARRIER": {
            "INITIALIZATION": "initial_directional_confirmation_side_state_carrier_v1",
            "INPUT": "inp.directional_confirmation_progress",
            "OUTPUT": "intermediate.directional_confirmation_progress_after",
            "PERSISTENCE_BOUNDARY": "caller replace inp carrier each cycle",
        },
        "SCOPE_CONFIRMATION": {
            "INPUT": "inp.scope_confirmation_state",
            "OUTPUT": "intermediate.scope_event.next_confirmation_state",
            "PERSISTENCE_BOUNDARY": "caller should feed next back; V2 omitted",
        },
        "REPLAY_BINDING": "integrated_offline_trading_logic_replay_v1._resolve_c3_confirmation_binding_v1",
    }
    path.write_text(json.dumps(trace, indent=2) + "\n", encoding="utf-8")


def write_v2_vs_s08_state_diff_v3(path: Path) -> Mapping[str, object]:
    diff = {
        "S08_WITNESS_STATE_INPUTS": [
            "policies=_policies_confirm_once()",
            "observation_acceptance_result=_injected_c1(...)",
            "scope_confirmation_state=_empty_scope_confirmation()",
            "confirmation_progress_session_id",
            "confirmation_progress_venue",
            "confirmation_progress_instrument",
            "side_state=LONG_ARMED",
        ],
        "V2_MULTI_CYCLE_STATE_INPUTS": [
            "directional_confirmation_progress (carried)",
            "existing_scope (carried)",
            "runtime_scope_state (carried)",
            "side_state (carried)",
            "observation_acceptance_result=MISSING → non_advancing_observation_acceptance_result_v1",
            "confirmation_progress_session_id=MISSING",
            "confirmation_progress_venue=MISSING",
            "confirmation_progress_instrument=MISSING",
            "scope_confirmation_state=RESET each cycle",
            "policies=default confirmation_epochs=2",
        ],
        "V2_MISSING_STATE_FIELDS": [
            "observation_acceptance_result (C1 DISTINCT per cycle)",
            "c1_acceptance_state persistence",
            "confirmation_progress_session_id",
            "confirmation_progress_venue",
            "confirmation_progress_instrument",
            "scope_confirmation_state carry-forward",
        ],
        "V2_RESET_STATE_FIELDS": [
            "scope_confirmation_state",
            "observation_acceptance (implicit non-advancing each cycle)",
        ],
        "V2_STATE_FIELDS_ALREADY_CORRECT": [
            "directional_confirmation_progress carry",
            "runtime_scope_state carry",
            "existing_scope carry",
            "side_state carry",
        ],
        "EXACT_NATURAL_ENTER_STATE_GAP": "C1 observation acceptance not persisted/advanced across cycles; scope confirmation clock not carried; C3 session/venue/instrument binding absent.",
    }
    path.write_text(json.dumps(diff, indent=2) + "\n", encoding="utf-8")
    return diff


def write_v2_zero_enter_root_cause_v3(path: Path) -> Mapping[str, object]:
    root = {
        "V2_ZERO_ENTER_ROOT_CAUSE": "C1_STATE_NOT_PERSISTED",
        "V2_ZERO_ENTER_ROOT_CAUSE_SECONDARY": [
            "CONFIRMATION_EPOCH_REINITIALIZED via non_advancing_observation_acceptance_result_v1",
            "SCOPE_STATE scope_confirmation not carried (scope clock separate from C3)",
        ],
        "V2_ZERO_ENTER_ROOT_CAUSE_PROVEN": True,
        "CLASSIFICATION": [
            "C1_STATE_NOT_PERSISTED",
            "CONTIGUOUS_CONFIRMATION_BROKEN",
            "LEGITIMATE_CORE_NO_ENTER without DISTINCT C1 chain",
        ],
        "NOT_PRIMARY": "MARKET_PATH_NEVER_REACHES_CONFIRMATION alone — S08 proves path sufficient with C1 inject",
    }
    path.write_text(json.dumps(root, indent=2) + "\n", encoding="utf-8")
    return root
