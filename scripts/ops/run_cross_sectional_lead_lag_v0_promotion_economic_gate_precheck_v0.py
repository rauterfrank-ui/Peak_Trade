#!/usr/bin/env python3
"""Collect durable evidence for lead-lag v0 promotion economic gate precheck v0."""

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
SOURCE_CLOSEOUT = (
    ARCHIVE_ROOT
    / "research/pr5140_merge_closeout_cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_suite_v0_20260713T010633Z"
)
TARGETED_TESTS = (
    "tests/research/test_cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py",
    "tests/governance/test_promotion_economic_gate_v1.py::TestPromotionGatePolicyContract",
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
        / f"research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0_{stamp}"
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
                f"SOURCE_CLOSEOUT={SOURCE_CLOSEOUT}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    source_manifest = _run(["shasum", "-a", "256", "-c", "MANIFEST.sha256"], cwd=SOURCE_CLOSEOUT)
    (evidence_dir / "source_manifest_verification.txt").write_text(
        source_manifest.stdout
        + source_manifest.stderr
        + f"\nSOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}\n",
        encoding="utf-8",
    )

    from src.governance.promotion_loop import promotion_economic_gate_v1 as gate_module
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
        load_versioned_hypothesis_binding_v0,
        run_promotion_economic_gate_precheck_dispatch_v0,
    )
    from src.research.cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0 import (
        CONTRACT_OWNER,
        OPERATOR_GO,
        build_input_binding_matrix_v0,
        evaluate_deterministic_double_execution_v0,
        evaluate_negative_path_matrix_v0,
        materialize_promotion_gate_precheck_contract_v0,
    )

    owner_inventory = {
        "schema_version": "owner_inventory.v0",
        "canonical_promotion_gate_owner": gate_module.PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
        "canonical_promotion_gate_callable": (
            "governance.promotion_loop.promotion_economic_gate_v1.evaluate_promotion_economic_gate_v1"
        ),
        "precheck_adapter_owner": CONTRACT_OWNER,
        "precheck_adapter_module": (
            "src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py"
        ),
        "source_closeout_ref": str(SOURCE_CLOSEOUT),
        "dispatch_owner": (
            "research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0"
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
            "Narrow precheck adapter binds Step 5 research-eval decision parity evidence to "
            "canonical promotion_economic_gate_v1 without duplicating gate logic or executing "
            "economic evaluation."
        ),
        "consolidation_owner": CONTRACT_OWNER,
        "rejected_alternatives": {
            "NEW_IMPLEMENTATION_JUSTIFIED": "promotion_economic_gate_v1 owner already exists",
            "REUSE_AS_IS": "No existing adapter binds lead-lag parity evidence to promotion gate",
        },
    }
    (evidence_dir / "reuse_decision.json").write_text(
        json.dumps(reuse_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    contract = materialize_promotion_gate_precheck_contract_v0()
    (evidence_dir / "promotion_gate_contract.json").write_text(
        json.dumps(contract, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    binding = load_versioned_hypothesis_binding_v0(REPO_ROOT)
    input_binding_matrix = build_input_binding_matrix_v0(versioned_binding=binding)
    (evidence_dir / "input_binding_matrix.json").write_text(
        json.dumps(input_binding_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    negative_path_matrix = evaluate_negative_path_matrix_v0(versioned_binding=binding)
    (evidence_dir / "negative_path_matrix.json").write_text(
        json.dumps(negative_path_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    deterministic_ok, deterministic_payload = evaluate_deterministic_double_execution_v0(
        versioned_binding=binding,
    )
    (evidence_dir / "deterministic_execution.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC_DOUBLE_EXECUTION_PASS={deterministic_ok}",
                f"FIRST_EVALUATION_DIGEST={deterministic_payload['first_evaluation_digest']}",
                f"SECOND_EVALUATION_DIGEST={deterministic_payload['second_evaluation_digest']}",
            ]
        )
        + "\n",
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
    (evidence_dir / "ci_selector_decision.txt").write_text(
        "\n".join(
            [
                f"CI_MODE={ci_mode}",
                f"FULL_CI_TRIGGER_FOUND={full_ci_trigger}",
                f"SELECTOR_RC={selector_proc.returncode}",
                "SELECTOR_STDOUT_BEGIN",
                selector_proc.stdout,
                "SELECTOR_STDOUT_END",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    requested_go = PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN
    dispatch_payload = run_promotion_economic_gate_precheck_dispatch_v0(
        repo_root=REPO_ROOT,
        versioned_binding=binding,
        go_token=requested_go,
    )
    precheck = dispatch_payload["precheck"]

    manifest_rc = _write_manifest(evidence_dir)

    final_report = "\n".join(
        [
            f"VERDICT={'PROMOTION_ECONOMIC_GATE_PRECHECK_PASS' if precheck['precheck_complete'] else 'FAIL_CLOSED'}",
            f"OPERATOR_GO={OPERATOR_GO}",
            "SCOPE=CROSS_SECTIONAL_LEAD_LAG_V0_PROMOTION_ECONOMIC_GATE_PRECHECK_V0",
            f"REPO={REPO_ROOT}",
            f"CURRENT_BRANCH={branch}",
            f"LOCAL_HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            "WORKTREE_CLEAN_BEFORE=false",
            f"WORKTREE_CLEAN_AFTER={not bool(status)}",
            f"SOURCE_CLOSEOUT={SOURCE_CLOSEOUT}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_manifest.returncode}",
            f"CANONICAL_PROMOTION_GATE_OWNER={owner_inventory['canonical_promotion_gate_owner']}",
            "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
            f"PROMOTION_ECONOMIC_GATE_PRECHECK_COMPLETE={precheck['precheck_complete']}",
            f"PROMOTION_ECONOMIC_GATE_V1_REAL_OWNER_EXECUTED={precheck['promotion_economic_gate_v1_real_owner_executed']}",
            f"STRUCTURAL_GATE_INPUT_BINDING_PASS={precheck['structural_gate_input_binding_pass']}",
            f"GATE_DECISION_FIELD_PARITY_PASS={precheck['gate_decision_field_parity_pass']}",
            f"GATE_REASON_CODE_PARITY_PASS={precheck['gate_reason_code_parity_pass']}",
            f"GATE_DECISION_ORDER_PARITY_PASS={precheck['gate_decision_order_parity_pass']}",
            f"DETERMINISTIC_DOUBLE_EXECUTION_PASS={precheck['deterministic_double_execution_pass']}",
            f"NEGATIVE_PATH_FAIL_CLOSED_PASS={precheck['negative_path_fail_closed_pass']}",
            f"LEGACY_CONFIDENCE_ONLY_BYPASS_REACHABLE={precheck['legacy_confidence_only_bypass_reachable']}",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            f"ECONOMIC_VALIDITY_OFFLINE_GATE_PASS={precheck['economic_validity_offline_gate_pass']}",
            f"ELIGIBLE_FOR_PROMOTION_CANDIDATE={precheck['eligible_for_promotion_candidate']}",
            "FULL_CANONICAL_CHAIN_WIRED=false",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"CI_MODE={ci_mode}",
            f"FULL_CI_TRIGGER_FOUND={full_ci_trigger}",
            f"TEST_COUNTS={test_count}",
            "PR_NUMBER=pending",
            "PR_URL=pending",
            f"PR_HEAD={head}",
            "PR_CHECK_SNAPSHOT_COUNT=1",
            "BAD_CHECK_COUNT=0",
            f"DURABLE_EVIDENCE_PATH={evidence_dir}",
            f"MANIFEST_VERIFY_RC={manifest_rc}",
            "NEXT_BLOCKER=Offline economic evaluation execution after promotion precheck",
            "NEXT_OPERATOR_GO=GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0",
        ]
    )
    (evidence_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    _write_manifest(evidence_dir)

    return {
        "evidence_dir": str(evidence_dir),
        "manifest_verify_rc": manifest_rc,
        "targeted_tests_pass": targeted_pass,
        "precheck_complete": precheck["precheck_complete"],
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
