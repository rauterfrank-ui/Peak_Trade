"""Static contract tests for Master V2 Decision Authority Map crosslinks (v0).

Machine-anchors existing docs-only authority boundaries across canonical Master V2
and Double Play governance surfaces. Protects review legibility without authorizing
runtime, trading, or gate passage — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
CAPITAL_SLOT_CONTRACT = SPECS / "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PROMOTION_SM = SPECS / "MASTER_V2_PROMOTION_STATE_MACHINE_V1.md"
LEARNING_INVENTORY = SPECS / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"

AUTHORITY_MAP_NAME = "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"
TRADING_LOGIC_MANIFEST_NAME = "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL_NAME = "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
BLOCKER_REGISTER_NAME = "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"

CANONICAL_DECISION_STAGES: tuple[str, ...] = (
    "Universe Selection and Market Eligibility",
    "Doubleplay directional evaluation",
    "Bull specialist contribution",
    "Bear specialist contribution",
    "LONG or SHORT or FLAT aggregation and arbitration",
    "Scope and Capital Envelope determination",
    "downstream Risk and Exposure Cap enforcement",
    "Safety and Kill-Switch veto layer",
    "staged Execution Enablement and promotion blocking",
    "learning, model, and policy change approval boundary",
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


def _register_table_row(blocker_id: str) -> str:
    text = _read(BLOCKER_REGISTER)
    for line in text.splitlines():
        if line.startswith(f"| {blocker_id} |"):
            return line
    raise AssertionError(f"missing register table row for {blocker_id}")


def test_canonical_authority_boundary_docs_exist_v0() -> None:
    for path in (
        AUTHORITY_MAP,
        TRADING_LOGIC_MANIFEST,
        SCOPE_CAPITAL,
        BLOCKER_REGISTER,
        PREFLIGHT_CONTRACT,
    ):
        assert path.is_file(), path


def test_decision_authority_map_master_v2_and_topology_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    lowered = text.lower()
    assert "master v2" in lowered
    assert "decision-authority" in lowered or "decision authority" in lowered
    assert "authority boundaries" in lowered or "authority boundary" in lowered
    assert "non-authorizing" in lowered
    assert "does not grant live permissions" in lowered


def test_decision_authority_map_canonical_stages_present_v0() -> None:
    text = _read(AUTHORITY_MAP)
    for stage in CANONICAL_DECISION_STAGES:
        assert stage in text, f"missing canonical stage: {stage!r}"


def test_decision_authority_map_partial_and_unclear_markers_preserved_v0() -> None:
    text = _read(AUTHORITY_MAP)
    assert "| partial |" in text
    assert "| unclear |" in text
    assert "explicit marking of unclear or missing authority handoffs" in text
    assert "Still open:" in text
    plain = _plain(AUTHORITY_MAP)
    assert "partial" in plain and "unclear" in plain and "missing" in plain
    assert "authority-gap closure slice" in plain


def test_decision_authority_map_doubleplay_and_bull_bear_stages_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    lowered = text.lower()
    assert "doubleplay" in lowered
    assert "bull specialist" in lowered
    assert "bear specialist" in lowered
    assert "long or short or flat" in lowered


def test_decision_authority_map_packet_runtime_separation_v0() -> None:
    text = _read(AUTHORITY_MAP)
    assert "## Doubleplay packet/runtime separation" in text
    assert "DoubleplayResolutionHandoffV1" in text
    assert "not a runtime mirror of `evaluate_double_play`" in text
    assert "Do not silently add runtime double-play fields" in text
    assert "Adapt to Master V2" in text


def test_decision_authority_map_execution_and_live_gate_boundary_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    lowered = text.lower()
    assert "staged execution enablement" in lowered
    assert "live authorization remains separate and external" in lowered
    assert "promotion eligibility status, not live authorization" in lowered
    assert "live_gates.py" in text


def test_decision_authority_map_ai_authority_non_executing_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    lowered = text.lower()
    assert "advisory ai and models vs authoritative execution decisions" in lowered
    assert "orchestration is not execution authority" in lowered
    assert LEARNING_INVENTORY.name in _read(AUTHORITY_MAP)
    assert "operator/external go remains required for live deploy" in lowered


def test_decision_authority_map_killswitch_and_switch_gate_distinction_v0() -> None:
    text = _plain(AUTHORITY_MAP)
    lowered = text.lower()
    assert "safety and kill-switch veto" in lowered
    assert "strategic switch-gate behavior is not equivalent to safety veto" in lowered
    assert "fail-closed" in lowered


def test_trading_logic_manifest_master_v2_double_play_v0() -> None:
    text = _plain(TRADING_LOGIC_MANIFEST)
    lowered = text.lower()
    assert "master v2" in lowered
    assert "double play" in lowered
    assert "non-authorizing" not in lowered  # manifest uses docs-only / keine Live-Freigabe
    assert "does not grant order placement" in lowered or "keine live-freigabe" in lowered


def test_trading_logic_manifest_state_switch_vs_killswitch_v0() -> None:
    text = _read(TRADING_LOGIC_MANIFEST)
    assert "State-Switch Logic" in text
    assert "KillSwitch flips to the other side" in text
    assert "Kill-All / Emergency Stop" in text
    assert "## 3. State-Switch statt KillSwitch" in text
    assert "State-Switch-Logik" in text
    assert "Long/Bull" in text
    assert "Short/Bear" in text


def test_trading_logic_manifest_crosslinks_capital_slot_contract_v0() -> None:
    text = _read(TRADING_LOGIC_MANIFEST)
    assert CAPITAL_SLOT_CONTRACT.name in text
    assert "ratchet" in text.lower()


def test_scope_capital_envelope_clarification_v0() -> None:
    text = _plain(SCOPE_CAPITAL)
    lowered = text.lower()
    assert "scope and capital envelope" in lowered
    assert "master v2" in lowered
    assert "non-authorizing" in lowered
    assert "downstream risk and exposure caps" in lowered
    assert AUTHORITY_MAP_NAME in _read(SCOPE_CAPITAL)


def test_scope_capital_envelope_distinct_from_risk_caps_v0() -> None:
    text = _plain(SCOPE_CAPITAL)
    assert "Scope and Capital Envelope versus risk caps" in text
    assert "must remain separate" in text.lower()
    assert "cap compliance is not equivalent to Scope correctness" in text


def test_capital_slot_contract_ratchet_no_top_up_inactivity_v0() -> None:
    text = _plain(CAPITAL_SLOT_CONTRACT)
    lowered = text.lower()
    assert "ratchet" in lowered
    assert "no auto top-up" in lowered or "no-top-up" in lowered
    assert "inactivity" in lowered
    assert "non-authorizing" in lowered
    assert TRADING_LOGIC_MANIFEST_NAME in _read(CAPITAL_SLOT_CONTRACT)


def test_blocker_register_glb010_glb011_blocked_v0() -> None:
    for blocker_id in ("GLB-010", "GLB-011"):
        row = _register_table_row(blocker_id)
        assert "| BLOCKED |" in row

    text = _plain(BLOCKER_REGISTER)
    assert "6.2 GLB-010 / GLB-011" in text
    assert "does not close GLB-010 or GLB-011 by itself" in text
    assert "capital-slot ratchet/release" in text.lower() or "capital slot" in text.lower()


def test_blocker_register_glb015_blocked_and_non_authorizing_v0() -> None:
    row = _register_table_row("GLB-015")
    assert "Repo docs treated as approval" in row
    assert "| BLOCKED |" in row

    text = _plain(BLOCKER_REGISTER)
    assert "6.5 GLB-015" in text
    assert "does not close GLB-015 by itself" in text
    assert "does not clear Preflight BLOCKED" in text


def test_blocker_register_crosslinks_authority_and_scope_capital_v0() -> None:
    text = _read(BLOCKER_REGISTER)
    assert AUTHORITY_MAP_NAME in text
    assert SCOPE_CAPITAL_NAME in text
    assert "Decision Authority Map" in text
    assert "Scope and Capital Envelope Clarification" in text


def test_authority_map_crosslinks_scope_capital_and_learning_inventory_v0() -> None:
    text = _read(AUTHORITY_MAP)
    assert LEARNING_INVENTORY.name in text
    assert PROMOTION_SM.name in _read(BLOCKER_REGISTER) or PROMOTION_SM.name in text
    assert "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md" in text


def test_blocker_register_crosslinks_promotion_state_machine_v0() -> None:
    text = _read(BLOCKER_REGISTER)
    assert "Promotion State Machine" in text
    assert PROMOTION_SM.is_file()


def test_preflight_blocked_and_glb015_continuity_v0() -> None:
    text = _plain(PREFLIGHT_CONTRACT)
    assert "BLOCKED" in text
    assert BLOCKER_REGISTER_NAME in _read(PREFLIGHT_CONTRACT)
    assert "GLB-015" in text
    assert "does not clear Preflight BLOCKED" in text
    assert "does not close GLB-014/GLB-015" in text
    assert "non-authorizing" in text.lower()


def test_authority_map_crosslinks_dataflow_and_reuse_inventory_v0() -> None:
    text = _read(AUTHORITY_MAP)
    assert "MASTER_V2_DATAFLOW_MAP_V1.md" in text
    assert "MASTER_V2_REUSE_REWIRE_INVENTORY_V1.md" in text


def test_core_docs_do_not_grant_live_authorization_v0() -> None:
    for path in (AUTHORITY_MAP, TRADING_LOGIC_MANIFEST, SCOPE_CAPITAL, BLOCKER_REGISTER):
        lowered = _lower(path)
        assert "live authorization" in lowered or "non-authorizing" in lowered, path.name


def test_glb014_authority_route_legibility_boundary_guard_v1() -> None:
    """GLB014_AUTHORITY_ROUTE_LEGIBILITY_BOUNDARY_GUARD_V1"""
    text = _read(AUTHORITY_MAP)
    plain = _plain(AUTHORITY_MAP)
    section = plain.split("SECTION5 / Preflight Go-No-Go Authority Route Legibility")[1].split(
        "11) Cross-References"
    )[0]

    for token in (
        "GLB014_AUTHORITY_ROUTE_LEGIBILITY_BOUNDARY_V0=true",
        "AUTHORITY_ROUTE_CANONICAL_OWNER_EXPLICIT=true",
        "APPROVAL_RECORD_TYPE_EXPLICIT=true",
        "OWNER_NAMING_NON_AUTHORIZING=true",
        "AMBIGUOUS_AUTHORITY_ROUTE_FAIL_CLOSED=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "EXECUTION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
    ):
        assert token in section
    assert "Stage-3 scoped executing approval record" in section
    assert "LB-APR-001" in section
    assert "Frank Rauter" in section
    assert "does not close GLB-014" in section
    assert "fail-closed" in section.lower()
    assert "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md" in text
    assert BLOCKER_REGISTER_NAME in text
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "LIVE_AUTHORIZED=true" not in collapsed


def test_glb016_preflight_packet_reproducibility_boundary_guard_v1() -> None:
    """GLB016_PREFLIGHT_PACKET_REPRODUCIBILITY_BOUNDARY_GUARD_V1"""
    text = _read(PREFLIGHT_CONTRACT)
    plain = _plain(PREFLIGHT_CONTRACT)
    section = plain.split("2b.2 GLB-016 Preflight Packet Reproducibility Boundary")[1].split(
        "Evidence Durable Closeout Retention RC"
    )[0]

    for token in (
        "GLB016_PREFLIGHT_PACKET_REPRODUCIBILITY_BOUNDARY_V0=true",
        "PREFLIGHT_PACKET_REQUIRED_ARTIFACTS_EXPLICIT=true",
        "PREFLIGHT_PACKET_VERSION_BINDING_EXPLICIT=true",
        "PREFLIGHT_PACKET_MANIFEST_VERIFICATION_REQUIRED=true",
        "INCOMPLETE_PACKET_FAIL_CLOSED=true",
        "REPRODUCIBLE_PACKET_NON_AUTHORIZING=true",
        "PREFLIGHT_REMAINS_BLOCKED=true",
        "READY_FOR_OPERATOR_ARMING=false",
        "EXECUTION_AUTHORIZED=false",
        "LIVE_AUTHORIZED=false",
    ):
        assert token in section
    assert "MANIFEST.sha256" in section
    assert "MANIFEST_VERIFY_RC=0" in section
    assert "/tmp" in section
    assert "does not close GLB-016" in section
    assert "Reproducible packet" in section
    assert "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md" in text
    assert "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md" in text
    collapsed = section.replace("**", "")
    assert "READY_FOR_OPERATOR_ARMING=true" not in collapsed
    assert "PREFLIGHT_REMAINS_BLOCKED=false" not in collapsed
