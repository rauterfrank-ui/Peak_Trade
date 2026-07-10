"""Registry contract for STEP 29M vol_breakout v1 economic evaluation config."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from src.backtest import (
    step29m_vol_breakout_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
VOL_BREAKOUT_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def _load_config() -> dict:
    return json.loads(VOL_BREAKOUT_CONFIG.read_text(encoding="utf-8"))


def test_vol_breakout_config_registered_in_canonical_registry() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert VOL_BREAKOUT_CONFIG.is_file()


def test_vol_breakout_config_digest_stable() -> None:
    cfg = _load_config()
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(
        json.loads(VOL_BREAKOUT_CONFIG.read_text(encoding="utf-8"))
    )


def test_vol_breakout_sizing_config_digest_matches_sizing_contract() -> None:
    cfg = _load_config()
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    sizing_contract = load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )
    expected_sizing_digest = compute_sizing_contract_digest_v1(sizing_contract)
    assert sizing["config_digest"] == expected_sizing_digest
    assert sizing["config_digest"] != compute_evaluation_config_digest_v1(cfg)


def test_vol_breakout_evaluation_config_digest_rejected_in_sizing_binding() -> None:
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
