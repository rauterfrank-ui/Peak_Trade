"""Cross-sectional relative-strength v0 versioned research binding materializer.

Completes and ratifies the full offline research binding contract for
strategy_id=cross_sectional_relative_strength, strategy_version=v0.
Wires PIT universe, dataset, period, cost, execution, and economic policy
bindings to existing repo owners without parallel stacks.

Research-only; no economic evaluation, runtime, orders, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_ranking_semantics_binding_v0 import (
    ATTESTED_OPERATOR_DECISION_DIGEST,
    EXTERNAL_BINDING_KEYS,
    HYPOTHESIS_ID,
    ORCHESTRATOR_OWNER,
    RATIFIED_OPERATOR_BINDING_VALUES,
    SCHEMA_VERSION,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    BindingFieldStatus,
    apply_ratified_operator_bindings_v0,
    compute_config_digest_v0,
    materialize_cross_sectional_ranking_semantics_binding_v0,
    materialize_versioned_cross_sectional_ranking_semantics_binding_v0,
    serialize_versioned_binding_artifact_json_v0,
)
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_score_v0 import (
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    MANIFEST_ARTIFACT_ID,
    UNIVERSE_ID,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_VERSIONED_RESEARCH_BINDING_V0=true"
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = "cross_sectional_relative_strength_v0_versioned_research_binding.v0"
CONFIG_REL_PATH = (
    "config/research/cross_sectional_relative_strength_v0_versioned_research_binding_v0.json"
)

STRATEGY_ID = "cross_sectional_relative_strength"
STRATEGY_VERSION = "v0"
RESEARCH_HYPOTHESIS_ID = HYPOTHESIS_ID

PIT_UNIVERSE_MANIFEST_REF = f"pit_futures_universe_manifest_v1:{MANIFEST_ARTIFACT_ID}"
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
PANEL_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"
PANEL_DATASET_MANIFEST_REF = f"pit_okx_pt1h_panel_ohlcv_dataset_v1:{PANEL_DATASET_ID}:v1"
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{PANEL_DATASET_ID}:v1"
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

WALK_FORWARD_POLICY_VERSION = "walk_forward_v1"
MONTE_CARLO_POLICY_VERSION = "monte_carlo_v1"
MONTE_CARLO_RUNS = 64
MONTE_CARLO_SEED = 42
STRESS_POLICY_VERSION = "stress_class_suite_v1"
PARAMETER_SENSITIVITY_POLICY_VERSION = "parameter_sensitivity_v1"

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


@dataclass(frozen=True)
class VersionedResearchBindingResultV0:
    verdict: BindingMaterializationVerdict
    binding: dict[str, Any]
    ranking_semantics_binding: dict[str, Any]
    validation_verdict: ValidationVerdict
    fail_reasons: tuple[str, ...]


def _field_bound(*, value: Any = None, ref: str = "") -> dict[str, Any]:
    payload: dict[str, Any] = {"status": BindingFieldStatus.BOUND.value}
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
            "module": "cross_sectional_relative_strength_v0_versioned_research_binding_v0",
            "orchestrator": ORCHESTRATOR_OWNER,
            "score_formula_version": SCORE_FORMULA_VERSION,
            "schema_version": BINDING_SCHEMA_VERSION,
        }
    )


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        "parameters": dict(RATIFIED_OPERATOR_BINDING_VALUES),
        "score_formula_version": SCORE_FORMULA_VERSION,
        "score_formula_expression": SCORE_FORMULA_EXPRESSION,
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
        "universe_policy_id": UNIVERSE_POLICY_ID,
        "universe_policy_version": UNIVERSE_POLICY_VERSION,
        "universe_id": UNIVERSE_ID,
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "pit_eligibility_semantics": "per_score_epoch_finalized_bar_close",
        "listing_timestamp_required": True,
        "delisting_handling": "exclude_at_score_epoch",
        "data_availability_required": True,
        "minimum_history_bars": 21,
        "minimum_eligible_member_count": 5,
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "duplicate_instrument_rejection": True,
        "inactive_instrument_handling": "exclude_at_score_epoch",
        "staleness_policy": "max_bar_staleness_bars_enforced",
        "bitcoin_exclusion_rules": "fail_closed_btc_xbt_bitcoin_tokens",
        "survivorship_bias_forbidden": True,
        "stable_universe_digest_required": True,
    }


def build_panel_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": PANEL_DATASET_ID,
        "dataset_version": "v1",
        "bar_interval": "PT1H",
        "panel_schema": "pit_okx_pt1h_panel_ohlcv_dataset_manifest_v1",
        "instrument_key": "instrument_id",
        "timestamp_key": "timestamp_utc",
        "timezone": "UTC",
        "ohlcv_fields": ("open", "high", "low", "close", "volume"),
        "price_usage": "close_for_score_computation",
        "missing_bars_policy": "exclude_non_selected_for_epoch",
        "duplicate_bars_policy": "fail_closed",
        "out_of_order_bars_policy": "fail_closed",
        "staleness_policy": "max_bar_staleness_bars_enforced",
        "warmup_bars": 21,
        "contract_lifecycle_semantics": "pit_lifecycle_registry_bound",
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "panel_ohlcv_dataset_manifest_ref": PANEL_DATASET_MANIFEST_REF,
        "ingestion_contract_version": "okx_public_pt1h_panel_ingest.v1",
        "data_provenance": "versioned_offline_panel_manifest_only",
        "network_access_forbidden": True,
        "credential_access_forbidden": True,
    }


def build_period_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v1",
        "period_binding_id": PERIOD_BINDING_ID,
        "split_policy_id": PERIOD_BINDING_ID,
        "split_timezone": "UTC",
        "boundary_semantics": "utc_bar_close_inclusive_end",
        "warmup_start": "2024-05-25T00:00:00Z",
        "warmup_end": "2024-05-30T19:00:00Z",
        "training_start": "2024-05-30T20:00:00Z",
        "training_end": "2024-05-31T08:00:00Z",
        "validation_start": "2024-05-31T10:00:00Z",
        "validation_end": "2024-05-31T16:00:00Z",
        "out_of_sample_start": "2024-05-31T18:00:00Z",
        "out_of_sample_end": "2024-06-01T01:00:00Z",
        "embargo_duration": "PT2H",
        "purge_duration": "PT2H",
        "periods_frozen_before_evaluation": True,
        "no_overlap_enforced": True,
        "holdout_isolation_enforced": True,
    }


def build_instrument_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "selection_mode": "single_top1_by_score_desc",
        "direction_policy": "symmetric_top1_sign",
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "synthetic_spot_excluded": True,
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
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
        "walk_forward_policy_binding": {
            "policy_version": WALK_FORWARD_POLICY_VERSION,
        },
        "monte_carlo_policy_binding": {
            "policy_version": MONTE_CARLO_POLICY_VERSION,
            "runs": MONTE_CARLO_RUNS,
            "seed": MONTE_CARLO_SEED,
        },
        "stress_policy_binding": {
            "policy_version": STRESS_POLICY_VERSION,
        },
        "parameter_sensitivity_policy_binding": {
            "policy_version": PARAMETER_SENSITIVITY_POLICY_VERSION,
        },
        "policy_lowering_forbidden": True,
        "promising_is_not_pass": True,
    }


def apply_complete_external_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    """Apply all ratified external bindings to ranking semantics binding."""
    result = deepcopy(binding)
    external = result["external_bindings"]
    external["pit_universe_manifest_ref"] = _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF)
    external["instrument_id_canonicalization_version"] = _field_bound(
        value=INSTRUMENT_ID_CANONICALIZATION_VERSION
    )
    external["panel_ohlcv_dataset_manifest_ref"] = _field_bound(ref=PANEL_DATASET_MANIFEST_REF)
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
    data_contract_digest = _stable_digest(
        {
            "dataset_id": PANEL_DATASET_ID,
            "panel_manifest_ref": PANEL_DATASET_MANIFEST_REF,
            "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        }
    )
    binding_digest = _stable_digest(
        {
            "config_digest": config_digest,
            "data_contract_digest": data_contract_digest,
            "implementation_digest": impl_digest,
            "operator_decision_digest": ATTESTED_OPERATOR_DECISION_DIGEST,
        }
    )

    digest = result["digest_bindings"]
    digest["implementation_digest"] = _field_bound(value=impl_digest)
    digest["config_digest"] = _field_bound(value=config_digest)
    digest["data_digest"] = _field_bound(value=data_contract_digest)

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
    """Materialize the complete versioned research binding envelope."""
    base_envelope = materialize_versioned_cross_sectional_ranking_semantics_binding_v0()
    complete_binding = apply_complete_external_bindings_v0(base_envelope["binding"])
    binding_digest = complete_binding.pop("_binding_digest", "")

    validation = validate_cross_sectional_ranking_semantics_binding_v0(complete_binding)

    envelope = {
        "artifact_kind": "cross_sectional_relative_strength_v0_versioned_research_binding",
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
        "data_contract_digest": complete_binding["digest_bindings"]["data_digest"]["value"],
        "binding_digest": binding_digest,
        "binding": complete_binding,
        "validation_verdict": validation.verdict.value,
    }
    return envelope


def materialize_and_validate_versioned_research_binding_v0() -> VersionedResearchBindingResultV0:
    envelope = materialize_versioned_research_binding_v0()
    binding = envelope["binding"]
    validation = validate_cross_sectional_ranking_semantics_binding_v0(binding)
    if not validation.valid:
        return VersionedResearchBindingResultV0(
            verdict=BindingMaterializationVerdict.REJECTED,
            binding=envelope,
            ranking_semantics_binding=binding,
            validation_verdict=validation.verdict,
            fail_reasons=validation.fail_reasons,
        )
    if validation.verdict == ValidationVerdict.ACCEPTED_COMPLETE:
        verdict = BindingMaterializationVerdict.COMPLETE
    else:
        verdict = BindingMaterializationVerdict.INCOMPLETE
    return VersionedResearchBindingResultV0(
        verdict=verdict,
        binding=envelope,
        ranking_semantics_binding=binding,
        validation_verdict=validation.verdict,
        fail_reasons=validation.fail_reasons,
    )


def serialize_versioned_research_binding_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_versioned_research_binding_config_v0(repo_root: Path) -> Path:
    """Write config artifact and updated ranking semantics binding to repo."""
    envelope = materialize_versioned_research_binding_v0()
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        serialize_versioned_research_binding_json_v0(envelope),
        encoding="utf-8",
    )

    ranking_path = repo_root / VERSIONED_BINDING_CONFIG_REL_PATH
    ranking_envelope = materialize_versioned_cross_sectional_ranking_semantics_binding_v0()
    ranking_envelope["binding"] = envelope["binding"]
    ranking_envelope["scope_classification"]["universe_binding_effect"] = "BOUND"
    ranking_envelope["materialization_scope"] = "FULL_VERSIONED_BINDING_RATIFIED"
    ranking_path.write_text(
        serialize_versioned_binding_artifact_json_v0(ranking_envelope),
        encoding="utf-8",
    )
    return config_path
