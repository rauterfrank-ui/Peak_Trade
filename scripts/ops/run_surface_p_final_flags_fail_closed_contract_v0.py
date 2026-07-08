#!/usr/bin/env python3
"""Collect durable evidence for Surface P final flags fail-closed contract v0."""

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
SOURCE_EVIDENCE_DIRS = (
    ARCHIVE_ROOT / "research/pr4984_runbook_compliant_merge_closeout_v0_20260707T235544Z",
    ARCHIVE_ROOT
    / "research/full_canonical_system_backtest_parity_gap_assessment_after_pr4984_v0_20260707T235724Z",
    ARCHIVE_ROOT
    / "research/surface_p_semantic_parity_gap_verification_after_pr4984_v0_20260707T235857Z",
    ARCHIVE_ROOT
    / "research/final_flags_fail_closed_contract_proposal_after_pr4984_v0_20260708T000035Z",
)
VERDICT = "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/surface_p_final_flags_fail_closed_contract_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "src/trading/master_v2/runtime_bridge_pre_activation_gate_v0.py",
    "scripts/ops/run_surface_p_final_flags_fail_closed_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_final_flags_fail_closed_contract_v0.py",
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


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/surface_p_final_flags_fail_closed_contract_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    worktree = _run(["git", "status", "--short"]).stdout.strip()
    changed = _run(["git", "diff", "--name-only", "origin/main...HEAD"]).stdout.strip()

    preflight_lines = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"WORKTREE_STATUS={worktree or 'clean'}",
        f"CONTRACT_SLICE_ID=SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0",
        f"DIRECT_TRUE_FLAG_ASSIGNMENT=false",
        f"RUNTIME_ACTIVATION=false",
    ]
    (evidence_dir / "preflight.txt").write_text("\n".join(preflight_lines) + "\n", encoding="utf-8")
    (evidence_dir / "changed_files.txt").write_text(
        (changed + "\n") if changed else "(no committed diff vs origin/main yet)\n",
        encoding="utf-8",
    )

    source_lines: list[str] = []
    source_rc = 0
    for source_dir in SOURCE_EVIDENCE_DIRS:
        proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=source_dir)
        source_lines.append(f"=== {source_dir} RC={proc.returncode} ===")
        source_lines.append(proc.stdout)
        source_lines.append(proc.stderr)
        if proc.returncode != 0:
            source_rc = proc.returncode
    (evidence_dir / "source_manifest_reverify.txt").write_text(
        "\n".join(source_lines) + f"\nSOURCE_MANIFEST_VERIFY_RC={source_rc}\n",
        encoding="utf-8",
    )

    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        render_parity_gap_matrix_json_v0,
    )
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        DIRECT_TRUE_FLAG_ASSIGNMENT,
        evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
        surface_p_final_flags_result_to_dict_v0,
    )

    final_flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()
    (evidence_dir / "FINAL_FLAGS.json").write_text(
        json.dumps(surface_p_final_flags_result_to_dict_v0(final_flags), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "FULL_CANONICAL_PARITY_GAP_MATRIX.json").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )
    (evidence_dir / "contract_summary.md").write_text(
        "\n".join(
            [
                "# Surface P Final Flags Fail-Closed Contract v0",
                "",
                f"CONTRACT=SurfacePFinalFlagsFailClosedContractV0",
                f"CONFIRMED_GAP=full_canonical_chain_final_flags",
                f"DIRECT_TRUE_FLAG_ASSIGNMENT={str(DIRECT_TRUE_FLAG_ASSIGNMENT).lower()}",
                f"FULL_CANONICAL_CHAIN_WIRED={str(final_flags.full_canonical_chain_wired).lower()}",
                (
                    "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                    f"{str(final_flags.backtest_runtime_decision_parity_pass).lower()}"
                ),
                (
                    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                    f"{str(final_flags.system_economic_evidence_admissible).lower()}"
                ),
                f"RUNTIME_BRIDGE_BINDING_STATUS=BOUND_NOT_ACTIVATED",
                "",
                "## Fail-closed reasons",
                "",
                *[f"- {reason}" for reason in final_flags.fail_closed_reasons],
            ]
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
    (evidence_dir / "test_results.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr + f"\nTARGETED_TESTS_RC={pytest_proc.returncode}\n",
        encoding="utf-8",
    )

    ruff_targets = [str(REPO_ROOT / p) for p in SLICE_CHANGED_FILES if p.endswith(".py")]
    ruff_format = _run([sys.executable, "-m", "ruff", "format", "--check", *ruff_targets])
    ruff_check = _run([sys.executable, "-m", "ruff", "check", *ruff_targets])
    (evidence_dir / "ruff_format.log").write_text(
        ruff_format.stdout + ruff_format.stderr + f"\nRUFF_FORMAT_RC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.log").write_text(
        ruff_check.stdout + ruff_check.stderr + f"\nRUFF_CHECK_RC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    blocked = (
        pytest_proc.returncode != 0
        or ruff_format.returncode != 0
        or ruff_check.returncode != 0
        or source_rc != 0
        or final_flags.full_canonical_chain_wired
        or final_flags.backtest_runtime_decision_parity_pass
        or final_flags.system_economic_evidence_admissible
        or final_flags.direct_true_flag_assignment
    )
    verdict = VERDICT if not blocked else "SURFACE_P_FINAL_FLAGS_FAIL_CLOSED_CONTRACT_V0_BLOCKED"

    (evidence_dir / "final_operator_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                f"TARGETED_TESTS_RC={pytest_proc.returncode}",
                f"LINT_RC={max(ruff_format.returncode, ruff_check.returncode)}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"DIRECT_TRUE_FLAG_ASSIGNMENT=false",
                f"RUNTIME_ACTIVATION=false",
                (
                    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                    f"{str(final_flags.system_economic_evidence_admissible).lower()}"
                ),
                f"FULL_CANONICAL_CHAIN_WIRED={str(final_flags.full_canonical_chain_wired).lower()}",
                (
                    "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                    f"{str(final_flags.backtest_runtime_decision_parity_pass).lower()}"
                ),
            ]
        )
        + "\n",
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
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out)
    print(result["verdict"])
    print(f"EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
