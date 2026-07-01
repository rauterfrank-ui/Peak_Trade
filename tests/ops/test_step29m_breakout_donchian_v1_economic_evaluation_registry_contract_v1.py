"""Registry contract for STEP 29M breakout_donchian v1 economic evaluation config."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.backtest import (
    step29m_breakout_donchian_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs" / "governance" / "PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
BREAKOUT_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file()
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_breakout_config_registered_in_canonical_registry() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert BREAKOUT_CONFIG.is_file()


def test_breakout_config_path_bound_in_progress_registry() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_PATH") == (
        contract.DEFAULT_EVALUATION_CONFIG_PATH
    )
    registered = _field_value(section, "STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS")
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registered.split(",")


def test_breakout_config_digest_stable() -> None:
    cfg = json.loads(BREAKOUT_CONFIG.read_text(encoding="utf-8"))
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(
        json.loads(BREAKOUT_CONFIG.read_text(encoding="utf-8"))
    )
    from src.backtest.offline_evaluation_sizing_contract_v1 import (
        compute_sizing_contract_digest_v1,
        load_offline_evaluation_sizing_contract_v1,
    )

    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    contract = load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )
    assert sizing["config_digest"] == compute_sizing_contract_digest_v1(contract)


def test_breakout_next_evaluation_strategy_binding() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_EVALUATION_STRATEGY_ID") == "breakout_donchian"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_VERSION") == "v1"
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_STATUS") == (
        "POLICY_RATIFIED_CONFIG_ADMISSIBLE_AWAITING_SEPARATE_RUN"
    )
