"""Repaired-binding inconclusive baseline evidence registration for bouchaud_microstructure_ohlcv_proxy/v1.

Offline-only ratification slice: registers post-repair reevaluation inconclusive baseline,
preserves prior failed execution-contract evaluation and PR #5099 repair lineage,
blocks unchanged-binding retry. No economic reevaluation, no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0=true"
)
SCHEMA_VERSION = (
    "bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block.v0"
)
REGISTRATION_ID = (
    "bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_REGISTER_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_INCONCLUSIVE_BASELINE_ADJUDICATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_repaired_binding_inconclusive_baseline_evidence_and_"
    "unchanged_retry_block_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_REPAIRED_BINDING_INCONCLUSIVE_BASELINE_EVIDENCE_AND_"
    "UNCHANGED_RETRY_BLOCK_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/bouchaud_microstructure_ohlcv_proxy_v1_versioned_research_binding_v0.json"
)
SCOPE_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0.json"
)

STRATEGY_ID = "bouchaud_microstructure"
STRATEGY_VERSION = "v1"
RESEARCH_SCOPE = "bouchaud_microstructure_ohlcv_proxy/v1"
STRATEGY_BINDING = RESEARCH_SCOPE
BINDING_CLASSIFICATION = "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
CANONICAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_repaired_same_semantic_binding_offline_"
    "baseline_reevaluation_v0_20260710T180542Z"
)
PRIOR_FAILED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T174747Z"
)
REPAIR_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5099_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_sizing_digest_and_"
    "admissibility_guard_repair_v0_20260710T180222Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260710T180542Z"
CANONICAL_MANIFEST_DIGEST = "276e8210ae34b72ad3b721f9bafcc7ae40124539cca57faa9335bd09056e69af"
PRIOR_FAILED_EVALUATION_TIMESTAMP = "20260710T174747Z"
SOURCE_PR = 5099
SOURCE_MERGE_COMMIT = "36431e46686fc9025368f0c465345952e9b82726"
PRE_MERGE_ORIGIN_MAIN = "b0ca2cf6403c9e96c000aa5cb038b749a7328bb8"

BINDING_DIGEST = "99d6153cfc25e550a429cde04a2d684c56e0e84369cc3e1196cae9f91ac26422"
OLD_BINDING_DIGEST = "39a783904714eb988e9a5fee34e6474e0bb65821ddf525af8df53268906f6e7c"
IMPLEMENTATION_DIGEST = "e76f7d06e9e8e92e2ea3db436e404894e66f218ee78e4f1e0962a37d4a8b2e35"
CONFIG_DIGEST = "a3af95053e4a60d302c47465d40b82d2002b75d51a2822a01d756b167bfafd95"
OLD_CONFIG_DIGEST = "a9c0f1d859855ef406e3f7cdc31e4f71ddf86e18d7e97a0bea2b2d0d1fdd1472"
OLD_SIZING_CONFIG_DIGEST = "c0b377c523ccc6ed8c69e0976c36f19ba6d1f5f01080aecd36004f9d87bcddee"
NEW_SIZING_CONFIG_DIGEST = "c75b7f115c62977a4e6a089c02c3eabe660cf6bf23c295229fd25294790616f0"
DATA_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
STRATEGY_PARAMS_DIGEST = "bda8f9eb343ce818a1c56e69377c3c10c0c014bcb1f16053b0c897bd0a304b3f"
MATERIAL_DIFFERENCE_DIGEST = "34599aa261c9ce32ced00e8000e09e152031ba59d5402d89558488c177a378a2"

PRIMARY_CAUSE_CLASS = "INSUFFICIENT_TRADE_SAMPLE_AFTER_REPAIRED_BINDING_REEVALUATION"
TERMINAL_STATUS = "TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE"
TERMINAL_FAILURE_CLASS = "INCONCLUSIVE_BASELINE_INSUFFICIENT_TRADE_SAMPLE"
BASELINE_VERDICT = "INCONCLUSIVE"
GROSS_RETURN = -0.005
NET_RETURN = -0.005
NET_EXPECTANCY = -50.0
PROFIT_FACTOR = 0.0
SHARPE = -0.13574571161896873
MAX_DRAWDOWN = -0.005
TRADE_COUNT = 1
POLICY_MINIMUM_TRADE_COUNT = 50
SAMPLE_SUFFICIENCY_STATUS = "INSUFFICIENT"
REEVALUATION_EXECUTION_COUNT = 1
PRIMARY_REASON_CODES = (
    "TRADE_COUNT_BELOW_THRESHOLD",
    "NET_EXPECTANCY_BELOW_THRESHOLD",
    "PROFIT_FACTOR_BELOW_THRESHOLD",
)
WALK_FORWARD_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"
MONTE_CARLO_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"
STRESS_STATUS = "DEFERRED_NEGATIVE_OR_INCONCLUSIVE_BASELINE"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = (
    "AWAIT_SEPARATE_OPERATOR_GO_FOR_DISTINCT_ROBUSTNESS_OR_NEW_RESEARCH_SCOPE_DECISION"
)

REQUIRED_CANONICAL_EVIDENCE_FILES = (
    "cryptographic_identity_comparison.json",
    "economic_result.json",
    "evaluation_exit_status.txt",
    "final_report.txt",
    "repaired_binding_verification.json",
    "reevaluation_invocation.json",
    "semantic_identity_comparison.json",
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


def normalize_binding_identity_comparison(
    repaired: Mapping[str, Any],
    crypto: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "bouchaud_repaired_binding_identity_relation.v0",
        "binding_classification": repaired.get("binding_classification", BINDING_CLASSIFICATION),
        "semantic_binding_identity_changed": not repaired.get(
            "semantic_binding_identity_match", True
        ),
        "cryptographic_binding_identity_changed": not crypto.get(
            "cryptographic_binding_identity_match", False
        ),
        "old_binding_digest": repaired.get("old_binding_digest", OLD_BINDING_DIGEST),
        "new_binding_digest": repaired.get("new_binding_digest", BINDING_DIGEST),
        "old_evaluation_config_digest": repaired.get(
            "old_evaluation_config_digest", OLD_CONFIG_DIGEST
        ),
        "new_evaluation_config_digest": repaired.get("new_evaluation_config_digest", CONFIG_DIGEST),
        "old_sizing_config_digest": repaired.get(
            "old_sizing_config_digest", OLD_SIZING_CONFIG_DIGEST
        ),
        "new_sizing_config_digest": repaired.get(
            "new_sizing_config_digest", NEW_SIZING_CONFIG_DIGEST
        ),
        "implementation_digest": repaired.get("implementation_digest", IMPLEMENTATION_DIGEST),
        "dataset_digest": DATA_DIGEST,
        "strategy_params_digest": STRATEGY_PARAMS_DIGEST,
        "prior_failed_evaluation_ref": str(PRIOR_FAILED_EVALUATION_DIR),
        "repair_pr5099_closeout_ref": str(REPAIR_CLOSEOUT_DIR),
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
    economic = _load_json(bundle_dir / "economic_result.json")
    accounting_pass = economic.get("accounting_reconciliation_pass") is True
    if require_accounting_pass and not accounting_pass:
        raise ValueError(f"accounting_reconciliation_not_pass:{bundle_dir}")
    return EvidenceBundleValidation(
        bundle_path=bundle_dir,
        manifest_verify_rc=manifest_verify_rc,
        manifest_digest=manifest_file_digest(bundle_dir),
        accounting_reconciliation_pass=accounting_pass,
    )


def validate_registration_preconditions(
    *,
    canonical_dir: Path = CANONICAL_EVALUATION_DIR,
    prior_failed_dir: Path = PRIOR_FAILED_EVALUATION_DIR,
    repair_closeout_dir: Path = REPAIR_CLOSEOUT_DIR,
) -> EvidenceBundleValidation:
    for bundle_dir in (prior_failed_dir, repair_closeout_dir):
        if verify_manifest_sha256(bundle_dir) != 0:
            raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    for name in REQUIRED_CANONICAL_EVIDENCE_FILES:
        if not (canonical_dir / name).is_file():
            raise ValueError(f"missing_required_evidence:{canonical_dir / name}")
    canonical = validate_evidence_bundle(canonical_dir, require_accounting_pass=True)
    if canonical.manifest_digest != CANONICAL_MANIFEST_DIGEST:
        raise ValueError("canonical_manifest_digest_mismatch")

    economic = _load_json(canonical_dir / "economic_result.json")
    if economic.get("verdict") != BASELINE_VERDICT:
        raise ValueError("economic_result_verdict_mismatch")
    if economic.get("baseline_status") != BASELINE_VERDICT:
        raise ValueError("economic_result_baseline_status_mismatch")
    if economic.get("sample_sufficiency_status") != SAMPLE_SUFFICIENCY_STATUS:
        raise ValueError("sample_sufficiency_status_mismatch")
    if int(economic.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("trade_count_mismatch")
    if float(economic.get("net_return", 0.0)) != NET_RETURN:
        raise ValueError("net_return_mismatch")
    if float(economic.get("net_expectancy", 0.0)) != NET_EXPECTANCY:
        raise ValueError("net_expectancy_mismatch")
    if float(economic.get("profit_factor", -1.0)) != PROFIT_FACTOR:
        raise ValueError("profit_factor_mismatch")
    if int(economic.get("minimum_trade_count_policy", -1)) != POLICY_MINIMUM_TRADE_COUNT:
        raise ValueError("policy_minimum_trade_count_mismatch")

    exit_status = (canonical_dir / "evaluation_exit_status.txt").read_text(encoding="utf-8")
    if "EVALUATION_EXIT_CODE=0" not in exit_status:
        raise ValueError("evaluation_exit_status_mismatch")

    invocation = _load_json(canonical_dir / "reevaluation_invocation.json")
    if int(invocation.get("reevaluation_execution_count", -1)) != REEVALUATION_EXECUTION_COUNT:
        raise ValueError("reevaluation_execution_count_mismatch")

    repaired = _load_json(canonical_dir / "repaired_binding_verification.json")
    crypto = _load_json(canonical_dir / "cryptographic_identity_comparison.json")
    identity = normalize_binding_identity_comparison(repaired, crypto)
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

    final_report = (canonical_dir / "final_report.txt").read_text(encoding="utf-8")
    if "BASELINE_STATUS=INCONCLUSIVE" not in final_report:
        raise ValueError("baseline_verdict_mismatch")
    if "SAMPLE_SUFFICIENCY_STATUS=INSUFFICIENT" not in final_report:
        raise ValueError("final_report_sample_sufficiency_mismatch")
    if "REEVALUATION_EXECUTION_COUNT=1" not in final_report:
        raise ValueError("final_report_reevaluation_execution_count_mismatch")
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
        repaired = _load_json(canonical_dir / "repaired_binding_verification.json")
        crypto = _load_json(canonical_dir / "cryptographic_identity_comparison.json")
        return normalize_binding_identity_comparison(repaired, crypto)
    return normalize_binding_identity_comparison({}, {})


def _metrics_from_canonical(canonical_dir: Path) -> dict[str, Any]:
    economic = _load_json(canonical_dir / "economic_result.json")
    return {
        "gross_return": float(economic["net_return"]),
        "net_return": float(economic["net_return"]),
        "net_expectancy": float(economic.get("net_expectancy", 0.0)),
        "profit_factor": float(economic["profit_factor"]),
        "sharpe": float(economic["sharpe"]),
        "max_drawdown": float(economic["max_drawdown"]),
        "trade_count": int(economic["trade_count"]),
        "sample_sufficiency_status": economic["sample_sufficiency_status"],
        "policy_minimum_trade_count": int(economic.get("minimum_trade_count_policy", 50)),
        "walk_forward_status": WALK_FORWARD_STATUS,
        "monte_carlo_status": MONTE_CARLO_STATUS,
        "stress_status": STRESS_STATUS,
        "primary_reason_codes": list(PRIMARY_REASON_CODES),
        "robustness_evidence_missing": True,
        "reevaluation_execution_count": REEVALUATION_EXECUTION_COUNT,
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
        "prior_failed_evaluation_bundle": str(PRIOR_FAILED_EVALUATION_DIR),
        "prior_failed_evaluation_timestamp": PRIOR_FAILED_EVALUATION_TIMESTAMP,
        "repair_closeout_dir": str(REPAIR_CLOSEOUT_DIR),
        "primary_cause_class": PRIMARY_CAUSE_CLASS,
        "terminal_status": TERMINAL_STATUS,
        "terminal_failure_class": TERMINAL_FAILURE_CLASS,
        "accounting_reconciliation_pass": True,
        "baseline_verdict": BASELINE_VERDICT,
        "terminal_economic_decision": BASELINE_VERDICT,
        "gross_return": metrics["gross_return"],
        "net_return": metrics["net_return"],
        "net_expectancy": metrics["net_expectancy"],
        "profit_factor": metrics["profit_factor"],
        "sharpe": metrics["sharpe"],
        "max_drawdown": metrics["max_drawdown"],
        "trade_count": metrics["trade_count"],
        "policy_minimum_trade_count": metrics["policy_minimum_trade_count"],
        "sample_sufficiency_status": metrics["sample_sufficiency_status"],
        "walk_forward_status": metrics["walk_forward_status"],
        "monte_carlo_status": metrics["monte_carlo_status"],
        "stress_status": metrics["stress_status"],
        "primary_reason_codes": list(metrics["primary_reason_codes"]),
        "robustness_evidence_missing": metrics["robustness_evidence_missing"],
        "reevaluation_execution_count": metrics["reevaluation_execution_count"],
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
                f"{PRIOR_FAILED_EVALUATION_DIR} (MANIFEST_VERIFY_RC=0)",
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
    updated["net_expectancy"] = registration["net_expectancy"]
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
    updated["prior_failed_evaluation_bundle"] = registration["prior_failed_evaluation_bundle"]
    updated["reevaluation_execution_count"] = registration["reevaluation_execution_count"]
    updated["robustness_evidence_missing"] = registration["robustness_evidence_missing"]
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
    updated["old_binding_digest_at_prior_failed_attempt"] = OLD_BINDING_DIGEST
    updated["implementation_digest_at_terminal_registration"] = IMPLEMENTATION_DIGEST
    updated["next_go_token"] = NEXT_CANONICAL_STEP
    updated["next_step"] = NEXT_CANONICAL_STEP
    updated["failed_execution_contract_evidence"] = False
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
    updated["net_expectancy"] = registration["net_expectancy"]
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
    updated["reevaluation_execution_count"] = registration["reevaluation_execution_count"]
    updated["robustness_evidence_missing"] = registration["robustness_evidence_missing"]
    updated["next_go_token"] = NEXT_CANONICAL_STEP
    updated["next_step"] = NEXT_CANONICAL_STEP
    return updated
