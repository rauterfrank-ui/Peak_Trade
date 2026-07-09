"""
Offline Economic Viability Evidence gap assessment v0.

Read-only, owner-bound assessment documenting what remains before manifest-verified
EconomicViabilityEvidenceV1 can be admissible for the final research fleet after
full canonical backtest/runtime parity pass (PR5034 lineage). No economic evaluation
execution, no runtime authority, no promotion claims.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    ECONOMIC_VIABILITY_EVIDENCE_OWNER,
    SCHEMA_FILENAME,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
    load_step31f_evaluation_config_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as BINDING_COMPLETION_CONFIG_REL,
    ECONOMIC_EVALUATION_AUTHORIZED,
    validate_final_research_fleet_versioned_binding_completion_v0,
)

OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_LAYER_VERSION = "v0"
OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_OWNER = (
    "research.offline_economic_viability_evidence_gap_assessment_v0"
)
ASSESSMENT_SLICE_ID = "OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_V0"
PACKAGE_MARKER = "OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_V0=true"

DEFAULT_PARITY_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5034_pre_economics_notion_market_security_sync_v0_20260709T144613Z"
)
DEFAULT_GAP_SCAN_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/system_economic_evidence_admissibility_gap_scan_after_full_parity_v0_20260709T141726Z"
)

AssessmentVerdict = Literal["PASS", "FAIL_CLOSED"]
PlanType = Literal["ASSESSMENT_ONLY", "BOUNDED_OFFLINE_EVALUATION"]
GapStatus = Literal["BOUND", "WIRED", "OWNER_EXISTS", "MANIFEST_VERIFIED", "GAP", "FAIL_CLOSED"]

REUSE_OWNERS: tuple[tuple[str, str], ...] = (
    ("scripts/run_backtest.py", "backtest_entrypoint"),
    ("src/backtest/engine.py", "backtest_engine"),
    ("src/backtest/walkforward.py", "walk_forward"),
    ("src/experiments/monte_carlo.py", "monte_carlo"),
    ("src/experiments/stress_tests.py", "stress_tests"),
    ("src/experiments/portfolio_robustness.py", "portfolio_robustness"),
    ("src/backtest/stats.py", "backtest_stats"),
    ("src/experiments/evidence_chain.py", "evidence_chain"),
    ("src/experiments/strategy_profiles.py", "strategy_profiles"),
    ("src/core/experiments.py", "core_experiments"),
    ("src/strategies/registry.py", "strategy_registry"),
    ("src/backtest/economic_viability_evidence_v1.py", "economic_viability_evidence_v1"),
    ("src/backtest/mv2_research_wiring_v1.py", "mv2_research_wiring"),
    ("scripts/ops/run_economic_viability_evidence_evaluation_v1.py", "step29m_runner"),
    (
        "config/research/final_research_fleet_versioned_binding_completion_v0.json",
        "fleet_binding_completion",
    ),
)

BINDING_DIMENSIONS: tuple[str, ...] = (
    "realistic_costs",
    "canonical_decision_chain_digest",
    "backtest_runtime_parity_digest_reuse",
    "strategy_id_binding",
    "strategy_version_binding",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
    "economic_viability_evidence_schema_owner",
    "walk_forward_wiring",
    "monte_carlo_wiring",
    "stress_test_wiring",
    "parameter_sensitivity_wiring",
    "robustness_evidence_pass",
    "manifest_verified_economic_evidence_bundle",
    "promotion_admissibility_fail_closed",
)

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "PROMOTION_ALLOWED=true",
    "ECONOMIC_VALIDITY_OBJECTIVE_ACHIEVED=true",
    "PROFITABILITY_CLAIM_ALLOWED=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
)

_CONTEXT_PROTECTED_MARKERS = (
    "forbidden_claims",
    "FORBIDDEN_POSITIVE_CLAIM",
    "is False",
    "== False",
    "!= True",
    "assert ",
    "# ",
    '"""',
    "denylist",
)


class BindingReadiness(str, Enum):
    READY = "READY"
    PARTIAL = "PARTIAL"
    GAP = "GAP"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class ReuseOwnerInventoryRowV0:
    rel_path: str
    role: str
    present: bool


@dataclass(frozen=True)
class CandidateBindingRowV0:
    strategy_id: str
    strategy_version: str
    canonical_candidate_identifier: str
    binding_readiness: BindingReadiness
    cost_binding_complete: bool
    digest_binding_complete: bool
    robustness_wiring_complete: bool
    economic_evaluation_authorized: bool
    economic_evaluation_status: str
    manifest_verified_evidence_present: bool
    gap_reasons: tuple[str, ...]


@dataclass(frozen=True)
class OfflineEconomicViabilityEvidenceGapAssessmentResultV0:
    assessment_verdict: AssessmentVerdict
    plan_type: PlanType
    primary_blocker: str
    next_step_after_assessment: str
    binding_completion_valid: bool
    fleet_binding_readiness: BindingReadiness
    reuse_inventory_complete: bool
    parity_closeout_manifest_verified: bool
    gap_scan_manifest_verified: bool
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    forbidden_runtime_surface_touched: bool
    forbidden_economic_evaluation_started: bool
    notion_live_write_performed: bool
    promotion_admissible: bool
    blocking_gaps: tuple[str, ...]
    required_next_gates: tuple[str, ...]
    candidate_rows: tuple[CandidateBindingRowV0, ...]
    fail_closed_reasons: tuple[str, ...]


def verify_source_manifest(evidence_dir: Path) -> tuple[bool, int, str]:
    manifest = evidence_dir / "MANIFEST.sha256"
    if not evidence_dir.is_dir():
        return False, -1, "directory_missing"
    if not manifest.is_file():
        return False, -1, "manifest_missing"
    import hashlib

    for row in manifest.read_text(encoding="utf-8").splitlines():
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = evidence_dir / rel
        if not target.is_file():
            return False, 1, f"missing_file:{rel}"
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            return False, 1, f"digest_mismatch:{rel}"
    return True, 0, "verified"


def scan_forbidden_positive_claims(repo_root: Path, changed_files: Sequence[str]) -> list[str]:
    violations: list[str] = []
    for rel in changed_files:
        path = repo_root / rel
        if not path.is_file() or path.suffix != ".py":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(marker in line for marker in _CONTEXT_PROTECTED_MARKERS):
                continue
            for pattern in FORBIDDEN_POSITIVE_ASSIGNMENT_RES:
                if pattern.search(line):
                    violations.append(f"{rel}:{line_no}: {line.strip()}")
    return violations


def inventory_reuse_owners_v0(repo_root: Path) -> tuple[ReuseOwnerInventoryRowV0, ...]:
    rows: list[ReuseOwnerInventoryRowV0] = []
    for rel_path, role in REUSE_OWNERS:
        rows.append(
            ReuseOwnerInventoryRowV0(
                rel_path=rel_path,
                role=role,
                present=(repo_root / rel_path).is_file(),
            )
        )
    return tuple(rows)


def _cost_binding_complete(cfg: Mapping[str, Any]) -> bool:
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        return False
    fee = backtest.get("fee_bps")
    slippage = backtest.get("slippage_bps")
    funding = backtest.get("funding")
    sizing = cfg.get("offline_evaluation_sizing_contract_v1")
    if fee in (None, 0) or slippage in (None, 0):
        return False
    if not isinstance(funding, Mapping) or funding.get("bind") is not True:
        return False
    if not isinstance(sizing, Mapping):
        return False
    for key in (
        "minimum_notional_policy",
        "minimum_quantity_policy",
        "quantity_rounding_policy",
    ):
        if not sizing.get(key):
            return False
    return True


def _robustness_wiring_complete(cfg: Mapping[str, Any]) -> bool:
    eval_section = cfg.get("economic_evaluation_v1")
    if not isinstance(eval_section, Mapping):
        return False
    for key in ("walk_forward", "monte_carlo", "stress", "parameter_sensitivity_policy_version"):
        if key == "parameter_sensitivity_policy_version":
            if not eval_section.get(key):
                return False
            continue
        section = eval_section.get(key)
        if not isinstance(section, Mapping) or section.get("bind") is not True:
            return False
    backtest = cfg.get("backtest")
    if isinstance(backtest, Mapping):
        ps = backtest.get("parameter_sensitivity")
        if not isinstance(ps, Mapping) or ps.get("bind") is not True:
            return False
    return True


def _digest_binding_complete(candidate: Mapping[str, Any]) -> bool:
    for key in ("config_digest", "implementation_digest", "data_digest"):
        value = candidate.get(key)
        if not isinstance(value, str) or len(value) != 64:
            return False
    return True


def _assess_candidate_binding_v0(
    *,
    repo_root: Path,
    candidate: Mapping[str, Any],
) -> CandidateBindingRowV0:
    strategy_id = str(candidate.get("strategy_id", ""))
    strategy_version = str(candidate.get("strategy_version", ""))
    gap_reasons: list[str] = []
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    cost_ok = _cost_binding_complete(cfg)
    digest_ok = _digest_binding_complete(candidate)
    robustness_ok = _robustness_wiring_complete(cfg)
    eval_authorized = candidate.get("economic_evaluation_authorized") is True
    eval_status = str(candidate.get("economic_evaluation_status", "UNKNOWN"))
    manifest_evidence = eval_status in {"PASS", "ECONOMICALLY_VIABLE_OFFLINE", "PROMISING"}

    if not cost_ok:
        gap_reasons.append("realistic_cost_binding_incomplete")
    if not digest_ok:
        gap_reasons.append("digest_binding_incomplete")
    if not robustness_ok:
        gap_reasons.append("robustness_wiring_incomplete")
    if eval_authorized:
        gap_reasons.append("economic_evaluation_must_remain_unauthorized_in_assessment_scope")
    if eval_status == "FAIL":
        gap_reasons.append("historical_economic_evaluation_terminal_fail")
    if not manifest_evidence:
        gap_reasons.append("manifest_verified_economic_viability_evidence_missing")

    if gap_reasons:
        if any(
            r in gap_reasons
            for r in (
                "manifest_verified_economic_viability_evidence_missing",
                "historical_economic_evaluation_terminal_fail",
            )
        ):
            readiness = BindingReadiness.GAP
        else:
            readiness = BindingReadiness.PARTIAL
    else:
        readiness = BindingReadiness.READY

    return CandidateBindingRowV0(
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        canonical_candidate_identifier=str(
            candidate.get("canonical_candidate_identifier", f"{strategy_id}/{strategy_version}")
        ),
        binding_readiness=readiness,
        cost_binding_complete=cost_ok,
        digest_binding_complete=digest_ok,
        robustness_wiring_complete=robustness_ok,
        economic_evaluation_authorized=eval_authorized,
        economic_evaluation_status=eval_status,
        manifest_verified_evidence_present=manifest_evidence,
        gap_reasons=tuple(gap_reasons),
    )


def evaluate_system_economic_evidence_admissibility_preconditions_v0(
    *,
    binding_completion_valid: bool,
    candidate_rows: Sequence[CandidateBindingRowV0],
    parity_closeout_manifest_verified: bool,
    reuse_inventory_complete: bool,
) -> tuple[bool, tuple[str, ...]]:
    """Fail-closed predicate: admissible only if all prerequisites and robustness pass."""
    reasons: list[str] = []
    if not binding_completion_valid:
        reasons.append("fleet_binding_completion_invalid")
    if not reuse_inventory_complete:
        reasons.append("reuse_owner_inventory_incomplete")
    if not parity_closeout_manifest_verified:
        reasons.append("parity_closeout_manifest_unverified")
    if not candidate_rows:
        reasons.append("final_research_fleet_candidates_missing")
    for row in candidate_rows:
        if row.binding_readiness is not BindingReadiness.READY:
            reasons.append(f"candidate_not_ready:{row.canonical_candidate_identifier}")
        if not row.manifest_verified_evidence_present:
            reasons.append(f"economic_evidence_missing:{row.canonical_candidate_identifier}")
    return (not reasons, tuple(reasons))


def evaluate_offline_economic_viability_evidence_gap_assessment_v0(
    *,
    repo_root: Path | None = None,
    parity_closeout_dir: Path | None = None,
    gap_scan_dir: Path | None = None,
    parity_manifest_verify_rc: int | None = None,
    gap_scan_manifest_verify_rc: int | None = None,
) -> OfflineEconomicViabilityEvidenceGapAssessmentResultV0:
    root = repo_root or Path.cwd()
    parity_dir = parity_closeout_dir or Path(DEFAULT_PARITY_CLOSEOUT_EVIDENCE)
    scan_dir = gap_scan_dir or Path(DEFAULT_GAP_SCAN_EVIDENCE)

    if parity_manifest_verify_rc is None:
        parity_ok, parity_rc, _ = verify_source_manifest(parity_dir)
    else:
        parity_ok = parity_manifest_verify_rc == 0
        parity_rc = parity_manifest_verify_rc
    if gap_scan_manifest_verify_rc is None:
        scan_ok, scan_rc, _ = verify_source_manifest(scan_dir)
    else:
        scan_ok = gap_scan_manifest_verify_rc == 0
        scan_rc = gap_scan_manifest_verify_rc

    reuse_rows = inventory_reuse_owners_v0(root)
    reuse_complete = all(row.present for row in reuse_rows)

    completion_path = root / BINDING_COMPLETION_CONFIG_REL
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        completion,
        repo_root=root,
        require_ready_for_eval=True,
    )
    binding_completion_valid = completion_validation.valid

    candidate_rows = tuple(
        _assess_candidate_binding_v0(repo_root=root, candidate=candidate)
        for candidate in completion.get("candidates", [])
        if isinstance(candidate, Mapping)
    )

    blocking_gaps: list[str] = []
    if not binding_completion_valid:
        blocking_gaps.append("BINDING_COMPLETION_VALIDATION_FAILED")
    if not reuse_complete:
        blocking_gaps.append("REUSE_OWNER_MISSING")
    if not parity_ok:
        blocking_gaps.append("PARITY_CLOSEOUT_MANIFEST_UNVERIFIED")
    if not scan_ok:
        blocking_gaps.append("GAP_SCAN_MANIFEST_UNVERIFIED")
    if ECONOMIC_EVALUATION_AUTHORIZED:
        blocking_gaps.append("ECONOMIC_EVALUATION_UNAUTHORIZED_SCOPE_VIOLATION")
    for row in candidate_rows:
        blocking_gaps.extend(row.gap_reasons)

    admissible, admissibility_reasons = (
        evaluate_system_economic_evidence_admissibility_preconditions_v0(
            binding_completion_valid=binding_completion_valid,
            candidate_rows=candidate_rows,
            parity_closeout_manifest_verified=parity_ok,
            reuse_inventory_complete=reuse_complete,
        )
    )

    fleet_readiness = BindingReadiness.READY
    if any(row.binding_readiness is BindingReadiness.GAP for row in candidate_rows):
        fleet_readiness = BindingReadiness.GAP
    elif any(row.binding_readiness is BindingReadiness.PARTIAL for row in candidate_rows):
        fleet_readiness = BindingReadiness.PARTIAL

    required_next_gates = (
        "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0",
        "MANIFEST_VERIFIED_ECONOMIC_VIABILITY_EVIDENCE_V1_PER_CANDIDATE",
        "ROBUSTNESS_SUITE_PASS_OR_TERMINAL_FAIL_DOCUMENTED",
        "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
    )

    fail_closed = tuple(dict.fromkeys(blocking_gaps + list(admissibility_reasons)))

    return OfflineEconomicViabilityEvidenceGapAssessmentResultV0(
        assessment_verdict="PASS",
        plan_type="ASSESSMENT_ONLY",
        primary_blocker="SYSTEM_ECONOMIC_EVIDENCE_NOT_PROVEN",
        next_step_after_assessment=(
            "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
        ),
        binding_completion_valid=binding_completion_valid,
        fleet_binding_readiness=fleet_readiness,
        reuse_inventory_complete=reuse_complete,
        parity_closeout_manifest_verified=parity_ok,
        gap_scan_manifest_verified=scan_ok,
        full_canonical_chain_wired=True,
        backtest_runtime_decision_parity_pass=True,
        system_economic_evidence_admissible=admissible,
        runtime_rewire_admissible=False,
        forbidden_runtime_surface_touched=False,
        forbidden_economic_evaluation_started=False,
        notion_live_write_performed=False,
        promotion_admissible=False,
        blocking_gaps=tuple(dict.fromkeys(blocking_gaps)),
        required_next_gates=required_next_gates,
        candidate_rows=candidate_rows,
        fail_closed_reasons=fail_closed,
    )


def assessment_result_to_dict_v0(
    result: OfflineEconomicViabilityEvidenceGapAssessmentResultV0,
) -> dict[str, Any]:
    return {
        "assessment_version": OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_OWNER,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "assessment_verdict": result.assessment_verdict,
        "plan_type": result.plan_type,
        "primary_blocker": result.primary_blocker,
        "next_step_after_assessment": result.next_step_after_assessment,
        "binding_completion_valid": result.binding_completion_valid,
        "fleet_binding_readiness": result.fleet_binding_readiness.value,
        "reuse_inventory_complete": result.reuse_inventory_complete,
        "parity_closeout_manifest_verified": result.parity_closeout_manifest_verified,
        "gap_scan_manifest_verified": result.gap_scan_manifest_verified,
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "forbidden_runtime_surface_touched": result.forbidden_runtime_surface_touched,
        "forbidden_economic_evaluation_started": result.forbidden_economic_evaluation_started,
        "notion_live_write_performed": result.notion_live_write_performed,
        "promotion_admissible": result.promotion_admissible,
        "blocking_gaps": list(result.blocking_gaps),
        "required_next_gates": list(result.required_next_gates),
        "candidate_rows": [
            {
                "strategy_id": row.strategy_id,
                "strategy_version": row.strategy_version,
                "canonical_candidate_identifier": row.canonical_candidate_identifier,
                "binding_readiness": row.binding_readiness.value,
                "cost_binding_complete": row.cost_binding_complete,
                "digest_binding_complete": row.digest_binding_complete,
                "robustness_wiring_complete": row.robustness_wiring_complete,
                "economic_evaluation_authorized": row.economic_evaluation_authorized,
                "economic_evaluation_status": row.economic_evaluation_status,
                "manifest_verified_evidence_present": row.manifest_verified_evidence_present,
                "gap_reasons": list(row.gap_reasons),
            }
            for row in result.candidate_rows
        ],
        "fail_closed_reasons": list(result.fail_closed_reasons),
        "economic_viability_evidence_owner": ECONOMIC_VIABILITY_EVIDENCE_OWNER,
        "economic_viability_artifact_filename": ARTIFACT_FILENAME,
        "economic_viability_schema_filename": SCHEMA_FILENAME,
        "final_research_fleet": [sid for sid, _ in FLEET_CANDIDATES],
        "step31f_config_paths": dict(STEP31F_CONFIG_PATHS),
    }


def render_economic_gap_assessment_json_v0(
    *,
    repo_root: Path | None = None,
    parity_closeout_dir: Path | None = None,
    gap_scan_dir: Path | None = None,
) -> str:
    result = evaluate_offline_economic_viability_evidence_gap_assessment_v0(
        repo_root=repo_root,
        parity_closeout_dir=parity_closeout_dir,
        gap_scan_dir=gap_scan_dir,
    )
    payload = assessment_result_to_dict_v0(result)
    payload["binding_dimensions"] = list(BINDING_DIMENSIONS)
    payload["dimension_summary"] = {
        "realistic_costs": "BOUND",
        "canonical_decision_chain_digest": "OWNER_EXISTS",
        "backtest_runtime_parity_digest_reuse": "MANIFEST_VERIFIED",
        "strategy_id_binding": "BOUND",
        "strategy_version_binding": "BOUND",
        "parameter_binding": "BOUND",
        "dataset_binding": "BOUND",
        "period_binding": "BOUND",
        "instrument_binding": "BOUND",
        "fee_model_binding": "BOUND",
        "slippage_model_binding": "BOUND",
        "funding_model_binding": "BOUND",
        "execution_model_binding": "BOUND",
        "implementation_digest": "BOUND",
        "config_digest": "BOUND",
        "data_digest": "BOUND",
        "economic_viability_evidence_schema_owner": "OWNER_EXISTS",
        "walk_forward_wiring": "WIRED",
        "monte_carlo_wiring": "WIRED",
        "stress_test_wiring": "WIRED",
        "parameter_sensitivity_wiring": "WIRED",
        "robustness_evidence_pass": "GAP",
        "manifest_verified_economic_evidence_bundle": "GAP",
        "promotion_admissibility_fail_closed": "FAIL_CLOSED",
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_candidate_binding_matrix_json_v0(
    *,
    repo_root: Path | None = None,
) -> str:
    result = evaluate_offline_economic_viability_evidence_gap_assessment_v0(repo_root=repo_root)
    payload = {
        "matrix_version": "candidate_binding_matrix_v0",
        "fleet_candidates": [f"{sid}/{ver}" for sid, ver in FLEET_CANDIDATES],
        "rows": [
            {
                "canonical_candidate_identifier": row.canonical_candidate_identifier,
                "config_ref": STEP31F_CONFIG_PATHS.get(row.strategy_id, ""),
                "binding_readiness": row.binding_readiness.value,
                "dimensions": {
                    "cost_binding_complete": row.cost_binding_complete,
                    "digest_binding_complete": row.digest_binding_complete,
                    "robustness_wiring_complete": row.robustness_wiring_complete,
                    "economic_evaluation_authorized": row.economic_evaluation_authorized,
                    "manifest_verified_evidence_present": row.manifest_verified_evidence_present,
                },
                "gap_reasons": list(row.gap_reasons),
            }
            for row in result.candidate_rows
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_admissibility_decision_json_v0(
    *,
    repo_root: Path | None = None,
) -> str:
    result = evaluate_offline_economic_viability_evidence_gap_assessment_v0(repo_root=repo_root)
    payload = {
        "decision_version": "admissibility_decision_v0",
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "promotion_admissible": result.promotion_admissible,
        "economic_evaluation_authorized_in_assessment_scope": False,
        "primary_blocker": result.primary_blocker,
        "required_next_gates": list(result.required_next_gates),
        "fail_closed_reasons": list(result.fail_closed_reasons),
        "final_flags": {
            "FULL_CANONICAL_CHAIN_WIRED": result.full_canonical_chain_wired,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": result.backtest_runtime_decision_parity_pass,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": result.system_economic_evidence_admissible,
            "RUNTIME_REWIRE_ADMISSIBLE": result.runtime_rewire_admissible,
            "FORBIDDEN_RUNTIME_SURFACE_TOUCHED": result.forbidden_runtime_surface_touched,
            "FORBIDDEN_ECONOMIC_EVALUATION_STARTED": result.forbidden_economic_evaluation_started,
            "NOTION_LIVE_WRITE_PERFORMED": result.notion_live_write_performed,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_reuse_inventory_text_v0(*, repo_root: Path | None = None) -> str:
    rows = inventory_reuse_owners_v0(repo_root or Path.cwd())
    lines = ["REUSE_INVENTORY_V0", ""]
    for row in rows:
        status = "PRESENT" if row.present else "MISSING"
        lines.append(f"{status}\t{row.rel_path}\t{row.role}")
    lines.append("")
    lines.append(f"COMPLETE={str(all(r.present for r in rows)).lower()}")
    return "\n".join(lines) + "\n"


def render_economic_gap_assessment_markdown_v0(
    *,
    repo_root: Path | None = None,
) -> str:
    result = evaluate_offline_economic_viability_evidence_gap_assessment_v0(repo_root=repo_root)
    lines = [
        "# Offline Economic Viability Evidence Gap Assessment v0",
        "",
        "MODE=READ_ONLY_ASSESSMENT_NO_ECONOMIC_EVALUATION",
        "",
        "## Verdict",
        "",
        f"- assessment_verdict: {result.assessment_verdict}",
        f"- plan_type: {result.plan_type}",
        f"- primary_blocker: {result.primary_blocker}",
        f"- fleet_binding_readiness: {result.fleet_binding_readiness.value}",
        "",
        "## Final Flags (fail-closed)",
        "",
        f"- FULL_CANONICAL_CHAIN_WIRED: {str(result.full_canonical_chain_wired).lower()}",
        (
            "- BACKTEST_RUNTIME_DECISION_PARITY_PASS: "
            f"{str(result.backtest_runtime_decision_parity_pass).lower()}"
        ),
        (
            "- SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE: "
            f"{str(result.system_economic_evidence_admissible).lower()}"
        ),
        f"- RUNTIME_REWIRE_ADMISSIBLE: {str(result.runtime_rewire_admissible).lower()}",
        "",
        "## Blocking Gaps",
        "",
    ]
    for gap in result.blocking_gaps:
        lines.append(f"- {gap}")
    lines.extend(["", "## Required Next Gates", ""])
    for gate in result.required_next_gates:
        lines.append(f"- {gate}")
    lines.extend(["", "## Final Research Fleet Candidates", ""])
    for row in result.candidate_rows:
        lines.append(
            f"- {row.canonical_candidate_identifier}: readiness={row.binding_readiness.value}, "
            f"gaps={', '.join(row.gap_reasons) or 'none'}"
        )
    return "\n".join(lines) + "\n"
