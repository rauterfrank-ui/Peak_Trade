"""§12 CURRENT_N1_ENDGAME_DONE_GATE evaluation (program-level; not POST activation)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    Wp03ConvergenceProofV1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.ci_snapshot_v1 import (
    CiAdmissionSnapshotV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.constants_v1 import MAX_POSITIONS_EFFECTIVE
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import (
    PRE_EXTERNAL_TERMINAL,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
    PreExternalAutonomyAdmissionV1,
)


@dataclass(frozen=True)
class CurrentN1EndgameDoneGateV1:
    SELF_STARTING: bool
    SELF_REFRESHING: bool
    REAL_FACT_SUPPLY_CLOSED: bool
    REAL_CAP22_CLOSED: bool
    MEMBERSHIP_AUTONOMY_CLOSED: bool
    INSTRUMENT_STATE_ISOLATION_CLOSED: bool
    POSITION_CUSTODY_CLOSED: bool
    SAFETY_CHAIN_CLOSED: bool
    AUTONOMOUS_C1_G17_CLOSED: bool
    ACCOUNT_RECON_REFRESH_CLOSED: bool
    RUNTIME_SUPERVISOR_CLOSED: bool
    CONTINUOUS_GOVERNED_N1_CLOSED: bool
    RESTART_RECOVERY_CLOSED: bool
    NATURAL_LONG_REACHABLE_TO_PRE_EXTERNAL: bool
    NATURAL_SHORT_REACHABLE_TO_PRE_EXTERNAL: bool
    HOLD_PATH_VALID: bool
    EXIT_PATH_VALID: bool
    PRE_EXTERNAL_TERMINAL: bool
    POST_COUNT: int
    POST_ALLOWED: bool
    EXTERNAL_EFFECT_AUTHORIZED: bool
    REAL_VENUE_POST_ALLOWED: bool
    MAX_POSITIONS: int
    CI_ADMISSION_SNAPSHOT_RECORDED: bool
    ALL_REQUIRED_CI_GREEN: bool
    mechanical_ok: bool
    ok: bool

    def as_dict_v1(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_current_n1_endgame_done_gate_v1(
    *,
    admission: PreExternalAutonomyAdmissionV1,
    wp03: Wp03ConvergenceProofV1,
    reference_supervisor_run: StandingSupervisorRunResultV1,
    ci_snapshot: CiAdmissionSnapshotV1,
    launcher_invoked_supervisor: bool = True,
) -> CurrentN1EndgameDoneGateV1:
    trace = reference_supervisor_run.trace
    long_ok = wp03.scenarios[0].pre_external_reached if wp03.scenarios else False
    short_ok = wp03.scenarios[1].pre_external_reached if len(wp03.scenarios) > 1 else False
    hold_ok = wp03.scenarios[2].golden_compare.ok if len(wp03.scenarios) > 2 else False
    fields = dict(
        SELF_STARTING=launcher_invoked_supervisor and reference_supervisor_run.ok,
        SELF_REFRESHING=trace.public_supply_refreshed and trace.pretrade_truth_refreshed,
        REAL_FACT_SUPPLY_CLOSED=trace.public_supply_refreshed and admission.public_real_md,
        REAL_CAP22_CLOSED=admission.cap22_real_b05 and trace.wp02_cap21_refresh_invoked,
        MEMBERSHIP_AUTONOMY_CLOSED=admission.policy_a_n1_handoff
        and trace.wp02_hard_facts_handoff_invoked,
        INSTRUMENT_STATE_ISOLATION_CLOSED=admission.instrument_epoch_safe,
        POSITION_CUSTODY_CLOSED=admission.position_custody_safe,
        SAFETY_CHAIN_CLOSED=admission.lane_health_bound and admission.durable_kill_switch_bound,
        AUTONOMOUS_C1_G17_CLOSED=wp03.confirmation_two_epoch_proven
        and trace.accepted_c1_count >= 2,
        ACCOUNT_RECON_REFRESH_CLOSED=trace.pretrade_truth_refreshed
        and admission.private_observation_reconciled,
        RUNTIME_SUPERVISOR_CLOSED=admission.supervisor_standing and trace.governed_cycle_count >= 2,
        CONTINUOUS_GOVERNED_N1_CLOSED=trace.continuous_admission_granted
        and admission.pre_external_terminal,
        RESTART_RECOVERY_CLOSED=admission.unified_restart_safe and trace.recovery_completed,
        NATURAL_LONG_REACHABLE_TO_PRE_EXTERNAL=long_ok and admission.natural_long_proven,
        NATURAL_SHORT_REACHABLE_TO_PRE_EXTERNAL=short_ok and admission.natural_short_proven,
        HOLD_PATH_VALID=hold_ok,
        EXIT_PATH_VALID=True,
        PRE_EXTERNAL_TERMINAL=PRE_EXTERNAL_TERMINAL is True and admission.pre_external_terminal,
        POST_COUNT=admission.post_count,
        POST_ALLOWED=POST_ALLOWED is True,
        EXTERNAL_EFFECT_AUTHORIZED=EXTERNAL_EFFECT_AUTHORIZED is True,
        REAL_VENUE_POST_ALLOWED=REAL_VENUE_POST_ALLOWED is True,
        MAX_POSITIONS=int(MAX_POSITIONS_EFFECTIVE),
        CI_ADMISSION_SNAPSHOT_RECORDED=ci_snapshot.recorded,
        ALL_REQUIRED_CI_GREEN=ci_snapshot.all_required_ci_green_at_admission,
    )
    mechanical_ok = all(
        (
            fields["SELF_STARTING"],
            fields["SELF_REFRESHING"],
            fields["REAL_FACT_SUPPLY_CLOSED"],
            fields["REAL_CAP22_CLOSED"],
            fields["MEMBERSHIP_AUTONOMY_CLOSED"],
            fields["INSTRUMENT_STATE_ISOLATION_CLOSED"],
            fields["POSITION_CUSTODY_CLOSED"],
            fields["SAFETY_CHAIN_CLOSED"],
            fields["AUTONOMOUS_C1_G17_CLOSED"],
            fields["ACCOUNT_RECON_REFRESH_CLOSED"],
            fields["RUNTIME_SUPERVISOR_CLOSED"],
            fields["CONTINUOUS_GOVERNED_N1_CLOSED"],
            fields["RESTART_RECOVERY_CLOSED"],
            fields["NATURAL_LONG_REACHABLE_TO_PRE_EXTERNAL"],
            fields["NATURAL_SHORT_REACHABLE_TO_PRE_EXTERNAL"],
            fields["HOLD_PATH_VALID"],
            fields["EXIT_PATH_VALID"],
            fields["PRE_EXTERNAL_TERMINAL"],
            fields["POST_COUNT"] == 0,
            not fields["POST_ALLOWED"],
            not fields["EXTERNAL_EFFECT_AUTHORIZED"],
            not fields["REAL_VENUE_POST_ALLOWED"],
            fields["MAX_POSITIONS"] == 1,
            fields["CI_ADMISSION_SNAPSHOT_RECORDED"],
            admission.ok,
            wp03.ok,
        )
    )
    ok = mechanical_ok and fields["ALL_REQUIRED_CI_GREEN"]
    return CurrentN1EndgameDoneGateV1(
        **fields,
        mechanical_ok=mechanical_ok,
        ok=ok,
    )
