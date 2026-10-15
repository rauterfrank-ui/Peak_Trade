"""S03 — contract-based semantic integrity checks."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Sequence

from src.ops.ghosv_bounded_context_v1.constants_v1 import (
    TRAFFIC_GREEN,
    TRAFFIC_RED,
    TRAFFIC_YELLOW,
)
from src.ops.ghosv_bounded_context_v1.types_v1 import (
    GhosvCompleteness,
    GhosvCorrelationGroupV1,
    GhosvEvidenceKind,
    GhosvEvidenceRecordV1,
    GhosvIntegrityFindingV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    HARD_STOP_CLASSES,
    ProductiveReconciliationClass,
)


def _by_kind(records: Sequence[GhosvEvidenceRecordV1], kind: str) -> list[GhosvEvidenceRecordV1]:
    return [r for r in records if r.kind == kind]


def _dec(
    traffic: str, check_id: str, reason: str, refs: tuple[str, ...]
) -> GhosvIntegrityFindingV1:
    outcome = (
        "PASS" if traffic == TRAFFIC_GREEN else ("FAIL" if traffic == TRAFFIC_RED else "UNKNOWN")
    )
    return GhosvIntegrityFindingV1(
        check_id=check_id,
        outcome=outcome,
        traffic=traffic,
        reason=reason,
        evidence_refs=refs,
    )


def _recon_traffic(recon: GhosvEvidenceRecordV1) -> tuple[str, str]:
    cls = str(
        recon.payload.get("classification")
        or recon.payload.get("reconciliation_classification")
        or ""
    ).upper()
    if recon.payload.get("hard_stop") is True:
        return TRAFFIC_RED, "RECON_HARD_STOP_FLAG"
    if cls in {c.value for c in HARD_STOP_CLASSES} or cls in {"HARD_STOP", "UNRECOVERABLE_DRIFT"}:
        return TRAFFIC_RED, f"RECON_{cls or 'HARD_STOP'}"
    if cls == ProductiveReconciliationClass.MATCH.value:
        return TRAFFIC_GREEN, "RECON_MATCH"
    if cls == ProductiveReconciliationClass.RECOVERABLE_DRIFT.value:
        return TRAFFIC_YELLOW, "RECON_RECOVERABLE_DRIFT"
    if cls:
        return TRAFFIC_YELLOW, f"RECON_NON_ALPHA_SAFE_{cls}"
    return TRAFFIC_YELLOW, "RECON_UNKNOWN"


def evaluate_semantic_integrity_v1(
    *,
    records: Sequence[GhosvEvidenceRecordV1],
    groups: Sequence[GhosvCorrelationGroupV1],
    ingest_rejected: Sequence[str] = (),
) -> tuple[GhosvIntegrityFindingV1, ...]:
    findings: list[GhosvIntegrityFindingV1] = []
    refs_all = tuple(r.event_id for r in records)

    if ingest_rejected:
        findings.append(
            _dec(
                TRAFFIC_YELLOW,
                "EVIDENCE_INGEST_INTEGRITY",
                "INGEST_REJECTED",
                refs_all,
            )
        )

    incomplete = [r for r in records if r.completeness != GhosvCompleteness.COMPLETE.value]
    if incomplete:
        findings.append(
            _dec(
                TRAFFIC_YELLOW,
                "EVIDENCE_COMPLETENESS",
                "INCOMPLETE_OR_UNKNOWN_EVIDENCE",
                tuple(r.event_id for r in incomplete),
            )
        )

    envelopes = _by_kind(records, GhosvEvidenceKind.ORDER_ENVELOPE.value)
    acks = _by_kind(records, GhosvEvidenceKind.ORDER_ACK.value)
    fills = (
        _by_kind(records, GhosvEvidenceKind.FILL.value)
        + _by_kind(records, GhosvEvidenceKind.PARTIAL_FILL.value)
        + _by_kind(records, GhosvEvidenceKind.FULL_FILL.value)
    )
    positions = _by_kind(records, GhosvEvidenceKind.POSITION_SNAPSHOT.value)
    recons = _by_kind(records, GhosvEvidenceKind.RECONCILIATION_GATE.value)

    # ORDER_IDENTITY_INTEGRITY
    for g in groups:
        refs = g.record_event_ids
        if g.status == "CONFLICT":
            findings.append(
                _dec(TRAFFIC_RED, "ORDER_IDENTITY_INTEGRITY", "IDENTITY_CONFLICT", refs)
            )
        elif g.status == "UNKNOWN":
            findings.append(
                _dec(TRAFFIC_YELLOW, "ORDER_IDENTITY_INTEGRITY", "IDENTITY_UNKNOWN", refs)
            )
        else:
            findings.append(_dec(TRAFFIC_GREEN, "ORDER_IDENTITY_INTEGRITY", "OK", refs))

    # ORDER_ACK_SEMANTICS — ACK != FILL
    if acks and fills:
        for ack in acks:
            if ack.payload.get("treated_as_fill") is True:
                findings.append(
                    _dec(
                        TRAFFIC_RED,
                        "ORDER_ACK_SEMANTICS",
                        "ACK_TREATED_AS_FILL",
                        (ack.event_id,),
                    )
                )
            else:
                findings.append(
                    _dec(
                        TRAFFIC_GREEN,
                        "ORDER_ACK_SEMANTICS",
                        "ACK_DISTINCT_FROM_FILL",
                        (ack.event_id,),
                    )
                )
    elif acks:
        findings.append(
            _dec(
                TRAFFIC_GREEN,
                "ORDER_ACK_SEMANTICS",
                "ACK_WITHOUT_FILL",
                tuple(a.event_id for a in acks),
            )
        )
    else:
        findings.append(_dec(TRAFFIC_YELLOW, "ORDER_ACK_SEMANTICS", "ACK_NOT_OBSERVED", refs_all))

    # FILL_IDENTITY + DUPLICATE_FILL
    if fills:
        missing_fill_id = any(not f.fill_id for f in fills)
        fill_ids = [f.fill_id for f in fills if f.fill_id]
        if missing_fill_id:
            findings.append(
                _dec(TRAFFIC_YELLOW, "FILL_IDENTITY_INTEGRITY", "MISSING_FILL_ID", refs_all)
            )
        elif len(set(fill_ids)) != len(fill_ids):
            findings.append(
                _dec(TRAFFIC_RED, "DUPLICATE_FILL_INTEGRITY", "DUPLICATE_FILL_ID", refs_all)
            )
        else:
            findings.append(
                _dec(TRAFFIC_GREEN, "DUPLICATE_FILL_INTEGRITY", "UNIQUE_FILL_IDS", refs_all)
            )
    else:
        findings.append(
            _dec(TRAFFIC_YELLOW, "FILL_IDENTITY_INTEGRITY", "NO_FILL_EVIDENCE", refs_all)
        )

    # FILL_QUANTITY_INTEGRITY
    qty_ok = True
    missing_qty = False
    for f in fills:
        qty = f.payload.get("fill_quantity")
        if qty is None:
            missing_qty = True
            continue
        try:
            if Decimal(str(qty)) < 0:
                qty_ok = False
        except (InvalidOperation, ValueError):
            qty_ok = False
        order_qty = f.payload.get("order_quantity")
        if order_qty is not None:
            try:
                if Decimal(str(qty)) > Decimal(str(order_qty)):
                    qty_ok = False
            except (InvalidOperation, ValueError):
                qty_ok = False
    if fills and not qty_ok:
        findings.append(
            _dec(TRAFFIC_RED, "FILL_QUANTITY_INTEGRITY", "QTY_OVERFLOW_OR_INVALID", refs_all)
        )
    elif fills and missing_qty:
        findings.append(
            _dec(TRAFFIC_YELLOW, "FILL_QUANTITY_INTEGRITY", "MISSING_FILL_QUANTITY", refs_all)
        )
    elif fills:
        findings.append(_dec(TRAFFIC_GREEN, "FILL_QUANTITY_INTEGRITY", "OK", refs_all))
    else:
        findings.append(_dec(TRAFFIC_YELLOW, "FILL_QUANTITY_INTEGRITY", "UNKNOWN", refs_all))

    # PARTIAL_FILL_SEMANTICS — partial not auto RED
    partial = _by_kind(records, GhosvEvidenceKind.PARTIAL_FILL.value)
    if partial:
        findings.append(
            _dec(
                TRAFFIC_GREEN, "PARTIAL_FILL_SEMANTICS", "PARTIAL_OBSERVED_NOT_VIOLATION", refs_all
            )
        )

    # POSITION_ATTRIBUTION — FILL != POSITION
    if fills and positions:
        for pos in positions:
            if (
                pos.payload.get("derived_only_from_fill") is True
                and pos.payload.get("venue_confirmed") is not True
            ):
                findings.append(
                    _dec(
                        TRAFFIC_YELLOW,
                        "POSITION_ATTRIBUTION",
                        "POSITION_INFERRED_FROM_FILL_ONLY",
                        (pos.event_id,),
                    )
                )
            else:
                findings.append(
                    _dec(
                        TRAFFIC_GREEN,
                        "POSITION_ATTRIBUTION",
                        "POSITION_DISTINCT_EVIDENCE",
                        (pos.event_id,),
                    )
                )
    elif positions:
        findings.append(
            _dec(TRAFFIC_YELLOW, "POSITION_ATTRIBUTION", "POSITION_WITHOUT_FILL", refs_all)
        )
    else:
        findings.append(
            _dec(TRAFFIC_YELLOW, "POSITION_ATTRIBUTION", "MISSING_POSITION_EVIDENCE", refs_all)
        )

    # RECONCILIATION_CONSISTENCY
    for recon in recons:
        traffic, reason = _recon_traffic(recon)
        findings.append(_dec(traffic, "RECONCILIATION_CONSISTENCY", reason, (recon.event_id,)))

    if not recons:
        findings.append(
            _dec(TRAFFIC_YELLOW, "RECONCILIATION_CONSISTENCY", "RECON_NOT_OBSERVED", refs_all)
        )

    # EXECUTION_STATE_CONSISTENCY — PRE_EXTERNAL != POST
    pre = _by_kind(records, GhosvEvidenceKind.PRE_EXTERNAL_REPORT.value)
    attempts = _by_kind(records, GhosvEvidenceKind.EXECUTION_ATTEMPT.value)
    for att in attempts:
        if (
            att.payload.get("post_occurred") is True
            and att.payload.get("external_effect_authorized") is not True
        ):
            findings.append(
                _dec(
                    TRAFFIC_RED,
                    "EXECUTION_STATE_CONSISTENCY",
                    "POST_WITHOUT_EXTERNAL_EFFECT_AUTHORIZATION",
                    (att.event_id,),
                )
            )
    for p in pre:
        if str(p.payload.get("disposition", "")).upper() == "PRE_EXTERNAL_EFFECT" and any(
            a.payload.get("post_occurred") is True for a in attempts
        ):
            findings.append(
                _dec(
                    TRAFFIC_RED,
                    "EXECUTION_STATE_CONSISTENCY",
                    "PRE_EXTERNAL_CONTRADICTS_POST",
                    (p.event_id,),
                )
            )
    if not attempts and not pre:
        findings.append(
            _dec(TRAFFIC_YELLOW, "EXECUTION_STATE_CONSISTENCY", "EXECUTION_STATE_UNKNOWN", refs_all)
        )

    # Envelope required fields
    for env in envelopes:
        if not env.client_order_id or not env.instrument_id:
            findings.append(
                _dec(
                    TRAFFIC_RED,
                    "ORDER_IDENTITY_INTEGRITY",
                    "ENVELOPE_MISSING_IDENTITY",
                    (env.event_id,),
                )
            )

    return tuple(findings)
