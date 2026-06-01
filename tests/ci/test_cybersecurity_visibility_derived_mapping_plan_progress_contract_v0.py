"""Static contract for Cybersecurity Visibility derived mapping plan progress v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Plan progress only — no mapping execution.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
DERIVED_REFLECTION_TEST = (
    "test_cybersecurity_visibility_derived_input_jsonl_reflection_contract_v0.py"
)
MAPPING_GUARD_TEST = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
THIS_MODULE = Path(__file__).name

PLAN_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_DERIVED_MAPPING_PLAN_PROGRESS_V0=true"
CONTRACT_EXTENSION_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_CONTRACT_EXTENSION_V0=true"
)
CHARTER_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_contract_extension_charter_readonly_v0_20260601T171650Z"
)
PRECHECK_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_definitive_mapping_readiness_precheck_readonly_v0_20260601T171452Z"
)
PLAN_PROGRESS_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_cyber_mapping_plan_progress_pr_merge_closeout_readonly_v0_20260601T171301Z"
)
PLANNING_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_mapping_after_derived_reflection_next_progress_readonly_v0_20260601T170753Z"
)
POST_MERGE_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_derived_input_artifact_repo_reflection_pr_merge_closeout_readonly_v0_20260601T170502Z"
)
PRECHECK_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_jsonl_mapping_precheck_readonly_v0_20260601T165920Z"
)

FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)

PLAN_PROGRESS_EXPECTED: dict[str, str] = {
    "DERIVED_MAPPING_PLAN_PROGRESS_ONLY": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT": "true",
    "DERIVED_CANDIDATE_ID_FAMILY_ONLY": "true",
}

PLAN_DERIVED_IDS = (
    "DERIVED-CYBER-R-001-001",
    "DERIVED-CYBER-R-002-001",
    "DERIVED-CYBER-R-007-001",
)

CONTRACT_EXTENSION_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_CONTRACT_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT": "true",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
    "DERIVED_CANDIDATE_ID_FAMILY_ONLY": "true",
}


def _ci_audit_text() -> str:
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _block_containing(text: str, anchor: str) -> str:
    start = text.find(anchor)
    assert start != -1, f"missing anchor {anchor}"
    fence_start = text.rfind("```", 0, start)
    fence_end = text.find("```", start)
    assert fence_start != -1 and fence_end != -1, f"missing fenced block for {anchor}"
    return text[fence_start : fence_end + 3]


def _machine_line_values(block: str) -> dict[str, str]:
    inner = FENCED_BLOCK_RX.search(block)
    assert inner, "fenced block must have inner content"
    values: dict[str, str] = {}
    for line in inner.group(1).splitlines():
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("|"):
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    section_start = text.find("### Retained cybersecurity risks R-001 through R-007")
    assert section_start != -1
    section = text[section_start : section_start + 4000]
    return {
        match.group(1): (match.group(2).strip(), match.group(3).strip())
        for match in RISK_TABLE_ROW_RX.finditer(section)
    }


def test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    plan_block = _block_containing(text, PLAN_BLOCK_ANCHOR)
    plan_values = _machine_line_values(plan_block)

    assert "Pending R-001/R-002/R-007 — derived mapping plan progress v0" in text
    assert PLANNING_BUNDLE_PATH in text
    assert POST_MERGE_CLOSEOUT_PATH in text
    assert PRECHECK_BUNDLE_PATH in text
    assert THIS_MODULE in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_PR" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text

    for derived_id in PLAN_DERIVED_IDS:
        assert derived_id in text

    for key, expected in PLAN_PROGRESS_EXPECTED.items():
        assert plan_values.get(key) == expected, (
            f"plan progress {key}={plan_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_mapping_plan_pending_table_unchanged_v0() -> None:
    rows = _risk_table_rows(_ci_audit_text())
    for pending_id in ("R-001", "R-002", "R-007"):
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()


def test_cybersecurity_visibility_derived_mapping_plan_progress_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived mapping plan progress" in truth_map
    assert "DERIVED_MAPPING_PLAN_PROGRESS_ONLY=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_contract_extension_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    extension_block = _block_containing(text, CONTRACT_EXTENSION_BLOCK_ANCHOR)
    extension_values = _machine_line_values(extension_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping contract extension v0" in text
    assert CHARTER_BUNDLE_PATH in text
    assert PRECHECK_BUNDLE_PATH in text
    assert PLAN_PROGRESS_CLOSEOUT_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text

    for key, expected in CONTRACT_EXTENSION_EXPECTED.items():
        assert extension_values.get(key) == expected, (
            f"contract extension {key}={extension_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_contract_extension_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping contract extension" in truth_map
    assert "DERIVED_ONLY_MAPPING_CONTRACT_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed
