"""
Next full canonical parity surface assessment after Surface P semantic parity v0.

Read-only / offline-only assessment that consumes trace-matrix NEXT_UNBOUND_NODE,
gap-assessment NEXT_RECOMMENDED_SLICE, and PR5023 Surface P semantic parity
evidence to make the next canonical parity work slice explicit. Does not activate
runtime, grant order authority, or promote final success flags.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

NEXT_FULL_CANONICAL_PARITY_SURFACE_ASSESSMENT_LAYER_VERSION = "v0"
NEXT_FULL_CANONICAL_PARITY_SURFACE_ASSESSMENT_OWNER = (
    "trading.master_v2.next_full_canonical_parity_surface_after_surface_p_assessment_v0"
)
ASSESSMENT_SLICE_ID = "NEXT_FULL_CANONICAL_PARITY_SURFACE_AFTER_SURFACE_P_ASSESSMENT_V0"
PACKAGE_MARKER = "NEXT_FULL_CANONICAL_PARITY_SURFACE_AFTER_SURFACE_P_ASSESSMENT_V0=true"

SELECTED_SURFACE = "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"
PLAN_TYPE = "ASSESSMENT_ONLY"

DEFAULT_PR5023_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5023_surface_p_semantic_parity_gap_assessment_targeted_v0_20260708T231817Z"
)
DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_parity_proof_bundle_v0_20260708T224152Z"
)

AssessmentVerdict = Literal["PASS", "FAIL_CLOSED"]
TraceNextUnboundNode = str

REASON_TRACE_NODES_ALL_BOUND = "TRACE_MATRIX_NEXT_UNBOUND_NODE_NONE"
REASON_SURFACE_P_SEMANTIC_PASS_REGISTRY_PARTIAL = (
    "SURFACE_P_SEMANTIC_PASS_REGISTRY_PARTIAL_RUNTIME_BRIDGE_BLOCKED"
)
REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED = "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_BY_POLICY"
REASON_SOURCE_MANIFEST_UNVERIFIED = "SOURCE_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_PR5023_CLOSEOUT_MISSING = "PR5023_SURFACE_P_SEMANTIC_CLOSEOUT_EVIDENCE_MISSING"
REASON_SURFACE_P_SEMANTIC_NOT_PASS = "SURFACE_P_SEMANTIC_PARITY_NOT_PASS"
REASON_FINAL_FLAGS_STILL_FALSE = "FINAL_SUCCESS_FLAGS_REMAIN_FAIL_CLOSED"

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "CLAIM_PROMOTION_ALLOWED=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"CLAIM_PROMOTION_ALLOWED\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
    re.compile(r'"claim_promotion_allowed"\s*:\s*true\b'),
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
class NextFullCanonicalParitySurfaceAssessmentResultV0:
    assessment_verdict: AssessmentVerdict
    trace_next_unbound_node_before: TraceNextUnboundNode
    next_unbound_node: str
    selected_surface: str
    plan_type: str
    surface_p_registry_status: str
    surface_p_semantic_post_status: str
    chain_surface_binding_complete: bool
    gap_assessment_next_recommended_slice: str
    blocked_reason: str
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
    pr5023_closeout_dir: Path | None = None,
    pr5022_proof_bundle_dir: Path | None = None,
) -> Tuple[SourceEvidenceRefV0, ...]:
    closeout = pr5023_closeout_dir or Path(DEFAULT_PR5023_CLOSEOUT_EVIDENCE)
    proof_bundle = pr5022_proof_bundle_dir or Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    refs: list[SourceEvidenceRefV0] = []
    for evidence_id, path in (
        ("pr5023_closeout", closeout),
        ("pr5022_proof_bundle", proof_bundle),
    ):
        present = path.is_dir()
        manifest_present = present and (path / "MANIFEST.sha256").is_file()
        if manifest_present:
            verified, rc, detail = verify_source_manifest(path)
            refs.append(
                SourceEvidenceRefV0(
                    evidence_id=evidence_id,
                    path=str(path),
                    present=True,
                    manifest_present=True,
                    manifest_verified=verified,
                    detail=detail if verified else f"rc={rc}:{detail}",
                )
            )
        else:
            refs.append(
                SourceEvidenceRefV0(
                    evidence_id=evidence_id,
                    path=str(path),
                    present=present,
                    manifest_present=False,
                    manifest_verified=False,
                    detail="missing" if not present else "manifest_missing",
                )
            )
    return tuple(refs)


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


def resolve_next_unbound_canonical_parity_node_v0(
    *,
    trace_next_unbound_node: str,
    gap_assessment_next_recommended_slice: str,
    surface_p_semantic_post_status: str,
) -> str:
    """Make the next canonical parity node explicit when trace surfaces are all bound."""
    if trace_next_unbound_node != "NONE":
        return trace_next_unbound_node
    if surface_p_semantic_post_status == "PASS":
        return gap_assessment_next_recommended_slice
    return gap_assessment_next_recommended_slice


def evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
    *,
    repo_root: Path | None = None,
    pr5023_closeout_dir: Path | None = None,
    pr5022_proof_bundle_dir: Path | None = None,
    source_manifest_verify_rc: int | None = None,
) -> NextFullCanonicalParitySurfaceAssessmentResultV0:
    """Evaluate next full canonical parity surface after Surface P; never grants authority."""
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        NEXT_RECOMMENDED_SLICE,
        parity_surface_assessments_v0,
    )
    from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
        evaluate_surface_p_semantic_parity_gap_assessment_v0,
    )

    root = repo_root or Path(__file__).resolve().parents[3]
    fail_reasons: list[str] = []
    source_refs = collect_source_evidence_refs(
        pr5023_closeout_dir=pr5023_closeout_dir,
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
    )
    closeout_ref = next(ref for ref in source_refs if ref.evidence_id == "pr5023_closeout")
    source_evidence_referenced = closeout_ref.present
    manifest_rc = (
        source_manifest_verify_rc
        if source_manifest_verify_rc is not None
        else (0 if closeout_ref.manifest_verified else -1)
    )
    if not closeout_ref.present:
        fail_reasons.append(REASON_PR5023_CLOSEOUT_MISSING)
    elif manifest_rc != 0:
        fail_reasons.append(REASON_SOURCE_MANIFEST_UNVERIFIED)

    trace_next_unbound, chain_binding_complete = _trace_matrix_snapshot_v0(root)

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    surface_p_registry_status = surface_p.parity_status

    semantic = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
        source_manifest_verify_rc=manifest_rc if manifest_rc != -1 else None,
    )
    surface_p_semantic_post_status = semantic.surface_p_post_status
    if surface_p_semantic_post_status != "PASS":
        fail_reasons.append(REASON_SURFACE_P_SEMANTIC_NOT_PASS)

    next_unbound_node = resolve_next_unbound_canonical_parity_node_v0(
        trace_next_unbound_node=trace_next_unbound,
        gap_assessment_next_recommended_slice=NEXT_RECOMMENDED_SLICE,
        surface_p_semantic_post_status=surface_p_semantic_post_status,
    )

    blocked_reason = semantic.next_blocker
    if blocked_reason == REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED:
        fail_reasons.append(REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED)

    next_step_after_pr = (
        "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0"
        if blocked_reason == REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED
        else SELECTED_SURFACE
    )

    assessment_verdict: AssessmentVerdict = (
        "PASS"
        if (
            next_unbound_node == SELECTED_SURFACE
            and surface_p_semantic_post_status == "PASS"
            and manifest_rc == 0
            and chain_binding_complete
        )
        else "FAIL_CLOSED"
    )

    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        build_surface_p_final_flags_evidence_input_v0,
        evaluate_surface_p_final_flags_fail_closed_contract_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    )

    offline_semantic = (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0()
    )
    final_flags = evaluate_surface_p_final_flags_fail_closed_contract_v0(
        build_surface_p_final_flags_evidence_input_v0(
            source_manifest_verify_rc=manifest_rc,
            surface_p_parity_suite_confirmed=(
                surface_p_semantic_post_status == "PASS" and chain_binding_complete
            ),
            runtime_bridge_binding_status=offline_semantic.surface_p_runtime_bridge_binding_status,
        )
    )

    return NextFullCanonicalParitySurfaceAssessmentResultV0(
        assessment_verdict=assessment_verdict,
        trace_next_unbound_node_before=trace_next_unbound,
        next_unbound_node=next_unbound_node,
        selected_surface=SELECTED_SURFACE,
        plan_type=PLAN_TYPE,
        surface_p_registry_status=surface_p_registry_status,
        surface_p_semantic_post_status=surface_p_semantic_post_status,
        chain_surface_binding_complete=chain_binding_complete,
        gap_assessment_next_recommended_slice=NEXT_RECOMMENDED_SLICE,
        blocked_reason=blocked_reason,
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
        fail_closed_reasons=tuple(dict.fromkeys(fail_reasons)),
    )


def next_full_canonical_parity_surface_assessment_to_dict_v0(
    result: NextFullCanonicalParitySurfaceAssessmentResultV0,
) -> Mapping[str, object]:
    return {
        "assessment_version": NEXT_FULL_CANONICAL_PARITY_SURFACE_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": NEXT_FULL_CANONICAL_PARITY_SURFACE_ASSESSMENT_OWNER,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "assessment_verdict": result.assessment_verdict,
        "trace_next_unbound_node_before": result.trace_next_unbound_node_before,
        "next_unbound_node": result.next_unbound_node,
        "selected_surface": result.selected_surface,
        "plan_type": result.plan_type,
        "surface_p_registry_status": result.surface_p_registry_status,
        "surface_p_semantic_post_status": result.surface_p_semantic_post_status,
        "chain_surface_binding_complete": result.chain_surface_binding_complete,
        "gap_assessment_next_recommended_slice": result.gap_assessment_next_recommended_slice,
        "blocked_reason": result.blocked_reason,
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
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def render_next_full_canonical_parity_surface_matrix_json_v0(
    *,
    repo_root: Path | None = None,
    pr5023_closeout_dir: Path | None = None,
    pr5022_proof_bundle_dir: Path | None = None,
) -> str:
    result = evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
        repo_root=repo_root,
        pr5023_closeout_dir=pr5023_closeout_dir,
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
    )
    source_refs = collect_source_evidence_refs(
        pr5023_closeout_dir=pr5023_closeout_dir,
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
    )
    payload = {
        **dict(next_full_canonical_parity_surface_assessment_to_dict_v0(result)),
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


def render_next_full_canonical_parity_surface_report_markdown_v0(
    *,
    repo_root: Path | None = None,
    pr5023_closeout_dir: Path | None = None,
    pr5022_proof_bundle_dir: Path | None = None,
) -> str:
    result = evaluate_next_full_canonical_parity_surface_after_surface_p_assessment_v0(
        repo_root=repo_root,
        pr5023_closeout_dir=pr5023_closeout_dir,
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
    )
    lines = [
        "# Next Full Canonical Parity Surface After Surface P Assessment v0",
        "",
        "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE",
        "",
        "## Selection",
        "",
        f"- trace_next_unbound_node_before: {result.trace_next_unbound_node_before}",
        f"- next_unbound_node: {result.next_unbound_node}",
        f"- selected_surface: {result.selected_surface}",
        f"- plan_type: {result.plan_type}",
        "",
        "## Surface P State After PR5023",
        "",
        f"- surface_p_registry_status: {result.surface_p_registry_status}",
        f"- surface_p_semantic_post_status: {result.surface_p_semantic_post_status}",
        f"- blocked_reason: {result.blocked_reason}",
        "",
        "## Chain Status",
        "",
        (f"- chain_surface_binding_complete: {str(result.chain_surface_binding_complete).lower()}"),
        (
            "- gap_assessment_next_recommended_slice: "
            f"{result.gap_assessment_next_recommended_slice}"
        ),
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
        f"NEXT_STEP_AFTER_PR={result.next_step_after_pr}",
        "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
        "NO_ECONOMIC_CLAIM_CONFIRMED=true",
    ]
    return "\n".join(lines) + "\n"


def assessment_result_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(NextFullCanonicalParitySurfaceAssessmentResultV0))
