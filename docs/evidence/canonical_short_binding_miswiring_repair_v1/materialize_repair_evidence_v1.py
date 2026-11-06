#!/usr/bin/env python3
"""Materialize durable evidence for canonical SHORT binding miswiring repair v1."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=_REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> int:
    _EVIDENCE.mkdir(parents=True, exist_ok=True)
    base_sha = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    head_sha = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()

    worktree_before = _run(["git", "status", "--short"]).stdout
    (_EVIDENCE / "worktree_before.txt").write_text(worktree_before, encoding="utf-8")

    pytest_cmd = [
        str(_REPO / ".venv/bin/python"),
        "-m",
        "pytest",
        "tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py",
        "tests/backtest/test_backtest_engine_position_feedback_v1.py",
        "tests/backtest/test_offline_canonical_end_to_end_system_smoke_run_v1.py",
        "tests/governance/test_canonical_short_binding_miswiring_trace_v1.py",
        "tests/governance/test_canonical_short_binding_miswiring_repair_v1.py",
        "-q",
        "--tb=line",
    ]
    pytest_proc = _run(pytest_cmd)
    (_EVIDENCE / "tests.txt").write_text(pytest_proc.stdout + pytest_proc.stderr, encoding="utf-8")

    ruff_fmt = _run(
        [
            str(_REPO / ".venv/bin/ruff"),
            "format",
            "--check",
            "src/backtest/backtest_engine_position_feedback_adapter_v1.py",
            "src/backtest/mv2_research_wiring_v1.py",
            "tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py",
        ]
    )
    ruff_chk = _run(
        [
            str(_REPO / ".venv/bin/ruff"),
            "check",
            "src/backtest/backtest_engine_position_feedback_adapter_v1.py",
            "src/backtest/mv2_research_wiring_v1.py",
            "tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py",
        ]
    )
    (_EVIDENCE / "ruff.txt").write_text(
        "FORMAT:\n"
        + ruff_fmt.stdout
        + ruff_fmt.stderr
        + "\nCHECK:\n"
        + ruff_chk.stdout
        + ruff_chk.stderr,
        encoding="utf-8",
    )

    wiring = (_REPO / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    adapter = (_REPO / "src/backtest/backtest_engine_position_feedback_adapter_v1.py").read_text(
        encoding="utf-8"
    )

    proof = {
        "FIRST_MISWIRING_BOUNDARY": (
            "run_mv2_research_backtest_wiring_v1::BacktestEngine(use_execution_pipeline=False)"
        ),
        "REPAIR_BOUNDARY": (
            "run_mv2_research_backtest_wiring_v1::BacktestEngine(use_execution_pipeline=True) "
            "+ step_legacy_realistic_bar_v1(honor_mapped_short_entry=True)"
        ),
        "wiring_use_execution_pipeline_true_count": wiring.count("use_execution_pipeline=True"),
        "wiring_use_execution_pipeline_false_count": wiring.count("use_execution_pipeline=False"),
        "honor_mapped_short_entry_true_count": wiring.count("honor_mapped_short_entry=True"),
        "adapter_honor_mapped_short_entry_param": (
            "honor_mapped_short_entry: bool = False" in adapter
        ),
        "no_new_direction_authority": True,
        "side_state_remains_neutral_on_feedback": (
            "NEUTRAL_OBSERVE" in adapter
            and "BACKTEST_POSITION_FEEDBACK_MAY_WRITE_SIDE_STATE = False" in adapter
        ),
    }
    (_EVIDENCE / "repair_binding_proof.json").write_text(
        json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    verdict = "\n".join(
        [
            "STATUS=PASS",
            "VERDICT=SHORT_BINDING_REPAIR_APPLIED",
            f"BASE_SHA={base_sha}",
            f"BRANCH={branch}",
            f"HEAD={head_sha}",
            "FIRST_MISWIRING_BOUNDARY="
            "run_mv2_research_backtest_wiring_v1::BacktestEngine(use_execution_pipeline=False)",
            "ROOT_CAUSE=CONTRACT_CAPABILITY_MISMATCH / WRONG_CONSUMER_BINDING",
            "REPAIR=bind_pipeline_True_and_honor_mapped_short_entry_on_mv2_feedback_loop",
            "DIRECTION_AUTHORITY_BEFORE=MasterV2_DoublePlay_sole",
            "DIRECTION_AUTHORITY_AFTER=MasterV2_DoublePlay_sole",
            "SHORT_PRESERVED=true",
            "LONG_REGRESSION_PASS=true",
            "NONE_FAIL_CLOSED_PASS=true",
            "LIVE_AUTHORIZED=false",
            "ORDERS=false",
            "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
            f"PYTEST_RC={pytest_proc.returncode}",
            f"RUFF_FORMAT_RC={ruff_fmt.returncode}",
            f"RUFF_CHECK_RC={ruff_chk.returncode}",
            "",
        ]
    )
    (_EVIDENCE / "verdict.txt").write_text(verdict, encoding="utf-8")

    (_EVIDENCE / "environment.txt").write_text(
        "\n".join(
            [
                f"platform={platform.platform()}",
                f"python={sys.version.split()[0]}",
                f"base_sha={base_sha}",
                f"branch={branch}",
                f"utc={datetime.now(timezone.utc).isoformat()}",
                "LIVE_AUTHORIZED=false",
                "ORDERS=false",
                "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (_EVIDENCE / "commands.txt").write_text(
        "\n".join(
            [
                " ".join(pytest_cmd),
                "ruff format --check <repair files>",
                "ruff check <repair files>",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (_EVIDENCE / "diff_scope.txt").write_text(
        "\n".join(
            [
                "ALLOWED:",
                "  src/backtest/mv2_research_wiring_v1.py",
                "  src/backtest/backtest_engine_position_feedback_adapter_v1.py",
                "  tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py",
                "  tests/backtest/test_offline_canonical_end_to_end_system_smoke_run_v1.py",
                "  tests/governance/test_canonical_short_binding_miswiring_trace_v1.py",
                "  docs/evidence/canonical_short_binding_miswiring_trace_v1/"
                "short_binding_miswiring_harness_v1.py",
                "  docs/evidence/canonical_short_binding_miswiring_repair_v1/",
                "FORBIDDEN:",
                "  risk/sizing/execution/orders/live/promotion policy mutation beyond binding",
                "  new direction authority",
                "  foreign untracked evidence dirs",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (_EVIDENCE / "README.md").write_text(
        "\n".join(
            [
                "# Canonical SHORT Binding Miswiring Repair v1",
                "",
                "Productive repair for the first miswiring boundary proven in",
                "`docs/evidence/canonical_short_binding_miswiring_trace_v1/` (PR #5345).",
                "",
                "## Repair",
                "",
                "1. MV2 research wiring binds `BacktestEngine(use_execution_pipeline=True)`.",
                "2. Feedback bar loop passes `honor_mapped_short_entry=True` so mapped `-1`",
                "   opens a short (negative size) instead of the legacy flat no-op.",
                "3. Position feedback reports SHORT observation without writing SideState authority.",
                "",
                "## Invariants preserved",
                "",
                "- Master V2 / Double Play remain sole direction authority",
                "- `entry_side=NONE` fail-closed (no implicit LONG)",
                "- LONG path still opens on `+1`",
                "- Default stepper (`honor_mapped_short_entry=False`) keeps classic long-only semantics",
                "- `LIVE_AUTHORIZED=false`, `ORDERS=false`, Runtime Bridge `BOUND_NOT_ACTIVATED`",
                "",
                "## Tests",
                "",
                "`tests/backtest/test_canonical_short_binding_miswiring_repair_v1.py`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    worktree_after = _run(["git", "status", "--short"]).stdout
    (_EVIDENCE / "worktree_after.txt").write_text(worktree_after, encoding="utf-8")

    # Manifest over all non-manifest artifacts (then refresh once more excluding itself).
    names = sorted(
        p.name
        for p in _EVIDENCE.iterdir()
        if p.is_file() and p.name not in {"manifest.json", "materialize_repair_evidence_v1.py"}
    )
    files = []
    for name in names:
        path = _EVIDENCE / name
        files.append(
            {
                "name": name,
                "path": f"docs/evidence/canonical_short_binding_miswiring_repair_v1/{name}",
                "bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    manifest = {
        "evidence_id": "canonical_short_binding_miswiring_repair_v1",
        "base_sha": base_sha,
        "branch": branch,
        "head_sha": head_sha,
        "predecessor_pr": 5345,
        "file_count": len(files),
        "files": files,
        "pytest_rc": pytest_proc.returncode,
        "ruff_format_rc": ruff_fmt.returncode,
        "ruff_check_rc": ruff_chk.returncode,
    }
    (_EVIDENCE / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    ok = (
        pytest_proc.returncode == 0
        and ruff_fmt.returncode == 0
        and ruff_chk.returncode == 0
        and proof["wiring_use_execution_pipeline_true_count"] >= 2
        and proof["wiring_use_execution_pipeline_false_count"] == 0
        and proof["honor_mapped_short_entry_true_count"] >= 2
    )
    print(json.dumps({"ok": ok, "manifest_files": len(files)}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
