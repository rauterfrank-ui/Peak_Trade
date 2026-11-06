"""Docs/contract checks for Master Runbook §4.10 (FND-004) Top-N non-authority.

Read-only documentation contract. Does not authorize Live, Testnet,
Canary execute, funding, orders, overlay apply, or COVER_USDC
instantiation. Does not re-test export/apply runtime behavior owned
elsewhere.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"

SECTION_4_10_HEADING = "## 4.10 Top-N promotion non-authority (FND-004)"
SECTION_4_11_CANON_HEADING = "## 4.11 Live-overrides apply fail-closed binding (FND-005)"
DIRTY_SECTION_4_11_FND004_HEADINGS = (
    "## 4.11 Top-N promotion non-authority (FND-004)",
    "## 4.11 Top-N promotion exporter non-canonical binding (FND-004)",
)

REQUIRED_NON_EQUIVALENCE = (
    "SWEEP_TOPN_EXPORT != RUNTIME_CONFIG",
    "SWEEP_TOPN_EXPORT != CHAMPION_CHALLENGER_SSOT",
    "SWEEP_TOPN_EXPORT != PROMOTION_LOOP_APPLY",
    "SWEEP_TOPN_EXPORT != LIVE_OVERRIDE",
    "SWEEP_TOPN_CANDIDATES != SINGLE_SELECTED_FUTURE",
    "SWEEP_TOPN_PROMOTION != SECTION_4_5_TOP_N_ACTIVE_SET",
    "RESEARCH_RANKING != EXECUTION_AUTHORITY",
    "SELF_LEARNING != SELF_AUTHORIZING",
    "CODE_EXISTS != RUNTIME_AUTHORITY",
    "TOML_EXPORT != AUTO_APPLY",
    "POLICY_CRITIC_CONSULTATION != APPLY",
)

HEADER_AUTHORITY_FLAGS = (
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    "PRODUCTIVE_CODE_CHANGED=false",
    "AUTHORITY_EXPANDED=false",
    "TOPN_PROMOTION_HAS_RUNTIME_AUTHORITY=false",
    "TOPN_PROMOTION_HAS_LIVE_AUTHORITY=false",
    "TOPN_PROMOTION_HAS_TESTNET_AUTHORITY=false",
    "TOPN_PROMOTION_HAS_FUNDING_AUTHORITY=false",
    "TOPN_PROMOTION_HAS_ORDER_AUTHORITY=false",
    "TOPN_PROMOTION_HAS_CANARY_AUTHORITY=false",
    "TOPN_PROMOTION_CAN_AUTO_APPLY=false",
    "TOPN_PROMOTION_CAN_REENABLE=false",
    "TOPN_PROMOTION_CAN_UNLOCK=false",
    "SELF_LEARNING_SELF_AUTHORIZING=false",
    "COVER_USDC=UNINSTANTIATED",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
)

STANDING_FLAGS = (
    "TOPN_PROMOTION_HAS_RUNTIME_AUTHORITY=false",
    "TOPN_PROMOTION_CAN_AUTO_APPLY=false",
    "TOPN_PROMOTION_CAN_REENABLE=false",
    "TOPN_PROMOTION_CAN_UNLOCK=false",
    "SELF_LEARNING_SELF_AUTHORIZING=false",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
)

DROPPED_DIRTY_STRINGS = (
    "TOP_N_SELECTION != PROMOTION_AUTHORITY",
    "PARALLEL_TOPN_EXPORTER != CANONICAL_CHAMPION_CHALLENGER_SSOT",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _fold(text: str) -> str:
    return " ".join(text.split())


def _section_4_10(text: str) -> str:
    start = text.find(SECTION_4_10_HEADING)
    assert start >= 0, "missing §4.10 heading"
    end = text.find("\n## 4.11 ", start)
    assert end > start, "missing §4.11 boundary after §4.10"
    return text[start:end]


def _header(section: str) -> str:
    end = section.find("### 4.10.1 Proven surfaces and outputs")
    assert end > 0, "missing §4.10.1 boundary"
    return section[:end]


def _proven_surfaces(section: str) -> str:
    start = section.find("### 4.10.1 Proven surfaces and outputs")
    assert start >= 0, "missing §4.10.1 heading"
    end = section.find("### 4.10.2 Mandatory non-equivalence", start)
    assert end > start, "missing §4.10.2 boundary after §4.10.1"
    return section[start:end]


def _non_equivalence(section: str) -> str:
    start = section.find("### 4.10.2 Mandatory non-equivalence")
    assert start >= 0, "missing §4.10.2 heading"
    end = section.find("### 4.10.3 Standing fail-closed binding", start)
    assert end > start, "missing §4.10.3 boundary after §4.10.2"
    return section[start:end]


def _standing(section: str) -> str:
    start = section.find("### 4.10.3 Standing fail-closed binding")
    assert start >= 0, "missing §4.10.3 heading"
    return section[start:]


def test_section_4_10_heading_is_fnd_004_canon_anchor() -> None:
    text = _read(MASTER_RUNBOOK)
    assert SECTION_4_10_HEADING in text
    assert SECTION_4_11_CANON_HEADING in text
    for dirty_heading in DIRTY_SECTION_4_11_FND004_HEADINGS:
        assert dirty_heading not in text


def test_section_4_10_parser_stops_before_section_4_11() -> None:
    text = _read(MASTER_RUNBOOK)
    section = _section_4_10(text)
    assert section.startswith(SECTION_4_10_HEADING)
    assert SECTION_4_11_CANON_HEADING not in section
    assert "FND_005_ID=FND-005" not in section
    assert "LIVE_OVERRIDE_APPLY_ACTIVE" not in section
    assert "FND_005_STATUS=" not in section
    for dirty_heading in DIRTY_SECTION_4_11_FND004_HEADINGS:
        assert dirty_heading not in section


def test_section_4_10_fnd_004_is_resolved_docs_only() -> None:
    header = _header(_section_4_10(_read(MASTER_RUNBOOK)))
    assert "FND_004_ID=FND-004" in header
    assert "FND_004_STATUS=RESOLVED_DOCS_ONLY" in header
    assert "FND_004_RESOLUTION=DOCS_ONLY_NON_AUTHORITY_BINDING" in header
    status_lines = [
        line.strip() for line in header.splitlines() if line.strip().startswith("FND_004_STATUS=")
    ]
    assert status_lines == ["FND_004_STATUS=RESOLVED_DOCS_ONLY"]


def test_section_4_10_header_authority_flags_remain_fail_closed() -> None:
    header = _header(_section_4_10(_read(MASTER_RUNBOOK)))
    for flag in HEADER_AUTHORITY_FLAGS:
        assert flag in header, flag
    assert "TOPN_PROMOTION_HAS_RUNTIME_AUTHORITY=true" not in header
    assert "TOPN_PROMOTION_CAN_AUTO_APPLY=true" not in header
    assert "LIVE_AUTHORIZED=true" not in header
    assert "TESTNET_AUTHORIZED=true" not in header
    assert "AUTHORITY_EXPANDED=true" not in header
    assert "FND_016_INCLUDED=false" in header
    assert "FND_005_INCLUDED=false" in header


def test_section_4_10_non_equivalence_rules() -> None:
    block = _non_equivalence(_section_4_10(_read(MASTER_RUNBOOK)))
    for rule in REQUIRED_NON_EQUIVALENCE:
        assert rule in block, rule
    assert "SWEEP_TOPN_EXPORT != RUNTIME_CONFIG" in block
    for dropped in DROPPED_DIRTY_STRINGS:
        assert dropped not in block


def test_section_4_10_standing_flags_forbid_auto_apply_and_runtime_authority() -> None:
    standing = _standing(_section_4_10(_read(MASTER_RUNBOOK)))
    folded = _fold(standing)
    for flag in STANDING_FLAGS:
        assert flag in standing, flag
    assert "TOPN_PROMOTION_HAS_RUNTIME_AUTHORITY=true" not in standing
    assert "TOPN_PROMOTION_CAN_AUTO_APPLY=true" not in standing
    assert "This subsection is not a Live unlock" in folded
    assert "not an apply re-enable" in folded


def test_section_4_10_export_and_promotion_are_not_runtime_or_apply_authority() -> None:
    section = _section_4_10(_read(MASTER_RUNBOOK))
    folded = _fold(section)
    proven = _fold(_proven_surfaces(section))
    assert "The operator CLI calls `export_top_n` only." in proven
    assert "does **not** write productive configuration" in proven
    assert "does **not** call `apply_proposals_to_live_overrides`" in proven
    assert "is **not** invoked by the operator CLI" in proven
    assert "A Top-N export must not be treated as activation of productive configuration." in folded
    assert "that document is not SSOT" in folded
    assert "does **not** authorize Live, Testnet, funding, orders," in folded
    assert "Canary execute, apply, re-enable, or unlock." in folded
    assert "Canonical owner for this finding is this subsection" in folded
