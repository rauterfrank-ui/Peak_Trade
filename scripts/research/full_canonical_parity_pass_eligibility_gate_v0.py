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


def evaluate_eligibility_criteria(
    repo_root: Path,
    closure: dict[str, Any],
    boundary: dict[str, Any],
    *,
    pr5020_closeout_verified: bool,
    pr5027_closeout_verified: bool,
    pr5027_closeout_reference_available: bool,
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
            satisfied=False,
            required=True,
            blocker_code=REASON_MANIFEST_VERIFIED_FULL_PARITY_PROOF_MISSING,
            detail="no manifest-verified full-chain parity proof bundle referenced",
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


def build_eligibility_gate(
    repo_root: Path,
    *,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
) -> dict[str, Any]:
    closure = build_closure_assessment(repo_root)
    boundary = build_boundary_chain_reassessment(repo_root)
    closeout_dir = pr5020_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5020_CLOSEOUT_EVIDENCE", DEFAULT_PR5020_CLOSEOUT_EVIDENCE)
    )
    pr5027_dir = pr5027_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5027_CLOSEOUT_EVIDENCE", DEFAULT_PR5027_CLOSEOUT_EVIDENCE)
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
    )
    failed = [item for item in criteria if item.required and not item.satisfied]
    claim_promotion_allowed = not failed

    if claim_promotion_allowed:
        parity_pass_eligibility_status = "ELIGIBLE_FOR_SEPARATE_PARITY_PASS_EVIDENCE"
        next_blocker = "NONE"
        primary_blocker = "NONE"
        next_gap_or_next_step = NEXT_STEP_AFTER_NOT_ELIGIBLE
        reason_codes = ["ALL_REQUIRED_ELIGIBILITY_CRITERIA_SATISFIED"]
    else:
        parity_pass_eligibility_status = "NOT_ELIGIBLE_FAIL_CLOSED"
        next_blocker = failed[0].blocker_code
        primary_blocker = next_blocker
        next_gap_or_next_step = NEXT_STEP_AFTER_NOT_ELIGIBLE
        reason_codes = [item.blocker_code for item in failed]

    assessment_verdict = (
        "PASS_ASSESSMENT_FAIL_CLOSED"
        if (
            parity_pass_eligibility_status == "NOT_ELIGIBLE_FAIL_CLOSED"
            and not claim_promotion_allowed
            and boundary["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
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
        "next_blocker": next_blocker,
        "claim_promotion_allowed": claim_promotion_allowed,
        "evidence_admissibility_reason_codes": reason_codes,
        "no_runtime_authority_confirmed": True,
        "no_economic_claim_confirmed": True,
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


def render_final_report(gate: dict[str, Any], *, verdict: str, manifest_verify_rc: int) -> str:
    lines = [
        f"VERDICT={verdict}",
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


def collect_evidence(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    durable_archive_root: Path | None = None,
    pr5020_closeout_dir: Path | None = None,
    pr5027_closeout_dir: Path | None = None,
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
        archive_root / f"research/full_canonical_parity_pass_eligibility_gate_v0_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()

    gate = build_eligibility_gate(
        repo_root,
        pr5020_closeout_dir=pr5020_closeout_dir,
        pr5027_closeout_dir=pr5027_closeout_dir,
    )
    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BRANCH={branch}",
                f"WORKTREE_STATUS={status or 'clean'}",
                f"SOURCE_PR5027_CLOSEOUT_DIR={gate['source_pr5027_closeout_dir']}",
                f"SOURCE_PR5020_CLOSEOUT_DIR={gate['source_pr5020_closeout_dir']}",
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
    ruff_format = _run(["ruff", "format", "--check", *ruff_targets], cwd=repo_root)
    ruff_check = _run(["ruff", "check", *ruff_targets], cwd=repo_root)
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

    gate_pass = (
        gate["parity_pass_eligibility_status"] == "NOT_ELIGIBLE_FAIL_CLOSED"
        and gate["assessment_verdict"] == "PASS_ASSESSMENT_FAIL_CLOSED"
        and gate["boundary_chain_status"] == "FAIL_CLOSED_DOCUMENTED"
        and gate["claim_promotion_allowed"] is False
        and gate["full_canonical_chain_wired"] is False
        and gate["backtest_runtime_decision_parity_pass"] is False
        and gate["next_blocker"] != "NONE"
    )
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        "PASS_ASSESSMENT_FAIL_CLOSED"
        if gate_pass and tests_pass and ruff_pass and py_compile_rc == 0 and forbidden_ok
        else "BLOCKED"
    )

    manifest_rc = write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        render_final_report(gate, verdict=verdict, manifest_verify_rc=manifest_rc),
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
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--durable-archive-root", default=None)
    parser.add_argument("--pr5020-closeout-dir", default=None)
    parser.add_argument("--pr5027-closeout-dir", default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    closeout_dir = Path(args.pr5020_closeout_dir).resolve() if args.pr5020_closeout_dir else None
    pr5027_dir = Path(args.pr5027_closeout_dir).resolve() if args.pr5027_closeout_dir else None
    result = collect_evidence(
        repo_root,
        output_dir=output_dir,
        durable_archive_root=archive_root,
        pr5020_closeout_dir=closeout_dir,
        pr5027_closeout_dir=pr5027_dir,
    )
    gate = result["gate"]
    print(f"VERDICT={result['verdict']}")
    print(f"ASSESSMENT_VERDICT={gate['assessment_verdict']}")
    print(f"PARITY_PASS_ELIGIBILITY_STATUS={gate['parity_pass_eligibility_status']}")
    print(f"BOUNDARY_CHAIN_STATUS={gate['boundary_chain_status']}")
    print(f"PRIMARY_BLOCKER={gate['primary_blocker']}")
    print(f"NEXT_GAP_OR_NEXT_STEP={gate['next_gap_or_next_step']}")
    print(f"NEXT_BLOCKER={gate['next_blocker']}")
    print(f"CLAIM_PROMOTION_ALLOWED={str(gate['claim_promotion_allowed']).lower()}")
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == "PASS_ASSESSMENT_FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
