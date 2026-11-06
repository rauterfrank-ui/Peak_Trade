"""Static crosslink contract tests for Master V2 First Live Execution Sequence (v0).

Machine-anchors docs-only First Live execution sequence governance from
MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md. Verifies companion posture to the
Go-Live Roadmap without importing runtime trading modules or authorizing execution
— static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

EXECUTION_SEQUENCE = SPECS / "MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0.md"
ROADMAP = SPECS / "MASTER_V2_GO_LIVE_ROADMAP_V0.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
GATE_STATUS_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"
PROMOTION_SM = SPECS / "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md"
DECISION_AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
SRP_CONTRACT = SPECS / "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md"
BOUNDED_PILOT_ENTRY = RUNBOOKS / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md"
BOUNDED_PILOT_REVIEW = RUNBOOKS / "RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md"

SEQUENCE_OVERVIEW_ROWS: tuple[str, ...] = (
    "| 1 | Confirm repo/readiness surfaces | Read-only confirmation |",
    "| 2 | Collect evidence / PRE_LIVE package | Review package preparation |",
    "| 3 | Select session for SRP/source-bound review | Explicit operator selection only |",
    "| 4 | Review gates/readiness/blockers | Go/No-Go preparation |",
    "| 5 | External/operator Go/No-Go decision | Authority required |",
    "| 6 | Bounded pilot preparation | No execution yet |",
    "| 7 | Preflight / kill criteria confirmation | Fail-closed gate |",
    "| 8 | Bounded pilot execution handoff | Requires separate authority |",
    "| 9 | Closeout / post-pilot review | Review only |",
    "| 10 | Promotion or STOP | Explicit decision only |",
)

STEP_SECTION_HEADINGS: tuple[str, ...] = (
    "## 5. Step 1 — Confirm Repo / Readiness Surfaces",
    "## 6. Step 2 — Collect Evidence / PRE_LIVE Package",
    "## 7. Step 3 — Select Session for SRP / Source-Bound Review",
    "## 8. Step 4 — Review Gates / Readiness / Blockers",
    "## 9. Step 5 — External / Operator Go-No-Go Decision",
    "## 10. Step 6 — Bounded Pilot Preparation",
    "## 11. Step 7 — Preflight / Kill Criteria Confirmation",
    "## 12. Step 8 — Bounded Pilot Execution Handoff",
    "## 13. Step 9 — Closeout / Post-Pilot Review",
    "## 14. Step 10 — Promotion or STOP",
)

STEP_GATE_SUBHEADINGS: tuple[str, ...] = (
    "### Entry Criteria",
    "### Exit Criteria",
    "### Hard STOP",
)

REQUIRED_CROSSLINK_FILENAMES: tuple[str, ...] = (
    "MASTER_V2_GO_LIVE_ROADMAP_V0.md",
    "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md",
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md",
    "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md",
    "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md",
    "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
    "MASTER_V2_SESSION_REVIEW_PACK_CONTRACT_V0.md",
    "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md",
    "RUNBOOK_STARTED_BOUNDED_PILOT_SESSION_REVIEW_V0.md",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "FIRST_LIVE_EXECUTION_SEQUENCE_V1",
    "MASTER_V2_FIRST_LIVE_STAGE_INDEX",
    "CANONICAL_FIRST_LIVE_EXECUTION_SEQUENCE",
    "FIRST_LIVE_EXECUTION_STAGE_MAP",
)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "live is authorized",
    "execution is approved",
    "broker orders are approved",
    "exchange orders are approved",
    "operator review can be bypassed",
    "blockers are cleared",
    "external signoff is complete",
    "external signoff complete",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "registry grants execution",
    "strategy grants execution authority",
    "this sequence authorizes live",
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


def test_first_live_execution_sequence_exists_with_token_and_non_authorizing_posture_v0() -> None:
    assert EXECUTION_SEQUENCE.is_file()
    text = _read(EXECUTION_SEQUENCE)
    lowered = text.lower()
    assert "# Master V2 First Live Execution Sequence V0" in text
    assert "docs_token: DOCS_TOKEN_MASTER_V2_FIRST_LIVE_EXECUTION_SEQUENCE_V0" in text
    assert "scope: docs-only" in text
    assert "non-authorizing" in text
    assert "It does not authorize live trading" in text
    assert "does not authorize live trading" in lowered
    assert "no live authorization" in lowered


def test_first_live_execution_sequence_companion_role_and_roadmap_wins_v0() -> None:
    text = _read(EXECUTION_SEQUENCE)
    section = text.split("## 3. Relationship to the Go-Live Roadmap", 1)[1].split("## 4.", 1)[0]
    lowered = section.lower()
    assert "companion" in lowered
    assert "MASTER_V2_GO_LIVE_ROADMAP_V0.md" in section
    assert "the roadmap wins" in lowered
    assert "does not replace, extend, or re-rank the roadmap" in lowered
    assert "ordered sequence of review and decision activities" in lowered
    assert "parallel stage owner" not in lowered


def test_first_live_execution_sequence_overview_and_step_sections_are_stable_v0() -> None:
    text = _read(EXECUTION_SEQUENCE)
    overview = text.split("## 4. Sequence Overview", 1)[1].split("## 5.", 1)[0]
    assert "| Step | Name | Decision posture |" in overview
    for row in SEQUENCE_OVERVIEW_ROWS:
        assert row in overview, f"missing overview row: {row!r}"

    positions = [text.index(heading) for heading in STEP_SECTION_HEADINGS]
    assert positions == sorted(positions), "numbered step section order drift"

    for heading in STEP_SECTION_HEADINGS:
        section = text.split(heading, 1)[1].split("\n## ", 1)[0]
        for subheading in STEP_GATE_SUBHEADINGS:
            assert subheading in section, f"missing {subheading} under {heading}"


def test_first_live_execution_sequence_preserves_fail_closed_gate_semantics_v0() -> None:
    text = _plain(EXECUTION_SEQUENCE)
    lowered = text.lower()
    assert "fail-closed" in lowered
    assert "explicit operator or external decision" in lowered
    assert "No live authorization" in text
    assert "No order placement" in text
    assert "No external authority completion claim" in text
    assert "Every step is fail-closed" in _read(EXECUTION_SEQUENCE)


def test_first_live_execution_sequence_authority_and_no_live_boundaries_v0() -> None:
    text = _read(EXECUTION_SEQUENCE)
    authority = text.split("## 15. Authority Boundaries", 1)[1].split("## 16.", 1)[0]
    no_live = text.split("## 16. No-Live-Authorization Statement", 1)[1].split("## 17.", 1)[0]
    assert "| Surface | May do | Must not do |" in authority
    assert "Execution sequence | Order review and decisions. | Authorize live trading." in authority
    assert "sequencing and review guidance only" in no_live
    assert "does not authorize live trading" in no_live.lower()
    assert "bypassing Risk, KillSwitch, Execution, or live gates" in no_live


def test_first_live_execution_sequence_glb006_step3_crosslink_present_v0() -> None:
    step3 = _read(EXECUTION_SEQUENCE).split("## 7. Step 3", 1)[1].split("## 8.", 1)[0]
    assert "GLB-006" in step3
    assert "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md" in step3
    assert "navigation and provenance only" in step3.lower()
    assert "does not replace" in step3.lower()
    assert "explicit operator-documented `session_id`" in step3
    assert "session_id" in step3.lower()


def test_first_live_execution_sequence_required_crosslinks_exist_and_targets_present_v0() -> None:
    text = _read(EXECUTION_SEQUENCE)
    for filename in REQUIRED_CROSSLINK_FILENAMES:
        assert filename in text, f"missing crosslink to {filename!r}"

    for path in (
        ROADMAP,
        BLOCKER_REGISTER,
        LADDER,
        READ_MODEL,
        GATE_STATUS_INDEX,
        PROMOTION_SM,
        DECISION_AUTHORITY_MAP,
        SRP_CONTRACT,
        BOUNDED_PILOT_ENTRY,
        BOUNDED_PILOT_REVIEW,
    ):
        assert path.is_file(), path


def test_first_live_execution_sequence_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(EXECUTION_SEQUENCE)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"

    for negated in (
        "does not authorize live trading",
        "no live authorization",
        "no order placement",
        "no external authority completion claim",
        "sequencing and review guidance only",
    ):
        assert negated in lowered


def test_first_live_execution_sequence_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    sequence_matches = list(SPECS.glob("*FIRST_LIVE_EXECUTION_SEQUENCE*"))
    assert sequence_matches == [EXECUTION_SEQUENCE], (
        f"unexpected execution sequence owner set: {sequence_matches}"
    )
