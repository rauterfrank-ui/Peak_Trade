"""Canonical volatility_estimate feature contract v1 (owner ratification only).

Pure offline declarative contract owner for ratified ``volatility_estimate`` semantics
on the CanonicalMarketContextV1 feature materialization path. Does not compute
volatility, mutate datasets, change MV2 replay behavior, or authorize runtime
execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "CANONICAL_VOLATILITY_ESTIMATE_FEATURE_CONTRACT_V1=true"

CONTRACT_ID = "canonical_volatility_estimate_feature_contract"
CONTRACT_VERSION = "canonical_volatility_estimate_feature_contract/v1"
CONTRACT_OWNER = "trading.master_v2.canonical_volatility_estimate_feature_contract_v1"
CONTRACT_CONFIG_REL_PATH = (
    "config/governance/canonical_volatility_estimate_feature_contract_v1.json"
)
RATIFICATION_ID = "canonical_volatility_estimate_feature_contract_v1_owner_ratification_v0"
RATIFICATION_SCOPE = "CANONICAL_VOLATILITY_ESTIMATE_FEATURE_CONTRACT_RATIFICATION_V0"
CANONICAL_SERIALIZATION_VERSION = "canonical_volatility_feature_contract_canonical_json_v1"

FEATURE_NAME = "volatility_estimate"
FEATURE_SEMANTICS = "ROLLING_STANDARD_DEVIATION_OF_FINALIZED_MARK_PRICE_LOG_RETURNS"
IMPLEMENTATION_REUSE_DECISION = "REUSE_WITH_NARROW_ADAPTER"
REUSE_BASIS = "src/analytics/regimes.py::_compute_rolling_volatility"
REUSE_LIMITATION = "ROLLING_WINDOW_MECHANICS_ONLY"
SELECTED_CANONICAL_OWNER = "CanonicalMarketContextV1 feature materialization path"

PRIMARY_PRICE_SOURCE = "VENUE_MARK_PRICE"
PRICE_FIELD = "mark_price"
BAR_INTERVAL = "PT1M"
RETURN_DEFINITION = "LOG_RETURN"
RETURN_FORMULA = "ln(mark_price_t/mark_price_t_minus_1)"
LOOKBACK_BARS = 60
WINDOW_DURATION = "PT60M"
MIN_PERIODS = 60
DDOF = 0
ANNUALIZATION_MODE = "NONE"
ANNUALIZATION_FACTOR = 1
OUTPUT_UNIT = "PER_BAR_DECIMAL_RETURN_VOLATILITY"
OUTPUT_ANNUALIZED = False
OUTPUT_PERCENT = False

WARMUP_REQUIRED = True
WARMUP_REQUIRED_PRICE_COUNT = 61
WARMUP_REQUIRED_RETURN_COUNT = 60
WARMUP_INCOMPLETE_OUTPUT = "NULL"
WARMUP_INCOMPLETE_STATUS = "WARMUP_REQUIRED"

NULL_OR_NONPOSITIVE_MARK_PRICE = "FAIL_CLOSED_DATA_INTEGRITY_INVALID"
MISSING_BAR_POLICY = "NO_IMPLICIT_FILL"
NONCONTIGUOUS_WINDOW_POLICY = "FAIL_CLOSED_WARMUP_INVALID"
CLIPPING_POLICY = "NONE"
FLOOR_POLICY = "NONE"
IMPLICIT_DEFAULT_ALLOWED = False
MV2_FALLBACK_0_2_ADMISSIBLE = False
FINALIZED_BAR_ONLY = True
POINT_IN_TIME_ONLY = True
NO_LOOKAHEAD = True
DETERMINISTIC_SERIALIZATION_REQUIRED = True

RATIFIED_VERDICT = "PASS_CANONICAL_VOLATILITY_ESTIMATE_FEATURE_CONTRACT_V1_RATIFIED"

_VOLATILITY_FORMULA_EXPRESSION = (
    "volatility_estimate_t = population_stdev("
    "ln(mark_price_i/mark_price_{i-1}) for i in (t-LOOKBACK_BARS+1..t); "
    "ddof=0; annualization=NONE) "
    "when contiguous finalized PT1M bars provide WARMUP_REQUIRED_RETURN_COUNT log returns "
    "from WARMUP_REQUIRED_PRICE_COUNT valid mark_price observations ending at t; "
    "else NULL with warmup_status=WARMUP_REQUIRED"
)

_IMPLEMENTATION_FORBIDDEN_IN_RATIFICATION_SCOPE = frozenset(
    {
        "NO_PRODUCTIVE_IMPLEMENTATION",
        "NO_REPO_SOURCE_CODE_CHANGE_BEYOND_CONTRACT_ARTIFACTS",
        "NO_MATERIALIZER_CHANGE",
        "NO_BARS_PARQUET_REGENERATION",
        "NO_ECONOMIC_EVALUATION",
        "NO_OLS_EXECUTION",
        "NO_CONFIG_DEFAULT_CHANGE",
        "NO_CORE_TRADING_LOGIC_CHANGE",
        "NO_MASTER_V2_BEHAVIOR_CHANGE",
        "NO_DOUBLE_PLAY_CHANGE",
        "NO_SCOPE_FORMULA_CHANGE",
        "NO_RISK_SIZING_CHANGE",
        "NO_RUNTIME_EFFECT",
        "NO_AUTHORITY_EFFECT",
    }
)

_NEXT_IMPLEMENTATION_SCOPE = (
    "ADMISSIBLE_FUTURES_VOLATILITY_ESTIMATE_SOURCE_PERSISTENCE_V0_IMPLEMENTATION"
)


class CanonicalVolatilityFeatureContractError(ValueError):
    """Fail-closed canonical volatility feature contract error."""


class RatificationVerdict(str, Enum):
    PASS_CANONICAL_VOLATILITY_ESTIMATE_FEATURE_CONTRACT_V1_RATIFIED = (
        "PASS_CANONICAL_VOLATILITY_ESTIMATE_FEATURE_CONTRACT_V1_RATIFIED"
    )


@dataclass(frozen=True)
class CanonicalVolatilityFeatureContractV1:
    contract_id: str
    contract_version: str
    feature_name: str
    feature_semantics: str
    implementation_reuse_decision: str
    reuse_basis: str
    reuse_limitation: str
    selected_canonical_owner: str
    primary_price_source: str
    price_field: str
    bar_interval: str
    return_definition: str
    return_formula: str
    lookback_bars: int
    window_duration: str
    min_periods: int
    ddof: int
    annualization_mode: str
    annualization_factor: int
    output_unit: str
    output_annualized: bool
    output_percent: bool
    warmup_required: bool
    warmup_required_price_count: int
    warmup_required_return_count: int
    warmup_incomplete_output: str
    warmup_incomplete_status: str
    null_or_nonpositive_mark_price: str
    missing_bar_policy: str
    noncontiguous_window_policy: str
    clipping_policy: str
    floor_policy: str
    implicit_default_allowed: bool
    mv2_fallback_0_2_admissible: bool
    finalized_bar_only: bool
    point_in_time_only: bool
    no_lookahead: bool
    deterministic_serialization_required: bool
    owner_ratification_complete: bool
    implementation_admissible: bool
    verdict: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "contract_version": self.contract_version,
            "feature_name": self.feature_name,
            "feature_semantics": self.feature_semantics,
            "implementation_reuse_decision": self.implementation_reuse_decision,
            "reuse_basis": self.reuse_basis,
            "reuse_limitation": self.reuse_limitation,
            "selected_canonical_owner": self.selected_canonical_owner,
            "primary_price_source": self.primary_price_source,
            "price_field": self.price_field,
            "bar_interval": self.bar_interval,
            "return_definition": self.return_definition,
            "return_formula": self.return_formula,
            "lookback_bars": self.lookback_bars,
            "window_duration": self.window_duration,
            "min_periods": self.min_periods,
            "ddof": self.ddof,
            "annualization_mode": self.annualization_mode,
            "annualization_factor": self.annualization_factor,
            "output_unit": self.output_unit,
            "output_annualized": self.output_annualized,
            "output_percent": self.output_percent,
            "warmup_required": self.warmup_required,
            "warmup_required_price_count": self.warmup_required_price_count,
            "warmup_required_return_count": self.warmup_required_return_count,
            "warmup_incomplete_output": self.warmup_incomplete_output,
            "warmup_incomplete_status": self.warmup_incomplete_status,
            "null_or_nonpositive_mark_price": self.null_or_nonpositive_mark_price,
            "missing_bar_policy": self.missing_bar_policy,
            "noncontiguous_window_policy": self.noncontiguous_window_policy,
            "clipping_policy": self.clipping_policy,
            "floor_policy": self.floor_policy,
            "implicit_default_allowed": self.implicit_default_allowed,
            "mv2_fallback_0_2_admissible": self.mv2_fallback_0_2_admissible,
            "finalized_bar_only": self.finalized_bar_only,
            "point_in_time_only": self.point_in_time_only,
            "no_lookahead": self.no_lookahead,
            "deterministic_serialization_required": self.deterministic_serialization_required,
            "owner_ratification_complete": self.owner_ratification_complete,
            "implementation_admissible": self.implementation_admissible,
            "verdict": self.verdict,
            "volatility_formula_expression": _VOLATILITY_FORMULA_EXPRESSION,
        }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def contract_config_path(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / CONTRACT_CONFIG_REL_PATH


def load_contract_config_v1(root: Path | None = None) -> dict[str, Any]:
    path = contract_config_path(root)
    if not path.is_file():
        msg = f"contract_config_missing:{path}"
        raise CanonicalVolatilityFeatureContractError(msg)
    return json.loads(path.read_text(encoding="utf-8"))


def _require_exact(payload: Mapping[str, Any], key: str, expected: Any) -> None:
    actual = payload.get(key)
    if actual != expected:
        msg = f"contract_field_mismatch:{key}:expected={expected!r}:actual={actual!r}"
        raise CanonicalVolatilityFeatureContractError(msg)


def validate_contract_config_v1(payload: Mapping[str, Any]) -> None:
    _require_exact(payload, "contract_id", CONTRACT_ID)
    _require_exact(payload, "contract_version", CONTRACT_VERSION)
    _require_exact(payload, "owner", CONTRACT_OWNER)
    _require_exact(payload, "feature_name", FEATURE_NAME)
    _require_exact(payload, "feature_semantics", FEATURE_SEMANTICS)
    _require_exact(payload, "implementation_reuse_decision", IMPLEMENTATION_REUSE_DECISION)
    _require_exact(payload, "reuse_basis", REUSE_BASIS)
    _require_exact(payload, "reuse_limitation", REUSE_LIMITATION)
    _require_exact(payload, "selected_canonical_owner", SELECTED_CANONICAL_OWNER)
    _require_exact(payload, "primary_price_source", PRIMARY_PRICE_SOURCE)
    _require_exact(payload, "price_field", PRICE_FIELD)
    _require_exact(payload, "bar_interval", BAR_INTERVAL)
    _require_exact(payload, "return_definition", RETURN_DEFINITION)
    _require_exact(payload, "return_formula", RETURN_FORMULA)
    _require_exact(payload, "lookback_bars", LOOKBACK_BARS)
    _require_exact(payload, "window_duration", WINDOW_DURATION)
    _require_exact(payload, "min_periods", MIN_PERIODS)
    _require_exact(payload, "ddof", DDOF)
    _require_exact(payload, "annualization_mode", ANNUALIZATION_MODE)
    _require_exact(payload, "annualization_factor", ANNUALIZATION_FACTOR)
    _require_exact(payload, "output_unit", OUTPUT_UNIT)
    _require_exact(payload, "output_annualized", OUTPUT_ANNUALIZED)
    _require_exact(payload, "output_percent", OUTPUT_PERCENT)
    _require_exact(payload, "warmup_required", WARMUP_REQUIRED)
    _require_exact(payload, "warmup_required_price_count", WARMUP_REQUIRED_PRICE_COUNT)
    _require_exact(payload, "warmup_required_return_count", WARMUP_REQUIRED_RETURN_COUNT)
    _require_exact(payload, "warmup_incomplete_output", WARMUP_INCOMPLETE_OUTPUT)
    _require_exact(payload, "warmup_incomplete_status", WARMUP_INCOMPLETE_STATUS)
    _require_exact(payload, "null_or_nonpositive_mark_price", NULL_OR_NONPOSITIVE_MARK_PRICE)
    _require_exact(payload, "missing_bar_policy", MISSING_BAR_POLICY)
    _require_exact(payload, "noncontiguous_window_policy", NONCONTIGUOUS_WINDOW_POLICY)
    _require_exact(payload, "clipping_policy", CLIPPING_POLICY)
    _require_exact(payload, "floor_policy", FLOOR_POLICY)
    _require_exact(payload, "implicit_default_allowed", IMPLICIT_DEFAULT_ALLOWED)
    _require_exact(payload, "mv2_fallback_0_2_admissible", MV2_FALLBACK_0_2_ADMISSIBLE)
    _require_exact(payload, "finalized_bar_only", FINALIZED_BAR_ONLY)
    _require_exact(payload, "point_in_time_only", POINT_IN_TIME_ONLY)
    _require_exact(payload, "no_lookahead", NO_LOOKAHEAD)
    _require_exact(
        payload, "deterministic_serialization_required", DETERMINISTIC_SERIALIZATION_REQUIRED
    )
    _require_exact(payload, "owner_ratification_complete", True)
    if payload.get("implementation_admissible") not in {True, False}:
        msg = "contract_field_mismatch:implementation_admissible:expected=bool:actual=invalid"
        raise CanonicalVolatilityFeatureContractError(msg)
    _require_exact(payload, "runtime_effect", False)
    _require_exact(payload, "authority_effect", "NONE")
    _require_exact(payload, "verdict", RATIFIED_VERDICT)


def parse_contract_v1(payload: Mapping[str, Any]) -> CanonicalVolatilityFeatureContractV1:
    validate_contract_config_v1(payload)
    return CanonicalVolatilityFeatureContractV1(
        contract_id=str(payload["contract_id"]),
        contract_version=str(payload["contract_version"]),
        feature_name=str(payload["feature_name"]),
        feature_semantics=str(payload["feature_semantics"]),
        implementation_reuse_decision=str(payload["implementation_reuse_decision"]),
        reuse_basis=str(payload["reuse_basis"]),
        reuse_limitation=str(payload["reuse_limitation"]),
        selected_canonical_owner=str(payload["selected_canonical_owner"]),
        primary_price_source=str(payload["primary_price_source"]),
        price_field=str(payload["price_field"]),
        bar_interval=str(payload["bar_interval"]),
        return_definition=str(payload["return_definition"]),
        return_formula=str(payload["return_formula"]),
        lookback_bars=int(payload["lookback_bars"]),
        window_duration=str(payload["window_duration"]),
        min_periods=int(payload["min_periods"]),
        ddof=int(payload["ddof"]),
        annualization_mode=str(payload["annualization_mode"]),
        annualization_factor=int(payload["annualization_factor"]),
        output_unit=str(payload["output_unit"]),
        output_annualized=bool(payload["output_annualized"]),
        output_percent=bool(payload["output_percent"]),
        warmup_required=bool(payload["warmup_required"]),
        warmup_required_price_count=int(payload["warmup_required_price_count"]),
        warmup_required_return_count=int(payload["warmup_required_return_count"]),
        warmup_incomplete_output=str(payload["warmup_incomplete_output"]),
        warmup_incomplete_status=str(payload["warmup_incomplete_status"]),
        null_or_nonpositive_mark_price=str(payload["null_or_nonpositive_mark_price"]),
        missing_bar_policy=str(payload["missing_bar_policy"]),
        noncontiguous_window_policy=str(payload["noncontiguous_window_policy"]),
        clipping_policy=str(payload["clipping_policy"]),
        floor_policy=str(payload["floor_policy"]),
        implicit_default_allowed=bool(payload["implicit_default_allowed"]),
        mv2_fallback_0_2_admissible=bool(payload["mv2_fallback_0_2_admissible"]),
        finalized_bar_only=bool(payload["finalized_bar_only"]),
        point_in_time_only=bool(payload["point_in_time_only"]),
        no_lookahead=bool(payload["no_lookahead"]),
        deterministic_serialization_required=bool(payload["deterministic_serialization_required"]),
        owner_ratification_complete=bool(payload["owner_ratification_complete"]),
        implementation_admissible=bool(payload["implementation_admissible"]),
        verdict=str(payload["verdict"]),
    )


def load_ratified_contract_v1(root: Path | None = None) -> CanonicalVolatilityFeatureContractV1:
    return parse_contract_v1(load_contract_config_v1(root))


def compute_contract_digest_v1(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def materialize_owner_ratification_v1(
    *,
    owner_operator: str = "Frank Rauter",
    source_evidence: str | None = None,
) -> dict[str, Any]:
    contract = load_ratified_contract_v1()
    config_payload = load_contract_config_v1()
    return {
        "artifact_kind": "canonical_volatility_estimate_feature_contract_owner_ratification",
        "artifact_version": "v0",
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "contract": contract.to_dict(),
        "contract_config_digest": compute_contract_digest_v1(config_payload),
        "contract_config_rel_path": CONTRACT_CONFIG_REL_PATH,
        "contract_owner": CONTRACT_OWNER,
        "implementation_admissible": False,
        "implementation_forbidden_in_ratification_scope": sorted(
            _IMPLEMENTATION_FORBIDDEN_IN_RATIFICATION_SCOPE
        ),
        "next_implementation_scope": _NEXT_IMPLEMENTATION_SCOPE,
        "next_step_requires_separate_operator_go": True,
        "owner_operator": owner_operator,
        "ratification_complete": True,
        "ratification_id": RATIFICATION_ID,
        "ratification_scope": RATIFICATION_SCOPE,
        "source_evidence": source_evidence,
        "verdict": RATIFIED_VERDICT,
    }


def materialize_normative_field_binding_v1() -> dict[str, Any]:
    contract = load_ratified_contract_v1()
    return {
        "artifact_kind": "canonical_volatility_estimate_normative_field_binding",
        "artifact_version": "v0",
        "bindings": contract.to_dict(),
        "contract_version": CONTRACT_VERSION,
        "feature_name": FEATURE_NAME,
        "scope_initialization_formula": (
            "initial_volatility_distance = volatility_estimate * finalized_mark_price"
        ),
    }


def materialize_implementation_boundary_v1() -> dict[str, Any]:
    return {
        "artifact_kind": "canonical_volatility_estimate_implementation_boundary",
        "artifact_version": "v0",
        "ratification_scope_complete": True,
        "implementation_scope": _NEXT_IMPLEMENTATION_SCOPE,
        "forbidden_in_ratification_scope": sorted(_IMPLEMENTATION_FORBIDDEN_IN_RATIFICATION_SCOPE),
        "permitted_in_next_implementation_scope": [
            "narrow_adapter_over_regimes_rolling_window_mechanics_only",
            "wire_into_stage_okx_economic_research_dataset_from_raw_staging_v1",
            "extend_admissible_versioned_futures_dataset_v1_schema_validation",
            "regenerate_inst_eth_usdt_perp_v1_minimal_lineage",
            "entry_bar_reference_snapshot_proof_for_two_target_rows",
        ],
        "explicitly_forbidden_in_next_scope_without_separate_go": [
            "change_scope_initialization_formula",
            "change_mv2_fallback_unless_proven_same_owner_and_required",
            "annualization_or_price_source_substitution",
            "implicit_default_or_constant_persistence",
        ],
    }


def materialize_test_requirements_v1() -> dict[str, Any]:
    return {
        "artifact_kind": "canonical_volatility_estimate_test_requirements",
        "artifact_version": "v0",
        "ratification_scope_tests": [
            "tests/trading/master_v2/test_canonical_volatility_estimate_feature_contract_v1.py",
        ],
        "deferred_to_implementation_scope": [
            "exact_expected_value_unit_tests",
            "no_lookahead_and_prefix_invariance_tests",
            "finalized_bar_only_tests",
            "warmup_null_tests",
            "deterministic_repeated_materialization_empty_diff",
            "dataset_schema_and_admissibility_tests",
            "entry_bar_snapshot_lookup_tests",
            "pr5147_row_materializer_tests",
        ],
    }


def assert_ratification_complete_v1() -> CanonicalVolatilityFeatureContractV1:
    contract = load_ratified_contract_v1()
    if not contract.owner_ratification_complete:
        msg = "owner_ratification_incomplete"
        raise CanonicalVolatilityFeatureContractError(msg)
    if contract.verdict != RATIFIED_VERDICT:
        msg = f"unexpected_verdict:{contract.verdict}"
        raise CanonicalVolatilityFeatureContractError(msg)
    return contract


def assert_implementation_admissible_v1() -> CanonicalVolatilityFeatureContractV1:
    contract = assert_ratification_complete_v1()
    if not contract.implementation_admissible:
        msg = "implementation_not_admissible"
        raise CanonicalVolatilityFeatureContractError(msg)
    return contract


__all__ = [
    "BAR_INTERVAL",
    "CANONICAL_SERIALIZATION_VERSION",
    "CONTRACT_CONFIG_REL_PATH",
    "CONTRACT_ID",
    "CONTRACT_OWNER",
    "CONTRACT_VERSION",
    "CanonicalVolatilityFeatureContractError",
    "CanonicalVolatilityFeatureContractV1",
    "FEATURE_NAME",
    "LOOKBACK_BARS",
    "MIN_PERIODS",
    "RATIFICATION_ID",
    "RATIFICATION_SCOPE",
    "RATIFIED_VERDICT",
    "assert_implementation_admissible_v1",
    "assert_ratification_complete_v1",
    "compute_contract_digest_v1",
    "contract_config_path",
    "load_contract_config_v1",
    "load_ratified_contract_v1",
    "materialize_implementation_boundary_v1",
    "materialize_normative_field_binding_v1",
    "materialize_owner_ratification_v1",
    "materialize_test_requirements_v1",
    "parse_contract_v1",
    "validate_contract_config_v1",
]
