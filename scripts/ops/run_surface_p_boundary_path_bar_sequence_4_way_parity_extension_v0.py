#!/usr/bin/env python3
"""Collect durable evidence for Surface P boundary-path bar-sequence 4-way parity extension v0."""

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
BASE_HEAD = "d2f0fbd76c4d2e43ea0f126d59cf45d1dc36b961"
SELECTOR_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/bounded_next_canonical_non_runtime_slice_selector_after_pr4978_v0_20260707T211730Z"
)
VERDICT = "SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_V0_PASS"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_surface_p_boundary_path_bar_sequence_4_way_parity_extension_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_surface_p_boundary_path_bar_sequence_4_way_parity_extension_v0.py",
    "tests/trading/master_v2/test_surface_p_boundary_path_bar_sequence_4_way_parity_extension_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


def _write_manifest(evidence_dir: Path) -> int:
    entries: list[str] = []
    for path in sorted(p for p in evidence_dir.rglob("*") if p.is_file()):
        if path.name == "MANIFEST.sha256":
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rel = path.relative_to(evidence_dir).as_posix()
        entries.append(f"{digest}  {rel}\n")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("".join(entries), encoding="utf-8")
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    return proc.returncode


def _verify_manifest(path: Path, label: str) -> tuple[int, str]:
    if not path.is_dir():
        return 1, f"{label}_ABSENT=true\n{label}_MANIFEST_VERIFY_RC=1\n"
    proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=path)
    return proc.returncode, (
        proc.stdout
        + proc.stderr
        + f"\n{label}_PATH={path}\n{label}_MANIFEST_VERIFY_RC={proc.returncode}\n"
    )


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/surface_p_boundary_path_bar_sequence_4_way_parity_extension_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir = evidence_dir / "MANIFEST_REVERIFY_LOGS"
    manifest_dir.mkdir(exist_ok=True)
    test_dir = evidence_dir / "TEST_OUTPUTS"
    test_dir.mkdir(exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status_before = _run(["git", "status", "--short"]).stdout.strip()

    selector_rc, selector_log = _verify_manifest(SELECTOR_EVIDENCE, "SELECTOR")
    (manifest_dir / "selector_manifest_reverify.log").write_text(selector_log, encoding="utf-8")

    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
        render_parity_gap_matrix_json_v0,
        scan_changed_paths_for_forbidden_runtime_v0,
    )
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
        SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT,
        evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
        surface_p_bar_sequence_fixtures_v0,
        surface_p_boundary_path_fixtures_v0,
    )
    from trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
        current_head_default_gate_input_v0,
        evaluate_runtime_bridge_pre_activation_gate_v0,
    )

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    gate_res = evaluate_runtime_bridge_pre_activation_gate_v0(current_head_default_gate_input_v0())

    ok_forbidden, violations = scan_changed_paths_for_forbidden_runtime_v0(SLICE_CHANGED_FILES)
    (evidence_dir / "CHANGED_FILES.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n", encoding="utf-8"
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"}
    pytest_proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (test_dir / "targeted_pytest.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    touched = [REPO_ROOT / rel for rel in SLICE_CHANGED_FILES if rel.endswith(".py")]
    ruff_format = _run(["ruff", "format", "--check", *[str(p) for p in touched]])
    ruff_check = _run(["ruff", "check", *[str(p) for p in touched]])
    (test_dir / "ruff_format_check.log").write_text(
        ruff_format.stdout + ruff_format.stderr,
        encoding="utf-8",
    )
    (test_dir / "ruff_check.log").write_text(
        ruff_check.stdout + ruff_check.stderr,
        encoding="utf-8",
    )

    (evidence_dir / "gap_assessment_after.log").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )

    boundary_names = ",".join(item.fixture_id for item in surface_p_boundary_path_fixtures_v0())

    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    blocked = (
        not tests_pass
        or not ruff_pass
        or not ok_forbidden
        or selector_rc != 0
        or not bar_assessment.boundary_path_fixtures_complete
    )
    verdict = (
        VERDICT
        if not blocked
        else "SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_V0_BLOCKED"
    )

    pytest_summary = "unknown"
    for line in pytest_proc.stdout.splitlines():
        if "passed" in line:
            pytest_summary = line.strip()
            break

    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(
            [
                f"VERDICT={verdict}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BASE_HEAD={BASE_HEAD}",
                f"SELECTOR_MANIFEST_VERIFY_RC={selector_rc}",
                f"WORKTREE_STATUS_BEFORE={status_before or 'clean'}",
                f"CHANGED_FILES={','.join(SLICE_CHANGED_FILES)}",
                f"FORBIDDEN_PATHS_VIOLATIONS={len(violations)}",
                f"BOUNDARY_FIXTURES_ADDED={SURFACE_P_BOUNDARY_PATH_FIXTURE_COUNT}:{boundary_names}",
                f"BAR_SEQUENCE_FIXTURES_TOTAL={len(surface_p_bar_sequence_fixtures_v0())}",
                f"SURFACE_P_STATUS={surface_p.parity_status}",
                "FINAL_GAP_STATUS=PARTIAL",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                f"RUNTIME_BRIDGE_STATUS={RUNTIME_REFERENCE_INTEGRATION_STATUS_V0}",
                f"RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE={str(gate_res.runtime_bridge_activation_admissible).lower()}",
                "RUNTIME_AUTHORITY_ACTIVATED=false",
                "PROMOTION_ACTION_ADMISSIBLE=false",
                "ECONOMIC_EVALUATION_ADMISSIBLE=false",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"TARGETED_PYTEST_RESULT={pytest_summary}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"RUFF_FORMAT_CHECK_RC={ruff_format.returncode}",
                f"BOUNDARY_PATH_FIXTURES_COMPLETE={str(bar_assessment.boundary_path_fixtures_complete).lower()}",
                f"CORE_FIXTURES_COMPLETE={str(bar_assessment.core_fixtures_complete).lower()}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Surface P Boundary Path Bar-Sequence 4-Way Parity Extension V0",
                "",
                f"Verdict: `{verdict}`",
                "",
                "Extended Surface P harness with five offline boundary-path fixtures:",
                "safety kernel, killswitch, reconciliation/unknown outcome, promotion gate,",
                "and AI/observability explainability boundaries.",
                "",
                f"Surface P status: {surface_p.parity_status} (unchanged; runtime policy-blocked)",
                f"Boundary fixtures complete: {bar_assessment.boundary_path_fixtures_complete}",
                f"Total fixtures: {len(surface_p_bar_sequence_fixtures_v0())}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "COMMAND_LOG.txt").write_text(
        f"collect_evidence_stamp={stamp}\nselector_rc={selector_rc}\n",
        encoding="utf-8",
    )
    manifest_rc = _write_manifest(evidence_dir)
    if manifest_rc != 0:
        verdict = "SURFACE_P_BOUNDARY_PATH_BAR_SEQUENCE_4_WAY_PARITY_EXTENSION_V0_BLOCKED"
    final_env_lines = (evidence_dir / "FINAL_REPORT.env").read_text(encoding="utf-8").splitlines()
    final_env_lines = [
        f"VERDICT={verdict}" if line.startswith("VERDICT=") else line for line in final_env_lines
    ]
    final_env_lines = [
        line for line in final_env_lines if not line.startswith("MANIFEST_VERIFY_RC=")
    ]
    final_env_lines.append(f"MANIFEST_VERIFY_RC={manifest_rc}")
    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(final_env_lines) + "\n", encoding="utf-8"
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
