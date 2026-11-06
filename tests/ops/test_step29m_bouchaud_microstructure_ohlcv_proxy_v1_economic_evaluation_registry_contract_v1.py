"""Registry contract for STEP 29M bouchaud_microstructure_ohlcv_proxy v1 economic evaluation config."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 as contract,
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
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_failed_execution_contract_evidence_and_unchanged_retry_block_v0 import (
    NEW_BINDING_DIGEST,
    NEW_EVALUATION_CONFIG_DIGEST,
    NEW_SIZING_CONFIG_DIGEST,
    OLD_BINDING_DIGEST,
    OLD_SIZING_CONFIG_DIGEST,
    PRIOR_FAILED_ATTEMPT_DIR,
    build_failed_attempt_registration_payload_v0,
    register_failed_execution_contract_evidence_v0,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_evaluation_config_v1,
)
from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0,
    compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BOUCHAUD_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH
BINDING_CONFIG = (
    REPO_ROOT
    / "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
MATERIAL_DIFF_CONFIG = (
    REPO_ROOT
    / "config/research/bouchaud_microstructure_ohlcv_proxy_v1_material_difference_and_non_claim_contract_v0.json"
)


def _load_config() -> dict:
    return json.loads(BOUCHAUD_CONFIG.read_text(encoding="utf-8"))


def _admissibility() -> contract.BouchaudMicrostructureOhlcvProxyV1AdmissibilityContractResultV1:
    return contract.evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=REPO_ROOT,
    )


def _sizing_contract(cfg: dict):
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    return load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )


def test_bouchaud_config_registered_in_canonical_registry() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert BOUCHAUD_CONFIG.is_file()


def test_bouchaud_sizing_config_digest_matches_sizing_contract() -> None:
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    expected_sizing_digest = compute_sizing_contract_digest_v1(_sizing_contract(cfg))
    assert sizing["config_digest"] == expected_sizing_digest
    assert sizing["config_digest"] == NEW_SIZING_CONFIG_DIGEST
    assert sizing["config_digest"] != OLD_SIZING_CONFIG_DIGEST
    assert sizing["config_digest"] != compute_evaluation_config_digest_v1(cfg)


def test_bouchaud_stale_sizing_digest_rejected_by_admissibility_guard() -> None:
    cfg = _load_config()
    bad = deepcopy(cfg)
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["config_digest"] = OLD_SIZING_CONFIG_DIGEST
    adm = _admissibility()
    reasons = contract.verify_bouchaud_microstructure_ohlcv_proxy_v1_sizing_config_digest_v1(
        bad,
        strategy_params_digest=adm.strategy_params_digest,
    )
    assert "sizing_config_digest_mismatch" in reasons
    with pytest.raises(OfflineEvaluationSizingError, match="sizing_config_digest_mismatch"):
        bind_offline_evaluation_sizing_v1(
            bad,
            strategy_params_digest=adm.strategy_params_digest,
            dataset_digest=bad["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
        )


def test_bouchaud_correct_sizing_digest_accepted_by_admissibility_guard() -> None:
    guard = contract.evaluate_bouchaud_microstructure_ohlcv_proxy_v1_sizing_digest_admissibility_guard_v1(
        repo_root=REPO_ROOT,
    )
    assert guard.admissible is True
    assert guard.reason_code == "OK"
    assert guard.economic_evaluation_executed is False
    assert guard.bound_sizing_config_digest == NEW_SIZING_CONFIG_DIGEST
    assert guard.computed_sizing_config_digest == NEW_SIZING_CONFIG_DIGEST


def test_bouchaud_repaired_sizing_config_digest_accepted_by_binding() -> None:
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    adm = _admissibility()
    contract_obj, _ = bind_offline_evaluation_sizing_v1(
        deepcopy(cfg),
        strategy_params_digest=adm.strategy_params_digest,
        dataset_digest=sizing["dataset_digest"],
    )
    assert contract_obj.config_digest == NEW_SIZING_CONFIG_DIGEST


def test_bouchaud_real_sizing_digest_owner_used() -> None:
    cfg = _load_config()
    materialized = materialize_evaluation_config_v1(REPO_ROOT)
    assert (
        materialized["offline_evaluation_sizing_contract_v1"]["config_digest"]
        == NEW_SIZING_CONFIG_DIGEST
    )
    assert materialized["offline_evaluation_sizing_contract_v1"][
        "config_digest"
    ] == compute_sizing_contract_digest_v1(_sizing_contract(materialized))


def test_bouchaud_materializer_to_binder_roundtrip_pass() -> None:
    materialized = materialize_evaluation_config_v1(REPO_ROOT)
    committed = _load_config()
    assert materialized == committed
    adm = _admissibility()
    bind_offline_evaluation_sizing_v1(
        deepcopy(materialized),
        strategy_params_digest=adm.strategy_params_digest,
        dataset_digest=materialized["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
    )


def test_bouchaud_repeated_materialization_deterministic() -> None:
    first = materialize_evaluation_config_v1(REPO_ROOT)
    second = materialize_evaluation_config_v1(REPO_ROOT)
    assert first == second


def test_bouchaud_second_materialization_diff_empty() -> None:
    first = json.dumps(materialize_evaluation_config_v1(REPO_ROOT), sort_keys=True)
    second = json.dumps(materialize_evaluation_config_v1(REPO_ROOT), sort_keys=True)
    assert first == second


def test_bouchaud_binding_digest_matches_canonical_materializer_after_repair() -> None:
    cfg = _load_config()
    adm = _admissibility()
    binding_cfg = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    material_diff = json.loads(MATERIAL_DIFF_CONFIG.read_text(encoding="utf-8"))
    eval_binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    data_period = binding_cfg["binding"]["period_binding"]["data_period"]
    binding_digest = compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
        config_digest=adm.config_digest,
        data_digest=cfg["offline_evaluation_sizing_contract_v1"]["dataset_digest"],
        implementation_digest=compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(
            REPO_ROOT
        ),
        strategy_params_digest=adm.strategy_params_digest,
        material_difference_digest=material_diff["material_difference_digest"],
        hypothesis_id=binding_cfg["hypothesis_id"],
        instrument_id=eval_binding["canonical_instrument_id"],
        data_period=data_period,
    )
    assert binding_digest == NEW_BINDING_DIGEST
    assert binding_cfg["binding_digest"] == NEW_BINDING_DIGEST
    assert binding_cfg["binding_digest"] != OLD_BINDING_DIGEST
    assert adm.config_digest == NEW_EVALUATION_CONFIG_DIGEST


def test_bouchaud_transitive_digest_chain_complete() -> None:
    adm = _admissibility()
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    assert sizing["config_digest"] == NEW_SIZING_CONFIG_DIGEST
    assert adm.config_digest == NEW_EVALUATION_CONFIG_DIGEST
    binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
    assert (
        binding["binding"]["digest_bindings"]["config_digest"]["value"]
        == NEW_EVALUATION_CONFIG_DIGEST
    )
    assert binding["binding_digest"] == NEW_BINDING_DIGEST


def test_bouchaud_semantic_payload_unchanged() -> None:
    materialized = materialize_evaluation_config_v1(REPO_ROOT)
    cfg = _load_config()
    for section in ("economic_evaluation_v1", "risk", "research_scope_binding_v1"):
        assert materialized[section] == cfg[section]


def test_bouchaud_previous_failed_attempt_preserved() -> None:
    registration = build_failed_attempt_registration_payload_v0()
    assert registration["FAILED_EXECUTION_CONTRACT_EVIDENCE"] is True
    assert registration["ECONOMIC_NEGATIVE_EDGE_EVIDENCE"] is False
    assert registration["UNCHANGED_RETRY_ALLOWED"] is False
    assert registration["PREVIOUS_FAILED_ATTEMPT_REF"] == str(PRIOR_FAILED_ATTEMPT_DIR)


def test_bouchaud_unchanged_retry_block_preserved() -> None:
    payload = register_failed_execution_contract_evidence_v0(REPO_ROOT)
    assert payload["unchanged_retry_blocked"] is True
    assert payload["unchanged_retry_allowed"] is False


def test_bouchaud_no_runtime_effect() -> None:
    payload = register_failed_execution_contract_evidence_v0(REPO_ROOT)
    assert payload["runtime_effect"] == "NONE"
    assert payload["authority_effect"] == "NONE"
