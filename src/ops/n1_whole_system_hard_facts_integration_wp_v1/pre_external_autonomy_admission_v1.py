"""RW-E23: PRE_EXTERNAL autonomy admission proof (POST forbidden)."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.composed_identity_custody_health_v1 import (
    prove_composed_safety_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import (
    EVIDENCE_ROOT_RELATIVE,
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    PRE_EXTERNAL_TERMINAL,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.execution_lifecycle_chain_v1 import (
    prove_execution_lifecycle_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.golden_happy_path_trace_harness_v1 import (
    GoldenHarnessAggregateV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.private_observation_chain_v1 import (
    prove_private_observation_chain_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    PublicRealMdChainProofV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.standing_n1_pre_external_supervisor_v1 import (
    prove_standing_n1_pre_external_supervisor_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.unified_recovery_orchestration_v1 import (
    UnifiedRecoveryOrchestrationResultV1,
)


@dataclass(frozen=True)
class PreExternalAutonomyAdmissionV1:
    ok: bool
    public_real_md: bool
    cap22_real_b05: bool
    policy_a_n1_handoff: bool
    instrument_epoch_safe: bool
    position_custody_safe: bool
    lane_health_bound: bool
    durable_kill_switch_bound: bool
    private_observation_reconciled: bool
    reservation_restart_safe: bool
    treasury_feedback_closed: bool
    unified_restart_safe: bool
    supervisor_standing: bool
    natural_long_proven: bool
    natural_short_proven: bool
    pre_external_terminal: bool
    post_count: int
    post_allowed: bool
    external_effect_authorized: bool
    real_venue_post_allowed: bool


def prove_pre_external_autonomy_admission_v1(
    *,
    public_chain: PublicRealMdChainProofV1,
    safety: Any,
    private: Any,
    execution: Any,
    recovery: UnifiedRecoveryOrchestrationResultV1,
    supervisor: Any,
    golden: GoldenHarnessAggregateV1,
    post_count: int = 0,
) -> PreExternalAutonomyAdmissionV1:
    auth = prove_hard_facts_authority_invariants_v1()
    admission = PreExternalAutonomyAdmissionV1(
        ok=False,
        public_real_md=public_chain.ok,
        cap22_real_b05=public_chain.cap22_real_b05,
        policy_a_n1_handoff=public_chain.policy_a_n1_handoff,
        instrument_epoch_safe=safety.instrument_epoch_safe,
        position_custody_safe=safety.position_custody_safe,
        lane_health_bound=safety.lane_health_membership_bound,
        durable_kill_switch_bound=safety.durable_kill_switch_bound,
        private_observation_reconciled=private.private_observation_productive_join,
        reservation_restart_safe=execution.reservation_restart_safe,
        treasury_feedback_closed=execution.treasury_feedback_closed,
        unified_restart_safe=recovery.ok,
        supervisor_standing=supervisor.supervisor_standing,
        natural_long_proven=golden.natural_long.ok,
        natural_short_proven=golden.natural_short.ok,
        pre_external_terminal=supervisor.continuous_n1_pre_external,
        post_count=post_count,
        post_allowed=POST_ALLOWED,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED,
    )
    ok = (
        auth.ok
        and admission.public_real_md
        and admission.cap22_real_b05
        and admission.policy_a_n1_handoff
        and admission.instrument_epoch_safe
        and admission.position_custody_safe
        and admission.lane_health_bound
        and admission.durable_kill_switch_bound
        and admission.private_observation_reconciled
        and admission.reservation_restart_safe
        and admission.treasury_feedback_closed
        and admission.unified_restart_safe
        and admission.supervisor_standing
        and admission.natural_long_proven
        and admission.natural_short_proven
        and admission.pre_external_terminal
        and PRE_EXTERNAL_TERMINAL is True
        and post_count == 0
        and not POST_ALLOWED
        and not EXTERNAL_EFFECT_AUTHORIZED
        and not REAL_VENUE_POST_ALLOWED
    )
    return PreExternalAutonomyAdmissionV1(
        ok=ok,
        public_real_md=admission.public_real_md,
        cap22_real_b05=admission.cap22_real_b05,
        policy_a_n1_handoff=admission.policy_a_n1_handoff,
        instrument_epoch_safe=admission.instrument_epoch_safe,
        position_custody_safe=admission.position_custody_safe,
        lane_health_bound=admission.lane_health_bound,
        durable_kill_switch_bound=admission.durable_kill_switch_bound,
        private_observation_reconciled=admission.private_observation_reconciled,
        reservation_restart_safe=admission.reservation_restart_safe,
        treasury_feedback_closed=admission.treasury_feedback_closed,
        unified_restart_safe=admission.unified_restart_safe,
        supervisor_standing=admission.supervisor_standing,
        natural_long_proven=admission.natural_long_proven,
        natural_short_proven=admission.natural_short_proven,
        pre_external_terminal=admission.pre_external_terminal,
        post_count=post_count,
        post_allowed=POST_ALLOWED,
        external_effect_authorized=EXTERNAL_EFFECT_AUTHORIZED,
        real_venue_post_allowed=REAL_VENUE_POST_ALLOWED,
    )


def write_admission_evidence_v1(
    *,
    repo_root: Path,
    admission: PreExternalAutonomyAdmissionV1,
    backlog_matrix: Mapping[str, Any],
) -> Path:
    out_dir = repo_root / EVIDENCE_ROOT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "admission": asdict(admission),
        "backlog_matrix": dict(backlog_matrix),
    }
    path = out_dir / "PRE_EXTERNAL_AUTONOMY_ADMISSION_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_private_rest_fetch_v1() -> Callable[[str, Mapping[str, str]], Mapping[str, Any]]:
    def _fetch(path: str, _params: Mapping[str, str]) -> Mapping[str, Any]:
        if path == "/api/v5/account/config":
            return {"code": "0", "data": [{"acctLv": "2", "posMode": "net_mode"}]}
        if path == "/api/v5/account/balance":
            return {
                "code": "0",
                "data": [{"totalEq": "100", "details": [{"ccy": "USDT", "availEq": "90"}]}],
            }
        if path == "/api/v5/account/positions":
            return {"code": "0", "data": []}
        if "orders" in path or path.endswith("fills"):
            return {"code": "0", "data": []}
        return {"code": "0", "data": []}

    return _fetch


def default_public_rest_fetch_v1() -> Callable[[str, Mapping[str, str]], Mapping[str, Any]]:
    def _fetch(path: str, params: Mapping[str, str]) -> Mapping[str, Any]:
        _ = path, params
        return {"code": "0", "data": []}

    return _fetch


def run_full_admission_proof_bundle_v1(
    *,
    public_chain: PublicRealMdChainProofV1,
    kill_switch_state_path: Optional[str] = None,
    public_store_root: Path,
    private_store_root: Path,
    golden: GoldenHarnessAggregateV1,
    pre_external_reached: bool,
) -> PreExternalAutonomyAdmissionV1:
    safety = prove_composed_safety_chain_v1(kill_switch_state_path=kill_switch_state_path)
    private = prove_private_observation_chain_v1(
        store_root=private_store_root,
        rest_fetch_json=default_private_rest_fetch_v1(),
    )
    execution = prove_execution_lifecycle_chain_v1()
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.unified_recovery_orchestration_v1 import (
        execute_unified_recovery_orchestration_v1,
    )

    recovery = execute_unified_recovery_orchestration_v1(
        public_store_root=public_store_root,
        private_store_root=private_store_root,
        public_rest_fetch=default_public_rest_fetch_v1(),
        private_rest_fetch=default_private_rest_fetch_v1(),
        kill_switch_state_path=kill_switch_state_path,
    )
    supervisor = prove_standing_n1_pre_external_supervisor_v1(
        pre_external_reached=pre_external_reached,
        post_count=0,
    )
    return prove_pre_external_autonomy_admission_v1(
        public_chain=public_chain,
        safety=safety,
        private=private,
        execution=execution,
        recovery=recovery,
        supervisor=supervisor,
        golden=golden,
        post_count=0,
    )
