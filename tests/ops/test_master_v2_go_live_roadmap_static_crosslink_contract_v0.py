"""Static crosslink contract tests for Master V2 Go-Live Roadmap (v0).

Machine-anchors docs-only Go-Live roadmap governance from
MASTER_V2_GO_LIVE_ROADMAP_V0.md. Protects review legibility without importing
runtime trading modules or authorizing execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

ROADMAP = SPECS / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
LEARNING_INVENTORY = SPECS / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
GAP_MAP = SPECS / "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md"
FLAT_PATH_INDEX = SPECS / "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md"
TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
PROMOTION_SM = SPECS / "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
GATE_STATUS_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"
GATE_REPORT_SURFACE = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
DECISION_AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"

STAGE_HEADINGS: tuple[str, ...] = (
    "## 4. Stage 1 — Research / Backtest / Robustness",
    "## 5. Stage 2 — Shadow / Paper Evidence",
    "## 6. Stage 3 — Testnet Evidence",
    "## 7. Stage 4 — Session Review Pack / Source-Bound Review",
    "## 8. Stage 5 — Pre-Live Package / External Decision",
    "## 9. Stage 6 — Bounded Real-Money Pilot",
    "## 10. Stage 7 — Post-Pilot Review / Promotion",
)

STAGE_GATE_SUBHEADINGS: tuple[str, ...] = (
    "### Entry Criteria",
    "### Exit Criteria",
    "### Hard Stops",
)

EXEC_SUMMARY_STAGE_SEQUENCE: tuple[str, ...] = (
    "1. Research / Backtest / Robustness",
    "2. Shadow / Paper Evidence",
    "3. Testnet Evidence",
    "4. Session Review Pack / Source-Bound Review",
    "5. Pre-Live Package / External Decision",
    "6. Bounded Real-Money Pilot",
    "7. Post-Pilot Review / Promotion",
)

REQUIRED_CROSSLINK_FILENAMES: tuple[str, ...] = (
    "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md",
    "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md",
    "MASTER_V2_PAPER_TESTNET_READINESS_GAP_MAP_V0.md",
    "MASTER_V2_OPERATOR_AUDIT_FLAT_PATH_INDEX_V0.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md",
    "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md",
    "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
    "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md",
    "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "GO_LIVE_ROADMAP_V1",
    "MASTER_V2_GO_LIVE_STAGE_INDEX",
    "GO_LIVE_STAGE_INDEX",
    "CANONICAL_GO_LIVE_ROADMAP",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "live is authorized",
    "approved for live trading",
    "strategy is ready for live",
    "external signoff is complete",
    "external signoff complete",
    "broker execution is approved",
    "exchange execution is approved",
    "operator approval is bypassed",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "this roadmap authorizes",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def _lower(path: Path) -> str:
    return _plain(path).lower()


def test_go_live_roadmap_doc_exists_with_token_and_non_authorizing_frontmatter_v0() -> None:
    assert ROADMAP.is_file()
    text = _read(ROADMAP)
    assert "# Master V2 Go-Live Roadmap V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_GO_LIVE_ROADMAP_V0" in text
    assert "scope: docs-only" in text
    assert "non-authorizing" in text
    assert "It does not authorize live trading" in text
    assert "It does not enable live execution" in text


def test_go_live_roadmap_declares_fail_closed_stage_gate_semantics_v0() -> None:
    text = _plain(ROADMAP)
    lowered = text.lower()
    assert "evidence-gated" in lowered
    assert "fail-closed" in lowered
    assert "explicit operator/external decisions" in lowered or "explicit operator" in lowered
    assert "No live authorization" in text
    assert "No external signoff claim" in text
    assert "No strategy readiness claim" in text
    assert "No autonomy readiness claim" in text


def test_go_live_roadmap_executive_summary_stage_sequence_is_stable_v0() -> None:
    text = _read(ROADMAP)
    summary = text.split("## 2. Purpose and Non-Goals", 1)[0]
    positions = [summary.index(stage) for stage in EXEC_SUMMARY_STAGE_SEQUENCE]
    assert positions == sorted(positions), "executive summary stage order drift"


def test_go_live_roadmap_stage_sections_exist_in_order_with_gate_subheadings_v0() -> None:
    text = _read(ROADMAP)
    positions = [text.index(heading) for heading in STAGE_HEADINGS]
    assert positions == sorted(positions), "numbered stage section order drift"

    for heading in STAGE_HEADINGS:
        section = text.split(heading, 1)[1].split("\n## ", 1)[0]
        for subheading in STAGE_GATE_SUBHEADINGS:
            assert subheading in section, f"missing {subheading} under {heading}"


def test_go_live_roadmap_autonomy_crosswalk_links_taxonomy_and_learning_inventory_v0() -> None:
    text = _read(ROADMAP)
    assert "### 3.1 Autonomy stage crosswalk (informative only)" in text
    assert "informative orientation only" in text
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in text
    assert "Autonomy Stage Authority Crosswalk" in text
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in text
    assert "§10" in text or "Stage-7" in text
    assert "AI ≠ authority" in text
    assert "Strategy ≠ authority" in text
    assert TAXONOMY.is_file()
    assert LEARNING_INVENTORY.is_file()


def test_go_live_roadmap_required_crosslinks_exist_and_targets_are_present_v0() -> None:
    text = _read(ROADMAP)
    for filename in REQUIRED_CROSSLINK_FILENAMES:
        assert filename in text, f"missing crosslink to {filename}"

    for path in (
        BLOCKER_REGISTER,
        LEARNING_INVENTORY,
        GAP_MAP,
        FLAT_PATH_INDEX,
        TAXONOMY,
        PROMOTION_SM,
        LADDER,
        READ_MODEL,
        GATE_STATUS_INDEX,
        GATE_REPORT_SURFACE,
        DECISION_AUTHORITY_MAP,
    ):
        assert path.is_file(), path


def test_go_live_roadmap_preserves_authority_boundary_table_v0() -> None:
    text = _plain(ROADMAP)
    assert "| Surface | May do | Must not do |" in text
    assert "Roadmap | Sequence the path to Go-Live. | Authorize live trading." in text
    assert "Tests | Pin expected behavior. | Authorize runtime behavior." in text


def test_go_live_roadmap_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(ROADMAP)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"

    for negated in (
        "does not authorize live trading",
        "no live authorization",
        "no external signoff claim",
        "no strategy readiness claim",
        "no autonomy readiness claim",
        "does not authorize:",
    ):
        assert negated in lowered


def test_go_live_roadmap_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    roadmap_matches = list(SPECS.glob("*GO_LIVE_ROADMAP*"))
    assert roadmap_matches == [ROADMAP], f"unexpected roadmap owner set: {roadmap_matches}"
