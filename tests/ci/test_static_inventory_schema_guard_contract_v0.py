"""Static contract for repo-static inventory schema validation guard v0.

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
MAPPING_GUARD_MODULE = "test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
INVENTORY_CHARTER_MODULE = "test_cybersecurity_visibility_r_pending_inventory_charter_v0.py"
CSC_LOSSLESS_V1_GUARD_MODULE = "test_csc_lossless_v1_dataset_reflection_contract_v0.py"
RCHAIN_GUARD_MODULE = "test_csc_rchain_v1_grouping_reflection_contract_v0.py"

STATIC_INVENTORY_JSONL = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "inventory/repo_static_cybersecurity_risk_candidates/"
    "repo_static_cybersecurity_risk_candidates_jsonl_generation_v0_20260524T070050Z/"
    "REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl"
)
VALIDATION_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/static_inventory_schema_validation_v0_20260601T040842Z"
)

GUARD_BLOCK_ANCHOR = "CYBERSECURITY_STATIC_INVENTORY_SCHEMA_VALIDATION_GUARD_V0=true"

EXPECTED_MACHINE_LINES: dict[str, str] = {
    "STATIC_INVENTORY_RESTART_SOURCE": "true",
    "STATIC_INVENTORY_SCHEMA_VALIDATION_PASSED": "true",
    "STATIC_INVENTORY_JSONL_VALID": "true",
    "STATIC_INVENTORY_RECORD_COUNT": "162",
    "ACCEPT_AS_LOSSLESS_INPUT": "false",
    "PARTIAL_RECOVERY_INPUT": "true",
    "RESTART_SOURCE_CANDIDATE": "true",
    "DEFINITIVE_MAPPING_ALLOWED": "false",
    "CONTAINS_R001": "false",
    "CONTAINS_R002": "false",
    "CONTAINS_R007": "false",
    "HAS_SEVERITY": "false",
    "HAS_CATEGORY": "true",
    "HAS_SOURCE_PATH": "true",
    "HAS_CONTEXT_OR_EVIDENCE_PAYLOAD": "true",
    "HAS_PROVENANCE": "false",
    "HAS_CHECKSUM": "false",
    "FAKE_RECONSTRUCTION_ALLOWED": "false",
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
    start = text.index("### Static inventory schema validation guard v0")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def test_static_inventory_schema_guard_contract_v0() -> None:
    text = _ci_audit_text()
    block = _guard_block(text)
    collapsed = block.lower()

    assert GUARD_BLOCK_ANCHOR in block
    assert "Static inventory schema validation guard v0" in text
    assert STATIC_INVENTORY_JSONL in block
    assert VALIDATION_BUNDLE in block
    assert THIS_MODULE in block
    assert MAPPING_GUARD_MODULE in block
    assert INVENTORY_CHARTER_MODULE in block
    assert CSC_LOSSLESS_V1_GUARD_MODULE in block
    assert RCHAIN_GUARD_MODULE in block

    for key, value in EXPECTED_MACHINE_LINES.items():
        assert f"{key}={value}" in block, f"missing or wrong {key}={value}"

    assert "does not** treat the 162-row inventory as lossless input" in block
    assert "does not** authorize definitive R-001/R-002/R-007 mapping" in block
    assert "does not** permit severity/provenance/checksum claims" in block
    assert "lossless_equivalent=false" in block
    assert "non-authorizing" in collapsed
    assert "security scans" in collapsed
    assert "fake reconstruction" in collapsed
    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_static_inventory_schema_guard_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "Static inventory schema validation guard v0" in truth_map
    assert THIS_MODULE in truth_map
    assert "STATIC_INVENTORY_RESTART_SOURCE=true" in truth_map
    assert "ACCEPT_AS_LOSSLESS_INPUT=false" in truth_map
    assert "DEFINITIVE_MAPPING_ALLOWED=false" in truth_map
    assert "non-authorizing" in collapsed


def test_static_inventory_schema_guard_reciprocal_owner_modules_exist_v0() -> None:
    text = _ci_audit_text()
    assert (REPO_ROOT / "tests" / "ci" / MAPPING_GUARD_MODULE).is_file()
    assert (REPO_ROOT / "tests" / "ci" / INVENTORY_CHARTER_MODULE).is_file()
    static_section = text.split("### Static visibility contract owners", 1)[1].split(
        "## Remote Runtime Contract", 1
    )[0]
    assert THIS_MODULE in static_section
