#!/usr/bin/env python3
"""Collect durable evidence for Surface P full-system 4-way parity rewire v0."""

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
BASE_HEAD = "e2c345863c0f8fdaee215e32a4c6d4459b439061"
BOUNDED_SELECTOR_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/bounded_selector_retry_surface_p_after_pr4974_hang_recovery_v0_20260707T201702Z"
)
VERDICT = "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0_PASS"
PROCESS_CLASSIFICATION = "NARROW_REUSE_FIRST_4_WAY_PARITY_REWIRE_OFFLINE_ONLY"
SCOPE_CLASSIFICATION = (
    "SURFACE_P_INTEGRATED_SCENARIO_BACKTEST_RUNTIME_REFERENCE_4_WAY_PARITY_"
    "NO_RUNTIME_AUTHORITY_NO_ORDERS_V0"
)
TARGETED_TESTS = (
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
REUSED_OWNERS = (
    "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0",
    "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "trading.master_v2.offline_double_play_scenario_replay_v0",
    "backtest.mv2_research_wiring_v1",
    "trading.master_v2.canonical_core_runtime_integration_bridge_v0",
    "trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0",
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


def _verify_source_manifest(path: Path, label: str) -> tuple[int, str]:
    if not path.is_dir():
        return 1, f"{label}_ABSENT=true\n{label}_MANIFEST_VERIFY_RC=1\n"
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=path)
    log = (
        proc.stdout
        + proc.stderr
        + f"\n{label}_PATH={path}\n{label}_MANIFEST_VERIFY_RC={proc.returncode}\n"
    )
    return proc.returncode, log


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/integrated_vs_scenario_replay_full_system_4_way_parity_rewire_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    selector_rc, selector_log = _verify_source_manifest(
        BOUNDED_SELECTOR_EVIDENCE,
        "BOUNDED_SELECTOR",
    )
    (evidence_dir / "source_manifest_reverify.log").write_text(selector_log, encoding="utf-8")

    (evidence_dir / "PREFLIGHT.env").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BASE_HEAD={BASE_HEAD}",
                f"WORKTREE_STATUS={status or 'clean'}",
                f"BOUNDED_SELECTOR_EVIDENCE={BOUNDED_SELECTOR_EVIDENCE}",
                f"BOUNDED_SELECTOR_MANIFEST_VERIFY_RC={selector_rc}",
                "OFFLINE_ONLY=true",
                "NO_RUNTIME_AUTHORITY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reused_owners.txt").write_text(
        "\n".join(REUSED_OWNERS) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    collect_proc = _run(
        ["pytest", "--collect-only", "-q", *TARGETED_TESTS],
    )
    (evidence_dir / "bounded_collect_only.log").write_text(
        collect_proc.stdout + collect_proc.stderr,
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "targeted_pytest.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    touched = [REPO_ROOT / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
    ruff_format = _run(["ruff", "format", "--check", *[str(p) for p in touched]])
    ruff_check = _run(["ruff", "check", *[str(p) for p in touched]])
    (evidence_dir / "ruff_format_check.log").write_text(
        ruff_format.stdout + ruff_format.stderr,
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.log").write_text(
        ruff_check.stdout + ruff_check.stderr,
        encoding="utf-8",
    )

    diff_proc = _run(["git", "diff", f"{BASE_HEAD}...HEAD"])
    (evidence_dir / "git_diff.patch").write_text(diff_proc.stdout, encoding="utf-8")

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
        render_parity_gap_matrix_json_v0,
    )

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    (evidence_dir / "surface_p_assessment.json").write_text(
        json.dumps(
            {
                "surface_id": surface_p.surface_id,
                "parity_status": surface_p.parity_status,
                "missing_binding": surface_p.missing_binding_if_any,
                "recommended_next_slice": surface_p.recommended_next_slice,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "gap_matrix.json").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    tests_pass = pytest_proc.returncode == 0 and collect_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    verdict = (
        VERDICT
        if tests_pass and ruff_pass and manifest_rc == 0 and selector_rc == 0
        else ("INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0_BLOCKED")
    )

    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
                f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
                f"BASE_HEAD={BASE_HEAD}",
                f"HEAD={head}",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"RUFF_FORMAT_CHECK_RC={ruff_format.returncode}",
                f"BOUNDED_SELECTOR_MANIFEST_VERIFY_RC={selector_rc}",
                f"SURFACE_P_STATUS={surface_p.parity_status}",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
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
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "selector_rc": selector_rc,
    }


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
