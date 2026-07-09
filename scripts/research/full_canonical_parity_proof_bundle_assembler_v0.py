from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    TRACE_REWIRE_BOUND_STATE,
    build_trace_matrix,
)
from scripts.research.full_canonical_parity_closure_assessment_v0 import (
    FORBIDDEN_POSITIVE_ASSIGNMENT_RES,
    FORBIDDEN_POSITIVE_CLAIM_LITERALS,
    build_closure_assessment,
)
from scripts.research.full_canonical_parity_pass_eligibility_gate_v0 import (
    REASON_GAP_ASSESSMENT_NOT_ALL_PASS,
    build_eligibility_gate,
)

ASSEMBLER_SCHEMA = "FullCanonicalParityProofBundleAssemblerV0"
ASSEMBLER_ID = "FULL_CANONICAL_PARITY_PROOF_BUNDLE_ASSEMBLER_V0"
REQUIRED_PROOF_INPUTS_SCHEMA = "FullCanonicalParityRequiredProofInputsMatrixV0"

DEFAULT_PR5020_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5020_full_canonical_parity_closure_assessment_v0_20260708T213101Z"
)
DEFAULT_PR5027_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5027_full_canonical_backtest_boundary_chain_reassessment_v0_20260709T004143Z"
)
DEFAULT_PR5028_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5028_full_canonical_parity_pass_eligibility_gate_fixture_cache_repair_v0_20260709T012954Z"
)
DEFAULT_PR5028_ELIGIBILITY_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_parity_pass_eligibility_gate_v0_20260709T004654Z"
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
    "src/trading/master_v2/surface_p_required_proof_input_binding_v0.py",
    "scripts/research/full_canonical_parity_closure_assessment_v0.py",
    "scripts/research/full_canonical_parity_pass_eligibility_gate_v0.py",
    "scripts/research/full_canonical_parity_proof_bundle_assembler_v0.py",
    "scripts/research/full_canonical_surface_p_required_proof_input_v0.py",
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_full_canonical_parity_pass_eligibility_gate_v0.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
    "tests/research/test_full_canonical_parity_proof_bundle_assembler_v0.py",
)

TARGETED_TESTS = (
    "tests/research/test_full_canonical_parity_proof_bundle_assembler_v0.py",
    "tests/research/test_full_canonical_parity_pass_eligibility_gate_v0.py",
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_full_canonical_backtest_boundary_chain_reassessment_v0.py",
    "tests/research/test_backtest_runtime_decision_parity_trace_matrix_v0.py",
    "tests/trading/master_v2/test_surface_p_required_proof_input_binding_contract_v0.py",
)


@dataclass(frozen=True)
class RequiredProofInputSpec:
    proof_input_id: str
    surface_id: str
    label: str


REQUIRED_PROOF_INPUT_SPECS: tuple[RequiredProofInputSpec, ...] = (
    RequiredProofInputSpec(
        "bull_bear_state_switch_boundary",
        "A",
        "Bull/Bear State Switch boundary/parity evidence",
    ),
    RequiredProofInputSpec("scope_adverse_exit_boundary", "B", "Scope adverse exit evidence"),
    RequiredProofInputSpec(
        "reversal_preparation_boundary",
        "C",
        "Reversal preparation evidence",
    ),
    RequiredProofInputSpec(
        "flat_before_opposite_side_boundary",
        "D",
        "Flat-before-opposite-side evidence",
    ),
    RequiredProofInputSpec(
        "survival_suitability_binding_boundary",
        "E",
        "Survival/Suitability binding evidence",
    ),
    RequiredProofInputSpec(
        "double_play_composition_boundary",
        "F",
        "Double Play composition evidence",
    ),
    RequiredProofInputSpec(
        "entry_position_exit_policy_boundary",
        "G",
        "Entry/Position/Exit policy evidence",
    ),
    RequiredProofInputSpec(
        "capital_risk_sizing_boundary",
        "H",
        "Capital/Risk/Sizing evidence",
    ),
    RequiredProofInputSpec(
        "canonical_order_intent_boundary",
        "I",
        "Canonical Order Intent boundary evidence",
    ),
    RequiredProofInputSpec(
        "safety_kernel_boundary",
        "J",
        "Safety Kernel boundary evidence",
    ),
    RequiredProofInputSpec("killswitch_boundary", "K", "KillSwitch boundary evidence"),
    RequiredProofInputSpec(
        "reconciliation_unknown_outcome_boundary",
        "L",
        "Reconciliation / Unknown Outcome evidence",
    ),
    RequiredProofInputSpec(
        "promotion_gate_boundary",
        "M",
        "Promotion Gate boundary evidence",
    ),
    RequiredProofInputSpec(
        "ai_observability_explainability_boundary",
        "N",
        "AI / Observability / Explainability boundary evidence",
    ),
    RequiredProofInputSpec(
        "feedback_learning_boundary",
        "O",
        "Feedback / Learning boundary evidence",
    ),
    RequiredProofInputSpec(
        "backtest_offline_replay_runtime_decision_parity",
        "P",
        "Backtest / Offline Replay / Runtime decision parity proof eligibility evidence",
    ),
)

REASON_CHAIN_BINDING_INCOMPLETE = "CHAIN_SURFACE_BINDING_INCOMPLETE"
REASON_UNBOUND_NODE_REMAINS = "KNOWN_UNBOUND_PARITY_NODE_REMAINS"
REASON_TRACE_REWIRE_BINDING_INCOMPLETE = "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH_INCOMPLETE"
REASON_SOURCE_MANIFEST_UNVERIFIED = "SOURCE_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_SOURCE_EVIDENCE_MISSING = "SOURCE_EVIDENCE_DIRECTORY_MISSING"
REASON_STALE_SOURCE_EVIDENCE = "STALE_SOURCE_EVIDENCE_DETECTED"
REASON_SURFACE_COVERAGE_INCOMPLETE = "REQUIRED_SURFACE_COVERAGE_INCOMPLETE"
REASON_SEMANTIC_PARITY_NOT_PROVEN = "SEMANTIC_PARITY_NOT_PROVEN_BEYOND_TRACE_BINDING"
REASON_FORBIDDEN_POSITIVE_CLAIMS = "FORBIDDEN_POSITIVE_CLAIMS_DETECTED"
REASON_ECONOMIC_EVIDENCE_NOT_PROVEN = "SYSTEM_ECONOMIC_EVIDENCE_NOT_PROVEN"
REASON_RUNTIME_REWIRE_NOT_PROVEN = "RUNTIME_REWIRE_PREREQUISITES_NOT_PROVEN"
REASON_MISSING_REQUIRED_PROOF_INPUT = "MISSING_REQUIRED_PROOF_INPUT"
REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P = "MISSING_REQUIRED_PROOF_INPUT_SURFACE_P"

STRONGER_TRACE_STATES = frozenset({TRACE_REWIRE_BOUND_STATE})


@dataclass(frozen=True)
class SourceEvidenceRef:
    evidence_id: str
    path: str
    present: bool
    manifest_present: bool
    manifest_verified: bool
    detail: str
    stale_detected: bool = False


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


def scan_assembler_forbidden_positive_claims(
    repo_root: Path, changed_files: list[str]
) -> list[str]:
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


def verify_manifest(evidence_dir: Path) -> tuple[bool, str]:
    if not evidence_dir.is_dir():
        return False, "directory missing"
    manifest = evidence_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return False, "MANIFEST.sha256 missing"
    for row in manifest.read_text(encoding="utf-8").splitlines():
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = evidence_dir / rel
        if not target.is_file() or _sha256_bytes(target.read_bytes()) != digest:
            return False, f"manifest mismatch for {rel}"
    return True, "verified"


def _extract_post_merge_head(evidence_dir: Path) -> str | None:
    final_report = evidence_dir / "final_report.txt"
    if not final_report.is_file():
        return None
    for line in final_report.read_text(encoding="utf-8").splitlines():
        if line.startswith("POST_MERGE_HEAD=") or line.startswith("POST_MERGE_ORIGIN_MAIN="):
            return line.split("=", 1)[1].strip()
    git_context = evidence_dir / "git_context.txt"
    if git_context.is_file():
        for line in git_context.read_text(encoding="utf-8").splitlines():
            if line.startswith("ORIGIN_MAIN=") or line.startswith("HEAD="):
                return line.split("=", 1)[1].strip()
    return None


def _load_gap_assessment_counts() -> dict[str, int]:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_status_counts_v0,
        parity_surface_assessments_v0,
    )

    counts = dict(parity_status_counts_v0())
    counts["TOTAL_SURFACES"] = len(parity_surface_assessments_v0())
    return counts


def _evidence_ref_path(ref: str) -> str:
    return ref.split("::", 1)[0]


def _count_present_evidence_refs(
    repo_root: Path, evidence_refs: tuple[str, ...]
) -> tuple[int, list[str]]:
    present: list[str] = []
    missing: list[str] = []
    for ref in evidence_refs:
        rel = _evidence_ref_path(ref)
        if (repo_root / rel).is_file():
            present.append(ref)
        else:
            missing.append(ref)
    return len(present), missing


def _surface_p_proof_input_entry(
    repo_root: Path,
    *,
    spec: RequiredProofInputSpec,
    assessment: Any,
) -> dict[str, Any]:
    from trading.master_v2.surface_p_required_proof_input_binding_v0 import (
        evaluate_surface_p_required_proof_input_binding_v0,
    )

    binding = evaluate_surface_p_required_proof_input_binding_v0(repo_root)
    return {
        "proof_input_id": spec.proof_input_id,
        "surface_id": spec.surface_id,
        "label": spec.label,
        "present": True,
        "parity_status": assessment.parity_status,
        "registry_parity_status": binding.registry_parity_status,
        "binding_owner": binding.owner,
        "binding_status": binding.binding_status,
        "offline_four_way_fixtures_complete": binding.offline_four_way_fixtures_complete,
        "semantic_binding_confirmations_complete": binding.semantic_binding_confirmations_complete,
        "surface_p_offline_parity_complete": binding.surface_p_offline_parity_complete,
        "runtime_bridge_bound_not_activated": binding.runtime_bridge_bound_not_activated,
        "evidence_ref_count": binding.evidence_ref_count,
        "present_evidence_ref_count": binding.present_evidence_ref_count,
        "missing_evidence_refs": list(binding.missing_evidence_refs),
        "status": binding.binding_status,
        "satisfied": binding.satisfied,
        "detail": binding.detail,
    }


def build_required_proof_inputs_matrix(repo_root: Path) -> dict[str, Any]:
    sys.path.insert(0, str(_REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
    )

    assessments_by_id = {item.surface_id: item for item in parity_surface_assessments_v0()}
    proof_inputs: list[dict[str, Any]] = []
    missing_proof_input_ids: list[str] = []
    satisfied_count = 0

    for spec in REQUIRED_PROOF_INPUT_SPECS:
        assessment = assessments_by_id.get(spec.surface_id)
        if assessment is None:
            proof_inputs.append(
                {
                    "proof_input_id": spec.proof_input_id,
                    "surface_id": spec.surface_id,
                    "label": spec.label,
                    "present": False,
                    "parity_status": "MISSING",
                    "evidence_ref_count": 0,
                    "present_evidence_ref_count": 0,
                    "missing_evidence_refs": [],
                    "status": "MISSING_REQUIRED_PROOF_INPUT",
                    "satisfied": False,
                    "detail": "surface assessment missing from gap registry",
                }
            )
            missing_proof_input_ids.append(spec.proof_input_id)
            continue

        if spec.surface_id == "P":
            entry = _surface_p_proof_input_entry(repo_root, spec=spec, assessment=assessment)
            proof_inputs.append(entry)
            if entry["satisfied"]:
                satisfied_count += 1
            else:
                missing_proof_input_ids.append(spec.proof_input_id)
            continue

        present_ref_count, missing_refs = _count_present_evidence_refs(
            repo_root, assessment.evidence_refs
        )
        parity_pass = assessment.parity_status == "PASS"
        refs_present = present_ref_count > 0
        satisfied = parity_pass and refs_present
        status = "VERIFIED" if satisfied else "MISSING_REQUIRED_PROOF_INPUT"
        if satisfied:
            satisfied_count += 1
        else:
            missing_proof_input_ids.append(spec.proof_input_id)

        detail_parts: list[str] = []
        if not parity_pass:
            detail_parts.append(f"parity_status={assessment.parity_status}")
        if not refs_present:
            detail_parts.append("no_present_evidence_refs")

        proof_inputs.append(
            {
                "proof_input_id": spec.proof_input_id,
                "surface_id": spec.surface_id,
                "label": spec.label,
                "present": True,
                "parity_status": assessment.parity_status,
                "evidence_ref_count": len(assessment.evidence_refs),
                "present_evidence_ref_count": present_ref_count,
                "missing_evidence_refs": missing_refs,
                "status": status,
                "satisfied": satisfied,
                "detail": "; ".join(detail_parts) if detail_parts else "verified",
            }
        )

    return {
        "schema": REQUIRED_PROOF_INPUTS_SCHEMA,
        "required_proof_input_count": len(REQUIRED_PROOF_INPUT_SPECS),
        "satisfied_proof_input_count": satisfied_count,
        "required_proof_inputs_complete": not missing_proof_input_ids,
        "missing_proof_input_ids": missing_proof_input_ids,
        "proof_inputs": proof_inputs,
    }


def _verify_eligibility_with_closeout_attestation(
    eligibility_dir: Path,
    closeout_dir: Path,
) -> tuple[bool, str]:
    verified, detail = verify_manifest(eligibility_dir)
    if verified:
        return True, detail
    if not closeout_dir.is_dir():
        return False, detail
    closeout_ok, closeout_detail = verify_manifest(closeout_dir)
    if not closeout_ok:
        return False, f"{detail}; closeout_unverified={closeout_detail}"
    ref_file = closeout_dir / "eligibility_gate_ref.txt"
    final_report = closeout_dir / "eligibility_gate_final_report.txt"
    if ref_file.is_file() and final_report.is_file():
        ref_text = ref_file.read_text(encoding="utf-8")
        if str(eligibility_dir) in ref_text and "ELIGIBILITY_GATE_RC=0" in ref_text:
            return True, f"{detail}; closeout_attested_eligibility_gate_rc=0"
    closeout_final = closeout_dir / "final_report.txt"
    if closeout_final.is_file():
        source_dir: str | None = None
        source_manifest_rc: str | None = None
        for line in closeout_final.read_text(encoding="utf-8").splitlines():
            if line.startswith("SOURCE_EVIDENCE_DIR="):
                source_dir = line.split("=", 1)[1].strip()
            elif line.startswith("SOURCE_MANIFEST_VERIFY_RC="):
                source_manifest_rc = line.split("=", 1)[1].strip()
        if (
            source_dir == str(eligibility_dir)
            and source_manifest_rc == "0"
            and "SOURCE_EVIDENCE_REFERENCED=true" in closeout_final.read_text(encoding="utf-8")
        ):
            return True, f"{detail}; closeout_attested_source_manifest_verify_rc=0"
    return False, detail


def _is_stale_evidence_head(
    recorded_head: str | None, current_origin_main: str, repo_root: Path
) -> bool:
    if not recorded_head or recorded_head == current_origin_main:
        return False
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", recorded_head, current_origin_main],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode != 0


def collect_source_evidence_refs(
    *,
    pr5020_closeout_dir: Path,
    pr5027_closeout_dir: Path,
    pr5028_closeout_dir: Path,
    pr5028_eligibility_dir: Path,
    current_origin_main: str,
    repo_root: Path,
) -> list[SourceEvidenceRef]:
    refs: list[SourceEvidenceRef] = []
    for evidence_id, path, closeout_for_attestation in (
        ("pr5020_closeout", pr5020_closeout_dir, None),
        ("pr5027_closeout", pr5027_closeout_dir, None),
        ("pr5028_closeout", pr5028_closeout_dir, None),
        ("pr5028_eligibility_gate", pr5028_eligibility_dir, pr5028_closeout_dir),
    ):
        present = path.is_dir()
        manifest_present = (path / "MANIFEST.sha256").is_file() if present else False
        if not present:
            refs.append(
                SourceEvidenceRef(
                    evidence_id=evidence_id,
                    path=str(path),
                    present=False,
                    manifest_present=False,
                    manifest_verified=False,
                    detail="directory missing",
                )
            )
            continue
        if closeout_for_attestation is not None:
            verified, detail = _verify_eligibility_with_closeout_attestation(
                path, closeout_for_attestation
            )
        else:
            verified, detail = verify_manifest(path)
        stale = False
        if verified:
            recorded_head = _extract_post_merge_head(path)
            if _is_stale_evidence_head(recorded_head, current_origin_main, repo_root):
                stale = True
                detail = f"{detail}; stale head {recorded_head} != {current_origin_main}"
        refs.append(
            SourceEvidenceRef(
                evidence_id=evidence_id,
                path=str(path),
                present=True,
                manifest_present=manifest_present,
                manifest_verified=verified,
                detail=detail,
                stale_detected=stale,
            )
        )
    return refs


def build_surface_coverage_matrix(closure: dict[str, Any]) -> dict[str, Any]:
    edges = closure["trace_edges"]
    by_surface = {edge["surface_id"]: edge for edge in edges}
    surfaces: list[dict[str, Any]] = []
    missing: list[str] = []
    covered = 0
    for surface_id in TRACE_PRIORITY:
        edge = by_surface.get(surface_id)
        if edge is None:
            missing.append(surface_id)
            surfaces.append(
                {
                    "surface_id": surface_id,
                    "present": False,
                    "trace_state": "MISSING",
                    "binding_status": "MISSING",
                    "meets_required_binding": False,
                }
            )
            continue
        trace_state = edge["trace_state"]
        meets = trace_state in STRONGER_TRACE_STATES
        if meets:
            covered += 1
        else:
            missing.append(surface_id)
        surfaces.append(
            {
                "surface_id": surface_id,
                "present": True,
                "trace_state": trace_state,
                "binding_status": trace_state,
                "meets_required_binding": meets,
                "next_action": edge["next_action"],
            }
        )
    return {
        "schema": "FullCanonicalParitySurfaceCoverageMatrixV0",
        "required_surface_count": len(TRACE_PRIORITY),
        "covered_surface_count": covered,
        "surface_coverage_complete": len(missing) == 0 and covered == len(TRACE_PRIORITY),
        "missing_surfaces": missing,
        "surfaces": surfaces,
    }


def evaluate_proof_bundle(
    repo_root: Path,
    *,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
    pr5028_closeout_dir: Path | None = None,
    pr5028_eligibility_dir: Path | None = None,
    current_origin_main: str | None = None,
    forbidden_violations: list[str] | None = None,
) -> dict[str, Any]:
    closure = build_closure_assessment(repo_root)
    closeout_5020 = pr5020_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    closeout_5027 = pr5027_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
    )
    closeout_5028 = pr5028_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5028_CLOSEOUT_EVIDENCE", DEFAULT_PR5028_CLOSEOUT_EVIDENCE)
    )
    eligibility_5028 = pr5028_eligibility_dir or Path(
        os.environ.get(
            "PEAK_TRADE_PR5028_ELIGIBILITY_EVIDENCE", DEFAULT_PR5028_ELIGIBILITY_EVIDENCE
        )
    )
    gate = build_eligibility_gate(
        repo_root,
        pr5020_closeout_dir=closeout_5020,
        pr5027_closeout_dir=closeout_5027,
    )
    inventory = build_inventory(repo_root)
    matrix = build_trace_matrix(inventory)
    gap_counts = _load_gap_assessment_counts()
    proof_inputs = build_required_proof_inputs_matrix(repo_root)
    gap_all_pass = (
        gap_counts.get("PARTIAL", 0) == 0
        and gap_counts.get("GAP", 0) == 0
        and gap_counts.get("PASS", 0) == gap_counts.get("TOTAL_SURFACES", 0)
    )

    origin_main = current_origin_main
    if origin_main is None:
        proc = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        origin_main = proc.stdout.strip()

    source_refs = collect_source_evidence_refs(
        pr5020_closeout_dir=closeout_5020,
        pr5027_closeout_dir=closeout_5027,
        pr5028_closeout_dir=closeout_5028,
        pr5028_eligibility_dir=eligibility_5028,
        current_origin_main=origin_main,
        repo_root=repo_root,
    )
    coverage = build_surface_coverage_matrix(closure)

    reason_codes: list[str] = []
    if forbidden_violations:
        reason_codes.append(REASON_FORBIDDEN_POSITIVE_CLAIMS)
    missing_sources = [ref for ref in source_refs if not ref.present]
    if missing_sources:
        reason_codes.append(REASON_SOURCE_EVIDENCE_MISSING)
    unverified_sources = [ref for ref in source_refs if ref.present and not ref.manifest_verified]
    if unverified_sources:
        reason_codes.append(REASON_SOURCE_MANIFEST_UNVERIFIED)
    stale_sources = [ref for ref in source_refs if ref.stale_detected]
    if stale_sources:
        reason_codes.append(REASON_STALE_SOURCE_EVIDENCE)
    if not closure["chain_surface_binding_complete"]:
        reason_codes.append(REASON_CHAIN_BINDING_INCOMPLETE)
    if closure["next_unbound_node"] != "NONE":
        reason_codes.append(REASON_UNBOUND_NODE_REMAINS)
    if not all(edge["trace_state"] in STRONGER_TRACE_STATES for edge in closure["trace_edges"]):
        reason_codes.append(REASON_TRACE_REWIRE_BINDING_INCOMPLETE)
    if not coverage["surface_coverage_complete"]:
        reason_codes.append(REASON_SURFACE_COVERAGE_INCOMPLETE)
    if not proof_inputs["required_proof_inputs_complete"]:
        if proof_inputs["missing_proof_input_ids"] == [
            "backtest_offline_replay_runtime_decision_parity"
        ]:
            reason_codes.append(REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P)
        reason_codes.append(REASON_MISSING_REQUIRED_PROOF_INPUT)
    if not gap_all_pass:
        reason_codes.append(REASON_GAP_ASSESSMENT_NOT_ALL_PASS)

    structural_ok = not {
        REASON_FORBIDDEN_POSITIVE_CLAIMS,
        REASON_SOURCE_EVIDENCE_MISSING,
        REASON_SOURCE_MANIFEST_UNVERIFIED,
        REASON_STALE_SOURCE_EVIDENCE,
        REASON_CHAIN_BINDING_INCOMPLETE,
        REASON_UNBOUND_NODE_REMAINS,
        REASON_TRACE_REWIRE_BINDING_INCOMPLETE,
        REASON_SURFACE_COVERAGE_INCOMPLETE,
        REASON_MISSING_REQUIRED_PROOF_INPUT,
        REASON_MISSING_REQUIRED_PROOF_INPUT_SURFACE_P,
    }.intersection(reason_codes)

    semantic_ok = structural_ok and gap_all_pass
    if structural_ok and not gap_all_pass:
        reason_codes.append(REASON_SEMANTIC_PARITY_NOT_PROVEN)

    if semantic_ok:
        full_parity_proof_bundle_status = "PROVEN_MANIFEST_VERIFIED"
        full_canonical_chain_wired = True
        backtest_runtime_decision_parity_pass = True
        claim_promotion_allowed = True
        next_blocker = REASON_ECONOMIC_EVIDENCE_NOT_PROVEN
        reason_codes.extend([REASON_ECONOMIC_EVIDENCE_NOT_PROVEN, REASON_RUNTIME_REWIRE_NOT_PROVEN])
    else:
        full_parity_proof_bundle_status = "NOT_PROVEN_FAIL_CLOSED"
        full_canonical_chain_wired = False
        backtest_runtime_decision_parity_pass = False
        claim_promotion_allowed = False
        next_blocker = reason_codes[0] if reason_codes else REASON_SEMANTIC_PARITY_NOT_PROVEN

    return {
        "schema": ASSEMBLER_SCHEMA,
        "assembler_id": ASSEMBLER_ID,
        "source_closure_assessment_schema": closure["schema"],
        "source_eligibility_gate_schema": gate["schema"],
        "source_boundary_chain_reassessment_schema": gate[
            "source_boundary_chain_reassessment_schema"
        ],
        "source_trace_matrix_schema": matrix["schema"],
        "source_evidence_refs": [asdict(ref) for ref in source_refs],
        "source_evidence_count": len(source_refs),
        "source_evidence_all_manifests_verified": all(
            ref.manifest_verified for ref in source_refs if ref.present
        )
        and not missing_sources,
        "source_evidence_missing": [ref.evidence_id for ref in missing_sources],
        "stale_source_evidence_detected": any(ref.stale_detected for ref in source_refs),
        "required_proof_inputs_matrix": proof_inputs,
        "required_proof_input_count": proof_inputs["required_proof_input_count"],
        "satisfied_proof_input_count": proof_inputs["satisfied_proof_input_count"],
        "required_proof_inputs_complete": proof_inputs["required_proof_inputs_complete"],
        "missing_proof_input_ids": proof_inputs["missing_proof_input_ids"],
        "surface_coverage_matrix": coverage,
        "surface_coverage_complete": coverage["surface_coverage_complete"],
        "required_surface_count": coverage["required_surface_count"],
        "covered_surface_count": coverage["covered_surface_count"],
        "missing_surfaces": coverage["missing_surfaces"],
        "chain_surface_binding_complete": closure["chain_surface_binding_complete"],
        "next_unbound_node": closure["next_unbound_node"],
        "boundary_chain_status": gate["boundary_chain_status"],
        "pass_eligibility_primary_blocker": gate["primary_blocker"],
        "pass_eligibility_next_step": gate["next_gap_or_next_step"],
        "closure_required_proof_inputs_complete": closure.get(
            "required_proof_inputs_complete", False
        ),
        "eligibility_required_proof_inputs_complete": gate.get(
            "required_proof_inputs_complete", False
        ),
        "required_proof_inputs_binding_consistent": (
            closure.get("required_proof_inputs_complete", False)
            == proof_inputs["required_proof_inputs_complete"]
            == gate.get("required_proof_inputs_complete", False)
        ),
        "parity_pass_claim_deferred": True,
        "gap_assessment_counts": gap_counts,
        "gap_assessment_all_pass": gap_all_pass,
        "full_parity_proof_bundle_status": full_parity_proof_bundle_status,
        "full_canonical_chain_wired": full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "claim_promotion_allowed": claim_promotion_allowed,
        "next_blocker": next_blocker,
        "reason_codes": reason_codes,
        "no_runtime_authority_confirmed": True,
        "no_economic_claim_confirmed": True,
        "assembler_rule": (
            "Manifest-verified source evidence, complete required proof-input coverage, and "
            "complete trace-rewire surface binding are necessary but not sufficient for full "
            "parity proof. Gap-assessment PASS across all surfaces is required before "
            "FULL_CANONICAL_CHAIN_WIRED and BACKTEST_RUNTIME_DECISION_PARITY_PASS may become "
            "true. Economic and runtime-rewire claims remain deferred unless separately proven."
        ),
    }


def render_final_report(bundle: dict[str, Any], *, verdict: str, manifest_verify_rc: int) -> str:
    lines = [
        f"VERDICT={verdict}",
        f"ASSEMBLER_ID={bundle['assembler_id']}",
        f"FULL_PARITY_PROOF_BUNDLE_STATUS={bundle['full_parity_proof_bundle_status']}",
        f"FULL_PARITY_PROOF_BUNDLE_MANIFEST_VERIFY_RC={manifest_verify_rc}",
        f"SOURCE_EVIDENCE_COUNT={bundle['source_evidence_count']}",
        (
            "SOURCE_EVIDENCE_ALL_MANIFESTS_VERIFIED="
            f"{str(bundle['source_evidence_all_manifests_verified']).lower()}"
        ),
        f"SOURCE_EVIDENCE_MISSING={','.join(bundle['source_evidence_missing']) or 'NONE'}",
        (f"STALE_SOURCE_EVIDENCE_DETECTED={str(bundle['stale_source_evidence_detected']).lower()}"),
        f"REQUIRED_PROOF_INPUT_COUNT={bundle['required_proof_input_count']}",
        f"SATISFIED_PROOF_INPUT_COUNT={bundle['satisfied_proof_input_count']}",
        (f"REQUIRED_PROOF_INPUTS_COMPLETE={str(bundle['required_proof_inputs_complete']).lower()}"),
        f"MISSING_PROOF_INPUT_IDS={','.join(bundle['missing_proof_input_ids']) or 'NONE'}",
        f"BOUNDARY_CHAIN_STATUS={bundle['boundary_chain_status']}",
        f"PASS_ELIGIBILITY_PRIMARY_BLOCKER={bundle['pass_eligibility_primary_blocker']}",
        f"PASS_ELIGIBILITY_NEXT_STEP={bundle['pass_eligibility_next_step']}",
        f"SURFACE_COVERAGE_COMPLETE={str(bundle['surface_coverage_complete']).lower()}",
        f"REQUIRED_SURFACE_COUNT={bundle['required_surface_count']}",
        f"COVERED_SURFACE_COUNT={bundle['covered_surface_count']}",
        f"MISSING_SURFACES={','.join(bundle['missing_surfaces']) or 'NONE'}",
        (f"CHAIN_SURFACE_BINDING_COMPLETE={str(bundle['chain_surface_binding_complete']).lower()}"),
        f"NEXT_UNBOUND_NODE={bundle['next_unbound_node']}",
        f"PARITY_PASS_CLAIM_DEFERRED={str(bundle['parity_pass_claim_deferred']).lower()}",
        f"FULL_CANONICAL_CHAIN_WIRED={str(bundle['full_canonical_chain_wired']).lower()}",
        (
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
            f"{str(bundle['backtest_runtime_decision_parity_pass']).lower()}"
        ),
        (
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
            f"{str(bundle['system_economic_evidence_admissible']).lower()}"
        ),
        f"RUNTIME_REWIRE_ADMISSIBLE={str(bundle['runtime_rewire_admissible']).lower()}",
        f"CLAIM_PROMOTION_ALLOWED={str(bundle['claim_promotion_allowed']).lower()}",
        f"NEXT_BLOCKER={bundle['next_blocker']}",
        f"REASON_CODES={','.join(bundle['reason_codes'])}",
        "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
        "NO_ECONOMIC_CLAIM_CONFIRMED=true",
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


REASON_RUFF_MODULE_UNAVAILABLE = "RUFF_MODULE_UNAVAILABLE"


def _ruff_module_available() -> tuple[bool, str]:
    probe = _run([sys.executable, "-m", "ruff", "--version"], cwd=_REPO_ROOT)
    if probe.returncode == 0:
        return True, (probe.stdout + probe.stderr).strip() or "ruff available"
    detail = (probe.stdout + probe.stderr).strip() or "ruff module probe failed"
    return False, detail


def _run_ruff(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    available, detail = _ruff_module_available()
    if not available:
        return subprocess.CompletedProcess(
            args=[sys.executable, "-m", "ruff", *args],
            returncode=1,
            stdout="",
            stderr=f"{REASON_RUFF_MODULE_UNAVAILABLE}: {detail}\n",
        )
    return _run([sys.executable, "-m", "ruff", *args], cwd=cwd)


def collect_evidence(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    durable_archive_root: Path | None = None,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
    pr5028_closeout_dir: Path | None = None,
    pr5028_eligibility_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    archive_root = Path(
        durable_archive_root
        or os.environ.get(
            "PEAK_TRADE_DURABLE_ARCHIVE_ROOT",
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
        )
    )
    evidence_dir = output_dir or (
        archive_root / f"research/full_canonical_parity_proof_bundle_v0_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()

    forbidden_violations = scan_assembler_forbidden_positive_claims(
        repo_root, list(SLICE_CHANGED_FILES)
    )
    bundle = evaluate_proof_bundle(
        repo_root,
        pr5020_closeout_dir=pr5020_closeout_dir,
        pr5027_closeout_dir=pr5027_closeout_dir,
        pr5028_closeout_dir=pr5028_closeout_dir,
        pr5028_eligibility_dir=pr5028_eligibility_dir,
        current_origin_main=origin_main,
        forbidden_violations=forbidden_violations,
    )

    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BRANCH={branch}",
                f"WORKTREE_STATUS={status or 'clean'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "proof_bundle.json").write_text(
        json.dumps(bundle, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_evidence_index.json").write_text(
        json.dumps(bundle["source_evidence_refs"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "surface_coverage_matrix.json").write_text(
        json.dumps(bundle["surface_coverage_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "required_proof_inputs_matrix.json").write_text(
        json.dumps(bundle["required_proof_inputs_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reason_codes.json").write_text(
        json.dumps(
            {
                "reason_codes": bundle["reason_codes"],
                "next_blocker": bundle["next_blocker"],
                "full_parity_proof_bundle_status": bundle["full_parity_proof_bundle_status"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    env = {**dict(os.environ), "PYTHONPATH": f"{repo_root / 'src'}:{repo_root}"}
    pytest_proc = _run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS], cwd=repo_root, env=env
    )
    (evidence_dir / "targeted_pytest.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    changed_py = [repo_root / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
    ruff_targets = [str(path) for path in changed_py if path.is_file()]
    ruff_format = _run_ruff(["format", "--check", *ruff_targets], cwd=repo_root)
    ruff_check = _run_ruff(["check", *ruff_targets], cwd=repo_root)
    (evidence_dir / "ruff_format_check.txt").write_text(
        (ruff_format.stdout + ruff_format.stderr) or f"RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.txt").write_text(
        (ruff_check.stdout + ruff_check.stderr) or f"RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    py_compile_lines: list[str] = []
    py_compile_rc = 0
    for path in changed_py:
        if not path.is_file():
            continue
        proc = _run([sys.executable, "-m", "py_compile", str(path)], cwd=repo_root)
        py_compile_lines.append(f"{path.relative_to(repo_root)} RC={proc.returncode}")
        if proc.returncode != 0:
            py_compile_rc = proc.returncode
            py_compile_lines.extend([proc.stdout, proc.stderr])
    (evidence_dir / "py_compile.txt").write_text(
        "\n".join(py_compile_lines) + "\n", encoding="utf-8"
    )

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

    bundle_pass = (
        bundle["full_parity_proof_bundle_status"] == "NOT_PROVEN_FAIL_CLOSED"
        and bundle["full_canonical_chain_wired"] is False
        and bundle["backtest_runtime_decision_parity_pass"] is False
        and bundle["claim_promotion_allowed"] is False
        and bundle["system_economic_evidence_admissible"] is False
        and bundle["runtime_rewire_admissible"] is False
        and bundle["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
        and bundle["chain_surface_binding_complete"] is True
        and bundle["next_unbound_node"] == "NONE"
        and bundle["surface_coverage_complete"] is True
        and bundle["required_proof_input_count"] == 16
        and bundle["required_proof_inputs_complete"] is True
        and bundle["satisfied_proof_input_count"] == 16
        and bundle["source_evidence_all_manifests_verified"] is True
        and not bundle["stale_source_evidence_detected"]
        and bundle["next_blocker"] == REASON_GAP_ASSESSMENT_NOT_ALL_PASS
    )
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        "PROOF_BUNDLE_ASSEMBLER_PASS_FAIL_CLOSED"
        if bundle_pass and tests_pass and ruff_pass and py_compile_rc == 0 and forbidden_ok
        else "BLOCKED"
    )

    manifest_rc = write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        render_final_report(bundle, verdict=verdict, manifest_verify_rc=manifest_rc),
        encoding="utf-8",
    )
    manifest_rc = write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "bundle": bundle,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "forbidden_ok": forbidden_ok,
        "py_compile_rc": py_compile_rc,
        "pytest_rc": pytest_proc.returncode,
        "ruff_format_rc": ruff_format.returncode,
        "ruff_check_rc": ruff_check.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--durable-archive-root", default=None)
    parser.add_argument("--pr5020-closeout-dir", default=None)
    parser.add_argument("--pr5027-closeout-dir", default=None)
    parser.add_argument("--pr5028-closeout-dir", default=None)
    parser.add_argument("--pr5028-eligibility-dir", default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    closeout_5020 = Path(args.pr5020_closeout_dir).resolve() if args.pr5020_closeout_dir else None
    closeout_5027 = Path(args.pr5027_closeout_dir).resolve() if args.pr5027_closeout_dir else None
    closeout_5028 = Path(args.pr5028_closeout_dir).resolve() if args.pr5028_closeout_dir else None
    eligibility_5028 = (
        Path(args.pr5028_eligibility_dir).resolve() if args.pr5028_eligibility_dir else None
    )
    result = collect_evidence(
        repo_root,
        output_dir=output_dir,
        durable_archive_root=archive_root,
        pr5020_closeout_dir=closeout_5020,
        pr5027_closeout_dir=closeout_5027,
        pr5028_closeout_dir=closeout_5028,
        pr5028_eligibility_dir=eligibility_5028,
    )
    bundle = result["bundle"]
    print(f"VERDICT={result['verdict']}")
    print(f"FULL_PARITY_PROOF_BUNDLE_STATUS={bundle['full_parity_proof_bundle_status']}")
    print(f"NEXT_BLOCKER={bundle['next_blocker']}")
    print(f"CLAIM_PROMOTION_ALLOWED={str(bundle['claim_promotion_allowed']).lower()}")
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == "PROOF_BUNDLE_ASSEMBLER_PASS_FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
