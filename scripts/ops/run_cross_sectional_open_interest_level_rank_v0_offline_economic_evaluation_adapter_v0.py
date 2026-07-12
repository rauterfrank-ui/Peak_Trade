#!/usr/bin/env python3
"""Offline economic evaluation adapter runner for cross_sectional_open_interest_level_rank/v0.

Validates binding, panel contract, and evaluation precheck wiring. Does not execute economic
evaluation. Operator GO:
GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_ADAPTER_IMPLEMENTATION_V0
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_adapter_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    GO_TOKEN,
    RUNTIME_EFFECT,
    adapter_result_to_dict,
    run_cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_adapter_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    materialize_versioned_hypothesis_binding_v0,
)

DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SCOPE_CLASSIFICATION = (
    "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_SOURCE_EVIDENCE_INTEGRITY_"
    "RECONCILIATION_AND_OFFLINE_EVALUATION_ADAPTER_IMPLEMENTATION_V0"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_origin_main(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _write_manifest(evidence_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            import hashlib

            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rel = path.relative_to(evidence_dir).as_posix()
            rows.append(f"{digest}  {rel}")
    manifest = evidence_dir / "MANIFEST.sha256"
    manifest.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=evidence_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--materialization-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--go-token", default=GO_TOKEN)
    args = parser.parse_args()

    if args.go_token != GO_TOKEN:
        _die(f"GO_TOKEN_INVALID:{args.go_token}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        args.durable_evidence_root
        / "research"
        / f"cross_sectional_open_interest_level_rank_v0_offline_evaluation_adapter_v0_{ts}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    binding = materialize_versioned_hypothesis_binding_v0()
    result = run_cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_adapter_v0(
        repo_root=args.repo_root,
        materialization_root=args.materialization_root,
        evidence_root=evidence_dir,
        go_token=args.go_token,
        versioned_binding=binding,
    )

    payload = adapter_result_to_dict(result)
    (evidence_dir / "adapter_result.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                f"VERDICT={'PASS' if result.adapter_binding_complete else 'FAIL_CLOSED'}",
                f"SCOPE={SCOPE_CLASSIFICATION}",
                f"ADAPTER_IMPLEMENTED=true",
                f"ECONOMIC_EVALUATION_EXECUTED=false",
                f"AUTHORITY_EFFECT={AUTHORITY_EFFECT}",
                f"RUNTIME_EFFECT={RUNTIME_EFFECT}",
                f"ORIGIN_MAIN={_resolve_origin_main(args.repo_root)}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_rc = _write_manifest(evidence_dir)
    print(json.dumps({**payload, "manifest_verify_rc": manifest_rc}, indent=2, sort_keys=True))
    if not result.adapter_binding_complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
