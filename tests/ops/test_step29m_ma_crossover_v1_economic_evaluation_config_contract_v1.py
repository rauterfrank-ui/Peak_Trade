"""Config contract for STEP 29M ma_crossover v1 economic evaluation config v1."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

from src.backtest import (
    step29m_ma_crossover_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS_REGISTRY = REPO_ROOT / "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md"
MA_CROSSOVER_CONFIG = REPO_ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH
RANK1_EVIDENCE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/bounded_step29m_additional_existing_strategy_policy_ratification_candidate_decision_read_only_v0_20260702T010015Z"
)


def _read_registry() -> str:
    assert PROGRESS_REGISTRY.is_file()
    return PROGRESS_REGISTRY.read_text(encoding="utf-8")


def _field_value(text: str, field: str) -> str:
    match = re.search(
        rf"\| `{re.escape(field)}` \| `([^`]*)`(?: <!--.*?-->)? \|",
        text,
    )
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _step_29m_section(text: str) -> str:
    start = text.index("#### RUNBOOK_STEP_29M — Economic Viability Evidence v1")
    end = text.index("#### RUNBOOK_STEP_29N — Promotion Economic Gate Binding v1", start)
    return text[start:end]


def test_ma_crossover_config_registered_in_canonical_registry() -> None:
    registry = contract.list_step29m_registered_economic_evaluation_configs_v1()
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registry
    assert MA_CROSSOVER_CONFIG.is_file()


def test_ma_crossover_config_path_bound_in_progress_registry() -> None:
    section = _step_29m_section(_read_registry())
    registered = _field_value(section, "STEP29M_REGISTERED_ECONOMIC_EVALUATION_CONFIGS").replace(
        "&#47;", "/"
    )
    assert contract.DEFAULT_EVALUATION_CONFIG_PATH in registered.split(",")
    assert _field_value(section, "NEXT_EVALUATION_CONFIG_PATH").replace("&#47;", "/") == (
        contract.DEFAULT_EVALUATION_CONFIG_PATH
    )


def test_ma_crossover_config_digest_stable() -> None:
    cfg = json.loads(MA_CROSSOVER_CONFIG.read_text(encoding="utf-8"))
    digest = compute_evaluation_config_digest_v1(cfg)
    assert len(digest) == 64
    assert digest == compute_evaluation_config_digest_v1(
        json.loads(MA_CROSSOVER_CONFIG.read_text(encoding="utf-8"))
    )
    sizing = cfg["offline_evaluation_sizing_contract_v1"]
    sizing_contract = load_offline_evaluation_sizing_contract_v1(
        cfg,
        strategy_params_digest=sizing["strategy_params_digest"],
        dataset_digest=sizing["dataset_digest"],
    )
    assert sizing["config_digest"] == compute_sizing_contract_digest_v1(sizing_contract)


def test_ma_crossover_ratification_config_flags_explicit() -> None:
    cfg = json.loads(MA_CROSSOVER_CONFIG.read_text(encoding="utf-8"))
    ratification = cfg["step29m_policy_ratification_v1"]
    assert ratification["evaluation_authorized"] is False
    assert ratification["promotion_authorized"] is False
    assert ratification["runtime_authorized"] is False
    assert ratification["parameter_tuning_allowed"] is False
    assert ratification["threshold_tuning_allowed"] is False
    assert ratification["dataset_replacement_allowed"] is False


def test_changed_economic_policy_rejected() -> None:
    bad = json.loads(MA_CROSSOVER_CONFIG.read_text(encoding="utf-8"))
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["economic_validity_policy_version"] = (
        "economic_validity_policy_v2"
    )
    reasons = contract.verify_ma_crossover_v1_config_schema_v1(bad)
    assert "economic_validity_policy_version_mismatch" in reasons


def test_conflicting_sizing_values_rejected() -> None:
    bad = deepcopy(json.loads(MA_CROSSOVER_CONFIG.read_text(encoding="utf-8")))
    bad["offline_evaluation_sizing_contract_v1"] = dict(
        bad["offline_evaluation_sizing_contract_v1"]
    )
    bad["offline_evaluation_sizing_contract_v1"]["stop_pct"] = 0.02
    reasons = contract.verify_ma_crossover_v1_sizing_policy_v1(bad)
    assert "stop_pct_not_ratified" in reasons


def test_rank1_evidence_ref_bound_in_registry() -> None:
    section = _step_29m_section(_read_registry())
    assert str(RANK1_EVIDENCE) in _field_value(
        section, "MA_CROSSOVER_V1_RANK1_CANDIDATE_EVIDENCE_REF"
    )


def test_next_canonical_step_preflight_read_only() -> None:
    section = _step_29m_section(_read_registry())
    assert _field_value(section, "NEXT_CANONICAL_STEP") == (
        "BOUNDED_STEP29M_MA_CROSSOVER_V1_REAL_ADMISSIBLE_FUTURES_ECONOMIC_EVALUATION_PREFLIGHT_READ_ONLY_V0"
    )
