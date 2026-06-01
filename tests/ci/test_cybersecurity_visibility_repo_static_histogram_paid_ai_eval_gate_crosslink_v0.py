"""Static contract for Cybersecurity Visibility repo-static histogram paid AI eval gate crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
runs paid Promptfoo/OpenAI evals, never touches runtime, scheduler, daemon,
adapter, hooks, launchctl, Notion, Market, broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

HISTOGRAM_CLASSIFICATION = "paid_ai_eval_gate"
HISTOGRAM_ROW_RX = re.compile(
    rf"^\| `{re.escape(HISTOGRAM_CLASSIFICATION)}` \| (\d+) \| (.+) \|$",
    re.MULTILINE,
)
HISTOGRAM_REUSE_PATH_RX = re.compile(r"Reuse `(tests/(?:ci|ops|webui)/[A-Za-z0-9_./-]+\.py)`")
RISK_TABLE_ROW_RX = re.compile(
    r"^\| (R-\d{3}) \| ([^|]*) \| ([^|]*) \|$",
    re.MULTILINE,
)
STATIC_OWNERS_SECTION_RX = re.compile(
    r"### Static visibility contract owners \(reuse — do not duplicate\)(.*?)(?:\n### |\Z)",
    re.DOTALL,
)

REQUIRED_PAID_AI_EVAL_REUSE_OWNER = (
    "tests/ci/test_aiops_promptfoo_cost_gate_workflow_contract_v0.py"
)
GROUPING_REFLECTION_GUARD_MODULE = "tests/ci/test_csc_rchain_v1_grouping_reflection_contract_v0.py"
ACCEPTED_SUBGROUP_009A = "CSC-RCHAIN-v1-009a"
ACCEPTED_SUBGROUP_009B = "CSC-RCHAIN-v1-009b"

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "paid evals enabled by default",
    "paid promptfoo approved",
    "openai eval authorized",
    "secret injection approved",
    "pr/push paid eval execution approved",
    "runtime start authorized",
    "testnet approved",
    "live approved",
    "operator bypass",
    "ready_for_start=true",
    "preflight_blocked_lifted=true",
    "r-001 mapped",
    "r-002 mapped",
    "r-007 mapped",
)


def _ci_audit_text() -> str:
    assert CI_AUDIT_KNOWN_ISSUES.is_file()
    return CI_AUDIT_KNOWN_ISSUES.read_text(encoding="utf-8")


def _histogram_section(text: str) -> str:
    start = text.find("**Interim classification histogram")
    assert start != -1, "histogram section missing"
    end = text.find("**Lossless recovery still required")
    assert end != -1, "histogram section end missing"
    return text[start:end]


def _csc_rchain_accepted_groups_guard_block(text: str) -> str:
    start = text.index("### CSC-RCHAIN-v1 accepted groups reflection guard v0")
    end = text.index("### Static visibility contract owners", start)
    return text[start:end]


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def test_cybersecurity_visibility_repo_static_histogram_paid_ai_eval_gate_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_PAID_AI_EVAL_GATE_CROSSLINK_V0=true" in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_PAID_AI_EVAL_GATE_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "4"
    notes_cell = match.group(2)
    assert f"Reuse `{REQUIRED_PAID_AI_EVAL_REUSE_OWNER}`" in notes_cell
    assert (REPO_ROOT / REQUIRED_PAID_AI_EVAL_REUSE_OWNER).is_file(), (
        f"missing reuse owner module: {REQUIRED_PAID_AI_EVAL_REUSE_OWNER}"
    )

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    assert REQUIRED_PAID_AI_EVAL_REUSE_OWNER in reuse_paths

    owners_match = STATIC_OWNERS_SECTION_RX.search(text)
    assert owners_match is not None, "static visibility contract owners section missing"
    owners_section = owners_match.group(1)
    assert "AI-Ops Promptfoo paid eval cost gate" in owners_section
    assert REQUIRED_PAID_AI_EVAL_REUSE_OWNER in owners_section

    rows = _risk_table_rows(text)
    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in rows
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()

    assert REQUIRED_PAID_AI_EVAL_REUSE_OWNER in text

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text

    guard_block = _csc_rchain_accepted_groups_guard_block(text)
    assert ACCEPTED_SUBGROUP_009A in guard_block
    assert ACCEPTED_SUBGROUP_009B in guard_block
    assert GROUPING_REFLECTION_GUARD_MODULE in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_GROUP_COUNT=20" in guard_block
    assert "CSC_RCHAIN_V1_ACCEPTED_CANDIDATE_COUNT=203" in guard_block
    assert "CSC_RCHAIN_V1_ACCEPT_REPO_REFLECTED_COUNT=203" in guard_block
    assert "CSC_RCHAIN_V1_HYBRID_AUTHORITY_POINTER_ACTIVE=true" in guard_block
    assert (
        "csc_rchain_v1_external_full_authority_bundle_draft_and_wiring_check_readonly_v0_20260601T104257Z"
        in guard_block
    )
    assert "CSC_RCHAIN_V1_OLD_124_COUNT_BUNDLES_HISTORICAL_ONLY=true" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMATION_MODEL_ACTIVE=true" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_CANDIDATE_COUNT=0" in guard_block
    assert "CSC_RCHAIN_V1_GROUP_PARK_REAFFIRMED_SUBSET_OF_PARK=true" in guard_block
    assert (
        "csc_rchain_v1_post_ops_closeout_contracts_batch_authority_refresh_and_next_batch_ranking_readonly_v0_20260601T133828Z"
        in guard_block
    )
    assert "CSC-RCHAIN-v1-009" in guard_block
    assert "parent **CSC-RCHAIN-v1-009**" in guard_block


def test_cybersecurity_visibility_repo_static_histogram_paid_ai_eval_gate_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert (
        "Cybersecurity Visibility repo-static histogram paid AI eval gate owner crosslink v0"
        in truth_map
    )
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_PAID_AI_EVAL_GATE_CROSSLINK_V0=true"
        in truth_map
        or "paid ai eval gate owner crosslink" in collapsed
    )
    assert "non-authorizing" in collapsed
    assert "input_jsonl_provided=false" in collapsed or "INPUT_JSONL_PROVIDED=false" in truth_map
