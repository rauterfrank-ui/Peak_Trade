#!/usr/bin/env python3
"""Collect durable evidence for backtest reconciliation state-file wiring v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
BASE_HEAD = "0a04d4283554d22bf5cb46b95106e415f5afcafa"
SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/backtest_killswitch_state_file_wiring_v0_merge_closeout_20260706T224652Z"
)
NEXT_RECOMMENDED_SLICE = "BACKTEST_CAPITAL_RISK_SIZING_WIRING_V0"
VERDICT = "BACKTEST_RECONCILIATION_STATE_FILE_WIRING_V0_PASS"
PROCESS_CLASSIFICATION = "FULL_CANONICAL_BACKTEST_PARITY_NARROW_REWIRE"
SCOPE_CLASSIFICATION = (
    "BACKTEST_RECONCILIATION_STATE_FILE_WIRING_V0_NO_RUNTIME_NO_ORDERS_NO_ECONOMIC_EVALUATION_V0"
)
TARGETED_TESTS = (
    "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_backtest_reconciliation_state_file_wiring_v0.py",
    "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
)
REUSED_OWNERS = (
    "trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0",
    "src.meta.learning_loop.runtime_state_reconciliation_v1",
    "trading.master_v2.double_play_entry_exit_policy_v0",
    "backtest.mv2_research_wiring_v1",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _write_manifest(evidence_dir: Path) -> int:
    entries: list[str] = []
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_dir() or path.name == "MANIFEST.sha256":
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  ./{rel}\n")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("".join(entries), encoding="utf-8")
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/backtest_reconciliation_state_file_wiring_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()
    diff_stat = _run(["git", "diff", "--stat", f"{BASE_HEAD}...HEAD"])

    source_manifest = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE)
    (evidence_dir / "source_closeout_manifest_verify.log").write_text(
        source_manifest.stdout
        + source_manifest.stderr
        + f"\nSOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}\n",
        encoding="utf-8",
    )

    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"BRANCH={branch}",
                f"ORIGIN_MAIN={origin_main}",
                f"PRE_MERGE_ORIGIN_MAIN={BASE_HEAD}",
                f"BASE_HEAD={BASE_HEAD}",
                f"WORKTREE_STATUS={status or 'clean'}",
                f"SOURCE_CLOSEOUT_EVIDENCE={SOURCE_EVIDENCE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reused_owners.txt").write_text(
        "\n".join(REUSED_OWNERS) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "implementation_summary.txt").write_text(
        "\n".join(
            [
                "BACKTEST_RECONCILIATION_STATE_FILE_BOUND_STATUS=true",
                "RECONCILIATION_SEMANTICS_REPRESENTED_IN_BACKTEST=true",
                "UNKNOWN_OUTCOME_SEMANTICS_REPRESENTED_IN_BACKTEST=true",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "NO_RUNTIME_AUTHORITY_FROM_RECONCILIATION_STATE_FILE=true",
                "NO_RUNTIME_AUTHORITY=true",
                "NO_ORDERS=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "diff_stat.txt").write_text(
        diff_stat.stdout + diff_stat.stderr, encoding="utf-8"
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    pytest_proc = subprocess.run(
        pytest_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False, env=env
    )
    (evidence_dir / "test_reconciliation_backtest_state_file.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    touched = " ".join(SLICE_CHANGED_FILES)
    ruff_format = _run(["python3", "-m", "ruff", "format", "--check", *SLICE_CHANGED_FILES])
    ruff_check = _run(["python3", "-m", "ruff", "check", *SLICE_CHANGED_FILES])
    (evidence_dir / "ruff.log").write_text(
        f"RUFF_FORMAT ({touched})\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + f"\nRUFF_CHECK ({touched})\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    verify_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    (evidence_dir / "MANIFEST_VERIFY.log").write_text(
        verify_proc.stdout
        + verify_proc.stderr
        + f"\nMANIFEST_VERIFY_RC={verify_proc.returncode}\n",
        encoding="utf-8",
    )

    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        VERDICT
        if tests_pass and ruff_pass and manifest_rc == 0 and source_manifest.returncode == 0
        else "BACKTEST_RECONCILIATION_STATE_FILE_WIRING_V0_BLOCKED"
    )

    report = "\n".join(
        [
            f"VERDICT={verdict}",
            f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
            f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
            "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
            f"BASE_HEAD={BASE_HEAD}",
            f"ORIGIN_MAIN={origin_main}",
            f"BRANCH={branch}",
            f"COMMIT={head}",
            f"SOURCE_CLOSEOUT_EVIDENCE={SOURCE_EVIDENCE}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}",
            "BACKTEST_RECONCILIATION_STATE_FILE_BOUND_STATUS=true",
            "RECONCILIATION_SEMANTICS_REPRESENTED_IN_BACKTEST=true",
            "UNKNOWN_OUTCOME_SEMANTICS_REPRESENTED_IN_BACKTEST=true",
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            "NO_RUNTIME_AUTHORITY=true",
            "NO_ORDERS=true",
            f"TESTS={'pass' if tests_pass else 'fail'}",
            f"RUFF={'pass' if ruff_pass else 'fail'}",
            f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            f"MANIFEST_VERIFY_RC={manifest_rc}",
            f"NEXT_STEP={NEXT_RECOMMENDED_SLICE}",
        ]
    )
    (evidence_dir / "FINAL_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    manifest_rc = _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "source_manifest_rc": source_manifest.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
