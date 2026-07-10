"""
Runtime Bridge Boundary Gap Assessment v0.

Read-only assessment documenting the remaining runtime-bridge boundary gap after
PR #5025 pre-activation gate assessment. Consumes manifest-verified PR5025 source
evidence, evaluates trace-chain binding completeness, and determines whether a
narrow reuse-first offline boundary rewire is justified without activating runtime,
granting order authority, or promoting final success flags.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_LAYER_VERSION = "v0"
RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_OWNER = (
    "trading.master_v2.runtime_bridge_boundary_gap_assessment_v0"
)
ASSESSMENT_SLICE_ID = "RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_V0"
PACKAGE_MARKER = "RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_V0=true"

DEFAULT_PR5025_SOURCE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/runtime_bridge_pre_activation_gate_assessment_v0_20260708T234554Z"
)

AssessmentVerdict = Literal["PASS", "FAIL_CLOSED"]
PlanType = Literal["ASSESSMENT_ONLY", "NARROW_REUSE_FIRST_REWIRE"]
BoundaryGapStatus = Literal[
    "FAIL_CLOSED_DOCUMENTED",
    "UNEXPECTED_REWIRE_JUSTIFIED",
    "EVALUATION_ERROR",
]

REASON_SOURCE_MANIFEST_UNVERIFIED = "SOURCE_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_PR5025_SOURCE_MISSING = "PR5025_PRE_ACTIVATION_GATE_ASSESSMENT_EVIDENCE_MISSING"
REASON_PRE_ACTIVATION_GATE_NOT_DOCUMENTED = "PRE_ACTIVATION_GATE_NOT_FAIL_CLOSED_DOCUMENTED"
REASON_TRACE_CHAIN_INCOMPLETE = "TRACE_CHAIN_SURFACE_BINDING_INCOMPLETE"
REASON_RUNTIME_BRIDGE_NOT_BOUND = "RUNTIME_BRIDGE_NOT_BOUND_NOT_ACTIVATED"
REASON_OFFLINE_PARITY_INCOMPLETE = "OFFLINE_PARITY_NOT_COMPLETE"
REASON_NARROW_REWIRE_UNEXPECTEDLY_JUSTIFIED = "NARROW_REWIRE_JUSTIFIED_UNEXPECTED_AT_CURRENT_HEAD"

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "CLAIM_PROMOTION_ALLOWED=true",
    "RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE=true",
    "NARROW_REWIRE_JUSTIFIED=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"CLAIM_PROMOTION_ALLOWED\s*=\s*True\b"),
    re.compile(r"RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"NARROW_REWIRE_JUSTIFIED\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
    re.compile(r'"claim_promotion_allowed"\s*:\s*true\b'),
    re.compile(r'"runtime_bridge_activation_admissible"\s*:\s*true\b'),
    re.compile(r'"narrow_rewire_justified"\s*:\s*true\b'),
)

_CONTEXT_PROTECTED_MARKERS = (
    "forbidden_claims",
    "FORBIDDEN_POSITIVE_CLAIM",
    "FORBIDDEN_POSITIVE_ASSIGNMENT",
    '_claimed": False',
    "is False",
    "== False",
    "!= True",
    "assert ",
    "# ",
    '"""',
    "'''",
    "unless fully proven",
    "denylist",
    "needle",
)


@dataclass(frozen=True)
class SourceEvidenceRefV0:
    evidence_id: str
    path: str
    present: bool
    manifest_present: bool
    manifest_verified: bool
    detail: str


@dataclass(frozen=True)
class RuntimeBridgeBoundaryGapAssessmentResultV0:
    assessment_verdict: AssessmentVerdict
    boundary_gap_status: BoundaryGapStatus
    plan_type: PlanType
    narrow_rewire_justified: bool
    narrow_rewire_admissible: bool
    trace_next_unbound_node: str
    chain_surface_binding_complete: bool
    runtime_bridge_boundary_status: str
    runtime_bridge_pre_activation_gate_status: str
    runtime_bridge_activation_admissible: bool
    offline_parity_complete_runtime_activation_pending: bool
    surface_p_registry_status: str
    surface_p_semantic_post_status: str
    canonical_runtime_entrypoint_status: str
    blocking_reasons: Tuple[str, ...]
    required_next_gates: Tuple[str, ...]
    primary_blocker: str
    next_step_after_pr: str
    source_evidence_referenced: bool
    source_manifest_verify_rc: int
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    claim_promotion_allowed: bool
    no_runtime_authority_confirmed: bool
    no_economic_claim_confirmed: bool
    no_runtime_evidence_before_core_system_complete: bool
    fail_closed_reasons: Tuple[str, ...]


def _line_context_protected(line: str) -> bool:
    lowered = line.lower()
    for marker in _CONTEXT_PROTECTED_MARKERS:
        if marker in line or marker in lowered:
            return True
    for literal in FORBIDDEN_POSITIVE_CLAIM_LITERALS:
        if literal in line and ("forbidden" in lowered or "deny" in lowered or "needle" in lowered):
            return True
    return False


def scan_forbidden_positive_claims(repo_root: Path, changed_files: list[str]) -> list[str]:
    violations: list[str] = []
    for rel in changed_files:
        path = repo_root / rel
        if not path.is_file() or path.suffix != ".py":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _line_context_protected(line):
                continue
            for pattern in FORBIDDEN_POSITIVE_ASSIGNMENT_RES:
                if pattern.search(line):
                    violations.append(f"{rel}:{line_no}: {line.strip()}")
    return violations


def verify_source_manifest(evidence_dir: Path) -> tuple[bool, int, str]:
    manifest = evidence_dir / "MANIFEST.sha256"
    if not evidence_dir.is_dir():
        return False, -1, "directory_missing"
    if not manifest.is_file():
        return False, -1, "manifest_missing"
    rows = manifest.read_text(encoding="utf-8").splitlines()
    for row in rows:
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = evidence_dir / rel
        if not target.is_file():
            return False, 1, f"missing_file:{rel}"
        import hashlib

        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            return False, 1, f"digest_mismatch:{rel}"
    return True, 0, "verified"


def collect_source_evidence_refs(
    *,
    pr5025_source_dir: Path | None = None,
) -> Tuple[SourceEvidenceRefV0, ...]:
    source = pr5025_source_dir or Path(DEFAULT_PR5025_SOURCE_EVIDENCE)
    present = source.is_dir()
    manifest_present = present and (source / "MANIFEST.sha256").is_file()
    if manifest_present:
        verified, rc, detail = verify_source_manifest(source)
        return (
            SourceEvidenceRefV0(
                evidence_id="pr5025_pre_activation_gate_assessment",
                path=str(source),
                present=True,
                manifest_present=True,
                manifest_verified=verified,
                detail=detail if verified else f"rc={rc}:{detail}",
            ),
        )
    return (
        SourceEvidenceRefV0(
            evidence_id="pr5025_pre_activation_gate_assessment",
            path=str(source),
            present=present,
            manifest_present=False,
            manifest_verified=False,
            detail="missing" if not present else "manifest_missing",
        ),
    )


def _trace_matrix_snapshot_v0(repo_root: Path) -> tuple[str, bool]:
    from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
    from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
        build_trace_matrix,
        compute_chain_surface_binding_complete,
        compute_next_unbound_node,
    )

    inventory = build_inventory(repo_root)
    matrix = build_trace_matrix(inventory)
    edges = matrix["trace_edges"]
    return (
        compute_next_unbound_node(edges),
        compute_chain_surface_binding_complete(edges),
    )


def _narrow_rewire_justified_v0(
    *,
    trace_next_unbound_node: str,
    chain_surface_binding_complete: bool,
    offline_parity_complete_runtime_activation_pending: bool,
    runtime_bridge_boundary_status: str,
) -> bool:
    """True only when a concrete offline trace/boundary node remains unbound."""
    if trace_next_unbound_node != "NONE":
        return True
    if not chain_surface_binding_complete:
        return True
    if (
        offline_parity_complete_runtime_activation_pending
        and runtime_bridge_boundary_status == "BOUND_NOT_ACTIVATED"
    ):
        return False
    return False


def evaluate_runtime_bridge_boundary_gap_assessment_v0(
    *,
    repo_root: Path | None = None,
    pr5025_source_dir: Path | None = None,
    source_manifest_verify_rc: int | None = None,
) -> RuntimeBridgeBoundaryGapAssessmentResultV0:
    """Document runtime-bridge boundary gap; never grants runtime authority."""
    from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
        INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    )
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        NEXT_RECOMMENDED_SLICE,
        parity_surface_assessments_v0,
    )
    from trading.master_v2.legacy_runtime_entrypoint_guard_v0 import (
        CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
    )
    from trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0 import (
        evaluate_runtime_bridge_pre_activation_gate_assessment_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        surface_p_offline_parity_complete_runtime_activation_pending_v0,
    )
    from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
        DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE,
        evaluate_surface_p_semantic_parity_gap_assessment_v0,
    )

    root = repo_root or Path(__file__).resolve().parents[3]
    fail_reasons: list[str] = []
    source_refs = collect_source_evidence_refs(pr5025_source_dir=pr5025_source_dir)
    source_ref = source_refs[0]
    source_evidence_referenced = source_ref.present
    manifest_rc = (
        source_manifest_verify_rc
        if source_manifest_verify_rc is not None
        else (0 if source_ref.manifest_verified else -1)
    )
    if not source_ref.present:
        fail_reasons.append(REASON_PR5025_SOURCE_MISSING)
    elif manifest_rc != 0:
        fail_reasons.append(REASON_SOURCE_MANIFEST_UNVERIFIED)

    pre_activation = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        source_manifest_verify_rc=manifest_rc if manifest_rc != -1 else None,
    )
    if pre_activation.assessment_verdict != "PASS":
        fail_reasons.append(REASON_PRE_ACTIVATION_GATE_NOT_DOCUMENTED)
    if pre_activation.runtime_bridge_pre_activation_gate_status != "FAIL":
        fail_reasons.append(REASON_PRE_ACTIVATION_GATE_NOT_DOCUMENTED)

    trace_next_unbound, chain_binding_complete = _trace_matrix_snapshot_v0(root)
    if not chain_binding_complete:
        fail_reasons.append(REASON_TRACE_CHAIN_INCOMPLETE)

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    surface_p_registry_status = surface_p.parity_status

    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    semantic = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=proof_bundle if proof_bundle.is_dir() else None,
        source_manifest_verify_rc=manifest_rc if manifest_rc != -1 else None,
    )
    surface_p_semantic_post_status = semantic.surface_p_post_status
    if not semantic.offline_four_way_fixtures_complete:
        fail_reasons.append(REASON_OFFLINE_PARITY_INCOMPLETE)

    offline_pending = surface_p_offline_parity_complete_runtime_activation_pending_v0()
    runtime_bridge_boundary_status = CANONICAL_RUNTIME_ENTRYPOINT_STATUS
    if runtime_bridge_boundary_status != INTEGRATION_STATUS_BOUND_NOT_ACTIVATED:
        fail_reasons.append(REASON_RUNTIME_BRIDGE_NOT_BOUND)

    narrow_rewire_justified = _narrow_rewire_justified_v0(
        trace_next_unbound_node=trace_next_unbound,
        chain_surface_binding_complete=chain_binding_complete,
        offline_parity_complete_runtime_activation_pending=offline_pending,
        runtime_bridge_boundary_status=runtime_bridge_boundary_status,
    )
    if narrow_rewire_justified:
        fail_reasons.append(REASON_NARROW_REWIRE_UNEXPECTEDLY_JUSTIFIED)

    plan_type: PlanType = (
        "NARROW_REUSE_FIRST_REWIRE" if narrow_rewire_justified else "ASSESSMENT_ONLY"
    )
    if narrow_rewire_justified:
        boundary_gap_status: BoundaryGapStatus = "UNEXPECTED_REWIRE_JUSTIFIED"
    elif (
        pre_activation.gate_assessment_status == "FAIL_CLOSED_DOCUMENTED"
        and chain_binding_complete
        and trace_next_unbound == "NONE"
        and offline_pending
        and runtime_bridge_boundary_status == INTEGRATION_STATUS_BOUND_NOT_ACTIVATED
    ):
        boundary_gap_status = "FAIL_CLOSED_DOCUMENTED"
    else:
        boundary_gap_status = "EVALUATION_ERROR"

    primary_blocker = pre_activation.primary_blocker
    next_step_after_pr = (
        NEXT_RECOMMENDED_SLICE if not narrow_rewire_justified else trace_next_unbound
    )

    assessment_verdict: AssessmentVerdict = (
        "PASS"
        if (
            boundary_gap_status == "FAIL_CLOSED_DOCUMENTED"
            and plan_type == "ASSESSMENT_ONLY"
            and not narrow_rewire_justified
            and manifest_rc == 0
            and pre_activation.runtime_bridge_pre_activation_gate_status == "FAIL"
            and not pre_activation.runtime_bridge_activation_admissible
            and pre_activation.no_runtime_authority_confirmed
            and pre_activation.no_economic_claim_confirmed
        )
        else "FAIL_CLOSED"
    )

    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        build_surface_p_final_flags_evidence_input_v0,
        evaluate_surface_p_final_flags_fail_closed_contract_v0,
    )

    final_flags = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        build_surface_p_final_flags_evidence_input_v0(
            source_manifest_verify_rc=manifest_rc,
            surface_p_parity_suite_confirmed=(
                offline_pending and surface_p_semantic_post_status == "PASS"
            ),
            runtime_bridge_binding_status=runtime_bridge_boundary_status,  # type: ignore[arg-type]
        )
    )

    return RuntimeBridgeBoundaryGapAssessmentResultV0(
        assessment_verdict=assessment_verdict,
        boundary_gap_status=boundary_gap_status,
        plan_type=plan_type,
        narrow_rewire_justified=narrow_rewire_justified,
        narrow_rewire_admissible=False,
        trace_next_unbound_node=trace_next_unbound,
        chain_surface_binding_complete=chain_binding_complete,
        runtime_bridge_boundary_status=runtime_bridge_boundary_status,
        runtime_bridge_pre_activation_gate_status=(
            pre_activation.runtime_bridge_pre_activation_gate_status
        ),
        runtime_bridge_activation_admissible=pre_activation.runtime_bridge_activation_admissible,
        offline_parity_complete_runtime_activation_pending=offline_pending,
        surface_p_registry_status=surface_p_registry_status,
        surface_p_semantic_post_status=surface_p_semantic_post_status,
        canonical_runtime_entrypoint_status=CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        blocking_reasons=pre_activation.blocking_reasons,
        required_next_gates=pre_activation.required_next_gates,
        primary_blocker=primary_blocker,
        next_step_after_pr=next_step_after_pr,
        source_evidence_referenced=source_evidence_referenced,
        source_manifest_verify_rc=manifest_rc,
        full_canonical_chain_wired=final_flags.full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=final_flags.backtest_runtime_decision_parity_pass,
        system_economic_evidence_admissible=final_flags.system_economic_evidence_admissible,
        runtime_rewire_admissible=False,
        claim_promotion_allowed=False,
        no_runtime_authority_confirmed=True,
        no_economic_claim_confirmed=True,
        no_runtime_evidence_before_core_system_complete=True,
        fail_closed_reasons=tuple(dict.fromkeys(fail_reasons)),
    )


def runtime_bridge_boundary_gap_assessment_to_dict_v0(
    result: RuntimeBridgeBoundaryGapAssessmentResultV0,
) -> Mapping[str, object]:
    return {
        "assessment_version": RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": RUNTIME_BRIDGE_BOUNDARY_GAP_ASSESSMENT_OWNER,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "assessment_verdict": result.assessment_verdict,
        "boundary_gap_status": result.boundary_gap_status,
        "plan_type": result.plan_type,
        "narrow_rewire_justified": result.narrow_rewire_justified,
        "narrow_rewire_admissible": result.narrow_rewire_admissible,
        "trace_next_unbound_node": result.trace_next_unbound_node,
        "chain_surface_binding_complete": result.chain_surface_binding_complete,
        "runtime_bridge_boundary_status": result.runtime_bridge_boundary_status,
        "runtime_bridge_pre_activation_gate_status": (
            result.runtime_bridge_pre_activation_gate_status
        ),
        "runtime_bridge_activation_admissible": result.runtime_bridge_activation_admissible,
        "offline_parity_complete_runtime_activation_pending": (
            result.offline_parity_complete_runtime_activation_pending
        ),
        "surface_p_registry_status": result.surface_p_registry_status,
        "surface_p_semantic_post_status": result.surface_p_semantic_post_status,
        "canonical_runtime_entrypoint_status": result.canonical_runtime_entrypoint_status,
        "blocking_reasons": list(result.blocking_reasons),
        "required_next_gates": list(result.required_next_gates),
        "primary_blocker": result.primary_blocker,
        "next_step_after_pr": result.next_step_after_pr,
        "source_evidence_referenced": result.source_evidence_referenced,
        "source_manifest_verify_rc": result.source_manifest_verify_rc,
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "claim_promotion_allowed": result.claim_promotion_allowed,
        "no_runtime_authority_confirmed": result.no_runtime_authority_confirmed,
        "no_economic_claim_confirmed": result.no_economic_claim_confirmed,
        "no_runtime_evidence_before_core_system_complete": (
            result.no_runtime_evidence_before_core_system_complete
        ),
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def render_runtime_bridge_boundary_gap_matrix_json_v0(
    *,
    repo_root: Path | None = None,
    pr5025_source_dir: Path | None = None,
) -> str:
    result = evaluate_runtime_bridge_boundary_gap_assessment_v0(
        repo_root=repo_root,
        pr5025_source_dir=pr5025_source_dir,
    )
    source_refs = collect_source_evidence_refs(pr5025_source_dir=pr5025_source_dir)
    payload = {
        **dict(runtime_bridge_boundary_gap_assessment_to_dict_v0(result)),
        "source_evidence_refs": [
            {
                "evidence_id": ref.evidence_id,
                "path": ref.path,
                "present": ref.present,
                "manifest_present": ref.manifest_present,
                "manifest_verified": ref.manifest_verified,
                "detail": ref.detail,
            }
            for ref in source_refs
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_runtime_bridge_boundary_gap_report_markdown_v0(
    *,
    repo_root: Path | None = None,
    pr5025_source_dir: Path | None = None,
) -> str:
    result = evaluate_runtime_bridge_boundary_gap_assessment_v0(
        repo_root=repo_root,
        pr5025_source_dir=pr5025_source_dir,
    )
    lines = [
        "# Runtime Bridge Boundary Gap Assessment v0",
        "",
        "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE",
        "",
        "## Verdict",
        "",
        f"- assessment_verdict: {result.assessment_verdict}",
        f"- boundary_gap_status: {result.boundary_gap_status}",
        f"- plan_type: {result.plan_type}",
        f"- narrow_rewire_justified: {str(result.narrow_rewire_justified).lower()}",
        f"- narrow_rewire_admissible: {str(result.narrow_rewire_admissible).lower()}",
        "",
        "## Trace / Boundary Context",
        "",
        f"- trace_next_unbound_node: {result.trace_next_unbound_node}",
        (f"- chain_surface_binding_complete: {str(result.chain_surface_binding_complete).lower()}"),
        f"- runtime_bridge_boundary_status: {result.runtime_bridge_boundary_status}",
        (
            "- offline_parity_complete_runtime_activation_pending: "
            f"{str(result.offline_parity_complete_runtime_activation_pending).lower()}"
        ),
        "",
        "## Pre-Activation Gate Context",
        "",
        (
            "- runtime_bridge_pre_activation_gate_status: "
            f"{result.runtime_bridge_pre_activation_gate_status}"
        ),
        (
            "- runtime_bridge_activation_admissible: "
            f"{str(result.runtime_bridge_activation_admissible).lower()}"
        ),
        f"- primary_blocker: {result.primary_blocker}",
        "",
        "## Surface P Context",
        "",
        f"- surface_p_registry_status: {result.surface_p_registry_status}",
        f"- surface_p_semantic_post_status: {result.surface_p_semantic_post_status}",
        f"- canonical_runtime_entrypoint_status: {result.canonical_runtime_entrypoint_status}",
        "",
        "## Blocking Reasons",
        "",
    ]
    if result.blocking_reasons:
        lines.extend(f"- {item}" for item in result.blocking_reasons)
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Required Next Gates",
            "",
        ]
    )
    if result.required_next_gates:
        lines.extend(f"- {item}" for item in result.required_next_gates)
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Final Status (fail-closed)",
            "",
            f"FULL_CANONICAL_CHAIN_WIRED={str(result.full_canonical_chain_wired).lower()}",
            (
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                f"{str(result.backtest_runtime_decision_parity_pass).lower()}"
            ),
            (
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                f"{str(result.system_economic_evidence_admissible).lower()}"
            ),
            f"RUNTIME_REWIRE_ADMISSIBLE={str(result.runtime_rewire_admissible).lower()}",
            f"CLAIM_PROMOTION_ALLOWED={str(result.claim_promotion_allowed).lower()}",
            (
                "NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE="
                f"{str(result.no_runtime_evidence_before_core_system_complete).lower()}"
            ),
            f"NEXT_STEP_AFTER_PR={result.next_step_after_pr}",
            "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
            "NO_ECONOMIC_CLAIM_CONFIRMED=true",
        ]
    )
    return "\n".join(lines) + "\n"


def assessment_result_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(RuntimeBridgeBoundaryGapAssessmentResultV0))
