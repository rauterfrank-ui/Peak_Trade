"""Contract tests for STEP29M armstrong_cycle/v1 offline economic baseline materialization v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (
    build_armstrong_cycle_v1_period_binding_data_period_v0,
    materialize_evaluation_config_v1,
    materialize_material_difference_contract_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_armstrong_binding_digest_v0,
    compute_step29m_armstrong_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_implementation_digest_deterministic() -> None:
    first = compute_step29m_armstrong_implementation_digest_v0(REPO_ROOT)
    second = compute_step29m_armstrong_implementation_digest_v0(REPO_ROOT)
    assert first == second
    assert len(first) == 64


def test_binding_digest_roundtrip() -> None:
    evaluation_config = materialize_evaluation_config_v1(REPO_ROOT)
    material_difference = materialize_material_difference_contract_v0()
    versioned_binding = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=material_difference,
        evaluation_config=evaluation_config,
    )
    binding = versioned_binding["binding"]
    digest_bindings = binding["digest_bindings"]
    recomputed = compute_step29m_armstrong_binding_digest_v0(
        config_digest=digest_bindings["config_digest"]["value"],
        data_digest=digest_bindings["data_digest"]["value"],
        implementation_digest=digest_bindings["implementation_digest"]["value"],
        strategy_params_digest=digest_bindings["strategy_params_digest"]["value"],
        material_difference_digest=digest_bindings["material_difference_digest"]["value"],
        hypothesis_id=versioned_binding["hypothesis_id"],
        instrument_id="inst-eth-usdt-perp",
        data_period=build_armstrong_cycle_v1_period_binding_data_period_v0(
            binding["period_binding"]
        ),
        universe_digest=digest_bindings["universe_digest"]["value"],
    )
    assert recomputed == versioned_binding["binding_digest"]


def test_second_materialization_produces_identical_binding() -> None:
    evaluation_config_a = materialize_evaluation_config_v1(REPO_ROOT)
    material_difference_a = materialize_material_difference_contract_v0()
    binding_a = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=material_difference_a,
        evaluation_config=evaluation_config_a,
    )
    evaluation_config_b = materialize_evaluation_config_v1(REPO_ROOT)
    material_difference_b = materialize_material_difference_contract_v0()
    binding_b = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=material_difference_b,
        evaluation_config=evaluation_config_b,
    )
    assert json.dumps(binding_a, sort_keys=True) == json.dumps(binding_b, sort_keys=True)
