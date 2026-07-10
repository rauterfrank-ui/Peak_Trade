"""Registry contract for STEP 29M el_karoui_vol_model v1 economic evaluation config."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_el_karoui_vol_model_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    OfflineEvaluationSizingError,
    bind_offline_evaluation_sizing_v1,
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.research.el_karoui_vol_model_v1_offline_economic_evaluation_scope_ratification_v0 import (
    compute_universe_digest_v0,
)
from src.research.step29m_el_karoui_vol_model_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_el_karoui_binding_digest_v0,
    compute_step29m_el_karoui_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EL_KAROUI_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH
RATIFIED_BINDING_DIGEST = "2ba82dd901c940a5d41d2aabd3ddeb693dbbf7cdd1f0308275d11b6df4d988b3"
STALE_RATIFIED_BINDING_DIGEST = "223845f2047779218390fc245c3f2ebb04631bb068139e3d40731781906d099b"
STALE_SIZING_CONFIG_DIGEST = "d49d85ede512dda6d3200dbf9a50d306a423de4279767d228d20d28d88975dd8"
RECOMPUTED_SIZING_CONFIG_DIGEST = "dd9152621c58c1ed283c7b42601d66cf4fdcd1bb009f439d8583ebef64dc4516"


def _load_config() -> dict:
    return json.loads(EL_KAROUI_CONFIG.read_text(encoding="utf-8"))


def _admissibility() -> contract.ElKarouiVolModelV1AdmissibilityContractResultV1:
    return contract.evaluate_el_karoui_vol_model_v1_admissibility_contract_v1(repo_root=REPO_ROOT)


def _sizing_contract(cfg: dict):
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    return load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )


def test_el_karoui_config_registered_in_canonical_registry() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert EL_KAROUI_CONFIG.is_file()


def test_el_karoui_config_digest_stable() -> None:
    cfg = _load_config()
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(
        json.loads(EL_KAROUI_CONFIG.read_text(encoding="utf-8"))
    )


def test_el_karoui_sizing_config_digest_matches_sizing_contract() -> None:
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    expected_sizing_digest = compute_sizing_contract_digest_v1(_sizing_contract(cfg))
    assert sizing["config_digest"] == expected_sizing_digest
    assert sizing["config_digest"] == RECOMPUTED_SIZING_CONFIG_DIGEST
    assert sizing["config_digest"] != STALE_SIZING_CONFIG_DIGEST
    assert sizing["config_digest"] != compute_evaluation_config_digest_v1(cfg)


def test_el_karoui_stale_sizing_config_digest_rejected_by_binding() -> None:
    cfg = _load_config()
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["config_digest"] = STALE_SIZING_CONFIG_DIGEST
    sizing = bad["offline_evaluation_sizing_contract_v1"]
    adm = _admissibility()
    with pytest.raises(OfflineEvaluationSizingError, match="sizing_config_digest_mismatch"):
        bind_offline_evaluation_sizing_v1(
            bad,
            strategy_params_digest=adm.strategy_params_digest,
            dataset_digest=sizing["dataset_digest"],
        )


def test_el_karoui_repaired_sizing_config_digest_accepted_by_binding() -> None:
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    adm = _admissibility()
    contract_obj, _ = bind_offline_evaluation_sizing_v1(
        deepcopy(cfg),
        strategy_params_digest=adm.strategy_params_digest,
        dataset_digest=sizing["dataset_digest"],
    )
    assert contract_obj.config_digest == RECOMPUTED_SIZING_CONFIG_DIGEST


def test_el_karoui_evaluation_config_digest_rejected_in_sizing_binding() -> None:
    cfg = _load_config()
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["config_digest"] = (
        compute_evaluation_config_digest_v1(cfg)
    )
    sizing = bad["offline_evaluation_sizing_contract_v1"]
    sizing_contract = load_offline_evaluation_sizing_contract_v1(
        bad,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )
    assert sizing["config_digest"] != compute_sizing_contract_digest_v1(sizing_contract)


def test_el_karoui_binding_digest_matches_canonical_materializer_after_repair() -> None:
    cfg = _load_config()
    adm = _admissibility()
    binding_cfg = json.loads(
        (
            REPO_ROOT / "config/research/el_karoui_vol_model_v1_versioned_research_binding_v0.json"
        ).read_text(encoding="utf-8")
    )
    material_diff = json.loads(
        (
            REPO_ROOT
            / "config/research/el_karoui_vol_model_v1_material_difference_and_non_claim_contract_v0.json"
        ).read_text(encoding="utf-8")
    )
    eval_binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    data_period = (
        f"{eval_binding['training_period']}|"
        f"{eval_binding['validation_period']}|"
        f"{eval_binding['out_of_sample_period']}"
    )
    binding_digest = compute_step29m_el_karoui_binding_digest_v0(
        config_digest=adm.config_digest,
        data_digest=cfg["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
        implementation_digest=compute_step29m_el_karoui_implementation_digest_v0(REPO_ROOT),
        strategy_params_digest=adm.strategy_params_digest,
        material_difference_digest=material_diff["material_difference_digest"],
        hypothesis_id=binding_cfg["hypothesis_id"],
        instrument_id=eval_binding["canonical_instrument_id"],
        data_period=data_period,
        universe_digest=compute_universe_digest_v0(),
    )
    assert binding_digest == RATIFIED_BINDING_DIGEST
    assert binding_cfg["binding_digest"] == RATIFIED_BINDING_DIGEST
    assert binding_cfg["binding_digest"] != STALE_RATIFIED_BINDING_DIGEST
    assert binding_cfg["binding"]["digest_bindings"]["config_digest"]["value"] == adm.config_digest
