"""Static contract: Productive Pure-Stack Input Authorities Owner Ratification v1.

Docs-only guard. Non-authorizing. No runtime, network, orders, or archive mutation.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RATIFICATION = (
    REPO_ROOT / "docs" / "ops" / "PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md"
)
OPTION_A = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "PRODUCTIVE_PURE_STACK_DISPLAY_DECISION_HOST_BINDING_V1_OPTION_A_OWNER_RATIFICATION_V1.md"
)

ALLOWED_STATUSES = frozenset(
    {
        "RATIFIED_FOR_IMPLEMENTATION",
        "BLOCKED_OWNER_VALUES_REQUIRED",
    }
)

REQUIRED_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_AUTHORITY_RATIFICATION",
    "STATUS=BLOCKED_OWNER_VALUES_REQUIRED",
    "DASHBOARD_ROLE=READ_ONLY_CONSUMER",
    "RESULTV1_MAPPING_AUTHORIZED=false",
    "NEW_TRADING_AUTHORITY_AUTHORIZED=false",
    "RUNTIME_IMPLEMENTED=false",
    "SOLE_TRADING_AUTHORITY=run_integrated_offline_trading_logic_replay_v1",
    "INV_NO_RESULTV1_CONVERSION=true",
    "INV_NO_NEW_TRADING_AUTHORITY=true",
    "INV_NO_ORDERS=true",
    "INV_NO_CMC_VOLATILITY_AS_REALIZED_VOLATILITY=true",
    "INV_NO_PARTIAL_COMPOSITION=true",
    "DEPENDENCY_GRAPH_COMPLETE=true",
    "DECISION_MATRIX_VERSION=1",
    "FORBIDDEN_SOURCE_CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY",
    "FORBIDDEN_SOURCE_SURVIVAL_RESULT_V1_MAPPING",
    "FORBIDDEN_SOURCE_SUITABILITY_RESULT_V1_MAPPING",
    "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
    "OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID",
    "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE",
    "PARTIAL_COMPOSITION=FORBIDDEN",
    "CMC.volatility_estimate != FuturesVolatilityProfile.realized_volatility",
)

REQUIRED_SECTIONS: tuple[str, ...] = (
    "## 5. FuturesInputSnapshot authority matrix",
    "## 6. DoublePlaySurvivalEnvelope authority matrix",
    "## 7. SuitabilityProjectionInput authority matrix",
    "## 8. CapitalSlotConfig authority matrix",
    "## 9. CapitalSlotState authority matrix",
    "## 11. Composition ratification",
    "## 12. Machine-readable decision matrix",
    "## 13. Implementation order and dependency graph",
)

REQUIRED_PURE_MODEL_PATHS: tuple[str, ...] = (
    "src/trading/master_v2/double_play_futures_input.py",
    "src/trading/master_v2/double_play_survival.py",
    "src/trading/master_v2/double_play_suitability.py",
    "src/trading/master_v2/double_play_capital_slot.py",
    "src/trading/master_v2/double_play_composition.py",
    "src/execution/paper/futures_accounting.py",
)

# Productive ratification must not adopt scenario/WebUI fixture numbers as law.
FORBIDDEN_PRODUCTIVE_LITERAL_CLAIMS: tuple[str, ...] = (
    "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT=0.10",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO=0.5",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE=0.2",
    "profit_step_pct=0.10 ratified",
    "min_path_survival_ratio=0.5 ratified",
)


def _read() -> str:
    assert RATIFICATION.is_file(), f"missing ratification doc: {RATIFICATION}"
    return RATIFICATION.read_text(encoding="utf-8")


def _plain(text: str) -> str:
    return text.replace("&#47;", "/")


def test_ratification_document_exists_v1() -> None:
    assert RATIFICATION.is_file()
    assert OPTION_A.is_file()


def test_status_is_allowed_closed_set_v1() -> None:
    text = _read()
    match = re.search(r"^STATUS=([A-Z0-9_]+)$", text, re.MULTILINE)
    assert match is not None, "STATUS= marker missing"
    assert match.group(1) in ALLOWED_STATUSES


def test_required_markers_present_v1() -> None:
    text = _read()
    for marker in REQUIRED_MARKERS:
        assert marker in text, f"missing marker: {marker}"


def test_required_sections_present_v1() -> None:
    text = _read()
    for section in REQUIRED_SECTIONS:
        assert section in text, f"missing section: {section}"


def test_decision_matrix_covers_five_input_families_v1() -> None:
    text = _read()
    for family in (
        "FuturesInputSnapshot|",
        "DoublePlaySurvivalEnvelope|",
        "SuitabilityProjectionInput|",
        "CapitalSlotConfig|",
        "CapitalSlotState|",
        "DoublePlayCompositionDecision|",
    ):
        assert family in text, f"decision matrix missing family prefix: {family}"


def test_pure_model_paths_exist_and_are_referenced_v1() -> None:
    text = _plain(_read())
    for rel in REQUIRED_PURE_MODEL_PATHS:
        assert (REPO_ROOT / rel).is_file(), f"missing pure/kernel surface: {rel}"
        assert rel in text, f"ratification must reference: {rel}"


def test_no_fixture_thresholds_claimed_as_owner_values_v1() -> None:
    text = _read().lower()
    for claim in FORBIDDEN_PRODUCTIVE_LITERAL_CLAIMS:
        assert claim.lower() not in text, f"forbidden productive literal claim: {claim}"


def test_invariants_forbid_resultv1_and_new_trading_authority_v1() -> None:
    text = _read()
    assert "RESULTV1_MAPPING_AUTHORIZED=false" in text
    assert "NEW_TRADING_AUTHORITY_AUTHORIZED=false" in text
    assert "RESULTV1_TO_PURE_STACK_MAPPING=UNAUTHORIZED" in text
    assert "NEW_TRADING_AUTHORITY=UNAUTHORIZED" in text


def test_composition_requires_full_canonical_set_v1() -> None:
    text = _read()
    assert "PARTIAL_COMPOSITION=FORBIDDEN" in text
    assert "PRESENTATION_FALLBACK=FORBIDDEN" in text
    assert "seven-Decision productive readiness" in text or "Capital Slot decisions" in text


def test_option_a_prerequisite_acknowledged_v1() -> None:
    text = _read()
    assert "OPTION_A_PREREQUISITE=MERGED_AND_CONFIRMED" in text
    assert "INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=false" in text
