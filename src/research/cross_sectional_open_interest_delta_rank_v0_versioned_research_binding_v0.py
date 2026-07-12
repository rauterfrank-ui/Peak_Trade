"""Versioned research binding for cross_sectional_open_interest_delta_rank/v0.

Binds the ratified five-instrument self-accumulated open-interest panel. Research-only;
no runtime or authority effect.
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
from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (
    CONTRACT_VERSION,
    LOOKBACK_K,
    RESEARCH_SCOPE,
    SIGNAL_LAG_BARS,
    build_pit_open_interest_semantics_contract_v0,
    pit_semantics_contract_to_dict,
)
from src.research.instrument_id_canonicalization_v1 import (
    INSTRUMENT_ID_CANONICALIZATION_VERSION,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (
    DATASET_EXTENSION,
    DATASET_ID,
    MODULE_VERSION as MATERIALIZER_MODULE_VERSION,
    PANEL_DATASET_SCHEMA,
    PANEL_ID,
    derive_target_instrument_bindings_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_and_materialization_admissibility_contract_v0 import (
    REQUIRED_CONTIGUOUS_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0 import (
    CANONICAL_UNIVERSE_BINDING,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_VERSIONED_RESEARCH_BINDING_V0=true"
BINDING_ARTIFACT_VERSION = "v0"
BINDING_SCHEMA_VERSION = "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding.v0"
CONFIG_REL_PATH = (
    "config/research/cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0.json"
)

STRATEGY_ID = "cross_sectional_open_interest_delta_rank"
STRATEGY_VERSION = "v0"
RESEARCH_HYPOTHESIS_ID = "cross_sectional_open_interest_delta_rank_v0"

PANEL_OI_MANIFEST_REF = (
    f"pit_okx_pt1h_panel_open_interest_dataset_v1:{PANEL_ID}:{DATASET_EXTENSION}"
)
PIT_UNIVERSE_MANIFEST_REF = (
    "pit_futures_universe_manifest_v1:"
    "pit_okx_linear_usdt_non_bitcoin_perpetual_universe_manifest_v1"
)
UNIVERSE_LIFECYCLE_REGISTRY_REF = "pit_futures_lifecycle_registry_v1:okx_production_lifecycle_v1"
ADMISSIBILITY_MANIFEST_REF = (
    f"pit_cross_sectional_research_dataset_envelope.v0:{DATASET_ID}:{DATASET_EXTENSION}"
)

RATIFIED_PANEL_DATASET_DIGEST = "0f57d48c40f02c3aeec9897ae7f2a43e313c01cff50dab68c8e08f879e0f2687"
RATIFIED_INSTRUMENT_UNIVERSE_DIGEST = (
    "e286db0053596e771c2168e82ff61c326f7ba1d51e90d606880237576b2c4791"
)
RATIFIED_BOUND_DATA_DIGEST = "fd2a020f055120eaa67e0087423333a41cb32b99b95076b18e3c1b50f543844a"
RATIFIED_ARCHIVE_SOURCE_DIGEST = "12647433643badc0944d71a1268969845d32f7d6b52bd4ad843ea557c8ef2cf0"

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

MATERIAL_DIFFERENCE_BASIS = (
    "cross_sectional_open_interest_delta_rank_not_funding_carry_or_funding_rank_delta"
)


class BindingMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    REJECTED = "REJECTED"


class BindingValidationVerdict(str, Enum):
    ACCEPTED_COMPLETE = "ACCEPTED_COMPLETE"
    REJECTED_INCOMPLETE = "REJECTED_INCOMPLETE"


@dataclass(frozen=True)
class VersionedResearchBindingResultV0:
    verdict: BindingMaterializationVerdict
    validation_verdict: BindingValidationVerdict
    binding: dict[str, Any]
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
            "module": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0",
            "materializer_owner": MATERIALIZER_MODULE_VERSION,
            "pit_semantics_contract_version": CONTRACT_VERSION,
            "schema_version": BINDING_SCHEMA_VERSION,
            "selection_mode": "open_interest_delta_rank_extremes_single_leg_rotation_v0",
        }
    )


def compute_material_difference_digest_v0() -> str:
    return _stable_digest(
        {
            "basis": MATERIAL_DIFFERENCE_BASIS,
            "open_interest_delta_rank_signal": True,
            "funding_carry_forbidden": True,
            "funding_rank_delta_forbidden": True,
            "self_accumulated_panel_only": True,
            "no_399_instrument_fallback": True,
        }
    )


def build_parameter_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "rank_lookback_k": LOOKBACK_K,
        "signal_lag_bars": SIGNAL_LAG_BARS,
        "minimum_panel_bars": REQUIRED_CONTIGUOUS_BARS,
        "open_interest_observation_field": "open_interest",
        "parameter_search_forbidden": True,
        "no_instrument_substitution": True,
        "no_universe_expansion": True,
        "unchanged_retry_of_failed_bindings_forbidden": True,
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
        "bitcoin_direction_allowed": False,
        "universe_policy_id": (
            "pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe"
        ),
        "universe_policy_version": "v1",
        "pit_universe_manifest_ref": PIT_UNIVERSE_MANIFEST_REF,
        "universe_lifecycle_registry_ref": UNIVERSE_LIFECYCLE_REGISTRY_REF,
        "minimum_eligible_member_count": len(CANONICAL_UNIVERSE_BINDING),
        "maximum_eligible_member_count": len(CANONICAL_UNIVERSE_BINDING),
        "instrument_identity_normalization": INSTRUMENT_ID_CANONICALIZATION_VERSION,
        "target_instrument_bindings": [
            {
                "instrument_id": inst_id,
                "native_instrument_id": native_id,
            }
            for inst_id, native_id in CANONICAL_UNIVERSE_BINDING
        ],
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
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
    }


def build_dataset_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "dataset_id": DATASET_ID,
        "dataset_extension": DATASET_EXTENSION,
        "panel_id": PANEL_ID,
        "panel_dataset_schema": PANEL_DATASET_SCHEMA,
        "panel_open_interest_manifest_ref": PANEL_OI_MANIFEST_REF,
        "admissibility_manifest_ref": ADMISSIBILITY_MANIFEST_REF,
        "source_mode": "SELF_ACCUMULATED_EFFECTIVE_ARCHIVE_VIEW",
        "materializer_owner": MATERIALIZER_MODULE_VERSION,
        "no_fallback_to_399_instrument_dataset": True,
        "panel_dataset_digest": RATIFIED_PANEL_DATASET_DIGEST,
        "bound_data_digest": RATIFIED_BOUND_DATA_DIGEST,
        "archive_source_digest": RATIFIED_ARCHIVE_SOURCE_DIGEST,
    }


def materialize_versioned_research_binding_v0() -> dict[str, Any]:
    pit_contract = build_pit_open_interest_semantics_contract_v0()
    parameter_binding = build_parameter_binding_v0()
    pit_universe_binding = build_pit_universe_binding_v0()
    dataset_binding = build_dataset_binding_v0()
    cost_binding = build_cost_execution_binding_v0()
    economic_policy = build_economic_policy_binding_v0()

    config_digest = _stable_digest(
        {
            "parameter_binding": parameter_binding,
            "pit_universe_binding": pit_universe_binding,
            "dataset_binding": dataset_binding,
        }
    )
    implementation_digest = compute_implementation_digest_v0()
    material_difference_digest = compute_material_difference_digest_v0()

    binding: dict[str, Any] = {
        "binding_status": {
            "overall_binding_status": "COMPLETE",
            "universe_binding_status": "BOUND",
            "dataset_binding_status": "BOUND",
            "digest_binding_status": "BOUND",
            "numeric_bindings_status": "BOUND",
            "cost_model_binding_status": "BOUND",
            "period_binding_status": "BOUND",
            "policy_classes_status": "BOUND",
        },
        "digest_bindings": {
            "config_digest": _field_bound(value=config_digest),
            "data_digest": _field_bound(value=RATIFIED_PANEL_DATASET_DIGEST),
            "implementation_digest": _field_bound(value=implementation_digest),
            "material_difference_digest": _field_bound(value=material_difference_digest),
            "instrument_universe_digest": _field_bound(value=RATIFIED_INSTRUMENT_UNIVERSE_DIGEST),
            "bound_data_digest": _field_bound(value=RATIFIED_BOUND_DATA_DIGEST),
        },
        "direction_semantics": {
            "selection_mode": "open_interest_delta_rank_extremes_single_leg_rotation_v0",
            "long_leg_means": "LONG_MIN_RANK_DELTA",
            "short_leg_means": "SHORT_MAX_RANK_DELTA",
            "single_slot_rotation": True,
            "panel_insufficient_target": "FLAT",
            "warmup_incomplete_target": "FLAT",
            "non_finite_open_interest_target": "FLAT",
        },
        "external_bindings": {
            "pit_universe_manifest_ref": _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF),
            "instrument_id_canonicalization_version": _field_bound(
                value=INSTRUMENT_ID_CANONICALIZATION_VERSION
            ),
            "panel_open_interest_dataset_manifest_ref": _field_bound(ref=PANEL_OI_MANIFEST_REF),
            "admissibility_manifest_ref": _field_bound(ref=ADMISSIBILITY_MANIFEST_REF),
            "pit_semantics_contract_version": _field_bound(value=CONTRACT_VERSION),
            "fee_model_version": _field_bound(value=FEE_MODEL_VERSION),
            "slippage_model_version": _field_bound(value=SLIPPAGE_MODEL_VERSION),
            "funding_model_version": _field_bound(value=FUNDING_MODEL_VERSION),
            "spread_model_version": _field_bound(value=SPREAD_MODEL_VERSION),
            "execution_model_version": _field_bound(value=EXECUTION_MODEL_VERSION),
        },
        "parameter_binding": parameter_binding,
        "pit_universe_binding": pit_universe_binding,
        "dataset_binding": dataset_binding,
    }

    return {
        "artifact_kind": "cross_sectional_open_interest_delta_rank_v0_versioned_research_binding",
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "schema_version": BINDING_SCHEMA_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "research_scope": RESEARCH_SCOPE,
        "binding": binding,
        "pit_semantics_contract": pit_semantics_contract_to_dict(pit_contract),
        "cost_execution_binding": cost_binding,
        "economic_policy_binding": economic_policy,
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_excluded": True,
            "synthetic_spot_excluded": True,
            "offline_only": True,
            "no_runtime": True,
            "no_parameter_optimization": True,
            "no_policy_rescue": True,
            "no_signal_logic_change": True,
            "no_dataset_change": True,
            "no_universe_change": True,
        },
        "data_digest": RATIFIED_PANEL_DATASET_DIGEST,
        "instrument_universe_digest": RATIFIED_INSTRUMENT_UNIVERSE_DIGEST,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
    }


def validate_versioned_research_binding_v0(
    envelope: Mapping[str, Any],
) -> tuple[BindingValidationVerdict, tuple[str, ...]]:
    reasons: list[str] = []
    binding = envelope.get("binding", {})
    status = binding.get("binding_status", {}).get("overall_binding_status")
    if status != "COMPLETE":
        reasons.append("BINDING_INCOMPLETE")

    digests = binding.get("digest_bindings", {})
    for key, expected in (
        ("data_digest", RATIFIED_PANEL_DATASET_DIGEST),
        ("instrument_universe_digest", RATIFIED_INSTRUMENT_UNIVERSE_DIGEST),
        ("bound_data_digest", RATIFIED_BOUND_DATA_DIGEST),
    ):
        entry = digests.get(key, {})
        if entry.get("value") != expected:
            reasons.append(f"DIGEST_MISMATCH:{key}")

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    dataset_binding = binding.get("dataset_binding", {})
    if dataset_binding.get("dataset_id") != DATASET_ID:
        reasons.append("DATASET_ID_MISMATCH")
    if dataset_binding.get("no_fallback_to_399_instrument_dataset") is not True:
        reasons.append("FALLBACK_FORBIDDEN_VIOLATION")

    target_bindings = binding.get("pit_universe_binding", {}).get("target_instrument_bindings", [])
    expected_ids = {inst_id for inst_id, _ in CANONICAL_UNIVERSE_BINDING}
    actual_ids = {item.get("instrument_id") for item in target_bindings}
    if actual_ids != expected_ids or len(actual_ids) != len(CANONICAL_UNIVERSE_BINDING):
        reasons.append("INSTRUMENT_BINDING_MISMATCH")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return BindingValidationVerdict.REJECTED_INCOMPLETE, unique_reasons
    return BindingValidationVerdict.ACCEPTED_COMPLETE, ()


def materialize_and_validate_versioned_research_binding_v0() -> VersionedResearchBindingResultV0:
    envelope = materialize_versioned_research_binding_v0()
    validation_verdict, fail_reasons = validate_versioned_research_binding_v0(envelope)
    verdict = (
        BindingMaterializationVerdict.COMPLETE
        if validation_verdict is BindingValidationVerdict.ACCEPTED_COMPLETE
        else BindingMaterializationVerdict.INCOMPLETE
    )
    return VersionedResearchBindingResultV0(
        verdict=verdict,
        validation_verdict=validation_verdict,
        binding=envelope,
        fail_reasons=fail_reasons,
    )


def load_versioned_research_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return materialize_versioned_research_binding_v0()


def serialize_versioned_binding_artifact_json_v0(envelope: Mapping[str, Any]) -> str:
    return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


def apply_complete_external_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(binding)
    external = result["binding"]["external_bindings"]
    external["pit_universe_manifest_ref"] = _field_bound(ref=PIT_UNIVERSE_MANIFEST_REF)
    external["panel_open_interest_dataset_manifest_ref"] = _field_bound(ref=PANEL_OI_MANIFEST_REF)
    return result
