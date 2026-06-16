"""Static contract for Cybersecurity Visibility repo-static histogram branch-environment crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
touches runtime, scheduler, daemon, adapter, hooks, launchctl, Notion, Market,
broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.ci.cybersecurity_visibility_retained_risk_row_assertions_v0 import (
    assert_retained_r001_r002_r007_pending_or_derived_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
THIS_MODULE = Path(__file__).name

HISTOGRAM_CLASSIFICATION = "branch_or_environment_authority"
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

REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER = (
    "tests/ci/test_workflow_write_permissions_visibility_contract_v0.py"
)

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "workflow write permission approved",
    "write permission approved",
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


def _risk_table_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for risk_id, owner_cell, status_cell in RISK_TABLE_ROW_RX.findall(text):
        rows[risk_id] = (owner_cell.strip(), status_cell.strip())
    return rows


def test_cybersecurity_visibility_repo_static_histogram_branch_environment_authority_crosslink_v0() -> (
    None
):
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_BRANCH_ENVIRONMENT_AUTHORITY_CROSSLINK_V0=true"
        in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_BRANCH_ENVIRONMENT_AUTHORITY_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "12"
    notes_cell = match.group(2)
    assert f"Reuse `{REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER}`" in notes_cell
    assert (REPO_ROOT / REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER).is_file(), (
        f"missing reuse owner module: {REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER}"
    )

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    assert REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER in reuse_paths

    owners_match = STATIC_OWNERS_SECTION_RX.search(text)
    assert owners_match is not None, "static visibility contract owners section missing"
    owners_section = owners_match.group(1)
    assert "Workflow write permissions" in owners_section
    assert REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER in owners_section

    assert_retained_r001_r002_r007_pending_or_derived_evidence(_risk_table_rows(text))

    assert REQUIRED_WRITE_PERMISSIONS_REUSE_OWNER in text

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_repo_static_histogram_branch_environment_authority_truth_map_crosslink_v0() -> (
    None
):
    truth_map = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    collapsed = truth_map.lower()

    assert (
        "Cybersecurity Visibility repo-static histogram branch-environment authority owner crosslink v0"
        in truth_map
    )
    assert "CI_AUDIT_KNOWN_ISSUES.md" in truth_map
    assert THIS_MODULE in truth_map
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_BRANCH_ENVIRONMENT_AUTHORITY_CROSSLINK_V0=true"
        in truth_map
        or "branch-environment authority owner crosslink" in collapsed
    )
    assert "non-authorizing" in collapsed
    assert "input_jsonl_provided=false" in collapsed or "INPUT_JSONL_PROVIDED=false" in truth_map
