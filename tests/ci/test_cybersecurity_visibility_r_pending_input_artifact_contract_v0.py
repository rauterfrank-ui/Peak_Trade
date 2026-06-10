"""Static contract for Cybersecurity Visibility pending R-001/R-002/R-007 input artifact v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests operator artifacts,
never dispatches workflows, and never touches runtime, hooks, Notion, or Market paths.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CHARTER_TEST = "test_cybersecurity_visibility_r_pending_inventory_charter_v0.py"
DERIVED_MAPPING_MODULE = (
    "tests/ci/test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0.py"
)
MAPPING_GUARD_MODULE = "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
ARTIFACT_RETENTION_MODULE = (
    "tests/ci/test_cybersecurity_visibility_repo_static_histogram_"
    "artifact_retention_or_evidence_gap_crosslink_v0.py"
)
THIS_MODULE = Path(__file__).name

CV3C_REPORT_HEADING = "### Static defensive visibility report contract v0 (SLICE-CV-3c)"
CV3C_BLOCK_ANCHOR = "CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_V0=true"
CV3C_PLANNING_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cv3_next_slice_decision_after_cv3b_v0_20260603T032809Z/"
)
CV3B_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_cv3b_defensive_visibility_readout_owner_triage_guard_merge_closeout_v0_20260603T032809Z/"
)
CV3C_EXPECTED_MACHINE_LINES: dict[str, str] = {
    "CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_V0": "true",
    "CYBERSECURITY_DEFENSIVE_VISIBILITY_CV3_PLUS_RC_V0_STARTED": "true",
    "CV3A_COMPLETE": "true",
    "CV3B_COMPLETE": "true",
    "CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_COMPLETE": "true",
    "DEFENSIVE_CYBER_ONLY": "true",
    "STATIC_DERIVED_VISIBILITY_ONLY": "true",
    "DEFINITIVE_CYBER_MAPPING_PERFORMED": "false",
    "INPUT_JSONL_REQUIRED": "false",
    "INPUT_JSONL_FABRICATED": "false",
    "INPUT_JSONL_PROVIDED": "false",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_DEFERRED": "true",
    "RUNTIME_AUTHORITY_ADDED": "false",
    "SECRET_SCANNING_REAL_SECRETS": "false",
    "REUSE_DRIFT_GUARD": "REUSE_OK",
    "NO_PARALLEL_DOCS": "true",
    "NO_PARALLEL_BUILDS": "true",
    "PREFLIGHT_REMAINS_BLOCKED": "true",
    "READY_FOR_OPERATOR_ARMING": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "LIVE_TOUCHED": "false",
    "ENFORCEMENT_ACTIVATED": "false",
    "EXPLOIT_CODE_ADDED": "false",
    "OFFENSIVE_AUTOMATION_ADDED": "false",
    "SLICE_CV3C_TESTS_ONLY": "true",
}
CV3C_FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "definitive mapping completed",
    "input_jsonl fabricated",
    "offensive_automation_enabled=true",
    "runtime authority granted",
    "secret scanning authorized",
)
CV3C_FORBIDDEN_MACHINE_TRUE_LINES: tuple[str, ...] = (
    "INPUT_JSONL_PROVIDED=true",
    "INPUT_JSONL_FABRICATED=true",
    "READY_FOR_OPERATOR_ARMING=true",
    "RUNTIME_AUTHORITY_ADDED=true",
    "ENFORCEMENT_ACTIVATED=true",
    "EXPLOIT_CODE_ADDED=true",
    "OFFENSIVE_AUTOMATION_ADDED=true",
    "DOCS_DRIFT_OR_POINTER_INTEGRITY_COMPLETE=true",
)


def _machine_line_values(block: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Z0-9_]+)=(.+)$", line.strip())
        if match:
            values[match.group(1)] = match.group(2)
    return values


def _cv3c_report_block(text: str) -> str:
    start = text.index(CV3C_REPORT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def _release_rc_index_section(text: str) -> str:
    start = text.index("**Planned slice decomposition (reference — not authorized until merged):**")
    end = text.index("**Operational rules:**", start)
    return text[start:end]


def test_cybersecurity_visibility_r_pending_input_artifact_contract_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert "Pending R-001/R-002/R-007 — input artifact contract v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_V0=true" in text
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=false" in text
    assert "INPUT_JSONL_REQUIRED=true" in text
    assert (
        "ACCEPTED_INPUT_ARTIFACTS=FULL_LOSSLESS_RISK_CANDIDATES.jsonl,"
        "APPROVED_OPERATOR_TRIAGE_ARTIFACT" in text
    )
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=false" in text
    assert "INPUT_JSONL_PROVIDED=true" in text
    assert "INPUT_JSONL=<absolute path" in text
    assert "no-mapping-without-input" in collapsed or "NO_MAPPING_WITHOUT_INPUT_ARTIFACT" in text

    assert "This contract **does not** ingest files" in text
    assert "**does not** set `LOSSLESS_JSONL_RECOVERY=true`" in text

    for risk_id in ("R-001", "R-002", "R-007"):
        assert risk_id in text
        assert "mapped" in collapsed

    assert "R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text

    assert "Forbidden as mapping input" in text
    assert "repo-static successor" in collapsed
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_r_pending_input_artifact_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "Cybersecurity Visibility R pending input artifact contract v0" in truth_map
    assert "INPUT_JSONL_REQUIRED=true" in truth_map
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true" in truth_map
    assert THIS_MODULE in truth_map
    assert CHARTER_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_cv3c_static_defensive_visibility_report_contract_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    block = _cv3c_report_block(text)
    collapsed = block.lower()
    machine_values = _machine_line_values(block)

    assert "GO_SLICE_CV3C_STATIC_DEFENSIVE_VISIBILITY_REPORT_CONTRACT_V0" in block
    assert CV3C_PLANNING_BUNDLE in block
    assert CV3B_CLOSEOUT_BUNDLE in block
    assert f"tests/ci/{THIS_MODULE}" in block
    assert DERIVED_MAPPING_MODULE in block
    assert MAPPING_GUARD_MODULE in block
    assert ARTIFACT_RETENTION_MODULE in block
    assert "static/derived/read-only only" in collapsed
    assert "input-artifact contract only" in collapsed
    assert "docs_drift_or_pointer_integrity" in collapsed
    assert "deferred" in collapsed
    assert "not falsely closed" in collapsed
    assert "Static visibility contract owners" in block
    assert "non-authorizing" in collapsed

    for owner in (
        f"tests/ci/{THIS_MODULE}",
        DERIVED_MAPPING_MODULE,
        MAPPING_GUARD_MODULE,
        ARTIFACT_RETENTION_MODULE,
    ):
        assert (REPO_ROOT / owner).is_file(), f"missing CV3C guard owner: {owner!r}"

    for key, expected in CV3C_EXPECTED_MACHINE_LINES.items():
        assert machine_values.get(key) == expected, (
            f"CV3C report {key}={machine_values.get(key)!r} expected {expected!r}"
        )

    report_lines = {line.strip() for line in block.splitlines()}
    for marker in CV3C_FORBIDDEN_MACHINE_TRUE_LINES:
        assert marker not in report_lines

    for phrase in CV3C_FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "exploit/offensive automation" in collapsed
    assert "secret scanning against real secrets" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_cv3c_input_artifact_report_reciprocal_crosslink_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    block = _cv3c_report_block(text)
    release_section = _release_rc_index_section(text)
    input_section_start = text.index("### Pending R-001/R-002/R-007 — input artifact contract v0")
    input_section_end = text.index(
        "### Pending R-001/R-002/R-007 — mapping guard v0", input_section_start
    )
    input_section = text[input_section_start:input_section_end]

    assert "SLICE-CV-3c" in release_section
    assert CV3C_BLOCK_ANCHOR in block
    assert CV3C_BLOCK_ANCHOR in input_section or THIS_MODULE in block
    assert "This contract **does not** ingest files" in input_section
    assert "INPUT_JSONL_PROVIDED=true" in input_section
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=false" in input_section
    assert "Forbidden as mapping input" in input_section

    derived_text = (REPO_ROOT / DERIVED_MAPPING_MODULE).read_text(encoding="utf-8")
    mapping_text = (REPO_ROOT / MAPPING_GUARD_MODULE).read_text(encoding="utf-8")
    retention_text = (REPO_ROOT / ARTIFACT_RETENTION_MODULE).read_text(encoding="utf-8")
    assert CV3C_BLOCK_ANCHOR in derived_text or CV3C_REPORT_HEADING in derived_text
    assert CV3C_BLOCK_ANCHOR in mapping_text or CV3C_REPORT_HEADING in mapping_text
    assert CV3C_BLOCK_ANCHOR in retention_text or CV3C_REPORT_HEADING in retention_text

    static_owners_start = text.index(
        "### Static visibility contract owners (reuse — do not duplicate)"
    )
    static_owners_end = text.index("## Remote Runtime Contract", static_owners_start)
    static_owners = text[static_owners_start:static_owners_end]
    assert THIS_MODULE in static_owners
    assert "Static defensive visibility report contract" in static_owners
