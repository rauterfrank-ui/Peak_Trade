"""DTOs for productive reconciliation runtime binding."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Optional

from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class PositionTruthV1:
    """Signed quantity position truth for a single instrument (Phase-1)."""

    instrument_id: str
    signed_quantity: Decimal
    side: str  # LONG|SHORT|FLAT
    mark_price: Optional[Decimal] = None
    source_id: str = "local"
    event_time_unix: Optional[float] = None
    wall_time_unix: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "signed_quantity": str(self.signed_quantity),
            "side": self.side,
            "mark_price": None if self.mark_price is None else str(self.mark_price),
            "source_id": self.source_id,
            "event_time_unix": self.event_time_unix,
            "wall_time_unix": self.wall_time_unix,
        }

    @staticmethod
    def from_signed(
        *,
        instrument_id: str,
        signed_quantity: Decimal | str | float | int,
        source_id: str = "local",
        mark_price: Decimal | str | float | int | None = None,
        event_time_unix: float | None = None,
        wall_time_unix: float | None = None,
    ) -> "PositionTruthV1":
        qty = Decimal(str(signed_quantity))
        if qty > 0:
            side = "LONG"
        elif qty < 0:
            side = "SHORT"
        else:
            side = "FLAT"
        mp = None if mark_price is None else Decimal(str(mark_price))
        return PositionTruthV1(
            instrument_id=str(instrument_id),
            signed_quantity=qty,
            side=side,
            mark_price=mp,
            source_id=source_id,
            event_time_unix=event_time_unix,
            wall_time_unix=wall_time_unix,
        )


@dataclass(frozen=True)
class PortfolioTruthSnapshotV1:
    positions: tuple[PositionTruthV1, ...] = ()
    cash: Optional[Decimal] = None
    source_id: str = "persisted"
    event_time_unix: Optional[float] = None
    wall_time_unix: Optional[float] = None
    missing: bool = False
    stale: bool = False
    duplicate: bool = False
    writer_conflict: bool = False
    max_age_seconds: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "positions": [p.to_dict() for p in self.positions],
            "cash": None if self.cash is None else str(self.cash),
            "source_id": self.source_id,
            "event_time_unix": self.event_time_unix,
            "wall_time_unix": self.wall_time_unix,
            "missing": self.missing,
            "stale": self.stale,
            "duplicate": self.duplicate,
            "writer_conflict": self.writer_conflict,
            "max_age_seconds": self.max_age_seconds,
        }

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class MutationPlanStepV1:
    instrument_id: str
    action: str  # REDUCE_TO|STATE_REPAIR_SET|NOOP
    from_signed_quantity: Decimal
    to_signed_quantity: Decimal
    reduce_only: bool = True
    opens_new_position: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "action": self.action,
            "from_signed_quantity": str(self.from_signed_quantity),
            "to_signed_quantity": str(self.to_signed_quantity),
            "reduce_only": self.reduce_only,
            "opens_new_position": self.opens_new_position,
        }


@dataclass(frozen=True)
class MutationPlanV1:
    steps: tuple[MutationPlanStepV1, ...] = ()
    admissible: bool = False
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [s.to_dict() for s in self.steps],
            "admissible": self.admissible,
            "reason_codes": list(self.reason_codes),
        }


@dataclass
class ProductiveReconciliationEvidenceV1:
    capability_id: str
    schema_version: str
    owner: str
    classification: str
    alpha_enabled: bool
    pre_state_digest: str
    observed_state_digest: str
    post_state_digest: str
    reconciliation_decision: str
    reason_codes: list[str] = field(default_factory=list)
    mutation_plan: dict[str, Any] = field(default_factory=dict)
    applied_mutation: dict[str, Any] = field(default_factory=dict)
    verification_result: dict[str, Any] = field(default_factory=dict)
    repository_sha: str = ""
    config_digest: str = ""
    event_time_unix: Optional[float] = None
    wall_time_unix: Optional[float] = None
    single_writer_identity: str = ""
    recovery_attempted: bool = False
    recovery_verified: bool = False
    hard_stop: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.to_dict()))


@dataclass(frozen=True)
class ProductiveReconciliationGateResultV1:
    ok: bool
    alpha_enabled: bool
    classification: ProductiveReconciliationClass
    master_v2_reconciliation_state: str  # reconciled|reconciliation_required|unknown
    hard_stop: bool
    evidence: ProductiveReconciliationEvidenceV1
    repaired_positions: tuple[PositionTruthV1, ...] = ()
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_enabled": self.alpha_enabled,
            "classification": self.classification.value,
            "master_v2_reconciliation_state": self.master_v2_reconciliation_state,
            "hard_stop": self.hard_stop,
            "evidence": self.evidence.to_dict(),
            "repaired_positions": [p.to_dict() for p in self.repaired_positions],
            "blockers": list(self.blockers),
        }
