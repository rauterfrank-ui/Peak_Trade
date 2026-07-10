"""Bouchaud microstructure OHLCV proxy v1 scope ratification v0.

Offline-only ratification slice: materializes versioned bindings, scope ratification
config, and evaluation infrastructure readiness without executing economic evaluation.
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
from src.backtest.step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1 import (
    BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_CANONICAL_PARAMS,
    BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REQUIRED_WARMUP_ROWS,
    BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_STRATEGY_OWNER,
    DEFAULT_EVALUATION_CONFIG_PATH,
    EVALUATION_GO_TOKEN,
    EXCLUDED_BINDING_PARAMS,
    HYPOTHESIS_ID,
    REGISTRY_STRATEGY_ID,
    RESEARCH_SCOPE,
    evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1,
)
from src.backtest.step29m_macd_v1_economic_evaluation_admissibility_contract_v1 import (
    compute_evaluation_config_digest_v1,
)
from src.research.step29m_bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0,
    compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0,
)

PACKAGE_MARKER = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"
)

STRATEGY_ID = REGISTRY_STRATEGY_ID
STRATEGY_VERSION = "v1"
CANDIDATE_ID = RESEARCH_SCOPE
SIGNAL_FAMILY = "BAR_LEVEL_MICROSTRUCTURE_PRESSURE_PROXY"
EVIDENCE_CLASS_ID = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0"
)

DATA_CLASS = "FINALIZED_OHLCV_BARS"
PROXY_SEMANTICS = True
TRUE_TICK_L2_MICROSTRUCTURE = False
TICK_L2_SCOPE = "bouchaud_microstructure_tick_l2/v1"
TICK_L2_STATUS = "NOT_IMPLEMENTED_DATA_CAPABILITY_MISSING"

VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
MATERIAL_DIFFERENCE_CONFIG_REL_PATH = "config/research/bouchaud_microstructure_ohlcv_proxy_v1_material_difference_and_non_claim_contract_v0.json"
SCOPE_SEPARATION_CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_scope_separation_contract_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = "config/research/bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0.json"
ADMISSIBILITY_CONTRACT_REL_PATH = "src/backtest/step29m_bouchaud_microstructure_ohlcv_proxy_v1_economic_evaluation_admissibility_contract_v1.py"
ADAPTER_OWNER_REL_PATH = "src/research/bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_evaluation_adapter_v0.py"
RUNNER_REL_PATH = "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"
INVOKE_REL_PATH = "scripts/ops/invoke_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
PR5097_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5097_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_"
    "instrument_offline_evaluation_adapter_implementation_v0_20260710T172226Z"
)
BLOCKED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T172515Z"
)
IMPLEMENTATION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_offline_"
    "evaluation_adapter_implementation_v0_20260710T170832Z"
)
DISCOVERY_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/post_armstrong_registry_primary_signal_exhaustion_new_hypothesis_generation_and_"
    "capability_gap_classification_read_only_v0_20260710T170020Z"
)

DATASET_ID = "inst-eth-usdt-perp_v1"
DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
EXPECTED_MANIFEST_DIGEST = "317105798c749943074911b1e9ea91ac9b94fab3b115fb7a64b692339426651a"
DATASET_PATH = (
    DURABLE_ARCHIVE_ROOT / "datasets/admissible_futures/inst-eth-usdt-perp/v1/bars.parquet"
)
INSTRUMENT_ID = "inst-eth-usdt-perp"

TRAINING_PERIOD = "2026-06-17 16:00:00+00:00..2026-06-24 13:03:00+00:00"
VALIDATION_PERIOD = "2026-06-24 13:04:00+00:00..2026-06-27 23:35:00+00:00"
OUT_OF_SAMPLE_PERIOD = "2026-06-27 23:36:00+00:00..2026-07-01 10:07:00+00:00"
DATA_PERIOD = "2026-06-17 16:00:00+00:00..2026-07-01 10:07:00+00:00"
DATA_PERIOD_START = "2026-06-17T16:00:00Z"
DATA_PERIOD_END = "2026-07-01T10:07:00Z"

NEXT_GO_TOKEN = EVALUATION_GO_TOKEN
NEXT_STEP = EVIDENCE_CLASS_ID

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

OPERATOR_GO_TOKEN = (
    "GO_RATIFY_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_VERSIONED_RESEARCH_BINDING_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NO_RUNTIME_AUTHORITY_V0"
)

PRIOR_CONFIG_DIGEST = "a9c0f1d859855ef406e3f7cdc31e4f71ddf86e18d7e97a0bea2b2d0d1fdd1472"
PRIOR_IMPLEMENTATION_DIGEST = "c36c717694d66e7a147fdccd2a8a7ffeb62c948be47746b335fc8ad5cb4467a9"
PRIOR_BINDING_DIGEST = "05b19c44ce3e477cdb6aafb0bb6b5ec19195e881243bbcb3b9eef2a24fca6eb4"


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


def compute_strategy_semantic_digest_v0() -> str:
    return _stable_digest(
        {
            "signal_family": SIGNAL_FAMILY,
            "signal_semantics": "LONG_FLAT_0_1",
            "entry_semantics": "bar_level_pressure_proxy_threshold",
            "exit_semantics": "bar_level_pressure_proxy_threshold",
            "hold_semantics": "bar_close_point_in_time",
            "state_semantics": "BAR_LEVEL_MICROSTRUCTURE_PRESSURE_PROXY",
            "proxy_semantics": True,
            "true_tick_l2_microstructure": False,
        }
    )


def build_period_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "data_period": DATA_PERIOD,
        "out_of_sample_period": OUT_OF_SAMPLE_PERIOD,
        "periods_frozen_before_execution": True,
        "random_split_forbidden": True,
        "training_period": TRAINING_PERIOD,
        "validation_period": VALIDATION_PERIOD,
    }


def load_committed_material_difference_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MATERIAL_DIFFERENCE_CONFIG_REL_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_committed_scope_separation_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / SCOPE_SEPARATION_CONFIG_REL_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_committed_evaluation_config_v1(repo_root: Path) -> dict[str, Any]:
    path = repo_root / DEFAULT_EVALUATION_CONFIG_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_versioned_research_binding_v0(
    repo_root: Path,
    *,
    material_difference: Mapping[str, Any],
    evaluation_config: Mapping[str, Any],
) -> dict[str, Any]:
    from src.backtest.strategy_signal_binding_v1 import (
        project_strategy_params_for_binding_v1,
        resolve_effective_strategy_params_v1,
    )

    _, strategy_params_digest = resolve_effective_strategy_params_v1(
        STRATEGY_ID,
        project_strategy_params_for_binding_v1(
            STRATEGY_ID, BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_CANONICAL_PARAMS
        ),
    )
    config_digest = compute_evaluation_config_digest_v1(dict(evaluation_config))
    implementation_digest = compute_step29m_bouchaud_ohlcv_proxy_implementation_digest_v0(repo_root)
    strategy_semantic_digest = compute_strategy_semantic_digest_v0()
    material_difference_digest = str(material_difference["material_difference_digest"])
    binding_digest = compute_step29m_bouchaud_ohlcv_proxy_binding_digest_v0(
        config_digest=config_digest,
        data_digest=DATASET_DIGEST,
        implementation_digest=implementation_digest,
        strategy_params_digest=strategy_params_digest,
        material_difference_digest=material_difference_digest,
        hypothesis_id=HYPOTHESIS_ID,
        instrument_id=INSTRUMENT_ID,
        data_period=DATA_PERIOD,
    )

    return {
        "adapter_implementation_status": "COMPLETE",
        "artifact_kind": "bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding",
        "artifact_version": "v0",
        "authority_effect": AUTHORITY_EFFECT,
        "binding": {
            "baseline_evaluation_contract": {
                "baseline_count": 1,
                "baseline_type": "FULL_CANONICAL_OFFLINE_BASELINE_SINGLE_INSTRUMENT",
                "economic_evaluation_executed_in_this_slice": False,
                "evidence_class_id": EVIDENCE_CLASS_ID,
                "parameter_tuning_after_baseline_forbidden": True,
                "parameter_tuning_during_baseline_forbidden": True,
            },
            "binding_status": {
                "baseline_binding_status": "BOUND",
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
            "candidate_binding": {
                "canonical_candidate_identifier": RESEARCH_SCOPE,
                "canonical_owner": "src/strategies/bouchaud/bouchaud_microstructure_strategy.py",
                "data_class": DATA_CLASS,
                "engine_signal_source": "configured_strategy_signal",
                "hypothesis_id": HYPOTHESIS_ID,
                "implementation_ref": BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_STRATEGY_OWNER,
                "proxy_semantics": True,
                "registry_class": "oop_strategy_spec",
                "registry_key": STRATEGY_ID,
                "research_scope": RESEARCH_SCOPE,
                "signal_family": SIGNAL_FAMILY,
                "strategy_id": STRATEGY_ID,
                "strategy_version": STRATEGY_VERSION,
                "true_tick_l2_microstructure": False,
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
                "canonical_instrument_id": INSTRUMENT_ID,
                "data_class": DATA_CLASS,
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
                "tick_data_required": False,
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
            },
            "economic_policy_binding": {
                "baseline_adjudication_policy": "PASS_FAIL_INCONCLUSIVE",
                "binding_version": "v1",
                "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
                "minimum_trade_count_policy_bound": True,
                "promising_is_not_pass_bound": True,
                "sample_sufficiency_policy": "economic_validity_policy_v1",
            },
            "external_bindings": {
                "adapter_owner_ref": {"ref": ADAPTER_OWNER_REL_PATH, "status": "BOUND"},
                "admissibility_contract_ref": {
                    "ref": ADMISSIBILITY_CONTRACT_REL_PATH,
                    "status": "BOUND",
                },
                "evaluation_config_ref": {
                    "ref": DEFAULT_EVALUATION_CONFIG_PATH,
                    "status": "BOUND",
                },
                "evaluation_runner_ref": {"ref": RUNNER_REL_PATH, "status": "BOUND"},
                "invocation_wrapper_ref": {"ref": INVOKE_REL_PATH, "status": "BOUND"},
                "material_difference_contract_ref": {
                    "ref": MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
                    "status": "BOUND",
                },
                "scope_ratification_config_ref": {
                    "ref": SCOPE_RATIFICATION_CONFIG_REL_PATH,
                    "status": "BOUND",
                },
                "scope_separation_contract_ref": {
                    "ref": SCOPE_SEPARATION_CONFIG_REL_PATH,
                    "status": "BOUND",
                },
                "strategy_signal_binding_owner": {
                    "status": "BOUND",
                    "value": "backtest.strategy_signal_binding_v1",
                },
            },
            "instrument_binding": {
                "binding_version": "v0",
                "bitcoin_direction_allowed": False,
                "canonical_instrument_id": INSTRUMENT_ID,
                "futures_only": True,
                "native_instrument_id": "ETH-USDT-SWAP",
                "source_venue": "OKX",
                "spot_allowed": False,
                "synthetic_spot_allowed": False,
            },
            "numeric_bindings": {
                "effective_entry_cost_bps": 20.0,
                "effective_exit_cost_bps": 20.0,
                "fee_bps_per_side": 10.0,
                "imbalance_threshold": 0.3,
                "lookback_ticks": 100,
                "min_liquidity_filter": 1000.0,
                "propagator_decay": 0.5,
                "required_warmup_rows": BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REQUIRED_WARMUP_ROWS,
                "risk_per_trade": 0.005,
                "roundtrip_cost_bps": 40.0,
                "slippage_bps_per_side": 5.0,
                "stop_pct": 0.025,
            },
            "parameter_binding": {
                "binding_version": "v0",
                "consumed_parameters": sorted(
                    BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_CANONICAL_PARAMS.keys()
                ),
                "excluded_parameters": sorted(EXCLUDED_BINDING_PARAMS),
                "parameter_search_forbidden": True,
                "parameters": dict(BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_CANONICAL_PARAMS),
            },
            "period_binding": build_period_binding_v0(),
            "sample_sufficiency_contract": {
                "minimum_trade_count_policy": "economic_validity_policy_v1",
                "trade_count_target_inflation_forbidden": True,
            },
            "signal_semantics_binding": {
                "entry_semantics": "bar_level_pressure_proxy_threshold",
                "exit_semantics": "bar_level_pressure_proxy_threshold",
                "hold_semantics": "bar_close_point_in_time",
                "proxy_semantics": True,
                "signal_semantics": "LONG_FLAT_0_1",
                "state_semantics": "BAR_LEVEL_MICROSTRUCTURE_PRESSURE_PROXY",
                "true_tick_l2_microstructure": False,
            },
            "warmup_binding": {
                "binding_version": "v0",
                "required_warmup_rows": BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REQUIRED_WARMUP_ROWS,
            },
        },
        "binding_digest": binding_digest,
        "binding_ratified": True,
        "candidate_id": CANDIDATE_ID,
        "data_class": DATA_CLASS,
        "durable_evidence_refs": (
            f"{PR5097_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{BLOCKED_EVALUATION_DIR} (MANIFEST_VERIFY_RC=0); "
            f"{IMPLEMENTATION_EVIDENCE_DIR} (MANIFEST_VERIFY_RC=0)"
        ),
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "evaluation_authorized": False,
        "evaluation_infrastructure_ready": True,
        "go_token": OPERATOR_GO_TOKEN,
        "hypothesis_id": HYPOTHESIS_ID,
        "material_difference_proven": True,
        "next_evaluation_operator_go": NEXT_GO_TOKEN,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "proxy_semantics": True,
        "research_scope": RESEARCH_SCOPE,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": "bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding.v0",
        "selection_mode": "single_instrument_prebound",
        "source_discovery_evidence_ref": str(DISCOVERY_EVIDENCE_DIR),
        "source_ratification_evidence_ref": str(PR5097_CLOSEOUT_DIR),
        "true_tick_l2_microstructure": False,
        "trading_logic_mutated": False,
    }


def materialize_scope_ratification_v0(
    versioned_binding: Mapping[str, Any],
    material_difference: Mapping[str, Any],
    scope_separation: Mapping[str, Any],
) -> dict[str, Any]:
    binding = versioned_binding["binding"]
    return {
        "all_required_bindings_ratified": True,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_digest": versioned_binding["binding_digest"],
        "binding_ratified": True,
        "binding_version": "v0",
        "candidate_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "candidate_id": CANDIDATE_ID,
        "canonical_evaluation_runner": RUNNER_REL_PATH,
        "canonical_invocation_wrapper": INVOKE_REL_PATH,
        "config_digest": binding["digest_bindings"]["config_digest"]["value"],
        "cost_execution_binding": binding["cost_execution_binding"],
        "data_class": DATA_CLASS,
        "data_digest": DATASET_DIGEST,
        "data_period": DATA_PERIOD,
        "data_period_end": DATA_PERIOD_END,
        "data_period_start": DATA_PERIOD_START,
        "dataset_binding": binding["dataset_binding"],
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "economic_policy_binding": binding["economic_policy_binding"],
        "evaluation_authorization_status": "NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO",
        "evaluation_execution_authorized": False,
        "evaluation_infrastructure_ready": True,
        "futures_only": True,
        "go_token": NEXT_GO_TOKEN,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_digest": binding["digest_bindings"]["implementation_digest"]["value"],
        "instrument_binding": binding["instrument_binding"],
        "instrument_id": INSTRUMENT_ID,
        "material_difference_confirmed": True,
        "material_difference_digest": material_difference["material_difference_digest"],
        "next_go_token": NEXT_GO_TOKEN,
        "next_step": NEXT_STEP,
        "offline_economic_evaluation_scope_ratified": True,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "parameter_binding": binding["parameter_binding"],
        "parameter_search_forbidden": True,
        "period_binding": binding["period_binding"],
        "prior_config_digest": PRIOR_CONFIG_DIGEST,
        "prior_binding_digest": PRIOR_BINDING_DIGEST,
        "prior_implementation_digest": PRIOR_IMPLEMENTATION_DIGEST,
        "prohibited_actions": [
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
        "proxy_semantics": True,
        "ratification_id": (
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0"
        ),
        "ratification_version": "v0",
        "research_scope": RESEARCH_SCOPE,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": (
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification.v0"
        ),
        "scope_classification": (
            "BOUNDED_FUTURES_ONLY_OHLCV_PROXY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
        ),
        "scope_id": (
            "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0"
        ),
        "scope_separation_contract_ref": SCOPE_SEPARATION_CONFIG_REL_PATH,
        "signal_family": SIGNAL_FAMILY,
        "single_instrument_only": True,
        "source_ratification_evidence_ref": str(PR5097_CLOSEOUT_DIR),
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "tick_l2_scope": TICK_L2_SCOPE,
        "tick_l2_status": TICK_L2_STATUS,
        "true_tick_l2_microstructure": False,
        "trading_logic_mutated": False,
    }


def validate_ratification_preconditions(repo_root: Path) -> tuple[ManifestVerification, ...]:
    bundles = (
        PR5097_CLOSEOUT_DIR,
        BLOCKED_EVALUATION_DIR,
        IMPLEMENTATION_EVIDENCE_DIR,
    )
    verifications = tuple(verify_manifest_sha256(path) for path in bundles)
    if any(item.manifest_verify_rc != 0 for item in verifications):
        raise ValueError("source_manifest_verification_failed")
    admissibility = evaluate_bouchaud_microstructure_ohlcv_proxy_v1_admissibility_contract_v1(
        repo_root=repo_root,
    )
    if admissibility.admissibility_result.value != "PASS":
        raise ValueError(f"admissibility_blocked:{admissibility.blocking_reasons}")
    return verifications


def materialize_ratification_bundle(repo_root: Path) -> dict[str, Any]:
    evaluation_config = load_committed_evaluation_config_v1(repo_root)
    material_difference = load_committed_material_difference_v0(repo_root)
    scope_separation = load_committed_scope_separation_v0(repo_root)

    versioned_binding = materialize_versioned_research_binding_v0(
        repo_root,
        material_difference=material_difference,
        evaluation_config=evaluation_config,
    )
    vb_path = repo_root / VERSIONED_BINDING_CONFIG_REL_PATH
    vb_path.write_text(
        json.dumps(versioned_binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    scope_ratification = materialize_scope_ratification_v0(
        versioned_binding,
        material_difference,
        scope_separation,
    )
    sr_path = repo_root / SCOPE_RATIFICATION_CONFIG_REL_PATH
    sr_path.write_text(
        json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return {
        "evaluation_config": evaluation_config,
        "material_difference": material_difference,
        "scope_separation": scope_separation,
        "versioned_binding": versioned_binding,
        "scope_ratification": scope_ratification,
    }
