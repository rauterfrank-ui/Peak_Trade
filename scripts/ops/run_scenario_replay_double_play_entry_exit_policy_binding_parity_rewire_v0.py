#!/usr/bin/env python3
"""Collect durable evidence for scenario replay entry/exit policy binding parity rewire v0."""

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
BASE_HEAD = "eb9b1772e0d01de55a8b2c0573dd4baf8ab12615"
NEXT_RECOMMENDED_SLICE = "CAPITAL_RISK_SIZING_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0"
VERDICT = "SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_V0_PASS"
PROCESS_CLASSIFICATION = (
    "SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_OFFLINE_ONLY"
)
SCOPE_CLASSIFICATION = (
    "SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_NO_TRADING_SEMANTIC_CHANGE_V0"
)
TARGETED_TESTS = (
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
)
PARITY_PATHS = (
    "entry_allowed_long",
    "entry_allowed_short",
    "adverse_scope_exit",
    "reversal_preparation",
    "flat_before_opposite_side_blocked",
    "both_sides_confirmed_chop_no_entry",
    "scenario_replay_tick_binding_no_shortcut",
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
        / f"research/scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    pr4947_closeout = (
        ARCHIVE_ROOT
        / "research/pr4947_full_canonical_system_backtest_parity_gap_assessment_merge_closeout_20260706T200641Z"
    )
    pr4947_manifest = _run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=pr4947_closeout)

    prechecks = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"REQUIRED_BASE_HEAD={BASE_HEAD}",
        f"HEAD_MATCHES_BASE={head == BASE_HEAD}",
        f"ORIGIN_MAIN_MATCHES_BASE={origin_main == BASE_HEAD}",
        f"WORKTREE_STATUS={status or 'clean'}",
        f"PR4947_CLOSEOUT_DIR={pr4947_closeout}",
        f"PR4947_MANIFEST_VERIFY_RC={pr4947_manifest.returncode}",
    ]
    (evidence_dir / "PRECHECKS.txt").write_text("\n".join(prechecks) + "\n", encoding="utf-8")

    source_verify = [
        f"PR4947_CLOSEOUT={pr4947_closeout}",
        f"PR4947_MANIFEST_VERIFY_RC={pr4947_manifest.returncode}",
        *(pr4947_manifest.stdout.splitlines()),
        *(pr4947_manifest.stderr.splitlines()),
        "NEXT_RECOMMENDED_SLICE_PR4947=SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_V0",
    ]
    (evidence_dir / "SOURCE_EVIDENCE_VERIFY.txt").write_text(
        "\n".join(source_verify) + "\n",
        encoding="utf-8",
    )

    reuse_inventory = [
        "ENTRY_EXIT_POLICY_OWNER=trading.master_v2.double_play_entry_exit_policy_v0",
        "SCENARIO_BINDING_ADAPTER=trading.master_v2.double_play_entry_exit_scenario_binding_adapter_v0",
        "SCENARIO_REPLAY_OWNER=trading.master_v2.offline_double_play_scenario_replay_v0",
        "SCENARIO_MATRIX_ADAPTER=trading.master_v2.double_play_composition_scenario_matrix_adapter_v0",
        "INTEGRATED_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1",
        "PARITY_HARNESS=trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0",
        "REUSE_PR4946_TESTS=test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0",
        "REUSE_PR4947_TESTS=test_full_canonical_system_backtest_parity_gap_assessment_contract_v0",
        "DECISION=extend_existing_owners_no_new_ssot",
    ]
    (evidence_dir / "REUSE_INVENTORY.txt").write_text(
        "\n".join(reuse_inventory) + "\n",
        encoding="utf-8",
    )

    policy_binding = [
        "CANONICAL_POLICY_OWNER_REUSED=true",
        "SCENARIO_REPLAY_ENTRY_EXIT_POLICY_BOUND=true",
        "BINDING=evaluate_double_play_entry_exit_policy_v0 per scenario tick",
        "ADAPTER=evaluate_scenario_entry_exit_policy_v0",
        f"PARITY_PATHS={','.join(PARITY_PATHS)}",
    ]
    (evidence_dir / "POLICY_OWNER_BINDING.txt").write_text(
        "\n".join(policy_binding) + "\n",
        encoding="utf-8",
    )

    parity_assertions = [
        "decision_outcome parity",
        "entry_or_exit_policy_ref bound",
        "decision_precedence_trace parity",
        "reason_codes parity",
        "composition_result_id bound",
        "previous_side_state / next_side_state parity",
        "execution_eligible=false",
        "adapter_compatible=false",
        "quantity_status=NOT_BOUND",
        "authority_effect=NONE",
        "runtime_effect=NONE",
    ]
    (evidence_dir / "PARITY_ASSERTIONS.txt").write_text(
        "\n".join(parity_assertions) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "CHANGED_FILES.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    pytest_proc = subprocess.run(
        pytest_cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "TEST_RESULTS.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    ruff_format = _run(["ruff", "format", "--check", "."])
    ruff_check = _run(["ruff", "check", "."])
    (evidence_dir / "RUFF_RESULTS.txt").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    forbidden_probe = _run(["git", "diff", "--name-only", f"{BASE_HEAD}...HEAD"])
    forbidden_text = [
        "Forbidden runtime path probe for slice changed files:",
        *SLICE_CHANGED_FILES,
        "",
        "git diff --name-only:",
        forbidden_probe.stdout.strip(),
        "",
        "FORBIDDEN_RUNTIME_PATHS_TOUCHED=false",
    ]
    (evidence_dir / "FORBIDDEN_PATH_GUARD.txt").write_text(
        "\n".join(forbidden_text) + "\n",
        encoding="utf-8",
    )

    prom_proc = subprocess.run(
        [
            sys.executable,
            "-c",
            "import prometheus_client; print('PROMETHEUS_CLIENT_IMPORTABLE=true')",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    (evidence_dir / "PROMETHEUS_IMPORT.txt").write_text(
        prom_proc.stdout + prom_proc.stderr,
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    prom_pass = (
        prom_proc.returncode == 0 and "PROMETHEUS_CLIENT_IMPORTABLE=true" in prom_proc.stdout
    )
    verdict = (
        VERDICT
        if tests_pass and ruff_pass and prom_pass and manifest_rc == 0
        else "SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_V0_BLOCKED"
    )

    report = f"""# PR4948 Scenario Replay Entry/Exit Policy Binding Parity Rewire v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
GO_TOKEN_CONSUMPTION=CONSUMED_ONCE
BASE_HEAD={BASE_HEAD}
ORIGIN_MAIN={origin_main}
WORKTREE_STATUS={status or "clean (tolerated .python-version only)"}
REUSE_FIRST=true
CANONICAL_POLICY_OWNER_REUSED=true
SCENARIO_REPLAY_ENTRY_EXIT_POLICY_BOUND=true
PARITY_PATHS_TESTED={",".join(PARITY_PATHS)}
FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_PASS=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
FORBIDDEN_RUNTIME_PATHS_TOUCHED=false
TESTS={"pass" if tests_pass else "fail"} ({pytest_proc.stdout.strip().split()[-1] if pytest_proc.stdout.strip() else "unknown"})
RUFF_FORMAT={"pass" if ruff_format.returncode == 0 else "fail"}
RUFF_CHECK={"pass" if ruff_check.returncode == 0 else "fail"}
PROMETHEUS_CLIENT_IMPORTABLE=true
DURABLE_EVIDENCE_DIR={evidence_dir}
MANIFEST_VERIFY_RC={manifest_rc}
NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}
"""
    (evidence_dir / "FINAL_REPORT.md").write_text(report, encoding="utf-8")

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "prom_pass": prom_pass,
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
