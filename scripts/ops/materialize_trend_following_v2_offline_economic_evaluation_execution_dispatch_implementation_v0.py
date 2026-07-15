#!/usr/bin/env python3
"""Materialize trend_following v2 offline economic evaluation execution dispatch implementation v0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (  # noqa: E402
    run_trend_following_v2_offline_economic_evaluation_execution_v0 as runner_module,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    verify_source_evidence_manifests_v0,
)

CONFIRM_GO = DISPATCH_IMPLEMENTATION_GO_TOKEN
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
FOCUSED_TEST = (
    "tests/research/"
    "test_trend_following_v2_offline_economic_evaluation_execution_dispatch_implementation_v0.py"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    run_tests: bool = True,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")

    source_ok, source_reasons = verify_source_evidence_manifests_v0()
    source_manifest_rc = 0 if source_ok else 1
    if source_manifest_rc != 0:
        _die(f"ERR:source_manifest_verify_failed:{source_reasons}")

    if run_tests:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", FOCUSED_TEST, "-q", "--tb=short"],
            cwd=_REPO_ROOT,
            check=False,
        )
        if proc.returncode != 0:
            _die(f"ERR:focused_tests_failed:{proc.returncode}")

    result = runner_module.run_execution_dispatch_implementation_v0(
        confirm=confirm,
        durable_evidence_root=durable_evidence_root,
        primary_worktree=primary_worktree,
    )
    final_report = (
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=EXECUTION_DISPATCH_IMPLEMENTATION_COMPLETE",
                "ROOT_CAUSE=AUTHORIZED_EXECUTION_GO_DISPATCH_NOT_BOUND_TO_CANONICAL_OWNER",
                "REPAIR_SCOPE=BOUNDED_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                f"MANIFEST_VERIFY_RC={result['manifest_verify_rc']}",
                f"DURABLE_EVIDENCE_DIR={result['durable_evidence_path']}",
                "NEXT_ADMISSIBLE_SCOPE=GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0",
            ]
        )
        + "\n"
    )
    bundle_dir = Path(result["durable_evidence_path"])
    (bundle_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    print(final_report)
    result["source_manifest_verify_rc"] = source_manifest_rc
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, default=_REPO_ROOT)
    parser.add_argument("--no-tests", action="store_true")
    args = parser.parse_args()
    payload = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        run_tests=not args.no_tests,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
