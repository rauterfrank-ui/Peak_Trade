#!/usr/bin/env python3
"""Collect durable evidence for backtest canonical order intent state-file wiring v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_BASE_HEAD = "0e41339bf78d8ef65c1afd125f84bcf303a4d843"
DEFAULT_SOURCE_EVIDENCE = (
    DEFAULT_ARCHIVE_ROOT
    / "research/pr_merge_closeout_backtest_capital_risk_sizing_wiring_v0_20260706T230540Z"
)
DEFAULT_RUNBOOK = (
    "/mnt/data/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.4_full_canonical_system_"
    "completion_post_merge_evidence_sync_guard_clarification.md"
)
NEXT_RECOMMENDED_SLICE = "BACKTEST_SAFETY_KERNEL_WIRING_V0"
VERDICT = "BACKTEST_CANONICAL_ORDER_INTENT_WIRING_V0_PASS"
PROCESS_CLASSIFICATION = "FULL_CANONICAL_BACKTEST_PARITY_NARROW_REWIRE"
SCOPE_CLASSIFICATION = (
    "BACKTEST_CANONICAL_ORDER_INTENT_WIRING_V0_NO_RUNTIME_NO_ORDERS_NO_ECONOMIC_EVALUATION_V0"
)
TARGETED_TESTS = (
    "tests/test_backtest_canonical_order_intent_wiring_v0.py",
    "tests/test_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/test_mv2_research_wiring_v1.py",
    "tests/trading/master_v2/test_canonical_order_intent_offline_replay_binding_parity_rewire_contract_v0.py",
    "tests/governance/test_canonical_order_intent_v1.py",
)
SLICE_CHANGED_FILES = (
    "src/trading/master_v2/canonical_order_intent_boundary_backtest_state_file_binding_adapter_v0.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "src/trading/master_v2/full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "scripts/ops/run_backtest_canonical_order_intent_wiring_v0.py",
    "tests/test_backtest_canonical_order_intent_wiring_v0.py",
    "tests/test_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "tests/test_mv2_research_wiring_v1.py",
)
REUSED_OWNERS = (
    "src.governance.canonical_order_intent_v1",
    "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0",
    "trading.master_v2.capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0",
    "backtest.mv2_research_wiring_v1",
)


@dataclass(frozen=True)
class RunConfig:
    repo_root: Path
    durable_root: Path
    runbook_path: str
    scope: str
    base_head: str
    operator: str
    reuse_first: bool
    no_runtime_authority: bool
    no_orders: bool
    no_credentials: bool
    forbid_live: bool
    forbid_scheduler: bool
    require_source_manifest_verify: bool
    require_closeout_manifest: bool
    source_evidence: Path


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
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


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def collect_evidence(config: RunConfig, out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        config.durable_root / f"research/backtest_canonical_order_intent_wiring_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _run(["git", "rev-parse", "HEAD"], cwd=config.repo_root).stdout.strip()
    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=config.repo_root).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"], cwd=config.repo_root).stdout.strip()
    status = _run(["git", "status", "--short"], cwd=config.repo_root).stdout.strip()
    diff_stat = _run(
        ["git", "diff", "--stat", f"{config.base_head}...HEAD"],
        cwd=config.repo_root,
    )

    source_manifest_rc = 0
    source_manifest_log = "SOURCE_EVIDENCE_ABSENT=true\n"
    if config.source_evidence.is_dir():
        source_manifest = _run(
            ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
            cwd=config.source_evidence,
        )
        source_manifest_rc = source_manifest.returncode
        source_manifest_log = (
            source_manifest.stdout
            + source_manifest.stderr
            + f"\nSOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}\n"
        )
    elif config.require_source_manifest_verify:
        source_manifest_rc = 1
        source_manifest_log = "SOURCE_EVIDENCE_PATH_MISSING=true\nSOURCE_MANIFEST_VERIFY_RC=1\n"

    (evidence_dir / "source_manifest_verify_pre_merge.log").write_text(
        source_manifest_log,
        encoding="utf-8",
    )

    (evidence_dir / "git_context.txt").write_text(
        "\n".join(
            [
                f"HEAD={head}",
                f"BRANCH={branch}",
                f"ORIGIN_MAIN={origin_main}",
                f"BASE_HEAD={config.base_head}",
                f"WORKTREE_STATUS={status or 'clean'}",
                f"SOURCE_EVIDENCE={config.source_evidence}",
                f"RUNBOOK={config.runbook_path}",
                f"SCOPE={config.scope}",
                f"OPERATOR={config.operator}",
                f"REUSE_FIRST={config.reuse_first}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(SLICE_CHANGED_FILES) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "reused_owners.txt").write_text(
        "\n".join(REUSED_OWNERS) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "implementation_summary.txt").write_text(
        "\n".join(
            [
                "CANONICAL_ORDER_INTENT_BOUND_TO_BACKTEST=true",
                "ORDER_INTENT_PROVENANCE_REPRESENTED_IN_BACKTEST=true",
                "ADAPTER_COMPATIBLE_REMAINS_FALSE_UNLESS_EXPLICITLY_TRANSFORMED=true",
                "FULL_CANONICAL_CHAIN_WIRED=false",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                f"NO_RUNTIME_AUTHORITY={config.no_runtime_authority}",
                f"NO_ORDERS={config.no_orders}",
                f"NO_CREDENTIALS={config.no_credentials}",
                f"FORBID_LIVE={config.forbid_live}",
                f"FORBID_SCHEDULER={config.forbid_scheduler}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "semantic_flags.txt").write_text(
        (evidence_dir / "implementation_summary.txt").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (evidence_dir / "diff_stat.txt").write_text(
        diff_stat.stdout + diff_stat.stderr, encoding="utf-8"
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(config.repo_root / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    pytest_proc = subprocess.run(
        pytest_cmd,
        cwd=str(config.repo_root),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (evidence_dir / "pytest_targeted_post_merge.log").write_text(
        pytest_proc.stdout + pytest_proc.stderr,
        encoding="utf-8",
    )

    ruff_format = _run(
        ["python3", "-m", "ruff", "format", "--check", *SLICE_CHANGED_FILES],
        cwd=config.repo_root,
    )
    ruff_check = _run(
        ["python3", "-m", "ruff", "check", *SLICE_CHANGED_FILES],
        cwd=config.repo_root,
    )
    (evidence_dir / "ruff_post_merge.log").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    verify_proc = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=evidence_dir)
    (evidence_dir / "MANIFEST_VERIFY.log").write_text(
        verify_proc.stdout
        + verify_proc.stderr
        + f"\nMANIFEST_VERIFY_RC={verify_proc.returncode}\n",
        encoding="utf-8",
    )

    tests_pass = pytest_proc.returncode == 0
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    closeout_ok = manifest_rc == 0
    if config.require_closeout_manifest and manifest_rc != 0:
        closeout_ok = False
    source_ok = source_manifest_rc == 0 or not config.require_source_manifest_verify
    verdict = (
        VERDICT
        if tests_pass and ruff_pass and closeout_ok and source_ok
        else "BACKTEST_CANONICAL_ORDER_INTENT_WIRING_V0_BLOCKED"
    )

    report = "\n".join(
        [
            f"VERDICT={verdict}",
            f"PROCESS_CLASSIFICATION={PROCESS_CLASSIFICATION}",
            f"SCOPE_CLASSIFICATION={SCOPE_CLASSIFICATION}",
            "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
            f"BASE_HEAD={config.base_head}",
            f"ORIGIN_MAIN={origin_main}",
            f"BRANCH={branch}",
            f"COMMIT={head}",
            f"SOURCE_EVIDENCE={config.source_evidence}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
            "CANONICAL_ORDER_INTENT_BOUND_TO_BACKTEST=true",
            "ORDER_INTENT_PROVENANCE_REPRESENTED_IN_BACKTEST=true",
            "ADAPTER_COMPATIBLE_REMAINS_FALSE_UNLESS_EXPLICITLY_TRANSFORMED=true",
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            f"NO_RUNTIME_AUTHORITY={config.no_runtime_authority}",
            f"NO_ORDERS={config.no_orders}",
            f"TESTS={'pass' if tests_pass else 'fail'}",
            f"RUFF={'pass' if ruff_pass else 'fail'}",
            f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            f"MANIFEST_VERIFY_RC={manifest_rc}",
            f"NEXT_STEP={NEXT_RECOMMENDED_SLICE}",
        ]
    )
    (evidence_dir / "FINAL_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    manifest_rc = _write_manifest(evidence_dir)

    return {
        "verdict": verdict,
        "evidence_dir": str(evidence_dir),
        "manifest_rc": manifest_rc,
        "tests_pass": tests_pass,
        "ruff_pass": ruff_pass,
        "source_manifest_rc": source_manifest_rc,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--durable-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--runbook", type=str, default=DEFAULT_RUNBOOK)
    parser.add_argument("--scope", type=str, default="BACKTEST_CANONICAL_ORDER_INTENT_WIRING_V0")
    parser.add_argument("--base-head", type=str, default=DEFAULT_BASE_HEAD)
    parser.add_argument("--operator", type=str, default="")
    parser.add_argument("--source-evidence", type=Path, default=DEFAULT_SOURCE_EVIDENCE)
    parser.add_argument("--reuse-first", type=str, default="true")
    parser.add_argument("--no-runtime-authority", type=str, default="true")
    parser.add_argument("--no-orders", type=str, default="true")
    parser.add_argument("--no-credentials", type=str, default="true")
    parser.add_argument("--forbid-live", type=str, default="true")
    parser.add_argument("--forbid-scheduler", type=str, default="true")
    parser.add_argument(
        "--require-source-manifest-verify",
        type=str,
        default="true",
    )
    parser.add_argument("--require-closeout-manifest", type=str, default="true")
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()

    config = RunConfig(
        repo_root=args.repo_root,
        durable_root=args.durable_root,
        runbook_path=args.runbook,
        scope=args.scope,
        base_head=args.base_head,
        operator=args.operator,
        reuse_first=_parse_bool(args.reuse_first),
        no_runtime_authority=_parse_bool(args.no_runtime_authority),
        no_orders=_parse_bool(args.no_orders),
        no_credentials=_parse_bool(args.no_credentials),
        forbid_live=_parse_bool(args.forbid_live),
        forbid_scheduler=_parse_bool(args.forbid_scheduler),
        require_source_manifest_verify=_parse_bool(args.require_source_manifest_verify),
        require_closeout_manifest=_parse_bool(args.require_closeout_manifest),
        source_evidence=args.source_evidence,
    )
    result = collect_evidence(config, args.out_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] == VERDICT else 1


if __name__ == "__main__":
    raise SystemExit(main())
