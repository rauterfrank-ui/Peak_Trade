"""Terminal inconclusive registration and distinct futures research scope definition for Ehlers v1.

Offline-only ratification slice: registers post-repair inconclusive baseline as terminal for the
exact unchanged binding, blocks same-binding retry, and defines one materially distinct futures-only
successor scope without economic evaluation or runtime authority.
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
    "EHLERS_CYCLE_FILTER_V1_TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE_AND_"
    "DISTINCT_FUTURES_RESEARCH_SCOPE_DEFINITION_V0=true"
)
SCHEMA_VERSION = (
    "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
    "distinct_futures_research_scope_definition.v0"
)
REGISTRATION_ID = (
    "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
    "distinct_futures_research_scope_definition_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_TERMINAL_INCONCLUSIVE_REGISTRATION_AND_"
    "DISTINCT_RESEARCH_SCOPE_DEFINITION_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_REGISTER_TERMINAL_INCONCLUSIVE_EHLERS_CYCLE_FILTER_V1_SAME_BINDING_"
    "AND_AUTHORIZE_DISTINCT_FUTURES_RESEARCH_SCOPE_DEFINITION_READ_ONLY_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "ehlers_cycle_filter_v1_terminal_inconclusive_insufficient_sample_and_"
    "distinct_futures_research_scope_definition_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "EHLERS_CYCLE_FILTER_V1_TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE_AND_"
    "DISTINCT_FUTURES_RESEARCH_SCOPE_DEFINITION_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json"
)

STRATEGY_ID = "ehlers_cycle_filter"
STRATEGY_VERSION = "v1"
RESEARCH_SCOPE = "ehlers_cycle_filter/v1"
STRATEGY_BINDING = RESEARCH_SCOPE

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_CLASSIFICATION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/classify_ehlers_cycle_filter_v1_inconclusive_baseline_cause_and_decide_"
    "distinct_research_scope_read_only_v0_20260710T123447Z"
)
PRE_REPAIR_CLASSIFICATION_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/classify_ehlers_cycle_filter_v1_baseline_inconclusive_cause_read_only_v0_"
    "20260710T110612Z"
)
CANONICAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0_"
    "20260710T115835Z"
)
PR5086_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5086_merge_closeout_ehlers_cycle_filter_v1_bound_offline_evaluation_"
    "runner_invocation_contract_repair_v0_20260710T123119Z"
)
DISCOVERY_EVIDENCE_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_"
    "read_only_v0_20260710T104236Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260710T115835Z"
PRE_REPAIR_CLASSIFICATION_TIMESTAMP = "20260710T110612Z"
POST_REPAIR_CLASSIFICATION_TIMESTAMP = "20260710T123447Z"
SOURCE_PR = 5086
PRE_MERGE_ORIGIN_MAIN = "f1117437a0bdfac8196d0ceffadc746d0b2b367e"

BINDING_DIGEST = "dc8704495c3bf08b14afd9f50890369973c7c785e0d1655ba0b5b351f06b6599"
IMPLEMENTATION_DIGEST = "4ec22ab14c7fa0923de83bfe89a6606514246d02b0045af28ff2d6cbe874fb34"
CONFIG_DIGEST = "c4db0a42b95156192d8c1fcf486aa3d616ae2f0b5dafa26b9e0d7d9a29c204a6"
DATA_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
STRATEGY_PARAMS_DIGEST = "49f8b07e7de872e66f74dd27b5e97a3ae3aaee414e25d3b08cba2674c40cc5b9"
MATERIAL_DIFFERENCE_DIGEST = "d96140d32c9eee87e35f6f97aaba357d1d6495395a43671960c77ad8f1ceaf1f"
CANONICAL_MANIFEST_DIGEST = "acd5a8a16e096904a1610ef3e45067488164a4c5b41a80f93de6416bb398e2b4"
CLASSIFICATION_MANIFEST_DIGEST = "3be386861653a15b4d4174f4e09be36e9667b116f0f9574bd966371587e6d5b9"

PRIMARY_CAUSE_CLASS = "SIGNAL_STARVATION_BY_CANONICAL_LOGIC_WITH_INSUFFICIENT_TRADE_SAMPLE"
TERMINAL_STATUS = "TERMINAL_INCONCLUSIVE_INSUFFICIENT_SAMPLE"
TERMINAL_FAILURE_CLASS = "INCONCLUSIVE_BASELINE_INSUFFICIENT_TRADE_SAMPLE"
BASELINE_VERDICT = "INCONCLUSIVE"
NET_RETURN = -0.020939974776106464
TRADE_COUNT = 6
POLICY_MINIMUM_TRADE_COUNT = 50
SAMPLE_SUFFICIENCY_STATUS = "INSUFFICIENT_TRADE_SAMPLE"

SELECTED_DISTINCT_SCOPE = "el_karoui_vol_model/v1"
SELECTED_DISTINCT_STRATEGY_ID = "el_karoui_vol_model"
SELECTED_DISTINCT_STRATEGY_VERSION = "v1"
SELECTED_DISTINCT_HYPOTHESIS_ID = "EL_KAROUI_STOCHASTIC_VOL_REGIME_NON_BITCOIN_FUTURES_V1"
SELECTED_DISTINCT_EVIDENCE_CLASS_ID = (
    "EL_KAROUI_VOL_MODEL_V1_FULL_CANONICAL_OFFLINE_BASELINE_ECONOMIC_EVALUATION_V0"
)
SELECTED_DISTINCT_CANONICAL_OWNER = "src/strategies/el_karoui/el_karoui_vol_model_strategy.py"
SELECTED_DISTINCT_SIGNAL_FAMILY = "STOCHASTIC_VOL_REGIME"
DISCOVERY_RANK = 2

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = (
    "GO_RATIFY_EL_KAROUI_VOL_MODEL_V1_VERSIONED_RESEARCH_BINDING_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NO_RUNTIME_AUTHORITY_V0"
)
NEXT_GO_TOKEN = (
    "GO_RATIFY_EL_KAROUI_VOL_MODEL_V1_VERSIONED_RESEARCH_BINDING_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NO_RUNTIME_AUTHORITY_V0"
)

REQUIRED_CANONICAL_EVIDENCE_FILES = (
    "accounting_reconciliation.json",
    "final_report.txt",
    "immutable_binding_snapshot.json",
    "performance_metrics.json",
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
    classification_dir: Path = SOURCE_CLASSIFICATION_EVIDENCE_DIR,
    pre_repair_classification_dir: Path = PRE_REPAIR_CLASSIFICATION_EVIDENCE_DIR,
    pr5086_closeout_dir: Path = PR5086_CLOSEOUT_DIR,
    discovery_dir: Path = DISCOVERY_EVIDENCE_DIR,
) -> EvidenceBundleValidation:
    for bundle_dir, required_files in ((canonical_dir, REQUIRED_CANONICAL_EVIDENCE_FILES),):
        for name in required_files:
            if not (bundle_dir / name).is_file():
                raise ValueError(f"missing_required_evidence:{bundle_dir / name}")
    for bundle_dir in (
        classification_dir,
        pre_repair_classification_dir,
        pr5086_closeout_dir,
        discovery_dir,
    ):
        if verify_manifest_sha256(bundle_dir) != 0:
            raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    canonical = validate_evidence_bundle(canonical_dir, require_accounting_pass=True)
    binding_snapshot = _load_json(canonical_dir / "immutable_binding_snapshot.json")
    if binding_snapshot.get("binding_digest") != BINDING_DIGEST:
        raise ValueError("binding_digest_mismatch")
    if binding_snapshot.get("implementation_digest") != IMPLEMENTATION_DIGEST:
        raise ValueError("implementation_digest_mismatch")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    if int(sample.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("trade_count_mismatch")
    if sample.get("status") != SAMPLE_SUFFICIENCY_STATUS:
        raise ValueError("sample_sufficiency_status_mismatch")
    performance = _load_json(canonical_dir / "performance_metrics.json")
    if int(performance.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("performance_trade_count_mismatch")
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


def is_materially_distinct_scope_admissible(selected_scope: str) -> bool:
    if selected_scope == RESEARCH_SCOPE:
        return False
    if selected_scope == SELECTED_DISTINCT_SCOPE:
        return True
    return selected_scope != RESEARCH_SCOPE


def _metrics_from_canonical(canonical_dir: Path) -> dict[str, Any]:
    performance = _load_json(canonical_dir / "performance_metrics.json")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    return {
        "net_return": performance["net_return"],
        "net_expectancy": performance.get("net_expectancy", 0.0),
        "profit_factor": performance["profit_factor"],
        "sharpe": performance["sharpe"],
        "max_drawdown": performance["max_drawdown"],
        "trade_count": performance["trade_count"],
        "sample_sufficiency_status": sample["status"],
        "policy_minimum_trade_count": sample.get("minimum_trade_count_policy", 50),
        "walk_forward_status": "NOT_EXECUTED_BASELINE_INCONCLUSIVE",
        "monte_carlo_status": "NOT_EXECUTED_BASELINE_INCONCLUSIVE",
        "stress_status": "NOT_EXECUTED_BASELINE_INCONCLUSIVE",
    }


def build_distinct_scope_candidate_inventory() -> dict[str, Any]:
    return {
        "schema_version": "distinct_scope_candidate_inventory.v0",
        "source_discovery_evidence_dir": str(DISCOVERY_EVIDENCE_DIR),
        "candidates": [
            {
                "research_scope": RESEARCH_SCOPE,
                "status": "TERMINAL_INCONCLUSIVE_SOURCE_NOT_CANDIDATE",
                "rejected": True,
                "rejection_reason": "SOURCE_BINDING_TERMINAL_INCONCLUSIVE",
            },
            {
                "research_scope": SELECTED_DISTINCT_SCOPE,
                "strategy_id": SELECTED_DISTINCT_STRATEGY_ID,
                "strategy_version": SELECTED_DISTINCT_STRATEGY_VERSION,
                "hypothesis_id": SELECTED_DISTINCT_HYPOTHESIS_ID,
                "discovery_rank": DISCOVERY_RANK,
                "status": "SELECTED",
                "rejected": False,
                "material_difference_proven": True,
            },
            {
                "research_scope": "ehlers_cycle_filter/v1@extended_window_only",
                "status": "REJECTED",
                "rejected": True,
                "rejection_reason": "LONGER_WINDOW_ONLY_WITHOUT_NEW_HYPOTHESIS",
            },
            {
                "research_scope": "cross_sectional_ma_crossover_panel_rank_rotation/v0",
                "status": "REJECTED",
                "rejected": True,
                "rejection_reason": "TERMINAL_NEGATIVE_ALREADY_REGISTERED",
            },
            {
                "research_scope": "vol_breakout/v1",
                "status": "REJECTED",
                "rejected": True,
                "rejection_reason": "TERMINAL_NEGATIVE_ALREADY_REGISTERED",
            },
        ],
    }


def build_material_difference_matrix() -> dict[str, Any]:
    return {
        "schema_version": "material_difference_matrix.v0",
        "baseline_scope": RESEARCH_SCOPE,
        "selected_scope": SELECTED_DISTINCT_SCOPE,
        "rows": [
            {
                "axis": "signal_mechanism",
                "baseline": "DSP super-smoother price crossover (close > smoothed)",
                "selected": "Realized-vol percentile regime classification (LOW/MEDIUM/HIGH)",
                "material_difference": True,
            },
            {
                "axis": "instrument_universe",
                "baseline": "Single instrument inst-eth-usdt-perp OKX futures",
                "selected": "Single instrument inst-eth-usdt-perp OKX futures (initial binding)",
                "material_difference": False,
                "note": "Same initial instrument allowed; signal mechanism differs",
            },
            {
                "axis": "bar_interval",
                "baseline": "1m",
                "selected": "1m (initial hypothesis binding)",
                "material_difference": False,
                "note": "Interval match does not collapse signal-family difference",
            },
            {
                "axis": "dataset_identity",
                "baseline": "inst-eth-usdt-perp_v1 point-in-time 1m bars",
                "selected": "Separate versioned binding required before reuse",
                "material_difference": True,
                "note": "Distinct evidence class and ratification required even if dataset reused",
            },
            {
                "axis": "portfolio_cross_sectional_semantics",
                "baseline": "Direct single-slot timing",
                "selected": "Direct single-slot vol-regime exposure",
                "material_difference": True,
            },
            {
                "axis": "entry_exit_semantics",
                "baseline": "Binary long/flat on price-vs-smooth rule with fixed stop",
                "selected": "Regime-threshold exposure mapping with vol-target scaling",
                "material_difference": True,
            },
            {
                "axis": "expected_opportunity_mechanism",
                "baseline": "Cycle-bandpass timing on smoothed price structure",
                "selected": "Vol-regime risk-on/risk-off and mean-reverting vol dynamics",
                "material_difference": True,
            },
            {
                "axis": "prior_evidence",
                "baseline": "Post-repair inconclusive baseline evaluation complete",
                "selected": "Discovery rank-2; no economic evaluation executed",
                "material_difference": True,
            },
            {
                "axis": "duplicate_near_duplicate_risk",
                "baseline": "N/A",
                "selected": "LOW",
                "material_difference": True,
            },
        ],
        "material_difference_proven": True,
        "material_difference_basis": "DISTINCT_SIGNAL_COMPOSITION_AND_DISTINCT_EVIDENCE_CLASS",
    }


def build_prior_classification_supersession_map() -> dict[str, Any]:
    return {
        "schema_version": "prior_classification_supersession_map.v0",
        "entries": [
            {
                "classification_timestamp": PRE_REPAIR_CLASSIFICATION_TIMESTAMP,
                "classification_bundle": str(PRE_REPAIR_CLASSIFICATION_EVIDENCE_DIR),
                "primary_verdict": "COMBINED_ACCOUNTING_DEFECT_AND_SAMPLE_INSUFFICIENCY",
                "superseded_by": POST_REPAIR_CLASSIFICATION_TIMESTAMP,
                "supersession_reason": "DEFECT_REPAIR_REEVALUATION_COMPLETED",
                "still_authoritative_for_retry": False,
            },
            {
                "classification_timestamp": POST_REPAIR_CLASSIFICATION_TIMESTAMP,
                "classification_bundle": str(SOURCE_CLASSIFICATION_EVIDENCE_DIR),
                "primary_verdict": "SIGNAL_STARVATION_BY_CANONICAL_LOGIC_WITH_INSUFFICIENT_TRADE_SAMPLE",
                "superseded_by": None,
                "supersession_reason": None,
                "still_authoritative_for_retry": False,
                "terminal_registration_authoritative": True,
            },
        ],
    }


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
        "distinct_scope_admissible": is_materially_distinct_scope_admissible(
            SELECTED_DISTINCT_SCOPE
        ),
        "blocked_retry_axes": [
            "UNCHANGED_BINDING_RETRY",
            "SAME_BINDING_RETRY",
            "LONGER_WINDOW_ONLY_WITHOUT_NEW_HYPOTHESIS",
            "THRESHOLD_LOWERING",
            "POLICY_RESCUE",
            "POST_RESULT_PARAMETER_CHANGE",
        ],
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
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_binding": STRATEGY_BINDING,
        "binding_digest": BINDING_DIGEST,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "config_digest": CONFIG_DIGEST,
        "data_digest": DATA_DIGEST,
        "strategy_params_digest": STRATEGY_PARAMS_DIGEST,
        "material_difference_digest": MATERIAL_DIFFERENCE_DIGEST,
        "canonical_evaluation_bundle": str(canonical.bundle_path),
        "canonical_evaluation_timestamp": CANONICAL_EVALUATION_TIMESTAMP,
        "canonical_manifest_digest": canonical.manifest_digest,
        "canonical_manifest_verify_rc": canonical.manifest_verify_rc,
        "source_classification_evidence_dir": str(SOURCE_CLASSIFICATION_EVIDENCE_DIR),
        "source_classification_manifest_digest": CLASSIFICATION_MANIFEST_DIGEST,
        "pre_repair_classification_evidence_dir": str(PRE_REPAIR_CLASSIFICATION_EVIDENCE_DIR),
        "pre_repair_classification_timestamp": PRE_REPAIR_CLASSIFICATION_TIMESTAMP,
        "post_repair_classification_timestamp": POST_REPAIR_CLASSIFICATION_TIMESTAMP,
        "primary_cause_class": PRIMARY_CAUSE_CLASS,
        "terminal_status": TERMINAL_STATUS,
        "terminal_failure_class": TERMINAL_FAILURE_CLASS,
        "accounting_reconciliation_pass": True,
        "baseline_verdict": BASELINE_VERDICT,
        "terminal_economic_decision": BASELINE_VERDICT,
        "net_return": metrics["net_return"],
        "trade_count": metrics["trade_count"],
        "policy_minimum_trade_count": metrics["policy_minimum_trade_count"],
        "sample_sufficiency_status": metrics["sample_sufficiency_status"],
        "walk_forward_status": metrics["walk_forward_status"],
        "monte_carlo_status": metrics["monte_carlo_status"],
        "stress_status": metrics["stress_status"],
        "economic_validity_offline_gate_pass": False,
        "retry_allowed_same_binding": False,
        "same_binding_retry_allowed": False,
        "unchanged_retry_blocked": True,
        "immutable_binding_retry_allowed": False,
        "terminal_negative_evidence_for_unchanged_binding": False,
        "terminal_inconclusive_evidence_for_unchanged_binding": True,
        "distinct_scope_required": True,
        "selected_distinct_scope": SELECTED_DISTINCT_SCOPE,
        "selected_distinct_strategy_id": SELECTED_DISTINCT_STRATEGY_ID,
        "selected_distinct_strategy_version": SELECTED_DISTINCT_STRATEGY_VERSION,
        "selected_distinct_hypothesis_id": SELECTED_DISTINCT_HYPOTHESIS_ID,
        "selected_distinct_evidence_class_id": SELECTED_DISTINCT_EVIDENCE_CLASS_ID,
        "selected_distinct_canonical_owner": SELECTED_DISTINCT_CANONICAL_OWNER,
        "material_difference_proven": True,
        "distinct_scope_ratified": True,
        "distinct_scope_implemented": True,
        "distinct_scope_candidate_inventory": build_distinct_scope_candidate_inventory(),
        "material_difference_matrix": build_material_difference_matrix(),
        "prior_classification_supersession_map": build_prior_classification_supersession_map(),
        "exact_binding_retry_guard_report": build_exact_binding_retry_guard_report(),
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
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "source_pr": SOURCE_PR,
        "pre_merge_origin_main": PRE_MERGE_ORIGIN_MAIN,
        "pr5086_closeout_dir": str(PR5086_CLOSEOUT_DIR),
        "discovery_evidence_dir": str(DISCOVERY_EVIDENCE_DIR),
        "durable_evidence_refs": "; ".join(
            [
                f"{canonical.bundle_path} (MANIFEST_VERIFY_RC=0)",
                f"{SOURCE_CLASSIFICATION_EVIDENCE_DIR} (MANIFEST_VERIFY_RC=0)",
                f"{PR5086_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0)",
            ]
        ),
        "metrics": metrics,
        "status": "TERMINAL_INCONCLUSIVE_REGISTRATION_AND_DISTINCT_SCOPE_DEFINITION_COMPLETE",
        "verdict": RegistrationVerdict.PASS.value,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "next_go_token": NEXT_GO_TOKEN,
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
    updated["terminal_negative_evidence_for_unchanged_binding"] = False
    updated["terminal_inconclusive_evidence_for_unchanged_binding"] = True
    updated["terminal_status"] = TERMINAL_STATUS
    updated["primary_cause_class"] = PRIMARY_CAUSE_CLASS
    updated["canonical_evaluation_timestamp"] = CANONICAL_EVALUATION_TIMESTAMP
    updated["canonical_evaluation_bundle"] = registration["canonical_evaluation_bundle"]
    updated["economic_viability_evidence_ref"] = (
        f"{registration['canonical_evaluation_bundle']} (MANIFEST_VERIFY_RC=0)"
    )
    updated["economic_viability_evidence_manifest_digest"] = registration[
        "canonical_manifest_digest"
    ]
    updated["classification_evidence_ref"] = (
        f"{registration['source_classification_evidence_dir']} (MANIFEST_VERIFY_RC=0)"
    )
    updated["durable_evidence_refs"] = registration["durable_evidence_refs"]
    updated["terminal_failure_class"] = TERMINAL_FAILURE_CLASS
    updated["walk_forward_status"] = registration["walk_forward_status"]
    updated["monte_carlo_status"] = registration["monte_carlo_status"]
    updated["stress_status"] = registration["stress_status"]
    updated["unchanged_retry_blocked"] = True
    updated["distinct_scope_required"] = True
    updated["selected_distinct_scope"] = SELECTED_DISTINCT_SCOPE
    updated["selected_distinct_scope_ratified"] = True
    updated["binding_digest_at_terminal_registration"] = BINDING_DIGEST
    updated["implementation_digest_at_terminal_registration"] = IMPLEMENTATION_DIGEST
    return updated
