#!/usr/bin/env python3
"""Collect durable evidence for Runtime Bridge Pre-Activation Gate Assessment v0."""

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
DEFAULT_PR5024_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/merge_closeout_pr5024_next_full_canonical_parity_surface_after_pr5023_v0_20260708T233946Z"
)

VERDICT = "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_assessment_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",
    "tests/trading/master_v2/test_next_full_canonical_parity_surface_after_surface_p_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/runtime_bridge_pre_activation_gate_assessment_v0.py",
    "scripts/ops/run_runtime_bridge_pre_activation_gate_assessment_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_assessment_contract_v0.py",
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
    from trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0 import (
        scan_forbidden_positive_claims,
    )

    violations = scan_forbidden_positive_claims(REPO_ROOT, changed_files)
    return (0 if not violations else 1, violations)


def collect_evidence(
    out_dir: Path | None = None,
    *,
    pr5024_closeout_dir: Path | None = None,
) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/runtime_bridge_pre_activation_gate_assessment_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    closeout_dir = pr5024_closeout_dir or DEFAULT_PR5024_CLOSEOUT

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()
    changed = _run(["git", "diff", "--name-only", "origin/main...HEAD"]).stdout.strip()

    (evidence_dir / "operator_intent.env").write_text(
        "\n".join(
            [
                "VERDICT_SCOPE=RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0",
                f"BASE_HEAD={head}",
                f"ORIGIN_MAIN_HEAD={origin_main}",
                "FEATURE_BRANCH=core-system-completion-runtime-bridge-pre-activation-gate-assessment-v0",
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
    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"WORKTREE_STATUS={worktree or 'clean'}",
                "ASSESSMENT_SLICE_ID=RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0",
                f"PR5024_CLOSEOUT_PATH={closeout_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        (changed + "\n") if changed else "(no committed diff vs origin/main yet)\n",
        encoding="utf-8",
    )

    source_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=closeout_dir)
    source_rc = source_proc.returncode
    (evidence_dir / "source_manifest_verify.txt").write_text(
        source_proc.stdout + source_proc.stderr + f"\nSOURCE_MANIFEST_VERIFY_RC={source_rc}\n",
        encoding="utf-8",
    )

    from trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0 import (
        evaluate_runtime_bridge_pre_activation_gate_assessment_v0,
        render_runtime_bridge_pre_activation_gate_matrix_json_v0,
        render_runtime_bridge_pre_activation_gate_report_markdown_v0,
        runtime_bridge_pre_activation_gate_assessment_to_dict_v0,
    )

    assessment = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=closeout_dir,
        source_manifest_verify_rc=source_rc,
    )
    (evidence_dir / "runtime_bridge_pre_activation_gate_matrix.json").write_text(
        render_runtime_bridge_pre_activation_gate_matrix_json_v0(
            pr5024_closeout_dir=closeout_dir,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "runtime_bridge_pre_activation_gate_assessment_v0.md").write_text(
        render_runtime_bridge_pre_activation_gate_report_markdown_v0(
            pr5024_closeout_dir=closeout_dir,
        ),
        encoding="utf-8",
    )
    (evidence_dir / "assessment_result.json").write_text(
        json.dumps(
            runtime_bridge_pre_activation_gate_assessment_to_dict_v0(assessment),
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
        or assessment.assessment_verdict != "PASS"
        or assessment.runtime_bridge_activation_admissible
        or assessment.runtime_bridge_pre_activation_gate_status != "FAIL"
        or assessment.full_canonical_chain_wired
        or assessment.backtest_runtime_decision_parity_pass
        or assessment.system_economic_evidence_admissible
        or assessment.runtime_rewire_admissible
        or assessment.claim_promotion_allowed
    )
    verdict = VERDICT if not blocked else "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0_BLOCKED"

    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"BASE_HEAD={head}",
                f"POST_BRANCH_HEAD={head}",
                "BRANCH_NAME=core-system-completion-runtime-bridge-pre-activation-gate-assessment-v0",
                f"GATE_ASSESSMENT_STATUS={assessment.gate_assessment_status}",
                (
                    "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_STATUS="
                    f"{assessment.runtime_bridge_pre_activation_gate_status}"
                ),
                (
                    "RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE="
                    f"{str(assessment.runtime_bridge_activation_admissible).lower()}"
                ),
                f"PRIMARY_BLOCKER={assessment.primary_blocker}",
                f"SURFACE_P_REGISTRY_STATUS={assessment.surface_p_registry_status}",
                f"SURFACE_P_SEMANTIC_POST_STATUS={assessment.surface_p_semantic_post_status}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
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
                (
                    "NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE="
                    f"{str(assessment.no_runtime_evidence_before_core_system_complete).lower()}"
                ),
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"NEXT_STEP_AFTER_PR={assessment.next_step_after_pr}",
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
        "ruff_rc": ruff_check.returncode,
        "ruff_format_rc": ruff_format.returncode,
        "py_compile_rc": compile_rc,
        "forbidden_rc": forbidden_rc,
        "assessment": assessment,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--pr5024-closeout", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out, pr5024_closeout_dir=args.pr5024_closeout)
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
