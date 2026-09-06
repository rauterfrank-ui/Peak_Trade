"""Mutation-critical control-state storage owner contract v1.

Documentation and isolation guard. Not a second semantic SSOT. No
productive host binding. No DDO observation-ledger replacement.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from src.learning.mutation_critical_control_state_storage_v1.authority_v1 import (
    DDO_OBSERVATION_STORAGE_OWNER,
    DDO_OBSERVATION_STORAGE_OWNER_UNCHANGED,
    DEPENDENT_MUTATION_ALLOWED,
    NEW_CONTROL_STATE_STORAGE_OWNER_CREATED,
    NEW_CONTROL_STATE_STORAGE_OWNER_IS_EXECUTION_AUTHORITY,
    NEW_CONTROL_STATE_STORAGE_OWNER_IS_PROMOTION_AUTHORITY,
    NEW_CONTROL_STATE_STORAGE_OWNER_IS_SUPERVISOR_AUTHORITY,
    NEW_CONTROL_STATE_STORAGE_OWNER_IS_TRADING_AUTHORITY,
    PRODUCTIVE_HOST_BINDING,
    RUNTIME_AUTHORIZED,
    STORAGE_OWNER_NAME,
)
from src.learning.mutation_critical_control_state_storage_v1.medium_binding_v1 import (
    CAP64_REUSED_AS_AUTHORITY_OWNER,
    CUSTOM_WAL_NOT_CHOSEN_BECAUSE_PATTERN_EXISTS,
    DDO_O_APPEND_LEDGER_REUSED_AS_AUTHORITY_OWNER,
    HOST_CRASH_DURABILITY,
    HOST_CRASH_PROOF_ENVIRONMENT_PRESENT,
    POWER_LOSS_DURABILITY,
    POWER_LOSS_PROOF_ENVIRONMENT_PRESENT,
    REJECTED_MEDIUM,
    RESEARCH_SQLITE_REUSED_AS_AUTHORITY_OWNER,
    SQLITE_NOT_CHOSEN_BECAUSE_DURABLE,
    STORAGE_MEDIUM,
    STORAGE_MEDIUM_SELECTION_STATUS,
)
from src.learning.mutation_critical_control_state_storage_v1.records_v1 import (
    FUTURE_ONLY_STATE_CLASSES,
    IMPLEMENTED_STATE_CLASSES,
    STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
    STATE_CLASS_C_EXECUTION_ACTION_IDENTITY,
    STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
    STATE_CLASS_E_RECONCILIATION_OBLIGATION,
    STATE_CLASS_F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY,
    STATE_CLASS_G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MAP_OF_TRUTH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_V1.md"
)
ATLAS_CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
PACKAGE_ROOT = REPO_ROOT / "src/learning/mutation_critical_control_state_storage_v1"
DDO_PACKAGE = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0"
OWNER_GO = "PEAK_TRADE_OWNER_GO_DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_V1"
BOUND_SHA = "f734626f48b6999d9c02066f60133b40657c9828"
FORBIDDEN_IMPORT_NEEDLES = (
    "src.trading.master_v2",
    "src.trading.double_play",
    "double_play_composition",
    "src.risk",
    "src.safety",
    "execution_permission",
    "execution_controller",
    "reconciliation_host",
    "supervisor_host",
    "live_host",
    "promotion_controller",
    "src.learning.deterministic_decision_outcome_v0.ledger_v0",
    "src.learning.deterministic_decision_outcome_v0.capture_v0",
    "src.learning.deterministic_decision_outcome_v0.supervisor_v0",
    "sqlite3",
)


def _new_persist_section(text: str) -> str:
    start = text.index(
        "### 11.13.5 Parallel-track DDO A1 mutation-critical control-state storage owner contract persist"
    )
    end = text.index(
        "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
    )
    return text[start:end]


def test_owner_constants_isolated_from_ddo_and_trading() -> None:
    assert STORAGE_OWNER_NAME == "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER"
    assert DDO_OBSERVATION_STORAGE_OWNER == "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
    assert DDO_OBSERVATION_STORAGE_OWNER_UNCHANGED is True
    assert NEW_CONTROL_STATE_STORAGE_OWNER_CREATED is True
    assert NEW_CONTROL_STATE_STORAGE_OWNER_IS_TRADING_AUTHORITY is False
    assert NEW_CONTROL_STATE_STORAGE_OWNER_IS_EXECUTION_AUTHORITY is False
    assert NEW_CONTROL_STATE_STORAGE_OWNER_IS_SUPERVISOR_AUTHORITY is False
    assert NEW_CONTROL_STATE_STORAGE_OWNER_IS_PROMOTION_AUTHORITY is False
    assert PRODUCTIVE_HOST_BINDING is False
    assert RUNTIME_AUTHORIZED is False
    assert DEPENDENT_MUTATION_ALLOWED is False
    assert STORAGE_MEDIUM == "CUSTOM_FILE_WAL_JOURNAL_V1"
    assert STORAGE_MEDIUM_SELECTION_STATUS == "BOUND"
    assert REJECTED_MEDIUM == "SQLITE_WAL_TRANSACTIONAL_STORE"
    assert SQLITE_NOT_CHOSEN_BECAUSE_DURABLE is False
    assert CUSTOM_WAL_NOT_CHOSEN_BECAUSE_PATTERN_EXISTS is False
    assert CAP64_REUSED_AS_AUTHORITY_OWNER is False
    assert RESEARCH_SQLITE_REUSED_AS_AUTHORITY_OWNER is False
    assert DDO_O_APPEND_LEDGER_REUSED_AS_AUTHORITY_OWNER is False
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert HOST_CRASH_PROOF_ENVIRONMENT_PRESENT is False
    assert POWER_LOSS_PROOF_ENVIRONMENT_PRESENT is False
    assert IMPLEMENTED_STATE_CLASSES == {
        STATE_CLASS_B_SUPERVISOR_CONTROL_STATE,
        STATE_CLASS_C_EXECUTION_ACTION_IDENTITY,
        STATE_CLASS_D_AMBIGUOUS_MUTATION_OBLIGATION,
    }
    assert FUTURE_ONLY_STATE_CLASSES == {
        STATE_CLASS_E_RECONCILIATION_OBLIGATION,
        STATE_CLASS_F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY,
        STATE_CLASS_G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY,
    }


def _imported_modules(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_package_has_no_forbidden_productive_imports() -> None:
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = _imported_modules(tree)
        for name in imported:
            for needle in FORBIDDEN_IMPORT_NEEDLES:
                assert needle not in name, f"{path} imports {name}"
        assert "sqlite3" not in imported


def test_ddo_observation_ledger_owner_unchanged() -> None:
    ledger = (DDO_PACKAGE / "ledger_v0.py").read_text(encoding="utf-8")
    assert "class AppendOnlyDdoLedgerV0:" in ledger
    ledger_py_files = sorted(path.name for path in DDO_PACKAGE.glob("*ledger*.py"))
    assert ledger_py_files == ["ledger_v0.py"]
    sqlite_hits = list(DDO_PACKAGE.glob("*.sqlite"))
    assert sqlite_hits == []
    assert not list(PACKAGE_ROOT.glob("*.sqlite"))


def test_contract_spec_bound() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    assert SPEC_PATH.is_file()
    assert f"OWNER_GO_THIS_SLICE={OWNER_GO}" in spec
    assert f"BOUND_ORIGIN_MAIN_SHA={BOUND_SHA}" in spec
    assert "STORAGE_OWNER_NAME=MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER" in spec
    assert "STORAGE_MEDIUM=CUSTOM_FILE_WAL_JOURNAL_V1" in spec
    assert "STORAGE_MEDIUM_SELECTION_STATUS=BOUND" in spec
    assert "DDO_OBSERVATION_STORAGE_OWNER_UNCHANGED=true" in spec
    assert "NEW_CONTROL_STATE_STORAGE_OWNER_CREATED=true" in spec
    assert "NEW_CONTROL_STATE_STORAGE_OWNER_IS_TRADING_AUTHORITY=false" in spec
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in spec
    assert "POWER_LOSS_DURABILITY=UNPROVEN" in spec
    assert "CRASH_DURABILITY_FULLY_PROVEN=false" in spec
    assert "PRODUCTIVE_HOST_BINDING=false" in spec
    assert "DEPENDENT_MUTATION_ALLOWED=false" in spec
    assert "NO_PRODUCTIVE_HOST_BINDING=true" in spec
    assert "CONTROL_STATE_CLASSES_IMPLEMENTED=" in spec
    assert (
        "B_SUPERVISOR_CONTROL_STATE|C_EXECUTION_ACTION_IDENTITY|D_AMBIGUOUS_MUTATION_OBLIGATION"
        in spec
    )
    assert "FUTURE_ONLY_STATE_CLASSES=" in spec
    assert (
        "E_RECONCILIATION_OBLIGATION|F_ACTIVE_ARTIFACT_IDENTITY_FUTURE_ONLY|"
        "G_ROLLBACK_KNOWN_GOOD_IDENTITY_FUTURE_ONLY"
    ) in spec


def test_master_runbook_additive_persist() -> None:
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    section = _new_persist_section(runbook)
    assert f"OWNER_GO={OWNER_GO}" in section
    assert "NEW_STORAGE_AUTHORITY_CREATED=true" in section
    assert "DDO_OBSERVATION_STORAGE_OWNER_UNCHANGED=true" in section
    assert "STORAGE_MEDIUM=CUSTOM_FILE_WAL_JOURNAL_V1" in section
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in section
    assert "CANONICAL_LIVE_NEXT_POINTER_CHANGED=false" in section
    assert "RUNTIME_AUTHORIZED=false" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert (
        "docs&#47;ops&#47;specs&#47;DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_V1.md"
        in section
    )
    crash_proof = runbook.index(
        "### 11.13.5 Parallel-track DDO A1 crash durability proof or explicit non-provability closure persist"
    )
    new_persist = runbook.index(
        "### 11.13.5 Parallel-track DDO A1 mutation-critical control-state storage owner contract persist"
    )
    z2db = runbook.index(
        "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
    )
    assert crash_proof < new_persist < z2db


def test_map_and_atlas_remain_navigation_only() -> None:
    mot = MAP_OF_TRUTH.read_text(encoding="utf-8")
    atlas = ATLAS_CATALOG.read_text(encoding="utf-8")
    assert "DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_V1.md" in mot
    assert (
        "DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER_CONTRACT_ROLE=NAVIGATION_POINTER_ONLY"
        in mot
    )
    assert "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER" in atlas
    assert "Atlas is not trading authority" in atlas
    ddo_entity = atlas.split("id: RUNTIME_COMPONENT:ddo_ledger_v0", 1)[1][:1200]
    assert "current_canonical: true" not in ddo_entity


def test_src_diff_stays_on_authorized_prefixes() -> None:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    allowed_src_prefixes = (
        "src/learning/deterministic_decision_outcome_v0/",
        "src/learning/mutation_critical_control_state_storage_v1/",
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/",
    )
    unexpected = [
        path
        for path in changed
        if path.startswith("src/") and not path.startswith(allowed_src_prefixes)
    ]
    assert unexpected == []
