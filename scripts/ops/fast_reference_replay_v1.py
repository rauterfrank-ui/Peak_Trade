#!/usr/bin/env python3
"""FAST_REFERENCE_REPLAY_V1 — bounded aggregator for existing recovery checks.

AUTHORITY_EFFECT=NONE. Does not trade, authorize live execution, or mutate credentials.
Not a reference framework; thin wrapper around existing ./scripts/pt and ops validators.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

V1_CHECK_IDS: tuple[str, ...] = (
    "runtime_check",
    "import_src",
    "mv2_dp_import",
    "kill_switch_reader_import",
    "orchestrator_pipeline_import",
    "compileall_src_scripts",
    "repo_truth_claims",
    "docs_token_policy",
    "map_currency_generate_check",
    "map_currency_validate",
    "ci_test_selection_smoke",
    "safety_standing_invariants",
)

DEFAULT_PER_CHECK_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    argv: tuple[str, ...]
    timeout_seconds: int = DEFAULT_PER_CHECK_TIMEOUT_SECONDS


@dataclass
class CheckResult:
    check_id: str
    status: str
    duration_seconds: float
    exit_code: int | None = None
    error: str | None = None


def repo_root_from_this_file() -> Path:
    return Path(__file__).resolve().parents[2]


def build_v1_check_specs(repo_root: Path) -> list[CheckSpec]:
    pt = str(repo_root / "scripts/pt")
    specs = [
        CheckSpec("runtime_check", (pt, "runtime-check"), 60),
        CheckSpec("import_src", (pt, "-c", "import src; assert hasattr(src,'__version__')"), 30),
        CheckSpec(
            "mv2_dp_import",
            (
                pt,
                "-c",
                "from trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus; "
                "import trading.master_v2.offline_double_play_scenario_replay_v0 as offline_dp_replay_v0; "
                "print('mv2_dp_import_ok', bool(CompositionStatus), bool(offline_dp_replay_v0))",
            ),
            45,
        ),
        CheckSpec(
            "kill_switch_reader_import",
            (
                pt,
                "-c",
                "from src.risk_layer.kill_switch import KillSwitch; assert KillSwitch is not None",
            ),
            45,
        ),
        CheckSpec(
            "orchestrator_pipeline_import",
            (
                pt,
                "-c",
                "from src.ai_orchestration.orchestrator import Orchestrator; assert Orchestrator is not None",
            ),
            45,
        ),
        CheckSpec("compileall_src_scripts", (pt, "-m", "compileall", "-q", "src", "scripts"), 120),
        CheckSpec("repo_truth_claims", (pt, "scripts/ops/check_repo_truth_claims.py"), 60),
        CheckSpec(
            "docs_token_policy",
            ("bash", "scripts/ops/preflight_docs_token_policy_changed.sh", "origin/main"),
            120,
        ),
        CheckSpec(
            "map_currency_generate_check",
            (
                pt,
                "scripts/ops/current_system_interaction_authority_map_v1.py",
                "generate",
                "--check",
            ),
            120,
        ),
        CheckSpec(
            "map_currency_validate",
            (
                pt,
                "scripts/ops/current_system_interaction_authority_map_v1.py",
                "validate",
                "--diff-base",
                "origin/main",
            ),
            120,
        ),
        CheckSpec(
            "ci_test_selection_smoke",
            (
                pt,
                "scripts/ops/ci_test_selection_v1.py",
                "--files",
                "scripts/pt-bootstrap",
                "tests/ci/test_ci_diff_aware_test_selection_v1.py",
            ),
            60,
        ),
        CheckSpec(
            "safety_standing_invariants",
            (
                pt,
                "-c",
                "from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import LIVE_ENABLED, LIVE_ARMED; "
                "from src.ops.current_productive_eea_universe_inventory_acquisition_v1.constants_v1 import WIRE_SEND_PERMITTED; "
                "from src.ops.deferred_work_recovery_register_contract_v1 import MULTI_FUTURE_RUNTIME_AUTHORIZED, MAX_POSITIONS_EFFECTIVE; "
                "assert LIVE_ENABLED is False and LIVE_ARMED is False and WIRE_SEND_PERMITTED is False; "
                "assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False and int(MAX_POSITIONS_EFFECTIVE)==1; "
                "print('SAFETY_INVARIANTS_OK')",
            ),
            45,
        ),
    ]
    ids = [spec.check_id for spec in specs]
    if ids != list(V1_CHECK_IDS):
        raise RuntimeError(
            "V1 check population drift: build_v1_check_specs does not match V1_CHECK_IDS"
        )
    return specs


def run_subprocess_check(
    spec: CheckSpec,
    *,
    repo_root: Path,
    runner: Callable[..., int] | None = None,
) -> CheckResult:
    t0 = time.monotonic()
    argv = list(spec.argv)
    try:
        if runner is not None:
            exit_code = runner(argv, cwd=repo_root, timeout=spec.timeout_seconds)
        else:
            proc = subprocess.run(
                argv,
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=spec.timeout_seconds,
            )
            exit_code = proc.returncode
        elapsed = time.monotonic() - t0
        if exit_code == 0:
            return CheckResult(spec.check_id, "PASS", round(elapsed, 3), exit_code=0)
        return CheckResult(spec.check_id, "FAIL", round(elapsed, 3), exit_code=exit_code)
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - t0
        return CheckResult(
            spec.check_id,
            "TIMEOUT",
            round(elapsed, 3),
            exit_code=None,
            error=f"TIMEOUT_AFTER_{spec.timeout_seconds}s",
        )


def run_fast_reference_replay_v1(
    repo_root: Path,
    *,
    runner: Callable[..., int] | None = None,
) -> tuple[list[CheckResult], str, float]:
    specs = build_v1_check_specs(repo_root)
    results = [run_subprocess_check(spec, repo_root=repo_root, runner=runner) for spec in specs]
    total = round(sum(r.duration_seconds for r in results), 3)
    if any(r.status == "TIMEOUT" for r in results):
        overall = "FAIL"
    elif any(r.status != "PASS" for r in results):
        overall = "FAIL"
    else:
        overall = "PASS"
    return results, overall, total


def format_human_report(results: list[CheckResult], overall: str, total_seconds: float) -> str:
    lines: list[str] = []
    for result in results:
        lines.append(f"CHECK_NAME={result.check_id}")
        lines.append(f"STATUS={result.status}")
        lines.append(f"DURATION={result.duration_seconds}s")
        if result.error:
            lines.append(f"ERROR={result.error}")
        lines.append("")
    pass_count = sum(1 for r in results if r.status == "PASS")
    fail_count = sum(1 for r in results if r.status == "FAIL")
    timeout_count = sum(1 for r in results if r.status == "TIMEOUT")
    lines.extend(
        [
            f"FAST_REFERENCE_REPLAY_RESULT={overall}",
            f"CHECK_COUNT={len(results)}",
            f"PASS_COUNT={pass_count}",
            f"FAIL_COUNT={fail_count}",
            f"TIMEOUT_COUNT={timeout_count}",
            f"TOTAL_RUNTIME_SECONDS={total_seconds}",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="FAST_REFERENCE_REPLAY_V1 (bounded existing checks)"
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)
    repo_root = (args.repo_root or repo_root_from_this_file()).resolve()
    results, overall, total = run_fast_reference_replay_v1(repo_root)
    sys.stdout.write(format_human_report(results, overall, total))
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
