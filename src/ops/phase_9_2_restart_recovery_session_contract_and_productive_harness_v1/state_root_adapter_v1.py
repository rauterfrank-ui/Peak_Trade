"""Durable Phase-9.2 state-root adapter over Cap 6.1/6.2/6.4/7.2 owners."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    PREDECESSOR_CAP61,
    PREDECESSOR_CAP62,
    PREDECESSOR_CAP64,
    PREDECESSOR_CAP72,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartCheckpointV1,
    StateRootBindingV1,
)


def build_state_root_classification_matrix_v1() -> list[dict[str, Any]]:
    """Classify Phase-9.2 restart checkpoint fields without new MV2/DP domains."""
    return [
        {
            "field": "confirmation_state",
            "owner_capability": PREDECESSOR_CAP61,
            "classification": "PERSIST_DIRECTLY",
            "reason": "Cap 6.1 confirmation carrier continuity",
        },
        {
            "field": "confirmation_session_id",
            "owner_capability": PREDECESSOR_CAP61,
            "classification": "PERSIST_DIRECTLY",
            "reason": "stable confirmation identity across process restart",
        },
        {
            "field": "observation_identity_epoch",
            "owner_capability": PREDECESSOR_CAP61,
            "classification": "PERSIST_DIRECTLY",
            "reason": "C1 epoch continuity; no rollback",
        },
        {
            "field": "dynamic_scope_state",
            "owner_capability": PREDECESSOR_CAP62,
            "classification": "PERSIST_DIRECTLY",
            "reason": "Cap 6.2 RuntimeScopeState continuity",
        },
        {
            "field": "required_decision_path_carrier_state",
            "owner_capability": PREDECESSOR_CAP62,
            "classification": "PERSIST_DIRECTLY",
            "reason": "only required carrier via Cap 6.2; no new MV2 domain",
        },
        {
            "field": "portfolio_state",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "PERSIST_DIRECTLY",
            "reason": "Cap 3.1/7.2 portfolio continuity",
        },
        {
            "field": "accounting_state",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "PERSIST_DIRECTLY",
            "reason": "futures accounting continuity",
        },
        {
            "field": "reconciliation_state_reference",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "REFERENCE_ONLY",
            "reason": "reconciliation-before-alpha gate reference",
        },
        {
            "field": "selected_instrument_reference",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "REFERENCE_ONLY",
            "reason": "Cap 2.4 selection remains sole authority",
        },
        {
            "field": "typed_volatility_reference",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "REFERENCE_ONLY",
            "reason": "typed presence reference only; no policy mutation",
        },
        {
            "field": "evidence_cursor",
            "owner_capability": PREDECESSOR_CAP64,
            "classification": "PERSIST_DIRECTLY",
            "reason": "Cap 6.4 pending evidence cursor continuity",
        },
        {
            "field": "atomic_decision_path_commit_position",
            "owner_capability": PREDECESSOR_CAP64,
            "classification": "PERSIST_DIRECTLY",
            "reason": "Cap 6.4 commit marker continuity",
        },
        {
            "field": "feature_vectors",
            "owner_capability": PREDECESSOR_CAP64,
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "rebuilt from persisted observation path",
        },
        {
            "field": "unrealized_pnl",
            "owner_capability": PREDECESSOR_CAP72,
            "classification": "REBUILD_DETERMINISTICALLY",
            "reason": "derived from position + mark",
        },
        {
            "field": "transport_metadata",
            "owner_capability": "market_data_transport",
            "classification": "EPHEMERAL",
            "reason": "process-local; not restart authority",
        },
        {
            "field": "wallclock_runtime_session_id",
            "owner_capability": "wallclock_session_host",
            "classification": "EPHEMERAL",
            "reason": "each process uses a new runtime_session_id",
        },
        {
            "field": "master_v2_full_decision_blob",
            "owner_capability": "none",
            "classification": "FORBIDDEN_TO_PERSIST",
            "reason": "MASTER_V2_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false",
        },
        {
            "field": "double_play_full_decision_blob",
            "owner_capability": "none",
            "classification": "FORBIDDEN_TO_PERSIST",
            "reason": "DOUBLE_PLAY_NEW_PERSISTENCE_DOMAIN_MODEL_ALLOWED=false",
        },
    ]


def materialize_checkpoint_bindings_v1(checkpoint: RestartCheckpointV1) -> list[StateRootBindingV1]:
    matrix = {row["field"]: row for row in build_state_root_classification_matrix_v1()}
    values = {
        "confirmation_state": {
            "confirmation_session_id": checkpoint.confirmation_session_id,
            "observation_epoch": checkpoint.observation_epoch,
            "observation_identity": checkpoint.observation_identity,
        },
        "confirmation_session_id": checkpoint.confirmation_session_id,
        "observation_identity_epoch": {
            "observation_identity": checkpoint.observation_identity,
            "observation_epoch": checkpoint.observation_epoch,
        },
        "dynamic_scope_state": {"scope_digest": checkpoint.scope_digest},
        "required_decision_path_carrier_state": {
            "runtime_state_digest": checkpoint.runtime_state_digest
        },
        "portfolio_state": {"portfolio_digest": checkpoint.portfolio_digest},
        "accounting_state": {"accounting_digest": checkpoint.accounting_digest},
        "reconciliation_state_reference": checkpoint.reconciliation_reference,
        "selected_instrument_reference": checkpoint.selected_instrument_reference,
        "typed_volatility_reference": checkpoint.typed_volatility_reference,
        "evidence_cursor": checkpoint.evidence_cursor,
        "atomic_decision_path_commit_position": checkpoint.atomic_commit_position,
    }
    bindings: list[StateRootBindingV1] = []
    for field_name, value in values.items():
        row = matrix[field_name]
        digest = sha256_canonical_v1({"field": field_name, "value": value})
        bindings.append(
            StateRootBindingV1(
                field_name=field_name,
                owner_capability=str(row["owner_capability"]),
                classification=str(row["classification"]),
                reason=str(row["reason"]),
                digest=digest,
                value=value,
            )
        )
    return bindings


def aggregate_state_root_digest_v1(bindings: list[StateRootBindingV1]) -> str:
    return sha256_canonical_v1([b.to_dict() for b in bindings])


def build_fixture_checkpoint_v1(
    *,
    confirmation_session_id: str,
    observation_epoch: int,
    open_position_present: bool,
    distinct_observation_count: int,
    evidence_cursor: str,
    portfolio_seed: str,
    scope_seed: str,
    accounting_seed: str,
    runtime_seed: str,
    instrument_id: str,
    restart_campaign_id: str,
    durable_state_lineage_id: str,
    applied_fill_ids: list[str] | None = None,
    applied_confirmation_ids: list[str] | None = None,
) -> RestartCheckpointV1:
    observation_identity = sha256_canonical_v1(
        {
            "epoch": observation_epoch,
            "instrument": instrument_id,
            "lineage": durable_state_lineage_id,
        }
    )
    portfolio_digest = sha256_canonical_v1(
        {
            "seed": portfolio_seed,
            "open": open_position_present,
            "qty": 1.0 if open_position_present else 0.0,
        }
    )
    scope_digest = sha256_canonical_v1({"seed": scope_seed, "epoch": observation_epoch})
    accounting_digest = sha256_canonical_v1(
        {"seed": accounting_seed, "fills": list(applied_fill_ids or [])}
    )
    runtime_state_digest = sha256_canonical_v1(
        {
            "seed": runtime_seed,
            "portfolio": portfolio_digest,
            "scope": scope_digest,
            "accounting": accounting_digest,
            "epoch": observation_epoch,
        }
    )
    checkpoint = RestartCheckpointV1(
        restart_campaign_id=restart_campaign_id,
        durable_state_lineage_id=durable_state_lineage_id,
        confirmation_session_id=confirmation_session_id,
        observation_epoch=observation_epoch,
        observation_identity=observation_identity,
        runtime_state_digest=runtime_state_digest,
        portfolio_digest=portfolio_digest,
        scope_digest=scope_digest,
        accounting_digest=accounting_digest,
        evidence_cursor=evidence_cursor,
        atomic_commit_position=sha256_canonical_v1(
            {"commit": "cap64", "cursor": evidence_cursor, "epoch": observation_epoch}
        ),
        selected_instrument_reference=instrument_id,
        typed_volatility_reference=sha256_canonical_v1({"vol_ref": instrument_id}),
        reconciliation_reference=sha256_canonical_v1(
            {"recon": runtime_state_digest, "portfolio": portfolio_digest}
        ),
        open_position_present=open_position_present,
        open_position_quantity=1.0 if open_position_present else 0.0,
        distinct_observation_count=distinct_observation_count,
        applied_fill_ids=list(applied_fill_ids or []),
        applied_confirmation_ids=list(applied_confirmation_ids or []),
    )
    bindings = materialize_checkpoint_bindings_v1(checkpoint)
    checkpoint.state_roots = [b.to_dict() for b in bindings]
    return checkpoint
