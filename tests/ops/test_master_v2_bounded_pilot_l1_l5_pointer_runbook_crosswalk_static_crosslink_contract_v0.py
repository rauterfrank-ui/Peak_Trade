"""Static crosslink contract tests for Master V2 Bounded Pilot L1–L5 Crosswalk (v0).

Machine-anchors docs-only bounded-pilot pointer/runbook crosswalk governance from
MASTER_V2_BOUNDED_PILOT_L1_L5_POINTER_RUNBOOK_CROSSWALK_V0.md. Verifies
navigation/readiness discipline only without importing runtime modules or
authorizing trading — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

CROSSWALK = SPECS / "MASTER_V2_BOUNDED_PILOT_L1_L5_POINTER_RUNBOOK_CROSSWALK_V0.md"
NAV_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
GATE_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"
GATE_REPORT_SURFACE = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_GATE_STATUS_REPORT_SURFACE_V1.md"
DECISION_AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
PROVENANCE = SPECS / "MASTER_V2_PROVENANCE_REPLAYABILITY_V1.md"
CROSS_GATE_POINTER = (
    SPECS / "MASTER_V2_BOUNDED_PILOT_CROSS_GATE_CANDIDATE_EVIDENCE_BUNDLE_POINTER_CONTRACT_V0.md"
)
CROSS_GATE_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_CROSS_GATE_EVIDENCE_BUNDLE_INDEX_V1.md"

L_LEVEL_POINTER_CONTRACTS: tuple[tuple[str, Path], ...] = (
    ("L1", SPECS / "MASTER_V2_BOUNDED_PILOT_L1_EVIDENCE_POINTER_CONTRACT_V0.md"),
    (
        "L2",
        SPECS / "MASTER_V2_BOUNDED_PILOT_L2_GO_NO_GO_EVIDENCE_POINTER_CONTRACT_V0.md",
    ),
    (
        "L3",
        SPECS / "MASTER_V2_BOUNDED_PILOT_L3_ENTRY_PREREQUISITE_EVIDENCE_POINTER_CONTRACT_V0.md",
    ),
    (
        "L4",
        SPECS / "MASTER_V2_BOUNDED_PILOT_L4_SESSION_FLOW_EVIDENCE_POINTER_CONTRACT_V0.md",
    ),
    (
        "L5",
        SPECS / "MASTER_V2_BOUNDED_PILOT_L5_INCIDENT_SAFE_STOP_EVIDENCE_POINTER_CONTRACT_V0.md",
    ),
)

L_LEVEL_TABLE_MARKERS: tuple[str, ...] = (
    "| L1 — Dry validation |",
    "| L2 — Go / no-go interpretation |",
    "| L3 — Entry contract prerequisites |",
    "| L4 — Candidate session flow |",
    "| L5 — Incident / safe-stop |",
)

GATE_INDEX_SECTION_MARKERS: tuple[str, ...] = (
    "§4.1 L1 pointer record",
    "§4.2 L2 pointer record",
    "§4.3 L3 pointer record",
    "§4.4 L4 pointer record",
    "§4.5 L5 pointer record",
)

GATE_INDEX_ANCHOR_FRAGMENTS: tuple[str, ...] = (
    "-g4)",
    "-g5)",
    "-g6)",
    "-g7)",
    "-g8)",
)

SECTION_8_CROSSLINK_FILENAMES: tuple[str, ...] = tuple(
    path.name for _, path in L_LEVEL_POINTER_CONTRACTS
) + (
    "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md",
    "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md",
)

REFERENCED_RUNBOOKS: tuple[Path, ...] = (
    RUNBOOKS / "RUNBOOK_BOUNDED_PILOT_DRY_VALIDATION.md",
    RUNBOOKS / "RUNBOOK_BOUNDED_PILOT_LIVE_ENTRY.md",
    RUNBOOKS / "RUNBOOK_BOUNDED_REAL_MONEY_PILOT_CANDIDATE_FLOW.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_EXCHANGE_DEGRADED.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_UNEXPECTED_EXPOSURE.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_RECONCILIATION_MISMATCH.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_SESSION_END_MISMATCH.md",
    RUNBOOKS / "RUNBOOK_PILOT_INCIDENT_RESTART_MID_SESSION.md",
)

REFERENCED_SPEC_SUPPORT: tuple[Path, ...] = (
    SPECS / "PILOT_GO_NO_GO_CHECKLIST.md",
    SPECS / "PILOT_GO_NO_GO_OPERATIONAL_SLICE.md",
    SPECS / "BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT.md",
    SPECS / "BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE.md",
    SPECS / "MASTER_V2_FAILURE_TAXONOMY_SAFE_FALLBACKS_V1.md",
)

FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS: tuple[str, ...] = (
    "L1_L5_POINTER_RUNBOOK_CROSSWALK_V1",
    "CANONICAL_L1_L5",
    "CANONICAL_BOUNDED_PILOT_L1_L5",
)

FORBIDDEN_COMPETING_READINESS_GLOBS: tuple[str, ...] = ("*BOUNDED_PILOT*L1*L5*READINESS*",)

_BANNED_STANDALONE_CLAIMS: tuple[str, ...] = (
    "live is authorized",
    "testnet is approved",
    "paper run is approved",
    "shadow run is approved",
    "signoff is complete",
    "gate is passed",
    "blocker is cleared",
    "operator approval can be bypassed",
    "broker execution is approved",
    "exchange execution is approved",
    "runtime is wired",
    "ai can authorize trades",
    "autonomy can authorize trades",
    "crosswalk grants authority",
    "navigation grants authority",
    "this crosswalk authorizes live",
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


def test_bounded_pilot_crosswalk_exists_with_token_and_non_authorizing_posture_v0() -> None:
    assert CROSSWALK.is_file()
    text = _read(CROSSWALK)
    lowered = _lower(CROSSWALK)
    assert (
        "# MASTER V2 — Bounded Pilot L1–L5 Pointer Runbook Crosswalk v0 (Canonical, Read-Only)"
        in text
    )
    assert (
        "docs_token: DOCS_TOKEN_MASTER_V2_BOUNDED_PILOT_L1_L5_POINTER_RUNBOOK_CROSSWALK_V0" in text
    )
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "read path" in lowered
    assert "crosswalk" in lowered
    assert "does not enable testnet, live, bounded-pilot execution" in lowered


def test_bounded_pilot_crosswalk_l1_l5_table_preserves_navigation_only_structure_v0() -> None:
    section = (
        _plain(CROSSWALK)
        .split("## 3) L1–L5 pointer crosswalk table", 1)[1]
        .split("## 4) Gate alignment", 1)[0]
    )
    lowered = section.lower()
    assert "non-proof" in lowered
    assert "does not prove" in lowered
    assert "approval sequence" not in lowered
    assert "operator go" not in lowered
    for marker in L_LEVEL_TABLE_MARKERS:
        assert marker in section, f"missing L-level table row: {marker!r}"
    for level, contract in L_LEVEL_POINTER_CONTRACTS:
        assert contract.name in section, f"missing {level} pointer contract link"
        assert contract.is_file(), contract


def test_bounded_pilot_crosswalk_referenced_pointer_contracts_and_runbooks_exist_v0() -> None:
    text = _read(CROSSWALK)
    for _, contract in L_LEVEL_POINTER_CONTRACTS:
        assert contract.name in text
        assert contract.is_file(), contract
    for runbook in REFERENCED_RUNBOOKS:
        assert runbook.name in text, f"missing runbook crosslink: {runbook.name!r}"
        assert runbook.is_file(), runbook
    for spec in REFERENCED_SPEC_SUPPORT:
        assert spec.name in text, f"missing spec crosslink: {spec.name!r}"
        assert spec.is_file(), spec


def test_bounded_pilot_crosswalk_gate_index_g4_g8_linkage_is_navigation_only_v0() -> None:
    text = _read(CROSSWALK)
    lowered = _lower(CROSSWALK)
    assert GATE_INDEX.name in text
    assert GATE_INDEX.is_file()
    assert "g4–g8" in lowered or "g4-g8" in lowered.replace("–", "-")
    assert "does not close g4–g8" in lowered or "does not close g4-g8" in lowered.replace("–", "-")
    for marker in GATE_INDEX_SECTION_MARKERS:
        assert marker in text, f"missing gate index section marker: {marker!r}"
    gate_section = (
        _plain(CROSSWALK)
        .split("## 4) Gate alignment (navigation only)", 1)[1]
        .split("## 5) Review workflow", 1)[0]
    )
    gate_lowered = gate_section.lower()
    assert "navigation only" in _lower(CROSSWALK)
    assert "partial" in gate_lowered
    assert "gate closure" in gate_lowered or "gate closure or live eligibility" in gate_lowered
    assert "authorizes nothing" in gate_lowered
    assert "G11" in text
    for anchor in GATE_INDEX_ANCHOR_FRAGMENTS:
        assert anchor in text.lower(), f"missing gate index anchor fragment: {anchor!r}"


def test_bounded_pilot_crosswalk_ladder_linkage_does_not_grant_authorization_v0() -> None:
    text = _read(CROSSWALK)
    lowered = _lower(CROSSWALK)
    assert LADDER.name in text
    assert LADDER.is_file()
    assert "ladder visibility" in lowered
    assert "execution permission" in lowered


def test_bounded_pilot_crosswalk_pre_live_navigation_reciprocal_linkage_v0() -> None:
    nav_text = _read(NAV_MODEL)
    assert CROSSWALK.name in nav_text
    assert "| C1a |" in nav_text
    assert "navigation pointer" in nav_text.lower()
    assert "read path only" in nav_text.lower() or "read path" in nav_text.lower()
    crosswalk_gate_section = _plain(CROSSWALK).split("## 4) Gate alignment", 1)[1]
    assert NAV_MODEL.name in crosswalk_gate_section


def test_bounded_pilot_crosswalk_non_goals_reject_evidence_signoff_runtime_v0() -> None:
    section = _plain(CROSSWALK).split("## 6) Non-goals", 1)[1].split("## 7)", 1)[0]
    lowered = section.lower()
    assert "no evidence creation" in lowered or "no evidence" in lowered
    assert "ingestion" in lowered or "validation engine" in lowered
    assert "signoff" in lowered
    assert "runtime" in lowered
    assert "enablement" in lowered
    assert "trading authority" in lowered or "trading" in lowered


def test_bounded_pilot_crosswalk_review_workflow_is_fail_closed_v0() -> None:
    section = (
        _plain(CROSSWALK)
        .split("## 5) Review workflow (safe, fail-closed)", 1)[1]
        .split("## 6) Non-goals", 1)[0]
    )
    lowered = section.lower()
    assert "fail-closed" in lowered
    assert "do not infer permission" in lowered
    assert "blocked" in lowered
    assert PROVENANCE.name in section
    assert READ_MODEL.name in section
    assert PROVENANCE.is_file()
    assert READ_MODEL.is_file()


def test_bounded_pilot_crosswalk_section_eight_crosslinks_and_peer_surfaces_exist_v0() -> None:
    section = _read(CROSSWALK).split("## 8) Cross-references", 1)[1]
    for filename in SECTION_8_CROSSLINK_FILENAMES:
        assert filename in section, f"missing §8 crosslink: {filename!r}"
    for path in (
        GATE_REPORT_SURFACE,
        DECISION_AUTHORITY_MAP,
        CROSS_GATE_POINTER,
        CROSS_GATE_INDEX,
    ):
        assert path.name in _read(CROSSWALK)
        assert path.is_file(), path


def test_bounded_pilot_crosswalk_non_authorizing_constraint_is_explicit_v0() -> None:
    section = _plain(CROSSWALK).split("## 9) Non-authorizing constraint", 1)[1]
    lowered = section.lower()
    assert "authorizes nothing" in lowered
    assert "read path" in lowered
    assert "crosswalk only" in lowered


def test_bounded_pilot_crosswalk_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(CROSSWALK)
    for claim in _BANNED_STANDALONE_CLAIMS:
        assert claim not in lowered, f"forbidden positive claim: {claim!r}"
    for negated in (
        "non-authorizing",
        "does not close g4",
        "does not enable testnet",
        "fail-closed",
        "authorizes nothing",
    ):
        assert negated in lowered


def test_bounded_pilot_crosswalk_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in FORBIDDEN_DUPLICATE_SPEC_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    for pattern in FORBIDDEN_COMPETING_READINESS_GLOBS:
        competing = [
            path
            for path in SPECS.glob(pattern)
            if path != CROSSWALK and "READINESS" in path.name.upper()
        ]
        assert competing == [], f"competing bounded-pilot L1-L5 readiness owners: {competing}"

    crosswalk_matches = list(SPECS.glob("*BOUNDED_PILOT*L1*L5*POINTER*RUNBOOK*CROSSWALK*"))
    assert crosswalk_matches == [CROSSWALK], (
        f"unexpected bounded-pilot L1-L5 crosswalk owner set: {crosswalk_matches}"
    )
