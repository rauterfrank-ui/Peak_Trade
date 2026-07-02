"""Registry contract for composite breakout confirmation vol-gated donchian v1 eval config."""

from __future__ import annotations

import json
from pathlib import Path

from src.backtest import (
    step29m_composite_breakout_confirmation_vol_gated_donchian_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def test_composite_breakout_confirmation_config_registered() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert EVAL_CONFIG.is_file()


def test_composite_breakout_confirmation_config_digest_stable() -> None:
    cfg = json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(
        json.loads(EVAL_CONFIG.read_text(encoding="utf-8"))
    )
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    sizing_contract = load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )
    assert sizing["config_digest"] == compute_sizing_contract_digest_v1(sizing_contract)
