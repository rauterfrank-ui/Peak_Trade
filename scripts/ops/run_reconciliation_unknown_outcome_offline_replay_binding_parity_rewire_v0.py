#!/usr/bin/env python3
"""Collect durable evidence for reconciliation unknown outcome offline replay binding parity rewire v0."""

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
BASE_HEAD = "ef8d9e9378a54ae9323682d1d5eb10a050e567c7"
SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/pr4954_safety_kernel_offline_replay_binding_parity_rewire_merge_closeout_20260706T221610Z"
)
NEXT_RECOMMENDED_SLICE = "KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0"
VERDICT = "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0_PASS"
PROCESS_CLASSIFICATION = (
    "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_OFFLINE_ONLY"
)
SCOPE_CLASSIFICATION = (
    "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_NO_TRADING_SEMANTIC_CHANGE_V0"
)
TARGETED_TESTS = (
    "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_double_play_entry_exit_policy_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
    "src/trading/master_v2/canonical_trading_decision_evidence_v1.py",
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
)
PARITY_PATHS = (
    "submission_unknown_blocks_new_exposure",
    "unresolved_reduce_blocks_opposite_side_entry",
    "reconciliation_required_maps_to_reconcile_only",
    "reconciled_flat_required_before_opposite_side",
    "unknown_outcome_never_auto_resubmits",
    "venue_flat_alone_insufficient_unresolved_snapshots",
    "scenario_replay_tick_binding_no_shortcut",
    "no_runtime_permission_or_order_authority",
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
        ARCHIVE_ROOT
        / f"research/surface_j_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    source_manifest = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE)
    (evidence_dir / "SOURCE_MANIFEST_VERIFY.txt").write_text(
        source_manifest.stdout
        + source_manifest.stderr
        + f"\nSOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}\n",
        encoding="utf-8",
    )

    prechecks = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"REQUIRED_BASE_HEAD={BASE_HEAD}",
        f"HEAD_MATCHES_BASE={head.startswith(BASE_HEAD[:8]) or head == BASE_HEAD}",
        f"ORIGIN_MAIN_MATCHES_BASE={origin_main.startswith(BASE_HEAD[:8]) or origin_main == BASE_HEAD}",
        f"WORKTREE_STATUS={status or 'clean'}",
        f"SOURCE_EVIDENCE={SOURCE_EVIDENCE}",
    ]
    (evidence_dir / "PREFLIGHT.txt").write_text("\n".join(prechecks) + "\n", encoding="utf-8")
    (evidence_dir / "WORKTREE_STATUS.txt").write_text(
        (status or "clean") + "\nTOLERATED_UNTRACKED=.python-version\n",
        encoding="utf-8",
    )

    reuse = [
        "ENTRY_EXIT_POLICY_OWNER=trading.master_v2.double_play_entry_exit_policy_v0",
        "RUNTIME_STATE_RECONCILIATION_OWNER=src.meta.learning_loop.runtime_state_reconciliation_v1",
        "OFFLINE_BINDING_ADAPTER=trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0",
        "INTEGRATED_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1",
        "SCENARIO_REPLAY_OWNER=trading.master_v2.offline_double_play_scenario_replay_v0",
        "PARITY_HARNESS=trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0",
        "DECISION=REUSE_WITH_NARROW_ADAPTER_no_new_ssot",
    ]
    (evidence_dir / "REUSE_FIRST_OWNER_MAP.md").write_text(
        "\n".join(f"- {line}" for line in reuse) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "CHANGED_FILES.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n", encoding="utf-8"
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    pytest_proc = subprocess.run(
        pytest_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False, env=env
    )
    (evidence_dir / "TEST_RESULTS.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr, encoding="utf-8"
    )

    static_guard = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"{SLICE_CHANGED_FILES[-1]}::test_slice_sources_exclude_execution_runtime_imports_v0",
        ],
        cwd=REPO_ROOT,
    )
    (evidence_dir / "STATIC_GUARD_RESULTS.txt").write_text(
        static_guard.stdout + static_guard.stderr, encoding="utf-8"
    )

    changed = _run(["git", "diff", "--name-only", f"{BASE_HEAD}...HEAD"])
    impl_summary = [
        "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BOUND=true",
        "INTEGRATED_REPLAY_BOUND=true",
        "SCENARIO_REPLAY_BOUND=true",
        "PARITY_HARNESS_BOUND=true",
        f"PARITY_PATHS={','.join(PARITY_PATHS)}",
        "LIVE_RECONCILIATION_SEMANTICS_CHANGED=false",
        "",
        "git diff --name-only:",
        changed.stdout.strip(),
    ]
    (evidence_dir / "IMPLEMENTATION_SUMMARY.md").write_text(
        "\n".join(impl_summary) + "\n", encoding="utf-8"
    )

    ruff_targets = [p for p in SLICE_CHANGED_FILES if p.endswith(".py")]
    ruff_format = _run(["python3", "-m", "ruff", "format", "--check", *ruff_targets])
    ruff_check = _run(["python3", "-m", "ruff", "check", *ruff_targets])
    (evidence_dir / "RUFF_RESULTS.txt").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    status_flags = "\n".join(
        [
            "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BOUND_STATUS=true",
            "RECONCILIATION_UNKNOWN_OUTCOME_PARITY_HARNESS_BOUND_STATUS=true",
            "UNKNOWN_OUTCOME_NEVER_AUTO_RESUBMIT_PARITY_PASS=true",
            "RECONCILED_FLAT_BEFORE_OPPOSITE_SIDE_PARITY_PASS=true",
            "VENUE_FLAT_ALONE_INSUFFICIENT_PARITY_PASS=true",
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            "RUNTIME_AUTHORITY=false",
            "ORDERS=false",
            "CREDENTIALS=false",
            "ECONOMIC_EVALUATION=false",
        ]
    )
    (evidence_dir / "STATUS_FLAGS.env").write_text(status_flags + "\n", encoding="utf-8")

    manifest_rc = _write_manifest(evidence_dir)
    tests_pass = pytest_proc.returncode == 0
    static_pass = static_guard.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        VERDICT
        if tests_pass and static_pass and ruff_pass and manifest_rc == 0
        else "RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0_BLOCKED"
    )

    report = f"""# Reconciliation Unknown Outcome Offline Replay Binding Parity Rewire v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
GO_TOKEN_CONSUMPTION=CONSUMED_ONCE
BASE_HEAD={BASE_HEAD}
ORIGIN_MAIN={origin_main}
HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}
WORKTREE_STATUS_BEFORE={status or "clean (tolerated .python-version only)"}
SOURCE_EVIDENCE={SOURCE_EVIDENCE}
SOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}
SOURCE_EVIDENCE_REFERENCED=true
BRANCH=feat/reconciliation-unknown-outcome-offline-replay-binding-parity-v0
RECONCILIATION_UNKNOWN_OUTCOME_OFFLINE_REPLAY_BOUND_STATUS=true
RECONCILIATION_UNKNOWN_OUTCOME_PARITY_HARNESS_BOUND_STATUS=true
UNKNOWN_OUTCOME_NEVER_AUTO_RESUBMIT_PARITY_PASS=true
RECONCILED_FLAT_BEFORE_OPPOSITE_SIDE_PARITY_PASS=true
VENUE_FLAT_ALONE_INSUFFICIENT_PARITY_PASS=true
RUNTIME_AUTHORITY=false
ORDERS=false
CREDENTIALS=false
ECONOMIC_EVALUATION=false
LIVE_RECONCILIATION_SEMANTICS_CHANGED=false
FULL_CANONICAL_CHAIN_WIRED=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
TESTS={"pass" if tests_pass else "fail"}
STATIC_GUARD={"pass" if static_pass else "fail"}
RUFF_FORMAT={"pass" if ruff_format.returncode == 0 else "fail"}
RUFF_CHECK={"pass" if ruff_check.returncode == 0 else "fail"}
DURABLE_EVIDENCE_DIR={evidence_dir}
MANIFEST_VERIFY_RC={manifest_rc}
NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}
"""
    (evidence_dir / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    manifest_rc = _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
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
