"""Static contract tests for mandatory durable closeout contract v0 (Preflight §2b.1)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
PRIMARY_EVIDENCE = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
PLANNING_RETENTION_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_planning_artifact_durable_retention_contract_v0.py"
)
PRIMARY_EVIDENCE_INVARIANT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_primary_evidence_retention_invariant_contract_v0.py"
)
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"
ER_RELEASE_RC_INDEX_HEADING = "### Evidence Durable Closeout Retention RC v0 — index v0"
THIS_MODULE = Path(__file__).name

MANDATORY_MARKERS = (
    "MANDATORY_DURABLE_CLOSEOUT_CONTRACT_V0=true",
    "MANDATORY_DURABLE_CLOSEOUT_DOCS_TESTS_ONLY=true",
    "TMP_ONLY_CLOSEOUT_INCOMPLETE=true",
    "MATERIAL_CLOSEOUT_REQUIRES_DURABLE_COPY=true",
    "DURABLE_COPY_README_REQUIRED=true",
    "MANIFEST_SHA256_REQUIRED=true",
    "MANIFEST_VERIFY_RC_ZERO_REQUIRED=true",
    "DURABLE_INDEX_OR_POINTER_REQUIRED=true",
    "MERGE_POST_PR_CLOSEOUTS_INCLUDED=true",
    "S3_NOT_CLOSEOUT_COMPLETION=true",
    "NOTION_NOT_AUTHORITY=true",
    "MARKET_DASHBOARD_NOT_AUTHORITY=true",
    "SOURCE_TMP_NOT_CANONICAL=true",
    "CLOSEOUT_DOES_NOT_AUTHORIZE_RUNTIME=true",
)


def _section_2b1() -> str:
    text = PREFLIGHT.read_text(encoding="utf-8")
    return text.split("## 2b.1 Mandatory Durable Closeout Contract v0", 1)[1].split(
        "## 3. Non-authority", 1
    )[0]


def test_section_2b1_present_with_markers() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "## 2b.1 Mandatory Durable Closeout Contract v0" in text
    for marker in MANDATORY_MARKERS:
        assert marker in text


def test_tmp_only_closeout_incomplete() -> None:
    section = _section_2b1()
    assert "TMP_ONLY_CLOSEOUT_INCOMPLETE" in section
    assert "/tmp" in section
    assert "incomplete" in section.lower()


def test_material_closeout_requires_durable_copy_and_readme() -> None:
    section = _section_2b1()
    assert "MATERIAL_CLOSEOUT_REQUIRES_DURABLE_COPY=true" in section
    assert "DURABLE_COPY_README_REQUIRED=true" in section
    assert "DURABLE_COPY_README.md" in section
    assert "outside `/tmp`" in section or "outside /tmp" in section.lower()


def test_manifest_sha256_and_verify_rc_zero_required() -> None:
    section = _section_2b1()
    assert "MANIFEST_SHA256_REQUIRED=true" in section
    assert "MANIFEST_VERIFY_RC_ZERO_REQUIRED=true" in section
    assert "MANIFEST.sha256" in section
    assert "RC=0" in section
    primary = PRIMARY_EVIDENCE.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in primary


def test_durable_index_or_pointer_required() -> None:
    section = _section_2b1()
    assert "DURABLE_INDEX_OR_POINTER_REQUIRED=true" in section
    assert "index" in section.lower() or "pointer" in section.lower()


def test_merge_post_pr_closeouts_included() -> None:
    section = _section_2b1()
    assert "MERGE_POST_PR_CLOSEOUTS_INCLUDED=true" in section
    assert "merge" in section.lower()
    assert "MERGE_CLOSEOUT" in section or "merge closeout" in section.lower()


def test_closeout_owner_pattern_not_single_hardcoded_timestamp_only() -> None:
    section = _section_2b1()
    assert (
        "Peak_Trade_runtime_evidence_archive_<id>" in section
        or "Peak_Trade_runtime_evidence_archive_*" in section
    )
    assert "closeout/" in section or "closeout&#47;" in section
    assert "Do **not** hardcode a single" in section or "not** hardcode a single" in section


def test_source_tmp_not_canonical() -> None:
    section = _section_2b1()
    assert "SOURCE_TMP_NOT_CANONICAL=true" in section
    assert (
        "must not be the sole owner" in section.lower()
        or "not be the sole owner" in section.lower()
    )


def test_s3_notion_dashboard_not_closeout_authority() -> None:
    section = _section_2b1()
    assert "S3_NOT_CLOSEOUT_COMPLETION=true" in section
    assert "NOTION_NOT_AUTHORITY=true" in section
    assert "MARKET_DASHBOARD_NOT_AUTHORITY=true" in section


def test_does_not_duplicate_runtime_primary_evidence_section_2a() -> None:
    section = _section_2b1()
    assert "§2a" in section
    assert "does **not** satisfy §2a" in section or "not** satisfy §2a" in section
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "## 2a. Primary evidence retention invariant v0" in text
    assert text.index("## 2a.") < text.index("## 2b.1")


def test_normative_static_only_no_copy_execution() -> None:
    section = _section_2b1()
    assert "MANDATORY_DURABLE_CLOSEOUT_DOCS_TESTS_ONLY=true" in section
    assert "does **not** execute copy" in section or "not** execute copy" in section.lower()


def test_taxonomy_crosslinks_section_2b1() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "§2b.1 mandatory durable closeout" in text
    assert "merge_closeout" in text
    assert PREFLIGHT.name in text


def test_owner_crosslinks() -> None:
    owner = Path(__file__).read_text(encoding="utf-8")
    assert PLANNING_RETENTION_TESTS.name in owner


def test_adjacent_section_ordering() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert text.index("## 2b. Planning artifact durable retention v0") < text.index(
        "## 2b.1 Mandatory Durable Closeout Contract v0"
    )
    assert text.index("## 2b.1 Mandatory Durable Closeout Contract v0") < text.index(
        "## 2b.2 Closeout Enforcement Planning Contract v0"
    )
    assert text.index("## 2b.2 Closeout Enforcement Planning Contract v0") < text.index(
        "## 3. Non-authority"
    )


def test_evidence_durable_closeout_retention_rc_v0_slice_er1_closeout_guard_crosslink_v0() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    start = text.find(ER_RELEASE_RC_INDEX_HEADING)
    assert start != -1, "missing Evidence Durable Closeout Retention RC v0 index section"
    section = text[start : start + 8000]
    collapsed = text.lower()

    assert "EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0" in section
    assert "SLICE-ER-1" in section
    assert "SLICE-ER-2" in section
    assert THIS_MODULE in section
    assert PRIMARY_EVIDENCE_INVARIANT_TESTS.name in section
    assert "docs/tests/tooling-only" in section
    assert "RETENTION_ENFORCEMENT_ACTIVATED=false" in text
    assert "PRE_FLIGHT_BLOCKED_LIFTED=false" in text
    assert "no parallel" in collapsed
    assert "NO_RUNTIME=true" in text
    assert "WORKFLOW_DISPATCH_EXECUTED=false" in text
