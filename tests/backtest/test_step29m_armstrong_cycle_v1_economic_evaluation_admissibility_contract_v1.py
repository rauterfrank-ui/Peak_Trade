"""Contract tests for STEP 29M armstrong_cycle v1 economic evaluation admissibility v1."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.backtest import (
    step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1 as contract,
)
from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    collect_configured_strategy_params_v1,
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.strategies.registry import get_strategy_registry_entry, resolve_strategy_id

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / contract.DEFAULT_EVALUATION_CONFIG_PATH
VERSIONED_BINDING_PATH = ROOT / (
    "config/research/armstrong_cycle_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_PATH = ROOT / (
    "config/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.json"
)
MATERIAL_DIFFERENCE_PATH = ROOT / (
    "config/research/armstrong_cycle_v1_material_difference_and_non_claim_contract_v0.json"
)


def _load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def cfg() -> dict:
    return _load_config()


def test_armstrong_registry_identity() -> None:
    resolution = resolve_strategy_id("armstrong_cycle")
    assert resolution.canonical_strategy_id == "armstrong_cycle"
    entry = get_strategy_registry_entry("armstrong_cycle")
    assert entry.strategy_version == "v1"
    assert entry.implementation_ref == contract.ARMSTRONG_CYCLE_V1_STRATEGY_OWNER
    assert entry.futures_compatible is True
    assert entry.spot_compatible is False


def test_config_schema_valid(cfg: dict) -> None:
    assert (
        cfg["config_schema_version"]
        == "step29m_armstrong_cycle_v1_economic_evaluation_admissibility_v1"
    )
    assert cfg["economic_evaluation_v1"]["strategy_id"] == "armstrong_cycle"
    assert (
        cfg["economic_evaluation_v1"]["strategy_params"]
        == contract.ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS
    )


def test_excluded_params_not_in_config(cfg: dict) -> None:
    params = cfg["economic_evaluation_v1"]["strategy_params"]
    for excluded in contract.EXCLUDED_BINDING_PARAMS:
        assert excluded not in params


def test_warmup_rows(cfg: dict) -> None:
    configured = collect_configured_strategy_params_v1(cfg, "armstrong_cycle")
    effective, _ = resolve_effective_strategy_params_v1(
        "armstrong_cycle",
        project_strategy_params_for_binding_v1("armstrong_cycle", configured),
    )
    assert compute_required_warmup_rows_v1("armstrong_cycle", effective) == 0


def test_admissibility_contract_passes(cfg: dict) -> None:
    result = contract.evaluate_armstrong_cycle_v1_admissibility_contract_v1(repo_root=ROOT)
    assert result.admissibility_result == contract.AdmissibilityResult.PASS
    assert result.blocking_reasons == ()
    assert result.required_warmup_rows == contract.ARMSTRONG_CYCLE_V1_REQUIRED_WARMUP_ROWS


def test_ratification_configs_crosslink() -> None:
    binding = json.loads(VERSIONED_BINDING_PATH.read_text(encoding="utf-8"))
    scope = json.loads(SCOPE_RATIFICATION_PATH.read_text(encoding="utf-8"))
    material = json.loads(MATERIAL_DIFFERENCE_PATH.read_text(encoding="utf-8"))
    assert scope["binding_digest"] == binding["binding_digest"]
    assert scope["material_difference_digest"] == material["material_difference_digest"]
    assert binding["economic_evaluation_executed"] is False
    assert scope["economic_evaluation_executed"] is False


def test_wrong_strategy_id_rejected() -> None:
    bad = deepcopy(_load_config())
    bad["economic_evaluation_v1"] = dict(bad["economic_evaluation_v1"])
    bad["economic_evaluation_v1"]["strategy_id"] = "ehlers_cycle_filter"
    path = ROOT / "config/ops/_tmp_armstrong_bad_config.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    try:
        result = contract.evaluate_armstrong_cycle_v1_admissibility_contract_v1(
            repo_root=ROOT,
            config_path=str(path.relative_to(ROOT)),
        )
        assert result.admissibility_result == contract.AdmissibilityResult.BLOCKED
        assert "config_strategy_id_mismatch" in result.blocking_reasons
    finally:
        path.unlink(missing_ok=True)


def test_futures_only_instrument_binding(cfg: dict) -> None:
    binding = cfg["real_admissible_futures_evaluation_binding_v1"]
    lowered = f"{binding['canonical_instrument_id']} {binding['native_instrument_id']}".lower()
    for forbidden in ("btc", "xbt", "bitcoin", "spot", "synthetic_spot"):
        assert forbidden not in lowered


def test_calendar_params_canonical(cfg: dict) -> None:
    params = cfg["economic_evaluation_v1"]["strategy_params"]
    assert params["reference_date"] == "2015-10-01"
    assert params["cycle_length_days"] == 3141
    assert params["phase_position_map"] == "default"
