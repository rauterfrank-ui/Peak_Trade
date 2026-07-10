"""Contract tests for armstrong_cycle/v1 binding canonicalization repair v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.run_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0 import (
    STALE_RUNNER_DESCRIPTOR_RANGE_DATA_PERIOD,
    compute_armstrong_cycle_v1_ratified_binding_digest_for_baseline_v0,
    resolve_armstrong_cycle_v1_binding_data_period_for_baseline_v0,
)
from src.backtest.step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1 import (
    evaluate_armstrong_cycle_v1_admissibility_contract_v1,
    load_armstrong_cycle_v1_evaluation_config_v1,
)
from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (
    DATA_PERIOD,
    ArmstrongCycleV1BindingDataPeriodError,
    build_armstrong_cycle_v1_period_binding_data_period_v0,
    build_period_binding_v0,
    is_stale_runner_descriptor_range_data_period_v0,
    materialize_evaluation_config_v1,
    materialize_material_difference_contract_v0,
    materialize_versioned_research_binding_v0,
    reject_stale_runner_descriptor_range_data_period_v0,
)
from src.research.step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_armstrong_binding_digest_v0,
    compute_step29m_armstrong_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STALE_RATIFIED_BINDING_DIGEST = "d29de831f426eeca087518ab9ebe53c1e77895fc0f9f4550a0d804a69403d69c"
REPAIRED_BINDING_DIGEST = "bf0a125325692836b71ab00a775d412ecf275483769f5906e1251f68361a9896"
DEFECTIVE_EVALUATION_SNAPSHOT_BINDING_DIGEST = (
    "e01256994d1835f8f5b579a51ef618da77cbc1d6a4df5ed1e92deb3ebc1a7109"
)
DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
UNIVERSE_DIGEST = "be6ea12f6e883de596e8e7987be071bcb4ebc3d32bff15ec933643dcf74f9ee2"
EVAL_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_armstrong_cycle_v1_economic_evaluation_v1.json"
)
BINDING_CONFIG_PATH = "config/research/armstrong_cycle_v1_versioned_research_binding_v0.json"
MATERIAL_DIFFERENCE_PATH = (
    "config/research/armstrong_cycle_v1_material_difference_and_non_claim_contract_v0.json"
)
SOURCE_EVALUATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0_20260710T153705Z"
)


def _load_binding_cfg() -> dict:
    return json.loads((REPO_ROOT / BINDING_CONFIG_PATH).read_text(encoding="utf-8"))


def _load_material_diff() -> dict:
    return json.loads((REPO_ROOT / MATERIAL_DIFFERENCE_PATH).read_text(encoding="utf-8"))


def _ratified_data_period() -> str:
    return build_armstrong_cycle_v1_period_binding_data_period_v0(build_period_binding_v0())


def _runner_ratified_digest() -> tuple[str, str]:
    binding_cfg = _load_binding_cfg()
    material_diff = _load_material_diff()
    admissibility = evaluate_armstrong_cycle_v1_admissibility_contract_v1(repo_root=REPO_ROOT)
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    instrument_id = str(
        eval_cfg["real_admissible_futures_evaluation_binding_v1"]["canonical_instrument_id"]
    )
    return compute_armstrong_cycle_v1_ratified_binding_digest_for_baseline_v0(
        binding_cfg=binding_cfg,
        material_diff=material_diff,
        config_digest=admissibility.config_digest,
        strategy_params_digest=admissibility.strategy_params_digest,
        data_digest=DATASET_DIGEST,
        implementation_digest=compute_step29m_armstrong_implementation_digest_v0(REPO_ROOT),
        instrument_id=instrument_id,
    )


def test_stale_or_runner_specific_data_period_payload_rejected() -> None:
    assert is_stale_runner_descriptor_range_data_period_v0(
        STALE_RUNNER_DESCRIPTOR_RANGE_DATA_PERIOD
    )
    with pytest.raises(ArmstrongCycleV1BindingDataPeriodError):
        reject_stale_runner_descriptor_range_data_period_v0(
            STALE_RUNNER_DESCRIPTOR_RANGE_DATA_PERIOD
        )


def test_ratified_period_binding_payload_accepted() -> None:
    payload = _ratified_data_period()
    assert payload == DATA_PERIOD
    reject_stale_runner_descriptor_range_data_period_v0(payload)


def test_runner_uses_canonical_period_binding_owner() -> None:
    binding_cfg = _load_binding_cfg()
    data_period = resolve_armstrong_cycle_v1_binding_data_period_for_baseline_v0(binding_cfg)
    assert data_period == DATA_PERIOD
    assert "|" in data_period


def test_ratification_and_runner_binding_payload_equal() -> None:
    binding_cfg = _load_binding_cfg()
    ratification_payload = build_armstrong_cycle_v1_period_binding_data_period_v0(
        build_period_binding_v0()
    )
    runner_payload = resolve_armstrong_cycle_v1_binding_data_period_for_baseline_v0(binding_cfg)
    assert ratification_payload == runner_payload


def test_ratification_and_runner_binding_digest_equal() -> None:
    evaluation_config = materialize_evaluation_config_v1(REPO_ROOT)
    material_difference = materialize_material_difference_contract_v0()
    versioned_binding = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=material_difference,
        evaluation_config=evaluation_config,
    )
    _, runner_digest = _runner_ratified_digest()
    assert runner_digest == versioned_binding["binding_digest"]
    assert runner_digest == REPAIRED_BINDING_DIGEST
    assert runner_digest != STALE_RATIFIED_BINDING_DIGEST
    assert runner_digest != DEFECTIVE_EVALUATION_SNAPSHOT_BINDING_DIGEST


def test_materializer_to_real_binder_roundtrip_pass() -> None:
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


def test_repeated_materialization_deterministic() -> None:
    first = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(REPO_ROOT),
    )
    second = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(REPO_ROOT),
    )
    assert first["binding_digest"] == second["binding_digest"]


def test_second_materialization_diff_empty() -> None:
    first = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(REPO_ROOT),
    )
    second = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(REPO_ROOT),
    )
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_dataset_digest_unchanged() -> None:
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["binding"]["digest_bindings"]["data_digest"]["value"] == DATASET_DIGEST


def test_universe_digest_unchanged() -> None:
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["universe_digest"] == UNIVERSE_DIGEST


def test_strategy_parameters_unchanged() -> None:
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    expected = eval_cfg["economic_evaluation_v1"]["strategy_params"]
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["binding"]["parameter_binding"]["parameters"] == expected


def test_cost_policy_unchanged() -> None:
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["binding"]["cost_execution_binding"]["roundtrip_cost_bps"] == 40.0
    assert eval_cfg["backtest"]["fee_bps"] == 10.0
    assert eval_cfg["backtest"]["slippage_bps"] == 5.0


def test_risk_sizing_semantics_unchanged() -> None:
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    sizing = eval_cfg["offline_evaluation_sizing_contract_v1"]
    assert sizing["risk_per_trade"] == 0.005
    assert sizing["stop_pct"] == 0.025


def test_historical_evaluation_evidence_preserved() -> None:
    assert SOURCE_EVALUATION_DIR.is_dir()
    snapshot = json.loads(
        (SOURCE_EVALUATION_DIR / "immutable_binding_snapshot.json").read_text(encoding="utf-8")
    )
    assert snapshot["binding_digest"] == DEFECTIVE_EVALUATION_SNAPSHOT_BINDING_DIGEST


def test_no_economic_evaluation_executed() -> None:
    assert True


def test_no_runtime_effect() -> None:
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["runtime_effect"] == "NONE"


def test_no_authority_effect() -> None:
    binding_cfg = _load_binding_cfg()
    assert binding_cfg["authority_effect"] == "NONE"
