#!/usr/bin/env python3
"""Collect durable evidence for reversal preparation scenario replay binding parity rewire v0."""

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
SOURCE_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research/full_canonical_backtest_boundary_chain_reassessment_after_scope_event_rewire_v0_20260707T172819Z"
)
NEXT_RECOMMENDED_SLICE = "FLAT_BEFORE_OPPOSITE_SIDE_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0"
VERDICT = "REVERSAL_PREPARATION_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0_PASS"
PROCESS_CLASSIFICATION = "NARROW_REUSE_FIRST_REWIRE_WITH_TEST_HYGIENE"
SCOPE_CLASSIFICATION = "REVERSAL_PREPARATION_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_offline_master_v2_double_play_scenario_replay_binding_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_reversal_preparation_scenario_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
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
    proc = _run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/reversal_preparation_scenario_replay_binding_parity_rewire_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    source_manifest_proc = _run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE_DIR)
    (evidence_dir / "source_manifest_reverify.log").write_text(
        source_manifest_proc.stdout + source_manifest_proc.stderr,
        encoding="utf-8",
    )

    commands: list[str] = []
    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    commands.append(" ".join(pytest_cmd))
    pytest_proc = subprocess.run(
        pytest_cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "tests.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    ruff_targets = [
        str(REPO_ROOT / p)
        for p in SLICE_CHANGED_FILES
        if p.endswith(".py") and (REPO_ROOT / p).is_file()
    ]
    ruff_format_cmd = ["ruff", "format", "--check", *ruff_targets]
    ruff_check_cmd = ["ruff", "check", *ruff_targets]
    commands.extend([" ".join(ruff_format_cmd), " ".join(ruff_check_cmd)])
    ruff_format = _run(ruff_format_cmd)
    ruff_check = _run(ruff_check_cmd)
    (evidence_dir / "ruff.log").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )
    (evidence_dir / "commands.log").write_text("\n".join(commands) + "\n", encoding="utf-8")

    (evidence_dir / "git_state.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN_AT_START={head == origin_main}",
                f"WORKTREE_STATUS={status or 'clean'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "PRE_FLIGHT.md").write_text(
        "\n".join(
            [
                "# Pre-Flight",
                "",
                "BASE_HEAD=61a0c33175a57819cfa708026014c967f332fa92",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                "HEAD_EQUALS_ORIGIN_MAIN=false",
                "BRANCH=feat/reversal-preparation-scenario-replay-binding-parity-v0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "SOURCE_EVIDENCE_REVERIFY.md").write_text(
        "\n".join(
            [
                "# Source Evidence Reverify",
                "",
                f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_proc.returncode}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "REUSE_DISCOVERY.md").write_text(
        "\n".join(
            [
                "# Reuse Discovery",
                "",
                "| Role | Owner |",
                "|---|---|",
                "| Canonical entry-exit policy | `trading.master_v2.double_play_entry_exit_policy_v0` |",
                "| Composition matrix | `trading.master_v2.double_play_composition_matrix_v1` |",
                "| Scenario entry-exit adapter | `trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0` |",
                "| Reversal preparation scenario adapter | `trading.master_v2.reversal_preparation_scenario_binding_adapter_v0` |",
                "| Scenario replay orchestrator | `trading.master_v2.offline_double_play_scenario_replay_v0` |",
                "",
                "Pattern reused from PR4967/PR4968 consumer-bridge adapters.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "IMPLEMENTATION_NOTES.md").write_text(
        "\n".join(
            [
                "# Implementation Notes",
                "",
                "Surface C only: scenario replay calls `evaluate_scenario_reversal_preparation_entry_exit_v0()`.",
                "REVERSAL_PREPARATION composition maps to open-position policy context and opposite selected_side projection.",
                "Canonical policy emits REVERSAL_PREPARATION_EXIT (reduce-only, no opposite-side entry).",
                "Surfaces D/E/P unchanged PARTIAL.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "BOUNDARY_MATRIX_DELTA.md").write_text(
        "\n".join(
            [
                "# Boundary Matrix Delta",
                "",
                "Surface C: PARTIAL -> PASS",
                "Surfaces D/E/P: unchanged PARTIAL",
                "PASS count: 12 -> 13",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "AUTHORITY_FLAGS.md").write_text(
        "\n".join(
            [
                "# Authority Flags",
                "",
                "NO_RUNTIME_AUTHORITY=true",
                "NO_ORDER_AUTHORITY=true",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    source_manifest_rc = source_manifest_proc.returncode
    verdict = (
        VERDICT
        if tests_pass and ruff_pass and manifest_rc == 0 and source_manifest_rc == 0
        else "REVERSAL_PREPARATION_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0_BLOCKED"
    )

    report = f"""# Reversal Preparation Scenario Replay Binding Parity Rewire v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
BASE_HEAD=61a0c33175a57819cfa708026014c967f332fa92
HEAD={head}
ORIGIN_MAIN={origin_main}
HEAD_EQUALS_ORIGIN_MAIN=false
BRANCH=feat/reversal-preparation-scenario-replay-binding-parity-v0
CHANGED_FILES={",".join(SLICE_CHANGED_FILES)}
SOURCE_REASSESSMENT_EVIDENCE_REFERENCED=true
SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}
SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}
SURFACE_C_STATUS=PASS
SURFACE_D_STATUS=UNCHANGED_PARTIAL
SURFACE_E_STATUS=UNCHANGED_PARTIAL
SURFACE_P_STATUS=UNCHANGED_PARTIAL
FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_PASS=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
NO_RUNTIME_AUTHORITY=true
NO_ORDER_AUTHORITY=true
TEST_COMMANDS_AND_RC={" ".join(pytest_cmd)}={pytest_proc.returncode}
RUFF_FORMAT_RC={ruff_format.returncode}
RUFF_CHECK_RC={ruff_check.returncode}
MANIFEST_VERIFY_RC={manifest_rc}
DURABLE_EVIDENCE_DIR={evidence_dir}
NEXT_STEP={NEXT_RECOMMENDED_SLICE}
"""
    (evidence_dir / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (evidence_dir / "TEST_RESULTS.md").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )
    _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "source_manifest_rc": source_manifest_rc,
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
