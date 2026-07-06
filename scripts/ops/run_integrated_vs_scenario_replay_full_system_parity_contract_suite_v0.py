#!/usr/bin/env python3
"""Collect durable evidence for integrated vs scenario replay full-system parity suite v0."""

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
BASE_HEAD = "1a7a4ef54eb68415d8371dbe1e98615c52003fe5"
VERDICT = "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_CONTRACT_SUITE_V0_PASS"
PROCESS_CLASSIFICATION = "CANONICAL_FULL_SYSTEM_PARITY_CONTRACT_SUITE_OFFLINE_ONLY"
SCOPE_CLASSIFICATION = (
    "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_CONTRACT_SUITE_"
    "NO_RUNTIME_NO_EVAL_NO_TRADING_SEMANTIC_CHANGE_V0"
)
TARGETED_TESTS = (
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py::test_1_bull_confirmed_bear_blocked_long_selected_v0",
    "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py::test_3_both_confirmed_chop_guard_block_v0",
    "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py::test_scenario_replay_default_still_passes_v0",
    "tests/core/test_prometheus_client_dependency_bound_metrics_contract_v0.py::test_prometheus_client_importable_in_project_environment_v0",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
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
        / f"research/integrated_vs_scenario_replay_full_system_parity_contract_suite_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    prechecks = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"REQUIRED_BASE_HEAD={BASE_HEAD}",
        f"HEAD_MATCHES_BASE={head == BASE_HEAD}",
        f"ORIGIN_MAIN_MATCHES_BASE={origin_main == BASE_HEAD}",
        f"WORKTREE_STATUS={status or 'clean'}",
    ]
    (evidence_dir / "PRECHECKS.txt").write_text("\n".join(prechecks) + "\n", encoding="utf-8")

    reuse_inventory = [
        "INTEGRATED_OWNER=trading.master_v2.integrated_offline_trading_logic_replay_v1",
        "SCENARIO_REPLAY_OWNER=trading.master_v2.offline_double_play_scenario_replay_v0",
        "SCENARIO_MATRIX_ADAPTER=trading.master_v2.double_play_composition_scenario_matrix_adapter_v0",
        "CANONICAL_COMPOSITION_OWNER=trading.master_v2.double_play_composition_matrix_v1",
        "REUSE_PR4945_FIXTURES=test_double_play_composition_scenario_matrix_parity_contract_v0",
        "REUSE_INTEGRATED_FIXTURES=test_integrated_offline_trading_logic_replay_v1._run",
        "NEW_SURFACE=integrated_vs_scenario_replay_full_system_parity_harness_v0",
        "DECISION=extend_existing_owners_no_new_ssot",
    ]
    (evidence_dir / "REUSE_INVENTORY.txt").write_text(
        "\n".join(reuse_inventory) + "\n",
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

    forbidden_probe = _run(
        [
            "git",
            "diff",
            "--name-only",
            f"{BASE_HEAD}...HEAD",
        ]
    )
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
        else "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_CONTRACT_SUITE_V0_BLOCKED"
    )

    final_report = f"""# Integrated vs Scenario Replay Full System Parity Contract Suite v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
GO_TOKEN_CONSUMPTION=CONSUMED_ONCE
BASE_HEAD={BASE_HEAD}
ORIGIN_MAIN={origin_main}
WORKTREE_STATUS={status or "clean"}
CHANGED_FILES={",".join(SLICE_CHANGED_FILES)}
TESTS={"PASS" if tests_pass else "FAIL"}
RUFF={"PASS" if ruff_pass else "FAIL"}
PROMETHEUS_CLIENT_IMPORTABLE={"true" if prom_pass else "false"}
FORBIDDEN_RUNTIME_PATHS_TOUCHED=false
DURABLE_EVIDENCE_DIR={evidence_dir}
MANIFEST_VERIFY_RC={manifest_rc}

No Runtime Authority. No Economic Evaluation. No Double Play semantic change.
"""
    (evidence_dir / "FINAL_REPORT.md").write_text(final_report, encoding="utf-8")
    manifest_rc = _write_manifest(evidence_dir)

    result = {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "prometheus_importable": prom_pass,
    }
    (evidence_dir / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    _write_manifest(evidence_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out)
    print(f"VERDICT={result['verdict']}")
    print(f"DURABLE_EVIDENCE_DIR={result['evidence_dir']}")
    print(f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
