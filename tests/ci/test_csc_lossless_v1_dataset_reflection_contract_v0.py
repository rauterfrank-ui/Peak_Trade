"""Static contract for CSC-LOSSLESS-v1 dataset reflection guard v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests JSONL, never
dispatches workflows, never touches runtime, scheduler, Notion, Market,
broker/exchange, network, secrets, or scan paths.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name
STATIC_INVENTORY_GUARD_MODULE = "test_static_inventory_schema_guard_contract_v0.py"
MAPPING_GUARD_MODULE = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"

NORMALIZED_JSONL = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "cybersecurity_lossless_pipeline/cybersecurity_lossless_pipeline_dry_run_v0_20260601T042949Z/"
    "NORMALIZED_JSONL/CSC_LOSSLESS_V1_CANDIDATES.jsonl"
)
POST_EXTRACT_REVIEW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_new_lossless_pipeline_post_extract_review_v0_20260601T043237Z"
)

GUARD_BLOCK_ANCHOR = "CYBERSECURITY_CSC_LOSSLESS_V1_DATASET_REFLECTION_GUARD_V0=true"

EXPECTED_MACHINE_LINES: dict[str, str] = {
    "NEW_LOSSLESS_DATASET_CREATED": "true",
    "ID_FAMILY": "CSC-LOSSLESS-v1",
    "PIPELINE_RUN_ID": "cybersecurity_lossless_pipeline_dry_run_v0_20260601T042949Z",
    "NORMALIZED_RECORD_COUNT": "672",
    "RAW_RECORD_COUNT": "672",
    "JSONL_VALID": "true",
    "REQUIRED_FIELDS_PRESENT": "true",
    "CANDIDATE_IDS_UNIQUE": "true",
    "SOURCE_FILE_CHECKSUM_COVERAGE": "true",
    "RECORD_CHECKSUM_COVERAGE": "true",
    "SOURCE_PATH_EXISTENCE_CHECK_PASSED": "true",
    "MAPPING_STATUS_UNMAPPED_COUNT": "672",
    "OLD_R_ID_EQUIVALENCE_CLAIM_COUNT": "0",
    "TRUE_OLD_LOSSLESS_INPUT_FOUND": "false",
    "ACCEPT_AS_OLD_LOSSLESS_INPUT": "false",
    "OLD_R_ID_MAPPING_ALLOWED": "false",
    "FAKE_RECONSTRUCTION_ALLOWED": "false",
    "STATIC_INVENTORY_IS_SEPARATE_SOURCE": "true",
    "STATIC_INVENTORY_RECORD_COUNT": "162",
    "STATIC_ID_OVERLAP_COUNT": "0",
    "SECURITY_SCAN_STARTED": "false",
    "RUNTIME_STARTED": "false",
    "SCHEDULER_STARTED": "false",
    "AWS_TOUCHED": "false",
    "NETWORK_TOUCHED": "false",
    "SECRETS_INCLUDED": "false",
}


def _ci_audit_text() -> str:
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _guard_block(text: str) -> str:
    start = text.index("### CSC-LOSSLESS-v1 dataset reflection guard v0")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def test_csc_lossless_v1_dataset_reflection_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block(text)
    collapsed = block.lower()

    assert GUARD_BLOCK_ANCHOR in block
    assert "CSC-LOSSLESS-v1 dataset reflection guard v0" in text
    assert NORMALIZED_JSONL in block
    assert POST_EXTRACT_REVIEW in block
    assert THIS_MODULE in block
    assert STATIC_INVENTORY_GUARD_MODULE in block
    assert MAPPING_GUARD_MODULE in block

    for key, value in EXPECTED_MACHINE_LINES.items():
        assert f"{key}={value}" in block, f"missing or wrong {key}={value}"

    assert "does not** treat v1 as recovered old lossless input" in block
    assert "does not** authorize definitive R-001/R-002/R-007 mapping" in block
    assert "does not** merge v1 with static inventory IDs" in block
    assert "CSC-STATIC-v0" in block
    assert "non-authorizing" in collapsed
    assert "security scans" in collapsed
    assert "fake reconstruction" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_csc_lossless_v1_dataset_reflection_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "CSC-LOSSLESS-v1 dataset reflection guard v0" in truth_map
    assert THIS_MODULE in truth_map
    assert "NEW_LOSSLESS_DATASET_CREATED=true" in truth_map
    assert "ID_FAMILY=CSC-LOSSLESS-v1" in truth_map
    assert "ACCEPT_AS_OLD_LOSSLESS_INPUT=false" in truth_map
    assert "OLD_R_ID_MAPPING_ALLOWED=false" in truth_map
    assert "non-authorizing" in collapsed


def test_csc_lossless_v1_dataset_reflection_reciprocal_owner_modules_exist_v0() -> None:
    text = _ci_audit_text()
    assert (REPO_ROOT / "tests" / "ci" / STATIC_INVENTORY_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / MAPPING_GUARD_MODULE).is_file()
    static_section = text.split("### Static visibility contract owners", 1)[1].split(
        "## Remote Runtime Contract", 1
    )[0]
    assert THIS_MODULE in static_section
