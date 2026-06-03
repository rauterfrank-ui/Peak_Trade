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

ADOPTION_HEADING = (
    "Pending R-001/R-002/R-007 — operator-accepted archive FULL_LOSSLESS governance adoption v0"
)
ADOPTION_BLOCK_ANCHOR = (
    "CYBERSECURITY_VISIBILITY_OPERATOR_ACCEPTED_ARCHIVE_FULL_LOSSLESS_ADOPTION_V0=true"
)
ARCHIVE_FULL_LOSSLESS_SHA256 = (
    "eff5698370a8cd38cacf02325d81223ca667d4995bda8cfcb6435b5de5327f26"
)
ARCHIVE_FULL_LOSSLESS_INTAKE_PATH = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "planning/cybersecurity_input_jsonl_operator_intake_readonly_v0_20260601T164324Z/"
    "operator_artifacts_pending/FULL_LOSSLESS_RISK_CANDIDATES.jsonl"
)

REPO_STATIC_JSONL = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "inventory/repo_static_cybersecurity_risk_candidates/"
    "repo_static_cybersecurity_risk_candidates_jsonl_generation_v0_20260524T070050Z/"
    "REPO_STATIC_CYBERSECURITY_RISK_CANDIDATES.jsonl"
)


def test_cybersecurity_visibility_archive_full_lossless_governance_adoption_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert ADOPTION_HEADING in text
    assert ADOPTION_BLOCK_ANCHOR in text
    assert ARCHIVE_FULL_LOSSLESS_SHA256 in text
    assert ARCHIVE_FULL_LOSSLESS_INTAKE_PATH in text
    assert "NOT_ORIGINAL_TMP_FULL_LOSSLESS=true" in text
    assert "ORIGINAL_TMP_FULL_LOSSLESS_AVAILABLE=false" in text
    assert "DERIVED_ONLY_USED_AS_AUTHORITY=false" in text
    assert "ARCHIVE_RECREATE_FULL_LOSSLESS_GOVERNANCE_ACCEPTED=true" in text
    assert "FORBIDS_ORIGINAL_TMP_RECOVERY_CLAIM=true" in text
    assert "Recreate → Intake PASS → Mapping PASS" in text
    for risk_id in ("R-001", "R-002", "R-007"):
        assert risk_id in text
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "FORBIDS_ORIGINAL_TMP_RECOVERY_CLAIM=true" in text
    assert "must **not** be claimed recovered" in text


def test_cybersecurity_visibility_r_pending_repo_static_inventory_charter_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    collapsed = text.lower()

    assert ADOPTION_HEADING in text
    assert "Cybersecurity Visibility Chain" in text
    assert "Pending R-001/R-002/R-007 — repo-static successor inventory charter v0" in text
    assert "CYBERSECURITY_VISIBILITY_R_PENDING_REPO_STATIC_INVENTORY_CHARTER_V0=true" in text
    assert "LOSSLESS_JSONL_RECOVERY=false" in text
    assert "REPO_STATIC_SUCCESSOR_INVENTORY=true" in text
    assert "ORIGINAL_DURABLE_JSONL_REQUIRED_FOR_LOSSLESS_RECOVERY=true" in text
    assert "ORIGINAL_TMP_FULL_LOSSLESS_NOT_FOUND=true" in text
    assert "FULL_LOSSLESS_RISK_CANDIDATES_JSONL_NOT_FOUND=false" in text
    assert "ARCHIVE_RECREATE_FULL_LOSSLESS_GOVERNANCE_ACCEPTED=true" in text
    assert "REPO_STATIC_SUCCESSOR_DOES_NOT_CONTAIN_R001_R002_R007=true" in text
    assert "R001_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R002_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text
    assert "R007_REPO_STATIC_CANDIDATE_ID_ASSIGNED=false" in text

    for risk_id in ("R-001", "R-002", "R-007"):
        assert risk_id in text
        assert "repo-static successor charter v0" in collapsed
        assert "no `candidate_id` assigned" in collapsed

    assert "lossless inventory row" in collapsed or "archive" in collapsed
    assert "This charter **does not** ingest archive JSONL into the repo" in text
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


CV3B_READOUT_HEADING = "### Defensive visibility readout / owner-triage guard v0 (SLICE-CV-3b)"
CV3B_BLOCK_ANCHOR = "CV3B_DEFENSIVE_VISIBILITY_READOUT_OWNER_TRIAGE_GUARD_V0=true"
MAPPING_GUARD_MODULE = "tests/ci/test_cybersecurity_visibility_r_pending_mapping_guard_v0.py"
DERIVED_MAPPING_PLAN_MODULE = (
    "tests/ci/test_cybersecurity_visibility_derived_mapping_plan_progress_contract_v0.py"
)


def _cv3b_readout_block(text: str) -> str:
    start = text.index(CV3B_READOUT_HEADING)
    end = text.index("Operators may use this histogram", start)
    return text[start:end]


def test_cybersecurity_visibility_cv3b_inventory_charter_readout_guard_v0() -> None:
    text = CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")
    block = _cv3b_readout_block(text)
    collapsed = block.lower()

    assert CV3B_BLOCK_ANCHOR in block
    assert THIS_MODULE in block
    assert MAPPING_GUARD_MODULE in block
    assert DERIVED_MAPPING_PLAN_MODULE in block
    assert "Repo-static successor inventory charter" in block
    assert "review-input only" in collapsed
    assert "no r-001/r-002/r-007 rows" in collapsed
    assert "REPO_STATIC_SUCCESSOR_DOES_NOT_CONTAIN_R001_R002_R007=true" in text
    assert "INPUT_JSONL_PROVIDED=false" in block
    assert "non-authorizing" in collapsed
    assert "input_jsonl fabrication" in collapsed
