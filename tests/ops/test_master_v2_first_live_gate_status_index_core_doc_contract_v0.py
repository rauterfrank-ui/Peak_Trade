"""Offline contract tests for Master V2 First-Live Gate Status Index core doc (v0).

Pins stable read-only anchors in the canonical gate status index without runtime,
broker access, or doc edits.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

GATE_STATUS_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
REPORT_SURFACE = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
DATAFLOW_MAP = SPECS / "MASTER_V2_DATAFLOW_MAP_V1.md"

LADDER_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
REPORT_SURFACE_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
AUTHORITY_MAP_NAME = "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
DATAFLOW_MAP_NAME = "MASTER_V2_DATAFLOW_MAP_V1.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def test_first_live_gate_status_index_doc_exists_v0() -> None:
    assert GATE_STATUS_INDEX.is_file()


def test_gate_status_index_points_to_readiness_ladder_v0() -> None:
    text = _read(GATE_STATUS_INDEX)
    assert LADDER_NAME in text
    assert "Readiness Ladder" in text
    assert LADDER.is_file()
    assert "G1 | Canonical First Live readiness anchor" in text


def test_gate_status_index_points_to_read_model_and_report_surface_v0() -> None:
    text = _read(GATE_STATUS_INDEX)
    assert READ_MODEL_NAME in text
    assert REPORT_SURFACE_NAME in text
    assert READ_MODEL.is_file()
    assert REPORT_SURFACE.is_file()
    assert "G2 | Canonical interpretation grammar availability" in text
    assert "G3 | Canonical report rendering carrier availability" in text


def test_gate_status_index_points_to_decision_authority_map_v0() -> None:
    text = _plain(GATE_STATUS_INDEX)
    assert AUTHORITY_MAP_NAME in _read(GATE_STATUS_INDEX)
    assert AUTHORITY_MAP.is_file()
    assert "G10 | Decision authority legibility for closure handoff" in text
    assert "promotion/readiness visibility" in text
    assert "live authorization" in text
    assert "4.6) G10 authority handoff legibility note" in text


def test_gate_status_index_distinguishes_interpretation_and_authorization_v0() -> None:
    text = _plain(GATE_STATUS_INDEX)
    assert "3) Canonical Status Model" in text
    assert (
        "status is interpretation-state for this index, not runtime-state and not authorization-state"
        in text
    )
    assert "Verified in this index is never equal to live authorized" in text
    assert "required authority" in text
    assert "evidence present" in text


def test_gate_status_index_does_not_claim_go_live_or_live_readiness_v0() -> None:
    text = _plain(GATE_STATUS_INDEX)
    lowered = text.lower()
    assert "non-authorizing" in lowered
    assert "does not grant live permission" in lowered
    assert "does not close gates" in lowered
    assert "This specification authorizes nothing" in text
    assert "Live progression remains separately gated and separately authorized" in text


def test_gate_status_index_preserves_no_implicit_clearance_semantics_v0() -> None:
    text = _plain(GATE_STATUS_INDEX)
    assert "G12 | Non-authorizing boundary lock for gate reporting" in text
    assert "Verified in this index is never equivalent to live authorized" in text
    assert "does not by itself close this gap" in text
    assert "does not claim completeness of material evidence across gates" in text


def test_gate_status_index_crosslinks_dataflow_map_v0() -> None:
    text = _read(GATE_STATUS_INDEX)
    assert DATAFLOW_MAP_NAME in text
    assert DATAFLOW_MAP.is_file()
    assert "G9 | Dataflow consistency for First Live surfaces" in text


def test_gate_status_index_section_nine_cross_references_v0() -> None:
    text = _read(GATE_STATUS_INDEX)
    assert "## 9) Cross-References" in text
    for name in (
        LADDER_NAME,
        READ_MODEL_NAME,
        REPORT_SURFACE_NAME,
        DATAFLOW_MAP_NAME,
        AUTHORITY_MAP_NAME,
    ):
        assert name in text.split("## 9) Cross-References", 1)[1]
