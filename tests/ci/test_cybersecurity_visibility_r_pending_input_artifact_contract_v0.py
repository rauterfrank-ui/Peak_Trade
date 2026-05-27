"""Static contract for Cybersecurity Visibility pending R-001/R-002/R-007 input artifact v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never ingests operator artifacts,
never dispatches workflows, and never touches runtime, hooks, Notion, or Market paths.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
CHARTER_TEST = "test_cybersecurity_visibility_r_pending_inventory_charter_v0.py"
THIS_MODULE = Path(__file__).name


def test_cybersecurity_visibility_r_pending_input_artifact_contract_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert "Pending R-001/R-002/R-007 — input artifact contract v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_INPUT_ARTIFACT_CONTRACT_V0=true" in text
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "INPUT_JSONL_REQUIRED=true" in text
    assert (
        "ACCEPTED_INPUT_ARTIFACTS=FULL_LOSSLESS_RISK_CANDIDATES.jsonl,"
        "APPROVED_OPERATOR_TRIAGE_ARTIFACT" in text
    )
    assert "NO_MAPPING_WITHOUT_INPUT_ARTIFACT=true" in text
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "INPUT_JSONL=<absolute path" in text
    assert "no-mapping-without-input" in collapsed or "NO_MAPPING_WITHOUT_INPUT_ARTIFACT" in text

    assert "This contract **does not** ingest files" in text
    assert "**does not** set `LOSSLESS_JSONL_RECOVERY=true`" in text

    for risk_id in ("R-001", "R-002", "R-007"):
        assert risk_id in text
        assert "pending" in collapsed or "Pending" in text

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
