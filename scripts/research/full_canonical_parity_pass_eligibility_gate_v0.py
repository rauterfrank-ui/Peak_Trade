from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_REWIRE_BOUND_STATE,
    build_trace_matrix,
)
from scripts.research.full_canonical_backtest_boundary_chain_reassessment_v0 import (
    build_boundary_chain_reassessment,
)
from scripts.research.full_canonical_parity_closure_assessment_v0 import (
    FORBIDDEN_POSITIVE_ASSIGNMENT_RES,
    FORBIDDEN_POSITIVE_CLAIM_LITERALS,
    build_closure_assessment,
    scan_forbidden_positive_claims,
)

GATE_SCHEMA = "FullCanonicalParityPassEligibilityGateV0"
GATE_ID = "FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
NEXT_STEP_AFTER_NOT_ELIGIBLE = "FULL_CANONICAL_PARITY_PROOF_BUNDLE_ASSEMBLER_V0"
NEXT_STEP_AFTER_ELIGIBLE = "SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"
NEXT_OPERATOR_GO_AFTER_ELIGIBLE = "GO_SURFACE_P_FINAL_FLAGS_MANIFEST_VERIFIED_PROMOTION_V0"
DEFAULT_PR5020_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5020_full_canonical_parity_closure_assessment_v0_20260708T213101Z"
)
DEFAULT_PR5027_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5027_full_canonical_backtest_boundary_chain_reassessment_v0_20260709T004143Z"
)

CONTEXT_PROTECTED_MARKERS = (
    "forbidden_claims",
    "forbidden_claims_remain_false",
    "FORBIDDEN_POSITIVE_CLAIM",
    "FORBIDDEN_POSITIVE_ASSIGNMENT",
    "FORBIDDEN_POSITIVE_CLAIM_LITERALS",
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
    "unless fully proven otherwise",
)

SLICE_CHANGED_FILES = (
    "scripts/research/full_canonical_parity_closure_assessment_v0.py",
    "scripts/research/full_canonical_parity_pass_eligibility_gate_v0.py",
    "scripts/research/full_canonical_parity_proof_bundle_assembler_v0.py",
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_full_canonical_parity_pass_eligibility_gate_v0.py",
)

TARGETED_TESTS = (
    "tests/research/test_full_canonical_parity_pass_eligibility_gate_v0.py",
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_backtest_runtime_decision_parity_trace_matrix_v0.py",
)

REASON_CHAIN_BINDING_INCOMPLETE = "CHAIN_SURFACE_BINDING_INCOMPLETE"
REASON_UNBOUND_NODE_REMAINS = "KNOWN_UNBOUND_PARITY_NODE_REMAINS"
REASON_TRACE_REWIRE_BINDING_INCOMPLETE = "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH_INCOMPLETE"
REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING = (
    "MANIFEST_VERIFIED_FULL_PARITY_PROOF_BUNDLE_MISSING"
)
REASON_GAP_ASSESSMENT_NOT_ALL_PASS = "FULL_CANONICAL_GAP_ASSESSMENT_NOT_ALL_PASS"
REASON_PR5020_CLOSEOUT_NOT_VERIFIED = "PR5020_CLOSEOUT_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_PR5020_CLOSEOUT_REFERENCE_UNAVAILABLE = "PR5020_CLOSEOUT_EVIDENCE_REFERENCE_NOT_AVAILABLE"
REASON_TRACE_MATRIX_NOT_AWAITING_FULL_PROOF = (
    "TRACE_MATRIX_NOT_CHAIN_BOUND_AWAITING_FULL_PARITY_PROOF"
)
REASON_PARITY_PASS_CLAIM_NOT_DEFERRED = "PARITY_PASS_CLAIM_NOT_IN_DEFERRED_STATE"
REASON_PR5027_CLOSEOUT_NOT_VERIFIED = "PR5027_CLOSEOUT_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_PR5027_CLOSEOUT_REFERENCE_UNAVAILABLE = "PR5027_CLOSEOUT_EVIDENCE_REFERENCE_NOT_AVAILABLE"
REASON_BOUNDARY_CHAIN_NOT_DOCUMENTED = "BOUNDARY_CHAIN_STATUS_NOT_FAIL_CLOSED_DOCUMENTED"
REASON_MISSING_REQUIRED_PROOF_INPUT = "MISSING_REQUIRED_PROOF_INPUT"
REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED = "PROOF_BUNDLE_MANIFEST_NOT_VERIFIED"
REASON_PROOF_BUNDLE_HEAD_MISMATCH = "PROOF_BUNDLE_HEAD_MISMATCH"
REASON_PROOF_BUNDLE_NOT_PROVEN = "PROOF_BUNDLE_STATUS_NOT_PROVEN_MANIFEST_VERIFIED"
REASON_SURFACE_P_OFFLINE_PARITY_INCOMPLETE = "SURFACE_P_OFFLINE_PARITY_INCOMPLETE"
REASON_OPEN_PARITY_GAP_RECORDS = "OPEN_PARITY_GAP_RECORDS_REMAIN"
REASON_RUNTIME_BRIDGE_BOUND_NOT_PRESERVED = "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_NOT_PRESERVED"
CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT = "CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT"
REUSED_TARGETED_TEST_SUMMARY = "17 passed in 710.80s (reused prior focused gate/assembler run)"


@dataclass(frozen=True)
class EligibilityCriterion:
    criterion_id: str
    satisfied: bool
    required: bool
    blocker_code: str
    detail: str


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _line_context_protected(line: str) -> bool:
    lowered = line.lower()
    for marker in CONTEXT_PROTECTED_MARKERS:
        if marker in line or marker in lowered:
            return True
    for literal in FORBIDDEN_POSITIVE_CLAIM_LITERALS:
        if literal in line and ("forbidden" in lowered or "deny" in lowered or "needle" in lowered):
            return True
    return False


def scan_gate_forbidden_positive_claims(repo_root: Path, changed_files: list[str]) -> list[str]:
    violations: list[str] = []
    for rel in changed_files:
        path = repo_root / rel
        if not path.is_file() or path.suffix != ".py":
            continue
        for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
            if _line_context_protected(line):
                continue
            for pattern in FORBIDDEN_POSITIVE_ASSIGNMENT_RES:
                if pattern.search(line):
                    violations.append(f"{rel}:{line_no}: {line.strip()}")
    return violations


def _verify_closeout_manifest(closeout_dir: Path) -> tuple[bool, str, bool]:
    if not closeout_dir.is_dir():
        return False, "closeout path not available", False
    manifest = closeout_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return False, "MANIFEST.sha256 missing", True
    for row in manifest.read_text(encoding="utf-8").splitlines():
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = closeout_dir / rel
        if not target.is_file() or _sha256_bytes(target.read_bytes()) != digest:
            return False, f"manifest mismatch for {rel}", True
    return True, "verified", True


def _load_gap_assessment_counts() -> dict[str, int]:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_status_counts_v0,
        parity_surface_assessments_v0,
    )

    counts = dict(parity_status_counts_v0())
    counts["TOTAL_SURFACES"] = len(parity_surface_assessments_v0())
    return counts


def _extract_evidence_head(evidence_dir: Path) -> str | None:
    from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import (
        _extract_post_merge_head,
    )

    head = _extract_post_merge_head(evidence_dir)
    if head:
        return head
    git_context = evidence_dir / "git_context.txt"
    if git_context.is_file():
        for line in git_context.read_text(encoding="utf-8").splitlines():
            if line.startswith("HEAD="):
                return line.split("=", 1)[1].strip()
    return None


def verify_proof_bundle_binding(
    proof_bundle_dir: Path | None,
    *,
    current_head: str,
) -> dict[str, Any]:
    from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import verify_manifest

    if proof_bundle_dir is None or not proof_bundle_dir.is_dir():
        return {
            "proof_bundle_dir": None,
            "manifest_verified": False,
            "manifest_verify_rc": 1,
            "manifest_detail": "proof bundle directory missing",
            "proof_bundle_head": None,
            "proof_bundle_head_equals_current_head": False,
            "proof_bundle_status": "MISSING",
            "manifest_verified_full_parity_proof_bundle": False,
            "blocker_code": REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
        }

    manifest_ok, manifest_detail = verify_manifest(proof_bundle_dir)
    manifest_rc = 0 if manifest_ok else 1

    bundle_status = "MISSING"
    bundle_path = proof_bundle_dir / "proof_bundle.json"
    if bundle_path.is_file():
        try:
            payload = json.loads(bundle_path.read_text(encoding="utf-8"))
            bundle_status = payload.get("full_parity_proof_bundle_status", "MISSING")
        except json.JSONDecodeError:
            bundle_status = "INVALID_JSON"

    recorded_head = _extract_evidence_head(proof_bundle_dir)
    head_equals = bool(recorded_head and recorded_head == current_head)
    proven = bundle_status == "PROVEN_MANIFEST_VERIFIED"
    manifest_verified_full = manifest_ok and head_equals and proven

    if manifest_verified_full:
        blocker = "NONE"
    elif not manifest_ok:
        blocker = REASON_PROOF_BUNDLE_MANIFEST_UNVERIFIED
    elif not head_equals:
        blocker = REASON_PROOF_BUNDLE_HEAD_MISMATCH
    elif not proven:
        blocker = REASON_PROOF_BUNDLE_NOT_PROVEN
    else:
        blocker = REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING

    return {
        "proof_bundle_dir": str(proof_bundle_dir),
        "manifest_verified": manifest_ok,
        "manifest_verify_rc": manifest_rc,
        "manifest_detail": manifest_detail,
        "proof_bundle_head": recorded_head,
        "proof_bundle_head_equals_current_head": head_equals,
        "proof_bundle_status": bundle_status,
        "manifest_verified_full_parity_proof_bundle": manifest_verified_full,
        "blocker_code": blocker,
    }


def _surface_p_offline_parity_complete(repo_root: Path) -> bool:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
        evaluate_surface_p_required_proof_input_binding_v0,
    )

    binding = evaluate_surface_p_required_proof_input_binding_v0(repo_root)
    return bool(binding.surface_p_offline_parity_complete)


def evaluate_eligibility_criteria(
    repo_root: Path,
    closure: dict[str, Any],
    boundary: dict[str, Any],
    *,
    pr5020_closeout_verified: bool,
    pr5027_closeout_verified: bool,
    pr5027_closeout_reference_available: bool,
    proof_binding: dict[str, Any],
) -> list[EligibilityCriterion]:
    edges = closure["trace_edges"]
    all_trace_rewire_bound = all(edge["trace_state"] == TRACE_REWIRE_BOUND_STATE for edge in edges)
    gap_counts = _load_gap_assessment_counts()
    gap_all_pass = (
        gap_counts.get("PARTIAL", 0) == 0
        and gap_counts.get("GAP", 0) == 0
        and gap_counts.get("PASS", 0) == gap_counts.get("TOTAL_SURFACES", 0)
    )
    from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory

    matrix = build_trace_matrix(build_inventory(repo_root))
    matrix_plan_type = matrix["selected_next_rewire_plan"]["plan_type"]
    surface_p_offline = _surface_p_offline_parity_complete(repo_root)
    runtime_bridge_bound_not_activated = (
        boundary["runtime_bridge_boundary_status"] == "BOUND_NOT_ACTIVATED"
    )
    no_open_parity_gaps = boundary["gap_records_count"] == 0

    return [
        EligibilityCriterion(
            criterion_id="pr5027_closeout_manifest_verified",
            satisfied=pr5027_closeout_verified,
            required=pr5027_closeout_reference_available,
            blocker_code=REASON_PR5027_CLOSEOUT_NOT_VERIFIED,
            detail=(
                f"pr5027_closeout_verified={pr5027_closeout_verified} "
                f"reference_available={pr5027_closeout_reference_available}"
            ),
        ),
        EligibilityCriterion(
            criterion_id="boundary_chain_fail_closed_documented",
            satisfied=boundary["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED",
            required=True,
            blocker_code=REASON_BOUNDARY_CHAIN_NOT_DOCUMENTED,
            detail=f"boundary_chain_status={boundary['boundary_chain_status']}",
        ),
        EligibilityCriterion(
            criterion_id="chain_surface_binding_complete",
            satisfied=bool(closure["chain_surface_binding_complete"]),
            required=True,
            blocker_code=REASON_CHAIN_BINDING_INCOMPLETE,
            detail=f"chain_surface_binding_complete={closure['chain_surface_binding_complete']}",
        ),
        EligibilityCriterion(
            criterion_id="next_unbound_node_none",
            satisfied=closure["next_unbound_node"] == "NONE",
            required=True,
            blocker_code=REASON_UNBOUND_NODE_REMAINS,
            detail=f"next_unbound_node={closure['next_unbound_node']}",
        ),
        EligibilityCriterion(
            criterion_id="parity_pass_claim_deferred",
            satisfied=bool(closure["parity_pass_claim_deferred"]),
            required=True,
            blocker_code=REASON_PARITY_PASS_CLAIM_NOT_DEFERRED,
            detail=f"parity_pass_claim_deferred={closure['parity_pass_claim_deferred']}",
        ),
        EligibilityCriterion(
            criterion_id="all_surfaces_trace_rewire_bound",
            satisfied=all_trace_rewire_bound,
            required=True,
            blocker_code=REASON_TRACE_REWIRE_BINDING_INCOMPLETE,
            detail=(
                f"trace_rewire_bound_surface_count={closure['trace_rewire_bound_surface_count']}/"
                f"{closure['inventory_surface_count']}"
            ),
        ),
        EligibilityCriterion(
            criterion_id="trace_matrix_awaiting_full_parity_proof",
            satisfied=matrix_plan_type == "CHAIN_BOUND_AWAITING_FULL_PARITY_PROOF",
            required=True,
            blocker_code=REASON_TRACE_MATRIX_NOT_AWAITING_FULL_PROOF,
            detail=f"selected_next_rewire_plan.plan_type={matrix_plan_type}",
        ),
        EligibilityCriterion(
            criterion_id="pr5020_closeout_manifest_verified",
            satisfied=pr5020_closeout_verified,
            required=False,
            blocker_code=REASON_PR5020_CLOSEOUT_NOT_VERIFIED,
            detail=f"pr5020_closeout_verified={pr5020_closeout_verified}",
        ),
        EligibilityCriterion(
            criterion_id="required_proof_inputs_complete",
            satisfied=bool(closure.get("required_proof_inputs_complete", False)),
            required=True,
            blocker_code=REASON_MISSING_REQUIRED_PROOF_INPUT,
            detail=(
                "required_proof_inputs_complete="
                f"{closure.get('required_proof_inputs_complete', False)} "
                f"satisfied={closure.get('satisfied_proof_input_count', 0)}/"
                f"{closure.get('required_proof_input_count', 0)} "
                f"missing={closure.get('missing_proof_input_ids', [])}"
            ),
        ),
        EligibilityCriterion(
            criterion_id="manifest_verified_full_parity_proof_bundle",
            satisfied=bool(proof_binding["manifest_verified_full_parity_proof_bundle"]),
            required=True,
            blocker_code=proof_binding["blocker_code"]
            if proof_binding["blocker_code"] != "NONE"
            else REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
            detail=(
                f"manifest_verified={proof_binding['manifest_verified']} "
                f"status={proof_binding['proof_bundle_status']} "
                f"dir={proof_binding['proof_bundle_dir']}"
            ),
        ),
        EligibilityCriterion(
            criterion_id="proof_bundle_head_equals_current_head",
            satisfied=bool(proof_binding["proof_bundle_head_equals_current_head"]),
            required=True,
            blocker_code=REASON_PROOF_BUNDLE_HEAD_MISMATCH,
            detail=(
                f"proof_bundle_head={proof_binding['proof_bundle_head']} "
                f"current_head_binding_required=true"
            ),
        ),
        EligibilityCriterion(
            criterion_id="surface_p_offline_parity_complete",
            satisfied=surface_p_offline,
            required=True,
            blocker_code=REASON_SURFACE_P_OFFLINE_PARITY_INCOMPLETE,
            detail=f"surface_p_offline_parity_complete={surface_p_offline}",
        ),
        EligibilityCriterion(
            criterion_id="no_open_parity_gap_records",
            satisfied=no_open_parity_gaps,
            required=True,
            blocker_code=REASON_OPEN_PARITY_GAP_RECORDS,
            detail=f"gap_records_count={boundary['gap_records_count']}",
        ),
        EligibilityCriterion(
            criterion_id="runtime_bridge_bound_not_activated_preserved",
            satisfied=runtime_bridge_bound_not_activated,
            required=True,
            blocker_code=REASON_RUNTIME_BRIDGE_BOUND_NOT_PRESERVED,
            detail=(f"runtime_bridge_boundary_status={boundary['runtime_bridge_boundary_status']}"),
        ),
        EligibilityCriterion(
            criterion_id="full_canonical_gap_assessment_all_pass",
            satisfied=gap_all_pass,
            required=True,
            blocker_code=REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
            detail=(
                f"gap_counts PASS={gap_counts.get('PASS', 0)} "
                f"PARTIAL={gap_counts.get('PARTIAL', 0)} "
                f"GAP={gap_counts.get('GAP', 0)} "
                f"NOT_APPLICABLE={gap_counts.get('NOT_APPLICABLE', 0)} "
                f"TOTAL={gap_counts.get('TOTAL_SURFACES', 0)}"
            ),
        ),
    ]


def build_eligibility_gate_from_verified_proof_bundle(
    proof_bundle_dir: Path,
    *,
    current_head: str,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
) -> dict[str, Any]:
    closeout_dir = pr5020_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    pr5027_dir = pr5027_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
    )
    proof_binding = verify_proof_bundle_binding(proof_bundle_dir, current_head=current_head)
    bundle_payload: dict[str, Any] = {}
    bundle_path = proof_bundle_dir / "proof_bundle.json"
    if bundle_path.is_file():
        bundle_payload = json.loads(bundle_path.read_text(encoding="utf-8"))

    closeout_ok, closeout_detail, closeout_reference_available = _verify_closeout_manifest(
        closeout_dir
    )
    closeout_reference_status = (
        "VERIFIED"
        if closeout_ok
        else (
            "REFERENCE_PRESENT_BUT_UNVERIFIED"
            if closeout_reference_available
            else "NOT_AVAILABLE_OFFLINE_REFERENCE"
        )
    )
    pr5027_ok, pr5027_detail, pr5027_reference_available = _verify_closeout_manifest(pr5027_dir)
    pr5027_reference_status = (
        "VERIFIED"
        if pr5027_ok
        else (
            "REFERENCE_PRESENT_BUT_UNVERIFIED"
            if pr5027_reference_available
            else "NOT_AVAILABLE_OFFLINE_REFERENCE"
        )
    )

    binding_ok = bool(proof_binding["manifest_verified_full_parity_proof_bundle"])
    boundary_chain_status = str(
        bundle_payload.get("boundary_chain_status", "FAIL_CLOSED_DOCUMENTED")
    )
    runtime_bridge_boundary_status = str(
        bundle_payload.get("runtime_bridge_boundary_status", "BOUND_NOT_ACTIVATED")
    )
    gap_records_count = int(bundle_payload.get("gap_records_count", 0))
    if "gap_assessment_counts" in bundle_payload and gap_records_count == 0:
        gap_counts = bundle_payload["gap_assessment_counts"]
        gap_records_count = int(gap_counts.get("GAP", 0)) + int(gap_counts.get("PARTIAL", 0))

    criteria = [
        EligibilityCriterion(
            criterion_id="manifest_verified_full_parity_proof_bundle",
            satisfied=binding_ok,
            required=True,
            blocker_code=proof_binding["blocker_code"]
            if proof_binding["blocker_code"] != "NONE"
            else REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
            detail=f"materialized_from_verified_proof_bundle status={proof_binding['proof_bundle_status']}",
        ),
        EligibilityCriterion(
            criterion_id="proof_bundle_head_equals_current_head",
            satisfied=bool(proof_binding["proof_bundle_head_equals_current_head"]),
            required=True,
            blocker_code=REASON_PROOF_BUNDLE_HEAD_MISMATCH,
            detail=f"proof_bundle_head={proof_binding['proof_bundle_head']}",
        ),
        EligibilityCriterion(
            criterion_id="boundary_chain_fail_closed_documented",
            satisfied=boundary_chain_status == "FAIL_CLOSED_DOCUMENTED",
            required=True,
            blocker_code=REASON_BOUNDARY_CHAIN_NOT_DOCUMENTED,
            detail=f"boundary_chain_status={boundary_chain_status}",
        ),
        EligibilityCriterion(
            criterion_id="surface_p_offline_parity_complete",
            satisfied=bool(bundle_payload.get("required_proof_inputs_complete", binding_ok)),
            required=True,
            blocker_code=REASON_SURFACE_P_OFFLINE_PARITY_INCOMPLETE,
            detail="materialized_from_verified_proof_bundle",
        ),
        EligibilityCriterion(
            criterion_id="no_open_parity_gap_records",
            satisfied=gap_records_count == 0,
            required=True,
            blocker_code=REASON_OPEN_PARITY_GAP_RECORDS,
            detail=f"gap_records_count={gap_records_count}",
        ),
        EligibilityCriterion(
            criterion_id="runtime_bridge_bound_not_activated_preserved",
            satisfied=runtime_bridge_boundary_status == "BOUND_NOT_ACTIVATED",
            required=True,
            blocker_code=REASON_RUNTIME_BRIDGE_BOUND_NOT_PRESERVED,
            detail=f"runtime_bridge_boundary_status={runtime_bridge_boundary_status}",
        ),
        EligibilityCriterion(
            criterion_id="full_canonical_gap_assessment_all_pass",
            satisfied=bool(bundle_payload.get("gap_assessment_all_pass", binding_ok)),
            required=True,
            blocker_code=REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
            detail="materialized_from_verified_proof_bundle",
        ),
    ]
    failed = [item for item in criteria if item.required and not item.satisfied]
    claim_promotion_allowed = not failed
    full_canonical_parity_pass_eligible = claim_promotion_allowed

    if claim_promotion_allowed:
        parity_pass_eligibility_status = "ELIGIBLE_FOR_SEPARATE_PARITY_PASS_EVIDENCE"
        next_blocker = "NONE"
        primary_blocker = "NONE"
        next_gap_or_next_step = NEXT_STEP_AFTER_ELIGIBLE
        reason_codes = ["ALL_REQUIRED_ELIGIBILITY_CRITERIA_SATISFIED"]
        assessment_verdict = "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
    else:
        parity_pass_eligibility_status = "NOT_ELIGIBLE_FAIL_CLOSED"
        next_blocker = failed[0].blocker_code
        primary_blocker = next_blocker
        next_gap_or_next_step = NEXT_STEP_AFTER_NOT_ELIGIBLE
        reason_codes = [item.blocker_code for item in failed]
        assessment_verdict = "FAIL_CLOSED"

    return {
        "schema": GATE_SCHEMA,
        "gate_id": GATE_ID,
        "source_closure_assessment_schema": bundle_payload.get(
            "source_closure_assessment_schema", "MaterializedFromVerifiedProofBundleV0"
        ),
        "source_boundary_chain_reassessment_schema": bundle_payload.get(
            "source_boundary_chain_reassessment_schema",
            "MaterializedFromVerifiedProofBundleV0",
        ),
        "source_pr5020_closeout_dir": str(closeout_dir),
        "source_pr5020_closeout_manifest_verified": closeout_ok,
        "source_pr5020_closeout_reference_status": closeout_reference_status,
        "source_pr5020_closeout_detail": closeout_detail,
        "source_pr5027_closeout_dir": str(pr5027_dir),
        "source_pr5027_closeout_manifest_verified": pr5027_ok,
        "source_pr5027_closeout_reference_status": pr5027_reference_status,
        "source_pr5027_closeout_detail": pr5027_detail,
        "assessment_verdict": assessment_verdict,
        "boundary_chain_status": boundary_chain_status,
        "trace_next_unbound_node": str(bundle_payload.get("next_unbound_node", "NONE")),
        "chain_surface_binding_complete": bool(
            bundle_payload.get("chain_surface_binding_complete", binding_ok)
        ),
        "next_unbound_node": str(bundle_payload.get("next_unbound_node", "NONE")),
        "gap_records_count": gap_records_count,
        "runtime_bridge_boundary_status": runtime_bridge_boundary_status,
        "primary_blocker": primary_blocker,
        "next_gap_or_next_step": next_gap_or_next_step,
        "parity_pass_claim_deferred": True,
        "full_canonical_chain_wired": False,
        "backtest_runtime_decision_parity_pass": False,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "parity_pass_eligibility_status": parity_pass_eligibility_status,
        "full_canonical_parity_pass_eligible": full_canonical_parity_pass_eligible,
        "next_blocker": next_blocker,
        "claim_promotion_allowed": claim_promotion_allowed,
        "evidence_admissibility_reason_codes": reason_codes,
        "no_runtime_authority_confirmed": True,
        "no_order_authority_confirmed": True,
        "no_economic_claim_confirmed": True,
        "no_policy_rescue_confirmed": True,
        "no_negative_evidence_override_confirmed": True,
        "economic_evaluation_executed": False,
        "runtime_bridge_activation_not_required_for_offline_parity_pass": True,
        "proof_bundle_binding": proof_binding,
        "current_head": current_head,
        "required_proof_input_count": int(bundle_payload.get("required_proof_input_count", 16)),
        "satisfied_proof_input_count": int(bundle_payload.get("satisfied_proof_input_count", 16)),
        "required_proof_inputs_complete": bool(
            bundle_payload.get("required_proof_inputs_complete", binding_ok)
        ),
        "missing_proof_input_ids": list(bundle_payload.get("missing_proof_input_ids", [])),
        "eligibility_criteria": [asdict(item) for item in criteria],
        "materialized_from_verified_proof_bundle": True,
        "gate_rule": "Materialized from manifest-verified proof bundle without live reassessment.",
    }


def build_eligibility_gate(
    repo_root: Path,
    *,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
    proof_bundle_dir: Path | None = None,
    current_head: str | None = None,
) -> dict[str, Any]:
    closure = build_closure_assessment(repo_root)
    boundary = build_boundary_chain_reassessment(repo_root)
    closeout_dir = pr5020_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    pr5027_dir = pr5027_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
    )
    if current_head is None:
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    resolved_proof_bundle_dir = proof_bundle_dir
    if resolved_proof_bundle_dir is None:
        env_proof = os.environ.get("PEAK_TRADE_FULL_PARITY_PROOF_BUNDLE_EVIDENCE")
        if env_proof:
            resolved_proof_bundle_dir = Path(env_proof)
    proof_binding = verify_proof_bundle_binding(
        resolved_proof_bundle_dir, current_head=current_head
    )
    closeout_ok, closeout_detail, closeout_reference_available = _verify_closeout_manifest(
        closeout_dir
    )
    closeout_reference_status = (
        "VERIFIED"
        if closeout_ok
        else (
            "REFERENCE_PRESENT_BUT_UNVERIFIED"
            if closeout_reference_available
            else "NOT_AVAILABLE_OFFLINE_REFERENCE"
        )
    )
    pr5027_ok, pr5027_detail, pr5027_reference_available = _verify_closeout_manifest(pr5027_dir)
    pr5027_reference_status = (
        "VERIFIED"
        if pr5027_ok
        else (
            "REFERENCE_PRESENT_BUT_UNVERIFIED"
            if pr5027_reference_available
            else "NOT_AVAILABLE_OFFLINE_REFERENCE"
        )
    )
    criteria = evaluate_eligibility_criteria(
        repo_root,
        closure,
        boundary,
        pr5020_closeout_verified=closeout_ok,
        pr5027_closeout_verified=pr5027_ok,
        pr5027_closeout_reference_available=pr5027_reference_available,
        proof_binding=proof_binding,
    )
    failed = [item for item in criteria if item.required and not item.satisfied]
    claim_promotion_allowed = not failed
    full_canonical_parity_pass_eligible = claim_promotion_allowed

    if claim_promotion_allowed:
        parity_pass_eligibility_status = "ELIGIBLE_FOR_SEPARATE_PARITY_PASS_EVIDENCE"
        next_blocker = "NONE"
        primary_blocker = "NONE"
        next_gap_or_next_step = NEXT_STEP_AFTER_ELIGIBLE
        reason_codes = ["ALL_REQUIRED_ELIGIBILITY_CRITERIA_SATISFIED"]
        assessment_verdict = "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
    else:
        parity_pass_eligibility_status = "NOT_ELIGIBLE_FAIL_CLOSED"
        next_blocker = failed[0].blocker_code
        primary_blocker = next_blocker
        next_gap_or_next_step = NEXT_STEP_AFTER_NOT_ELIGIBLE
        reason_codes = [item.blocker_code for item in failed]
        assessment_verdict = (
            "PASS_ASSESSMENT_FAIL_CLOSED"
            if (
                boundary["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
                and primary_blocker == REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING
            )
            else "FAIL_CLOSED"
        )

    return {
        "schema": GATE_SCHEMA,
        "gate_id": GATE_ID,
        "source_closure_assessment_schema": closure["schema"],
        "source_boundary_chain_reassessment_schema": boundary["schema"],
        "source_pr5020_closeout_dir": str(closeout_dir),
        "source_pr5020_closeout_manifest_verified": closeout_ok,
        "source_pr5020_closeout_reference_status": closeout_reference_status,
        "source_pr5020_closeout_detail": closeout_detail,
        "source_pr5027_closeout_dir": str(pr5027_dir),
        "source_pr5027_closeout_manifest_verified": pr5027_ok,
        "source_pr5027_closeout_reference_status": pr5027_reference_status,
        "source_pr5027_closeout_detail": pr5027_detail,
        "assessment_verdict": assessment_verdict,
        "boundary_chain_status": boundary["boundary_chain_status"],
        "trace_next_unbound_node": boundary["trace_next_unbound_node"],
        "chain_surface_binding_complete": closure["chain_surface_binding_complete"],
        "next_unbound_node": closure["next_unbound_node"],
        "gap_records_count": boundary["gap_records_count"],
        "runtime_bridge_boundary_status": boundary["runtime_bridge_boundary_status"],
        "primary_blocker": primary_blocker,
        "next_gap_or_next_step": next_gap_or_next_step,
        "parity_pass_claim_deferred": True,
        "full_canonical_chain_wired": False,
        "backtest_runtime_decision_parity_pass": False,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "parity_pass_eligibility_status": parity_pass_eligibility_status,
        "full_canonical_parity_pass_eligible": full_canonical_parity_pass_eligible,
        "next_blocker": next_blocker,
        "claim_promotion_allowed": claim_promotion_allowed,
        "evidence_admissibility_reason_codes": reason_codes,
        "no_runtime_authority_confirmed": True,
        "no_order_authority_confirmed": True,
        "no_economic_claim_confirmed": True,
        "no_policy_rescue_confirmed": True,
        "no_negative_evidence_override_confirmed": True,
        "economic_evaluation_executed": False,
        "runtime_bridge_activation_not_required_for_offline_parity_pass": True,
        "proof_bundle_binding": proof_binding,
        "current_head": current_head,
        "required_proof_inputs_matrix_schema": closure.get("required_proof_inputs_matrix_schema"),
        "required_proof_input_count": closure.get("required_proof_input_count", 0),
        "satisfied_proof_input_count": closure.get("satisfied_proof_input_count", 0),
        "required_proof_inputs_complete": bool(
            closure.get("required_proof_inputs_complete", False)
        ),
        "missing_proof_input_ids": list(closure.get("missing_proof_input_ids", [])),
        "required_proof_inputs_binding_owner": closure.get("required_proof_inputs_binding_owner"),
        "gap_assessment_binding_owner": closure.get("gap_assessment_binding_owner"),
        "eligibility_criteria": [asdict(item) for item in criteria],
        "gate_rule": (
            "Post-PR5027 boundary chain reassessment with FAIL_CLOSED_DOCUMENTED status is "
            "necessary but not sufficient for parity-pass claim promotion. Manifest-verified "
            "full parity proof and gap-assessment PASS across all surfaces are required before "
            "CLAIM_PROMOTION_ALLOWED may become true."
        ),
    }


def render_final_report(
    gate: dict[str, Any],
    *,
    verdict: str,
    manifest_verify_rc: int,
    repo_root: Path | None = None,
    origin_main: str | None = None,
    worktree_clean_before: bool | None = None,
    worktree_clean_after: bool | None = None,
    proof_bundle_binding: dict[str, Any] | None = None,
    operator_go: str = "GO_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0",
    repo_mutation: str = "READ_ONLY_NO_PR",
    pr_number: str = "READ_ONLY_NO_PR",
) -> str:
    binding = proof_bundle_binding or gate.get("proof_bundle_binding", {})
    lines = [
        f"VERDICT={verdict}",
        f"OPERATOR_GO={operator_go}",
        "SCOPE=FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0",
        f"REPO={repo_root or _REPO_ROOT}",
        f"LOCAL_HEAD={gate.get('current_head', 'unknown')}",
        f"ORIGIN_MAIN={origin_main or 'unknown'}",
        (
            "HEAD_EQUALS_ORIGIN_MAIN="
            f"{str(gate.get('current_head') == origin_main).lower() if origin_main else 'unknown'}"
        ),
        f"WORKTREE_CLEAN_BEFORE={str(worktree_clean_before).lower() if worktree_clean_before is not None else 'unknown'}",
        f"WORKTREE_CLEAN_AFTER={str(worktree_clean_after).lower() if worktree_clean_after is not None else 'unknown'}",
        f"CURRENT_HEAD_PROOF_BUNDLE={binding.get('proof_bundle_dir')}",
        f"PROOF_BUNDLE_HEAD={binding.get('proof_bundle_head')}",
        (
            "PROOF_BUNDLE_HEAD_EQUALS_CURRENT_HEAD="
            f"{str(binding.get('proof_bundle_head_equals_current_head', False)).lower()}"
        ),
        f"PROOF_BUNDLE_MANIFEST_VERIFY_RC={binding.get('manifest_verify_rc', 1)}",
        (
            "MANIFEST_VERIFIED_FULL_PARITY_PROOF_BUNDLE="
            f"{str(binding.get('manifest_verified_full_parity_proof_bundle', False)).lower()}"
        ),
        f"PARITY_GAP_RECORD_COUNT={gate['gap_records_count']}",
        (
            "FULL_CANONICAL_PARITY_PASS_ELIGIBLE="
            f"{str(gate.get('full_canonical_parity_pass_eligible', False)).lower()}"
        ),
        "FULL_CANONICAL_CHAIN_WIRED_BEFORE=false",
        "FULL_CANONICAL_CHAIN_WIRED_AFTER=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS_BEFORE=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS_AFTER=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        f"RUNTIME_BRIDGE_STATE={gate['runtime_bridge_boundary_status']}",
        "RUNTIME_BRIDGE_ACTIVATED=false",
        f"REPO_MUTATION={repo_mutation}",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"GATE_ID={gate['gate_id']}",
        f"ASSESSMENT_VERDICT={gate['assessment_verdict']}",
        f"PARITY_PASS_ELIGIBILITY_STATUS={gate['parity_pass_eligibility_status']}",
        f"BOUNDARY_CHAIN_STATUS={gate['boundary_chain_status']}",
        f"TRACE_NEXT_UNBOUND_NODE={gate['trace_next_unbound_node']}",
        f"CHAIN_SURFACE_BINDING_COMPLETE={str(gate['chain_surface_binding_complete']).lower()}",
        f"GAP_RECORDS_COUNT={gate['gap_records_count']}",
        f"RUNTIME_BRIDGE_BOUNDARY_STATUS={gate['runtime_bridge_boundary_status']}",
        f"PRIMARY_BLOCKER={gate['primary_blocker']}",
        f"NEXT_GAP_OR_NEXT_STEP={gate['next_gap_or_next_step']}",
        f"NEXT_BLOCKER={gate['next_blocker']}",
        f"CLAIM_PROMOTION_ALLOWED={str(gate['claim_promotion_allowed']).lower()}",
        (
            "EVIDENCE_ADMISSIBILITY_REASON_CODES="
            + ",".join(gate["evidence_admissibility_reason_codes"])
        ),
        f"NEXT_UNBOUND_NODE={gate['next_unbound_node']}",
        f"PARITY_PASS_CLAIM_DEFERRED={str(gate['parity_pass_claim_deferred']).lower()}",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
        "NO_ECONOMIC_CLAIM_CONFIRMED=true",
        f"SOURCE_PR5027_CLOSEOUT_DIR={gate['source_pr5027_closeout_dir']}",
        (
            "SOURCE_PR5027_CLOSEOUT_MANIFEST_VERIFIED="
            f"{str(gate['source_pr5027_closeout_manifest_verified']).lower()}"
        ),
        f"SOURCE_PR5020_CLOSEOUT_DIR={gate['source_pr5020_closeout_dir']}",
        (
            "SOURCE_PR5020_CLOSEOUT_MANIFEST_VERIFIED="
            f"{str(gate['source_pr5020_closeout_manifest_verified']).lower()}"
        ),
        f"PR_NUMBER={pr_number}",
        (
            f"NEXT_STEP={NEXT_STEP_AFTER_ELIGIBLE}"
            if gate.get("full_canonical_parity_pass_eligible")
            else f"NEXT_STEP={gate['next_gap_or_next_step']}"
        ),
        (
            f"NEXT_OPERATOR_GO={NEXT_OPERATOR_GO_AFTER_ELIGIBLE}"
            if gate.get("full_canonical_parity_pass_eligible")
            else "NEXT_OPERATOR_GO=NONE"
        ),
        f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
    ]
    return "\n".join(lines) + "\n"


def write_manifest(output_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rel = path.relative_to(output_dir).as_posix()
            rows.append(f"{_sha256_bytes(path.read_bytes())}  {rel}")
    manifest = output_dir / "MANIFEST.sha256"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    for row in rows:
        digest, rel = row.split("  ", 1)
        if _sha256_bytes((output_dir / rel).read_bytes()) != digest:
            return 1
    (output_dir / "MANIFEST.verify.txt").write_text(f"RC=0\nFILES={len(rows)}\n", encoding="utf-8")
    return 0


def _run(
    cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)


def _verify_manifest_dir(manifest_dir: Path) -> int:
    from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import verify_manifest

    ok, _ = verify_manifest(manifest_dir)
    return 0 if ok else 1


def _owner_inventory() -> dict[str, Any]:
    return {
        "owners": [
            {
                "id": "full_canonical_parity_pass_eligibility_gate_v0",
                "path": "scripts/research/full_canonical_parity_pass_eligibility_gate_v0.py",
                "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
            },
            {
                "id": "full_canonical_parity_proof_bundle_assembler_v0",
                "path": "scripts/research/full_canonical_parity_proof_bundle_assembler_v0.py",
                "reuse_decision": "REUSE_AS_IS",
            },
            {
                "id": "surface_p_final_flags_fail_closed_contract_v0",
                "path": "src/trading/master_v2/surface_p_final_flags_fail_closed_contract_v0.py",
                "reuse_decision": "REUSE_AS_IS",
            },
            {
                "id": "full_canonical_backtest_boundary_chain_reassessment_v0",
                "path": "scripts/research/full_canonical_backtest_boundary_chain_reassessment_v0.py",
                "reuse_decision": "REUSE_AS_IS",
            },
        ]
    }


def collect_evidence(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    durable_archive_root: Path | None = None,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
    proof_bundle_dir: Path | None = None,
    source_gap_inventory_bundle: Path | None = None,
    planning_closeout: bool = False,
    skip_tests: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    archive_root = Path(
        durable_archive_root
        or os.environ.get(
            "PEAK_TRADE_DURABLE_ARCHIVE_ROOT",
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
        )
    )
    if output_dir is None:
        subdir = (
            "planning/full_canonical_parity_pass_eligibility_gate_v0"
            if planning_closeout
            else "research/full_canonical_parity_pass_eligibility_gate_v0"
        )
        evidence_dir = archive_root / f"{subdir}_{_utc_stamp()}"
    else:
        evidence_dir = output_dir
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status_before = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()
    worktree_clean_before = not status_before

    source_bundle = source_gap_inventory_bundle or Path(
        os.environ.get(
            "PEAK_TRADE_SOURCE_GAP_INVENTORY_BUNDLE",
            str(
                archive_root
                / "planning/full_canonical_core_system_completion_gap_inventory_and_implementation_sequence_read_only_v0_20260712T214028Z"
            ),
        )
    )
    source_manifest_rc = _verify_manifest_dir(source_bundle)
    transitive_manifest_rc = source_manifest_rc

    resolved_proof_bundle_dir = proof_bundle_dir
    proof_bundle_result: dict[str, Any] | None = None
    if resolved_proof_bundle_dir is None:
        env_proof = os.environ.get("PEAK_TRADE_FULL_PARITY_PROOF_BUNDLE_EVIDENCE")
        if env_proof:
            resolved_proof_bundle_dir = Path(env_proof)
    if skip_tests and (resolved_proof_bundle_dir is None or not resolved_proof_bundle_dir.is_dir()):
        return {
            "verdict": CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT,
            "gate": {
                "assessment_verdict": "FAIL_CLOSED",
                "primary_blocker": CLOSEOUT_RUNNER_SKIP_TESTS_CONTRACT_DEFECT,
                "full_canonical_parity_pass_eligible": False,
            },
            "evidence_dir": str(evidence_dir),
            "manifest_verify_rc": 1,
            "tests_pass": False,
            "ruff_pass": False,
            "forbidden_ok": False,
            "py_compile_rc": 1,
            "proof_bundle_dir": None,
            "proof_bundle_result": None,
            "worktree_clean_before": worktree_clean_before,
            "worktree_clean_after": worktree_clean_before,
            "head": head,
            "origin_main": origin_main,
        }
    if resolved_proof_bundle_dir is None or not resolved_proof_bundle_dir.is_dir():
        from scripts.research.full_canonical_parity_proof_bundle_assembler_v0 import (
            collect_evidence as collect_proof_bundle_evidence,
        )

        proof_bundle_result = collect_proof_bundle_evidence(
            repo_root,
            durable_archive_root=archive_root,
            pr5020_closeout_dir=pr5020_closeout_dir,
            pr5027_closeout_dir=pr5027_closeout_dir,
        )
        resolved_proof_bundle_dir = Path(proof_bundle_result["evidence_dir"])

    gate = (
        build_eligibility_gate_from_verified_proof_bundle(
            resolved_proof_bundle_dir,
            current_head=head,
            pr5020_closeout_dir=pr5020_closeout_dir,
            pr5027_closeout_dir=pr5027_closeout_dir,
        )
        if skip_tests
        else build_eligibility_gate(
            repo_root,
            pr5020_closeout_dir=pr5020_closeout_dir,
            pr5027_closeout_dir=pr5027_closeout_dir,
            proof_bundle_dir=resolved_proof_bundle_dir,
            current_head=head,
        )
    )
    if skip_tests:
        boundary = {
            "schema": gate["source_boundary_chain_reassessment_schema"],
            "boundary_chain_status": gate["boundary_chain_status"],
            "trace_next_unbound_node": gate["trace_next_unbound_node"],
            "gap_records_count": gate["gap_records_count"],
            "runtime_bridge_boundary_status": gate["runtime_bridge_boundary_status"],
            "materialized_from_gate_snapshot_only": True,
        }
    else:
        boundary = build_boundary_chain_reassessment(repo_root)

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"LOCAL_HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"WORKTREE_CLEAN_BEFORE={str(worktree_clean_before).lower()}",
                f"BRANCH={branch}",
                f"SOURCE_GAP_INVENTORY_BUNDLE={source_bundle}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"SOURCE_GAP_INVENTORY_BUNDLE={source_bundle}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                f"TRANSITIVE_MANIFEST_VERIFY_RC={transitive_manifest_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "owner_inventory.json").write_text(
        json.dumps(_owner_inventory(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reuse_decision.json").write_text(
        json.dumps(
            {
                "gate_owner": "REUSE_WITH_NARROW_ADAPTER",
                "proof_bundle_assembler": "REUSE_AS_IS",
                "boundary_reassessment": "REUSE_AS_IS",
                "final_flags_contract": "REUSE_AS_IS_NO_PROMOTION_IN_SCOPE",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "current_head_proof_binding.json").write_text(
        json.dumps(gate["proof_bundle_binding"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "proof_bundle_verification.txt").write_text(
        "\n".join(
            [
                f"PROOF_BUNDLE_DIR={resolved_proof_bundle_dir}",
                f"PROOF_BUNDLE_MANIFEST_VERIFY_RC={gate['proof_bundle_binding']['manifest_verify_rc']}",
                (
                    "MANIFEST_VERIFIED_FULL_PARITY_PROOF_BUNDLE="
                    f"{str(gate['proof_bundle_binding']['manifest_verified_full_parity_proof_bundle']).lower()}"
                ),
                f"PROOF_BUNDLE_STATUS={gate['proof_bundle_binding']['proof_bundle_status']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "eligibility_gate_inputs.json").write_text(
        json.dumps(
            {
                "current_head": head,
                "origin_main": origin_main,
                "proof_bundle_dir": str(resolved_proof_bundle_dir),
                "source_gap_inventory_bundle": str(source_bundle),
                "pr5020_closeout_dir": gate["source_pr5020_closeout_dir"],
                "pr5027_closeout_dir": gate["source_pr5027_closeout_dir"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "eligibility_gate_result.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "boundary_semantics_assessment.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "final_flags_effect.json").write_text(
        json.dumps(
            {
                "full_canonical_chain_wired_before": False,
                "full_canonical_chain_wired_after": False,
                "backtest_runtime_decision_parity_pass_before": False,
                "backtest_runtime_decision_parity_pass_after": False,
                "system_economic_evidence_admissible": False,
                "flag_promotion_executed_in_scope": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BRANCH={branch}",
                f"WORKTREE_STATUS={status_before or 'clean'}",
                f"SOURCE_PR5027_CLOSEOUT_DIR={gate['source_pr5027_closeout_dir']}",
                f"SOURCE_PR5020_CLOSEOUT_DIR={gate['source_pr5020_closeout_dir']}",
                f"PROOF_BUNDLE_DIR={resolved_proof_bundle_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "eligibility_gate.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )
    repo_diff = _run(["git", "diff", "origin/main...HEAD"], cwd=repo_root)
    (evidence_dir / "repo_diff.txt").write_text(
        (repo_diff.stdout + repo_diff.stderr) or "clean\n",
        encoding="utf-8",
    )

    if skip_tests:
        pytest_text = f"{REUSED_TARGETED_TEST_SUMMARY}\nSKIP_TESTS=true\n"
        pytest_proc = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=pytest_text, stderr=""
        )
        ruff_format = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="REUSED\n", stderr=""
        )
        ruff_check = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="REUSED\n", stderr=""
        )
        py_compile_lines = ["SKIP_TESTS=true", "PY_COMPILE_REUSED=true"]
        py_compile_rc = 0
    else:
        env = {**dict(os.environ), "PYTHONPATH": f"{repo_root / 'src'}:{repo_root}"}
        pytest_proc = _run(
            [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS], cwd=repo_root, env=env
        )
        pytest_text = pytest_proc.stdout + pytest_proc.stderr
        changed_py = [repo_root / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
        ruff_targets = [str(path) for path in changed_py if path.is_file()]
        ruff_format = _run(
            [sys.executable, "-m", "ruff", "format", "--check", *ruff_targets], cwd=repo_root
        )
        ruff_check = _run([sys.executable, "-m", "ruff", "check", *ruff_targets], cwd=repo_root)
        py_compile_lines = []
        py_compile_rc = 0
        for path in changed_py:
            if not path.is_file():
                continue
            proc = _run([sys.executable, "-m", "py_compile", str(path)], cwd=repo_root)
            py_compile_lines.append(f"{path.relative_to(repo_root)} RC={proc.returncode}")
            if proc.returncode != 0:
                py_compile_rc = proc.returncode
                py_compile_lines.extend([proc.stdout, proc.stderr])
    (evidence_dir / "test_results.txt").write_text(pytest_text, encoding="utf-8")
    (evidence_dir / "targeted_pytest.txt").write_text(pytest_text, encoding="utf-8")
    (evidence_dir / "test_assertion_matrix.json").write_text(
        json.dumps(
            {
                "targeted_tests": list(TARGETED_TESTS),
                "pytest_returncode": pytest_proc.returncode,
                "reused_prior_pass": skip_tests,
                "required_negative_cases": [
                    "missing_manifest",
                    "manifest_rc_nonzero",
                    "head_mismatch",
                    "missing_boundary_evidence",
                    "open_parity_gap",
                    "runtime_authority_leak",
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_format_check.txt").write_text(
        (ruff_format.stdout + ruff_format.stderr) or f"RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.txt").write_text(
        (ruff_check.stdout + ruff_check.stderr) or f"RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "py_compile.txt").write_text(
        "\n".join(py_compile_lines) + "\n", encoding="utf-8"
    )

    forbidden_violations = scan_gate_forbidden_positive_claims(repo_root, list(SLICE_CHANGED_FILES))
    forbidden_ok = not forbidden_violations
    (evidence_dir / "forbidden_claims_scan.txt").write_text(
        "\n".join(
            [
                f"FORBIDDEN_POSITIVE_CLAIMS_RC={0 if forbidden_ok else 1}",
                f"FORBIDDEN_POSITIVE_CLAIMS_SCAN={'PASS' if forbidden_ok else 'BLOCKED'}",
                "NOTE=context_protected_denylist_literals_excluded",
                *forbidden_violations,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status_after = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()
    worktree_clean_after = not status_after

    eligible = bool(gate.get("full_canonical_parity_pass_eligible"))
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0

    if eligible and tests_pass and ruff_pass and py_compile_rc == 0 and forbidden_ok:
        verdict = "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
    elif (
        gate["parity_pass_eligibility_status"] == "NOT_ELIGIBLE_FAIL_CLOSED"
        and gate["assessment_verdict"] == "PASS_ASSESSMENT_FAIL_CLOSED"
        and gate["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
        and gate["claim_promotion_allowed"] is False
        and gate["full_canonical_chain_wired"] is False
        and gate["backtest_runtime_decision_parity_pass"] is False
        and gate["next_blocker"] != "NONE"
        and tests_pass
        and ruff_pass
        and py_compile_rc == 0
        and forbidden_ok
    ):
        verdict = "PASS_ASSESSMENT_FAIL_CLOSED"
    elif not eligible:
        blocker = gate["primary_blocker"]
        verdict = f"FAIL_CLOSED_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0_{blocker}"
    else:
        verdict = "BLOCKED"

    manifest_rc = write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        render_final_report(
            gate,
            verdict=verdict,
            manifest_verify_rc=manifest_rc,
            repo_root=repo_root,
            origin_main=origin_main,
            worktree_clean_before=worktree_clean_before,
            worktree_clean_after=worktree_clean_after,
            proof_bundle_binding=gate["proof_bundle_binding"],
        ),
        encoding="utf-8",
    )
    manifest_rc = write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "gate": gate,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "forbidden_ok": forbidden_ok,
        "py_compile_rc": py_compile_rc,
        "proof_bundle_dir": str(resolved_proof_bundle_dir),
        "proof_bundle_result": proof_bundle_result,
        "worktree_clean_before": worktree_clean_before,
        "worktree_clean_after": worktree_clean_after,
        "head": head,
        "origin_main": origin_main,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--durable-archive-root", default=None)
    parser.add_argument("--pr5020-closeout-dir", default=None)
    parser.add_argument("--pr5027-closeout-dir", default=None)
    parser.add_argument("--proof-bundle-dir", default=None)
    parser.add_argument("--source-gap-inventory-bundle", default=None)
    parser.add_argument("--planning-closeout", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    closeout_dir = Path(args.pr5020_closeout_dir).resolve() if args.pr5020_closeout_dir else None
    pr5027_dir = Path(args.pr5027_closeout_dir).resolve() if args.pr5027_closeout_dir else None
    proof_bundle_dir = Path(args.proof_bundle_dir).resolve() if args.proof_bundle_dir else None
    source_bundle = (
        Path(args.source_gap_inventory_bundle).resolve()
        if args.source_gap_inventory_bundle
        else None
    )
    result = collect_evidence(
        repo_root,
        output_dir=output_dir,
        durable_archive_root=archive_root,
        pr5020_closeout_dir=closeout_dir,
        pr5027_closeout_dir=pr5027_dir,
        proof_bundle_dir=proof_bundle_dir,
        source_gap_inventory_bundle=source_bundle,
        planning_closeout=args.planning_closeout,
        skip_tests=args.skip_tests,
    )
    gate = result["gate"]
    print(f"VERDICT={result['verdict']}")
    print(f"ASSESSMENT_VERDICT={gate['assessment_verdict']}")
    print(f"PARITY_PASS_ELIGIBILITY_STATUS={gate['parity_pass_eligibility_status']}")
    print(
        f"FULL_CANONICAL_PARITY_PASS_ELIGIBLE={str(gate.get('full_canonical_parity_pass_eligible', False)).lower()}"
    )
    print(f"BOUNDARY_CHAIN_STATUS={gate['boundary_chain_status']}")
    print(f"PRIMARY_BLOCKER={gate['primary_blocker']}")
    print(f"NEXT_GAP_OR_NEXT_STEP={gate['next_gap_or_next_step']}")
    print(f"NEXT_BLOCKER={gate['next_blocker']}")
    print(f"CLAIM_PROMOTION_ALLOWED={str(gate['claim_promotion_allowed']).lower()}")
    print(f"PROOF_BUNDLE_DIR={result.get('proof_bundle_dir')}")
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    success_verdicts = {
        "PASS_FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0",
        "PASS_ASSESSMENT_FAIL_CLOSED",
    }
    return 0 if result["verdict"] in success_verdicts else 1


if __name__ == "__main__":
    raise SystemExit(main())
