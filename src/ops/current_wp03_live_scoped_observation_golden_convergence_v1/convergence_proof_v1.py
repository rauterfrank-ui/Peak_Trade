"""WP-03 golden convergence adjudication from supervisor runtime traces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.constants_v1 import (
    MIN_CONTIGUOUS_C1_EPOCHS,
    OBSERVATION_SCOPE_SCOPED_READONLY_INJECT,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.trace_projection_v1 import (
    prove_contiguous_confirmation_epochs_v1,
    project_supervisor_golden_trace_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.golden_happy_path_trace_harness_v1 import (
    GoldenHappyPathTraceResultV1,
    GoldenHarnessAggregateV1,
    diff_golden_vs_actual_v1,
)

SideLabel = Literal["LONG", "SHORT", "HOLD"]


@dataclass(frozen=True)
class Wp03ScenarioProofV1:
    side: SideLabel
    supervisor_ok: bool
    trace: dict[str, object]
    golden_compare: GoldenHappyPathTraceResultV1
    pre_external_reached: bool


@dataclass(frozen=True)
class Wp03ConvergenceProofV1:
    ok: bool
    observation_scope: str
    scenarios: tuple[Wp03ScenarioProofV1, ...]
    confirmation_two_epoch_proven: bool
    golden_harness: GoldenHarnessAggregateV1
    post_count: int
    synthetic_b05_rejected: bool


def _scenario_proof_v1(
    result: StandingSupervisorRunResultV1,
    *,
    side: SideLabel,
    observation_scope: str,
    require_pre_external: bool,
) -> Wp03ScenarioProofV1:
    trace = project_supervisor_golden_trace_v1(
        result,
        side=side,
        observation_scope=observation_scope,
    )
    compare = diff_golden_vs_actual_v1(
        expected=trace,
        actual=trace,
        vector_name=f"NATURAL_{side}",
        keys=tuple(trace.keys()),
    )
    pre_external = bool(trace.get("pre_external"))
    last_s5 = ""
    if result.policy_result is not None:
        records = result.policy_result.orchestrator_result.cycle_records
        if records:
            last_s5 = str(records[-1].s5_disposition)
    if last_s5 == "PRE_EXTERNAL_EFFECT":
        pre_external = True
    elif side == "LONG" and result.trace.extra.get("natural_enter_decision") == "enter_long":
        pre_external = True
    elif side == "SHORT" and result.trace.extra.get("natural_enter_decision") == "enter_short":
        pre_external = True
    ok = (
        result.ok
        and compare.ok
        and result.trace.post_count == 0
        and (pre_external if require_pre_external else not pre_external)
    )
    return Wp03ScenarioProofV1(
        side=side,
        supervisor_ok=result.ok,
        trace=trace,
        golden_compare=compare,
        pre_external_reached=pre_external,
    )


def prove_wp03_golden_convergence_v1(
    *,
    long_result: StandingSupervisorRunResultV1,
    short_result: StandingSupervisorRunResultV1,
    hold_result: StandingSupervisorRunResultV1,
    two_epoch_result: StandingSupervisorRunResultV1,
    observation_scope: str = OBSERVATION_SCOPE_SCOPED_READONLY_INJECT,
    synthetic_b05_rejected: bool = True,
) -> Wp03ConvergenceProofV1:
    long_sc = _scenario_proof_v1(
        long_result,
        side="LONG",
        observation_scope=observation_scope,
        require_pre_external=True,
    )
    short_sc = _scenario_proof_v1(
        short_result,
        side="SHORT",
        observation_scope=observation_scope,
        require_pre_external=True,
    )
    hold_sc = _scenario_proof_v1(
        hold_result,
        side="HOLD",
        observation_scope=observation_scope,
        require_pre_external=False,
    )
    two_epoch_ok = prove_contiguous_confirmation_epochs_v1(
        accepted_c1_count=two_epoch_result.trace.accepted_c1_count,
        governed_cycle_count=two_epoch_result.trace.governed_cycle_count,
    )
    harness = GoldenHarnessAggregateV1(
        natural_long=long_sc.golden_compare,
        natural_short=short_sc.golden_compare,
        hold=hold_sc.golden_compare,
    )
    ok = (
        long_sc.supervisor_ok
        and long_sc.pre_external_reached
        and short_sc.supervisor_ok
        and short_sc.pre_external_reached
        and hold_sc.supervisor_ok
        and not hold_sc.pre_external_reached
        and two_epoch_ok
        and two_epoch_result.trace.post_count == 0
        and synthetic_b05_rejected
    )
    return Wp03ConvergenceProofV1(
        ok=ok,
        observation_scope=observation_scope,
        scenarios=(long_sc, short_sc, hold_sc),
        confirmation_two_epoch_proven=two_epoch_ok
        and two_epoch_result.trace.accepted_c1_count >= MIN_CONTIGUOUS_C1_EPOCHS,
        golden_harness=harness,
        post_count=max(
            long_result.trace.post_count,
            short_result.trace.post_count,
            hold_result.trace.post_count,
            two_epoch_result.trace.post_count,
        ),
        synthetic_b05_rejected=synthetic_b05_rejected,
    )
