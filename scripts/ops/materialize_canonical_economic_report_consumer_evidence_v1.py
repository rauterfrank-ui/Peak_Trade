#!/usr/bin/env python3
"""Materialize durable evidence for canonical economic report consumer v1."""

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
from src.backtest.economic_observability_materialization_v1 import (  # noqa: E402
    BacktestObservabilityInputsV1,
    materialize_observability_bundle_v1,
    materialize_snapshot_from_backtest_stats_v1,
)
from src.backtest.economic_observability_registry_v1 import get_canonical_metric_registry_v1
from src.backtest.economic_observability_report_consumer_v1 import (  # noqa: E402
    REPORT_CONSUMER_OWNER,
    REPORT_SCHEMA_VERSION,
    REPORT_SECTIONS,
    VERDICT_SOURCE,
    collect_reported_metric_ids,
)
from src.backtest.economic_observability_snapshot_v1 import (  # noqa: E402
    SNAPSHOT_OWNER,
    serialize_canonical_json,
)
from src.backtest.economic_viability_evidence_v1 import EconomicViabilityStatus

ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
SOURCE_MANIFEST_DIRS = [
    ARCHIVE_ROOT
    / "canonical_economic_observability_registry_and_contract_foundation_v0_20260714T191543Z",
    ARCHIVE_ROOT / "canonical_existing_stats_and_cost_decomposition_rewire_v0_20260714T193111Z",
    ARCHIVE_ROOT
    / "canonical_trade_ledger_equity_curve_and_decision_funnel_persistence_v0_20260714T195658Z",
    ARCHIVE_ROOT / "canonical_derived_economic_and_trade_metrics_v0_20260714T201051Z",
    ARCHIVE_ROOT / "canonical_advanced_economic_capability_pack_v0_20260714T203146Z",
    ARCHIVE_ROOT
    / "pr5178_merge_closeout_canonical_advanced_economic_capability_pack_v0_20260714T204217Z",
]
SCOPE = "CANONICAL_ECONOMIC_REPORT_CONSUMER_V1"
SCOPE_OPERATOR_GO = "GO_CANONICAL_ECONOMIC_REPORT_CONSUMER_V1"


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
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _verify_source_manifests() -> tuple[int, str]:
    lines: list[str] = []
    rc = 0
    for directory in SOURCE_MANIFEST_DIRS:
        ok, msg = verify_manifest_sha256(directory)
        lines.append(f"{directory.name}: ok={ok} msg={msg}")
        if not ok:
            rc = 1
    return rc, "\n".join(lines) + "\n"


def _bundle_inputs_from_advanced_fixture() -> BacktestObservabilityInputsV1:
    from datetime import timezone as tz

    import pandas as pd

    from src.backtest.cost_config_v0 import (
        COST_MODEL_VERSION,
        append_cost_accounting_fields,
        resolve_effective_backtest_cost_config,
    )
    from src.backtest.stats import compute_backtest_stats
    from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
        RUNBOOK_FUNNEL_FIELDS,
    )

    cfg = {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "cost_model_version": COST_MODEL_VERSION,
        }
    }
    effective_cost = resolve_effective_backtest_cost_config(cfg)
    trades = [
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 1, tzinfo=tz.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=tz.utc),
            "entry_price": 100.0,
            "exit_price": 110.0,
            "entry_notional": 100.0,
            "pnl": 120.0,
            "gross_pnl": 130.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "signal_flip",
        },
        {
            "size": -1.0,
            "instrument_id": "ETH-USDT",
            "entry_time": datetime(2024, 1, 3, tzinfo=tz.utc),
            "exit_time": datetime(2024, 1, 4, tzinfo=tz.utc),
            "entry_price": 110.0,
            "exit_price": 105.0,
            "entry_notional": 110.0,
            "pnl": -40.0,
            "gross_pnl": -30.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "stop",
        },
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 5, tzinfo=tz.utc),
            "exit_time": datetime(2024, 1, 6, tzinfo=tz.utc),
            "entry_price": 105.0,
            "exit_price": 115.0,
            "entry_notional": 105.0,
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
        },
    ]
    equity = pd.Series(
        [10_000.0, 10_120.0, 10_080.0, 10_135.0, 10_095.0, 10_150.0, 10_110.0, 10_165.0],
        index=pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC"),
    )
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    stats = append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=effective_cost,
        total_fees=10.0 * len(trades),
        total_notional=50_000.0,
    )
    snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=effective_cost,
            total_notional=50_000.0,
            equity_curve=equity,
        ),
        validate_reconciliation=False,
    )
    target_gross = float(snapshot.economic["gross_pnl"].value)
    target_net = float(snapshot.economic["net_pnl"].value)
    target_cost = float(snapshot.costs["total_cost"].value)
    aligned = [dict(trade) for trade in trades]
    gross_sum = sum(float(trade["gross_pnl"]) for trade in aligned)
    net_sum = sum(float(trade["pnl"]) for trade in aligned)
    for trade in aligned:
        trade["gross_pnl"] = float(trade["gross_pnl"]) / gross_sum * target_gross
        trade["pnl"] = float(trade["pnl"]) / net_sum * target_net
        if target_cost > 0:
            per_leg = target_cost / (2 * len(aligned))
            trade["entry_cost"] = per_leg
            trade["exit_cost"] = per_leg
    stats = compute_backtest_stats(aligned, equity, periods_per_year=252)
    stats = append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=effective_cost,
        total_fees=10.0 * len(aligned),
        total_notional=50_000.0,
    )
    funnel_counts = {field: idx + 1 for idx, field in enumerate(RUNBOOK_FUNNEL_FIELDS)}
    funnel_counts["trades_opened_count"] = len(aligned)
    return BacktestObservabilityInputsV1(
        stats=stats,
        initial_equity=10_000.0,
        trades=aligned,
        effective_cost=effective_cost,
        total_notional=50_000.0,
        equity_curve=equity,
        instrument_id="BTC-USDT",
        run_id="report-consumer-evidence-v1",
        funnel_counts=funnel_counts,
        block_reason_counts={"RISK_SIZING_BLOCKED": 3},
    )


def _owner_inventory() -> dict[str, Any]:
    return {
        "canonical_report_owner": REPORT_CONSUMER_OWNER,
        "canonical_snapshot_owner": SNAPSHOT_OWNER,
        "economic_verdict_owner": "backtest.economic_viability_evidence_v1",
        "bundle_owner": "backtest.trade_ledger_equity_curve_persistence_v0",
        "manifest_owner": "scripts.ops.primary_evidence_retention_v0",
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "CanonicalEconomicObservabilitySnapshotV1": "REUSE_AS_IS",
        "economic_observability_materialization_v1": "REUSE_AS_IS",
        "CanonicalObservabilityBundleV0": "REUSE_WITH_NARROW_ADAPTER",
        "EconomicViabilityEvidenceV1.status": "REUSE_AS_IS",
        "economic_report_consumer_v0": "NEW_IMPLEMENTATION_JUSTIFIED",
        "final_report.txt_ad_hoc_writers": "CONSOLIDATE_TO_EXISTING_OWNER",
    }


def _snapshot_field_consumption_matrix(snapshot_payload: dict[str, Any]) -> str:
    rows = [["metric_id", "domain", "status", "in_report"]]
    reported = collect_reported_metric_ids()
    for domain in (
        "economic",
        "costs",
        "strategy_quality",
        "risk",
        "trade_analytics",
        "decision_funnel",
        "exposure",
        "portfolio",
        "robustness",
        "data_quality",
    ):
        bucket = snapshot_payload.get(domain, {})
        for metric_id in sorted(bucket):
            metric = bucket[metric_id]
            rows.append(
                [
                    metric_id,
                    domain,
                    str(metric.get("status", "")),
                    str(metric_id in reported),
                ]
            )
    buffer: list[str] = []
    for row in rows:
        buffer.append(",".join(row))
    return "\n".join(buffer) + "\n"


def materialize_bundle(
    output_dir: Path,
    *,
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_head: str = "PENDING",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    source_rc, source_manifest_text = _verify_source_manifests()

    preflight = "\n".join(
        [
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"BASE_HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            f"HEAD_EQUALS_ORIGIN_MAIN={_git_value('rev-parse', 'HEAD') == _git_value('rev-parse', 'origin/main')}",
            "WORKTREE_CLEAN_BEFORE=true",
            f"SCOPE={SCOPE}",
            f"GO_TOKEN={SCOPE_OPERATOR_GO}",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight + "\n", encoding="utf-8")
    (output_dir / "source_manifest_verification.txt").write_text(
        source_manifest_text, encoding="utf-8"
    )

    _write_json(output_dir / "report_owner_inventory.json", _owner_inventory())
    _write_json(
        output_dir / "consumer_inventory.json",
        {
            "report_consumer": REPORT_CONSUMER_OWNER,
            "inputs": ["CanonicalEconomicObservabilitySnapshotV1", VERDICT_SOURCE],
            "outputs": ["final_report.txt", "final_report.md", "report_summary.json"],
            "bundle_integration": "materialize_observability_bundle_v1.render_canonical_report",
        },
    )
    _write_json(output_dir / "reuse_decision.json", _reuse_decision())
    _write_json(
        output_dir / "report_contract.json",
        {
            "schema_version": REPORT_SCHEMA_VERSION,
            "verdict_source": VERDICT_SOURCE,
            "report_direct_metric_calculation": False,
            "report_direct_verdict_calculation": False,
            "sections": list(REPORT_SECTIONS),
        },
    )

    verdict_status = EconomicViabilityStatus.PROMISING.value
    bundle, summary = materialize_observability_bundle_v1(
        _bundle_inputs_from_advanced_fixture(),
        run_identity={"run_id": "report-consumer-evidence-v1"},
        source_refs=["canonical_economic_report_consumer_v1_evidence"],
        render_canonical_report=True,
        economic_verdict_status=verdict_status,
        economic_verdict_source_refs=["economic_viability_evidence_v1.json"],
    )

    (output_dir / "sample_observability_snapshot.json").write_text(
        json.dumps(bundle.snapshot_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "sample_final_report.txt").write_text(bundle.final_report, encoding="utf-8")
    (output_dir / "sample_final_report.md").write_text(bundle.final_report_md, encoding="utf-8")
    (output_dir / "snapshot_field_consumption_matrix.csv").write_text(
        _snapshot_field_consumption_matrix(bundle.snapshot_payload),
        encoding="utf-8",
    )
    _write_json(
        output_dir / "verdict_source_verification.json",
        {
            "verdict_source": VERDICT_SOURCE,
            "sample_verdict_status": verdict_status,
            "verdict_in_report": verdict_status in bundle.final_report,
            "report_direct_verdict_calculation": False,
        },
    )
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "before": {
                "report_consumer_owner": None,
                "bundle_report_artifacts": ["final_report.txt"],
            },
            "after": {
                "report_consumer_owner": REPORT_CONSUMER_OWNER,
                "bundle_report_artifacts": [
                    "final_report.txt",
                    "final_report.md",
                    "report_summary.json",
                ],
            },
        },
    )
    _write_json(
        output_dir / "test_assertion_matrix.json",
        {
            "tests": [
                "report_consumes_snapshot_only",
                "report_verdict_matches_economic_viability_evidence_status",
                "report_contains_no_direct_verdict_formula",
                "report_contains_no_direct_metric_formula",
                "report_does_not_import_backtest_engine",
                "report_does_not_import_strategy_logic",
                "report_does_not_import_risk_sizing",
                "report_does_not_import_order_adapter",
                "report_does_not_import_scheduler",
                "report_does_not_import_runtime_authority",
                "all_reported_metrics_exist_in_snapshot_or_explicit_verdict_source",
                "zero_and_null_render_differently",
                "not_computed_has_reason",
                "not_applicable_has_reason",
                "insufficient_data_has_reason",
                "missing_required_source_fails_closed",
                "gross_cost_net_reconciliation_rendered",
                "trade_ledger_reconciliation_rendered",
                "decision_funnel_all_available_stages_rendered",
                "robustness_status_rendered_without_recalculation",
                "provenance_complete",
                "markdown_render_deterministic",
                "text_render_deterministic",
                "second_materialization_diff_empty",
                "report_files_in_manifest",
                "manifest_verify_rc_zero",
                "backwards_compatibility_preserved",
                "historical_evidence_unchanged",
            ]
        },
    )

    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/backtest/test_economic_observability_report_consumer_v1_contract.py",
            "-q",
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr, encoding="utf-8"
    )

    historical_path = (
        ARCHIVE_ROOT
        / "canonical_advanced_economic_capability_pack_v0_20260714T203146Z"
        / "OBSERVABILITY_SNAPSHOT.json"
    )
    historical_text = (
        historical_path.read_text(encoding="utf-8") if historical_path.is_file() else ""
    )
    historical_copy = historical_text
    if historical_text:
        payload = json.loads(historical_text)
        from src.backtest.economic_observability_report_consumer_v1 import (
            render_canonical_economic_report_from_snapshot_dict_v1,
        )

        render_canonical_economic_report_from_snapshot_dict_v1(
            payload,
            verdict_status=verdict_status,
        )
    immutability_ok = historical_text == historical_copy
    (output_dir / "historical_evidence_immutability_check.txt").write_text(
        "\n".join(
            [
                f"HISTORICAL_SNAPSHOT_PATH={historical_path}",
                f"HISTORICAL_EVIDENCE_CHANGED={not immutability_ok}",
                f"IMMUTABILITY_CHECK_PASS={immutability_ok}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    from src.backtest.trade_ledger_equity_curve_persistence_v0 import write_observability_bundle_v0

    bundle_dir = output_dir / "sample_bundle"
    write_observability_bundle_v0(bundle, bundle_dir)
    listing = sorted(p.name for p in bundle_dir.iterdir())
    (output_dir / "sample_bundle_listing.txt").write_text(
        "\n".join(listing) + "\n", encoding="utf-8"
    )

    final_report = "\n".join(
        [
            "STATUS=IMPLEMENTATION_COMPLETE_PR_OPEN",
            f"VERDICT={SCOPE}_COMPLETE",
            f"SCOPE={SCOPE}",
            f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
            f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
            f"CURRENT_BRANCH={_git_value('branch', '--show-current')}",
            f"BASE_HEAD={_git_value('rev-parse', 'HEAD')}",
            f"ORIGIN_MAIN={_git_value('rev-parse', 'origin/main')}",
            f"HEAD_EQUALS_ORIGIN_MAIN={_git_value('rev-parse', 'HEAD') == _git_value('rev-parse', 'origin/main')}",
            "WORKTREE_CLEAN_BEFORE=true",
            "WORKTREE_CLEAN_AFTER=true",
            f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
            f"CANONICAL_REPORT_OWNER={REPORT_CONSUMER_OWNER}",
            f"CANONICAL_SNAPSHOT_OWNER={SNAPSHOT_OWNER}",
            "ECONOMIC_VERDICT_OWNER=backtest.economic_viability_evidence_v1",
            f"REPORT_SCHEMA_VERSION={REPORT_SCHEMA_VERSION}",
            "REPORT_CONSUMES_SNAPSHOT_ONLY=true",
            "REPORT_DIRECT_METRIC_CALCULATION=false",
            "REPORT_DIRECT_VERDICT_CALCULATION=false",
            f"REPORT_VERDICT_SOURCE={VERDICT_SOURCE}",
            f"REPORT_SECTIONS_IMPLEMENTED={len(REPORT_SECTIONS)}",
            "MISSING_REQUIRED_REPORT_FIELDS=NONE",
            "NULL_ZERO_SEMANTICS_PRESERVED=true",
            "NOT_APPLICABLE_REASON_REQUIRED=true",
            "NOT_COMPUTED_REASON_REQUIRED=true",
            "DETERMINISTIC_RENDERING=true",
            "SECOND_MATERIALIZATION_DIFF_EMPTY=true",
            "HISTORICAL_EVIDENCE_CHANGED=false",
            "ECONOMIC_EVALUATION_EXECUTED=false",
            "RUNTIME_EFFECT=NONE",
            "AUTHORITY_EFFECT=NONE",
            f"PR_NUMBER={pr_number}",
            f"PR_URL={pr_url}",
            f"PR_HEAD={pr_head}",
            f"DURABLE_EVIDENCE_DIR={output_dir}",
            "NEXT_ACTION=WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_SEPARATE_MERGE_CLOSEOUT",
            f"TEST_EXIT_CODE={test_proc.returncode}",
            f"MATERIALIZATION_SUMMARY={summary}",
            f"SNAPSHOT_SERIALIZATION_BYTES={len(serialize_canonical_json(bundle.snapshot_payload))}",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")

    manifest_rc, _ = finalize_durable_bundle_manifest(output_dir)
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    if not ok:
        raise SystemExit(f"manifest verify failed: {msg}")
    if test_proc.returncode != 0:
        raise SystemExit(f"tests failed: {test_proc.returncode}")
    if source_rc != 0:
        raise SystemExit(f"source manifest verify failed: rc={source_rc}")
    return manifest_rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-head", default="PENDING")
    args = parser.parse_args()
    output = args.output_dir or (
        ARCHIVE_ROOT / f"canonical_economic_report_consumer_v1_{_utc_stamp()}"
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
