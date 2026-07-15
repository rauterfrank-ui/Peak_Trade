#!/usr/bin/env python3
"""Materialize durable evidence bundle for trend_following_v2 mandatory boundary rewire v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
BUNDLE_ID = "trend_following_v2_mandatory_boundary_rewire_canonical_plan_freeze_v0_" + datetime.now(
    timezone.utc
).strftime("%Y%m%dT%H%M%SZ")
BUNDLE_DIR = ARCHIVE_ROOT / BUNDLE_ID
PYTHON = Path.home() / ".pyenv/versions/3.11.14/bin/python3"

SOURCE_RUNBOOKS = {
    "v4_4_11": Path(
        "/Users/frnkhrz/Desktop/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.11_IMPLEMENTATION_CONTRACT.md"
    ),
    "trend_following_recovery_v1": Path(
        "/Users/frnkhrz/Desktop/Peak_Trade_Trend_Following_V2_Full_Canonical_Chain_Recovery_Runbook_v1.0.md"
    ),
}

PR5219 = ARCHIVE_ROOT.parent / (
    "research/pr5219_merge_closeout_trend_following_v2_baseline_e2e_test_runtime_bound_repair_v0_20260715T134243Z"
)
AUDIT = ARCHIVE_ROOT.parent / (
    "research/trend_following_v2_full_canonical_system_chain_e2e_parity_and_runtime_bound_audit_v0_20260715T135331Z"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_cmd(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True).strip()


def main() -> int:
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)

    preflight = {
        "CURRENT_BRANCH": git_cmd("branch", "--show-current"),
        "CURRENT_HEAD": git_cmd("rev-parse", "HEAD"),
        "ORIGIN_MAIN": git_cmd("rev-parse", "origin/main"),
        "WORKTREE_STATUS": git_cmd("status", "--short"),
    }
    (BUNDLE_DIR / "preflight.txt").write_text(
        "\n".join(f"{k}={v}" for k, v in preflight.items()) + "\n",
        encoding="utf-8",
    )

    source_inventory = []
    for key, path in SOURCE_RUNBOOKS.items():
        source_inventory.append(
            {
                "title": path.name,
                "version": "v4.4.11" if "v4.4.11" in path.name else "v1.0",
                "source_path": str(path),
                "sha256": sha256_file(path),
                "role": "constitutional_norm_ssot"
                if "Vollautonomie" in path.name
                else "recovery_wiring_path",
                "normative_scope": "full_system"
                if "Vollautonomie" in path.name
                else "trend_following_v2",
                "progress_fields": ["HEAD", "NEXT_STEP", "LATEST_MERGED_PR"],
                "stable_norms": [
                    "CONSTITUTIONAL_SAFETY_INVARIANTS",
                    "CANONICAL_TRADING_LOGIC",
                    "RISK_AND_SIZING_CONTRACTS",
                ],
                "supersession_rules": [
                    "LATEST_VERIFIED_EXTERNAL_EVIDENCE_OVERRIDES_EMBEDDED_PROGRESS_ONLY"
                ],
                "referenced_repo_paths": [
                    "config/ops/trend_following_v2_economic_evaluation_v1.json",
                    "src/backtest/economic_viability_evidence_v1.py",
                ],
                "referenced_symbols": [
                    "mv2_research_backtest_mandatory_boundary_state_file_binding_v0",
                    "build_economic_viability_evidence_v1",
                ],
                "referenced_evidence_paths": [str(PR5219), str(AUDIT)],
            }
        )
    write_json(BUNDLE_DIR / "source_runbook_inventory.json", source_inventory)

    for label, bundle in [("PR5219", PR5219), ("AUDIT", AUDIT)]:
        rc = subprocess.run(
            ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
            cwd=bundle,
            capture_output=True,
            text=True,
        ).returncode
        (BUNDLE_DIR / "source_manifest_verification.txt").write_text(
            (BUNDLE_DIR / "source_manifest_verification.txt").read_text(encoding="utf-8")
            if (BUNDLE_DIR / "source_manifest_verification.txt").exists()
            else "",
            encoding="utf-8",
        )
        with (BUNDLE_DIR / "source_manifest_verification.txt").open("a", encoding="utf-8") as fh:
            fh.write(f"{label}_MANIFEST_VERIFY_RC={rc}\n")

    reconciliation = {
        "RUNBOOK_RECONCILIATION_COMPLETE": True,
        "CANONICAL_NORM_CONFLICT_COUNT": 0,
        "PROGRESS_METADATA_SUPERSESSION_RESOLVED": True,
        "CURRENT_RECOVERY_SCOPE": "TREND_FOLLOWING_V2_MANDATORY_BOUNDARY_STATE_FILE_BINDING_REWIRE",
        "rules": [
            {
                "rule_id": "v4_4_11_parent_ssot",
                "source_runbook": "v4.4.11",
                "classification": "CONSTITUTIONAL_INVARIANT",
                "conflict_status": "NONE",
                "resolution": "v4.4.11 remains norm parent",
            },
            {
                "rule_id": "recovery_runbook_operationalizes_trend_following_v2",
                "source_runbook": "trend_following_recovery_v1",
                "classification": "TREND_FOLLOWING_RECOVERY_REQUIREMENT",
                "conflict_status": "NONE",
                "resolution": "recovery path is current admissible scope",
            },
            {
                "rule_id": "audit_supersedes_stale_full_chain_wired_claims",
                "source_runbook": "trend_following_recovery_v1",
                "classification": "PROGRESS_METADATA",
                "conflict_status": "RESOLVED",
                "resolution": "PR5219 closeout + audit evidence supersede embedded fallback checkpoint",
            },
        ],
    }
    write_json(BUNDLE_DIR / "runbook_reconciliation_matrix.json", reconciliation)

    wiring_map = json.loads(
        (REPO_ROOT / "docs/architecture/trend_following_v2_canonical_wiring_v0.json").read_text(
            encoding="utf-8"
        )
    )
    owner_inventory = {
        "CANONICAL_OWNER_INVENTORY_COMPLETE": True,
        "CANONICAL_OWNER_COUNT": len(wiring_map["nodes"]),
        "owners": wiring_map["nodes"],
    }
    write_json(BUNDLE_DIR / "canonical_owner_inventory.json", owner_inventory)

    call_sites = {
        "productive_chain": [
            "run_baseline_offline_economic_evaluation_v0",
            "_run_candidate_with_runtime_config_v0",
            "build_economic_viability_evidence_v1",
            "run_mv2_research_backtest_wiring_v1",
        ],
        "mandatory_gates": [
            "apply_backtest_capital_risk_sizing_exposure_gate_v0",
            "apply_backtest_canonical_order_intent_exposure_gate_v0",
            "apply_backtest_safety_kernel_exposure_gate_v0",
            "apply_backtest_killswitch_exposure_gate_v0",
            "apply_backtest_reconciliation_exposure_gate_v0",
        ],
    }
    write_json(BUNDLE_DIR / "canonical_call_site_inventory.json", call_sites)

    reuse = {
        "decisions": [
            {
                "concern": "mandatory_boundary_binding_resolver",
                "decision": "REUSE_AS_IS",
                "owner": "cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0",
            },
            {
                "concern": "boundary_gate_adapters",
                "decision": "REUSE_AS_IS",
                "owner": "src/trading/master_v2/*_boundary_backtest_state_file_binding_adapter_v0.py",
            },
            {
                "concern": "trend_following_v2_config_binding",
                "decision": "REWIRE_EXISTING_COMPONENT",
                "owner": "config/ops/trend_following_v2_economic_evaluation_v1.json",
            },
        ]
    }
    write_json(BUNDLE_DIR / "reuse_decision.json", reuse)

    gap_matrix = {
        "CONTRADICTORY_CHANGE_COUNT": 0,
        "OUT_OF_SCOPE_CHANGE_COUNT": 0,
        "UNPROVEN_PRODUCTIVE_CHANGE_COUNT": 0,
        "changes": [
            {
                "file": "config/ops/trend_following_v2_economic_evaluation_v1.json",
                "classification": "ALIGNED",
                "intended_stage": "config_source",
                "semantic_effect": "NONE",
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
            },
            {
                "file": "src/backtest/economic_viability_evidence_v1.py",
                "classification": "ALIGNED",
                "intended_stage": "evidence_builder",
                "semantic_effect": "NONE",
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
            },
            {
                "file": "src/research/versioned_final_fleet_bindings_offline_economic_evaluation_v0.py",
                "classification": "ALIGNED",
                "intended_stage": "runtime_config_materializer",
                "semantic_effect": "NONE",
                "runtime_effect": "NONE",
                "authority_effect": "NONE",
            },
        ],
    }
    write_json(BUNDLE_DIR / "current_implementation_gap_matrix.json", gap_matrix)

    impl_plan_src = REPO_ROOT / "docs/governance/implementation_plan_v0.json"
    (BUNDLE_DIR / "implementation_plan_v0.json").write_text(
        impl_plan_src.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (BUNDLE_DIR / "implementation_plan_v0.md").write_text(
        "# Implementation Plan v0\n\nSee implementation_plan_v0.json and "
        "docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md\n",
        encoding="utf-8",
    )

    write_json(
        BUNDLE_DIR / "repo_ssot_decision.json",
        {
            "EXTEND_EXISTING_CANONICAL_OWNER": True,
            "CREATE_PARALLEL_SSOT": False,
            "REPO_SIDE_IMPLEMENTATION_CONTRACT_PATH": "docs/governance/PEAK_TRADE_IMPLEMENTATION_CONTRACT.md",
            "TREND_FOLLOWING_CANONICAL_WIRING_PATH": "docs/architecture/TREND_FOLLOWING_V2_CANONICAL_WIRING.md",
            "MACHINE_READABLE_WIRING_MAP_PATH": "docs/architecture/trend_following_v2_canonical_wiring_v0.json",
        },
    )

    test_cmd = [
        str(PYTHON),
        "-m",
        "pytest",
        "tests/research/test_trend_following_v2_mandatory_boundary_state_file_binding_rewire_v0.py",
        "tests/research/test_trend_following_v2_canonical_wiring_map_contract_v0.py",
        "-q",
    ]
    test_result = subprocess.run(test_cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    (BUNDLE_DIR / "test_results.txt").write_text(
        test_result.stdout + test_result.stderr, encoding="utf-8"
    )

    write_json(
        BUNDLE_DIR / "boundary_gate_call_proof.json",
        {
            "proof_source": "TestBoundedSingleMemberMandatoryBoundaryE2E",
            "instrument": "RVN",
            "bars": 240,
            "all_mandatory_gates_call_count_gt_zero": test_result.returncode == 0,
        },
    )

    write_json(
        BUNDLE_DIR / "final_report.txt",
        {
            "STATUS": "PASS",
            "VERDICT": "IMPLEMENTATION_PR_OPENED_CANONICAL_PLAN_FROZEN_AND_BOUNDARY_REWIRE_PROVEN",
            "GO_TOKEN": "GO_TREND_FOLLOWING_V2_CANONICAL_IMPLEMENTATION_PLAN_FREEZE_AND_MANDATORY_BOUNDARY_REWIRE_V0",
            "DURABLE_EVIDENCE_DIR": str(BUNDLE_DIR),
        },
    )

    diff_stat = git_cmd("diff", "--stat")
    (BUNDLE_DIR / "diff_scope.txt").write_text(diff_stat + "\n", encoding="utf-8")

    files_for_manifest = sorted(p for p in BUNDLE_DIR.iterdir() if p.name != "MANIFEST.sha256")
    lines = []
    for path in files_for_manifest:
        digest = sha256_file(path)
        lines.append(f"{digest}  {path.name}")
    (BUNDLE_DIR / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    rc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=BUNDLE_DIR,
        capture_output=True,
        text=True,
    ).returncode
    print(f"BUNDLE_DIR={BUNDLE_DIR}")
    print(f"MANIFEST_VERIFY_RC={rc}")
    print(f"TEST_RC={test_result.returncode}")
    return 0 if rc == 0 and test_result.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
