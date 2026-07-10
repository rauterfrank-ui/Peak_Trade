"""Armstrong cycle v1 versioned research binding and scope ratification v0.

Offline-only ratification slice: materializes versioned bindings, material-difference
contract, scope ratification config, and evaluation config readiness without executing
economic evaluation or touching runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.backtest.step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1 import (
    ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS,
    ARMSTRONG_CYCLE_V1_REQUIRED_WARMUP_ROWS,
    ARMSTRONG_CYCLE_V1_STRATEGY_ID,
    ARMSTRONG_CYCLE_V1_STRATEGY_OWNER,
    ARMSTRONG_CYCLE_V1_STRATEGY_VERSION,
    DEFAULT_EVALUATION_CONFIG_PATH,
    EXCLUDED_BINDING_PARAMS,
    evaluate_armstrong_cycle_v1_admissibility_contract_v1,
)
from src.backtest.offline_evaluation_sizing_contract_v1 import (
    compute_sizing_contract_digest_v1,
    load_offline_evaluation_sizing_contract_v1,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.backtest.strategy_signal_binding_v1 import (
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)
from src.research.step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_armstrong_binding_digest_v0,
    compute_step29m_armstrong_implementation_digest_v0,
)

PACKAGE_MARKER = "ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"

STRATEGY_ID = ARMSTRONG_CYCLE_V1_STRATEGY_ID
STRATEGY_VERSION = ARMSTRONG_CYCLE_V1_STRATEGY_VERSION
RESEARCH_SCOPE = "armstrong_cycle/v1"
CANDIDATE_ID = RESEARCH_SCOPE
HYPOTHESIS_ID = "ARMSTRONG_ECM_MACRO_CALENDAR_CYCLE_PHASE_NON_BITCOIN_FUTURES_V1"
SIGNAL_FAMILY = "MACRO_CALENDAR_ECM_CYCLE_PHASE"
EVIDENCE_CLASS_ID = "ARMSTRONG_CYCLE_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0"

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/armstrong_cycle_v1_versioned_research_binding_v0.json"
)
MATERIAL_DIFFERENCE_CONFIG_REL_PATH = (
    "config/research/armstrong_cycle_v1_material_difference_and_non_claim_contract_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0.md"
)
ADMISSIBILITY_CONTRACT_REL_PATH = (
    "src/backtest/step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1.py"
)

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_"
    "post_el_karoui_inconclusive_read_only_v0_20260710T151847Z"
)
EHLERS_TERMINAL_SCOPE_DEFINITION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/register_terminal_inconclusive_ehlers_cycle_filter_v1_same_binding_and_"
    "authorize_distinct_futures_research_scope_definition_read_only_v0_20260710T124034Z"
)
EL_KAROUI_TERMINAL_INCONCLUSIVE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/el_karoui_vol_model_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T135114Z"
)

DATASET_ID = "inst-eth-usdt-perp_v1"
DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
EXPECTED_MANIFEST_DIGEST = "317105798c749943074911b1e9ea91ac9b94fab3b115fb7a64b692339426651a"
DATASET_PATH = (
    DURABLE_ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
)

TRAINING_PERIOD = "2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00"
VALIDATION_PERIOD = "2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00"
OUT_OF_SAMPLE_PERIOD = "2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00"
DATA_PERIOD = f"{TRAINING_PERIOD}|{VALIDATION_PERIOD}|{OUT_OF_SAMPLE_PERIOD}"

NEXT_GO_TOKEN = (
    "GO_ARMSTRONG_CYCLE_V1_BOUNDED_OFFLINE_ECONOMIC_BASELINE_EVALUATION_NO_RUNTIME_AUTHORITY_V0"
)
NEXT_STEP = EVIDENCE_CLASS_ID

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False

OPERATOR_GO_TOKEN = (
    "GO_RATIFY_ARMSTRONG_CYCLE_V1_VERSIONED_RESEARCH_BINDING_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NO_RUNTIME_AUTHORITY_V0"
)

CALENDAR_ORIGIN = "2015-10-01"
CALENDAR_TIMEZONE = "UTC"
CALENDAR_EPOCH_RULES = "ECM_REFERENCE_PEAK_DATE_CALENDAR_DAY_COUNT_MOD_CYCLE_LENGTH_UTC_MIDNIGHT"
ECM_PHASE_STATE_MACHINE = "ECM_PHASE_STATE_MACHINE_V1"
ECM_PHASES = (
    "CRISIS",
    "EXPANSION",
    "CONTRACTION",
    "PRE_CRISIS",
    "POST_CRISIS",
)


class RatificationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ManifestVerification:
    bundle_path: Path
    manifest_verify_rc: int


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(serialize_canonical_json(payload).encode("utf-8")).hexdigest()


def verify_manifest_sha256(bundle_dir: Path) -> ManifestVerification:
    manifest = bundle_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=1)
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return ManifestVerification(bundle_path=bundle_dir, manifest_verify_rc=proc.returncode)


def compute_universe_digest_v0() -> str:
    return _stable_digest(
        {
            "canonical_instrument_id": "inst-eth-usdt-perp",
            "native_instrument_id": "ETH-USDT-SWAP",
            "source_venue": "OKX",
            "futures_only": True,
            "bitcoin_present": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "selection_mode": "single_instrument_prebound",
        }
    )


def compute_strategy_semantic_digest_v0() -> str:
    return _stable_digest(
        {
            "signal_family": SIGNAL_FAMILY,
            "signal_semantics": "LONG_FLAT_0_1",
            "regime_position_map": "default",
            "entry_semantics": "ecm_phase_position_mapping",
            "exit_semantics": "ecm_phase_position_mapping",
            "hold_semantics": "calendar_day_point_in_time",
            "state_semantics": "ECM_MACRO_CALENDAR_CYCLE_PHASE",
        }
    )


def build_calendar_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "timezone": CALENDAR_TIMEZONE,
        "calendar_origin": CALENDAR_ORIGIN,
        "epoch_rules": CALENDAR_EPOCH_RULES,
        "cycle_length_days": ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS["cycle_length_days"],
        "event_window_days": ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS["event_window_days"],
        "phase_state_machine": ECM_PHASE_STATE_MACHINE,
        "phases": list(ECM_PHASES),
        "phase_position_map": "default",
        "required_warmup_rows": ARMSTRONG_CYCLE_V1_REQUIRED_WARMUP_ROWS,
        "warmup_derivation": "calendar_domain_no_bar_warmup",
        "no_lookahead": True,
        "no_lookahead_semantics": "point_in_time_bar_close_v1",
        "finalized_bar_semantics": "point_in_time_bar_close_v1",
        "time_order_guard": "bar_timestamp_monotonic_non_decreasing",
    }


def build_evaluation_config_template_v1(
    *, strategy_params_digest: str, config_digest: str
) -> dict[str, Any]:
    return {
        "backtest": {
            "cost_model_version": "backtest_cost_v0",
            "dataset_admissibility": {
                "bind": True,
                "dataset_profile": "economic_research_v1",
                "execution_cost_binding": {
                    "conservative_half_spread_bps": 5.0,
                    "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                    "spread_model_version": "research_conservative_bps_v1",
                },
                "profile_binding": {
                    "dataset_profile": "economic_research_v1",
                    "execution_cost_binding": {
                        "conservative_half_spread_bps": 5.0,
                        "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                        "spread_model_version": "research_conservative_bps_v1",
                    },
                    "l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
                },
            },
            "economic_research_execution_cost": {
                "conservative_half_spread_bps": 5.0,
                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                "fee_bps": 10.0,
                "slippage_bps": 5.0,
                "spread_model_version": "research_conservative_bps_v1",
            },
            "fee_bps": 10.0,
            "fee_model_version": "backtest_fee_taker_symmetric_v0",
            "funding": {
                "bind": True,
                "model_version": "backtest_funding_perpetual_interval_v1",
            },
            "initial_cash": 10000.0,
            "parameter_sensitivity": {
                "bind": True,
                "grid": {
                    "grid_id": "okx_eth_perp_research_cost_grid_v1",
                    "parameter_names": ["fee_bps", "slippage_bps"],
                    "parameter_values": [[8.0, 10.0, 12.0], [4.0, 5.0, 6.0]],
                    "search_space_bounds": {
                        "fee_bps": {"max": 12.0, "min": 8.0},
                        "slippage_bps": {"max": 6.0, "min": 4.0},
                    },
                    "seed": 42,
                },
                "grid_version": "v1",
                "policy_version": "parameter_sensitivity_v1",
            },
            "slippage_bps": 5.0,
            "slippage_model_version": "backtest_slippage_symmetric_v0",
        },
        "config_schema_version": (
            "step29m_armstrong_cycle_v1_economic_evaluation_admissibility_v1"
        ),
        "config_version": "v1",
        "economic_evaluation_v1": {
            "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
            "engine_signal_source": "configured_strategy_signal",
            "monte_carlo": {
                "bind": True,
                "policy_version": "monte_carlo_v1",
                "runs": 64,
                "seed": 42,
            },
            "parameter_sensitivity_policy_version": "parameter_sensitivity_v1",
            "strategy_id": STRATEGY_ID,
            "strategy_params": dict(ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS),
            "strategy_version": STRATEGY_VERSION,
            "stress": {"bind": True, "policy_version": "stress_class_suite_v1"},
            "walk_forward": {
                "bind": True,
                "policy_version": "walk_forward_v1",
                "step_bars": 1440,
                "test_bars": 1440,
                "train_bars": 4320,
            },
        },
        "offline_evaluation_sizing_contract_v1": {
            "config_digest": config_digest,
            "dataset_digest": DATASET_DIGEST,
            "initial_equity": 10000.0,
            "instrument_metadata_source": "versioned_dataset_manifest_v1",
            "max_position_pct": 0.25,
            "minimum_notional_policy": "USE_RISK_MIN_POSITION_VALUE_v1",
            "minimum_quantity_policy": "REJECT_BELOW_MIN_NOTIONAL_v1",
            "oversize_policy": "REJECT_OVERSIZE",
            "price_source": "bar_close_v1",
            "quantity_rounding_policy": "NONE_v1",
            "risk_per_trade": 0.005,
            "sizing_contract_version": "offline_evaluation_sizing_contract_v1",
            "sizing_mode": "fixed_fractional_risk_per_trade_v1",
            "sizing_owner": "backtest.offline_evaluation_sizing_contract_v1",
            "stop_distance_policy": "FIXED_PCT_FROM_ENTRY_v1",
            "stop_pct": 0.025,
            "stop_pct_derivation_ref": "fleet_precedent:macd_v3_post_risk_limits_rewire",
            "strategy_params_digest": strategy_params_digest,
        },
        "real_admissible_futures_evaluation_binding_v1": {
            "canonical_instrument_id": "inst-eth-usdt-perp",
            "canonical_trading_logic_version": "integrated_offline_trading_logic_replay_v1",
            "dataset_path": str(DATASET_PATH),
            "dataset_profile": "economic_research_v1",
            "effective_entry_cost_bps": 20.0,
            "effective_exit_cost_bps": 20.0,
            "execution_model_version": "backtest_execution_v0",
            "expected_dataset_digest": DATASET_DIGEST,
            "expected_l1_observation_status": "EXECUTION_MODEL_BOUND_NOT_OBSERVED",
            "expected_manifest_digest": EXPECTED_MANIFEST_DIGEST,
            "native_instrument_id": "ETH-USDT-SWAP",
            "out_of_sample_period": OUT_OF_SAMPLE_PERIOD,
            "require_dataset_admissible": True,
            "require_integrity_pass": True,
            "require_observed_l1_used_false": True,
            "roundtrip_cost_bps": 40.0,
            "source_venue": "OKX",
            "training_period": TRAINING_PERIOD,
            "validation_period": VALIDATION_PERIOD,
        },
        "risk": {
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
            "risk_per_trade": 0.005,
        },
        "step29m_policy_ratification_v1": {
            "dataset_replacement_allowed": False,
            "evaluation_authorized": False,
            "instrument_id": "inst-eth-usdt-perp",
            "operator_policy_derivation_ref": (
                "operator_policy_decision:STEP29M_ARMSTRONG_CYCLE_V1"
            ),
            "parameter_tuning_allowed": False,
            "promotion_authorized": False,
            "runtime_authorized": False,
            "sizing_precedent_ref": "fleet_precedent:macd_v3_post_risk_limits_rewire",
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "threshold_tuning_allowed": False,
            "venue_id": "okx",
        },
    }


def materialize_evaluation_config_v1(repo_root: Path) -> dict[str, Any]:
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        STRATEGY_ID,
        project_strategy_params_for_binding_v1(STRATEGY_ID, ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS),
    )
    draft = build_evaluation_config_template_v1(
        strategy_params_digest=strategy_params_digest,
        config_digest="",
    )
    sizing_contract = load_offline_evaluation_sizing_contract_v1(
        draft,
        strategy_params_digest=strategy_params_digest,
        dataset_digest=DATASET_DIGEST,
    )
    sizing_config_digest = compute_sizing_contract_digest_v1(sizing_contract)
    return build_evaluation_config_template_v1(
        strategy_params_digest=strategy_params_digest,
        config_digest=sizing_config_digest,
    )


def materialize_material_difference_contract_v0() -> dict[str, Any]:
    body = {
        "artifact_kind": "armstrong_cycle_v1_material_difference_and_non_claim_contract",
        "artifact_version": "v0",
        "baseline_scope": "el_karoui_vol_model/v1",
        "explicit_non_claims": [
            "SIGNAL_UNTESTED=false",
            "NO_PRIOR_SINGLE_INSTRUMENT_EVALUATION=true",
            "NEW_SIGNAL_FAMILY=true",
            "TERMINAL_SINGLE_INSTRUMENT_EVIDENCE_SUPERSEDED=false",
            "DATASET_CHANGE_ALONE_SUFFICIENT=false",
            "THRESHOLD_VARIATION_ONLY=false",
            "POLICY_RESCUE=false",
            "UNCHANGED_RETRY_OF_EHLERS_BINDING=false",
            "UNCHANGED_RETRY_OF_EL_KAROUI_BINDING=false",
        ],
        "material_difference_axes": [
            "SIGNAL_FAMILY=MACRO_CALENDAR_ECM_CYCLE_PHASE_NOT_DSP_CYCLE_BANDPASS",
            "SIGNAL_FAMILY=MACRO_CALENDAR_ECM_CYCLE_PHASE_NOT_STOCHASTIC_VOL_REGIME",
            "DATA_SOURCE=OHLCV_SINGLE_INSTRUMENT_NOT_PANEL_OR_FUNDING_SCORE",
            "RANKING_GEOMETRY=NONE_SINGLE_INSTRUMENT_NOT_CROSS_SECTIONAL_TOP1_ROTATION",
            "EVALUATION_WIRING=STEP29M_SINGLE_INSTRUMENT_NOT_PANEL_ORCHESTRATOR",
            "PORTFOLIO_AGGREGATION=DIRECT_SINGLE_SLOT_CALENDAR_PHASE_EXPOSURE",
            "WARMUP_DOMAIN=CALENDAR_EPOCH_NOT_BAR_LOOKBACK",
        ],
        "material_difference_basis": (
            "MACRO_CALENDAR_ECM_CYCLE_PHASE_SINGLE_INSTRUMENT_EXPOSURE_NOT_DSP_OR_STOCHASTIC_VOL"
        ),
        "material_difference_confirmed": True,
        "material_difference_vs_ehlers_cycle_filter_v1_confirmed": True,
        "material_difference_vs_el_karoui_vol_model_v1_confirmed": True,
        "material_difference_vs_cross_sectional_ma_crossover_panel_rank_rotation_v0_confirmed": True,
        "material_difference_vs_cross_sectional_funding_fleet_confirmed": True,
        "material_difference_vs_step29m_final_research_fleet_v0_confirmed": True,
        "material_difference_vs_vol_breakout_v1_confirmed": True,
        "near_duplicate_risk": "LOW",
        "prior_evidence_exclusion_pass": True,
        "schema_version": "armstrong_cycle_v1_material_difference_and_non_claim_contract.v0",
        "signal_family": SIGNAL_FAMILY,
        "signal_family_material_difference": True,
        "source_discovery_evidence_ref": str(SOURCE_EVIDENCE_DIR),
        "source_terminal_scope_definition_ref": (
            "config/research/"
            "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
            "distinct_futures_research_scope_definition_v0.json"
        ),
        "source_el_karoui_terminal_inconclusive_ref": str(EL_KAROUI_TERMINAL_INCONCLUSIVE_DIR),
    }
    body["contract_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "contract_digest"}
    )
    body["material_difference_digest"] = body["contract_digest"]
    return body


def materialize_versioned_research_binding_v0(
    repo_root: Path,
    *,
    material_difference: Mapping[str, Any],
    evaluation_config: Mapping[str, Any],
) -> dict[str, Any]:
    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        STRATEGY_ID,
        project_strategy_params_for_binding_v1(STRATEGY_ID, ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS),
    )
    config_digest = compute_evaluation_config_digest_v1(dict(evaluation_config))
    implementation_digest = compute_step29m_armstrong_implementation_digest_v0(repo_root)
    strategy_semantic_digest = compute_strategy_semantic_digest_v0()
    universe_digest = compute_universe_digest_v0()
    material_difference_digest = str(material_difference["material_difference_digest"])
    calendar_binding = build_calendar_binding_v0()
    binding_digest = compute_step29m_armstrong_binding_digest_v0(
        config_digest=config_digest,
        data_digest=DATASET_DIGEST,
        implementation_digest=implementation_digest,
        strategy_params_digest=strategy_params_digest,
        material_difference_digest=material_difference_digest,
        hypothesis_id=HYPOTHESIS_ID,
        instrument_id="inst-eth-usdt-perp",
        data_period=DATA_PERIOD,
        universe_digest=universe_digest,
    )

    return {
        "accounting_reconciliation_pass": True,
        "artifact_kind": "armstrong_cycle_v1_versioned_research_binding",
        "artifact_version": "v0",
        "authority_effect": AUTHORITY_EFFECT,
        "binding": {
            "baseline_evaluation_contract": {
                "baseline_count": 1,
                "baseline_type": "FULL_CANONICAL_OFFLINE_BASELINE_SINGLE_INSTRUMENT",
                "conditional_monte_carlo": (
                    "only_after_positive_baseline_and_separate_admissibility_check"
                ),
                "conditional_stress": (
                    "only_after_positive_baseline_and_separate_admissibility_check"
                ),
                "conditional_walk_forward": (
                    "only_after_positive_baseline_and_separate_admissibility_check"
                ),
                "economic_evaluation_executed_in_this_slice": False,
                "evidence_class_id": EVIDENCE_CLASS_ID,
                "parameter_tuning_after_baseline_forbidden": True,
                "parameter_tuning_during_baseline_forbidden": True,
            },
            "binding_status": {
                "baseline_binding_status": "BOUND",
                "calendar_binding_status": "BOUND",
                "candidate_binding_status": "BOUND",
                "cost_model_binding_status": "BOUND",
                "dataset_binding_status": "BOUND",
                "digest_binding_status": "BOUND",
                "instrument_binding_status": "BOUND",
                "numeric_bindings_status": "BOUND",
                "overall_binding_status": "COMPLETE",
                "parameter_binding_status": "BOUND",
                "period_binding_status": "BOUND",
                "policy_classes_status": "BOUND",
                "warmup_binding_status": "BOUND",
            },
            "calendar_binding": calendar_binding,
            "candidate_binding": {
                "canonical_candidate_identifier": RESEARCH_SCOPE,
                "canonical_owner": "src/strategies/armstrong/armstrong_cycle_strategy.py",
                "engine_signal_source": "configured_strategy_signal",
                "hypothesis_id": HYPOTHESIS_ID,
                "implementation_ref": ARMSTRONG_CYCLE_V1_STRATEGY_OWNER,
                "registry_class": "oop_strategy_spec",
                "registry_key": STRATEGY_ID,
                "signal_family": SIGNAL_FAMILY,
                "strategy_id": STRATEGY_ID,
                "strategy_version": STRATEGY_VERSION,
            },
            "cost_execution_binding": {
                "binding_version": "v0",
                "execution_model_version": "backtest_execution_v0",
                "execution_price_observation_source": "MODELLED_NOT_OBSERVED",
                "fee_model_version": "backtest_fee_taker_symmetric_v0",
                "funding_bind": True,
                "funding_model_version": "backtest_funding_perpetual_interval_v1",
                "implicit_zero_cost_forbidden": True,
                "roundtrip_cost_bps": 40.0,
                "slippage_model_version": "backtest_slippage_symmetric_v0",
                "spread_model_version": "research_conservative_bps_v1",
            },
            "dataset_binding": {
                "binding_version": "v1",
                "canonical_instrument_id": "inst-eth-usdt-perp",
                "dataset_digest": DATASET_DIGEST,
                "dataset_id": DATASET_ID,
                "dataset_path": str(DATASET_PATH),
                "dataset_profile": "economic_research_v1",
                "dataset_version": "v1",
                "expected_manifest_digest": EXPECTED_MANIFEST_DIGEST,
                "native_instrument_id": "ETH-USDT-SWAP",
                "no_lookahead_semantics": "point_in_time_bar_close_v1",
                "point_in_time_binding": True,
                "source_venue": "OKX",
                "survivorship_bias_forbidden": True,
            },
            "digest_bindings": {
                "config_digest": {"status": "BOUND", "value": config_digest},
                "data_digest": {"status": "BOUND", "value": DATASET_DIGEST},
                "implementation_digest": {"status": "BOUND", "value": implementation_digest},
                "material_difference_digest": {
                    "status": "BOUND",
                    "value": material_difference_digest,
                },
                "strategy_params_digest": {"status": "BOUND", "value": strategy_params_digest},
                "strategy_semantic_digest": {
                    "status": "BOUND",
                    "value": strategy_semantic_digest,
                },
                "universe_digest": {"status": "BOUND", "value": universe_digest},
            },
            "economic_policy_binding": {
                "binding_version": "v1",
                "baseline_adjudication_policy": "PASS_FAIL_INCONCLUSIVE",
                "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
                "minimum_trade_count_policy_bound": True,
                "promising_is_not_pass_bound": True,
                "sample_sufficiency_policy": "economic_validity_policy_v1",
            },
            "external_bindings": {
                "admissibility_contract_ref": {
                    "ref": ADMISSIBILITY_CONTRACT_REL_PATH,
                    "status": "BOUND",
                },
                "evaluation_config_ref": {
                    "ref": DEFAULT_EVALUATION_CONFIG_PATH,
                    "status": "BOUND",
                },
                "execution_model_version": {"status": "BOUND", "value": "backtest_execution_v0"},
                "fee_model_version": {
                    "status": "BOUND",
                    "value": "backtest_fee_taker_symmetric_v0",
                },
                "funding_model_version": {
                    "status": "BOUND",
                    "value": "backtest_funding_perpetual_interval_v1",
                },
                "instrument_id_canonicalization_version": {
                    "status": "BOUND",
                    "value": "instrument_id_canonicalization.v1",
                },
                "material_difference_contract_ref": {
                    "ref": MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
                    "status": "BOUND",
                },
                "slippage_model_version": {
                    "status": "BOUND",
                    "value": "backtest_slippage_symmetric_v0",
                },
                "spread_model_version": {
                    "status": "BOUND",
                    "value": "research_conservative_bps_v1",
                },
                "strategy_signal_binding_owner": {
                    "status": "BOUND",
                    "value": "backtest.strategy_signal_binding_v1",
                },
            },
            "instrument_binding": {
                "binding_version": "v0",
                "bitcoin_direction_allowed": False,
                "bitcoin_present": False,
                "canonical_instrument_id": "inst-eth-usdt-perp",
                "futures_only": True,
                "native_instrument_id": "ETH-USDT-SWAP",
                "selection_mode": "single_instrument_prebound",
                "source_venue": "OKX",
                "spot_allowed": False,
                "synthetic_spot_allowed": False,
            },
            "numeric_bindings": {
                "conservative_half_spread_bps": 5.0,
                "cycle_length_days": 3141,
                "effective_entry_cost_bps": 20.0,
                "effective_exit_cost_bps": 20.0,
                "event_window_days": 90,
                "fee_bps_per_side": 10.0,
                "phase_position_map": "default",
                "reference_date": "2015-10-01",
                "required_warmup_rows": ARMSTRONG_CYCLE_V1_REQUIRED_WARMUP_ROWS,
                "risk_per_trade": 0.005,
                "roundtrip_cost_bps": 40.0,
                "slippage_bps_per_side": 5.0,
                "stop_pct": 0.025,
            },
            "parameter_binding": {
                "binding_version": "v0",
                "consumed_parameters": [
                    "cycle_length_days",
                    "event_window_days",
                    "reference_date",
                    "phase_position_map",
                ],
                "excluded_parameters": sorted(EXCLUDED_BINDING_PARAMS),
                "parameter_search_forbidden": True,
                "parameters": dict(ARMSTRONG_CYCLE_V1_CANONICAL_PARAMS),
            },
            "period_binding": {
                "binding_version": "v1",
                "out_of_sample_period": OUT_OF_SAMPLE_PERIOD,
                "periods_frozen_before_execution": True,
                "random_split_forbidden": True,
                "training_period": TRAINING_PERIOD,
                "validation_period": VALIDATION_PERIOD,
            },
            "prior_evidence_exclusion": {
                "excluded_terminal_inconclusive_bindings": [
                    "ehlers_cycle_filter/v1",
                    "el_karoui_vol_model/v1",
                ],
                "excluded_terminal_negative_bindings": [
                    "cross_sectional_ma_crossover_panel_rank_rotation/v0",
                    "vol_breakout/v1",
                    "trend_following/v1",
                    "bollinger_bands/v1",
                    "momentum_1h/v1",
                    "cross_sectional_funding_rate_rank_delta/v0",
                    "cross_sectional_funding_rate_persistence_reversal_filter/v0",
                    "cross_sectional_funding_rate_dispersion_zscore_reversion/v0",
                    "cross_sectional_funding_rate_dual_leg_spread/v1",
                    "cross_sectional_funding_rate_delta_momentum/v0",
                    "cross_sectional_funding_rate_carry/v0",
                    "cross_sectional_funding_rate_extreme_carry_reversion/v0",
                    "cross_sectional_relative_strength/v0",
                    "cross_sectional_realized_volatility_rank_rotation/v0",
                ],
                "near_duplicate_retry_blocked": True,
                "no_rescue_rules": [
                    "NO_POLICY_RESCUE",
                    "NO_THRESHOLD_LOWERING",
                    "NO_UNCHANGED_RETRY",
                    "NO_RENAME_ONLY_SUCCESSOR",
                ],
                "prior_evidence_exclusion_pass": True,
                "unchanged_retry_blocked": True,
            },
            "sample_sufficiency_contract": {
                "minimum_trade_count_policy": "economic_validity_policy_v1",
                "trade_count_target_inflation_forbidden": True,
            },
            "signal_semantics_binding": {
                "entry_semantics": "ecm_phase_position_mapping",
                "exit_semantics": "ecm_phase_position_mapping",
                "hold_semantics": "calendar_day_point_in_time",
                "regime_position_map": "default",
                "signal_semantics": "LONG_FLAT_0_1",
                "state_semantics": "ECM_MACRO_CALENDAR_CYCLE_PHASE",
                "use_risk_scaling_fixed": False,
                "underlying_fixed": None,
            },
            "warmup_binding": {
                "derivation": "calendar_domain",
                "required_warmup_rows": ARMSTRONG_CYCLE_V1_REQUIRED_WARMUP_ROWS,
                "warmup_bars_before_train_start_required": False,
            },
        },
        "binding_changed": False,
        "binding_digest": binding_digest,
        "binding_ratified": True,
        "binding_version": "v0",
        "bitcoin_direction_allowed": False,
        "bitcoin_present": False,
        "candidate_id": CANDIDATE_ID,
        "distinct_from_ehlers_cycle_filter_v1": True,
        "distinct_from_el_karoui_vol_model_v1": True,
        "durable_evidence_refs": (
            f"{SOURCE_EVIDENCE_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{EHLERS_TERMINAL_SCOPE_DEFINITION_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{EL_KAROUI_TERMINAL_INCONCLUSIVE_DIR} (MANIFEST_VERIFY_RC=0)"
        ),
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "futures_only": True,
        "go_token": OPERATOR_GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "hypothesis_id": HYPOTHESIS_ID,
        "material_difference_proven": True,
        "next_go_token": NEXT_GO_TOKEN,
        "next_step": NEXT_STEP,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "parameter_search_forbidden": True,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": "armstrong_cycle_v1_versioned_research_binding.v0",
        "source_ratification_evidence_ref": str(SOURCE_EVIDENCE_DIR),
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "trading_logic_mutated": False,
        "unchanged_retry_blocked": True,
        "universe_digest": universe_digest,
    }


def materialize_scope_ratification_v0(
    versioned_binding: Mapping[str, Any],
    material_difference: Mapping[str, Any],
) -> dict[str, Any]:
    binding = versioned_binding["binding"]
    return {
        "all_required_bindings_ratified": True,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_digest": versioned_binding["binding_digest"],
        "binding_ratified": True,
        "binding_version": versioned_binding["binding_version"],
        "bitcoin_direction_allowed": False,
        "bitcoin_present": False,
        "candidate_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "candidate_id": CANDIDATE_ID,
        "config_digest": binding["digest_bindings"]["config_digest"]["value"],
        "cost_execution_binding": binding["cost_execution_binding"],
        "data_digest": DATASET_DIGEST,
        "dataset_binding": binding["dataset_binding"],
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "economic_policy_binding": binding["economic_policy_binding"],
        "evaluation_authorization_status": ("NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO"),
        "evaluation_execution_authorized": False,
        "evaluation_infrastructure_ready": True,
        "futures_only": True,
        "go_token": NEXT_GO_TOKEN,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_digest": binding["digest_bindings"]["implementation_digest"]["value"],
        "instrument_binding": binding["instrument_binding"],
        "material_difference_confirmed": True,
        "material_difference_digest": material_difference["material_difference_digest"],
        "next_go_token": NEXT_GO_TOKEN,
        "next_step": NEXT_STEP,
        "offline_economic_evaluation_scope_ratified": True,
        "order_effect": ORDER_EFFECT,
        "parameter_binding": binding["parameter_binding"],
        "parameter_search_forbidden": True,
        "period_binding": binding["period_binding"],
        "prior_evidence_exclusion_pass": True,
        "prohibited_actions": [
            "ECONOMIC_EVALUATION_EXECUTION",
            "PARAMETER_SEARCH",
            "PARAMETER_TUNING",
            "RUNTIME_REWIRE",
            "RUNTIME",
            "SCHEDULER",
            "SHADOW",
            "PAPER",
            "TESTNET",
            "CANARY",
            "LIVE",
            "ORDERS",
            "CANCELS",
            "CREDENTIALS",
            "ARMING",
            "CANDIDATE_PROMOTION",
            "POLICY_THRESHOLD_RETROFIT",
        ],
        "promotion_admissible": False,
        "ratification_id": ("armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0"),
        "ratification_version": "v0",
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": ("armstrong_cycle_v1_offline_economic_evaluation_scope_ratification.v0"),
        "scope_classification": (
            "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
        ),
        "scope_id": "ARMSTRONG_CYCLE_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0",
        "signal_family": SIGNAL_FAMILY,
        "source_ratification_evidence_ref": str(SOURCE_EVIDENCE_DIR),
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "trading_logic_mutated": False,
        "universe_digest": versioned_binding["universe_digest"],
    }


def validate_ratification_preconditions(repo_root: Path) -> tuple[ManifestVerification, ...]:
    bundles = (
        SOURCE_EVIDENCE_DIR,
        EHLERS_TERMINAL_SCOPE_DEFINITION_DIR,
        EL_KAROUI_TERMINAL_INCONCLUSIVE_DIR,
    )
    verifications = tuple(verify_manifest_sha256(path) for path in bundles)
    if any(item.manifest_verify_rc != 0 for item in verifications):
        raise ValueError("source_manifest_verification_failed")
    admissibility = evaluate_armstrong_cycle_v1_admissibility_contract_v1(repo_root=repo_root)
    if admissibility.admissibility_result.value != "PASS":
        raise ValueError(f"admissibility_blocked:{admissibility.blocking_reasons}")
    return verifications


def materialize_ratification_bundle(repo_root: Path) -> dict[str, Any]:
    evaluation_config = materialize_evaluation_config_v1(repo_root)
    eval_path = repo_root / DEFAULT_EVALUATION_CONFIG_PATH
    eval_path.parent.mkdir(parents=True, exist_ok=True)
    eval_path.write_text(
        json.dumps(evaluation_config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    material_difference = materialize_material_difference_contract_v0()
    md_path = repo_root / MATERIAL_DIFFERENCE_CONFIG_REL_PATH
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        json.dumps(material_difference, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    versioned_binding = materialize_versioned_research_binding_v0(
        repo_root,
        material_difference=material_difference,
        evaluation_config=evaluation_config,
    )
    vb_path = repo_root / VERSIONED_BINDING_CONFIG_REL_PATH
    vb_path.write_text(
        json.dumps(versioned_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    scope_ratification = materialize_scope_ratification_v0(versioned_binding, material_difference)
    sr_path = repo_root / SCOPE_RATIFICATION_CONFIG_REL_PATH
    sr_path.write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return {
        "evaluation_config": evaluation_config,
        "material_difference": material_difference,
        "versioned_binding": versioned_binding,
        "scope_ratification": scope_ratification,
    }
