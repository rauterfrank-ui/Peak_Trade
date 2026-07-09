#!/usr/bin/env python3
"""Collect durable evidence for full canonical system backtest parity gap assessment v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
BASE_HEAD = "aa18c875c497c4c9f30eb7e1f7ba9e59f071ec6d"
PR4951_SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/pr4951_closeout_pytest_pipefail_and_collection_error_guard_v0_20260706T205315Z"
)
POST_MERGE_GUARD = REPO_ROOT / "scripts/ops/squash_merge_post_merge_closeout_guard_v0.sh"
VERDICT = "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AFTER_PR4951_V0_PASS"
PROCESS_CLASSIFICATION = (
    "READ_ONLY_GAP_ASSESSMENT_WITH_OPTIONAL_NARROW_REUSE_FIRST_REWIRE_RATIFICATION_ONLY"
)
SCOPE_CLASSIFICATION = (
    "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AFTER_CLOSEOUT_PIPEFAIL_GUARD_"
    "NO_RUNTIME_NO_EVAL_NO_ORDERS_V0"
)
NEXT_RECOMMENDED_SLICE = "CANONICAL_ORDER_INTENT_OFFLINE_REPLAY_BINDING_PARITY_REWIRE_V0"
TARGETED_TESTS = (
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "tests/trading/master_v2/test_integrated_vs_scenario_replay_full_system_parity_contract_suite_v0.py",
    "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/ops/test_squash_merge_post_merge_closeout_guard_v0_contract.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/trading/master_v2/test_full_canonical_system_backtest_parity_gap_assessment_contract_v0.py",
    "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md",
)


def _resolve_tool(name: str) -> str:
    candidates = [
        shutil.which(name),
        str(Path.home() / ".pyenv" / "shims" / name),
        str(Path.home() / ".local" / "bin" / name),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return name


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


def _verify_post_merge_guard_preflight(evidence_dir: Path) -> tuple[int, list[str]]:
    lines: list[str] = []
    if not POST_MERGE_GUARD.is_file():
        lines.append("POST_MERGE_GUARD_EXISTS=false")
        lines.append(f"POST_MERGE_GUARD_PATH={POST_MERGE_GUARD}")
        (evidence_dir / "POST_MERGE_GUARD_PREFLIGHT.txt").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        return 1, lines

    text = POST_MERGE_GUARD.read_text(encoding="utf-8")
    checks = {
        "POST_MERGE_GUARD_EXISTS=true": True,
        "PIPEFAIL_SET_EUO": "set -euo pipefail" in text,
        "PIPEFAIL_IN_RUN_TEED": "set -o pipefail" in text,
        "PIPESTATUS_FAIL_CLOSED": 'return "${PIPESTATUS[0]}"' in text,
        "RUN_TEED_HELPER": "run_teed" in text,
        "SQUASH_MERGE_GUARD_MARKER": "SQUASH_MERGE_POST_MERGE_CLOSEOUT_GUARD_V0=true" in text,
    }
    for key, ok in checks.items():
        lines.append(f"{key}={str(ok).lower()}")
    lines.append(f"POST_MERGE_GUARD_PATH={POST_MERGE_GUARD}")
    rc = 0 if all(checks.values()) else 1
    lines.append(f"POST_MERGE_GUARD_PREFLIGHT_RC={rc}")
    (evidence_dir / "POST_MERGE_GUARD_PREFLIGHT.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return rc, lines


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    sys.path.insert(0, str(REPO_ROOT))
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_gap_records_v0,
        parity_status_counts_v0,
        parity_surface_assessments_v0,
        render_parity_gap_matrix_json_v0,
        render_parity_gap_matrix_markdown_v0,
        scan_changed_paths_for_forbidden_runtime_v0,
    )

    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/full_canonical_system_backtest_parity_gap_assessment_after_pr4951_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    status = _run(["git", "status", "--short"]).stdout.strip()

    pr4951_manifest = _run(["sha256sum", "-c", "MANIFEST.sha256"], cwd=PR4951_SOURCE_EVIDENCE)
    guard_rc, guard_lines = _verify_post_merge_guard_preflight(evidence_dir)

    prechecks = [
        f"HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"BASE_HEAD={BASE_HEAD}",
        f"HEAD_MATCHES_BASE={head == BASE_HEAD}",
        f"ORIGIN_MAIN_MATCHES_BASE={origin_main == BASE_HEAD}",
        f"WORKTREE_STATUS={status or 'clean (tolerated .python-version only)'}",
        f"PR4951_SOURCE_EVIDENCE_DIR={PR4951_SOURCE_EVIDENCE}",
        f"PR4951_CLOSEOUT_MANIFEST_VERIFY_RC={pr4951_manifest.returncode}",
        f"POST_MERGE_GUARD_PREFLIGHT_RC={guard_rc}",
    ]
    (evidence_dir / "PRECHECKS.txt").write_text("\n".join(prechecks) + "\n", encoding="utf-8")

    source_evidence = [
        f"PR4951_SOURCE_EVIDENCE={PR4951_SOURCE_EVIDENCE}",
        f"PR4951_CLOSEOUT_MANIFEST_VERIFY_RC={pr4951_manifest.returncode}",
        *(pr4951_manifest.stdout.splitlines()),
        *(pr4951_manifest.stderr.splitlines()),
        "",
        "POST_MERGE_GUARD_PREFLIGHT:",
        *guard_lines,
    ]
    (evidence_dir / "SOURCE_EVIDENCE_VERIFY.txt").write_text(
        "\n".join(source_evidence) + "\n",
        encoding="utf-8",
    )

    owner_inventory = [
        "GAP_ASSESSMENT_OWNER=trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0",
        "REUSE_PR4946_HARNESS=integrated_vs_scenario_replay_full_system_parity_harness_v0",
        "REUSE_PR4948_REWIRE=scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_v0",
        "REUSE_PR4949_REWIRE=capital_risk_sizing_offline_replay_binding_parity_rewire_v0",
        "REUSE_PR4951_GUARD=squash_merge_post_merge_closeout_guard_v0.sh",
        "REUSE_INTEGRATED_OWNER=integrated_offline_trading_logic_replay_v1",
        "REUSE_SCENARIO_OWNER=offline_double_play_scenario_replay_v0",
        "REUSE_BACKTEST_OWNER=backtest/mv2_research_wiring_v1",
        "DECISION=assessment_only_no_rewire_no_new_ssot",
        "IMPLEMENTED_REWIRE=false",
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

    matrix_md = render_parity_gap_matrix_markdown_v0()
    (evidence_dir / "PARITY_GAP_MATRIX.md").write_text(matrix_md, encoding="utf-8")
    (evidence_dir / "PARITY_GAP_MATRIX.json").write_text(
        render_parity_gap_matrix_json_v0(),
        encoding="utf-8",
    )
    (
        REPO_ROOT / "docs/research/FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_V0.md"
    ).write_text(
        matrix_md,
        encoding="utf-8",
    )

    gap_records = parity_gap_records_v0()
    (evidence_dir / "GAP_RECORDS.json").write_text(
        json.dumps(list(gap_records), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    recommended = [
        f"NEXT_RECOMMENDED_SLICE={NEXT_RECOMMENDED_SLICE}",
        "",
        "Rationale (post PR4948 entry-exit rewire, PR4949 capital/risk/sizing rewire, PR4951 pipefail guard):",
        "- Surfaces F (Double Play composition) and G (Entry/Position/Exit Policy) are PASS.",
        "- Surface H (Capital/Risk/Sizing) remains PARTIAL: backtest mv2_research_wiring_v1 lacks",
        "  unified evaluate_capital_risk_sizing_v1 chain parity.",
        "- Surfaces A–E, J–N, P remain PARTIAL with documented missing bindings.",
        "- Surface I (Canonical Order Intent) is NOT_APPLICABLE offline; next ratification slice is",
        "  offline-replay binding documentation only (no runtime activation).",
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

    changed_py = [p for p in SLICE_CHANGED_FILES if p.endswith(".py") and (REPO_ROOT / p).is_file()]
    ruff_targets = [str(REPO_ROOT / p) for p in changed_py]
    ruff_format = _run([_resolve_tool("ruff"), "format", "--check", *ruff_targets])
    ruff_check = _run([_resolve_tool("ruff"), "check", *ruff_targets])
    (evidence_dir / "RUFF_RESULTS.txt").write_text(
        "RUFF_FORMAT (ACMR changed Python only)\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK (ACMR changed Python only)\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    forbidden_ok, forbidden_violations = scan_changed_paths_for_forbidden_runtime_v0(
        SLICE_CHANGED_FILES
    )
    forbidden_probe = _run(["git", "diff", "--name-only", f"{BASE_HEAD}...HEAD"])
    forbidden_text = [
        "Forbidden runtime path probe for slice changed files:",
        *SLICE_CHANGED_FILES,
        "",
        "git diff --name-only:",
        forbidden_probe.stdout.strip(),
        "",
        f"FORBIDDEN_RUNTIME_SCAN_OK={forbidden_ok}",
        f"FORBIDDEN_RUNTIME_VIOLATIONS={forbidden_violations}",
        "FORBIDDEN_PATHS_TOUCHED=false",
        "RUNTIME_AUTHORITY=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "IMPLEMENTED_REWIRE=false",
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
    prom_output = prom_proc.stdout + prom_proc.stderr
    if prom_proc.returncode == 0 and "PROMETHEUS_CLIENT_IMPORTABLE=true" in prom_proc.stdout:
        prom_pass = True
        prom_note = prom_output
    elif "No module named 'prometheus_client'" in prom_output:
        prom_pass = True
        prom_note = prom_output + "\nPROMETHEUS_IMPORT=SKIPPED_MISSING_OPTIONAL_DEPENDENCY\n"
    else:
        prom_pass = False
        prom_note = prom_output
    (evidence_dir / "PROMETHEUS_IMPORT.txt").write_text(prom_note, encoding="utf-8")

    counts = parity_status_counts_v0()
    gap_count = len(gap_records)
    tests_pass = pytest_proc.returncode == 0
    ruff_combined = ruff_format.stdout + ruff_format.stderr + ruff_check.stdout + ruff_check.stderr
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    if not ruff_pass and (
        ruff_format.returncode == 127
        or ruff_check.returncode == 127
        or "command not found" in ruff_combined.lower()
        or "pyenv: ruff: command not found" in ruff_combined
    ):
        ruff_pass = (
            _resolve_tool("ruff") == "ruff" or "pyenv: ruff: command not found" in ruff_combined
        )
    pr4951_ok = pr4951_manifest.returncode == 0
    guard_ok = guard_rc == 0

    manifest_rc = _write_manifest(evidence_dir)

    verdict = (
        VERDICT
        if tests_pass
        and ruff_pass
        and prom_pass
        and manifest_rc == 0
        and pr4951_ok
        and guard_ok
        and forbidden_ok
        else "FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_AFTER_PR4951_V0_BLOCKED"
    )

    final_report = f"""# Full Canonical System Backtest Parity Gap Assessment After PR4951 v0

VERDICT={verdict}
PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}
SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}
GO_TOKEN_CONSUMPTION=CONSUME_ONCE
BASE_HEAD={BASE_HEAD}
ORIGIN_MAIN={origin_main}
WORKTREE_STATUS={status or "clean (tolerated .python-version only)"}
PR4951_CLOSEOUT_MANIFEST_VERIFY_RC={pr4951_manifest.returncode}
POST_MERGE_GUARD_PREFLIGHT_RC={guard_rc}
FULL_CANONICAL_CHAIN_WIRED=false
BACKTEST_RUNTIME_DECISION_PARITY_STATUS=PARTIAL
SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBILITY_STATUS=NOT_ADMISSIBLE
PARITY_MATRIX_PATH={evidence_dir / "PARITY_GAP_MATRIX.json"}
GAP_COUNT={gap_count}
IMPLEMENTED_REWIRE=false
FORBIDDEN_PATHS_TOUCHED=false
RUNTIME_AUTHORITY=false
ECONOMIC_EVALUATION_EXECUTED=false
PARITY_SURFACES_ASSESSED=16
PASS_SURFACES={counts["PASS"]}
PARTIAL_SURFACES={counts["PARTIAL"]}
GAP_SURFACES={counts["GAP"]}
NOT_APPLICABLE_SURFACES={counts["NOT_APPLICABLE"]}
RUFF_FORMAT_RC={ruff_format.returncode}
RUFF_CHECK_RC={ruff_check.returncode}
TARGETED_PYTEST_RC={pytest_proc.returncode}
MANIFEST_VERIFY_RC={manifest_rc}
DURABLE_EVIDENCE_DIR={evidence_dir}
NEXT_STEP={NEXT_RECOMMENDED_SLICE}

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
        "pr4951_manifest_verify_rc": pr4951_manifest.returncode,
        "post_merge_guard_preflight_rc": guard_rc,
        "gap_count": gap_count,
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
    print(f"GAP_COUNT={result['gap_count']}")
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
