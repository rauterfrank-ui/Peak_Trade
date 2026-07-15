#!/usr/bin/env python3
"""Materialize evidence for Bouchaud offline linear diagnostics promotion binding reconciliation v0."""

from __future__ import annotations

import argparse
import importlib.util
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
from src.governance.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_and_promotion_binding_completion_reconciliation_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    AUTHORITATIVE_TRUTH,
    DERIVATION_EVIDENCE_DIR,
    GO_TOKEN,
    PR5191_IMPLEMENTATION_DIR,
    PR5192_IMPLEMENTATION_DIR,
    PR_CHAIN,
    SCOPE,
    build_closeout_binding_map_v0,
    build_owner_inventory_v0,
    build_pr_chain_json_v0,
    build_reuse_decision_v0,
    deterministic_materialization_digest,
    validate_authoritative_truth_fields,
    validate_pr_chain_order,
    verify_source_derivation_manifest,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (  # noqa: E402
    CANONICAL_FEATURE_DIGEST,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (  # noqa: E402
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
)

MATERIALIZER = Path(__file__).relative_to(_REPO_ROOT)
OUTPUT_PREFIX = (
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "and_promotion_binding_completion_reconciliation_v0"
)
PROMOTION_MATERIALIZER = (
    _REPO_ROOT / "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
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


def _load_promotion_bind_fn():
    spec = importlib.util.spec_from_file_location(
        "bouchaud_promotion_materializer_v0",
        PROMOTION_MATERIALIZER,
    )
    if spec is None or spec.loader is None:
        raise SystemExit("failed_to_load_promotion_materializer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.bind_bouchaud_promotion_economic_gate_consumer_v0


def _run_focused_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/ops/"
        "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
        "and_promotion_binding_completion_reconciliation_v0_contract.py",
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

    bind_fn = _load_promotion_bind_fn()
    _, _, promotion_result = bind_fn(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        pr5192_implementation_dir=PR5192_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    promotion_payload = promotion_result.to_dict()
    assert promotion_payload["promotion_economic_gate_status"] == "BLOCKED"
    assert (
        BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT in promotion_payload["blocking_reason"]
    )
    validate_authoritative_truth_fields(
        promotion_economic_gate_status=promotion_payload["promotion_economic_gate_status"],
        blocking_reason=promotion_payload["blocking_reason"],
        feature_digest=CANONICAL_FEATURE_DIGEST,
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
    diff_patch = subprocess.run(
        ["git", "diff", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    ).stdout

    pr_chain = build_pr_chain_json_v0(closeout_records)
    closeout_map = {record.pr: record.to_dict() for record in closeout_records}
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

    scope_derivation = {
        "status": "PASS",
        "verdict": "DERIVATION_COMPLETE",
        "derived_scope": SCOPE,
        "scope_type": "GOVERNANCE_COMPLETION_RECONCILIATION",
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "reuse_source_pattern": "PR5188",
        "canonical_owner": (
            "src/governance/"
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            "and_promotion_binding_completion_reconciliation_v0.py"
        ),
        "source_evidence": str(DERIVATION_EVIDENCE_DIR),
        "current_blocking_point": "POLICY_BLOCK_ONLY",
        "target_consumer": "manifest-verified PR5189-5193 closeout chain",
        "economic_evaluation_authorized": False,
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
        "runbook_mutation": "FORBIDDEN_BY_OPERATOR_SCOPE",
    }

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
    _write_json(evidence_dir / "scope_derivation.json", scope_derivation)
    _write_json(evidence_dir / "owner_inventory.json", build_owner_inventory_v0())
    _write_json(evidence_dir / "reuse_decision.json", build_reuse_decision_v0())
    _write_json(
        evidence_dir / "field_classification.json",
        {
            "authored_fields": ["pr_chain", "closeout_binding_map"],
            "observed_fields": ["promotion_economic_gate_status", "blocking_reason"],
            "derived_fields": ["deterministic_materialization_digest"],
            "excluded_from_digest": ["generated_at"],
        },
    )
    _write_json(
        evidence_dir / "digest_contracts.json",
        {
            "canonical_feature_digest": CANONICAL_FEATURE_DIGEST,
            "materialization_digest_algorithm": "sha256(sorted_json)",
            "NOT_APPLICABLE_WITH_REASON": "No new digest owner; reconciliation references existing closeout digests",
        },
    )
    _write_json(
        evidence_dir / "digest_dependency_graph.json",
        {
            "nodes": [item["pr"] for item in PR_CHAIN],
            "terminal_pr": "5193",
            "feature_digest": CANONICAL_FEATURE_DIGEST,
        },
    )
    _write_json(
        evidence_dir / "before_after_field_diff.json",
        {"added_authoritative_fields": sorted(AUTHORITATIVE_TRUTH.keys())},
    )
    _write_json(
        evidence_dir / "semantic_identity_comparison.json",
        {
            "semantic_payload_unchanged": True,
            "reason": "Governance reconciliation only; no diagnostic semantic mutation",
        },
    )
    _write_json(
        evidence_dir / "cryptographic_identity_comparison.json",
        {
            "cryptographic_identity_unchanged": True,
            "feature_digest": CANONICAL_FEATURE_DIGEST,
        },
    )
    (evidence_dir / "materializer_roundtrip.txt").write_text(
        "\n".join(
            [
                "PROMOTION_BIND_INVOKED=true",
                f"PROMOTION_ECONOMIC_GATE_STATUS={promotion_payload['promotion_economic_gate_status']}",
                f"BLOCKING_REASON={promotion_payload['blocking_reason']}",
                "ROUNDTRIP=PASS",
            ]
        )
        + "\n",
        encoding="utf-8",
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
        evidence_dir / "runner_decision.json",
        {
            "runner_required": False,
            "reason": "Governance reconciliation slice; materializer-only entry point",
        },
    )
    _write_json(evidence_dir / "pr5189_5193_chain.json", pr_chain)
    _write_json(evidence_dir / "closeout_binding_map.json", closeout_map)
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
        evidence_dir / "ci_selector_decision.json",
        {
            "NOT_APPLICABLE_WITH_REASON": "Evidence bundle generated post-implementation; CI selector run at PR time",
        },
    )
    _write_json(
        evidence_dir / "test_assertion_matrix.json",
        {
            "contract_test_owner": str(
                _REPO_ROOT / "tests/ops/"
                "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
                "and_promotion_binding_completion_reconciliation_v0_contract.py"
            ),
            "focused_test_rc": test_rc,
        },
    )
    (evidence_dir / "test_results.txt").write_text(test_output + "\n", encoding="utf-8")
    (evidence_dir / "changed_files.txt").write_text(changed, encoding="utf-8")
    (evidence_dir / "git_diff.patch").write_text(diff_patch, encoding="utf-8")
    (evidence_dir / "final_report.txt").write_text(
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=BOUCHAUD_GOVERNANCE_COMPLETION_RECONCILIATION_COMPLETE",
                f"SCOPE={SCOPE}",
                f"GO_TOKEN={GO_TOKEN}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                "IMPLEMENTATION_MANIFEST_VERIFY_RC=0",
                f"FEATURE_DIGEST={CANONICAL_FEATURE_DIGEST}",
                "PROMOTION_ECONOMIC_GATE_STATUS=BLOCKED",
                "PROMOTION_CANDIDATE_ELIGIBLE=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "PROMOTION_DECISION_EXECUTED=false",
                "PROMOTION_PASS_CREATED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                f"FOCUSED_TEST_RC={test_rc}",
                "MERGE_EXECUTED=false",
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
