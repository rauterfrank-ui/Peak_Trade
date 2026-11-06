"""Contract tests for Bollinger/MR midband exit-efficiency hypothesis after terminal closeout."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
    REQUIRED_HYPOTHESIS_ID,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V1.md"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_terminal_inconclusive() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 1
    assert report["evaluation_run_count_authorized"] == 1
    assert report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["pass_criteria_frozen"] is True
    assert report["cost_model_canonical"] is True


def test_terminal_contract_fields() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["slice_class"] == "DEVELOPMENT_EVALUATION_TERMINAL_CLOSEOUT"
    assert contract["evaluation_executed"] is True
    assert contract["evaluation_started"] is True
    assert contract["evaluation_completed"] is False
    assert contract["evaluation_run_count"] == 1
    assert contract["pass"] is False
    assert contract["fail"] is False
    assert contract["holdout_data_accessed"] is False
    assert contract["exit_mechanism"]["frozen_parameters"] == REQUIRED_FROZEN_EXIT_PARAMETERS
    assert float(contract["cost_model"]["cost_multiplier"]) == 1.0
    assert contract["decision_thresholds"]["pass_criteria_frozen"] is True


def test_holdout_still_rejected() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_preregistration_governance_doc_present() -> None:
    assert GOVERNANCE.is_file()
