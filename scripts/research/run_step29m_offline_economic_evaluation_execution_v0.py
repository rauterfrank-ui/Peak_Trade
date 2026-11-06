#!/usr/bin/env python3
"""
STEP29M offline economic evaluation execution runner v0.

Offline-only, authority-neutral runner for materialising execution evidence from
the versioned STEP29M execution-plan contract.

This runner intentionally remains fail-closed unless all plan preconditions and
required reusable research capabilities are present. It does not submit orders,
does not use credentials, does not start scheduler/runtime paths, and does not
claim system economic viability by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]

PLAN_JSON = (
    REPO_ROOT
    / "docs/research/step29m_offline_economic_evaluation_execution_plan_separate_operator_go_required_v0.json"
)
PLAN_MD = (
    REPO_ROOT
    / "docs/research/STEP29M_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_PLAN_SEPARATE_OPERATOR_GO_REQUIRED_V0.md"
)

REQUIRED_REUSE_PATHS = [
    "scripts/run_backtest.py",
    "src/backtest/engine.py",
    "src/backtest/walkforward.py",
    "src/experiments/monte_carlo.py",
    "src/experiments/stress_tests.py",
    "src/experiments/portfolio_robustness.py",
    "src/backtest/stats.py",
    "src/experiments/evidence_chain.py",
    "src/experiments/strategy_profiles.py",
    "src/core/experiments.py",
]

AUTHORITY_NEUTRAL = {
    "AUTHORITY_EFFECT": "NONE",
    "RUNTIME_EFFECT": "NONE",
    "LIVE_AUTHORIZED": False,
    "ORDERS_ALLOWED": False,
    "SCHEDULER_RUNTIME_ALLOWED": False,
    "SHADOW_AUTHORIZED": False,
    "PAPER_AUTHORIZED": False,
    "TESTNET_AUTHORIZED": False,
    "CANARY_AUTHORIZED": False,
    "ECONOMIC_EVALUATION_EXECUTED": False,
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
    "RUNTIME_REWIRE_ADMISSIBLE": False,
}


@dataclass(frozen=True)
class RunnerResult:
    verdict: str
    status: str
    reason_codes: List[str]
    plan_digest: str
    git_head: str
    origin_main_head: str
    required_reuse_paths_present: bool
    missing_reuse_paths: List[str]
    generated_files: List[str]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_git(args: Sequence[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def _load_plan() -> Dict[str, Any]:
    if not PLAN_JSON.exists():
        raise FileNotFoundError(f"missing plan contract: {PLAN_JSON}")
    data = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("plan contract must be a JSON object")
    return data


def _extract_boolish(mapping: Mapping[str, Any], key: str) -> bool | None:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower == "true":
            return True
        if lower == "false":
            return False
    return None


def _walk_values(obj: Any) -> Iterable[Any]:
    if isinstance(obj, dict):
        for value in obj.values():
            yield value
            yield from _walk_values(value)
    elif isinstance(obj, list):
        for value in obj:
            yield value
            yield from _walk_values(value)


def _plan_has_forbidden_executed_flags(plan: Mapping[str, Any]) -> List[str]:
    failures: List[str] = []
    for key, value in plan.items():
        if key.endswith("_executed") and value is not False:
            failures.append(key)
    for value in _walk_values(plan):
        if isinstance(value, dict):
            for key, inner in value.items():
                if isinstance(key, str) and key.endswith("_executed") and inner is not False:
                    failures.append(key)
    return sorted(set(failures))


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest(out_dir: Path) -> int:
    manifest = out_dir / "MANIFEST.sha256"
    rows: List[str] = []
    for path in sorted(
        p for p in out_dir.rglob("*") if p.is_file() and p.name != "MANIFEST.sha256"
    ):
        rel = path.relative_to(out_dir)
        rows.append(f"{_sha256_file(path)}  {rel.as_posix()}")
    manifest.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")

    verify = out_dir / "manifest_verify.txt"
    errors: List[str] = []
    for row in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = row.split("  ", 1)
        actual = _sha256_file(out_dir / rel)
        if actual != digest:
            errors.append(f"FAILED {rel}: expected={digest} actual={actual}")
    if errors:
        verify.write_text("\n".join(errors) + "\n", encoding="utf-8")
        return 1
    verify.write_text("MANIFEST_VERIFY_RC=0\n", encoding="utf-8")
    return 0


def run(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)

    reason_codes: List[str] = []
    generated_files: List[str] = []

    try:
        git_head = _run_git(["rev-parse", "HEAD"])
        origin_main_head = _run_git(["rev-parse", "origin/main"])
    except Exception as exc:  # pragma: no cover - defensive CLI reporting
        git_head = "UNKNOWN"
        origin_main_head = "UNKNOWN"
        reason_codes.append(f"GIT_CONTEXT_UNAVAILABLE:{exc}")

    try:
        plan = _load_plan()
    except Exception as exc:
        failure = {
            "created_at": _utc_now(),
            "verdict": "FAIL_CLOSED_STEP29M_PLAN_CONTRACT_UNAVAILABLE",
            "status": "FAIL_CLOSED",
            "reason_codes": [str(exc)],
            **AUTHORITY_NEUTRAL,
        }
        _write_json(out_dir / "step29m_execution_result_v0.json", failure)
        (out_dir / "final_report.txt").write_text(
            "VERDICT=FAIL_CLOSED_STEP29M_PLAN_CONTRACT_UNAVAILABLE\n"
            "AUTHORITY_EFFECT=NONE\n"
            "RUNTIME_EFFECT=NONE\n",
            encoding="utf-8",
        )
        return 2

    plan_digest = _sha256_file(PLAN_JSON)
    if PLAN_MD.exists():
        generated_files.append(str(PLAN_MD.relative_to(REPO_ROOT)))

    forbidden_executed = _plan_has_forbidden_executed_flags(plan)
    if forbidden_executed:
        reason_codes.append("PLAN_CONTAINS_PRE_EXECUTED_FLAGS_NOT_FALSE")

    missing = [path for path in REQUIRED_REUSE_PATHS if not (REPO_ROOT / path).exists()]
    required_present = not missing
    if missing:
        reason_codes.append("REQUIRED_REUSE_CAPABILITY_PATHS_MISSING")

    full_chain = bool(plan.get("FULL_CANONICAL_CHAIN_WIRED", False))
    parity = bool(plan.get("BACKTEST_RUNTIME_DECISION_PARITY_PASS", False))
    costs = bool(plan.get("REALISTIC_COSTS_BOUND", False))
    robustness = bool(plan.get("ROBUSTNESS_EVIDENCE_PASS", False))

    admissible = full_chain and parity and costs and robustness
    if not admissible:
        reason_codes.append("SYSTEM_ECONOMIC_EVIDENCE_NOT_ADMISSIBLE_FROM_PLAN_PRECONDITIONS")

    execution_payload = {
        "created_at": _utc_now(),
        "runner": "scripts/research/run_step29m_offline_economic_evaluation_execution_v0.py",
        "plan_json": str(PLAN_JSON.relative_to(REPO_ROOT)),
        "plan_digest": plan_digest,
        "git_head": git_head,
        "origin_main_head": origin_main_head,
        "head_equals_origin_main": git_head == origin_main_head,
        "required_reuse_paths": REQUIRED_REUSE_PATHS,
        "missing_reuse_paths": missing,
        "required_reuse_paths_present": required_present,
        "preconditions": {
            "FULL_CANONICAL_CHAIN_WIRED": full_chain,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": parity,
            "REALISTIC_COSTS_BOUND": costs,
            "ROBUSTNESS_EVIDENCE_PASS": robustness,
        },
        "admissibility": {
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": admissible,
            "ECONOMIC_EVALUATION_AUTHORIZED": admissible,
            "RUNTIME_REWIRE_ADMISSIBLE": False,
        },
        "execution_chain": {
            "offline_backtest_executed": False,
            "walk_forward_executed": False,
            "monte_carlo_executed": False,
            "stress_executed": False,
            "economic_viability_evidence_emitted": False,
        },
        "authority": AUTHORITY_NEUTRAL,
        "status": "FAIL_CLOSED" if reason_codes else "READY_FAIL_CLOSED_NO_EVAL_CLAIM",
        "verdict": (
            "FAIL_CLOSED_STEP29M_EXECUTION_PRECONDITIONS_NOT_ADMISSIBLE"
            if reason_codes
            else "PASS_STEP29M_VERSIONED_EXECUTION_RUNNER_PREFLIGHT_READY_NO_ECONOMIC_CLAIM"
        ),
        "reason_codes": reason_codes,
    }

    result_path = out_dir / "step29m_execution_result_v0.json"
    _write_json(result_path, execution_payload)
    generated_files.append(str(result_path.relative_to(out_dir)))

    report_lines = [
        f"VERDICT={execution_payload['verdict']}",
        f"STATUS={execution_payload['status']}",
        f"PLAN_DIGEST={plan_digest}",
        f"GIT_HEAD={git_head}",
        f"ORIGIN_MAIN_HEAD={origin_main_head}",
        f"HEAD_EQUALS_ORIGIN_MAIN={str(git_head == origin_main_head).lower()}",
        f"REQUIRED_REUSE_PATHS_PRESENT={str(required_present).lower()}",
        f"MISSING_REUSE_PATHS={','.join(missing) if missing else 'NONE'}",
        f"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE={str(admissible).lower()}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "OFFLINE_BACKTEST_EXECUTED=false",
        "WALK_FORWARD_EXECUTED=false",
        "MONTE_CARLO_EXECUTED=false",
        "STRESS_EXECUTED=false",
        "ECONOMIC_VIABILITY_EVIDENCE_EMITTED=false",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_EFFECT=NONE",
        "ORDERS_ALLOWED=false",
        "SCHEDULER_RUNTIME_ALLOWED=false",
        "LIVE_AUTHORIZED=false",
        f"REASON_CODES={','.join(reason_codes) if reason_codes else 'NONE'}",
    ]
    (out_dir / "final_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    manifest_rc = _manifest(out_dir)
    return 0 if manifest_rc == 0 else 3


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run STEP29M offline economic evaluation execution v0 preflight."
    )
    parser.add_argument("--out", required=True, help="Durable evidence output directory")
    args = parser.parse_args(argv)
    return run(Path(args.out).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
