"""Phase 4 Canonical Robustness Suite v1 (research evidence only).

Deterministic, versioned robustness evaluation for a Canonical Experiment
Identity bound candidate. This layer reuses Phase 1 identity, Phase 2
experiment_id / REJECTED_* dispositions, and Phase 3 Failure Memory. It
has no runtime, order, live, funding, canary, promotion, or config-write
authority.

BEST_SHARPE => PROMOTE is forbidden. Missing required evidence cannot be
treated as PASS.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import pandas as pd

from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    canonicalize_value,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import (
    REF_KIND_IDENTITY_DIGEST_BOUND,
    derive_experiment_id_v1,
)
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    FAILURE_CLASS_TO_FAILED_GATE,
    build_canonical_failure_memory_record_v1,
)
from src.experiments.monte_carlo import MonteCarloConfig, run_monte_carlo_from_returns
from src.experiments.stress_tests import (
    StressScenarioConfig,
    run_stress_test_suite,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_robustness_suite_v1"
ROBUSTNESS_DOMAIN: Final[str] = "peak_trade.canonical_robustness_suite.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
METRIC_DEFINITION_VERSION: Final[str] = "canonical_robustness_metrics_v1"
REF_KIND_IDENTITY_BOUND: Final[str] = REF_KIND_IDENTITY_DIGEST_BOUND

ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY: Final[bool] = False
ROBUSTNESS_SUITE_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
ROBUSTNESS_SUITE_CAN_PROMOTE: Final[bool] = False
ROBUSTNESS_SUITE_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
ROBUSTNESS_SUITE_CAN_INCREASE_RISK: Final[bool] = False
ROBUSTNESS_SUITE_CAN_INCREASE_LEVERAGE: Final[bool] = False
ROBUSTNESS_SUITE_CAN_FUND: Final[bool] = False
ROBUSTNESS_SUITE_CAN_SUBMIT_ORDER: Final[bool] = False
ROBUSTNESS_SUITE_CAN_ARM: Final[bool] = False
ROBUSTNESS_SUITE_CAN_ENABLE: Final[bool] = False
ROBUSTNESS_SUITE_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
ROBUSTNESS_SUITE_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
ROBUSTNESS_SUITE_CAN_AUTHORIZE_CANARY: Final[bool] = False
ROBUSTNESS_SUITE_CAN_PROMOTE_TO_LIVE: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
SINGLE_METRIC_PROMOTION: Final[bool] = False
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
DETERMINISTIC_RANDOMNESS_KIND: Final[str] = "NUMPY_GENERATOR_DEFAULT_RNG"

STATUS_PASS: Final[str] = "PASS"
STATUS_FAIL: Final[str] = "FAIL"
STATUS_BLOCKED: Final[str] = "BLOCKED"
STATUS_NOT_APPLICABLE: Final[str] = "NOT_APPLICABLE"
STATUS_NOT_EVALUATED: Final[str] = "NOT_EVALUATED"
STATUS_BLOCKED_MISSING_CAPABILITY: Final[str] = "BLOCKED_MISSING_CAPABILITY"
TEST_STATUSES: Final[tuple[str, ...]] = (
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_BLOCKED,
    STATUS_NOT_APPLICABLE,
    STATUS_NOT_EVALUATED,
    STATUS_BLOCKED_MISSING_CAPABILITY,
)
AGGREGATE_STATUSES: Final[tuple[str, ...]] = (
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_BLOCKED,
)
DIMENSION_COMPUTED: Final[str] = "COMPUTED"
DIMENSION_MISSING: Final[str] = "MISSING"
PROMOTION_INTENT_FORBIDDEN: Final[str] = "FORBIDDEN"

REQUIRED_ROBUSTNESS_TESTS: Final[tuple[str, ...]] = (
    "TRAIN_VALIDATION_HOLDOUT",
    "WALK_FORWARD",
    "ROLLING_OOS",
    "PURGED_SPLIT",
    "EMBARGO",
    "MONTE_CARLO",
    "BLOCK_BOOTSTRAP",
    "PARAMETER_SENSITIVITY",
    "FEE_STRESS",
    "SLIPPAGE_STRESS",
    "FUNDING_STRESS",
    "LATENCY_STRESS",
    "SPREAD_STRESS",
    "LIQUIDITY_STRESS",
    "CRASH_SCENARIOS",
    "MISSING_DATA_STRESS",
    "BAD_TICK_STRESS",
    "REGIME_STRESS",
    "RISK_STRESS",
    "MULTIPLE_TESTING_CONTROLS",
    "SINGLE_METRIC_PROMOTION_GUARD",
)
DEFERRED_STATISTICAL_CONTROLS: Final[tuple[str, ...]] = (
    "DEFLATED_SHARPE_RATIO",
    "PROBABILISTIC_SHARPE_RATIO",
    "PROBABILITY_OF_BACKTEST_OVERFITTING",
    "CPCV",
    "WHITE_REALITY_CHECK",
    "SPA_TEST",
)
ALL_CATALOG_TESTS: Final[tuple[str, ...]] = (
    REQUIRED_ROBUSTNESS_TESTS + DEFERRED_STATISTICAL_CONTROLS
)
REQUIRED_EVIDENCE_DIMENSIONS: Final[tuple[str, ...]] = (
    "sharpe",
    "sortino",
    "max_dd",
    "profit_factor",
    "turnover",
    "fee_drag",
    "slippage_sensitivity",
    "funding_sensitivity",
    "tail_risk",
    "exposure",
    "parameter_stability",
    "oos_stability",
    "regime_concentration",
    "sample_size",
)
TEST_FAILURE_CLASSES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "TRAIN_VALIDATION_HOLDOUT": "REJECTED_OVERFIT",
        "WALK_FORWARD": "REJECTED_OVERFIT",
        "ROLLING_OOS": "REJECTED_OVERFIT",
        "PURGED_SPLIT": "REJECTED_OVERFIT",
        "EMBARGO": "REJECTED_OVERFIT",
        "MONTE_CARLO": "REJECTED_TAIL_RISK",
        "BLOCK_BOOTSTRAP": "REJECTED_TAIL_RISK",
        "PARAMETER_SENSITIVITY": "REJECTED_OVERFIT",
        "FEE_STRESS": "REJECTED_COST_SENSITIVITY",
        "SLIPPAGE_STRESS": "REJECTED_COST_SENSITIVITY",
        "FUNDING_STRESS": "REJECTED_COST_SENSITIVITY",
        "LATENCY_STRESS": "REJECTED_COST_SENSITIVITY",
        "SPREAD_STRESS": "REJECTED_COST_SENSITIVITY",
        "LIQUIDITY_STRESS": "REJECTED_COST_SENSITIVITY",
        "CRASH_SCENARIOS": "REJECTED_TAIL_RISK",
        "MISSING_DATA_STRESS": "REJECTED_DATA_QUALITY",
        "BAD_TICK_STRESS": "REJECTED_DATA_QUALITY",
        "REGIME_STRESS": "REJECTED_REGIME_CONCENTRATION",
        "RISK_STRESS": "REJECTED_TAIL_RISK",
        "MULTIPLE_TESTING_CONTROLS": "REJECTED_OVERFIT",
        "SINGLE_METRIC_PROMOTION_GUARD": "REJECTED_POLICY",
    }
)
_STATISTICAL_CONTROL_REASONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "DEFLATED_SHARPE_RATIO": (
            "Deflated Sharpe Ratio is not implemented: no bound non-centrality "
            "and trial-count contract exists for Canonical Experiment Identity"
        ),
        "PROBABILISTIC_SHARPE_RATIO": (
            "Probabilistic Sharpe Ratio is not implemented: no bound Sharpe "
            "sampling distribution owner is wired to this suite"
        ),
        "PROBABILITY_OF_BACKTEST_OVERFITTING": (
            "Probability of Backtest Overfitting is not implemented: CSCV/PBO "
            "requires a combinatorially partitioned trial matrix that this "
            "identity contract does not yet own"
        ),
        "CPCV": (
            "Combinatorial Purged Cross-Validation is not implemented: no "
            "purged combinatorial split engine is bound to experiment identity"
        ),
        "WHITE_REALITY_CHECK": (
            "White Reality Check is not implemented: no bound benchmark-null "
            "and resampling family exists for this contract"
        ),
        "SPA_TEST": (
            "Hansen SPA test is not implemented: no bound superior predictive "
            "ability resampling owner exists for this contract"
        ),
    }
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
    }
)
_IDENTITY_REF_BINDINGS: Final[tuple[tuple[str, str], ...]] = (
    ("dataset_ref", "dataset_digest"),
    ("split_policy_ref", "split_policy_digest"),
    ("cost_model_ref", "cost_model_digest"),
    ("risk_policy_ref", "risk_policy_digest"),
)
_CORE_LOGIC_DIGEST_FIELDS: Final[tuple[str, ...]] = (
    "trading_decision_core_digest",
    "market_context_contract_digest",
    "bull_bear_logic_digest",
    "state_switch_logic_digest",
    "survival_logic_digest",
    "suitability_logic_digest",
    "double_play_logic_digest",
    "entry_position_exit_logic_digest",
)

_LOGGER = logging.getLogger(__name__)


class RobustnessSuiteValidationError(ValueError):
    """Fail-closed Canonical Robustness Suite v1 validation error."""


@dataclass(frozen=True)
class CanonicalRobustnessSuiteRequestV1:
    experiment_identity: Mapping[str, Any]
    candidate_ref: str
    dataset_ref: Mapping[str, Any]
    split_policy_ref: Mapping[str, Any]
    cost_model_ref: Mapping[str, Any]
    risk_policy_ref: Mapping[str, Any]
    seed: int
    created_at: str
    robustness_policy: Mapping[str, Any]
    observations: Mapping[str, Any]
    hypothesis_id: str
    regime: str
    parameter_region: Mapping[str, Any]
    metric_definition_version: str = METRIC_DEFINITION_VERSION
    experiment_id: str | None = None
    promotion_intent: str | None = None


def canonical_robustness_policy_v1() -> dict[str, Any]:
    return {
        "annualization": "MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION",
        "crash_max_dd_limit": 0.9,
        "crash_severity": 0.2,
        "crash_window": 5,
        "cost_stress_sharpe_collapse_ratio": 0.5,
        "max_neighbor_degradation": 0.5,
        "max_parameter_sign_flips": 0,
        "mc_block_size": 5,
        "mc_min_p5_sharpe": -1.0,
        "mc_num_runs": 16,
        "min_sample_size": 16,
        "min_split_size": 4,
        "multiple_testing_correction": "BONFERRONI",
        "oos_sharpe_collapse_ratio": 0.5,
        "policy_id": "canonical_robustness_policy_v1",
        "regime_min_share": 0.15,
        "required_evidence_dimensions": list(REQUIRED_EVIDENCE_DIMENSIONS),
        "required_tests_for_pass": list(REQUIRED_ROBUSTNESS_TESTS),
        "rolling_step": 8,
        "rolling_test_size": 8,
        "train_fraction": 0.5,
        "validation_fraction": 0.25,
    }


def derive_robustness_policy_digest_v1(policy: Mapping[str, Any]) -> str:
    canonical = _canonicalize_tree("robustness_policy", policy)
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{ROBUSTNESS_DOMAIN}.robustness_policy",
        "payload": canonical,
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def derive_robustness_suite_identity_v1(
    *,
    experiment_id: str,
    candidate_ref: str,
    robustness_policy_digest: str,
    observations_digest: str,
    seed: int,
    metric_definition_version: str,
) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{ROBUSTNESS_DOMAIN}.suite_identity",
        "payload": {
            "candidate_ref": candidate_ref,
            "experiment_id": experiment_id,
            "metric_definition_version": metric_definition_version,
            "observations_digest": observations_digest,
            "robustness_policy_digest": robustness_policy_digest,
            "robustness_suite_version": SCHEMA_VERSION,
            "seed": seed,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def build_canonical_robustness_evidence_v1(
    request: CanonicalRobustnessSuiteRequestV1,
) -> Mapping[str, Any]:
    identity = _require_identity(request.experiment_identity)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    if request.experiment_id is not None:
        provided = _require_sha256("experiment_id", request.experiment_id)
        if provided != experiment_id:
            raise RobustnessSuiteValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    if request.metric_definition_version != METRIC_DEFINITION_VERSION:
        raise RobustnessSuiteValidationError("metric_definition_version mismatch")
    if identity.get("seed") != request.seed:
        raise RobustnessSuiteValidationError("seed must match experiment_identity.seed")
    created_at = _require_created_at(request.created_at)
    candidate_ref = _require_token("candidate_ref", request.candidate_ref)
    hypothesis_id = _require_token("hypothesis_id", request.hypothesis_id)
    regime = _require_token("regime", request.regime)
    policy = _canonicalize_tree("robustness_policy", request.robustness_policy)
    _validate_policy(policy)
    policy_digest = derive_robustness_policy_digest_v1(policy)
    observations = _canonicalize_tree("observations", request.observations)
    observations_digest = compute_content_sha256(
        {
            "digest_algorithm": DIGEST_ALGORITHM,
            "digest_domain": f"{ROBUSTNESS_DOMAIN}.observations",
            "payload": observations,
            "schema_version": SCHEMA_VERSION,
        }
    )
    dataset_ref = _bound_ref("dataset_ref", request.dataset_ref, identity)
    split_policy_ref = _bound_ref("split_policy_ref", request.split_policy_ref, identity)
    cost_model_ref = _bound_ref("cost_model_ref", request.cost_model_ref, identity)
    risk_policy_ref = _bound_ref("risk_policy_ref", request.risk_policy_ref, identity)
    parameter_region = _canonicalize_tree("parameter_region", request.parameter_region)
    promotion_intent = _require_promotion_intent(request.promotion_intent)
    test_results = _evaluate_catalog(
        policy=policy,
        observations=observations,
        seed=request.seed,
        promotion_intent=promotion_intent,
    )
    failed_gates = [item["test_id"] for item in test_results if item["status"] == STATUS_FAIL]
    dimensions = _evidence_dimensions(observations, policy)
    aggregate_status = _aggregate_status(test_results, dimensions, policy)
    suite_identity = derive_robustness_suite_identity_v1(
        experiment_id=experiment_id,
        candidate_ref=candidate_ref,
        robustness_policy_digest=policy_digest,
        observations_digest=observations_digest,
        seed=request.seed,
        metric_definition_version=request.metric_definition_version,
    )
    evidence = {
        "aggregate_status": aggregate_status,
        "candidate_ref": candidate_ref,
        "canonical_trading_decision_core_bound": True,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "cost_model_ref": cost_model_ref,
        "created_at": created_at,
        "dataset_digest": identity["dataset_digest"],
        "dataset_ref": dataset_ref,
        "deterministic_randomness_contract": {
            "kind": DETERMINISTIC_RANDOMNESS_KIND,
            "monte_carlo_owner": "src.experiments.monte_carlo",
            "seed": request.seed,
            "stress_tests_owner": "src.experiments.stress_tests",
        },
        "digest_algorithm": DIGEST_ALGORITHM,
        "evidence_dimensions": dimensions,
        "evidence_refs": [
            {
                "digest": identity["identity_digest"],
                "kind": "EXPERIMENT_RECORD",
                "ref": experiment_id,
            }
        ],
        "experiment_id": experiment_id,
        "experiment_identity": identity,
        "failed_gates": failed_gates,
        "hypothesis_id": hypothesis_id,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "metric_definition_version": METRIC_DEFINITION_VERSION,
        "observations_digest": observations_digest,
        "parameter_region": parameter_region,
        "promotion_authority": PROMOTION_AUTHORITY,
        "promotion_intent": promotion_intent,
        "regime": regime,
        "risk_policy_ref": risk_policy_ref,
        "robustness_domain": ROBUSTNESS_DOMAIN,
        "robustness_policy_digest": policy_digest,
        "robustness_suite_can_arm": ROBUSTNESS_SUITE_CAN_ARM,
        "robustness_suite_can_authorize_canary": ROBUSTNESS_SUITE_CAN_AUTHORIZE_CANARY,
        "robustness_suite_can_create_confirm_token": (ROBUSTNESS_SUITE_CAN_CREATE_CONFIRM_TOKEN),
        "robustness_suite_can_enable": ROBUSTNESS_SUITE_CAN_ENABLE,
        "robustness_suite_can_fund": ROBUSTNESS_SUITE_CAN_FUND,
        "robustness_suite_can_increase_leverage": ROBUSTNESS_SUITE_CAN_INCREASE_LEVERAGE,
        "robustness_suite_can_increase_risk": ROBUSTNESS_SUITE_CAN_INCREASE_RISK,
        "robustness_suite_can_mutate_live_config": ROBUSTNESS_SUITE_CAN_MUTATE_LIVE_CONFIG,
        "robustness_suite_can_promote": ROBUSTNESS_SUITE_CAN_PROMOTE,
        "robustness_suite_can_promote_to_live": ROBUSTNESS_SUITE_CAN_PROMOTE_TO_LIVE,
        "robustness_suite_can_submit_order": ROBUSTNESS_SUITE_CAN_SUBMIT_ORDER,
        "robustness_suite_can_use_confirm_token": ROBUSTNESS_SUITE_CAN_USE_CONFIRM_TOKEN,
        "robustness_suite_can_write_live_config": ROBUSTNESS_SUITE_CAN_WRITE_LIVE_CONFIG,
        "robustness_suite_has_runtime_authority": ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY,
        "robustness_suite_identity": suite_identity,
        "robustness_suite_version": SCHEMA_VERSION,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "seed": request.seed,
        "self_learning_self_authorizing_separation": (SELF_LEARNING_SELF_AUTHORIZING_SEPARATION),
        "single_metric_promotion": SINGLE_METRIC_PROMOTION,
        "split_policy_ref": split_policy_ref,
        "test_results": test_results,
    }
    evidence["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in evidence.items() if key != "integrity"}
        )
    }
    validate_canonical_robustness_evidence_v1(evidence)
    frozen = _freeze(evidence)
    _LOGGER.info(
        "canonical_robustness_suite_v1 built identity=%s aggregate=%s failed_gates=%s",
        suite_identity,
        aggregate_status,
        failed_gates,
    )
    return frozen


def validate_canonical_robustness_evidence_v1(evidence: Mapping[str, Any]) -> None:
    if not isinstance(evidence, Mapping):
        raise RobustnessSuiteValidationError("robustness evidence must be a mapping")
    payload = _plain_mapping(evidence)
    if payload.get("robustness_suite_version") != SCHEMA_VERSION:
        raise RobustnessSuiteValidationError("robustness_suite_version mismatch")
    if payload.get("robustness_domain") != ROBUSTNESS_DOMAIN:
        raise RobustnessSuiteValidationError("robustness_domain mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise RobustnessSuiteValidationError("non-COMPLETE robustness evidence is forbidden")
    if payload.get("metric_definition_version") != METRIC_DEFINITION_VERSION:
        raise RobustnessSuiteValidationError("metric_definition_version mismatch")
    if payload.get("single_metric_promotion") is not False:
        raise RobustnessSuiteValidationError("single_metric_promotion must be false")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise RobustnessSuiteValidationError("promotion_authority must be NONE")
    if payload.get("robustness_suite_has_runtime_authority") is not False:
        raise RobustnessSuiteValidationError("robustness_suite_has_runtime_authority must be false")
    if payload.get("robustness_suite_can_promote") is not False:
        raise RobustnessSuiteValidationError("robustness_suite_can_promote must be false")
    if payload.get("robustness_suite_can_mutate_live_config") is not False:
        raise RobustnessSuiteValidationError(
            "robustness_suite_can_mutate_live_config must be false"
        )
    if payload.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise RobustnessSuiteValidationError("runtime_authority_impact must be NONE")
    identity = _require_identity(payload.get("experiment_identity"))
    experiment_id = _require_sha256("experiment_id", payload.get("experiment_id"))
    if experiment_id != derive_experiment_id_v1(str(identity["identity_digest"])):
        raise RobustnessSuiteValidationError(
            "experiment_id is not bound to the Canonical Experiment Identity digest"
        )
    if payload.get("dataset_digest") != identity.get("dataset_digest"):
        raise RobustnessSuiteValidationError(
            "dataset_digest must match experiment_identity.dataset_digest"
        )
    if payload.get("seed") != identity.get("seed"):
        raise RobustnessSuiteValidationError("seed must match experiment_identity.seed")
    for field_name in _CORE_LOGIC_DIGEST_FIELDS:
        _require_sha256(field_name, identity.get(field_name))
    test_results = payload.get("test_results")
    if not isinstance(test_results, list):
        raise RobustnessSuiteValidationError("test_results must be a list")
    seen: set[str] = set()
    for item in test_results:
        if not isinstance(item, Mapping):
            raise RobustnessSuiteValidationError("test_results items must be mappings")
        test_id = item.get("test_id")
        if test_id not in ALL_CATALOG_TESTS:
            raise RobustnessSuiteValidationError(f"unknown robustness test_id: {test_id}")
        if test_id in seen:
            raise RobustnessSuiteValidationError(f"duplicate test_id: {test_id}")
        seen.add(str(test_id))
        if item.get("status") not in TEST_STATUSES:
            raise RobustnessSuiteValidationError(f"invalid test status for {test_id}")
        if item.get("status") == STATUS_PASS and not item.get("reason"):
            raise RobustnessSuiteValidationError(f"PASS without reason is forbidden: {test_id}")
    if seen != set(ALL_CATALOG_TESTS):
        raise RobustnessSuiteValidationError(
            "catalog is incomplete; silent omissions are forbidden"
        )
    if payload.get("aggregate_status") not in AGGREGATE_STATUSES:
        raise RobustnessSuiteValidationError("aggregate_status is invalid")
    if payload.get("aggregate_status") == STATUS_PASS:
        for item in test_results:
            if item["test_id"] in REQUIRED_ROBUSTNESS_TESTS and item["status"] != STATUS_PASS:
                raise RobustnessSuiteValidationError(
                    "aggregate PASS with non-PASS required test is forbidden"
                )
            if item["status"] == STATUS_FAIL:
                raise RobustnessSuiteValidationError("aggregate PASS with FAIL is forbidden")
        dimensions = payload.get("evidence_dimensions")
        if not isinstance(dimensions, Mapping):
            raise RobustnessSuiteValidationError("evidence_dimensions must be a mapping")
        for name in REQUIRED_EVIDENCE_DIMENSIONS:
            dim = dimensions.get(name)
            if not isinstance(dim, Mapping) or dim.get("status") != DIMENSION_COMPUTED:
                raise RobustnessSuiteValidationError(
                    f"aggregate PASS with missing required evidence dimension: {name}"
                )
    integrity = payload.get("integrity")
    expected = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected:
        raise RobustnessSuiteValidationError("integrity.content_sha256 mismatch")


def build_failure_records_for_failed_gates_v1(
    evidence: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    validate_canonical_robustness_evidence_v1(evidence)
    payload = _plain_mapping(evidence)
    records: list[Mapping[str, Any]] = []
    for item in payload["test_results"]:
        if item["status"] != STATUS_FAIL:
            continue
        failure_class = TEST_FAILURE_CLASSES[str(item["test_id"])]
        request = CanonicalFailureMemoryRecordRequestV1(
            experiment_identity=payload["experiment_identity"],
            hypothesis_id=str(payload["hypothesis_id"]),
            failure_class=failure_class,
            failed_gate=FAILURE_CLASS_TO_FAILED_GATE[failure_class],
            rejection_reason=failure_class,
            regime=str(payload["regime"]),
            parameter_region=payload["parameter_region"],
            cost_sensitivity={
                "failed_test_id_digest": _token_digest(str(item["test_id"])),
            },
            instability_indicators={
                "robustness_suite_identity_present": 1,
            },
            evidence_refs=[
                {
                    "kind": "EXPERIMENT_RECORD",
                    "ref": payload["experiment_id"],
                    "digest": payload["experiment_identity"]["identity_digest"],
                }
            ],
            created_at=str(payload["created_at"]),
            robustness_policy_digest=str(payload["robustness_policy_digest"]),
            experiment_id=str(payload["experiment_id"]),
        )
        records.append(build_canonical_failure_memory_record_v1(request))
    return tuple(records)


def canonical_record_payload(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def _evaluate_catalog(
    *,
    policy: Mapping[str, Any],
    observations: Mapping[str, Any],
    seed: int,
    promotion_intent: str,
) -> list[dict[str, Any]]:
    returns = _optional_returns(observations.get("returns"))
    results = [
        _eval_train_validation_holdout(observations, policy, returns),
        _eval_walk_forward(observations, policy),
        _eval_rolling_oos(observations, policy, returns),
        _eval_observation_gate(
            "PURGED_SPLIT",
            observations.get("purged_split"),
            policy,
            missing_reason=("purged split engine is not bound to Canonical Experiment Identity"),
        ),
        _eval_observation_gate(
            "EMBARGO",
            observations.get("embargo"),
            policy,
            missing_reason=("embargo split engine is not bound to Canonical Experiment Identity"),
        ),
        _eval_monte_carlo(returns, policy, seed, method="simple", test_id="MONTE_CARLO"),
        _eval_monte_carlo(
            returns, policy, seed, method="block_bootstrap", test_id="BLOCK_BOOTSTRAP"
        ),
        _eval_parameter_sensitivity(observations.get("parameter_sensitivity"), policy),
        _eval_cost_axis("FEE_STRESS", observations.get("cost_stress"), "fee", policy),
        _eval_cost_axis("SLIPPAGE_STRESS", observations.get("cost_stress"), "slippage", policy),
        _eval_cost_axis("FUNDING_STRESS", observations.get("cost_stress"), "funding", policy),
        _eval_cost_axis("LATENCY_STRESS", observations.get("latency_stress"), None, policy),
        _eval_cost_axis("SPREAD_STRESS", observations.get("spread_stress"), None, policy),
        _eval_cost_axis("LIQUIDITY_STRESS", observations.get("liquidity_stress"), None, policy),
        _eval_crash_scenarios(returns, policy, seed),
        _eval_missing_data(observations.get("missing_data_stress"), policy),
        _eval_bad_tick(observations.get("bad_tick_stress"), policy),
        _eval_regime_stress(observations.get("regime_stress"), policy),
        _eval_risk_stress(observations.get("risk_stress"), policy),
        _eval_multiple_testing(observations.get("multiple_testing"), policy),
        _eval_single_metric_promotion_guard(observations, promotion_intent),
    ]
    for test_id in DEFERRED_STATISTICAL_CONTROLS:
        results.append(
            _test_result(
                test_id,
                STATUS_BLOCKED_MISSING_CAPABILITY,
                _STATISTICAL_CONTROL_REASONS[test_id],
                implementation="NOT_IMPLEMENTED_METHOD_GUARD",
            )
        )
    ordered = {item["test_id"]: item for item in results}
    return [ordered[test_id] for test_id in ALL_CATALOG_TESTS]


def _eval_train_validation_holdout(
    observations: Mapping[str, Any],
    policy: Mapping[str, Any],
    returns: list[float] | None,
) -> dict[str, Any]:
    split_metrics = observations.get("split_metrics")
    metrics = _three_way_metrics(split_metrics, returns, policy)
    if metrics is None:
        return _test_result(
            "TRAIN_VALIDATION_HOLDOUT",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            (
                "train/validation/holdout requires split_metrics or a returns series; "
                "full backtest split runner is not imported into this contract"
            ),
            implementation="ADAPT:src.backtest.parameter_sensitivity_v1.split_bars_train_validation_oos_v1",
        )
    return _oos_gate("TRAIN_VALIDATION_HOLDOUT", metrics, policy)


def _eval_walk_forward(
    observations: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    windows = observations.get("walk_forward_windows")
    if not isinstance(windows, list) or not windows:
        return _test_result(
            "WALK_FORWARD",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            (
                "walk-forward re-optimization runner is not bound to this contract; "
                "provide walk_forward_windows observations to evaluate a produced path"
            ),
            implementation="ADAPT:src.backtest.walkforward.split_train_test_windows",
        )
    test_sharpes: list[float] = []
    train_sharpes: list[float] = []
    for index, window in enumerate(windows):
        if not isinstance(window, Mapping):
            raise RobustnessSuiteValidationError(f"walk_forward_windows[{index}] must be a mapping")
        train_sharpes.append(
            _require_finite(
                f"walk_forward_windows[{index}].train_sharpe",
                window.get("train_sharpe"),
            )
        )
        test_sharpes.append(
            _require_finite(
                f"walk_forward_windows[{index}].test_sharpe",
                window.get("test_sharpe"),
            )
        )
        sample_size = window.get("sample_size")
        if not isinstance(sample_size, int) or sample_size < int(policy["min_split_size"]):
            return _test_result(
                "WALK_FORWARD",
                STATUS_FAIL,
                "walk-forward window sample_size is below policy min_split_size",
                failure_class="REJECTED_OVERFIT",
            )
    collapse = float(policy["oos_sharpe_collapse_ratio"])
    for train_sharpe, test_sharpe in zip(train_sharpes, test_sharpes):
        if train_sharpe > 0 and test_sharpe < train_sharpe * collapse:
            return _test_result(
                "WALK_FORWARD",
                STATUS_FAIL,
                "walk-forward OOS sharpe collapsed versus train",
                failure_class="REJECTED_OVERFIT",
                details={"train_sharpes": train_sharpes, "test_sharpes": test_sharpes},
            )
    return _test_result(
        "WALK_FORWARD",
        STATUS_PASS,
        "walk-forward window observations remain within OOS collapse policy",
        implementation="ADAPT:src.backtest.walkforward",
        details={"window_count": len(windows)},
    )


def _eval_rolling_oos(
    observations: Mapping[str, Any],
    policy: Mapping[str, Any],
    returns: list[float] | None,
) -> dict[str, Any]:
    windows = observations.get("walk_forward_windows")
    if isinstance(windows, list) and windows:
        test_sharpes = [
            _require_finite("rolling_oos.test_sharpe", window.get("test_sharpe"))
            for window in windows
            if isinstance(window, Mapping)
        ]
        if test_sharpes and all(
            value >= float(policy["mc_min_p5_sharpe"]) for value in test_sharpes
        ):
            return _test_result(
                "ROLLING_OOS",
                STATUS_PASS,
                "rolling OOS test sharpes remain above policy floor",
                implementation="ADAPT:src.backtest.walkforward",
                details={"test_sharpes": test_sharpes},
            )
        return _test_result(
            "ROLLING_OOS",
            STATUS_FAIL,
            "rolling OOS test sharpe breached policy floor",
            failure_class="REJECTED_OVERFIT",
        )
    if returns is None or len(returns) < int(policy["min_sample_size"]):
        return _test_result(
            "ROLLING_OOS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "rolling OOS requires walk_forward_windows or a returns series of min_sample_size",
            implementation="ADAPT:src.backtest.walkforward",
        )
    test_size = int(policy["rolling_test_size"])
    step = int(policy["rolling_step"])
    train_size = max(int(policy["min_split_size"]), len(returns) - test_size)
    sharpes: list[float] = []
    index = 0
    while index + train_size + test_size <= len(returns):
        test = returns[index + train_size : index + train_size + test_size]
        sharpes.append(_sharpe(test))
        index += step
    if not sharpes:
        return _test_result(
            "ROLLING_OOS",
            STATUS_BLOCKED,
            "returns series is too short to form a complete rolling OOS window",
        )
    if any(value < float(policy["mc_min_p5_sharpe"]) for value in sharpes):
        return _test_result(
            "ROLLING_OOS",
            STATUS_FAIL,
            "rolling OOS sharpe breached policy floor",
            failure_class="REJECTED_OVERFIT",
            details={"sharpes": sharpes},
        )
    return _test_result(
        "ROLLING_OOS",
        STATUS_PASS,
        "rolling OOS sharpes remain above policy floor",
        implementation="ADAPT:src.backtest.walkforward",
        details={"sharpes": sharpes},
    )


def _eval_monte_carlo(
    returns: list[float] | None,
    policy: Mapping[str, Any],
    seed: int,
    *,
    method: str,
    test_id: str,
) -> dict[str, Any]:
    if returns is None or len(returns) < int(policy["min_sample_size"]):
        return _test_result(
            test_id,
            STATUS_BLOCKED_MISSING_CAPABILITY,
            f"{test_id} requires a returns series of min_sample_size",
            implementation="REUSE:src.experiments.monte_carlo",
        )
    config = MonteCarloConfig(
        num_runs=int(policy["mc_num_runs"]),
        method=method,  # type: ignore[arg-type]
        block_size=int(policy["mc_block_size"]),
        seed=seed,
    )
    summary = run_monte_carlo_from_returns(
        pd.Series(returns, dtype="float64"),
        config,
        stats_fn=_suite_stats,
    )
    p5 = float(summary.metric_quantiles["sharpe"]["p5"])
    details = {
        "num_runs": summary.num_runs,
        "p5_sharpe": p5,
        "p50_sharpe": float(summary.metric_quantiles["sharpe"]["p50"]),
    }
    if p5 < float(policy["mc_min_p5_sharpe"]):
        return _test_result(
            test_id,
            STATUS_FAIL,
            f"{test_id} p5 sharpe breached policy floor",
            failure_class="REJECTED_TAIL_RISK",
            implementation="REUSE:src.experiments.monte_carlo",
            details=details,
        )
    return _test_result(
        test_id,
        STATUS_PASS,
        f"{test_id} p5 sharpe remains above policy floor",
        implementation="REUSE:src.experiments.monte_carlo",
        details=details,
    )


def _eval_parameter_sensitivity(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(
            "PARAMETER_SENSITIVITY",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            (
                "parameter sensitivity grid runner is not imported; provide "
                "parameter_sensitivity observations to evaluate stability"
            ),
            implementation="ADAPT:src.backtest.parameter_sensitivity_v1",
        )
    points = payload.get("points")
    if not isinstance(points, list) or len(points) < 2:
        return _test_result(
            "PARAMETER_SENSITIVITY",
            STATUS_BLOCKED,
            "parameter_sensitivity.points must contain at least two evaluated points",
        )
    sharpes: list[float] = []
    for index, point in enumerate(points):
        if not isinstance(point, Mapping):
            raise RobustnessSuiteValidationError(
                f"parameter_sensitivity.points[{index}] must be a mapping"
            )
        sharpes.append(
            _require_finite(
                f"parameter_sensitivity.points[{index}].sharpe",
                point.get("sharpe"),
            )
        )
    sign_flips = sum(1 for left, right in zip(sharpes, sharpes[1:]) if (left > 0) != (right > 0))
    if sign_flips > int(policy["max_parameter_sign_flips"]):
        return _test_result(
            "PARAMETER_SENSITIVITY",
            STATUS_FAIL,
            "parameter sensitivity sign flips exceed policy",
            failure_class="REJECTED_OVERFIT",
            details={"sign_flips": sign_flips, "sharpes": sharpes},
        )
    center = payload.get("center")
    if isinstance(center, Mapping) and "sharpe" in {str(key) for key in center.keys()}:
        center_sharpe = _require_finite("parameter_sensitivity.center.sharpe", center.get("sharpe"))
        if center_sharpe != 0:
            degradation = max(abs((center_sharpe - value) / center_sharpe) for value in sharpes)
            if degradation > float(policy["max_neighbor_degradation"]):
                return _test_result(
                    "PARAMETER_SENSITIVITY",
                    STATUS_FAIL,
                    "parameter neighbor degradation exceeds policy",
                    failure_class="REJECTED_OVERFIT",
                    details={"degradation": degradation},
                )
    return _test_result(
        "PARAMETER_SENSITIVITY",
        STATUS_PASS,
        "parameter sensitivity observations remain within stability policy",
        implementation="ADAPT:src.backtest.parameter_sensitivity_v1",
        details={"sign_flips": sign_flips, "sharpes": sharpes},
    )


def _eval_cost_axis(
    test_id: str,
    payload: Any,
    axis: str | None,
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    missing_reasons = {
        "FEE_STRESS": "fee stress requires cost_stress.fee observations; cost grid runner is not imported",
        "SLIPPAGE_STRESS": "slippage stress requires cost_stress.slippage observations",
        "FUNDING_STRESS": "funding stress requires cost_stress.funding observations",
        "LATENCY_STRESS": "latency stress is deferred in mv2 research wiring; provide latency_stress observations",
        "SPREAD_STRESS": "spread model is not a bound suite capability; provide spread_stress observations",
        "LIQUIDITY_STRESS": "liquidity stress has no bound market-impact owner; provide liquidity_stress observations",
    }
    if not isinstance(payload, Mapping):
        return _test_result(
            test_id,
            STATUS_BLOCKED_MISSING_CAPABILITY,
            missing_reasons[test_id],
            implementation="REUSE:src.backtest.cost_config_v0",
        )
    if axis is None:
        baseline = payload.get("baseline")
        stressed = payload.get("stressed")
    else:
        baseline = payload.get("baseline")
        stressed = payload.get(axis)
    if not isinstance(baseline, Mapping) or not isinstance(stressed, Mapping):
        return _test_result(
            test_id,
            STATUS_BLOCKED_MISSING_CAPABILITY,
            missing_reasons[test_id],
        )
    baseline_sharpe = _require_finite(f"{test_id}.baseline.sharpe", baseline.get("sharpe"))
    stressed_sharpe = _require_finite(f"{test_id}.stressed.sharpe", stressed.get("sharpe"))
    if baseline_sharpe > 0 and stressed_sharpe < baseline_sharpe * float(
        policy["cost_stress_sharpe_collapse_ratio"]
    ):
        return _test_result(
            test_id,
            STATUS_FAIL,
            f"{test_id} sharpe collapsed versus baseline",
            failure_class=TEST_FAILURE_CLASSES[test_id],
            details={"baseline_sharpe": baseline_sharpe, "stressed_sharpe": stressed_sharpe},
        )
    return _test_result(
        test_id,
        STATUS_PASS,
        f"{test_id} remains within cost-stress collapse policy",
        implementation="REUSE:src.backtest.cost_config_v0",
        details={"baseline_sharpe": baseline_sharpe, "stressed_sharpe": stressed_sharpe},
    )


def _eval_crash_scenarios(
    returns: list[float] | None,
    policy: Mapping[str, Any],
    seed: int,
) -> dict[str, Any]:
    if returns is None or len(returns) < int(policy["min_sample_size"]):
        return _test_result(
            "CRASH_SCENARIOS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "crash scenarios require a returns series of min_sample_size",
            implementation="REUSE:src.experiments.stress_tests",
        )
    scenarios = [
        StressScenarioConfig(
            scenario_type="single_crash_bar",
            severity=float(policy["crash_severity"]),
            window=int(policy["crash_window"]),
            position="middle",
            seed=seed,
        ),
        StressScenarioConfig(
            scenario_type="vol_spike",
            severity=float(policy["crash_severity"]),
            window=int(policy["crash_window"]),
            position="middle",
            seed=seed,
        ),
        StressScenarioConfig(
            scenario_type="gap_down_open",
            severity=float(policy["crash_severity"]),
            window=int(policy["crash_window"]),
            position="middle",
            seed=seed,
        ),
    ]
    suite = run_stress_test_suite(
        pd.Series(returns, dtype="float64"),
        scenarios,
        _suite_stats,
    )
    worst_dd = 0.0
    for result in suite.scenario_results:
        worst_dd = max(worst_dd, float(result.stressed_metrics.get("max_dd", 0.0)))
    details = {
        "scenario_count": len(suite.scenario_results),
        "worst_stressed_max_dd": worst_dd,
    }
    if worst_dd > float(policy["crash_max_dd_limit"]):
        return _test_result(
            "CRASH_SCENARIOS",
            STATUS_FAIL,
            "crash-scenario max_dd exceeded policy limit",
            failure_class="REJECTED_TAIL_RISK",
            implementation="REUSE:src.experiments.stress_tests",
            details=details,
        )
    return _test_result(
        "CRASH_SCENARIOS",
        STATUS_PASS,
        "crash-scenario max_dd remains within policy limit",
        implementation="REUSE:src.experiments.stress_tests",
        details=details,
    )


def _eval_missing_data(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(
            "MISSING_DATA_STRESS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "missing-data injector is not bound to this contract; provide missing_data_stress observations",
        )
    missing_fraction = _require_finite(
        "missing_data_stress.missing_fraction", payload.get("missing_fraction")
    )
    if missing_fraction > 0:
        return _test_result(
            "MISSING_DATA_STRESS",
            STATUS_FAIL,
            "missing-data stress reported a positive missing_fraction",
            failure_class="REJECTED_DATA_QUALITY",
            details={"missing_fraction": missing_fraction},
        )
    return _test_result(
        "MISSING_DATA_STRESS",
        STATUS_PASS,
        "missing-data stress observations report zero missing_fraction",
        details={
            "missing_fraction": missing_fraction,
            "min_sample_size": policy["min_sample_size"],
        },
    )


def _eval_bad_tick(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(
            "BAD_TICK_STRESS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "bad-tick injector is not bound to this contract; provide bad_tick_stress observations",
        )
    bad_tick_count = payload.get("bad_tick_count")
    if not isinstance(bad_tick_count, int) or bad_tick_count < 0:
        raise RobustnessSuiteValidationError(
            "bad_tick_stress.bad_tick_count must be a non-negative int"
        )
    if bad_tick_count > 0:
        return _test_result(
            "BAD_TICK_STRESS",
            STATUS_FAIL,
            "bad-tick stress reported a positive bad_tick_count",
            failure_class="REJECTED_DATA_QUALITY",
            details={"bad_tick_count": bad_tick_count},
        )
    return _test_result(
        "BAD_TICK_STRESS",
        STATUS_PASS,
        "bad-tick stress observations report zero bad ticks",
        details={"bad_tick_count": bad_tick_count, "min_sample_size": policy["min_sample_size"]},
    )


def _eval_regime_stress(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or not isinstance(payload.get("regimes"), Mapping):
        return _test_result(
            "REGIME_STRESS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "regime-aware evaluation is a later phase; provide regime_stress.regimes to gate concentration",
        )
    regimes = payload["regimes"]
    if not regimes:
        return _test_result(
            "REGIME_STRESS",
            STATUS_FAIL,
            "regime_stress.regimes is empty",
            failure_class="REJECTED_REGIME_CONCENTRATION",
        )
    total = 0
    for name, item in regimes.items():
        if not isinstance(item, Mapping):
            raise RobustnessSuiteValidationError(f"regime_stress.regimes.{name} must be a mapping")
        sample_size = item.get("sample_size")
        if not isinstance(sample_size, int) or sample_size < 1:
            raise RobustnessSuiteValidationError(
                f"regime_stress.regimes.{name}.sample_size must be a positive int"
            )
        total += sample_size
    min_share = float(policy["regime_min_share"])
    for name, item in regimes.items():
        share = int(item["sample_size"]) / total
        if share < min_share:
            return _test_result(
                "REGIME_STRESS",
                STATUS_FAIL,
                "regime concentration breached policy min share",
                failure_class="REJECTED_REGIME_CONCENTRATION",
                details={"regime": name, "share": share},
            )
    return _test_result(
        "REGIME_STRESS",
        STATUS_PASS,
        "regime sample shares remain above policy min share",
        details={"regime_count": len(regimes)},
    )


def _eval_risk_stress(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(
            "RISK_STRESS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "risk-stress execution is not bound to this research contract; provide risk_stress observations",
        )
    baseline = payload.get("baseline")
    stressed = payload.get("stressed")
    if not isinstance(baseline, Mapping) or not isinstance(stressed, Mapping):
        return _test_result(
            "RISK_STRESS",
            STATUS_BLOCKED,
            "risk_stress requires baseline and stressed max_dd observations",
        )
    stressed_dd = _require_finite("risk_stress.stressed.max_dd", stressed.get("max_dd"))
    if stressed_dd > float(policy["crash_max_dd_limit"]):
        return _test_result(
            "RISK_STRESS",
            STATUS_FAIL,
            "risk-stress max_dd exceeded policy limit",
            failure_class="REJECTED_TAIL_RISK",
            details={"stressed_max_dd": stressed_dd},
        )
    return _test_result(
        "RISK_STRESS",
        STATUS_PASS,
        "risk-stress max_dd remains within policy limit",
        details={"stressed_max_dd": stressed_dd},
    )


def _eval_multiple_testing(payload: Any, policy: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(
            "MULTIPLE_TESTING_CONTROLS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            "multiple-testing family is not owned by this suite unless explicitly provided",
        )
    correction = payload.get("correction")
    if correction != policy["multiple_testing_correction"]:
        return _test_result(
            "MULTIPLE_TESTING_CONTROLS",
            STATUS_BLOCKED_MISSING_CAPABILITY,
            (
                f"only {policy['multiple_testing_correction']} is implemented; "
                f"requested {correction!r} is not a bound capability"
            ),
        )
    family_size = payload.get("family_size")
    p_value = payload.get("p_value")
    alpha = payload.get("alpha")
    if not isinstance(family_size, int) or family_size < 1:
        raise RobustnessSuiteValidationError("multiple_testing.family_size must be a positive int")
    p_value_f = _require_finite("multiple_testing.p_value", p_value)
    alpha_f = _require_finite("multiple_testing.alpha", alpha)
    adjusted = p_value_f * family_size
    if adjusted > alpha_f:
        return _test_result(
            "MULTIPLE_TESTING_CONTROLS",
            STATUS_FAIL,
            "Bonferroni-adjusted p-value exceeds alpha",
            failure_class="REJECTED_OVERFIT",
            details={"adjusted_p_value": adjusted, "alpha": alpha_f},
        )
    return _test_result(
        "MULTIPLE_TESTING_CONTROLS",
        STATUS_PASS,
        "Bonferroni-adjusted p-value remains within alpha",
        details={"adjusted_p_value": adjusted, "alpha": alpha_f, "family_size": family_size},
    )


def _eval_observation_gate(
    test_id: str,
    payload: Any,
    policy: Mapping[str, Any],
    *,
    missing_reason: str,
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        return _test_result(test_id, STATUS_BLOCKED_MISSING_CAPABILITY, missing_reason)
    train_sharpe = _require_finite(f"{test_id}.train_sharpe", payload.get("train_sharpe"))
    test_sharpe = _require_finite(f"{test_id}.test_sharpe", payload.get("test_sharpe"))
    sample_size = payload.get("sample_size")
    if not isinstance(sample_size, int) or sample_size < int(policy["min_split_size"]):
        return _test_result(
            test_id,
            STATUS_FAIL,
            f"{test_id} sample_size is below policy min_split_size",
            failure_class="REJECTED_OVERFIT",
        )
    if train_sharpe > 0 and test_sharpe < train_sharpe * float(policy["oos_sharpe_collapse_ratio"]):
        return _test_result(
            test_id,
            STATUS_FAIL,
            f"{test_id} OOS sharpe collapsed versus train",
            failure_class="REJECTED_OVERFIT",
        )
    return _test_result(
        test_id,
        STATUS_PASS,
        f"{test_id} observations remain within OOS collapse policy",
        details={"train_sharpe": train_sharpe, "test_sharpe": test_sharpe},
    )


def _eval_single_metric_promotion_guard(
    observations: Mapping[str, Any],
    promotion_intent: str,
) -> dict[str, Any]:
    metrics = observations.get("metrics")
    metric_keys = set(metrics.keys()) if isinstance(metrics, Mapping) else set()
    if promotion_intent != PROMOTION_INTENT_FORBIDDEN:
        return _test_result(
            "SINGLE_METRIC_PROMOTION_GUARD",
            STATUS_FAIL,
            "promotion_intent other than FORBIDDEN is rejected; BEST_SHARPE => PROMOTE is forbidden",
            failure_class="REJECTED_POLICY",
        )
    if metric_keys == {"sharpe"}:
        return _test_result(
            "SINGLE_METRIC_PROMOTION_GUARD",
            STATUS_FAIL,
            "single-metric Sharpe payload cannot be treated as promotion evidence",
            failure_class="REJECTED_POLICY",
        )
    return _test_result(
        "SINGLE_METRIC_PROMOTION_GUARD",
        STATUS_PASS,
        "single-metric promotion is forbidden and was not attempted",
        details={"promotion_authority": PROMOTION_AUTHORITY},
    )


def _three_way_metrics(
    split_metrics: Any,
    returns: list[float] | None,
    policy: Mapping[str, Any],
) -> dict[str, dict[str, float]] | None:
    if isinstance(split_metrics, Mapping):
        out: dict[str, dict[str, float]] = {}
        for name in ("train", "validation", "holdout"):
            item = split_metrics.get(name)
            if not isinstance(item, Mapping):
                return None
            sample_size = item.get("sample_size")
            if not isinstance(sample_size, int):
                raise RobustnessSuiteValidationError(
                    f"split_metrics.{name}.sample_size must be an int"
                )
            out[name] = {
                "sample_size": float(sample_size),
                "sharpe": _require_finite(f"split_metrics.{name}.sharpe", item.get("sharpe")),
            }
        return out
    if returns is None or len(returns) < int(policy["min_sample_size"]):
        return None
    train_end = max(
        int(policy["min_split_size"]),
        int(len(returns) * float(policy["train_fraction"])),
    )
    val_end = train_end + max(
        int(policy["min_split_size"]), int(len(returns) * float(policy["validation_fraction"]))
    )
    if val_end + int(policy["min_split_size"]) > len(returns):
        return None
    train = returns[:train_end]
    validation = returns[train_end:val_end]
    holdout = returns[val_end:]
    return {
        "train": {"sample_size": float(len(train)), "sharpe": _sharpe(train)},
        "validation": {"sample_size": float(len(validation)), "sharpe": _sharpe(validation)},
        "holdout": {"sample_size": float(len(holdout)), "sharpe": _sharpe(holdout)},
    }


def _oos_gate(
    test_id: str,
    metrics: Mapping[str, Mapping[str, float]],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    min_size = float(policy["min_split_size"])
    for name in ("train", "validation", "holdout"):
        if metrics[name]["sample_size"] < min_size:
            return _test_result(
                test_id,
                STATUS_FAIL,
                f"{name} sample_size is below policy min_split_size",
                failure_class="REJECTED_OVERFIT",
                details=metrics,
            )
    train_sharpe = metrics["train"]["sharpe"]
    holdout_sharpe = metrics["holdout"]["sharpe"]
    collapse = float(policy["oos_sharpe_collapse_ratio"])
    if train_sharpe > 0 and holdout_sharpe < train_sharpe * collapse:
        return _test_result(
            test_id,
            STATUS_FAIL,
            "holdout sharpe collapsed versus train",
            failure_class="REJECTED_OVERFIT",
            details=metrics,
        )
    return _test_result(
        test_id,
        STATUS_PASS,
        "train/validation/holdout remain within OOS collapse policy",
        implementation="ADAPT:src.backtest.parameter_sensitivity_v1",
        details=metrics,
    )


def _evidence_dimensions(
    observations: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    metrics = observations.get("metrics")
    if not isinstance(metrics, Mapping):
        metrics = {}
    dimensions: dict[str, Any] = {}
    required = tuple(policy["required_evidence_dimensions"])
    for name in required:
        if name not in metrics:
            dimensions[name] = {
                "status": DIMENSION_MISSING,
                "reason": "required evidence dimension was not provided",
            }
            continue
        value = _require_finite(f"metrics.{name}", metrics.get(name))
        dimensions[name] = {"status": DIMENSION_COMPUTED, "value": value}
    return dimensions


def _aggregate_status(
    test_results: Sequence[Mapping[str, Any]],
    dimensions: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> str:
    if any(item["status"] == STATUS_FAIL for item in test_results):
        return STATUS_FAIL
    required_tests = tuple(policy["required_tests_for_pass"])
    for item in test_results:
        if item["test_id"] in required_tests and item["status"] != STATUS_PASS:
            return STATUS_BLOCKED
    for name in tuple(policy["required_evidence_dimensions"]):
        dim = dimensions.get(name)
        if not isinstance(dim, Mapping) or dim.get("status") != DIMENSION_COMPUTED:
            return STATUS_BLOCKED
    return STATUS_PASS


def _suite_stats(returns: pd.Series) -> dict[str, float]:
    values = [float(item) for item in returns.tolist()]
    return {
        "max_dd": _max_dd(values),
        "mean": float(sum(values) / len(values)),
        "sharpe": _sharpe(values),
    }


def _sharpe(values: Sequence[float]) -> float:
    if len(values) < 2:
        raise RobustnessSuiteValidationError("sharpe requires at least two returns")
    mean = sum(values) / len(values)
    variance = sum((item - mean) ** 2 for item in values) / (len(values) - 1)
    std = math.sqrt(variance)
    if std == 0.0:
        if mean == 0.0:
            return 0.0
        raise RobustnessSuiteValidationError("zero volatility with non-zero mean is fail-closed")
    return mean / std


def _max_dd(values: Sequence[float]) -> float:
    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for item in values:
        equity *= 1.0 + item
        peak = max(peak, equity)
        if peak == 0.0:
            raise RobustnessSuiteValidationError("equity peak of zero is fail-closed")
        max_dd = max(max_dd, abs((equity - peak) / peak))
    return max_dd


def _optional_returns(value: Any) -> list[float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not value:
        raise RobustnessSuiteValidationError(
            "observations.returns must be a non-empty list when provided"
        )
    return [_require_finite(f"returns[{index}]", item) for index, item in enumerate(value)]


def _test_result(
    test_id: str,
    status: str,
    reason: str,
    *,
    failure_class: str | None = None,
    implementation: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "reason": reason,
        "status": status,
        "test_id": test_id,
    }
    if failure_class is not None:
        payload["failure_class"] = failure_class
        payload["failed_gate"] = FAILURE_CLASS_TO_FAILED_GATE[failure_class]
    if implementation is not None:
        payload["implementation"] = implementation
    if details is not None:
        payload["details"] = _canonicalize_tree(f"test_results.{test_id}.details", details)
    return payload


def _validate_policy(policy: Mapping[str, Any]) -> None:
    required_keys = {
        "annualization",
        "crash_max_dd_limit",
        "crash_severity",
        "crash_window",
        "cost_stress_sharpe_collapse_ratio",
        "max_neighbor_degradation",
        "max_parameter_sign_flips",
        "mc_block_size",
        "mc_min_p5_sharpe",
        "mc_num_runs",
        "min_sample_size",
        "min_split_size",
        "multiple_testing_correction",
        "oos_sharpe_collapse_ratio",
        "policy_id",
        "regime_min_share",
        "required_evidence_dimensions",
        "required_tests_for_pass",
        "rolling_step",
        "rolling_test_size",
        "train_fraction",
        "validation_fraction",
    }
    missing = sorted(required_keys - set(policy.keys()))
    if missing:
        raise RobustnessSuiteValidationError(f"robustness_policy missing keys: {missing}")
    if policy.get("annualization") != "MEAN_OVER_SAMPLE_STD_NO_ANNUALIZATION":
        raise RobustnessSuiteValidationError("unsupported robustness_policy.annualization")
    if tuple(policy["required_evidence_dimensions"]) != REQUIRED_EVIDENCE_DIMENSIONS:
        raise RobustnessSuiteValidationError(
            "required_evidence_dimensions cannot be silently reduced"
        )
    extra_required = set(policy["required_tests_for_pass"]) - set(REQUIRED_ROBUSTNESS_TESTS)
    if extra_required:
        raise RobustnessSuiteValidationError(
            f"required_tests_for_pass contains unknown tests: {sorted(extra_required)}"
        )


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RobustnessSuiteValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise RobustnessSuiteValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _bound_ref(field_name: str, value: Any, identity: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RobustnessSuiteValidationError(f"{field_name} must be a mapping")
    if value.get("kind") != REF_KIND_IDENTITY_BOUND:
        raise RobustnessSuiteValidationError(f"{field_name}.kind must be IDENTITY_DIGEST_BOUND")
    digest_field = dict(_IDENTITY_REF_BINDINGS)[field_name]
    expected = _require_sha256(digest_field, identity.get(digest_field))
    provided = _require_sha256(f"{field_name}.digest", value.get("digest"))
    if provided != expected:
        raise RobustnessSuiteValidationError(
            f"{field_name}.digest must match experiment_identity.{digest_field}"
        )
    extra_keys = set(str(key) for key in value.keys()) - {"kind", "digest"}
    if extra_keys:
        raise RobustnessSuiteValidationError(
            f"{field_name} has unsupported keys: {sorted(extra_keys)}"
        )
    return {"digest": expected, "kind": REF_KIND_IDENTITY_BOUND}


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise RobustnessSuiteValidationError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise RobustnessSuiteValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise RobustnessSuiteValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise RobustnessSuiteValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _require_promotion_intent(value: Any) -> str:
    if value is None:
        return PROMOTION_INTENT_FORBIDDEN
    if not isinstance(value, str) or not value.strip():
        raise RobustnessSuiteValidationError("promotion_intent is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise RobustnessSuiteValidationError(
            "promotion_intent cannot use implicit unavailable tokens"
        )
    return value


def _require_finite(field_name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise RobustnessSuiteValidationError(f"{field_name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise RobustnessSuiteValidationError(
            f"non-finite numeric values are forbidden in {field_name}"
        )
    return number


def _canonicalize_tree(field_name: str, value: Any) -> Any:
    try:
        return canonicalize_value(value, path=f"$.{field_name}")
    except CanonicalExperimentIdentityError as exc:
        message = str(exc)
        if "non-finite float" in message:
            raise RobustnessSuiteValidationError(
                f"non-finite numeric values are forbidden in {field_name}"
            ) from exc
        raise RobustnessSuiteValidationError(
            f"{field_name} is not canonically serializable: {exc}"
        ) from exc


def _token_digest(value: str) -> str:
    return compute_content_sha256({"token": value})


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


__all__ = [
    "ALL_CATALOG_TESTS",
    "CanonicalRobustnessSuiteRequestV1",
    "DEFERRED_STATISTICAL_CONTROLS",
    "METRIC_DEFINITION_VERSION",
    "PROMOTION_AUTHORITY",
    "REQUIRED_EVIDENCE_DIMENSIONS",
    "REQUIRED_ROBUSTNESS_TESTS",
    "ROBUSTNESS_DOMAIN",
    "ROBUSTNESS_SUITE_CAN_PROMOTE",
    "ROBUSTNESS_SUITE_HAS_RUNTIME_AUTHORITY",
    "RUNTIME_AUTHORITY_IMPACT",
    "SCHEMA_VERSION",
    "SINGLE_METRIC_PROMOTION",
    "TEST_FAILURE_CLASSES",
    "RobustnessSuiteValidationError",
    "build_canonical_robustness_evidence_v1",
    "build_failure_records_for_failed_gates_v1",
    "canonical_record_payload",
    "canonical_robustness_policy_v1",
    "derive_robustness_policy_digest_v1",
    "derive_robustness_suite_identity_v1",
    "validate_canonical_robustness_evidence_v1",
]
