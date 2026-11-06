"""Offline contract tests for Master V2 First-Live enablement core doc crosslinks (v0).

Pins stable read-only anchors across the canonical readiness ladder, read model,
report surface, dataflow map, decision-authority map, and reuse inventory after
PR #3567 — without runtime, broker access, or doc edits.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
REPORT_SURFACE = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
DATAFLOW_MAP = SPECS / "MASTER_V2_DATAFLOW_MAP_V1.md"
AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
REUSE_INVENTORY = SPECS / "MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md"

READ_MODEL_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
REPORT_SURFACE_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
DATAFLOW_MAP_NAME = "MASTER_V2_DATAFLOW_MAP_V1.md"
AUTHORITY_MAP_NAME = "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"

CLAIM_CLASS_HEADING = "## 6) Claim Discipline"
CLAIM_CLASSES: tuple[str, ...] = (
    "`repo-evidenced`",
    "`documented`",
    "`operator-stated`",
    "`unverified`",
    "`not-claimed`",
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def test_master_v2_first_live_core_docs_exist_v0() -> None:
    for path in (LADDER, READ_MODEL, REPORT_SURFACE, DATAFLOW_MAP, AUTHORITY_MAP, REUSE_INVENTORY):
        assert path.is_file(), path


def test_readiness_ladder_points_to_read_model_and_report_surface_v0() -> None:
    text = _read(LADDER)
    assert READ_MODEL_NAME in text
    assert REPORT_SURFACE_NAME in text
    assert "Companion interpretation layer (read-only, non-authorizing):" in text
    assert "Readiness Read Model v1" in text
    assert "Gate-Status Report Surface v1" in text


def test_read_model_claim_discipline_section_and_classes_v0() -> None:
    text = _read(READ_MODEL)
    assert CLAIM_CLASS_HEADING in text
    for claim_class in CLAIM_CLASSES:
        assert claim_class in text, f"missing claim class {claim_class}"
    assert "do not mix multiple claim classes in one atomic statement" in text
    assert "if evidence is missing, downgrade to `unverified` or `not-claimed`" in text


def test_read_model_remains_non_authorizing_v0() -> None:
    text = _plain(READ_MODEL)
    assert "non-authorizing" in text.lower()
    assert "no live authorization" in text.lower()


def test_report_surface_couples_to_read_model_claim_discipline_v0() -> None:
    text = _plain(REPORT_SURFACE)
    assert READ_MODEL_NAME in _read(REPORT_SURFACE)
    assert "claim hygiene in status narrative MUST follow read model claim discipline" in text
    assert (
        "read model is authoritative for status/claim/evidence/blocker interpretation grammar"
        in text
    )
    assert "does not redefine interpretation semantics from the read model" in text
    assert "does not set gate closure, approval state, or live authority" in text


def test_dataflow_map_hands_off_to_decision_authority_map_after_pr3567_v0() -> None:
    text = _read(DATAFLOW_MAP)
    assert AUTHORITY_MAP_NAME in text
    assert "Canonical decision-authority map" in text
    assert "E2: Decision-authority consolidation handoff" in text
    e2_lines = [
        line for line in text.splitlines() if "E2: Decision-authority consolidation handoff" in line
    ]
    assert len(e2_lines) == 1
    assert "| `explicit` |" in e2_lines[0]
    assert "Dataflow Map -> Decision Authority Map" in text
    assert "duplicate decision-authority mapping" in text


def test_reuse_inventory_materialized_map_owners_not_genuinely_missing_v0() -> None:
    text = _read(REUSE_INVENTORY)
    assert DATAFLOW_MAP_NAME in text
    assert AUTHORITY_MAP_NAME in text
    assert "Materialized higher-order map surfaces (subordinate; reuse pointers only):" in text
    assert "Materialized / rewired (no new parallel map surface required):" in text
    assert "no new dataflow map required; canonical owner is materialized" in text
    assert "no new decision-authority map required; canonical owner is materialized" in text
    genuinely_missing_block = text.split("## 6) Genuinely Missing / Unclear Areas", 1)[1].split(
        "## 7)", 1
    )[0]
    assert DATAFLOW_MAP_NAME not in genuinely_missing_block.split("Materialized / rewired", 1)[0]
    assert AUTHORITY_MAP_NAME not in genuinely_missing_block.split("Materialized / rewired", 1)[0]
    assert "canonical cross-surface dataflow map (docs-only)" not in genuinely_missing_block
    assert "canonical decision-authority map surface (docs-only)" not in genuinely_missing_block


def test_decision_authority_map_is_non_authorizing_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    assert "non-authorizing" in text.lower()
    assert "does not grant live permissions" in text.lower()


def test_core_first_live_docs_do_not_grant_live_authorization_v0() -> None:
    for path in (LADDER, READ_MODEL, REPORT_SURFACE, DATAFLOW_MAP, AUTHORITY_MAP, REUSE_INVENTORY):
        lowered = _plain(path).lower()
        assert "non-authorizing" in lowered or "non authorizing" in lowered, path.name
        assert "live authorization artifact" not in lowered or "must not be used" in lowered, (
            path.name
        )
