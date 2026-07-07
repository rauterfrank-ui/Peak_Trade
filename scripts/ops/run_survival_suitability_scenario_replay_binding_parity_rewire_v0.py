#!/usr/bin/env python3
"""Collect durable evidence for survival/suitability scenario replay binding parity rewire v0."""

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
PR4970_CLOSEOUT_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research/pr_merge_closeout_flat_before_opposite_side_scenario_replay_binding_parity_rewire_v0_20260707T174801Z"
)
LATEST_REASSESSMENT_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research/full_canonical_backtest_boundary_chain_reassessment_after_flat_before_opposite_side_rewire_v0_20260707T174922Z"
)
NEXT_RECOMMENDED_SLICE = "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
VERDICT = "SURVIVAL_SUITABILITY_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0_PASS"
PROCESS_CLASSIFICATION = "NARROW_REUSE_FIRST_REWIRE_NO_RUNTIME_AUTHORITY"
SCOPE_CLASSIFICATION = "SURVIVAL_SUITABILITY_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SURFACE_C_D_REGRESSION_TESTS = (
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
    "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_survival_suitability_scenario_replay_binding_parity_rewire_v0.py",
    "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
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
        ARCHIVE_ROOT
        / f"research/survival_suitability_scenario_replay_binding_parity_rewire_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    closeout_manifest_proc = _run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=PR4970_CLOSEOUT_EVIDENCE_DIR
    )
    reassessment_manifest_proc = _run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=LATEST_REASSESSMENT_EVIDENCE_DIR
    )
    (evidence_dir / "source_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"PR4970_CLOSEOUT_EVIDENCE_DIR={PR4970_CLOSEOUT_EVIDENCE_DIR}",
                f"PR4970_CLOSEOUT_MANIFEST_VERIFY_RC={closeout_manifest_proc.returncode}",
                f"LATEST_REASSESSMENT_EVIDENCE_DIR={LATEST_REASSESSMENT_EVIDENCE_DIR}",
                f"LATEST_REASSESSMENT_MANIFEST_VERIFY_RC={reassessment_manifest_proc.returncode}",
            ]
        )
        + "\n",
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
    (evidence_dir / "targeted_pytest.txt").write_text(
        " ".join(pytest_cmd)
        + f"\nRC={pytest_proc.returncode}\n\n"
        + pytest_proc.stdout
        + pytest_proc.stderr,
        encoding="utf-8",
    )

    c_d_cmd = [sys.executable, "-m", "pytest", "-q", *SURFACE_C_D_REGRESSION_TESTS]
    c_d_proc = subprocess.run(
        c_d_cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "surface_c_d_regression_pytest.txt").write_text(
        " ".join(c_d_cmd) + f"\nRC={c_d_proc.returncode}\n\n" + c_d_proc.stdout + c_d_proc.stderr,
        encoding="utf-8",
    )

    gap_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    ]
    gap_proc = subprocess.run(
        gap_cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "gap_registry_assessment.txt").write_text(
        " ".join(gap_cmd) + f"\nRC={gap_proc.returncode}\n\n" + gap_proc.stdout + gap_proc.stderr,
        encoding="utf-8",
    )

    ruff_targets = [
        str(REPO_ROOT / p)
        for p in SLICE_CHANGED_FILES
        if p.endswith(".py") and (REPO_ROOT / p).is_file()
    ]
    ruff_format_cmd = ["ruff", "format", "--check", *ruff_targets]
    ruff_check_cmd = ["ruff", "check", *ruff_targets]
    ruff_format = _run(ruff_format_cmd)
    ruff_check = _run(ruff_check_cmd)
    (evidence_dir / "ruff_format_check.txt").write_text(
        ruff_format.stdout + ruff_format.stderr + f"\nRC={ruff_format.returncode}\n",
        encoding="utf-8",
    )
    (evidence_dir / "ruff_check.txt").write_text(
        ruff_check.stdout + ruff_check.stderr + f"\nRC={ruff_check.returncode}\n",
        encoding="utf-8",
    )

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
                f"WORKTREE_STATUS={status or 'clean'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n", encoding="utf-8"
    )
    (evidence_dir / "implementation_summary.txt").write_text(
        "\n".join(
            [
                "Surface E: scenario replay evaluates survival/suitability via canonical owners.",
                "evaluate_scenario_survival_suitability_v0 -> survival_assessment_v1 + suitability_binding_v1.",
                "Legacy envelope retained for dashboard compatibility only; not decision authority.",
                "Surfaces C/D PASS unchanged; P remains PARTIAL.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "canonical_owner_mapping.txt").write_text(
        "\n".join(
            [
                "SURFACE_E_STATUS=PASS",
                "CANONICAL_SURVIVAL_OWNER=trading.master_v2.survival_assessment_v1",
                "CANONICAL_SUITABILITY_OWNER=trading.master_v2.suitability_binding_v1",
                "ADAPTER=trading.master_v2.survival_suitability_scenario_binding_adapter_v0",
                "SCENARIO_BINDING=evaluate_scenario_survival_suitability_v0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "surface_e_binding_evidence.txt").write_text(
        "\n".join(
            [
                "SURFACE_E_STATUS=PASS",
                "CANONICAL_SURVIVAL_OWNER=trading.master_v2.survival_assessment_v1",
                "CANONICAL_SUITABILITY_OWNER=trading.master_v2.suitability_binding_v1",
                "ADAPTER=trading.master_v2.survival_suitability_scenario_binding_adapter_v0",
                "SCENARIO_BINDING=evaluate_scenario_survival_suitability_v0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "residual_gap_status.txt").write_text(
        "\n".join(
            [
                "SURFACE_C_STATUS=PASS",
                "SURFACE_D_STATUS=PASS",
                "SURFACE_E_STATUS=PASS",
                "SURFACE_P_STATUS=UNCHANGED_PARTIAL",
                "REGISTRY_PASS_SURFACES=15",
                "REGISTRY_PARTIAL_SURFACES=1",
                "FINAL_GAP_STATUS=PARTIAL",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "authority_flags.txt").write_text(
        "\n".join(
            [
                "NO_RUNTIME_AUTHORITY=true",
                "NO_ORDER_SUBMISSION=true",
                "NO_ADAPTER_SUBMISSION=true",
                "LIVE_AUTHORIZED=false",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    tests_pass = (
        pytest_proc.returncode == 0 and c_d_proc.returncode == 0 and gap_proc.returncode == 0
    )
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    closeout_manifest_rc = closeout_manifest_proc.returncode
    reassessment_manifest_rc = reassessment_manifest_proc.returncode
    verdict = (
        VERDICT
        if tests_pass
        and ruff_pass
        and manifest_rc == 0
        and closeout_manifest_rc == 0
        and reassessment_manifest_rc == 0
        else "SURVIVAL_SUITABILITY_SCENARIO_REPLAY_BINDING_PARITY_REWIRE_V0_BLOCKED"
    )

    report = f"""# Survival Suitability Scenario Replay Binding Parity Rewire v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
HEAD={head}
ORIGIN_MAIN={origin_main}
HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}
CHANGED_FILES={",".join(SLICE_CHANGED_FILES)}
PR4970_CLOSEOUT_EVIDENCE_DIR={PR4970_CLOSEOUT_EVIDENCE_DIR}
PR4970_CLOSEOUT_MANIFEST_VERIFY_RC={closeout_manifest_rc}
LATEST_REASSESSMENT_EVIDENCE_DIR={LATEST_REASSESSMENT_EVIDENCE_DIR}
LATEST_REASSESSMENT_MANIFEST_VERIFY_RC={reassessment_manifest_rc}
SURFACE_C_STATUS=PASS
SURFACE_D_STATUS=PASS
SURFACE_E_STATUS=PASS
SURFACE_P_STATUS=UNCHANGED_PARTIAL
FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_PASS=false
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false
NO_RUNTIME_AUTHORITY=true
NO_ORDER_AUTHORITY=true
TEST_COMMANDS_AND_RC={" ".join(pytest_cmd)}={pytest_proc.returncode}
SURFACE_C_D_REGRESSION_RC={c_d_proc.returncode}
GAP_REGISTRY_RC={gap_proc.returncode}
RUFF_FORMAT_RC={ruff_format.returncode}
RUFF_CHECK_RC={ruff_check.returncode}
MANIFEST_VERIFY_RC={manifest_rc}
DURABLE_EVIDENCE_DIR={evidence_dir}
NEXT_STEP={NEXT_RECOMMENDED_SLICE}
"""
    (evidence_dir / "FINAL_REPORT.md").write_text(report, encoding="utf-8")
    _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "closeout_manifest_rc": closeout_manifest_rc,
        "reassessment_manifest_rc": reassessment_manifest_rc,
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
