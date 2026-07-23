"""Definition-only contract tests for CS path-efficiency continuation preregistration v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.research.cross_sectional_path_efficiency_continuation_v1_hypothesis_preregistration_v1 import (
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
    / "config/research/cross_sectional_path_efficiency_continuation_program_definition_operator_decision_packet_v1.json"
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
        == "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
    )
    payload = _load(CONTRACT_PATH)
    assert compute_contract_digest(payload) == payload["contract_digest"]
    frozen = payload["parameter_governance"]["frozen_non_grid_parameters"]
    assert frozen["lookback_N"] == 48
    assert frozen["rebalance_interval_bars"] == 8
    assert frozen["signal_lag_bars"] == 1
    assert frozen["min_eligible_members_for_rank"] == 5
    assert frozen["vol_normalization"] is False
    assert frozen["strategy_stop"] == "none"
    assert payload["parameter_governance"]["development_only_bounded_grid"]["authorized"] is False
    assert (
        payload["score_and_selection"]["polarity"] == "PATH_EFFICIENCY_CONTINUATION_ER_TIMES_SIGN"
    )
    assert (
        payload["score_and_selection"]["score_family_policy"]
        == "path_efficiency_ratio_times_sign_net_log_return_fixed_lookback_v1"
    )
    assert payload["costs"]["fee_bps_per_side"] == 10.0
    assert payload["costs"]["slippage_bps_per_side"] == 5.0
    assert payload["costs"]["half_spread_bps"] == 5.0
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
    bad3["parameter_governance"]["frozen_non_grid_parameters"]["lookback_N"] = 24
    with pytest.raises(PreregistrationValidationError, match="LOOKBACK_N"):
        validate_measurement_contract(bad3)


def test_decision_packet_and_owner_map_consistency() -> None:
    packet = _load(DECISION_PACKET)
    assert (
        packet["scope_id"]
        == "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_PROGRAM_SSOT_AND_PREREGISTRATION_PERSISTENCE_ONLY_V1"
    )
    assert (
        packet["go_token"]
        == "GO_CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_PROGRAM_SSOT_AND_PREREGISTRATION_PERSISTENCE_ONLY_V1"
    )
    assert packet["evaluation_authorized"] is False
    assert packet["implementation_authorized"] is False
    assert packet["separate_open_sibling_must_remain_unchanged"] is True
    assert (
        packet["separate_open_sibling_program_id"]
        == "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
    )
    owner = _load(OWNER_MAP)
    surfaces = owner["allowed_optimization_surfaces"]
    key = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V1"
    assert key in surfaces
    assert CONTRACT_REL_PATH in surfaces[key]["path_prefixes"]
