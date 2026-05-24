"""Static contract tests for Futures Master V2 Protected Runtime Stage (v0).

Machine-anchors docs-only Protected Runtime Stage ladder from
FUTURES_MASTER_V2_PROTECTED_RUNTIME_STAGE_CONTRACT_V0.md (GAP-PRT-STATIC-001).
Protects review legibility without importing runtime trading modules or
authorizing execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

PRT_CONTRACT = SPECS / "FUTURES_MASTER_V2_PROTECTED_RUNTIME_STAGE_CONTRACT_V0.md"
DSE_CONTRACT = SPECS / "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
SS_CONTRACT = SPECS / "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
RGB_CONTRACT = SPECS / "FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
KILLSWITCH_CONTRACT = SPECS / "FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
LANE_TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"
SCHEDULER_BOUNDARY = SPECS / "SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0.md"

AUTHORITY_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_master_v2_decision_authority_map_static_crosslink_contract_v0.py"
)
PURE_STACK_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py"
)
DSE_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_master_v2_dynamic_scope_envelope_contract_static_v0.py"
)
SS_TEST = REPO_ROOT / "tests" / "ops" / "test_master_v2_state_switch_contract_static_v0.py"
RGB_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_master_v2_runtime_governance_boundary_contract_static_v0.py"
)

MACHINE_MARKERS: tuple[str, ...] = (
    "MARKER: PROTECTED_RUNTIME_STAGE_CONTRACT_V0_EXISTS",
    "MARKER: PROTECTED_RUNTIME_STAGE_CONTRACT_V0",
    "MARKER: PROTECTED_RUNTIME_IMPLEMENTED=false",
    "MARKER: DOCS_ONLY",
    "MARKER: NON_AUTHORIZING_POSTURE",
    "MARKER: GLOBAL_HOLD_REMAINS_ACTIVE",
    "MARKER: PREFLIGHT_REMAINS_BLOCKED",
    "MARKER: EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME",
    "MARKER: FIRST_SAFE_STAGE_STOP",
    "MARKER: DSE_PREDECESSOR_REQUIRED",
    "MARKER: STATE_SWITCH_PREDECESSOR_REQUIRED",
    "MARKER: RUNTIME_GOVERNANCE_BOUNDARY_PREDECESSOR_REQUIRED",
    "MARKER: PURE_STACK_HANDOFF_REVIEW_PREDECESSOR_REQUIRED",
    "MARKER: OFFLINE_GOVERNANCE_TICK_HARNESS_FUTURE_SEPARATE_APPROVAL",
    "MARKER: OFFLINE_GOVERNANCE_TICK_HARNESS_IMPLEMENTED=false",
    "MARKER: BEHAVIOR_TESTS_FUTURE_SEPARATE_APPROVAL",
    "MARKER: PAPER_SHADOW_TESTNET_LIVE_BLOCKED",
    "MARKER: BROKER_EXCHANGE_AUTHORITY=false",
    "MARKER: SCOPE_CAPITAL_RUNTIME_UNCHANGED",
    "MARKER: KILLSWITCH_SUPERIOR",
    "MARKER: EXECUTION_LIVE_GATE_UNCHANGED",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_PROTECTED_RUNTIME_STAGE",
    "MARKER: AI_AUTHORITY=false",
    "MARKER: DASHBOARD_AUTHORITY=false",
    "MARKER: UNIVERSE_SELECTOR_UNCHANGED",
    "MARKER: STRATEGY_SUITABILITY_UNCHANGED",
    "MARKER: PROTECTED_RUNTIME_SEPARATE_APPROVAL_REQUIRED",
    "MARKER: GAP_PRT_001_CLOSED_BY_THIS_DOC",
    "MARKER: GAP_PRT_STATIC_001_FUTURE_TESTS_ONLY",
    "MARKER: NO_DUPLICATION_OF_RGB_CONTRACT_OWNER",
    "MARKER: NO_DUPLICATION_OF_DSE_CONTRACT_OWNER",
    "MARKER: NO_DUPLICATION_OF_STATE_SWITCH_CONTRACT_OWNER",
    "MARKER: NO_DUPLICATION_OF_PR3648_AUTHORITY_MAP_OWNER",
    "MARKER: NO_DUPLICATION_OF_PR3649_PURE_STACK_OWNER",
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


def test_protected_runtime_stage_contract_exists_v0() -> None:
    assert PRT_CONTRACT.is_file()
    text = _read(PRT_CONTRACT)
    assert "Futures Master V2 Protected Runtime Stage Contract v0" in text
    assert "DOCS_TOKEN_FUTURES_MASTER_V2_PROTECTED_RUNTIME_STAGE_CONTRACT_V0" in text


def test_required_contract_markers_are_present_v0() -> None:
    text = _read(PRT_CONTRACT)
    for marker in MACHINE_MARKERS:
        assert marker in text, f"missing machine marker: {marker!r}"


def test_stage_zero_stop_is_active_safe_stage_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "FIRST_SAFE_STAGE_STOP=true" in text
    assert "stage 0" in lowered and "stop" in lowered
    assert "active now" in lowered or "current authorized posture" in lowered
    assert "first safe current stage" in lowered
    assert "PROTECTED_RUNTIME_IMPLEMENTED=false" in text


def test_stage_ladder_future_gated_sequence_is_present_v0() -> None:
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "## 7. protected runtime stage ladder" in lowered
    assert "static-contract tests" in lowered or "static contract tests" in lowered
    assert "offline harness design review" in lowered or "offline harness" in lowered
    assert "offline harness implementation" in lowered
    assert "behavior tests" in lowered
    assert "paper / shadow / testnet / live" in lowered or "paper, shadow, testnet, live" in lowered
    assert "far downstream" in lowered and "blocked" in lowered
    assert "separate operator approval" in lowered


def test_predecessor_dependency_crosslinks_are_present_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert DSE_CONTRACT.name in text
    assert SS_CONTRACT.name in text
    assert RGB_CONTRACT.name in text
    assert DSE_CONTRACT.is_file()
    assert SS_CONTRACT.is_file()
    assert RGB_CONTRACT.is_file()
    assert "pure-stack-handoff" in lowered or "pure stack handoff" in lowered
    assert "a_stop" in lowered or "a stop" in lowered
    assert "DSE_PREDECESSOR_REQUIRED" in text
    assert "STATE_SWITCH_PREDECESSOR_REQUIRED" in text
    assert "RUNTIME_GOVERNANCE_BOUNDARY_PREDECESSOR_REQUIRED" in text
    assert "PURE_STACK_HANDOFF_REVIEW_PREDECESSOR_REQUIRED" in text
    assert "pointer only" in lowered
    assert "does not duplicate" in lowered


def test_non_authorizing_boundaries_are_present_v0() -> None:
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    raw = _read(PRT_CONTRACT)
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "global hold" in lowered and "remains active" in lowered
    assert "preflight" in lowered and "blocked" in lowered
    assert "evidence" in lowered and "does not authorize runtime" in lowered
    assert PREFLIGHT_CONTRACT.name in raw
    assert "does not grant order placement" in lowered or "no execution authorization" in lowered


def test_protected_runtime_and_harness_remain_unimplemented_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "PROTECTED_RUNTIME_IMPLEMENTED=false" in text
    assert "OFFLINE_GOVERNANCE_TICK_HARNESS_IMPLEMENTED=false" in text
    assert "implement protected runtime" in lowered and "does not" in lowered
    assert "offline governance-tick harness" in lowered
    assert "future separate approval" in lowered or "separate approval" in lowered


def test_behavior_tests_and_runtime_stages_remain_future_separate_approval_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "BEHAVIOR_TESTS_FUTURE_SEPARATE_APPROVAL" in text
    assert "PROTECTED_RUNTIME_SEPARATE_APPROVAL_REQUIRED" in text
    assert "OFFLINE_GOVERNANCE_TICK_HARNESS_FUTURE_SEPARATE_APPROVAL" in text
    assert "behavior tests" in lowered
    assert "not authorized by this contract" in lowered
    assert "RUNTIME_GOVERNANCE_IMPLEMENTED=false" in text
    assert "STATE_SWITCH_IMPLEMENTED=false" in text


def test_paper_shadow_testnet_live_and_broker_exchange_remain_blocked_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "PAPER_SHADOW_TESTNET_LIVE_BLOCKED" in text
    assert "BROKER_EXCHANGE_AUTHORITY=false" in text
    assert "paper" in lowered and "shadow" in lowered and "testnet" in lowered and "live" in lowered
    assert "broker" in lowered and "exchange" in lowered
    assert SCHEDULER_BOUNDARY.name in text
    assert "no broker or exchange" in lowered or "broker/exchange" in lowered


def test_scope_capital_killswitch_execution_live_gate_boundaries_are_preserved_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert SCOPE_CAPITAL.name in text
    assert KILLSWITCH_CONTRACT.name in text
    assert BLOCKER_REGISTER.name in text
    assert "SCOPE_CAPITAL_RUNTIME_UNCHANGED" in text
    assert "KILLSWITCH_SUPERIOR" in text
    assert "EXECUTION_LIVE_GATE_UNCHANGED" in text
    assert "capital slots" in lowered
    assert "overrides" in lowered
    assert "visibility labels only" in lowered or "visibility only" in lowered


def test_ai_dashboard_evidence_non_authority_is_preserved_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert LANE_TAXONOMY.name in text
    assert "AI_AUTHORITY=false" in text
    assert "DASHBOARD_AUTHORITY=false" in text
    assert "EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME" in text
    assert "review inputs" in lowered
    assert "none" in lowered


def test_universe_selector_strategy_suitability_market_airport_boundaries_are_preserved_v0() -> None:
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    raw = _read(PRT_CONTRACT)
    assert "UNIVERSE_SELECTOR_UNCHANGED" in raw
    assert "STRATEGY_SUITABILITY_UNCHANGED" in raw
    assert "universe selector" in lowered
    assert "strategy suitability" in lowered
    assert "market-airport" in lowered
    assert "no pure-stack handoff wiring" in lowered or "pure-stack handoff" in lowered


def test_gap_prt_static_001_is_anchored_v0() -> None:
    text = _read(PRT_CONTRACT)
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    assert "GAP-PRT-001" in text
    assert "GAP-PRT-STATIC-001" in text
    assert "GAP_PRT_001_CLOSED_BY_THIS_DOC" in text
    assert "GAP_PRT_STATIC_001_FUTURE_TESTS_ONLY" in text
    assert "test_master_v2_protected_runtime_stage_contract_static_v0.py" in text.replace(
        "&#47;", "/"
    )
    assert "implementation-stage ladder" in lowered or "stage ladder" in lowered


def test_contract_does_not_claim_live_readiness_or_execution_authority_v0() -> None:
    plain = _plain(PRT_CONTRACT)
    lowered = plain.lower()
    raw = _read(PRT_CONTRACT)
    assert "## 20. stop conditions" in lowered
    assert "stop immediately if" in lowered
    assert "live_authorization: true" in lowered or "live_authorization`" in raw
    assert "imply live readiness" in lowered
    dangerous = (
        "live trading authorized",
        "testnet authorized",
        "paper authorized",
        "shadow authorized",
        "broker authorized",
        "exchange authorized",
        "execution authorized by this contract",
    )
    for phrase in dangerous:
        assert phrase not in lowered


def test_protected_runtime_stage_contract_no_duplicate_static_owners_v0() -> None:
    """Authority #3648, pure stack #3649, DSE, SS, and RGB tests remain separate owners."""
    assert AUTHORITY_TEST.is_file()
    assert PURE_STACK_TEST.is_file()
    assert DSE_TEST.is_file()
    assert SS_TEST.is_file()
    assert RGB_TEST.is_file()
    contract_text = _read(PRT_CONTRACT)
    assert "NO_DUPLICATION_OF_RGB_CONTRACT_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_DSE_CONTRACT_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_STATE_SWITCH_CONTRACT_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_PR3648_AUTHORITY_MAP_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_PR3649_PURE_STACK_OWNER" in contract_text
    assert contract_text.count("MARKER:") >= len(MACHINE_MARKERS)
