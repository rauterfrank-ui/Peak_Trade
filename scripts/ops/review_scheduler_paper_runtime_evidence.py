#!/usr/bin/env python3
"""Review bounded scheduler paper-runtime evidence without running anything."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

PASS = "PASS"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REVIEW_REQUIRED_EXIT = 1
USAGE_EXIT = 2

ACCOUNT_FILE = "account.json"
FILLS_FILE = "fills.json"
MANIFEST_FILE = "evidence_manifest.json"
STDOUT_FILE = "scheduler_stdout.log"
STDERR_FILE = "scheduler_stderr.log"

TIMEOUT_RE = re.compile(
    r"run_with_timeout:\s*exceeded\s+--timeout-seconds=(?P<seconds>[0-9]+(?:\.[0-9]+)?)"
)


def _consume_argv(argv: list[str] | None) -> list[str]:
    if argv is None:
        return sys.argv[1:]
    if argv and not argv[0].startswith("-"):
        return list(argv[1:])
    return list(argv)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"{path.name} is not valid JSON: {exc}"


def _json_contains_string(value: Any, needle: str) -> bool:
    if isinstance(value, str):
        return value == needle
    if isinstance(value, dict):
        return any(_json_contains_string(v, needle) for v in value.values())
    if isinstance(value, list):
        return any(_json_contains_string(v, needle) for v in value)
    return False


def _timeout_observed(stderr_text: str, expected_timeout_seconds: float) -> bool:
    for match in TIMEOUT_RE.finditer(stderr_text):
        try:
            observed = float(match.group("seconds"))
        except ValueError:
            continue
        if math.isclose(observed, expected_timeout_seconds, rel_tol=0.0, abs_tol=1e-9):
            return True
    return False


def _fills_count(data: Any) -> int | None:
    if isinstance(data, dict) and isinstance(data.get("fills"), list):
        return len(data["fills"])
    if isinstance(data, list):
        return len(data)
    return None


def _account_cash(data: Any) -> int | float | None:
    if not isinstance(data, dict):
        return None
    cash = data.get("cash")
    if isinstance(cash, bool) or not isinstance(cash, (int, float)):
        return None
    return cash


def _positions_count(data: Any) -> int | None:
    if not isinstance(data, dict):
        return None
    positions = data.get("positions")
    if not isinstance(positions, dict):
        return None
    return len(positions)


def review_evidence(
    *,
    outroot: Path,
    logroot: Path,
    expected_timeout_seconds: float,
) -> dict[str, Any]:
    issues: list[str] = []
    outroot = outroot.expanduser()
    logroot = logroot.expanduser()

    paths = {
        "account": outroot / ACCOUNT_FILE,
        "fills": outroot / FILLS_FILE,
        "manifest": outroot / MANIFEST_FILE,
        "stdout": logroot / STDOUT_FILE,
        "stderr": logroot / STDERR_FILE,
    }

    if not outroot.is_dir():
        issues.append(f"outroot does not exist or is not a directory: {outroot}")
    if not logroot.is_dir():
        issues.append(f"logroot does not exist or is not a directory: {logroot}")

    for path in paths.values():
        if not path.is_file():
            issues.append(f"missing required file: {path}")

    account_json: Any | None = None
    fills_json: Any | None = None
    manifest_json: Any | None = None

    if paths["account"].is_file():
        account_json, error = _load_json(paths["account"])
        if error:
            issues.append(error)
    if paths["fills"].is_file():
        fills_json, error = _load_json(paths["fills"])
        if error:
            issues.append(error)
    if paths["manifest"].is_file():
        manifest_json, error = _load_json(paths["manifest"])
        if error:
            issues.append(error)

    fills_count = _fills_count(fills_json)
    account_cash = _account_cash(account_json)
    positions_count = _positions_count(account_json)

    if fills_json is not None and fills_count is None:
        issues.append("fills_count is not parseable")
    if account_json is not None and account_cash is None:
        issues.append("account_cash is not parseable")
    if account_json is not None and positions_count is None:
        issues.append("positions_count is not parseable")

    stdout_bytes = paths["stdout"].stat().st_size if paths["stdout"].is_file() else None
    stderr_bytes = paths["stderr"].stat().st_size if paths["stderr"].is_file() else None

    stderr_text = ""
    if paths["stderr"].is_file():
        stderr_text = paths["stderr"].read_text(encoding="utf-8", errors="replace")
    timeout_observed = _timeout_observed(stderr_text, expected_timeout_seconds)
    if not timeout_observed:
        issues.append(
            "scheduler_stderr.log does not contain matching run_with_timeout timeout semantics"
        )

    manifest_references_computed_hashes = False
    computed_hashes: dict[str, str] = {}
    if paths["account"].is_file() and paths["fills"].is_file():
        computed_hashes = {
            ACCOUNT_FILE: _sha256(paths["account"]),
            FILLS_FILE: _sha256(paths["fills"]),
        }
    if manifest_json is not None and computed_hashes:
        manifest_references_computed_hashes = all(
            _json_contains_string(manifest_json, digest) for digest in computed_hashes.values()
        )
    if manifest_json is not None and not manifest_references_computed_hashes:
        issues.append("evidence_manifest.json does not reference computed account/fills sha256")

    metrics = {
        "fills_count": fills_count,
        "account_cash": account_cash,
        "positions_count": positions_count,
        "stdout_bytes": stdout_bytes,
        "stderr_bytes": stderr_bytes,
        "timeout_observed": timeout_observed,
        "manifest_references_computed_hashes": manifest_references_computed_hashes,
    }
    verdict = (
        PASS
        if not issues and all(value is not None for value in metrics.values())
        else REVIEW_REQUIRED
    )

    return {
        "verdict": verdict,
        "metrics": metrics,
        "issues": issues,
        "computed_hashes": computed_hashes,
        "inputs": {
            "outroot": str(outroot),
            "logroot": str(logroot),
            "expected_timeout_seconds": expected_timeout_seconds,
        },
    }


def _print_human(result: dict[str, Any]) -> None:
    print(f"VERDICT: {result['verdict']}")
    print("METRICS:")
    for key, value in result["metrics"].items():
        print(f"  {key}: {value}")
    if result["issues"]:
        print("issues:")
        for issue in result["issues"]:
            print(f"  - {issue}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review scheduler paper-runtime evidence files without executing runtime paths."
    )
    parser.add_argument("--outroot", type=Path, required=True)
    parser.add_argument("--logroot", type=Path, required=True)
    parser.add_argument("--expected-timeout-seconds", type=float, required=True)
    parser.add_argument("--json", action="store_true", dest="json_output")

    try:
        args = parser.parse_args(_consume_argv(argv))
    except SystemExit:
        return USAGE_EXIT

    if args.expected_timeout_seconds <= 0:
        print(
            "review_scheduler_paper_runtime_evidence: --expected-timeout-seconds must be > 0",
            file=sys.stderr,
        )
        return USAGE_EXIT

    outroot = args.outroot.expanduser().resolve()
    logroot = args.logroot.expanduser().resolve()
    if not outroot.is_dir() or not logroot.is_dir():
        print(
            "review_scheduler_paper_runtime_evidence: "
            "--outroot and --logroot must exist as directories",
            file=sys.stderr,
        )
        return USAGE_EXIT

    result = review_evidence(
        outroot=outroot,
        logroot=logroot,
        expected_timeout_seconds=args.expected_timeout_seconds,
    )

    if args.json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        _print_human(result)

    return 0 if result["verdict"] == PASS else REVIEW_REQUIRED_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
