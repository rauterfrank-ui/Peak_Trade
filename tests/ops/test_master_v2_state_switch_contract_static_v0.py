"""Static contract tests for Futures Double Play State-Switch Contract (v0).

Machine-anchors docs-only State-Switch governance from
FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md (GAP-SS-STATIC-001). Protects
review legibility without importing runtime trading modules or authorizing
execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"
REMOTE_RUNTIME_DOCS_GUARD = (
    REPO_ROOT / "tests" / "ops" / "test_remote_runtime_contract_docs_guard_v0.py"
)

THIS_MODULE = Path(__file__).name

SS_CONTRACT = SPECS / "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
DSE_CONTRACT = SPECS / "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
LEARNING_INVENTORY = SPECS / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
STRATEGY_INTEGRATION = SPECS / "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md"
CAPITAL_SLOT = SPECS / "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"

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

MACHINE_MARKERS: tuple[str, ...] = (
    "MARKER: FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0_EXISTS",
    "MARKER: STATE_SWITCH_CONTRACT_V0",
    "MARKER: STATE_SWITCH_IMPLEMENTED=false",
    "MARKER: DOCS_ONLY",
    "MARKER: NON_AUTHORIZING_POSTURE",
    "MARKER: GLOBAL_HOLD_REMAINS_ACTIVE",
    "MARKER: PREFLIGHT_REMAINS_BLOCKED",
    "MARKER: EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME",
    "MARKER: DSE_PREDECESSOR_REQUIRED",
    "MARKER: DOWNSCOPE_CONFIRMED_REQUIRED_FOR_LONG_TO_SHORT",
    "MARKER: UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG",
    "MARKER: CANDIDATE_EVENTS_DO_NOT_AUTHORIZE_SIDE_SWITCH",
    "MARKER: CANDIDATE_VS_CONFIRMED_SWITCH_EVENTS_DISTINCT",
    "MARKER: KILLSWITCH_SUPERIOR",
    "MARKER: STATE_SWITCH_NOT_KILLSWITCH_FLIP",
    "MARKER: EXECUTION_LIVE_GATE_UNCHANGED",
    "MARKER: SCOPE_CAPITAL_RUNTIME_UNCHANGED",
    "MARKER: AI_AUTHORITY=false",
    "MARKER: DASHBOARD_AUTHORITY=false",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_STATE_SWITCH",
    "MARKER: SWITCH_COMPLIANCE_NOT_LIVE_AUTHORIZATION",
    "MARKER: GAP_SS_001_CLOSED_BY_THIS_DOC",
    "MARKER: GAP_SS_STATIC_001_FUTURE_TESTS_ONLY",
    "MARKER: NO_DUPLICATION_OF_PR3648_STATE_SWITCH_VS_KILLSWITCH_OWNER",
    "MARKER: NO_DUPLICATION_OF_PR3649_PURE_STACK_READINESS_OWNER",
    "MARKER: MANIFEST_SECTION_20_CROSSLINK_TO_THIS_CONTRACT",
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


def test_state_switch_contract_exists_v0() -> None:
    assert SS_CONTRACT.is_file()
    text = _read(SS_CONTRACT)
    assert "Futures Double Play State-Switch Contract v0" in text
    assert "DOCS_TOKEN_FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0" in text


def test_state_switch_contract_purpose_and_gap_ss_001_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "canonical docs-only owner" in lowered
    assert "gap-ss-001" in lowered
    assert "gap addressed" in lowered
    assert DSE_CONTRACT.name in _read(SS_CONTRACT)


def test_state_switch_contract_governance_boundaries_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "global hold" in lowered and "remains active" in lowered
    assert "preflight" in lowered and "blocked" in lowered
    assert "evidence" in lowered and "does not authorize runtime" in lowered
    assert "STATE_SWITCH_IMPLEMENTED=false" in _read(SS_CONTRACT)
    assert "does not implement State-Switch" in text or "does not implement state-switch" in lowered
    assert PREFLIGHT_CONTRACT.name in _read(SS_CONTRACT)


def test_state_switch_contract_dse_predecessor_dependency_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    lowered = plain.lower()
    assert DSE_CONTRACT.name in text
    assert DSE_CONTRACT.is_file()
    assert "predecessor" in lowered
    assert "produces/constrains scope events" in plain or "scope events" in lowered
    assert "side states transition" in lowered or "side-state" in lowered
    assert "STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY" in text


def test_state_switch_contract_allowed_dse_inputs_v0() -> None:
    text = _read(SS_CONTRACT)
    assert "DOWNSCOPE_CONFIRMED" in text
    assert "UPSCOPE_CONFIRMED" in text
    plain = _plain(SS_CONTRACT)
    assert "long" in plain.lower() and "short" in plain.lower()
    assert "DOWNSCOPE_CONFIRMED_REQUIRED_FOR_LONG_TO_SHORT" in text
    assert "UPSCOPE_CONFIRMED_REQUIRED_FOR_SHORT_TO_LONG" in text


def test_state_switch_contract_candidate_events_rejected_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    assert "DOWNSCOPE_CANDIDATE" in text
    assert "UPSCOPE_CANDIDATE" in text
    assert "does not" in plain.lower() and "authorize side switch" in plain.lower()
    assert "CANDIDATE_EVENTS_DO_NOT_AUTHORIZE_SIDE_SWITCH" in text


def test_state_switch_contract_long_bull_short_bear_vocabulary_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "long/bull" in lowered
    assert "short/bear" in lowered
    assert "side-state" in lowered or "side state" in lowered
    assert "master v2" in lowered
    assert "double play" in lowered


def test_state_switch_contract_side_state_vocabulary_v0() -> None:
    text = _read(SS_CONTRACT)
    for state in (
        "NEUTRAL_OBSERVE",
        "LONG_ARMED",
        "LONG_ACTIVE",
        "SHORT_ARMED",
        "SHORT_ACTIVE",
        "SWITCH_LONG_TO_SHORT_PENDING",
        "SWITCH_SHORT_TO_LONG_PENDING",
        "CHOP_GUARD_BLOCK",
        "KILL_ALL",
    ):
        assert state in text


def test_state_switch_contract_switch_pipelines_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    assert "LONG_ACTIVE" in text and "SHORT_ACTIVE" in text
    assert "DOWNSCOPE_CONFIRMED" in text
    assert "UPSCOPE_CONFIRMED" in text
    assert "long → short" in plain.lower() or "long to short" in plain.lower()
    assert "short → long" in plain.lower() or "short to long" in plain.lower()


def test_state_switch_contract_switch_events_candidate_vs_confirmed_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    assert "SIDE_SWITCH_CANDIDATE" in text
    assert "SIDE_SWITCH_CONFIRMED" in text
    assert "SIDE_SWITCH_BLOCKED" in text
    assert "does not" in plain.lower() and "alone complete side change" in plain.lower()
    assert "CANDIDATE_VS_CONFIRMED_SWITCH_EVENTS_DISTINCT" in text


def test_state_switch_contract_inherited_dse_prerequisites_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "hysteresis" in lowered
    assert "cooldown" in lowered
    assert "confirmation" in lowered
    assert "scope stability" in lowered or "scope prerequisite" in lowered or "inherits" in lowered


def test_state_switch_contract_fail_closed_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "fail closed" in lowered or "fail-closed" in lowered
    assert "scope_unknown" in lowered or "scope unknown" in lowered
    assert "observe/neutral" in lowered or "observe" in lowered


def test_state_switch_contract_scope_capital_boundary_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert SCOPE_CAPITAL.name in _read(SS_CONTRACT)
    assert "mutate capital-slot" in lowered or "capital-slot runtime" in lowered
    assert "scope_capital_runtime_unchanged" in lowered.replace("-", "_").replace(" ", "_")
    assert CAPITAL_SLOT.name in _read(SS_CONTRACT)


def test_state_switch_contract_killswitch_superior_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "kill-all" in lowered or "kill all" in lowered
    assert "superior" in lowered
    assert "cannot override" in lowered
    assert "killswitch_superior" in lowered.replace("-", "_").replace(" ", "_")
    assert "do not duplicate" in lowered and "pr #3648" in lowered


def test_state_switch_contract_execution_live_gates_boundary_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert BLOCKER_REGISTER.name in _read(SS_CONTRACT)
    assert "not sufficient for execution" in lowered or "live_authorization" in lowered
    assert "execution_live_gate_unchanged" in lowered.replace("-", "_").replace(" ", "_")
    assert "no order authorization" in lowered


def test_state_switch_contract_ai_dashboard_evidence_boundaries_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    lowered = plain.lower()
    assert LEARNING_INVENTORY.name in text
    assert STRATEGY_INTEGRATION.name in text
    assert "does not authorize side switch" in lowered or "does not authorize execution" in lowered
    assert "display" in lowered and "freigabe" in lowered
    assert "evidence" in lowered and "not switch authority" in lowered
    assert "AI_AUTHORITY=false" in text or "ai_authority=false" in lowered.replace(" ", "_")


def test_state_switch_contract_non_goals_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "## 24. non-goals" in lowered
    assert "no execution authorization" in lowered
    assert "no broker or exchange" in lowered
    assert "no runtime behavior change" in lowered
    assert "no state-switch" in lowered and "implementation" in lowered
    assert "market-airport" in lowered


def test_state_switch_contract_machine_markers_present_v0() -> None:
    text = _read(SS_CONTRACT)
    for marker in MACHINE_MARKERS:
        assert marker in text, f"missing machine marker: {marker!r}"


def test_state_switch_contract_stop_conditions_v0() -> None:
    text = _plain(SS_CONTRACT)
    lowered = text.lower()
    assert "## 25. stop conditions" in lowered
    assert "stop immediately if" in lowered
    assert "live_authorization: true" in lowered or "live_authorization`" in _read(SS_CONTRACT)
    assert "candidate scope events alone authorize side switch" in lowered


def test_state_switch_contract_gap_ss_static_001_and_staging_v0() -> None:
    text = _read(SS_CONTRACT)
    plain = _plain(SS_CONTRACT)
    assert "GAP-SS-STATIC-001" in text
    assert "Static-contract tests" in text or "static-contract tests" in plain.lower()
    assert "Protected runtime State-Switch implementation" in text or (
        "protected runtime" in plain.lower()
    )
    assert "## 21. Implementation staging" in text or "implementation staging" in plain.lower()


def test_state_switch_contract_crossreferences_v0() -> None:
    text = _read(SS_CONTRACT)
    for name in (
        DSE_CONTRACT.name,
        TRADING_LOGIC_MANIFEST.name,
        "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
        SCOPE_CAPITAL.name,
        PURE_STACK_MAP.name,
        BLOCKER_REGISTER.name,
        PREFLIGHT_CONTRACT.name,
    ):
        assert name in text


def test_state_switch_contract_no_duplicate_static_owners_v0() -> None:
    """Authority #3648, pure stack #3649, and DSE tests remain separate owners."""
    assert AUTHORITY_TEST.is_file()
    assert PURE_STACK_TEST.is_file()
    assert DSE_TEST.is_file()
    contract_text = _read(SS_CONTRACT)
    assert "NO_DUPLICATION_OF_PR3648_STATE_SWITCH_VS_KILLSWITCH_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_PR3649_PURE_STACK_READINESS_OWNER" in contract_text
    assert contract_text.count("MARKER:") >= len(MACHINE_MARKERS)


def test_state_switch_contract_reciprocal_remote_runtime_docs_guard_v0() -> None:
    guard_text = REMOTE_RUNTIME_DOCS_GUARD.read_text(encoding="utf-8")
    assert THIS_MODULE in guard_text
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text
