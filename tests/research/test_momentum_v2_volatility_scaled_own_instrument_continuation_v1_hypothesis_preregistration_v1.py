"""Definition-only contract tests for Momentum V2 vol-scaled continuation preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_research_program_v1 import (
    load_and_validate_repo_program,
)
from src.research.momentum_v2_volatility_scaled_own_instrument_continuation_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    PreregistrationValidationError,
    compute_contract_digest,
    load_and_validate_repo_contract,
    validate_measurement_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
OWNER_MAP = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
DECISION_PACKET = (
    REPO
    / "config/research/momentum_v2_volatility_scaled_own_instrument_continuation_program_definition_operator_decision_packet_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only_digest_and_frozen_params() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["evaluation_authorized"] is False
    assert report["implementation_authorized"] is False
    assert report["development_run_count"] == 0
    assert report["development_run_limit"] == 1
    assert (
        report["hypothesis_id"]
        == "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    assert (
        report["scope_id"]
        == "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_DEFINITION_ONLY_PREREGISTRATION_V1"
    )
    payload = _load(CONTRACT_PATH)
    assert compute_contract_digest(payload) == payload["contract_digest"]
    frozen = payload["parameter_governance"]["frozen_non_grid_parameters"]
    assert frozen["lookback_period"] == 20
    assert frozen["vol_scaled_entry_z"] == 1.0
    assert frozen["vol_scaled_exit_z"] == 0.0
    assert frozen["vol_scaling_required"] is True
    assert frozen["pit_safe"] is True
    assert frozen["short_entry_forbidden"] is True
    assert frozen["registry_mutation_forbidden"] is True
    assert payload["parameter_governance"]["development_only_bounded_grid"]["authorized"] is False
    assert payload["baseline"]["entry_threshold"] == 0.02
    assert payload["baseline"]["exit_threshold"] == -0.01
    assert payload["treatment"]["treatment_id"] == (
        "VOLATILITY_SCALED_MOMENTUM_SCORE_THRESHOLD_CROSS_V1"
    )
    assert payload["universe_scope"]["bitcoin_excluded"] is True
    assert payload["universe_scope"]["spot_excluded"] is True
    assert payload["costs"]["fee_bps_per_side"] == 10.0
    assert payload["costs"]["predefined_cost_stress_multipliers"] == [0.5, 1.0, 1.5, 2.0]
    thresholds = payload["economic_admission_contract"]["thresholds"]
    assert thresholds["minimum_trade_count"]["value"] == 50
    assert thresholds["net_profit_factor_min"]["value"] == 1.3
    assert thresholds["maximum_max_drawdown"]["value"] == 0.25
    assert (
        payload["directional_form"]["sole_directional_transition_authority"]
        == "trading.master_v2.double_play_state.transition_state"
    )
    assert payload["run_limit"]["retry_forbidden"] is True
    assert payload["sealed_holdout_binding_status"] == "UNBOUND_UNTOUCHED_ACCESS_FORBIDDEN"


def test_fail_closed_on_digest_or_eval_mutation() -> None:
    payload = _load(CONTRACT_PATH)
    bad = copy.deepcopy(payload)
    bad["evaluation_authorized"] = True
    with pytest.raises(PreregistrationValidationError, match="EVALUATION_AUTHORIZED"):
        validate_measurement_contract(bad)
    bad2 = copy.deepcopy(payload)
    bad2["contract_digest"] = "0" * 64
    with pytest.raises(PreregistrationValidationError, match="CONTRACT_DIGEST_MISMATCH"):
        validate_measurement_contract(bad2)
    bad3 = copy.deepcopy(payload)
    bad3["parameter_governance"]["frozen_non_grid_parameters"]["lookback_period"] = 24
    with pytest.raises(PreregistrationValidationError, match="LOOKBACK_PERIOD"):
        validate_measurement_contract(bad3)
    bad4 = copy.deepcopy(payload)
    bad4["parameter_governance"]["frozen_non_grid_parameters"]["vol_scaled_entry_z"] = 0.5
    with pytest.raises(PreregistrationValidationError, match="FROZEN_ENTRY_Z"):
        validate_measurement_contract(bad4)


def test_program_and_backlog_terminally_retired() -> None:
    program = load_and_validate_repo_program(REPO)
    assert program["valid"] is True
    assert program["evaluation_authorized"] is False
    assert program["implementation_authorized"] is False
    assert program["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    backlog = load_and_validate_repo_backlog(REPO)
    assert backlog["valid"] is True
    assert backlog["preregistered_count"] == 0
    assert backlog["terminal_count"] == 1
    assert backlog["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["evaluation_authorized"] is False


def test_decision_packet_and_owner_map_consistency() -> None:
    packet = _load(DECISION_PACKET)
    assert (
        packet["scope_id"]
        == "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_TERMINAL_RETIREMENT_CLOSEOUT_V1"
    )
    assert (
        packet["go_token"]
        == "GO_MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_TERMINAL_RETIREMENT_CLOSEOUT_V1"
    )
    assert packet["decision_id"] == "CLOSE_LANE_NO_FURTHER_RESEARCH"
    assert packet["lane_status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert packet["evaluation_authorized"] is False
    assert packet["implementation_authorized"] is False
    assert packet["separate_pending_momentum_1h_v2_scope_must_remain_unchanged"] is True
    assert (
        packet["separate_pending_momentum_1h_v2_hypothesis_id"]
        == "MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2"
    )
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    key = (
        "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_V1_"
        "HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    )
    assert key in surfaces
    assert CONTRACT_REL_PATH in surfaces[key]["path_prefixes"]
    assert (
        "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_RESEARCH_PROGRAM_V1" in surfaces
    )
    assert (
        "MOMENTUM_V2_VOLATILITY_SCALED_OWN_INSTRUMENT_CONTINUATION_HYPOTHESIS_BACKLOG_V1"
        in surfaces
    )
