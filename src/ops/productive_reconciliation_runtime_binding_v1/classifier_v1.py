"""Classify persisted vs observed portfolio/position truth fail-closed."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    PHASE1_MAX_OPEN_POSITIONS,
    QUANTITY_TOLERANCE_ABS,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    MutationPlanStepV1,
    MutationPlanV1,
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)

_TOL = Decimal(QUANTITY_TOLERANCE_ABS)


def _nonzero_positions(snapshot: PortfolioTruthSnapshotV1) -> dict[str, PositionTruthV1]:
    out: dict[str, PositionTruthV1] = {}
    for pos in snapshot.positions:
        if abs(pos.signed_quantity) > _TOL:
            out[pos.instrument_id] = pos
    return out


def _is_reduce_only(from_qty: Decimal, to_qty: Decimal) -> bool:
    """True iff transition never increases absolute exposure and never flips side."""
    if from_qty == to_qty:
        return True
    if from_qty == 0:
        # Opening from flat is never reduce-only.
        return abs(to_qty) <= _TOL
    if (from_qty > 0 and to_qty < 0) or (from_qty < 0 and to_qty > 0):
        return False
    return abs(to_qty) <= abs(from_qty) + _TOL


def build_reduce_only_mutation_plan(
    *,
    persisted: PortfolioTruthSnapshotV1,
    observed: PortfolioTruthSnapshotV1,
) -> MutationPlanV1:
    """Plan state-repair that only reduces or sets flat; never opens/flips."""
    local = _nonzero_positions(persisted)
    remote = _nonzero_positions(observed)
    instruments = sorted(set(local) | set(remote))
    steps: list[MutationPlanStepV1] = []
    reasons: list[str] = []

    if len(remote) > PHASE1_MAX_OPEN_POSITIONS:
        return MutationPlanV1(
            steps=(),
            admissible=False,
            reason_codes=("MULTI_POSITION_OBSERVED_EXCEEDS_PHASE1_MAX",),
        )

    for inst in instruments:
        from_qty = local[inst].signed_quantity if inst in local else Decimal("0")
        to_qty = remote[inst].signed_quantity if inst in remote else Decimal("0")
        if abs(from_qty - to_qty) <= _TOL:
            continue
        if not _is_reduce_only(from_qty, to_qty):
            reasons.append(f"NOT_REDUCE_ONLY:{inst}")
            continue
        opens = from_qty == 0 and abs(to_qty) > _TOL
        if opens:
            reasons.append(f"WOULD_OPEN:{inst}")
            continue
        steps.append(
            MutationPlanStepV1(
                instrument_id=inst,
                action="REDUCE_TO" if abs(to_qty) > _TOL else "STATE_REPAIR_SET",
                from_signed_quantity=from_qty,
                to_signed_quantity=to_qty,
                reduce_only=True,
                opens_new_position=False,
            )
        )

    admissible = not reasons and bool(steps)
    if not steps and not reasons:
        # No mutation needed — caller should have classified MATCH.
        return MutationPlanV1(steps=(), admissible=False, reason_codes=("NO_DRIFT",))
    if reasons:
        return MutationPlanV1(steps=tuple(steps), admissible=False, reason_codes=tuple(reasons))
    return MutationPlanV1(
        steps=tuple(steps),
        admissible=True,
        reason_codes=("REDUCE_ONLY_STATE_REPAIR",),
    )


def classify_productive_reconciliation_v1(
    *,
    persisted: PortfolioTruthSnapshotV1,
    observed: PortfolioTruthSnapshotV1,
    now_unix: Optional[float] = None,
) -> tuple[ProductiveReconciliationClass, MutationPlanV1, tuple[str, ...]]:
    """Return taxonomy class, optional recovery plan, and reason codes."""
    reasons: list[str] = []

    if persisted.writer_conflict or observed.writer_conflict:
        return (
            ProductiveReconciliationClass.CONFLICTING_WRITER,
            MutationPlanV1(admissible=False, reason_codes=("CONFLICTING_WRITER",)),
            ("CONFLICTING_WRITER",),
        )
    if persisted.duplicate or observed.duplicate:
        return (
            ProductiveReconciliationClass.DUPLICATE_STATE,
            MutationPlanV1(admissible=False, reason_codes=("DUPLICATE_STATE",)),
            ("DUPLICATE_STATE",),
        )
    if persisted.missing:
        return (
            ProductiveReconciliationClass.MISSING_TRUTH,
            MutationPlanV1(admissible=False, reason_codes=("MISSING_PERSISTED_TRUTH",)),
            ("MISSING_PERSISTED_TRUTH",),
        )
    if observed.missing:
        return (
            ProductiveReconciliationClass.MISSING_TRUTH,
            MutationPlanV1(admissible=False, reason_codes=("MISSING_OBSERVED_TRUTH",)),
            ("MISSING_OBSERVED_TRUTH",),
        )
    if persisted.stale or observed.stale:
        return (
            ProductiveReconciliationClass.STALE_SOURCE,
            MutationPlanV1(admissible=False, reason_codes=("STALE_SOURCE",)),
            ("STALE_SOURCE",),
        )

    # Optional explicit max-age check against wall/event times.
    if now_unix is not None:
        for snap, label in ((persisted, "PERSISTED"), (observed, "OBSERVED")):
            if snap.max_age_seconds is None:
                continue
            ref = snap.event_time_unix if snap.event_time_unix is not None else snap.wall_time_unix
            if ref is None:
                reasons.append(f"MISSING_TIMESTAMP_FOR_MAX_AGE:{label}")
                return (
                    ProductiveReconciliationClass.STALE_SOURCE,
                    MutationPlanV1(
                        admissible=False, reason_codes=("STALE_SOURCE_MISSING_TIMESTAMP",)
                    ),
                    tuple(reasons),
                )
            if (now_unix - float(ref)) > float(snap.max_age_seconds):
                return (
                    ProductiveReconciliationClass.STALE_SOURCE,
                    MutationPlanV1(admissible=False, reason_codes=(f"STALE_SOURCE:{label}",)),
                    (f"STALE_SOURCE:{label}",),
                )

    local = _nonzero_positions(persisted)
    remote = _nonzero_positions(observed)

    if len(remote) > PHASE1_MAX_OPEN_POSITIONS:
        return (
            ProductiveReconciliationClass.UNRECOVERABLE_DRIFT,
            MutationPlanV1(
                admissible=False, reason_codes=("MULTI_POSITION_OBSERVED_EXCEEDS_PHASE1_MAX",)
            ),
            ("MULTI_POSITION_OBSERVED_EXCEEDS_PHASE1_MAX",),
        )

    if not local and not remote:
        return (
            ProductiveReconciliationClass.MATCH,
            MutationPlanV1(admissible=False, reason_codes=("NO_POSITION_CLEAN",)),
            ("NO_POSITION_CLEAN",),
        )

    instruments = sorted(set(local) | set(remote))
    quantity_mismatches: list[str] = []
    side_mismatches: list[str] = []
    unknown_external: list[str] = []
    missing_local: list[str] = []

    for inst in instruments:
        lq = local[inst].signed_quantity if inst in local else Decimal("0")
        rq = remote[inst].signed_quantity if inst in remote else Decimal("0")
        if abs(lq - rq) <= _TOL:
            continue
        if inst not in local and abs(rq) > _TOL:
            unknown_external.append(inst)
        if inst not in remote and abs(lq) > _TOL:
            missing_local.append(inst)
        if (lq > 0 and rq < 0) or (lq < 0 and rq > 0):
            side_mismatches.append(inst)
        else:
            quantity_mismatches.append(inst)

    if side_mismatches:
        return (
            ProductiveReconciliationClass.UNRECOVERABLE_DRIFT,
            MutationPlanV1(
                admissible=False,
                reason_codes=tuple(f"SIDE_DRIFT:{i}" for i in side_mismatches),
            ),
            tuple(f"SIDE_DRIFT:{i}" for i in side_mismatches),
        )

    # Unknown external open while local flat: cannot open via recovery.
    if unknown_external and not local:
        return (
            ProductiveReconciliationClass.UNRECOVERABLE_DRIFT,
            MutationPlanV1(
                admissible=False,
                reason_codes=tuple(f"UNKNOWN_EXTERNAL_POSITION:{i}" for i in unknown_external),
            ),
            tuple(f"UNKNOWN_EXTERNAL_POSITION:{i}" for i in unknown_external),
        )

    if not quantity_mismatches and not missing_local and not unknown_external:
        return (
            ProductiveReconciliationClass.MATCH,
            MutationPlanV1(admissible=False, reason_codes=("POSITIONS_MATCH",)),
            ("POSITIONS_MATCH",),
        )

    plan = build_reduce_only_mutation_plan(persisted=persisted, observed=observed)
    if plan.admissible:
        reasons = list(plan.reason_codes)
        if quantity_mismatches:
            reasons.extend(f"QUANTITY_DRIFT:{i}" for i in quantity_mismatches)
        if missing_local:
            reasons.extend(f"MISSING_ON_OBSERVED:{i}" for i in missing_local)
        return (
            ProductiveReconciliationClass.RECOVERABLE_DRIFT,
            plan,
            tuple(reasons),
        )

    return (
        ProductiveReconciliationClass.UNRECOVERABLE_DRIFT,
        plan,
        tuple(plan.reason_codes)
        or tuple(f"QUANTITY_DRIFT:{i}" for i in quantity_mismatches)
        or ("UNRECOVERABLE_DRIFT",),
    )
