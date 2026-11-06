"""F1/M9 scoped Owner Threshold Value authority tests (Owner-ratified policy)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.governance.authorized_productive_parameter_seam_v1 import (
    resolve_age_policy_from_authorized_seam_record_v1,
)
from src.governance.explicit_productive_authorization_v1 import (
    build_owner_explicit_productive_authorization_input_v1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    build_owner_apply_authorization_input_v1,
)
from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    build_owner_threshold_value_authorization_input_v1,
    compute_owner_threshold_value_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_authorization_chain_resolver_v1 import (
    resolve_f1_m9_per_ingress_authorization_chain_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    evaluate_f1_m9_per_ingress_authorization_binding_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    initialize_empty_revocation_ledger_v1,
)
from src.governance.f1_m9_scoped_owner_apply_authority_v1 import (
    F1M9ScopedOwnerApplyAdjudicationRequestV1,
    RUNTIME_APPLY_AUTHORITY_VALUE,
    evaluate_f1_m9_scoped_owner_productive_apply_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_authority_v1 import (
    CONCRETE_THRESHOLD_VALUE_AUTHORIZED,
    F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
    RUNTIME_THRESHOLD_VALUE_AUTHORITY,
    evaluate_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_closure_v1 import (
    prove_f1_m9_scoped_owner_threshold_value_authority_v1,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    append_threshold_revocation_ledger_entry_v1,
    initialize_empty_threshold_revocation_ledger_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationMaterializeRequestV1,
    materialize_governed_productive_configuration_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    ProductiveApplyAuthorizationStatusV1,
    ProductiveNumericMaxAgePolicyAdmissionV1,
    build_productive_target_contract_v1,
    validate_policy_admission_request_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID,
    CAPABILITY_VERSION,
    ThresholdValueAuthorizationStatusV1,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    OptimizationProposalGovernanceAdmissionRequestV1,
    evaluate_optimization_proposal_governance_admission_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    load_scoped_join_registry_v1,
)
from src.ops.productive_pure_stack_numeric_policy_shadow_campaign_v1.constants_v1 import (
    PRODUCTIVE_NUMERIC_VALUES_SET,
)
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED,
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    THRESHOLD_STATUS_UNRESOLVED,
    build_ratified_unresolved_max_age_policy_contract_v1,
    resolve_canonical_volatility_max_age_policy_for_evaluation_v1,
)
from src.trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from tests.governance.test_optimization_proposal_governance_ingress_v1 import (
    _ingress_for_m9,
)
from tests.trading.master_v2.test_double_play_runtime_typed_volatility_presence_gate_v1 import (
    _context,
    _valid_estimate,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
    evaluate_typed_volatility_binding_eligibility_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _apply_ledger_paths(tmp_path: Path) -> F1M9ProductiveApplyLedgerPathsV1:
    rev = tmp_path / "apply_revocation.jsonl"
    initialize_empty_revocation_ledger_v1(rev)
    return F1M9ProductiveApplyLedgerPathsV1(
        apply_ledger_path=tmp_path / "apply.jsonl",
        revocation_ledger_path=rev,
    )


def _threshold_ledger_paths(tmp_path: Path) -> F1M9ThresholdValueAuthorizationLedgerPathsV1:
    rev = tmp_path / "threshold_revocation.jsonl"
    initialize_empty_threshold_revocation_ledger_v1(rev)
    return F1M9ThresholdValueAuthorizationLedgerPathsV1(
        threshold_ledger_path=tmp_path / "threshold.jsonl",
        threshold_revocation_ledger_path=rev,
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


def _applied_configuration(artifacts: dict[str, Any], tmp_path: Path) -> Any:
    apply_input = _apply_input_from_artifacts(artifacts)
    paths = _apply_ledger_paths(tmp_path)
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
    assert result.productive_apply_authorized
    assert result.configuration_after_apply is not None
    return result.configuration_after_apply, apply_input, paths


def _threshold_input_from_applied(
    artifacts: dict[str, Any],
    applied_config: Any,
    apply_input: Any,
    *,
    numeric_override: float | None = None,
) -> Any:
    record = applied_config.configuration_record
    assert record is not None
    contract = build_productive_target_contract_v1()
    numeric = float(record["numeric_max_age_seconds"])
    if numeric_override is not None:
        numeric = float(numeric_override)
    now = datetime.now(timezone.utc)
    apply_digest = str(apply_input.owner_apply_authorization_record_digest)
    return build_owner_threshold_value_authorization_input_v1(
        registry_digest=artifacts["registry_digest"],
        ingress_digest=str(record["ingress_digest"]),
        per_ingress_binding_digest=artifacts["binding"].binding_digest,
        owner_authorization_record_digest=str(record["owner_authorization_record_digest"]),
        authorization_id=str(record["authorization_id"]),
        authorization_digest=str(record["authorization_digest"]),
        configuration_id=str(record["configuration_id"]),
        configuration_digest=str(record["configuration_digest"]),
        candidate_parameter_value_digest=str(record["candidate_parameter_value_digest"]),
        productive_target_id=str(record["productive_target_id"]),
        productive_target_version=str(record["productive_target_version"]),
        productive_target_contract_digest=str(contract["contract_digest"]),
        ratified_threshold_capability_id=str(record["threshold_capability_id"]),
        ratified_threshold_capability_version=str(record["threshold_capability_version"]),
        owner_apply_authorization_record_digest=apply_digest,
        productive_apply_authorization_digest=apply_digest,
        threshold_numeric_max_age_seconds=numeric,
        not_before=(now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        expires_at=(now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def test_closure_proof() -> None:
    assert prove_f1_m9_scoped_owner_threshold_value_authority_v1(repo_root=REPO_ROOT)


def test_global_invariants() -> None:
    assert PRODUCTIVE_NUMERIC_VALUES_SET == 0
    assert NUMERIC_MAX_AGE_DECIDED is False
    assert ENFORCEMENT_ENABLED is False
    assert CONCRETE_THRESHOLD_VALUE_AUTHORIZED is False


def test_config_numeric_alone_does_not_ratify_policy(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    from src.governance.authorized_productive_parameter_seam_v1 import (
        AuthorizedProductiveParameterSeamBindRequestV1,
        bind_authorized_productive_parameter_seam_v1,
    )

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=artifacts["configuration"])
    )
    assert seam.seam_record is not None
    policy = resolve_age_policy_from_authorized_seam_record_v1(seam.seam_record)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED


def test_apply_alone_does_not_ratify_seam_policy(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, _, _ = _applied_configuration(artifacts, tmp_path)
    from src.governance.authorized_productive_parameter_seam_v1 import (
        AuthorizedProductiveParameterSeamBindRequestV1,
        bind_authorized_productive_parameter_seam_v1,
    )

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(configuration=applied)
    )
    assert seam.seam_record is not None
    policy = resolve_age_policy_from_authorized_seam_record_v1(seam.seam_record)
    assert policy.threshold_status == THRESHOLD_STATUS_UNRESOLVED


def test_valid_threshold_authorizes_and_closes_admission_gate(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(artifacts, applied, apply_input)
    threshold_paths = _threshold_ledger_paths(tmp_path)
    result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=applied,
            registry_digest=artifacts["registry_digest"],
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=threshold_paths,
        )
    )
    assert result.threshold_value_authorized is True
    assert result.runtime_threshold_authority == RUNTIME_THRESHOLD_VALUE_AUTHORITY
    assert result.configuration_after_threshold is not None
    from src.governance.authorized_productive_parameter_seam_v1 import (
        AuthorizedProductiveParameterSeamBindRequestV1,
        bind_authorized_productive_parameter_seam_v1,
    )

    seam = bind_authorized_productive_parameter_seam_v1(
        AuthorizedProductiveParameterSeamBindRequestV1(
            configuration=result.configuration_after_threshold
        )
    )
    assert seam.seam_record is not None
    policy = resolve_age_policy_from_authorized_seam_record_v1(seam.seam_record)
    assert policy.threshold_status == THRESHOLD_STATUS_RATIFIED_NUMERIC
    assert policy.enforcement_enabled is False


def test_full_chain_threshold_to_presence_gate(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, _ = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(artifacts, applied, apply_input)
    chain = resolve_f1_m9_per_ingress_authorization_chain_v1(
        ingress=artifacts["ingress"],
        admission=artifacts["admission"],
        owner_input=artifacts["owner_input"],
        registry_digest=artifacts["registry_digest"],
        owner_apply_input=apply_input,
        ledger_paths=_apply_ledger_paths(tmp_path),
        owner_threshold_input=threshold_input,
        threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
    )
    assert chain.threshold_value_authorized is True
    assert chain.seam is not None and chain.seam.seam_record is not None
    estimate = _valid_estimate()
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        with_computed_input_digest(_context(volatility_estimate=0.0)),
        estimate,
    )
    elig = evaluate_typed_volatility_binding_eligibility_v1(ctx)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        ctx,
        eligibility=elig,
        authorized_productive_parameter_seam=chain.seam.seam_record,
    )
    assert gate.max_age_policy_evidence is not None
    assert gate.max_age_policy_evidence.threshold_status == THRESHOLD_STATUS_RATIFIED_NUMERIC
    assert gate.max_age_policy_evidence.enforcement_applied is False


def test_numeric_mismatch_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    record = applied.configuration_record
    assert record is not None
    wrong = float(record["numeric_max_age_seconds"]) + 60.0
    threshold_input = _threshold_input_from_applied(
        artifacts, applied, apply_input, numeric_override=wrong
    )
    result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=applied,
            registry_digest=artifacts["registry_digest"],
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
        )
    )
    assert result.threshold_value_authorized is False
    assert "THRESHOLD_NUMERIC_CONFIGURATION_MISMATCH" in result.reason_codes


def test_out_of_domain_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(
        artifacts, applied, apply_input, numeric_override=301.0
    )
    result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=applied,
            registry_digest=artifacts["registry_digest"],
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
        )
    )
    assert result.threshold_value_authorized is False


def test_expired_threshold_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(artifacts, applied, apply_input)
    record = dict(threshold_input.owner_threshold_authorization_record)
    record["expires_at"] = "2020-01-01T00:00:00Z"
    record["threshold_value_authorization_record_digest"] = (
        compute_owner_threshold_value_authorization_record_digest_v1(record)
    )
    from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
        OwnerThresholdValueAuthorizationInputV1,
    )

    bad = OwnerThresholdValueAuthorizationInputV1(
        owner_threshold_authorization_record=record,
        owner_threshold_authorization_record_digest=str(
            record["threshold_value_authorization_record_digest"]
        ),
    )
    result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=bad,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=applied,
            registry_digest=artifacts["registry_digest"],
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=_threshold_ledger_paths(tmp_path),
            evaluation_time_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    assert result.threshold_value_authorized is False
    assert "THRESHOLD_EXPIRED" in result.reason_codes


def test_revoked_threshold_denied(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(artifacts, applied, apply_input)
    threshold_paths = _threshold_ledger_paths(tmp_path)
    digest = threshold_input.owner_threshold_authorization_record_digest
    config_digest = str(applied.configuration_record["configuration_digest"])
    append_threshold_revocation_ledger_entry_v1(
        revocation_ledger_path=threshold_paths.threshold_revocation_ledger_path,
        threshold_value_authorization_record_digest=digest,
        configuration_digest=config_digest,
        reason="test",
        operator_reference="test",
        revoked_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    result = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
        F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
            owner_threshold_input=threshold_input,
            per_ingress_binding=artifacts["binding"],
            authorization=artifacts["authorization"],
            configuration=applied,
            registry_digest=artifacts["registry_digest"],
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=threshold_paths,
        )
    )
    assert result.threshold_value_authorized is False


def test_threshold_replay_idempotent(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, apply_paths = _applied_configuration(artifacts, tmp_path)
    threshold_input = _threshold_input_from_applied(artifacts, applied, apply_input)
    threshold_paths = _threshold_ledger_paths(tmp_path)
    request = F1M9ScopedOwnerThresholdValueAdjudicationRequestV1(
        owner_threshold_input=threshold_input,
        per_ingress_binding=artifacts["binding"],
        authorization=artifacts["authorization"],
        configuration=applied,
        registry_digest=artifacts["registry_digest"],
        apply_ledger_paths=apply_paths,
        threshold_ledger_paths=threshold_paths,
    )
    first = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(request)
    second = evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(request)
    assert first.threshold_value_authorized and second.threshold_value_authorized
    assert second.threshold_status == "IDEMPOTENT_REPLAY"
    assert first.threshold_ledger_entry_digest == second.threshold_ledger_entry_digest


def test_apply_without_threshold_record_admission_still_blocked(tmp_path: Path) -> None:
    artifacts = _build_chain_artifacts(tmp_path)
    applied, apply_input, _ = _applied_configuration(artifacts, tmp_path)
    record = applied.configuration_record
    assert record is not None
    admission = ProductiveNumericMaxAgePolicyAdmissionV1(
        productive_target_id=str(record["productive_target_id"]),
        productive_target_version=str(record["productive_target_version"]),
        ratified_threshold_capability_id=CAPABILITY_ID,
        ratified_threshold_capability_version=CAPABILITY_VERSION,
        threshold_value_authorization_status="NONE",
        threshold_value_authorization_digest=None,
        threshold_numeric_max_age_seconds=float(record["numeric_max_age_seconds"]),
        productive_apply_authorization_status=ProductiveApplyAuthorizationStatusV1.AUTHORIZED.value,
        productive_apply_authorization_digest=str(record["productive_apply_authorization_digest"]),
    )
    ok, reasons = validate_policy_admission_request_v1(admission)
    assert ok is False
    assert "THRESHOLD_VALUE_AUTHORIZATION_REQUIRED" in reasons
    policy = resolve_canonical_volatility_max_age_policy_for_evaluation_v1(admission)
    assert policy == build_ratified_unresolved_max_age_policy_contract_v1()
