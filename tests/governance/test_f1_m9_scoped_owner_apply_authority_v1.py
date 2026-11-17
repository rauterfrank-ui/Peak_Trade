"""F1/M9 scoped Owner Productive Apply authority tests (Owner-ratified policy)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest

from src.governance.explicit_productive_authorization_v1 import (
    build_owner_explicit_productive_authorization_input_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    build_owner_apply_authorization_input_v1,
    compute_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    ChainStageV1,
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    append_revocation_ledger_entry_v1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
    resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
)
from src.governance.f1_m9_productive_apply_execution_boundary_v1 import DECISION_CONFIG
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    F1M9ScopedOwnerApplyAdjudicationRequestV1,
    RUNTIME_APPLY_AUTHORITY_VALUE,
    evaluate_f1_m9_scoped_owner_productive_apply_v1,
)
from src.governance.f1_m9_scoped_owner_apply_closure_v1 import (
    prove_f1_m9_scoped_owner_apply_authority_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
    runtime_apply_possible_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    ProductiveApplyAuthorizationStatusV1,
    ProductiveNumericMaxAgePolicyAdmissionV1,
    build_productive_target_contract_v1,
    validate_policy_admission_request_v1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
    direct_productive_write_possible_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    NUMERIC_MAX_AGE_DECIDED,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def _build_chain_artifacts(tmp_path: Path) -> dict[str, Any]:
    registry = load_scoped_join_registry_v1(repo_root=REPO_ROOT)
    ingress = _ingress_for_m9(tmp_path)
    admission = evaluate_optimization_proposal_governance_admission_v1(
        OptimizationProposalGovernanceAdmissionRequestV1(ingress=ingress)
    )
    owner_input = build_owner_explicit_productive_authorization_input_v1(
        ingress=ingress,
        productive_target_id=PRODUCTIVE_TARGET_ID,
    )
    binding = evaluate_f1_m9_per_ingress_authorization_binding_v1(
        ingress=ingress,
        owner_input=owner_input,
        registry_digest=str(registry["registry_digest"]),
    )
    from src.governance.explicit_productive_authorization_v1 import (
        ExplicitProductiveAuthorizationEvaluateRequestV1,
        evaluate_explicit_productive_authorization_v1,
    )

    authorization = evaluate_explicit_productive_authorization_v1(
        ExplicitProductiveAuthorizationEvaluateRequestV1(
            ingress=ingress,
            admission=admission,
            productive_target_id=PRODUCTIVE_TARGET_ID,
            owner_authorization_input=owner_input,
        )
    )
    configuration = materialize_governed_productive_configuration_v1(
        GovernedProductiveConfigurationMaterializeRequestV1(
            authorization=authorization,
            ingress=ingress,
        )
    )
    return {
        "registry_digest": str(registry["registry_digest"]),
        "ingress": ingress,
        "admission": admission,
        "owner_input": owner_input,
        "binding": binding,
        "authorization": authorization,
        "configuration": configuration,
    }


def _apply_input_from_artifacts(artifacts: dict[str, Any]) -> Any:
    config = artifacts["configuration"].configuration_record
    assert config is not None
    contract = build_productive_target_contract_v1()
    now = datetime.now(timezone.utc)
    return build_owner_apply_authorization_input_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(config["ingress_digest"]),
        binding_digest=artifacts["binding"].binding_digest,
        owner_authorization_record_digest=str(config["owner_authorization_record_digest"]),
        authorization_id=str(config["authorization_id"]),
        authorization_digest=str(config["authorization_digest"]),
        configuration_id=str(config["configuration_id"]),
        configuration_digest=str(config["configuration_digest"]),
        candidate_parameter_value_digest=str(config["candidate_parameter_value_digest"]),
        productive_target_id=str(config["productive_target_id"]),
        productive_target_version=str(config["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        not_before=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def test_closure_proof() -> None:
    assert prove_f1_m9_scoped_owner_apply_authority_v1(repo_root=REPO_ROOT)


def test_authorization_without_apply_record_blocked_at_chain(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
    )
    assert chain.productive_apply_authorized is False
    assert chain.stop_stage == ChainStageV1.PRODUCTIVE_APPLY


def test_valid_apply_authorizes_scoped_configuration(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = _ledger_paths(tmp_path)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
        owner_apply_input=apply_input,
        ledger_paths=paths,
    )
    assert chain.productive_apply_authorized is True
    assert chain.runtime_apply_authority == RUNTIME_APPLY_AUTHORITY_VALUE
    assert chain.configuration is not None
    record = chain.configuration.configuration_record
    assert record is not None
    assert record["runtime_applied"] is True
    assert record["runtime_apply_authority"] == RUNTIME_APPLY_AUTHORITY_VALUE


def test_apply_record_cannot_authorize_other_configuration_digest(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    record = dict(apply_input.owner_apply_authorization_record)
    record["configuration_digest"] = "0" * 64
    record["owner_apply_authorization_record_digest"] = (
        compute_owner_apply_authorization_record_digest_v1(record)
    )
    bad_input = OwnerApplyAuthorizationInputV1(
        owner_apply_authorization_record=record,
        owner_apply_authorization_record_digest=str(
            record["owner_apply_authorization_record_digest"]
        ),
    )
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=bad_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
        )
    )
    assert result.productive_apply_authorized is False
    assert "CONFIGURATION_DIGEST_MISMATCH" in result.reason_codes


@pytest.mark.parametrize("execution_proof", [False, True])
def test_resealed_foreign_issuer_is_denied_before_ledger(
    tmp_path: Path, execution_proof: bool
) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    record = dict(apply_input.owner_apply_authorization_record)
    record["authorizer_identity"] = "FOREIGN_APPLY_ISSUER"
    digest = compute_owner_apply_authorization_record_digest_v1(record)
    record["owner_apply_authorization_record_digest"] = digest
    paths = _ledger_paths(tmp_path)
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=OwnerApplyAuthorizationInputV1(record, digest),
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=paths,
        ),
        execution_proof=execution_proof,
    )
    assert result.reason_codes == ("AUTHORIZER_IDENTITY_MISMATCH",)
    assert result.productive_apply_authorized is False
    assert result.configuration_after_apply is None
    assert not paths.apply_ledger_path.exists()


def test_scoped_record_with_owner_name_requires_bound_decision_before_ledger(
    tmp_path: Path,
) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    paths = _ledger_paths(tmp_path)
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=_apply_input_from_artifacts(artifacts),
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=paths,
        ),
        repo_root=REPO_ROOT,
    )
    assert "OWNER_APPLY_RECORD_NOT_BOUND_BY_OWNER_DECISION" in result.reason_codes
    assert result.productive_apply_authorized is False
    assert result.configuration_after_apply is None
    assert not paths.apply_ledger_path.exists()


def test_execution_proof_cannot_write_the_configured_durable_apply_ledger(
    tmp_path: Path,
) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    decision = tmp_path / DECISION_CONFIG
    decision.parent.mkdir(parents=True)
    decision.write_bytes((REPO_ROOT / DECISION_CONFIG).read_bytes())
    paths = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=tmp_path)
    initialize_empty_revocation_ledger_v1(paths.revocation_ledger_path)
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=_apply_input_from_artifacts(artifacts),
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=paths,
        ),
        repo_root=tmp_path,
        execution_proof=True,
    )
    assert result.reason_codes == ("EXECUTION_PROOF_REQUIRES_ISOLATED_APPLY_LEDGER",)
    assert result.productive_apply_authorized is False
    assert not paths.apply_ledger_path.exists()


def test_expired_apply_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    now = datetime.now(timezone.utc)
    apply_input = build_owner_apply_authorization_input_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(artifacts["configuration"].configuration_record["ingress_digest"]),
        binding_digest=artifacts["binding"].binding_digest,
        owner_authorization_record_digest=str(
            artifacts["configuration"].configuration_record["owner_authorization_record_digest"]
        ),
        authorization_id=str(artifacts["configuration"].configuration_record["authorization_id"]),
        authorization_digest=str(
            artifacts["configuration"].configuration_record["authorization_digest"]
        ),
        configuration_id=str(artifacts["configuration"].configuration_record["configuration_id"]),
        configuration_digest=str(
            artifacts["configuration"].configuration_record["configuration_digest"]
        ),
        candidate_parameter_value_digest=str(
            artifacts["configuration"].configuration_record["candidate_parameter_value_digest"]
        ),
        productive_target_id=str(
            artifacts["configuration"].configuration_record["productive_target_id"]
        ),
        productive_target_version=str(
            artifacts["configuration"].configuration_record["productive_target_version"]
        ),
        productive_target_contract_digest=str(
            build_productive_target_contract_v1()["contract_digest"]
        ),
        not_before=(now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=_ledger_paths(tmp_path),
            evaluation_time_utc=now,
        )
    )
    assert result.productive_apply_authorized is False
    assert "APPLY_EXPIRED" in result.reason_codes


def test_revoked_apply_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = _ledger_paths(tmp_path)
    digest = apply_input.owner_apply_authorization_record_digest
    config_digest = str(apply_input.owner_apply_authorization_record["configuration_digest"])
    append_revocation_ledger_entry_v1(
        revocation_ledger_path=paths.revocation_ledger_path,
        owner_apply_authorization_record_digest=digest,
        configuration_digest=config_digest,
        reason="operator_revoke",
        operator_reference="test",
        revoked_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=paths,
        )
    )
    assert result.productive_apply_authorized is False
    assert "owner_apply_authorization_revoked" in result.reason_codes


def test_unavailable_revocation_ledger_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=tmp_path / "missing_revocation.jsonl",
    )
    result = evaluate_f1_m9_scoped_owner_productive_apply_v1(
        F1M9ScopedOwnerApplyAdjudicationRequestV1(
            owner_apply_input=apply_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=artifacts["configuration"],
            registry_digest=artifacts["registry_digest"],
            ledger_paths=paths,
        )
    )
    assert result.productive_apply_authorized is False
    assert "revocation_ledger_unavailable" in result.reason_codes


def test_apply_replay_idempotent(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = _ledger_paths(tmp_path)
    request = F1M9ScopedOwnerApplyAdjudicationRequestV1(
        owner_apply_input=apply_input,
        per_ingress_binding=artifacts["binding"],
        authorization=artifacts["authorization"],
        configuration=artifacts["configuration"],
        registry_digest=artifacts["registry_digest"],
        ledger_paths=paths,
    )
    first = evaluate_f1_m9_scoped_owner_productive_apply_v1(request, execution_proof=True)
    second = evaluate_f1_m9_scoped_owner_productive_apply_v1(request, execution_proof=True)
    assert first.productive_apply_authorized is True
    assert second.productive_apply_authorized is True
    assert second.apply_status == "IDEMPOTENT_REPLAY"
    assert first.apply_ledger_entry_digest == second.apply_ledger_entry_digest


def test_global_invariants_unchanged() -> None:
    assert runtime_apply_possible_v1() is False
    assert direct_productive_write_possible_v1() is False
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False


def test_runtime_applied_does_not_ratify_threshold_admission(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = _ledger_paths(tmp_path)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
        owner_apply_input=apply_input,
        ledger_paths=paths,
    )
    assert chain.productive_apply_authorized is True
    record = chain.configuration.configuration_record
    assert record is not None
    admission = ProductiveNumericMaxAgePolicyAdmissionV1(
        productive_target_id=str(record["productive_target_id"]),
        productive_target_version=str(record["productive_target_version"]),
        ratified_threshold_capability_id=str(record["threshold_capability_id"]),
        ratified_threshold_capability_version=str(record["threshold_capability_version"]),
        threshold_value_authorization_status="NONE",
        threshold_value_authorization_digest=None,
        threshold_numeric_max_age_seconds=float(record["numeric_max_age_seconds"]),
        productive_apply_authorization_status=ProductiveApplyAuthorizationStatusV1.AUTHORIZED.value,
        productive_apply_authorization_digest=str(record["productive_apply_authorization_digest"]),
    )
    ok, reasons = validate_policy_admission_request_v1(admission)
    assert ok is False
    assert "THRESHOLD_VALUE_AUTHORIZATION_REQUIRED" in reasons
