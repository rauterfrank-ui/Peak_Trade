"""Static contract tests for planning artifact durable retention v0 (offline, no runtime)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_OWNER = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
)


def _owner_text() -> str:
    return CANONICAL_OWNER.read_text(encoding="utf-8")


def _section_2b(text: str) -> str:
    start = text.index("## 2b. Planning artifact durable retention v0")
    end = text.index("## 2b.1 Mandatory Durable Closeout Contract v0")
    return text[start:end]


def test_canonical_owner_exists() -> None:
    assert CANONICAL_OWNER.is_file()


def test_planning_artifact_durable_retention_marker_present() -> None:
    assert "PLANNING_ARTIFACT_DURABLE_RETENTION_REQUIRED=true" in _owner_text()


def test_section_2b_exists_adjacent_to_primary_evidence_invariant() -> None:
    text = _owner_text()
    assert "## 2a. Primary evidence retention invariant v0" in text
    assert "## 2b. Planning artifact durable retention v0" in text
    assert text.index("## 2a.") < text.index("## 2b.") < text.index("## 2b.1") < text.index("## 3.")


def test_tmp_is_scratch_not_durable_for_material_artifacts() -> None:
    section = _section_2b(_owner_text())
    assert "/tmp" in section
    assert "not" in section.lower() and "durable" in section.lower()
    assert "scratch" in section.lower() or "staging" in section.lower()
    assert "must **not** remain `/tmp`-only" in section or "not remain `/tmp`-only" in section


def test_durable_archive_planning_path_pattern() -> None:
    section = _section_2b(_owner_text())
    assert "runtime_evidence_archive" in section
    assert "planning/" in section


def test_requires_manifest_sha256_or_checksum_verification() -> None:
    section = _section_2b(_owner_text())
    assert "MANIFEST.sha256" in section
    assert "shasum -a 256 -c" in section
    assert "RC=0" in section


def test_distinguishes_planning_from_runtime_primary_evidence() -> None:
    text = _owner_text()
    section = _section_2b(text)
    assert (
        "Not primary runtime evidence" in section
        or "not** automatically runtime primary evidence" in section
    )
    assert "§2a" in section or "2a" in section
    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in text


def test_notion_and_chat_not_durable_artifact_storage() -> None:
    section = _section_2b(_owner_text())
    assert "Notion" in section
    assert "chat-summary" in section or "chat" in section.lower()


def test_does_not_imply_runtime_testnet_live_authorization() -> None:
    section = _section_2b(_owner_text())
    lowered = section.lower()
    assert "does **not** authorize" in section or "not authorize" in lowered
    for term in ("testnet", "live", "scheduler", "broker"):
        assert term in lowered


def test_preserves_primary_evidence_invariant_marker() -> None:
    text = _owner_text()
    assert "PRIMARY_EVIDENCE_REQUIRED_FOR_EVERY_RUN=true" in text
    assert "## 2a. Primary evidence retention invariant v0" in text
