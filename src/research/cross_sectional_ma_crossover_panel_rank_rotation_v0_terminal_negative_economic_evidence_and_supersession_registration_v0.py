"""Terminal-negative economic evidence and supersession registration for CS MA-crossover v0.

Offline-only ratification slice: registers corrected evaluation bundle as canonical,
supersedes accounting-incomplete original evaluation, blocks unchanged-binding retry.
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
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
    "terminal_negative_economic_evidence_and_supersession_registration.v0"
)
REGISTRATION_ID = (
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
    "terminal_negative_economic_evidence_and_supersession_registration_v0"
)
REGISTRATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = (
    "research_terminal_negative_supersession_registration_canonical_json_v1"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_RATIFY_CORRECTED_TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_"
    "terminal_negative_economic_evidence_and_supersession_registration_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "TERMINAL_NEGATIVE_ECONOMIC_EVIDENCE_AND_SUPERSESSION_REGISTRATION_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0.json"
)

STRATEGY_ID = "cross_sectional_ma_crossover_panel_rank_rotation"
STRATEGY_VERSION = "v0"
RESEARCH_SCOPE = "cross_sectional_ma_crossover_panel_rank_rotation/v0"
STRATEGY_BINDING = RESEARCH_SCOPE

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
ORIGINAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_20260710T101306Z"
)
CORRECTED_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_ma_crossover_panel_rank_rotation_v0_offline_economic_evaluation_20260710T101815Z"
)
PR5080_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5080_merge_closeout_cs_ma_crossover_panel_rank_rotation_v0_accounting_reconciliation_20260710T102332Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260710T101815Z"
SUPERSEDED_EVALUATION_TIMESTAMP = "20260710T101306Z"
SOURCE_PR = 5080
SOURCE_MERGE_COMMIT = "48dd6e367f9e61361861b6d8a0d250def424f222"
PRE_MERGE_ORIGIN_MAIN = "8ea5670cda60f9eb3656ef1aa483ed6f823457b5"

BINDING_DIGEST = "89f80951dd71e43168b9b37b0d6f04d57ba7ca025fcd4923c9901d0f244f43e6"
CONFIG_DIGEST = "eaca6226b6e040580227c8380c86a3aaa4f3e3bdad9292b37d9cbef736405141"
DATA_DIGEST = "b0eb7802c269bcab987d2025fe1e960b83079d5ac5f305799e0867661d42f2e0"
UNIVERSE_DIGEST = "ccc36aa52d9df3aa2067fbc0a75aea6ae33a458583ec8a15b08d69f54b8b9a8b"
RATIFICATION_DIGEST = "24e417edf5ec40a6e1cc50a790b2dd3b533bd2786037de3d90cdf10104a07b28"
CANONICAL_MANIFEST_DIGEST = "3a132a93e01a209c3d0c58f5573d0e04ab588ba563048d58419c03450b1b609c"
SUPERSEDED_MANIFEST_DIGEST = "1366b57fb19f0b8ea90f37b1ae2111a1b7599eeefa2728fd04650c60162b36f6"

SUPERSESSION_REASON = (
    "ORIGINAL_EVALUATION_ACCOUNTING_INCOMPLETE_OPEN_END_OF_WINDOW_POSITION_"
    "AND_WRONG_RECONCILIATION_IDENTITY"
)
TERMINAL_FAILURE_CLASS = "NEGATIVE_ECONOMIC_BASELINE_AND_INSUFFICIENT_TRADE_SAMPLE"
END_OF_WINDOW_POLICY = "force_close_at_window_end_inclusive_v0"
ACCOUNTING_FAILURE_CLASS = "FORCED_END_OF_WINDOW_LIQUIDATION"
ACCOUNTING_ROOT_CAUSE = (
    "open_position_at_window_end_without_force_close_trade_ledger_entry;"
    "wrong_reconciliation_identity"
)

BASELINE_VERDICT = "FAIL"
NET_RETURN = -0.1529057247280985
TRADE_COUNT = 4
SAMPLE_SUFFICIENCY_STATUS = "INSUFFICIENT_TRADE_SAMPLE"
WALK_FORWARD_STATUS = "NOT_EXECUTED_BASELINE_NEGATIVE"
MONTE_CARLO_STATUS = "NOT_EXECUTED_BASELINE_NEGATIVE"
STRESS_STATUS = "NOT_EXECUTED_BASELINE_NEGATIVE"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = "NEW_RATIFIED_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"

REQUIRED_CORRECTED_EVIDENCE_FILES = (
    "accounting_reconciliation.json",
    "baseline_results.json",
    "economic_viability_evidence_v1.json",
    "previous_vs_corrected_evaluation.json",
    "robustness_status.json",
    "sample_sufficiency.json",
    "superseded_evaluation_reference.json",
)

REQUIRED_ORIGINAL_EVIDENCE_FILES = (
    "accounting_reconciliation.json",
    "economic_viability_evidence_v1.json",
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


def validate_supersession_link(corrected_dir: Path, original_dir: Path) -> None:
    superseded_ref = _load_json(corrected_dir / "superseded_evaluation_reference.json")
    previous_vs = _load_json(corrected_dir / "previous_vs_corrected_evaluation.json")
    if Path(superseded_ref["superseded_bundle"]).resolve() != original_dir.resolve():
        raise ValueError("superseded_bundle_mismatch")
    if Path(previous_vs["superseded_evaluation_bundle"]).resolve() != original_dir.resolve():
        raise ValueError("previous_vs_superseded_bundle_mismatch")
    if corrected_dir.resolve() == original_dir.resolve():
        raise ValueError("canonical_equals_superseded")
    if superseded_ref.get("superseded_accounting_reconciliation_pass") is not False:
        raise ValueError("superseded_accounting_must_be_false")
    if previous_vs.get("binding_changed") is not False:
        raise ValueError("binding_changed_must_be_false")
    if previous_vs.get("trading_logic_changed") is not False:
        raise ValueError("trading_logic_changed_must_be_false")
    if previous_vs.get("cost_policy_changed") is not False:
        raise ValueError("cost_policy_changed_must_be_false")


def validate_registration_preconditions(
    *,
    original_dir: Path = ORIGINAL_EVALUATION_DIR,
    corrected_dir: Path = CORRECTED_EVALUATION_DIR,
    pr5080_closeout_dir: Path = PR5080_CLOSEOUT_DIR,
) -> tuple[EvidenceBundleValidation, EvidenceBundleValidation]:
    for bundle_dir, required_files in (
        (original_dir, REQUIRED_ORIGINAL_EVIDENCE_FILES),
        (corrected_dir, REQUIRED_CORRECTED_EVIDENCE_FILES),
    ):
        for name in required_files:
            if not (bundle_dir / name).is_file():
                raise ValueError(f"missing_required_evidence:{bundle_dir / name}")
    original = validate_evidence_bundle(original_dir, require_accounting_pass=False)
    corrected = validate_evidence_bundle(corrected_dir, require_accounting_pass=True)
    if original.manifest_digest == corrected.manifest_digest:
        raise ValueError("canonical_and_superseded_manifest_digest_equal")
    if not pr5080_closeout_dir.is_dir():
        raise ValueError(f"missing_pr5080_closeout:{pr5080_closeout_dir}")
    if verify_manifest_sha256(pr5080_closeout_dir) != 0:
        raise ValueError("pr5080_closeout_manifest_verify_failed")
    validate_supersession_link(corrected_dir, original_dir)
    return original, corrected


def _metrics_from_corrected(corrected_dir: Path) -> dict[str, Any]:
    economic = _load_json(corrected_dir / "economic_viability_evidence_v1.json")
    sample = _load_json(corrected_dir / "sample_sufficiency.json")
    robustness = _load_json(corrected_dir / "robustness_status.json")
    return {
        "net_return": economic["net_return"],
        "net_expectancy": economic["net_expectancy"],
        "profit_factor": economic["profit_factor"],
        "sharpe": economic["sharpe"],
        "sortino": economic["sortino"],
        "max_drawdown": economic["max_drawdown"],
        "calmar": economic["calmar"],
        "trade_count": economic["trade_count"],
        "turnover": economic["turnover"],
        "fee_drag": economic["fee_drag"],
        "funding_drag": economic["funding_drag"],
        "slippage_impact": economic["slippage_impact"],
        "sample_sufficiency_status": sample["status"],
        "walk_forward_status": robustness["walk_forward_status"],
        "monte_carlo_status": robustness["monte_carlo_status"],
        "stress_status": robustness["stress_status"],
        "reason_codes": economic.get("reason_codes", []),
    }


def materialize_registration_config(
    *,
    original: EvidenceBundleValidation,
    corrected: EvidenceBundleValidation,
    registration_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    metrics = _metrics_from_corrected(corrected.bundle_path)
    payload: dict[str, Any] = {
        "artifact_kind": REGISTRATION_ID,
        "artifact_version": REGISTRATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": OPERATOR_GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "binding_config_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_binding": STRATEGY_BINDING,
        "binding_digest": BINDING_DIGEST,
        "config_digest": CONFIG_DIGEST,
        "data_digest": DATA_DIGEST,
        "universe_digest": UNIVERSE_DIGEST,
        "ratification_digest": RATIFICATION_DIGEST,
        "canonical_evaluation_bundle": str(corrected.bundle_path),
        "canonical_evaluation_timestamp": CANONICAL_EVALUATION_TIMESTAMP,
        "canonical_manifest_digest": corrected.manifest_digest,
        "canonical_manifest_verify_rc": corrected.manifest_verify_rc,
        "superseded_evaluation_bundle": str(original.bundle_path),
        "superseded_evaluation_timestamp": SUPERSEDED_EVALUATION_TIMESTAMP,
        "superseded_manifest_digest": original.manifest_digest,
        "superseded_manifest_verify_rc": original.manifest_verify_rc,
        "supersession_reason": SUPERSESSION_REASON,
        "terminal_failure_class": TERMINAL_FAILURE_CLASS,
        "accounting_reconciliation_pass": True,
        "accounting_failure_class": ACCOUNTING_FAILURE_CLASS,
        "accounting_root_cause": ACCOUNTING_ROOT_CAUSE,
        "end_of_window_policy": END_OF_WINDOW_POLICY,
        "baseline_verdict": BASELINE_VERDICT,
        "net_return": metrics["net_return"],
        "trade_count": metrics["trade_count"],
        "sample_sufficiency_status": metrics["sample_sufficiency_status"],
        "walk_forward_status": metrics["walk_forward_status"],
        "monte_carlo_status": metrics["monte_carlo_status"],
        "stress_status": metrics["stress_status"],
        "economic_validity_offline_gate_pass": False,
        "retry_allowed_same_binding": False,
        "terminal_negative_evidence_for_unchanged_binding": True,
        "immutable_binding_retry_allowed": False,
        "unchanged_retry_allowed": False,
        "new_evidence_class_required_for_further_evaluation": True,
        "trading_logic_changed": False,
        "binding_changed": False,
        "dataset_changed": False,
        "cost_policy_changed": False,
        "no_economic_reevaluation": True,
        "no_parameter_change": True,
        "no_policy_rescue": True,
        "no_runtime_or_promotion_action": True,
        "promotion_granted": False,
        "runtime_authority_touched": False,
        "offline_only": True,
        "source_pr": SOURCE_PR,
        "source_merge_commit": SOURCE_MERGE_COMMIT,
        "pre_merge_origin_main": PRE_MERGE_ORIGIN_MAIN,
        "pr5080_closeout_dir": str(PR5080_CLOSEOUT_DIR),
        "economic_viability_evidence_ref": (f"{corrected.bundle_path} (MANIFEST_VERIFY_RC=0)"),
        "superseded_evaluation_ref": f"{original.bundle_path} (MANIFEST_VERIFY_RC=0)",
        "durable_evidence_refs": "; ".join(
            [
                f"{corrected.bundle_path} (MANIFEST_VERIFY_RC=0)",
                f"{original.bundle_path} (SUPERSEDED_MANIFEST_VERIFY_RC=0)",
                f"{PR5080_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0)",
            ]
        ),
        "metrics": metrics,
        "status": "TERMINAL_NEGATIVE_EVIDENCE_AND_SUPERSESSION_REGISTRATION_COMPLETE",
        "verdict": RegistrationVerdict.PASS.value,
        "terminal_economic_decision": BASELINE_VERDICT,
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
    updated["economic_evaluation_status"] = "COMPLETE_FAIL"
    updated["economic_validity_offline_gate_pass"] = False
    updated["promotion_eligible"] = False
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
    updated["baseline_verdict"] = BASELINE_VERDICT
    updated["sample_sufficiency_status"] = registration["sample_sufficiency_status"]
    updated["accounting_reconciliation_pass"] = True
    updated["terminal_negative_evidence_for_unchanged_binding"] = True
    updated["canonical_evaluation_timestamp"] = CANONICAL_EVALUATION_TIMESTAMP
    updated["superseded_evaluation_timestamp"] = SUPERSEDED_EVALUATION_TIMESTAMP
    updated["supersession_reason"] = SUPERSESSION_REASON
    updated["superseded_evaluation_bundle"] = registration["superseded_evaluation_bundle"]
    updated["canonical_evaluation_bundle"] = registration["canonical_evaluation_bundle"]
    updated["economic_viability_evidence_ref"] = registration["economic_viability_evidence_ref"]
    updated["economic_viability_evidence_manifest_digest"] = registration[
        "canonical_manifest_digest"
    ]
    updated["superseded_evaluation_manifest_digest"] = registration["superseded_manifest_digest"]
    updated["superseded_evaluation_ref"] = registration["superseded_evaluation_ref"]
    updated["durable_evidence_refs"] = registration["durable_evidence_refs"]
    updated["source_pr"] = SOURCE_PR
    updated["source_merge_commit"] = SOURCE_MERGE_COMMIT
    updated["terminal_failure_class"] = TERMINAL_FAILURE_CLASS
    updated["walk_forward_status"] = registration["walk_forward_status"]
    updated["monte_carlo_status"] = registration["monte_carlo_status"]
    updated["stress_status"] = registration["stress_status"]
    updated["economic_evaluation_reason_codes"] = registration["metrics"]["reason_codes"]
    return updated
