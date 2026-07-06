"""Contract tests for ratified final fleet offline economic evaluation execution v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
)
from src.research.ratified_final_fleet_offline_economic_evaluation_execution_v0 import (
    BINDING_COMPLETION_REL,
    CONFIRM_GO,
    EVIDENCE_CLASS_ID,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXECUTION_SCOPE_REL,
    GOVERNANCE_REL,
    PROCESS_CLASSIFICATION,
    RATIFICATION_REL,
    RATIFIED_SCOPE_FILES,
    REUSABLE_OWNERS,
    SCOPE_CLASSIFICATION,
    verify_preconditions_v0,
    verify_pr4917_ratification_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_go_token_and_scope_classification() -> None:
    assert CONFIRM_GO == "GO_EXECUTE_RATIFIED_FINAL_FLEET_VERSIONED_OFFLINE_ECONOMIC_EVALUATION_V0"
    assert PROCESS_CLASSIFICATION == (
        "RATIFIED_FINAL_FLEET_VERSIONED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
    )
    assert SCOPE_CLASSIFICATION == PROCESS_CLASSIFICATION
    assert EVIDENCE_CLASS_ID == PROCESS_CLASSIFICATION
    assert EXPECTED_ORIGIN_MAIN_SHA == "400b6e9d8cbbf1ade46f36e8fda797808b6db47a"


def test_no_runtime_authority_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"
    assert ORDER_EFFECT == "NONE"


def test_execution_scope_config_authorizes_offline_only() -> None:
    payload = json.loads((REPO_ROOT / EXECUTION_SCOPE_REL).read_text(encoding="utf-8"))
    assert payload["execution_go_token"] == CONFIRM_GO
    assert payload["economic_evaluation_authorized"] is True
    assert payload["runtime_rewire_admissible"] is False
    assert payload["parent_ratification_pr"] == 4917
    assert payload["execution_performed"] is False


def test_pr4917_ratification_and_required_configs_exist() -> None:
    for rel in (
        *RATIFIED_SCOPE_FILES,
        RATIFICATION_REL,
        EXECUTION_SCOPE_REL,
        BINDING_COMPLETION_REL,
    ):
        assert (REPO_ROOT / rel).is_file(), rel
    assert (REPO_ROOT / GOVERNANCE_REL).is_file()
    ratification = json.loads((REPO_ROOT / RATIFICATION_REL).read_text(encoding="utf-8"))
    ok, reasons = verify_pr4917_ratification_v0(ratification)
    assert ok, reasons


def test_reusable_owner_inventory_paths_exist() -> None:
    for rel in REUSABLE_OWNERS:
        assert (REPO_ROOT / rel).is_file(), rel


def test_runner_script_exists() -> None:
    runner = (
        REPO_ROOT
        / "scripts/research/execute_ratified_final_fleet_offline_economic_evaluation_v0.py"
    )
    assert runner.is_file()


def test_preconditions_fail_closed_on_invalid_go_token() -> None:
    ok, reasons = verify_preconditions_v0(
        repo_root=REPO_ROOT,
        confirm="GO_INVALID",
        require_clean_worktree=False,
    )
    assert not ok
    assert any("GO_TOKEN" in reason for reason in reasons)
