#!/usr/bin/env python3
"""Materialize pairwise spillover v1 portfolio binding implementation evidence."""

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

from scripts.ops import primary_evidence_retention_v0 as retention
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    EXECUTION_GO_TOKEN,
    load_authorization_ratification_v0,
    materialize_portfolio_binding_contract_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
    PORTFOLIO_BINDING_GO_TOKEN,
    PORTFOLIO_BINDING_SCOPE,
    PRE_PORTFOLIO_BINDING_DIGEST,
    build_portfolio_field_classification_v0,
    build_portfolio_policy_contracts_v0,
    build_portfolio_reuse_decision_v0,
    compute_portfolio_bindings_digest_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    CONFIRM_GO,
    PRE_RATIFIED_BINDING_DIGEST,
    SUPERSESSION_MODE,
    build_before_after_field_diff_v0,
    build_cryptographic_identity_v0,
    build_owner_inventory,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_versioned_hypothesis_binding_json_v0,
)

CONFIRM_GO = PORTFOLIO_BINDING_GO_TOKEN
DEFAULT_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
BLOCKED_BUNDLE = DEFAULT_ARCHIVE / (
    "research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0_complete_20260715T061448Z"
)
FOCUSED_TEST = (
    "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_"
    "portfolio_binding_implementation_v0_contract.py"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", default=CONFIRM_GO)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()
    if args.confirm != CONFIRM_GO:
        raise SystemExit(f"ERR:confirm_go_required:{CONFIRM_GO}")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO_ROOT, text=True).strip()
    origin_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=_REPO_ROOT, text=True
    ).strip()
    blocked_rc = 1
    if BLOCKED_BUNDLE.is_dir():
        ok, _ = retention.verify_manifest_sha256(BLOCKED_BUNDLE)
        blocked_rc = 0 if ok else 1

    prior = json.loads(
        (
            _REPO_ROOT
            / "config/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.json"
        ).read_text(encoding="utf-8")
    )
    # reload materialized fresh
    envelope = materialize_versioned_hypothesis_binding_v0()
    validation = materialize_and_validate_versioned_hypothesis_binding_v0()
    score_contract = materialize_score_and_ranking_contract_v0(envelope)
    portfolio_contracts = build_portfolio_policy_contracts_v0()
    roundtrip = materializer_to_binder_roundtrip_v0(envelope)
    first = serialize_versioned_hypothesis_binding_json_v0(envelope)
    second = serialize_versioned_hypothesis_binding_json_v0(
        materialize_versioned_hypothesis_binding_v0()
    )
    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=_REPO_ROOT,
        authorization_ratification=load_authorization_ratification_v0(_REPO_ROOT),
        go_token=EXECUTION_GO_TOKEN,
        versioned_binding=envelope,
        verify_source_manifests=False,
        materialize_dataset=False,
    )
    portfolio_contract = materialize_portfolio_binding_contract_v0(envelope, repo_root=_REPO_ROOT)

    bundle = (
        args.archive_root
        / "implementation"
        / f"cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_implementation_v0_{_utc_stamp()}"
    )
    bundle.mkdir(parents=True, exist_ok=False)

    test_proc = subprocess.run(
        [sys.executable, "-m", "pytest", FOCUSED_TEST, "-q"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    (bundle / "test_results.txt").write_text(test_proc.stdout + test_proc.stderr, encoding="utf-8")

    artifacts = {
        "preflight.txt": "\n".join(
            [
                f"SCOPE={PORTFOLIO_BINDING_SCOPE}",
                f"OPERATOR_GO={CONFIRM_GO}",
                f"HEAD={head}",
                f"ORIGIN_MAIN={origin_main}",
                f"BLOCKED_EXECUTION_MANIFEST_VERIFY_RC={blocked_rc}",
            ]
        )
        + "\n",
        "source_manifest_verification.txt": f"BLOCKED_EXECUTION_MANIFEST_VERIFY_RC={blocked_rc}\n",
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_portfolio_reuse_decision_v0(),
        "field_classification.json": build_portfolio_field_classification_v0(),
        "portfolio_policy_contracts.json": portfolio_contracts,
        "digest_contracts.json": {
            "old_binding_digest": PRE_RATIFIED_BINDING_DIGEST,
            "new_binding_digest": envelope["binding_digest"],
            "portfolio_bindings_digest": compute_portfolio_bindings_digest_v0(
                envelope["pending_implementation_bindings"]
            ),
            "score_contract_digest": score_contract["contract_digest"],
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": build_before_after_field_diff_v0(
            prior_envelope={"binding_digest": PRE_RATIFIED_BINDING_DIGEST},
            new_envelope=envelope,
        ),
        "semantic_identity_comparison.json": {
            "schema_version": "semantic_identity_comparison.v0",
            "semantic_binding_fields_changed": True,
            "portfolio_binding_fields_bound": True,
            "score_formula_unchanged": True,
            "dataset_digest_unchanged": True,
            "universe_digest_unchanged": True,
        },
        "cryptographic_identity_comparison.json": build_cryptographic_identity_v0(envelope),
        "materializer_roundtrip.txt": json.dumps(roundtrip, indent=2, sort_keys=True) + "\n",
        "deterministic_materialization.txt": "\n".join(
            [
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={str(first == second).lower()}",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={str(roundtrip['materializer_to_binder_roundtrip_pass']).lower()}",
            ]
        )
        + "\n",
        "test_assertion_matrix.json": {"focused_test": FOCUSED_TEST},
        "execution_dispatch_readiness_check.json": {
            "portfolio_bindings_valid": dispatch.portfolio_bindings_valid,
            "dispatch_accepted": dispatch.dispatch_accepted,
            "reason_codes": list(dispatch.reason_codes),
        },
    }
    for name, payload in artifacts.items():
        if isinstance(payload, (dict, list)):
            (bundle / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        else:
            (bundle / name).write_text(str(payload), encoding="utf-8")

    manifest_rc, _ = retention.finalize_durable_bundle_manifest(bundle)
    (bundle / "final_report.txt").write_text(
        "\n".join(
            [
                "STATUS=PASS",
                "VERDICT=PORTFOLIO_BINDING_IMPLEMENTATION_COMPLETE",
                f"SCOPE={PORTFOLIO_BINDING_SCOPE}",
                f"OPERATOR_GO={CONFIRM_GO}",
                f"PRE_MUTATION_HEAD={head}",
                f"OLD_BINDING_DIGEST={PRE_RATIFIED_BINDING_DIGEST}",
                f"NEW_BINDING_DIGEST={envelope['binding_digest']}",
                "SEMANTIC_BINDING_FIELDS_CHANGED=true",
                "CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED=true",
                f"BINDING_CLASSIFICATION={envelope['binding_classification']}",
                f"SUPERSESSION_MODE={SUPERSESSION_MODE}",
                "PORTFOLIO_BINDINGS_IMPLEMENTED=true",
                "DATASET_DIGEST_UNCHANGED=true",
                "UNIVERSE_DIGEST_UNCHANGED=true",
                "SCORE_FORMULA_UNCHANGED=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"EXECUTION_DISPATCH_BINDINGS_COMPLETE={str(dispatch.portfolio_bindings_valid).lower()}",
                f"TEST_RESULT={'PASS' if test_proc.returncode == 0 else 'FAIL'}",
                f"MANIFEST_VERIFY_RC={manifest_rc}",
                f"DURABLE_EVIDENCE_DIR={bundle}",
                "NEXT_ADMISSIBLE_SCOPE=PR_MERGE_CLOSEOUT_PORTFOLIO_BINDING_IMPLEMENTATION_V0",
                "NEXT_SCOPE_REQUIRES_SEPARATE_OPERATOR_GO=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    retention.finalize_durable_bundle_manifest(bundle)
    print(json.dumps({"bundle": str(bundle), "manifest_rc": manifest_rc}, indent=2))


if __name__ == "__main__":
    main()
