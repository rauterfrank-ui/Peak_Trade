"""Static contract for Cybersecurity Visibility pending R-001/R-002/R-007 charter v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
calls external APIs, never touches runtime, scheduler, daemon, adapter, hooks,
launchctl, Notion, Market, broker/exchange, or order paths.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

REPO_STATIC_JSONL = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "inventory/repo_static_cybersecurity_risk_candidates/"
    "repo_static_cybersecurity_risk_candidates_jsonl_generation_v0_20260524T070050Z/"
    "REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl"
)


def test_cybersecurity_visibility_r_pending_repo_static_inventory_charter_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert "Cybersecurity Visibility Chain" in text
    assert "Pending R-001/R-002/R-007 — repo-static successor inventory charter v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_REPO_STATIC_INVENTORY_CHARTER_V0=true" in text
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "REPO_STATIC_SUCCESSOR_INVENTORY=true" in text
    assert "ORIGINAL_DURABLE_JSONL_REQUIRED_FOR_LOSSLESS_RECOVERY=true" in text
    assert "FULL_LOSSLESS_RISK_CANDIDATES_JSONL_NOT_FOUND=true" in text
    assert "REPO_STATIC_SUCCESSOR_DOES_NOT_CONTAIN_R001_R002_R007=true" in text
    assert "R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text

    for risk_id in ("R-001", "R-002", "R-007"):
        assert risk_id in text
        assert "repo-static successor charter v0" in collapsed
        assert "no `candidate_id` assigned" in collapsed

    assert "lossless inventory row" in collapsed
    assert "This charter **does not** recover, regenerate, or claim equivalence" in text
    assert REPO_STATIC_JSONL in text
    assert "repo_static_cybersecurity_risk_candidates_jsonl_generation_v0" in text
    assert "Candidate rows | `162`" in text or "Candidate rows | 162" in text
    assert "non-authorizing" in collapsed
    assert "broker/exchange" in collapsed or "broker" in collapsed

    assert "tests/ops/test_run_sample_size_ramp_script_contract_v0.py" in text
    assert "tests/ci/test_prcd_aws_export_write_smoke_workflow_contract_v0.py" in text

    assert "post_closeout_chain_execute_v0.py" not in text


def test_cybersecurity_visibility_r_pending_charter_truth_map_crosslink_v0() -> None:
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert "Cybersecurity Visibility R pending repo-static inventory charter v0" in truth_map
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert (
        "lossless_jsonl_recovery=false" in collapsed or "LOSSLESS_JSONL_RECOVERY=false" in truth_map
    )
    assert "non-authorizing" in collapsed
    assert "r-001" in collapsed or "R-001" in truth_map
