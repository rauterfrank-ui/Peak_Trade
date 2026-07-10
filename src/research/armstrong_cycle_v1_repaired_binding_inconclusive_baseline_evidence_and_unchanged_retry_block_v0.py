"""Repaired-binding inconclusive baseline evidence registration for armstrong_cycle/v1.

Offline-only ratification slice: registers post-repair reevaluation inconclusive baseline,
preserves prior blocked evaluation and repair closeout lineage, blocks unchanged-binding retry.
No economic reevaluation, no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "ARMSTRONG_CYCLE_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0=true"
)
SCHEMA_VERSION = (
    "armstrong_cycle_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block.v0"
)
REGISTRATION_ID = (
    "armstrong_cycle_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_PERSIST_ARMSTRONG_CYCLE_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_"
    "AND_BLOCK_UNCHANGED_RETRY_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "armstrong_cycle_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "ARMSTRONG_CYCLE_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/armstrong_cycle_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0.json"
)

STRATEGY_ID = "armstrong_cycle"
STRATEGY_VERSION = "v1"
RESEARCH_SCOPE = "armstrong_cycle/v1"
STRATEGY_BINDING = RESEARCH_SCOPE
BINDING_CLASSIFICATION = "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
CANONICAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/armstrong_cycle_v1_repaired_same_semantic_binding_offline_baseline_"
    "reevaluation_v0_20260710T162406Z"
)
PRIOR_BLOCKED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T153705Z"
)
REPAIR_CLOSEOUT_PR5094_DIR = (
    DURABLE_ARCHIVE_ROOT / "research/pr5094_merge_closeout_armstrong_cycle_v1_baseline_expectancy_"
    "materialization_repair_v0_20260710T160607Z"
)
REPAIR_CLOSEOUT_PR5095_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5095_merge_closeout_armstrong_cycle_v1_legacy_gross_pnl_trade_record_"
    "emission_repair_v0_20260710T161954Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260710T162406Z"
CANONICAL_MANIFEST_DIGEST = "dc052e84020d682878f9740bc2a0cc375d6c40c638f964b1195f3390abd18123"
PRIOR_BLOCKED_EVALUATION_TIMESTAMP = "20260710T153705Z"
SOURCE_PR = 5095
SOURCE_MERGE_COMMIT = "8d9aea27c0ed2f91a66fa62d73f28f0b313a8992"
PRE_MERGE_ORIGIN_MAIN = "8d9aea27c0ed2f91a66fa62d73f28f0b313a8992"

BINDING_DIGEST = "bf0a125325692836b71ab00a775d412ecf275483769f5906e1251f68361a9896"
OLD_BINDING_DIGEST = "d29de831f426eeca087518ab9ebe53c1e77895fc0f9f4550a0d804a69403d69c"
IMPLEMENTATION_DIGEST = "e8e572b88b5fd3eb0cec598fd9fee6de73945325b897c692da002863f1c21c66"
OLD_IMPLEMENTATION_DIGEST = "5cef09f0c031acce49743ca94020c7d82bf56ecf0d4c1ce4abf4d45e7f0088f8"
CONFIG_DIGEST = "00fd45b4e3ca16799f4b892a367ecc7567363a12dd20dfaecfef5d9a4b920173"
DATA_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
STRATEGY_PARAMS_DIGEST = "e13973325ae605f55927973055d2a836967ab2844c0bcc22fd366877dafa2ef1"
MATERIAL_DIFFERENCE_DIGEST = "dc17557606eb6578ca97c2d90905ec0ffeeed2ef95b9ec77858615f2d1f71e85"
UNIVERSE_DIGEST = "be6ea12f6e883de596e8e7987be071bcb4ebc3d32bff15ec933643dcf74f9ee2"

PRIMARY_CAUSE_CLASS = "INSUFFICIENT_TRADE_SAMPLE_AFTER_REPAIRED_BINDING_RERATIFICATION"
TERMINAL_STATUS = "TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE"
TERMINAL_FAILURE_CLASS = "INCONCLUSIVE_BASELINE_INSUFFICIENT_TRADE_SAMPLE"
BASELINE_VERDICT = "INCONCLUSIVE"
GROSS_RETURN = -0.020757522861812868
NET_RETURN = -0.020757522861812868
PROFIT_FACTOR = 0.16135445765529374
SHARPE = -0.23834481082283004
MAX_DRAWDOWN = -0.02475124687812495
TRADE_COUNT = 6
POLICY_MINIMUM_TRADE_COUNT = 50
SAMPLE_SUFFICIENCY_STATUS = "INSUFFICIENT_TRADE_SAMPLE"
WALK_FORWARD_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"
MONTE_CARLO_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"
STRESS_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = "NEW_DISTINCT_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"

REQUIRED_CANONICAL_EVIDENCE_FILES = (
    "accounting_reconciliation.json",
    "binding_identity_comparison.json",
    "economic_metrics.json",
    "final_report.txt",
    "sample_sufficiency.json",
    "trade_ledger.jsonl",
)


class RegistrationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class EvidenceBundleValidation:
    bundle_path: Path
    manifest_verify_rc: int
    manifest_digest: str
    accounting_reconciliation_pass: bool
    accounting_delta: float | None


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_registration_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "registration_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def verify_manifest_sha256(bundle_dir: Path) -> int:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return 1
    result = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return 0 if result.returncode == 0 else 1


def manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _accounting_pass(reconciliation: Mapping[str, Any]) -> bool:
    if reconciliation.get("accounting_reconciliation_pass") is True:
        return True
    if reconciliation.get("reconciled") is True:
        delta = reconciliation.get("accounting_delta")
        if delta is None:
            return True
        return math.isclose(float(delta), 0.0, abs_tol=1e-8)
    return False


def normalize_binding_identity_comparison(
    comparison: Mapping[str, Any],
) -> dict[str, Any]:
    """Thin normalization for El-Karoui identity_relation parity."""
    return {
        "schema_version": "armstrong_repaired_binding_identity_relation.v0",
        "binding_classification": comparison.get("binding_classification", BINDING_CLASSIFICATION),
        "semantic_binding_identity_changed": not comparison.get(
            "semantic_binding_identity_match", True
        ),
        "cryptographic_binding_identity_changed": not comparison.get(
            "cryptographic_binding_identity_match", False
        ),
        "old_binding_digest": comparison.get("binding_digest_ratified_config", OLD_BINDING_DIGEST),
        "new_binding_digest": comparison.get("binding_digest_computed_current", BINDING_DIGEST),
        "old_implementation_digest": comparison.get(
            "implementation_digest_ratified_config", OLD_IMPLEMENTATION_DIGEST
        ),
        "new_implementation_digest": comparison.get(
            "implementation_digest_current", IMPLEMENTATION_DIGEST
        ),
        "dataset_digest": comparison.get("dataset_digest", DATA_DIGEST),
        "universe_digest": comparison.get("universe_digest", UNIVERSE_DIGEST),
        "strategy_params_digest": comparison.get("strategy_params_digest", STRATEGY_PARAMS_DIGEST),
        "prior_blocked_evaluation_ref": comparison.get(
            "previous_failed_attempt_ref", str(PRIOR_BLOCKED_EVALUATION_DIR)
        ),
        "repair_pr5094_closeout_ref": comparison.get("pr5094_repair_closeout_ref"),
        "repair_pr5095_closeout_ref": comparison.get("pr5095_repair_closeout_ref"),
        "repair_pr_number": SOURCE_PR,
    }


def validate_evidence_bundle(
    bundle_dir: Path, *, require_accounting_pass: bool
) -> EvidenceBundleValidation:
    if not bundle_dir.is_dir():
        raise ValueError(f"missing_bundle_dir:{bundle_dir}")
    manifest_verify_rc = verify_manifest_sha256(bundle_dir)
    if manifest_verify_rc != 0:
        raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    reconciliation = _load_json(bundle_dir / "accounting_reconciliation.json")
    accounting_pass = _accounting_pass(reconciliation)
    if require_accounting_pass and not accounting_pass:
        raise ValueError(f"accounting_reconciliation_not_pass:{bundle_dir}")
    delta_raw = reconciliation.get("accounting_delta")
    delta = float(delta_raw) if delta_raw is not None else None
    return EvidenceBundleValidation(
        bundle_path=bundle_dir,
        manifest_verify_rc=manifest_verify_rc,
        manifest_digest=manifest_file_digest(bundle_dir),
        accounting_reconciliation_pass=accounting_pass,
        accounting_delta=delta,
    )


def validate_registration_preconditions(
    *,
    canonical_dir: Path = CANONICAL_EVALUATION_DIR,
    prior_blocked_dir: Path = PRIOR_BLOCKED_EVALUATION_DIR,
    repair_closeout_pr5094_dir: Path = REPAIR_CLOSEOUT_PR5094_DIR,
    repair_closeout_pr5095_dir: Path = REPAIR_CLOSEOUT_PR5095_DIR,
) -> EvidenceBundleValidation:
    for bundle_dir in (
        prior_blocked_dir,
        repair_closeout_pr5094_dir,
        repair_closeout_pr5095_dir,
    ):
        if verify_manifest_sha256(bundle_dir) != 0:
            raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    for name in REQUIRED_CANONICAL_EVIDENCE_FILES:
        if not (canonical_dir / name).is_file():
            raise ValueError(f"missing_required_evidence:{canonical_dir / name}")
    canonical = validate_evidence_bundle(canonical_dir, require_accounting_pass=True)
    identity_raw = _load_json(canonical_dir / "binding_identity_comparison.json")
    identity = normalize_binding_identity_comparison(identity_raw)
    if identity["new_binding_digest"] != BINDING_DIGEST:
        raise ValueError("binding_digest_mismatch")
    if identity["binding_classification"] != BINDING_CLASSIFICATION:
        raise ValueError("binding_classification_mismatch")
    if identity["old_binding_digest"] != OLD_BINDING_DIGEST:
        raise ValueError("old_binding_digest_mismatch")
    if identity["semantic_binding_identity_changed"] is not False:
        raise ValueError("semantic_binding_identity_changed")
    if identity["cryptographic_binding_identity_changed"] is not True:
        raise ValueError("cryptographic_binding_identity_unchanged")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    if int(sample.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("trade_count_mismatch")
    if sample.get("status") != SAMPLE_SUFFICIENCY_STATUS:
        raise ValueError("sample_sufficiency_status_mismatch")
    metrics = _load_json(canonical_dir / "economic_metrics.json")
    if int(metrics.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("economic_metrics_trade_count_mismatch")
    final_report = (canonical_dir / "final_report.txt").read_text(encoding="utf-8")
    if "BASELINE_STATUS=INCONCLUSIVE" not in final_report:
        raise ValueError("baseline_verdict_mismatch")
    return canonical


def is_exact_binding_retry_blocked(
    *,
    research_scope: str,
    binding_digest: str,
    implementation_digest: str,
) -> bool:
    if research_scope != RESEARCH_SCOPE:
        return False
    return binding_digest == BINDING_DIGEST and implementation_digest == IMPLEMENTATION_DIGEST


def build_exact_binding_retry_guard_report() -> dict[str, Any]:
    return {
        "schema_version": "exact_binding_retry_guard_report.v0",
        "research_scope": RESEARCH_SCOPE,
        "binding_digest": BINDING_DIGEST,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "unchanged_retry_blocked": True,
        "same_binding_retry_allowed": False,
        "exact_binding_retry_blocked": is_exact_binding_retry_blocked(
            research_scope=RESEARCH_SCOPE,
            binding_digest=BINDING_DIGEST,
            implementation_digest=IMPLEMENTATION_DIGEST,
        ),
        "blocked_retry_axes": [
            "UNCHANGED_BINDING_RETRY",
            "SAME_BINDING_RETRY",
            "THRESHOLD_LOWERING",
            "POLICY_RESCUE",
            "POST_RESULT_PARAMETER_CHANGE",
            "PARAMETER_RELAXATION",
        ],
    }


def build_identity_relation_record(canonical_dir: Path | None = None) -> dict[str, Any]:
    if canonical_dir is not None:
        identity_raw = _load_json(canonical_dir / "binding_identity_comparison.json")
        return normalize_binding_identity_comparison(identity_raw)
    return normalize_binding_identity_comparison({})


def _metrics_from_canonical(canonical_dir: Path) -> dict[str, Any]:
    metrics = _load_json(canonical_dir / "economic_metrics.json")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    return {
        "gross_return": metrics["net_return"],
        "net_return": metrics["net_return"],
        "net_expectancy": metrics.get("net_expectancy", 0.0),
        "profit_factor": metrics["profit_factor"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "trade_count": metrics["trade_count"],
        "sample_sufficiency_status": sample["status"],
        "policy_minimum_trade_count": sample.get("minimum_trade_count_policy", 50),
        "walk_forward_status": WALK_FORWARD_STATUS,
        "monte_carlo_status": MONTE_CARLO_STATUS,
        "stress_status": STRESS_STATUS,
    }


def materialize_registration_config(
    *,
    canonical: EvidenceBundleValidation,
    registration_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    metrics = _metrics_from_canonical(canonical.bundle_path)
    payload: dict[str, Any] = {
        "artifact_kind": REGISTRATION_ID,
        "artifact_version": REGISTRATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": OPERATOR_GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "binding_config_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "scope_ratification_config_ref": SCOPE_RATIFICATION_CONFIG_REL_PATH,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_binding": STRATEGY_BINDING,
        "binding_classification": BINDING_CLASSIFICATION,
        "binding_digest": BINDING_DIGEST,
        "old_binding_digest": OLD_BINDING_DIGEST,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "old_implementation_digest": OLD_IMPLEMENTATION_DIGEST,
        "config_digest": CONFIG_DIGEST,
        "data_digest": DATA_DIGEST,
        "strategy_params_digest": STRATEGY_PARAMS_DIGEST,
        "material_difference_digest": MATERIAL_DIFFERENCE_DIGEST,
        "universe_digest": UNIVERSE_DIGEST,
        "canonical_evaluation_bundle": str(canonical.bundle_path),
        "canonical_evaluation_timestamp": CANONICAL_EVALUATION_TIMESTAMP,
        "canonical_manifest_digest": canonical.manifest_digest,
        "canonical_manifest_verify_rc": canonical.manifest_verify_rc,
        "prior_blocked_evaluation_bundle": str(PRIOR_BLOCKED_EVALUATION_DIR),
        "prior_blocked_evaluation_timestamp": PRIOR_BLOCKED_EVALUATION_TIMESTAMP,
        "repair_closeout_pr5094_dir": str(REPAIR_CLOSEOUT_PR5094_DIR),
        "repair_closeout_pr5095_dir": str(REPAIR_CLOSEOUT_PR5095_DIR),
        "primary_cause_class": PRIMARY_CAUSE_CLASS,
        "terminal_status": TERMINAL_STATUS,
        "terminal_failure_class": TERMINAL_FAILURE_CLASS,
        "accounting_reconciliation_pass": True,
        "baseline_verdict": BASELINE_VERDICT,
        "terminal_economic_decision": BASELINE_VERDICT,
        "gross_return": metrics["gross_return"],
        "net_return": metrics["net_return"],
        "profit_factor": metrics["profit_factor"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "trade_count": metrics["trade_count"],
        "policy_minimum_trade_count": metrics["policy_minimum_trade_count"],
        "sample_sufficiency_status": metrics["sample_sufficiency_status"],
        "walk_forward_status": metrics["walk_forward_status"],
        "monte_carlo_status": metrics["monte_carlo_status"],
        "stress_status": metrics["stress_status"],
        "economic_validity_offline_gate_pass": False,
        "promotion_admissible": False,
        "runtime_rewire_admissible": False,
        "retry_allowed_same_binding": False,
        "same_binding_retry_allowed": False,
        "unchanged_retry_allowed": False,
        "unchanged_retry_blocked": True,
        "immutable_binding_retry_allowed": False,
        "parameter_relaxation_authorized": False,
        "policy_rescue_allowed": False,
        "terminal_negative_evidence_for_unchanged_binding": False,
        "terminal_inconclusive_evidence_for_unchanged_binding": True,
        "new_distinct_research_scope_or_new_evidence_class_required": True,
        "exact_binding_retry_guard_report": build_exact_binding_retry_guard_report(),
        "identity_relation": build_identity_relation_record(canonical.bundle_path),
        "trading_logic_changed": False,
        "binding_changed": False,
        "dataset_changed": False,
        "cost_policy_changed": False,
        "risk_sizing_semantics_changed": False,
        "no_economic_reevaluation": True,
        "no_parameter_change": True,
        "no_policy_rescue": True,
        "no_runtime_or_promotion_action": True,
        "offline_only": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "source_pr": SOURCE_PR,
        "source_merge_commit": SOURCE_MERGE_COMMIT,
        "pre_merge_origin_main": PRE_MERGE_ORIGIN_MAIN,
        "durable_evidence_refs": "; ".join(
            [
                f"{canonical.bundle_path} (MANIFEST_VERIFY_RC=0)",
                f"{PRIOR_BLOCKED_EVALUATION_DIR} (MANIFEST_VERIFY_RC=0)",
                f"{REPAIR_CLOSEOUT_PR5094_DIR} (MANIFEST_VERIFY_RC=0)",
                f"{REPAIR_CLOSEOUT_PR5095_DIR} (MANIFEST_VERIFY_RC=0)",
            ]
        ),
        "metrics": metrics,
        "status": "REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_REGISTRATION_COMPLETE",
        "verdict": RegistrationVerdict.PASS.value,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    if registration_evidence_dir is not None:
        payload["registration_evidence_dir"] = str(registration_evidence_dir)
    payload["registration_digest"] = compute_registration_digest(payload)
    return payload


def sync_reratified_digest_fields(
    binding: Mapping[str, Any],
    *,
    fresh_binding: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(binding)
    updated["binding_digest"] = fresh_binding["binding_digest"]
    binding_body = dict(updated["binding"])
    binding_body["digest_bindings"] = fresh_binding["binding"]["digest_bindings"]
    updated["binding"] = binding_body
    if "universe_digest" in fresh_binding:
        updated["universe_digest"] = fresh_binding["universe_digest"]
    return updated


def apply_versioned_binding_registration_fields(
    binding: Mapping[str, Any],
    registration: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(binding)
    updated["economic_evaluation_executed"] = True
    updated["economic_evaluation_status"] = "COMPLETE_INCONCLUSIVE"
    updated["economic_validity_offline_gate_pass"] = False
    updated["promotion_eligible"] = False
    updated["promotion_admissible"] = False
    updated["runtime_rewire_admissible"] = False
    updated["retry_unchanged_binding_allowed"] = False
    updated["re_evaluation_allowed"] = False
    updated["evaluation_authorized"] = False
    updated["economic_evaluation_authorized"] = False
    updated["policy_or_threshold_changed"] = False
    updated["binding_changed"] = False
    updated["binding_classification"] = BINDING_CLASSIFICATION
    updated["historical_economic_result"] = BASELINE_VERDICT
    updated["trade_count"] = registration["trade_count"]
    updated["net_return"] = registration["net_return"]
    updated["gross_return"] = registration["gross_return"]
    updated["profit_factor"] = registration["profit_factor"]
    updated["sharpe"] = registration["sharpe"]
    updated["max_drawdown"] = registration["max_drawdown"]
    updated["baseline_verdict"] = BASELINE_VERDICT
    updated["sample_sufficiency_status"] = registration["sample_sufficiency_status"]
    updated["accounting_reconciliation_pass"] = True
    updated["terminal_negative_evidence_for_unchanged_binding"] = False
    updated["terminal_inconclusive_evidence_for_unchanged_binding"] = True
    updated["terminal_status"] = TERMINAL_STATUS
    updated["primary_cause_class"] = PRIMARY_CAUSE_CLASS
    updated["canonical_evaluation_timestamp"] = CANONICAL_EVALUATION_TIMESTAMP
    updated["canonical_evaluation_bundle"] = registration["canonical_evaluation_bundle"]
    updated["prior_blocked_evaluation_bundle"] = registration["prior_blocked_evaluation_bundle"]
    updated["economic_viability_evidence_ref"] = (
        f"{registration['canonical_evaluation_bundle']} (MANIFEST_VERIFY_RC=0)"
    )
    updated["economic_viability_evidence_manifest_digest"] = registration[
        "canonical_manifest_digest"
    ]
    updated["durable_evidence_refs"] = registration["durable_evidence_refs"]
    updated["terminal_failure_class"] = TERMINAL_FAILURE_CLASS
    updated["walk_forward_status"] = registration["walk_forward_status"]
    updated["monte_carlo_status"] = registration["monte_carlo_status"]
    updated["stress_status"] = registration["stress_status"]
    updated["unchanged_retry_blocked"] = True
    updated["unchanged_retry_allowed"] = False
    updated["parameter_relaxation_authorized"] = False
    updated["policy_rescue_allowed"] = False
    updated["new_distinct_research_scope_or_new_evidence_class_required"] = True
    updated["binding_digest_at_terminal_registration"] = BINDING_DIGEST
    updated["old_binding_digest_at_prior_blocked_attempt"] = OLD_BINDING_DIGEST
    updated["implementation_digest_at_terminal_registration"] = IMPLEMENTATION_DIGEST
    updated["next_go_token"] = NEXT_CANONICAL_STEP
    updated["next_step"] = NEXT_CANONICAL_STEP
    return updated


def apply_scope_ratification_registration_fields(
    scope_ratification: Mapping[str, Any],
    registration: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(scope_ratification)
    updated["binding_digest"] = BINDING_DIGEST
    updated["implementation_digest"] = IMPLEMENTATION_DIGEST
    updated["economic_evaluation_executed"] = True
    updated["economic_evaluation_status"] = "COMPLETE_INCONCLUSIVE"
    updated["evaluation_execution_authorized"] = False
    updated["economic_evaluation_authorized"] = False
    updated["evaluation_authorization_status"] = "COMPLETE_INCONCLUSIVE_BINDING_BLOCKED_RETRY"
    updated["baseline_verdict"] = BASELINE_VERDICT
    updated["terminal_status"] = TERMINAL_STATUS
    updated["trade_count"] = registration["trade_count"]
    updated["net_return"] = registration["net_return"]
    updated["sample_sufficiency_status"] = registration["sample_sufficiency_status"]
    updated["accounting_reconciliation_pass"] = True
    updated["economic_validity_offline_gate_pass"] = False
    updated["promotion_admissible"] = False
    updated["unchanged_retry_blocked"] = True
    updated["unchanged_retry_allowed"] = False
    updated["parameter_relaxation_authorized"] = False
    updated["policy_rescue_allowed"] = False
    updated["new_distinct_research_scope_or_new_evidence_class_required"] = True
    updated["canonical_evaluation_bundle"] = registration["canonical_evaluation_bundle"]
    updated["canonical_evaluation_timestamp"] = CANONICAL_EVALUATION_TIMESTAMP
    updated["next_go_token"] = NEXT_CANONICAL_STEP
    updated["next_step"] = NEXT_CANONICAL_STEP
    return updated
