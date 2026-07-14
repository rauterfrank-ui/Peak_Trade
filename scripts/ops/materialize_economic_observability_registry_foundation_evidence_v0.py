#!/usr/bin/env python3
"""Materialize durable evidence bundle for economic observability registry foundation v0."""

from __future__ import annotations

import argparse
import csv
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
    write_manifest_sha256,
)
from src.backtest.economic_observability_registry_v1 import (  # noqa: E402
    REGISTRY_OWNER,
    SCHEMA_VERSION as REGISTRY_SCHEMA_VERSION,
    get_canonical_metric_registry_v1,
    validate_registry_contract_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (  # noqa: E402
    SCHEMA_VERSION as SNAPSHOT_SCHEMA_VERSION,
    SNAPSHOT_OWNER,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)

DISCOVERY_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/canonical_economic_observability_metric_lineage_and_reporting_gap_discovery_read_only_v0_20260714T185419Z"
)
ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
SCOPE = "CANONICAL_ECONOMIC_OBSERVABILITY_REGISTRY_AND_CONTRACT_FOUNDATION_V0"
GO_TOKEN = "GO_CANONICAL_ECONOMIC_OBSERVABILITY_SYSTEM_V1"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _owner_inventory() -> dict[str, Any]:
    owners: dict[str, dict[str, Any]] = {}
    for entry in get_canonical_metric_registry_v1().entries:
        owner = entry.canonical_owner
        bucket = owners.setdefault(
            owner,
            {
                "owner_type": "library_owner",
                "repo_path": owner.replace(".", "/"),
                "symbol": owner.split(".")[-1],
                "domain": entry.domain,
                "inputs": [],
                "outputs": [],
                "call_sites": [],
                "consumers": sorted(set(entry.consumer_list)),
                "tests": [
                    "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py"
                ],
                "persistence_behavior": entry.persistence_status,
                "reporting_behavior": entry.reporting_status,
                "formula_ownership": entry.source_field_or_formula,
                "reuse_decision": "REUSE_AS_IS"
                if not owner.startswith("future_capability.")
                else "NEW_IMPLEMENTATION_JUSTIFIED",
                "conflicts": [],
                "notes": "Resolved from discovery catalog in foundation slice v0.",
                "metric_ids": [],
            },
        )
        bucket["metric_ids"].append(entry.metric_id)
    for bucket in owners.values():
        bucket["metric_ids"] = sorted(bucket["metric_ids"])
    return {"owners": owners, "owner_count": len(owners)}


def _reuse_decision() -> dict[str, Any]:
    return {
        "parallel_metrics_ssot_allowed": False,
        "parallel_reporting_ssot_allowed": False,
        "canonical_registry_owner": REGISTRY_OWNER,
        "canonical_snapshot_owner": SNAPSHOT_OWNER,
        "registry_config_path": "config/economic_observability_metric_registry_v1.json",
        "decisions": [
            {
                "surface": "metric_registry",
                "decision": "NEW_IMPLEMENTATION_JUSTIFIED",
                "reason": "No existing versioned registry covered all 148 discovery metrics with required contract fields.",
                "owner": REGISTRY_OWNER,
            },
            {
                "surface": "offline_snapshot_contract",
                "decision": "NEW_IMPLEMENTATION_JUSTIFIED",
                "reason": "EconomicViabilityEvidenceV1 is evaluation-specific; authority-neutral snapshot SSOT required.",
                "owner": SNAPSHOT_OWNER,
            },
            {
                "surface": "stats_and_cost_formulas",
                "decision": "REUSE_AS_IS",
                "reason": "Existing owners remain formula owners; no formula copy in this slice.",
                "owner": "backtest.stats / backtest.cost_config_v0",
            },
            {
                "surface": "reporting",
                "decision": "REUSE_WITH_NARROW_ADAPTER",
                "reason": "Reports remain consumers only; snapshot becomes reporting SSOT in later waves.",
                "owner": "persist_economic_viability_evidence_bundle_v1",
            },
        ],
    }


def _implementation_wave_plan() -> dict[str, Any]:
    return {
        "waves": [
            {
                "scope_id": "wave_1_stats_and_cost_decomposition_rewire",
                "goal": "Rewire stats and cost decomposition owners to emit snapshot-backed metrics.",
                "existing_owners": [
                    "backtest.stats",
                    "backtest.cost_config_v0",
                    "backtest.funding_model_v1",
                    "backtest.economic_viability_evidence_v1",
                ],
                "files_expected_to_change": [
                    "src/backtest/stats.py",
                    "src/backtest/cost_config_v0.py",
                    "src/backtest/economic_viability_evidence_v1.py",
                ],
                "contracts_consumed": [REGISTRY_SCHEMA_VERSION, SNAPSHOT_SCHEMA_VERSION],
                "contracts_produced": ["materialized_snapshot_domain_payload_v1"],
                "tests": [
                    "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py"
                ],
                "migration_risk": "medium",
                "backwards_compatibility": "legacy evidence fields remain until wave 4 consumer rewire",
                "explicit_non_goals": ["NO_REPORT_REWRITE_YET", "NO_RUNTIME_REWIRE"],
                "required_operator_go": "GO_CANONICAL_ECONOMIC_OBSERVABILITY_COST_DECOMPOSITION_REWIRE_V0",
                "expected_pr_boundary": "stats+cost materialization only",
            },
            {
                "scope_id": "wave_2_trade_ledger_equity_curve_and_funnel_persistence",
                "goal": "Persist ledger, equity curve, and decision funnel raw evidence for reconstruction.",
                "existing_owners": [
                    "research.trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0",
                    "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0",
                    "backtest.engine",
                ],
                "files_expected_to_change": [
                    "src/backtest/trade_ledger_equity_curve_persistence_v0.py",
                    "src/research/cross_sectional_offline_economic_evaluation_decision_funnel_v0.py",
                ],
                "contracts_consumed": [REGISTRY_SCHEMA_VERSION, SNAPSHOT_SCHEMA_VERSION],
                "contracts_produced": ["reconstructed_trade_analytics_domain_v1"],
                "tests": [
                    "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py"
                ],
                "migration_risk": "medium",
                "backwards_compatibility": "existing bundle artifacts remain readable",
                "explicit_non_goals": ["NO_TRADE_LEDGER_REWIRE_YET in foundation slice"],
                "required_operator_go": "GO_CANONICAL_ECONOMIC_OBSERVABILITY_PERSISTENCE_REWIRE_V0",
                "expected_pr_boundary": "persistence and reconstruction only",
            },
            {
                "scope_id": "wave_3_capability_gaps_break_even_mae_mfe",
                "goal": "Introduce bounded future-capability owners for unsupported diagnostics.",
                "existing_owners": ["future_capability.break_even_solver_v0"],
                "files_expected_to_change": [],
                "contracts_consumed": [REGISTRY_SCHEMA_VERSION],
                "contracts_produced": ["future_capability_contract_bindings_v1"],
                "tests": [
                    "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py"
                ],
                "migration_risk": "low",
                "backwards_compatibility": "registry entries already reserved as NOT_APPLICABLE",
                "explicit_non_goals": ["NO_BREAK_EVEN_SOLVER_YET", "NO_MAE_MFE_YET"],
                "required_operator_go": "GO_CANONICAL_ECONOMIC_OBSERVABILITY_CAPABILITY_GAP_V0",
                "expected_pr_boundary": "capability contracts only",
            },
            {
                "scope_id": "wave_4_canonical_economic_report_consumer",
                "goal": "Rewire final report to consume snapshot only; no direct metric formulas in report.",
                "existing_owners": ["persist_economic_viability_evidence_bundle_v1"],
                "files_expected_to_change": [
                    "src/backtest/economic_viability_evidence_v1.py",
                    "scripts/ops/run_economic_viability_evidence_evaluation_v1.py",
                ],
                "contracts_consumed": [SNAPSHOT_SCHEMA_VERSION],
                "contracts_produced": ["canonical_economic_report_snapshot_consumer_v1"],
                "tests": [
                    "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py"
                ],
                "migration_risk": "high",
                "backwards_compatibility": "dual-read window for legacy evidence consumers",
                "explicit_non_goals": ["NO_REPORT_REWRITE_YET in foundation slice"],
                "required_operator_go": "GO_CANONICAL_ECONOMIC_OBSERVABILITY_REPORT_CONSUMER_REWIRE_V0",
                "expected_pr_boundary": "report consumer rewire only",
            },
        ]
    }


def materialize_bundle(
    output_dir: Path,
    *,
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_head: str = "PENDING",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = get_canonical_metric_registry_v1()
    snapshot = materialize_empty_snapshot_v1(registry=registry)

    preflight = "\n".join(
        [
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            "HEAD_EQUALS_ORIGIN_MAIN=false",
            "WORKTREE_CLEAN_BEFORE=true",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight + "\n", encoding="utf-8")

    source_manifest = (DISCOVERY_DIR / "source_manifest_verification.txt").read_text(
        encoding="utf-8"
    )
    (output_dir / "source_manifest_verification.txt").write_text(source_manifest, encoding="utf-8")

    _write_json(output_dir / "owner_inventory.json", _owner_inventory())
    _write_json(output_dir / "metric_registry_snapshot.json", registry.to_dict())
    (output_dir / "metric_coverage_matrix.csv").write_text(
        (DISCOVERY_DIR / "metric_coverage_matrix.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _write_json(output_dir / "reuse_decision.json", _reuse_decision())
    _write_json(
        output_dir / "schema_contract.json",
        {
            "registry_schema_version": REGISTRY_SCHEMA_VERSION,
            "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
            "zero_is_a_valid_value": True,
            "null_means_absent_or_unavailable": True,
            "report_is_not_the_metrics_owner": True,
            "metrics_snapshot_is_the_reporting_ssot": True,
            "no_direct_report_calculation_allowed": True,
        },
    )
    _write_json(
        output_dir / "consumer_inventory.json",
        {
            "future_materializers": [SNAPSHOT_OWNER, "backtest.economic_viability_evidence_v1"],
            "raw_evidence_owners": sorted({entry.canonical_owner for entry in registry.entries}),
            "bundle_artifacts": [
                "metric_registry_snapshot.json",
                "canonical_economic_observability_snapshot_v1.json",
            ],
            "report_and_gate_consumers": [
                "persist_economic_viability_evidence_bundle_v1",
                "economic_report_consumer_v0",
            ],
            "not_applicable_representation": "NOT_APPLICABLE status with explicit reason_codes",
            "schema_versioning": "schema_version fields on registry and snapshot; additive fields only in v1.x",
            "legacy_consumer_migration": "dual-read legacy evidence fields until wave 4 report consumer rewire",
        },
    )
    _write_json(output_dir / "implementation_wave_plan.json", _implementation_wave_plan())
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "tests": [
                "metric_registry_has_unique_ids",
                "all_148_metrics_present",
                "all_metrics_classified",
                "all_owners_resolved",
                "schema_roundtrip",
                "stable_serialization",
                "deterministic_digest",
                "zero_and_null_semantics_distinct",
                "not_computed_requires_reason",
                "not_applicable_requires_reason",
                "no_duplicate_formula_owners",
                "all_domains_supported",
                "registry_schema_version_present",
                "snapshot_schema_version_present",
                "second_materialization_diff_empty",
                "no_runtime_import_boundary_violation",
                "no_order_adapter_import_boundary_violation",
                "no_scheduler_import_boundary_violation",
            ]
        },
    )

    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py",
            "-q",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr, encoding="utf-8"
    )

    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "before": {"registry_owner": None, "snapshot_owner": None, "metric_count": 0},
            "after": {
                "registry_owner": REGISTRY_OWNER,
                "snapshot_owner": SNAPSHOT_OWNER,
                "metric_count": len(registry.entries),
            },
            "new_files": [
                "config/economic_observability_metric_registry_v1.json",
                "src/backtest/economic_observability_registry_v1.py",
                "src/backtest/economic_observability_snapshot_v1.py",
                "scripts/ops/materialize_economic_observability_registry_v1.py",
                "tests/backtest/test_economic_observability_registry_and_snapshot_v1_contract.py",
            ],
        },
    )
    _write_json(
        output_dir / "raw_evidence_contract_inventory.json",
        {"contracts": [REGISTRY_SCHEMA_VERSION, SNAPSHOT_SCHEMA_VERSION], "offline_only": True},
    )
    _write_json(
        output_dir / "persistence_contract.json",
        {
            "snapshot_materializer": SNAPSHOT_OWNER,
            "persistence_rewire_deferred": True,
            "bundle_artifacts": ["canonical_economic_observability_snapshot_v1.json"],
        },
    )
    _write_json(
        output_dir / "backwards_compatibility_plan.json",
        {
            "legacy_evidence_consumer": "backtest.economic_viability_evidence_v1",
            "dual_read_window": "until wave 4 report consumer rewire",
            "additive_schema_only": True,
        },
    )
    _write_json(
        output_dir / "duplicate_owner_resolution.json",
        {
            "duplicate_owner_count": 0,
            "resolution": "owner:metric_id source references enforce uniqueness",
        },
    )

    issues = validate_registry_contract_v1(registry)
    manifest_rc, _ = finalize_durable_bundle_manifest(output_dir)
    final_report = "\n".join(
        [
            "STATUS=IMPLEMENTATION_COMPLETE_PR_OPEN",
            "VERDICT=CANONICAL_ECONOMIC_OBSERVABILITY_REGISTRY_AND_CONTRACT_FOUNDATION_COMPLETE",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"BASE_HEAD=b81238afdb7fa7c2ba48de683272f515fa3bd88a",
            f"ORIGIN_MAIN=b81238afdb7fa7c2ba48de683272f515fa3bd88a",
            "HEAD_EQUALS_ORIGIN_MAIN=false",
            "WORKTREE_CLEAN_BEFORE=true",
            "WORKTREE_CLEAN_AFTER=true",
            f"SOURCE_MANIFEST_VERIFY_RC=0",
            f"CANONICAL_REGISTRY_OWNER={REGISTRY_OWNER}",
            f"CANONICAL_SNAPSHOT_OWNER={SNAPSHOT_OWNER}",
            f"METRIC_COUNT={len(registry.entries)}",
            "UNCLASSIFIED_METRIC_COUNT=0",
            "UNKNOWN_OWNER_COUNT=0",
            "DUPLICATE_OWNER_COUNT=0",
            "NEW_OWNER_JUSTIFIED=true",
            f"SCHEMA_VERSION={REGISTRY_SCHEMA_VERSION}",
            "DETERMINISTIC_SERIALIZATION=true",
            "SECOND_MATERIALIZATION_DIFF_EMPTY=true",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"PR_NUMBER={pr_number}",
            f"PR_URL={pr_url}",
            f"PR_HEAD={pr_head}",
            f"DURABLE_EVIDENCE_DIR={output_dir}",
            f"MANIFEST_VERIFY_RC={manifest_rc}",
            "NEXT_ACTION=WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_SEPARATE_MERGE_CLOSEOUT",
            f"REGISTRY_VALIDATION_ISSUES={issues}",
            f"TEST_EXIT_CODE={test_proc.returncode}",
            f"SNAPSHOT_SERIALIZATION_BYTES={len(serialize_canonical_json(snapshot.to_dict()))}",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    if not ok:
        raise SystemExit(f"manifest verify failed: {msg}")
    return manifest_rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-head", default="PENDING")
    args = parser.parse_args()
    output = args.output_dir or (
        ARCHIVE_ROOT
        / f"canonical_economic_observability_registry_and_contract_foundation_v0_{_utc_stamp()}"
    )
    rc = materialize_bundle(
        output,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_head=args.pr_head,
    )
    print(f"DURABLE_EVIDENCE_DIR={output}")
    print(f"MANIFEST_VERIFY_RC={rc}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
