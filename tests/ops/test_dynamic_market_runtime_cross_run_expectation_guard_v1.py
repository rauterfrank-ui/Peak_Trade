"""Cross-run Golden expectation guard for dynamic market evidence contract."""

from __future__ import annotations

import copy

import pytest

from src.ops.full_core_live_path_composition_root_v1.dynamic_market_runtime_cross_run_expectation_guard_v1 import (
    CrossRunGoldenExpectationGuardError,
    assert_no_cross_run_golden_expectation_keys_v1,
    validate_dynamic_market_evidence_contract_v1,
)
from src.ops.full_core_live_path_composition_root_v1.dynamic_market_selection_evidence_contract_v1 import (
    build_dynamic_market_selection_evidence_contract_v1,
    observation_context_from_mapping_v1,
)
from pathlib import Path
import json

POST_PR7017_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "ops"
    / "dynamic_market_selection_evidence_post_pr7017_sand_measurement_v1.json"
)


def test_guard_rejects_cross_run_expectation_key() -> None:
    with pytest.raises(CrossRunGoldenExpectationGuardError):
        assert_no_cross_run_golden_expectation_keys_v1(
            {"dynamic_value_observations": [{"expected_cross_run_value": "SAND-USDT-SWAP"}]}
        )


def test_valid_contract_passes_guard() -> None:
    ctx = observation_context_from_mapping_v1(json.loads(POST_PR7017_FIXTURE.read_text()))
    contract = build_dynamic_market_selection_evidence_contract_v1(ctx)
    validate_dynamic_market_evidence_contract_v1(contract)


def test_guard_rejects_cross_run_expectation_true_on_observation() -> None:
    ctx = observation_context_from_mapping_v1(json.loads(POST_PR7017_FIXTURE.read_text()))
    contract = build_dynamic_market_selection_evidence_contract_v1(ctx)
    bad = copy.deepcopy(contract)
    bad["dynamic_value_observations"][0]["cross_run_expectation"] = True
    with pytest.raises(CrossRunGoldenExpectationGuardError):
        validate_dynamic_market_evidence_contract_v1(bad)
