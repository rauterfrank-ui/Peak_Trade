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
DECISION_RECORD_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_DECISION_RECORD_V0=true"
)
EXECUTION_CHARTER_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_EXECUTION_CHARTER_V0=true"
)
EXECUTION_GO_RECORD_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORD_V0=true"
)
GUARD_EXTENSION_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_GUARD_EXTENSION_V0=true"
)
WAVE1_CHARTER_BLOCK_ANCHOR = "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_WAVE1_CHARTER_V0=true"
WAVE1_EXECUTION_GUARD_PREP_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_WAVE1_EXECUTION_GUARD_PREP_V0=true"
)
WAVE1_BATCH_CLOSURE_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0=true"
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
READINESS_REFRESH_BUNDLE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_readiness_refresh_readonly_v0_20260601T172844Z"
)
PR3888_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_pr3888_derived_only_mapping_contract_extension_merge_closeout_readonly_v0_20260601T172611Z"
)
EXECUTION_CHARTER_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_execution_charter_precheck_readonly_v0_20260601T173815Z"
)
PR3889_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_decision_record_pr_merge_closeout_readonly_v0_20260601T173555Z"
)
EXECUTION_GO_READINESS_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_execution_go_readiness_precheck_readonly_v0_20260601T174752Z"
)
PR3890_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_execution_charter_pr_merge_closeout_readonly_v0_20260601T174422Z"
)
PR3891_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_execution_go_record_pr_merge_closeout_readonly_v0_20260601T175356Z"
)
GUARD_EXTENSION_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_guard_extension_precheck_readonly_v0_20260601T175637Z"
)
DERIVED_JSONL_BUILD_VALIDATE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_jsonl_build_validate_v0_20260601T165743Z"
)
WAVE_SCOPE_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_wave_scope_precheck_readonly_v0_20260601T180641Z"
)
PR3892_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_guard_extension_pr_merge_closeout_readonly_v0_20260601T180415Z"
)
WAVE1_EXECUTION_READINESS_PRECHECK_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_wave1_execution_readiness_precheck_readonly_v0_20260601T182100Z"
)
PR3893_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_wave1_charter_pr_merge_closeout_readonly_v0_20260601T181212Z"
)
WAVE1_BATCH_CLOSURE_PLAN_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_derived_only_mapping_wave1_batch_closure_plan_readonly_v0_20260601T182957Z"
)
PR3894_CLOSEOUT_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "closeout/after_small_derived_only_mapping_wave1_execution_guard_prep_pr_merge_closeout_readonly_v0_20260601T182216Z"
)
WRITE_PERMISSIONS_OWNER_TEST = "test_workflow_write_permissions_visibility_contract_v0.py"
SECRETS_REFERENCE_OWNER_TEST = "test_workflow_secrets_reference_visibility_contract_v0.py"

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

DECISION_RECORD_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_DECISION_RECORDED": "true",
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

EXECUTION_CHARTER_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_EXECUTION_CHARTER_PROPOSED": "true",
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

EXECUTION_GO_RECORD_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED": "true",
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

GUARD_EXTENSION_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED": "true",
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

WAVE1_CHARTER_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_WAVE1_CHARTER_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED": "true",
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

WAVE1_EXECUTION_GUARD_PREP_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_WAVE1_EXECUTION_GUARD_PREP_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_WAVE1_CHARTER_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED": "true",
    "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT": "true",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
    "DERIVED_CANDIDATE_ID_FAMILY_ONLY": "true",
    "DIRECT_MAPPING_WAVE_BLOCKED": "true",
}

WAVE1_BATCH_CLOSURE_EXPECTED: dict[str, str] = {
    "DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0": "true",
    "MAPPED_BY_DERIVED_EVIDENCE_ONLY": "true",
    "DERIVED_EVIDENCE_MAPPED_STATUS_ALLOWED": "true",
    "FORBIDS_DEFINITIVE_MAPPED_WITHOUT_INPUT": "true",
    "FORBIDS_PENDING_RISK_TABLE_DEFINITIVE_MAPPED_WITHOUT_INPUT": "true",
    "DERIVED_ONLY_MAPPING_WAVE1_EXECUTION_GUARD_PREP_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_WAVE1_CHARTER_PROPOSED": "true",
    "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO": "true",
    "INPUT_JSONL_PROVIDED": "false",
    "DERIVED_INPUT_JSONL_PROVIDED_EXTERNAL": "true",
    "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED": "true",
    "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT": "true",
    "LOSSLESS_JSONL_RECOVERY": "false",
    "ORIGINAL_FULL_LOSSLESS_EQUIVALENCE_CLAIMED": "false",
    "OLD_R_ID_RECONSTRUCTION_ALLOWED": "false",
    "DERIVED_CANDIDATE_ID_FAMILY_ONLY": "true",
    "DIRECT_MAPPING_WAVE_BLOCKED": "false",
}

DERIVED_EVIDENCE_MAPPED_RISKS: dict[str, tuple[str, str]] = {
    "R-001": (
        "tests/ci/test_workflow_write_permissions_visibility_contract_v0.py",
        "DERIVED-CYBER-R-001-001",
    ),
    "R-002": (
        "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py",
        "DERIVED-CYBER-R-002-001",
    ),
    "R-007": (
        "tests/ci/test_workflow_secrets_reference_visibility_contract_v0.py",
        "DERIVED-CYBER-R-007-001",
    ),
}


def _assert_derived_evidence_mapped(status_cell: str) -> None:
    assert "mapped-by-derived-evidence" in status_cell.lower()
    assert status_cell.strip().lower() != "mapped"


def _assert_derived_evidence_mapped_row(
    owner_cell: str,
    status_cell: str,
    *,
    expected_owner: str,
    derived_id: str,
) -> None:
    assert expected_owner in owner_cell
    _assert_derived_evidence_mapped(status_cell)
    assert derived_id in status_cell


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


def test_cybersecurity_visibility_derived_mapping_plan_wave1_derived_evidence_table_v0() -> None:
    rows = _risk_table_rows(_ci_audit_text())
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )


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


def test_cybersecurity_visibility_derived_only_mapping_decision_record_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    decision_block = _block_containing(text, DECISION_RECORD_BLOCK_ANCHOR)
    decision_values = _machine_line_values(decision_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping decision record v0" in text
    assert READINESS_REFRESH_BUNDLE_PATH in text
    assert PR3888_CLOSEOUT_PATH in text
    assert CHARTER_BUNDLE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text

    for key, expected in DECISION_RECORD_EXPECTED.items():
        assert decision_values.get(key) == expected, (
            f"decision record {key}={decision_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_decision_record_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping decision record" in truth_map
    assert "DERIVED_ONLY_MAPPING_DECISION_RECORDED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_execution_charter_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    charter_block = _block_containing(text, EXECUTION_CHARTER_BLOCK_ANCHOR)
    charter_values = _machine_line_values(charter_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping execution charter v0" in text
    assert EXECUTION_CHARTER_PRECHECK_PATH in text
    assert PR3889_CLOSEOUT_PATH in text
    assert READINESS_REFRESH_BUNDLE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text

    for key, expected in EXECUTION_CHARTER_EXPECTED.items():
        assert charter_values.get(key) == expected, (
            f"execution charter {key}={charter_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_execution_charter_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping execution charter" in truth_map
    assert "DERIVED_ONLY_MAPPING_EXECUTION_CHARTER_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_execution_go_record_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    go_record_block = _block_containing(text, EXECUTION_GO_RECORD_BLOCK_ANCHOR)
    go_record_values = _machine_line_values(go_record_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping execution GO record v0" in text
    assert EXECUTION_GO_READINESS_PRECHECK_PATH in text
    assert PR3890_CLOSEOUT_PATH in text
    assert EXECUTION_CHARTER_PRECHECK_PATH in text
    assert THIS_MODULE in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text

    for key, expected in EXECUTION_GO_RECORD_EXPECTED.items():
        assert go_record_values.get(key) == expected, (
            f"execution GO record {key}={go_record_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_execution_go_record_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping execution GO record" in truth_map
    assert "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_guard_extension_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    guard_block = _block_containing(text, GUARD_EXTENSION_BLOCK_ANCHOR)
    guard_values = _machine_line_values(guard_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping guard extension v0" in text
    assert GUARD_EXTENSION_PRECHECK_PATH in text
    assert PR3891_CLOSEOUT_PATH in text
    assert DERIVED_JSONL_BUILD_VALIDATE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text

    for key, expected in GUARD_EXTENSION_EXPECTED.items():
        assert guard_values.get(key) == expected, (
            f"guard extension {key}={guard_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_guard_extension_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping guard extension" in truth_map
    assert "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_EXECUTION_GO_RECORDED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_charter_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    wave1_block = _block_containing(text, WAVE1_CHARTER_BLOCK_ANCHOR)
    wave1_values = _machine_line_values(wave1_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping wave-1 charter v0" in text
    assert WAVE_SCOPE_PRECHECK_PATH in text
    assert PR3892_CLOSEOUT_PATH in text
    assert DERIVED_JSONL_BUILD_VALIDATE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "DIRECT_MAPPING_WAVE_BLOCKED=true" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text
    assert "does not** edit owner test modules" in text

    for derived_id in PLAN_DERIVED_IDS:
        assert derived_id in text

    for key, expected in WAVE1_CHARTER_EXPECTED.items():
        assert wave1_values.get(key) == expected, (
            f"wave-1 charter {key}={wave1_values.get(key)!r} expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_charter_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping wave-1 charter" in truth_map
    assert "DERIVED_ONLY_MAPPING_WAVE1_CHARTER_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_execution_guard_prep_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    guard_prep_block = _block_containing(text, WAVE1_EXECUTION_GUARD_PREP_BLOCK_ANCHOR)
    guard_prep_values = _machine_line_values(guard_prep_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping wave-1 execution guard prep v0" in text
    assert WAVE1_EXECUTION_READINESS_PRECHECK_PATH in text
    assert PR3893_CLOSEOUT_PATH in text
    assert WAVE_SCOPE_PRECHECK_PATH in text
    assert DERIVED_JSONL_BUILD_VALIDATE_PATH in text
    assert THIS_MODULE in text
    assert "OPERATOR_GO_DERIVED_ONLY_MAPPING_EXECUTION" in text
    assert "DIRECT_MAPPING_WAVE_BLOCKED=true" in text
    assert "does not** execute mapping" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** flip the pending risk table to **mapped**" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text
    assert "does not** edit owner test modules" in text

    for derived_id in PLAN_DERIVED_IDS:
        assert derived_id in text

    for key, expected in WAVE1_EXECUTION_GUARD_PREP_EXPECTED.items():
        assert guard_prep_values.get(key) == expected, (
            f"wave-1 execution guard prep {key}={guard_prep_values.get(key)!r} "
            f"expected {expected!r}"
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_execution_guard_prep_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping wave-1 execution guard prep" in truth_map
    assert "DERIVED_ONLY_MAPPING_WAVE1_EXECUTION_GUARD_PREP_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_WAVE1_CHARTER_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_GUARD_EXTENSION_PROPOSED=true" in truth_map
    assert "DERIVED_ONLY_MAPPING_PATH_REQUIRES_SEPARATE_GO=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert "DIRECT_MAPPING_WAVE_BLOCKED=true" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_batch_closure_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    batch_block = _block_containing(text, WAVE1_BATCH_CLOSURE_BLOCK_ANCHOR)
    batch_values = _machine_line_values(batch_block)

    assert "Pending R-001/R-002/R-007 — derived-only mapping wave-1 batch closure v0" in text
    assert WAVE1_BATCH_CLOSURE_PLAN_PATH in text
    assert PR3894_CLOSEOUT_PATH in text
    assert WAVE1_EXECUTION_READINESS_PRECHECK_PATH in text
    assert DERIVED_JSONL_BUILD_VALIDATE_PATH in text
    assert THIS_MODULE in text
    assert MAPPING_GUARD_TEST in text
    assert DERIVED_REFLECTION_TEST in text
    assert WRITE_PERMISSIONS_OWNER_TEST in text
    assert SECRETS_REFERENCE_OWNER_TEST in text
    assert "OPERATOR_GO_WAVE1_BATCH_CLOSURE_PR=true" in text
    assert "does not** set `INPUT_JSONL_PROVIDED=true`" in text
    assert "does not** claim derived JSONL is the original" in text
    assert "does not** authorize Old-R-ID reconstruction" in text
    assert "does not** assign definitive **`mapped`** status" in text
    assert "is distinct from definitive mapped" in text

    for derived_id in PLAN_DERIVED_IDS:
        assert derived_id in text

    for key, expected in WAVE1_BATCH_CLOSURE_EXPECTED.items():
        assert batch_values.get(key) == expected, (
            f"wave-1 batch closure {key}={batch_values.get(key)!r} expected {expected!r}"
        )

    rows = _risk_table_rows(text)
    for risk_id, (expected_owner, derived_id) in DERIVED_EVIDENCE_MAPPED_RISKS.items():
        owner_cell, status_cell = rows[risk_id]
        _assert_derived_evidence_mapped_row(
            owner_cell,
            status_cell,
            expected_owner=expected_owner,
            derived_id=derived_id,
        )

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_derived_only_mapping_wave1_batch_closure_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "derived-only mapping wave-1 batch closure" in truth_map
    assert "DERIVED_ONLY_MAPPING_WAVE1_BATCH_CLOSURE_V0=true" in truth_map
    assert "MAPPED_BY_DERIVED_EVIDENCE_ONLY=true" in truth_map
    assert "DERIVED_EVIDENCE_MAPPED_STATUS_ALLOWED=true" in truth_map
    assert "FORBIDS_DEFINITIVE_MAPPED_WITHOUT_INPUT=true" in truth_map
    assert "INPUT_JSONL_PROVIDED=false" in truth_map
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in truth_map
    assert THIS_MODULE in truth_map
    assert DERIVED_REFLECTION_TEST in truth_map
    assert MAPPING_GUARD_TEST in truth_map
    assert WRITE_PERMISSIONS_OWNER_TEST in truth_map
    assert SECRETS_REFERENCE_OWNER_TEST in truth_map
    assert "mapped-by-derived-evidence" in collapsed
    assert "non-authorizing" in collapsed
