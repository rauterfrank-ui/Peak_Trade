from __future__ import annotations

import argparse
import hashlib
import json
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

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import (
    SURFACES,
    build_inventory,
)
from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    TRACE_PRIORITY,
    TRACE_REWIRE_BOUND_STATE,
    build_trace_matrix,
)

ASSESSMENT_ID = "FULL_CANONICAL_PARITY_CLOSURE_AFTER_ALL_SURFACES_BOUND"
SCHEMA = "FullCanonicalParityClosureAssessmentV0"

OWNER_INVENTORY = (
    "INVENTORY_OWNER=scripts/research/backtest_runtime_decision_parity_inventory_v0.py",
    "TRACE_MATRIX_OWNER=scripts/research/backtest_runtime_decision_parity_trace_matrix_v0.py",
    "CLOSURE_ASSESSMENT_OWNER=scripts/research/full_canonical_parity_closure_assessment_v0.py",
    "HARNESS_OWNER=src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "DECISION=read_only_closure_assessment_no_rewire_no_new_ssot",
)

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
)

CONTEXT_PROTECTED_MARKERS = (
    "forbidden_claims",
    "forbidden_claims_remain_false",
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
    "scripts/research/backtest_runtime_decision_parity_trace_matrix_v0.py",
    "scripts/research/full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_backtest_runtime_decision_parity_trace_matrix_v0.py",
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_adverse_scope_exit_reversal_preparation_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_flat_before_opposite_side_narrow_reuse_first_rewire_v0.py",
)

TARGETED_TESTS = (
    "tests/research/test_full_canonical_parity_closure_assessment_v0.py",
    "tests/research/test_backtest_runtime_decision_parity_inventory_v0.py",
    "tests/research/test_backtest_runtime_decision_parity_trace_matrix_v0.py",
    "tests/research/test_bull_bear_state_switch_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_scope_adverse_exit_and_reversal_preparation_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_adverse_scope_exit_reversal_preparation_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_flat_before_opposite_side_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_entry_position_exit_policy_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_capital_risk_sizing_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_promotion_gate_boundary_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_double_play_composition_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_survival_suitability_narrow_reuse_first_rewire_v0.py",
    "tests/research/test_canonical_order_intent_boundary_narrow_reuse_first_rewire_v0.py",
)


@dataclass(frozen=True)
class ClosureAssessment:
    schema: str
    assessment: str
    chain_surface_binding_complete: bool
    known_unbound_parity_node: str
    next_unbound_node: str
    parity_pass_claim_deferred: bool
    trace_rewire_bound_surface_count: int
    inventory_surface_count: int
    trace_edge_count: int
    no_runtime_authority: bool
    no_order_authority: bool
    no_economic_evidence: bool
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    runtime_authority: bool
    orders_allowed: bool
    economic_claim: bool
    full_canonical_chain_wired_claimed: bool
    backtest_runtime_decision_parity_pass_claimed: bool
    trace_edges: list[dict[str, Any]]
    surface_ids: list[str]


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


def scan_forbidden_positive_claims(repo_root: Path, changed_files: list[str]) -> list[str]:
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


def build_closure_assessment(repo_root: Path) -> dict[str, Any]:
    inventory = build_inventory(repo_root)
    matrix = build_trace_matrix(inventory)
    edges = matrix["trace_edges"]
    bound_count = sum(1 for edge in edges if edge["trace_state"] == TRACE_REWIRE_BOUND_STATE)
    chain_complete = bool(matrix["chain_surface_binding_complete"])
    next_unbound = str(matrix["next_unbound_node"])

    assessment = ClosureAssessment(
        schema=SCHEMA,
        assessment=ASSESSMENT_ID,
        chain_surface_binding_complete=chain_complete,
        known_unbound_parity_node=next_unbound,
        next_unbound_node=next_unbound,
        parity_pass_claim_deferred=True,
        trace_rewire_bound_surface_count=bound_count,
        inventory_surface_count=int(inventory["inventory_surface_count"]),
        trace_edge_count=int(matrix["trace_edge_count"]),
        no_runtime_authority=True,
        no_order_authority=True,
        no_economic_evidence=True,
        full_canonical_chain_wired=False,
        backtest_runtime_decision_parity_pass=False,
        system_economic_evidence_admissible=False,
        runtime_rewire_admissible=False,
        runtime_authority=False,
        orders_allowed=False,
        economic_claim=False,
        full_canonical_chain_wired_claimed=False,
        backtest_runtime_decision_parity_pass_claimed=False,
        trace_edges=edges,
        surface_ids=list(TRACE_PRIORITY),
    )
    payload = asdict(assessment)
    payload["source_inventory_schema"] = inventory["schema"]
    payload["source_trace_matrix_schema"] = matrix["schema"]
    payload["configured_surface_ids"] = [surface["surface_id"] for surface in SURFACES]
    payload["forbidden_positive_claim_literals"] = list(FORBIDDEN_POSITIVE_CLAIM_LITERALS)
    payload["closure_rule"] = (
        "Trace-rewire binding on all known parity surfaces does not authorize full-chain, "
        "parity-pass, economic-evidence, or runtime-rewire claims."
    )
    return payload


def render_closure_markdown(assessment: dict[str, Any]) -> str:
    lines = [
        "# Full Canonical Parity Closure Assessment V0",
        "",
        "```text",
        f"ASSESSMENT={assessment['assessment']}",
        f"CHAIN_SURFACE_BINDING_COMPLETE={str(assessment['chain_surface_binding_complete']).lower()}",
        f"KNOWN_UNBOUND_PARITY_NODE={assessment['known_unbound_parity_node']}",
        f"NEXT_UNBOUND_NODE={assessment['next_unbound_node']}",
        f"PARITY_PASS_CLAIM_DEFERRED={str(assessment['parity_pass_claim_deferred']).lower()}",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDER_AUTHORITY=true",
        "NO_ECONOMIC_EVIDENCE=true",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "```",
        "",
        "## Trace chain",
        "",
    ]
    for edge in assessment["trace_edges"]:
        lines.extend(
            [
                f"### {edge['surface_id']}",
                f"- trace_state: `{edge['trace_state']}`",
                f"- next_action: `{edge['next_action']}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def render_chain_surface_matrix_text(assessment: dict[str, Any]) -> str:
    lines = [
        "CHAIN_SURFACE_MATRIX",
        f"SURFACE_COUNT={assessment['inventory_surface_count']}",
        f"TRACE_EDGE_COUNT={assessment['trace_edge_count']}",
        f"TRACE_REWIRE_BOUND_SURFACE_COUNT={assessment['trace_rewire_bound_surface_count']}",
        f"CHAIN_SURFACE_BINDING_COMPLETE={str(assessment['chain_surface_binding_complete']).lower()}",
        f"NEXT_UNBOUND_NODE={assessment['next_unbound_node']}",
        "",
    ]
    for edge in assessment["trace_edges"]:
        lines.append(f"{edge['surface_id']}|{edge['trace_state']}|{edge['next_action']}")
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
    verify_path = output_dir / "MANIFEST.verify.txt"
    verify_path.write_text(f"RC=0\nFILES={len(rows)}\n", encoding="utf-8")
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
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    archive_root = durable_archive_root or Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
    )
    evidence_dir = output_dir or (
        archive_root
        / f"research/full_canonical_parity_closure_assessment_after_all_surfaces_bound_v0_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=repo_root).stdout.strip()
    branch = _run(["git", "branch", "--show-current"], cwd=repo_root).stdout.strip()
    status = _run(["git", "status", "--short"], cwd=repo_root).stdout.strip()

    git_context = (
        "\n".join(
            [
                f"REPO={repo_root}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BRANCH={branch}",
                f"WORKTREE_STATUS={status or 'clean'}",
            ]
        )
        + "\n"
    )
    (evidence_dir / "git_context.txt").write_text(git_context, encoding="utf-8")

    assessment = build_closure_assessment(repo_root)
    (evidence_dir / "closure_assessment.json").write_text(
        json.dumps(assessment, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "closure_assessment.txt").write_text(
        render_closure_markdown(assessment),
        encoding="utf-8",
    )
    (evidence_dir / "chain_surface_matrix.txt").write_text(
        render_chain_surface_matrix_text(assessment),
        encoding="utf-8",
    )
    (evidence_dir / "chain_surface_matrix.json").write_text(
        json.dumps(
            {
                "schema": "FullCanonicalParityChainSurfaceMatrixV0",
                "trace_edges": assessment["trace_edges"],
                "next_unbound_node": assessment["next_unbound_node"],
                "chain_surface_binding_complete": assessment["chain_surface_binding_complete"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    owner_lines = list(OWNER_INVENTORY)
    for surface_id in assessment["surface_ids"]:
        owner_lines.append(f"SURFACE={surface_id}|trace_state={TRACE_REWIRE_BOUND_STATE}")
    (evidence_dir / "owner_inventory.txt").write_text(
        "\n".join(owner_lines) + "\n", encoding="utf-8"
    )

    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(repo_root / "src")}
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

    forbidden_violations = scan_forbidden_positive_claims(repo_root, list(SLICE_CHANGED_FILES))
    forbidden_ok = not forbidden_violations
    (evidence_dir / "forbidden_claims_scan.txt").write_text(
        "\n".join(
            [
                f"FORBIDDEN_POSITIVE_CLAIMS_SCAN_OK={str(forbidden_ok).lower()}",
                f"VIOLATION_COUNT={len(forbidden_violations)}",
                *forbidden_violations,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc = write_manifest(evidence_dir)
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    assessment_pass = (
        assessment["chain_surface_binding_complete"]
        and assessment["next_unbound_node"] == "NONE"
        and assessment["parity_pass_claim_deferred"] is True
        and assessment["full_canonical_chain_wired"] is False
        and assessment["backtest_runtime_decision_parity_pass"] is False
    )
    verdict = (
        "PASS"
        if tests_pass
        and ruff_pass
        and py_compile_rc == 0
        and forbidden_ok
        and manifest_rc == 0
        and assessment_pass
        else "BLOCKED"
    )

    final_report = (
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"ASSESSMENT={ASSESSMENT_ID}",
                f"CHAIN_SURFACE_BINDING_COMPLETE={str(assessment['chain_surface_binding_complete']).lower()}",
                f"KNOWN_UNBOUND_PARITY_NODE={assessment['known_unbound_parity_node']}",
                f"NEXT_UNBOUND_NODE={assessment['next_unbound_node']}",
                f"PARITY_PASS_CLAIM_DEFERRED={str(assessment['parity_pass_claim_deferred']).lower()}",
                "NO_RUNTIME_AUTHORITY=true",
                "NO_ORDER_AUTHORITY=true",
                "NO_ECONOMIC_EVIDENCE=true",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"RUFF_FORMAT_RC={ruff_format.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"PY_COMPILE_RC={py_compile_rc}",
                f"FORBIDDEN_CLAIMS_SCAN_OK={str(forbidden_ok).lower()}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n"
    )
    (evidence_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    manifest_rc = write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "assessment": assessment,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "forbidden_ok": forbidden_ok,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--durable-archive-root", default=None)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    archive_root = Path(args.durable_archive_root).resolve() if args.durable_archive_root else None
    result = collect_evidence(repo_root, output_dir=output_dir, durable_archive_root=archive_root)
    print(f"VERDICT={result['verdict']}")
    print(f"NEXT_UNBOUND_NODE={result['assessment']['next_unbound_node']}")
    print(
        "CHAIN_SURFACE_BINDING_COMPLETE="
        f"{str(result['assessment']['chain_surface_binding_complete']).lower()}"
    )
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
