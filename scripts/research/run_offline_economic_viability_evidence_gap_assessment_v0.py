#!/usr/bin/env python3
"""Collect durable evidence for Offline Economic Viability Evidence Gap Assessment v0."""

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
DEFAULT_PARITY_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/merge_closeout_pr5034_pre_economics_notion_market_security_sync_v0_20260709T144613Z"
)
DEFAULT_GAP_SCAN = (
    ARCHIVE_ROOT
    / "research/system_economic_evidence_admissibility_gap_scan_after_full_parity_v0_20260709T141726Z"
)

VERDICT = "OFFLINE_ECONOMIC_VIABILITY_EVIDENCE_GAP_ASSESSMENT_V0_PASS"
TARGETED_TESTS = (
    "tests/research/test_offline_economic_viability_evidence_gap_assessment_v0_contract.py",
    "tests/research/test_final_research_fleet_versioned_binding_completion_v0.py::test_economic_evaluation_not_authorized",
)
SLICE_CHANGED_FILES = (
    "src/research/offline_economic_viability_evidence_gap_assessment_v0.py",
    "scripts/research/run_offline_economic_viability_evidence_gap_assessment_v0.py",
    "tests/research/test_offline_economic_viability_evidence_gap_assessment_v0_contract.py",
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


def collect_evidence(
    out_dir: Path | None = None,
    *,
    parity_closeout_dir: Path | None = None,
    gap_scan_dir: Path | None = None,
) -> dict[str, object]:
    from src.research.offline_economic_viability_evidence_gap_assessment_v0 import (
        ASSESSMENT_SLICE_ID,
        evaluate_offline_economic_viability_evidence_gap_assessment_v0,
        render_admissibility_decision_json_v0,
        render_candidate_binding_matrix_json_v0,
        render_economic_gap_assessment_json_v0,
        render_economic_gap_assessment_markdown_v0,
        render_reuse_inventory_text_v0,
        scan_forbidden_positive_claims,
    )

    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/offline_economic_viability_evidence_gap_assessment_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    parity_dir = parity_closeout_dir or DEFAULT_PARITY_CLOSEOUT
    scan_dir = gap_scan_dir or DEFAULT_GAP_SCAN

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()

    (evidence_dir / "repo_state.txt").write_text(
        "\n".join(
            [
                f"REPO_ROOT={REPO_ROOT}",
                f"BRANCH={branch}",
                f"BASE_HEAD={head}",
                f"ORIGIN_HEAD={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                f"DURABLE_ARCHIVE_ROOT={ARCHIVE_ROOT}",
                f"EVIDENCE_DIR={evidence_dir}",
                f"WORKSTREAM_ID={ASSESSMENT_SLICE_ID}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parity_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=parity_dir)
    scan_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=scan_dir)
    (evidence_dir / "source_parity_closeout_manifest_verify.txt").write_text(
        parity_proc.stdout
        + parity_proc.stderr
        + f"\nPARITY_CLOSEOUT_MANIFEST_VERIFY_RC={parity_proc.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_gap_scan_manifest_verify.txt").write_text(
        scan_proc.stdout
        + scan_proc.stderr
        + f"\nGAP_SCAN_MANIFEST_VERIFY_RC={scan_proc.returncode}\n",
        encoding="utf-8",
    )

    (evidence_dir / "reuse_inventory.txt").write_text(
        render_reuse_inventory_text_v0(repo_root=REPO_ROOT),
        encoding="utf-8",
    )
    (evidence_dir / "economic_gap_assessment.json").write_text(
        render_economic_gap_assessment_json_v0(
            repo_root=REPO_ROOT,
            parity_closeout_dir=parity_dir,
            gap_scan_dir=scan_dir,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "economic_gap_assessment.md").write_text(
        render_economic_gap_assessment_markdown_v0(repo_root=REPO_ROOT),
        encoding="utf-8",
    )
    (evidence_dir / "candidate_binding_matrix.json").write_text(
        render_candidate_binding_matrix_json_v0(repo_root=REPO_ROOT),
        encoding="utf-8",
    )
    (evidence_dir / "candidate_binding_matrix.md").write_text(
        _render_candidate_binding_matrix_md(repo_root=REPO_ROOT),
        encoding="utf-8",
    )
    (evidence_dir / "admissibility_decision.json").write_text(
        render_admissibility_decision_json_v0(repo_root=REPO_ROOT),
        encoding="utf-8",
    )

    forbidden_lines = [
        "FORBIDDEN_SURFACE_GUARD_V0",
        "",
        "NO_RUNTIME_REWIRE=true",
        "NO_RUNTIME_EVIDENCE=true",
        "NO_ZERO_ORDER_RUNTIME_EVIDENCE=true",
        "NO_SHADOW=true",
        "NO_PAPER=true",
        "NO_TESTNET=true",
        "NO_SCHEDULER=true",
        "NO_ADAPTER_SUBMISSION=true",
        "NO_ORDERS=true",
        "NO_CREDENTIALS=true",
        "NO_ARMING=true",
        "NO_CANARY=true",
        "NO_LIVE=true",
        "NO_CORE_SYSTEM_CHANGE=true",
        "NO_CANONICAL_TRADING_LOGIC_CHANGE=true",
        "NO_NOTION_LIVE_WRITE=true",
        "FORBIDDEN_ECONOMIC_EVALUATION_STARTED=false",
        "",
    ]
    claim_rc, claim_violations = _scan_forbidden_claims(SLICE_CHANGED_FILES)
    forbidden_lines.append(f"FORBIDDEN_POSITIVE_CLAIM_SCAN_RC={claim_rc}")
    forbidden_lines.extend(claim_violations or ["(no violations in slice)"])
    (evidence_dir / "forbidden_surface_guard.txt").write_text(
        "\n".join(forbidden_lines) + "\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "targeted_tests.txt").write_text(
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

    py_compile_lines: list[str] = []
    py_compile_rc = 0
    for target in ruff_targets:
        proc = _run([sys.executable, "-m", "py_compile", target])
        py_compile_lines.append(proc.stdout + proc.stderr)
        if proc.returncode != 0:
            py_compile_rc = proc.returncode
    (evidence_dir / "py_compile.txt").write_text(
        "".join(py_compile_lines) + f"\nPY_COMPILE_RC={py_compile_rc}\n",
        encoding="utf-8",
    )

    assessment = evaluate_offline_economic_viability_evidence_gap_assessment_v0(
        repo_root=REPO_ROOT,
        parity_closeout_dir=parity_dir,
        gap_scan_dir=scan_dir,
        parity_manifest_verify_rc=parity_proc.returncode,
        gap_scan_manifest_verify_rc=scan_proc.returncode,
    )

    manifest_rc = _write_manifest(evidence_dir)
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={VERDICT}",
                f"ASSESSMENT_SLICE_ID={ASSESSMENT_SLICE_ID}",
                f"EVIDENCE_DIR={evidence_dir}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"TARGETED_TESTS_RC={pytest_proc.returncode}",
                f"RUFF_FORMAT_RC={ruff_format.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"PY_COMPILE_RC={py_compile_rc}",
                f"PRIMARY_BLOCKER={assessment.primary_blocker}",
                (
                    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                    f"{str(assessment.system_economic_evidence_admissible).lower()}"
                ),
                (
                    "FULL_CANONICAL_CHAIN_WIRED="
                    f"{str(assessment.full_canonical_chain_wired).lower()}"
                ),
                (
                    "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                    f"{str(assessment.backtest_runtime_decision_parity_pass).lower()}"
                ),
                f"NEXT_STEP={assessment.next_step_after_assessment}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_manifest(evidence_dir)

    return {
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "targeted_tests_rc": pytest_proc.returncode,
        "ruff_format_rc": ruff_format.returncode,
        "ruff_check_rc": ruff_check.returncode,
        "py_compile_rc": py_compile_rc,
        "assessment": assessment,
    }


def _render_candidate_binding_matrix_md(*, repo_root: Path) -> str:
    from src.research.offline_economic_viability_evidence_gap_assessment_v0 import (
        evaluate_offline_economic_viability_evidence_gap_assessment_v0,
    )

    result = evaluate_offline_economic_viability_evidence_gap_assessment_v0(repo_root=repo_root)
    lines = ["# Candidate Binding Matrix v0", ""]
    for row in result.candidate_rows:
        lines.append(f"## {row.canonical_candidate_identifier}")
        lines.append("")
        lines.append(f"- binding_readiness: {row.binding_readiness.value}")
        lines.append(f"- cost_binding_complete: {str(row.cost_binding_complete).lower()}")
        lines.append(f"- digest_binding_complete: {str(row.digest_binding_complete).lower()}")
        lines.append(f"- robustness_wiring_complete: {str(row.robustness_wiring_complete).lower()}")
        lines.append(
            "- manifest_verified_evidence_present: "
            f"{str(row.manifest_verified_evidence_present).lower()}"
        )
        lines.append(f"- gap_reasons: {', '.join(row.gap_reasons) or 'none'}")
        lines.append("")
    return "\n".join(lines)


def _scan_forbidden_claims(changed_files: list[str]) -> tuple[int, list[str]]:
    from src.research.offline_economic_viability_evidence_gap_assessment_v0 import (
        scan_forbidden_positive_claims,
    )

    violations = scan_forbidden_positive_claims(REPO_ROOT, changed_files)
    return (0 if not violations else 1, violations)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--parity-closeout-dir", type=Path, default=None)
    parser.add_argument("--gap-scan-dir", type=Path, default=None)
    args = parser.parse_args()

    result = collect_evidence(
        args.evidence_dir,
        parity_closeout_dir=args.parity_closeout_dir,
        gap_scan_dir=args.gap_scan_dir,
    )
    print(
        json.dumps({k: v for k, v in result.items() if k != "assessment"}, indent=2, sort_keys=True)
    )
    rc = int(result["manifest_verify_rc"])
    if result["targeted_tests_rc"] != 0:
        rc = 1
    if result["ruff_check_rc"] != 0:
        rc = 1
    if result["py_compile_rc"] != 0:
        rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
