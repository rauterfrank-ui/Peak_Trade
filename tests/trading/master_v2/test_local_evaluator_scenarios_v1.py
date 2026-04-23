# tests/trading/master_v2/test_local_evaluator_scenarios_v1.py
from __future__ import annotations

import pytest

from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    build_master_v2_scenario_matrix_v1,
    get_master_v2_scenario_case_v1,
    scenario_matrix_all_names_v1,
)
from trading.master_v2.local_evaluator_scenarios_v1 import (
    SCENARIO_HARNESS_LAYER_VERSION,
    assert_master_v2_scenario_harness_outcome_v1,
    run_master_v2_scenario_case_v1,
    run_master_v2_scenario_matrix_v1,
)


def test_harness_version() -> None:
    assert SCENARIO_HARNESS_LAYER_VERSION == "v1"


def test_run_matrix_size_and_names() -> None:
    a = run_master_v2_scenario_matrix_v1()
    b = build_master_v2_scenario_matrix_v1()
    assert set(a.keys()) == scenario_matrix_all_names_v1() == set(b.keys())
    assert len(a) == 5


@pytest.mark.parametrize(
    "name",
    (
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    ),
)
def test_each_harness_scenario_matches_matrix(name: str) -> None:
    c = get_master_v2_scenario_case_v1(name)
    r = run_master_v2_scenario_case_v1(name)
    assert_master_v2_scenario_harness_outcome_v1(c, r)
