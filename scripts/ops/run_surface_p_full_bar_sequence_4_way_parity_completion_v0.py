#!/usr/bin/env python3
"""Collect durable evidence for Surface P full bar-sequence 4-way parity completion v0."""

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
BASE_HEAD = "ed5adb7ad5042c531d52a77f99c99996aaa61e72"
PREVIOUS_REASSESSMENT_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/full_canonical_backtest_boundary_chain_reassessment_after_pr4977_v0_20260707T210247Z"
)
VERDICT = "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0_PASS"
PROCESS_CLASSIFICATION = "NARROW_REUSE_FIRST_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_OFFLINE_ONLY"
SCOPE_CLASSIFICATION = "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_NO_RUNTIME_AUTHORITY_NO_ORDERS_V0"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "scripts/ops/run_surface_p_full_bar_sequence_4_way_parity_completion_v0.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
)
REUSED_OWNERS = (
    "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0",
    "trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "trading.master_v2.offline_double_play_scenario_replay_v0",
    "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0",
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0",
    "backtest.mv2_research_wiring_v1",
    "trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0",
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
        ARCHIVE_ROOT / f"research/surface_p_full_bar_sequence_4_way_parity_completion_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status_before = _run(["git", "status", "--short"]).stdout.strip()

    prev_rc, prev_log = _verify_manifest(PREVIOUS_REASSESSMENT_EVIDENCE, "PREVIOUS_REASSESSMENT")
    (evidence_dir / "previous_reassessment_manifest_reverify.log").write_text(
        prev_log, encoding="utf-8"
    )
    (evidence_dir / "source_manifest_reverify.log").write_text(
        "SOURCE_EVIDENCE_REFERENCED=false\nNOT_APPLICABLE_NO_SOURCE_EVIDENCE_REFERENCED\n",
        encoding="utf-8",
    )
    (evidence_dir / "reuse_discovery.log").write_text(
        "\n".join(
            [
                "REUSE_DISCOVERY=SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0",
                "REUSED_OWNERS:",
                *[f"- {owner}" for owner in REUSED_OWNERS],
                "",
                "DISCOVERED_FUNCTIONS:",
                "- evaluate_surface_p_full_bar_sequence_four_way_parity_v0",
                "- surface_p_bar_sequence_fixtures_v0",
                "- bind_backtest_bar_parity_lane_at_index_v0",
                "- extract_runtime_reference_parity_envelope_v0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.log").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )

    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
        render_parity_gap_matrix_json_v0,
        scan_changed_paths_for_forbidden_runtime_v0,
    )
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        RUNTIME_REFERENCE_INTEGRATION_STATUS_V0,
        evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
        surface_p_bar_sequence_fixtures_v0,
    )

    surface_p_before = "PARTIAL"
    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()

    ok_forbidden, violations = scan_changed_paths_for_forbidden_runtime_v0(SLICE_CHANGED_FILES)
    (evidence_dir / "forbidden_paths_check.env").write_text(
        "\n".join(
            [
                f"FORBIDDEN_PATHS_VIOLATIONS={len(violations)}",
                f"FORBIDDEN_PATHS_OK={str(ok_forbidden).lower()}",
                f"VIOLATIONS={','.join(violations) if violations else 'none'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    matrix_lines = [
        "# Surface P Parity Fixture Matrix",
        "",
        "| Fixture | Path Kind | Backtest Bar | Four-Way Bound |",
        "|---------|-----------|--------------|----------------|",
    ]
    for fixture, assessment in zip(
        surface_p_bar_sequence_fixtures_v0(),
        bar_assessment.fixture_assessments,
        strict=True,
    ):
        matrix_lines.append(
            f"| {fixture.fixture_id} | {fixture.path_kind} | {fixture.backtest_bar_index}"
            f" | {assessment.four_way_fixture_parity_bound} |"
        )
    (evidence_dir / "parity_fixture_matrix.md").write_text(
        "\n".join(matrix_lines) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "implementation_summary.md").write_text(
        "\n".join(
            [
                "# Surface P Full Bar-Sequence 4-Way Parity Completion V0",
                "",
                "Extended integrated_vs_scenario_replay_full_system_parity_harness_v0 with",
                " eight bar-sequence fixtures covering entry, hold, adverse exit, reversal",
                " preparation, flat-before-opposite, capital/risk/sizing, canonical order",
                " intent, and blocked/no-action paths.",
                "",
                f"Fixtures complete: {bar_assessment.fixtures_complete}",
                f"Surface P status after: {surface_p.parity_status}",
                "Runtime bridge: BOUND_NOT_ACTIVATED (policy-blocked)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "runtime_authority_boundary_check.env").write_text(
        "\n".join(
            [
                f"RUNTIME_BRIDGE_STATUS={RUNTIME_REFERENCE_INTEGRATION_STATUS_V0}",
                "RUNTIME_AUTHORITY_ACTIVATED=false",
                "ORDERS_ALLOWED=false",
                "SCHEDULER_RUNTIME_ALLOWED=false",
                "NO_RUNTIME_AUTHORITY=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "PREFLIGHT.env").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BASE_HEAD={BASE_HEAD}",
                f"PREVIOUS_REASSESSMENT_EVIDENCE={PREVIOUS_REASSESSMENT_EVIDENCE}",
                f"PREVIOUS_REASSESSMENT_MANIFEST_VERIFY_RC={prev_rc}",
                f"WORKTREE_STATUS={status_before or 'clean'}",
                "OFFLINE_ONLY=true",
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

    (evidence_dir / "gap_assessment_after.log").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )

    status_after = _run(["git", "status", "--short"]).stdout.strip()
    manifest_rc = _write_manifest(evidence_dir)

    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    blocked = (
        not tests_pass
        or not ruff_pass
        or not ok_forbidden
        or manifest_rc != 0
        or prev_rc != 0
        or not bar_assessment.fixtures_complete
    )
    verdict = (
        VERDICT if not blocked else "SURFACE_P_FULL_BAR_SEQUENCE_4_WAY_PARITY_COMPLETION_V0_BLOCKED"
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
                f"HEAD_EQUALS_ORIGIN_MAIN={str(head == origin_main).lower()}",
                "BRANCH=feat/surface-p-full-bar-sequence-4-way-parity-completion-v0",
                f"PREVIOUS_REASSESSMENT_MANIFEST_VERIFY_RC={prev_rc}",
                "SOURCE_EVIDENCE_REFERENCED=false",
                "SOURCE_MANIFEST_VERIFY_RC=NOT_APPLICABLE_NO_SOURCE_EVIDENCE_REFERENCED",
                f"WORKTREE_STATUS_BEFORE={status_before or 'clean'}",
                f"WORKTREE_STATUS_AFTER={status_after or 'clean'}",
                f"CHANGED_FILES={','.join(SLICE_CHANGED_FILES)}",
                f"FORBIDDEN_PATHS_VIOLATIONS={len(violations)}",
                f"TARGETED_PYTEST_RC={pytest_proc.returncode}",
                f"TARGETED_PYTEST_RESULT={pytest_summary}",
                f"RUFF_CHECK_RC={ruff_check.returncode}",
                f"RUFF_FORMAT_CHECK_RC={ruff_format.returncode}",
                "RUFF_FORMAT_CHECK_MD=SKIPPED_EXPERIMENTAL",
                f"SURFACE_P_STATUS_BEFORE={surface_p_before}",
                f"SURFACE_P_STATUS_AFTER={surface_p.parity_status}",
                "FULL_CANONICAL_CHAIN_WIRED_STATUS=false",
                "BACKTEST_RUNTIME_DECISION_PARITY_STATUS=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                f"RUNTIME_BRIDGE_STATUS={RUNTIME_REFERENCE_INTEGRATION_STATUS_V0}",
                "RUNTIME_AUTHORITY_ACTIVATED=false",
                "ORDERS_ALLOWED=false",
                "SCHEDULER_RUNTIME_ALLOWED=false",
                "NEXT_STEP=FULL_CANONICAL_BACKTEST_BOUNDARY_CHAIN_REASSESSMENT_V0",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"BAR_SEQUENCE_FIXTURES_COMPLETE={str(bar_assessment.fixtures_complete).lower()}",
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
        "prev_rc": prev_rc,
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
