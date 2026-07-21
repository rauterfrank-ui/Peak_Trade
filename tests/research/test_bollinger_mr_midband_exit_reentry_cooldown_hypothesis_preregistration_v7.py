"""Contract tests for Bollinger/MR midband exit reentry-cooldown hypothesis preregistration v7.

Definition-only: V7 is DEFINITION_ONLY_PREREGISTERED with run count 0.
V6 remains terminal FAIL (run count 1; no rerun).
Genuine economic change vs V6: same-side reentry cooldown after forced midband exit.
No evaluation executed in this slice.
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6 import (
    load_and_validate_repo_contract as load_v6,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7 import (
    CONTRACT_REL_PATH,
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    REQUIRED_BINDING_FIX_SURFACE,
    REQUIRED_COOLDOWN_BARS,
    REQUIRED_FALSY_ZERO_HYGIENE_SURFACE,
    REQUIRED_HYPOTHESIS_ID,
    REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
    REQUIRED_MECHANISM_ID,
    REQUIRED_OBSERVABILITY_SURFACE,
    REQUIRED_OWNER_SURFACE,
    REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
    HypothesisPreregistrationError,
    load_and_validate_repo_contract,
    reject_holdout_dataset_or_path,
    validate_preregistration_contract,
)
from src.research.bollinger_mr_midband_exit_efficiency_process_lifecycle_checkpoint_v5.import_safety_v5 import (
    assert_no_runner_entrypoint_on_import,
    import_safety_attestation_v5,
)

REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / CONTRACT_REL_PATH
V6_CONTRACT_PATH = (
    REPO
    / "config/research/bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v6.json"
)
OWNER_MAP_PATH = (
    REPO / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE = (
    REPO
    / "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V7.md"
)
EVIDENCE = (
    REPO / "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v7"
)
V6_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v6"
)
V7_EVAL_EVIDENCE = (
    REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7"
)
BACKLOG = REPO / "config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json"
PREREG_SRC = (
    REPO
    / "src/research/bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7.py"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_repo_contract_definition_only() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert report["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 0
    assert report["evaluation_started"] is False
    assert report["evaluation_completed"] is False
    assert report["evaluation_executed"] is False
    assert report["result_class"] == "NOT_EVALUATED"
    assert report["economic_verdict"] == "NOT_EVALUATED"
    assert report["rerun_allowed"] is False
    assert report["mechanism_id"] == REQUIRED_MECHANISM_ID
    assert report["identical_exit_mechanism_to_development_v6"] is False
    assert report["economic_change_vs_development_v6"] is True
    assert report["cooldown_bars"] == REQUIRED_COOLDOWN_BARS
    assert report["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert (
        report["development_preregistration_digest"] == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    )
    assert (
        report["development_preregistration_digest"]
        == "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
    )


def test_v6_terminal_immutability() -> None:
    v6 = load_v6(REPO)
    assert v6["hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert v6["result_class"] == "FAIL"
    assert v6["evaluation_run_count"] == 1
    assert v6["rerun_allowed"] is False
    contract = _load(V6_CONTRACT_PATH)
    assert "FAIL" in str(contract.get("status") or "")
    assert contract.get("evaluation_run_count") == 1


def test_economic_change_vs_v6_encoded() -> None:
    contract = _load(CONTRACT_PATH)
    assert contract["identical_exit_mechanism_to_development_v6"] is False
    assert contract["identical_economic_hypothesis_to_development_v6"] is False
    assert contract["economic_change_vs_development_v6"] is True
    assert contract["predecessor_partial_metrics_used"] is False
    mech = contract["exit_mechanism"]
    assert mech["mechanism_id"] == REQUIRED_MECHANISM_ID
    cooldown = mech["cooldown"]
    assert cooldown["cooldown_bars"] == 24
    assert cooldown["cooldown_hours"] == 24
    assert cooldown["scope_keys"] == ["instrument_id", "direction"]
    assert contract["control_arm"]["reentry_cooldown_applied"] is False
    assert contract["treatment"]["primary_target_side"] == "short"
    assert contract["treatment"]["midband_exit_eligibility_unchanged"] is True
    assert contract["treatment"]["max_holding_rule_unchanged"] is True


def test_no_runner_start_during_import_or_validation() -> None:
    assert_no_runner_entrypoint_on_import()
    attestation = import_safety_attestation_v5()
    assert attestation["runner_started_at_import"] is False
    assert attestation["run_slot_claimed_at_import"] is False
    assert attestation["evaluation_executed_at_import"] is False
    assert attestation["panel_data_accessed_at_import"] is False
    assert attestation["holdout_data_accessed_at_import"] is False
    tree = ast.parse(PREREG_SRC.read_text(encoding="utf-8"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    forbidden_names = {
        "run_development_evaluation",
        "claim_run_slot",
        "load_development_panel",
        "execute_evaluation",
    }
    for call in calls:
        func = call.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        assert name not in forbidden_names
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_executed"] is False


def test_holdout_access_forbidden() -> None:
    with pytest.raises(HypothesisPreregistrationError):
        reject_holdout_dataset_or_path("offline_economic_reevaluation_sealed_long_panel_v1")


def test_owner_map_and_backlog_consistency() -> None:
    owner_map = _load(OWNER_MAP_PATH)
    owners = owner_map["allowed_optimization_surfaces"]
    assert REQUIRED_OWNER_SURFACE in owners
    assert REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE in owners
    assert REQUIRED_OBSERVABILITY_SURFACE in owners
    backlog = _load(BACKLOG)
    assert backlog["governance_rules"]["preregistered_count_exact"] == 1
    pref = backlog["preregistered_hypotheses"][0]
    assert pref["hypothesis_id"] == REQUIRED_HYPOTHESIS_ID
    assert pref["evaluation_run_count"] == 0
    assert pref["lifecycle_checkpoint_surface"] == REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE
    assert pref["predecessor_hypothesis_id"] == REQUIRED_PREDECESSOR_HYPOTHESIS_ID
    assert pref["identical_exit_mechanism_to_development_v6"] is False
    assert pref["economic_change_vs_development_v6"] is True
    assert pref["cooldown_bars"] == 24
    terminal_ids = {e["hypothesis_id"] for e in backlog["terminal_hypotheses"]}
    assert REQUIRED_PREDECESSOR_HYPOTHESIS_ID in terminal_ids
    assert "NO_V7_EVALUATION_IN_THIS_SLICE" in backlog["explicit_non_actions"]
    assert "NO_V8_AUTO_CREATE" in backlog["explicit_non_actions"]
    assert "NO_V6_RERUN" in backlog["explicit_non_actions"]
    assert "NO_V7_AUTO_CREATE" in backlog["explicit_non_actions"]


def test_governance_and_evidence_present_docs_token_escaped() -> None:
    assert GOVERNANCE.is_file()
    text = GOVERNANCE.read_text(encoding="utf-8")
    assert "&#47;" in text
    assert "DEFINITION_ONLY_PREREGISTERED" in text
    assert EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST in text
    assert (EVIDENCE / "summary.json").is_file()
    assert (EVIDENCE / "safety_attestation.md").is_file()
    assert (EVIDENCE / "README.md").is_file()
    readme = (EVIDENCE / "README.md").read_text(encoding="utf-8")
    assert "&#47;" in readme
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 0
    assert summary["run_slot_claimed"] is False
    assert summary["runner_started"] is False
    assert summary["panel_data_accessed"] is False
    assert summary["holdout_accessed"] is False
    assert summary["economic_hypothesis_changed"] is True


def test_no_v7_evaluation_evidence_dir() -> None:
    assert not V7_EVAL_EVIDENCE.exists()
    assert V6_EVAL_EVIDENCE.is_dir()


def test_mutated_run_count_fails_closed() -> None:
    contract = _load(CONTRACT_PATH)
    bad = copy.deepcopy(contract)
    bad["evaluation_run_count"] = 1
    with pytest.raises(HypothesisPreregistrationError):
        validate_preregistration_contract(bad)


def test_surfaces_bound() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["observability_surface"] == REQUIRED_OBSERVABILITY_SURFACE
    assert REQUIRED_BINDING_FIX_SURFACE
    assert REQUIRED_FALSY_ZERO_HYGIENE_SURFACE
