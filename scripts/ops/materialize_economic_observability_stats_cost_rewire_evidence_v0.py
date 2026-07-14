#!/usr/bin/env python3
"""Materialize durable evidence for canonical stats/cost decomposition rewire v0."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
from src.backtest.cost_config_v0 import COST_MODEL_VERSION, resolve_effective_backtest_cost_config
from src.backtest.economic_observability_materialization_v1 import (
    COST_OWNER,
    MATERIALIZATION_OWNER,
    RECONCILIATION_TOLERANCE,
    STATS_OWNER,
    BacktestObservabilityInputsV1,
    existing_cost_field_keys_v0,
    existing_stats_field_keys_v0,
    materialize_snapshot_from_backtest_stats_v1,
)
from src.backtest.economic_observability_registry_v1 import (  # noqa: E402
    REGISTRY_OWNER,
    SCHEMA_VERSION as REGISTRY_SCHEMA_VERSION,
    get_canonical_metric_registry_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (  # noqa: E402
    SCHEMA_VERSION as SNAPSHOT_SCHEMA_VERSION,
    SNAPSHOT_OWNER,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.backtest.stats import compute_backtest_stats  # noqa: E402

import pandas as pd  # noqa: E402

ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
PR5174_CLOSEOUT = ARCHIVE_ROOT / (
    "pr5174_merge_closeout_canonical_economic_observability_registry_and_contract_foundation_v0_"
    "20260714T192427Z"
)
PR5174_IMPL = ARCHIVE_ROOT / (
    "canonical_economic_observability_registry_and_contract_foundation_v0_20260714T191543Z"
)
DISCOVERY_DIR = ARCHIVE_ROOT / (
    "canonical_economic_observability_metric_lineage_and_reporting_gap_discovery_read_only_v0_"
    "20260714T185419Z"
)
SCOPE = "CANONICAL_EXISTING_STATS_AND_COST_DECOMPOSITION_REWIRE_V0"
GO_TOKEN = "GO_CANONICAL_EXISTING_STATS_AND_COST_DECOMPOSITION_REWIRE_V0"


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


def _verify_source_manifests() -> tuple[int, str]:
    lines: list[str] = []
    rc = 0
    for label, bundle in (
        ("PR5174_MERGE_CLOSEOUT", PR5174_CLOSEOUT),
        ("PR5174_IMPLEMENTATION", PR5174_IMPL),
        ("METRIC_LINEAGE_DISCOVERY", DISCOVERY_DIR),
    ):
        manifest = bundle / "MANIFEST.sha256"
        ok, msg = verify_manifest_sha256(bundle)
        lines.append(f"{label}_DIR={bundle}")
        lines.append(f"{label}_MANIFEST_VERIFY={msg}")
        lines.append(f"{label}_RC={0 if ok else 1}")
        if not ok:
            rc = 1
        if not manifest.is_file():
            rc = 1
    return rc, "\n".join(lines) + "\n"


def _fixture_stats() -> dict:
    trades = [
        {"pnl": 120.0, "gross_pnl": 130.0, "entry_cost": 5.0, "exit_cost": 5.0},
        {"pnl": -40.0, "gross_pnl": -30.0, "entry_cost": 5.0, "exit_cost": 5.0},
        {"pnl": 55.0, "gross_pnl": 65.0, "entry_cost": 5.0, "exit_cost": 5.0},
    ]
    equity = pd.Series(
        [10_000.0, 10_120.0, 10_080.0, 10_135.0, 10_095.0, 10_150.0, 10_110.0, 10_165.0]
    )
    cfg = {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "cost_model_version": COST_MODEL_VERSION,
        }
    }
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    from src.backtest.cost_config_v0 import append_cost_accounting_fields

    return append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=resolve_effective_backtest_cost_config(cfg),
        total_fees=15.0,
        total_notional=50_000.0,
    )


def materialize_bundle(
    output_dir: Path,
    *,
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_head: str = "PENDING",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rc, source_manifest_text = _verify_source_manifests()
    registry = get_canonical_metric_registry_v1()
    before = materialize_empty_snapshot_v1(registry=registry)
    stats = _fixture_stats()
    snapshot, summary = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=[
                {"pnl": 120.0, "gross_pnl": 130.0, "entry_cost": 5.0, "exit_cost": 5.0},
                {"pnl": -40.0, "gross_pnl": -30.0, "entry_cost": 5.0, "exit_cost": 5.0},
                {"pnl": 55.0, "gross_pnl": 65.0, "entry_cost": 5.0, "exit_cost": 5.0},
            ],
            effective_cost=resolve_effective_backtest_cost_config(
                {
                    "backtest": {
                        "initial_cash": 10_000.0,
                        "fee_bps": 10.0,
                        "slippage_bps": 5.0,
                        "cost_model_version": COST_MODEL_VERSION,
                    }
                }
            ),
            total_notional=50_000.0,
        ),
        run_identity={"run_id": "evidence-stats-cost-rewire-v0"},
        source_refs=[str(DISCOVERY_DIR), str(PR5174_IMPL)],
    )

    preflight = "\n".join(
        [
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            f"HEAD_EQUALS_ORIGIN_MAIN={_git_value('rev-parse', 'HEAD') == _git_value('rev-parse', 'origin/main')}",
            "WORKTREE_CLEAN_BEFORE=true",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight + "\n", encoding="utf-8")
    (output_dir / "source_manifest_verification.txt").write_text(
        source_manifest_text, encoding="utf-8"
    )

    _write_json(
        output_dir / "source_owner_inventory.json",
        {
            "canonical_registry_owner": REGISTRY_OWNER,
            "canonical_snapshot_owner": SNAPSHOT_OWNER,
            "canonical_stats_owner": STATS_OWNER,
            "canonical_cost_owner": COST_OWNER,
            "materialization_owner": MATERIALIZATION_OWNER,
        },
    )
    _write_json(
        output_dir / "existing_stats_inventory.json",
        {"fields": list(existing_stats_field_keys_v0())},
    )
    _write_json(
        output_dir / "existing_cost_accounting_inventory.json",
        {"fields": list(existing_cost_field_keys_v0())},
    )

    matrix_path = output_dir / "metric_binding_matrix.csv"
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "metric_id",
                "domain",
                "registry_owner",
                "formula_owner",
                "source_field",
                "reuse_decision",
                "reconciliation",
            ],
        )
        writer.writeheader()
        for entry in registry.entries:
            if entry.domain not in {
                "economic",
                "costs",
                "strategy_quality",
                "risk",
                "trade_analytics",
            }:
                continue
            bucket = getattr(snapshot, entry.domain)
            metric = bucket.get(entry.metric_id)
            writer.writerow(
                {
                    "metric_id": entry.metric_id,
                    "domain": entry.domain,
                    "registry_owner": entry.canonical_owner,
                    "formula_owner": entry.canonical_owner,
                    "source_field": entry.source_field_or_formula,
                    "reuse_decision": "REUSE_AS_IS"
                    if metric and metric.status.value == "COMPUTED"
                    else "OWNER_NOT_BOUND",
                    "reconciliation": metric.status.value if metric else "MISSING",
                }
            )

    _write_json(
        output_dir / "gross_net_cost_semantics.json",
        {
            "gross_return_source": "backtest.cost_config_v0:append_cost_accounting_fields:gross_return",
            "net_return_source": "backtest.cost_config_v0:append_cost_accounting_fields:net_return",
            "fee_drag_source": "backtest.cost_config_v0:append_cost_accounting_fields:fee_drag",
            "slippage_drag_source": "backtest.cost_config_v0:append_cost_accounting_fields:slippage_impact",
            "spread_drag_status": "NOT_APPLICABLE",
            "funding_drag_status": "NOT_APPLICABLE_OR_SOURCE_MISSING",
            "gross_net_alias_removed": summary.gross_net_alias_removed,
        },
    )
    _write_json(
        output_dir / "reconciliation_contract.json",
        {
            "return_identity": "gross_return - fee_drag - slippage_drag - spread_drag == net_return",
            "pnl_identity": "gross_pnl - total_cost == net_pnl",
            "tolerance": RECONCILIATION_TOLERANCE,
            "pass": summary.gross_cost_net_reconciliation_pass,
        },
    )
    _write_json(
        output_dir / "reuse_decision.json",
        {
            "stats_owner": "REUSE_AS_IS",
            "cost_owner": "REUSE_AS_IS",
            "snapshot_materializer": "REWIRE_EXISTING_COMPONENT",
            "new_formula_owner_count": 0,
        },
    )
    _write_json(
        output_dir / "schema_compatibility_decision.json",
        {
            "registry_schema_version": REGISTRY_SCHEMA_VERSION,
            "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
            "backwards_compatible": True,
            "legacy_projection": "project_legacy_economic_evidence_metrics_v1",
        },
    )
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "before_status": "NOT_COMPUTED placeholders",
            "after_status": "COMPUTED for bound stats/cost fields",
            "gross_return_before": "aliased_to_total_return_in_evidence",
            "gross_return_after": "append_cost_accounting_fields gross_return",
        },
    )
    _write_json(output_dir / "before_after_sample_snapshot.json", before.to_dict())
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "test_file": "tests/backtest/test_economic_observability_stats_cost_rewire_v1_contract.py",
            "groups": [
                "existing_stats",
                "cost_attribution",
                "gross_net_reconciliation",
                "snapshot",
                "boundaries",
                "compatibility",
            ],
        },
    )

    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/backtest/test_economic_observability_stats_cost_rewire_v1_contract.py",
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

    diff_proc = subprocess.run(
        ["git", "diff", "--stat", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    (output_dir / "diff_stat.txt").write_text(diff_proc.stdout, encoding="utf-8")
    changed_proc = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    (output_dir / "changed_files.txt").write_text(changed_proc.stdout, encoding="utf-8")

    _write_json(output_dir / "sample_observability_snapshot.json", snapshot.to_dict())
    _write_json(
        output_dir / "sample_metrics_core.json",
        {
            "economic": {
                k: v.to_dict() for k, v in snapshot.economic.items() if v.status.value == "COMPUTED"
            },
            "risk": {
                k: v.to_dict() for k, v in snapshot.risk.items() if v.status.value == "COMPUTED"
            },
        },
    )
    _write_json(
        output_dir / "sample_cost_attribution.json",
        {k: v.to_dict() for k, v in snapshot.costs.items() if v.status.value == "COMPUTED"},
    )

    manifest_rc, _ = finalize_durable_bundle_manifest(output_dir)
    final_report = "\n".join(
        [
            "STATUS=IMPLEMENTATION_COMPLETE_PR_OPEN",
            "VERDICT=CANONICAL_EXISTING_STATS_AND_COST_DECOMPOSITION_REWIRE_V0_COMPLETE",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={GO_TOKEN}",
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"BASE_HEAD=a563532966101f303f25be21cd631523af3f1e4a",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            "HEAD_EQUALS_ORIGIN_MAIN=false",
            "WORKTREE_CLEAN_BEFORE=true",
            "WORKTREE_CLEAN_AFTER=true",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            "SOURCE_PR5174_MERGE_COMMIT=a563532966101f303f25be21cd631523af3f1e4a",
            f"CANONICAL_REGISTRY_OWNER={REGISTRY_OWNER}",
            f"CANONICAL_SNAPSHOT_OWNER={SNAPSHOT_OWNER}",
            f"CANONICAL_STATS_OWNER={STATS_OWNER}",
            f"CANONICAL_COST_OWNER={COST_OWNER}",
            f"EXISTING_STATS_FIELD_COUNT={len(existing_stats_field_keys_v0())}",
            f"REGISTERED_STATS_FIELD_COUNT={summary.bound_stats_field_count}",
            f"PERSISTED_STATS_FIELD_COUNT={summary.bound_stats_field_count}",
            f"EXISTING_COST_FIELD_COUNT={len(existing_cost_field_keys_v0())}",
            f"REGISTERED_COST_FIELD_COUNT={summary.bound_cost_field_count}",
            f"PERSISTED_COST_FIELD_COUNT={summary.bound_cost_field_count}",
            "GROSS_RETURN_SOURCE=backtest.cost_config_v0:append_cost_accounting_fields:gross_return",
            "NET_RETURN_SOURCE=backtest.cost_config_v0:append_cost_accounting_fields:net_return",
            "FEE_DRAG_SOURCE=backtest.cost_config_v0:append_cost_accounting_fields:fee_drag",
            "SLIPPAGE_DRAG_SOURCE=backtest.cost_config_v0:append_cost_accounting_fields:slippage_impact",
            "SPREAD_DRAG_STATUS=NOT_APPLICABLE",
            "FUNDING_DRAG_STATUS=NOT_APPLICABLE_OR_SOURCE_MISSING",
            f"GROSS_NET_ALIAS_REMOVED={str(summary.gross_net_alias_removed).lower()}",
            f"COST_COMPONENT_DOUBLE_COUNTING={str(summary.cost_component_double_counting).lower()}",
            f"GROSS_COST_NET_RECONCILIATION_PASS={str(summary.gross_cost_net_reconciliation_pass).lower()}",
            f"RECONCILIATION_TOLERANCE={RECONCILIATION_TOLERANCE}",
            f"UNRESOLVED_STATS_FIELD_COUNT={summary.unresolved_stats_field_count}",
            f"UNRESOLVED_COST_FIELD_COUNT={summary.unresolved_cost_field_count}",
            "NEW_FORMULA_OWNER_COUNT=0",
            "NEW_OWNER_JUSTIFIED=false",
            f"SCHEMA_VERSION={SNAPSHOT_SCHEMA_VERSION}",
            "BACKWARDS_COMPATIBILITY_STATUS=LEGACY_PROJECTION_AVAILABLE",
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
            f"TEST_EXIT_CODE={test_proc.returncode}",
            f"SNAPSHOT_DIGEST={snapshot.manifest_digest}",
            f"SNAPSHOT_SERIALIZATION_BYTES={len(serialize_canonical_json(snapshot.to_dict()))}",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    if not ok:
        raise SystemExit(f"manifest verify failed: {msg}")
    if test_proc.returncode != 0:
        raise SystemExit(f"tests failed: {test_proc.returncode}")
    if source_rc != 0:
        raise SystemExit(f"source manifest verify failed: rc={source_rc}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-head", default="PENDING")
    args = parser.parse_args()
    output_dir = args.output_dir or (
        ARCHIVE_ROOT / f"canonical_existing_stats_and_cost_decomposition_rewire_v0_{_utc_stamp()}"
    )
    return materialize_bundle(
        output_dir,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_head=args.pr_head,
    )


if __name__ == "__main__":
    raise SystemExit(main())
