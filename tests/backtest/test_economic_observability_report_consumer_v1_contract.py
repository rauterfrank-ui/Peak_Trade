"""Contract tests for canonical economic report consumer v1."""

from __future__ import annotations

import ast
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EffectiveBacktestCostConfigV0,
    append_cost_accounting_fields,
    resolve_effective_backtest_cost_config,
)
from src.backtest.economic_observability_materialization_v1 import (
    BacktestObservabilityInputsV1,
    materialize_observability_bundle_v1,
    materialize_snapshot_from_backtest_stats_v1,
)
from src.backtest.economic_observability_report_consumer_v1 import (
    REPORT_CONSUMER_OWNER,
    REPORT_DIRECT_METRIC_CALCULATION,
    REPORT_DIRECT_VERDICT_CALCULATION,
    REPORT_SCHEMA_VERSION,
    REPORT_SECTIONS,
    VERDICT_SOURCE,
    CanonicalEconomicReportArtifactsV1,
    EconomicReportVerdictRefV1,
    ReportConsumerError,
    assert_report_module_import_boundary,
    collect_reported_metric_ids,
    render_canonical_economic_report_from_snapshot_dict_v1,
    render_canonical_economic_report_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    CanonicalEconomicObservabilitySnapshotV1,
    MetricMaterializationStatus,
    MetricValueV1,
    compute_snapshot_digest,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.backtest.economic_viability_evidence_v1 import EconomicViabilityStatus
from src.backtest.stats import compute_backtest_stats
from src.backtest.trade_ledger_equity_curve_persistence_v0 import write_observability_bundle_v0
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    RUNBOOK_FUNNEL_FIELDS,
)
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_MODULE = REPO_ROOT / "src/backtest/economic_observability_report_consumer_v1.py"
ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
)
HISTORICAL_SNAPSHOT_DIR = (
    ARCHIVE_ROOT / "canonical_advanced_economic_capability_pack_v0_20260714T203146Z"
)
VERDICT_STATUS = EconomicViabilityStatus.PROMISING.value


def _minimal_cfg() -> dict:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "cost_model_version": COST_MODEL_VERSION,
        }
    }


def _effective_cost() -> EffectiveBacktestCostConfigV0:
    return resolve_effective_backtest_cost_config(_minimal_cfg())


def _fixture_trades() -> list[dict]:
    return [
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
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
            "entry_time": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 4, tzinfo=timezone.utc),
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
            "entry_time": datetime(2024, 1, 5, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 6, tzinfo=timezone.utc),
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


def _fixture_equity() -> pd.Series:
    index = pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC")
    return pd.Series(
        [10_000.0, 10_120.0, 10_080.0, 10_135.0, 10_095.0, 10_150.0, 10_110.0, 10_165.0],
        index=index,
    )


def _compute_stats(trades: list[dict]) -> dict:
    equity = _fixture_equity() if trades else pd.Series([10_000.0, 10_000.0])
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    return append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=_effective_cost(),
        total_fees=10.0 * len(trades),
        total_notional=50_000.0,
    )


def _fixture_funnel_counts(*, trade_count: int = 3) -> dict[str, int]:
    counts = {field: idx + 1 for idx, field in enumerate(RUNBOOK_FUNNEL_FIELDS)}
    counts["trades_opened_count"] = trade_count
    return counts


def _align_trades_to_snapshot(trades: list[dict], *, stats: dict) -> list[dict]:
    snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=_effective_cost(),
            total_notional=50_000.0,
            equity_curve=_fixture_equity(),
        ),
        run_identity={"run_id": "align-trades-to-snapshot"},
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
    return aligned


def _bundle_inputs(**kwargs) -> BacktestObservabilityInputsV1:
    trades = kwargs.pop("trades", _fixture_trades())
    base_stats = kwargs.pop("stats", _compute_stats(trades))
    trades = _align_trades_to_snapshot(trades, stats=base_stats)
    stats = _compute_stats(trades)
    return BacktestObservabilityInputsV1(
        stats=stats,
        initial_equity=10_000.0,
        trades=trades,
        effective_cost=kwargs.pop("effective_cost", _effective_cost()),
        total_notional=kwargs.pop("total_notional", 50_000.0),
        equity_curve=kwargs.pop("equity_curve", _fixture_equity()),
        instrument_id="ETH/USDT",
        run_id="fixture-report-consumer-v1",
        strategy_ref="trend_following/v1",
        funnel_counts=kwargs.pop("funnel_counts", _fixture_funnel_counts(trade_count=len(trades))),
        block_reason_counts=kwargs.pop("block_reason_counts", {"RISK_SIZING_BLOCKED": 3}),
        **kwargs,
    )


def _materialized_snapshot_and_bundle():
    bundle, _ = materialize_observability_bundle_v1(
        _bundle_inputs(),
        run_identity={"run_id": "fixture-report-consumer-v1"},
        source_refs=["fixture_report_consumer_v1"],
        render_canonical_report=True,
        economic_verdict_status=VERDICT_STATUS,
        economic_verdict_source_refs=["economic_viability_evidence_v1.json"],
    )
    snapshot = CanonicalEconomicObservabilitySnapshotV1.from_dict(bundle.snapshot_payload)
    return snapshot, bundle


def _collect_import_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


@pytest.fixture(name="report_bundle")
def fixture_report_bundle():
    return _materialized_snapshot_and_bundle()


def test_report_consumes_snapshot_only(report_bundle) -> None:
    snapshot, bundle = report_bundle
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    assert "REPORT_DIRECT_METRIC_CALCULATION=false" in artifacts.final_report_txt
    assert artifacts.report_summary_json["snapshot_manifest_digest"] == snapshot.manifest_digest


def test_report_verdict_matches_economic_viability_evidence_status(report_bundle) -> None:
    snapshot, _ = report_bundle
    for status in EconomicViabilityStatus:
        artifacts = render_canonical_economic_report_v1(
            snapshot,
            verdict_ref=EconomicReportVerdictRefV1(status=status.value),
        )
        assert f"verdict={status.value}" in artifacts.final_report_txt
        assert artifacts.report_summary_json["verdict"] == status.value


def test_report_contains_no_direct_verdict_formula() -> None:
    source = REPORT_MODULE.read_text(encoding="utf-8")
    forbidden = ("_resolve_status", "evaluate_economic_validity", "build_economic_viability")
    for token in forbidden:
        assert token not in source


def test_report_contains_no_direct_metric_formula() -> None:
    source = REPORT_MODULE.read_text(encoding="utf-8")
    forbidden = (
        "compute_backtest_stats",
        "derive_all_metrics",
        "append_cost_accounting_fields",
        "materialize_advanced_economic",
    )
    for token in forbidden:
        assert token not in source


@pytest.mark.parametrize(
    ("test_name", "pattern"),
    [
        ("report_does_not_import_backtest_engine", r"backtest\.engine"),
        ("report_does_not_import_strategy_logic", r"strategy(?!_quality)"),
        ("report_does_not_import_risk_sizing", r"(risk|sizing)"),
        ("report_does_not_import_order_adapter", r"order[_\.]?adapter"),
        ("report_does_not_import_scheduler", r"scheduler"),
        ("report_does_not_import_runtime_authority", r"runtime"),
    ],
)
def test_report_forbidden_imports(test_name: str, pattern: str) -> None:
    modules = _collect_import_modules(REPORT_MODULE)
    regex = re.compile(pattern)
    hits = [module for module in modules if regex.search(module)]
    assert hits == [], f"{test_name} violations={hits}"


def test_all_reported_metrics_exist_in_snapshot_or_explicit_verdict_source(report_bundle) -> None:
    snapshot, _ = report_bundle
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "verdict=" in artifacts.final_report_txt
    for metric_id in collect_reported_metric_ids():
        assert metric_id in artifacts.final_report_txt


def test_zero_and_null_render_differently() -> None:
    snapshot = materialize_empty_snapshot_v1(
        run_identity={"run_id": "zero-null-semantics"},
    )
    snapshot.economic["gross_return"] = MetricValueV1(
        value=0.0,
        unit="ratio",
        status=MetricMaterializationStatus.COMPUTED,
        owner="fixture",
        source="fixture",
        formula_version="v0",
        sample_count=1,
        quality_flags=(),
        reason_codes=(),
    )
    snapshot.economic["net_return"] = MetricValueV1(
        value=None,
        unit="ratio",
        status=MetricMaterializationStatus.NOT_COMPUTED,
        owner="fixture",
        source="fixture",
        formula_version="v0",
        sample_count=None,
        quality_flags=(),
        reason_codes=("METRIC_NOT_COMPUTED_AWAITING_REWIRE",),
    )
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "gross_return=0 status=COMPUTED" in artifacts.final_report_txt
    assert "net_return=NULL status=NOT_COMPUTED" in artifacts.final_report_txt


def test_not_computed_has_reason() -> None:
    snapshot = materialize_empty_snapshot_v1(run_identity={"run_id": "not-computed"})
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "reason_codes=" in artifacts.final_report_txt
    assert "NOT_COMPUTED" in artifacts.final_report_txt


def test_not_applicable_has_reason() -> None:
    snapshot = materialize_empty_snapshot_v1(run_identity={"run_id": "not-applicable"})
    snapshot.risk["ulcer_index"] = MetricValueV1(
        value=None,
        unit="index",
        status=MetricMaterializationStatus.NOT_APPLICABLE,
        owner="fixture",
        source="fixture",
        formula_version="v0",
        sample_count=None,
        quality_flags=(),
        reason_codes=("METRIC_NOT_APPLICABLE_IN_CURRENT_SCOPE",),
    )
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "ulcer_index=NULL status=NOT_APPLICABLE" in artifacts.final_report_txt
    assert "METRIC_NOT_APPLICABLE_IN_CURRENT_SCOPE" in artifacts.final_report_txt


def test_insufficient_data_has_reason() -> None:
    snapshot = materialize_empty_snapshot_v1(run_identity={"run_id": "insufficient-data"})
    snapshot.economic["cost_to_gross_edge_ratio"] = MetricValueV1(
        value=None,
        unit="ratio",
        status=MetricMaterializationStatus.INSUFFICIENT_DATA,
        owner="fixture",
        source="fixture",
        formula_version="v0",
        sample_count=0,
        quality_flags=(),
        reason_codes=("ZERO_GROSS_EDGE",),
    )
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "ZERO_GROSS_EDGE" in artifacts.final_report_txt
    assert "status=INSUFFICIENT_DATA" in artifacts.final_report_txt


def test_missing_required_source_fails_closed() -> None:
    snapshot = materialize_empty_snapshot_v1(run_identity={"run_id": "missing-verdict"})
    payload = snapshot.to_dict()
    snapshot.manifest_digest = compute_snapshot_digest(payload)
    with pytest.raises(ReportConsumerError, match="VERDICT_SOURCE_MISSING"):
        render_canonical_economic_report_v1(
            snapshot, verdict_ref=EconomicReportVerdictRefV1(status="")
        )


def test_gross_cost_net_reconciliation_rendered(report_bundle) -> None:
    _, bundle = report_bundle
    assert "gross_pnl_reconciliation_pass" in bundle.final_report
    assert "net_pnl_reconciliation_pass" in bundle.final_report
    assert "total_cost_reconciliation_pass" in bundle.final_report


def test_trade_ledger_reconciliation_rendered(report_bundle) -> None:
    _, bundle = report_bundle
    assert "trade_count_reconciliation_pass" in bundle.final_report


def test_decision_funnel_all_available_stages_rendered(report_bundle) -> None:
    snapshot, _ = report_bundle
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "## decision_funnel" in artifacts.final_report_txt
    for metric_id in sorted(snapshot.decision_funnel):
        assert metric_id in artifacts.final_report_txt


def test_robustness_status_rendered_without_recalculation(report_bundle) -> None:
    snapshot, _ = report_bundle
    source = REPORT_MODULE.read_text(encoding="utf-8")
    assert "monte_carlo" not in source or "lookup_metric" in source
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "robustness_status" in artifacts.final_report_txt


def test_provenance_complete(report_bundle) -> None:
    snapshot, _ = report_bundle
    artifacts = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
    )
    assert "manifest_digest=" in artifacts.final_report_txt
    assert "source_evidence_refs=" in artifacts.final_report_txt


def test_markdown_render_deterministic(report_bundle) -> None:
    snapshot, bundle = report_bundle
    first = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    second = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    assert first.final_report_md == second.final_report_md


def test_text_render_deterministic(report_bundle) -> None:
    snapshot, bundle = report_bundle
    first = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    second = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    assert first.final_report_txt == second.final_report_txt


def test_second_materialization_diff_empty(report_bundle) -> None:
    snapshot, bundle = report_bundle
    first = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    second = render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(status=VERDICT_STATUS),
        reconciliation_payload=bundle.reconciliation_payload,
    )
    assert first.report_digest == second.report_digest


def test_report_files_in_manifest(report_bundle, tmp_path: Path) -> None:
    _, bundle = report_bundle
    write_observability_bundle_v0(bundle, tmp_path)
    assert (tmp_path / "final_report.txt").is_file()
    assert (tmp_path / "final_report.md").is_file()
    assert (tmp_path / "report_summary.json").is_file()


def test_manifest_verify_rc_zero(report_bundle, tmp_path: Path) -> None:
    from scripts.ops.primary_evidence_retention_v0 import (
        finalize_durable_bundle_manifest,
        verify_manifest_sha256,
    )

    _, bundle = report_bundle
    write_observability_bundle_v0(bundle, tmp_path)
    rc, _ = finalize_durable_bundle_manifest(tmp_path)
    ok, _ = verify_manifest_sha256(tmp_path)
    assert rc == 0
    assert ok


def test_backwards_compatibility_preserved() -> None:
    bundle, _ = materialize_observability_bundle_v1(
        _bundle_inputs(),
        run_identity={"run_id": "backwards-compat"},
        render_canonical_report=False,
    )
    assert bundle.final_report == ""
    assert bundle.final_report_md == ""
    assert bundle.report_summary_json == {}


def test_historical_evidence_unchanged() -> None:
    historical_snapshot_path = HISTORICAL_SNAPSHOT_DIR / "OBSERVABILITY_SNAPSHOT.json"
    if not historical_snapshot_path.is_file():
        pytest.skip("historical snapshot fixture unavailable")
    original_text = historical_snapshot_path.read_text(encoding="utf-8")
    payload = json.loads(original_text)
    copied = copy.deepcopy(payload)
    render_canonical_economic_report_from_snapshot_dict_v1(
        payload,
        verdict_status=VERDICT_STATUS,
    )
    assert serialize_canonical_json(payload) == serialize_canonical_json(copied)


def test_report_sections_implemented() -> None:
    assert len(REPORT_SECTIONS) == 10


def test_no_runtime_import_boundary_violation() -> None:
    assert scan_file_import_boundary(REPORT_MODULE, repo_root=REPO_ROOT) == []


def test_assert_report_module_import_boundary() -> None:
    assert assert_report_module_import_boundary() == []


def test_bundle_integration_fail_closed_without_verdict() -> None:
    with pytest.raises(ReportConsumerError, match="VERDICT_SOURCE_MISSING"):
        materialize_observability_bundle_v1(
            _bundle_inputs(),
            render_canonical_report=True,
            validate_reconciliation=False,
        )
