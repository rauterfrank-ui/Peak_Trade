"""Offline contract tests for Master V2 Go-Live Blocker Register core doc (v0).

Pins stable read-only anchors in the canonical blocker register without runtime,
broker access, or doc edits.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"

BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
LADDER = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL = SPECS / "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
GATE_STATUS_INDEX = SPECS / "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"

LADDER_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_LADDER.md"
READ_MODEL_NAME = "MASTER_V2_FIRST_LIVE_ENABLEMENT_READINESS_READ_MODEL_V1.md"
GATE_STATUS_INDEX_NAME = "MASTER_V2_FIRST_LIVE_GATE_STATUS_INDEX_V1.md"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing canonical doc: {path}"
    return path.read_text(encoding="utf-8")


def _plain(path: Path) -> str:
    text = _read(path)
    text = text.replace("&#47;", "/")
    return re.sub(r"[`*]", "", text)


def _register_table_row(blocker_id: str) -> str:
    text = _read(BLOCKER_REGISTER)
    for line in text.splitlines():
        if line.startswith(f"| {blocker_id} |"):
            return line
    raise AssertionError(f"missing register table row for {blocker_id}")


def test_go_live_blocker_register_doc_exists_v0() -> None:
    assert BLOCKER_REGISTER.is_file()


def test_glb006_implicit_session_selection_blocked_default_v0() -> None:
    row = _register_table_row("GLB-006")
    assert "Source-bound session selection implicit" in row
    assert "| BLOCKED |" in row

    text = _plain(BLOCKER_REGISTER)
    assert "6.1 GLB-006" in text or "GLB-006 — Binding session selection scope" in text
    assert "implicit selection is STOP" in text
    assert "session_id" in text
    assert "does not satisfy explicit session_id selection" in text


def test_glb014_external_operator_go_no_go_blocked_v0() -> None:
    row = _register_table_row("GLB-014")
    assert "External/operator Go-No-Go owner unclear" in row
    assert "| BLOCKED |" in row
    assert "External/operator authority" in row

    text = _plain(BLOCKER_REGISTER)
    assert "external/operator authority is missing" in text


def test_glb014_authority_route_legibility_crosslink_guard_v1() -> None:
    """GLB014_AUTHORITY_ROUTE_LEGIBILITY_CROSSLINK_GUARD_V1"""
    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.2 GLB-014")[1].split("6.5.3 GLB-016")[0]

    assert "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md" in text
    assert "Authority Route Legibility" in section
    assert "Stage-3 scoped executing approval record" in section
    assert "LB-APR-001" in section
    assert "Owner/Operator naming" in section
    assert "owner/operator naming" in section.lower()
    assert "fail-closed" in section.lower()
    assert "does not close GLB-014" in section
    assert "does not lift preflight" in section
    assert "PREFLIGHT_REMAINS_BLOCKED" not in section or "does not lift preflight" in section
    assert "test_master_v2_decision_authority_map_static_crosslink_contract_v0.py" in text
    assert "Evidence, mapping, FML reflection" in section or "evidence, mapping" in section.lower()
    assert "non-authorizing" in section.lower()
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed


def test_glb016_preflight_packet_reproducibility_crosslink_guard_v1() -> None:
    """GLB016_PREFLIGHT_PACKET_REPRODUCIBILITY_CROSSLINK_GUARD_V1"""
    row = _register_table_row("GLB-016")
    assert "Preflight packet unavailable" in row
    assert "| BLOCKED |" in row

    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.3 GLB-016")[1].split("6.6 GLB-008")[0]

    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "Preflight Packet Reproducibility" in section
    assert "MANIFEST.sha256" in section
    assert "MANIFEST_VERIFY_RC=0" in section
    assert "/tmp" in section
    assert "Reproducible packet" in section
    assert "does not close GLB-016" in section
    assert (
        "does not execute preflight" in section.lower()
        or "does not execute preflight scripts" in section
    )
    assert "fail-closed" in section.lower()
    assert "test_master_v2_decision_authority_map_static_crosslink_contract_v0.py" in text
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed


def test_glb017_incident_abort_route_crosslink_guard_v1() -> None:
    """GLB017_INCIDENT_ABORT_ROUTE_CROSSLINK_GUARD_V1"""
    row = _register_table_row("GLB-017")
    assert "Incident/abort route unclear" in row
    assert "| BLOCKED |" in row

    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.4 GLB-017")[1].split("6.5.5 GLB-018")[0]

    assert "RUNBOOK_BOUNDED_PILOT_INCIDENT_ABORT_TRIAGE_COMPASS.md" in text
    assert "Incident/Abort Route Legibility" in section
    assert "KILL_SWITCH_RUNBOOK.md" in text
    assert "fail-closed" in section.lower()
    assert "does not close GLB-017" in section
    assert "does not execute incident/abort" in section.lower()
    assert "NO_TRADE" in section or "safe stop" in section.lower()
    assert (
        "automatic trading resume" in section.lower()
        or "no automatic trading resume" in section.lower()
    )
    assert "non-authorizing" in section.lower()
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed


def test_glb018_closeout_path_crosslink_guard_v1() -> None:
    """GLB018_CLOSEOUT_PATH_CROSSLINK_GUARD_V1"""
    row = _register_table_row("GLB-018")
    assert "Closeout path missing" in row
    assert "| OPEN |" in row

    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.5 GLB-018")[1].split("6.6 GLB-008")[0]

    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "Closeout Path Legibility" in section
    assert "MANIFEST.sha256" in section
    assert "MANIFEST_VERIFY_RC=0" in section
    assert "/tmp" in section
    assert "Safe end state" in section or "safe end state" in section.lower()
    assert "does not close GLB-018" in section
    assert "does not execute closeout" in section.lower()
    assert "closeout" in section.lower() and "approval" in section.lower()
    assert "fail-closed" in section.lower() or "incomplete closeout" in section.lower()
    assert "non-authorizing" in section.lower()
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed


def test_glb019_event_stream_crosslink_guard_v1() -> None:
    """GLB019_EVENT_STREAM_CROSSLINK_GUARD_V1"""
    row = _register_table_row("GLB-019")
    assert "Event stream missing or inconsistent" in row
    assert "| OPEN |" in row

    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.6 GLB-019")[1].split("6.5.7 GLB-020")[0]

    assert "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md" in text
    assert "Event Stream Legibility" in section
    assert "State transitions" in section or "state transitions" in section.lower()
    assert "Gate / blocker decisions" in section or "gate / blocker" in section.lower()
    assert "fail-closed" in section.lower()
    assert "does not close GLB-019" in section
    assert "does not execute event" in section.lower()
    assert "event" in section.lower() and "approval" in section.lower()
    assert "event" in section.lower() and "promotion" in section.lower()
    assert "non-authorizing" in section.lower()
    assert "correlation" in section.lower()
    assert "§2b.4" in text or "2b.4" in section
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed


def test_glb020_promotion_boundary_crosslink_guard_v1() -> None:
    """GLB020_PROMOTION_BOUNDARY_CROSSLINK_GUARD_V1"""
    row = _register_table_row("GLB-020")
    assert "Promotion would be automatic or PnL-only" in row
    assert "| BLOCKED |" in row

    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.7 GLB-020")[1].split("6.6 GLB-008")[0]

    assert "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md" in text
    assert "Promotion Static Boundary" in section
    assert "live-gated" in section.lower()
    assert "live-authorized" in section.lower()
    assert "explicit" in section.lower()
    assert "fail-closed" in section.lower()
    assert "does not close GLB-020" in section
    assert "does not execute promotion" in section.lower()
    assert "evidence" in section.lower() and "promotion" in section.lower()
    assert "event stream" in section.lower() or "event" in section.lower()
    assert "automatic" in section.lower() or "pnl-only" in section.lower()
    assert "non-authorizing" in section.lower() or "does not authorize promotion" in section.lower()
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed
    assert "PROMOTION_EXECUTED=true" not in collapsed


def test_glb015_repo_docs_not_final_approval_blocked_v0() -> None:
    row = _register_table_row("GLB-015")
    assert "Repo docs treated as approval" in row
    assert "| BLOCKED |" in row
    assert "In-repo doc is used as final approval" in row

    text = _plain(BLOCKER_REGISTER)
    assert "6.5 GLB-015" in text or "GLB-015 — Repo docs, evidence, ledger" in text
    assert "READINESS_EVIDENCE_LEDGER_PASS_BLOCKED_SAFE" in text
    assert "READINESS_GATE_SNAPSHOT_PASS_BLOCKED_SAFE" in text
    assert "triple_lane_primary_evidence=true" in text
    assert "does not close GLB-015 by itself" in text
    assert "does not clear Preflight BLOCKED" in text


def test_glb015_section5_criteria_precedence_crosslink_guard_v1() -> None:
    text = _read(BLOCKER_REGISTER)
    plain = _plain(BLOCKER_REGISTER)
    section = plain.split("6.5.1 GLB-015")[1].split("6.6 GLB-008")[0]

    assert "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md" in text
    assert "Criteria-Block-Precedence" in section
    assert "Final Machine Lines" in section
    assert "non-authorizing" in section.lower()
    assert "Documentation" in section and "Approval" in section
    assert "Evidence" in section and "Authorization" in section
    assert "Static tests" in section or "static tests" in section.lower()
    assert "fail-closed" in section.lower()
    assert "does not close GLB-015 by itself" in section
    assert "test_section5_preflight_gap_owner_map_contract_v0.py" in text
    assert "PREFLIGHT_REMAINS_BLOCKED" in section
    assert "ALL_GAPS_CLOSED" in section
    assert "arming" in section.lower()


def test_no_green_claim_rule_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    assert "7. No-Green Claim Rule" in text
    assert "prevent accidental" in text.lower() and "green" in text.lower()
    assert "Go-Live approved" in text
    assert "live trading authorized" in text
    assert "all gates passed" in text
    assert "external signoff complete" in text
    assert "Closing one blocker does not imply readiness for First Live" in text


def test_repo_tests_and_docs_do_not_implicitly_clear_blockers_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    assert "does not close GLB-010" in text or "does not close GLB-008" in text
    assert "by itself" in text
    assert "not inferred solely from generic repository tests or CI success" in text
    assert (
        "Default posture: blockers are OPEN unless evidence and the correct authority explicitly close or accept them"
        in text
    )


def test_register_distinguishes_evidence_readiness_and_authority_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    assert "make evidence and decision requirements visible" in text
    assert "does not authorize live execution" in text
    assert "external authority" in text
    assert "No state in this table authorizes live trading by itself" in text
    assert "Owner labels in this register are role categories, not approvals" in text


def test_register_preserves_non_authorizing_live_semantics_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    lowered = text.lower()
    assert "non-authorizing" in lowered
    assert "does not mark peak_trade as ready for live trading" in lowered
    assert "no live authorization" in lowered
    assert "no external signoff claim" in lowered


def test_blocker_register_crosslinks_readiness_ladder_and_gate_index_v0() -> None:
    text = _read(BLOCKER_REGISTER)
    assert LADDER_NAME in text
    assert GATE_STATUS_INDEX_NAME in text
    assert "Readiness, gates, and authority:" in text
    assert LADDER.is_file()
    assert GATE_STATUS_INDEX.is_file()


def test_blocker_register_references_read_model_companion_surfaces_v0() -> None:
    text = _read(BLOCKER_REGISTER)
    assert "Decision Authority Map" in text
    assert "Promotion State Machine" in text
    assert READ_MODEL.is_file()


def test_preflight_lift_blocker_decision_record_inactive_section_present_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    assert "6.17 Preflight-Lift Blocker Decision Record" in text
    assert "PREFLIGHT_LIFT_BLOCKER_DECISION_RECORD_INACTIVE=true" in text
    assert "DECISION_RECORD_NO_LIFT=true" in text
    assert "NO_AUTHORITY_CHANGE=true" in text


def test_preflight_lift_blocker_decision_record_q1_q4_confirmations_documented_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    assert "Q1_ACTIVE_HARD_BLOCKERS_REMAIN_BLOCKED=CONFIRMED_BY_OPERATOR_SCOPE_GO" in text
    assert "Q2_DECISION_RECORD_IS_INACTIVE_NO_LIFT=CONFIRMED_BY_OPERATOR_SCOPE_GO" in text
    assert (
        "Q3_BOUNDED_DOCS_TESTS_SLICE_ALLOWED_AFTER_CONFIRM=CONFIRMED_BY_OPERATOR_SCOPE_GO" in text
    )
    assert "Q4_NO_RUNTIME_LIVE_PREFLIGHT_TRUTH_AUTHORITY=CONFIRMED_BY_OPERATOR_SCOPE_GO" in text


def test_preflight_lift_blocker_decision_record_hard_blockers_remain_blocked_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    for marker in (
        "HARD_BLOCKERS_REMAIN_BLOCKED=true",
        "HARD_BLOCKER_COUNT=18",
        "OBS_001_STATUS=BLOCKED",
        "OBS_002_STATUS=BLOCKED",
        "OBS_003_STATUS=BLOCKED",
        "GLB_016_STATUS=BLOCKED",
        "PREFLIGHT_STATUS=BLOCKED",
        "LIVE_STATUS=BLOCKED",
        "ARMING_STATUS=BLOCKED",
        "STRICT_UPSTREAM_REMAINS_BLOCKED=true",
        "STRICT_UPSTREAM_REMAINS_BLOCKED_FOR_PUBLIC_VIEW=true",
        "PROVIDER_AUTHENTIC_MIN_NOTIONAL_SOURCE_FOUND=false",
    ):
        assert marker in text


def test_preflight_lift_blocker_decision_record_no_lift_authority_language_v0() -> None:
    text = _plain(BLOCKER_REGISTER)
    section = text.split("6.17 Preflight-Lift Blocker Decision Record")[1].split(
        "This reflection records"
    )[0]
    assert "PREFLIGHT_LIFT_AUTHORIZED=false" in section
    assert "PREFLIGHT_GATE_LIFTED=false" in section
    assert "PREFLIGHT_REMAINS_BLOCKED=true" in section
    assert "LIVE_AUTHORIZED=false" in section
    assert "READY_FOR_OPERATOR_ARMING=false" in section
    assert "ALL_AUTHORITY_FLAGS_REMAIN_FALSE=true" in section
    marker_lines = [line.strip() for line in section.splitlines() if "=" in line and line.strip()]
    forbidden_markers = (
        "PREFLIGHT_LIFT_READY=true",
        "PREFLIGHT_LIFT_AUTHORIZED=true",
        "LIVE_AUTHORIZED=true",
        "READY_FOR_OPERATOR_ARMING=true",
    )
    for marker in forbidden_markers:
        assert marker not in marker_lines
