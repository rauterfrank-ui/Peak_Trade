"""Static contract for Cybersecurity Visibility artifact-retention histogram crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
uploads artifacts, never changes retention policy, never touches runtime,
scheduler, daemon, adapter, hooks, launchctl, Notion, Market, broker/exchange,
or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.ci.cybersecurity_visibility_retained_risk_row_assertions_v0 import (
    assert_retained_r001_r002_r007_pending_or_derived_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

HISTOGRAM_CLASSIFICATION = "artifact_retention_or_evidence_gap"
HISTOGRAM_ROW_RX = re.compile(
    rf"^\| `{re.escape(HISTOGRAM_CLASSIFICATION)}` \| (\d+) \| (.+) \|$",
    re.MULTILINE,
)
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)
STATIC_OWNERS_SECTION_RX = re.compile(
    r"### Static visibility contract owners \(reuse — do not duplicate\)(.*?)(?:\n### |\Z)",
    re.DOTALL,
)

REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER = (
    "tests/ci/test_workflow_artifact_retention_visibility_contract_v0.py"
)
REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS: tuple[str, ...] = (
    "tests/ops/test_run_primary_evidence_retention_hard_gate_v0.py",
    "tests/ops/test_primary_evidence_retention_invariant_contract_v0.py",
)
RECIPROCAL_CROSSLINK_MARKER = "CYBERSECURITY_VISIBILITY_ARTIFACT_RETENTION_DURABLE_PRIMARY_EVIDENCE_RECIPROCAL_CROSSLINK_V0=true"

PE6_CYBER_ER_CROSSLINK_MARKERS: tuple[str, ...] = (
    "PE6_CYBER_ER_ARTIFACT_RETENTION_CROSSLINK_V0=true",
    "CYBER_VISIBILITY_ARTIFACTS_RETENTION_LINKED_TO_PRIMARY_EVIDENCE_V0=true",
    "ER_ARTIFACT_RETENTION_LINKED_TO_CYBER_VISIBILITY_V0=true",
    "CYBER_VISIBILITY_ARTIFACTS_DEFENSIVE_DERIVED_STATIC_ONLY=true",
    "SLICE_PE6_TESTS_ONLY=true",
)

PE6_PRIMARY_EVIDENCE_RETENTION_SEMANTICS: tuple[str, ...] = (
    "durable primary evidence",
    "/tmp`-only",
    "manifest",
    "checksum",
    "does not activate enforcement",
)

ARTIFACT_RETENTION_PARALLEL_MARKERS = (
    "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_ARTIFACT_RETENTION_OR_EVIDENCE_GAP_CROSSLINK_V0=true",
    "Cybersecurity Visibility repo-static histogram artifact retention or evidence gap",
)

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "artifact retention fixed",
    "retention policy changed",
    "evidence gap remediated",
    "runtime start authorized",
    "testnet approved",
    "live approved",
    "operator bypass",
    "ready_for_start=true",
    "preflight_blocked_lifted=true",
    "r-001 mapped",
    "r-002 mapped",
    "r-007 mapped",
)

FORBIDDEN_MACHINE_LINES: tuple[str, ...] = (
    "LOSSLESS_JSONL_RECOVERY=true",
    "R001_R002_R007_MAPPING_COMPLETED=true",
    "ARTIFACT_RETENTION_OR_EVIDENCE_GAP_MAPPING_COMPLETED=true",
)


def _ci_audit_text() -> str:
    assert CI_AUDIT_KNOWN_ISSUES.is_file()
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _histogram_section(text: str) -> str:
    start = text.find("**Interim classification histogram")
    assert start != -1, "histogram section missing"
    end = text.find("**Lossless recovery still required")
    assert end != -1, "histogram section end missing"
    return text[start:end]


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def test_cybersecurity_visibility_repo_static_histogram_artifact_retention_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_ARTIFACT_RETENTION_OR_EVIDENCE_GAP_CROSSLINK_V0=true"
        in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_ARTIFACT_RETENTION_OR_EVIDENCE_GAP_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert RECIPROCAL_CROSSLINK_MARKER in text
    assert (
        "CYBERSECURITY_VISIBILITY_ARTIFACT_RETENTION_DURABLE_PRIMARY_EVIDENCE_RECIPROCAL_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed
    assert HISTOGRAM_CLASSIFICATION in histogram

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "6"
    notes_cell = match.group(2)
    assert f"Reuse `{REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER}`" in notes_cell
    for durable_owner in REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS:
        assert f"Reuse `{durable_owner}`" in notes_cell
        assert (REPO_ROOT / durable_owner).is_file(), (
            f"missing reuse owner module: {durable_owner!r}"
        )

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    assert REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER in reuse_paths
    for durable_owner in REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS:
        assert durable_owner in reuse_paths

    owners_match = STATIC_OWNERS_SECTION_RX.search(text)
    assert owners_match is not None, "static visibility contract owners section missing"
    owners_section = owners_match.group(1)
    assert "Workflow artifact retention" in owners_section
    assert REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER in owners_section
    assert "Durable primary evidence hard gate" in owners_section
    assert "Primary evidence retention invariant" in owners_section
    for durable_owner in REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS:
        assert durable_owner in owners_section

    assert_retained_r001_r002_r007_pending_or_derived_evidence(_risk_table_rows(text))

    assert REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER in text

    lines = {line.strip() for line in text.splitlines()}
    for marker in FORBIDDEN_MACHINE_LINES:
        assert marker not in lines

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "workflow_dispatch executed" not in collapsed
    assert "mapping completed" not in collapsed
    assert "artifact_retention_or_evidence_gap mapping completed" not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_artifact_retention_crosslink_has_no_parallel_doc_surface() -> (
    None
):
    canonical = CI_AUDIT_KNOWN_ISSUES.resolve()
    parallel_docs: list[Path] = []

    for path in (REPO_ROOT / "docs").rglob("*.md"):
        if path.resolve() == canonical:
            continue
        body = path.read_text(encoding="utf-8")
        if any(marker in body for marker in ARTIFACT_RETENTION_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(REPO_ROOT))

    assert parallel_docs == []


def test_cybersecurity_visibility_artifact_retention_durable_primary_evidence_reciprocal_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    hard_gate = REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS[0]
    invariant = REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS[1]

    assert hard_gate in text
    assert invariant in text
    assert (
        "primary_evidence_retention_v0.py"
        not in text.split("Static visibility contract owners", 1)[0]
    )

    hard_gate_text = (REPO_ROOT / hard_gate).read_text(encoding="utf-8")
    invariant_text = (REPO_ROOT / invariant).read_text(encoding="utf-8")
    assert THIS_MODULE in hard_gate_text
    assert THIS_MODULE in invariant_text
    assert RECIPROCAL_CROSSLINK_MARKER in hard_gate_text
    assert RECIPROCAL_CROSSLINK_MARKER in invariant_text


def test_cybersecurity_visibility_artifact_retention_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert (
        "Cybersecurity artifact-retention durable primary evidence reciprocal crosslink v0"
        in truth_map
    )
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert "test_run_primary_evidence_retention_hard_gate_v0.py" in truth_map
    assert "test_primary_evidence_retention_invariant_contract_v0.py" in truth_map
    assert (
        RECIPROCAL_CROSSLINK_MARKER in truth_map
        or "artifact-retention durable primary evidence reciprocal crosslink" in collapsed
    )
    assert "non-authorizing" in collapsed
    assert "input_jsonl_provided=false" in collapsed or "INPUT_JSONL_PROVIDED=false" in truth_map


def test_pe6_ci_audit_documents_cyber_er_bidirectional_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    for token in PE6_CYBER_ER_CROSSLINK_MARKERS:
        assert token in text
    assert RECIPROCAL_CROSSLINK_MARKER in text
    assert "Cyber ↔ ER artifact-retention crosslink" in text
    assert "defensive/derived/static" in collapsed
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "does not activate enforcement" in collapsed


def test_pe6_reciprocal_owners_reference_primary_evidence_retention_chain_v0() -> None:
    text = _ci_audit_text()
    hard_gate_text = (REPO_ROOT / REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS[0]).read_text(
        encoding="utf-8"
    )
    invariant_text = (REPO_ROOT / REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS[1]).read_text(
        encoding="utf-8"
    )
    for owner_path in REQUIRED_DURABLE_PRIMARY_EVIDENCE_REUSE_OWNERS:
        owner_text = (REPO_ROOT / owner_path).read_text(encoding="utf-8")
        assert THIS_MODULE in owner_text
        assert RECIPROCAL_CROSSLINK_MARKER in owner_text
    assert "PE5_GAP4_GAP2A1_DEPENDENCY_GUARD_V0=true" in hard_gate_text
    assert "PE2_RUN_TYPE_GUARD_MATRIX" in hard_gate_text
    assert "artifact_retention_or_evidence_gap" in invariant_text
    for marker in PE6_CYBER_ER_CROSSLINK_MARKERS:
        assert marker in text
    histogram = _histogram_section(text)
    assert REQUIRED_ARTIFACT_RETENTION_REUSE_OWNER in histogram


def test_pe6_cyber_visibility_retention_linked_to_durable_primary_evidence_semantics_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    for phrase in PE6_PRIMARY_EVIDENCE_RETENTION_SEMANTICS:
        assert phrase.lower() in collapsed or phrase in text


def test_pe6_cyber_er_crosslink_module_is_static_no_subprocess_v0() -> None:
    import ast

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess"
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


HISTOGRAM_DEFENSIVE_CLOSURE_HEADING = "### CSC-RCHAIN histogram defensive closure v0 (SLICE-CV-3a)"
GROUPING_REFLECTION_GUARD_MODULE = "tests/ci/test_csc_rchain_v1_grouping_reflection_contract_v0.py"
CV3A_PLANNING_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/next_larger_release_candidate_after_pe_rc_core_complete_v0_20260603T031800Z/"
)
HISTOGRAM_COMPLETE_CLASSIFICATIONS: tuple[str, ...] = (
    "manual_dispatch_sensitive_surface",
    "workflow_secrets_visibility",
    "scheduler_or_runtime_boundary",
    "branch_or_environment_authority",
    "artifact_retention_or_evidence_gap",
    "paid_ai_eval_gate",
)
CV3A_CLOSURE_MARKERS: tuple[str, ...] = (
    "CSC_RCHAIN_HISTOGRAM_DEFENSIVE_CLOSURE_V0=true",
    "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STARTED=true",
    "CSC_RCHAIN_HISTOGRAM_DEFENSIVE_CLOSURE_COMPLETE=true",
    "HISTOGRAM_BUCKET_CROSSLINKS_COMPLETE=true",
    "CSC_RCHAIN_V1_003A_BLOCKED=true",
    "CSC_RCHAIN_V1_003E_BLOCKED=true",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true",
)
CV3A_FORBIDDEN_OFFENSIVE_PHRASES: tuple[str, ...] = (
    "exploit payload added",
    "offensive_automation_enabled=true",
    "penetration test automation enabled",
)


def _histogram_defensive_closure_block(text: str) -> str:
    start = text.index(HISTOGRAM_DEFENSIVE_CLOSURE_HEADING)
    end = text.index("**Lossless recovery still required", start)
    return text[start:end]


def test_cybersecurity_visibility_histogram_defensive_closure_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _histogram_defensive_closure_block(text)
    collapsed = block.lower()
    histogram = _histogram_section(text)

    for marker in CV3A_CLOSURE_MARKERS:
        assert marker in block

    assert "GO_SLICE_CV3A_CSC_RCHAIN_HISTOGRAM_DEFENSIVE_CLOSURE_V0" in block
    assert CV3A_PLANNING_BUNDLE in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert THIS_MODULE in block
    assert "INPUT_JSONL_PROVIDED=false" in block
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in block
    assert "defensive/derived/static" in collapsed or "defensive" in collapsed
    assert "non-authorizing" in collapsed

    for classification in HISTOGRAM_COMPLETE_CLASSIFICATIONS:
        assert f"`{classification}`" in block
        assert "**complete**" in block or "complete" in collapsed
        assert classification in histogram

    assert "`docs_drift_or_pointer_integrity`" in block
    assert "**deferred**" in block or "deferred" in collapsed
    assert "Review-input only" in histogram

    assert_retained_r001_r002_r007_pending_or_derived_evidence(_risk_table_rows(text))

    for phrase in CV3A_FORBIDDEN_OFFENSIVE_PHRASES:
        assert phrase not in collapsed

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    for marker in FORBIDDEN_MACHINE_LINES:
        assert marker not in {line.strip() for line in text.splitlines()}

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


CV3B_READOUT_HEADING = "### Defensive visibility readout / owner-triage guard v0 (SLICE-CV-3b)"
CV3B_BLOCK_ANCHOR = "CV3B_DEFENSIVE_VISIBILITY_READOUT_OWNER_TRIAGE_GUARD_V0=true"
DERIVED_MAPPING_PLAN_MODULE = (
    "tests/ci/test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0.py"
)
MAPPING_GUARD_MODULE = "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
INVENTORY_CHARTER_MODULE = (
    "tests/ci/test_cybersecurity_visibility_r_pending_inventory_charter_v0.py"
)


def _cv3b_readout_block(text: str) -> str:
    start = text.index(CV3B_READOUT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def test_cybersecurity_visibility_cv3b_histogram_readout_reciprocal_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _cv3b_readout_block(text)
    collapsed = block.lower()

    assert CV3B_BLOCK_ANCHOR in block
    assert THIS_MODULE in block
    assert DERIVED_MAPPING_PLAN_MODULE in block
    assert MAPPING_GUARD_MODULE in block
    assert INVENTORY_CHARTER_MODULE in block
    assert "CV3A histogram closure routing" in block
    assert "complete" in collapsed
    assert "deferred" in collapsed
    assert "CSC_RCHAIN_HISTOGRAM_DEFENSIVE_CLOSURE_COMPLETE=true" in text
    assert "INPUT_JSONL_FABRICATED=false" in block
    assert "RUNTIME_AUTHORITY_ADDED=false" in block
    assert "non-authorizing" in collapsed

    derived_text = (REPO_ROOT / DERIVED_MAPPING_PLAN_MODULE).read_text(encoding="utf-8")
    mapping_text = (REPO_ROOT / MAPPING_GUARD_MODULE).read_text(encoding="utf-8")
    assert CV3B_BLOCK_ANCHOR in derived_text or CV3B_READOUT_HEADING in derived_text
    assert CV3B_BLOCK_ANCHOR in mapping_text or CV3B_READOUT_HEADING in mapping_text


CV3C_REPORT_HEADING = "### Static defensive visibility report contract v0 (SLICE-CV-3c)"
CV3C_BLOCK_ANCHOR = "CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_V0=true"
INPUT_ARTIFACT_MODULE = (
    "tests/ci/test_cybersecurity_visibility_r_pending_input_artifact_contract_v0.py"
)


def _cv3c_report_block(text: str) -> str:
    start = text.index(CV3C_REPORT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def test_cybersecurity_visibility_cv3c_histogram_report_reciprocal_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _cv3c_report_block(text)
    collapsed = block.lower()

    assert CV3C_BLOCK_ANCHOR in block
    assert THIS_MODULE in block
    assert INPUT_ARTIFACT_MODULE in block
    assert DERIVED_MAPPING_PLAN_MODULE in block
    assert MAPPING_GUARD_MODULE in block
    assert "docs_drift_or_pointer_integrity" in collapsed
    assert "deferred" in collapsed
    assert "not falsely closed" in collapsed
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in block
    assert "complete" in collapsed
    assert "INPUT_JSONL_FABRICATED=false" in block
    assert "RUNTIME_AUTHORITY_ADDED=false" in block
    assert "non-authorizing" in collapsed

    input_text = (REPO_ROOT / INPUT_ARTIFACT_MODULE).read_text(encoding="utf-8")
    assert CV3C_BLOCK_ANCHOR in input_text or CV3C_REPORT_HEADING in input_text


CV3_POINTER_INTEGRITY_HEADING = "### Docs drift / pointer integrity crosslink guard v0 (SLICE-CV-3)"
CV3_POINTER_INTEGRITY_BLOCK_ANCHOR = (
    "SLICE_CV3_DOCS_DRIFT_POINTER_INTEGRITY_CROSSLINK_GUARD_V0=true"
)
CV3_RANKING_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/systemwide_next_safe_scope_ranking_after_market_dashboard_pr4162_crosslink_guard_merge_no_run_v1_20260612T080955Z/"
)
CV3_PREP_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_docs_drift_pointer_integrity_bounded_prep_no_run_v1_20260611T020817Z/"
)
CV3_PR15_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/csc_rchain_v1_pr15_no_safe_reaffirmation_block_stop_idle_finalization_v0_20260601T162636Z/"
)
DOCS_DRIFT_GUARD_SCRIPT = "scripts/ops/check_docs_drift_guard.py"
DOCS_TRUTH_MAP_CONFIG = "config/ops/docs_truth_map.yaml"
DOCS_DRIFT_GUARD_TEST_MODULE = "tests/ops/test_check_docs_drift_guard.py"
CV3_POINTER_INTEGRITY_EXPECTED_MACHINE_LINES: dict[str, str] = {
    "SLICE_CV3_DOCS_DRIFT_POINTER_INTEGRITY_CROSSLINK_GUARD_V0": "true",
    "SLICE_CV3_DOCS_DRIFT_POINTER_INTEGRITY_CROSSLINK_GUARD_COMPLETE": "true",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED": "true",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_COMPLETE": "false",
    "CSC_RCHAIN_PR15_FINALIZATION_PR_NECESSARY": "false",
    "CSC_RCHAIN_PR15_STOP_IDLE_NO_SAFE_REAFFIRMATION_BLOCK": "true",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "SLICE_CV3_DOCS_TESTS_ONLY": "true",
    "REUSE_DRIFT_GUARD": "REUSE_OK",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "READY_FOR_OPERATOR_ARMING": "false",
}
CV3_POINTER_INTEGRITY_FORBIDDEN_MACHINE_LINES: tuple[str, ...] = (
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_COMPLETE=true",
    "HISTOGRAM_BUCKET_CROSSLINKS_COMPLETE=false",
    "INPUT_JSONL_PROVIDED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "FINALIZATION_PR_NECESSARY=true",
)


def _cv3_pointer_integrity_block(text: str) -> str:
    start = text.index(CV3_POINTER_INTEGRITY_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if "=" not in stripped or stripped.startswith("```"):
            continue
        key, _, value = stripped.partition("=")
        values[key] = value
    return values


def test_cybersecurity_visibility_cv3_docs_drift_pointer_integrity_crosslink_v0() -> None:
    text = _ci_audit_text()
    block = _cv3_pointer_integrity_block(text)
    collapsed = block.lower()
    machine_values = _machine_line_values(block)

    assert CV3_POINTER_INTEGRITY_BLOCK_ANCHOR in block
    assert (
        "GO_CYBERSECURITY_VISIBILITY_SLICE_CV3_CSC_RCHAIN_PR15_OR_DOCS_DRIFT_POINTER_INTEGRITY_DOCS_TESTS_NO_RUN_V1"
        in block
    )
    assert CV3_RANKING_BUNDLE in block
    assert CV3_PREP_BUNDLE in block
    assert CV3_PR15_CLOSEOUT_BUNDLE in block
    assert THIS_MODULE in block
    assert DOCS_DRIFT_GUARD_TEST_MODULE in block
    assert DOCS_DRIFT_GUARD_SCRIPT in block
    assert DOCS_TRUTH_MAP_CONFIG in block
    assert GROUPING_REFLECTION_GUARD_MODULE in block
    assert "`docs_drift_or_pointer_integrity`" in block
    assert "deferred" in collapsed
    assert "not falsely closed" in collapsed
    assert "stop_idle" in collapsed
    assert "non-authorizing" in collapsed

    for key, expected in CV3_POINTER_INTEGRITY_EXPECTED_MACHINE_LINES.items():
        assert machine_values.get(key) == expected, (
            f"SLICE-CV-3 {key}={machine_values.get(key)!r} expected {expected!r}"
        )

    closure_lines = {line.strip() for line in block.splitlines()}
    for marker in CV3_POINTER_INTEGRITY_FORBIDDEN_MACHINE_LINES:
        assert marker not in closure_lines

    assert (REPO_ROOT / DOCS_DRIFT_GUARD_SCRIPT).is_file()
    assert (REPO_ROOT / DOCS_TRUTH_MAP_CONFIG).is_file()
    assert (REPO_ROOT / DOCS_DRIFT_GUARD_TEST_MODULE).is_file()

    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "SLICE-CV-3" in truth_map
    assert "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED=true" in truth_map
    assert (
        DOCS_DRIFT_GUARD_SCRIPT.replace("/", "&#47;") in truth_map
        or DOCS_DRIFT_GUARD_SCRIPT in truth_map
    )

    drift_test_text = (REPO_ROOT / DOCS_DRIFT_GUARD_TEST_MODULE).read_text(encoding="utf-8")
    assert (
        CV3_POINTER_INTEGRITY_HEADING in drift_test_text
        or CV3_POINTER_INTEGRITY_BLOCK_ANCHOR in drift_test_text
    )
