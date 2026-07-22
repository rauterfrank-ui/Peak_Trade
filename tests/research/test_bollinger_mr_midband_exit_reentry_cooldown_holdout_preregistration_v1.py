"""Contract tests for Exit V8 holdout confirmation preregistration v1.

Definition-only. No holdout data access. No runner. No V8 reopen/rerun.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
    CONTRACT_REL_PATH,
    EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
    EXPECTED_HOLDOUT_SPLIT_DIGEST,
    GOVERNANCE_REL_PATH,
    OPERATOR_GO_ENV,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_MECHANISM_ID,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    REQUIRED_V8_PREREGISTRATION_DIGEST,
    HoldoutPreregistrationError,
    assert_execution_go_present,
    expected_holdout_split_digest,
    load_and_validate_repo_holdout_contract,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
EVIDENCE = REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1"
GOVERNANCE = REPO / GOVERNANCE_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_holdout_contract_validates() -> None:
    report = load_and_validate_repo_holdout_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["holdout_executed"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["mechanism_id"] == REQUIRED_MECHANISM_ID
    assert report["holdout_run_count"] == 1
    assert report["holdout_run_limit"] == 1
    assert report["execution_authorized"] is False
    assert report["holdout_split_digest"] == EXPECTED_HOLDOUT_SPLIT_DIGEST
    assert report["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST
    assert report["v8_preregistration_digest"] == REQUIRED_V8_PREREGISTRATION_DIGEST
    assert report["frozen_mechanism_match"] is True
    assert report["terminal_holdout_result_class"] == "FAIL"


def test_hypothesis_id_is_new_and_not_v8_reuse() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert contract["hypothesis_id"] != REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert contract["holdout_run_count"] == 1
    assert contract["status"] == "HOLDOUT_EVALUATION_EXECUTED_TERMINAL"


def test_v8_development_contract_unchanged_and_holdout_forbidden() -> None:
    v8 = _load(
        REPO
        / "config/research/bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v8.json"
    )
    assert v8["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v8["holdout_allowed"] is False
    assert v8["holdout_forbidden"] is True
    assert v8["exit_mechanism"]["mechanism_id"] == REQUIRED_MECHANISM_ID


def test_split_digest_matches() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["splits"]["split_intervals_sha256"] == expected_holdout_split_digest()
    summary = _load(EVIDENCE / "summary.json")
    assert summary["holdout_split_digest"] == EXPECTED_HOLDOUT_SPLIT_DIGEST
    assert summary["holdout_preregistration_digest"] == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST


def test_execution_go_absent_by_default() -> None:
    with pytest.raises(HoldoutPreregistrationError, match="HOLDOUT_V1_EXECUTION_GO_REQUIRED"):
        assert_execution_go_present(environ={})
    assert_execution_go_present(environ={OPERATOR_GO_ENV: "true"})


def test_evidence_and_governance_exist_with_evaluate_dir() -> None:
    assert GOVERNANCE.is_file()
    assert (EVIDENCE / "README.md").is_file()
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "split_manifest.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "timing_proof.txt").is_file()
    evaluate = REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1"
    assert evaluate.is_dir()
    assert (evaluate / "summary.json").is_file()
    assert (evaluate / ".holdout_run_consumed").is_file()
