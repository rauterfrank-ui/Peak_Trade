"""Versioned fail-closed restart session contract builder and validator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    CAPABILITY_ID,
    CONFIRMATION_SESSION_ID,
    CONTROLLED_RESTART_REASON,
    DURABLE_STATE_LINEAGE_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    NO_ORDER_BOUNDARY_ASSERTIONS,
    REQUIRED_CONTRACT_FIELDS,
    REQUIRED_RECONCILIATION_BEFORE_ALPHA,
    RESTART_CAMPAIGN_ID,
    SCHEMA_VERSION,
    SEGMENT_ROLE_POST,
    SEGMENT_ROLE_PRE,
    SEGMENT_ROLES,
    SESSION_ID,
    CANONICAL_INSTRUMENT_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartSessionContractV1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)


class RestartContractError(RuntimeError):
    """Fail-closed restart contract error."""


def _activation_digest_v1(*, repo_root: Path) -> str:
    activation = load_activation_config_v1(
        config_path=repo_root
        / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
    )
    if not bool(activation.full_canonical_stateful_runtime_active):
        raise RestartContractError("activation_not_active")
    if not bool(activation.simulated_execution_active):
        raise RestartContractError("simulated_execution_not_active")
    return str(activation.config_digest)


def build_restart_session_contract_v1(
    *,
    repository_sha: str,
    segment_role: str,
    segment_id: str,
    runtime_session_id: str,
    authorization_id: str,
    authorization_digest: str,
    expected_runtime_state_digest: str,
    expected_portfolio_digest: str,
    expected_scope_digest: str,
    expected_accounting_digest: str,
    expected_evidence_cursor: str,
    predecessor_segment_id: str | None = None,
    predecessor_terminal_manifest_digest: str | None = None,
    restart_campaign_id: str = RESTART_CAMPAIGN_ID,
    durable_state_lineage_id: str = DURABLE_STATE_LINEAGE_ID,
    confirmation_session_id: str = CONFIRMATION_SESSION_ID,
    instrument_identity: str = CANONICAL_INSTRUMENT_ID,
    controlled_restart_reason: str = CONTROLLED_RESTART_REASON,
    minimum_pre_restart_distinct_observations: int = MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    repo_root: Path | None = None,
) -> RestartSessionContractV1:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    if segment_role not in SEGMENT_ROLES:
        raise RestartContractError(f"invalid_segment_role:{segment_role}")
    if segment_role == SEGMENT_ROLE_PRE:
        if predecessor_segment_id is not None or predecessor_terminal_manifest_digest is not None:
            raise RestartContractError("pre_restart_must_not_have_predecessor")
    if segment_role == SEGMENT_ROLE_POST:
        if not predecessor_segment_id or not predecessor_terminal_manifest_digest:
            raise RestartContractError("post_restart_requires_predecessor")

    config_digest = _activation_digest_v1(repo_root=root)
    provisional: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "capability_id": CAPABILITY_ID,
        "restart_campaign_id": restart_campaign_id,
        "durable_state_lineage_id": durable_state_lineage_id,
        "segment_id": segment_id,
        "segment_role": segment_role,
        "predecessor_segment_id": predecessor_segment_id,
        "predecessor_terminal_manifest_digest": predecessor_terminal_manifest_digest,
        "expected_repository_sha": repository_sha,
        "expected_config_digest": config_digest,
        "expected_instrument_identity": instrument_identity,
        "expected_confirmation_session_id": confirmation_session_id,
        "expected_runtime_state_digest": expected_runtime_state_digest,
        "expected_portfolio_digest": expected_portfolio_digest,
        "expected_scope_digest": expected_scope_digest,
        "expected_accounting_digest": expected_accounting_digest,
        "expected_evidence_cursor": expected_evidence_cursor,
        "authorization_id": authorization_id,
        "authorization_digest": authorization_digest,
        "runtime_session_id": runtime_session_id,
        "controlled_restart_reason": controlled_restart_reason,
        "minimum_pre_restart_distinct_observations": int(minimum_pre_restart_distinct_observations),
        "required_reconciliation_before_alpha": REQUIRED_RECONCILIATION_BEFORE_ALPHA,
        "no_order_boundary_assertions": list(NO_ORDER_BOUNDARY_ASSERTIONS),
        "session_id": SESSION_ID,
    }
    digest = sha256_canonical_v1({k: v for k, v in provisional.items() if k != "contract_digest"})
    return RestartSessionContractV1(
        schema_version=SCHEMA_VERSION,
        capability_id=CAPABILITY_ID,
        restart_campaign_id=restart_campaign_id,
        durable_state_lineage_id=durable_state_lineage_id,
        segment_id=segment_id,
        segment_role=segment_role,
        predecessor_segment_id=predecessor_segment_id,
        predecessor_terminal_manifest_digest=predecessor_terminal_manifest_digest,
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        expected_instrument_identity=instrument_identity,
        expected_confirmation_session_id=confirmation_session_id,
        expected_runtime_state_digest=expected_runtime_state_digest,
        expected_portfolio_digest=expected_portfolio_digest,
        expected_scope_digest=expected_scope_digest,
        expected_accounting_digest=expected_accounting_digest,
        expected_evidence_cursor=expected_evidence_cursor,
        authorization_id=authorization_id,
        authorization_digest=authorization_digest,
        runtime_session_id=runtime_session_id,
        controlled_restart_reason=controlled_restart_reason,
        minimum_pre_restart_distinct_observations=int(minimum_pre_restart_distinct_observations),
        required_reconciliation_before_alpha=REQUIRED_RECONCILIATION_BEFORE_ALPHA,
        no_order_boundary_assertions=tuple(NO_ORDER_BOUNDARY_ASSERTIONS),
        contract_digest=digest,
    )


def validate_restart_session_contract_v1(
    payload: Mapping[str, Any],
    *,
    repository_sha: str | None = None,
    config_digest: str | None = None,
    instrument_identity: str | None = None,
    confirmation_session_id: str | None = None,
    durable_state_lineage_id: str | None = None,
    restart_campaign_id: str | None = None,
    consumed_authorization_ids: set[str] | None = None,
) -> RestartSessionContractV1:
    if not isinstance(payload, Mapping):
        raise RestartContractError("contract_not_mapping")
    unknown = sorted(
        set(payload.keys()) - set(REQUIRED_CONTRACT_FIELDS) - {"contract_digest", "session_id"}
    )
    if unknown:
        raise RestartContractError(f"unknown_fields:{','.join(unknown)}")
    missing = [k for k in REQUIRED_CONTRACT_FIELDS if k not in payload]
    if missing:
        raise RestartContractError(f"missing_fields:{','.join(missing)}")

    role = str(payload["segment_role"])
    if role not in SEGMENT_ROLES:
        raise RestartContractError(f"invalid_segment_role:{role}")
    if str(payload["schema_version"]) != SCHEMA_VERSION:
        raise RestartContractError("schema_version_mismatch")
    if str(payload["capability_id"]) != CAPABILITY_ID:
        raise RestartContractError("capability_id_mismatch")

    if repository_sha is not None and str(payload["expected_repository_sha"]) != repository_sha:
        raise RestartContractError("repository_mismatch")
    if config_digest is not None and str(payload["expected_config_digest"]) != config_digest:
        raise RestartContractError("config_mismatch")
    if (
        instrument_identity is not None
        and str(payload["expected_instrument_identity"]) != instrument_identity
    ):
        raise RestartContractError("instrument_mismatch")
    if (
        confirmation_session_id is not None
        and str(payload["expected_confirmation_session_id"]) != confirmation_session_id
    ):
        raise RestartContractError("confirmation_session_mismatch")
    if (
        durable_state_lineage_id is not None
        and str(payload["durable_state_lineage_id"]) != durable_state_lineage_id
    ):
        raise RestartContractError("lineage_mismatch")
    if (
        restart_campaign_id is not None
        and str(payload["restart_campaign_id"]) != restart_campaign_id
    ):
        raise RestartContractError("campaign_mismatch")

    auth_id = str(payload["authorization_id"])
    if consumed_authorization_ids and auth_id in consumed_authorization_ids:
        raise RestartContractError("authorization_reuse_forbidden")

    if role == SEGMENT_ROLE_PRE:
        if payload.get("predecessor_segment_id") is not None:
            raise RestartContractError("pre_restart_must_not_have_predecessor")
        if payload.get("predecessor_terminal_manifest_digest") is not None:
            raise RestartContractError("pre_restart_must_not_have_predecessor_digest")
    if role == SEGMENT_ROLE_POST:
        if not payload.get("predecessor_segment_id"):
            raise RestartContractError("post_restart_requires_predecessor")
        if not payload.get("predecessor_terminal_manifest_digest"):
            raise RestartContractError("post_restart_requires_predecessor_digest")

    assertions = payload["no_order_boundary_assertions"]
    if not isinstance(assertions, list) or sorted(assertions) != sorted(
        NO_ORDER_BOUNDARY_ASSERTIONS
    ):
        raise RestartContractError("no_order_boundary_assertions_mismatch")
    if bool(payload["required_reconciliation_before_alpha"]) is not True:
        raise RestartContractError("reconciliation_before_alpha_required")

    provisional = {k: payload[k] for k in REQUIRED_CONTRACT_FIELDS}
    provisional["session_id"] = payload.get("session_id", SESSION_ID)
    digest = sha256_canonical_v1(provisional)
    declared = payload.get("contract_digest")
    if declared is not None and str(declared) != digest:
        raise RestartContractError("contract_digest_mismatch")

    return RestartSessionContractV1(
        schema_version=str(payload["schema_version"]),
        capability_id=str(payload["capability_id"]),
        restart_campaign_id=str(payload["restart_campaign_id"]),
        durable_state_lineage_id=str(payload["durable_state_lineage_id"]),
        segment_id=str(payload["segment_id"]),
        segment_role=role,
        predecessor_segment_id=(
            None
            if payload.get("predecessor_segment_id") is None
            else str(payload["predecessor_segment_id"])
        ),
        predecessor_terminal_manifest_digest=(
            None
            if payload.get("predecessor_terminal_manifest_digest") is None
            else str(payload["predecessor_terminal_manifest_digest"])
        ),
        expected_repository_sha=str(payload["expected_repository_sha"]),
        expected_config_digest=str(payload["expected_config_digest"]),
        expected_instrument_identity=str(payload["expected_instrument_identity"]),
        expected_confirmation_session_id=str(payload["expected_confirmation_session_id"]),
        expected_runtime_state_digest=str(payload["expected_runtime_state_digest"]),
        expected_portfolio_digest=str(payload["expected_portfolio_digest"]),
        expected_scope_digest=str(payload["expected_scope_digest"]),
        expected_accounting_digest=str(payload["expected_accounting_digest"]),
        expected_evidence_cursor=str(payload["expected_evidence_cursor"]),
        authorization_id=auth_id,
        authorization_digest=str(payload["authorization_digest"]),
        runtime_session_id=str(payload["runtime_session_id"]),
        controlled_restart_reason=str(payload["controlled_restart_reason"]),
        minimum_pre_restart_distinct_observations=int(
            payload["minimum_pre_restart_distinct_observations"]
        ),
        required_reconciliation_before_alpha=bool(payload["required_reconciliation_before_alpha"]),
        no_order_boundary_assertions=tuple(str(x) for x in assertions),
        contract_digest=digest,
    )
