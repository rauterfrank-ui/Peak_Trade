"""Post-no-pass sparse-signal / zero-trade versioned binding completion v0.

Deterministic materialization of NEW versioned bindings (strategy_version=v2) for
trend_following, bollinger_bands, and momentum_1h addressing the sparse-signal /
zero-trade failure class. Reuses canonical STEP31F parameters unchanged (no parameter
rescue). Structural binding differences only: panel-sequential signal-density research
instrument binding and extended chronological period binding.

Binding ratification only — no economic evaluation, no runtime, no authority effect.
Operator GO: GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_ID,
    FLEET_VERSION,
    STEP31F_CONFIG_PATHS,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
)

PACKAGE_MARKER = "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_COMPLETION_V0=true"

SCHEMA_VERSION = "post_no_pass_sparse_signal_zero_trade_versioned_binding_completion.v0"
COMPLETION_ID = "post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0"
CONFIG_REL_PATH = (
    "config/research/post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0.md"
)
SCOPE_DEFINITION_REL_PATH = (
    "config/research/post_no_pass_robustness_failure_next_research_scope_definition_v0.json"
)
CLASS_D_COMPLETION_REL_PATH = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

CONFIRM_GO = "GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
NEXT_EXECUTION_GO = (
    "GO_POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
SCOPE_CLASSIFICATION = "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0"
PROCESS_CLASSIFICATION = "VERSIONED_BINDING_RATIFICATION_ONLY_V0"
BINDING_CLASS = "SPARSE_SIGNAL_ZERO_TRADE_RESEARCH_V0"
STRATEGY_VERSION = "v2"
FAILED_STRATEGY_VERSION = "v1"
FAILED_CANDIDATE_VERDICT = "ROBUSTNESS_FAILED"

RESEARCH_CANDIDATES: tuple[str, ...] = (
    "trend_following",
    "bollinger_bands",
    "momentum_1h",
)

CLASS_D_COMPLETION_DIGEST = "0610afa34b347abde08768fb2fbfb30fd4bb19ae010f3b2042c67155fb6c0fc4"
BASELINE_HEAD = "a113c6bb667fc38da160637e47f018a5411365a3"
BASELINE_PR = "4879"
PARENT_SCOPE_ID = "POST_NO_PASS_ROBUSTNESS_FAILURE_NEXT_RESEARCH_SCOPE_DEFINITION_V0"

PANEL_STAGING_ROOT = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
PANEL_DATA_DIGEST = "0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1"

PERIOD_BINDING_ID = "extended_chronological_sparse_signal_research_v0"
PERIOD_BINDING_VERSION = "v0"
COVERAGE_START = "2024-05-01T00:00:00Z"
COVERAGE_END = "2024-09-01T00:00:00Z"
TRAINING_START = "2024-05-01T00:00:00Z"
TRAINING_END = "2024-06-15T00:00:00Z"
VALIDATION_START = "2024-06-15T00:00:00Z"
VALIDATION_END = "2024-07-15T00:00:00Z"
OOS_START = "2024-07-15T00:00:00Z"
OOS_END = "2024-09-01T00:00:00Z"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
RUNTIME_REWIRE_ADMISSIBLE = False
SAME_BINDING_RETRY_ALLOWED = False
PARAMETER_RESCUE_ALLOWED = False
THRESHOLD_LOWERING_ALLOWED = False

REQUIRED_BINDING_FIELDS: tuple[str, ...] = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "expected_output_contract",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BindingValidationResultV0:
    verdict: ValidationVerdict
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0",
            "binding_class": BINDING_CLASS,
            "strategy_version": STRATEGY_VERSION,
            "schema_version": SCHEMA_VERSION,
        }
    )


def compute_period_digest_v0() -> str:
    return _stable_digest(
        {
            "period_binding_id": PERIOD_BINDING_ID,
            "period_binding_version": PERIOD_BINDING_VERSION,
            "coverage_period_start_utc": COVERAGE_START,
            "coverage_period_end_utc": COVERAGE_END,
            "training_start": TRAINING_START,
            "training_end": TRAINING_END,
            "validation_start": VALIDATION_START,
            "validation_end": VALIDATION_END,
            "out_of_sample_start": OOS_START,
            "out_of_sample_end": OOS_END,
        }
    )


def build_period_binding_v0(*, period_digest: str) -> dict[str, Any]:
    return {
        "coverage_period_end_utc": COVERAGE_END,
        "coverage_period_start_utc": COVERAGE_START,
        "embargo_duration": "PT2H",
        "period_binding_id": PERIOD_BINDING_ID,
        "period_binding_ref": f"{PERIOD_BINDING_ID}:{PERIOD_BINDING_VERSION}",
        "period_binding_version": PERIOD_BINDING_VERSION,
        "period_digest": period_digest,
        "purge_duration": "PT2H",
        "sparse_signal_research_binding": True,
        "split_policy_id": PERIOD_BINDING_ID,
        "split_policy_version": PERIOD_BINDING_VERSION,
    }


def build_sparse_signal_instrument_binding_v0(
    *,
    class_d_instrument_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "binding_mode": "panel_sequential_signal_density_research_v0",
        "binding_class": BINDING_CLASS,
        "bitcoin_direction_allowed": False,
        "eligible_instrument_count": class_d_instrument_binding.get(
            "eligible_instrument_count", 118
        ),
        "eligible_instrument_ids": list(
            class_d_instrument_binding.get("eligible_instrument_ids", ())
        ),
        "evaluation_mode": "sequential_panel_member_rotation",
        "futures_only": True,
        "instrument_binding_version": "v0",
        "instrument_selection_owner": (
            "post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0"
        ),
        "no_parallel_universe_ssot": True,
        "panel_member_rotation_policy": "deterministic_instrument_id_asc",
        "signal_density_research": True,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "substantially_differs_from_class_d_narrow_eth": True,
        "venue_id": "okx",
    }


def build_sparse_signal_dataset_binding_v0(
    *,
    class_d_dataset_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "dataset_binding_active": True,
        "dataset_extension_funding": "extended_chronological_with_funding_v1",
        "dataset_extension_ohlcv": "extended_chronological_v1",
        "dataset_id": DATASET_ID,
        "evaluation_price_data_adapter": {
            "adapter_kind": "PANEL_SEQUENTIAL_SIGNAL_DENSITY_RESEARCH_ADAPTER_v0",
            "binding_class": BINDING_CLASS,
            "panel_member_count": class_d_dataset_binding.get("panel_member_count", 118),
            "panel_staging_root": PANEL_STAGING_ROOT,
            "panel_dataset_digest": PANEL_DATA_DIGEST,
            "sequential_rotation": True,
            "substantially_differs_from_class_d_narrow_eth": True,
        },
        "funding_coverage_ratio": 1.0,
        "network_access_forbidden": True,
        "panel_calendar_end_utc": COVERAGE_END,
        "panel_calendar_start_utc": COVERAGE_START,
        "panel_dataset_manifest_ref": class_d_dataset_binding.get("panel_dataset_manifest_ref"),
        "panel_funding_dataset_manifest_ref": class_d_dataset_binding.get(
            "panel_funding_dataset_manifest_ref"
        ),
        "panel_member_count": class_d_dataset_binding.get("panel_member_count", 118),
        "panel_staging_root": PANEL_STAGING_ROOT,
    }


def build_parameter_binding_v0(
    *,
    class_d_parameter_binding: Mapping[str, Any],
    parameter_schema_version: str,
) -> dict[str, Any]:
    return {
        **dict(class_d_parameter_binding),
        "binding_class": BINDING_CLASS,
        "parameter_rescue_forbidden": True,
        "parameter_optimization_forbidden": True,
        "threshold_lowering_forbidden": True,
        "unchanged_from_terminal_class_d_v1": True,
        "parameter_schema_version": parameter_schema_version,
    }


def build_expected_output_contract_v0(*, strategy_id: str) -> dict[str, Any]:
    return {
        "contract_version": "sparse_signal_zero_trade_research_output_v0",
        "required_artifacts": [
            "trade_count",
            "sparse_signal_density_metrics",
            "walk_forward_oos_trade_count",
            "monte_carlo_sequence_stability",
            "stress_cost_sensitivity",
            "economic_validity_verdict",
        ],
        "strategy_id": strategy_id,
        "strategy_version": STRATEGY_VERSION,
    }


def _load_class_d_candidate(
    class_d_completion: Mapping[str, Any],
    strategy_id: str,
) -> dict[str, Any]:
    for candidate in class_d_completion.get("candidates", ()):
        if isinstance(candidate, Mapping) and candidate.get("strategy_id") == strategy_id:
            return dict(candidate)
    raise KeyError(f"missing class_d candidate: {strategy_id}")


def materialize_sparse_signal_candidate_v0(
    *,
    strategy_id: str,
    class_d_completion: Mapping[str, Any],
    period_digest: str,
    implementation_digest: str,
) -> dict[str, Any]:
    class_d = _load_class_d_candidate(class_d_completion, strategy_id)
    parameter_binding = build_parameter_binding_v0(
        class_d_parameter_binding=class_d["parameter_binding"],
        parameter_schema_version=str(class_d["parameter_schema_version"]),
    )
    instrument_binding = build_sparse_signal_instrument_binding_v0(
        class_d_instrument_binding=class_d["instrument_binding"],
    )
    dataset_binding = build_sparse_signal_dataset_binding_v0(
        class_d_dataset_binding=class_d["dataset_binding"],
    )
    period_binding = build_period_binding_v0(period_digest=period_digest)
    candidate: dict[str, Any] = {
        "binding_class": BINDING_CLASS,
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, STRATEGY_VERSION
        ),
        "canonical_trading_logic_binding_version": class_d[
            "canonical_trading_logic_binding_version"
        ],
        "canonical_trading_logic_version": class_d["canonical_trading_logic_version"],
        "config_digest": class_d["config_digest"],
        "data_digest": PANEL_DATA_DIGEST,
        "dataset_binding": dataset_binding,
        "dataset_provenance": {
            "binding_class": BINDING_CLASS,
            "cross_branch_evidence_forbidden": True,
            "dataset_extension_funding": "extended_chronological_with_funding_v1",
            "dataset_id": DATASET_ID,
            "panel_staging_root": PANEL_STAGING_ROOT,
            "pit_safe": True,
            "sparse_signal_research": True,
        },
        "dataset_version": "v1",
        "economic_evaluation_authorized": False,
        "economic_policy_binding": {
            "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
            "sparse_signal_research_policy": True,
        },
        "execution_model_binding": dict(class_d["execution_model_binding"]),
        "expected_output_contract": build_expected_output_contract_v0(strategy_id=strategy_id),
        "fee_model_binding": dict(class_d["fee_model_binding"]),
        "funding_model_binding": dict(class_d["funding_model_binding"]),
        "implementation_digest": implementation_digest,
        "instrument_binding": instrument_binding,
        "operator_ratification_ref": (
            "post_no_pass_sparse_signal_zero_trade_versioned_binding_ratification_v0"
        ),
        "out_of_sample_period": {
            "end": OOS_END,
            "start": OOS_START,
            "status": "BOUND_NOT_MATERIALIZED",
        },
        "parameter_binding": parameter_binding,
        "parameter_schema_version": class_d["parameter_schema_version"],
        "period_binding": period_binding,
        "period_digest": period_digest,
        "ratified": True,
        "slippage_model_binding": dict(class_d["slippage_model_binding"]),
        "source_class_d_binding_ref": (
            f"{CLASS_D_COMPLETION_REL_PATH}#{strategy_id}/{FAILED_STRATEGY_VERSION}"
        ),
        "source_class_d_binding_semantic_digest": class_d["binding_semantic_digest"],
        "source_config_ref": STEP31F_CONFIG_PATHS[strategy_id],
        "strategy_id": strategy_id,
        "strategy_params_digest": class_d["strategy_params_digest"],
        "strategy_version": STRATEGY_VERSION,
        "substantially_differs_from_class_d_v1": True,
        "terminal_class_d_v1_verdict": FAILED_CANDIDATE_VERDICT,
        "training_period": {
            "end": TRAINING_END,
            "start": TRAINING_START,
            "status": "BOUND_NOT_MATERIALIZED",
        },
        "validation_period": {
            "end": VALIDATION_END,
            "start": VALIDATION_START,
            "status": "BOUND_NOT_MATERIALIZED",
        },
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
    *,
    repo_root: Path,
    class_d_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if class_d_completion is None:
        class_d_path = repo_root / CLASS_D_COMPLETION_REL_PATH
        class_d_completion = json.loads(class_d_path.read_text(encoding="utf-8"))

    period_digest = compute_period_digest_v0()
    implementation_digest = compute_implementation_digest_v0()
    candidates = [
        materialize_sparse_signal_candidate_v0(
            strategy_id=strategy_id,
            class_d_completion=class_d_completion,
            period_digest=period_digest,
            implementation_digest=implementation_digest,
        )
        for strategy_id in RESEARCH_CANDIDATES
    ]

    completion_body: dict[str, Any] = {
        "artifact_kind": "post_no_pass_sparse_signal_zero_trade_versioned_binding_completion",
        "artifact_version": "v0",
        "authority_effect": AUTHORITY_EFFECT,
        "baseline_head": BASELINE_HEAD,
        "baseline_pr": BASELINE_PR,
        "binding_class": BINDING_CLASS,
        "binding_materialization_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "blocked_actions": [
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "SAME_BINDING_RETRY",
            "UNCHANGED_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "RESULT_RESCUE",
            "RUNTIME",
            "SHADOW",
            "PAPER",
            "TESTNET",
            "SCHEDULER",
            "ORDERS",
            "CREDENTIALS",
            "ARMING",
            "CANARY",
            "LIVE",
        ],
        "candidates": candidates,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "class_d_terminal_binding_exclusion": {
            "completion_digest": CLASS_D_COMPLETION_DIGEST,
            "failed_candidate_verdict": FAILED_CANDIDATE_VERDICT,
            "failed_candidates": list(RESEARCH_CANDIDATES),
            "failed_strategy_version": FAILED_STRATEGY_VERSION,
            "retry_forbidden": True,
            "same_binding_retry_allowed": False,
        },
        "completion_id": COMPLETION_ID,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "evidence_class_id": "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_VERSIONED_BINDING_RATIFICATION_V0",
        "expected_output_contract_required": True,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "futures_only": FUTURES_ONLY,
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "governance_ref": GOVERNANCE_REL_PATH,
        "implementation_digest": implementation_digest,
        "no_evaluation_authority": True,
        "no_promotion_authority": True,
        "no_runtime_authority": True,
        "non_authorizing": True,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "parameter_rescue_allowed": False,
        "parent_scope_id": PARENT_SCOPE_ID,
        "parent_scope_ref": SCOPE_DEFINITION_REL_PATH,
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_eligible": False,
        "required_binding_fields": list(REQUIRED_BINDING_FIELDS),
        "required_next_go_for_execution": NEXT_EXECUTION_GO,
        "research_hypothesis": (
            "SPARSE_SIGNAL_ZERO_TRADE_REQUIRES_NEW_VERSIONED_BINDINGS_NOT_UNCHANGED_CLASS_D_RETRY"
        ),
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "same_binding_retry_allowed": SAME_BINDING_RETRY_ALLOWED,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "spot_allowed": SPOT_ALLOWED,
        "status": "BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED",
        "strategy_version": STRATEGY_VERSION,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "terminal_negative_evidence_unchanged": True,
        "threshold_lowering_allowed": THRESHOLD_LOWERING_ALLOWED,
        "trading_effect": "NONE",
    }
    completion_body["completion_digest"] = compute_completion_digest_v0(completion_body)
    return completion_body


def serialize_completion_canonical_v0(completion: Mapping[str, Any]) -> str:
    return json.dumps(completion, indent=2, sort_keys=True) + "\n"


def _candidate_has_required_fields(candidate: Mapping[str, Any]) -> tuple[str, ...]:
    missing: list[str] = []
    for field in REQUIRED_BINDING_FIELDS:
        if field not in candidate:
            missing.append(field)
    return tuple(missing)


def validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
    completion: Any,
    *,
    class_d_completion: Mapping[str, Any] | None = None,
) -> BindingValidationResultV0:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            fail_reasons=("COMPLETION_NOT_OBJECT",),
        )

    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if completion.get("go_token") != CONFIRM_GO:
        reasons.append("GO_TOKEN_MISMATCH")
    if completion.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_MUST_BE_FALSE")
    if completion.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if completion.get("same_binding_retry_allowed") is not False:
        reasons.append("SAME_BINDING_RETRY_MUST_BE_FALSE")
    if completion.get("parameter_rescue_allowed") is not False:
        reasons.append("PARAMETER_RESCUE_MUST_BE_FALSE")
    if completion.get("threshold_lowering_allowed") is not False:
        reasons.append("THRESHOLD_LOWERING_MUST_BE_FALSE")
    if completion.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_MUST_BE_TRUE")
    if completion.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_ALLOWED_MUST_BE_FALSE")
    if completion.get("authority_effect") != AUTHORITY_EFFECT:
        reasons.append("AUTHORITY_EFFECT_MISMATCH")
    if completion.get("runtime_effect") != RUNTIME_EFFECT:
        reasons.append("RUNTIME_EFFECT_MISMATCH")

    expected_digest = compute_completion_digest_v0(completion)
    if completion.get("completion_digest") != expected_digest:
        reasons.append("COMPLETION_DIGEST_MISMATCH")

    candidates = completion.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(RESEARCH_CANDIDATES):
        reasons.append("CANDIDATE_COUNT_MISMATCH")
    else:
        seen: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                reasons.append("CANDIDATE_NOT_OBJECT")
                continue
            strategy_id = str(candidate.get("strategy_id", ""))
            if strategy_id in seen:
                reasons.append(f"DUPLICATE_CANDIDATE:{strategy_id}")
            seen.add(strategy_id)
            if candidate.get("strategy_version") != STRATEGY_VERSION:
                reasons.append(f"WRONG_STRATEGY_VERSION:{strategy_id}")
            if candidate.get("terminal_class_d_v1_verdict") != FAILED_CANDIDATE_VERDICT:
                reasons.append(f"TERMINAL_VERDICT_MISSING:{strategy_id}")
            if candidate.get("substantially_differs_from_class_d_v1") is not True:
                reasons.append(f"NOT_SUBSTANTIALLY_DIFFERENT:{strategy_id}")
            missing = _candidate_has_required_fields(candidate)
            for field in missing:
                reasons.append(f"MISSING_REQUIRED_FIELD:{strategy_id}:{field}")
            param = candidate.get("parameter_binding")
            if isinstance(param, Mapping):
                if param.get("parameter_rescue_forbidden") is not True:
                    reasons.append(f"PARAMETER_RESCUE_NOT_FORBIDDEN:{strategy_id}")
                if param.get("unchanged_from_terminal_class_d_v1") is not True:
                    reasons.append(f"PARAMETER_NOT_UNCHANGED:{strategy_id}")
            expected_semantic = compute_binding_semantic_digest_v0(candidate)
            if candidate.get("binding_semantic_digest") != expected_semantic:
                reasons.append(f"BINDING_SEMANTIC_DIGEST_MISMATCH:{strategy_id}")

    if class_d_completion is not None:
        for strategy_id in RESEARCH_CANDIDATES:
            class_d = _load_class_d_candidate(class_d_completion, strategy_id)
            candidate = next(
                (
                    item
                    for item in candidates
                    if isinstance(item, Mapping) and item.get("strategy_id") == strategy_id
                ),
                None,
            )
            if candidate is None:
                continue
            if class_d["parameter_binding"] != {
                key: value
                for key, value in candidate["parameter_binding"].items()
                if key
                not in (
                    "binding_class",
                    "parameter_rescue_forbidden",
                    "parameter_optimization_forbidden",
                    "threshold_lowering_forbidden",
                    "unchanged_from_terminal_class_d_v1",
                    "parameter_schema_version",
                )
            }:
                reasons.append(f"PARAMETER_BINDING_CHANGED:{strategy_id}")

    if reasons:
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            fail_reasons=tuple(reasons),
        )
    return BindingValidationResultV0(verdict=ValidationVerdict.ACCEPTED, fail_reasons=())
