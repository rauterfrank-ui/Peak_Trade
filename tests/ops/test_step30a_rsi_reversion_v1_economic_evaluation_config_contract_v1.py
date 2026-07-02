"""Config contract for STEP30A rsi_reversion economic evaluation config v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest import (
    step30a_rsi_reversion_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP30A_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def _load_config() -> dict:
    return json.loads(STEP30A_CONFIG.read_text(encoding="utf-8"))


def test_step30a_config_registered_singleton() -> None:
    registry = contract.list_step30a_registered_economic_evaluation_configs_v1()
    assert registry == (contract.DEFAULT_EVALUATION_CONFIG_PATH,)
    assert STEP30A_CONFIG.is_file()


def test_step30a_config_digest_stable() -> None:
    cfg = _load_config()
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(_load_config())


def test_step30a_config_digests_frozen_after_promotion() -> None:
    cfg = _load_config()
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    assert not binding["expected_dataset_digest"].startswith("PLACEHOLDER")
    assert not binding["expected_manifest_digest"].startswith("PLACEHOLDER")
    assert binding["development_partition_digest"]
    assert binding["frozen_holdout_digest"]
    assert binding["missing_historical_l1_reason"] == "NOT_AVAILABLE_BY_PUBLIC_SOURCE"
    assert sizing["dataset_digest"] == binding["expected_dataset_digest"]
    assert not sizing["config_digest"].startswith("PLACEHOLDER")
    assert not sizing["strategy_params_digest"].startswith("PLACEHOLDER")


def test_step30a_periods_bound_and_holdout_frozen() -> None:
    cfg = _load_config()
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    assert binding["training_period"] == "2026-04-02 10:07:00+00:00..2026-05-18 23:59:00+00:00"
    assert binding["validation_period"] == "2026-05-19 00:00:00+00:00..2026-06-16 23:59:00+00:00"
    assert binding["out_of_sample_period"] == "2026-06-17 10:07:00+00:00..2026-07-01 10:07:00+00:00"


def test_step30a_ratification_flags_block_evaluation() -> None:
    cfg = _load_config()
    ratification = cfg["step30a_policy_ratification_v1"]
    assert ratification["evaluation_authorized"] is False
    assert ratification["promotion_authorized"] is False
    assert ratification["runtime_authorized"] is False
    assert ratification["parameter_tuning_allowed"] is False
    assert ratification["threshold_tuning_allowed"] is False
    assert ratification["dataset_replacement_allowed"] is False
