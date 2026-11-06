"""Optimization universe M4 — offline experiment plane (proposal-only seam).

Closes a typed offline research chain from validated optimization learning input
through experiment identity, search, candidate proposal, challenger evaluation, and
robustness/failure evidence. Does not authorize productive surfaces, search join,
promotion, or runtime mutation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_advanced_search_v1 import (
    SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
    SEARCH_METHOD_VERSION,
    STATUS_PROPOSED,
    CanonicalAdvancedSearchRequestV1,
    SearchSpaceV1,
    build_canonical_advanced_search_v1,
    canonical_advanced_search_constraint_v1,
    canonical_advanced_search_objective_v1,
)
from src.experiments.canonical_champion_challenger_v1 import (
    PROMOTION_AUTHORITY as CHAMPION_PROMOTION_AUTHORITY,
    evaluate_canonical_champion_challenger_v1,
    CanonicalChampionChallengerRequestV1,
)
from src.experiments.canonical_comparison_ssot_v1 import ComparisonCandidateV1
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_NOT_AUTHORIZED,
    SYNTHETIC_OFFLINE_SURFACE_ID,
    OptimizableEnvelopeResolveRequestV1,
    build_authorized_surface_registry_v1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    SCHEMA_VERSION as LEARNING_INPUT_SCHEMA_VERSION,
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    METRIC_DEFINITION_VERSION,
    SCHEMA_VERSION as ROBUSTNESS_SUITE_VERSION,
    CanonicalRobustnessSuiteRequestV1,
    build_canonical_robustness_evidence_v1,
    build_failure_records_for_failed_gates_v1,
    canonical_robustness_policy_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    zero_authorized_productive_targets_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_optimization_universe_experiment_plane_v1"
EXPERIMENT_PLANE_DOMAIN: Final[str] = (
    "peak_trade.canonical_optimization_universe_experiment_plane.v1"
)
BOUND_ORIGIN_MAIN_SHA: Final[str] = "c889577bef56300f74039d921472f0638cbb8810"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/OPTIMIZATION_UNIVERSE_EXPERIMENT_PLANE_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = (
    "config/governance/optimization_universe_experiment_plane_v1_decision_v1.json"
)

OFFLINE_CONTEXT_KIND: Final[str] = "OFFLINE_SYNTHETIC_RESEARCH_CONTEXT"
CANDIDATE_DISPOSITION: Final[str] = "PROPOSAL_ONLY"
PROPOSAL_DISPOSITION: Final[str] = "PROPOSAL_ONLY"

PLANE_STATUS_COMPLETE: Final[str] = "PLANE_OFFLINE_CHAIN_COMPLETE"
PLANE_STATUS_REJECTED_INPUT: Final[str] = "PLANE_REJECTED_INVALID_INPUT"
PLANE_STATUS_REJECTED_STALE_INPUT: Final[str] = "PLANE_REJECTED_STALE_INPUT_CONTRACT"
PLANE_STATUS_REJECTED_NO_CANDIDATE: Final[str] = "PLANE_REJECTED_NO_PROPOSED_CANDIDATE"

OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
ZERO_AUTHORIZED_PRODUCTIVE_TARGETS: Final[bool] = zero_authorized_productive_targets_v1()
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROPOSAL_NOT_AUTHORITY: Final[bool] = True
NO_SELF_DEPLOY: Final[bool] = True
NO_TRADING_RESELECTION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"

LINEAGE_KIND_ROOT: Final[str] = "ROOT"
_DEFAULT_HYPOTHESIS_KIND: Final[str] = "PARAMETER_REGION"
_DEFAULT_STRATEGY_FAMILY: Final[str] = "synthetic_offline_research"
_DEFAULT_REGIME: Final[str] = "mixed"
_TIME_HORIZON: Final[Mapping[str, str]] = MappingProxyType(
    {"start": "2020-01-01T00:00:00Z", "end": "2024-12-31T00:00:00Z"}
)
_MARKET_UNIVERSE: Final[tuple[str, ...]] = ("SYNTHETIC-OFFLINE-RESEARCH-ONLY",)

_LOGGER = logging.getLogger(__name__)


class OptimizationUniverseExperimentPlaneError(ValueError):
    """Fail-closed experiment plane request error."""


@dataclass(frozen=True)
class OptimizationUniverseExperimentPlaneRequestV1:
    learning_evidence: Mapping[str, Any]
    identity_template: CanonicalExperimentIdentityRequestV1
    search_space: SearchSpaceV1
    champion: ComparisonCandidateV1
    champion_score: float
    challenger_score: float
    created_at: str
    search_seed: int = 17
    search_budget: int = 1
    search_space_cardinality_limit: int = 64
    parent_hypothesis_id: str = "hyp.optimization_plane.offline.v1"
    hypothesis_kind: str = _DEFAULT_HYPOTHESIS_KIND
    strategy_family: str = _DEFAULT_STRATEGY_FAMILY
    regime: str = _DEFAULT_REGIME
    robustness_policy_digest: str | None = None
    robustness_observations: Mapping[str, Any] | None = None
    learning_input_schema_version: str | None = LEARNING_INPUT_SCHEMA_VERSION


def build_offline_research_context_v1(
    *,
    learning_evidence_digest: str,
    learning_input_status: str,
    learning_input_reason: str,
) -> MappingProxyType[str, Any]:
    envelope_resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SYNTHETIC_OFFLINE_SURFACE_ID)
    )
    body = {
        "context_kind": OFFLINE_CONTEXT_KIND,
        "bound_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "learning_evidence_digest": learning_evidence_digest,
        "learning_input_status": learning_input_status,
        "learning_input_reason": learning_input_reason,
        "synthetic_surface_id": SYNTHETIC_OFFLINE_SURFACE_ID,
        "envelope_resolution": dict(envelope_resolution),
        "envelope_not_productive_authorization": (
            envelope_resolution["resolution"] == RESOLUTION_NOT_AUTHORIZED
        ),
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
    }
    body["context_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def run_optimization_universe_experiment_plane_v1(
    request: OptimizationUniverseExperimentPlaneRequestV1,
) -> MappingProxyType[str, Any]:
    if request.learning_input_schema_version != LEARNING_INPUT_SCHEMA_VERSION:
        return MappingProxyType(
            _plane_payload(
                status=PLANE_STATUS_REJECTED_STALE_INPUT,
                reason="LEARNING_INPUT_SCHEMA_VERSION_MISMATCH",
                offline_context=None,
                chain=None,
            )
        )

    learning_input = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(
            learning_evidence=request.learning_evidence
        )
    )
    if learning_input["status"] != STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT:
        return MappingProxyType(
            _plane_payload(
                status=PLANE_STATUS_REJECTED_INPUT,
                reason=str(learning_input["reason"]),
                offline_context=None,
                chain=None,
                learning_input_validation=dict(learning_input),
            )
        )

    evidence_digest = str(learning_input["learning_evidence_digest"])
    offline_context = build_offline_research_context_v1(
        learning_evidence_digest=evidence_digest,
        learning_input_status=str(learning_input["status"]),
        learning_input_reason=str(learning_input["reason"]),
    )

    policy_digest = request.robustness_policy_digest or compute_content_sha256(
        canonical_robustness_policy_v1()
    )
    search_record = build_canonical_advanced_search_v1(
        CanonicalAdvancedSearchRequestV1(
            identity_template=request.identity_template,
            search_space=request.search_space,
            search_method=SEARCH_METHOD_BOUNDED_DETERMINISTIC_CONSTRAINED_REGION_SEARCH,
            search_method_version=SEARCH_METHOD_VERSION,
            seed=request.search_seed,
            budget=request.search_budget,
            search_space_cardinality_limit=request.search_space_cardinality_limit,
            objective=canonical_advanced_search_objective_v1(),
            constraint=canonical_advanced_search_constraint_v1(),
            created_at=request.created_at,
            parent_hypothesis_id=request.parent_hypothesis_id,
            lineage_kind=LINEAGE_KIND_ROOT,
            hypothesis_kind=request.hypothesis_kind,
            strategy_family=request.strategy_family,
            regime=request.regime,
            robustness_policy_digest=policy_digest,
        )
    )

    proposed = [
        item
        for item in search_record["candidates"]
        if item.get("status") == STATUS_PROPOSED and item.get("experiment_identity")
    ]
    if not proposed:
        return MappingProxyType(
            _plane_payload(
                status=PLANE_STATUS_REJECTED_NO_CANDIDATE,
                reason="NO_PROPOSED_SEARCH_CANDIDATE",
                offline_context=offline_context,
                chain={
                    "learning_input_validation": dict(learning_input),
                    "search_identity": search_record.get("search_identity"),
                },
                learning_input_validation=dict(learning_input),
            )
        )

    selected = proposed[0]
    challenger_identity = selected["experiment_identity"]
    challenger_experiment_id = derive_experiment_id_v1(str(challenger_identity["identity_digest"]))
    template_identity = build_canonical_experiment_identity_v1(request.identity_template)

    challenger_candidate = ComparisonCandidateV1(
        experiment_identity=challenger_identity,
        robustness_suite_version=ROBUSTNESS_SUITE_VERSION,
        metric_definitions=METRIC_DEFINITION_VERSION,
        time_horizon=dict(_TIME_HORIZON),
        market_universe=list(_MARKET_UNIVERSE),
        experiment_id=challenger_experiment_id,
        evidence_refs=(
            {
                "kind": "SEARCH_CANDIDATE",
                "ref": str(selected["candidate_ref"]),
                "digest": str(challenger_identity["identity_digest"]),
            },
        ),
    )
    challenger_evaluation = evaluate_canonical_champion_challenger_v1(
        CanonicalChampionChallengerRequestV1(
            champion=request.champion,
            challengers=(challenger_candidate,),
            scores={
                str(
                    request.champion.experiment_id
                    or derive_experiment_id_v1(
                        str(request.champion.experiment_identity["identity_digest"])
                    )
                ): float(request.champion_score),
                challenger_experiment_id: float(request.challenger_score),
            },
            created_at=request.created_at,
        )
    )

    observations = _observations_or_default(request.robustness_observations)
    robustness_evidence = build_canonical_robustness_evidence_v1(
        CanonicalRobustnessSuiteRequestV1(
            experiment_identity=challenger_identity,
            candidate_ref=str(selected["candidate_ref"]),
            dataset_ref=_bound_ref(str(challenger_identity["dataset_digest"])),
            split_policy_ref=_bound_ref(str(challenger_identity["split_policy_digest"])),
            cost_model_ref=_bound_ref(str(challenger_identity["cost_model_digest"])),
            risk_policy_ref=_bound_ref(str(challenger_identity["risk_policy_digest"])),
            seed=int(challenger_identity["seed"]),
            created_at=request.created_at,
            robustness_policy=canonical_robustness_policy_v1(),
            observations=observations,
            hypothesis_id=str(selected["hypothesis_id"]),
            regime=request.regime,
            parameter_region=dict(selected["parameter_region"]),
            metric_definition_version=METRIC_DEFINITION_VERSION,
            experiment_id=challenger_experiment_id,
        )
    )
    failure_records = list(build_failure_records_for_failed_gates_v1(robustness_evidence))
    if selected.get("failure_signals"):
        failure_records.append(
            {
                "kind": "SEARCH_FAILURE_SIGNAL",
                "payload": dict(selected["failure_signals"]),
                "evidence_only": True,
            }
        )

    proposal = MappingProxyType(
        {
            "disposition": PROPOSAL_DISPOSITION,
            "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
            "promotion_authority": PROMOTION_AUTHORITY,
            "candidate_ref": str(selected["candidate_ref"]),
            "experiment_id": challenger_experiment_id,
            "identity_digest": str(challenger_identity["identity_digest"]),
            "template_identity_digest": str(template_identity["identity_digest"]),
            "search_identity": str(search_record["search_identity"]),
            "challenger_evaluation_disposition": challenger_evaluation.get("overall_disposition"),
            "robustness_suite_identity": robustness_evidence.get("robustness_suite_identity"),
            "external_effect_authorized": False,
            "productive_config_mutation": False,
        }
    )

    chain = {
        "learning_input_validation": dict(learning_input),
        "offline_research_context": dict(offline_context),
        "template_identity_digest": str(template_identity["identity_digest"]),
        "search_identity": search_record.get("search_identity"),
        "selected_candidate": {
            "status": selected.get("status"),
            "disposition": CANDIDATE_DISPOSITION,
            "candidate_ref": selected.get("candidate_ref"),
            "experiment_id": challenger_experiment_id,
            "parameter_region": dict(selected.get("parameter_region") or {}),
        },
        "challenger_evaluation": dict(challenger_evaluation),
        "robustness_evidence_digest": robustness_evidence.get("integrity"),
        "failure_evidence_count": len(failure_records),
        "failure_evidence": failure_records,
        "proposal": dict(proposal),
    }

    return MappingProxyType(
        _plane_payload(
            status=PLANE_STATUS_COMPLETE,
            reason="OFFLINE_RESEARCH_PROPOSAL_ONLY",
            offline_context=offline_context,
            chain=chain,
            learning_input_validation=dict(learning_input),
            plane_identity=_derive_plane_identity(
                evidence_digest=evidence_digest,
                search_identity=str(search_record["search_identity"]),
                candidate_ref=str(selected["candidate_ref"]),
            ),
        )
    )


def _bound_ref(digest: str) -> dict[str, str]:
    return {"kind": "IDENTITY_DIGEST_BOUND", "digest": digest}


def _observations_or_default(raw: Mapping[str, Any] | None) -> dict[str, Any]:
    if raw is not None:
        return dict(raw)
    returns = [0.01, -0.004, 0.006, -0.002, 0.005, -0.003, 0.007, -0.001] * 4
    metrics = {
        "exposure": 0.4,
        "fee_drag": 0.01,
        "funding_sensitivity": 0.02,
        "max_dd": 0.08,
        "oos_stability": 0.85,
        "parameter_stability": 0.9,
        "profit_factor": 1.4,
        "regime_concentration": 0.35,
        "sample_size": 32.0,
        "sharpe": 1.2,
        "slippage_sensitivity": 0.04,
        "sortino": 1.5,
        "tail_risk": 0.07,
        "turnover": 0.2,
    }
    return {
        "metrics": metrics,
        "returns": returns,
        "walk_forward_windows": [
            {"sample_size": 16, "test_sharpe": 1.0, "train_sharpe": 1.2},
            {"sample_size": 16, "test_sharpe": 0.95, "train_sharpe": 1.1},
        ],
        "split_metrics": {
            "holdout": {"sample_size": 16, "sharpe": 1.0},
            "train": {"sample_size": 32, "sharpe": 1.2},
            "validation": {"sample_size": 16, "sharpe": 1.1},
        },
        "cost_stress": {
            "baseline": {"sharpe": 1.2},
            "fee": {"sharpe": 1.0},
            "funding": {"sharpe": 1.05},
            "slippage": {"sharpe": 1.02},
        },
        "parameter_sensitivity": {
            "center": {"fast": 10.0, "sharpe": 1.2},
            "points": [
                {"fast": 10.0, "sharpe": 1.2},
                {"fast": 12.0, "sharpe": 1.15},
            ],
        },
        "regime_stress": {
            "regimes": {
                "high_vol": {"sample_size": 16, "sharpe": 0.9},
                "low_vol": {"sample_size": 16, "sharpe": 1.1},
            }
        },
        "purged_split": {
            "purge_bars": 2,
            "sample_size": 16,
            "test_sharpe": 1.0,
            "train_sharpe": 1.2,
        },
        "embargo": {"embargo_bars": 2, "sample_size": 16, "test_sharpe": 1.0, "train_sharpe": 1.2},
        "multiple_testing": {
            "alpha": 0.05,
            "correction": "BONFERRONI",
            "discoveries": 1,
            "family_size": 1,
            "p_value": 0.01,
        },
        "bad_tick_stress": {"bad_tick_count": 0, "max_abs_return": 0.04},
        "latency_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.1}},
        "liquidity_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.08}},
        "missing_data_stress": {"missing_fraction": 0.0, "sharpe": 1.2},
        "risk_stress": {"baseline": {"max_dd": 0.08}, "stressed": {"max_dd": 0.12}},
        "spread_stress": {"baseline": {"sharpe": 1.2}, "stressed": {"sharpe": 1.09}},
    }


def _derive_plane_identity(
    *,
    evidence_digest: str,
    search_identity: str,
    candidate_ref: str,
) -> str:
    registry = build_authorized_surface_registry_v1()
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": EXPERIMENT_PLANE_DOMAIN,
        "learning_evidence_digest": evidence_digest,
        "search_identity": search_identity,
        "candidate_ref": candidate_ref,
        "authorized_surface_count": registry["authorized_surface_count"],
    }
    return compute_content_sha256(body)


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _plane_payload(
    *,
    status: str,
    reason: str,
    offline_context: Mapping[str, Any] | None,
    chain: Mapping[str, Any] | None,
    learning_input_validation: Mapping[str, Any] | None = None,
    plane_identity: str | None = None,
) -> dict[str, Any]:
    registry = build_authorized_surface_registry_v1()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": EXPERIMENT_PLANE_DOMAIN,
        "status": status,
        "reason": reason,
        "plane_identity": plane_identity,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
        "zero_authorized_productive_targets": ZERO_AUTHORIZED_PRODUCTIVE_TARGETS,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "proposal_not_authority": PROPOSAL_NOT_AUTHORITY,
        "no_trading_reselection": NO_TRADING_RESELECTION,
        "champion_promotion_authority": CHAMPION_PROMOTION_AUTHORITY,
        "offline_research_context": dict(offline_context) if offline_context else None,
        "learning_input_validation": learning_input_validation,
        "chain": dict(chain) if chain else None,
        "envelope_registry_authorized_surface_count": registry["authorized_surface_count"],
        "normative_spec": NORMATIVE_SPEC,
        "decision_config": DECISION_CONFIG,
    }
    digest_body = _json_safe({key: value for key, value in body.items() if key != "result_digest"})
    body["result_digest"] = compute_content_sha256(digest_body)
    return body
