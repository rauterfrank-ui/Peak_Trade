"""Contract/unit tests for midband exit-efficiency DEVELOPMENT evaluation v5 closeout.

No real panel evaluation. Reads durable terminal evidence only. Must never
invoke the panel runner or start a second evaluation run.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v5 import (
    PACKAGE_MARKER as PACKAGE_MARKER_V5,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v5.constants_v5 import (
    BINDING_FIX_SURFACE,
    CONTRACT_REL_PATH,
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v4 import (
    load_and_validate_repo_contract as load_v4_repo_contract,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v5 import (
    load_and_validate_repo_contract as load_v5_repo_contract,
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
    banned = {
        "run_development_evaluation",
        "run_arm",
        "load_member_bars",
        "resolve_development_archive_root",
        "verify_development_panel_hashes",
        "included_panel_members",
    }
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


def test_package_marker_v5() -> None:
    assert (
        PACKAGE_MARKER_V5 == "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V5=true"
    )


def test_constants_v5_identity() -> None:
    assert HYPOTHESIS_ID == (
        "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V5"
    )
    assert EVALUATION_RUN_ID == "evaluate_bollinger_mr_midband_exit_efficiency_development_v5"
    assert CONTRACT_REL_PATH.endswith(
        "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v5.json"
    )
    assert (
        EVIDENCE_REL_PATH
        == "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v5/"
    )
    assert GOVERNANCE_REL_PATH == (
        "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V5.md"
    )
    assert BINDING_FIX_SURFACE == "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"


def test_runner_script_exists() -> None:
    script = (
        REPO
        / "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v5.py"
    )
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "run_development_evaluation" in text
    assert "EvaluationRunnerLifecycleObservabilityV1" in text
    assert "AUTO_RERUN_EXECUTED=false" in text
    assert "while True" not in text
    assert "run_slot_claim.json" in text


def test_panel_runner_falsy_zero_hygiene_lifecycle_and_claim() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v5"
        / "panel_runner_v5.py"
    )
    text = path.read_text(encoding="utf-8")
    assert 'evaluation_run_count") or -1' not in text
    assert 'evaluation_run_count", -1)' in text
    assert "run_measurement_validity_preflight" in text
    assert "_claim_run_slot_atomic_v5" in text
    assert "commit_checkpoint_v5" in text
    assert "predecessor_development_v4" in text
    claim_pos = text.find("_claim_run_slot_atomic_v5(output_dir")
    archive_pos = text.find("resolve_development_archive_root(")
    assert 0 < claim_pos < archive_pos


def test_terminal_evidence_infrastructure_failure() -> None:
    summary = _load(EVIDENCE / "summary.json")
    claim = _load(EVIDENCE / "run_slot_claim.json")
    decision = _load(EVIDENCE / "comparison_decision.json")
    checkpoint = _load(EVIDENCE / "process_lifecycle_checkpoint_v5.json")
    assert summary["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert summary["diagnostic_class"] == (
        "PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL"
    )
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_completed"] is False
    assert summary["economic_verdict"] == "NOT_EVALUATED"
    assert summary["acceptance_criteria_met"] is False
    assert summary["partial_metrics_authoritative"] is False
    assert summary["auto_rerun_executed"] is False
    assert summary["rerun_allowed"] is False
    assert summary["holdout_data_accessed"] is False
    assert summary["v4_rerun"] is False
    assert summary["baseline_members_completed"] == "3/46"
    assert summary["treatment_members_completed"] == "0/46"
    assert claim["slot_claimed"] is True
    assert claim["slot_consumed"] is True
    assert claim["evaluation_run_count_after_claim"] == 1
    assert decision["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert checkpoint["progress"]["lifecycle_state"] == "TERMINAL_COMMITTED"
    assert checkpoint["checkpoint_can_reclaim_run_slot"] is False
    assert checkpoint["partial_metrics_authoritative"] is False


def test_v4_and_v5_contracts_and_backlog() -> None:
    v4 = load_v4_repo_contract(REPO)
    v5 = load_v5_repo_contract(REPO)
    assert v4["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v4["evaluation_run_count"] == 1
    assert v4["rerun_allowed"] is False
    assert v5["result_class"] == "INFRASTRUCTURE_FAILURE"
    assert v5["evaluation_run_count"] == 1
    assert v5["evaluation_completed"] is False
    assert v5["rerun_allowed"] is False
    backlog = load_and_validate_repo_backlog(REPO)
    assert backlog["preregistered_count"] == 0
    assert backlog["development_run_count"] == 6
