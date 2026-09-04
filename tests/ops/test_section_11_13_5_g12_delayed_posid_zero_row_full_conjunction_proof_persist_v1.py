"""Persist-lock for the delayed G12 conjunction contract. Offline. No GET."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    G12_STATUS,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = REPO_ROOT / "docs/ops/specs/G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1.md"
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
HEADING = "### 11.13.5 G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"


def test_runbook_slice_keeps_g12_open() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(HEADING)
    end = text.find(LADDER_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={OWNER_GO}" in section
    assert f"THIS_SLICE={THIS_SLICE}" in section
    assert f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
    assert f"G12_STATUS={G12_STATUS}" in section
    assert "TARGET_POSITION_ZERO_PROVEN=false" in section
    assert "LIVE_FLATTEN_PROVABILITY_PROVEN=false" in section
    assert "DELAYED_ZERO_DOES_NOT_IMPLY_LIVE_FLATTEN_PROVEN=true" in section
    assert "EMPTY_DATA_IS_ZERO=false" in section
    assert "GET_PERFORMED_THIS_PERSIST=false" in section
    assert "POST_PERFORMED=false" in section
    assert f"NEXT_OWNER_GO_REQUIRED={NEXT_OWNER_GO_REQUIRED}" in section
    assert "PR_6252_TEXT_REWRITTEN=false" in section
    assert "CHOICE_B_EVALUATOR_REWRITTEN=false" in section


def test_spec_and_mot_navigation_exist() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1" in spec
    assert "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN" in spec
    mot = MOT.read_text(encoding="utf-8")
    assert "G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT" in mot
    assert "G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT_V1.md" in mot
