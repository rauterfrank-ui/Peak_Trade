"""Prospective F1/M9 candidate-selection campaign preregistration v1 (not executed)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.f1_m9_productive_candidate_selection_policy_v1 import (
    HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
    HISTORICAL_PREREGISTRATION_CONFIG,
    HISTORICAL_PREREGISTRATION_DIGEST,
    OWNER_SELECTION_POLICY_ID,
    WORKPACKAGE_ID,
    build_owner_selection_policy_v1,
    compute_owner_selection_policy_digest,
    load_owner_selection_policy_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)

SCHEMA_VERSION: Final[str] = "f1_m9_prospective_candidate_selection_campaign_preregistration/v1"
CAPABILITY_ID: Final[str] = (
    "F1_M9_PROSPECTIVE_VOLATILITY_NUMERIC_MAX_AGE_CANDIDATE_SELECTION_CAMPAIGN_PREREGISTRATION_V1"
)
PREREGISTRATION_CONFIG: Final[str] = (
    "config/research/f1_m9_prospective_volatility_numeric_max_age_candidate_selection_"
    "campaign_preregistration_v1.json"
)
CAMPAIGN_BINDING_CONFIG: Final[str] = (
    "config/governance/f1_m9_prospective_candidate_selection_campaign_binding_v1.json"
)

CAMPAIGN_ID_PREFIX: Final[str] = "cv_maxage_f1_m9_prospective_candidate_selection_v1"
PREREGISTRATION_FROZEN_AT_UTC: Final[str] = "2026-09-24T21:00:00Z"


@dataclass(frozen=True, slots=True)
class F1M9ProspectivePreregistrationResolutionV1:
    new_preregistration_id: str
    new_preregistration_digest: str
    new_campaign_id: str
    threshold_selection_authorized_within_new_campaign: bool
    new_prospective_campaign_preregistered: bool
    new_prospective_campaign_executed: bool
    new_decision_making_evidence_generated: bool
    historical_preregistration_unchanged: bool
    historical_evidence_decision_leakage: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "historical_evidence_decision_leakage": self.historical_evidence_decision_leakage,
            "historical_preregistration_unchanged": self.historical_preregistration_unchanged,
            "new_campaign_id": self.new_campaign_id,
            "new_decision_making_evidence_generated": self.new_decision_making_evidence_generated,
            "new_preregistration_digest": self.new_preregistration_digest,
            "new_preregistration_id": self.new_preregistration_id,
            "new_prospective_campaign_executed": self.new_prospective_campaign_executed,
            "new_prospective_campaign_preregistered": self.new_prospective_campaign_preregistered,
            "threshold_selection_authorized_within_new_campaign": (
                self.threshold_selection_authorized_within_new_campaign
            ),
        }


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CONFIG_NOT_MAPPING:{path}")
    return payload


def preregistration_body_for_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "preregistration_digest"}


def compute_preregistration_digest(payload: Mapping[str, Any]) -> str:
    return compute_content_sha256(preregistration_body_for_digest(payload))


def derive_campaign_id_v1(*, owner_selection_policy_digest: str) -> str:
    suffix = owner_selection_policy_digest[:16]
    return f"{CAMPAIGN_ID_PREFIX}_{suffix}"


def build_prospective_candidate_selection_campaign_preregistration_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    policy = build_owner_selection_policy_v1(repo_root=root)
    policy_digest = str(policy["owner_selection_policy_digest"])
    campaign_id = derive_campaign_id_v1(owner_selection_policy_digest=policy_digest)

    body: dict[str, Any] = {
        "artifact_class": "F1_M9_PROSPECTIVE_CANDIDATE_SELECTION_CAMPAIGN_PREREGISTRATION_V1",
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "capability_id": CAPABILITY_ID,
        "preregistration_id": CAPABILITY_ID,
        "bound_origin_main_sha": policy["bound_origin_main_sha"],
        "campaign_id": campaign_id,
        "campaign_purpose": (
            "Prospective REAL public-MD evidence campaign for F1/M9 governed candidate "
            "proposal selection only under a frozen owner selection policy. "
            "Threshold selection is authorized only within this preregistration and only "
            "via the precommitted deterministic selection rule. Does not authorize "
            "productive enforcement, apply, or promotion."
        ),
        "authority_state": "PREREGISTERED_UNEXECUTED",
        "campaign_execution_authorized": False,
        "network_authorized": False,
        "evidence_write_authorized": False,
        "threshold_selection_authorized": True,
        "parameter_decision_authorized": False,
        "productive_apply_authorized": False,
        "promotion_authorized": False,
        "enforcement_activation_authorized": False,
        "surface_id": OPTIMIZATION_SURFACE_ID,
        "parameter_ids": {
            "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
            "target_policy_parameter": TARGET_POLICY_PARAMETER,
        },
        "target_consumer_module": POLICY_CONSUMER_MODULE,
        "owner_selection_policy_id": OWNER_SELECTION_POLICY_ID,
        "owner_selection_policy_digest": policy_digest,
        "owner_selection_policy_config": (
            "config/governance/f1_m9_productive_candidate_selection_policy_v1.json"
        ),
        "research_age_grid_seconds": list(OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS),
        "decision_making_evidence_constraints": {
            "evidence_must_bind_new_preregistration_digest": True,
            "evidence_timestamp_or_run_id_must_be_downstream_of_preregistration": True,
            "pre_preregistration_evidence_decision_forbidden": True,
            "historical_counterfactual_campaign_evidence_decision_forbidden": True,
            "historical_counterfactual_campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
            "historical_preregistration_digest": HISTORICAL_PREREGISTRATION_DIGEST,
        },
        "abort_block_criteria": [
            "REPOSITORY_SHA_DRIFT",
            "PREREGISTRATION_DIGEST_DRIFT",
            "OWNER_SELECTION_POLICY_DIGEST_DRIFT",
            "CAMPAIGN_ID_REUSE_WITH_DIFFERENT_POLICY",
            "UNAUTHORIZED_SESSION_START",
            "NETWORK_ACCESS_BEFORE_SEPARATE_AUTHORIZATION",
            "EVIDENCE_WRITE_BEFORE_SEPARATE_AUTHORIZATION",
            "PRE_PREREGISTRATION_EVIDENCE_USED_FOR_SELECTION",
            "HISTORICAL_COUNTERFACTUAL_EVIDENCE_USED_FOR_SELECTION",
            "ENFORCEMENT_ACTIVATION",
            "PRODUCTIVE_APPLY",
            "PARAMETER_PROMOTION_WITHOUT_SEPARATE_AUTHORIZATION",
            "ALPHA_STATE_COMPOSITION_MUTATION",
        ],
        "non_promotion_invariants": {
            "COUNTERFACTUAL_ONLY": False,
            "THRESHOLD_SELECTION_WITHIN_CAMPAIGN_ONLY": True,
            "SELECTION_OUTCOME_IS_PROPOSAL_ONLY": True,
            "PRODUCTIVE_NUMERIC_MUTATION_FORBIDDEN": True,
            "ENFORCEMENT_APPLIED": False,
            "AUTO_PROMOTION_ALLOWED": False,
        },
        "campaign_termination_rules": {
            "terminal_on_selection_outcome_or_no_selection": True,
            "terminal_on_fail_closed_abort": True,
            "no_auto_productive_apply_on_selection": True,
        },
        "expected_durable_campaign_root": (
            f"docs/evidence/canonical_volatility_max_age_productive_research_evidence_ledger_v1/"
            f"campaigns/{campaign_id}"
        ),
        "planned_sessions_minimum": 2,
        "selection_rule_binding": policy["selection_rule"]["selection_rule_id"],
        "created_at_utc": PREREGISTRATION_FROZEN_AT_UTC,
        "frozen_at_utc": PREREGISTRATION_FROZEN_AT_UTC,
    }
    body["preregistration_digest"] = compute_preregistration_digest(body)
    return body


def verify_prospective_candidate_selection_campaign_preregistration_v1(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> None:
    root = _repo_root(repo_root)
    stored = str(payload.get("preregistration_digest") or "")
    if not is_valid_sha256_hex(stored):
        raise ValueError("PREREGISTRATION_DIGEST_INVALID")
    if compute_preregistration_digest(payload) != stored:
        raise ValueError("PREREGISTRATION_DIGEST_MISMATCH")
    expected = build_prospective_candidate_selection_campaign_preregistration_v1(repo_root=root)
    if preregistration_body_for_digest(expected) != preregistration_body_for_digest(dict(payload)):
        raise ValueError("PREREGISTRATION_BODY_DRIFT")
    if payload.get("threshold_selection_authorized") is not True:
        raise ValueError("THRESHOLD_SELECTION_NOT_AUTHORIZED_IN_NEW_PREREG")
    if payload.get("campaign_execution_authorized") is True:
        raise ValueError("CAMPAIGN_EXECUTION_MUST_NOT_BE_AUTHORIZED_IN_THIS_SLICE")
    policy_digest = str(payload.get("owner_selection_policy_digest") or "")
    if policy_digest != compute_owner_selection_policy_digest(
        load_owner_selection_policy_v1(repo_root=root)
    ):
        raise ValueError("OWNER_SELECTION_POLICY_BINDING_DRIFT")


def load_prospective_candidate_selection_campaign_preregistration_v1(
    *, repo_root: Path | None = None
) -> dict[str, Any]:
    root = _repo_root(repo_root)
    payload = _load_json(root / PREREGISTRATION_CONFIG)
    verify_prospective_candidate_selection_campaign_preregistration_v1(payload, repo_root=root)
    return payload


def assert_historical_preregistration_unchanged_v1(*, repo_root: Path | None = None) -> bool:
    root = _repo_root(repo_root)
    historical = _load_json(root / HISTORICAL_PREREGISTRATION_CONFIG)
    digest = str(historical.get("preregistration_digest") or "")
    if digest != HISTORICAL_PREREGISTRATION_DIGEST:
        return False
    abort = historical.get("abort_block_criteria") or []
    if "THRESHOLD_SELECTION" not in abort:
        return False
    invariants = historical.get("non_promotion_invariants") or {}
    return invariants.get("COUNTERFACTUAL_ONLY") is True


def resolve_prospective_preregistration_v1(
    *, repo_root: Path | None = None
) -> F1M9ProspectivePreregistrationResolutionV1:
    root = _repo_root(repo_root)
    path = root / PREREGISTRATION_CONFIG
    historical_ok = assert_historical_preregistration_unchanged_v1(repo_root=root)
    if not path.is_file():
        return F1M9ProspectivePreregistrationResolutionV1(
            new_preregistration_id=CAPABILITY_ID,
            new_preregistration_digest="",
            new_campaign_id="",
            threshold_selection_authorized_within_new_campaign=False,
            new_prospective_campaign_preregistered=False,
            new_prospective_campaign_executed=False,
            new_decision_making_evidence_generated=False,
            historical_preregistration_unchanged=historical_ok,
            historical_evidence_decision_leakage=False,
        )
    prereg = load_prospective_candidate_selection_campaign_preregistration_v1(repo_root=root)
    binding_path = root / CAMPAIGN_BINDING_CONFIG
    executed = False
    if binding_path.is_file():
        binding = _load_json(binding_path)
        executed = binding.get("campaign_executed") is True
    campaign_root = root / str(prereg.get("expected_durable_campaign_root") or "")
    evidence_generated = (campaign_root / "campaign_manifest.json").is_file()

    return F1M9ProspectivePreregistrationResolutionV1(
        new_preregistration_id=str(prereg.get("preregistration_id") or CAPABILITY_ID),
        new_preregistration_digest=str(prereg.get("preregistration_digest") or ""),
        new_campaign_id=str(prereg.get("campaign_id") or ""),
        threshold_selection_authorized_within_new_campaign=(
            prereg.get("threshold_selection_authorized") is True
        ),
        new_prospective_campaign_preregistered=True,
        new_prospective_campaign_executed=executed,
        new_decision_making_evidence_generated=evidence_generated,
        historical_preregistration_unchanged=historical_ok,
        historical_evidence_decision_leakage=False,
    )


__all__ = [
    "CAMPAIGN_BINDING_CONFIG",
    "CAPABILITY_ID",
    "PREREGISTRATION_CONFIG",
    "SCHEMA_VERSION",
    "F1M9ProspectivePreregistrationResolutionV1",
    "assert_historical_preregistration_unchanged_v1",
    "build_prospective_candidate_selection_campaign_preregistration_v1",
    "compute_preregistration_digest",
    "derive_campaign_id_v1",
    "load_prospective_candidate_selection_campaign_preregistration_v1",
    "preregistration_body_for_digest",
    "resolve_prospective_preregistration_v1",
    "verify_prospective_candidate_selection_campaign_preregistration_v1",
]
