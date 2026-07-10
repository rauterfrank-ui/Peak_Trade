"""Repaired-binding inconclusive baseline evidence registration for el_karoui_vol_model/v1.

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
    "EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0=true"
)
SCHEMA_VERSION = (
    "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block.v0"
)
REGISTRATION_ID = (
    "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_PERSIST_EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_"
    "AND_BLOCK_UNCHANGED_RETRY_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "el_karoui_vol_model_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "EL_KAROUI_VOL_MODEL_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/el_karoui_vol_model_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/el_karoui_vol_model_v1_offline_economic_evaluation_scope_ratification_v0.json"
)

STRATEGY_ID = "el_karoui_vol_model"
STRATEGY_VERSION = "v1"
RESEARCH_SCOPE = "el_karoui_vol_model/v1"
STRATEGY_BINDING = RESEARCH_SCOPE
BINDING_CLASSIFICATION = "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
CANONICAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/el_karoui_vol_model_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T135114Z"
)
PRIOR_BLOCKED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/el_karoui_vol_model_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T130747Z"
)
DEFECT_REPAIR_BUNDLE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/el_karoui_vol_model_v1_defect_repair_sizing_config_digest_same_binding_"
    "no_runtime_authority_v0_20260710T131442Z"
)
REPAIR_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5089_merge_closeout_el_karoui_vol_model_v1_sizing_config_digest_same_"
    "semantic_binding_new_cryptographic_identity_repair_v0_20260710T134808Z"
)
SCOPE_RATIFICATION_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5088_merge_closeout_el_karoui_vol_model_v1_versioned_research_binding_and_"
    "offline_economic_evaluation_scope_no_runtime_authority_v0_20260710T130332Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260710T135114Z"
CANONICAL_MANIFEST_DIGEST = "11de71c7b7c19e90700c358ae88d3b049b75679fecfc2736ab52df1d759ac941"
PRIOR_BLOCKED_EVALUATION_TIMESTAMP = "20260710T130747Z"
SOURCE_PR = 5089
SOURCE_MERGE_COMMIT = "b1d2d55757fc8b188f129ed99bd38e0ce2ac4cbf"
PRE_MERGE_ORIGIN_MAIN = "5177b8af165cdce94a6589b9e5fa099fc5f9f3cc"

BINDING_DIGEST = "2ba82dd901c940a5d41d2aabd3ddeb693dbbf7cdd1f0308275d11b6df4d988b3"
OLD_BINDING_DIGEST = "223845f2047779218390fc245c3f2ebb04631bb068139e3d40731781906d099b"
IMPLEMENTATION_DIGEST = "11a8e1e3bef9bbe3a74edc329c4539d9438649c52dbdfe1034c4bd904f2a0c35"
CONFIG_DIGEST = "5d0afaed79c84a34bc0e92fc04c150dca1c0b828af4ee44b37384d0cd5943afc"
OLD_CONFIG_DIGEST = "1b45ed11abdc5310f14a160200a63bb488c55d9677cd6caec0aa4bb202969d61"
OLD_SIZING_CONFIG_DIGEST = "d49d85ede512dda6d3200dbf9a50d306a423de4279767d228d20d28d88975dd8"
NEW_SIZING_CONFIG_DIGEST = "dd9152621c58c1ed283c7b42601d66cf4fdcd1bb009f439d8583ebef64dc4516"
DATA_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
STRATEGY_PARAMS_DIGEST = "6c4a1fb8fba62cc91d5be84bdcac4b090896697f740c02afa73ec4a1376db508"
MATERIAL_DIFFERENCE_DIGEST = "db8090f93f84d842b053b3cc21fbaa8a6281d25e06ed2528477715980e43bcc2"

PRIMARY_CAUSE_CLASS = "INSUFFICIENT_TRADE_SAMPLE_AFTER_REPAIRED_BINDING_REEVALUATION"
TERMINAL_STATUS = "TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE"
TERMINAL_FAILURE_CLASS = "INCONCLUSIVE_BASELINE_INSUFFICIENT_TRADE_SAMPLE"
BASELINE_VERDICT = "INCONCLUSIVE"
GROSS_RETURN = -0.018596903598067184
NET_RETURN = -0.018596903598067184
PROFIT_FACTOR = 0.2486478079412187
SHARPE = -0.19761798607677777
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
    "baseline_adjudication.json",
    "baseline_metrics.json",
    "final_report.txt",
    "identity_relation.json",
    "repaired_binding_verification.json",
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
    defect_repair_dir: Path = DEFECT_REPAIR_BUNDLE_DIR,
    repair_closeout_dir: Path = REPAIR_CLOSEOUT_DIR,
    scope_ratification_closeout_dir: Path = SCOPE_RATIFICATION_CLOSEOUT_DIR,
) -> EvidenceBundleValidation:
    for bundle_dir in (
        prior_blocked_dir,
        defect_repair_dir,
        repair_closeout_dir,
        scope_ratification_closeout_dir,
    ):
        if verify_manifest_sha256(bundle_dir) != 0:
            raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    for name in REQUIRED_CANONICAL_EVIDENCE_FILES:
        if not (canonical_dir / name).is_file():
            raise ValueError(f"missing_required_evidence:{canonical_dir / name}")
    canonical = validate_evidence_bundle(canonical_dir, require_accounting_pass=True)
    repaired = _load_json(canonical_dir / "repaired_binding_verification.json")
    if repaired.get("binding_digest") != BINDING_DIGEST:
        raise ValueError("binding_digest_mismatch")
    identity = _load_json(canonical_dir / "identity_relation.json")
    if identity.get("binding_classification") != BINDING_CLASSIFICATION:
        raise ValueError("binding_classification_mismatch")
    if identity.get("old_binding_digest") != OLD_BINDING_DIGEST:
        raise ValueError("old_binding_digest_mismatch")
    if identity.get("new_binding_digest") != BINDING_DIGEST:
        raise ValueError("new_binding_digest_mismatch")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    if int(sample.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("trade_count_mismatch")
    if sample.get("status") != SAMPLE_SUFFICIENCY_STATUS:
        raise ValueError("sample_sufficiency_status_mismatch")
    metrics = _load_json(canonical_dir / "baseline_metrics.json")
    if int(metrics.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("baseline_metrics_trade_count_mismatch")
    adjudication = _load_json(canonical_dir / "baseline_adjudication.json")
    if adjudication.get("baseline_verdict") != BASELINE_VERDICT:
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


def build_identity_relation_record() -> dict[str, Any]:
    return {
        "schema_version": "el_karoui_repaired_binding_identity_relation.v0",
        "binding_classification": BINDING_CLASSIFICATION,
        "semantic_binding_identity_changed": False,
        "cryptographic_binding_identity_changed": True,
        "old_binding_digest": OLD_BINDING_DIGEST,
        "new_binding_digest": BINDING_DIGEST,
        "old_config_digest": OLD_CONFIG_DIGEST,
        "new_config_digest": CONFIG_DIGEST,
        "old_sizing_config_digest": OLD_SIZING_CONFIG_DIGEST,
        "new_sizing_config_digest": NEW_SIZING_CONFIG_DIGEST,
        "prior_blocked_evaluation_ref": str(PRIOR_BLOCKED_EVALUATION_DIR),
        "repair_pr_closeout_ref": str(REPAIR_CLOSEOUT_DIR),
        "repair_pr_number": SOURCE_PR,
    }


def _metrics_from_canonical(canonical_dir: Path) -> dict[str, Any]:
    metrics = _load_json(canonical_dir / "baseline_metrics.json")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    return {
        "gross_return": metrics["gross_return"],
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
        "config_digest": CONFIG_DIGEST,
        "old_config_digest": OLD_CONFIG_DIGEST,
        "old_sizing_config_digest": OLD_SIZING_CONFIG_DIGEST,
        "new_sizing_config_digest": NEW_SIZING_CONFIG_DIGEST,
        "data_digest": DATA_DIGEST,
        "strategy_params_digest": STRATEGY_PARAMS_DIGEST,
        "material_difference_digest": MATERIAL_DIFFERENCE_DIGEST,
        "canonical_evaluation_bundle": str(canonical.bundle_path),
        "canonical_evaluation_timestamp": CANONICAL_EVALUATION_TIMESTAMP,
        "canonical_manifest_digest": canonical.manifest_digest,
        "canonical_manifest_verify_rc": canonical.manifest_verify_rc,
        "prior_blocked_evaluation_bundle": str(PRIOR_BLOCKED_EVALUATION_DIR),
        "prior_blocked_evaluation_timestamp": PRIOR_BLOCKED_EVALUATION_TIMESTAMP,
        "defect_repair_bundle_dir": str(DEFECT_REPAIR_BUNDLE_DIR),
        "repair_closeout_dir": str(REPAIR_CLOSEOUT_DIR),
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
        "identity_relation": build_identity_relation_record(),
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
                f"{DEFECT_REPAIR_BUNDLE_DIR} (MANIFEST_VERIFY_RC=0)",
                f"{REPAIR_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0)",
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
    updated["binding_classification"] = BINDING_CLASSIFICATION
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
