"""Bridge public-MD observation continuity into the PR #5665 checkpoint contract."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    CONFIRMATION_SESSION_ID,
    DURABLE_STATE_LINEAGE_ID,
    MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS,
    RESTART_CAMPAIGN_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.models_v1 import (
    RestartCheckpointV1,
)
from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.state_root_adapter_v1 import (
    build_fixture_checkpoint_v1,
)


class CheckpointBridgeError(RuntimeError):
    """Fail-closed checkpoint bridge error."""


def build_checkpoint_from_public_md_observations_v1(
    *,
    distinct_observation_count: int,
    observation_identities: list[str],
    open_position_present: bool = False,
    open_position_quantity: float = 0.0,
    applied_fill_ids: list[str] | None = None,
    applied_confirmation_ids: list[str] | None = None,
    instrument_id: str = CANONICAL_INSTRUMENT_ID,
    confirmation_session_id: str = CONFIRMATION_SESSION_ID,
    wallclock_evidence_cursor: str | None = None,
) -> RestartCheckpointV1:
    """Build a restart checkpoint from observed MD continuity (no forced fills/intents)."""
    if distinct_observation_count < MINIMUM_PRE_RESTART_DISTINCT_OBSERVATIONS:
        raise CheckpointBridgeError("insufficient_distinct_observations")
    if len(observation_identities) < distinct_observation_count:
        raise CheckpointBridgeError("observation_identity_count_mismatch")
    # Dedup identities prove DISTINCT acceptance without injecting confirmation advances.
    unique = []
    seen: set[str] = set()
    for oid in observation_identities:
        if oid in seen:
            continue
        seen.add(oid)
        unique.append(oid)
    if len(unique) < distinct_observation_count:
        raise CheckpointBridgeError("duplicate_observations_collapsed_below_minimum")

    cursor = wallclock_evidence_cursor or sha256_canonical_v1(
        {"cursor": "phase92_productive_md", "n": distinct_observation_count, "ids": unique[:8]}
    )
    conf_ids = list(applied_confirmation_ids or [])
    fill_ids = list(applied_fill_ids or [])
    # Natural confirmation ids may be empty; recovery still binds observation epoch.
    checkpoint = build_fixture_checkpoint_v1(
        confirmation_session_id=confirmation_session_id,
        observation_epoch=distinct_observation_count,
        open_position_present=open_position_present,
        distinct_observation_count=distinct_observation_count,
        evidence_cursor=cursor,
        portfolio_seed="productive_md_portfolio_v1",
        scope_seed="productive_md_scope_v1",
        accounting_seed="productive_md_accounting_v1",
        runtime_seed="productive_md_runtime_v1",
        instrument_id=instrument_id,
        restart_campaign_id=RESTART_CAMPAIGN_ID,
        durable_state_lineage_id=DURABLE_STATE_LINEAGE_ID,
        applied_fill_ids=fill_ids,
        applied_confirmation_ids=conf_ids,
    )
    if open_position_present and open_position_quantity <= 0:
        raise CheckpointBridgeError("open_position_quantity_invalid")
    if not open_position_present and open_position_quantity != 0:
        raise CheckpointBridgeError("flat_position_quantity_nonzero")
    return checkpoint


def checkpoint_digest_v1(checkpoint: RestartCheckpointV1 | Mapping[str, Any]) -> str:
    payload = (
        checkpoint.to_dict() if isinstance(checkpoint, RestartCheckpointV1) else dict(checkpoint)
    )
    return sha256_canonical_v1(payload)
