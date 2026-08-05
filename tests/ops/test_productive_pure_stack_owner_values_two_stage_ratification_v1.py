"""Static contract: Pure-Stack Owner Values two-stage ratification v1.

Docs/manifest-only. Non-authorizing. No runtime, orders, archive, or dashboard mutation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_OPS = REPO_ROOT / "docs" / "ops"

TWO_STAGE = DOCS_OPS / "PRODUCTIVE_PURE_STACK_OWNER_VALUES_TWO_STAGE_RATIFICATION_V1.md"
CALIBRATION = DOCS_OPS / "PRODUCTIVE_PURE_STACK_NUMERIC_POLICY_CALIBRATION_PROTOCOL_V1.md"
MANIFEST = DOCS_OPS / "PRODUCTIVE_PURE_STACK_OWNER_VALUES_STRUCTURAL_MANIFEST_V1.json"
PARENT = DOCS_OPS / "PRODUCTIVE_PURE_STACK_INPUT_AUTHORITIES_OWNER_RATIFICATION_V1.md"
HOST_CONSTANTS = (
    REPO_ROOT
    / "src"
    / "ops"
    / "productive_pure_stack_display_decision_host_binding_v1"
    / "constants_v1.py"
)

ALLOWED_CATEGORIES = frozenset(
    {
        "STRUCTURAL_RATIFIED",
        "MECHANICALLY_COUPLED",
        "NUMERIC_CALIBRATION_REQUIRED",
        "DEFERRED_FAIL_CLOSED",
    }
)

EXPECTED_TOKENS: tuple[str, ...] = (
    "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS",
    "OWNER_VALUE_REALIZED_VOLATILITY_HORIZON",
    "OWNER_VALUE_REALIZED_VOLATILITY_UNIT",
    "OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID",
    "OWNER_VALUE_ATR_OR_RANGE_WINDOW",
    "OWNER_VALUE_ATR_OR_RANGE_UNIT",
    "OWNER_VALUE_ATR_OR_RANGE_FORMULA_ID",
    "OWNER_VALUE_VOLATILITY_REGIME_TAXONOMY_ID",
    "OWNER_VALUE_OPPORTUNITY_SCORE_SCALE",
    "OWNER_VALUE_OPPORTUNITY_SCORE_FORMULA_ID",
    "OWNER_VALUE_ACTIVITY_OR_INACTIVITY_SCORE_FORMULA_ID",
    "OWNER_VALUE_LIQUIDITY_SPREAD_SOURCE_FORMULA_ID",
    "OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID",
    "OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE",
    "OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER",
    "OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS",
    "OWNER_VALUE_STRATEGY_SIDE_DECLARATION_SCHEMA_ID",
    "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT",
    "OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION",
    "OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE",
    "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP",
    "OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM",
    "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE",
    "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE",
)

STRUCTURAL_EXPECTED: frozenset[str] = frozenset(
    {
        "OWNER_VALUE_REALIZED_VOLATILITY_HORIZON",
        "OWNER_VALUE_REALIZED_VOLATILITY_UNIT",
        "OWNER_VALUE_REALIZED_VOLATILITY_FORMULA_ID",
        "OWNER_VALUE_ATR_OR_RANGE_WINDOW",
        "OWNER_VALUE_ATR_OR_RANGE_UNIT",
        "OWNER_VALUE_ATR_OR_RANGE_FORMULA_ID",
        "OWNER_VALUE_VOLATILITY_REGIME_TAXONOMY_ID",
        "OWNER_VALUE_OPPORTUNITY_SCORE_SCALE",
        "OWNER_VALUE_OPPORTUNITY_SCORE_FORMULA_ID",
        "OWNER_VALUE_ACTIVITY_OR_INACTIVITY_SCORE_FORMULA_ID",
        "OWNER_VALUE_LIQUIDITY_SPREAD_SOURCE_FORMULA_ID",
        "OWNER_VALUE_SEQUENCE_PATH_SURVIVAL_RATIO_DEFINITION_ID",
        "OWNER_VALUE_SEQUENCE_METRIC_SET_DEFINITION_ID",
        "OWNER_VALUE_STRATEGY_SIDE_DECLARATION_SCHEMA_ID",
        "OWNER_VALUE_CAPITAL_SLOT_TIME_QUANTUM",
    }
)

NUMERIC_EXPECTED: frozenset[str] = frozenset(
    {
        "OWNER_VALUE_FUTURES_INPUT_FRESHNESS_MAX_AGE_SECONDS",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_PATH_SURVIVAL_RATIO",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EARLY_LOSS_TOXICITY",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_MARGIN_BUFFER_AT_RISK_99",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_SEQUENCE_FRAGILITY_INDEX",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_LIQUIDATION_NEAR_MISS_RATE",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_GOVERNANCE_BREACH_FREQUENCY",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_CHOP_SWITCH_SURVIVAL_SCORE",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_EFFECTIVE_LEVERAGE",
        "OWNER_VALUE_SURVIVAL_LIMIT_MIN_LIQUIDATION_BUFFER",
        "OWNER_VALUE_SURVIVAL_LIMIT_MAX_ADVERSE_FILL_LOSS",
        "OWNER_VALUE_CAPITAL_SLOT_PROFIT_STEP_PCT",
        "OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION",
        "OWNER_VALUE_CAPITAL_SLOT_MIN_REALIZED_VOLATILITY",
        "OWNER_VALUE_CAPITAL_SLOT_MIN_ATR_OR_RANGE",
        "OWNER_VALUE_CAPITAL_SLOT_MAX_TIME_WITHOUT_CASHFLOW_STEP",
        "OWNER_VALUE_CAPITAL_SLOT_MIN_OPPORTUNITY_SCORE",
        "OWNER_VALUE_CAPITAL_SLOT_INITIAL_SLOT_BASE",
    }
)

FORBIDDEN_AUTHORITY_CLAIMS: tuple[str, ...] = (
    "CMC.volatility_estimate = FuturesVolatilityProfile.realized_volatility",
    "CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY=true",
    "RESULTV1_MAPPING_AUTHORIZED=true",
    "INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=true",
    "FIXTURE_SCENARIO_WEBUI_AS_AUTHORITY=true",
    "PRODUCTIVE_NUMERIC_VALUES_SET=1",
    "profit_step_pct=0.10 ratified productive",
    "min_path_survival_ratio=0.5 ratified productive",
)


def _load_manifest() -> dict:
    assert MANIFEST.is_file(), f"missing manifest: {MANIFEST}"
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _read(path: Path) -> str:
    assert path.is_file(), f"missing: {path}"
    return path.read_text(encoding="utf-8")


def test_artifacts_exist_v1() -> None:
    assert TWO_STAGE.is_file()
    assert CALIBRATION.is_file()
    assert MANIFEST.is_file()
    assert PARENT.is_file()


def test_exactly_34_tokens_classified_v1() -> None:
    manifest = _load_manifest()
    tokens = manifest["tokens"]
    assert len(EXPECTED_TOKENS) == 34
    assert int(manifest["token_count"]) == 34
    assert len(tokens) == 34
    names = [t["token"] for t in tokens]
    assert names == list(EXPECTED_TOKENS)
    assert len(set(names)) == 34


def test_categories_exact_partition_v1() -> None:
    manifest = _load_manifest()
    by_cat: dict[str, list[str]] = {c: [] for c in ALLOWED_CATEGORIES}
    for entry in manifest["tokens"]:
        cat = entry["category"]
        assert cat in ALLOWED_CATEGORIES
        by_cat[cat].append(entry["token"])
        assert "productive_numeric_value" in entry
        assert entry["productive_numeric_value"] is None

    assert set(by_cat["STRUCTURAL_RATIFIED"]) == STRUCTURAL_EXPECTED
    assert by_cat["MECHANICALLY_COUPLED"] == ["OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION"]
    assert set(by_cat["NUMERIC_CALIBRATION_REQUIRED"]) == NUMERIC_EXPECTED
    assert by_cat["DEFERRED_FAIL_CLOSED"] == []
    counts = manifest["category_counts"]
    assert counts["STRUCTURAL_RATIFIED"] == 15
    assert counts["MECHANICALLY_COUPLED"] == 1
    assert counts["NUMERIC_CALIBRATION_REQUIRED"] == 18
    assert counts["DEFERRED_FAIL_CLOSED"] == 0


def test_reinvest_coupled_exclusively_from_lock_v1() -> None:
    manifest = _load_manifest()
    reinvest = next(
        t for t in manifest["tokens"] if t["token"] == "OWNER_VALUE_CAPITAL_SLOT_REINVEST_FRACTION"
    )
    assert reinvest["category"] == "MECHANICALLY_COUPLED"
    assert reinvest["coupling_rule"] == "1 - OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION"
    assert reinvest["productive_numeric_value"] is None
    two_stage = _read(TWO_STAGE)
    assert "COUPLING_RULE=1 - OWNER_VALUE_CAPITAL_SLOT_CASHFLOW_LOCK_FRACTION" in two_stage
    assert "Independent reinvest values are invalid" in two_stage


def test_no_fixture_scenario_webui_or_cmc_alias_ratified_v1() -> None:
    two_stage = _read(TWO_STAGE)
    calibration = _read(CALIBRATION)
    manifest = _read(MANIFEST)
    blob = "\n".join([two_stage, calibration, manifest])
    for claim in FORBIDDEN_AUTHORITY_CLAIMS:
        assert claim not in blob, f"forbidden claim present: {claim}"
    assert "CMC_VOLATILITY_ESTIMATE_AS_REALIZED_VOLATILITY=false" in two_stage
    assert "CMC.volatility_estimate != FuturesVolatilityProfile.realized_volatility" in two_stage
    assert "FIXTURE_SCENARIO_WEBUI_AS_AUTHORITY=false" in two_stage
    assert "Forbidden" in calibration or "FORBIDDEN" in calibration
    assert "fixture" in calibration.lower()


def test_no_productive_numeric_threshold_set_v1() -> None:
    manifest = _load_manifest()
    assert int(manifest["productive_numeric_values_set"]) == 0
    for entry in manifest["tokens"]:
        assert entry["productive_numeric_value"] is None
    two_stage = _read(TWO_STAGE)
    assert "PRODUCTIVE_NUMERIC_VALUES_SET=0" in two_stage
    assert "STATUS=STAGE1_STRUCTURAL_RATIFIED_STAGE2_CALIBRATION_PROTOCOL_ONLY" in two_stage
    calibration = _read(CALIBRATION)
    assert "PRODUCTIVE_NUMERIC_VALUES_SET=0" in calibration
    assert "AUTO_PROMOTION_TO_PRODUCTIVE_CONFIG=false" in calibration


def test_input_authority_flags_remain_false_v1() -> None:
    constants = _read(HOST_CONSTANTS)
    for flag in (
        "INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT = False",
        "INPUT_AUTHORITY_SURVIVAL_ENVELOPE = False",
        "INPUT_AUTHORITY_SUITABILITY_PROJECTION = False",
        "INPUT_AUTHORITY_CAPITAL_SLOT_CONFIG = False",
        "INPUT_AUTHORITY_CAPITAL_SLOT_STATE_INIT = False",
        "RESULTV1_MAPPING_AUTHORIZED = False",
        'DASHBOARD_ROLE = "READ_ONLY_CONSUMER"',
    ):
        assert flag in constants, f"host constant drift: {flag}"
    two_stage = _read(TWO_STAGE)
    assert "INPUT_AUTHORITY_FUTURES_INPUT_SNAPSHOT=false" in two_stage
    assert "RESULTV1_MAPPING_AUTHORIZED=false" in two_stage
    assert "DASHBOARD_ROLE=READ_ONLY_CONSUMER" in two_stage
    assert "STAGE1_PRODUCERS_PRODUCTIVE_ACTIVATION=false" in two_stage


def test_parent_tokens_covered_exactly_v1() -> None:
    parent = _read(PARENT)
    parent_tokens = re.findall(r"^OWNER_VALUE_[A-Z0-9_]+$", parent, re.MULTILINE)
    assert sorted(parent_tokens) == sorted(EXPECTED_TOKENS)
    assert len(parent_tokens) == 34


def test_calibration_protocol_required_elements_v1() -> None:
    text = _read(CALIBRATION)
    required = (
        "Versioned dataset / observation provenance",
        "Instrument and market-regime stratification",
        "Train / calibration / validation separation",
        "Walk-forward evaluation",
        "Bootstrap or Monte-Carlo",
        "Stress cases",
        "Sensitivity analysis per threshold",
        "Stability across instruments",
        "No isolated Sharpe / profit optimization",
        "Primary safety metrics",
        "Secondary economic metrics",
        "out-of-sample acceptance",
        "Separate Owner decision per productive number",
        "Full audit trail",
        "false_allow_rate",
        "path_survival",
        "liquidation_near_miss_rate",
        "ORDERS_ALLOWED=false",
        "CMC Numeric-Max-Age",
    )
    for marker in required:
        assert marker in text, f"missing calibration element: {marker}"


def test_structural_values_documented_in_two_stage_doc_v1() -> None:
    text = _read(TWO_STAGE)
    manifest = _load_manifest()
    for entry in manifest["tokens"]:
        if entry["category"] != "STRUCTURAL_RATIFIED":
            continue
        value = entry["structural_value"]
        assert value in text, f"structural value missing from doc: {value}"
        assert entry["token"] in text
