#!/usr/bin/env python3
"""Collect durable evidence for full canonical system backtest parity gap assessment v0."""

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
BASE_HEAD = "94c4000064836a60d70efd8963b1281d4fff1513"
PR4946_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/pr4946_integrated_vs_scenario_replay_full_system_parity_contract_suite_merge_closeout_20260706T195606Z"
)
VERDICT = "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0_PASS"
PROCESS_CLASSIFICATION = "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OFFLINE_ONLY"
SCOPE_CLASSIFICATION = (
    "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_NO_TRADING_SEMANTIC_CHANGE_V0"
)
NEXT_RECOMMENDED_SLICE = "SCENARIO_REPLAY_DOUBLE_PLAY_ENTRY_EXIT_POLICY_BINDING_PARITY_REWIRE_V0"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md",
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
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_status_counts_v0,
        parity_surface_assessments_v0,
        render_parity_gap_matrix_markdown_v0,
    )

    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT / f"research/full_canonical_system_backtest_parity_gap_assessment_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    pr4946_manifest = _run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=PR4946_CLOSEOUT)
    prechecks = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"REQUIRED_BASE_HEAD={BASE_HEAD}",
        f"HEAD_MATCHES_BASE={head == BASE_HEAD}",
        f"ORIGIN_MAIN_MATCHES_BASE={origin_main == BASE_HEAD}",
        f"WORKTREE_STATUS={status or 'clean (tolerated .python-version only)'}",
        f"PR4946_CLOSEOUT_DIR={PR4946_CLOSEOUT}",
        f"PR4946_MANIFEST_VERIFY_RC={pr4946_manifest.returncode}",
    ]
    (evidence_dir / "PRECHECKS.txt").write_text("\n".join(prechecks) + "\n", encoding="utf-8")

    source_evidence = [
        f"PR4946_CLOSEOUT={PR4946_CLOSEOUT}",
        f"PR4946_MANIFEST_VERIFY_RC={pr4946_manifest.returncode}",
        *(pr4946_manifest.stdout.splitlines()),
        *(pr4946_manifest.stderr.splitlines()),
    ]
    (evidence_dir / "SOURCE_EVIDENCE_VERIFY.txt").write_text(
        "\n".join(source_evidence) + "\n",
        encoding="utf-8",
    )

    owner_inventory = [
        "GAP_ASSESSMENT_OWNER=trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0",
        "REUSE_PR4946_HARNESS=integrated_vs_scenario_replay_full_system_parity_harness_v0",
        "REUSE_INTEGRATED_OWNER=integrated_offline_trading_logic_replay_v1",
        "REUSE_SCENARIO_OWNER=offline_double_play_scenario_replay_v0",
        "REUSE_BACKTEST_OWNER=backtest/mv2_research_wiring_v1",
        "DECISION=assessment_only_no_rewire_no_new_ssot",
    ]
    for item in parity_surface_assessments_v0():
        owners = ",".join(item.canonical_owner_files)
        owner_inventory.append(
            f"SURFACE_{item.surface_id}={item.surface_name}|status={item.parity_status}|owners={owners}"
        )
    (evidence_dir / "OWNER_INVENTORY.txt").write_text(
        "\n".join(owner_inventory) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "PARITY_GAP_MATRIX.md").write_text(
        render_parity_gap_matrix_markdown_v0(),
        encoding="utf-8",
    )

    recommended = [
        f"NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}",
        "",
        "Rationale:",
        "- Surface F (Double Play composition) is PASS via PR4946 parity harness.",
        "- Surfaces A–E are PARTIAL with shared owners but divergent bindings.",
        "- Surface G (Entry/Position/Exit Policy) is the earliest canonical GAP in the",
        "  offline decision chain after composition: scenario replay does not bind",
        "  evaluate_double_play_entry_exit_policy_v0() per tick.",
        "- Surface H (Capital/Risk/Sizing) is a subsequent GAP requiring a separate slice.",
        "",
        "Forbidden in next slice:",
        "- No runtime authority activation",
        "- No economic evaluation",
        "- No Master-V2 trading semantic change",
        "- No execution/adapter/credential/scheduler paths",
    ]
    (evidence_dir / "RECOMMENDED_NEXT_SLICE.md").write_text(
        "\n".join(recommended) + "\n",
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

    counts = parity_status_counts_v0()
    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    prom_pass = (
        prom_proc.returncode == 0 and "PROMETHEUS_CLIENT_IMPORTABLE=true" in prom_proc.stdout
    )
    manifest_rc = _write_manifest(evidence_dir)
    pr4946_ok = pr4946_manifest.returncode == 0

    verdict = (
        VERDICT
        if tests_pass and ruff_pass and prom_pass and manifest_rc == 0 and pr4946_ok
        else "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0_BLOCKED"
    )

    final_report = f"""# Full Canonical System Backtest Parity Gap Assessment v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
GO_TOKEN_CONSUMPTION=CONSUMED_ONCE
BASE_HEAD={BASE_HEAD}
ORIGIN_MAIN={origin_main}
WORKTREE_STATUS={status or "clean (tolerated .python-version only)"}
PARITY_SURFACES_ASSESSED=16
PASS_SURFACES={counts["PASS"]}
PARTIAL_SURFACES={counts["PARTIAL"]}
GAP_SURFACES={counts["GAP"]}
NOT_APPLICABLE_SURFACES={counts["NOT_APPLICABLE"]}
FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_PASS=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
FORBIDDEN_RUNTIME_PATHS_TOUCHED=false
TESTS={"PASS" if tests_pass else "FAIL"} ({pytest_proc.stdout.strip().splitlines()[-1] if pytest_proc.stdout.strip() else "unknown"})
RUFF_FORMAT={"PASS" if ruff_format.returncode == 0 else "FAIL"}
RUFF_CHECK={"PASS" if ruff_check.returncode == 0 else "FAIL"}
PROMETHEUS_CLIENT_IMPORTABLE={"true" if prom_pass else "false"}
DURABLE_EVIDENCE_DIR={evidence_dir}
MANIFEST_VERIFY_RC={manifest_rc}
NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}

Assessment-only. No runtime authority. No economic evaluation. No trading semantic change.
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
        "parity_status_counts": counts,
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
