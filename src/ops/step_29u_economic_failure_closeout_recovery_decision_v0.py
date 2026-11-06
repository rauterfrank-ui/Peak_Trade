"""STEP 29U Economic Failure Closeout and Recovery Decision v0.

Offline, fail-closed closeout of truthful economic FAIL for Step-29U activation
eligibility. Produces a machine-readable failure-cause inventory and an
operator decision inventory of admissible recovery options.

Reuses existing canonical authorities only:
- ops.step_29u_economic_validity_readiness_v0
- ops.step_29u_audit_provenance_v0
- ops.step_29u_activation_eligibility_inventory_v0 (activation ineligibility)
- config/research/post_pr4940_final_research_fleet_negative_evidence_...
- config/ops/shadow_preparation_readiness_gate_v0.toml
- sealed Step-29U economic readiness evidence (PR #5553)

Does not activate Step 29U, invent thresholds, recompute metrics, select or
execute a recovery option, or authorize Runtime/Scheduler/Network/Orders.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.backtest.economic_validity_policy_v1 import (
    ECONOMIC_VALIDITY_POLICY_OWNER,
    ECONOMIC_VALIDITY_POLICY_VERSION,
)
from src.ops.step_29u_activation_eligibility_inventory_v0 import (
    evaluate_step_29u_activation_eligibility_inventory_v0,
)
from src.ops.step_29u_audit_provenance_v0 import (
    STATUS_COMPLETE as AUDIT_STATUS_COMPLETE,
    evaluate_step_29u_audit_provenance_v0,
)
from src.ops.step_29u_economic_validity_readiness_v0 import (
    CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
    READINESS_CONFIG_RELPATH,
    STATUS_CONTRADICTORY as ECON_STATUS_CONTRADICTORY,
    STATUS_FAIL as ECON_STATUS_FAIL,
    STATUS_PASS as ECON_STATUS_PASS,
    EconomicValidityReadinessOverridesV0,
    evaluate_step_29u_economic_validity_readiness_v0,
)

PACKAGE_MARKER = "STEP_29U_ECONOMIC_FAILURE_CLOSEOUT_RECOVERY_DECISION_V0=true"
PRODUCER_FAMILY = "ops.step_29u_economic_failure_closeout_recovery_decision_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_ECONOMIC_FAILURE_CLOSEOUT_RECOVERY_DECISION_V0"

SEALED_ECONOMIC_READINESS_EVIDENCE_RELPATH = (
    "evidence/ops/step_29u_activation_evidence_economic_readiness/20260726T011500Z_local_pre_pr"
)
SEALED_ECONOMIC_RESULT_RELPATH = (
    f"{SEALED_ECONOMIC_READINESS_EVIDENCE_RELPATH}/economic_validity_result.json"
)
SEALED_COMPOSED_RESULT_RELPATH = (
    f"{SEALED_ECONOMIC_READINESS_EVIDENCE_RELPATH}/composed_eligibility_result.json"
)
GOVERNANCE_TERMINAL_BOUNDARY_RELPATH = (
    "docs/governance/POST_PR4939_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_"
    "TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_V0.md"
)
GOVERNANCE_MATERIAL_DIFFERENT_PREP_RELPATH = (
    "docs/governance/POST_PR4941_MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_"
    "SCOPE_DISCOVERY_AND_RATIFICATION_PREP_V0.md"
)

CLOSEOUT_COMPLETE = "COMPLETE"
CLOSEOUT_INCOMPLETE = "INCOMPLETE"

OPTION_ELIGIBLE = "ELIGIBLE_FOR_OPERATOR_SELECTION"
OPTION_BLOCKED = "BLOCKED"

FORBIDDEN_IMPORT_SURFACES = frozenset(
    {
        "src.runtime",
        "src.scheduler",
        "src.exchange",
        "src.broker",
        "src.orders",
        "src.live",
        "src.paper",
        "src.testnet",
    }
)


class Step29UEconomicFailureCloseoutError(ValueError):
    """Fail-closed economic failure closeout error."""


@dataclass(frozen=True)
class FailureCauseEntryV0:
    failed_gate_or_metric: str
    observed_value: Any
    required_threshold: Any
    sample_panel_identity: Any
    cost_assumptions: Any
    trade_count: Any
    confidence_or_evidence_quality_limitation: str
    failure_classification: str
    canonical_evidence_reference: str
    terminal_for_tested_hypothesis: bool
    further_research_technically_permitted: bool
    operator_selection_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "failed_gate_or_metric": self.failed_gate_or_metric,
            "observed_value": self.observed_value,
            "required_threshold": self.required_threshold,
            "sample_panel_identity": self.sample_panel_identity,
            "cost_assumptions": self.cost_assumptions,
            "trade_count": self.trade_count,
            "confidence_or_evidence_quality_limitation": (
                self.confidence_or_evidence_quality_limitation
            ),
            "failure_classification": self.failure_classification,
            "canonical_evidence_reference": self.canonical_evidence_reference,
            "terminal_for_tested_hypothesis": self.terminal_for_tested_hypothesis,
            "further_research_technically_permitted": (self.further_research_technically_permitted),
            "operator_selection_required": self.operator_selection_required,
        }


@dataclass(frozen=True)
class RecoveryOptionEntryV0:
    option_id: str
    objective: str
    exact_evidence_gap_addressed: str
    prerequisites: tuple[str, ...]
    expected_production_files: tuple[str, ...]
    expected_tests: tuple[str, ...]
    expected_ci_impact: str
    runtime_network_order_impact: str
    risks: tuple[str, ...]
    explicit_non_goals: tuple[str, ...]
    operator_visible_value: str
    status: str
    blocked_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "option_id": self.option_id,
            "objective": self.objective,
            "exact_evidence_gap_addressed": self.exact_evidence_gap_addressed,
            "prerequisites": list(self.prerequisites),
            "expected_production_files": list(self.expected_production_files),
            "expected_tests": list(self.expected_tests),
            "expected_ci_impact": self.expected_ci_impact,
            "runtime_network_order_impact": self.runtime_network_order_impact,
            "risks": list(self.risks),
            "explicit_non_goals": list(self.explicit_non_goals),
            "operator_visible_value": self.operator_visible_value,
            "status": self.status,
        }
        if self.blocked_reason is not None:
            out["blocked_reason"] = self.blocked_reason
        return out


@dataclass(frozen=True)
class EconomicFailureCloseoutResultV0:
    schema_id: str
    schema_version: str
    generated_at: str
    capability_id: str
    status: str
    evaluator_valid: bool
    economic_closeout_status: str
    audit_provenance_status: str
    economic_validity_status: str
    economic_validity_proven: bool
    activation_eligible: bool
    step_29u_activated: bool
    automatic_next_research_action_allowed: bool
    operator_selection_required: bool
    selected_recovery_option_id: Optional[str]
    canonical_blockers: tuple[str, ...]
    canonical_economic_evidence: tuple[Mapping[str, Any], ...]
    failure_cause_inventory: tuple[FailureCauseEntryV0, ...]
    recovery_option_inventory: tuple[RecoveryOptionEntryV0, ...]
    reasons: tuple[str, ...]
    provenance: Mapping[str, Any]
    safety_facts: Mapping[str, Any] = field(default_factory=dict)
    inputs: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "capability_id": self.capability_id,
            "status": self.status,
            "evaluator_valid": self.evaluator_valid,
            "economic_closeout_status": self.economic_closeout_status,
            "audit_provenance_status": self.audit_provenance_status,
            "economic_validity_status": self.economic_validity_status,
            "economic_validity_proven": self.economic_validity_proven,
            "activation_eligible": self.activation_eligible,
            "step_29u_activated": self.step_29u_activated,
            "automatic_next_research_action_allowed": (self.automatic_next_research_action_allowed),
            "operator_selection_required": self.operator_selection_required,
            "selected_recovery_option_id": self.selected_recovery_option_id,
            "canonical_blockers": list(self.canonical_blockers),
            "canonical_economic_evidence": [dict(x) for x in self.canonical_economic_evidence],
            "failure_cause_inventory": [e.to_dict() for e in self.failure_cause_inventory],
            "recovery_option_inventory": [o.to_dict() for o in self.recovery_option_inventory],
            "reasons": list(self.reasons),
            "provenance": dict(self.provenance),
            "safety_facts": dict(self.safety_facts),
            "inputs": dict(self.inputs),
        }


@dataclass(frozen=True)
class EconomicFailureCloseoutOverridesV0:
    fleet_closeout_path: Optional[Path] = None
    readiness_config_path: Optional[Path] = None
    sealed_economic_result_path: Optional[Path] = None
    sealed_composed_result_path: Optional[Path] = None
    force_economic_status: Optional[str] = None
    overlay_gate_pass: Optional[bool] = None
    overlay_fleet_verdict: Optional[str] = None
    claim_auto_select_recovery: bool = False
    claim_activation_eligible: bool = False
    claim_economic_ready_from_audit_complete: bool = False


def default_repo_root_v0() -> Path:
    return Path(__file__).resolve().parents[2]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Step29UEconomicFailureCloseoutError(f"JSON_MALFORMED:{path}:{exc}") from exc
    except OSError as exc:
        raise Step29UEconomicFailureCloseoutError(f"JSON_UNREADABLE:{path}:{exc}") from exc


def _evidence_ref(
    *,
    relpath: str,
    digest: Optional[str],
    schema_version: Optional[str],
    provenance_note: str,
) -> dict[str, Any]:
    return {
        "relpath": relpath,
        "sha256": digest,
        "schema_version": schema_version,
        "provenance_note": provenance_note,
    }


def _build_failure_cause_inventory(
    *,
    fleet: Mapping[str, Any],
    fleet_relpath: str,
    econ_status: str,
) -> tuple[FailureCauseEntryV0, ...]:
    panel = fleet.get("final_research_fleet")
    sample_panel_identity = (
        panel if isinstance(panel, list) else "NOT_PRESENT_IN_CANONICAL_CLOSEOUT"
    )
    terminal = fleet.get("negative_evidence_terminal_for_unchanged_bindings") is True
    further_permitted = (
        str(fleet.get("next_admissible_boundary") or "").strip()
        == "MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_OR_RATIFICATION_ONLY_NO_EVAL"
    )
    classes = fleet.get("confirmed_failure_classes")
    axes = fleet.get("confirmed_failure_axes")
    candidates = fleet.get("candidate_results")
    entries: list[FailureCauseEntryV0] = []

    entries.append(
        FailureCauseEntryV0(
            failed_gate_or_metric="economic_validity_offline_gate_pass",
            observed_value=fleet.get("economic_validity_offline_gate_pass"),
            required_threshold=True,
            sample_panel_identity=sample_panel_identity,
            cost_assumptions="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
            trade_count="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
            confidence_or_evidence_quality_limitation=(
                "CLOSEOUT_BINDS_TERMINAL_FLEET_FAIL_WITHOUT_PER_METRIC_RECOMPUTE"
            ),
            failure_classification=str(fleet.get("fleet_verdict") or econ_status),
            canonical_evidence_reference=fleet_relpath,
            terminal_for_tested_hypothesis=terminal,
            further_research_technically_permitted=further_permitted,
            operator_selection_required=True,
        )
    )

    if isinstance(classes, list):
        for cls in classes:
            entries.append(
                FailureCauseEntryV0(
                    failed_gate_or_metric=str(cls),
                    observed_value="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    required_threshold="BOUND_BY_economic_validity_policy_v1",
                    sample_panel_identity=sample_panel_identity,
                    cost_assumptions="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    trade_count="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    confidence_or_evidence_quality_limitation=(
                        "CLASS_CONFIRMED_IN_FLEET_CLOSEOUT_WITHOUT_NUMERIC_OBSERVED_VALUE"
                    ),
                    failure_classification=str(cls),
                    canonical_evidence_reference=fleet_relpath,
                    terminal_for_tested_hypothesis=terminal,
                    further_research_technically_permitted=further_permitted,
                    operator_selection_required=True,
                )
            )

    if isinstance(axes, list):
        for axis in axes:
            entries.append(
                FailureCauseEntryV0(
                    failed_gate_or_metric=str(axis),
                    observed_value="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    required_threshold="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    sample_panel_identity=sample_panel_identity,
                    cost_assumptions="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    trade_count="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    confidence_or_evidence_quality_limitation=(
                        "AXIS_CONFIRMED_IN_FLEET_CLOSEOUT_NO_CAUSAL_INFERENCE_ADDED"
                    ),
                    failure_classification=str(axis),
                    canonical_evidence_reference=fleet_relpath,
                    terminal_for_tested_hypothesis=terminal,
                    further_research_technically_permitted=further_permitted,
                    operator_selection_required=True,
                )
            )

    if isinstance(candidates, dict):
        for strategy_id, verdict in sorted(candidates.items()):
            entries.append(
                FailureCauseEntryV0(
                    failed_gate_or_metric=f"candidate_result:{strategy_id}",
                    observed_value=str(verdict),
                    required_threshold="PASS",
                    sample_panel_identity=strategy_id,
                    cost_assumptions="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    trade_count="NOT_PRESENT_IN_CANONICAL_CLOSEOUT",
                    confidence_or_evidence_quality_limitation=(
                        "PER_CANDIDATE_VERDICT_ONLY_NO_METRIC_TABLE_IN_CLOSEOUT"
                    ),
                    failure_classification=str(verdict),
                    canonical_evidence_reference=fleet_relpath,
                    terminal_for_tested_hypothesis=terminal,
                    further_research_technically_permitted=further_permitted,
                    operator_selection_required=True,
                )
            )

    return tuple(entries)


def _build_recovery_option_inventory(
    *,
    fleet: Mapping[str, Any],
) -> tuple[RecoveryOptionEntryV0, ...]:
    admissible_tokens = fleet.get("admissible_next_go_tokens")
    if not isinstance(admissible_tokens, list):
        admissible_tokens = []
    required_next_go = str(fleet.get("required_next_go_for_material_scope") or "")
    blocked_actions = fleet.get("blocked_actions")
    if not isinstance(blocked_actions, list):
        blocked_actions = []
    blocked_set = {str(x) for x in blocked_actions}
    raw_classes = fleet.get("confirmed_failure_classes")
    failure_classes = {str(x) for x in raw_classes} if isinstance(raw_classes, list) else set()
    raw_axes = fleet.get("confirmed_failure_axes")
    failure_axes = {str(x) for x in raw_axes} if isinstance(raw_axes, list) else set()

    options: list[RecoveryOptionEntryV0] = []

    # 1) Retire terminal unchanged final-fleet hypotheses (already terminalized).
    options.append(
        RecoveryOptionEntryV0(
            option_id="RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES",
            objective=(
                "Operator-acknowledge terminal retirement of unchanged final "
                "research fleet bindings after durable FLEET_ECONOMIC_VALIDITY_FAIL."
            ),
            exact_evidence_gap_addressed=(
                "Operator decision surface for already-bound "
                "NEGATIVE_EVIDENCE_TERMINAL_FOR_UNCHANGED_BINDINGS"
            ),
            prerequisites=(
                "CANONICAL_FLEET_FAIL_CLOSEOUT_PRESENT",
                "ECONOMIC_VALIDITY_STATUS_FAIL",
                "EXPLICIT_OPERATOR_SELECTION",
            ),
            expected_production_files=(
                "docs/ops/roadmap/CURRENT_FOCUS.md",
                "docs/ops/EVIDENCE_INDEX.md",
            ),
            expected_tests=(
                "tests/ops/test_step_29u_economic_failure_closeout_recovery_decision_v0.py",
            ),
            expected_ci_impact="FOCUSED_OR_PR_BOUNDED_DOCS_OPS",
            runtime_network_order_impact="NONE",
            risks=(
                "MISREAD_AS_ACTIVATION_OR_PROMOTION",
                "IMPLIED_RETRY_OF_UNCHANGED_BINDINGS",
            ),
            explicit_non_goals=(
                "NO_SAME_BINDING_RETRY",
                "NO_THRESHOLD_LOWERING",
                "NO_RUNTIME_AUTHORITY",
                "NO_STRATEGY_HYPOTHESIS_INVENTION",
            ),
            operator_visible_value=(
                "Closes research retry pressure on terminal-failed fleet bindings."
            ),
            status=OPTION_ELIGIBLE
            if fleet.get("negative_evidence_terminal_for_unchanged_bindings") is True
            else OPTION_BLOCKED,
            blocked_reason=(
                None
                if fleet.get("negative_evidence_terminal_for_unchanged_bindings") is True
                else "TERMINALIZATION_FLAG_ABSENT"
            ),
        )
    )

    # 2) Return to ratified material-different research backlog / scope discovery.
    material_eligible = (
        str(fleet.get("next_admissible_boundary") or "")
        == "MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_OR_RATIFICATION_ONLY_NO_EVAL"
        and bool(admissible_tokens or required_next_go)
    )
    options.append(
        RecoveryOptionEntryV0(
            option_id="RETURN_TO_RATIFIED_MATERIAL_DIFFERENT_RESEARCH_BACKLOG",
            objective=(
                "Operator-select already-ratified material-different offline-only "
                "research scope discovery/ratification path (no eval in this closeout)."
            ),
            exact_evidence_gap_addressed=(
                "Step-29U activation blocked by ECONOMIC_VALIDITY_PROVEN=false; "
                "admissible research path is material-different scope discovery only"
            ),
            prerequisites=(
                required_next_go or "GO_DEFINE_NEW_VERSIONED_MATERIAL_RESEARCH_SCOPE_...",
                "NO_EVAL_IN_THIS_CLOSEOUT",
                "EXPLICIT_OPERATOR_SELECTION",
            ),
            expected_production_files=(
                GOVERNANCE_MATERIAL_DIFFERENT_PREP_RELPATH,
                "config/research/*material*scope*",
            ),
            expected_tests=("tests/research/*material*scope*",),
            expected_ci_impact="DEPENDS_ON_OPERATOR_SELECTED_SCOPE_SLICE",
            runtime_network_order_impact="NONE",
            risks=(
                "SCOPE_CREEP_INTO_EVALUATION_WITHOUT_NEW_GO",
                "NEAR_DUPLICATE_ARCHETYPE_RETRY",
            ),
            explicit_non_goals=(
                "NO_ECONOMIC_EVALUATION_EXECUTION_IN_THIS_OPTION",
                "NO_STEP_29U_ACTIVATION",
                "NO_UNCHANGED_BINDING_RETRY",
                "NO_STRATEGY_INVENTION_BY_THIS_CLOSEOUT",
            ),
            operator_visible_value=(
                "Restores a governed research path without claiming economic readiness."
            ),
            status=OPTION_ELIGIBLE if material_eligible else OPTION_BLOCKED,
            blocked_reason=None if material_eligible else "ADMISSIBLE_BOUNDARY_ABSENT",
        )
    )

    # 3) Improve sample sufficiency — only if evidence supports insufficiency.
    sample_supported = "INSUFFICIENT_SAMPLE" in failure_classes or any(
        "insufficient" in a.lower() or "sample" in a.lower() for a in failure_axes
    )
    options.append(
        RecoveryOptionEntryV0(
            option_id="IMPROVE_SAMPLE_SUFFICIENCY",
            objective="Address sample-sufficiency gap if durable evidence classifies it.",
            exact_evidence_gap_addressed="sample_sufficiency",
            prerequisites=("EVIDENCE_CLASS_INSUFFICIENT_SAMPLE", "EXPLICIT_OPERATOR_SELECTION"),
            expected_production_files=("config/research/*sample*",),
            expected_tests=("tests/research/*sample*",),
            expected_ci_impact="RESEARCH_FOCUSED",
            runtime_network_order_impact="NONE",
            risks=("FALSE_RESCUE_VIA_SAMPLE_EXPANSION_ON_TERMINAL_BINDING",),
            explicit_non_goals=(
                "NO_THRESHOLD_LOWERING",
                "NO_UNCHANGED_BINDING_RETRY_WITHOUT_MATERIAL_DIFFERENCE",
            ),
            operator_visible_value="Would clarify whether FAIL is sample-limited.",
            status=OPTION_ELIGIBLE if sample_supported else OPTION_BLOCKED,
            blocked_reason=(
                None
                if sample_supported
                else "EVIDENCE_DOES_NOT_SUPPORT_SAMPLE_INSUFFICIENCY_AS_PRIMARY_FAILURE"
            ),
        )
    )

    # 4) Isolate cost-drag sensitivity — blocked unless evidence supports and not banned.
    cost_supported = any("cost" in a.lower() for a in failure_axes) or (
        "COST_DRAG" in failure_classes
    )
    cost_blocked_by_governance = "PARAMETER_SENSITIVITY_EXECUTION" in blocked_set
    options.append(
        RecoveryOptionEntryV0(
            option_id="ISOLATE_COST_DRAG_SENSITIVITY",
            objective="Isolate cost-drag contribution if durable evidence supports it.",
            exact_evidence_gap_addressed="cost_drag_sensitivity",
            prerequisites=(
                "COST_AXIS_PRESENT_IN_CANONICAL_EVIDENCE",
                "EXPLICIT_OPERATOR_SELECTION",
            ),
            expected_production_files=("config/research/*cost*",),
            expected_tests=("tests/research/*cost*",),
            expected_ci_impact="RESEARCH_FOCUSED",
            runtime_network_order_impact="NONE",
            risks=("CAUSAL_OVERCLAIM_WITHOUT_NUMERIC_COST_TABLE",),
            explicit_non_goals=("NO_THRESHOLD_RELAXATION", "NO_RESULT_RESCUE"),
            operator_visible_value="Would separate cost drag from signal insufficiency.",
            status=(
                OPTION_ELIGIBLE
                if cost_supported and not cost_blocked_by_governance
                else OPTION_BLOCKED
            ),
            blocked_reason=(
                None
                if cost_supported and not cost_blocked_by_governance
                else (
                    "PARAMETER_SENSITIVITY_EXECUTION_BLOCKED"
                    if cost_blocked_by_governance
                    else "EVIDENCE_DOES_NOT_SUPPORT_COST_DRAG_ISOLATION"
                )
            ),
        )
    )

    # 5) Robustness/stress revalidation on unchanged bindings — blocked by governance.
    stress_axis = "stress_gate_failure" in failure_axes or "STRESS_GATE_FAIL" in failure_classes
    stress_exec_blocked = "STRESS_EXECUTION" in blocked_set or "SAME_BINDING_RETRY" in blocked_set
    options.append(
        RecoveryOptionEntryV0(
            option_id="PERFORM_ROBUSTNESS_STRESS_VALIDATION",
            objective=(
                "Re-run robustness/stress validation only if governance admits it "
                "for a material-different, newly authorized scope."
            ),
            exact_evidence_gap_addressed="robustness_stress_validation",
            prerequisites=(
                "MATERIAL_DIFFERENT_SCOPE_RATIFIED",
                "EXPLICIT_OPERATOR_GO_FOR_EVAL",
            ),
            expected_production_files=("config/research/*robustness*",),
            expected_tests=("tests/research/*robustness*",),
            expected_ci_impact="RESEARCH_FOCUSED",
            runtime_network_order_impact="NONE",
            risks=("SAME_BINDING_STRESS_RETRY_DISGUISED_AS_VALIDATION",),
            explicit_non_goals=(
                "NO_UNCHANGED_BINDING_STRESS_RERUN",
                "NO_STEP_29U_ACTIVATION",
            ),
            operator_visible_value=(
                "Would only be admissible after material-different scope ratification."
            ),
            status=OPTION_BLOCKED,
            blocked_reason=(
                "STRESS_OR_SAME_BINDING_RETRY_BLOCKED_ON_TERMINAL_FLEET"
                if stress_exec_blocked or stress_axis
                else "NOT_ADMISSIBLE_WITHOUT_NEW_MATERIAL_SCOPE_AND_EVAL_GO"
            ),
        )
    )

    return tuple(options)


def assert_no_forbidden_imports_v0(source_text: str) -> None:
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                for forbidden in FORBIDDEN_IMPORT_SURFACES:
                    if alias.name.startswith(forbidden) or f"src.{root}" == forbidden:
                        raise Step29UEconomicFailureCloseoutError(f"FORBIDDEN_IMPORT:{alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in FORBIDDEN_IMPORT_SURFACES:
                if node.module.startswith(forbidden):
                    raise Step29UEconomicFailureCloseoutError(f"FORBIDDEN_IMPORT:{node.module}")


def evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
    *,
    repo_root: Path | None = None,
    overrides: EconomicFailureCloseoutOverridesV0 | None = None,
) -> EconomicFailureCloseoutResultV0:
    """Compose economic FAIL closeout + recovery decision inventory."""
    root = (repo_root or default_repo_root_v0()).resolve()
    ov = overrides or EconomicFailureCloseoutOverridesV0()
    generated_at = _utc_now()
    reasons: list[str] = []

    if ov.claim_auto_select_recovery:
        raise Step29UEconomicFailureCloseoutError("AUTOMATIC_RECOVERY_SELECTION_FORBIDDEN")
    if ov.claim_activation_eligible:
        raise Step29UEconomicFailureCloseoutError(
            "ACTIVATION_ELIGIBILITY_CLAIM_FORBIDDEN_WHILE_CLOSEOUT"
        )
    if ov.claim_economic_ready_from_audit_complete:
        raise Step29UEconomicFailureCloseoutError("AUDIT_COMPLETE_DOES_NOT_IMPLY_ECONOMIC_READY")

    fleet_path = (
        ov.fleet_closeout_path.resolve()
        if ov.fleet_closeout_path is not None
        else (root / CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH).resolve()
    )
    sealed_econ_path = (
        ov.sealed_economic_result_path.resolve()
        if ov.sealed_economic_result_path is not None
        else (root / SEALED_ECONOMIC_RESULT_RELPATH).resolve()
    )
    sealed_composed_path = (
        ov.sealed_composed_result_path.resolve()
        if ov.sealed_composed_result_path is not None
        else (root / SEALED_COMPOSED_RESULT_RELPATH).resolve()
    )

    if not fleet_path.is_file():
        raise Step29UEconomicFailureCloseoutError(
            f"CANONICAL_ECONOMIC_EVIDENCE_MISSING:{CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH}"
        )
    if not sealed_econ_path.is_file():
        raise Step29UEconomicFailureCloseoutError(
            f"CANONICAL_ECONOMIC_EVIDENCE_MISSING:{SEALED_ECONOMIC_RESULT_RELPATH}"
        )

    fleet = _load_json(fleet_path)
    if not isinstance(fleet, dict):
        raise Step29UEconomicFailureCloseoutError("FLEET_CLOSEOUT_NOT_OBJECT")
    sealed_econ = _load_json(sealed_econ_path)
    if not isinstance(sealed_econ, dict):
        raise Step29UEconomicFailureCloseoutError("SEALED_ECONOMIC_RESULT_NOT_OBJECT")

    econ = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=root,
        overrides=EconomicValidityReadinessOverridesV0(
            readiness_config_path=ov.readiness_config_path,
            fleet_closeout_path=fleet_path,
            force_status=ov.force_economic_status,
            overlay_gate_pass=ov.overlay_gate_pass,
            overlay_fleet_verdict=ov.overlay_fleet_verdict,
        ),
    )
    audit = evaluate_step_29u_audit_provenance_v0(repo_root=root)
    eligibility = evaluate_step_29u_activation_eligibility_inventory_v0(repo_root=root)

    sealed_status = str(sealed_econ.get("status") or "")
    live_status = econ.status
    sealed_proven = sealed_econ.get("economic_validity_proven") is True
    live_proven = econ.economic_validity_proven is True

    # Contradictory economic PASS vs FAIL across sealed vs live composition.
    if (sealed_status == ECON_STATUS_PASS) != (live_status == ECON_STATUS_PASS):
        raise Step29UEconomicFailureCloseoutError(
            f"CONTRADICTORY_ECONOMIC_PASS_FAIL:sealed={sealed_status}:live={live_status}"
        )
    if sealed_proven != live_proven:
        raise Step29UEconomicFailureCloseoutError(
            f"CONTRADICTORY_ECONOMIC_PROVEN_FLAG:sealed={sealed_proven}:live={live_proven}"
        )
    if live_status == ECON_STATUS_CONTRADICTORY:
        raise Step29UEconomicFailureCloseoutError(
            "CONTRADICTORY_ECONOMIC_PASS_FAIL:live_status=CONTRADICTORY"
        )

    # Audit COMPLETE must never be re-labelled as economic READY/PASS.
    if audit.status == AUDIT_STATUS_COMPLETE and (
        live_status == ECON_STATUS_PASS or live_proven is True
    ):
        raise Step29UEconomicFailureCloseoutError("AUDIT_COMPLETE_CANNOT_PRODUCE_ECONOMIC_READY")

    if live_proven is True:
        raise Step29UEconomicFailureCloseoutError(
            "UNEXPECTED_ECONOMIC_VALIDITY_PROVEN_TRUE_DURING_FAIL_CLOSEOUT"
        )
    if eligibility.activation_eligible is True:
        raise Step29UEconomicFailureCloseoutError(
            "UNEXPECTED_ACTIVATION_ELIGIBLE_TRUE_DURING_FAIL_CLOSEOUT"
        )

    expected_fail = live_status == ECON_STATUS_FAIL
    if not expected_fail:
        raise Step29UEconomicFailureCloseoutError(
            f"ECONOMIC_CLOSEOUT_REQUIRES_FAIL_STATUS:got={live_status}"
        )

    # Confirm no contradictory READY claim in sealed composed eligibility.
    if sealed_composed_path.is_file():
        composed = _load_json(sealed_composed_path)
        if isinstance(composed, dict):
            if composed.get("activation_eligible") is True:
                raise Step29UEconomicFailureCloseoutError(
                    "CONTRADICTORY_ACTIVATION_ELIGIBLE_CLAIM_IN_SEALED_EVIDENCE"
                )
            if composed.get("economic_validity_proven") is True:
                raise Step29UEconomicFailureCloseoutError(
                    "CONTRADICTORY_ECONOMIC_PASS_CLAIM_IN_SEALED_EVIDENCE"
                )

    fleet_digest = _sha256_file(fleet_path)
    sealed_digest = _sha256_file(sealed_econ_path)
    readiness_path = root / READINESS_CONFIG_RELPATH
    readiness_digest = _sha256_file(readiness_path) if readiness_path.is_file() else None

    canonical_evidence = (
        _evidence_ref(
            relpath=CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
            digest=fleet_digest,
            schema_version=str(fleet.get("schema_version") or ""),
            provenance_note="terminal_final_research_fleet_FAIL_closeout",
        ),
        _evidence_ref(
            relpath=SEALED_ECONOMIC_RESULT_RELPATH,
            digest=sealed_digest,
            schema_version=str(sealed_econ.get("schema_version") or ""),
            provenance_note="sealed_step29u_economic_validity_result_pr5553",
        ),
        _evidence_ref(
            relpath=READINESS_CONFIG_RELPATH,
            digest=readiness_digest,
            schema_version="shadow_preparation_readiness_gate_v0",
            provenance_note="economic_validity_offline_gate_pass_authority",
        ),
        _evidence_ref(
            relpath="src/backtest/economic_validity_policy_v1.py",
            digest=None,
            schema_version=ECONOMIC_VALIDITY_POLICY_VERSION,
            provenance_note=f"policy_identity_owner={ECONOMIC_VALIDITY_POLICY_OWNER}",
        ),
        _evidence_ref(
            relpath=GOVERNANCE_TERMINAL_BOUNDARY_RELPATH,
            digest=None,
            schema_version="v0",
            provenance_note="governance_terminalization_and_next_material_boundary",
        ),
    )

    failure_inventory = _build_failure_cause_inventory(
        fleet=fleet,
        fleet_relpath=CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
        econ_status=live_status,
    )
    recovery_inventory = _build_recovery_option_inventory(fleet=fleet)

    # Hard invariant: never auto-select.
    selected_id = None
    eligible_options = [o for o in recovery_inventory if o.status == OPTION_ELIGIBLE]
    if not eligible_options:
        reasons.append("NO_ELIGIBLE_RECOVERY_OPTIONS")
    else:
        reasons.append(f"ELIGIBLE_RECOVERY_OPTION_COUNT={len(eligible_options)}")
    reasons.append("AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED=false")
    reasons.append("OPERATOR_SELECTION_REQUIRED=true")
    reasons.extend(list(econ.reasons))

    blockers = tuple(
        dict.fromkeys(
            list(eligibility.blockers)
            + [f"ECONOMIC_VALIDITY_STATUS:{live_status}"]
            + ["AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED:false"]
        )
    )

    closeout_status = CLOSEOUT_COMPLETE if expected_fail else CLOSEOUT_INCOMPLETE
    status = "PASS" if closeout_status == CLOSEOUT_COMPLETE else "FAIL"

    return EconomicFailureCloseoutResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        capability_id=CAPABILITY_ID,
        status=status,
        evaluator_valid=True,
        economic_closeout_status=closeout_status,
        audit_provenance_status=str(audit.status),
        economic_validity_status=live_status,
        economic_validity_proven=False,
        activation_eligible=False,
        step_29u_activated=False,
        automatic_next_research_action_allowed=False,
        operator_selection_required=True,
        selected_recovery_option_id=selected_id,
        canonical_blockers=blockers,
        canonical_economic_evidence=canonical_evidence,
        failure_cause_inventory=failure_inventory,
        recovery_option_inventory=recovery_inventory,
        reasons=tuple(dict.fromkeys(reasons)),
        provenance={
            "package_marker": PACKAGE_MARKER,
            "producer_family": PRODUCER_FAMILY,
            "reuses_economic_validity_readiness": True,
            "reuses_audit_provenance": True,
            "reuses_activation_eligibility_inventory": True,
            "reuses_fleet_fail_closeout": True,
            "no_threshold_invention": True,
            "no_metric_recomputation": True,
            "no_automatic_recovery_selection": True,
            "no_strategy_hypothesis_invention": True,
        },
        safety_facts={
            "RUNTIME_ACTIVATED": False,
            "SCHEDULER_ACTIVATED": False,
            "NETWORK_USED": False,
            "ORDERS_CREATED": False,
            "ORDERS_SUBMITTED": False,
            "STEP_29U_ACTIVATED": False,
            "ACTIVATION_ELIGIBLE": False,
            "ECONOMIC_VALIDITY_PROVEN": False,
            "AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED": False,
            "OPERATOR_SELECTION_REQUIRED": True,
            "BTC_EXCLUDED": True,
            "SPOT_EXCLUDED": True,
            "KRAKEN_LEGACY_EXCLUDED": True,
        },
        inputs={
            "fleet_closeout_relpath": CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
            "fleet_closeout_digest": fleet_digest,
            "sealed_economic_result_relpath": SEALED_ECONOMIC_RESULT_RELPATH,
            "sealed_economic_result_digest": sealed_digest,
            "readiness_config_relpath": READINESS_CONFIG_RELPATH,
            "readiness_config_digest": readiness_digest,
            "audit_status": audit.status,
            "eligibility_activation_eligible": eligibility.activation_eligible,
            "policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
            "policy_owner": ECONOMIC_VALIDITY_POLICY_OWNER,
        },
    )


def serialize_result_json_v0(result: EconomicFailureCloseoutResultV0) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"


def result_to_machine_lines(
    result: EconomicFailureCloseoutResultV0,
) -> list[str]:
    option_ids = [o.option_id for o in result.recovery_option_inventory]
    eligible_ids = [
        o.option_id for o in result.recovery_option_inventory if o.status == OPTION_ELIGIBLE
    ]
    evidence_paths = [e.get("relpath") for e in result.canonical_economic_evidence]
    return [
        f"STATUS={result.status}",
        f"EVALUATOR_VALID={str(result.evaluator_valid).lower()}",
        f"ECONOMIC_CLOSEOUT={result.economic_closeout_status}",
        f"ECONOMIC_CLOSEOUT_STATUS={result.economic_closeout_status}",
        f"AUDIT_PROVENANCE_STATUS={result.audit_provenance_status}",
        f"ECONOMIC_VALIDITY_STATUS={result.economic_validity_status}",
        f"ECONOMIC_VALIDITY_PROVEN={str(result.economic_validity_proven).lower()}",
        f"ACTIVATION_ELIGIBLE={str(result.activation_eligible).lower()}",
        f"STEP_29U_ACTIVATED={str(result.step_29u_activated).lower()}",
        f"AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED="
        f"{str(result.automatic_next_research_action_allowed).lower()}",
        f"OPERATOR_SELECTION_REQUIRED={str(result.operator_selection_required).lower()}",
        f"SELECTED_RECOVERY_OPTION_ID={result.selected_recovery_option_id}",
        f"CANONICAL_BLOCKERS={list(result.canonical_blockers)!r}",
        f"CANONICAL_ECONOMIC_EVIDENCE={evidence_paths!r}",
        f"FAILURE_CAUSE_INVENTORY_COUNT={len(result.failure_cause_inventory)}",
        f"RECOVERY_OPTION_INVENTORY_COUNT={len(result.recovery_option_inventory)}",
        f"RECOVERY_OPTIONS={option_ids!r}",
        f"ELIGIBLE_RECOVERY_OPTIONS={eligible_ids!r}",
        f"RUNTIME_ACTIVATED={str(result.safety_facts.get('RUNTIME_ACTIVATED')).lower()}",
        f"SCHEDULER_ACTIVATED={str(result.safety_facts.get('SCHEDULER_ACTIVATED')).lower()}",
        f"NETWORK_USED={str(result.safety_facts.get('NETWORK_USED')).lower()}",
        f"ORDERS_CREATED={str(result.safety_facts.get('ORDERS_CREATED')).lower()}",
        f"ORDERS_SUBMITTED={str(result.safety_facts.get('ORDERS_SUBMITTED')).lower()}",
        f"BTC_EXCLUDED={str(result.safety_facts.get('BTC_EXCLUDED')).lower()}",
        f"SPOT_EXCLUDED={str(result.safety_facts.get('SPOT_EXCLUDED')).lower()}",
        f"KRAKEN_LEGACY_EXCLUDED={str(result.safety_facts.get('KRAKEN_LEGACY_EXCLUDED')).lower()}",
        f"SCHEMA_ID={result.schema_id}",
        f"SCHEMA_VERSION={result.schema_version}",
        f"CAPABILITY_ID={result.capability_id}",
    ]


def eligible_recovery_option_ids_v0(
    result: EconomicFailureCloseoutResultV0,
) -> tuple[str, ...]:
    return tuple(
        o.option_id for o in result.recovery_option_inventory if o.status == OPTION_ELIGIBLE
    )


__all__ = [
    "CAPABILITY_ID",
    "CLOSEOUT_COMPLETE",
    "EconomicFailureCloseoutOverridesV0",
    "EconomicFailureCloseoutResultV0",
    "FORBIDDEN_IMPORT_SURFACES",
    "OPTION_BLOCKED",
    "OPTION_ELIGIBLE",
    "PACKAGE_MARKER",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "Step29UEconomicFailureCloseoutError",
    "assert_no_forbidden_imports_v0",
    "eligible_recovery_option_ids_v0",
    "evaluate_step_29u_economic_failure_closeout_recovery_decision_v0",
    "result_to_machine_lines",
    "serialize_result_json_v0",
]
