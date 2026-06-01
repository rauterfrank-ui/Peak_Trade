"""Static contract for CSC-RCHAIN-v1 accepted groups reflection guard v0.

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
CSC_LOSSLESS_V1_GUARD_MODULE = "test_csc_lossless_v1_dataset_reflection_contract_v0.py"
STATIC_INVENTORY_GUARD_MODULE = "test_static_inventory_schema_guard_contract_v0.py"
MAPPING_GUARD_MODULE = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"

ACCEPT_GROUPS = (
    "CSC-RCHAIN-v1-006",
    "CSC-RCHAIN-v1-007",
    "CSC-RCHAIN-v1-008",
    "CSC-RCHAIN-v1-009a",
    "CSC-RCHAIN-v1-009b",
    "CSC-RCHAIN-v1-002-infra",
    "CSC-RCHAIN-v1-002-integration",
    "CSC-RCHAIN-v1-002-p101",
)
PARK_GROUPS = (
    "CSC-RCHAIN-v1-001",
    "CSC-RCHAIN-v1-002",
    "CSC-RCHAIN-v1-003",
    "CSC-RCHAIN-v1-004",
    "CSC-RCHAIN-v1-005",
    "CSC-RCHAIN-v1-009",
)

OPERATOR_DECISION = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_rchain_v1_operator_decision_filed_v0_20260601T045040Z"
)
GROUPING_REVIEW = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/csc_lossless_v1_r_chain_candidate_grouping_review_v0_20260601T044523Z"
)

GUARD_BLOCK_ANCHOR = "CYBERSECURITY_CSC_RCHAIN_V1_ACCEPTED_GROUPS_REFLECTION_GUARD_V0=true"

EXPECTED_MACHINE_LINES: dict[str, str] = {
    "CSC_RCHAIN_V1_OPERATOR_DECISION_RECORDED": "true",
    "CSC_RCHAIN_V1_ACCEPTED_GROUPS": (
        "CSC-RCHAIN-v1-006,CSC-RCHAIN-v1-007,CSC-RCHAIN-v1-008,"
        "CSC-RCHAIN-v1-009a,CSC-RCHAIN-v1-009b,CSC-RCHAIN-v1-002-infra,"
        "CSC-RCHAIN-v1-002-integration,CSC-RCHAIN-v1-002-p101"
    ),
    "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT": "8",
    "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT": "127",
    "CSC_RCHAIN_V1_PARKED_GROUP_COUNT": "6",
    "CSC_RCHAIN_V1_REJECTED_GROUPS": "",
    "CSC_RCHAIN_V1_NEED_MORE_REVIEW_GROUPS": "",
    "SOURCE_DATASET_ID_FAMILY": "CSC-LOSSLESS-v1",
    "SOURCE_DATASET_RECORD_COUNT": "672",
    "NEW_RCHAIN_FAMILY": "CSC-RCHAIN-v1",
    "TRACEABILITY_TO_CSC_LOSSLESS_PASSED": "true",
    "OLD_R_ID_MAPPING_ALLOWED": "false",
    "OLD_R_ID_EQUIVALENCE_CLAIM_ALLOWED": "false",
    "OLD_R_ID_EQUIVALENCE_CLAIM_COUNT": "0",
    "OLD_RCHAIN_RESTORED": "false",
    "LEGACY_R_ID_REFERENCE_ALLOWED": "false",
    "FAKE_RECONSTRUCTION_ALLOWED": "false",
    "STATIC_INVENTORY_IS_SEPARATE_SOURCE": "true",
    "STATIC_INVENTORY_RECORD_COUNT": "162",
    "PARK_GROUPS_NOT_AUTHORIZED_FOR_REFLECTION": "true",
    "SCHEDULER_PARK_GROUPS_SPLIT_RECOMMENDED": "true",
    "GROUP_009_SPLIT_RECOMMENDED": "true",
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
    start = text.index("### CSC-RCHAIN-v1 accepted groups reflection guard v0")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def test_csc_rchain_v1_grouping_reflection_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block(text)
    collapsed = block.lower()

    assert GUARD_BLOCK_ANCHOR in block
    assert "CSC-RCHAIN-v1 accepted groups reflection guard v0" in text
    assert OPERATOR_DECISION in block
    assert GROUPING_REVIEW in block
    assert THIS_MODULE in block
    assert CSC_LOSSLESS_V1_GUARD_MODULE in block
    assert STATIC_INVENTORY_GUARD_MODULE in block
    assert MAPPING_GUARD_MODULE in block

    for key, value in EXPECTED_MACHINE_LINES.items():
        assert f"{key}={value}" in block, f"missing or wrong {key}={value}"

    for gid in ACCEPT_GROUPS:
        assert gid in block
    for gid in PARK_GROUPS:
        assert gid in block

    assert "CSC_RCHAIN_V1_PARKED_GROUPS=" in block
    parked_line = next(
        line for line in block.splitlines() if line.startswith("CSC_RCHAIN_V1_PARKED_GROUPS=")
    )
    for gid in PARK_GROUPS:
        assert gid in parked_line
    accepted_line = next(
        line for line in block.splitlines() if line.startswith("CSC_RCHAIN_V1_ACCEPTED_GROUPS=")
    )
    for gid in ACCEPT_GROUPS:
        assert gid in accepted_line

    assert "Does **not** treat PARK groups as accepted" in block
    assert "does **not** authorize definitive R-001/R-002/R-007 mapping" in block
    assert "does **not** claim old R-ID equivalence" in block
    assert "not** restoration of the legacy" in block
    assert "non-authorizing" in collapsed
    assert "security scans" in collapsed
    assert "fake reconstruction" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_csc_rchain_v1_grouping_reflection_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "CSC-RCHAIN-v1 accepted groups reflection guard v0" in truth_map
    assert THIS_MODULE in truth_map
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT=8" in truth_map
    assert "CSC-RCHAIN-v1-009a" in truth_map
    assert "CSC-RCHAIN-v1-009b" in truth_map
    assert "CSC-RCHAIN-v1-002-infra" in truth_map
    assert "CSC-RCHAIN-v1-002-integration" in truth_map
    assert "CSC-RCHAIN-v1-002-p101" in truth_map
    assert "PARK_GROUPS_NOT_AUTHORIZED_FOR_REFLECTION=true" in truth_map
    assert "OLD_RCHAIN_RESTORED=false" in truth_map
    assert "non-authorizing" in collapsed


def test_csc_rchain_v1_grouping_reflection_reciprocal_owner_modules_exist_v0() -> None:
    text = _ci_audit_text()
    assert (REPO_ROOT / "tests" / "ci" / CSC_LOSSLESS_V1_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / STATIC_INVENTORY_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / MAPPING_GUARD_MODULE).is_file()
    static_section = text.split("### Static visibility contract owners", 1)[1].split(
        "## Remote Runtime Contract", 1
    )[0]
    assert THIS_MODULE in static_section
