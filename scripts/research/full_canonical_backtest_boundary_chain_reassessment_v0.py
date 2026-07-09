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
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import build_inventory
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    build_trace_matrix,
    compute_chain_surface_binding_complete,
    compute_next_unbound_node,
)
from scripts.research.full_canonical_parity_closure_assessment_v0 import (
    build_closure_assessment,
)

ASSESSMENT_SLICE_ID = "FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0"
ASSESSMENT_SCHEMA = "FullCanonicalBacktestBoundaryChainReassessmentV0"
FEATURE_BRANCH = "core-system-completion-full-canonical-backtest-boundary-chain-reassessment-v0"
NEXT_STEP_AFTER_PASS = "FULL_CANONICAL_PARITY_PASS_ELIGIBILITY_GATE_V0"
DEFAULT_PR5026_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5026_runtime_bridge_boundary_rewire_or_gap_assessment_v0_20260709T001400Z"
)

TOLERATED_UNTRACKED_PREFIXES = (
    ".python-version",
    ".comparison_ssot_pytest_outputs/",
)

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "NARROW_REWIRE_JUSTIFIED=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"NARROW_REWIRE_JUSTIFIED\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
    re.compile(r'"narrow_rewire_justified"\s*:\s*true\b'),
)

CONTEXT_PROTECTED_MARKERS = (
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

SLICE_CHANGED_FILES = (
    "scripts/research/full_canonical_backtest_boundary_chain_reassessment_v0.py",
    "tests/research/test_full_canonical_backtest_boundary_chain_reassessment_v0.py",
)

TARGETED_TESTS = ("tests/research/test_full_canonical_backtest_boundary_chain_reassessment_v0.py",)

REASON_PR5026_SOURCE_MISSING = "PR5026_CLOSEOUT_EVIDENCE_MISSING"
REASON_PR5026_MANIFEST_UNVERIFIED = "PR5026_CLOSEOUT_MANIFEST_NOT_VERIFIED"
REASON_TRACE_CHAIN_INCOMPLETE = "TRACE_CHAIN_SURFACE_BINDING_INCOMPLETE"
REASON_OFFLINE_PARITY_GAP_REMAINS = "OFFLINE_CANONICAL_PARITY_GAP_REMAINS"
REASON_NARROW_REWIRE_UNEXPECTEDLY_JUSTIFIED = "NARROW_REWIRE_JUSTIFIED_UNEXPECTED_AT_CURRENT_HEAD"
REASON_GIT_CONTEXT_INVALID = "GIT_CONTEXT_NOT_MAIN_DERIVED_OR_SYNCED"


@dataclass(frozen=True)
class GitContext:
    head: str
    origin_main: str
    branch: str
    worktree_status: str
    head_equals_origin_main: bool
    main_derived_context_ok: bool
    detail: str


@dataclass(frozen=True)
class ChainBoundaryRow:
    boundary_id: str
    display_name: str
    registry_surface_id: str
    canonical_owner: str
    trace_state: str
    parity_status: str
    matrix_status: str
    offline_parity_gap: bool
    missing_contract: str
    smallest_next_slice: str


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _run(
    cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False, env=env)


def _line_context_protected(line: str) -> bool:
    lowered = line.lower()
    for marker in CONTEXT_PROTECTED_MARKERS:
        if marker in line or marker in lowered:
            return True
    for literal in FORBIDDEN_POSITIVE_CLAIM_LITERALS:
        if literal in line and ("forbidden" in lowered or "deny" in lowered or "needle" in lowered):
            return True
    return False


def scan_forbidden_positive_claims(paths: list[Path]) -> list[str]:
    """Scan only explicitly passed file paths; never discover paths recursively."""
    violations: list[str] = []
    for path in paths:
        if not path.is_file() or path.suffix != ".py":
            continue
        display = path.name
        for line_no, line in enumerate(_read_text(path).splitlines(), start=1):
            if _line_context_protected(line):
                continue
            for pattern in FORBIDDEN_POSITIVE_ASSIGNMENT_RES:
                if pattern.search(line):
                    violations.append(f"{display}:{line_no}: {line.strip()}")
    return violations


def _is_tolerated_untracked(line: str) -> bool:
    path = line[3:].strip() if line.startswith("?? ") else line.strip()
    return any(path == prefix or path.startswith(prefix) for prefix in TOLERATED_UNTRACKED_PREFIXES)


def verify_git_context(
    repo_root: Path,
    *,
    feature_branch: str = FEATURE_BRANCH,
    allow_feature_branch: bool = True,
) -> GitContext:
    """CLI/evidence-only git validation. Not used by pytest."""
    fetch = _run(["git", "fetch", "origin", "--prune"], cwd=repo_root)
    if fetch.returncode != 0:
        return GitContext("", "", "", "", False, False, f"git_fetch_failed:{fetch.stderr.strip()}")

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status_lines = [
        line
        for line in _run(["git", "status", "--short"], cwd=repo_root).stdout.splitlines()
        if line.strip() and not _is_tolerated_untracked(line.strip())
    ]
    worktree_status = "clean" if not status_lines else ";".join(status_lines)
    head_equals_origin_main = bool(head and origin_main and head == origin_main)

    if branch == feature_branch and allow_feature_branch:
        merge_base = _run(
            ["git", "merge-base", "origin/main", "HEAD"], cwd=repo_root
        ).stdout.strip()
        ok = bool(merge_base and merge_base == origin_main)
        detail = "feature_branch_derived_from_origin_main" if ok else REASON_GIT_CONTEXT_INVALID
        return GitContext(
            head=head,
            origin_main=origin_main,
            branch=branch,
            worktree_status=worktree_status,
            head_equals_origin_main=head_equals_origin_main,
            main_derived_context_ok=ok,
            detail=detail,
        )

    if branch == "main" and head_equals_origin_main and worktree_status == "clean":
        return GitContext(
            head=head,
            origin_main=origin_main,
            branch=branch,
            worktree_status=worktree_status,
            head_equals_origin_main=True,
            main_derived_context_ok=True,
            detail="origin_main_synced_clean",
        )

    return GitContext(
        head=head,
        origin_main=origin_main,
        branch=branch,
        worktree_status=worktree_status,
        head_equals_origin_main=head_equals_origin_main,
        main_derived_context_ok=False,
        detail=REASON_GIT_CONTEXT_INVALID,
    )


def verify_source_manifest(evidence_dir: Path) -> tuple[bool, int, str]:
    manifest = evidence_dir / "MANIFEST.sha256"
    if not evidence_dir.is_dir():
        return False, -1, "directory_missing"
    if not manifest.is_file():
        return False, -1, "manifest_missing"
    for row in manifest.read_text(encoding="utf-8").splitlines():
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = evidence_dir / rel
        if not target.is_file():
            return False, 1, f"missing_file:{rel}"
        if _sha256_bytes(target.read_bytes()) != digest:
            return False, 1, f"digest_mismatch:{rel}"
    return True, 0, "verified"


def _trace_surface_to_registry_ids(surface_id: str) -> tuple[str, ...]:
    mapping = {
        "bull_bear_state_switch": ("A",),
        "scope_adverse_exit_and_reversal_preparation": ("B", "C"),
        "flat_before_opposite_side": ("D",),
        "entry_position_exit_policy": ("G",),
        "capital_risk_sizing": ("H",),
        "safety_kernel_and_killswitch_boundary": ("J", "K"),
        "reconciliation_unknown_outcome": ("L",),
        "promotion_gate_boundary": ("M",),
        "ai_observability_feedback_boundary": ("N", "O"),
        "double_play_composition": ("F",),
        "survival_and_suitability": ("E",),
        "canonical_order_intent_boundary": ("I",),
    }
    return mapping.get(surface_id, ())


def evaluate_closeout_reference(
    closeout_dir: Path,
    *,
    source_manifest_verify_rc: int | None = None,
) -> tuple[int, str, list[str]]:
    """Pure closeout reference validation without full chain reassessment."""
    if source_manifest_verify_rc is None:
        verified, manifest_rc, manifest_detail = verify_source_manifest(closeout_dir)
        source_manifest_verify_rc = manifest_rc if verified else -1
    else:
        manifest_detail = "verified" if source_manifest_verify_rc == 0 else "unverified"

    fail_reasons: list[str] = []
    if not closeout_dir.is_dir():
        fail_reasons.append(REASON_PR5026_SOURCE_MISSING)
    elif source_manifest_verify_rc != 0:
        fail_reasons.append(REASON_PR5026_MANIFEST_UNVERIFIED)
    return source_manifest_verify_rc, manifest_detail, fail_reasons


def _build_chain_boundary_table(
    repo_root: Path,
    *,
    edges_by_surface: dict[str, dict[str, Any]],
    runtime: Any,
) -> list[dict[str, Any]]:
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        normalize_matrix_status_v0,
        parity_surface_assessments_v0,
    )

    registry_by_id = {item.surface_id: item for item in parity_surface_assessments_v0()}
    rows: list[ChainBoundaryRow] = []

    for surface_id in TRACE_PRIORITY:
        edge = edges_by_surface[surface_id]
        registry_ids = _trace_surface_to_registry_ids(surface_id)
        primary_registry = registry_by_id[registry_ids[0]] if registry_ids else None
        display_name = (
            primary_registry.surface_name if primary_registry else surface_id.replace("_", " ")
        )
        parity_status = primary_registry.parity_status if primary_registry else "UNKNOWN"
        matrix_status = (
            normalize_matrix_status_v0(primary_registry.parity_status)
            if primary_registry
            else "UNKNOWN"
        )
        offline_gap = matrix_status in ("GAP", "UNKNOWN") or parity_status in ("GAP", "PARTIAL")
        if surface_id == "safety_kernel_and_killswitch_boundary" and primary_registry:
            offline_gap = parity_status != "PASS"
        rows.append(
            ChainBoundaryRow(
                boundary_id=surface_id,
                display_name=display_name,
                registry_surface_id=",".join(registry_ids) if registry_ids else "NONE",
                canonical_owner=(
                    primary_registry.canonical_owner_files[0]
                    if primary_registry and primary_registry.canonical_owner_files
                    else "NONE"
                ),
                trace_state=edge["trace_state"],
                parity_status=parity_status,
                matrix_status=matrix_status,
                offline_parity_gap=offline_gap,
                missing_contract=primary_registry.missing_binding_if_any
                if primary_registry
                else "",
                smallest_next_slice=(
                    primary_registry.recommended_next_slice if primary_registry else "NONE"
                ),
            )
        )

    surface_p = registry_by_id["P"]
    rows.append(
        ChainBoundaryRow(
            boundary_id="runtime_bridge_boundary",
            display_name="Runtime Bridge boundary (BOUND_NOT_ACTIVATED)",
            registry_surface_id="P",
            canonical_owner=surface_p.canonical_owner_files[0],
            trace_state="BOUND_NOT_ACTIVATED_OFFLINE_PARITY_COMPLETE",
            parity_status=surface_p.parity_status,
            matrix_status="PARTIAL_RUNTIME_ACTIVATION_PENDING",
            offline_parity_gap=False,
            missing_contract=surface_p.missing_binding_if_any,
            smallest_next_slice=NEXT_STEP_AFTER_PASS,
        )
    )
    rows.append(
        ChainBoundaryRow(
            boundary_id="runtime_bridge_pre_activation_gate",
            display_name="Runtime Bridge pre-activation gate",
            registry_surface_id="P",
            canonical_owner="trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0",
            trace_state=runtime.runtime_bridge_pre_activation_gate_status,
            parity_status="DOCUMENTED_FAIL_CLOSED",
            matrix_status="POLICY_BLOCKED",
            offline_parity_gap=False,
            missing_contract=runtime.primary_blocker,
            smallest_next_slice=NEXT_STEP_AFTER_PASS,
        )
    )
    return [asdict(row) for row in rows]


def build_boundary_chain_reassessment(
    repo_root: Path,
    *,
    pr5026_closeout_dir: Path | None = None,
    source_manifest_verify_rc: int | None = None,
) -> dict[str, Any]:
    """Pure offline reassessment builder. No git fetch, no subprocess, no pytest."""
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_gap_records_v0,
        parity_status_counts_v0,
        render_parity_gap_matrix_json_v0,
    )
    from trading.master_v2.runtime_bridge_boundary_gap_assessment_v0 import (
        evaluate_runtime_bridge_boundary_gap_assessment_v0,
    )

    closeout_dir = pr5026_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5026_CLOSEOUT_EVIDENCE", DEFAULT_PR5026_CLOSEOUT_EVIDENCE)
    )
    source_manifest_verify_rc, manifest_detail, closeout_fail_reasons = evaluate_closeout_reference(
        closeout_dir,
        source_manifest_verify_rc=source_manifest_verify_rc,
    )
    verified = source_manifest_verify_rc == 0

    closure = build_closure_assessment(repo_root)
    inventory = build_inventory(repo_root)
    matrix = build_trace_matrix(inventory)
    edges = matrix["trace_edges"]
    edges_by_surface = {edge["surface_id"]: edge for edge in edges}
    trace_next_unbound = compute_next_unbound_node(edges)
    chain_binding_complete = compute_chain_surface_binding_complete(edges)
    gap_records = list(parity_gap_records_v0())
    gap_counts = dict(parity_status_counts_v0())
    runtime = evaluate_runtime_bridge_boundary_gap_assessment_v0(
        repo_root=repo_root,
        source_manifest_verify_rc=source_manifest_verify_rc if verified else -1,
    )
    chain_boundary_table = _build_chain_boundary_table(
        repo_root,
        edges_by_surface=edges_by_surface,
        runtime=runtime,
    )

    offline_parity_gaps = [
        row
        for row in chain_boundary_table
        if row["offline_parity_gap"] and row["boundary_id"] != "runtime_bridge_boundary"
    ]
    narrow_rewire_justified = trace_next_unbound != "NONE" or bool(gap_records)
    fail_reasons: list[str] = list(closeout_fail_reasons)
    if not chain_binding_complete:
        fail_reasons.append(REASON_TRACE_CHAIN_INCOMPLETE)
    if gap_records:
        fail_reasons.append(REASON_OFFLINE_PARITY_GAP_REMAINS)
    if narrow_rewire_justified:
        fail_reasons.append(REASON_NARROW_REWIRE_UNEXPECTEDLY_JUSTIFIED)

    boundary_chain_status = (
        "FAIL_CLOSED_DOCUMENTED"
        if (
            chain_binding_complete
            and trace_next_unbound == "NONE"
            and not gap_records
            and not narrow_rewire_justified
            and runtime.runtime_bridge_boundary_status == "BOUND_NOT_ACTIVATED"
        )
        else "OFFLINE_PARITY_GAPS_REMAIN"
        if gap_records or not chain_binding_complete or narrow_rewire_justified
        else "EVALUATION_ERROR"
    )

    if gap_records:
        next_gap_or_next_step = str(gap_records[0]["narrow_reuse_first_remediation"])
        primary_blocker = str(gap_records[0]["missing_binding"] or gap_records[0]["surface_id"])
    elif trace_next_unbound != "NONE":
        next_gap_or_next_step = trace_next_unbound
        primary_blocker = REASON_TRACE_CHAIN_INCOMPLETE
    else:
        next_gap_or_next_step = NEXT_STEP_AFTER_PASS
        primary_blocker = runtime.primary_blocker

    assessment_verdict = (
        "PASS"
        if (
            boundary_chain_status == "FAIL_CLOSED_DOCUMENTED"
            and not narrow_rewire_justified
            and source_manifest_verify_rc == 0
            and runtime.runtime_bridge_pre_activation_gate_status == "FAIL"
            and not runtime.runtime_bridge_activation_admissible
            and runtime.no_runtime_authority_confirmed
            and runtime.no_economic_claim_confirmed
        )
        else "FAIL_CLOSED"
    )

    invariant_table = {
        "FULL_CANONICAL_CHAIN_WIRED": False,
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
        "RUNTIME_REWIRE_ADMISSIBLE": False,
        "NO_RUNTIME_AUTHORITY_CONFIRMED": True,
        "NO_ECONOMIC_CLAIM_CONFIRMED": True,
        "NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE": True,
        "NARROW_REWIRE_JUSTIFIED": narrow_rewire_justified,
        "NARROW_REWIRE_ADMISSIBLE": False,
        "CLAIM_PROMOTION_ALLOWED": False,
    }

    return {
        "schema": ASSESSMENT_SCHEMA,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "assessment_verdict": assessment_verdict,
        "boundary_chain_status": boundary_chain_status,
        "plan_type": "ASSESSMENT_ONLY",
        "narrow_rewire_justified": narrow_rewire_justified,
        "trace_next_unbound_node": trace_next_unbound,
        "chain_surface_binding_complete": chain_binding_complete,
        "trace_rewire_bound_surface_count": closure["trace_rewire_bound_surface_count"],
        "gap_records_count": len(gap_records),
        "gap_status_counts": gap_counts,
        "offline_canonical_parity_gaps": offline_parity_gaps,
        "runtime_bridge_boundary_status": runtime.runtime_bridge_boundary_status,
        "runtime_bridge_pre_activation_gate_status": runtime.runtime_bridge_pre_activation_gate_status,
        "runtime_bridge_activation_admissible": runtime.runtime_bridge_activation_admissible,
        "offline_parity_complete_runtime_activation_pending": (
            runtime.offline_parity_complete_runtime_activation_pending
        ),
        "surface_p_registry_status": runtime.surface_p_registry_status,
        "surface_p_semantic_post_status": runtime.surface_p_semantic_post_status,
        "primary_blocker": primary_blocker,
        "next_gap_or_next_step": next_gap_or_next_step,
        "source_pr5026_closeout_dir": str(closeout_dir),
        "source_manifest_verify_rc": source_manifest_verify_rc,
        "source_manifest_detail": manifest_detail,
        "invariant_table": invariant_table,
        "chain_boundary_table": chain_boundary_table,
        "gap_records": gap_records,
        "trace_edges": edges,
        "parity_gap_matrix": json.loads(render_parity_gap_matrix_json_v0()),
        "fail_closed_reasons": fail_reasons,
        "reassessment_rule": (
            "Offline trace-rewire binding complete across all known parity surfaces does not "
            "authorize full-chain wiring, parity-pass, economic-evidence, or runtime-rewire claims. "
            "Surface P PARTIAL with runtime bridge BOUND_NOT_ACTIVATED is policy-documented, not "
            "an offline canonical parity gap requiring narrow rewire."
        ),
    }


def render_reassessment_markdown(assessment: dict[str, Any]) -> str:
    lines = [
        "# Full Canonical Backtest Boundary Chain Reassessment v0",
        "",
        "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE",
        "",
        "## Verdict",
        "",
        f"- assessment_verdict: {assessment['assessment_verdict']}",
        f"- boundary_chain_status: {assessment['boundary_chain_status']}",
        f"- plan_type: {assessment['plan_type']}",
        f"- narrow_rewire_justified: {str(assessment['narrow_rewire_justified']).lower()}",
        f"- trace_next_unbound_node: {assessment['trace_next_unbound_node']}",
        (
            "- chain_surface_binding_complete: "
            f"{str(assessment['chain_surface_binding_complete']).lower()}"
        ),
        f"- primary_blocker: {assessment['primary_blocker']}",
        f"- next_gap_or_next_step: {assessment['next_gap_or_next_step']}",
        "",
        "## Invariant table",
        "",
    ]
    for key, value in assessment["invariant_table"].items():
        lines.append(f"- {key}={str(value).lower()}")
    lines.extend(["", "## Chain boundary table", ""])
    for row in assessment["chain_boundary_table"]:
        lines.extend(
            [
                f"### {row['boundary_id']}",
                f"- display_name: {row['display_name']}",
                f"- trace_state: {row['trace_state']}",
                f"- parity_status: {row['parity_status']}",
                f"- matrix_status: {row['matrix_status']}",
                f"- offline_parity_gap: {str(row['offline_parity_gap']).lower()}",
                f"- missing_contract: {row['missing_contract'] or 'NONE'}",
                f"- smallest_next_slice: {row['smallest_next_slice']}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_chain_boundary_matrix_text(assessment: dict[str, Any]) -> str:
    lines = [
        "CHAIN_BOUNDARY_MATRIX",
        f"BOUNDARY_COUNT={len(assessment['chain_boundary_table'])}",
        f"TRACE_NEXT_UNBOUND_NODE={assessment['trace_next_unbound_node']}",
        (
            "CHAIN_SURFACE_BINDING_COMPLETE="
            f"{str(assessment['chain_surface_binding_complete']).lower()}"
        ),
        f"GAP_RECORDS_COUNT={assessment['gap_records_count']}",
        "",
    ]
    for row in assessment["chain_boundary_table"]:
        lines.append(
            "|".join(
                [
                    row["boundary_id"],
                    row["trace_state"],
                    row["parity_status"],
                    row["matrix_status"],
                    str(row["offline_parity_gap"]).lower(),
                    row["smallest_next_slice"],
                ]
            )
        )
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
    return 0


def collect_evidence(
    repo_root: Path,
    output_dir: Path,
    *,
    durable_archive_root: Path | None = None,
    pr5026_closeout_dir: Path | None = None,
    skip_git_check: bool = False,
) -> dict[str, Any]:
    """CLI-only evidence bundle generation. May invoke git/ruff/pytest subprocesses."""
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    git = verify_git_context(repo_root)
    if skip_git_check:
        git = GitContext(
            head=git.head,
            origin_main=git.origin_main,
            branch=git.branch,
            worktree_status=git.worktree_status,
            head_equals_origin_main=git.head_equals_origin_main,
            main_derived_context_ok=True,
            detail="git_check_skipped",
        )

    closeout_dir = pr5026_closeout_dir or Path(
        os.environ.get("PEAK_TRADE_PR5026_CLOSEOUT_EVIDENCE", DEFAULT_PR5026_CLOSEOUT_EVIDENCE)
    )
    source_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=closeout_dir)
    source_rc = source_proc.returncode if closeout_dir.is_dir() else -1
    (output_dir / "source_manifest_verify.txt").write_text(
        source_proc.stdout + source_proc.stderr + f"\nSOURCE_MANIFEST_VERIFY_RC={source_rc}\n",
        encoding="utf-8",
    )

    assessment = build_boundary_chain_reassessment(
        repo_root,
        pr5026_closeout_dir=closeout_dir,
        source_manifest_verify_rc=source_rc,
    )
    assessment["git_context"] = asdict(git)
    if not git.main_derived_context_ok:
        assessment["fail_closed_reasons"] = list(assessment["fail_closed_reasons"]) + [
            REASON_GIT_CONTEXT_INVALID
        ]

    (output_dir / "boundary_chain_reassessment_v0.json").write_text(
        json.dumps(assessment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "boundary_chain_reassessment_v0.md").write_text(
        render_reassessment_markdown(assessment),
        encoding="utf-8",
    )
    (output_dir / "chain_boundary_matrix.txt").write_text(
        render_chain_boundary_matrix_text(assessment),
        encoding="utf-8",
    )
    (output_dir / "invariant_table.txt").write_text(
        "\n".join(
            f"{key}={str(value).lower()}" for key, value in assessment["invariant_table"].items()
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={git.head}",
                f"ORIGIN_MAIN={git.origin_main}",
                f"BRANCH={git.branch}",
                f"WORKTREE_STATUS={git.worktree_status}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(git.head_equals_origin_main).lower()}",
                f"MAIN_DERIVED_CONTEXT_OK={str(git.main_derived_context_ok).lower()}",
                f"FEATURE_BRANCH={FEATURE_BRANCH}",
                f"PR5026_CLOSEOUT_DIR={closeout_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "operator_intent.env").write_text(
        "\n".join(
            [
                f"VERDICT_SCOPE={ASSESSMENT_SLICE_ID}",
                f"BASE_HEAD={git.head}",
                f"ORIGIN_MAIN_HEAD={git.origin_main}",
                f"FEATURE_BRANCH={FEATURE_BRANCH}",
                "MODE=READ_ONLY_ASSESSMENT_FIRST",
                "NO_RUNTIME_AUTHORITY=true",
                "NO_RUNTIME_EVIDENCE=true",
                "NO_ZERO_ORDER_RUNTIME_EVIDENCE=true",
                "NO_SHADOW=true",
                "NO_PAPER=true",
                "NO_TESTNET=true",
                "NO_CANARY=true",
                "NO_LIVE=true",
                "NO_ORDERS=true",
                "NO_CREDENTIALS=true",
                "NO_ARMING=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    env = {**dict(os.environ), "PYTHONPATH": f"{repo_root / 'src'}:{repo_root}"}
    pytest_proc = _run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS], cwd=repo_root, env=env
    )
    (output_dir / "targeted_pytest.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    changed_py = [repo_root / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
    ruff_targets = [str(path) for path in changed_py if path.is_file()]
    ruff_format = _run(["ruff", "format", "--check", *ruff_targets], cwd=repo_root)
    ruff_check = _run(["ruff", "check", *ruff_targets], cwd=repo_root)
    (output_dir / "ruff_format_check.txt").write_text(
        (ruff_format.stdout + ruff_format.stderr) or f"RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (output_dir / "ruff_check.txt").write_text(
        (ruff_check.stdout + ruff_check.stderr) or f"RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    py_compile_rc = 0
    py_compile_lines: list[str] = []
    for path in changed_py:
        if not path.is_file():
            continue
        proc = _run([sys.executable, "-m", "py_compile", str(path)], cwd=repo_root)
        py_compile_lines.append(f"{path.relative_to(repo_root)} RC={proc.returncode}")
        if proc.returncode != 0:
            py_compile_rc = proc.returncode
            py_compile_lines.extend([proc.stdout, proc.stderr])
    (output_dir / "py_compile.txt").write_text(
        "\n".join(py_compile_lines) + "\n",
        encoding="utf-8",
    )

    forbidden_violations = scan_forbidden_positive_claims(changed_py)
    forbidden_rc = 0 if not forbidden_violations else 1
    (output_dir / "forbidden_claims_scan.txt").write_text(
        "\n".join(
            [
                f"FORBIDDEN_CLAIMS_SCAN_RC={forbidden_rc}",
                *forbidden_violations,
                "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
                "NO_ECONOMIC_CLAIM_CONFIRMED=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    assessment_pass = assessment["assessment_verdict"] == "PASS"
    verdict = (
        f"{ASSESSMENT_SLICE_ID}_PASS"
        if tests_pass
        and ruff_pass
        and py_compile_rc == 0
        and forbidden_rc == 0
        and source_rc == 0
        and assessment_pass
        and git.main_derived_context_ok
        else f"{ASSESSMENT_SLICE_ID}_BLOCKED"
    )

    final_report = (
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"ASSESSMENT_SLICE_ID={ASSESSMENT_SLICE_ID}",
                f"BASE_SHA={git.head}",
                f"HEAD_SHA={git.head}",
                f"ORIGIN_MAIN_SHA={git.origin_main}",
                f"BRANCH={git.branch}",
                f"BOUNDARY_CHAIN_STATUS={assessment['boundary_chain_status']}",
                f"PLAN_TYPE={assessment['plan_type']}",
                f"NARROW_REWIRE_JUSTIFIED={str(assessment['narrow_rewire_justified']).lower()}",
                f"TRACE_NEXT_UNBOUND_NODE={assessment['trace_next_unbound_node']}",
                (
                    "CHAIN_SURFACE_BINDING_COMPLETE="
                    f"{str(assessment['chain_surface_binding_complete']).lower()}"
                ),
                f"GAP_RECORDS_COUNT={assessment['gap_records_count']}",
                f"RUNTIME_BRIDGE_BOUNDARY_STATUS={assessment['runtime_bridge_boundary_status']}",
                (
                    "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_STATUS="
                    f"{assessment['runtime_bridge_pre_activation_gate_status']}"
                ),
                f"PRIMARY_BLOCKER={assessment['primary_blocker']}",
                f"NEXT_GAP_OR_NEXT_STEP={assessment['next_gap_or_next_step']}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
                "NO_ECONOMIC_CLAIM_CONFIRMED=true",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"RUFF_FORMAT_RC={ruff_format.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"PY_COMPILE_RC={py_compile_rc}",
                f"FORBIDDEN_POSITIVE_CLAIMS_RC={forbidden_rc}",
                f"DURABLE_EVIDENCE_DIR={output_dir}",
            ]
        )
        + "\n"
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "final_report.txt").write_text(
        final_report + f"MANIFEST_VERIFY_RC={manifest_rc}\n",
        encoding="utf-8",
    )
    manifest_rc = write_manifest(output_dir)

    return {
        "verdict": verdict,
        "assessment": assessment,
        "evidence_dir": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "git_context": git,
        "source_manifest_verify_rc": source_rc,
        "pytest_rc": pytest_proc.returncode,
        "ruff_format_rc": ruff_format.returncode,
        "ruff_check_rc": ruff_check.returncode,
        "py_compile_rc": py_compile_rc,
        "forbidden_rc": forbidden_rc,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--durable-archive-root", default=None)
    parser.add_argument("--pr5026-closeout", default=None)
    parser.add_argument("--skip-git-check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    closeout_dir = Path(args.pr5026_closeout).resolve() if args.pr5026_closeout else None
    if archive_root and not output_dir.is_absolute():
        output_dir = archive_root / output_dir
    result = collect_evidence(
        repo_root,
        output_dir,
        durable_archive_root=archive_root,
        pr5026_closeout_dir=closeout_dir,
        skip_git_check=args.skip_git_check,
    )
    print(f"VERDICT={result['verdict']}")
    print(f"NEXT_GAP_OR_NEXT_STEP={result['assessment']['next_gap_or_next_step']}")
    print(
        "CHAIN_SURFACE_BINDING_COMPLETE="
        f"{str(result['assessment']['chain_surface_binding_complete']).lower()}"
    )
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == f"{ASSESSMENT_SLICE_ID}_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
