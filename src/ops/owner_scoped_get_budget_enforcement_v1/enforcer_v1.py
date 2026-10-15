"""Transport-facing Owner-scoped GET budget enforcer."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from pathlib import Path

from src.ops.owner_scoped_get_budget_enforcement_v1.constants_v1 import (
    RESERVATION_OUTCOME_COMPLETED,
    RESERVATION_OUTCOME_RELEASED_NO_SEND,
    RESERVATION_OUTCOME_UNCERTAIN_WIRE,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.durable_ledger_v1 import (
    OwnerScopedGetBudgetReservationV1,
    atomic_pre_send_reserve_v1,
    finalize_reservation_v1,
    load_owner_scoped_get_budget_ledger_v1,
    mint_owner_scoped_get_budget_grant_v1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError
from src.ops.owner_scoped_get_budget_enforcement_v1.grant_identity_v1 import (
    OwnerScopedGetBudgetGrantBindingV1,
    compute_owner_grant_identity_digest_v1,
    owner_grant_id_from_identity_v1,
)


@dataclass(frozen=True)
class OwnerScopedGetBudgetGrantContextV1:
    store_root: Path
    grant_id: str
    binding: OwnerScopedGetBudgetGrantBindingV1

    @classmethod
    def mint_v1(
        cls,
        *,
        store_root: Path | str,
        binding: OwnerScopedGetBudgetGrantBindingV1,
    ) -> "OwnerScopedGetBudgetGrantContextV1":
        minted = mint_owner_scoped_get_budget_grant_v1(store_root=store_root, binding=binding)
        gid = str(minted.get("grant_id") or "")
        return cls(store_root=Path(store_root), grant_id=gid, binding=binding)

    def identity_digest_v1(self) -> str:
        return compute_owner_grant_identity_digest_v1(self.binding)


class OwnerScopedGetBudgetEnforcerV1:
    """Atomic pre-send reservation with durable cumulative accounting."""

    def __init__(self, *, grant_context: OwnerScopedGetBudgetGrantContextV1) -> None:
        self._ctx = grant_context
        expected = owner_grant_id_from_identity_v1(grant_context.identity_digest_v1())
        if expected != owner_grant_id_from_identity_v1(grant_context.grant_id):
            raise OwnerScopedGetBudgetError("GRANT_CONTEXT_ID_MISMATCH")

    @property
    def grant_id(self) -> str:
        return self._ctx.grant_id

    def ledger_snapshot_v1(self) -> dict[str, object]:
        loaded = load_owner_scoped_get_budget_ledger_v1(
            store_root=self._ctx.store_root,
            grant_id=self._ctx.grant_id,
        )
        record = loaded.get("record") or {}
        return {
            "present": loaded.get("present"),
            "committed_request_count": record.get("committed_request_count"),
            "uncertain_request_count": record.get("uncertain_request_count"),
            "in_flight_request_count": record.get("in_flight_request_count"),
            "state": record.get("state"),
        }

    def begin_get_v1(self, *, endpoint_path: str) -> OwnerScopedGetBudgetReservationV1:
        reservation_id = secrets.token_hex(16)
        return atomic_pre_send_reserve_v1(
            store_root=self._ctx.store_root,
            grant_id=self._ctx.grant_id,
            reservation_id=reservation_id,
            endpoint_path=endpoint_path,
        )

    def complete_get_v1(
        self,
        reservation: OwnerScopedGetBudgetReservationV1,
        *,
        outcome: str,
    ) -> None:
        finalize_reservation_v1(
            store_root=self._ctx.store_root,
            grant_id=self._ctx.grant_id,
            reservation_id=reservation.reservation_id,
            outcome=outcome,
        )

    def release_unsent_v1(self, reservation: OwnerScopedGetBudgetReservationV1) -> None:
        self.complete_get_v1(reservation, outcome=RESERVATION_OUTCOME_RELEASED_NO_SEND)

    def mark_completed_v1(self, reservation: OwnerScopedGetBudgetReservationV1) -> None:
        self.complete_get_v1(reservation, outcome=RESERVATION_OUTCOME_COMPLETED)

    def mark_uncertain_wire_v1(self, reservation: OwnerScopedGetBudgetReservationV1) -> None:
        self.complete_get_v1(reservation, outcome=RESERVATION_OUTCOME_UNCERTAIN_WIRE)
