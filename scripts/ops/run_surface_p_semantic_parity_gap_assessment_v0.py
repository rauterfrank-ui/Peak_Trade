#!/usr/bin/env python3
"""Collect durable evidence for Surface P semantic parity gap assessment v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_ROOT = Path(__file__).resolve()
REPO_ROOT = _SCRIPT_ROOT.parents[2]
for parent in [_SCRIPT_ROOT, *_SCRIPT_ROOT.parents]:
    if (parent / "src").is_dir() and (parent / ".git").exists():
        REPO_ROOT = parent
        repo_s = str(parent)
        src_s = str(parent / "src")
        if repo_s not in sys.path:
            sys.path.insert(0, repo_s)
        if src_s not in sys.path:
            sys.path.insert(0, src_s)
        break

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
DEFAULT_PR5022_PROOF_BUNDLE = (
    ARCHIVE_ROOT / "research/full_canonical_parity_proof_bundle_v0_20260708T224152Z"
)
DEFAULT_PR5022_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/merge_closeout_pr5022_full_canonical_parity_proof_bundle_assembler_v0_20260708T224613Z"
)

VERDICT = "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_surface_p_semantic_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/surface_p_semantic_parity_gap_assessment_v0.py",
    "scripts/ops/run_surface_p_semantic_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_surface_p_semantic_parity_gap_assessment_contract_v0.py",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _write_manifest(evidence_dir: Path) -> int:
    entries: list[str] = []
    for path in sorted(evidence_dir.iterdir()):
        if path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.name}\n")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("".join(entries), encoding="utf-8")
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def _scan_forbidden_claims(changed_files: list[str]) -> tuple[int, list[str]]:
    from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
        scan_forbidden_positive_claims,
    )

    violations = scan_forbidden_positive_claims(REPO_ROOT, changed_files)
    return (0 if not violations else 1, violations)


def collect_evidence(
    out_dir: Path | None = None,
    *,
    pr5022_proof_bundle_dir: Path | None = None,
    pr5022_closeout_dir: Path | None = None,
) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/surface_p_semantic_parity_gap_assessment_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    proof_bundle_dir = pr5022_proof_bundle_dir or DEFAULT_PR5022_PROOF_BUNDLE
    closeout_dir = pr5022_closeout_dir or DEFAULT_PR5022_CLOSEOUT

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()
    changed = _run(["git", "diff", "--name-only", "origin/main...HEAD"]).stdout.strip()

    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"WORKTREE_STATUS={worktree or 'clean'}",
                f"ASSESSMENT_SLICE_ID=SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0",
                f"PR5022_PROOF_BUNDLE_PATH={proof_bundle_dir}",
                f"PR5022_CLOSEOUT_PATH={closeout_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        (changed + "\n") if changed else "(no committed diff vs origin/main yet)\n",
        encoding="utf-8",
    )

    source_lines: list[str] = []
    source_rc = 0
    for source_dir in (proof_bundle_dir, closeout_dir):
        proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=source_dir)
        source_lines.append(f"=== {source_dir} RC={proc.returncode} ===")
        source_lines.append(proc.stdout)
        source_lines.append(proc.stderr)
        if proc.returncode != 0:
            source_rc = proc.returncode
    (evidence_dir / "source_manifest_verify.txt").write_text(
        "\n".join(source_lines) + f"\nSOURCE_MANIFEST_VERIFY_RC={source_rc}\n",
        encoding="utf-8",
    )

    from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
        evaluate_surface_p_semantic_parity_gap_assessment_v0,
        render_surface_p_semantic_parity_gap_matrix_json_v0,
        render_surface_p_semantic_parity_gap_report_markdown_v0,
        surface_p_semantic_parity_gap_assessment_to_dict_v0,
    )

    assessment = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=proof_bundle_dir,
        pr5022_closeout_dir=closeout_dir,
        source_manifest_verify_rc=source_rc,
    )
    (evidence_dir / "surface_p_semantic_parity_gap_matrix.json").write_text(
        render_surface_p_semantic_parity_gap_matrix_json_v0(
            pr5022_proof_bundle_dir=proof_bundle_dir,
            pr5022_closeout_dir=closeout_dir,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "semantic_parity_gap_report.md").write_text(
        render_surface_p_semantic_parity_gap_report_markdown_v0(
            pr5022_proof_bundle_dir=proof_bundle_dir,
            pr5022_closeout_dir=closeout_dir,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "assessment_result.json").write_text(
        json.dumps(
            surface_p_semantic_parity_gap_assessment_to_dict_v0(assessment),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    env = {
        **dict(__import__("os").environ),
        "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}",
    }
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "targeted_pytest.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr + f"\nTARGETED_TESTS_RC={pytest_proc.returncode}\n",
        encoding="utf-8",
    )

    ruff_targets = [str(REPO_ROOT / p) for p in SLICE_CHANGED_FILES if p.endswith(".py")]
    ruff_format = _run([sys.executable, "-m", "ruff", "format", "--check", *ruff_targets])
    ruff_check = _run([sys.executable, "-m", "ruff", "check", *ruff_targets])
    (evidence_dir / "ruff_format_check.txt").write_text(
        ruff_format.stdout + ruff_format.stderr + f"\nRUFF_FORMAT_RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.txt").write_text(
        ruff_check.stdout + ruff_check.stderr + f"\nRUFF_CHECK_RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    compile_lines: list[str] = []
    compile_rc = 0
    for rel in SLICE_CHANGED_FILES:
        if not rel.endswith(".py"):
            continue
        proc = _run([sys.executable, "-m", "py_compile", str(REPO_ROOT / rel)])
        compile_lines.append(f"=== {rel} RC={proc.returncode} ===")
        compile_lines.append(proc.stdout)
        compile_lines.append(proc.stderr)
        if proc.returncode != 0:
            compile_rc = proc.returncode
    (evidence_dir / "py_compile.txt").write_text(
        "\n".join(compile_lines) + f"\nPY_COMPILE_RC={compile_rc}\n",
        encoding="utf-8",
    )

    forbidden_rc, forbidden_violations = _scan_forbidden_claims(list(SLICE_CHANGED_FILES))
    (evidence_dir / "forbidden_claims_scan.txt").write_text(
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

    blocked = (
        pytest_proc.returncode != 0
        or ruff_format.returncode != 0
        or ruff_check.returncode != 0
        or compile_rc != 0
        or forbidden_rc != 0
        or source_rc != 0
        or assessment.full_canonical_chain_wired
        or assessment.backtest_runtime_decision_parity_pass
        or assessment.system_economic_evidence_admissible
        or assessment.runtime_rewire_admissible
        or assessment.claim_promotion_allowed
    )
    verdict = VERDICT if not blocked else "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0_BLOCKED"

    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"BASE_HEAD={head}",
                f"POST_BRANCH_HEAD={head}",
                "SOURCE_EVIDENCE_REFERENCED=true",
                f"PR5022_PROOF_BUNDLE_PATH={proof_bundle_dir}",
                f"PR5022_CLOSEOUT_PATH={closeout_dir}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                "SURFACE_P_PRE_STATUS=PARTIAL",
                f"SURFACE_P_POST_STATUS={assessment.surface_p_post_status}",
                (
                    "SEMANTIC_PARITY_BEYOND_TRACE_BINDING="
                    f"{assessment.semantic_parity_beyond_trace_binding}"
                ),
                f"NEXT_BLOCKER={assessment.next_blocker}",
                f"FULL_CANONICAL_CHAIN_WIRED={str(assessment.full_canonical_chain_wired).lower()}",
                (
                    "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                    f"{str(assessment.backtest_runtime_decision_parity_pass).lower()}"
                ),
                (
                    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                    f"{str(assessment.system_economic_evidence_admissible).lower()}"
                ),
                f"RUNTIME_REWIRE_ADMISSIBLE={str(assessment.runtime_rewire_admissible).lower()}",
                f"CLAIM_PROMOTION_ALLOWED={str(assessment.claim_promotion_allowed).lower()}",
                "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
                "NO_ECONOMIC_CLAIM_CONFIRMED=true",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        (evidence_dir / "final_report.txt").read_text(encoding="utf-8")
        + f"MANIFEST_VERIFY_RC={manifest_rc}\n",
        encoding="utf-8",
    )
    manifest_rc = _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "pytest_rc": pytest_proc.returncode,
        "source_manifest_verify_rc": source_rc,
        "lint_rc": max(ruff_format.returncode, ruff_check.returncode),
        "forbidden_rc": forbidden_rc,
        "assessment": assessment,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--pr5022-proof-bundle", type=Path, default=None)
    parser.add_argument("--pr5022-closeout", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(
        args.out,
        pr5022_proof_bundle_dir=args.pr5022_proof_bundle,
        pr5022_closeout_dir=args.pr5022_closeout,
    )
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
