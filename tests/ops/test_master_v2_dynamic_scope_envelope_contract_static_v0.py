"""Static contract tests for Futures Dynamic Scope Envelope Contract (v0).

Machine-anchors docs-only dynamic scope envelope governance from
FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md (GAP-DSE-STATIC-001). Protects
review legibility without importing runtime trading modules or authorizing
execution — static file-content tests only.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPECS = REPO_ROOT / "docs" / "ops" / "specs"
RUNBOOKS = REPO_ROOT / "docs" / "ops" / "runbooks"

DSE_CONTRACT = SPECS / "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
FUTURES_INPUT_READ_MODEL = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md"
FUTURES_INPUT_PRODUCER = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md"
LEARNING_INVENTORY = SPECS / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
STRATEGY_INTEGRATION = SPECS / "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md"

TRADING_LOGIC_MANIFEST_NAME = "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
SCOPE_CAPITAL_NAME = "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"

MACHINE_MARKERS: tuple[str, ...] = (
    "MARKER: FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0_EXISTS",
    "MARKER: DYNAMIC_SCOPE_ENVELOPE_DISTINCT_FROM_DEPLOYABLE_CAPITAL",
    "MARKER: STATIC_HARD_LIMITS_NEVER_WIDENED_BY_DYNAMIC_RULES",
    "MARKER: LIVE_AUTHORIZATION_REMAINS_FALSE_IN_ENVELOPE",
    "MARKER: DYNAMIC_SCOPE_TRAIL_NOT_KILLSWITCH",
    "MARKER: STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY",
    "MARKER: ENVELOPE_COMPLIANCE_NOT_LIVE_AUTHORIZATION",
    "MARKER: CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT",
    "MARKER: CONFIRMATION_TICKS_VOCABULARY_PRESENT",
    "MARKER: HYSTERESIS_COOLDOWN_VOCABULARY_PRESENT",
    "MARKER: TRAILING_SCOPE_BANDS_VOCABULARY_PRESENT",
    "MARKER: FUTURES_INPUT_READY_FOR_DYNAMIC_SCOPE_CROSSLINK",
    "MARKER: HOT_PATH_NO_HEAVY_RECOMPUTE",
    "MARKER: MANIFEST_SECTION_20_CROSSLINK_TO_THIS_CONTRACT",
    "MARKER: SEQUENCING_BEFORE_STATE_SWITCH_CONTRACT",
    "MARKER: NON_AUTHORIZING_POSTURE",
    "MARKER: NO_DUPLICATION_OF_PR3648_STATE_SWITCH_VS_KILLSWITCH_OWNER",
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


def test_dynamic_scope_envelope_contract_exists_v0() -> None:
    assert DSE_CONTRACT.is_file()
    text = _read(DSE_CONTRACT)
    assert "Futures Dynamic Scope Envelope Contract v0" in text
    assert "DOCS_TOKEN_FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0" in text


def test_dynamic_scope_envelope_purpose_and_gap_dse_001_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "canonical docs-only owner" in lowered
    assert "dynamic scope envelope" in lowered
    assert "gap-dse-001" in lowered
    assert "gap addressed" in lowered
    assert TRADING_LOGIC_MANIFEST_NAME in _read(DSE_CONTRACT)


def test_dynamic_scope_envelope_non_authority_and_safety_posture_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "docs-only" in lowered
    assert "non-authorizing" in lowered
    assert "global hold" in lowered and "remains active" in lowered
    assert "preflight" in lowered and "blocked" in lowered
    assert "evidence" in lowered and "does not authorize runtime" in lowered
    assert "dashboard" in lowered and "does not authorize trades" in lowered
    assert "ai" in lowered and "does not authorize execution" in lowered
    assert PREFLIGHT_CONTRACT.name in _read(DSE_CONTRACT)


def test_dynamic_scope_envelope_sequencing_before_state_switch_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    lowered = plain.lower()
    assert "sequencing lock" in lowered
    assert "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md" in text
    assert "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md" in text
    assert "first" in lowered and "manifest §20 order" in lowered
    assert "does not specify the state-switch state machine" in lowered


def test_dynamic_scope_envelope_master_v2_double_play_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "master v2" in lowered
    assert "double play" in lowered
    assert "one selected future" in lowered
    assert "long/bull" in lowered or "long" in lowered
    assert "short/bear" in lowered or "short" in lowered


def test_dynamic_scope_envelope_trading_logic_manifest_crosslink_v0() -> None:
    text = _read(DSE_CONTRACT)
    assert TRADING_LOGIC_MANIFEST_NAME in text
    assert TRADING_LOGIC_MANIFEST.is_file()
    assert "§5–8" in text or "consolidates and crosslinks" in _plain(DSE_CONTRACT)


def test_dynamic_scope_envelope_scope_capital_boundary_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert SCOPE_CAPITAL_NAME in _read(DSE_CONTRACT)
    assert "deployable capital" in lowered or "deployable scope" in lowered
    assert "must not collapse" in lowered
    assert "instrument-level price/structure boundaries" in lowered


def test_dynamic_scope_envelope_killswitch_boundary_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "kill-all" in lowered or "kill all" in lowered
    assert "does not implement killswitch" in lowered
    assert "dynamic_scope_trail_not_killswitch" in lowered.replace("-", "_").replace(" ", "_") or (
        "scope trail" in lowered and "killswitch" in lowered
    )
    assert "do not duplicate" in lowered and "pr #3648" in lowered


def test_dynamic_scope_envelope_execution_live_gates_boundary_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "not sufficient for execution" in lowered
    assert BLOCKER_REGISTER.name in _read(DSE_CONTRACT)
    assert "live_authorization" in lowered
    assert (
        "envelope_compliance_not_live_authorization" in lowered.replace("-", "_").replace(" ", "_")
        or "not sufficient for execution" in lowered
    )


def test_dynamic_scope_envelope_ai_and_dashboard_authority_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    lowered = plain.lower()
    assert LEARNING_INVENTORY.name in text
    assert "display ≠ freigabe" in plain or "display" in lowered and "freigabe" in lowered
    assert STRATEGY_INTEGRATION.name in text
    assert "no hot-path envelope recomputation" in lowered


def test_dynamic_scope_envelope_vocabulary_trailing_hysteresis_cooldown_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "trailing scope bands" in lowered
    assert "hysteresis" in lowered
    assert "cooldown" in lowered
    assert "confirmation_ticks" in lowered or "confirmation ticks" in lowered
    assert "scope drift" in lowered or "scope trail" in lowered
    assert "hard guardrails" in lowered or "hard limits" in lowered


def test_dynamic_scope_envelope_candidate_vs_confirmed_events_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    assert "DOWNSCOPE_CANDIDATE" in text
    assert "DOWNSCOPE_CONFIRMED" in text
    assert "UPSCOPE_CANDIDATE" in text
    assert "UPSCOPE_CONFIRMED" in text
    assert "alone authorize State-Switch" in plain
    assert "CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT" in text


def test_dynamic_scope_envelope_non_goals_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "## 29. non-goals" in lowered
    assert "no execution authorization" in lowered
    assert "no broker or exchange" in lowered
    assert "no runtime behavior change" in lowered
    assert "no killswitch" in lowered and "implementation or replacement" in lowered
    assert "no state-switch side state machine" in lowered
    assert "market-airport" in lowered


def test_dynamic_scope_envelope_machine_markers_present_v0() -> None:
    text = _read(DSE_CONTRACT)
    for marker in MACHINE_MARKERS:
        assert marker in text, f"missing machine marker: {marker!r}"


def test_dynamic_scope_envelope_stop_conditions_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "## 30. stop conditions" in lowered
    assert "stop immediately if" in lowered
    assert "live_authorization: true" in lowered or "live_authorization`" in _read(DSE_CONTRACT)
    assert "widening static hard limits" in lowered
    assert "state-switch contract drafted before this contract merged" in lowered


def test_dynamic_scope_envelope_gap_dse_static_001_and_staging_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    assert "GAP-DSE-STATIC-001" in text
    assert "Static-contract tests" in text or "static-contract tests" in plain.lower()
    assert "State-Switch contract" in text
    assert "## 26. Implementation staging" in text or "implementation staging" in plain.lower()


def test_dynamic_scope_envelope_futures_input_crosslink_v0() -> None:
    text = _read(DSE_CONTRACT)
    assert FUTURES_INPUT_READ_MODEL.name in text
    assert FUTURES_INPUT_PRODUCER.name in text
    assert "ready_for_dynamic_scope" in text
    assert "FUTURES_INPUT_READY_FOR_DYNAMIC_SCOPE_CROSSLINK" in text


def test_dynamic_scope_envelope_pure_stack_reference_not_runtime_sm_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert PURE_STACK_MAP.name in _read(DSE_CONTRACT)
    assert "not a running runtime state machine" in lowered
    assert "hot_path_no_heavy_recompute" in lowered.replace("-", "_").replace(" ", "_") or (
        "no heavy recompute" in lowered
    )


def test_dynamic_scope_envelope_crossreferences_v0() -> None:
    text = _read(DSE_CONTRACT)
    for name in (
        TRADING_LOGIC_MANIFEST_NAME,
        "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
        SCOPE_CAPITAL_NAME,
        PURE_STACK_MAP.name,
        BLOCKER_REGISTER.name,
        PREFLIGHT_CONTRACT.name,
    ):
        assert name in text


def test_dynamic_scope_envelope_does_not_duplicate_pure_stack_dynamic_scope_owner_v0() -> None:
    """Pure stack map pins inventory headline; this contract owns envelope vocabulary."""
    authority_test = (
        REPO_ROOT
        / "tests"
        / "ops"
        / ("test_master_v2_double_play_pure_stack_readiness_map_static_crosslink_contract_v0.py")
    )
    assert authority_test.is_file()
    pure_stack_text = _read(PURE_STACK_MAP)
    contract_text = _read(DSE_CONTRACT)
    assert "state / dynamic scope" in pure_stack_text.lower()
    assert "Dynamic Scope Envelope vocabulary" in contract_text
    assert contract_text.count("MARKER:") >= len(MACHINE_MARKERS)
