"""Static contract tests for Futures Master V2 Runtime Governance Boundary (v0).

Machine-anchors docs-only Runtime Governance Boundary composition from
FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0.md (GAP-RGB-STATIC-001).
Protects review legibility without importing runtime trading modules or
authorizing execution — static file-content tests only.
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

RGB_CONTRACT = SPECS / "FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0.md"
DSE_CONTRACT = SPECS / "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
SS_CONTRACT = SPECS / "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
KILLSWITCH_CONTRACT = SPECS / "FUTURES_RISK_SAFETY_KILLSWITCH_CONTRACT_V0.md"
LANE_TAXONOMY = SPECS / "RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md"

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

MACHINE_MARKERS: tuple[str, ...] = (
    "MARKER: RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0_EXISTS",
    "MARKER: RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0",
    "MARKER: RUNTIME_GOVERNANCE_IMPLEMENTED=false",
    "MARKER: DOCS_ONLY",
    "MARKER: NON_AUTHORIZING_POSTURE",
    "MARKER: GLOBAL_HOLD_REMAINS_ACTIVE",
    "MARKER: PREFLIGHT_REMAINS_BLOCKED",
    "MARKER: EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME",
    "MARKER: DSE_PREDECESSOR_REQUIRED",
    "MARKER: STATE_SWITCH_PREDECESSOR_REQUIRED",
    "MARKER: STATE_SWITCH_IS_NOT_EXECUTION_AUTHORITY",
    "MARKER: SCOPE_CAPITAL_RUNTIME_UNCHANGED",
    "MARKER: KILLSWITCH_SUPERIOR",
    "MARKER: EXECUTION_LIVE_GATE_UNCHANGED",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_RUNTIME_GOVERNANCE",
    "MARKER: AI_AUTHORITY=false",
    "MARKER: DASHBOARD_AUTHORITY=false",
    "MARKER: PROTECTED_RUNTIME_SEPARATE_APPROVAL_REQUIRED",
    "MARKER: PURE_STACK_HANDOFF_SEPARATE_APPROVAL_REQUIRED",
    "MARKER: GAP_RGB_001_CLOSED_BY_THIS_DOC",
    "MARKER: GAP_RGB_STATIC_001_FUTURE_TESTS_ONLY",
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


def test_runtime_governance_boundary_contract_exists_v0() -> None:
    assert RGB_CONTRACT.is_file()
    text = _read(RGB_CONTRACT)
    assert "Futures Master V2 Runtime Governance Boundary Contract v0" in text
    assert "DOCS_TOKEN_FUTURES_MASTER_V2_RUNTIME_GOVERNANCE_BOUNDARY_CONTRACT_V0" in text


def test_runtime_governance_boundary_contract_purpose_and_gap_rgb_001_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "canonical docs-only owner" in lowered
    assert "gap-rgb-001" in lowered
    assert "gap addressed" in lowered
    assert DSE_CONTRACT.name in _read(RGB_CONTRACT)
    assert SS_CONTRACT.name in _read(RGB_CONTRACT)


def test_runtime_governance_boundary_contract_governance_boundaries_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    raw = _read(RGB_CONTRACT)
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "global hold" in lowered and "remains active" in lowered
    assert "preflight" in lowered and "blocked" in lowered
    assert "evidence" in lowered and "does not authorize runtime" in lowered
    assert "RUNTIME_GOVERNANCE_IMPLEMENTED=false" in raw
    assert "does not implement runtime governance" in lowered
    assert PREFLIGHT_CONTRACT.name in raw


def test_runtime_governance_boundary_contract_composition_chain_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "dynamic scope envelope" in lowered
    assert "state-switch" in lowered
    assert "scope/capital" in lowered
    assert "killswitch" in lowered
    assert "execution / live gates" in lowered or "execution/live gates" in lowered
    assert "governance chain composition" in lowered or "governance chain" in lowered
    assert "dse → state-switch" in lowered or "dse -> state-switch" in lowered


def test_runtime_governance_boundary_contract_dse_predecessor_v0() -> None:
    text = _read(RGB_CONTRACT)
    plain = _plain(RGB_CONTRACT)
    lowered = plain.lower()
    assert DSE_CONTRACT.name in text
    assert DSE_CONTRACT.is_file()
    assert "predecessor" in lowered
    assert "scope-event predecessor" in lowered or "scope event" in lowered
    assert "DSE_PREDECESSOR_REQUIRED" in text
    assert "pointer only" in lowered


def test_runtime_governance_boundary_contract_state_switch_predecessor_v0() -> None:
    text = _read(RGB_CONTRACT)
    plain = _plain(RGB_CONTRACT)
    lowered = plain.lower()
    assert SS_CONTRACT.name in text
    assert SS_CONTRACT.is_file()
    assert "side-state governance predecessor" in lowered or "side-state governance" in lowered
    assert "STATE_SWITCH_PREDECESSOR_REQUIRED" in text
    assert "does not redefine state-switch vocabulary" in lowered


def test_runtime_governance_boundary_contract_state_switch_not_execution_authority_v0() -> None:
    text = _read(RGB_CONTRACT)
    plain = _plain(RGB_CONTRACT)
    lowered = plain.lower()
    assert "STATE_SWITCH_IS_NOT_EXECUTION_AUTHORITY" in text
    assert "not execution authority" in lowered
    assert "compliance ≠ execution permission" in plain or (
        "compliance" in lowered and "execution permission" in lowered
    )
    assert "STATE_SWITCH_IMPLEMENTED=false" in _read(SS_CONTRACT)


def test_runtime_governance_boundary_contract_scope_capital_boundary_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    raw = _read(RGB_CONTRACT)
    assert SCOPE_CAPITAL.name in raw
    assert "capital slots" in lowered
    assert "ratchets" in lowered
    assert "reserve" in lowered and "allocation" in lowered
    assert "release" in lowered and "reassignment" in lowered
    assert "scope_capital_runtime_unchanged" in lowered.replace("-", "_").replace(" ", "_")
    assert "capital slot" in lowered


def test_runtime_governance_boundary_contract_killswitch_superior_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    raw = _read(RGB_CONTRACT)
    assert KILLSWITCH_CONTRACT.name in raw
    assert "kill-all" in lowered or "kill all" in lowered
    assert "overrides" in lowered
    assert "killswitch_superior" in lowered.replace("-", "_").replace(" ", "_")
    assert "do not duplicate" in lowered and "pr #3648" in lowered


def test_runtime_governance_boundary_contract_execution_live_gates_boundary_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    raw = _read(RGB_CONTRACT)
    assert BLOCKER_REGISTER.name in raw
    assert "execution_live_gate_unchanged" in lowered.replace("-", "_").replace(" ", "_")
    assert "no execution authorization" in lowered or "does not grant order placement" in lowered
    assert "live / testnet / paper / shadow" in lowered or "paper, shadow, testnet, live" in lowered
    assert "LIVE_AUTHORIZATION_REMAINS_FALSE_IN_RUNTIME_GOVERNANCE" in raw


def test_runtime_governance_boundary_contract_ai_dashboard_evidence_boundaries_v0() -> None:
    text = _read(RGB_CONTRACT)
    plain = _plain(RGB_CONTRACT)
    lowered = plain.lower()
    assert LANE_TAXONOMY.name in text
    assert "review inputs" in lowered
    assert "metrics" in lowered and "reports" in lowered
    assert "archive indexes" in lowered
    assert "AI_AUTHORITY=false" in text
    assert "DASHBOARD_AUTHORITY=false" in text
    assert "does not authorize execution" in lowered or "none for execution" in lowered


def test_runtime_governance_boundary_contract_deferred_surfaces_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    raw = _read(RGB_CONTRACT)
    assert "protected runtime" in lowered and "separate" in lowered
    assert "pure-stack handoff" in lowered or "pure stack handoff" in lowered
    assert "universe selector" in lowered
    assert "strategy suitability" in lowered
    assert "behavior tests" in lowered or "golden-vector" in lowered
    assert "PROTECTED_RUNTIME_SEPARATE_APPROVAL_REQUIRED" in raw
    assert "PURE_STACK_HANDOFF_SEPARATE_APPROVAL_REQUIRED" in raw


def test_runtime_governance_boundary_contract_fail_closed_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "fail closed" in lowered or "fail-closed" in lowered
    assert "block arming" in lowered
    assert "block side transition" in lowered
    assert "block execution" in lowered


def test_runtime_governance_boundary_contract_non_goals_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "## 21. non-goals" in lowered
    assert "no execution authorization" in lowered
    assert "no broker or exchange" in lowered
    assert "no runtime behavior change" in lowered
    assert "no runtime governance" in lowered and "implementation" in lowered
    assert "market-airport" in lowered


def test_runtime_governance_boundary_contract_machine_markers_present_v0() -> None:
    text = _read(RGB_CONTRACT)
    for marker in MACHINE_MARKERS:
        assert marker in text, f"missing machine marker: {marker!r}"


def test_runtime_governance_boundary_contract_stop_conditions_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "## 22. stop conditions" in lowered
    assert "stop immediately if" in lowered
    assert "live_authorization: true" in lowered or "live_authorization`" in _read(RGB_CONTRACT)
    assert "pure-stack handoff or protected runtime implied as authorized" in lowered


def test_runtime_governance_boundary_contract_gap_rgb_static_001_and_staging_v0() -> None:
    text = _read(RGB_CONTRACT)
    plain = _plain(RGB_CONTRACT)
    assert "GAP-RGB-STATIC-001" in text
    assert "Static-contract tests" in text or "static-contract tests" in plain.lower()
    assert "Protected runtime governance implementation" in text or (
        "protected runtime" in plain.lower()
    )
    assert "## 18. Implementation staging" in text or "implementation staging" in plain.lower()


def test_runtime_governance_boundary_contract_crossreferences_v0() -> None:
    text = _read(RGB_CONTRACT)
    for name in (
        DSE_CONTRACT.name,
        SS_CONTRACT.name,
        TRADING_LOGIC_MANIFEST.name,
        "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
        SCOPE_CAPITAL.name,
        PURE_STACK_MAP.name,
        BLOCKER_REGISTER.name,
        PREFLIGHT_CONTRACT.name,
    ):
        assert name in text


def test_runtime_governance_boundary_contract_canonical_owners_v0() -> None:
    text = _plain(RGB_CONTRACT)
    lowered = text.lower()
    assert "runtime governance boundary composition" in lowered
    assert "this contract" in lowered and "owner" in lowered
    assert "do not duplicate" in lowered
    assert "pointer only" in lowered


def test_runtime_governance_boundary_contract_no_duplicate_static_owners_v0() -> None:
    """Authority #3648, pure stack #3649, DSE, and SS tests remain separate owners."""
    assert AUTHORITY_TEST.is_file()
    assert PURE_STACK_TEST.is_file()
    assert DSE_TEST.is_file()
    assert SS_TEST.is_file()
    contract_text = _read(RGB_CONTRACT)
    assert "NO_DUPLICATION_OF_DSE_CONTRACT_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_STATE_SWITCH_CONTRACT_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_PR3648_AUTHORITY_MAP_OWNER" in contract_text
    assert "NO_DUPLICATION_OF_PR3649_PURE_STACK_OWNER" in contract_text
    assert contract_text.count("MARKER:") >= len(MACHINE_MARKERS)


def test_runtime_governance_boundary_reciprocal_remote_runtime_docs_guard_v0() -> None:
    guard_text = REMOTE_RUNTIME_DOCS_GUARD.read_text(encoding="utf-8")
    assert THIS_MODULE in guard_text
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text
