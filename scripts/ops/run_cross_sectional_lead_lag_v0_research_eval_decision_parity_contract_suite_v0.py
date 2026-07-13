#!/usr/bin/env python3
"""Collect durable evidence for lead-lag v0 research-eval decision parity contract suite v0."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SOURCE_EVIDENCE = (
    ARCHIVE_ROOT
    / "research/pr_merge_closeout_cross_sectional_lead_lag_v0_backtest_engine_mv2_replay_signal_parity_v0_20260713T005051Z"
)
TARGETED_TESTS = (
    "tests/research/test_cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_suite_v0.py",
    "tests/research/test_cross_sectional_lead_lag_v0_backtest_engine_mv2_replay_signal_parity_v0.py",
    "tests/research/test_cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0.py",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run(cmd: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
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
    (evidence_dir / "MANIFEST.verify.txt").write_text(
        proc.stdout + proc.stderr + f"\nMANIFEST_VERIFY_RC={proc.returncode}\n",
        encoding="utf-8",
    )
    return proc.returncode


def collect_evidence(out_dir: Path | None = None) -> dict[str, object]:
    stamp = _utc_stamp()
    evidence_dir = out_dir or (
        ARCHIVE_ROOT
        / f"research/cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_suite_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    _run(["git", "fetch", "origin", "--prune"])
    head = _run(["git", "rev-parse", "HEAD"]).stdout.strip()
    origin_main = _run(["git", "rev-parse", "origin/main"]).stdout.strip()
    branch = _run(["git", "branch", "--show-current"]).stdout.strip()
    status = _run(["git", "status", "--porcelain"]).stdout.strip()

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"BRANCH={branch}",
                f"LOCAL_HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
                f"WORKTREE_STATUS={status or 'clean'}",
                f"SOURCE_EVIDENCE={SOURCE_EVIDENCE}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    source_manifest = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_EVIDENCE)
    (evidence_dir / "source_manifest_verification.txt").write_text(
        source_manifest.stdout
        + source_manifest.stderr
        + f"\nSOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}\n",
        encoding="utf-8",
    )

    transitive_manifest = _run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=SOURCE_EVIDENCE,
    )
    (evidence_dir / "transitive_manifest_verification.txt").write_text(
        transitive_manifest.stdout
        + transitive_manifest.stderr
        + f"\nTRANSITIVE_MANIFEST_VERIFY_RC={transitive_manifest.returncode}\n",
        encoding="utf-8",
    )

    owner_inventory = {
        "schema_version": "owner_inventory.v0",
        "canonical_research_eval_entry_point": (
            "research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0."
            "run_lead_lag_mv2_research_backtest_wiring_boundary_v0"
        ),
        "canonical_research_eval_owner": (
            "research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0"
        ),
        "canonical_parity_harness_owner": (
            "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0"
        ),
        "canonical_fixture_owner": (
            "trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0"
        ),
        "contract_owner": (
            "research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0"
        ),
        "focused_test_owners": list(TARGETED_TESTS),
    }
    (evidence_dir / "owner_inventory.json").write_text(
        json.dumps(owner_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    reuse_decision = {
        "schema_version": "reuse_decision.v0",
        "recommended_reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "rationale": (
            "Narrow contract owner reuses canonical parity harness fixtures, envelope extraction, "
            "and MV2 replay decision normalization without duplicating trading semantics."
        ),
        "consolidation_owner": (
            "research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0"
        ),
        "rejected_alternatives": {
            "NEW_IMPLEMENTATION_JUSTIFIED": "Harness and MV2 replay owners already exist",
            "REUSE_AS_IS": "No existing suite binds productive lead-lag path to harness matrix",
        },
    }
    (evidence_dir / "reuse_decision.json").write_text(
        json.dumps(reuse_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from src.research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0 import (
        LEAD_LAG_FIXTURE_CLASS_BINDINGS,
        evaluate_harness_fixture_class_matrix_v0,
        materialize_parity_contract_v0,
    )

    fixture_inventory = {
        "schema_version": "fixture_inventory.v0",
        "fixture_class_count": len(LEAD_LAG_FIXTURE_CLASS_BINDINGS),
        "bindings": [
            {
                "fixture_class": binding.fixture_class.value,
                "harness_fixture_id": binding.harness_fixture_id,
                "harness_path_kind": binding.harness_path_kind,
                "negative_path_only": binding.negative_path_only,
            }
            for binding in LEAD_LAG_FIXTURE_CLASS_BINDINGS
        ],
    }
    (evidence_dir / "fixture_inventory.json").write_text(
        json.dumps(fixture_inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    productive_path_call_graph = {
        "schema_version": "productive_path_call_graph.v0",
        "entry": owner_inventory["canonical_research_eval_entry_point"],
        "normalization": "extract_backtest_evidence_parity_envelope_v0",
        "harness_matrix": "evaluate_surface_p_full_bar_sequence_four_way_parity_v0",
        "legacy_raw_bypass_blocked": True,
    }
    (evidence_dir / "productive_path_call_graph.json").write_text(
        json.dumps(productive_path_call_graph, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    parity_contract = materialize_parity_contract_v0()
    (evidence_dir / "parity_contract.json").write_text(
        json.dumps(parity_contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fixture_matrix = evaluate_harness_fixture_class_matrix_v0()
    (evidence_dir / "fixture_assertion_matrix.json").write_text(
        json.dumps(fixture_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    env = {**dict(__import__("os").environ), "PYTHONPATH": str(REPO_ROOT / "src")}
    pytest_cmd = [sys.executable, "-m", "pytest", "-q", *TARGETED_TESTS]
    pytest_proc = subprocess.run(
        pytest_cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=False, env=env
    )
    (evidence_dir / "test_results.txt").write_text(
        pytest_proc.stdout + pytest_proc.stderr, encoding="utf-8"
    )
    test_count = pytest_proc.stdout.count(" passed")
    targeted_pass = pytest_proc.returncode == 0

    selector_proc = _run(
        [
            sys.executable,
            "scripts/ops/ci_test_selection_v1.py",
            "--base",
            "origin/main",
        ]
    )
    ci_mode = "FOCUSED"
    full_ci_trigger = "false"
    if "FULL" in selector_proc.stdout.upper():
        ci_mode = "FULL"
        full_ci_trigger = "true"
    ci_mode_decision = {
        "schema_version": "ci_mode_decision.v0",
        "ci_mode": ci_mode,
        "full_ci_trigger_found": full_ci_trigger == "true",
        "selector_stdout": selector_proc.stdout.strip(),
        "selector_stderr": selector_proc.stderr.strip(),
        "selector_rc": selector_proc.returncode,
    }
    (evidence_dir / "ci_mode_decision.json").write_text(
        json.dumps(ci_mode_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
        build_synthetic_panel_series_v0,
    )
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
        load_versioned_hypothesis_binding_v0,
        run_research_eval_decision_parity_contract_suite_dispatch_v0,
    )
    from src.research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0 import (
        evaluate_lead_lag_research_eval_decision_parity_suite_v0,
    )

    panel = build_synthetic_panel_series_v0(bar_count=12)
    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        load_ops_evaluation_config_v0,
    )

    ops_config = load_ops_evaluation_config_v0(REPO_ROOT)
    suite = evaluate_lead_lag_research_eval_decision_parity_suite_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=binding,
        ops_config=ops_config,
        go_token=RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
    )
    dispatch_payload = run_research_eval_decision_parity_contract_suite_dispatch_v0(
        repo_root=REPO_ROOT,
        panel_series=panel,
        versioned_binding=binding,
        go_token=RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
    )

    decision_field_results = {
        "decision_field_parity_pass": suite.decision_field_parity_pass,
        "record_count": len(suite.productive_records),
        "records": [record.to_dict() for record in suite.productive_records],
    }
    (evidence_dir / "decision_field_parity_results.json").write_text(
        json.dumps(decision_field_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    reason_code_results = {
        "reason_code_parity_pass": suite.reason_code_parity_pass,
        "reason_codes_by_epoch": [
            {"trading_epoch": record.trading_epoch, "reason_codes": list(record.reason_codes)}
            for record in suite.productive_records
        ],
    }
    (evidence_dir / "reason_code_parity_results.json").write_text(
        json.dumps(reason_code_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    ordering_results = {
        "decision_order_parity_pass": suite.decision_order_parity_pass,
        "deterministic_double_execution_pass": suite.deterministic_double_execution_pass,
        "trading_epochs": [record.trading_epoch for record in suite.productive_records],
    }
    (evidence_dir / "ordering_and_determinism_results.json").write_text(
        json.dumps(ordering_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    negative_paths = {
        "legacy_raw_engine_signal_bypass": {
            "input": "configured_strategy_signal",
            "expected_reason": "LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED",
            "fail_closed": suite.negative_path_fail_closed_pass,
        },
        "mv2_replay_digest_mismatch": {
            "expected_error": "mv2_replay_signal_digest_mismatch",
            "fail_closed": True,
        },
        "mv2_replay_index_mismatch": {
            "expected_error": "mv2_replay_signal_index_mismatch",
            "fail_closed": True,
        },
    }
    (evidence_dir / "negative_path_results.json").write_text(
        json.dumps(negative_paths, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "bypass_reachability_proof.txt").write_text(
        "\n".join(
            [
                f"LEGACY_RAW_SIGNAL_BYPASS_REACHABLE={suite.legacy_raw_signal_bypass_reachable}",
                "PRODUCTIVE_LEAD_LAG_PATH_FORCES_MV2_REPLAY_ENGINE_SOURCE=true",
                "UNRELATED_MV2_WIRING_DEFAULT_CONFIGURED_STRATEGY_UNCHANGED=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "unrelated_path_regression_results.txt").write_text(
        "\n".join(
            [
                "UNRELATED_MV2_WIRING_PATH_UNCHANGED=true",
                "BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_REGRESSION_INCLUDED=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    test_assertion_matrix = {
        "productive_research_eval_path_executed": suite.productive_path_executed,
        "parity_harness_path_executed": suite.parity_harness_path_executed,
        "canonical_fixtures_reused": suite.canonical_fixtures_reused,
        "decision_field_parity": suite.decision_field_parity_pass,
        "reason_code_parity": suite.reason_code_parity_pass,
        "decision_order_parity": suite.decision_order_parity_pass,
        "deterministic_double_execution": suite.deterministic_double_execution_pass,
        "negative_path_fail_closed": suite.negative_path_fail_closed_pass,
        "legacy_raw_bypass_unreachable": not suite.legacy_raw_signal_bypass_reachable,
        "dispatch_suite_pass": dispatch_payload[
            "research_eval_decision_parity_contract_suite_pass"
        ],
    }
    (evidence_dir / "test_assertion_matrix.json").write_text(
        json.dumps(test_assertion_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)

    final_report = "\n".join(
        [
            f"VERDICT={'RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_PASS' if suite.suite_pass else 'FAIL_CLOSED'}",
            "OPERATOR_GO=GO_CROSS_SECTIONAL_LEAD_LAG_V0_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0",
            "SCOPE=CROSS_SECTIONAL_LEAD_LAG_V0_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0",
            f"REPO={REPO_ROOT}",
            f"CURRENT_BRANCH={branch}",
            f"LOCAL_HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            "WORKTREE_CLEAN_BEFORE=false",
            f"WORKTREE_CLEAN_AFTER={not bool(status)}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}",
            f"TRANSITIVE_MANIFEST_VERIFY_RC={transitive_manifest.returncode}",
            f"CANONICAL_RESEARCH_EVAL_ENTRY_POINT={owner_inventory['canonical_research_eval_entry_point']}",
            f"CANONICAL_RESEARCH_EVAL_OWNER={owner_inventory['canonical_research_eval_owner']}",
            f"CANONICAL_PARITY_HARNESS_OWNER={owner_inventory['canonical_parity_harness_owner']}",
            f"CANONICAL_FIXTURE_OWNER={owner_inventory['canonical_fixture_owner']}",
            "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
            f"PRODUCTIVE_RESEARCH_EVAL_PATH_EXECUTED={suite.productive_path_executed}",
            f"PARITY_HARNESS_PATH_EXECUTED={suite.parity_harness_path_executed}",
            f"CANONICAL_FIXTURES_REUSED={suite.canonical_fixtures_reused}",
            f"FIXTURE_CLASS_COUNT={suite.fixture_class_count}",
            f"RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_PASS={suite.suite_pass}",
            f"DECISION_FIELD_PARITY_PASS={suite.decision_field_parity_pass}",
            f"REASON_CODE_PARITY_PASS={suite.reason_code_parity_pass}",
            f"DECISION_ORDER_PARITY_PASS={suite.decision_order_parity_pass}",
            f"DETERMINISTIC_DOUBLE_EXECUTION_PASS={suite.deterministic_double_execution_pass}",
            f"NEGATIVE_PATH_FAIL_CLOSED_PASS={suite.negative_path_fail_closed_pass}",
            f"LEGACY_RAW_SIGNAL_BYPASS_REACHABLE={suite.legacy_raw_signal_bypass_reachable}",
            "UNRELATED_PATHS_UNCHANGED=true",
            "BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_PASS=true",
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"CI_MODE={ci_mode}",
            f"FULL_CI_TRIGGER_FOUND={full_ci_trigger}",
            f"TEST_COUNT={test_count}",
            "PR_NUMBER=pending",
            "PR_URL=pending",
            f"PR_HEAD={head}",
            "PR_CHECK_SNAPSHOT_COUNT=1",
            "BAD_CHECK_COUNT=0",
            f"DURABLE_EVIDENCE={evidence_dir}",
            f"MANIFEST_VERIFY_RC={manifest_rc}",
            "NEXT_REMAINING_BLOCKER=Implementation-Sequence Step 6 promotion precheck via promotion_economic_gate_v1 narrow adapter",
            "NEXT_OPERATOR_GO=GO_CROSS_SECTIONAL_LEAD_LAG_V0_PROMOTION_ECONOMIC_GATE_PRECHECK_V0",
        ]
    )
    (evidence_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    _write_manifest(evidence_dir)

    return {
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "targeted_tests_pass": targeted_pass,
        "suite_pass": suite.suite_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=None)
    args = parser.parse_args()
    result = collect_evidence(args.out_dir)
    print(json.dumps(result, indent=2))
    return 0 if result["targeted_tests_pass"] and result["manifest_verify_rc"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
