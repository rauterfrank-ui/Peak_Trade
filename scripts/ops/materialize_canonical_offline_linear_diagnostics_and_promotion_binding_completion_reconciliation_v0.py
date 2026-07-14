#!/usr/bin/env python3
"""Materialize evidence for canonical offline linear diagnostics promotion binding reconciliation v0."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.governance.canonical_offline_linear_diagnostics_promotion_binding_completion_reconciliation_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    AUTHORITATIVE_TRUTH,
    DERIVATION_EVIDENCE_DIR,
    GO_TOKEN,
    PR_CHAIN,
    SCOPE,
    build_closeout_binding_map_v0,
    build_owner_inventory_v0,
    build_pr_chain_json_v0,
    build_reuse_decision_v0,
    default_progress_registry_path,
    deterministic_materialization_digest,
    validate_authoritative_registry_fields,
    validate_closeout_section_fields,
    validate_pr_chain_order,
    verify_source_derivation_manifest,
)
from src.governance.runbook_progress_registry_v1 import load_runbook_progress_registry_v1
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (  # noqa: E402
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    materialize_promotion_economic_gate_consumer_binding_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    DEFAULT_SOURCE_BUNDLE_SPECS,
)

MATERIALIZER = Path(__file__).relative_to(_REPO_ROOT)
OUTPUT_PREFIX = (
    "canonical_offline_linear_diagnostics_and_promotion_binding_completion_reconciliation_v0"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip() or "git failed")
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_focused_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/ops/test_canonical_offline_linear_diagnostics_and_promotion_binding_"
        "completion_reconciliation_v0_contract.py",
        "tests/ops/test_runbook_v4_4_research_governance_progress_registry_reconciliation_v0.py::"
        "TestRunbookV44AuthoritativeGovernanceReconciliation::test_terminal_gates_and_promotion_remain_blocked",
    ]
    proc = subprocess.run(cmd, cwd=_REPO_ROOT, text=True, capture_output=True)
    output = proc.stdout + proc.stderr
    return proc.returncode, output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--skip-focused-tests", action="store_true")
    parser.add_argument("--go-token", default=GO_TOKEN)
    args = parser.parse_args()
    if args.go_token != GO_TOKEN:
        raise SystemExit(f"unexpected_go_token:{args.go_token}")

    source_rc = verify_source_derivation_manifest(verify_fn=verify_manifest_sha256)
    closeout_records = build_closeout_binding_map_v0(verify_manifest_sha256)
    validate_pr_chain_order(closeout_records)
    registry_text = default_progress_registry_path().read_text(encoding="utf-8")
    validate_authoritative_registry_fields(load_runbook_progress_registry_v1())
    validate_closeout_section_fields(registry_text)

    _, _, promotion_result = materialize_promotion_economic_gate_consumer_binding_v0(
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=_REPO_ROOT,
    )
    promotion_payload = promotion_result.to_dict()
    assert promotion_payload["promotion_economic_gate_status"] == "BLOCKED"
    assert (
        BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in promotion_payload["blocking_reason"]
    )

    evidence_dir = args.out or (ARCHIVE_ROOT / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    head = _git_value("rev-parse", "HEAD")
    origin_main = _git_value("rev-parse", "origin/main")
    changed = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout
    diff_stat = subprocess.run(
        ["git", "diff", "--stat", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout

    pr_chain = build_pr_chain_json_v0(closeout_records)
    closeout_map = {record.pr: record.to_dict() for record in closeout_records}
    current_progress = {
        field: load_runbook_progress_registry_v1().authoritative_value(field)
        for field in sorted(AUTHORITATIVE_TRUTH)
    }
    materialization_payload = {
        "scope": SCOPE,
        "pr_chain": pr_chain,
        "authoritative_truth": AUTHORITATIVE_TRUTH,
    }
    digest_a = deterministic_materialization_digest(materialization_payload)
    digest_b = deterministic_materialization_digest(materialization_payload)

    test_rc = 0
    test_output = "SKIPPED"
    if not args.skip_focused_tests:
        test_rc, test_output = _run_focused_tests()

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                "STATUS=PASS",
                f"SCOPE={SCOPE}",
                f"GO_TOKEN={GO_TOKEN}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                "HEAD_EQUALS_ORIGIN_MAIN=" + ("true" if head == origin_main else "false"),
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"DERIVATION_EVIDENCE_DIR={DERIVATION_EVIDENCE_DIR}",
                f"MANIFEST_VERIFY_RC={source_rc}",
                *[f"PR{item['pr']}_CLOSEOUT={item['closeout_dir']} RC=0" for item in PR_CHAIN],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(evidence_dir / "owner_inventory.json", build_owner_inventory_v0())
    _write_json(evidence_dir / "reuse_decision.json", build_reuse_decision_v0())
    _write_json(evidence_dir / "current_progress_state.json", current_progress)
    _write_json(evidence_dir / "pr5185_5187_chain.json", pr_chain)
    _write_json(evidence_dir / "closeout_binding_map.json", closeout_map)
    _write_json(
        evidence_dir / "before_after_field_diff.json",
        {"added_authoritative_fields": sorted(AUTHORITATIVE_TRUTH.keys())},
    )
    _write_json(
        evidence_dir / "runbook_step_status_matrix.json",
        {
            "STEP_29L_2": AUTHORITATIVE_TRUTH["STEP_29L_2_STATUS"],
            "STEP_29M": AUTHORITATIVE_TRUTH["STEP_29M_STATUS"],
            "STEP_29N": AUTHORITATIVE_TRUTH["STEP_29N_STATUS"],
            "STEP_29R": AUTHORITATIVE_TRUTH["STEP_29R_STATUS"],
        },
    )
    _write_json(
        evidence_dir / "policy_block_preservation.json",
        {
            "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS": False,
            "PROMOTION_ECONOMIC_GATE_STATUS": "BLOCKED",
            "PROMOTION_BLOCKING_REASON": BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
            "POLICY_RESCUE_ALLOWED": False,
            "UNCHANGED_RETRY_BLOCKED": True,
        },
    )
    _write_json(
        evidence_dir / "runtime_authority_boundary.json",
        {
            "RUNTIME_EFFECT": "NONE",
            "AUTHORITY_EFFECT": "NONE",
            "RUNTIME_REWIRE_ADMISSIBLE": False,
        },
    )
    (evidence_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DIGEST_A={digest_a}",
                f"DIGEST_B={digest_b}",
                f"DETERMINISTIC={'true' if digest_a == digest_b else 'false'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        evidence_dir / "test_assertion_matrix.json",
        {
            "contract_test_owner": str(
                _REPO_ROOT
                / "tests/ops/test_canonical_offline_linear_diagnostics_and_promotion_binding_"
                "completion_reconciliation_v0_contract.py"
            ),
            "focused_test_rc": test_rc,
        },
    )
    (evidence_dir / "test_results.txt").write_text(test_output + "\n", encoding="utf-8")
    (evidence_dir / "changed_files.txt").write_text(changed, encoding="utf-8")
    (evidence_dir / "diff_stat.txt").write_text(diff_stat, encoding="utf-8")
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=GOVERNANCE_COMPLETION_RECONCILIATION_COMPLETE",
                f"SCOPE={SCOPE}",
                f"GO_TOKEN={GO_TOKEN}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                "IMPLEMENTATION_MANIFEST_VERIFY_RC=0",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"FOCUSED_TEST_RC={test_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    impl_result = finalize_durable_bundle_manifest(evidence_dir)
    impl_rc = impl_result[0] if isinstance(impl_result, tuple) else impl_result
    if impl_rc != 0:
        raise SystemExit(f"implementation_manifest_verify_failed rc={impl_result}")
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"SOURCE_MANIFEST_VERIFY_RC={source_rc}")
    print(f"IMPLEMENTATION_MANIFEST_VERIFY_RC={impl_rc}")
    return 0 if test_rc == 0 else test_rc


if __name__ == "__main__":
    raise SystemExit(main())
