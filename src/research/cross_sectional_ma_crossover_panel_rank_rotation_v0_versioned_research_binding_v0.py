"""Cross-sectional MA-crossover panel rank-rotation v0 versioned research binding materializer."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_v0 import (
    ATTESTED_OPERATOR_DECISION_DIGEST,
    EXTERNAL_BINDING_KEYS,
    HYPOTHESIS_ID,
    ORCHESTRATOR_OWNER,
    RATIFIED_OPERATOR_BINDING_VALUES,
    SCHEMA_VERSION,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_ratified_operator_bindings_v0,
    compute_config_digest_v0,
    materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
    materialize_versioned_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
    serialize_versioned_binding_artifact_json_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1 import (
    MATERIAL_DIFFERENCE_AXES,
    TERMINAL_FAILED_BINDING_EXCLUSIONS,
    TERMINAL_UNDERLYING_CONFIG_DIGEST,
    TERMINAL_UNDERLYING_DATASET_DIGEST,
    TERMINAL_UNDERLYING_SIGNAL_BINDING,
    UNDERLYING_SIGNAL_BINDING,
    _material_difference_digest_v1,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_score_v0 import (
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_VERSIONED_RESEARCH_BINDING_V0=true"
)
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0.json"
)

STRATEGY_ID = "cross_sectional_ma_crossover_panel_rank_rotation"
STRATEGY_VERSION = "v0"
RESEARCH_HYPOTHESIS_ID = HYPOTHESIS_ID

PANEL_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_pt1h_panel"
PANEL_DATASET_DIGEST = "c753c5795ab40d26237a066702cb72a06065bfce0143440ec0ccadfe249cc0e0"
PANEL_DATA_DIGEST = "e14b0f2bb7723cacef259e1e1cb29b017cdaca060ff9dbb8c46a5204cb681dad"
LIFECYCLE_DATA_DIGEST = "e394d91f64ea5a05e181d6fbb172f1090ec10fde5eb7b35be4ea857d4a955599"
INSTRUMENT_COUNT = 399
ROW_COUNT_TOTAL = 37905
UNIVERSE_INSTRUMENTS_DIGEST = "ccc36aa52d9df3aa2067fbc0a75aea6ae33a458583ec8a15b08d69f54b8b9a8b"
INSTRUMENTS_ARTIFACT_DIGEST = "e47a6bb1d7ac072ab4b87c2f8f149d590a7023abc3489e6d6be1a225921ec91d"
SOURCE_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5078_merge_closeout_cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_"
    "dataset_materialization_v0_20260710T094803Z"
)
PANEL_STAGING_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/datasets/"
    "admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v2"
)
PHASE3_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_"
    "20260710T093500Z"
)

PANEL_DATASET_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{PANEL_DATASET_ID}:sha256:{PANEL_DATASET_DIGEST}"
)
PIT_UNIVERSE_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_universe_v1:{PANEL_DATASET_ID}:instrument_count:{INSTRUMENT_COUNT}"
)
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
INSTRUMENTS_ARTIFACT_REF = (
    f"{SOURCE_CLOSEOUT_BUNDLE}/INSTRUMENTS.json:sha256:{INSTRUMENTS_ARTIFACT_DIGEST}"
)
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{PANEL_DATASET_ID}:v2"
)
PERIOD_BINDING_ID = "pit_cross_sectional_panel_common_coverage_period.v1"
PERIOD_BINDING_REF = f"{PERIOD_BINDING_ID}:v1"
WINDOW_START_UTC = "2026-07-06T10:00:00Z"
WINDOW_END_UTC = "2026-07-10T08:00:00Z"
BAR_INTERVAL = "PT1H"
WARMUP_BARS = 51

FEE_MODEL_VERSION = "backtest_fee_taker_symmetric_v0"
FEE_BPS_PER_SIDE = 10.0
SLIPPAGE_MODEL_VERSION = "backtest_slippage_symmetric_v0"
SLIPPAGE_BPS_PER_SIDE = 5.0
FUNDING_MODEL_VERSION = "backtest_funding_perpetual_interval_v1"
SPREAD_MODEL_VERSION = "research_conservative_bps_v1"
CONSERVATIVE_HALF_SPREAD_BPS = 5.0
EXECUTION_MODEL_VERSION = "backtest_execution_v0"
EFFECTIVE_ENTRY_COST_BPS = FEE_BPS_PER_SIDE + SLIPPAGE_BPS_PER_SIDE + CONSERVATIVE_HALF_SPREAD_BPS
EFFECTIVE_EXIT_COST_BPS = EFFECTIVE_ENTRY_COST_BPS
ROUNDTRIP_COST_BPS = EFFECTIVE_ENTRY_COST_BPS + EFFECTIVE_EXIT_COST_BPS

WALK_FORWARD_POLICY_VERSION = "walk_forward_v1"
MONTE_CARLO_POLICY_VERSION = "monte_carlo_v1"
MONTE_CARLO_RUNS = 64
MONTE_CARLO_SEED = 42
STRESS_POLICY_VERSION = "stress_class_suite_v1"
PARAMETER_SENSITIVITY_POLICY_VERSION = "parameter_sensitivity_v1"

OPERATOR_GO_BINDING_RATIFICATION = (
    "GO_VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION"
)
OPERATOR_GO_ECONOMIC_EVALUATION = "GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"


class BindingMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class BindingRatificationStatus(str, Enum):
    BINDINGS_RATIFIED = "BINDINGS_RATIFIED"
    FAIL_CLOSED_NOT_RATIFIED = "FAIL_CLOSED_NOT_RATIFIED"


@dataclass(frozen=True)
class VersionedResearchBindingResultV0:
    verdict: BindingMaterializationVerdict
    ratification_status: BindingRatificationStatus
    binding: dict[str, Any]
    ranking_semantics_binding: dict[str, Any]
    validation_verdict: ValidationVerdict
    fail_reasons: tuple[str, ...]


def _field_bound(*, value: Any = None, ref: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"status": "BOUND"}
    if value is not None:
        payload["value"] = value
    if ref:
        payload["ref"] = ref
    return payload


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0",
            "orchestrator": ORCHESTRATOR_OWNER,
            "score_formula_version": SCORE_FORMULA_VERSION,
            "schema_version": BINDING_SCHEMA_VERSION,
            "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
        }
    )


def compute_material_difference_digest_v0() -> str:
    return _material_difference_digest_v1()


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        "parameters": dict(RATIFIED_OPERATOR_BINDING_VALUES),
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
        "price_col": "close",
        "underlying_signal_strategy_id": "ma_crossover",
        "underlying_signal_strategy_version": "v1",
        "underlying_signal_binding": UNDERLYING_SIGNAL_BINDING,
        "parameter_search_forbidden": True,
        "unchanged_single_instrument_retry_forbidden": True,
    }


def build_pit_universe_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "venue": "OKX",
        "instrument_type": "LINEAR_PERPETUAL",
        "settlement_asset": "USDT",
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
        "futures_only": True,
        "universe_policy_id": (
            "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe/v1"
        ),
        "lifecycle_policy_id": "okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1",
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "instrument_count": INSTRUMENT_COUNT,
        "universe_instruments_digest": UNIVERSE_INSTRUMENTS_DIGEST,
        "instruments_artifact_ref": INSTRUMENTS_ARTIFACT_REF,
        "pit_eligibility_semantics": "per_score_epoch_finalized_bar_close",
        "minimum_eligible_member_count": 5,
        "survivorship_bias_forbidden": True,
    }


def build_panel_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v2",
        "dataset_id": PANEL_DATASET_ID,
        "dataset_version": "v2",
        "dataset_schema": "pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1",
        "dataset_digest": PANEL_DATASET_DIGEST,
        "panel_data_digest": PANEL_DATA_DIGEST,
        "lifecycle_data_digest": LIFECYCLE_DATA_DIGEST,
        "bar_interval": BAR_INTERVAL,
        "panel_staging_root": PANEL_STAGING_ROOT,
        "panel_ohlcv_dataset_manifest_ref": PANEL_DATASET_MANIFEST_REF,
        "source_closeout_bundle_ref": SOURCE_CLOSEOUT_BUNDLE,
        "phase3_closeout_evidence_ref": PHASE3_CLOSEOUT_EVIDENCE,
        "instrument_key": "instrument_id",
        "timestamp_key": "timestamp_utc",
        "timezone": "UTC",
        "ohlcv_fields": ("open", "high", "low", "close", "volume"),
        "price_usage": "close_for_ma_crossover_score_computation",
        "missing_bars_policy": "exclude_non_selected_for_epoch",
        "duplicate_bars_policy": "fail_closed",
        "out_of_order_bars_policy": "fail_closed",
        "warmup_bars": WARMUP_BARS,
        "row_count_total": ROW_COUNT_TOTAL,
        "network_access_forbidden": True,
        "credential_access_forbidden": True,
    }


def build_period_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v1",
        "period_binding_id": PERIOD_BINDING_ID,
        "period_binding_ref": PERIOD_BINDING_REF,
        "window_start_utc": WINDOW_START_UTC,
        "window_end_utc": WINDOW_END_UTC,
        "bar_interval": BAR_INTERVAL,
        "split_timezone": "UTC",
        "boundary_semantics": "utc_bar_close_inclusive_end",
        "warmup_bars": WARMUP_BARS,
        "periods_frozen_before_evaluation": True,
        "no_overlap_enforced": True,
        "holdout_isolation_enforced": True,
    }


def build_instrument_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "selection_mode": "top1_by_ma_crossover_score_desc_single_slot_rotation_v0",
        "direction_policy": "symmetric_top1_sign_ma_crossover_score_v0",
        "max_active_instruments": 1,
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
        "single_slot_rotation": True,
        "rotation_requires_reconciled_flat": True,
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "instrument_id_canonicalization_version": INSTRUMENT_ID_CANONICALIZATION_VERSION,
    }


def build_cost_execution_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "fee_model_binding": {
            "fee_model_version": FEE_MODEL_VERSION,
            "fee_bps_per_side": FEE_BPS_PER_SIDE,
        },
        "slippage_model_binding": {
            "slippage_model_version": SLIPPAGE_MODEL_VERSION,
            "slippage_bps_per_side": SLIPPAGE_BPS_PER_SIDE,
        },
        "funding_model_binding": {
            "funding_model_version": FUNDING_MODEL_VERSION,
            "bind": True,
        },
        "spread_model_binding": {
            "spread_model_version": SPREAD_MODEL_VERSION,
            "conservative_half_spread_bps": CONSERVATIVE_HALF_SPREAD_BPS,
        },
        "execution_model_binding": {
            "execution_model_version": EXECUTION_MODEL_VERSION,
            "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
            "effective_entry_cost_bps": EFFECTIVE_ENTRY_COST_BPS,
            "effective_exit_cost_bps": EFFECTIVE_EXIT_COST_BPS,
            "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        },
        "implicit_zero_cost_forbidden": True,
        "maker_rebate_assumption_forbidden": True,
    }


def build_economic_policy_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v1",
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "walk_forward_policy_binding": {"policy_version": WALK_FORWARD_POLICY_VERSION},
        "monte_carlo_policy_binding": {
            "policy_version": MONTE_CARLO_POLICY_VERSION,
            "runs": MONTE_CARLO_RUNS,
            "seed": MONTE_CARLO_SEED,
        },
        "stress_policy_binding": {"policy_version": STRESS_POLICY_VERSION},
        "parameter_sensitivity_policy_binding": {
            "policy_version": PARAMETER_SENSITIVITY_POLICY_VERSION,
        },
        "policy_lowering_forbidden": True,
        "promising_is_not_pass": True,
        "post_result_threshold_change_forbidden": True,
        "post_result_policy_change_forbidden": True,
    }


def apply_complete_external_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(binding)
    external = result["external_bindings"]
    external["pit_universe_manifest_ref"] = _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF)
    external["instrument_id_canonicalization_version"] = _field_bound(
        value=INSTRUMENT_ID_CANONICALIZATION_VERSION
    )
    external["panel_ohlcv_dataset_manifest_ref"] = _field_bound(ref=PANEL_DATASET_MANIFEST_REF)
    external["instruments_artifact_ref"] = _field_bound(ref=INSTRUMENTS_ARTIFACT_REF)
    external["admissibility_manifest_ref"] = _field_bound(ref=ADMISSIBILITY_MANIFEST_REF)
    external["evaluation_period_binding"] = _field_bound(ref=PERIOD_BINDING_REF)
    external["source_closeout_bundle_ref"] = _field_bound(ref=SOURCE_CLOSEOUT_BUNDLE)
    external["fee_model_version"] = _field_bound(value=FEE_MODEL_VERSION)
    external["slippage_model_version"] = _field_bound(value=SLIPPAGE_MODEL_VERSION)
    external["funding_model_version"] = _field_bound(value=FUNDING_MODEL_VERSION)
    external["spread_model_version"] = _field_bound(value=SPREAD_MODEL_VERSION)
    external["execution_model_version"] = _field_bound(value=EXECUTION_MODEL_VERSION)

    impl_digest = compute_implementation_digest_v0()
    material_diff_digest = compute_material_difference_digest_v0()
    config_bytes = json.dumps(
        {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "parameter_binding": build_parameter_binding_v0(),
            "pit_universe_binding": build_pit_universe_binding_v0(),
            "panel_dataset_binding": build_panel_dataset_binding_v0(),
            "period_binding": build_period_binding_v0(),
            "cost_execution_binding": build_cost_execution_binding_v0(),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    config_digest = compute_config_digest_v0(config_bytes)
    data_digest = _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "dataset_digest": PANEL_DATASET_DIGEST,
            "panel_data_digest": PANEL_DATA_DIGEST,
            "lifecycle_data_digest": LIFECYCLE_DATA_DIGEST,
            "universe_instruments_digest": UNIVERSE_INSTRUMENTS_DIGEST,
            "instruments_artifact_digest": INSTRUMENTS_ARTIFACT_DIGEST,
            "window_start_utc": WINDOW_START_UTC,
            "window_end_utc": WINDOW_END_UTC,
        }
    )
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": impl_digest,
            "material_difference_digest": material_diff_digest,
            "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        }
    )

    digest = result["digest_bindings"]
    digest["implementation_digest"] = _field_bound(value=impl_digest)
    digest["config_digest"] = _field_bound(value=config_digest)
    digest["data_digest"] = _field_bound(value=data_digest)
    digest["material_difference_digest"] = _field_bound(value=material_diff_digest)
    digest["universe_instruments_digest"] = _field_bound(value=UNIVERSE_INSTRUMENTS_DIGEST)

    status = result["binding_status"]
    status["universe_binding_status"] = "BOUND"
    status["dataset_binding_status"] = "BOUND"
    status["period_binding_status"] = "BOUND"
    status["cost_model_binding_status"] = "BOUND"
    status["digest_binding_status"] = "BOUND"
    status["overall_binding_status"] = "COMPLETE"

    result["_binding_digest"] = binding_digest
    return result


def materialize_versioned_research_binding_v0() -> dict[str, Any]:
    base = materialize_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0()
    with_numeric = apply_ratified_operator_bindings_v0(base)
    complete_binding = apply_complete_external_bindings_v0(with_numeric)
    binding_digest = complete_binding.pop("_binding_digest", "")

    validation = validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0(
        complete_binding
    )

    return {
        "artifact_kind": (
            "cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding"
        ),
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_scope": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "operator_go_token_binding_ratification": OPERATOR_GO_BINDING_RATIFICATION,
        "operator_go_token_economic_evaluation": OPERATOR_GO_ECONOMIC_EVALUATION,
        "hypothesis_frozen": True,
        "binding_ratified": True,
        "all_required_bindings_ratified": True,
        "non_authorizing": True,
        "research_binding_only": True,
        "economic_evaluation_executed": False,
        "economic_evaluation_authorized": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "unchanged_single_instrument_retry_blocked": True,
        },
        "terminal_underlying_signal_binding": TERMINAL_UNDERLYING_SIGNAL_BINDING,
        "terminal_underlying_config_digest": TERMINAL_UNDERLYING_CONFIG_DIGEST,
        "terminal_underlying_dataset_digest": TERMINAL_UNDERLYING_DATASET_DIGEST,
        "terminal_failed_binding_exclusions": list(TERMINAL_FAILED_BINDING_EXCLUSIONS),
        "material_difference_axes": list(MATERIAL_DIFFERENCE_AXES),
        "ranking_semantics_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "ranking_semantics_schema_version": SCHEMA_VERSION,
        "orchestrator_owner": ORCHESTRATOR_OWNER,
        "parameter_binding": build_parameter_binding_v0(),
        "pit_universe_binding": build_pit_universe_binding_v0(),
        "panel_dataset_binding": build_panel_dataset_binding_v0(),
        "period_binding": build_period_binding_v0(),
        "instrument_binding": build_instrument_binding_v0(),
        "cost_execution_binding": build_cost_execution_binding_v0(),
        "economic_policy_binding": build_economic_policy_binding_v0(),
        "implementation_digest": compute_implementation_digest_v0(),
        "config_digest": complete_binding["digest_bindings"]["config_digest"]["value"],
        "data_digest": complete_binding["digest_bindings"]["data_digest"]["value"],
        "material_difference_digest": complete_binding["digest_bindings"][
            "material_difference_digest"
        ]["value"],
        "binding_digest": binding_digest,
        "binding": complete_binding,
        "validation_verdict": validation.verdict.value,
    }


def materialize_and_validate_versioned_research_binding_v0() -> VersionedResearchBindingResultV0:
    envelope = materialize_versioned_research_binding_v0()
    binding = envelope["binding"]
    validation = validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0(binding)
    if not validation.valid:
        return VersionedResearchBindingResultV0(
            verdict=BindingMaterializationVerdict.REJECTED,
            ratification_status=BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED,
            binding=envelope,
            ranking_semantics_binding=binding,
            validation_verdict=validation.verdict,
            fail_reasons=validation.fail_reasons,
        )
    return VersionedResearchBindingResultV0(
        verdict=BindingMaterializationVerdict.COMPLETE,
        ratification_status=BindingRatificationStatus.BINDINGS_RATIFIED,
        binding=envelope,
        ranking_semantics_binding=binding,
        validation_verdict=validation.verdict,
        fail_reasons=validation.fail_reasons,
    )


def serialize_versioned_research_binding_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_versioned_research_binding_config_v0(repo_root: Path) -> Path:
    envelope = materialize_versioned_research_binding_v0()
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(serialize_versioned_research_binding_json_v0(envelope), encoding="utf-8")

    ranking_path = repo_root / VERSIONED_BINDING_CONFIG_REL_PATH
    ranking_envelope = (
        materialize_versioned_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0()
    )
    ranking_envelope["binding"] = envelope["binding"]
    ranking_path.write_text(
        serialize_versioned_binding_artifact_json_v0(ranking_envelope),
        encoding="utf-8",
    )
    return config_path
