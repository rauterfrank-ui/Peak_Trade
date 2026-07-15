"""Momentum 1h v2 versioned research binding materializer v0.

Deterministic materialization of immutable versioned bindings for momentum_1h/v2
as the second admissible post-discovery research generation. Reuses canonical sparse-signal
v2 binding geometry without parameter rescue. Binding ratification only.
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
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    canonical_candidate_identifier,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    BINDING_CLASS,
    CLASS_D_COMPLETION_REL_PATH,
    DATASET_ID,
    PANEL_DATA_DIGEST,
    PANEL_STAGING_ROOT,
    STRATEGY_VERSION,
    compute_implementation_digest_v0 as compute_sparse_implementation_digest_v0,
    compute_period_digest_v0,
    materialize_sparse_signal_candidate_v0,
)

PACKAGE_MARKER = "MOMENTUM_1H_V2_VERSIONED_RESEARCH_BINDING_V0=true"

SCHEMA_VERSION = "momentum_1h_v2_versioned_research_binding.v0"
BINDING_ARTIFACT_VERSION = "v0"
CONFIG_REL_PATH = "config/research/momentum_1h_v2_versioned_research_binding_v0.json"
GOVERNANCE_REL_PATH = (
    "docs/governance/MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_V0.md"
)

STRATEGY_ID = "momentum_1h"
RESEARCH_SCOPE = "momentum_1h/v2"
STRATEGY_ARCHETYPE = "MOMENTUM_HORIZON_V2"
REPLACES_FAILED_BINDING = "momentum_1h/v1"
HYPOTHESIS_ID = "MOMENTUM_HORIZON_V2_NON_BITCOIN_FUTURES_V2"
BINDING_GENERATION = "post_pr4921"
EXPECTED_BINDING_DIGEST = "366f7aeb21d781a2531d477ef32943c04d5edb262b7be9e540bbfcfc2528985f"

DISCOVERY_EVIDENCE_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/new_distinct_research_scope_discovery_v0_20260715T104548Z"
)
DECISION_PACKET_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/post_trend_following_v2_terminal_fail_next_admissible_scope_decision_packet_v0_"
    "20260715T154217Z"
)
TREND_FOLLOWING_V2_CLOSEOUT_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5221_merge_closeout_trend_following_v2_post_repair_economic_fail_"
    "governance_closeout_v0_20260715T153815Z"
)
POST_PR4921_CLOSEOUT_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/post_pr4921_versioned_research_bindings_no_eval_merge_closeout_"
    "20260706T083055Z"
)

AUTHORITY_EFFECT = "OFFLINE_EVALUATION_AUTHORIZATION_ONLY"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"


class BindingMaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class BindingRatificationStatus(str, Enum):
    BINDINGS_RATIFIED = "BINDINGS_RATIFIED"
    FAIL_CLOSED_NOT_RATIFIED = "FAIL_CLOSED_NOT_RATIFIED"


@dataclass(frozen=True)
class VersionedResearchBindingResultV0:
    verdict: BindingMaterializationVerdict
    ratification_status: BindingRatificationStatus
    binding: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_module_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "momentum_1h_v2_versioned_research_binding_v0",
            "strategy_archetype": STRATEGY_ARCHETYPE,
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "schema_version": SCHEMA_VERSION,
            "sparse_signal_binding_class": BINDING_CLASS,
            "binding_generation": BINDING_GENERATION,
        }
    )


def serialize_versioned_binding_json_v0(binding: Mapping[str, Any]) -> str:
    return json.dumps(binding, indent=2, sort_keys=True) + "\n"


def materialize_versioned_research_binding_v0(
    *,
    repo_root: Path | None = None,
    class_d_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    if class_d_completion is None:
        class_d_completion = json.loads(
            (root / CLASS_D_COMPLETION_REL_PATH).read_text(encoding="utf-8")
        )

    period_digest = compute_period_digest_v0()
    sparse_implementation_digest = compute_sparse_implementation_digest_v0()
    candidate = materialize_sparse_signal_candidate_v0(
        strategy_id=STRATEGY_ID,
        class_d_completion=class_d_completion,
        period_digest=period_digest,
        implementation_digest=sparse_implementation_digest,
    )

    binding_digest = str(candidate["binding_semantic_digest"])
    binding_body: dict[str, Any] = {
        "artifact_kind": "momentum_1h_v2_versioned_research_binding",
        "artifact_version": BINDING_ARTIFACT_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "binding": candidate,
        "binding_class": BINDING_CLASS,
        "binding_digest": binding_digest,
        "binding_generation": BINDING_GENERATION,
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "binding_ratified": True,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            STRATEGY_ID, STRATEGY_VERSION
        ),
        "canonical_serialization_version": "research_versioned_binding_canonical_json_v1",
        "config_digest": candidate["config_digest"],
        "data_digest": candidate["data_digest"],
        "dataset_digest": PANEL_DATA_DIGEST,
        "dataset_id": DATASET_ID,
        "decision_packet_dir": DECISION_PACKET_DIR,
        "discovery_evidence_dir": DISCOVERY_EVIDENCE_DIR,
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "economic_policy_binding": candidate["economic_policy_binding"],
        "economic_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "excluded_failed_binding": REPLACES_FAILED_BINDING,
        "execution_model_binding": candidate["execution_model_binding"],
        "fee_model_binding": candidate["fee_model_binding"],
        "funding_model_binding": candidate["funding_model_binding"],
        "go_token": ("GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"),
        "governance_ref": GOVERNANCE_REL_PATH,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_digest": candidate["implementation_digest"],
        "instrument_binding": candidate["instrument_binding"],
        "material_difference_basis": (
            "MOMENTUM_HORIZON_V2 replaces terminal momentum_1h/v1 with panel-sequential "
            "signal-density research binding; distinct from trend_following/v2 lineage."
        ),
        "module_implementation_digest": compute_module_implementation_digest_v0(),
        "offline_only": True,
        "panel_staging_root": PANEL_STAGING_ROOT,
        "parameter_binding": candidate["parameter_binding"],
        "period_binding": candidate["period_binding"],
        "period_digest": candidate["period_digest"],
        "post_pr4921_closeout_dir": POST_PR4921_CLOSEOUT_DIR,
        "promotion_granted": False,
        "ratification_status": BindingRatificationStatus.BINDINGS_RATIFIED.value,
        "research_scope": RESEARCH_SCOPE,
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": SCHEMA_VERSION,
        "slippage_model_binding": candidate["slippage_model_binding"],
        "strategy_archetype": STRATEGY_ARCHETYPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "trend_following_v2_closeout_dir": TREND_FOLLOWING_V2_CLOSEOUT_DIR,
        "unchanged_retry_allowed": False,
        "verdict": BindingMaterializationVerdict.COMPLETE.value,
    }
    binding_body["binding_digest"] = binding_digest
    return binding_body


def validate_versioned_research_binding_v0(
    binding: Mapping[str, Any],
) -> VersionedResearchBindingResultV0:
    reasons: list[str] = []
    if binding.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if binding.get("research_scope") != RESEARCH_SCOPE:
        reasons.append("RESEARCH_SCOPE_MISMATCH")
    if binding.get("strategy_id") != STRATEGY_ID:
        reasons.append("STRATEGY_ID_MISMATCH")
    if binding.get("strategy_version") != STRATEGY_VERSION:
        reasons.append("STRATEGY_VERSION_MISMATCH")
    if binding.get("binding_generation") != BINDING_GENERATION:
        reasons.append("BINDING_GENERATION_MISMATCH")
    if binding.get("excluded_failed_binding") != REPLACES_FAILED_BINDING:
        reasons.append("EXCLUDED_FAILED_BINDING_MISMATCH")
    if binding.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if binding.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE_IN_BINDING_SCOPE")
    if binding.get("unchanged_retry_allowed") is not False:
        reasons.append("UNCHANGED_RETRY_ALLOWED_MUST_BE_FALSE")
    if binding.get("dataset_digest") != PANEL_DATA_DIGEST:
        reasons.append("DATASET_DIGEST_MISMATCH")
    if binding.get("binding_digest") != EXPECTED_BINDING_DIGEST:
        reasons.append("BINDING_DIGEST_MISMATCH")
    candidate = binding.get("binding", {})
    if not isinstance(candidate, Mapping):
        reasons.append("BINDING_CANDIDATE_MISSING")
    else:
        expected_digest = candidate.get("binding_semantic_digest")
        if binding.get("binding_digest") != expected_digest:
            reasons.append("BINDING_CANDIDATE_DIGEST_MISMATCH")

    verdict = (
        BindingMaterializationVerdict.COMPLETE
        if not reasons
        else BindingMaterializationVerdict.INCOMPLETE
    )
    ratification_status = (
        BindingRatificationStatus.BINDINGS_RATIFIED
        if not reasons
        else BindingRatificationStatus.FAIL_CLOSED_NOT_RATIFIED
    )
    return VersionedResearchBindingResultV0(
        verdict=verdict,
        ratification_status=ratification_status,
        binding=deepcopy(dict(binding)),
        fail_reasons=tuple(reasons),
    )


__all__ = [
    "AUTHORITY_EFFECT",
    "BINDING_ARTIFACT_VERSION",
    "BINDING_GENERATION",
    "CONFIG_REL_PATH",
    "DECISION_PACKET_DIR",
    "DISCOVERY_EVIDENCE_DIR",
    "EXPECTED_BINDING_DIGEST",
    "GOVERNANCE_REL_PATH",
    "HYPOTHESIS_ID",
    "ORDER_EFFECT",
    "PANEL_DATA_DIGEST",
    "POST_PR4921_CLOSEOUT_DIR",
    "REPLACES_FAILED_BINDING",
    "RESEARCH_SCOPE",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "STRATEGY_ARCHETYPE",
    "STRATEGY_ID",
    "STRATEGY_VERSION",
    "TREND_FOLLOWING_V2_CLOSEOUT_DIR",
    "BindingMaterializationVerdict",
    "BindingRatificationStatus",
    "VersionedResearchBindingResultV0",
    "compute_module_implementation_digest_v0",
    "materialize_versioned_research_binding_v0",
    "serialize_versioned_binding_json_v0",
    "validate_versioned_research_binding_v0",
]
