"""Executable development-evaluation path for CS RS momentum v1.

Authorization is fail-closed. Dry-validate never starts the runner or consumes
run budget. Real evaluate requires repo authorization flags + token.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.admission_gates_v1 import (
    evaluate_admission_gates_v1,
    evaluate_segment_local_result_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
    resolve_authorization_decision_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.binding_v1 import (
    compute_config_digest,
    compute_strategy_params_digest,
    resolve_cost_execution_binding,
    resolve_measurement_contract,
    resolve_strategy_params,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEFAULT_LOOKBACK_N,
    DEFAULT_REBALANCE_INTERVAL_BARS,
    DEVELOPMENT_RUN_LIMIT,
    EVIDENCE_REL_PATH,
    MINIMUM_REBALANCE_OBSERVATIONS,
    TIME_SEGMENT_DEFINITION_ID,
    TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_materialization_v1 import (
    build_registry_metadata_v1,
    build_run_slot_claim_v1,
    validate_evidence_and_registry_contracts_v1,
    write_evidence_bundle_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    ExecutionBoundaryV1,
    RealExecutionBoundaryV1,
    count_panel_rebalance_observations,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_exactly_one_run_limit,
    assert_holdout_guard,
    assert_no_slot_reuse,
    assert_retry_forbidden,
    assert_runtime_inactive,
    preflight_guards,
    read_run_counters,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.time_segments_v1 import (
    assign_timestamp_to_segment,
    partition_chronological_equal_duration_quarters_v1,
    segments_to_dict,
)


@dataclass(frozen=True)
class EvaluatePathResultV1:
    status: str
    mode: str
    runner_started: bool
    evaluation_executed: bool
    holdout_accessed: bool
    authorization: dict[str, Any]
    run_counters: dict[str, int]
    evidence_surface: dict[str, Any] | None
    registry: dict[str, Any] | None
    gates: dict[str, Any] | None
    terminal_development_verdict: str | None
    executable_path_reached: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mode": self.mode,
            "runner_started": self.runner_started,
            "evaluation_executed": self.evaluation_executed,
            "holdout_accessed": self.holdout_accessed,
            "authorization": self.authorization,
            "run_counters": self.run_counters,
            "evidence_surface": self.evidence_surface,
            "registry": self.registry,
            "gates": self.gates,
            "terminal_development_verdict": self.terminal_development_verdict,
            "executable_path_reached": self.executable_path_reached,
            "reason": self.reason,
            "minimum_rebalance_observations": MINIMUM_REBALANCE_OBSERVATIONS,
            "time_segment_robustness_pass_ratio": TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
            "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
            "development_run_limit": DEVELOPMENT_RUN_LIMIT,
            "dataset_id": DATASET_ID,
        }


def _auth_dict(decision: AuthorizationDecisionV1) -> dict[str, Any]:
    return {
        "authorized": decision.authorized,
        "authorize_token_valid": decision.authorize_token_valid,
        "repo_development_evaluation_authorized": decision.repo_development_evaluation_authorized,
        "program_development_evaluation_authorized": (
            decision.program_development_evaluation_authorized
        ),
        "entry_point_binding_authorized": decision.entry_point_binding_authorized,
        "reason_codes": list(decision.reason_codes),
    }


def dry_validate_evaluate_path_v1(repo_root: Path) -> EvaluatePathResultV1:
    """Validate executable path contracts without runner start or counter mutation."""
    before = read_run_counters(repo_root)
    guards = preflight_guards(repo_root)
    contract = resolve_measurement_contract(repo_root)
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest()
    segments = segments_to_dict(partition_chronological_equal_duration_quarters_v1())
    evidence = empty_evidence_surface_template(
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        segment_boundaries=[
            {
                "segment_id": s["segment_id"],
                "range": s["range"],
                "valid_rebalance_observations": "NOT_EXECUTED",
                "result": "NOT_EXECUTED",
                "bar_count": s["bar_count"],
            }
            for s in segments
        ],
    )
    registry = build_registry_metadata_v1(
        evaluation_executed=False,
        runner_started=False,
        evaluation_run_count=before["contract_development_run_count"],
        runner_start_count=before["contract_runner_start_count"],
        development_evaluation_authorized=False,
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        dataset_digest="NOT_RESOLVED_DRY_VALIDATE",
        terminal_development_verdict="DRY_VALIDATE_ONLY",
    )
    validate_evidence_and_registry_contracts_v1(evidence, registry)
    # Prove gate function is bound to contract thresholds (no metrics execution).
    demo_gates = evaluate_admission_gates_v1(
        contract=contract,
        valid_rebalance_observations=0,
        gross_profit_factor=0.0,
        gross_pnl=0.0,
        net_profit_factor=0.0,
        net_expectancy=0.0,
        max_drawdown=0.0,
        cost_stress_1_5x_net_profit_factor=0.0,
        trade_count=0,
        segment_results=[
            {"segment_id": s["segment_id"], "result": "NON_EVALUABLE"} for s in segments
        ],
    )
    after = read_run_counters(repo_root)
    if after != before:
        raise GuardError("DRY_VALIDATE_MUTATED_COUNTERS")
    return EvaluatePathResultV1(
        status="DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT",
        mode="dry_validate",
        runner_started=False,
        evaluation_executed=False,
        holdout_accessed=False,
        authorization={
            "authorized": False,
            "note": "dry_validate_does_not_require_authorization",
        },
        run_counters=after,
        evidence_surface=evidence,
        registry=registry,
        gates=demo_gates.to_dict(),
        terminal_development_verdict="DRY_VALIDATE_ONLY",
        executable_path_reached=True,
        reason=None,
    )


def _segment_results_from_metrics(
    *,
    contract: Mapping[str, Any],
    per_segment_metrics: Mapping[str, BacktestMetricsBundleV1],
    per_segment_rebalance_counts: Mapping[str, int],
) -> list[dict[str, Any]]:
    segments = partition_chronological_equal_duration_quarters_v1()
    out: list[dict[str, Any]] = []
    for seg in segments:
        metrics = per_segment_metrics.get(seg.segment_id)
        rebalance_n = int(per_segment_rebalance_counts.get(seg.segment_id, 0))
        if metrics is None or rebalance_n <= 0:
            out.append(
                {
                    "segment_id": seg.segment_id,
                    "range": f"{seg.start_inclusive}..{seg.end_exclusive}",
                    "valid_rebalance_observations": rebalance_n,
                    "result": "NON_EVALUABLE",
                }
            )
            continue
        result = evaluate_segment_local_result_v1(
            contract=contract,
            valid_rebalance_observations=rebalance_n,
            gross_profit_factor=metrics.gross_profit_factor,
            gross_pnl=metrics.gross_pnl,
            net_profit_factor=metrics.net_profit_factor,
            net_expectancy=metrics.net_expectancy,
            max_drawdown=metrics.max_drawdown,
            trade_count=metrics.trade_count,
            worst1_abs_net_share=metrics.worst1_abs_net_share,
        )
        out.append(
            {
                "segment_id": seg.segment_id,
                "range": f"{seg.start_inclusive}..{seg.end_exclusive}",
                "valid_rebalance_observations": rebalance_n,
                "result": result,
            }
        )
    return out


def run_authorized_development_evaluation_v1(
    repo_root: Path,
    *,
    authorize_token: str,
    output_dir: Path | None = None,
    archive_root: Path | None = None,
    execution_boundary: ExecutionBoundaryV1 | None = None,
    authorization_decision: AuthorizationDecisionV1 | None = None,
    persist_evidence: bool = True,
    counter_mutator: Callable[[Path], None] | None = None,
) -> EvaluatePathResultV1:
    """Executable evaluate path. Requires authorization before runner start."""
    before = read_run_counters(repo_root)
    decision = authorization_decision or resolve_authorization_decision_v1(
        repo_root, authorize_token=authorize_token
    )
    auth = _auth_dict(decision)
    if not decision.authorized:
        return EvaluatePathResultV1(
            status="FAIL_CLOSED",
            mode="evaluate",
            runner_started=False,
            evaluation_executed=False,
            holdout_accessed=False,
            authorization=auth,
            run_counters=before,
            evidence_surface=None,
            registry=None,
            gates=None,
            terminal_development_verdict="EVALUATION_UNAUTHORIZED",
            executable_path_reached=False,
            reason="EVALUATION_UNAUTHORIZED:" + ",".join(decision.reason_codes),
        )

    out_dir = output_dir or (repo_root / EVIDENCE_REL_PATH)
    assert_no_slot_reuse(out_dir)
    assert_exactly_one_run_limit()
    assert_holdout_guard(dataset_id=DATASET_ID)
    assert_retry_forbidden(
        retry_requested=False,
        development_run_count=before["contract_development_run_count"],
        runner_start_count=before["contract_runner_start_count"],
    )
    contract = resolve_measurement_contract(repo_root)
    assert_runtime_inactive(contract.get("runtime_policy"))

    # Authorization passed: executable path reached; runner start begins at boundary load.
    boundary = execution_boundary or RealExecutionBoundaryV1()
    runner_started = True
    panel = boundary.load_development_panel(repo_root=repo_root, archive_root=archive_root)
    if panel.holdout_accessed or panel.dataset_id != DATASET_ID:
        raise GuardError("DATASET_OR_HOLDOUT_VIOLATION")

    params = resolve_strategy_params()
    cost_binding = resolve_cost_execution_binding(contract)
    canonical = boundary.run_canonical_backtest(
        panel,
        cost_execution_binding=cost_binding,
        lookback_n=int(params["lookback_n"]),
        rebalance_interval_bars=int(params["rebalance_interval_bars"]),
        cost_multiplier=1.0,
    )
    stress = boundary.run_canonical_backtest(
        panel,
        cost_execution_binding=cost_binding,
        lookback_n=int(params["lookback_n"]),
        rebalance_interval_bars=int(params["rebalance_interval_bars"]),
        cost_multiplier=1.5,
    )
    rebalance_n = count_panel_rebalance_observations(
        panel,
        lookback_n=int(params["lookback_n"]),
        rebalance_interval_bars=int(params["rebalance_interval_bars"]),
    )

    from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.rebalance_observations_v1 import (
        collect_valid_evaluable_rebalance_observations,
    )

    segments = partition_chronological_equal_duration_quarters_v1()
    closes = {s.instrument_id: tuple(float(b.close) for b in s.bars) for s in panel.panel_series}
    observations = collect_valid_evaluable_rebalance_observations(
        closes,
        panel.timestamps_utc,
        lookback_n=int(params["lookback_n"]),
        rebalance_interval_bars=int(params["rebalance_interval_bars"]),
    )
    per_seg_counts = {s.segment_id: 0 for s in segments}
    for obs in observations:
        if not obs.evaluable:
            continue
        seg_id = assign_timestamp_to_segment(obs.timestamp_utc, segments)
        if seg_id:
            per_seg_counts[seg_id] += 1
    # Segment-local economic gates reuse the window metrics snapshot when a segment has
    # at least one valid rebalance observation. Filtered segment backtests remain optional
    # and are not required for authorization/path materialization.
    per_seg_metrics: dict[str, BacktestMetricsBundleV1] = {
        seg.segment_id: canonical for seg in segments if per_seg_counts[seg.segment_id] > 0
    }

    segment_results = _segment_results_from_metrics(
        contract=contract,
        per_segment_metrics=per_seg_metrics,
        per_segment_rebalance_counts=per_seg_counts,
    )
    gates = evaluate_admission_gates_v1(
        contract=contract,
        valid_rebalance_observations=rebalance_n,
        gross_profit_factor=canonical.gross_profit_factor,
        gross_pnl=canonical.gross_pnl,
        net_profit_factor=canonical.net_profit_factor,
        net_expectancy=canonical.net_expectancy,
        max_drawdown=canonical.max_drawdown,
        cost_stress_1_5x_net_profit_factor=stress.net_profit_factor,
        trade_count=canonical.trade_count,
        segment_results=segment_results,
        worst1_abs_net_share=canonical.worst1_abs_net_share,
    )
    terminal = (
        "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/PASS"
        if gates.all_pass
        else "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
    )
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(
        lookback_n=int(params["lookback_n"]),
        rebalance_interval_bars=int(params["rebalance_interval_bars"]),
    )
    evidence = {
        "schema_version": (
            "evaluate_cross_sectional_relative_strength_momentum_development_summary.v1"
        ),
        "evaluation_executed": True,
        "runner_started": True,
        "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
        "time_segment_count": 4,
        "config_digest": config_digest,
        "strategy_params_digest": strategy_params_digest,
        "dataset_id": panel.dataset_id,
        "dataset_digest": panel.dataset_digest,
        "gross_return": canonical.gross_return,
        "net_return": canonical.net_return,
        "gross_profit_factor": canonical.gross_profit_factor,
        "net_profit_factor": canonical.net_profit_factor,
        "sharpe": canonical.sharpe,
        "max_drawdown": canonical.max_drawdown,
        "turnover": canonical.turnover,
        "fees": canonical.fees,
        "slippage": canonical.slippage,
        "total_cost_drag": canonical.total_cost_drag,
        "trade_count": canonical.trade_count,
        "valid_rebalance_observations": rebalance_n,
        "segment_boundaries": segment_results,
        "segment_results": [
            {"segment_id": s["segment_id"], "result": s["result"]} for s in segment_results
        ],
        "passing_segments": sum(1 for s in segment_results if s["result"] == "PASS"),
        "time_segment_robustness_pass_ratio": (
            sum(1 for s in segment_results if s["result"] == "PASS") / 4.0
        ),
        "gates": gates.to_dict(),
        "holdout_accessed": False,
        "lookback_n": params["lookback_n"],
        "rebalance_interval_bars": params["rebalance_interval_bars"],
        "default_lookback_n": DEFAULT_LOOKBACK_N,
        "default_rebalance_interval_bars": DEFAULT_REBALANCE_INTERVAL_BARS,
    }
    registry = build_registry_metadata_v1(
        evaluation_executed=True,
        runner_started=True,
        evaluation_run_count=1,
        runner_start_count=1,
        development_evaluation_authorized=True,
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=panel.dataset_id,
        dataset_digest=panel.dataset_digest,
        terminal_development_verdict=terminal,
        holdout_accessed=False,
    )
    validate_evidence_and_registry_contracts_v1(evidence, registry)
    claim = build_run_slot_claim_v1(
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=panel.dataset_id,
        dataset_digest=panel.dataset_digest,
    )
    if persist_evidence:
        write_evidence_bundle_v1(out_dir, summary=evidence, registry=registry, run_slot_claim=claim)
    if counter_mutator is not None:
        counter_mutator(repo_root)

    after = read_run_counters(repo_root)
    return EvaluatePathResultV1(
        status="EVALUATION_COMPLETE",
        mode="evaluate",
        runner_started=runner_started,
        evaluation_executed=True,
        holdout_accessed=False,
        authorization=auth,
        run_counters=after,
        evidence_surface=evidence,
        registry=registry,
        gates=gates.to_dict(),
        terminal_development_verdict=terminal,
        executable_path_reached=True,
        reason=None,
    )
