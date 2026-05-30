"""Static contract for Cybersecurity Visibility manual-dispatch histogram crosslink v0.

Reads docs/ops/CI_AUDIT_KNOWN_ISSUES.md only. Never dispatches workflows, never
touches runtime, scheduler, daemon, adapter, hooks, launchctl, Notion, Market,
broker/exchange, or order paths.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_AUDIT_KNOWN_ISSUES = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

HISTOGRAM_CLASSIFICATION = "manual_dispatch_sensitive_surface"
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

REQUIRED_MANUAL_DISPATCH_REUSE_OWNER = (
    "tests/ci/test_workflow_manual_dispatch_sensitive_surface_contract_v0.py"
)

MANUAL_DISPATCH_PARALLEL_MARKERS = (
    "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_MANUAL_DISPATCH_SENSITIVE_SURFACE_CROSSLINK_V0=true",
    "Cybersecurity Visibility repo-static histogram manual dispatch sensitive surface",
)

FORBIDDEN_AUTHORIZATION_PHRASES: tuple[str, ...] = (
    "manual dispatch approved",
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

FORBIDDEN_MACHINE_LINES: tuple[str, ...] = (
    "INPUT_JSONL_PROVIDED=true",
    "R001_R002_R007_MAPPING_COMPLETED=true",
    "MANUAL_DISPATCH_SENSITIVE_SURFACE_MAPPING_COMPLETED=true",
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


def test_cybersecurity_visibility_repo_static_histogram_manual_dispatch_crosslink_v0() -> None:
    text = _ci_audit_text()
    collapsed = text.lower()
    histogram = _histogram_section(text)

    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_MANUAL_DISPATCH_SENSITIVE_SURFACE_CROSSLINK_V0=true"
        in text
    )
    assert (
        "CYBERSECURITY_VISIBILITY_REPO_STATIC_HISTOGRAM_MANUAL_DISPATCH_SENSITIVE_SURFACE_CROSSLINK_DOCS_TESTS_ONLY=true"
        in text
    )
    assert "INPUT_JSONL_PROVIDED=false" in text
    assert "DEFINITIVE_R001_R002_R007_MAPPING_BLOCKED=true" in text
    assert "non-authorizing" in collapsed
    assert HISTOGRAM_CLASSIFICATION in histogram

    match = HISTOGRAM_ROW_RX.search(histogram)
    assert match is not None, f"missing histogram row for {HISTOGRAM_CLASSIFICATION!r}"
    assert match.group(1) == "70"
    notes_cell = match.group(2)
    assert f"Reuse `{REQUIRED_MANUAL_DISPATCH_REUSE_OWNER}`" in notes_cell
    assert (REPO_ROOT / REQUIRED_MANUAL_DISPATCH_REUSE_OWNER).is_file(), (
        f"missing reuse owner module: {REQUIRED_MANUAL_DISPATCH_REUSE_OWNER}"
    )

    reuse_paths = HISTOGRAM_REUSE_PATH_RX.findall(histogram)
    assert REQUIRED_MANUAL_DISPATCH_REUSE_OWNER in reuse_paths

    owners_match = STATIC_OWNERS_SECTION_RX.search(text)
    assert owners_match is not None, "static visibility contract owners section missing"
    owners_section = owners_match.group(1)
    assert "Manual-dispatch sensitive surfaces" in owners_section
    assert REQUIRED_MANUAL_DISPATCH_REUSE_OWNER in owners_section

    rows = _risk_table_rows(text)
    for pending_id in ("R-001", "R-002", "R-007"):
        assert pending_id in rows
        owner_cell, status_cell = rows[pending_id]
        assert owner_cell == "—"
        assert "pending" in status_cell.lower()
        assert "mapped" not in status_cell.lower()

    assert REQUIRED_MANUAL_DISPATCH_REUSE_OWNER in text

    lines = {line.strip() for line in text.splitlines()}
    for marker in FORBIDDEN_MACHINE_LINES:
        assert marker not in lines

    for phrase in FORBIDDEN_AUTHORIZATION_PHRASES:
        assert phrase not in collapsed

    assert "workflow_dispatch executed" not in collapsed
    assert "mapping completed" not in collapsed

    assert "CYBERSECURITY_VISIBILITY_CHAIN_PARALLEL_ANCHOR" not in text


def test_cybersecurity_visibility_manual_dispatch_crosslink_has_no_parallel_doc_surface() -> None:
    canonical = CI_AUDIT_KNOWN_ISSUES.resolve()
    parallel_docs: list[Path] = []

    for path in (REPO_ROOT / "docs").rglob("*.md"):
        if path.resolve() == canonical:
            continue
        body = path.read_text(encoding="utf-8")
        if any(marker in body for marker in MANUAL_DISPATCH_PARALLEL_MARKERS):
            parallel_docs.append(path.relative_to(REPO_ROOT))

    assert parallel_docs == []
