"""Productive reconciliation startup gate — must run before first decision cycle."""

from __future__ import annotations

import time
from decimal import Decimal
from pathlib import Path
from typing import Optional

from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CAPABILITY_ID,
    OWNER,
    SCHEMA_VERSION,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    MutationPlanV1,
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationEvidenceV1,
    ProductiveReconciliationGateResultV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    config_digest_for_binding,
    detect_duplicate_portfolio_state,
    load_persisted_portfolio_state,
    persist_reconciliation_bundle_atomic,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ConflictingWriterError,
    ProductivePortfolioSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    HARD_STOP_CLASSES,
    ProductiveReconciliationClass,
)

# Map onto Master V2 ReconciliationState string values without mutating trading logic.
_MV2_RECONCILED = "reconciled"
_MV2_RECONCILIATION_REQUIRED = "reconciliation_required"
_MV2_UNKNOWN = "unknown"


def _apply_mutation_plan(
    *,
    persisted: PortfolioTruthSnapshotV1,
    plan: MutationPlanV1,
) -> tuple[PositionTruthV1, ...]:
    by_id = {p.instrument_id: p for p in persisted.positions}
    for step in plan.steps:
        if step.opens_new_position:
            raise RuntimeError("INVARIANT_RECOVERY_MUST_NOT_OPEN")
        if not step.reduce_only:
            raise RuntimeError("INVARIANT_RECOVERY_MUST_BE_REDUCE_ONLY")
        mark = by_id[step.instrument_id].mark_price if step.instrument_id in by_id else None
        by_id[step.instrument_id] = PositionTruthV1.from_signed(
            instrument_id=step.instrument_id,
            signed_quantity=step.to_signed_quantity,
            source_id="repaired",
            mark_price=mark,
            event_time_unix=persisted.event_time_unix,
            wall_time_unix=persisted.wall_time_unix,
        )
    # Drop flats from repaired set for clarity; empty means flat book.
    return tuple(p for p in by_id.values() if abs(p.signed_quantity) > Decimal("0"))


def _map_master_v2_state(
    classification: ProductiveReconciliationClass,
    *,
    alpha_enabled: bool,
) -> str:
    if alpha_enabled and classification in {
        ProductiveReconciliationClass.MATCH,
        ProductiveReconciliationClass.RECOVERABLE_DRIFT,
    }:
        return _MV2_RECONCILED
    if classification in HARD_STOP_CLASSES:
        return _MV2_RECONCILIATION_REQUIRED
    return _MV2_UNKNOWN


def run_productive_reconciliation_startup_gate_v1(
    *,
    state_root: Path,
    observed: PortfolioTruthSnapshotV1,
    session_id: str,
    repository_sha: str,
    now_unix: Optional[float] = None,
    writer_identity: str = SINGLE_WRITER_IDENTITY,
    require_persisted_present: bool = False,
    simulate_crash_after_persist_before_verify: bool = False,
    inject_conflicting_writer: bool = False,
) -> ProductiveReconciliationGateResultV1:
    """Session-start reconciliation gate. Alpha only on MATCH or verified recovery."""
    wall = float(now_unix if now_unix is not None else time.time())
    root = Path(state_root)
    root.mkdir(parents=True, exist_ok=True)

    cfg_digest = config_digest_for_binding(repository_sha=repository_sha)

    if inject_conflicting_writer:
        poison = ProductivePortfolioSingleWriterV1(
            state_root=root,
            writer_identity="legacy_parallel_writer",
            session_id="poison",
        )
        poison.acquire(now_unix=wall)

    if detect_duplicate_portfolio_state(root):
        observed = PortfolioTruthSnapshotV1(
            positions=observed.positions,
            cash=observed.cash,
            source_id=observed.source_id,
            event_time_unix=observed.event_time_unix,
            wall_time_unix=observed.wall_time_unix,
            missing=observed.missing,
            stale=observed.stale,
            duplicate=True,
            writer_conflict=observed.writer_conflict,
            max_age_seconds=observed.max_age_seconds,
        )

    writer = ProductivePortfolioSingleWriterV1(
        state_root=root,
        writer_identity=writer_identity,
        session_id=session_id,
    )
    try:
        writer.acquire(now_unix=wall)
    except ConflictingWriterError as exc:
        evidence = ProductiveReconciliationEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            owner=OWNER,
            classification=ProductiveReconciliationClass.CONFLICTING_WRITER.value,
            alpha_enabled=False,
            pre_state_digest="",
            observed_state_digest=observed.digest(),
            post_state_digest="",
            reconciliation_decision="HARD_STOP",
            reason_codes=["CONFLICTING_WRITER", str(exc)],
            mutation_plan={},
            applied_mutation={},
            verification_result={"ok": False, "error": "CONFLICTING_WRITER"},
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            event_time_unix=observed.event_time_unix,
            wall_time_unix=wall,
            single_writer_identity=writer_identity,
            hard_stop=True,
            notes=["ALPHA_BLOCKED", "PARALLEL_WRITER_AUTHORITY_REJECTED"],
        )
        return ProductiveReconciliationGateResultV1(
            ok=False,
            alpha_enabled=False,
            classification=ProductiveReconciliationClass.CONFLICTING_WRITER,
            master_v2_reconciliation_state=_MV2_RECONCILIATION_REQUIRED,
            hard_stop=True,
            evidence=evidence,
            blockers=("CONFLICTING_WRITER",),
        )

    try:
        persisted = load_persisted_portfolio_state(root, require_present=require_persisted_present)
        classification, plan, reasons = classify_productive_reconciliation_v1(
            persisted=persisted,
            observed=observed,
            now_unix=wall,
        )
        pre_digest = persisted.digest()
        observed_digest = observed.digest()
        recovery_attempted = False
        recovery_verified = False
        applied: dict = {}
        repaired_positions: tuple[PositionTruthV1, ...] = persisted.positions
        post_snapshot = persisted
        verification: dict = {"ok": False, "skipped": True}
        alpha_enabled = False
        hard_stop = classification in HARD_STOP_CLASSES
        decision = "HARD_STOP"

        if classification == ProductiveReconciliationClass.MATCH:
            post_snapshot = PortfolioTruthSnapshotV1(
                positions=tuple(observed.positions if observed.positions else persisted.positions),
                cash=observed.cash if observed.cash is not None else persisted.cash,
                source_id="reconciled_match",
                event_time_unix=observed.event_time_unix or persisted.event_time_unix,
                wall_time_unix=wall,
            )
            repaired_positions = post_snapshot.positions
            decision = "CONTINUE"
            alpha_enabled = True
            hard_stop = False
        elif classification == ProductiveReconciliationClass.RECOVERABLE_DRIFT:
            if not plan.admissible:
                hard_stop = True
                decision = "HARD_STOP"
                classification = ProductiveReconciliationClass.UNRECOVERABLE_DRIFT
            else:
                recovery_attempted = True
                repaired_positions = _apply_mutation_plan(persisted=persisted, plan=plan)
                applied = {"steps": [s.to_dict() for s in plan.steps]}
                post_snapshot = PortfolioTruthSnapshotV1(
                    positions=repaired_positions,
                    cash=observed.cash if observed.cash is not None else persisted.cash,
                    source_id="reconciled_repaired",
                    event_time_unix=observed.event_time_unix or persisted.event_time_unix,
                    wall_time_unix=wall,
                )
                # Recheck against observed after repair.
                reclass, _, re_reasons = classify_productive_reconciliation_v1(
                    persisted=post_snapshot,
                    observed=observed,
                    now_unix=wall,
                )
                if reclass == ProductiveReconciliationClass.MATCH:
                    recovery_verified = True
                    alpha_enabled = True
                    hard_stop = False
                    decision = "RECOVERED_CONTINUE"
                    reasons = tuple(list(reasons) + list(re_reasons) + ["RECOVERY_VERIFIED"])
                else:
                    hard_stop = True
                    decision = "HARD_STOP_RECOVERY_FAILED_RECHECK"
                    alpha_enabled = False
                    reasons = tuple(list(reasons) + list(re_reasons) + ["RECOVERY_RECHECK_FAILED"])
                    classification = ProductiveReconciliationClass.UNRECOVERABLE_DRIFT
        else:
            decision = "HARD_STOP"
            alpha_enabled = False
            hard_stop = True

        evidence = ProductiveReconciliationEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            owner=AUTHORITY_OWNER,
            classification=classification.value,
            alpha_enabled=alpha_enabled,
            pre_state_digest=pre_digest,
            observed_state_digest=observed_digest,
            post_state_digest=post_snapshot.digest(),
            reconciliation_decision=decision,
            reason_codes=list(reasons),
            mutation_plan=plan.to_dict(),
            applied_mutation=applied,
            verification_result={},
            repository_sha=repository_sha,
            config_digest=cfg_digest,
            event_time_unix=observed.event_time_unix or persisted.event_time_unix,
            wall_time_unix=wall,
            single_writer_identity=writer_identity,
            recovery_attempted=recovery_attempted,
            recovery_verified=recovery_verified,
            hard_stop=hard_stop,
            notes=[
                "RECONCILIATION_BEFORE_ALPHA",
                "NO_NEW_POSITIONS_IN_RECOVERY",
                "SINGLE_WRITER_ENFORCED",
            ],
        )

        # Persist even on hard-stop for auditability (except conflicting writer path above).
        persist_result = persist_reconciliation_bundle_atomic(
            state_root=root,
            writer=writer,
            portfolio=post_snapshot,
            evidence=evidence,
            simulate_crash_after_persist_before_verify=simulate_crash_after_persist_before_verify,
        )
        evidence.verification_result = dict(persist_result)
        verification = dict(persist_result)

        if simulate_crash_after_persist_before_verify:
            alpha_enabled = False
            hard_stop = True
            evidence.alpha_enabled = False
            evidence.hard_stop = True
            evidence.reconciliation_decision = "HARD_STOP_CRASH_BEFORE_VERIFY"
            evidence.reason_codes.append("CRASH_AFTER_PERSIST_BEFORE_VERIFY")
            return ProductiveReconciliationGateResultV1(
                ok=False,
                alpha_enabled=False,
                classification=classification,
                master_v2_reconciliation_state=_MV2_RECONCILIATION_REQUIRED,
                hard_stop=True,
                evidence=evidence,
                repaired_positions=repaired_positions,
                blockers=("CRASH_AFTER_PERSIST_BEFORE_VERIFY",),
            )

        if not persist_result.get("ok"):
            alpha_enabled = False
            hard_stop = True
            evidence.alpha_enabled = False
            evidence.hard_stop = True
            evidence.reason_codes.append("PERSIST_VERIFY_FAILED")

        # Restart semantics: alpha requires successful verify-after-write.
        if alpha_enabled and not verification.get("ok"):
            alpha_enabled = False
            hard_stop = True

        master_state = _map_master_v2_state(classification, alpha_enabled=alpha_enabled)
        evidence.alpha_enabled = alpha_enabled
        evidence.hard_stop = hard_stop
        evidence.post_state_digest = post_snapshot.digest()
        evidence.verification_result = verification

        return ProductiveReconciliationGateResultV1(
            ok=alpha_enabled and not hard_stop,
            alpha_enabled=alpha_enabled,
            classification=classification,
            master_v2_reconciliation_state=master_state,
            hard_stop=hard_stop,
            evidence=evidence,
            repaired_positions=repaired_positions,
            blockers=() if alpha_enabled else tuple(evidence.reason_codes),
        )
    finally:
        writer.release()
