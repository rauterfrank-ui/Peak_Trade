"""Contract/unit tests for midband exit-efficiency DEVELOPMENT evaluation v4 surface.

Definition-only / pre-run safe. Must never invoke the panel runner, start a run,
claim a run slot, or access panel/holdout archives.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v4 import (
    PACKAGE_MARKER as PACKAGE_MARKER_V4,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v4.constants_v4 import (
    BINDING_FIX_SURFACE,
    CONTRACT_REL_PATH,
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v4.measurement_validity_preflight_v4 import (
    run_measurement_validity_preflight,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v3 import (
    load_and_validate_repo_contract as load_v3_repo_contract,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v4 import (
    load_and_validate_repo_contract as load_v4_repo_contract,
)

REPO = Path(__file__).resolve().parents[2]
TEST_FILE = Path(__file__).resolve()
PREFLIGHT_FILE = (
    REPO
    / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v4"
    / "measurement_validity_preflight_v4.py"
)


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


def test_preflight_module_does_not_import_panel_loaders() -> None:
    tree = ast.parse(PREFLIGHT_FILE.read_text(encoding="utf-8"))
    banned_modules = {
        "src.research.entry_effective_mr_eligibility_development_evaluation_v1.dev_panel_bars_v1",
    }
    banned_names = {
        "load_member_bars",
        "resolve_development_archive_root",
        "verify_development_panel_hashes",
        "included_panel_members",
        "run_development_evaluation",
        "run_arm",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module in banned_modules:
                raise AssertionError(f"banned_import:{node.module}")
            for alias in node.names:
                if alias.name in banned_names:
                    raise AssertionError(f"banned_import_name:{alias.name}")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in banned_modules:
                    raise AssertionError(f"banned_import:{alias.name}")


def test_package_marker_v4() -> None:
    assert (
        PACKAGE_MARKER_V4 == "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V4=true"
    )


def test_constants_v4_identity() -> None:
    assert HYPOTHESIS_ID == (
        "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V4"
    )
    assert EVALUATION_RUN_ID == "evaluate_bollinger_mr_midband_exit_efficiency_development_v4"
    assert CONTRACT_REL_PATH.endswith(
        "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v4.json"
    )
    assert (
        EVIDENCE_REL_PATH
        == "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v4/"
    )
    assert GOVERNANCE_REL_PATH == (
        "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V4.md"
    )
    assert BINDING_FIX_SURFACE == "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"


def test_runner_script_exists() -> None:
    script = (
        REPO
        / "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v4.py"
    )
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "run_development_evaluation" in text
    assert "EvaluationRunnerLifecycleObservabilityV1" in text
    assert "AUTO_RERUN_EXECUTED=false" in text
    assert "OPERATOR_GO" not in text
    assert 'os.environ.get("GO_' not in text
    assert "while True" not in text


def test_panel_runner_falsy_zero_hygiene_and_validity_gate() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v4"
        / "panel_runner_v4.py"
    )
    text = path.read_text(encoding="utf-8")
    assert 'evaluation_run_count") or -1' not in text
    assert 'evaluation_run_count", -1)' in text
    assert "run_measurement_validity_preflight" in text
    assert "BINDING_FIX_SURFACE" in text
    assert "predecessor_development_v3" in text


def test_v4_contract_still_definition_only_run_count_zero() -> None:
    report = load_v4_repo_contract(REPO)
    assert report["valid"] is True
    assert report["definition_only"] is True
    assert report["hypothesis_id"] == HYPOTHESIS_ID
    assert report["evaluation_run_count"] == 0
    assert report["preregistration_state"] == "DEFINITION_ONLY_PREREGISTERED"
    assert report["result_class"] == "NOT_EVALUATED"
    contract = _load(REPO / CONTRACT_REL_PATH)
    assert contract["preregistration_state"] == "DEFINITION_ONLY_PREREGISTERED"
    assert int(contract["evaluation_run_count"]) == 0
    assert contract["holdout_data_accessed"] is False
    assert int(contract["evaluation_run_count_authorized"]) == 1


def test_v3_remains_terminal_fail_run_count_one() -> None:
    v3_report = load_v3_repo_contract(REPO)
    assert v3_report["evaluation_run_count"] == 1
    assert v3_report["result_class"] == "FAIL"
    assert v3_report["rerun_allowed"] is False


def test_no_evaluation_evidence_or_slot_claim_in_definition_only_slice() -> None:
    evidence = REPO / EVIDENCE_REL_PATH
    assert evidence.exists() is False or not (evidence / "summary.json").exists()
    assert not (evidence / "run_slot_claim.json").exists() if evidence.exists() else True


def test_measurement_validity_preflight_passes_on_synthetic_fixture() -> None:
    result = run_measurement_validity_preflight(repo_root=REPO)
    assert result["passed"] is True
    assert result["result_class"] is None
    assert result["effective_configs_differ"] is True
    assert result["open_side_binding_observed"] is True
    assert int(result["exit_bars_observed"]) > 0
    assert result["synthetic_divergence_observed"] is True
    assert result["binding_fix_surface"] == BINDING_FIX_SURFACE


def test_governance_doc_awaiting_execution() -> None:
    governance = REPO / GOVERNANCE_REL_PATH
    assert governance.is_file()
    text = governance.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V4" in text
    assert "AWAITING_EVALUATION_EXECUTION" in text
    assert "EVALUATION_RUN_COUNT=0" in text
    assert "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX" in text
