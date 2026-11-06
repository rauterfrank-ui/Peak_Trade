"""N1 startup: inspect selection, observe the bound account, then admit binding."""

from dataclasses import dataclass
from pathlib import Path
import time

from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
    CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1,
    acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1,
    inspect_selection_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
    HostAccountObservationV1,
    collect_host_account_observation_v1,
)


@dataclass(frozen=True)
class AccountBoundN1StartupV1:
    handoff: CurrentProductive29PCap24BoundInstrumentProvenanceHandoffV1
    observation: HostAccountObservationV1


def acquire_account_bound_n1_startup_v1(
    *,
    productivity_root: Path,
    repository_sha: str,
    binding_epoch: str,
    expected_account_identity: str,
    session_id: str,
    private_rest_fetch,
    expected_bound=None,
    clock=time.time,
) -> AccountBoundN1StartupV1:
    if not isinstance(expected_account_identity, str) or not expected_account_identity.strip():
        raise ValueError("N1_START_ACCOUNT_IDENTITY_REQUIRED")
    inspected = inspect_selection_v1(
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
    )
    selection = inspected.selection
    identity = {
        "instrument_id": selection.instrument_id,
        "venue_native_id": selection.venue_native_id,
        "selection_id": selection.selection_id,
        "selection_integrity_digest": selection.integrity_digest,
        "ranking_snapshot_id": inspected.ranking.ranking_snapshot_id,
        "ranking_integrity_digest": inspected.ranking.integrity_digest,
        "universe_snapshot_id": inspected.universe.snapshot_id,
    }
    if expected_bound is not None and any(
        str(getattr(expected_bound, name, None)) != str(value) for name, value in identity.items()
    ):
        raise ValueError("N1_START_SELECTION_BINDING_MISMATCH")
    observation = collect_host_account_observation_v1(
        private_rest_fetch=private_rest_fetch,
        instrument_ids_by_native_id={selection.venue_native_id: selection.instrument_id},
        session_id=session_id,
        clock=clock,
        expected_account=expected_account_identity,
    )
    if observation.pending_orders:
        raise ValueError("N1_START_PENDING_ORDERS_UNRESOLVED")
    handoff = acquire_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1(
        productivity_root=productivity_root,
        repository_sha=repository_sha,
        binding_epoch=binding_epoch,
        session_id=session_id,
        observed_portfolio=observation.observed,
        expected_selection_integrity_digest=selection.integrity_digest,
        observation_now_unix=clock(),
    )
    if (
        handoff.selection_id != selection.selection_id
        or handoff.selection_integrity_digest != selection.integrity_digest
    ):
        raise ValueError("N1_START_SELECTION_CHANGED_DURING_OBSERVATION")
    return AccountBoundN1StartupV1(handoff, observation)
