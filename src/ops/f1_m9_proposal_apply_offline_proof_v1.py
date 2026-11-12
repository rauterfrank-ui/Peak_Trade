"""Bind a stored M9 review to the canonical owner Apply execution proof."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Any

from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID,
    compute_m9_reproducibility_digest_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    OwnerExplicitProductiveAuthorizationInputV1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    format_aware_utc_datetime_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    ChainStageV1,
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import (
    STATUS_EXECUTION_READY,
    F1M9ProductiveApplyExecutionPhaseV1,
    F1M9ProductiveApplyExecutionRequestV1,
    evaluate_f1_m9_productive_apply_execution_boundary_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    load_apply_ledger_entries_v1,
)
from src.governance.f1_m9_productive_runtime_apply_start_owner_binding_v1 import (
    evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1,
)
from src.governance.f1_m9_proposal_review_feedback_v1 import (
    read_f1_m9_proposal_review_feedback_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    ADMISSION_ADMITTED,
    OptimizationProposalGovernanceAdmissionRequestV1,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

_SCHEMA_VERSION = "f1_m9_proposal_apply_offline_proof_v1"


@dataclass(frozen=True, slots=True)
class F1M9ProposalApplyOfflineProofRequestV1:
    repo_root: Path
    original_plane_path: Path
    original_experiment_evidence_path: Path
    review_store: Path
    review_policy_digest: str
    review_feedback_digest: str
    evaluation_time_utc: datetime
    owner_configuration_authorization: OwnerExplicitProductiveAuthorizationInputV1 | None = None
    owner_apply_authorization: OwnerApplyAuthorizationInputV1 | None = None
    revocation_ledger_path: Path | None = None


def _read_original(path: Path, digest_key: str) -> dict[str, Any]:
    body = json.loads(path.read_bytes())
    if not isinstance(body, dict):
        raise ValueError(f"F1_M9_PROPOSAL_SOURCE_INVALID:{digest_key}")
    digest = body.get(digest_key)
    if compute_content_sha256({k: v for k, v in body.items() if k != digest_key}) != digest:
        raise ValueError(f"F1_M9_PROPOSAL_SOURCE_DIGEST_MISMATCH:{digest_key}")
    return body


def _disposition(context: dict[str, Any], status: str, reasons: tuple[str, ...]) -> dict[str, Any]:
    return {**context, "status": status, "reason_codes": list(reasons)}


def _evaluate(request: F1M9ProposalApplyOfflineProofRequestV1) -> dict[str, Any]:
    if request.evaluation_time_utc.utcoffset() is None:
        raise ValueError("F1_M9_PROPOSAL_APPLY_REQUIRES_AWARE_EVALUATION_TIME")
    plane = _read_original(request.original_plane_path, "result_digest")
    experiment = _read_original(request.original_experiment_evidence_path, "content_hash")
    ingress = build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=experiment,
        optimization_surface_id=SURFACE_ID,
    )
    if (
        ingress["experiment_id"] != experiment["candidate_experiment_id"]
        or ingress["candidate_ref"] != experiment["candidate_ref"]
    ):
        raise ValueError("F1_M9_PROPOSAL_EXPERIMENT_IDENTITY_MISMATCH")
    review = read_f1_m9_proposal_review_feedback_v1(
        store_root=request.review_store,
        ingress=ingress,
        review_policy_digest=request.review_policy_digest,
        expected_feedback_digest=request.review_feedback_digest,
    )
    proof = {
        "schema_version": _SCHEMA_VERSION,
        "authority": "NONE",
        "productive_apply_occurred": False,
        "external_effect_authorized": False,
        "evaluation_time_utc": format_aware_utc_datetime_v1(request.evaluation_time_utc),
        "plane_result_digest": plane["result_digest"],
        "experiment_evidence_digest": experiment["content_hash"],
        "ingress_digest": review.ingress_digest,
        "proposal_identity_digest": review.proposal_identity_digest,
        "review_feedback_digest": review.feedback_digest,
        "review_policy_digest": review.review_policy_digest,
        "candidate_ref": review.candidate_ref,
        "experiment_id": review.experiment_id,
        "parameter_config_delta": dict(ingress["parameter_config_delta"]),
        "admission_status": review.admission_status,
    }
    if compute_m9_reproducibility_digest_v1() != review.review_policy_digest:
        return _disposition(proof, "REVIEW_POLICY_CHANGED", ("M9_REVIEW_POLICY_DRIFT",))
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    if (
        admission.admission_status != review.admission_status
        or admission.reason_codes != review.reason_codes
        or compute_m9_reproducibility_digest_v1() != review.review_policy_digest
    ):
        return _disposition(proof, "REVIEW_DISPOSITION_CHANGED", admission.reason_codes)
    if admission.admission_status != ADMISSION_ADMITTED:
        return _disposition(proof, "REVIEW_DENIED", review.reason_codes)

    owner_input = request.owner_configuration_authorization
    if owner_input is None:
        return _disposition(
            proof, "AWAITING_OWNER_CONFIGURATION_AUTHORIZATION", ("OWNER_AUTHORIZATION_REQUIRED",)
        )
    registry_digest = str(
        load_scoped_join_registry_v1(repo_root=request.repo_root)["registry_digest"]
    )
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=ingress,
        admission=admission,
        owner_input=owner_input,
        registry_digest=registry_digest,
    )
    proof.update(
        registry_digest=registry_digest,
        owner_configuration_authorization_digest=owner_input.owner_authorization_record_digest,
        stopped_at=chain.stop_stage.value,
    )
    if (
        chain.stop_stage != ChainStageV1.PRODUCTIVE_APPLY
        or chain.per_ingress_binding is None
        or chain.authorization is None
        or chain.configuration is None
        or chain.runtime_transport is None
    ):
        return _disposition(proof, "CONFIGURATION_BOUNDARY_DENIED", chain.reason_codes)
    proof["configuration_digest"] = chain.configuration.configuration_digest
    apply_input = request.owner_apply_authorization
    if apply_input is None:
        return _disposition(
            proof, "AWAITING_OWNER_APPLY_AUTHORIZATION", ("OWNER_APPLY_RECORD_REQUIRED",)
        )
    source_revocations = request.revocation_ledger_path
    if source_revocations is None or not source_revocations.is_file():
        return _disposition(
            proof, "AWAITING_APPLY_REVOCATION_STATE", ("REVOCATION_LEDGER_REQUIRED",)
        )

    revocations = source_revocations.read_bytes()
    gate = evaluate_real_productive_apply_with_runtime_apply_start_precedence_v1(
        owner_apply_authorization_record_digest=apply_input.owner_apply_authorization_record_digest,
        repo_root=request.repo_root,
    )
    proof.update(
        owner_apply_record_digest=apply_input.owner_apply_authorization_record_digest,
        source_revocation_ledger_sha256=hashlib.sha256(revocations).hexdigest(),
        execution_phase=F1M9ProductiveApplyExecutionPhaseV1.EXECUTION_PROOF.value,
        productive_apply_binding_status=gate.binding_status,
        productive_apply_binding_reasons=list(gate.reason_codes),
    )
    with TemporaryDirectory(prefix="f1-m9-proposal-apply-proof-") as workspace:
        root = Path(workspace)
        ledgers = F1M9ProductiveApplyLedgerPathsV1(root / "apply.jsonl", root / "revocations.jsonl")
        ledgers.revocation_ledger_path.write_bytes(revocations)
        result = evaluate_f1_m9_productive_apply_execution_boundary_v1(
            F1M9ProductiveApplyExecutionRequestV1(
                owner_apply_input=apply_input,
                per_ingress_binding=chain.per_ingress_binding,
                authorization=chain.authorization,
                configuration=chain.configuration,
                registry_digest=registry_digest,
                ledger_paths=ledgers,
                execution_phase=F1M9ProductiveApplyExecutionPhaseV1.EXECUTION_PROOF,
                evaluation_time_utc=request.evaluation_time_utc,
            ),
            repo_root=request.repo_root,
        )
        if source_revocations.read_bytes() != revocations:
            raise ValueError("F1_M9_PROPOSAL_APPLY_REVOCATIONS_CHANGED")
        if (
            result.execution_status != STATUS_EXECUTION_READY
            or not result.productive_apply_authorized
            or result.configuration_after_execution is None
        ):
            return _disposition(proof, "APPLY_PROOF_DENIED", result.reason_codes)
        [entry] = load_apply_ledger_entries_v1(ledgers.apply_ledger_path)
        if (
            result.productive_apply_occurred
            or entry["apply_ledger_entry_digest"] != result.apply_ledger_entry_digest
            or entry["configuration_digest"]
            != result.configuration_after_execution.configuration_digest
            or entry["ingress_digest"] != review.ingress_digest
            or entry["authorization_digest"] != chain.authorization.authorization_digest
            or entry["owner_apply_authorization_record_digest"]
            != apply_input.owner_apply_authorization_record_digest
        ):
            raise ValueError("F1_M9_PROPOSAL_APPLY_OFFLINE_READBACK_MISMATCH")
    proof.update(
        offline_apply_ledger_entry_digest=entry["apply_ledger_entry_digest"],
        offline_configuration_digest=entry["configuration_digest"],
        execution_evidence_digest=result.execution_evidence_digest,
    )
    return _disposition(proof, "APPLY_PROOF_COMPLETE", result.reason_codes)


def read_f1_m9_proposal_apply_offline_proof_v1(
    *, store_root: Path, expected_sha256: str
) -> dict[str, Any]:
    if not is_valid_sha256_hex(expected_sha256):
        raise ValueError("F1_M9_PROPOSAL_APPLY_PROOF_DIGEST_INVALID")
    data = (store_root / f"{expected_sha256}.json").read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("F1_M9_PROPOSAL_APPLY_PROOF_DIGEST_MISMATCH")
    proof = json.loads(data)
    if (
        proof["schema_version"] != _SCHEMA_VERSION
        or proof["authority"] != "NONE"
        or proof["productive_apply_occurred"] is not False
        or proof["external_effect_authorized"] is not False
    ):
        raise ValueError("F1_M9_PROPOSAL_APPLY_PROOF_SCHEMA_MISMATCH")
    return proof


def run_and_store_f1_m9_proposal_apply_offline_proof_v1(
    request: F1M9ProposalApplyOfflineProofRequestV1, *, store_root: Path
) -> tuple[str, dict[str, Any]]:
    data = (deterministic_json_dumps(_evaluate(request)) + "\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    store_root.mkdir(parents=True, exist_ok=True)
    dest = store_root / f"{digest}.json"
    with NamedTemporaryFile(dir=store_root, prefix=".apply-proof-", delete=False) as stream:
        staging = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            try:
                os.link(staging, dest)
            except FileExistsError:
                pass
        finally:
            staging.unlink()
    return digest, read_f1_m9_proposal_apply_offline_proof_v1(
        store_root=store_root, expected_sha256=digest
    )
