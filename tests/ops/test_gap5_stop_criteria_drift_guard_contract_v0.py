"""Static contract for Gap-5 stop-criteria drift guard v0.

Reads repo markdown/TOML/source only. Never executes stop/scheduler/runtime, never reads
external archive paths as pass/fail SSOT, and never treats external F5 approval or planning
charters as repo Gap-5 rehearsal execution or proof acceptance.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef,import-not-found]

ROOT = Path(__file__).resolve().parents[2]
SECTION5_DOC = (
    ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
PREFLIGHT_CONTRACT = (
    ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)
PREFLIGHT_TOML = ROOT / "config" / "ops" / "paper_shadow_247_preflight.toml"
GAP5_TESTS = ROOT / "tests" / "ops" / "test_gap5_stop_criteria_contract_v0.py"
HARDENING_OWNER = ROOT / "tests" / "ops" / "test_scheduler_dry_run_hardening_source_contract_v0.py"
FINAL_MACHINE_LINES_HEADER = "## Final Machine Lines"
GAP5_SECTION_HEADER = "## Gap 5 Stop Criteria Contract v0"
GAP5_GOVERNED_REFLECTION_HEADER = "## Gap 5 Governed Stop Proof Acceptance Reflection v0"
GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER = (
    "## Gap 5 Governed Stop Proof Accepted Final-Line Reflection v0"
)
_MARKER_TRUE = "=true"

# External planning posture only — must not appear as verified/rehearsed/proof in repo SSOT.
GAP5_STOP_CRITERIA_PLANNED = True
GAP5_STOP_CRITERIA_VERIFIED = False
F5_APPROVAL_IS_PROCEDURE_TEXT_ONLY = True
FUTURE_REHEARSAL_REQUIRES_OPERATOR_GO_AND_RUN_ID = True
EVIDENCE_EQUALS_APPROVAL = False
CRITERIA_COMPLETE_EQUALS_GAP_CLOSED = False

DRIFT_GUARD_REQUIRED_FINAL_LINES = (
    "PREFLIGHT_REMAINS_BLOCKED=true",
    "READY_FOR_OPERATOR_ARMING=false",
    "PATH_B_LIFT_DISCUSSION_READY=false",
    "ALL_GAPS_CLOSED=false",
    "GAP5_STOP_REHEARSAL_EXECUTED=false",
    "GAP5_STOP_PROOF_ACCEPTED=true",
    "GAP5_TYPE2_WAIVER_GRANTED=false",
    "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=false",
)

DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS = (
    "GAP5_STOP_REHEARSAL_EXECUTED=true",
    "GAP5_TYPE2_WAIVER_GRANTED=true",
    "GAP5_RUNTIME_STOP_AUTHORITY_CHANGED=true",
    "GAP5_SCHEDULER_EXECUTION_AUTHORIZED=true",
    "GAP5_STOP_CRITERIA_DEFAULT_ON=true",
    "GAP5_STOP_CRITERIA_VERIFIED=true",
    "F5_EXACT_PROCEDURE_APPROVED=true",
    "WORKSHEET_COMPLETE=true",
    "PATH_B_LIFT_DISCUSSION_READY=true",
    "ALL_GAPS_CLOSED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "PREFLIGHT_REMAINS_BLOCKED=false",
    "GAP6_DRY_RUN_PROOF_ACCEPTED=true",
)

PREFLIGHT_AUTHORIZATION_KEYS = (
    "activation_authorized",
    "daemon_activation_authorized",
    "scheduler_execution_authorized",
    "paper_runtime_authorized",
    "shadow_runtime_authorized",
    "testnet_authorized",
    "live_authorized",
    "broker_authorized",
    "exchange_authorized",
    "order_submission_authorized",
)


def _final_machine_lines(text: str) -> str:
    return text.split(FINAL_MACHINE_LINES_HEADER, 1)[1]


def _gap5_section(text: str) -> str:
    return text.split(GAP5_SECTION_HEADER, 1)[1].split("## Gap 2 Canonical Job Set Contract v0", 1)[
        0
    ]


def _gap5_governed_reflection_section(text: str) -> str:
    return text.split(GAP5_GOVERNED_REFLECTION_HEADER, 1)[1].split(
        GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1
    )[0]


def _gap5_accepted_final_line_reflection_section(text: str) -> str:
    return text.split(GAP5_ACCEPTED_FINAL_LINE_REFLECTION_HEADER, 1)[1].split(
        "## Gap 6 Governed Dry-Run Proof Acceptance Reflection v0", 1
    )[0]


def _section5_text() -> str:
    return SECTION5_DOC.read_text(encoding="utf-8")


def _preflight_payload() -> dict:
    return tomllib.loads(PREFLIGHT_TOML.read_text(encoding="utf-8"))


def test_gap5_stop_criteria_drift_guard_external_planning_constants_v0() -> None:
    assert GAP5_STOP_CRITERIA_PLANNED is True
    assert GAP5_STOP_CRITERIA_VERIFIED is False
    assert F5_APPROVAL_IS_PROCEDURE_TEXT_ONLY is True
    assert FUTURE_REHEARSAL_REQUIRES_OPERATOR_GO_AND_RUN_ID is True
    assert EVIDENCE_EQUALS_APPROVAL is False
    assert CRITERIA_COMPLETE_EQUALS_GAP_CLOSED is False


def test_gap5_stop_criteria_drift_guard_final_machine_lines_remain_blocked_v0() -> None:
    block = _final_machine_lines(_section5_text())
    for marker in DRIFT_GUARD_REQUIRED_FINAL_LINES:
        assert marker in block


def test_gap5_stop_criteria_drift_guard_forbids_lift_and_verified_tokens_v0() -> None:
    block = _final_machine_lines(_section5_text())
    lines = {line.strip() for line in block.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS:
        assert token not in lines


def test_gap5_stop_criteria_drift_guard_repo_ssot_forbids_f5_and_verified_tokens_v0() -> None:
    text = _section5_text()
    assert "F5_EXACT_PROCEDURE_APPROVED=true" not in text
    assert "GAP5_STOP_CRITERIA_VERIFIED=true" not in text
    assert "WORKSHEET_COMPLETE=true" not in text


def test_gap5_stop_criteria_drift_guard_gap5_section_preserves_criteria_only_v0() -> None:
    section = _gap5_section(_section5_text())
    assert "GAP5_STOP_CRITERIA_CONTRACT_V0=true" in section
    assert "GAP5_CRITERIA_ONLY=true" in section
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in section
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in section
    assert "GAP5_TYPE2_WAIVER_GRANTED=false" in section
    assert "does not execute or claim a stop-tool rehearsal" in section
    assert "does not accept or verify stop proof" in section
    assert "does not execute stop tools" in section
    lines = {line.strip() for line in section.splitlines()}
    for token in DRIFT_GUARD_FORBIDDEN_GAP5_REPO_TOKENS:
        assert token not in lines


def test_gap5_stop_criteria_drift_guard_f5_approval_not_rehearsal_or_proof_v0() -> None:
    text = _section5_text()
    block = _final_machine_lines(text)
    assert "F5_EXACT_PROCEDURE_APPROVED=true" not in text
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in block
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block


def test_gap5_accepted_final_line_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap5_accepted_final_line_reflection_section(text)
    acceptance = _gap5_governed_reflection_section(text)
    criteria = _gap5_section(text)
    block = _final_machine_lines(text)

    assert "GAP5_STOP_PROOF_ACCEPTED_FINAL_LINE_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in reflection
    assert "ACCEPTED_MODE=READ_ONLY_SNAPSHOT_FINAL_LINE_ACCEPTED" in reflection
    assert "GOVERNED_ACCEPTANCE_BASIS=GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "EXTERNAL_ACCEPTANCE_RECORD_POINTER=" in reflection
    assert (
        "gap5_stop_rehearsal_read_only_snapshot_proof_accepted_external_v0_20260531T194049Z"
        in reflection
    )
    assert "INPUT_STRATEGY_POINTER=" in reflection
    assert "section5_remaining_gaps_closure_strategy_no_lift_v0_20260603T160500Z" in reflection
    assert "INPUT_GAP7_CLOSEOUT_POINTER=" in reflection
    assert (
        "pr3966_gap7_risk_boundary_final_line_reflection_post_merge_closeout_v0_20260603T161613Z"
        in reflection
    )
    assert (
        "OPERATOR_GO=GO_GAP5_STOP_PROOF_ACCEPTED_FINAL_LINE_REPO_REFLECTION_DOCS_TESTS_V0"
        in reflection
    )
    assert "NO_RUNTIME_AUTHORITY=true" in reflection
    assert "does not claim stop-tool rehearsal was executed" in reflection
    assert "does not modify Gap-5 criteria block acceptance posture" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not set `ALL_GAPS_CLOSED=true`" in reflection
    assert "does not lift preflight" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in acceptance
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in criteria
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
    assert "ALL_GAPS_CLOSED=false" in block
    assert "READY_FOR_OPERATOR_ARMING=false" in block
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in block
    reflection_lines = {line.strip() for line in reflection.splitlines()}
    criteria_lines = {line.strip() for line in criteria.splitlines()}
    block_lines = {line.strip() for line in block.splitlines()}
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection_lines
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block_lines
    assert "GAP5_STOP_PROOF_ACCEPTED=true" not in criteria_lines
    assert "GAP5_STOP_PROOF_ACCEPTED=false" not in block_lines


def test_gap5_stop_criteria_drift_guard_preflight_contract_remains_blocked_v0() -> None:
    text = PREFLIGHT_CONTRACT.read_text(encoding="utf-8")
    assert "Current status: **BLOCKED**." in text
    assert "Evidence ≠ approval" in text


def test_gap5_stop_criteria_drift_guard_preflight_toml_stop_commands_inventory_only_v0() -> None:
    payload = _preflight_payload()
    assert payload["stop_command"] == (
        "uv run python scripts/ops/report_paper_shadow_247_preflight_status.py --json"
    )
    assert payload["emergency_stop_command"] == (
        "uv run python scripts/ops/snapshot_operator_stop_signals.py --json"
    )
    for key in PREFLIGHT_AUTHORIZATION_KEYS:
        assert payload[key] is False, key


def test_gap5_stop_criteria_drift_guard_gap4_gap6_tokens_untouched_v0() -> None:
    block = _final_machine_lines(_section5_text())
    assert "GAP4_OUTPUT_EVIDENCE_PATHS_VERIFIED=true" in block
    assert "GAP6_DRY_RUN_PROOF_ACCEPTED=false" in block
    assert "GAP6_DRY_RUN_RC0_OBSERVED=false" in block
    assert "GAP6_DRY_RUN_PROOF_VERIFIED=false" in block


def test_gap5_stop_criteria_drift_guard_criteria_complete_does_not_close_gaps_v0() -> None:
    text = _section5_text()
    assert "SECTION5_OWNER_MAP_CONTRACT_V0_COMPLETE=true" in text
    assert "ALL_GAPS_CLOSED=false" in text
    assert "GAP5_CRITERIA_ONLY=true" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in _gap5_section(text)
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in _final_machine_lines(text)


def test_gap5_stop_criteria_drift_guard_evidence_not_approval_language_v0() -> None:
    section = _gap5_section(_section5_text())
    assert "criteria-only" in section
    assert "not rehearsal-executed" in section
    assert "not proof-accepted" in section
    assert "does not treat any archive or prior stop rehearsal as proof accepted" in section


def test_gap5_stop_criteria_drift_guard_module_is_static_parse_only_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


def test_gap5_stop_criteria_drift_guard_owner_crosslinks_gap5_criteria_tests_v0() -> None:
    assert GAP5_TESTS.is_file()
    text = GAP5_TESTS.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_drift_guard_contract_v0.py" in text


def test_gap5_stop_criteria_drift_guard_owner_crosslinks_hardening_source_contract_v0() -> None:
    assert HARDENING_OWNER.is_file()
    text = HARDENING_OWNER.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_drift_guard_contract_v0.py" in text
    lines = {line.strip() for line in text.splitlines()}
    assert ("GAP5_STOP_REHEARSAL_EXECUTED" + _MARKER_TRUE) not in lines
    assert ("GAP5_STOP_PROOF_ACCEPTED" + _MARKER_TRUE) not in lines


def test_gap5_stop_criteria_drift_guard_owner_crosslinks_gap5_gap4_dependency_v0() -> None:
    dependency = (
        ROOT / "tests" / "ops" / "test_gap5_gap4_durable_evidence_dependency_contract_v0.py"
    )
    assert dependency.is_file()
    text = dependency.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_drift_guard_contract_v0.py" in text
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in text


def test_gap5_stop_criteria_drift_guard_owner_crosslinks_rehearsal_classification_v0() -> None:
    classification = (
        ROOT / "tests" / "ops" / "test_gap5_stop_rehearsal_evidence_classification_contract_v0.py"
    )
    assert classification.is_file()
    text = classification.read_text(encoding="utf-8")
    assert "test_gap5_stop_criteria_drift_guard_contract_v0.py" in text
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in text


def test_gap5_stop_criteria_drift_guard_governed_reflection_scoped_acceptance_v0() -> None:
    text = _section5_text()
    reflection = _gap5_governed_reflection_section(text)
    block = _final_machine_lines(text)
    criteria = _gap5_section(text)

    assert "GAP5_STOP_PROOF_GOVERNED_REFLECTION_V0=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in reflection
    assert "GAP5_STOP_REHEARSAL_EXECUTED=false" in reflection
    assert "ACCEPTED_MODE=READ_ONLY_SNAPSHOT" in reflection
    assert "NO_REPO_FLAG_LIFT_FROM_EXTERNAL_ACCEPTANCE=true" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED_EXTERNAL=true" not in text
    assert "does not verify Gap-4 output evidence paths" in reflection
    assert "does not enable operator arming" in reflection
    assert "does not start or authorize Runtime, Paper, Shadow, Testnet, or Live" in reflection
    assert "Evidence acceptance is not runtime authorization" in reflection
    assert "GAP5_STOP_PROOF_ACCEPTED=false" in criteria
    assert "GAP5_STOP_PROOF_ACCEPTED=true" in block
    assert "GAP7_RISK_BOUNDARY_VERIFIED=true" in block
