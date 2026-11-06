"""Docs/contract checks for Master Runbook §4.12 (FND-010) identity.

Read-only documentation contract. Does not authorize Live, Testnet,
Canary execute, funding, orders, overlay apply, or COVER_USDC
instantiation. Does not re-test identity runtime flags or apply-writer
behavior owned elsewhere.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "canonical" / "PEAK_TRADE_MASTER_RUNBOOK.md"

SECTION_4_12_HEADING = "## 4.12 Canonical Experiment Identity non-equivalence (FND-010)"
SECTION_4_13_CANON_HEADING = "## 4.13 Phase-17 LIVE-unimplemented header superseded (FND-015)"
DIRTY_SECTION_4_12_HEADING = (
    "## 4.12 Legacy-sweep identifiers non-canonical vs Canonical Experiment Identity (FND-010)"
)
DIRTY_SECTION_4_13_FND012_HEADING = (
    "## 4.13 Untracked OKX Europe fee-page YAML dumps are non-SSOT (FND-012)"
)

REQUIRED_NON_EQUIVALENCE = (
    "SWEEP_ID != CANONICAL_EXPERIMENT_IDENTITY",
    "RUN_ID != CANONICAL_EXPERIMENT_IDENTITY",
    "SWEEP_NAME != CANONICAL_EXPERIMENT_IDENTITY",
    "RESEARCH_PLAYGROUND_NAME != CANONICAL_EXPERIMENT_IDENTITY",
    "TOPN_SWEEP_LABEL != CANONICAL_EXPERIMENT_IDENTITY",
    "LEGACY_IDENTIFIER_PERSISTENCE != CANONICAL_EXPERIMENT_IDENTITY",
    "LEGACY_IDENTIFIER_EXPORT != CANONICAL_EXPERIMENT_IDENTITY",
    "LEGACY_IDENTIFIER_SORT != CANONICAL_EXPERIMENT_IDENTITY",
    "PACKAGE_N_EXPERIMENT_ID != PHASE1_COMPLETE_IDENTITY",
    "ADMITTED != PROMOTED",
    "I16_ASSESSMENT_CONSUMABLE != APPLY",
    "SWEEP_TOPN_EXPORT != RUNTIME_CONFIG",
    "CODE_EXISTS != RUNTIME_AUTHORITY",
)

DROPPED_DIRTY_STRINGS = (
    "LEGACY_SWEEP_IDENTITY != CANONICAL_EXPERIMENT_IDENTITY",
    "SWEEP_RUN_ID != EXPERIMENT_ID",
    "LEGACY_SELECTION != PROMOTION_AUTHORITY",
    "LEGACY_EXPORT != DEPLOYMENT",
    "RESEARCH_OUTPUT != RUNTIME_CONFIG",
    "OFFLINE_EVALUATION != LIVE_AUTHORITY",
    "FND_010_CLASS=B",
    "SURFACE_ID=LS-01-RESEARCH-PLAYGROUND",
)

HEADER_AUTHORITY_FLAGS = (
    "RUNTIME_AUTHORIZATION_EFFECT=NONE",
    "PRODUCTIVE_CODE_CHANGED=false",
    "AUTHORITY_EXPANDED=false",
    "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_RUNTIME_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_LIVE_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_ORDER_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_LOADER_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_CONFIG_APPLY_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_AUTHORIZATION_AUTHORITY=false",
    "PROMOTION_APPLY_ALLOWED=false",
    "ADMISSION_AUTHORITY=RESEARCH_EVIDENCE_PARENT_ONLY",
    "PROMOTION_AUTHORITY=NONE",
    "TOPN_SWEEP_EXPORT_IS_RESEARCH_ARTIFACT=true",
    "COVER_USDC=UNINSTANTIATED",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
)

STANDING_FLAGS = (
    "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_RUNTIME_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_LIVE_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_ORDER_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_LOADER_AUTHORITY=false",
    "LEGACY_SWEEP_IDENTIFIER_HAS_CONFIG_APPLY_AUTHORITY=false",
    "PROMOTION_APPLY_ALLOWED=false",
    "LIVE_AUTHORIZED=false",
    "FUNDING_AUTHORIZED=false",
    "ORDER_SUBMIT_AUTHORIZED=false",
    "CANARY_EXECUTE_AUTHORIZED=false",
    "TESTNET_AUTHORIZED=false",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical path: {path}"
    return path.read_text(encoding="utf-8")


def _fold(text: str) -> str:
    return " ".join(text.split())


def _section_4_12(text: str) -> str:
    start = text.find(SECTION_4_12_HEADING)
    assert start >= 0, "missing §4.12 heading"
    end = text.find("\n## 4.13 ", start)
    assert end > start, "missing §4.13 boundary after §4.12"
    return text[start:end]


def _header(section: str) -> str:
    end = section.find("### 4.12.1 Proven surfaces and identity contract")
    assert end > 0, "missing §4.12.1 boundary"
    return section[:end]


def _proven_surfaces(section: str) -> str:
    start = section.find("### 4.12.1 Proven surfaces and identity contract")
    assert start >= 0, "missing §4.12.1 heading"
    end = section.find("### 4.12.2 Mandatory non-equivalence", start)
    assert end > start, "missing §4.12.2 boundary after §4.12.1"
    return section[start:end]


def _non_equivalence(section: str) -> str:
    start = section.find("### 4.12.2 Mandatory non-equivalence")
    assert start >= 0, "missing §4.12.2 heading"
    end = section.find("### 4.12.3 Standing fail-closed binding", start)
    assert end > start, "missing §4.12.3 boundary after §4.12.2"
    return section[start:end]


def _standing(section: str) -> str:
    start = section.find("### 4.12.3 Standing fail-closed binding")
    assert start >= 0, "missing §4.12.3 heading"
    return section[start:]


def test_section_4_12_heading_is_fnd_010_canon_anchor() -> None:
    text = _read(MASTER_RUNBOOK)
    assert SECTION_4_12_HEADING in text
    assert SECTION_4_13_CANON_HEADING in text
    assert DIRTY_SECTION_4_12_HEADING not in text
    assert DIRTY_SECTION_4_13_FND012_HEADING not in text


def test_section_4_12_parser_stops_before_section_4_13_fnd_015() -> None:
    text = _read(MASTER_RUNBOOK)
    section = _section_4_12(text)
    assert section.startswith(SECTION_4_12_HEADING)
    assert SECTION_4_13_CANON_HEADING not in section
    assert "FND_015_ID=FND-015" not in section
    assert "PHASE_17_LIVE_UNIMPLEMENTED_HEADER=SUPERSEDED" not in section
    assert DIRTY_SECTION_4_13_FND012_HEADING not in section
    assert "FND_012_STATUS=" not in section
    assert "FND_016_STATUS=" not in section
    assert "FND_016_ID=" not in section
    assert "§4.9.7" not in section
    assert DIRTY_SECTION_4_12_HEADING not in section


def test_section_4_12_fnd_010_is_resolved_docs_only() -> None:
    header = _header(_section_4_12(_read(MASTER_RUNBOOK)))
    assert "FND_010_ID=FND-010" in header
    assert "FND_010_STATUS=RESOLVED_DOCS_ONLY" in header
    assert "FND_010_RESOLUTION=DOCS_ONLY_NON_EQUIVALENCE_BINDING" in header
    status_lines = [
        line.strip() for line in header.splitlines() if line.strip().startswith("FND_010_STATUS=")
    ]
    assert status_lines == ["FND_010_STATUS=RESOLVED_DOCS_ONLY"]


def test_section_4_12_header_authority_flags_remain_fail_closed() -> None:
    header = _header(_section_4_12(_read(MASTER_RUNBOOK)))
    for flag in HEADER_AUTHORITY_FLAGS:
        assert flag in header, flag
    assert "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=true" not in header
    assert "LEGACY_SWEEP_IDENTIFIER_HAS_RUNTIME_AUTHORITY=true" not in header
    assert "PROMOTION_APPLY_ALLOWED=true" not in header
    assert "AUTHORITY_EXPANDED=true" not in header
    assert "LIVE_AUTHORIZED=true" not in header
    assert "TESTNET_AUTHORIZED=true" not in header
    assert "FND_016_INCLUDED=false" in header
    assert "FND_012_INCLUDED=false" in header
    assert "FND_004_INCLUDED=false" in header
    assert "FND_005_INCLUDED=false" in header


def test_section_4_12_non_equivalence_rules() -> None:
    block = _non_equivalence(_section_4_12(_read(MASTER_RUNBOOK)))
    for rule in REQUIRED_NON_EQUIVALENCE:
        assert rule in block, rule
    assert "SWEEP_ID != CANONICAL_EXPERIMENT_IDENTITY" in block
    for dropped in DROPPED_DIRTY_STRINGS:
        assert dropped not in block


def test_section_4_12_standing_flags_forbid_runtime_and_apply_authority() -> None:
    standing = _standing(_section_4_12(_read(MASTER_RUNBOOK)))
    folded = _fold(standing)
    for flag in STANDING_FLAGS:
        assert flag in standing, flag
    assert "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=true" not in standing
    assert "LEGACY_SWEEP_IDENTIFIER_HAS_RUNTIME_AUTHORITY=true" not in standing
    assert "PROMOTION_APPLY_ALLOWED=true" not in standing
    assert "This subsection is not a Live unlock" in folded
    assert "not an apply re-enable" in folded
    assert "FND-012 and FND-016 are not bound here." in folded


def test_section_4_12_proven_surfaces_are_identity_not_runtime_authority() -> None:
    section = _section_4_12(_read(MASTER_RUNBOOK))
    folded = _fold(section)
    proven = _fold(_proven_surfaces(section))
    assert "CODE_OWNER=src/experiments/canonical_experiment_identity_v1.py" in proven
    assert "EXPERIMENT_IDENTITY_HAS_RUNTIME_AUTHORITY=false" in proven
    assert "ADMISSION_AUTHORITY=RESEARCH_EVIDENCE_PARENT_ONLY" in proven
    assert "PROMOTION_AUTHORITY=NONE" in proven
    assert "PROMOTION_APPLY_ALLOWED=false" in proven
    assert "LEGACY_RESEARCH_PLAYGROUND=src/experiments/research_playground.py" in proven
    assert "LEGACY_STRATEGY_SWEEPS=src/experiments/strategy_sweeps.py" in proven
    assert "does **not** authorize Live, Testnet, funding, orders," in folded
    assert "Canary execute, apply, re-enable, or unlock." in folded
    assert "FND-012 and FND-016 are explicitly **not** part of this subsection." in folded
    assert "does **not** create Canonical Experiment Identity." in folded
    assert "`ADMITTED` is not apply" in folded
    assert "this subsection adds identity non-equivalence only." in folded
    assert "Canonical owner for this finding is this subsection" in folded
