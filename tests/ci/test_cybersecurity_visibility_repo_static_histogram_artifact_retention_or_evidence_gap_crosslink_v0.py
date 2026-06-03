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
    "INPUT_JSONL_PROVIDED=true",
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
