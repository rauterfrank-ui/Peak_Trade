"""Cross-sectional funding-rate delta momentum v0 versioned research binding materializer."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_v0 import (
    ATTESTED_OPERATOR_DECISION_DIGEST,
    HYPOTHESIS_ID,
    ORCHESTRATOR_OWNER,
    SCHEMA_VERSION,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    apply_ratified_operator_bindings_v0,
    compute_config_digest_v0,
    materialize_funding_rate_delta_momentum_ranking_semantics_binding_v0,
    materialize_versioned_funding_rate_delta_momentum_ranking_semantics_binding_v0,
    serialize_versioned_binding_artifact_json_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_delta_momentum_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_scoring_v0 import (
    FUNDING_DELTA_LOOKBACK_K,
    FUNDING_SIGNAL_LAG,
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_VERSIONED_RESEARCH_BINDING_V0=true"
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = (
    "cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding.v0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0.json"
)

STRATEGY_ID = "cross_sectional_funding_rate_delta_momentum"
STRATEGY_VERSION = "v0"
RESEARCH_HYPOTHESIS_ID = HYPOTHESIS_ID

PANEL_CALENDAR_START_UTC = "2024-05-01T00:00:00Z"
PANEL_CALENDAR_END_UTC = "2024-09-01T00:00:00Z"
PANEL_WARMUP_BARS = 21
PANEL_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
PANEL_DATASET_EXTENSION = "extended_chronological_with_funding_v1"
PANEL_FUNDING_DATASET_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_funding_dataset_v1:{PANEL_DATASET_ID}:{PANEL_DATASET_EXTENSION}"
)
PIT_UNIVERSE_MANIFEST_REF = "pit_futures_universe_manifest_v1:pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{PANEL_DATASET_ID}:{PANEL_DATASET_EXTENSION}"
)
PERIOD_BINDING_ID = "pit_cross_sectional_research_chronological_holdout_v1"
PERIOD_BINDING_REF = f"{PERIOD_BINDING_ID}:v1"

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


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0",
            "orchestrator": ORCHESTRATOR_OWNER,
            "score_formula_version": SCORE_FORMULA_VERSION,
            "schema_version": BINDING_SCHEMA_VERSION,
            "narrow_adapter": "pit_okx_pt1h_panel_funding_field_materialization.v0",
        }
    )


def build_parameter_binding_v0() -> dict[str, Any]:
    from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_v0 import (
        RATIFIED_OPERATOR_BINDING_VALUES,
    )

    return {
        "binding_version": "v0",
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        "parameters": dict(RATIFIED_OPERATOR_BINDING_VALUES),
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
        "funding_delta_lookback_k": FUNDING_DELTA_LOOKBACK_K,
        "funding_signal_lag": FUNDING_SIGNAL_LAG,
        "funding_observation_field": "funding_rate",
        "parameter_search_forbidden": True,
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
        "universe_policy_id": "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe",
        "universe_policy_version": "v1",
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "minimum_eligible_member_count": 5,
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "survivorship_bias_forbidden": True,
    }


def build_panel_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": PANEL_DATASET_ID,
        "dataset_extension": PANEL_DATASET_EXTENSION,
        "dataset_version": "v1",
        "bar_interval": "PT1H",
        "panel_schema": "pit_okx_pt1h_panel_funding_dataset_manifest_v1",
        "instrument_key": "instrument_id",
        "timestamp_key": "timestamp_utc",
        "timezone": "UTC",
        "ohlcv_fields": ("open", "high", "low", "close", "volume"),
        "funding_fields": ("funding_rate",),
        "price_usage": "close_for_execution_reference_only",
        "funding_usage": "funding_rate_for_score_computation",
        "narrow_adapter": "pit_okx_pt1h_panel_funding_field_materialization.v0",
        "missing_bars_policy": "exclude_non_selected_for_epoch",
        "duplicate_bars_policy": "fail_closed",
        "out_of_order_bars_policy": "fail_closed",
        "warmup_bars": FUNDING_DELTA_LOOKBACK_K + FUNDING_SIGNAL_LAG,
        "network_access_forbidden": True,
        "credential_access_forbidden": True,
        "panel_funding_dataset_manifest_ref": PANEL_FUNDING_DATASET_MANIFEST_REF,
        "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
        "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
    }


def build_period_binding_v0() -> dict[str, Any]:
    start = _parse_utc(PANEL_CALENDAR_START_UTC)
    end = _parse_utc(PANEL_CALENDAR_END_UTC)
    total_bars = int((end - start).total_seconds() // 3600)
    warmup_end = start + timedelta(hours=PANEL_WARMUP_BARS - 1)
    post_warmup_bars = total_bars - PANEL_WARMUP_BARS
    training_bars = int(post_warmup_bars * 0.40)
    validation_bars = int(post_warmup_bars * 0.30)
    training_start = warmup_end + timedelta(hours=1)
    training_end = training_start + timedelta(hours=training_bars - 1)
    validation_start = training_end + timedelta(hours=3)
    validation_end = validation_start + timedelta(hours=validation_bars - 1)
    oos_start = validation_end + timedelta(hours=3)
    oos_end = end - timedelta(hours=1)
    return {
        "binding_version": "v1",
        "period_binding_id": PERIOD_BINDING_ID,
        "split_policy_id": PERIOD_BINDING_ID,
        "split_timezone": "UTC",
        "boundary_semantics": "utc_bar_close_inclusive_end",
        "warmup_start": _format_utc(start),
        "warmup_end": _format_utc(warmup_end),
        "training_start": _format_utc(training_start),
        "training_end": _format_utc(training_end),
        "validation_start": _format_utc(validation_start),
        "validation_end": _format_utc(validation_end),
        "out_of_sample_start": _format_utc(oos_start),
        "out_of_sample_end": _format_utc(oos_end),
        "embargo_duration": "PT2H",
        "purge_duration": "PT2H",
        "periods_frozen_before_evaluation": True,
        "no_overlap_enforced": True,
        "holdout_isolation_enforced": True,
    }


def build_instrument_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "selection_mode": "funding_delta_extremes_single_leg_rotation_v0",
        "direction_policy": "symmetric_funding_delta_extremum_mean_reversion_single_leg_rotation_v0",
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
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
    }


def build_economic_policy_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v1",
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "policy_lowering_forbidden": True,
        "promising_is_not_pass": True,
        "minimum_trade_count": 50,
    }


def apply_complete_external_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(binding)
    external = result["external_bindings"]
    external["pit_universe_manifest_ref"] = _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF)
    external["instrument_id_canonicalization_version"] = _field_bound(
        value=INSTRUMENT_ID_CANONICALIZATION_VERSION
    )
    external["panel_funding_dataset_manifest_ref"] = _field_bound(
        ref=PANEL_FUNDING_DATASET_MANIFEST_REF
    )
    external["admissibility_manifest_ref"] = _field_bound(ref=ADMISSIBILITY_MANIFEST_REF)
    external["evaluation_period_binding"] = _field_bound(ref=PERIOD_BINDING_REF)
    external["fee_model_version"] = _field_bound(value=FEE_MODEL_VERSION)
    external["slippage_model_version"] = _field_bound(value=SLIPPAGE_MODEL_VERSION)
    external["funding_model_version"] = _field_bound(value=FUNDING_MODEL_VERSION)
    external["spread_model_version"] = _field_bound(value=SPREAD_MODEL_VERSION)
    external["execution_model_version"] = _field_bound(value=EXECUTION_MODEL_VERSION)

    impl_digest = compute_implementation_digest_v0()
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
            "dataset_extension": PANEL_DATASET_EXTENSION,
            "panel_funding_manifest_ref": PANEL_FUNDING_DATASET_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
            "funding_field": "funding_rate",
            "panel_calendar_start_utc": PANEL_CALENDAR_START_UTC,
            "panel_calendar_end_utc": PANEL_CALENDAR_END_UTC,
        }
    )
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_digest": data_digest,
            "implementation_digest": impl_digest,
            "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        }
    )

    digest = result["digest_bindings"]
    digest["implementation_digest"] = _field_bound(value=impl_digest)
    digest["config_digest"] = _field_bound(value=config_digest)
    digest["data_digest"] = _field_bound(value=data_digest)

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
    base = materialize_funding_rate_delta_momentum_ranking_semantics_binding_v0()
    with_numeric = apply_ratified_operator_bindings_v0(base)
    complete_binding = apply_complete_external_bindings_v0(with_numeric)
    binding_digest = complete_binding.pop("_binding_digest", "")
    validation = validate_funding_rate_delta_momentum_ranking_semantics_binding_v0(complete_binding)
    return {
        "artifact_kind": "cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding",
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "hypothesis_frozen": True,
        "non_authorizing": True,
        "research_binding_only": True,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
        },
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
        "binding_digest": binding_digest,
        "binding": complete_binding,
        "validation_verdict": validation.verdict.value,
    }


def materialize_and_validate_versioned_research_binding_v0() -> VersionedResearchBindingResultV0:
    envelope = materialize_versioned_research_binding_v0()
    binding = envelope["binding"]
    validation = validate_funding_rate_delta_momentum_ranking_semantics_binding_v0(binding)
    if not validation.valid:
        return VersionedResearchBindingResultV0(
            verdict=BindingMaterializationVerdict.REJECTED,
            ratification_status=BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED,
            binding=envelope,
            ranking_semantics_binding=binding,
            validation_verdict=validation.verdict,
            fail_reasons=validation.fail_reasons,
        )
    if validation.verdict == ValidationVerdict.ACCEPTED_COMPLETE:
        verdict = BindingMaterializationVerdict.COMPLETE
        ratification = BindingRatificationStatus.BINDINGS_RATIFIED
    else:
        verdict = BindingMaterializationVerdict.INCOMPLETE
        ratification = BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED
    return VersionedResearchBindingResultV0(
        verdict=verdict,
        ratification_status=ratification,
        binding=envelope,
        ranking_semantics_binding=binding,
        validation_verdict=validation.verdict,
        fail_reasons=validation.fail_reasons,
    )


def serialize_versioned_research_binding_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_versioned_research_binding_artifacts_v0(repo_root: Path) -> tuple[Path, Path]:
    envelope = materialize_versioned_research_binding_v0()
    ranking_envelope = (
        materialize_versioned_funding_rate_delta_momentum_ranking_semantics_binding_v0()
    )
    config_path = repo_root / CONFIG_REL_PATH
    ranking_path = repo_root / VERSIONED_BINDING_CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    ranking_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(serialize_versioned_research_binding_json_v0(envelope), encoding="utf-8")
    ranking_path.write_text(
        serialize_versioned_binding_artifact_json_v0(ranking_envelope),
        encoding="utf-8",
    )
    return config_path, ranking_path
