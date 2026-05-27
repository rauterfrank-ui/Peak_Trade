"""Static mapping guard contract for Cybersecurity Visibility R-001/R-002/R-007.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests operator artifacts or
touches runtime, hooks, Notion, Market, broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
INPUT_ARTIFACT_TEST = "test_cybersecurity_visibility_r_pending_input_artifact_contract_v0.py"
THIS_MODULE = Path(__file__).name

RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def test_cybersecurity_visibility_r_pending_mapping_guard_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert "Pending R-001/R-002/R-007 — mapping guard v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_MAPPING_GUARD_V0=true" in text
    assert "FORBIDS_FLIPPING_INPUT_JSONL_PROVIDED_WITHOUT_AUTHORIZED_MAPPING_SLICE=true" in text
    assert "FORBIDS_PENDING_RISK_TABLE_MAPPED_STATUS_WITHOUT_INPUT=true" in text
    assert "FORBIDS_REPO_STATIC_SUCCESSOR_AS_DEFINITIVE_MAPPING_INPUT=true" in text
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true" in text
    assert (
        "ACCEPTED_INPUT_ARTIFACTS=FULL_LOSSLESS_RISK_CANDIDATES.jsonl,"
        "APPROVED_OPERATOR_TRIAGE_ARTIFACT" in text
    )
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text

    assert "cannot be documented or tested as **recovered**" in text
    assert "repo-static successor `REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl` alone" in text

    rows = _risk_table_rows(text)
    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in rows
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()

    for mapped_id, expected_owner in (
        ("R-003", "tests/ops/test_run_sample_size_ramp_script_contract_v0.py"),
        ("R-004", "tests/ops/test_run_testnet_evidence_flow_v2_script_contract_v0.py"),
        ("R-005", "tests/ops/test_knowledge_prod_smoke_script.py"),
        ("R-006", "tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py"),
    ):
        owner_cell, status_cell = rows[mapped_id]
        assert expected_owner in owner_cell
        assert status_cell.lower() == "mapped"

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("INPUT_JSONL_PROVIDED="):
            assert stripped == "INPUT_JSONL_PROVIDED=false"
        if stripped.startswith("LOSSLESS_JSONL_RECOVERY="):
            assert stripped == "LOSSLESS_JSONL_RECOVERY=false"

    for marker in (
        "R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
        "R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
        "R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false",
    ):
        assert marker in text

    assert "non-authorizing" in collapsed


def test_cybersecurity_visibility_r_pending_mapping_guard_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "Cybersecurity Visibility R pending mapping guard v0" in truth_map
    assert THIS_MODULE in truth_map
    assert INPUT_ARTIFACT_TEST in truth_map
    assert "non-authorizing" in collapsed
    assert "fastpath" in collapsed or "fast-path" in collapsed or "tests/ci" in truth_map
