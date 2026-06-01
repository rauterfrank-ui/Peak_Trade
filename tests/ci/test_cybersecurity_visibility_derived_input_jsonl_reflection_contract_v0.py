"""Static contract for Cybersecurity Visibility derived CSC-RCHAIN evidence input reflection v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests external JSONL into the repo.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
MAPPING_GUARD_TEST = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
THIS_MODULE = Path(__file__).name

DERIVED_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_DERIVED_INPUT_JSONL_REFLECTION_V0=true"
DERIVED_JSONL_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_input_jsonl_operator_intake_readonly_v0_20260601T164324Z/"
    "operator_artifacts_pending/DERIVED_LOSSLESS_RISK_CANDIDATES_FROM_CSC_RCHAIN_EVIDENCE.jsonl"
)
PRECHECK_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_jsonl_mapping_precheck_readonly_v0_20260601T165920Z"
)
BUILD_VALIDATE_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_jsonl_build_validate_v0_20260601T165743Z"
)
CHARTER_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_lossless_jsonl_replacement_charter_readonly_v0_20260601T165515Z"
)

FENCED_BLOCK_RX = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)

DERIVED_REFLECTION_EXPECTED: dict[str, str] = {
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "NO_MAPPING_WITHOUT_INPUT_ARTIFACT": "true",
    "DERIVED_LOSSLESS_ARTIFACT_FILENAME": (
        "DERIVED_LOSSLESS_RISK_CANDIDATES_FROM_CSC_RCHAIN_EVIDENCE.jsonl"
    ),
    "DERIVED_INPUT_JSONL_LINE_COUNT": "39",
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


def test_cybersecurity_visibility_derived_input_jsonl_reflection_contract_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    derived_block = _block_containing(text, DERIVED_BLOCK_ANCHOR)
    derived_values = _machine_line_values(derived_block)

    assert "Pending R-001/R-002/R-007 — derived CSC-RCHAIN evidence input reflection v0" in text
    assert DERIVED_JSONL_PATH in text
    assert PRECHECK_BUNDLE_PATH in text
    assert BUILD_VALIDATE_BUNDLE_PATH in text
    assert CHARTER_BUNDLE_PATH in text
    assert THIS_MODULE in text
    assert "does not** claim the derived file is the original lossless inventory" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text

    for key, expected in DERIVED_REFLECTION_EXPECTED.items():
        assert derived_values.get(key) == expected, (
            f"derived reflection {key}={derived_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_input_pending_table_unchanged_v0() -> None:
    rows = _risk_table_rows(_ci_audit_text())
    for pending_id in ("R-001", "R-002", "R-007"):
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()


def test_cybersecurity_visibility_derived_input_jsonl_reflection_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived CSC-RCHAIN evidence input reflection" in truth_map
    assert "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed
