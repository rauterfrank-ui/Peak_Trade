"""Phase 6 Canonical Champion-Challenger v1 (research evaluation only).

Deterministic Champion versus Challenger evaluation. Comparability is
delegated entirely to Phase 5 Comparison SSOT. This layer classifies and
recommends; it does not swap the Champion, mutate runtime, write config,
promote, fund, or submit orders.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_comparison_ssot_v1 import (
    COMPARISON_CONTRACT_VERSION,
    CanonicalComparisonRankingRequestV1,
    CanonicalComparisonRequestV1,
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    OVERALL_COMPARABLE,
    RANKING_STATUS_RANKED,
    SCHEMA_VERSION as COMPARISON_SSOT_VERSION,
    build_canonical_comparison_result_v1,
    canonical_record_payload,
    rank_comparable_candidates_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_champion_challenger_v1"
CHAMPION_CHALLENGER_DOMAIN: Final[str] = "peak_trade.canonical_champion_challenger.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVALUATION_POLICY_VERSION: Final[str] = "canonical_champion_challenger_policy_v1"
SCORE_METRIC: Final[str] = "explicit_research_score"

CHAMPION_CHALLENGER_PRESENT: Final[bool] = True
AUTONOMOUS_CHAMPION_SWAP: Final[bool] = False
CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY: Final[bool] = False
CHAMPION_CHALLENGER_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
CHAMPION_CHALLENGER_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
CHAMPION_CHALLENGER_CAN_PROMOTE: Final[bool] = False
CHAMPION_CHALLENGER_CAN_PROMOTE_TO_LIVE: Final[bool] = False
CHAMPION_CHALLENGER_CAN_INCREASE_RISK: Final[bool] = False
CHAMPION_CHALLENGER_CAN_INCREASE_LEVERAGE: Final[bool] = False
CHAMPION_CHALLENGER_CAN_FUND: Final[bool] = False
CHAMPION_CHALLENGER_CAN_SUBMIT_ORDER: Final[bool] = False
CHAMPION_CHALLENGER_CAN_ARM: Final[bool] = False
CHAMPION_CHALLENGER_CAN_ENABLE: Final[bool] = False
CHAMPION_CHALLENGER_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
CHAMPION_CHALLENGER_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
CHAMPION_CHALLENGER_CAN_AUTHORIZE_CANARY: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

ROLE_CHALLENGER: Final[str] = "CHALLENGER"
DISPOSITION_RESEARCH_PREFERRED: Final[str] = "CHALLENGER_RESEARCH_PREFERRED"
DISPOSITION_INFERIOR: Final[str] = "CHALLENGER_INFERIOR"
DISPOSITION_TIE: Final[str] = "TIE_OR_INCONCLUSIVE"
DISPOSITION_NO_CLEAR_WINNER: Final[str] = "NO_CLEAR_WINNER"
DISPOSITION_REJECTED_COMPARABILITY: Final[str] = "REJECTED_COMPARABILITY"
EVALUATION_COMPLETE: Final[str] = "EVALUATION_COMPLETE"
EVALUATION_REJECTED: Final[str] = "EVALUATION_REJECTED"

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
        "compatible",
    }
)

_LOGGER = logging.getLogger(__name__)


class ChampionChallengerValidationError(ValueError):
    """Fail-closed Canonical Champion-Challenger v1 validation error."""


@dataclass(frozen=True)
class CanonicalChampionChallengerRequestV1:
    champion: ComparisonCandidateV1
    challengers: Sequence[ComparisonCandidateV1]
    scores: Mapping[str, float]
    created_at: str
    evaluation_policy_version: str = EVALUATION_POLICY_VERSION
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None
    score_metric: str = SCORE_METRIC


def evaluate_canonical_champion_challenger_v1(
    request: CanonicalChampionChallengerRequestV1,
) -> Mapping[str, Any]:
    if request.evaluation_policy_version != EVALUATION_POLICY_VERSION:
        raise ChampionChallengerValidationError("evaluation_policy_version mismatch")
    if request.score_metric != SCORE_METRIC:
        raise ChampionChallengerValidationError("score_metric mismatch")
    if not request.challengers:
        raise ChampionChallengerValidationError("at least one challenger is required")
    created_at = _require_created_at(request.created_at)
    champion_id = _experiment_id(request.champion)
    challenger_ids = [_experiment_id(item) for item in request.challengers]
    if champion_id in challenger_ids:
        raise ChampionChallengerValidationError("champion cannot also appear as a challenger")
    if len(set(challenger_ids)) != len(challenger_ids):
        raise ChampionChallengerValidationError("challenger experiment_id values must be unique")
    all_ids = [champion_id, *challenger_ids]
    scores = _canonicalize_scores(request.scores, all_ids)
    pair_results, comparable_challengers, rejected_challengers = _compare_challengers(
        champion=request.champion,
        champion_id=champion_id,
        challengers=request.challengers,
        challenger_ids=challenger_ids,
        created_at=created_at,
        compatibility_contract=request.compatibility_contract,
    )
    ranking_payload, ranked_ids = _rank_comparable_subset(
        champion=request.champion,
        champion_id=champion_id,
        comparable_challengers=comparable_challengers,
        scores=scores,
        created_at=created_at,
        compatibility_contract=request.compatibility_contract,
    )
    challenger_results = _classify_challengers(
        champion_id=champion_id,
        scores=scores,
        comparable_challengers=comparable_challengers,
        rejected_challengers=rejected_challengers,
    )
    research_recommendation = _overall_recommendation(challenger_results)
    overall_status = (
        EVALUATION_REJECTED
        if research_recommendation == DISPOSITION_REJECTED_COMPARABILITY
        else EVALUATION_COMPLETE
    )
    champion_state = {
        "champion_experiment_id": champion_id,
        "mutated": False,
        "swapped": False,
    }
    evidence_refs = _evidence_refs(champion_id, pair_results)
    evaluation_identity = derive_champion_challenger_identity_v1(
        champion_experiment_id=champion_id,
        challenger_experiment_ids=challenger_ids,
        pair_results=pair_results,
        challenger_results=challenger_results,
        ranked_experiment_ids=ranked_ids,
        research_recommendation=research_recommendation,
    )
    record = {
        "autonomous_champion_swap": AUTONOMOUS_CHAMPION_SWAP,
        "challenger_experiment_ids": list(challenger_ids),
        "challenger_results": challenger_results,
        "champion_challenger_can_arm": CHAMPION_CHALLENGER_CAN_ARM,
        "champion_challenger_can_authorize_canary": CHAMPION_CHALLENGER_CAN_AUTHORIZE_CANARY,
        "champion_challenger_can_create_confirm_token": (
            CHAMPION_CHALLENGER_CAN_CREATE_CONFIRM_TOKEN
        ),
        "champion_challenger_can_enable": CHAMPION_CHALLENGER_CAN_ENABLE,
        "champion_challenger_can_fund": CHAMPION_CHALLENGER_CAN_FUND,
        "champion_challenger_can_increase_leverage": CHAMPION_CHALLENGER_CAN_INCREASE_LEVERAGE,
        "champion_challenger_can_increase_risk": CHAMPION_CHALLENGER_CAN_INCREASE_RISK,
        "champion_challenger_can_mutate_live_config": CHAMPION_CHALLENGER_CAN_MUTATE_LIVE_CONFIG,
        "champion_challenger_can_promote": CHAMPION_CHALLENGER_CAN_PROMOTE,
        "champion_challenger_can_promote_to_live": CHAMPION_CHALLENGER_CAN_PROMOTE_TO_LIVE,
        "champion_challenger_can_submit_order": CHAMPION_CHALLENGER_CAN_SUBMIT_ORDER,
        "champion_challenger_can_use_confirm_token": CHAMPION_CHALLENGER_CAN_USE_CONFIRM_TOKEN,
        "champion_challenger_can_write_live_config": CHAMPION_CHALLENGER_CAN_WRITE_LIVE_CONFIG,
        "champion_challenger_domain": CHAMPION_CHALLENGER_DOMAIN,
        "champion_challenger_has_runtime_authority": CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY,
        "champion_challenger_present": CHAMPION_CHALLENGER_PRESENT,
        "champion_experiment_id": champion_id,
        "champion_state": champion_state,
        "comparable_challenger_experiment_ids": [
            item["experiment_id"] for item in comparable_challengers
        ],
        "comparison_contract_version": COMPARISON_CONTRACT_VERSION,
        "comparison_ssot_version": COMPARISON_SSOT_VERSION,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "evaluation_identity": evaluation_identity,
        "evaluation_policy_version": EVALUATION_POLICY_VERSION,
        "evidence_refs": evidence_refs,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "metric_definitions": _optional_token(
            "metric_definitions", request.champion.metric_definitions
        ),
        "overall_status": overall_status,
        "pair_results": pair_results,
        "promotion_authority": PROMOTION_AUTHORITY,
        "ranked_experiment_ids": ranked_ids,
        "ranking": ranking_payload,
        "research_recommendation": research_recommendation,
        "robustness_suite_version": _optional_token(
            "robustness_suite_version", request.champion.robustness_suite_version
        ),
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "score_metric": SCORE_METRIC,
        "scores": scores,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
    }
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_champion_challenger_result_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_champion_challenger_v1 built identity=%s recommendation=%s",
        evaluation_identity,
        research_recommendation,
    )
    return frozen


def derive_champion_challenger_identity_v1(
    *,
    champion_experiment_id: str,
    challenger_experiment_ids: Sequence[str],
    pair_results: Sequence[Mapping[str, Any]],
    challenger_results: Sequence[Mapping[str, Any]],
    ranked_experiment_ids: Sequence[str],
    research_recommendation: str,
) -> str:
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{CHAMPION_CHALLENGER_DOMAIN}.evaluation_identity",
        "payload": {
            "challenger_experiment_ids": list(challenger_experiment_ids),
            "challenger_results": list(challenger_results),
            "champion_experiment_id": champion_experiment_id,
            "comparison_ssot_version": COMPARISON_SSOT_VERSION,
            "evaluation_policy_version": EVALUATION_POLICY_VERSION,
            "pair_results": list(pair_results),
            "ranked_experiment_ids": list(ranked_experiment_ids),
            "research_recommendation": research_recommendation,
        },
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def validate_canonical_champion_challenger_result_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise ChampionChallengerValidationError("evaluation result must be a mapping")
    payload = _plain_mapping(record)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ChampionChallengerValidationError("schema_version mismatch")
    if payload.get("champion_challenger_domain") != CHAMPION_CHALLENGER_DOMAIN:
        raise ChampionChallengerValidationError("champion_challenger_domain mismatch")
    if payload.get("comparison_ssot_version") != COMPARISON_SSOT_VERSION:
        raise ChampionChallengerValidationError("comparison_ssot_version mismatch")
    if payload.get("comparison_contract_version") != COMPARISON_CONTRACT_VERSION:
        raise ChampionChallengerValidationError("comparison_contract_version mismatch")
    if payload.get("evaluation_policy_version") != EVALUATION_POLICY_VERSION:
        raise ChampionChallengerValidationError("evaluation_policy_version mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise ChampionChallengerValidationError("non-COMPLETE evaluation results are forbidden")
    if payload.get("champion_challenger_present") is not True:
        raise ChampionChallengerValidationError("champion_challenger_present must be true")
    if payload.get("autonomous_champion_swap") is not False:
        raise ChampionChallengerValidationError("autonomous_champion_swap must be false")
    if payload.get("champion_challenger_has_runtime_authority") is not False:
        raise ChampionChallengerValidationError(
            "champion_challenger_has_runtime_authority must be false"
        )
    if payload.get("champion_challenger_can_mutate_live_config") is not False:
        raise ChampionChallengerValidationError(
            "champion_challenger_can_mutate_live_config must be false"
        )
    if payload.get("champion_challenger_can_promote") is not False:
        raise ChampionChallengerValidationError("champion_challenger_can_promote must be false")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise ChampionChallengerValidationError("promotion_authority must be NONE")
    champion_id = _require_sha256("champion_experiment_id", payload.get("champion_experiment_id"))
    champion_state = payload.get("champion_state")
    if not isinstance(champion_state, Mapping):
        raise ChampionChallengerValidationError("champion_state must be a mapping")
    if champion_state.get("champion_experiment_id") != champion_id:
        raise ChampionChallengerValidationError(
            "champion_state does not preserve champion identity"
        )
    if champion_state.get("mutated") is not False or champion_state.get("swapped") is not False:
        raise ChampionChallengerValidationError("champion_state mutation or swap is forbidden")
    ranked_ids = payload.get("ranked_experiment_ids")
    rejected_ids = {
        item["challenger_experiment_id"]
        for item in payload.get("challenger_results", [])
        if isinstance(item, Mapping)
        and item.get("disposition") == DISPOSITION_REJECTED_COMPARABILITY
    }
    if not isinstance(ranked_ids, list):
        raise ChampionChallengerValidationError("ranked_experiment_ids must be a list")
    if rejected_ids.intersection(ranked_ids):
        raise ChampionChallengerValidationError(
            "incomparable challengers cannot appear in ranked_experiment_ids"
        )
    expected_integrity = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise ChampionChallengerValidationError("integrity.content_sha256 mismatch")


def canonical_record_payload_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def _compare_challengers(
    *,
    champion: ComparisonCandidateV1,
    champion_id: str,
    challengers: Sequence[ComparisonCandidateV1],
    challenger_ids: Sequence[str],
    created_at: str,
    compatibility_contract: ComparisonCompatibilityContractV1 | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    pair_results: list[dict[str, Any]] = []
    comparable: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for challenger, challenger_id in zip(challengers, challenger_ids, strict=True):
        pair = canonical_record_payload(
            build_canonical_comparison_result_v1(
                CanonicalComparisonRequestV1(
                    left=champion,
                    right=challenger,
                    created_at=created_at,
                    compatibility_contract=compatibility_contract,
                )
            )
        )
        summary = {
            "challenger_experiment_id": challenger_id,
            "champion_experiment_id": champion_id,
            "comparison_identity": pair["comparison_identity"],
            "overall_comparability": pair["overall_comparability"],
            "rejection_reasons": list(pair["rejection_reasons"]),
        }
        pair_results.append(summary)
        if pair["overall_comparability"] == OVERALL_COMPARABLE:
            comparable.append({"candidate": challenger, "experiment_id": challenger_id})
        else:
            rejected.append(
                {
                    "experiment_id": challenger_id,
                    "rejection_reasons": list(pair["rejection_reasons"]),
                }
            )
    return pair_results, comparable, rejected


def _rank_comparable_subset(
    *,
    champion: ComparisonCandidateV1,
    champion_id: str,
    comparable_challengers: Sequence[Mapping[str, Any]],
    scores: Mapping[str, float],
    created_at: str,
    compatibility_contract: ComparisonCompatibilityContractV1 | None,
) -> tuple[Mapping[str, Any] | None, list[str]]:
    if not comparable_challengers:
        return None, []
    candidates = [champion, *[item["candidate"] for item in comparable_challengers]]
    subset_ids = [champion_id, *[item["experiment_id"] for item in comparable_challengers]]
    ranking = canonical_record_payload(
        rank_comparable_candidates_v1(
            CanonicalComparisonRankingRequestV1(
                candidates=candidates,
                scores={experiment_id: scores[experiment_id] for experiment_id in subset_ids},
                created_at=created_at,
                compatibility_contract=compatibility_contract,
                score_metric="explicit_score",
            )
        )
    )
    summary = {
        "ranking_identity": ranking["ranking_identity"],
        "ranking_status": ranking["ranking_status"],
        "ranked_experiment_ids": list(ranking["ranked_experiment_ids"]),
        "rejection_reasons": list(ranking["rejection_reasons"]),
    }
    if ranking["ranking_status"] != RANKING_STATUS_RANKED:
        return summary, []
    return summary, list(ranking["ranked_experiment_ids"])


def _classify_challengers(
    *,
    champion_id: str,
    scores: Mapping[str, float],
    comparable_challengers: Sequence[Mapping[str, Any]],
    rejected_challengers: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    champion_score = scores[champion_id]
    results: list[dict[str, Any]] = []
    for item in comparable_challengers:
        experiment_id = str(item["experiment_id"])
        score = scores[experiment_id]
        if score > champion_score:
            disposition = DISPOSITION_RESEARCH_PREFERRED
        elif score < champion_score:
            disposition = DISPOSITION_INFERIOR
        else:
            disposition = DISPOSITION_TIE
        results.append(
            {
                "challenger_experiment_id": experiment_id,
                "disposition": disposition,
                "role": ROLE_CHALLENGER,
                "score": score,
            }
        )
    for item in rejected_challengers:
        results.append(
            {
                "challenger_experiment_id": str(item["experiment_id"]),
                "disposition": DISPOSITION_REJECTED_COMPARABILITY,
                "rejection_reasons": list(item["rejection_reasons"]),
                "role": ROLE_CHALLENGER,
                "score": scores[str(item["experiment_id"])],
            }
        )
    results.sort(key=lambda item: item["challenger_experiment_id"])
    return results


def _overall_recommendation(challenger_results: Sequence[Mapping[str, Any]]) -> str:
    comparable = [
        item
        for item in challenger_results
        if item["disposition"] != DISPOSITION_REJECTED_COMPARABILITY
    ]
    if not comparable:
        return DISPOSITION_REJECTED_COMPARABILITY
    preferred = [
        item for item in comparable if item["disposition"] == DISPOSITION_RESEARCH_PREFERRED
    ]
    if preferred:
        best_score = max(float(item["score"]) for item in preferred)
        leaders = [item for item in preferred if float(item["score"]) == best_score]
        if len(leaders) == 1:
            return DISPOSITION_RESEARCH_PREFERRED
        return DISPOSITION_NO_CLEAR_WINNER
    if all(item["disposition"] == DISPOSITION_INFERIOR for item in comparable):
        return DISPOSITION_INFERIOR
    if all(item["disposition"] == DISPOSITION_TIE for item in comparable):
        return DISPOSITION_TIE
    return DISPOSITION_NO_CLEAR_WINNER


def _evidence_refs(
    champion_id: str,
    pair_results: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    refs = [
        {
            "digest": champion_id,
            "kind": "EXPERIMENT_RECORD",
            "ref": champion_id,
        }
    ]
    for item in pair_results:
        refs.append(
            {
                "digest": str(item["comparison_identity"]),
                "kind": "COMPARISON_RESULT",
                "ref": str(item["challenger_experiment_id"]),
            }
        )
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for item in refs:
        unique[(item["kind"], item["ref"], item["digest"])] = item
    return [unique[key] for key in sorted(unique)]


def _experiment_id(candidate: ComparisonCandidateV1) -> str:
    identity = candidate.experiment_identity
    if not isinstance(identity, Mapping):
        raise ChampionChallengerValidationError("experiment_identity present and valid is required")
    payload = _plain_mapping(identity)
    try:
        validate_canonical_experiment_identity_v1(payload)
    except CanonicalExperimentIdentityError as exc:
        raise ChampionChallengerValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    experiment_id = derive_experiment_id_v1(str(payload["identity_digest"]))
    if candidate.experiment_id is not None:
        provided = _require_sha256("experiment_id", candidate.experiment_id)
        if provided != experiment_id:
            raise ChampionChallengerValidationError(
                "experiment_id is not bound to the Canonical Experiment Identity digest"
            )
    return experiment_id


def _canonicalize_scores(
    scores: Mapping[str, float],
    experiment_ids: Sequence[str],
) -> dict[str, float]:
    if not isinstance(scores, Mapping):
        raise ChampionChallengerValidationError("scores must be a mapping")
    canonical: dict[str, float] = {}
    for experiment_id in experiment_ids:
        if experiment_id not in scores:
            raise ChampionChallengerValidationError(f"scores missing experiment_id {experiment_id}")
        value = scores[experiment_id]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ChampionChallengerValidationError(
                f"scores[{experiment_id}] must be a finite number"
            )
        number = float(value)
        if not math.isfinite(number):
            raise ChampionChallengerValidationError(f"scores[{experiment_id}] must be finite")
        canonical[experiment_id] = number
    extra = set(str(key) for key in scores.keys()) - set(experiment_ids)
    if extra:
        raise ChampionChallengerValidationError(
            f"scores contain unknown experiment_id values: {sorted(extra)}"
        )
    return canonical


def _optional_token(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        return None
    if not _TOKEN_RE.fullmatch(value):
        raise ChampionChallengerValidationError(f"{field_name} is missing or malformed")
    return value


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise ChampionChallengerValidationError(
            f"{field_name} must be a lowercase sha256 hex digest"
        )
    return value


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise ChampionChallengerValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


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
    "AUTONOMOUS_CHAMPION_SWAP",
    "CHAMPION_CHALLENGER_CAN_PROMOTE",
    "CHAMPION_CHALLENGER_HAS_RUNTIME_AUTHORITY",
    "CHAMPION_CHALLENGER_PRESENT",
    "CanonicalChampionChallengerRequestV1",
    "ChampionChallengerValidationError",
    "DISPOSITION_INFERIOR",
    "DISPOSITION_NO_CLEAR_WINNER",
    "DISPOSITION_REJECTED_COMPARABILITY",
    "DISPOSITION_RESEARCH_PREFERRED",
    "DISPOSITION_TIE",
    "EVALUATION_POLICY_VERSION",
    "PROMOTION_AUTHORITY",
    "SCHEMA_VERSION",
    "canonical_record_payload_v1",
    "derive_champion_challenger_identity_v1",
    "evaluate_canonical_champion_challenger_v1",
    "validate_canonical_champion_challenger_result_v1",
]
