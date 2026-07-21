"""Contract/unit tests for midband exit-efficiency DEVELOPMENT evaluation v3 closeout.

No real panel evaluation. Reads durable terminal evidence only. Must never
invoke the panel runner or start a second evaluation run.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v3 import (
    PACKAGE_MARKER as PACKAGE_MARKER_V3,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v3.constants_v3 import (
    CONTRACT_REL_PATH,
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v2 import (
    load_and_validate_repo_contract as load_v2_repo_contract,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v3 import (
    load_and_validate_repo_contract as load_v3_repo_contract,
)
from src.research.canonical_open_mr_exit_efficiency_hypothesis_backlog_v1 import (
    load_and_validate_repo_backlog,
)

REPO = Path(__file__).resolve().parents[2]
TEST_FILE = Path(__file__).resolve()
EVIDENCE = REPO / EVIDENCE_REL_PATH


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unit_tests_do_not_call_panel_runner_or_start_a_run() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    banned = {"run_development_evaluation", "run_arm", "load_member_bars"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in banned:
                raise AssertionError(f"banned_call:{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in banned:
                raise AssertionError(f"banned_call:{node.func.attr}")
    imports_os = False
    touches_environ = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "os" for alias in node.names):
            imports_os = True
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            imports_os = True
        if isinstance(node, ast.Attribute) and node.attr == "environ":
            touches_environ = True
    assert imports_os is False
    assert touches_environ is False


def test_package_marker_v3() -> None:
    assert (
        PACKAGE_MARKER_V3 == "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V3=true"
    )


def test_constants_v3_identity() -> None:
    assert HYPOTHESIS_ID == (
        "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V3"
    )
    assert EVALUATION_RUN_ID == "evaluate_bollinger_mr_midband_exit_efficiency_development_v3"
    assert CONTRACT_REL_PATH.endswith(
        "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v3.json"
    )
    assert (
        EVIDENCE_REL_PATH
        == "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v3/"
    )


def test_runner_script_exists() -> None:
    script = (
        REPO
        / "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v3.py"
    )
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "run_development_evaluation" in text
    assert "EvaluationRunnerLifecycleObservabilityV1" in text
    assert "AUTO_RERUN_EXECUTED=false" in text


def test_panel_runner_falsy_zero_hygiene() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v3"
        / "panel_runner_v3.py"
    )
    text = path.read_text(encoding="utf-8")
    assert 'evaluation_run_count") or -1' not in text
    assert 'evaluation_run_count", -1)' in text


def test_v3_contract_terminal_fail_run_count_one() -> None:
    report = load_v3_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is False
    assert report["hypothesis_id"] == HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 1
    assert report["evaluation_started"] is True
    assert report["evaluation_completed"] is True
    assert report["evaluation_executed"] is True
    assert report["result_class"] == "FAIL"
    assert report["economic_verdict"] == "FAIL"
    assert report["rerun_allowed"] is False
    contract = _load(REPO / CONTRACT_REL_PATH)
    assert contract["status"] == "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    assert contract["evaluation_run_count"] == 1
    assert contract["pass"] is False
    assert contract["fail"] is True
    assert contract["holdout_data_accessed"] is False


def test_v2_remains_terminal_inconclusive_run_count_one() -> None:
    v2_report = load_v2_repo_contract(REPO)
    assert v2_report["evaluation_run_count"] == 1
    assert v2_report["result_class"] == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"
    assert v2_report["rerun_allowed"] is False


def test_terminal_summary_evidence() -> None:
    summary = _load(EVIDENCE / "summary.json")
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_started"] is True
    assert summary["evaluation_completed"] is True
    assert summary["result_class"] == "FAIL"
    assert summary["economic_verdict"] == "FAIL"
    assert summary["pass"] is False
    assert summary["fail"] is True
    assert summary["baseline_members_completed"] == "46/46"
    assert summary["treatment_members_completed"] == "46/46"
    assert summary["holdout_data_accessed"] is False
    assert summary["rerun_allowed"] is False
    assert summary["v2_rerun"] is False
    assert summary["v2_partial_results_reused"] is False
    assert summary["auto_rerun_executed"] is False
    assert summary["acceptance_criteria_met"] is False
    decision = _load(EVIDENCE / "comparison_decision.json")
    assert decision["result_class"] == "FAIL"
    assert decision["reason"] == "identical_arms_no_exit_divergence"
    assert decision["exit_divergence_observed"] is False
    assert (EVIDENCE / "baseline_metrics.json").is_file()
    assert (EVIDENCE / "treatment_metrics.json").is_file()
    assert (EVIDENCE / "MANIFEST.sha256").is_file()
    assert (EVIDENCE / "runner_lifecycle_heartbeat.json").is_file()


def test_terminal_backlog_validates() -> None:
    report = load_and_validate_repo_backlog(REPO)
    assert report["valid"] is True
    assert report["preregistered_count"] == 1
    assert report["terminal_count"] == 6
    assert report["development_run_count"] == 6
    assert report["v2_evaluation_run_count"] == 1
    assert report["v3_evaluation_run_count"] == 1
    assert report["v3_result_class"] == "FAIL"
    assert report["v4_evaluation_run_count"] == 1
    assert report["v3_is_rerun_of_v2"] is False
    assert report["rerun_allowed"] is False


def test_governance_terminal_doc() -> None:
    governance = REPO / GOVERNANCE_REL_PATH
    assert governance.is_file()
    text = governance.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V3" in text
    assert "FAIL" in text
    assert "identical_arms_no_exit_divergence" in text
    assert "AWAITING_EVALUATION_EXECUTION" not in text
