"""Canonical economic report consumer v1 (offline, authority-neutral).

Consumes ``CanonicalEconomicObservabilitySnapshotV1`` only. Verdict is sourced
exclusively from ``EconomicViabilityEvidenceV1.status`` via an explicit reference
passed by the caller — no direct metric formulas or verdict calculation here.
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.backtest.economic_observability_snapshot_v1 import (
    SNAPSHOT_DOMAIN_KEYS,
    CanonicalEconomicObservabilitySnapshotV1,
    MetricMaterializationStatus,
    MetricValueV1,
    REASON_REQUIRED_STATUSES,
    SnapshotContractError,
    serialize_canonical_json,
)

REPORT_SCHEMA_VERSION = "canonical_economic_report_snapshot_consumer.v1"
REPORT_CONSUMER_OWNER = "backtest.economic_observability_report_consumer_v1"
VERDICT_SOURCE = "EconomicViabilityEvidenceV1.status"
REPORT_DIRECT_METRIC_CALCULATION = False
REPORT_DIRECT_VERDICT_CALCULATION = False

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "backtest.engine",
    "strategy",
    "risk",
    "sizing",
    "order_adapter",
    "order.adapter",
    "scheduler",
    "runtime",
    "governance",
    "execution",
)

EXECUTIVE_FIELDS: tuple[tuple[str, str], ...] = (
    ("gross_return", "economic"),
    ("net_return", "economic"),
    ("gross_pnl", "economic"),
    ("net_pnl", "economic"),
    ("total_cost", "costs"),
    ("cost_to_gross_edge_ratio", "economic"),
    ("required_gross_edge_for_break_even", "economic"),
    ("net_expectancy", "strategy_quality"),
    ("profit_factor_net", "strategy_quality"),
    ("max_drawdown_percent", "risk"),
    ("sharpe", "risk"),
    ("trade_count", "trade_analytics"),
    ("zero_trade_causal_classification", "decision_funnel"),
    ("robustness_status", "robustness"),
)

ECONOMIC_ATTRIBUTION_FIELDS: tuple[tuple[str, str], ...] = (
    ("gross_pnl", "economic"),
    ("entry_fees", "costs"),
    ("exit_fees", "costs"),
    ("maker_fees", "costs"),
    ("taker_fees", "costs"),
    ("spread_cost", "costs"),
    ("slippage_cost", "costs"),
    ("funding_paid", "costs"),
    ("funding_received", "costs"),
    ("net_funding", "costs"),
    ("net_pnl", "economic"),
    ("gross_cost_net_reconciliation_status", "economic"),
)

STRATEGY_QUALITY_FIELDS: tuple[tuple[str, str], ...] = (
    ("win_rate", "strategy_quality"),
    ("profit_factor_gross", "strategy_quality"),
    ("profit_factor_net", "strategy_quality"),
    ("expectancy_gross", "strategy_quality"),
    ("expectancy_net", "strategy_quality"),
    ("average_winner", "strategy_quality"),
    ("average_loser", "strategy_quality"),
    ("payoff_ratio", "strategy_quality"),
    ("best_trade", "strategy_quality"),
    ("worst_trade", "strategy_quality"),
)

RISK_FIELDS: tuple[tuple[str, str], ...] = (
    ("max_drawdown_percent", "risk"),
    ("drawdown_duration", "risk"),
    ("sharpe", "risk"),
    ("sortino", "risk"),
    ("calmar", "risk"),
    ("ulcer_index", "risk"),
    ("tail_loss", "risk"),
    ("var_95", "risk"),
    ("cvar_95", "risk"),
)

EXPOSURE_PORTFOLIO_FIELDS: tuple[tuple[str, str], ...] = (
    ("time_in_market", "exposure"),
    ("gross_exposure", "exposure"),
    ("net_exposure", "exposure"),
    ("turnover", "portfolio"),
    ("position_count", "portfolio"),
    ("long_contribution", "portfolio"),
    ("short_contribution", "portfolio"),
    ("concentration_hhi", "portfolio"),
    ("capacity_utilization", "portfolio"),
    ("liquidity_stress_score", "portfolio"),
)

TRADE_ANALYTICS_FIELDS: tuple[tuple[str, str], ...] = (
    ("trade_count", "trade_analytics"),
    ("avg_holding_time", "trade_analytics"),
    ("median_holding_time", "trade_analytics"),
    ("exit_reason_distribution", "trade_analytics"),
    ("mae_bps", "trade_analytics"),
    ("mfe_bps", "trade_analytics"),
    ("pnl_by_side", "trade_analytics"),
    ("pnl_by_instrument", "trade_analytics"),
    ("pnl_by_regime", "trade_analytics"),
    ("pnl_by_exit_reason", "trade_analytics"),
    ("trade_ledger_reconciliation_status", "trade_analytics"),
)

ROBUSTNESS_FIELDS: tuple[tuple[str, str], ...] = (
    ("walk_forward_status", "robustness"),
    ("monte_carlo_status", "robustness"),
    ("stress_status", "robustness"),
    ("parameter_sensitivity_status", "robustness"),
    ("robustness_status", "robustness"),
    ("robustness_reason_codes", "robustness"),
)

REPORT_SECTIONS = (
    "executive_decision_summary",
    "economic_attribution",
    "strategy_quality",
    "risk",
    "decision_funnel",
    "trade_analytics",
    "exposure_and_portfolio",
    "robustness",
    "data_quality_and_missing_metrics",
    "provenance",
)


class ReportConsumerError(ValueError):
    """Raised when report rendering cannot proceed fail-closed."""


@dataclass(frozen=True)
class EconomicReportVerdictRefV1:
    """Explicit verdict reference — caller must supply EVE status, not computed here."""

    status: str
    source: str = VERDICT_SOURCE
    source_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CanonicalEconomicReportArtifactsV1:
    final_report_txt: str
    final_report_md: str
    report_summary_json: dict[str, Any]
    report_digest: str = field(default="")


def _lookup_metric(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    metric_id: str,
    domain_hint: str | None = None,
) -> MetricValueV1 | None:
    if domain_hint:
        bucket = getattr(snapshot, domain_hint, None)
        if isinstance(bucket, dict) and metric_id in bucket:
            return bucket[metric_id]
    for domain in SNAPSHOT_DOMAIN_KEYS:
        if domain == "provenance":
            metric = snapshot.provenance_metrics.get(metric_id)
        else:
            bucket = getattr(snapshot, domain)
            metric = bucket.get(metric_id) if isinstance(bucket, dict) else None
        if metric is not None:
            return metric
    return None


def _render_metric_line(metric_id: str, metric: MetricValueV1 | None) -> str:
    if metric is None:
        return (
            f"{metric_id}=ABSENT status=SOURCE_MISSING "
            f"value=NULL reason_codes=METRIC_NOT_IN_SNAPSHOT"
        )
    value_repr = "NULL" if metric.value is None else str(metric.value)
    if metric.value == 0 and metric.status in {
        MetricMaterializationStatus.COMPUTED,
        MetricMaterializationStatus.RECONSTRUCTED,
    }:
        value_repr = "0"
    reason = ",".join(metric.reason_codes) if metric.reason_codes else "NONE"
    return (
        f"{metric_id}={value_repr} status={metric.status.value} unit={metric.unit} "
        f"owner={metric.owner} reason_codes={reason}"
    )


def _render_metric_markdown(metric_id: str, metric: MetricValueV1 | None) -> str:
    return f"| `{metric_id}` | {_render_metric_line(metric_id, metric).split('=', 1)[1]} |"


def _metric_summary_dict(metric_id: str, metric: MetricValueV1 | None) -> dict[str, Any]:
    if metric is None:
        return {
            "metric_id": metric_id,
            "value": None,
            "status": MetricMaterializationStatus.SOURCE_MISSING.value,
            "reason_codes": ["METRIC_NOT_IN_SNAPSHOT"],
            "owner": REPORT_CONSUMER_OWNER,
        }
    return {
        "metric_id": metric_id,
        "value": metric.value,
        "status": metric.status.value,
        "unit": metric.unit,
        "owner": metric.owner,
        "source": metric.source,
        "reason_codes": list(metric.reason_codes),
    }


def _section_txt(title: str, rows: Sequence[str]) -> list[str]:
    lines = [f"## {title}"]
    lines.extend(rows)
    return lines


def _render_decision_funnel_section(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
) -> list[str]:
    lines = ["## decision_funnel"]
    if not snapshot.decision_funnel:
        lines.append("status=SOURCE_MISSING reason_codes=NO_FUNNEL_METRICS_IN_SNAPSHOT")
        return lines
    for metric_id in sorted(snapshot.decision_funnel):
        lines.append(_render_metric_line(metric_id, snapshot.decision_funnel[metric_id]))
    return lines


def _render_data_quality_table(snapshot: CanonicalEconomicObservabilitySnapshotV1) -> list[str]:
    lines = ["## data_quality_and_missing_metrics"]
    lines.append("metric|status|reason|owner|next_action")
    rows: list[tuple[str, MetricValueV1]] = []
    for domain in SNAPSHOT_DOMAIN_KEYS:
        if domain == "provenance":
            bucket = snapshot.provenance_metrics
        else:
            bucket = getattr(snapshot, domain)
        if not isinstance(bucket, dict):
            continue
        for metric_id, metric in sorted(bucket.items()):
            if metric.status not in {
                MetricMaterializationStatus.COMPUTED,
                MetricMaterializationStatus.RECONSTRUCTED,
            }:
                rows.append((metric_id, metric))
    if not rows:
        lines.append("ALL_MATERIALIZED|COMPUTED|NONE|snapshot|NONE")
        return lines
    for metric_id, metric in rows:
        reason = ",".join(metric.reason_codes) if metric.reason_codes else "NONE"
        next_action = (
            "AWAIT_OWNER_BINDING"
            if metric.status is MetricMaterializationStatus.NOT_COMPUTED
            else "NONE"
        )
        lines.append(f"{metric_id}|{metric.status.value}|{reason}|{metric.owner}|{next_action}")
    return lines


def _render_provenance_section(snapshot: CanonicalEconomicObservabilitySnapshotV1) -> list[str]:
    lines = ["## provenance"]
    provenance = dict(snapshot.provenance)
    provenance.pop("metrics", None)
    for key in sorted(provenance):
        lines.append(f"{key}={json.dumps(provenance[key], sort_keys=True, default=str)}")
    run_identity = snapshot.run_identity
    for key in sorted(run_identity):
        lines.append(
            f"run_identity.{key}={json.dumps(run_identity[key], sort_keys=True, default=str)}"
        )
    if snapshot.manifest_digest:
        lines.append(f"manifest_digest={snapshot.manifest_digest}")
    if snapshot.source_refs:
        lines.append(f"source_evidence_refs={','.join(sorted(snapshot.source_refs))}")
    for metric_id in sorted(snapshot.provenance_metrics):
        lines.append(_render_metric_line(metric_id, snapshot.provenance_metrics[metric_id]))
    return lines


def _validate_verdict_ref(
    verdict_ref: EconomicReportVerdictRefV1 | None,
) -> EconomicReportVerdictRefV1:
    if verdict_ref is None or not str(verdict_ref.status).strip():
        raise ReportConsumerError(
            "VERDICT_SOURCE_MISSING:EconomicViabilityEvidenceV1.status required"
        )
    if verdict_ref.source != VERDICT_SOURCE:
        raise ReportConsumerError(
            f"VERDICT_SOURCE_INVALID:expected={VERDICT_SOURCE}:actual={verdict_ref.source}"
        )
    return verdict_ref


def _validate_snapshot(snapshot: CanonicalEconomicObservabilitySnapshotV1) -> None:
    if not snapshot.schema_version:
        raise ReportConsumerError("SNAPSHOT_SOURCE_MISSING:schema_version required")
    if not snapshot.manifest_digest:
        raise ReportConsumerError("SNAPSHOT_NOT_MATERIALIZED:manifest_digest missing")


def render_canonical_economic_report_v1(
    snapshot: CanonicalEconomicObservabilitySnapshotV1,
    *,
    verdict_ref: EconomicReportVerdictRefV1,
    reconciliation_payload: Mapping[str, Any] | None = None,
) -> CanonicalEconomicReportArtifactsV1:
    """Render deterministic report artifacts from a materialized snapshot."""
    _validate_snapshot(snapshot)
    resolved_verdict = _validate_verdict_ref(verdict_ref)

    txt_lines: list[str] = [
        f"REPORT_SCHEMA_VERSION={REPORT_SCHEMA_VERSION}",
        f"REPORT_CONSUMER_OWNER={REPORT_CONSUMER_OWNER}",
        f"REPORT_VERDICT_SOURCE={VERDICT_SOURCE}",
        f"REPORT_DIRECT_METRIC_CALCULATION={str(REPORT_DIRECT_METRIC_CALCULATION).lower()}",
        f"REPORT_DIRECT_VERDICT_CALCULATION={str(REPORT_DIRECT_VERDICT_CALCULATION).lower()}",
        f"verdict={resolved_verdict.status}",
        f"verdict_source={resolved_verdict.source}",
    ]
    if resolved_verdict.source_evidence_refs:
        txt_lines.append(
            f"verdict_source_evidence_refs={','.join(sorted(resolved_verdict.source_evidence_refs))}"
        )

    exec_lines = [f"verdict={resolved_verdict.status}"]
    exec_metrics: dict[str, Any] = {"verdict": resolved_verdict.status}
    for metric_id, domain in EXECUTIVE_FIELDS:
        metric = _lookup_metric(snapshot, metric_id, domain)
        exec_lines.append(_render_metric_line(metric_id, metric))
        exec_metrics[metric_id] = _metric_summary_dict(metric_id, metric)
    txt_lines.extend(_section_txt("executive_decision_summary", exec_lines))

    attr_lines = []
    for metric_id, domain in ECONOMIC_ATTRIBUTION_FIELDS:
        attr_lines.append(
            _render_metric_line(metric_id, _lookup_metric(snapshot, metric_id, domain))
        )
    if reconciliation_payload:
        for key in (
            "gross_pnl_reconciliation_pass",
            "net_pnl_reconciliation_pass",
            "total_cost_reconciliation_pass",
            "trade_count_reconciliation_pass",
        ):
            if key in reconciliation_payload:
                attr_lines.append(f"reconciliation.{key}={reconciliation_payload[key]}")
    txt_lines.extend(_section_txt("economic_attribution", attr_lines))

    for section_title, fields in (
        ("strategy_quality", STRATEGY_QUALITY_FIELDS),
        ("risk", RISK_FIELDS),
        ("exposure_and_portfolio", EXPOSURE_PORTFOLIO_FIELDS),
        ("trade_analytics", TRADE_ANALYTICS_FIELDS),
        ("robustness", ROBUSTNESS_FIELDS),
    ):
        section_lines = [
            _render_metric_line(metric_id, _lookup_metric(snapshot, metric_id, domain))
            for metric_id, domain in fields
        ]
        txt_lines.extend(_section_txt(section_title, section_lines))

    txt_lines.extend(_render_decision_funnel_section(snapshot))
    txt_lines.extend(_render_data_quality_table(snapshot))
    txt_lines.extend(_render_provenance_section(snapshot))

    md_lines = [
        "# Canonical Economic Report",
        "",
        f"- **schema_version**: `{REPORT_SCHEMA_VERSION}`",
        f"- **consumer_owner**: `{REPORT_CONSUMER_OWNER}`",
        f"- **verdict**: `{resolved_verdict.status}`",
        f"- **verdict_source**: `{VERDICT_SOURCE}`",
        "",
        "## A. Executive Decision Summary",
        "",
        "| metric | detail |",
        "| --- | --- |",
    ]
    md_lines.append(f"| `verdict` | `{resolved_verdict.status}` |")
    for metric_id, domain in EXECUTIVE_FIELDS:
        md_lines.append(
            _render_metric_markdown(metric_id, _lookup_metric(snapshot, metric_id, domain))
        )

    md_lines.extend(["", "## B. Economic Attribution", "", "| metric | detail |", "| --- | --- |"])
    for metric_id, domain in ECONOMIC_ATTRIBUTION_FIELDS:
        md_lines.append(
            _render_metric_markdown(metric_id, _lookup_metric(snapshot, metric_id, domain))
        )

    section_map = (
        ("C. Strategy Quality", STRATEGY_QUALITY_FIELDS),
        ("D. Risk", RISK_FIELDS),
        ("E. Decision Funnel", ()),
        ("F. Trade Analytics", TRADE_ANALYTICS_FIELDS),
        ("G. Exposure and Portfolio", EXPOSURE_PORTFOLIO_FIELDS),
        ("H. Robustness", ROBUSTNESS_FIELDS),
    )
    for title, fields in section_map:
        md_lines.extend(["", f"## {title}", ""])
        if title.endswith("Decision Funnel"):
            md_lines.append("```")
            md_lines.extend(_render_decision_funnel_section(snapshot)[1:])
            md_lines.append("```")
            continue
        md_lines.extend(["| metric | detail |", "| --- | --- |"])
        for metric_id, domain in fields:
            md_lines.append(
                _render_metric_markdown(metric_id, _lookup_metric(snapshot, metric_id, domain))
            )

    md_lines.extend(["", "## I. Data Quality and Missing Metrics", ""])
    md_lines.append("```")
    md_lines.extend(_render_data_quality_table(snapshot)[1:])
    md_lines.append("```")

    md_lines.extend(["", "## J. Provenance", ""])
    md_lines.append("```")
    md_lines.extend(_render_provenance_section(snapshot)[1:])
    md_lines.append("```")

    summary = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "consumer_owner": REPORT_CONSUMER_OWNER,
        "verdict_source": VERDICT_SOURCE,
        "verdict": resolved_verdict.status,
        "verdict_source_evidence_refs": sorted(resolved_verdict.source_evidence_refs),
        "report_direct_metric_calculation": REPORT_DIRECT_METRIC_CALCULATION,
        "report_direct_verdict_calculation": REPORT_DIRECT_VERDICT_CALCULATION,
        "sections": list(REPORT_SECTIONS),
        "executive_decision_summary": exec_metrics,
        "snapshot_manifest_digest": snapshot.manifest_digest,
        "snapshot_schema_version": snapshot.schema_version,
    }

    final_report_txt = "\n".join(txt_lines) + "\n"
    final_report_md = "\n".join(md_lines) + "\n"
    digest = hashlib.sha256(final_report_txt.encode("utf-8")).hexdigest()
    return CanonicalEconomicReportArtifactsV1(
        final_report_txt=final_report_txt,
        final_report_md=final_report_md,
        report_summary_json=summary,
        report_digest=digest,
    )


def render_canonical_economic_report_from_snapshot_dict_v1(
    snapshot_payload: Mapping[str, Any],
    *,
    verdict_status: str,
    verdict_source_refs: Sequence[str] = (),
    reconciliation_payload: Mapping[str, Any] | None = None,
) -> CanonicalEconomicReportArtifactsV1:
    snapshot = CanonicalEconomicObservabilitySnapshotV1.from_dict(snapshot_payload)
    return render_canonical_economic_report_v1(
        snapshot,
        verdict_ref=EconomicReportVerdictRefV1(
            status=verdict_status,
            source_evidence_refs=tuple(sorted(verdict_source_refs)),
        ),
        reconciliation_payload=reconciliation_payload,
    )


def assert_report_module_import_boundary() -> list[str]:
    """Return forbidden import module paths found in this module (for contract tests)."""
    from pathlib import Path

    module_path = Path(__file__)
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _module_forbidden(alias.name):
                    violations.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if _module_forbidden(node.module):
                violations.append(node.module)
    return violations


def _module_forbidden(module: str) -> bool:
    normalized = module.lower().replace("-", "_")
    if normalized.startswith("src.backtest.economic_observability"):
        return False
    if normalized == "src.backtest.economic_observability_snapshot_v1":
        return False
    for token in FORBIDDEN_IMPORT_SUBSTRINGS:
        if token in normalized:
            return True
    return False


def collect_reported_metric_ids() -> frozenset[str]:
    ids: set[str] = set()
    for fields in (
        EXECUTIVE_FIELDS,
        ECONOMIC_ATTRIBUTION_FIELDS,
        STRATEGY_QUALITY_FIELDS,
        RISK_FIELDS,
        EXPOSURE_PORTFOLIO_FIELDS,
        TRADE_ANALYTICS_FIELDS,
        ROBUSTNESS_FIELDS,
    ):
        ids.update(metric_id for metric_id, _ in fields)
    return frozenset(ids)


def validate_reason_semantics(metric: MetricValueV1) -> None:
    if metric.status in REASON_REQUIRED_STATUSES and not metric.reason_codes:
        raise SnapshotContractError(f"metric {metric.status.value} requires reason_codes")
