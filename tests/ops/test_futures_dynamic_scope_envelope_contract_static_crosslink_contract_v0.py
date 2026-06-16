"""Static crosslink contract tests for Futures Dynamic Scope Envelope (v0).

Machine-anchors docs-only dynamic scope envelope governance and crosslinks from
FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md (GAP-DSE-STATIC-001). Verifies
manifest §20 ordering, §25–§27 machine markers, and non-authorizing posture
without importing runtime trading modules — static file-content tests only.
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
DSE_CONTRACT = SPECS / "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
TRADING_LOGIC_MANIFEST = SPECS / "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
STATE_SWITCH_CONTRACT = SPECS / "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"
SCOPE_CAPITAL = SPECS / "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md"
BLOCKER_REGISTER = SPECS / "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md"
PREFLIGHT_CONTRACT = RUNBOOKS / "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
PURE_STACK_MAP = SPECS / "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md"
FUTURES_INPUT_READ_MODEL = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md"
FUTURES_INPUT_PRODUCER = SPECS / "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md"
LEARNING_INVENTORY = SPECS / "MASTER_V2_LEARNING_AI_AUTONOMY_INVENTORY_V1.md"
STRATEGY_INTEGRATION = SPECS / "STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md"
CAPITAL_SLOT = SPECS / "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md"
ARITHMETIC_SURVIVAL = SPECS / "MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md"
DECISION_AUTHORITY_MAP = SPECS / "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md"

DSE_CONTRACT_NAME = "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0.md"
TRADING_LOGIC_MANIFEST_NAME = "MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md"
STATE_SWITCH_CONTRACT_NAME = "FUTURES_DOUBLE_PLAY_STATE_SWITCH_CONTRACT_V0.md"

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

SECTION_31_CROSSLINKS: tuple[str, ...] = (
    TRADING_LOGIC_MANIFEST_NAME,
    "MASTER_V2_DECISION_AUTHORITY_MAP_V1.md",
    "MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md",
    "MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md",
    "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md",
    "MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md",
    "MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md",
    "MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md",
    "MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md",
    "PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md",
)

_BANNED_POSITIVE_AUTHORITY_CLAIMS: tuple[str, ...] = (
    "live authorization granted",
    "live is authorized",
    "testnet is approved",
    "paper is approved",
    "execution is authorized",
    "this contract authorizes live",
    "preflight is cleared",
    "preflight cleared",
)

_FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS: tuple[str, ...] = (
    "FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V1",
    "CANONICAL_DYNAMIC_SCOPE_ENVELOPE_V1",
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


def test_futures_dynamic_scope_envelope_contract_exists_v0() -> None:
    assert DSE_CONTRACT.is_file()
    text = _read(DSE_CONTRACT)
    assert "Futures Dynamic Scope Envelope Contract v0" in text
    assert "DOCS_TOKEN_FUTURES_DYNAMIC_SCOPE_ENVELOPE_CONTRACT_V0" in text


def test_futures_dynamic_scope_envelope_purpose_and_gap_dse_001_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "canonical docs-only owner" in lowered
    assert "dynamic scope envelope" in lowered
    assert "gap-dse-001" in lowered
    assert TRADING_LOGIC_MANIFEST_NAME in _read(DSE_CONTRACT)


def test_futures_dynamic_scope_envelope_non_authority_and_safety_posture_v0() -> None:
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


def test_futures_dynamic_scope_envelope_manifest_section_20_crosslink_v0() -> None:
    contract_text = _read(DSE_CONTRACT)
    manifest_text = _read(TRADING_LOGIC_MANIFEST)
    assert DSE_CONTRACT_NAME in manifest_text
    assert "MARKER: MANIFEST_SECTION_20_CROSSLINK_TO_THIS_CONTRACT" in contract_text
    assert TRADING_LOGIC_MANIFEST.is_file()
    manifest_block = manifest_text.split("## 20. Empfohlene Repo-Manifeste / Contracts", 1)[1]
    dse_pos = manifest_block.index(DSE_CONTRACT_NAME)
    state_switch_pos = manifest_block.index(STATE_SWITCH_CONTRACT_NAME)
    assert dse_pos < state_switch_pos, "manifest §20 must list DSE before State-Switch contract"


def test_futures_dynamic_scope_envelope_sequencing_before_state_switch_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    lowered = plain.lower()
    assert "sequencing lock" in lowered
    assert STATE_SWITCH_CONTRACT_NAME in text
    assert "first" in lowered and "manifest §20 order" in lowered
    assert "does not specify the state-switch state machine" in lowered
    assert STATE_SWITCH_CONTRACT.is_file()


def test_futures_dynamic_scope_envelope_static_vs_dynamic_scope_boundary_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "static hard limits" in lowered
    assert "dynamic scope rules" in lowered
    assert "must not expand" in lowered or "must not widen" in lowered
    assert "fixed price thresholds are insufficient" in lowered
    assert "STATIC_HARD_LIMITS_NEVER_WIDENED_BY_DYNAMIC_RULES" in _read(DSE_CONTRACT)


def test_futures_dynamic_scope_envelope_scope_capital_crosslink_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert SCOPE_CAPITAL.name in _read(DSE_CONTRACT)
    assert "deployable capital" in lowered or "deployable scope" in lowered
    assert "must not collapse" in lowered
    assert "instrument-level price/structure boundaries" in lowered
    assert SCOPE_CAPITAL.is_file()


def test_futures_dynamic_scope_envelope_killswitch_and_execution_boundaries_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "does not implement killswitch" in lowered
    assert "DYNAMIC_SCOPE_TRAIL_NOT_KILLSWITCH" in _read(DSE_CONTRACT)
    assert "do not duplicate" in lowered and "pr #3648" in lowered
    assert "not sufficient for execution" in lowered
    assert BLOCKER_REGISTER.name in _read(DSE_CONTRACT)
    assert "ENVELOPE_COMPLIANCE_NOT_LIVE_AUTHORIZATION" in _read(DSE_CONTRACT)
    assert "live_authorization: false" in lowered or "live_authorization remains false" in lowered


def test_futures_dynamic_scope_envelope_hysteresis_cooldown_confirmation_volatility_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "hysteresis" in lowered
    assert "cooldown" in lowered
    assert "confirmation_ticks" in lowered or "confirmation ticks" in lowered
    assert "chop guard" in lowered
    assert "atr_or_realized_volatility" in lowered or "realized volatility" in lowered
    assert "min_band_width" in lowered and "max_band_width" in lowered
    assert "HYSTERESIS_COOLDOWN_VOCABULARY_PRESENT" in _read(DSE_CONTRACT)
    assert "CONFIRMATION_TICKS_VOCABULARY_PRESENT" in _read(DSE_CONTRACT)


def test_futures_dynamic_scope_envelope_trailing_and_candidate_confirmed_events_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    lowered = plain.lower()
    assert "trailing scope bands" in lowered
    assert "scope drift" in lowered or "scope trail" in lowered
    assert "TRAILING_SCOPE_BANDS_VOCABULARY_PRESENT" in text
    for event in (
        "DOWNSCOPE_CANDIDATE",
        "DOWNSCOPE_CONFIRMED",
        "UPSCOPE_CANDIDATE",
        "UPSCOPE_CONFIRMED",
    ):
        assert event in text
    assert "alone authorize State-Switch" in plain
    assert "CANDIDATE_VS_CONFIRMED_SCOPE_EVENTS_DISTINCT" in text
    assert "STATE_SWITCH_CONSUMES_CONFIRMED_SCOPE_EVENTS_ONLY" in text


def test_futures_dynamic_scope_envelope_hot_path_governance_boundary_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "hot-path boundary" in lowered or "hot path" in lowered
    assert "no heavy recompute" in lowered
    assert "HOT_PATH_NO_HEAVY_RECOMPUTE" in _read(DSE_CONTRACT)
    assert "o(1)" in lowered or "lightweight hot-path" in lowered


def test_futures_dynamic_scope_envelope_futures_input_and_pure_stack_crosslinks_v0() -> None:
    text = _read(DSE_CONTRACT)
    assert FUTURES_INPUT_READ_MODEL.name in text
    assert FUTURES_INPUT_PRODUCER.name in text
    assert PURE_STACK_MAP.name in text
    assert "ready_for_dynamic_scope" in text
    assert "FUTURES_INPUT_READY_FOR_DYNAMIC_SCOPE_CROSSLINK" in text
    assert FUTURES_INPUT_READ_MODEL.is_file()
    assert FUTURES_INPUT_PRODUCER.is_file()
    assert PURE_STACK_MAP.is_file()
    assert "not a running runtime state machine" in _plain(DSE_CONTRACT).lower()


def test_futures_dynamic_scope_envelope_section_31_crosslink_targets_exist_v0() -> None:
    text = _read(DSE_CONTRACT)
    for filename in SECTION_31_CROSSLINKS:
        assert filename in text, f"missing §31 crosslink to {filename!r}"
    for path in (
        TRADING_LOGIC_MANIFEST,
        DECISION_AUTHORITY_MAP,
        SCOPE_CAPITAL,
        PURE_STACK_MAP,
        FUTURES_INPUT_READ_MODEL,
        FUTURES_INPUT_PRODUCER,
        ARITHMETIC_SURVIVAL,
        CAPITAL_SLOT,
        BLOCKER_REGISTER,
        PREFLIGHT_CONTRACT,
    ):
        assert path.is_file(), path


def test_futures_dynamic_scope_envelope_ai_dashboard_strategy_boundaries_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    lowered = plain.lower()
    assert LEARNING_INVENTORY.name in text
    assert STRATEGY_INTEGRATION.name in text
    assert "display ≠ freigabe" in plain or ("display" in lowered and "freigabe" in lowered)
    assert "no hot-path envelope recomputation" in lowered
    assert LEARNING_INVENTORY.is_file()
    assert STRATEGY_INTEGRATION.is_file()


def test_futures_dynamic_scope_envelope_machine_markers_section_27_v0() -> None:
    text = _read(DSE_CONTRACT)
    assert "## 27. Machine markers (for GAP-DSE-STATIC-001)" in text
    for marker in MACHINE_MARKERS:
        assert marker in text, f"missing machine marker: {marker!r}"


def test_futures_dynamic_scope_envelope_gap_static_001_and_staging_sections_v0() -> None:
    text = _read(DSE_CONTRACT)
    plain = _plain(DSE_CONTRACT)
    assert "GAP-DSE-STATIC-001" in text
    assert THIS_MODULE in text.replace("&#47;", "/")
    assert "## 25. Validation / future tests pointer" in text
    assert "## 26. Implementation staging" in text
    assert "Static-contract tests" in text or "static-contract tests" in plain.lower()
    assert "State-Switch contract" in text


def test_futures_dynamic_scope_envelope_stop_conditions_v0() -> None:
    text = _plain(DSE_CONTRACT)
    lowered = text.lower()
    assert "## 30. stop conditions" in lowered
    assert "stop immediately if" in lowered
    assert "widening static hard limits" in lowered
    assert "state-switch contract drafted before this contract merged" in lowered


def test_futures_dynamic_scope_envelope_has_no_positive_authority_claims_v0() -> None:
    lowered = _lower(DSE_CONTRACT)
    for claim in _BANNED_POSITIVE_AUTHORITY_CLAIMS:
        assert claim not in lowered, f"forbidden positive authority claim: {claim!r}"
    for required in (
        "non-authorizing",
        "live_authorization: false",
        "preflight remains blocked",
        "does not authorize execution",
    ):
        assert required in lowered


def test_futures_dynamic_scope_envelope_no_duplicate_canonical_owner_candidates_v0() -> None:
    matches: list[Path] = []
    for fragment in _FORBIDDEN_DUPLICATE_OWNER_FRAGMENTS:
        matches.extend(SPECS.glob(f"*{fragment}*"))
    assert matches == [], f"duplicate canonical owner candidates: {matches}"

    dse_matches = list(SPECS.glob("*FUTURES_DYNAMIC_SCOPE_ENVELOPE*"))
    assert dse_matches == [DSE_CONTRACT], (
        f"unexpected dynamic scope envelope owner set: {dse_matches}"
    )


def test_futures_dynamic_scope_envelope_reciprocal_remote_runtime_docs_guard_v0() -> None:
    guard_text = REMOTE_RUNTIME_DOCS_GUARD.read_text(encoding="utf-8")
    assert THIS_MODULE in guard_text
    owner_text = Path(__file__).read_text(encoding="utf-8")
    assert "test_remote_runtime_contract_docs_guard_v0.py" in owner_text
