"""Post-PR4937 final research fleet bindings and offline evaluation scope ratification v0.

Deterministic, fail-closed validation of versioned final fleet bindings for
trend_following/v1, bollinger_bands/v1, and momentum_1h/v1 by reusing
authoritative class-D binding completion and offline evaluation scope owners.

Binding/scope ratification only. No economic evaluation execution, no runtime
or order effect.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    compute_binding_semantic_digest_v0,
)

PACKAGE_MARKER = (
    "POST_PR4937_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVAL_SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = "post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification.v0"
SCOPE_ID = "POST_PR4937_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0"
CONFIG_REL_PATH = "config/research/post_pr4937_final_research_fleet_bindings_and_offline_eval_scope_ratification_v0.json"
GO_TOKEN = (
    "GO_RATIFY_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
PROCESS_CLASSIFICATION = (
    "VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_NO_EVAL_V0"
)
SCOPE_CLASSIFICATION = (
    "FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVAL_SCOPE_RATIFICATION_NO_EVAL_NO_RUNTIME_"
    "AUTHORITY_V0"
)
VERDICT = "BINDINGS_AND_SCOPE_RATIFIED_NOT_EVALUATED"
NEXT_STEP = "merge_closeout_after_checks_green_or_separate_offline_evaluation_execution_GO"

BINDING_COMPLETION_OWNER = (
    "config/research/final_research_fleet_class_d_versioned_binding_completion_v0.json"
)
OFFLINE_EVALUATION_SCOPE_OWNER = "config/research/final_research_fleet_class_d_offline_economic_evaluation_scope_ratification_v0.json"

FLEET_CANDIDATE_IDS = frozenset({"trend_following", "bollinger_bands", "momentum_1h"})
EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES = frozenset(
    {
        "cross_sectional_funding_rate_rank_delta",
        "cross_sectional_funding_rate_persistence_reversal_filter",
        "cross_sectional_funding_rate_dispersion_zscore_reversion",
        "cross_sectional_funding_rate_dual_leg_spread",
        "cross_sectional_funding_rate_delta_momentum",
        "cross_sectional_funding_rate_carry",
    }
)

REQUIRED_BINDING_FIELDS = (
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
    "source_owner_references",
    "admissibility_status",
    "fail_closed_missing_field_semantics",
)

REQUIRED_CONTRACT_FLAGS: tuple[tuple[str, Any], ...] = (
    ("binding_ratification_only", True),
    ("evaluation_authorized", False),
    ("evaluation_executed", False),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_scope_ratified", True),
    ("offline_economic_evaluation_scope_ratified", True),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("threshold_lowering_authorized", False),
    ("result_rescue_authorized", False),
    ("parameter_rescue_authorized", False),
    ("runtime_rewire_admissible", False),
    ("orders_allowed", False),
    ("live_authorized", False),
)

SHARED_BINDING_FIELDS = (
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "data_digest",
)

ALLOWED_FUTURE_ACTIONS = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RatificationValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def load_ratification_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        raise FileNotFoundError(f"missing_ratification_config:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def _validate_owner_binding_completion_v0(completion: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if (
        completion.get("completion_id")
        != "final_research_fleet_class_d_versioned_binding_completion_v0"
    ):
        reasons.append("OWNER_BINDING_COMPLETION_ID_MISMATCH")
    if completion.get("economic_evaluation_authorized") is not False:
        reasons.append("OWNER_BINDING_EVALUATION_AUTHORIZED_TRUE")
    expected_ids = {f"{sid}/{ver}" for sid, ver in FLEET_CANDIDATES}
    seen: set[str] = set()
    candidates = completion.get("candidates")
    if not isinstance(candidates, list):
        return ["OWNER_BINDING_CANDIDATES_MISSING"]
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            reasons.append("OWNER_BINDING_CANDIDATE_NOT_OBJECT")
            continue
        ref = str(candidate.get("canonical_candidate_identifier", ""))
        if ref in expected_ids:
            seen.add(ref)
        if candidate.get("economic_evaluation_authorized") is not False:
            reasons.append(f"OWNER_BINDING_CANDIDATE_EVAL_AUTH_TRUE:{ref}")
        for digest_field in ("implementation_digest", "config_digest", "data_digest"):
            if not candidate.get(digest_field):
                reasons.append(f"OWNER_BINDING_MISSING_DIGEST:{digest_field}:{ref}")
        expected_semantic = compute_binding_semantic_digest_v0(candidate)
        if str(candidate.get("binding_semantic_digest", "")) != expected_semantic:
            reasons.append(f"OWNER_BINDING_SEMANTIC_DIGEST_MISMATCH:{ref}")
    if seen != expected_ids:
        reasons.append("OWNER_BINDING_FLEET_CANDIDATE_SET_MISMATCH")
    return reasons


def _validate_owner_offline_scope_v0(
    scope: Mapping[str, Any],
    *,
    expected_completion_digest: str,
) -> list[str]:
    reasons: list[str] = []
    if scope.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append("OWNER_SCOPE_NOT_RATIFIED")
    if scope.get("economic_evaluation_authorized") is not False:
        reasons.append("OWNER_SCOPE_EVALUATION_AUTHORIZED_TRUE")
    if scope.get("evaluation_execution_performed") is not False:
        reasons.append("OWNER_SCOPE_EVALUATION_EXECUTED")
    if str(scope.get("fleet_binding_digest", "")) != expected_completion_digest:
        reasons.append("OWNER_SCOPE_FLEET_BINDING_DIGEST_MISMATCH")
    candidate_refs = scope.get("candidate_refs")
    if not isinstance(candidate_refs, list) or len(candidate_refs) != 3:
        reasons.append("OWNER_SCOPE_CANDIDATE_REFS_MISMATCH")
    return reasons


def _candidate_from_binding_completion(
    completion: Mapping[str, Any],
    strategy_id: str,
) -> Mapping[str, Any] | None:
    candidates = completion.get("candidates")
    if not isinstance(candidates, list):
        return None
    for candidate in candidates:
        if isinstance(candidate, Mapping) and candidate.get("strategy_id") == strategy_id:
            return candidate
    return None


def validate_ratified_binding_entry_v0(
    binding: Any,
    *,
    owner_completion: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if not isinstance(binding, Mapping):
        return ["RATIFIED_BINDING_NOT_OBJECT"]

    strategy_id = binding.get("strategy_id")
    strategy_version = binding.get("strategy_version")
    if strategy_id not in FLEET_CANDIDATE_IDS:
        reasons.append(f"UNKNOWN_FLEET_CANDIDATE:{strategy_id}")
    if strategy_id in EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES:
        reasons.append(f"EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATE_REINTRODUCED:{strategy_id}")

    for field in REQUIRED_BINDING_FIELDS:
        if field not in binding or binding.get(field) in (None, "", {}):
            reasons.append(f"MISSING_REQUIRED_BINDING_FIELD:{field}:{strategy_id}")

    if binding.get("evaluation_authorized") is not False:
        reasons.append(f"EVALUATION_AUTHORIZED_MUST_BE_FALSE:{strategy_id}")
    if binding.get("fail_closed_missing_field_semantics") != "REJECT_RATIFICATION":
        reasons.append(f"FAIL_CLOSED_SEMANTICS_MISMATCH:{strategy_id}")

    owner_candidate = _candidate_from_binding_completion(owner_completion, str(strategy_id))
    if owner_candidate is None:
        reasons.append(f"OWNER_BINDING_MISSING:{strategy_id}")
        return reasons

    for digest_field in (
        "implementation_digest",
        "config_digest",
        "data_digest",
        "binding_semantic_digest",
    ):
        if str(binding.get(digest_field, "")) != str(owner_candidate.get(digest_field, "")):
            reasons.append(f"OWNER_DIGEST_MISMATCH:{digest_field}:{strategy_id}")

    expected_version = next((v for s, v in FLEET_CANDIDATES if s == strategy_id), None)
    if strategy_version != expected_version:
        reasons.append(f"WRONG_STRATEGY_VERSION:{strategy_id}")

    return reasons


def validate_ratification_config_v0(
    config: Mapping[str, Any],
    *,
    repo_root: Path,
) -> RatificationValidationResultV0:
    reasons: list[str] = []

    if config.get("scope_id") != SCOPE_ID:
        reasons.append("UNEXPECTED_SCOPE_ID")
    if config.get("go_token") != GO_TOKEN:
        reasons.append("UNEXPECTED_GO_TOKEN")
    if config.get("verdict") != VERDICT:
        reasons.append("UNEXPECTED_VERDICT")
    if config.get("next_step") != NEXT_STEP:
        reasons.append("UNEXPECTED_NEXT_STEP")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        reasons.append("UNEXPECTED_PROCESS_CLASSIFICATION")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        reasons.append("UNEXPECTED_SCOPE_CLASSIFICATION")

    for field, expected in REQUIRED_CONTRACT_FLAGS:
        if config.get(field) is not expected:
            reasons.append(f"CONTRACT_FLAG_MISMATCH:{field}")

    prerequisite = config.get("pr4937_terminalization_prerequisite", {})
    if not isinstance(prerequisite, Mapping):
        reasons.append("MISSING_PR4937_TERMINALIZATION_PREREQUISITE")
    else:
        if prerequisite.get("cross_sectional_funding_research_fleet_status") != "COMPLETE_NO_PASS":
            reasons.append("PR4937_FLEET_STATUS_MISMATCH")
        if (
            prerequisite.get("selected_next_scope")
            != "FINAL_RESEARCH_FLEET_BINDINGS_CANONICAL_RUNBOOK_PATH"
        ):
            reasons.append("PR4937_SELECTED_NEXT_SCOPE_MISMATCH")

    blocked = set(config.get("blocked_actions", []))
    for forbidden in (
        "THRESHOLD_LOWERING",
        "RESULT_RESCUE",
        "PARAMETER_RESCUE",
        "RUNTIME_REWIRE",
        "LIVE",
        "ORDERS",
    ):
        if forbidden not in blocked:
            reasons.append(f"MISSING_BLOCKED_ACTION:{forbidden}")

    future_actions = config.get("allowed_future_actions_after_separate_go", [])
    if list(future_actions) != list(ALLOWED_FUTURE_ACTIONS):
        reasons.append("ALLOWED_FUTURE_ACTIONS_MISMATCH")

    binding_owner_rel = str(config.get("binding_completion_owner_ref", ""))
    scope_owner_rel = str(config.get("offline_economic_evaluation_scope_owner_ref", ""))
    if binding_owner_rel != BINDING_COMPLETION_OWNER:
        reasons.append("BINDING_COMPLETION_OWNER_MISMATCH")
    if scope_owner_rel != OFFLINE_EVALUATION_SCOPE_OWNER:
        reasons.append("OFFLINE_EVALUATION_SCOPE_OWNER_MISMATCH")

    binding_path = repo_root / binding_owner_rel
    scope_path = repo_root / scope_owner_rel
    if not binding_path.is_file():
        reasons.append("BINDING_COMPLETION_OWNER_MISSING")
    if not scope_path.is_file():
        reasons.append("OFFLINE_EVALUATION_SCOPE_OWNER_MISSING")

    owner_completion: dict[str, Any] = {}
    owner_scope: dict[str, Any] = {}
    if binding_path.is_file():
        owner_completion = _load_json(binding_path)
        reasons.extend(_validate_owner_binding_completion_v0(owner_completion))
    if scope_path.is_file():
        owner_scope = _load_json(scope_path)
        expected_digest = (
            str(owner_completion.get("completion_digest", "")) if owner_completion else ""
        )
        reasons.extend(
            _validate_owner_offline_scope_v0(
                owner_scope,
                expected_completion_digest=expected_digest,
            )
        )

    ratified_bindings = config.get("ratified_bindings", [])
    if not isinstance(ratified_bindings, list) or len(ratified_bindings) != 3:
        reasons.append("RATIFIED_BINDINGS_COUNT_MISMATCH")
        ratified_bindings = ratified_bindings or []

    seen_ids: set[str] = set()
    parsed_bindings: list[Mapping[str, Any]] = []
    for binding in ratified_bindings:
        sid = str(binding.get("strategy_id", "")) if isinstance(binding, Mapping) else ""
        seen_ids.add(sid)
        entry_reasons = validate_ratified_binding_entry_v0(
            binding,
            owner_completion=owner_completion,
        )
        reasons.extend(entry_reasons)
        if isinstance(binding, Mapping):
            parsed_bindings.append(binding)

    if seen_ids != FLEET_CANDIDATE_IDS:
        reasons.extend(
            f"MISSING_RATIFIED_CANDIDATE:{sid}" for sid in sorted(FLEET_CANDIDATE_IDS - seen_ids)
        )
        reasons.extend(
            f"EXTRA_RATIFIED_CANDIDATE:{sid}" for sid in sorted(seen_ids - FLEET_CANDIDATE_IDS)
        )

    excluded = config.get("excluded_cross_sectional_funding_candidates", [])
    if set(excluded) != EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES:
        reasons.append("EXCLUDED_CROSS_SECTIONAL_FUNDING_SET_MISMATCH")

    if len(parsed_bindings) >= 2:
        reference = parsed_bindings[0]
        for field in SHARED_BINDING_FIELDS:
            ref_val = reference.get(field)
            for candidate in parsed_bindings[1:]:
                if candidate.get(field) != ref_val:
                    reasons.append(
                        f"SHARED_BINDING_MISMATCH:{field}:{candidate.get('strategy_id')}"
                    )

    expected_completion_digest = str(config.get("expected_binding_completion_digest", ""))
    if owner_completion and expected_completion_digest != str(
        owner_completion.get("completion_digest", "")
    ):
        reasons.append("EXPECTED_BINDING_COMPLETION_DIGEST_MISMATCH")

    expected_scope_digest = str(config.get("expected_offline_evaluation_scope_digest", ""))
    if owner_scope and expected_scope_digest != str(owner_scope.get("ratification_digest", "")):
        reasons.append("EXPECTED_OFFLINE_EVALUATION_SCOPE_DIGEST_MISMATCH")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return RatificationValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
        )
    return RatificationValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def materialize_ratified_binding_summaries_v0(*, repo_root: Path) -> list[dict[str, Any]]:
    completion = _load_json(repo_root / BINDING_COMPLETION_OWNER)
    summaries: list[dict[str, Any]] = []
    for strategy_id, _strategy_version in FLEET_CANDIDATES:
        candidate = _candidate_from_binding_completion(completion, strategy_id)
        if candidate is None:
            raise ValueError(f"missing_owner_candidate:{strategy_id}")
        candidate_map = dict(candidate)
        summaries.append(
            {
                "strategy_id": candidate_map["strategy_id"],
                "strategy_version": candidate_map["strategy_version"],
                "canonical_candidate_identifier": candidate_map["canonical_candidate_identifier"],
                "binding_semantic_digest": candidate_map["binding_semantic_digest"],
                "admissibility_status": candidate_map.get(
                    "binding_status",
                    "READY_FOR_SEPARATE_OFFLINE_EVALUATION_RATIFICATION",
                ),
                "parameter_binding": deepcopy(candidate_map["parameter_binding"]),
                "dataset_binding": deepcopy(candidate_map["dataset_binding"]),
                "period_binding": deepcopy(candidate_map["period_binding"]),
                "instrument_binding": deepcopy(candidate_map["instrument_binding"]),
                "fee_model_binding": deepcopy(candidate_map["fee_model_binding"]),
                "slippage_model_binding": deepcopy(candidate_map["slippage_model_binding"]),
                "funding_model_binding": deepcopy(candidate_map["funding_model_binding"]),
                "execution_model_binding": deepcopy(candidate_map["execution_model_binding"]),
                "economic_policy_binding": deepcopy(candidate_map["economic_policy_binding"]),
                "implementation_digest": candidate_map["implementation_digest"],
                "config_digest": candidate_map["config_digest"],
                "data_digest": candidate_map["data_digest"],
                "source_owner_references": {
                    "binding_completion_ref": BINDING_COMPLETION_OWNER,
                    "offline_evaluation_scope_ref": OFFLINE_EVALUATION_SCOPE_OWNER,
                    "step31f_template_config_ref": candidate_map["reproducibility_metadata"][
                        "template_config_ref"
                    ],
                    "strategy_registry_owner": "src/strategies/registry.py",
                    "parameter_binding_owner": "src/backtest/strategy_signal_binding_v1.py",
                },
                "evaluation_authorized": False,
                "promotion_admissible": False,
                "runtime_rewire_admissible": False,
                "fail_closed_missing_field_semantics": "REJECT_RATIFICATION",
            }
        )
    summaries.sort(key=lambda item: item["strategy_id"])
    return summaries


__all__ = [
    "GO_TOKEN",
    "SCOPE_ID",
    "VERDICT",
    "NEXT_STEP",
    "PROCESS_CLASSIFICATION",
    "SCOPE_CLASSIFICATION",
    "CONFIG_REL_PATH",
    "ALLOWED_FUTURE_ACTIONS",
    "FLEET_CANDIDATE_IDS",
    "EXCLUDED_CROSS_SECTIONAL_FUNDING_CANDIDATES",
    "REQUIRED_BINDING_FIELDS",
    "validate_ratification_config_v0",
    "validate_ratified_binding_entry_v0",
    "materialize_ratified_binding_summaries_v0",
    "RatificationValidationResultV0",
    "ValidationVerdict",
]
