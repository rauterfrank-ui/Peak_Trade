"""STEP 29U Terminal Unchanged Final Fleet Hypothesis Retirement v0.

Offline, fail-closed application of the operator-selected recovery option
RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES.

Reuses existing canonical authorities only:
- ops.step_29u_economic_failure_closeout_recovery_decision_v0
- config/research/post_pr4940_final_research_fleet_negative_evidence_...
- sealed Step-29U economic readiness evidence

Does not activate Step 29U, invent a strategy hypothesis, auto-select a
materially different backlog candidate, mutate historical economic evidence,
or authorize Runtime/Scheduler/Network/Orders.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.step_29u_economic_failure_closeout_recovery_decision_v0 import (
    CLOSEOUT_COMPLETE,
    OPTION_ELIGIBLE,
    EconomicFailureCloseoutOverridesV0,
    EconomicFailureCloseoutResultV0,
    evaluate_step_29u_economic_failure_closeout_recovery_decision_v0,
)
from src.ops.step_29u_economic_validity_readiness_v0 import (
    CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
    STATUS_FAIL as ECON_STATUS_FAIL,
)
from src.research.post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0 import (
    FINAL_RESEARCH_FLEET,
    validate_boundary_config_v0,
)

PACKAGE_MARKER = "STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0=true"
PRODUCER_FAMILY = "ops.step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"
CAPABILITY_ID = "STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0"

SELECTED_RECOVERY_OPTION = "RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES"
RETIREMENT_SCOPE = "UNCHANGED_FINAL_FLEET_ONLY"
RETIREMENT_REASON = "TERMINAL_ECONOMIC_FAILURE"
RETIREMENT_STATUS_COMPLETE = "COMPLETE"
RETIREMENT_STATUS_INCOMPLETE = "INCOMPLETE"

RETIREMENT_CONFIG_RELPATH = (
    "config/research/step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.json"
)
GOVERNANCE_TERMINAL_BOUNDARY_RELPATH = (
    "docs/governance/POST_PR4939_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_"
    "TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_V0.md"
)
SEALED_ECONOMIC_RESULT_RELPATH = (
    "evidence/ops/step_29u_activation_evidence_economic_readiness/"
    "20260726T011500Z_local_pre_pr/economic_validity_result.json"
)

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


class Step29UTerminalFleetHypothesisRetirementError(ValueError):
    """Fail-closed terminal fleet hypothesis retirement error."""


@dataclass(frozen=True)
class RetiredHypothesisEntryV0:
    hypothesis_id: str
    strategy_id: str
    strategy_version: str
    binding_digest: str
    terminal_verdict: str
    retirement_status: str
    retirement_reason: str
    canonical_negative_evidence_ref: str
    historical_evidence_preserved: bool
    unchanged_rerun_allowed: bool
    unchanged_repromotion_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "binding_digest": self.binding_digest,
            "terminal_verdict": self.terminal_verdict,
            "retirement_status": self.retirement_status,
            "retirement_reason": self.retirement_reason,
            "canonical_negative_evidence_ref": self.canonical_negative_evidence_ref,
            "historical_evidence_preserved": self.historical_evidence_preserved,
            "unchanged_rerun_allowed": self.unchanged_rerun_allowed,
            "unchanged_repromotion_allowed": self.unchanged_repromotion_allowed,
        }


@dataclass(frozen=True)
class TerminalFleetHypothesisRetirementResultV0:
    schema_id: str
    schema_version: str
    generated_at: str
    capability_id: str
    status: str
    evaluator_valid: bool
    selected_recovery_option: str
    retirement_status: str
    retirement_inventory_complete: bool
    retired_hypothesis_count: int
    retired_hypothesis_ids: tuple[str, ...]
    retirement_scope: str
    retirement_reason: str
    historical_evidence_preserved: bool
    unchanged_rerun_allowed: bool
    unchanged_repromotion_allowed: bool
    automatic_backlog_selection_allowed: bool
    next_research_candidate_selected: bool
    operator_selection_required_for_next_material_research: bool
    economic_validity_status: str
    economic_validity_proven: bool
    activation_eligible: bool
    activated: bool
    retirement_inventory: tuple[RetiredHypothesisEntryV0, ...]
    canonical_evidence: tuple[Mapping[str, Any], ...]
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
            "selected_recovery_option": self.selected_recovery_option,
            "retirement_status": self.retirement_status,
            "retirement_inventory_complete": self.retirement_inventory_complete,
            "retired_hypothesis_count": self.retired_hypothesis_count,
            "retired_hypothesis_ids": list(self.retired_hypothesis_ids),
            "retirement_scope": self.retirement_scope,
            "retirement_reason": self.retirement_reason,
            "historical_evidence_preserved": self.historical_evidence_preserved,
            "unchanged_rerun_allowed": self.unchanged_rerun_allowed,
            "unchanged_repromotion_allowed": self.unchanged_repromotion_allowed,
            "automatic_backlog_selection_allowed": (self.automatic_backlog_selection_allowed),
            "next_research_candidate_selected": self.next_research_candidate_selected,
            "operator_selection_required_for_next_material_research": (
                self.operator_selection_required_for_next_material_research
            ),
            "economic_validity_status": self.economic_validity_status,
            "economic_validity_proven": self.economic_validity_proven,
            "activation_eligible": self.activation_eligible,
            "activated": self.activated,
            "retirement_inventory": [e.to_dict() for e in self.retirement_inventory],
            "canonical_evidence": [dict(x) for x in self.canonical_evidence],
            "reasons": list(self.reasons),
            "provenance": dict(self.provenance),
            "safety_facts": dict(self.safety_facts),
            "inputs": dict(self.inputs),
        }


@dataclass(frozen=True)
class TerminalFleetHypothesisRetirementOverridesV0:
    fleet_closeout_path: Optional[Path] = None
    retirement_config_path: Optional[Path] = None
    sealed_economic_result_path: Optional[Path] = None
    selected_recovery_option: Optional[str] = None
    claim_activation_eligible: bool = False
    claim_economic_pass: bool = False
    claim_automatic_backlog_selection: bool = False
    claim_next_research_candidate_selected: bool = False
    extra_hypothesis_ids: tuple[str, ...] = ()
    mutate_historical_evidence: bool = False


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
        raise Step29UTerminalFleetHypothesisRetirementError(f"JSON_MALFORMED:{path}:{exc}") from exc
    except OSError as exc:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"JSON_UNREADABLE:{path}:{exc}"
        ) from exc


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


def assert_no_forbidden_imports_v0(source_text: str) -> None:
    tree = ast.parse(source_text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                for forbidden in FORBIDDEN_IMPORT_SURFACES:
                    if alias.name.startswith(forbidden) or f"src.{root}" == forbidden:
                        raise Step29UTerminalFleetHypothesisRetirementError(
                            f"FORBIDDEN_IMPORT:{alias.name}"
                        )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in FORBIDDEN_IMPORT_SURFACES:
                if node.module.startswith(forbidden):
                    raise Step29UTerminalFleetHypothesisRetirementError(
                        f"FORBIDDEN_IMPORT:{node.module}"
                    )


def _authorized_fleet_hypothesis_ids(fleet: Mapping[str, Any]) -> tuple[str, ...]:
    exclusions = fleet.get("terminal_failed_binding_exclusions")
    if not isinstance(exclusions, list) or not exclusions:
        raise Step29UTerminalFleetHypothesisRetirementError("FINAL_FLEET_HYPOTHESIS_SET_MISSING")
    ids: list[str] = []
    for item in exclusions:
        if not isinstance(item, dict):
            raise Step29UTerminalFleetHypothesisRetirementError(
                "FINAL_FLEET_EXCLUSION_ENTRY_MALFORMED"
            )
        hid = str(item.get("canonical_candidate_identifier") or "").strip()
        if not hid:
            raise Step29UTerminalFleetHypothesisRetirementError("FINAL_FLEET_HYPOTHESIS_ID_MISSING")
        ids.append(hid)
    return tuple(ids)


def _build_retirement_inventory_from_fleet(
    *,
    fleet: Mapping[str, Any],
    fleet_relpath: str,
) -> tuple[RetiredHypothesisEntryV0, ...]:
    exclusions = fleet.get("terminal_failed_binding_exclusions")
    if not isinstance(exclusions, list):
        raise Step29UTerminalFleetHypothesisRetirementError("FINAL_FLEET_HYPOTHESIS_SET_MISSING")
    fleet_strategies = fleet.get("final_research_fleet")
    if not isinstance(fleet_strategies, list):
        raise Step29UTerminalFleetHypothesisRetirementError("FINAL_RESEARCH_FLEET_MISSING")
    fleet_strategy_set = {str(x) for x in fleet_strategies}
    if set(FINAL_RESEARCH_FLEET) != fleet_strategy_set:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"FINAL_RESEARCH_FLEET_MISMATCH:expected={list(FINAL_RESEARCH_FLEET)}"
            f":got={sorted(fleet_strategy_set)}"
        )

    candidate_results = fleet.get("candidate_results")
    if not isinstance(candidate_results, dict):
        raise Step29UTerminalFleetHypothesisRetirementError("CANDIDATE_RESULTS_MISSING")

    entries: list[RetiredHypothesisEntryV0] = []
    seen: set[str] = set()
    for item in exclusions:
        if not isinstance(item, dict):
            raise Step29UTerminalFleetHypothesisRetirementError(
                "FINAL_FLEET_EXCLUSION_ENTRY_MALFORMED"
            )
        hypothesis_id = str(item.get("canonical_candidate_identifier") or "").strip()
        strategy_id = str(item.get("strategy_id") or "").strip()
        strategy_version = str(item.get("strategy_version") or "").strip()
        binding_digest = str(item.get("binding_digest") or "").strip()
        terminal_verdict = str(item.get("terminal_verdict") or "").strip()
        retry_allowed = item.get("retry_unchanged_binding_allowed")

        if not hypothesis_id:
            raise Step29UTerminalFleetHypothesisRetirementError("FINAL_FLEET_HYPOTHESIS_ID_MISSING")
        if hypothesis_id in seen:
            # Deterministic/idempotent: skip duplicates with identical identity.
            continue
        seen.add(hypothesis_id)

        if strategy_id not in fleet_strategy_set:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"HYPOTHESIS_OUTSIDE_AUTHORIZED_FINAL_FLEET:{hypothesis_id}"
            )
        if terminal_verdict != "FAIL":
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"MISSING_TERMINAL_NEGATIVE_EVIDENCE:{hypothesis_id}:{terminal_verdict}"
            )
        if candidate_results.get(strategy_id) != "FAIL":
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"MISSING_TERMINAL_NEGATIVE_EVIDENCE:{hypothesis_id}:candidate_results"
            )
        if retry_allowed is not False:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"UNCHANGED_RETRY_NOT_PROHIBITED:{hypothesis_id}"
            )
        if not binding_digest or len(binding_digest) != 64:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"BINDING_DIGEST_INVALID:{hypothesis_id}"
            )
        if not strategy_version:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"STRATEGY_VERSION_MISSING:{hypothesis_id}"
            )

        entries.append(
            RetiredHypothesisEntryV0(
                hypothesis_id=hypothesis_id,
                strategy_id=strategy_id,
                strategy_version=strategy_version,
                binding_digest=binding_digest,
                terminal_verdict="FAIL",
                retirement_status="RETIRED",
                retirement_reason=RETIREMENT_REASON,
                canonical_negative_evidence_ref=fleet_relpath,
                historical_evidence_preserved=True,
                unchanged_rerun_allowed=False,
                unchanged_repromotion_allowed=False,
            )
        )

    if not entries:
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_INVENTORY_EMPTY")
    if len(entries) != len(FINAL_RESEARCH_FLEET):
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"RETIRED_HYPOTHESIS_COUNT_MISMATCH:expected={len(FINAL_RESEARCH_FLEET)}"
            f":got={len(entries)}"
        )
    return tuple(entries)


def _validate_retirement_config_against_inventory(
    *,
    config: Mapping[str, Any],
    inventory: Sequence[RetiredHypothesisEntryV0],
) -> None:
    if config.get("schema_version") != (
        "step_29u_terminal_unchanged_final_fleet_hypothesis_retirement.v0"
    ):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_SCHEMA_MISMATCH")
    if config.get("selected_recovery_option") != SELECTED_RECOVERY_OPTION:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "RETIREMENT_CONFIG_SELECTED_OPTION_MISMATCH"
        )
    if config.get("retirement_scope") != RETIREMENT_SCOPE:
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_SCOPE_MISMATCH")
    if config.get("retirement_reason") != RETIREMENT_REASON:
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_REASON_MISMATCH")
    if config.get("economic_validity_status") != ECON_STATUS_FAIL:
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CANNOT_CONVERT_FAIL_STATUS")
    if config.get("economic_validity_proven") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "RETIREMENT_CANNOT_GRANT_ECONOMIC_VALIDITY"
        )
    if config.get("activation_eligible") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "RETIREMENT_CANNOT_GRANT_ACTIVATION_ELIGIBILITY"
        )
    if config.get("activated") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CANNOT_GRANT_ACTIVATION")
    if config.get("automatic_backlog_selection_allowed") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError("AUTOMATIC_BACKLOG_SELECTION_FORBIDDEN")
    if config.get("next_research_candidate_selected") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "NEXT_RESEARCH_CANDIDATE_SELECTION_FORBIDDEN"
        )
    if config.get("unchanged_rerun_allowed") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError("UNCHANGED_RERUN_MUST_REMAIN_FALSE")
    if config.get("unchanged_repromotion_allowed") is not False:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "UNCHANGED_REPROMOTION_MUST_REMAIN_FALSE"
        )
    if config.get("historical_evidence_preserved") is not True:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "HISTORICAL_EVIDENCE_MUST_REMAIN_PRESERVED"
        )

    cfg_ids = config.get("retired_hypothesis_ids")
    if not isinstance(cfg_ids, list):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_IDS_MALFORMED")
    expected_ids = [e.hypothesis_id for e in inventory]
    if cfg_ids != expected_ids:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"RETIREMENT_CONFIG_IDS_MISMATCH:expected={expected_ids}:got={cfg_ids}"
        )
    if int(config.get("retired_hypothesis_count") or -1) != len(expected_ids):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_COUNT_MISMATCH")

    cfg_inventory = config.get("retirement_inventory")
    if not isinstance(cfg_inventory, list) or len(cfg_inventory) != len(inventory):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_INVENTORY_MISMATCH")
    for expected, actual in zip(inventory, cfg_inventory, strict=True):
        if not isinstance(actual, dict):
            raise Step29UTerminalFleetHypothesisRetirementError(
                "RETIREMENT_CONFIG_INVENTORY_ENTRY_MALFORMED"
            )
        if actual.get("hypothesis_id") != expected.hypothesis_id:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"RETIREMENT_CONFIG_INVENTORY_ID_DRIFT:{expected.hypothesis_id}"
            )
        if actual.get("terminal_verdict") != "FAIL":
            raise Step29UTerminalFleetHypothesisRetirementError(
                "RETIREMENT_CANNOT_CONVERT_FAIL_TO_NON_FAIL"
            )
        if actual.get("retirement_status") != "RETIRED":
            raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_STATUS_MUST_BE_RETIRED")


def build_canonical_retirement_config_v0(
    *,
    inventory: Sequence[RetiredHypothesisEntryV0],
    fleet_digest: str,
) -> dict[str, Any]:
    """Deterministic SSOT payload for the retirement config (no timestamps)."""
    return {
        "artifact_kind": "step_29u_terminal_unchanged_final_fleet_hypothesis_retirement",
        "artifact_version": "v0",
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "schema_version": ("step_29u_terminal_unchanged_final_fleet_hypothesis_retirement.v0"),
        "capability_id": CAPABILITY_ID,
        "status": RETIREMENT_STATUS_COMPLETE,
        "selected_recovery_option": SELECTED_RECOVERY_OPTION,
        "retirement_inventory_complete": True,
        "retired_hypothesis_count": len(inventory),
        "retired_hypothesis_ids": [e.hypothesis_id for e in inventory],
        "retirement_scope": RETIREMENT_SCOPE,
        "retirement_reason": RETIREMENT_REASON,
        "historical_evidence_preserved": True,
        "unchanged_rerun_allowed": False,
        "unchanged_repromotion_allowed": False,
        "automatic_backlog_selection_allowed": False,
        "next_research_candidate_selected": False,
        "operator_selection_required_for_next_material_research": True,
        "economic_validity_status": ECON_STATUS_FAIL,
        "economic_validity_proven": False,
        "activation_eligible": False,
        "activated": False,
        "retirement_inventory": [e.to_dict() for e in inventory],
        "canonical_fleet_closeout_relpath": CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
        "canonical_fleet_closeout_sha256": fleet_digest,
        "reuses_closeout_owner": ("ops.step_29u_economic_failure_closeout_recovery_decision_v0"),
        "reuses_fleet_terminalization_owner": (
            "research.post_pr4940_final_research_fleet_negative_evidence_"
            "terminalization_and_next_material_research_boundary_v0"
        ),
        "retired_means_deleted": False,
        "retired_means_globally_invalid_under_all_future_hypotheses": False,
        "materially_different_research_requires_new_hypothesis_identity": True,
    }


def is_hypothesis_retired_v0(
    hypothesis_id: str,
    *,
    result: TerminalFleetHypothesisRetirementResultV0 | None = None,
    repo_root: Path | None = None,
) -> bool:
    if result is not None:
        return hypothesis_id in set(result.retired_hypothesis_ids)
    root = (repo_root or default_repo_root_v0()).resolve()
    cfg_path = root / RETIREMENT_CONFIG_RELPATH
    if not cfg_path.is_file():
        return False
    payload = _load_json(cfg_path)
    if not isinstance(payload, dict):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_NOT_OBJECT")
    ids = payload.get("retired_hypothesis_ids")
    if not isinstance(ids, list):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_IDS_MALFORMED")
    return hypothesis_id in {str(x) for x in ids}


def assert_unchanged_resubmission_blocked_v0(
    hypothesis_id: str,
    *,
    result: TerminalFleetHypothesisRetirementResultV0 | None = None,
    repo_root: Path | None = None,
) -> None:
    """Fail-closed guard against automatic unchanged resubmission/selection."""
    if is_hypothesis_retired_v0(hypothesis_id, result=result, repo_root=repo_root):
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"UNCHANGED_RESUBMISSION_BLOCKED:{hypothesis_id}"
        )


def evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0(
    *,
    repo_root: Path | None = None,
    overrides: TerminalFleetHypothesisRetirementOverridesV0 | None = None,
) -> TerminalFleetHypothesisRetirementResultV0:
    """Apply operator-selected retirement of terminal unchanged Final Fleet hypotheses."""
    root = (repo_root or default_repo_root_v0()).resolve()
    ov = overrides or TerminalFleetHypothesisRetirementOverridesV0()
    generated_at = _utc_now()
    reasons: list[str] = []

    selected = (ov.selected_recovery_option or SELECTED_RECOVERY_OPTION).strip()
    if selected != SELECTED_RECOVERY_OPTION:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"UNAUTHORIZED_RECOVERY_OPTION:{selected}"
        )
    if ov.claim_activation_eligible:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "RETIREMENT_CANNOT_GRANT_ACTIVATION_ELIGIBILITY"
        )
    if ov.claim_economic_pass:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "RETIREMENT_CANNOT_CONVERT_FAIL_TO_PASS"
        )
    if ov.claim_automatic_backlog_selection:
        raise Step29UTerminalFleetHypothesisRetirementError("AUTOMATIC_BACKLOG_SELECTION_FORBIDDEN")
    if ov.claim_next_research_candidate_selected:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "NEXT_RESEARCH_CANDIDATE_SELECTION_FORBIDDEN"
        )
    if ov.mutate_historical_evidence:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "HISTORICAL_EVIDENCE_MUTATION_FORBIDDEN"
        )
    if ov.extra_hypothesis_ids:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "HYPOTHESIS_OUTSIDE_AUTHORIZED_FINAL_FLEET:" + ",".join(ov.extra_hypothesis_ids)
        )

    fleet_path = (
        ov.fleet_closeout_path.resolve()
        if ov.fleet_closeout_path is not None
        else (root / CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH).resolve()
    )
    retirement_cfg_path = (
        ov.retirement_config_path.resolve()
        if ov.retirement_config_path is not None
        else (root / RETIREMENT_CONFIG_RELPATH).resolve()
    )
    sealed_path = (
        ov.sealed_economic_result_path.resolve()
        if ov.sealed_economic_result_path is not None
        else (root / SEALED_ECONOMIC_RESULT_RELPATH).resolve()
    )

    if not fleet_path.is_file():
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"CANONICAL_ECONOMIC_EVIDENCE_MISSING:{CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH}"
        )
    if not sealed_path.is_file():
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"CANONICAL_ECONOMIC_EVIDENCE_MISSING:{SEALED_ECONOMIC_RESULT_RELPATH}"
        )
    if not retirement_cfg_path.is_file():
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"RETIREMENT_CONFIG_MISSING:{RETIREMENT_CONFIG_RELPATH}"
        )

    fleet = _load_json(fleet_path)
    if not isinstance(fleet, dict):
        raise Step29UTerminalFleetHypothesisRetirementError("FLEET_CLOSEOUT_NOT_OBJECT")

    boundary = validate_boundary_config_v0(fleet, repo_root=root)
    if not boundary.valid:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "FLEET_TERMINALIZATION_INVALID:" + ",".join(boundary.reasons)
        )

    closeout: EconomicFailureCloseoutResultV0 = (
        evaluate_step_29u_economic_failure_closeout_recovery_decision_v0(
            repo_root=root,
            overrides=EconomicFailureCloseoutOverridesV0(
                fleet_closeout_path=fleet_path,
                sealed_economic_result_path=sealed_path,
            ),
        )
    )
    if closeout.economic_closeout_status != CLOSEOUT_COMPLETE:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"ECONOMIC_CLOSEOUT_INCOMPLETE:{closeout.economic_closeout_status}"
        )
    if closeout.economic_validity_status != ECON_STATUS_FAIL:
        raise Step29UTerminalFleetHypothesisRetirementError(
            f"ECONOMIC_VALIDITY_STATUS_NOT_FAIL:{closeout.economic_validity_status}"
        )
    if closeout.economic_validity_proven is True:
        raise Step29UTerminalFleetHypothesisRetirementError(
            "CONTRADICTORY_ECONOMIC_VALIDITY_PROVEN"
        )
    if closeout.activation_eligible is True or closeout.step_29u_activated is True:
        raise Step29UTerminalFleetHypothesisRetirementError("CONTRADICTORY_ACTIVATION_CLAIM")

    eligible_ids = {
        o.option_id for o in closeout.recovery_option_inventory if o.status == OPTION_ELIGIBLE
    }
    if SELECTED_RECOVERY_OPTION not in eligible_ids:
        raise Step29UTerminalFleetHypothesisRetirementError("SELECTED_RECOVERY_OPTION_NOT_ELIGIBLE")

    inventory = _build_retirement_inventory_from_fleet(
        fleet=fleet,
        fleet_relpath=CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
    )
    authorized_ids = set(_authorized_fleet_hypothesis_ids(fleet))
    for entry in inventory:
        if entry.hypothesis_id not in authorized_ids:
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"HYPOTHESIS_OUTSIDE_AUTHORIZED_FINAL_FLEET:{entry.hypothesis_id}"
            )

    fleet_digest = _sha256_file(fleet_path)
    sealed_digest = _sha256_file(sealed_path)
    expected_cfg = build_canonical_retirement_config_v0(
        inventory=inventory,
        fleet_digest=fleet_digest,
    )
    retirement_cfg = _load_json(retirement_cfg_path)
    if not isinstance(retirement_cfg, dict):
        raise Step29UTerminalFleetHypothesisRetirementError("RETIREMENT_CONFIG_NOT_OBJECT")
    _validate_retirement_config_against_inventory(
        config=retirement_cfg,
        inventory=inventory,
    )
    # Idempotent: config must match deterministic expected payload for key fields.
    for key in (
        "selected_recovery_option",
        "retired_hypothesis_ids",
        "retired_hypothesis_count",
        "retirement_scope",
        "retirement_reason",
        "economic_validity_status",
        "activation_eligible",
        "activated",
        "automatic_backlog_selection_allowed",
        "next_research_candidate_selected",
        "unchanged_rerun_allowed",
        "unchanged_repromotion_allowed",
        "historical_evidence_preserved",
        "canonical_fleet_closeout_sha256",
    ):
        if retirement_cfg.get(key) != expected_cfg.get(key):
            raise Step29UTerminalFleetHypothesisRetirementError(f"RETIREMENT_CONFIG_DRIFT:{key}")

    # Guard surface: every retired identity is discoverable as retired; external
    # callers must use assert_unchanged_resubmission_blocked_v0 before resubmit.
    for hid in [e.hypothesis_id for e in inventory]:
        if not is_hypothesis_retired_v0(hid, repo_root=root):
            raise Step29UTerminalFleetHypothesisRetirementError(
                f"RETIRED_HYPOTHESIS_NOT_DISCOVERABLE:{hid}"
            )

    reasons.append("OPERATOR_SELECTED_RECOVERY_OPTION=" + SELECTED_RECOVERY_OPTION)
    reasons.append("RETIREMENT_INVENTORY_COMPLETE=true")
    reasons.append("ECONOMIC_VALIDITY_STATUS=FAIL")
    reasons.append("ACTIVATION_ELIGIBLE=false")
    reasons.append("NEXT_RESEARCH_CANDIDATE_SELECTED=false")
    reasons.append("OPERATOR_SELECTION_REQUIRED_FOR_NEXT_MATERIAL_RESEARCH=true")

    retired_ids = tuple(e.hypothesis_id for e in inventory)
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
            schema_version="v0",
            provenance_note="sealed_step29u_economic_validity_result_pr5553",
        ),
        _evidence_ref(
            relpath=RETIREMENT_CONFIG_RELPATH,
            digest=_sha256_file(retirement_cfg_path),
            schema_version=str(retirement_cfg.get("schema_version") or ""),
            provenance_note="retirement_inventory_ssot",
        ),
        _evidence_ref(
            relpath=GOVERNANCE_TERMINAL_BOUNDARY_RELPATH,
            digest=None,
            schema_version="v0",
            provenance_note="governance_terminalization_and_next_material_boundary",
        ),
    )

    return TerminalFleetHypothesisRetirementResultV0(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        capability_id=CAPABILITY_ID,
        status="COMPLETE",
        evaluator_valid=True,
        selected_recovery_option=SELECTED_RECOVERY_OPTION,
        retirement_status=RETIREMENT_STATUS_COMPLETE,
        retirement_inventory_complete=True,
        retired_hypothesis_count=len(retired_ids),
        retired_hypothesis_ids=retired_ids,
        retirement_scope=RETIREMENT_SCOPE,
        retirement_reason=RETIREMENT_REASON,
        historical_evidence_preserved=True,
        unchanged_rerun_allowed=False,
        unchanged_repromotion_allowed=False,
        automatic_backlog_selection_allowed=False,
        next_research_candidate_selected=False,
        operator_selection_required_for_next_material_research=True,
        economic_validity_status=ECON_STATUS_FAIL,
        economic_validity_proven=False,
        activation_eligible=False,
        activated=False,
        retirement_inventory=inventory,
        canonical_evidence=canonical_evidence,
        reasons=tuple(dict.fromkeys(reasons)),
        provenance={
            "package_marker": PACKAGE_MARKER,
            "producer_family": PRODUCER_FAMILY,
            "reuses_economic_failure_closeout": True,
            "reuses_fleet_terminalization": True,
            "no_historical_evidence_mutation": True,
            "no_automatic_backlog_selection": True,
            "no_strategy_hypothesis_invention": True,
            "no_activation": True,
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
            "AUTOMATIC_BACKLOG_SELECTION_ALLOWED": False,
            "NEXT_RESEARCH_CANDIDATE_SELECTED": False,
            "BTC_EXCLUDED": True,
            "SPOT_EXCLUDED": True,
            "KRAKEN_LEGACY_EXCLUDED": True,
        },
        inputs={
            "fleet_closeout_relpath": CANONICAL_FLEET_FAIL_CLOSEOUT_RELPATH,
            "fleet_closeout_digest": fleet_digest,
            "retirement_config_relpath": RETIREMENT_CONFIG_RELPATH,
            "retirement_config_digest": _sha256_file(retirement_cfg_path),
            "sealed_economic_result_relpath": SEALED_ECONOMIC_RESULT_RELPATH,
            "sealed_economic_result_digest": sealed_digest,
            "closeout_status": closeout.economic_closeout_status,
            "closeout_economic_validity_status": closeout.economic_validity_status,
        },
    )


def serialize_result_json_v0(
    result: TerminalFleetHypothesisRetirementResultV0,
) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n"


def result_to_machine_lines(
    result: TerminalFleetHypothesisRetirementResultV0,
) -> list[str]:
    return [
        f"STATUS={result.status}",
        f"EVALUATOR_VALID={str(result.evaluator_valid).lower()}",
        f"SELECTED_RECOVERY_OPTION={result.selected_recovery_option}",
        f"RETIREMENT_STATUS={result.retirement_status}",
        f"RETIREMENT_INVENTORY_COMPLETE={str(result.retirement_inventory_complete).lower()}",
        f"RETIRED_HYPOTHESIS_COUNT={result.retired_hypothesis_count}",
        f"RETIRED_HYPOTHESIS_IDS={list(result.retired_hypothesis_ids)!r}",
        f"RETIREMENT_SCOPE={result.retirement_scope}",
        f"RETIREMENT_REASON={result.retirement_reason}",
        f"HISTORICAL_EVIDENCE_PRESERVED={str(result.historical_evidence_preserved).lower()}",
        f"UNCHANGED_RERUN_ALLOWED={str(result.unchanged_rerun_allowed).lower()}",
        f"UNCHANGED_REPROMOTION_ALLOWED={str(result.unchanged_repromotion_allowed).lower()}",
        f"AUTOMATIC_BACKLOG_SELECTION_ALLOWED="
        f"{str(result.automatic_backlog_selection_allowed).lower()}",
        f"NEXT_RESEARCH_CANDIDATE_SELECTED={str(result.next_research_candidate_selected).lower()}",
        f"OPERATOR_SELECTION_REQUIRED_FOR_NEXT_MATERIAL_RESEARCH="
        f"{str(result.operator_selection_required_for_next_material_research).lower()}",
        f"ECONOMIC_VALIDITY_STATUS={result.economic_validity_status}",
        f"ECONOMIC_VALIDITY_PROVEN={str(result.economic_validity_proven).lower()}",
        f"ACTIVATION_ELIGIBLE={str(result.activation_eligible).lower()}",
        f"STEP_29U_ACTIVATED={str(result.activated).lower()}",
        f"ACTIVATED={str(result.activated).lower()}",
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


__all__ = [
    "CAPABILITY_ID",
    "FORBIDDEN_IMPORT_SURFACES",
    "PACKAGE_MARKER",
    "RETIREMENT_CONFIG_RELPATH",
    "RETIREMENT_REASON",
    "RETIREMENT_SCOPE",
    "RETIREMENT_STATUS_COMPLETE",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "SELECTED_RECOVERY_OPTION",
    "Step29UTerminalFleetHypothesisRetirementError",
    "TerminalFleetHypothesisRetirementOverridesV0",
    "TerminalFleetHypothesisRetirementResultV0",
    "assert_no_forbidden_imports_v0",
    "assert_unchanged_resubmission_blocked_v0",
    "build_canonical_retirement_config_v0",
    "evaluate_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0",
    "is_hypothesis_retired_v0",
    "result_to_machine_lines",
    "serialize_result_json_v0",
]
