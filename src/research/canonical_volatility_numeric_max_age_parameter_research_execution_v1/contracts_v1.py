"""Pre-evaluation research contracts bound and digested before result scoring."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    AGE_FORMULA,
    AGE_REFERENCE_CLOCK,
    AGE_UNIT,
    ALTERNATIVE_HYPOTHESIS_H1,
    AUTHORITY_SCOPE,
    BASELINE_CANDIDATE_ID,
    BOOTSTRAP_BLOCK_SECONDS,
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    CANDIDATE_DOMAIN_SCHEMA_VERSION,
    COUNTERFACTUAL_ONLY,
    EMBARGO_SECONDS,
    ENFORCEMENT_DURING_RESEARCH,
    EXPECTED_PREREGISTRATION_DIGEST,
    HOLDING_HORIZON_SECONDS,
    HOLDOUT_FRACTION,
    HYPOTHESIS_SCHEMA_VERSION,
    LABEL_HORIZON_SECONDS,
    LOOKBACK_HORIZON_SECONDS,
    MANIFEST_SCHEMA_VERSION,
    NEIGHBORHOOD_PERTURBATION_FACTORS,
    NON_AUTHORITY_SCOPE,
    NULL_HYPOTHESIS_H0,
    NUMERIC_THRESHOLD_SELECTED,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
    PARAMETER_PROMOTED,
    RESEARCH_QUESTION,
    ROBUSTNESS_SCHEMA_VERSION,
    SPLIT_SCHEMA_VERSION,
    SURVIVAL_HORIZON_SECONDS,
    THRESHOLD_STATUS,
    TRAIN_FRACTION_WITHIN_NON_HOLDOUT,
    WALK_FORWARD_FOLDS,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
    digest_excluding_keys,
)


class MaxAgeResearchExecutionError(ValueError):
    """Fail-closed research execution contract / evidence error."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CandidateDomainContractV1:
    schema_version: str
    repository_sha: str
    preregistration_digest: str
    execution_id: str
    created_at_utc: str
    candidate_max_age_seconds: tuple[int, ...]
    baseline_candidate_id: str
    age_unit: str
    candidate_authority: str
    non_authority: str
    immutable_after_bind: bool
    domain_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_unit": self.age_unit,
            "authority_scope": AUTHORITY_SCOPE,
            "baseline_candidate_id": self.baseline_candidate_id,
            "candidate_authority": self.candidate_authority,
            "candidate_max_age_seconds": list(self.candidate_max_age_seconds),
            "created_at_utc": self.created_at_utc,
            "domain_digest": self.domain_digest,
            "execution_id": self.execution_id,
            "immutable_after_bind": self.immutable_after_bind,
            "non_authority": self.non_authority,
            "non_authority_scope": NON_AUTHORITY_SCOPE,
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class HypothesisContractV1:
    schema_version: str
    repository_sha: str
    preregistration_digest: str
    execution_id: str
    created_at_utc: str
    research_question: str
    null_hypothesis_h0: str
    alternative_hypothesis_h1: str
    baseline: str
    age_reference_clock: str
    age_unit: str
    age_formula: str
    enforcement_during_research: bool
    counterfactual_only: bool
    alpha_decision_mutation_allowed: bool
    threshold_status: str
    numeric_threshold_selected: bool
    parameter_promoted: bool
    hypothesis_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "age_formula": self.age_formula,
            "age_reference_clock": self.age_reference_clock,
            "age_unit": self.age_unit,
            "alpha_decision_mutation_allowed": self.alpha_decision_mutation_allowed,
            "alternative_hypothesis_h1": self.alternative_hypothesis_h1,
            "authority_scope": AUTHORITY_SCOPE,
            "baseline": self.baseline,
            "counterfactual_only": self.counterfactual_only,
            "created_at_utc": self.created_at_utc,
            "enforcement_during_research": self.enforcement_during_research,
            "execution_id": self.execution_id,
            "hypothesis_digest": self.hypothesis_digest,
            "non_authority_scope": NON_AUTHORITY_SCOPE,
            "null_hypothesis_h0": self.null_hypothesis_h0,
            "numeric_threshold_selected": self.numeric_threshold_selected,
            "parameter_promoted": self.parameter_promoted,
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "research_question": self.research_question,
            "schema_version": self.schema_version,
            "threshold_status": self.threshold_status,
        }


@dataclass(frozen=True)
class SplitAndEmbargoContractV1:
    schema_version: str
    repository_sha: str
    preregistration_digest: str
    execution_id: str
    created_at_utc: str
    split_policy: str
    walk_forward_folds: int
    holdout_fraction: float
    train_fraction_within_non_holdout: float
    lookback_horizon_seconds: int
    holding_horizon_seconds: int
    survival_horizon_seconds: int
    label_horizon_seconds: int
    embargo_seconds: int
    embargo_derivation: str
    holdout_untouched_until_final_evaluation: bool
    no_random_iid_shuffle: bool
    no_future_event_time_labels: bool
    no_holdout_candidate_selection: bool
    no_retrospective_regime_relabel: bool
    split_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_scope": AUTHORITY_SCOPE,
            "created_at_utc": self.created_at_utc,
            "embargo_derivation": self.embargo_derivation,
            "embargo_seconds": self.embargo_seconds,
            "execution_id": self.execution_id,
            "holding_horizon_seconds": self.holding_horizon_seconds,
            "holdout_fraction": self.holdout_fraction,
            "holdout_untouched_until_final_evaluation": (
                self.holdout_untouched_until_final_evaluation
            ),
            "label_horizon_seconds": self.label_horizon_seconds,
            "lookback_horizon_seconds": self.lookback_horizon_seconds,
            "no_future_event_time_labels": self.no_future_event_time_labels,
            "no_holdout_candidate_selection": self.no_holdout_candidate_selection,
            "no_random_iid_shuffle": self.no_random_iid_shuffle,
            "no_retrospective_regime_relabel": self.no_retrospective_regime_relabel,
            "non_authority_scope": NON_AUTHORITY_SCOPE,
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "schema_version": self.schema_version,
            "split_digest": self.split_digest,
            "split_policy": self.split_policy,
            "survival_horizon_seconds": self.survival_horizon_seconds,
            "train_fraction_within_non_holdout": self.train_fraction_within_non_holdout,
            "walk_forward_folds": self.walk_forward_folds,
        }


@dataclass(frozen=True)
class RobustnessExecutionContractV1:
    schema_version: str
    repository_sha: str
    preregistration_digest: str
    execution_id: str
    created_at_utc: str
    methods: tuple[str, ...]
    bootstrap_repetitions: int
    bootstrap_block_seconds: int
    bootstrap_seed: int
    neighborhood_perturbation_factors: tuple[float, ...]
    resampling_policy: str
    monte_carlo_policy: str
    limitations: tuple[str, ...]
    robustness_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_scope": AUTHORITY_SCOPE,
            "bootstrap_block_seconds": self.bootstrap_block_seconds,
            "bootstrap_repetitions": self.bootstrap_repetitions,
            "bootstrap_seed": self.bootstrap_seed,
            "created_at_utc": self.created_at_utc,
            "execution_id": self.execution_id,
            "limitations": list(self.limitations),
            "methods": list(self.methods),
            "monte_carlo_policy": self.monte_carlo_policy,
            "neighborhood_perturbation_factors": list(self.neighborhood_perturbation_factors),
            "non_authority_scope": NON_AUTHORITY_SCOPE,
            "preregistration_digest": self.preregistration_digest,
            "repository_sha": self.repository_sha,
            "resampling_policy": self.resampling_policy,
            "robustness_digest": self.robustness_digest,
            "schema_version": self.schema_version,
        }


def verify_preregistration_digest_v1(actual_digest: str) -> None:
    if actual_digest != EXPECTED_PREREGISTRATION_DIGEST:
        raise MaxAgeResearchExecutionError(
            "preregistration_digest_mismatch:"
            f"expected={EXPECTED_PREREGISTRATION_DIGEST}:actual={actual_digest}"
        )


def bind_candidate_domain_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    created_at_utc: Optional[str] = None,
    candidate_max_age_seconds: Sequence[int] | None = None,
) -> CandidateDomainContractV1:
    verify_preregistration_digest_v1(preregistration_digest)
    candidates = tuple(
        int(x)
        for x in (
            candidate_max_age_seconds
            if candidate_max_age_seconds is not None
            else OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS
        )
    )
    if not candidates:
        raise MaxAgeResearchExecutionError("candidate_domain_empty")
    if candidates != tuple(sorted(candidates)):
        raise MaxAgeResearchExecutionError("candidate_domain_must_be_ordered_ascending")
    if len(set(candidates)) != len(candidates):
        raise MaxAgeResearchExecutionError("candidate_domain_duplicate_values")
    if any(c < 0 for c in candidates):
        raise MaxAgeResearchExecutionError("candidate_domain_negative_forbidden")

    created = created_at_utc or _utc_now_iso()
    provisional = {
        "age_unit": AGE_UNIT,
        "authority_scope": AUTHORITY_SCOPE,
        "baseline_candidate_id": BASELINE_CANDIDATE_ID,
        "candidate_authority": (
            "EXPLICIT_OPERATOR_OR_CALLER_SUPPLIED_RESEARCH_ARGUMENT_ONLY;"
            "NOT_CONFIG;"
            "NOT_POLICY;"
            "NOT_PRODUCTIVE_DEFAULT"
        ),
        "candidate_max_age_seconds": list(candidates),
        "created_at_utc": created,
        "execution_id": execution_id,
        "immutable_after_bind": True,
        "non_authority": (
            "CANDIDATE_VALUES_ARE_RESEARCH_ARGUMENTS_ONLY;NO_CONFIG_AUTHORITY;NO_POLICY_AUTHORITY"
        ),
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "schema_version": CANDIDATE_DOMAIN_SCHEMA_VERSION,
    }
    digest = digest_excluding_keys(
        provisional, exclude={"domain_digest", "execution_id", "created_at_utc"}
    )
    return CandidateDomainContractV1(
        schema_version=CANDIDATE_DOMAIN_SCHEMA_VERSION,
        repository_sha=repository_sha,
        preregistration_digest=preregistration_digest,
        execution_id=execution_id,
        created_at_utc=created,
        candidate_max_age_seconds=candidates,
        baseline_candidate_id=BASELINE_CANDIDATE_ID,
        age_unit=AGE_UNIT,
        candidate_authority=str(provisional["candidate_authority"]),
        non_authority=str(provisional["non_authority"]),
        immutable_after_bind=True,
        domain_digest=digest,
    )


def bind_hypothesis_contract_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    created_at_utc: Optional[str] = None,
) -> HypothesisContractV1:
    verify_preregistration_digest_v1(preregistration_digest)
    created = created_at_utc or _utc_now_iso()
    provisional = {
        "age_formula": AGE_FORMULA,
        "age_reference_clock": AGE_REFERENCE_CLOCK,
        "age_unit": AGE_UNIT,
        "alpha_decision_mutation_allowed": False,
        "alternative_hypothesis_h1": ALTERNATIVE_HYPOTHESIS_H1,
        "authority_scope": AUTHORITY_SCOPE,
        "baseline": BASELINE_CANDIDATE_ID,
        "counterfactual_only": COUNTERFACTUAL_ONLY,
        "created_at_utc": created,
        "enforcement_during_research": ENFORCEMENT_DURING_RESEARCH,
        "execution_id": execution_id,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "null_hypothesis_h0": NULL_HYPOTHESIS_H0,
        "numeric_threshold_selected": NUMERIC_THRESHOLD_SELECTED,
        "parameter_promoted": PARAMETER_PROMOTED,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "research_question": RESEARCH_QUESTION,
        "schema_version": HYPOTHESIS_SCHEMA_VERSION,
        "threshold_status": THRESHOLD_STATUS,
    }
    digest = digest_excluding_keys(
        provisional, exclude={"hypothesis_digest", "execution_id", "created_at_utc"}
    )
    return HypothesisContractV1(
        schema_version=HYPOTHESIS_SCHEMA_VERSION,
        repository_sha=repository_sha,
        preregistration_digest=preregistration_digest,
        execution_id=execution_id,
        created_at_utc=created,
        research_question=RESEARCH_QUESTION,
        null_hypothesis_h0=NULL_HYPOTHESIS_H0,
        alternative_hypothesis_h1=ALTERNATIVE_HYPOTHESIS_H1,
        baseline=BASELINE_CANDIDATE_ID,
        age_reference_clock=AGE_REFERENCE_CLOCK,
        age_unit=AGE_UNIT,
        age_formula=AGE_FORMULA,
        enforcement_during_research=ENFORCEMENT_DURING_RESEARCH,
        counterfactual_only=COUNTERFACTUAL_ONLY,
        alpha_decision_mutation_allowed=False,
        threshold_status=THRESHOLD_STATUS,
        numeric_threshold_selected=NUMERIC_THRESHOLD_SELECTED,
        parameter_promoted=PARAMETER_PROMOTED,
        hypothesis_digest=digest,
    )


def bind_split_and_embargo_contract_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    created_at_utc: Optional[str] = None,
) -> SplitAndEmbargoContractV1:
    verify_preregistration_digest_v1(preregistration_digest)
    created = created_at_utc or _utc_now_iso()
    derivation = (
        "embargo_seconds=max("
        "lookback_horizon_seconds,"
        "holding_horizon_seconds,"
        "survival_horizon_seconds,"
        "label_horizon_seconds"
        f")={EMBARGO_SECONDS};"
        "horizons_bound_before_evaluation=true;"
        "source=canonical_volatility_lookback_bars*bar_interval_seconds"
    )
    provisional = {
        "authority_scope": AUTHORITY_SCOPE,
        "created_at_utc": created,
        "embargo_derivation": derivation,
        "embargo_seconds": EMBARGO_SECONDS,
        "execution_id": execution_id,
        "holding_horizon_seconds": HOLDING_HORIZON_SECONDS,
        "holdout_fraction": HOLDOUT_FRACTION,
        "holdout_untouched_until_final_evaluation": True,
        "label_horizon_seconds": LABEL_HORIZON_SECONDS,
        "lookback_horizon_seconds": LOOKBACK_HORIZON_SECONDS,
        "no_future_event_time_labels": True,
        "no_holdout_candidate_selection": True,
        "no_random_iid_shuffle": True,
        "no_retrospective_regime_relabel": True,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "schema_version": SPLIT_SCHEMA_VERSION,
        "split_policy": "PURGED_CHRONOLOGICAL_SPLITS_WITH_EVENT_TIME_EMBARGO",
        "survival_horizon_seconds": SURVIVAL_HORIZON_SECONDS,
        "train_fraction_within_non_holdout": TRAIN_FRACTION_WITHIN_NON_HOLDOUT,
        "walk_forward_folds": WALK_FORWARD_FOLDS,
    }
    digest = digest_excluding_keys(
        provisional, exclude={"split_digest", "execution_id", "created_at_utc"}
    )
    return SplitAndEmbargoContractV1(
        schema_version=SPLIT_SCHEMA_VERSION,
        repository_sha=repository_sha,
        preregistration_digest=preregistration_digest,
        execution_id=execution_id,
        created_at_utc=created,
        split_policy="PURGED_CHRONOLOGICAL_SPLITS_WITH_EVENT_TIME_EMBARGO",
        walk_forward_folds=WALK_FORWARD_FOLDS,
        holdout_fraction=HOLDOUT_FRACTION,
        train_fraction_within_non_holdout=TRAIN_FRACTION_WITHIN_NON_HOLDOUT,
        lookback_horizon_seconds=LOOKBACK_HORIZON_SECONDS,
        holding_horizon_seconds=HOLDING_HORIZON_SECONDS,
        survival_horizon_seconds=SURVIVAL_HORIZON_SECONDS,
        label_horizon_seconds=LABEL_HORIZON_SECONDS,
        embargo_seconds=EMBARGO_SECONDS,
        embargo_derivation=derivation,
        holdout_untouched_until_final_evaluation=True,
        no_random_iid_shuffle=True,
        no_future_event_time_labels=True,
        no_holdout_candidate_selection=True,
        no_retrospective_regime_relabel=True,
        split_digest=digest,
    )


def bind_robustness_execution_contract_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    created_at_utc: Optional[str] = None,
) -> RobustnessExecutionContractV1:
    verify_preregistration_digest_v1(preregistration_digest)
    created = created_at_utc or _utc_now_iso()
    methods = (
        "WALK_FORWARD",
        "FINAL_HOLDOUT",
        "CANDIDATE_NEIGHBORHOOD_PERTURBATION",
        "REGIME_SLICES",
        "SESSION_SLICES",
        "MISSING_SAMPLE_STRESS",
        "DUPLICATE_SAMPLE_STRESS",
        "OUT_OF_ORDER_STRESS",
        "STALE_DATA_STRESS",
        "RESTART_RESUME_CONSISTENCY",
        "LEDGER_RELOAD_CONSISTENCY",
        "BLOCK_BOOTSTRAP_CONFIDENCE_INTERVALS",
    )
    limitations = (
        "BOOTSTRAP_PRESERVES_TEMPORAL_BLOCKS_NOT_IID",
        "MONTE_CARLO_REQUIRES_REAL_FILL_SEQUENCE",
        "ECONOMIC_METRICS_ONLY_WHEN_JOINABLE",
        "NO_SYNTHETIC_PRODUCTIVE_EVIDENCE_INVENTION",
    )
    provisional = {
        "authority_scope": AUTHORITY_SCOPE,
        "bootstrap_block_seconds": BOOTSTRAP_BLOCK_SECONDS,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "created_at_utc": created,
        "execution_id": execution_id,
        "limitations": list(limitations),
        "methods": list(methods),
        "monte_carlo_policy": (
            "TRADE_SEQUENCE_MONTE_CARLO_ONLY_IF_REAL_FILL_SEQUENCE_PRESENT;ELSE_NOT_APPLICABLE"
        ),
        "neighborhood_perturbation_factors": list(NEIGHBORHOOD_PERTURBATION_FACTORS),
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "resampling_policy": "BLOCK_BOOTSTRAP_EVENT_TIME_PRESERVING",
        "schema_version": ROBUSTNESS_SCHEMA_VERSION,
    }
    digest = digest_excluding_keys(
        provisional, exclude={"robustness_digest", "execution_id", "created_at_utc"}
    )
    return RobustnessExecutionContractV1(
        schema_version=ROBUSTNESS_SCHEMA_VERSION,
        repository_sha=repository_sha,
        preregistration_digest=preregistration_digest,
        execution_id=execution_id,
        created_at_utc=created,
        methods=methods,
        bootstrap_repetitions=BOOTSTRAP_REPETITIONS,
        bootstrap_block_seconds=BOOTSTRAP_BLOCK_SECONDS,
        bootstrap_seed=BOOTSTRAP_SEED,
        neighborhood_perturbation_factors=NEIGHBORHOOD_PERTURBATION_FACTORS,
        resampling_policy="BLOCK_BOOTSTRAP_EVENT_TIME_PRESERVING",
        monte_carlo_policy=str(provisional["monte_carlo_policy"]),
        limitations=limitations,
        robustness_digest=digest,
    )


def build_research_execution_manifest_shell_v1(
    *,
    repository_sha: str,
    preregistration_digest: str,
    execution_id: str,
    candidate_domain_digest: str,
    hypothesis_contract_digest: str,
    split_contract_digest: str,
    robustness_contract_digest: str,
    input_evidence_manifest_digest: str,
    created_at_utc: Optional[str] = None,
) -> dict[str, Any]:
    created = created_at_utc or _utc_now_iso()
    provisional: dict[str, Any] = {
        "authority_scope": AUTHORITY_SCOPE,
        "candidate_domain_digest": candidate_domain_digest,
        "capability_id": "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1",
        "created_at_utc": created,
        "enforcement_applied": False,
        "execution_id": execution_id,
        "hypothesis_contract_digest": hypothesis_contract_digest,
        "input_evidence_manifest_digest": input_evidence_manifest_digest,
        "non_authority_scope": NON_AUTHORITY_SCOPE,
        "numeric_threshold_selected": False,
        "parameter_promoted": False,
        "preregistration_digest": preregistration_digest,
        "repository_sha": repository_sha,
        "robustness_contract_digest": robustness_contract_digest,
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "split_contract_digest": split_contract_digest,
        "threshold_status": THRESHOLD_STATUS,
    }
    provisional["manifest_digest"] = digest_excluding_keys(provisional, exclude={"manifest_digest"})
    return provisional


def assert_candidate_domain_immutable_v1(
    bound: CandidateDomainContractV1,
    *,
    attempted_candidates: Sequence[int],
) -> None:
    if tuple(int(x) for x in attempted_candidates) != bound.candidate_max_age_seconds:
        raise MaxAgeResearchExecutionError("candidate_domain_immutable_after_bind")


def assert_candidates_not_config_authority_v1(domain: Mapping[str, Any]) -> None:
    text = json_blob(domain)
    for forbidden in (
        "productive_policy_default",
        "config_default_max_age",
        "NUMERIC_MAX_AGE_SECONDS=",
    ):
        if forbidden in text:
            raise MaxAgeResearchExecutionError("candidate_values_must_not_be_config_authority")
    if domain.get("candidate_authority", "").find("NOT_CONFIG") < 0:
        raise MaxAgeResearchExecutionError("candidate_authority_missing_not_config")


def json_blob(payload: Mapping[str, Any]) -> str:
    from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.serialization_v1 import (
        canonical_json_dumps,
    )

    return canonical_json_dumps(payload)
