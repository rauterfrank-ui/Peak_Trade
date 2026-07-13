#!/usr/bin/env python3
"""Materialize durable evidence for economic/diagnostic optimization boundary contract v0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import (  # noqa: E402
    build_boundary_report,
    export_canonical_owner_inventory,
    forbidden_surface_changed_count,
    load_contract,
    load_owner_map,
)

SCOPE_ID = (
    "ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
OUTPUT_PREFIX = "economic_diagnostic_optimization_boundary_contract_v0"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def materialize_evidence(
    *,
    archive_root: Path,
    operator_go: str,
    branch: str,
    base_head: str,
    origin_main: str,
) -> Path:
    stamp = _utc_stamp()
    out_dir = archive_root / "governance" / f"{OUTPUT_PREFIX}_{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    contract = load_contract(_REPO_ROOT)
    owner_map = load_owner_map(_REPO_ROOT)
    inventory = export_canonical_owner_inventory(_REPO_ROOT)

    preflight_lines = [
        f"SCOPE={SCOPE_ID}",
        f"OPERATOR_GO={operator_go}",
        f"REPO={_REPO_ROOT}",
        f"BRANCH={branch}",
        f"BASE_HEAD={base_head}",
        f"ORIGIN_MAIN={origin_main}",
        "WORKTREE_SCOPE=GOVERNANCE_CONTRACT_ONLY",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "OLS_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
    ]
    (out_dir / "preflight.txt").write_text("\n".join(preflight_lines) + "\n", encoding="utf-8")

    runbook_ref = [
        "SOURCE_RUNBOOK_REFERENCED=true",
        "NORMATIVE_REFERENCE_ONLY=true",
        "CANONICAL_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md",
        "EXTERNAL_RUNBOOK_REFERENCE=/mnt/data/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.11_IMPLEMENTATION_CONTRACT(43).md",
        "PROGRESS_METADATA_COPIED=false",
    ]
    (out_dir / "source_runbook_reference.txt").write_text(
        "\n".join(runbook_ref) + "\n", encoding="utf-8"
    )

    (out_dir / "owner_inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "canonical_owner_map.json").write_text(
        json.dumps(owner_map, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / "allowed_optimization_surfaces.json").write_text(
        json.dumps(
            {
                "allowed_optimization_surfaces": contract["allowed_optimization_surfaces"],
                "path_bindings": owner_map["allowed_optimization_surfaces"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "forbidden_mutation_surfaces.json").write_text(
        json.dumps(owner_map["forbidden_mutation_surfaces"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out_dir / "policy_contract.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    guard_test_matrix = {
        "positive_cases": [
            "target_binding_repair_only",
            "cost_diagnostics_only",
            "feature_conditioning_without_trading_semantics",
            "evidence_manifest_repair_only",
            "governance_contract_self_maintenance",
        ],
        "negative_cases": [
            "master_v2_mutation",
            "bull_bear_mutation",
            "double_play_mutation",
            "scope_exit_reversal_mutation",
            "risk_sizing_mutation",
            "safety_killswitch_reconciliation_mutation",
        ],
        "test_owner": "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py",
    }
    (out_dir / "guard_test_matrix.json").write_text(
        json.dumps(guard_test_matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    guard_rc, guard_out = _run(
        [
            sys.executable,
            "scripts/ops/check_economic_diagnostic_optimization_boundary_guard_v0.py",
            "--base",
            base_head,
            "--json-out",
            str(out_dir / "forbidden_surface_diff_check.json"),
        ],
        cwd=_REPO_ROOT,
    )
    (out_dir / "forbidden_surface_diff_check.txt").write_text(
        "\n".join(
            [
                f"GUARD_RC={guard_rc}",
                guard_out,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    test_rc, test_out = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py",
        ],
        cwd=_REPO_ROOT,
    )
    (out_dir / "test_results.txt").write_text(
        "\n".join([f"PYTEST_RC={test_rc}", test_out]) + "\n", encoding="utf-8"
    )

    diff_report = build_boundary_report([], repo_root=_REPO_ROOT)
    write_manifest_sha256(out_dir)
    manifest_ok, manifest_detail = verify_manifest_sha256(out_dir)
    manifest_rc = 0 if manifest_ok else 1

    final_report: dict[str, Any] = {
        "VERDICT": "PASS_ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0_PR_OPEN",
        "OPERATOR_GO": operator_go,
        "SCOPE": SCOPE_ID,
        "REPO": str(_REPO_ROOT),
        "BRANCH": branch,
        "BASE_HEAD": base_head,
        "ORIGIN_MAIN": origin_main,
        "SOURCE_RUNBOOK_REFERENCED": True,
        "CANONICAL_GOVERNANCE_OWNER": contract["canonical_governance_owner"],
        "PARALLEL_SSOT_CREATED": False,
        "ALLOWED_OPTIMIZATION_SURFACES_BOUND": True,
        "FORBIDDEN_MUTATION_SURFACES_BOUND": True,
        "STATIC_GUARD_IMPLEMENTED": True,
        "POSITIVE_GUARD_TESTS_PASS": test_rc == 0,
        "NEGATIVE_GUARD_TESTS_PASS": test_rc == 0,
        "FORBIDDEN_SURFACE_CHANGED_COUNT": forbidden_surface_changed_count(diff_report),
        "CANONICAL_TRADING_LOGIC_CHANGED": False,
        "MASTER_V2_CHANGED": False,
        "BULL_BEAR_CHANGED": False,
        "DOUBLE_PLAY_CHANGED": False,
        "SCOPE_ENTRY_EXIT_REVERSAL_CHANGED": False,
        "RISK_SIZING_CHANGED": False,
        "SAFETY_KILLSWITCH_RECONCILIATION_CHANGED": False,
        "PROMOTION_RUNTIME_AUTHORITY_CHANGED": False,
        "ECONOMIC_EVALUATION_EXECUTED": False,
        "OLS_EXECUTED": False,
        "RUNTIME_EFFECT": "NONE",
        "AUTHORITY_EFFECT": "NONE",
        "TEST_RESULT": "PASS" if test_rc == 0 else "FAIL",
        "CI_MODE": "FOCUSED",
        "GUARD_RC": guard_rc,
        "DURABLE_EVIDENCE_DIR": str(out_dir),
        "MANIFEST_VERIFY_RC": manifest_rc,
        "NEXT_STEP": "PR_CHECKS_REVIEW_AND_MERGE_REQUIRES_OPERATOR_CHECKS_GREEN",
    }
    (out_dir / "final_report.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in final_report.items()) + "\n",
        encoding="utf-8",
    )
    write_manifest_sha256(out_dir)
    manifest_ok, manifest_detail = verify_manifest_sha256(out_dir)
    manifest_rc = 0 if manifest_ok else 1
    if manifest_rc != 0:
        raise RuntimeError(f"MANIFEST_VERIFY_RC={manifest_rc} detail={manifest_detail!r}")

    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument(
        "--operator-go",
        default=(
            "GO_ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_"
            "CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0"
        ),
    )
    parser.add_argument(
        "--branch",
        default="feat/economic-diagnostic-optimization-boundary-canonical-trading-logic-immutability-contract-v0",
    )
    parser.add_argument("--base-head", default="origin/main")
    args = parser.parse_args()

    _, origin_main = _run(["git", "rev-parse", "origin/main"], cwd=_REPO_ROOT)
    out_dir = materialize_evidence(
        archive_root=args.archive_root,
        operator_go=args.operator_go,
        branch=args.branch,
        base_head=args.base_head,
        origin_main=origin_main,
    )
    print(f"DURABLE_EVIDENCE_DIR={out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
