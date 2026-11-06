"""Regenerate standing PRE_EXTERNAL admission using WP-01..03 runtime semantics."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    Wp03ConvergenceProofV1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
    ADMISSION_ARTIFACT_KIND,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.done_gate_v1 import (
    CurrentN1EndgameDoneGateV1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.runtime_supervisor_proof_v1 import (
    prove_standing_supervisor_from_runtime_session_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
    PreExternalAutonomyAdmissionV1,
    run_full_admission_proof_bundle_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    PublicRealMdChainProofV1,
)


def prove_standing_pre_external_admission_v1(
    *,
    public_chain: PublicRealMdChainProofV1,
    public_store_root: Path,
    private_store_root: Path,
    wp03: Wp03ConvergenceProofV1,
    reference_supervisor_run: StandingSupervisorRunResultV1,
) -> PreExternalAutonomyAdmissionV1:
    pre_external = any(s.pre_external_reached for s in wp03.scenarios[:2])
    supervisor = prove_standing_supervisor_from_runtime_session_v1(
        reference_supervisor_run,
        pre_external_reached=pre_external,
    )
    return run_full_admission_proof_bundle_v1(
        public_chain=public_chain,
        public_store_root=public_store_root,
        private_store_root=private_store_root,
        golden=wp03.golden_harness,
        pre_external_reached=pre_external,
        supervisor=supervisor,
    )


def build_standing_admission_payload_v1(
    *,
    admission: PreExternalAutonomyAdmissionV1,
    wp03: Wp03ConvergenceProofV1,
    done_gate: CurrentN1EndgameDoneGateV1,
    tested_code_sha: str,
    backlog_matrix: Mapping[str, Any],
    ci_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_kind": ADMISSION_ARTIFACT_KIND,
        "admission": asdict(admission),
        "backlog_matrix": dict(backlog_matrix),
        "wp03_observation_scope": wp03.observation_scope,
        "wp03_confirmation_two_epoch_proven": wp03.confirmation_two_epoch_proven,
        "TESTED_CODE_SHA": tested_code_sha,
        "done_gate": done_gate.as_dict_v1(),
        "ci_admission_snapshot": dict(ci_snapshot),
        "ENDGAME_IMPLEMENTATION_COMPLETE": done_gate.ok,
        "POST_ACTIVATION_IN_SCOPE": False,
    }
