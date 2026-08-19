"""Docs/contract checks for Master Runbook §4.11 (FND-005) live-overrides.

Read-only documentation contract. Does not authorize Live, Testnet,
Canary execute, funding, orders, overlay apply, or COVER_USDC
instantiation. Does not re-enable apply. Does not re-test loader/writer
runtime behavior owned elsewhere.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"
AUTO_TOML = REPO_ROOT / "config" / "live_overrides" / "auto.toml"
PEAK_CONFIG = REPO_ROOT / "src" / "core" / "peak_config.py"
PROMOTION_ENGINE = REPO_ROOT / "src" / "governance" / "promotion_loop" / "engine.py"

SECTION_4_11_HEADING = "## 4.11 Live-overrides apply fail-closed binding (FND-005)"
SECTION_4_12_CANON_HEADING = "## 4.12 Canonical Experiment Identity non-equivalence (FND-010)"
DIRTY_SECTION_4_10_FND005_HEADING = "## 4.10 Live-overrides apply fail-closed binding (FND-005)"

REQUIRED_NON_EQUIVALENCE = (
    "COMMENT_CLAIM_APPLY != RUNTIME_APPLY",
    "LIVE_OVERRIDES_AUTO_TOML != LIVE_CONFIG_AUTHORITY",
    "LIVE_OVERRIDES_AUTO_TOML != LIVE_UNLOCK",
    "LIVE_OVERRIDES_AUTO_TOML != ENABLED",
    "LIVE_OVERRIDES_AUTO_TOML != ARMED",
    "LIVE_OVERRIDES_AUTO_TOML != ORDER_SUBMIT",
    "LIVE_OVERRIDES_AUTO_TOML != RISK_LIMIT_INCREASE",
    "LOAD_CONFIG_WITH_LIVE_OVERRIDES == LOAD_CONFIG",
    "APPLY_PROPOSALS_TO_LIVE_OVERRIDES == NONE",
    "FORCE_APPLY_OVERRIDES != APPLY_AUTHORIZATION",
    "PROMOTION_LOOP_PROPOSAL_ARTIFACTS != LIVE_OVERLAY_WRITE",
    "LEFTOVER_OVERRIDE_PARSER != RUNTIME_MERGE",
    "BOUNDED_LIVE_TOML != LIVE_OVERRIDE_AUTO_TOML",
    "SELF_LEARNING != SELF_AUTHORIZING",
    "CODE_EXISTS != RUNTIME_AUTHORITY",
)

HEADER_AUTHORITY_FLAGS = (
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    "PRODUCTIVE_CODE_CHANGED=false",
    "APPLY_REENABLED=false",
    "AUTHORITY_EXPANDED=false",
    "LIVE_OVERRIDE_APPLY_ACTIVE=false",
    "LOAD_CONFIG_WITH_LIVE_OVERRIDES_MERGES=false",
    "APPLY_PROPOSALS_TO_LIVE_OVERRIDES_WRITES=false",
    "FORCE_APPLY_OVERRIDES_HAS_EFFECT=false",
    "LIVE_OVERRIDE_HAS_RUNTIME_AUTHORITY=false",
    "LIVE_OVERRIDE_HAS_LIVE_AUTHORITY=false",
    "LIVE_OVERRIDE_HAS_ORDER_AUTHORITY=false",
    "LIVE_OVERRIDE_HAS_AUTHORIZATION_AUTHORITY=false",
    "LIVE_OVERRIDE_CAN_UNLOCK_LIVE=false",
    "LIVE_OVERRIDE_CAN_SET_ENABLED=false",
    "LIVE_OVERRIDE_CAN_SET_ARMED=false",
    "LIVE_OVERRIDE_CAN_SUBMIT_ORDER=false",
    "LIVE_OVERRIDE_CAN_INCREASE_RISK_OR_EXPOSURE=false",
    "LIVE_OVERRIDE_CAN_BYPASS_FAIL_CLOSED_GATES=false",
    "SELF_LEARNING_EQUALS_SELF_AUTHORIZING=false",
    "COVER_USDC=UNINSTANTIATED",
    "NUMERIC_FUNDING_AMOUNT=NONE",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
    "GENERAL_LIVE_UNLOCKED=false",
)

STANDING_FLAGS = (
    "LIVE_OVERRIDE_HAS_RUNTIME_AUTHORITY=false",
    "LIVE_OVERRIDE_APPLY_ACTIVE=false",
    "LIVE_OVERRIDE_CAN_UNLOCK_LIVE=false",
    "LIVE_OVERRIDE_CAN_SET_ENABLED=false",
    "LIVE_OVERRIDE_CAN_SET_ARMED=false",
    "LIVE_OVERRIDE_CAN_SUBMIT_ORDER=false",
    "LIVE_OVERRIDE_CAN_INCREASE_RISK_OR_EXPOSURE=false",
    "LIVE_OVERRIDE_CAN_BYPASS_FAIL_CLOSED_GATES=false",
    "APPLY_REENABLED=false",
    "SELF_LEARNING_SELF_AUTHORIZING=false",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
)

NAMED_SURFACES = (
    "SURFACE_ID=LO-01-AUTO-TOML-HEADER",
    "SURFACE_ID=LO-02-LEGACY-OVERLAY-LOADER",
    "SURFACE_ID=LO-03-LEGACY-OVERLAY-WRITER",
    "SURFACE_ID=LO-04-HISTORICAL-INTEGRATION-DOC",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _fold(text: str) -> str:
    return " ".join(text.split())


def _section_4_11(text: str) -> str:
    start = text.find(SECTION_4_11_HEADING)
    assert start >= 0, "missing §4.11 heading"
    end = text.find("\n## 4.12 ", start)
    assert end > start, "missing §4.12 boundary after §4.11"
    return text[start:end]


def _header(section: str) -> str:
    end = section.find("### 4.11.1 Proven surfaces and behavior")
    assert end > 0, "missing §4.11.1 boundary"
    return section[:end]


def _proven_surfaces(section: str) -> str:
    start = section.find("### 4.11.1 Proven surfaces and behavior")
    assert start >= 0, "missing §4.11.1 heading"
    end = section.find("### 4.11.2 Mandatory non-equivalence", start)
    assert end > start, "missing §4.11.2 boundary after §4.11.1"
    return section[start:end]


def _non_equivalence(section: str) -> str:
    start = section.find("### 4.11.2 Mandatory non-equivalence")
    assert start >= 0, "missing §4.11.2 heading"
    end = section.find("### 4.11.3 Standing fail-closed binding", start)
    assert end > start, "missing §4.11.3 boundary after §4.11.2"
    return section[start:end]


def _standing(section: str) -> str:
    start = section.find("### 4.11.3 Standing fail-closed binding")
    assert start >= 0, "missing §4.11.3 heading"
    return section[start:]


def test_section_4_11_heading_is_fnd_005_canon_anchor() -> None:
    text = _read(MASTER_RUNBOOK)
    assert SECTION_4_11_HEADING in text
    assert SECTION_4_12_CANON_HEADING in text
    assert DIRTY_SECTION_4_10_FND005_HEADING not in text


def test_section_4_11_parser_stops_before_section_4_12() -> None:
    text = _read(MASTER_RUNBOOK)
    section = _section_4_11(text)
    assert section.startswith(SECTION_4_11_HEADING)
    assert SECTION_4_12_CANON_HEADING not in section
    assert "FND_010_ID=FND-010" not in section
    assert "SWEEP_ID != CANONICAL_EXPERIMENT_IDENTITY" not in section
    assert "FND_016_STATUS=" not in section
    assert "FND_016_ID=" not in section
    assert "§4.9.7" not in section
    assert DIRTY_SECTION_4_10_FND005_HEADING not in section


def test_section_4_11_fnd_005_is_resolved_docs_only() -> None:
    header = _header(_section_4_11(_read(MASTER_RUNBOOK)))
    assert "FND_005_ID=FND-005" in header
    assert "FND_005_STATUS=RESOLVED_DOCS_ONLY" in header
    assert "FND_005_RESOLUTION=DOCS_ONLY_FAIL_CLOSED_NON_AUTHORITY_BINDING" in header
    status_lines = [
        line.strip() for line in header.splitlines() if line.strip().startswith("FND_005_STATUS=")
    ]
    assert status_lines == ["FND_005_STATUS=RESOLVED_DOCS_ONLY"]


def test_section_4_11_header_authority_flags_remain_fail_closed() -> None:
    header = _header(_section_4_11(_read(MASTER_RUNBOOK)))
    for flag in HEADER_AUTHORITY_FLAGS:
        assert flag in header, flag
    assert "LIVE_OVERRIDE_APPLY_ACTIVE=true" not in header
    assert "LOAD_CONFIG_WITH_LIVE_OVERRIDES_MERGES=true" not in header
    assert "APPLY_PROPOSALS_TO_LIVE_OVERRIDES_WRITES=true" not in header
    assert "APPLY_REENABLED=true" not in header
    assert "AUTHORITY_EXPANDED=true" not in header
    assert "LIVE_AUTHORIZED=true" not in header
    assert "TESTNET_AUTHORIZED=true" not in header
    assert "FND_016_INCLUDED=false" in header
    assert "FND_004_INCLUDED=false" in header
    assert "FND_010_INCLUDED=false" in header


def test_section_4_11_non_equivalence_rules() -> None:
    block = _non_equivalence(_section_4_11(_read(MASTER_RUNBOOK)))
    for rule in REQUIRED_NON_EQUIVALENCE:
        assert rule in block, rule


def test_section_4_11_standing_flags_forbid_apply_and_runtime_authority() -> None:
    standing = _standing(_section_4_11(_read(MASTER_RUNBOOK)))
    folded = _fold(standing)
    for flag in STANDING_FLAGS:
        assert flag in standing, flag
    assert "LIVE_OVERRIDE_APPLY_ACTIVE=true" not in standing
    assert "APPLY_REENABLED=true" not in standing
    assert "This subsection is not a Live unlock" in folded
    assert "not an apply re-enable" in folded


def test_section_4_11_named_surfaces_lo01_to_lo04_remain_non_authorizing() -> None:
    standing = _standing(_section_4_11(_read(MASTER_RUNBOOK)))
    for surface in NAMED_SURFACES:
        assert surface in standing, surface
    assert "FILE=config/live_overrides/auto.toml" in standing
    assert "ROLE=SUPERSEDED_FAIL_CLOSED_HEADER" in standing
    assert "APPLIED_AT_RUNTIME=false" in standing
    assert "SYMBOL=load_config_with_live_overrides" in standing
    assert "ROLE=PERMANENTLY_FAIL_CLOSED_BASE_CONFIG_ONLY" in standing
    assert "MERGES_OVERLAY=false" in standing
    assert "SYMBOL=apply_proposals_to_live_overrides" in standing
    assert "ROLE=PERMANENTLY_FAIL_CLOSED_NON_WRITER" in standing
    assert "WRITES_OVERRIDE_FILE=false" in standing
    assert "FILE=docs/LIVE_OVERRIDES_CONFIG_INTEGRATION.md" in standing
    assert "ROLE=HISTORICAL_SUPERSEDED_NON_SSOT" in standing
    assert "AUTHORITY=NONE" in standing


def test_section_4_11_proven_surfaces_are_not_apply_or_runtime_authority() -> None:
    section = _section_4_11(_read(MASTER_RUNBOOK))
    folded = _fold(section)
    proven = _fold(_proven_surfaces(section))
    assert "returns `load_config(path)` only." in proven
    assert "always returns `None` and never" in proven
    assert "The empty `[auto_applied]` table is path-compatibility only." in proven
    assert "That description is **SUPERSEDED**." in folded
    assert "Canonical owner for this finding is this subsection" in folded
    assert "does **not** authorize Live, Testnet, funding, orders," in folded
    assert "Canary execute, apply, re-enable, or unlock." in folded
    assert "must not be read as current apply semantics." in folded


def test_auto_toml_header_is_superseded_fail_closed_for_section_4_11() -> None:
    header = _read(AUTO_TOML)
    table_start = header.rfind("[auto_applied]")
    assert table_start > 0
    comments = header[:table_start]
    assert "SUPERSEDED" in comments
    assert "FAIL-CLOSED" in comments
    assert "§4.11" in comments
    assert "§4.10" not in comments
    assert "FND-016" not in comments
    assert "§4.9.7" not in comments
    assert "not applied" in comments.lower() or "returns base config only" in comments
    assert "wird NUR in live-ähnlichen Umgebungen" not in comments
    assert "eingemischt" not in comments
    payload_lines = [
        ln
        for ln in header.splitlines()
        if ln.strip() and not ln.lstrip().startswith("#") and ln.strip() != "[auto_applied]"
    ]
    assert header[table_start:].strip() == "[auto_applied]"
    assert payload_lines == []


def test_named_python_surfaces_retain_fail_closed_comments_without_finding_id() -> None:
    peak = _read(PEAK_CONFIG)
    engine = _read(PROMOTION_ENGINE)
    assert "permanently fail-closed" in peak
    assert "Permanently fail-closed" in engine
    assert "FND-016" not in peak
    assert "FND-016" not in engine
    assert "§4.9.7" not in peak
    assert "§4.9.7" not in engine
