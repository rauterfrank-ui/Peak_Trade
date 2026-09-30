"""End-to-end WP-04 proof composition (reuse WP-01..03 producers)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    Wp03ConvergenceProofV1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.admission_refresh_v1 import (
    build_standing_admission_payload_v1,
    prove_standing_pre_external_admission_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.ci_snapshot_v1 import (
    CiAdmissionSnapshotV1,
    load_ci_admission_snapshot_v1,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
    REQUIRED_CI_CONFIG_RELATIVE,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.done_gate_v1 import (
    CurrentN1EndgameDoneGateV1,
    evaluate_current_n1_endgame_done_gate_v1,
)
from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    StandingSupervisorRunResultV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
    PreExternalAutonomyAdmissionV1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.public_real_md_cap22_n1_chain_v1 import (
    PublicRealMdChainProofV1,
)


@dataclass(frozen=True)
class Wp04PackageProofV1:
    ok: bool
    admission: PreExternalAutonomyAdmissionV1
    done_gate: CurrentN1EndgameDoneGateV1
    ci_snapshot: CiAdmissionSnapshotV1
    admission_payload: Mapping[str, Any]


def prove_current_wp04_package_v1(
    *,
    repo_root: Path,
    public_chain: PublicRealMdChainProofV1,
    public_store_root: Path,
    private_store_root: Path,
    wp03: Wp03ConvergenceProofV1,
    reference_supervisor_run: StandingSupervisorRunResultV1,
    tested_code_sha: str,
    backlog_matrix: Mapping[str, Any],
    all_required_ci_green_at_admission: bool = False,
) -> Wp04PackageProofV1:
    admission = prove_standing_pre_external_admission_v1(
        public_chain=public_chain,
        public_store_root=public_store_root,
        private_store_root=private_store_root,
        wp03=wp03,
        reference_supervisor_run=reference_supervisor_run,
    )
    ci_snapshot = load_ci_admission_snapshot_v1(
        repo_root=repo_root,
        config_relative=REQUIRED_CI_CONFIG_RELATIVE,
        all_required_ci_green_at_admission=all_required_ci_green_at_admission,
    )
    done_gate = evaluate_current_n1_endgame_done_gate_v1(
        admission=admission,
        wp03=wp03,
        reference_supervisor_run=reference_supervisor_run,
        ci_snapshot=ci_snapshot,
    )
    payload = build_standing_admission_payload_v1(
        admission=admission,
        wp03=wp03,
        done_gate=done_gate,
        tested_code_sha=tested_code_sha,
        backlog_matrix=backlog_matrix,
        ci_snapshot={
            "schema_version": ci_snapshot.schema_version,
            "effective_required_contexts": list(ci_snapshot.effective_required_contexts),
            "all_required_ci_green_at_admission": ci_snapshot.all_required_ci_green_at_admission,
            "verification_note": ci_snapshot.verification_note,
        },
    )
    ok = admission.ok and wp03.ok and done_gate.mechanical_ok
    return Wp04PackageProofV1(
        ok=ok,
        admission=admission,
        done_gate=done_gate,
        ci_snapshot=ci_snapshot,
        admission_payload=payload,
    )


def write_standing_pre_external_autonomy_admission_evidence_v1(
    *,
    repo_root: Path,
    payload: Mapping[str, Any],
) -> Path:
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.constants_v1 import (
        EVIDENCE_ROOT_RELATIVE,
    )

    out_dir = repo_root / EVIDENCE_ROOT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "STANDING_PRE_EXTERNAL_AUTONOMY_ADMISSION_V1.json"
    path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
