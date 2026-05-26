"""Static contract tests for Closeout Enforcement Planning Contract v0 (Preflight §2b.2)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
TAXONOMY = (
    REPO_ROOT / "docs" / "ops" / "specs" / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
)
MANDATORY_CLOSEOUT_TESTS = (
    REPO_ROOT / "tests" / "ops" / "test_mandatory_durable_closeout_contract_v0.py"
)
POST_MERGE_CLOSEOUT = REPO_ROOT / "scripts" / "governance" / "post_merge_closeout.sh"
APPEND_CLOSEOUT_INDEX = REPO_ROOT / "scripts" / "ops" / "append_closeout_index.py"
PRIMARY_EVIDENCE = REPO_ROOT / "scripts" / "ops" / "primary_evidence_retention_v0.py"
DOCS_TRUTH_MAP = REPO_ROOT / "docs" / "ops" / "registry" / "DOCS_TRUTH_MAP.md"

ENFORCEMENT_MARKERS = (
    "CLOSEOUT_ENFORCEMENT_PLANNING_CONTRACT_V0=true",
    "CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true",
    "CLOSEOUT_ENFORCEMENT_NO_COPY_VERIFY_IMPLEMENTATION=true",
    "CLOSEOUT_ENFORCEMENT_NO_ARCHIVE_MUTATION=true",
    "CLOSEOUT_ENFORCEMENT_NO_TMP_DELETE=true",
    "CLOSEOUT_ENFORCEMENT_TMP_ONLY_INCOMPLETE=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_DESTINATION_OUTSIDE_TMP=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_COPY_README=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_SHA256=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_INDEX_OR_POINTER=true",
    "CLOSEOUT_ENFORCEMENT_SOURCE_TMP_NOT_CANONICAL=true",
    "CLOSEOUT_ENFORCEMENT_S3_NOT_COMPLETION=true",
    "CLOSEOUT_ENFORCEMENT_NOTION_NOT_COMPLETION=true",
    "CLOSEOUT_ENFORCEMENT_DASHBOARD_NOT_COMPLETION=true",
    "CLOSEOUT_ENFORCEMENT_POST_MERGE_CLOSEOUT_SH_NOT_COMPLETION=true",
    "CLOSEOUT_ENFORCEMENT_APPEND_CLOSEOUT_INDEX_NOT_CANONICAL_ARCHIVE_INDEX=true",
    "CLOSEOUT_ENFORCEMENT_REQUIRED_BEFORE_REMOTE_IMPLEMENTATION_CHARTER=true",
    "CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true",
    "CLOSEOUT_ENFORCEMENT_DOES_NOT_AUTHORIZE_RUNTIME=true",
)


def _section_2b2() -> str:
    text = PREFLIGHT.read_text(encoding="utf-8")
    return text.split("## 2b.2 Closeout Enforcement Planning Contract v0", 1)[1].split(
        "## 3. Non-authority", 1
    )[0]


def test_section_2b2_present_with_markers() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert "## 2b.2 Closeout Enforcement Planning Contract v0" in text
    for marker in ENFORCEMENT_MARKERS:
        assert marker in text


def test_planning_only_no_copy_verify_or_archive_mutation() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true" in section
    assert "CLOSEOUT_ENFORCEMENT_NO_COPY_VERIFY_IMPLEMENTATION=true" in section
    assert "CLOSEOUT_ENFORCEMENT_NO_ARCHIVE_MUTATION=true" in section
    assert "CLOSEOUT_ENFORCEMENT_NO_TMP_DELETE=true" in section
    assert "does **not** ship copy/verify" in section or "not** ship copy/verify" in section


def test_tmp_only_incomplete_and_durable_destination_outside_tmp() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_TMP_ONLY_INCOMPLETE=true" in section
    assert "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_DESTINATION_OUTSIDE_TMP=true" in section
    assert "/tmp" in section
    assert "Peak_Trade_runtime_evidence_archive" in section


def test_durable_copy_readme_manifest_and_verify_required() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_COPY_README=true" in section
    assert "CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_SHA256=true" in section
    assert "CLOSEOUT_ENFORCEMENT_REQUIRES_MANIFEST_VERIFY_RC_ZERO=true" in section
    assert "DURABLE_COPY_README.md" in section
    assert "MANIFEST.sha256" in section
    assert "RC=0" in section
    primary = PRIMARY_EVIDENCE.read_text(encoding="utf-8")
    assert "verify_manifest_sha256" in primary


def test_durable_index_or_pointer_and_source_tmp_not_canonical() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_REQUIRES_DURABLE_INDEX_OR_POINTER=true" in section
    assert "CLOSEOUT_ENFORCEMENT_SOURCE_TMP_NOT_CANONICAL=true" in section
    assert "not** be deleted before verify" in section or "not be deleted before verify" in section


def test_s3_notion_dashboard_not_completion() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_S3_NOT_COMPLETION=true" in section
    assert "CLOSEOUT_ENFORCEMENT_NOTION_NOT_COMPLETION=true" in section
    assert "CLOSEOUT_ENFORCEMENT_DASHBOARD_NOT_COMPLETION=true" in section


def test_post_merge_closeout_sh_classified_not_completion() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_POST_MERGE_CLOSEOUT_SH_NOT_COMPLETION=true" in section
    assert "post_merge_closeout.sh" in section
    post_merge = POST_MERGE_CLOSEOUT.read_text(encoding="utf-8")
    assert "git fetch" in post_merge or "git pull" in post_merge
    assert "Sync local main" in post_merge or "Sync" in post_merge


def test_append_closeout_index_not_canonical_archive_index() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_APPEND_CLOSEOUT_INDEX_NOT_CANONICAL_ARCHIVE_INDEX=true" in section
    assert "append_closeout_index.py" in section
    assert "index_post_merge_closeouts.jsonl" in section
    append = APPEND_CLOSEOUT_INDEX.read_text(encoding="utf-8")
    assert "index_post_merge_closeouts.jsonl" in append


def test_canonical_archive_closeout_owner_pattern_documented() -> None:
    section = _section_2b2()
    assert "closeout/" in section or "closeout&#47;" in section
    assert "Peak_Trade_runtime_evidence_archive" in section


def test_future_helper_expectations_documented_not_implemented() -> None:
    section = _section_2b2()
    assert "copy-only" in section.lower()
    assert "fail closed" in section.lower()
    assert "does **not** modify" in section or "not** modify" in section
    assert "post_merge_closeout.sh" in section
    assert "append_closeout_index.py" in section


def test_binds_section_2b1_2a_remote_and_s3() -> None:
    section = _section_2b2()
    assert "§2b.1" in section
    assert "§2a" in section
    assert "§6a.0" in section
    assert "§6a.3" in section


def test_gates_remote_charter_and_dry_template() -> None:
    section = _section_2b2()
    assert "CLOSEOUT_ENFORCEMENT_REQUIRED_BEFORE_REMOTE_IMPLEMENTATION_CHARTER=true" in section
    assert "CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true" in section
    assert "CLOSEOUT_ENFORCEMENT_DOES_NOT_AUTHORIZE_RUNTIME=true" in section


def test_relationship_to_section_2b1_no_duplication() -> None:
    section = _section_2b2()
    assert "§2b.1 defines" in section or "§2b.1" in section
    assert "does **not** replace §2b.1" in section or "not** replace §2b.1" in section
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert text.index("## 2b.1 Mandatory Durable Closeout Contract v0") < text.index(
        "## 2b.2 Closeout Enforcement Planning Contract v0"
    )


def test_taxonomy_crosslinks_section_2b2() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "§2b.2 closeout enforcement planning" in text
    assert PREFLIGHT.name in text


def test_taxonomy_6a05_dry_gate_references_section_2b2() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    dry_gate = text.split("#### Dry command template gate (normative)", 1)[1].split(
        "#### Forbidden content", 1
    )[0]
    assert "§2b.2" in dry_gate
    assert "CLOSEOUT_ENFORCEMENT_REVIEW_REQUIRED_BEFORE_DRY_COMMAND_TEMPLATE=true" in dry_gate


def test_preflight_crosslinks_section_2b2_under_non_authority() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    non_authority = text.split("## 3. Non-authority", 1)[1].split("## 3a.", 1)[0]
    assert "§2b.2 Closeout Enforcement Planning Contract v0" in non_authority
    assert "CLOSEOUT_ENFORCEMENT_PLANNING_ONLY=true" in non_authority


def test_docs_truth_map_lists_section_2b2() -> None:
    text = DOCS_TRUTH_MAP.read_text(encoding="utf-8")
    assert "§2b.2" in text
    assert "Closeout Enforcement Planning Contract v0" in text


def test_mandatory_closeout_contract_tests_still_present() -> None:
    assert MANDATORY_CLOSEOUT_TESTS.is_file()
    text = MANDATORY_CLOSEOUT_TESTS.read_text(encoding="utf-8")
    assert "## 2b.1 Mandatory Durable Closeout Contract v0" in text


def test_adjacent_section_ordering() -> None:
    text = PREFLIGHT.read_text(encoding="utf-8")
    assert text.index("## 2b.1 Mandatory Durable Closeout Contract v0") < text.index(
        "## 2b.2 Closeout Enforcement Planning Contract v0"
    )
    assert text.index("## 2b.2 Closeout Enforcement Planning Contract v0") < text.index(
        "## 3. Non-authority"
    )
