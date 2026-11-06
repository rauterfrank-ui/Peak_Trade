"""Executable development-evaluation path for VEPC v1 (orchestration surface).

Authorization is fail-closed. Dry-validate never starts the runner, opens a panel,
or consumes run budget. Real evaluate requires repo authorization flags + token and
an injectable execution boundary (real or fake). TREATMENT PnL is realized exclusively
from strategy-emitted roundtrips (no evaluator-side exit reconstruction); BASELINE is
realized via the identical declarative exit-search path as every other package.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.admission_gates_v1 import (
    evaluate_admission_gates_v1,
    evaluate_segment_local_result_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.authorization_v1 import (
    AuthorizationDecisionV1,
    resolve_authorization_decision_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.binding_v1 import (
    assert_exit_state_machine_bound,
    assert_shared_channel_core_bound,
    compute_config_digest,
    compute_strategy_params_digest,
    load_and_validate_entry_point_binding,
    resolve_cost_execution_binding,
    resolve_measurement_contract,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    EVIDENCE_REL_PATH,
    MIN_EVALUABLE_TREATMENT_BREAKOUT_EVENTS,
    TIME_SEGMENT_DEFINITION_ID,
    TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.evidence_materialization_v1 import (
    build_registry_metadata_v1,
    build_run_slot_claim_v1,
    build_technical_fail_closed_summary_v1,
    validate_evidence_and_registry_contracts_v1,
    write_evidence_bundle_v1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.evidence_schema_v1 import (
    empty_evidence_surface_template,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.execution_boundary_v1 import (
    BacktestMetricsBundleV1,
    ExecutionBoundaryV1,
    RealExecutionBoundaryV1,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.guards_v1 import (
    GuardError,
    assert_exactly_one_run_limit,
    assert_holdout_guard,
    assert_no_slot_reuse,
    assert_retry_forbidden,
    assert_runtime_inactive,
    assert_run_counters_unchanged,
    preflight_guards,
    read_run_counters,
)
from src.research.volatility_expansion_pullback_continuation_v1_development_evaluation_v1.time_segments_v1 import (
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
    development_dataset_loaded: bool
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
            "development_dataset_loaded": self.development_dataset_loaded,
            "authorization": self.authorization,
            "run_counters": self.run_counters,
            "evidence_surface": self.evidence_surface,
            "registry": self.registry,
            "gates": self.gates,
            "terminal_development_verdict": self.terminal_development_verdict,
            "executable_path_reached": self.executable_path_reached,
            "reason": self.reason,
            "development_run_limit": DEVELOPMENT_RUN_LIMIT,
            "time_segment_definition_id": TIME_SEGMENT_DEFINITION_ID,
            "dataset_id": DATASET_ID,
            "min_evaluable_treatment_breakout_events": MIN_EVALUABLE_TREATMENT_BREAKOUT_EVENTS,
            "time_segment_robustness_pass_ratio": TIME_SEGMENT_ROBUSTNESS_PASS_RATIO,
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
    assert_shared_channel_core_bound()
    assert_exit_state_machine_bound()
    config_digest = compute_config_digest(repo_root)
    strategy_params_digest = compute_strategy_params_digest(contract)
    segments = segments_to_dict(partition_chronological_equal_duration_quarters_v1())
    evidence = empty_evidence_surface_template(
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        segment_boundaries=[
            {
                "segment_id": s["segment_id"],
                "range": s["range"],
                "evaluable_treatment_breakout_events": "NOT_EXECUTED",
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
        development_evaluation_authorized=True,
        config_digest=config_digest,
        strategy_params_digest=strategy_params_digest,
        dataset_id=DATASET_ID,
        dataset_digest="NOT_RESOLVED_DRY_VALIDATE",
        terminal_development_verdict="DRY_VALIDATE_ONLY",
    )
    validate_evidence_and_registry_contracts_v1(evidence, registry)
    demo_gates = evaluate_admission_gates_v1(
        contract=contract,
        evaluable_treatment_breakout_events=0,
        trade_count=0,
        gross_profit_factor=0.0,
        gross_pnl=0.0,
        net_profit_factor=0.0,
        baseline_net_profit_factor=0.0,
        net_expectancy=0.0,
        max_drawdown=0.0,
        cost_stress_1_5x_net_profit_factor=0.0,
        segment_results=[
            {
                "segment_id": s["segment_id"],
                "result": "NON_EVALUABLE",
                "evaluable_treatment_breakout_events": 0,
            }
            for s in segments
        ],
    )
    after = read_run_counters(repo_root)
    assert_run_counters_unchanged(before, after)
    return EvaluatePathResultV1(
        status="DRY_VALIDATE_PASS_EXECUTABLE_PATH_PRESENT",
        mode="dry-validate",
        runner_started=False,
        evaluation_executed=False,
        holdout_accessed=False,
        development_dataset_loaded=False,
        authorization={
            "authorized": False,
            "guards": guards,
            "cost_execution_binding": resolve_cost_execution_binding(contract),
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
    per_segment_event_counts: Mapping[str, int],
) -> list[dict[str, Any]]:
    segments = partition_chronological_equal_duration_quarters_v1()
    out: list[dict[str, Any]] = []
    for seg in segments:
        metrics = per_segment_metrics.get(seg.segment_id)
        events_n = int(per_segment_event_counts.get(seg.segment_id, 0))
        if metrics is None or events_n <= 0:
            out.append(
                {
                    "segment_id": seg.segment_id,
                    "range": f"{seg.start_inclusive}..{seg.end_exclusive}",
                    "evaluable_treatment_breakout_events": events_n,
                    "result": "NON_EVALUABLE",
                }
            )
            continue
        result = evaluate_segment_local_result_v1(
            contract=contract,
            evaluable_treatment_breakout_events=events_n,
            gross_profit_factor=metrics.gross_profit_factor,
            gross_pnl=metrics.gross_pnl,
            net_profit_factor=metrics.net_profit_factor,
            baseline_net_profit_factor=metrics.baseline_net_profit_factor,
            net_expectancy=metrics.net_expectancy,
            max_drawdown=metrics.max_drawdown,
            trade_count=metrics.trade_count,
        )
        out.append(
            {
                "segment_id": seg.segment_id,
                "range": f"{seg.start_inclusive}..{seg.end_exclusive}",
                "evaluable_treatment_breakout_events": events_n,
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
            development_dataset_loaded=False,
            authorization=auth,
            run_counters=before,
            evidence_surface=None,
            registry=None,
            gates=None,
            terminal_development_verdict="EVALUATION_UNAUTHORIZED",
            executable_path_reached=False,
            reason="EVALUATION_UNAUTHORIZED:" + ",".join(decision.reason_codes or ("UNKNOWN",)),
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
    assert_shared_channel_core_bound()
    assert_exit_state_machine_bound()
    config_digest = compute_config_digest(repo_root)
    binding = load_and_validate_entry_point_binding(repo_root)
    if str(binding.get("config_digest")) != config_digest:
        raise GuardError("CONFIG_DIGEST_MISMATCH")

    boundary = execution_boundary or RealExecutionBoundaryV1()
    runner_started = True
    development_dataset_loaded = False
    dataset_digest = "NOT_RESOLVED_TECHNICAL_FAIL_CLOSED"
    strategy_params_digest = compute_strategy_params_digest(contract)

    def _persist_technical_fail_closed(exc: BaseException) -> EvaluatePathResultV1:
        reason = (
            str(exc) if isinstance(exc, GuardError) else f"UNEXPECTED:{type(exc).__name__}:{exc}"
        )
        if "UNPAIRABLE_ENTRY_NO_EXIT" in reason:
            terminal = (
                "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT"
            )
            if "NOT_RESOLVED" in dataset_digest:
                digest_for_claim = "NOT_RESOLVED_UNPAIRABLE_ENTRY_NO_EXIT"
            else:
                digest_for_claim = dataset_digest
        else:
            terminal = "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL_CLOSED_TECHNICAL"
            digest_for_claim = dataset_digest
        evidence = build_technical_fail_closed_summary_v1(
            config_digest=config_digest,
            strategy_params_digest=strategy_params_digest,
            dataset_id=DATASET_ID,
            dataset_digest=digest_for_claim,
            reason=reason,
            development_dataset_loaded=development_dataset_loaded,
            terminal_development_verdict=terminal,
        )
        registry = build_registry_metadata_v1(
            evaluation_executed=False,
            runner_started=True,
            evaluation_run_count=1,
            runner_start_count=1,
            development_evaluation_authorized=True,
            config_digest=config_digest,
            strategy_params_digest=strategy_params_digest,
            dataset_id=DATASET_ID,
            dataset_digest=digest_for_claim,
            terminal_development_verdict=terminal,
            holdout_accessed=False,
        )
        claim = build_run_slot_claim_v1(
            config_digest=config_digest,
            strategy_params_digest=strategy_params_digest,
            dataset_id=DATASET_ID,
            dataset_digest=digest_for_claim,
            slot_consumption_boundary=(
                "RUNNER_STARTED_BEFORE_TECHNICAL_FAIL_CLOSED_PRE_EVIDENCE_SUCCESS_PATH"
            ),
        )
        validate_evidence_and_registry_contracts_v1(evidence, registry)
        if persist_evidence:
            write_evidence_bundle_v1(
                out_dir, summary=evidence, registry=registry, run_slot_claim=claim
            )
        after = read_run_counters(repo_root)
        return EvaluatePathResultV1(
            status="FAIL_CLOSED",
            mode="evaluate",
            runner_started=True,
            evaluation_executed=False,
            holdout_accessed=False,
            development_dataset_loaded=development_dataset_loaded,
            authorization=auth,
            run_counters=after,
            evidence_surface=evidence,
            registry=registry,
            gates=None,
            terminal_development_verdict=terminal,
            executable_path_reached=True,
            reason=reason,
        )

    try:
        panel = boundary.load_development_panel(
            repo_root=repo_root,
            archive_root=archive_root,
            expected_dataset_id=DATASET_ID,
            time_segment_definition_id=TIME_SEGMENT_DEFINITION_ID,
            expected_config_digest=config_digest,
        )
        if panel.holdout_accessed or panel.dataset_id != DATASET_ID:
            raise GuardError("DATASET_OR_HOLDOUT_VIOLATION")
        if not panel.panel_series or panel.instrument_count <= 0:
            raise GuardError("EMPTY_PANEL_MATERIALIZATION")
        development_dataset_loaded = True
        dataset_digest = str(panel.dataset_digest)

        cost_binding = resolve_cost_execution_binding(contract)
        canonical = boundary.run_canonical_backtest(
            panel,
            cost_execution_binding=cost_binding,
            cost_multiplier=1.0,
        )
        stress = boundary.run_canonical_backtest(
            panel,
            cost_execution_binding=cost_binding,
            cost_multiplier=1.5,
        )

        segments = partition_chronological_equal_duration_quarters_v1()
        handoff = boundary.wire_treatment_baseline(panel)
        per_seg_counts = {s.segment_id: 0 for s in segments}
        for arm in handoff.treatment:
            for ts, is_entry in zip(arm.timestamps_utc, arm.entry_event_mask):
                if not is_entry:
                    continue
                seg_id = assign_timestamp_to_segment(ts, segments)
                if seg_id:
                    per_seg_counts[seg_id] += 1
        per_seg_metrics: dict[str, BacktestMetricsBundleV1] = {
            seg.segment_id: canonical for seg in segments if per_seg_counts[seg.segment_id] > 0
        }
        segment_results = _segment_results_from_metrics(
            contract=contract,
            per_segment_metrics=per_seg_metrics,
            per_segment_event_counts=per_seg_counts,
        )
        gates = evaluate_admission_gates_v1(
            contract=contract,
            evaluable_treatment_breakout_events=canonical.evaluable_treatment_breakout_events,
            trade_count=canonical.trade_count,
            gross_profit_factor=canonical.gross_profit_factor,
            gross_pnl=canonical.gross_pnl,
            net_profit_factor=canonical.net_profit_factor,
            baseline_net_profit_factor=canonical.baseline_net_profit_factor,
            net_expectancy=canonical.net_expectancy,
            max_drawdown=canonical.max_drawdown,
            cost_stress_1_5x_net_profit_factor=stress.net_profit_factor,
            segment_results=segment_results,
        )
        terminal = (
            "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/PASS"
            if gates.all_pass
            else "DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL/FAIL"
        )
        evidence = {
            "schema_version": "evaluate_volatility_expansion_pullback_continuation_development_summary.v1",
            "evaluation_executed": True,
            "runner_started": True,
            "development_dataset_loaded": True,
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
            "max_drawdown": canonical.max_drawdown,
            "trade_count": canonical.trade_count,
            "evaluable_treatment_breakout_events": canonical.evaluable_treatment_breakout_events,
            "baseline_net_profit_factor": canonical.baseline_net_profit_factor,
            "baseline_net_return": canonical.extras.get("baseline_net_return"),
            "long_trade_count": canonical.extras.get("long_trade_count"),
            "short_trade_count": canonical.extras.get("short_trade_count"),
            "exit_reason_attribution": canonical.extras.get("exit_reason_attribution"),
            "productive_exit_pnl_evaluator_bound": canonical.extras.get(
                "productive_exit_pnl_evaluator_bound"
            ),
            "strategy_emitted_exits_used_for_treatment": canonical.extras.get(
                "strategy_emitted_exits_used_for_treatment"
            ),
            "evaluator_reconstruction_used_for_treatment": canonical.extras.get(
                "evaluator_reconstruction_used_for_treatment"
            ),
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
            "economic_gate_pass": gates.all_pass,
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
            write_evidence_bundle_v1(
                out_dir, summary=evidence, registry=registry, run_slot_claim=claim
            )
        if counter_mutator is not None:
            counter_mutator(repo_root)

        after = read_run_counters(repo_root)
        return EvaluatePathResultV1(
            status="EVALUATION_COMPLETE",
            mode="evaluate",
            runner_started=runner_started,
            evaluation_executed=True,
            holdout_accessed=False,
            development_dataset_loaded=True,
            authorization=auth,
            run_counters=after,
            evidence_surface=evidence,
            registry=registry,
            gates=gates.to_dict(),
            terminal_development_verdict=terminal,
            executable_path_reached=True,
            reason=None,
        )
    except Exception as exc:  # noqa: BLE001 - durable fail-closed after runner start
        return _persist_technical_fail_closed(exc)
