import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.experiments.canonical_advanced_search_v1 import SearchAxisV1, SearchSpaceV1
from src.experiments.canonical_experiment_identity_v1 import (
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    run_optimization_universe_experiment_plane_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    build_owner_explicit_productive_authorization_input_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    build_owner_apply_authorization_input_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    append_revocation_ledger_entry_v1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_proposal_review_feedback_v1 import (
    evaluate_and_store_f1_m9_proposal_review_feedback_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.ops.f1_m9_proposal_apply_offline_proof_v1 import (
    F1M9ProposalApplyOfflineProofRequestV1,
    run_and_store_f1_m9_proposal_apply_offline_proof_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _champion,
    _identity_request,
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 11, 12, 8, 40, tzinfo=timezone.utc)


def _original_proposal(tmp_path, seconds):
    evidence = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    template = _identity_request(strategy_params={"max_age_seconds": 600})
    champion_identity = build_canonical_experiment_identity_v1(template)
    plane = run_optimization_universe_experiment_plane_v1(
        _plane_request(
            evidence,
            identity_template=template,
            champion=_champion(
                experiment_identity=champion_identity,
                experiment_id=derive_experiment_id_v1(champion_identity["identity_digest"]),
            ),
            search_space=SearchSpaceV1(
                search_space_id="search.m9.offline.v1",
                axes=(SearchAxisV1(name="max_age_seconds", values=(seconds,)),),
            ),
        )
    )
    experiment = build_optimization_experiment_evidence_from_plane_v1(plane)
    ingress = build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1(
        plane_result=plane,
        optimization_experiment_evidence=experiment,
        optimization_surface_id=SURFACE_ID,
    )
    assert ingress["parameter_config_delta"] == {"max_age_seconds": seconds}
    plane_path = tmp_path / "plane.json"
    experiment_path = tmp_path / "experiment.json"
    for path, payload in ((plane_path, plane), (experiment_path, experiment)):
        path.write_text(json.dumps(payload, default=dict), encoding="utf-8")
    review_store = tmp_path / "reviews"
    receipt = evaluate_and_store_f1_m9_proposal_review_feedback_v1(
        store_root=review_store, ingress=ingress
    )
    request = F1M9ProposalApplyOfflineProofRequestV1(
        repo_root=ROOT,
        original_plane_path=plane_path,
        original_experiment_evidence_path=experiment_path,
        review_store=review_store,
        review_policy_digest=receipt.review_policy_digest,
        review_feedback_digest=receipt.feedback_digest,
        evaluation_time_utc=NOW,
    )
    return request, ingress


def _owner_records(request, ingress):
    owner = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress, productive_target_id=PRODUCTIVE_TARGET_ID
    )
    registry_digest = str(load_scoped_join_registry_v1(repo_root=ROOT)["registry_digest"])
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=ingress, admission=admission, owner_input=owner, registry_digest=registry_digest
    )
    config = chain.configuration.configuration_record
    apply = build_owner_apply_authorization_input_v1(
        registry_digest=registry_digest,
        ingress_digest=config["ingress_digest"],
        binding_digest=chain.per_ingress_binding.binding_digest,
        owner_authorization_record_digest=config["owner_authorization_record_digest"],
        authorization_id=config["authorization_id"],
        authorization_digest=config["authorization_digest"],
        configuration_id=config["configuration_id"],
        configuration_digest=config["configuration_digest"],
        candidate_parameter_value_digest=config["candidate_parameter_value_digest"],
        productive_target_id=config["productive_target_id"],
        productive_target_version=config["productive_target_version"],
        productive_target_contract_digest=build_productive_target_contract_v1()["contract_digest"],
        not_before=(NOW - timedelta(minutes=1)).isoformat(),
        expires_at=(NOW + timedelta(minutes=1)).isoformat(),
    )
    return replace(
        request, owner_configuration_authorization=owner, owner_apply_authorization=apply
    )


def test_new_proposal_reaches_apply_proof_with_both_original_owner_records(tmp_path):
    request, ingress = _original_proposal(tmp_path, 300)
    store = tmp_path / "proof"
    _, missing = run_and_store_f1_m9_proposal_apply_offline_proof_v1(request, store_root=store)
    assert missing["status"] == "AWAITING_OWNER_CONFIGURATION_AUTHORIZATION"
    request = _owner_records(request, ingress)
    _, missing = run_and_store_f1_m9_proposal_apply_offline_proof_v1(
        replace(request, owner_apply_authorization=None), store_root=store
    )
    assert missing["status"] == "AWAITING_OWNER_APPLY_AUTHORIZATION"
    _, missing = run_and_store_f1_m9_proposal_apply_offline_proof_v1(request, store_root=store)
    assert missing["status"] == "AWAITING_APPLY_REVOCATION_STATE"
    revocations = tmp_path / "revocations.jsonl"
    initialize_empty_revocation_ledger_v1(revocations)
    request = replace(request, revocation_ledger_path=revocations)
    original_bytes = revocations.read_bytes()

    with ThreadPoolExecutor(max_workers=2) as executor:
        attempts = [
            executor.submit(
                run_and_store_f1_m9_proposal_apply_offline_proof_v1, request, store_root=store
            )
            for _ in range(2)
        ]
        first, second = (attempt.result() for attempt in attempts)
    assert first == second
    digest, proof = first
    assert len(list(store.glob("*.json"))) == 4
    assert proof["status"] == "APPLY_PROOF_COMPLETE"
    assert proof["parameter_config_delta"] == {"max_age_seconds": 300}
    assert proof["review_feedback_digest"] == request.review_feedback_digest
    assert proof["execution_phase"] == "EXECUTION_PROOF"
    assert proof["productive_apply_binding_status"] != "REAL_PRODUCTIVE_APPLY_DECISION_BOUND"
    assert proof["productive_apply_binding_reasons"]
    assert proof["authority"] == "NONE"
    assert proof["productive_apply_occurred"] is False
    assert proof["external_effect_authorized"] is False
    assert revocations.read_bytes() == original_bytes
    assert not (tmp_path / "apply.jsonl").exists()

    code = """
import json, sys
from pathlib import Path
from src.ops.f1_m9_proposal_apply_offline_proof_v1 import read_f1_m9_proposal_apply_offline_proof_v1
print(json.dumps(read_f1_m9_proposal_apply_offline_proof_v1(
    store_root=Path(sys.argv[1]), expected_sha256=sys.argv[2]
)))
"""
    cold = subprocess.run(
        ["./scripts/pt", "-c", code, str(store), digest],
        cwd=ROOT,
        capture_output=True,
        check=True,
        text=True,
    )
    assert json.loads(cold.stdout.splitlines()[-1]) == proof

    _, expired = run_and_store_f1_m9_proposal_apply_offline_proof_v1(
        replace(request, evaluation_time_utc=NOW + timedelta(minutes=1)), store_root=store
    )
    assert expired["status"] == "APPLY_PROOF_DENIED"
    assert "APPLY_EXPIRED" in expired["reason_codes"]
    assert "offline_apply_ledger_entry_digest" not in expired

    append_revocation_ledger_entry_v1(
        revocation_ledger_path=revocations,
        owner_apply_authorization_record_digest=proof["owner_apply_record_digest"],
        configuration_digest=proof["configuration_digest"],
        reason="offline test",
        operator_reference="offline fixture",
        revoked_at=NOW.isoformat(),
    )
    revoked_bytes = revocations.read_bytes()
    _, revoked = run_and_store_f1_m9_proposal_apply_offline_proof_v1(request, store_root=store)
    assert revoked["status"] == "APPLY_PROOF_DENIED"
    assert "owner_apply_authorization_revoked" in revoked["reason_codes"]
    assert "offline_apply_ledger_entry_digest" not in revoked
    assert revocations.read_bytes() == revoked_bytes


def test_denied_original_proposal_and_modified_evidence_stop_before_apply(tmp_path):
    request, _ = _original_proposal(tmp_path, 999)
    store = tmp_path / "proof"
    _, rejected = run_and_store_f1_m9_proposal_apply_offline_proof_v1(request, store_root=store)
    assert rejected["status"] == "REVIEW_DENIED"
    assert rejected["reason_codes"] == ["CANDIDATE_TARGET_OUT_OF_BOUNDS"]
    assert "offline_apply_ledger_entry_digest" not in rejected
    original = json.loads(request.original_plane_path.read_bytes())
    original["chain"]["selected_candidate"]["parameter_region"]["max_age_seconds"] = 300
    request.original_plane_path.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(ValueError, match="F1_M9_PROPOSAL_SOURCE_DIGEST_MISMATCH:result_digest"):
        run_and_store_f1_m9_proposal_apply_offline_proof_v1(request, store_root=store)
    assert len(list(store.glob("*.json"))) == 1
