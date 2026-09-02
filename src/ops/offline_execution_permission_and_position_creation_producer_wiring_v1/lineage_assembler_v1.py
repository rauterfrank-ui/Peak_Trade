"""Pure typed adapter: canonical upstream outputs → Z2DB lineage snapshot.

The assembler transforms and validates. It does not decide side, quantity,
risk, safety, or instrument. HOLD/EXIT cannot become ENTER.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Union

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingChainResultV1,
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingOutcome,
    QuantityProvenanceV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    CanonicalLineageSnapshotV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    ASSEMBLER_CONTRACT_VERSION,
    ASSEMBLER_ID,
    BLOCKED_DECISION_OUTCOMES,
    ENTRY_INTENT_ACTIONS,
    EXIT_DECISION_OUTCOMES,
    HOLD_DECISION_OUTCOMES,
    LINEAGE_PROVENANCE_PRODUCTIVE,
    PLAN_TO_DECISION_OUTCOME,
    PLAN_TO_MAPPER_SIDE,
    PLAN_TO_PLAN_SIDE,
    REQUIRED_QUANTITY_UNIT,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayBindingResultV0,
)

RiskSizingResultV1 = Union[CapitalRiskSizingChainResultV1, CapitalRiskSizingDecisionV1]


class LineageAssemblyStatusV1(str, Enum):
    PASS = "PASS"
    DENY = "DENY"
    HALT = "HALT"


@dataclass(frozen=True)
class CanonicalLineageAssemblyInputV1:
    selection_instrument_id: str
    evidence: CanonicalTradingDecisionEvidenceV1 | None
    risk_chain: RiskSizingResultV1 | None
    safety_binding: SafetyKernelOfflineReplayBindingResultV0 | None
    intent: CanonicalOrderIntentV1 | None
    mapper_action: IntendedAnalyticalActionV1 | None
    cycle_index: int
    live_send_allowed: bool = False


@dataclass(frozen=True)
class AssembledCanonicalLineageV1:
    lineage: CanonicalLineageSnapshotV1
    provenance: str
    assembly_digest: str
    assembler_id: str
    assembler_contract_version: str
    quantity_unit: str


@dataclass(frozen=True)
class CanonicalLineageAssemblyResultV1:
    status: LineageAssemblyStatusV1
    lineage: CanonicalLineageSnapshotV1 | None
    assembled: AssembledCanonicalLineageV1 | None
    reason_codes: tuple[str, ...]
    provenance: str | None


def _qty_text(value: Decimal) -> str:
    return format(value, "f")


def _parse_qty(raw: object) -> Decimal | None:
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, ValueError, TypeError):
        return None
    if not value.is_finite():
        return None
    return value


def _missing_token(raw: object) -> bool:
    token = str(raw or "").strip()
    return token == "" or token.upper() in {"UNKNOWN", "MISSING", "NONE"}


def _sha256_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _risk_digest(provenance: QuantityProvenanceV1) -> str:
    return _sha256_payload(
        {
            "capital_envelope_ref": provenance.capital_envelope_ref,
            "config_digest": provenance.config_digest,
            "implementation_digest": provenance.implementation_digest,
            "policy_version": provenance.policy_version,
            "post_sizing_risk_ref": provenance.post_sizing_risk_ref,
            "pre_sizing_risk_ref": provenance.pre_sizing_risk_ref,
            "sizing_ref": provenance.sizing_ref,
        }
    )


def _assembly_digest(lineage: CanonicalLineageSnapshotV1, *, provenance: str) -> str:
    payload = lineage.to_dict()
    payload["provenance"] = provenance
    payload["assembler_id"] = ASSEMBLER_ID
    payload["assembler_contract_version"] = ASSEMBLER_CONTRACT_VERSION
    return _sha256_payload(payload)


def _result(
    *,
    status: LineageAssemblyStatusV1,
    reasons: tuple[str, ...],
    assembled: AssembledCanonicalLineageV1 | None = None,
) -> CanonicalLineageAssemblyResultV1:
    lineage = None if assembled is None else assembled.lineage
    provenance = None if assembled is None else assembled.provenance
    return CanonicalLineageAssemblyResultV1(
        status=status,
        lineage=lineage,
        assembled=assembled,
        reason_codes=tuple(dict.fromkeys(reasons)),
        provenance=provenance,
    )


def assemble_canonical_lineage_snapshot_v1(
    payload: CanonicalLineageAssemblyInputV1,
) -> CanonicalLineageAssemblyResultV1:
    """Transform typed upstream outputs into Z2DB lineage. No I/O. No defaults."""
    reasons: list[str] = []
    status = LineageAssemblyStatusV1.PASS

    if payload.live_send_allowed:
        return _result(status=LineageAssemblyStatusV1.HALT, reasons=("LIVE_SEND_ALLOWED",))

    if int(payload.cycle_index) < 0:
        return _result(
            status=LineageAssemblyStatusV1.HALT,
            reasons=("CYCLE_INDEX_MUST_BE_NON_NEGATIVE",),
        )

    if payload.evidence is None:
        return _result(status=LineageAssemblyStatusV1.DENY, reasons=("MISSING_DECISION",))
    evidence = payload.evidence
    if _missing_token(evidence.decision_id):
        reasons.append("MISSING_DECISION_ID")
        status = LineageAssemblyStatusV1.DENY
    if _missing_token(evidence.replay_id):
        reasons.append("MISSING_CORRELATION_ID")
        status = LineageAssemblyStatusV1.DENY
    if _missing_token(payload.selection_instrument_id):
        reasons.append("MISSING_BINDING")
        status = LineageAssemblyStatusV1.DENY
    if _missing_token(evidence.instrument_id):
        reasons.append("MISSING_BINDING")
        status = LineageAssemblyStatusV1.DENY
    elif str(evidence.instrument_id) != str(payload.selection_instrument_id):
        reasons.append("SELECTION_BINDING_MISMATCH")
        status = LineageAssemblyStatusV1.DENY
    if evidence.execution_eligible or evidence.adapter_compatible:
        reasons.append("PLAN_ONLY_BOUNDARY_VIOLATION")
        status = LineageAssemblyStatusV1.HALT

    outcome = str(evidence.decision_outcome or "").strip().lower()
    if outcome in HOLD_DECISION_OUTCOMES:
        reasons.append("HOLD")
        status = LineageAssemblyStatusV1.DENY
    elif outcome in EXIT_DECISION_OUTCOMES:
        reasons.append("EXIT")
        status = LineageAssemblyStatusV1.DENY
    elif outcome in BLOCKED_DECISION_OUTCOMES:
        reasons.append("BLOCKED")
        status = LineageAssemblyStatusV1.DENY
    elif _missing_token(outcome):
        reasons.append("UNKNOWN")
        status = LineageAssemblyStatusV1.DENY

    if payload.risk_chain is None:
        reasons.append("RISK_FAIL")
        status = LineageAssemblyStatusV1.DENY
        risk_chain = None
    else:
        risk_chain = payload.risk_chain
        if risk_chain.outcome is not CapitalRiskSizingOutcome.PASS:
            reasons.append("RISK_FAIL")
            status = LineageAssemblyStatusV1.DENY
        if risk_chain.quantity_provenance is None:
            reasons.append("RISK_DIGEST_MISSING_OR_UNKNOWN")
            status = LineageAssemblyStatusV1.DENY

    if payload.safety_binding is None:
        reasons.append("SAFETY_FAIL")
        status = LineageAssemblyStatusV1.DENY
        safety_binding = None
    else:
        safety_binding = payload.safety_binding
        if not safety_binding.binding_applied:
            reasons.append("SAFETY_FAIL")
            status = LineageAssemblyStatusV1.DENY
        bound_evidence = safety_binding.evidence
        if bound_evidence.decision_id != evidence.decision_id:
            reasons.append("DECISION_ID_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
        if bound_evidence.instrument_id != evidence.instrument_id:
            reasons.append("INSTRUMENT_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
        if safety_binding.boundary.hard_block_reasons:
            reasons.append("SAFETY_FAIL")
            status = LineageAssemblyStatusV1.DENY
        if _missing_token(safety_binding.boundary.semantic_digest):
            reasons.append("SAFETY_DIGEST_MISSING_OR_UNKNOWN")
            status = LineageAssemblyStatusV1.DENY

    if payload.intent is None:
        reasons.append("PLAN_MISSING")
        status = LineageAssemblyStatusV1.DENY
        intent = None
    else:
        intent = payload.intent
        if intent.execution_eligible or intent.adapter_compatible:
            reasons.append("PLAN_EXECUTION_ELIGIBLE")
            status = LineageAssemblyStatusV1.HALT
        if intent.submission_authorized:
            reasons.append("PLAN_SUBMISSION_AUTHORIZED")
            status = LineageAssemblyStatusV1.HALT
        if _missing_token(intent.intent_action):
            reasons.append("PLAN_MISSING")
            status = LineageAssemblyStatusV1.DENY
        elif intent.intent_action not in ENTRY_INTENT_ACTIONS:
            if intent.intent_action in {"EXIT", "REDUCE"}:
                reasons.append("EXIT")
            elif intent.intent_action in {"NO_ACTION", "HOLD"}:
                reasons.append("HOLD")
            else:
                reasons.append("PLAN_NOT_POSITION_CREATION")
            status = LineageAssemblyStatusV1.DENY
        if intent.decision_id != evidence.decision_id:
            reasons.append("DECISION_ID_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
        if intent.instrument_id != evidence.instrument_id:
            reasons.append("INSTRUMENT_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
        if str(intent.trading_epoch) != str(evidence.trading_epoch):
            reasons.append("TRADING_EPOCH_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
        if str(intent.quantity_unit or "") != REQUIRED_QUANTITY_UNIT:
            reasons.append("QUANTITY_UNIT_UNSUPPORTED")
            status = LineageAssemblyStatusV1.DENY
        if _missing_token(intent.semantic_digest) and _missing_token(intent.provenance_digest):
            reasons.append("PLAN_DIGEST_MISSING_OR_UNKNOWN")
            status = LineageAssemblyStatusV1.DENY

    if payload.mapper_action is None:
        reasons.append("MAPPER_MISSING")
        status = LineageAssemblyStatusV1.DENY
        mapper = None
    else:
        mapper = payload.mapper_action
        if mapper.safety_blocked:
            reasons.append("SAFETY_FAIL")
            status = LineageAssemblyStatusV1.DENY
        if str(mapper.intended_side or "").strip().upper() == "HOLD":
            reasons.append("HOLD")
            status = LineageAssemblyStatusV1.DENY

    if status is not LineageAssemblyStatusV1.PASS:
        return _result(status=status, reasons=tuple(reasons) or ("DENIED",))

    assert intent is not None
    assert mapper is not None
    assert risk_chain is not None
    assert safety_binding is not None
    assert risk_chain.quantity_provenance is not None

    plan_action = intent.intent_action
    expected_outcome = PLAN_TO_DECISION_OUTCOME[plan_action]
    expected_plan_side = PLAN_TO_PLAN_SIDE[plan_action]
    expected_mapper_side = PLAN_TO_MAPPER_SIDE[plan_action]
    if outcome != expected_outcome:
        reasons.append("DECISION_PLAN_MISMATCH")
        status = LineageAssemblyStatusV1.DENY
    if intent.side != expected_plan_side:
        reasons.append("PLAN_SIDE_MISMATCH")
        status = LineageAssemblyStatusV1.DENY
    mapper_side = str(mapper.intended_side or "").strip().upper()
    if mapper_side != expected_mapper_side:
        reasons.append("MAPPER_SIDE_MISMATCH")
        status = LineageAssemblyStatusV1.DENY
    mapper_intent = str(mapper.intent_action or "").strip()
    if mapper_intent not in {plan_action, expected_outcome, ""}:
        if mapper_intent != plan_action:
            reasons.append("MAPPER_INTENT_MISMATCH")
            status = LineageAssemblyStatusV1.DENY
    mapper_outcome = str(mapper.decision_outcome or "").strip().lower()
    if mapper_outcome and mapper_outcome != expected_outcome:
        reasons.append("MAPPER_INTENT_MISMATCH")
        status = LineageAssemblyStatusV1.DENY

    plan_qty = _parse_qty(intent.quantity)
    mapper_qty = _parse_qty(mapper.intended_quantity)
    risk_qty = _parse_qty(risk_chain.final_quantity)
    if plan_qty is None or mapper_qty is None:
        reasons.append("QTY_INVALID")
        status = LineageAssemblyStatusV1.DENY
    elif plan_qty == 0 or mapper_qty == 0:
        reasons.append("ZERO_QTY")
        status = LineageAssemblyStatusV1.DENY
    elif plan_qty < 0 or mapper_qty < 0:
        reasons.append("NEGATIVE_OR_INVALID_QTY")
        status = LineageAssemblyStatusV1.DENY
    elif plan_qty != mapper_qty:
        reasons.append("MAPPER_QTY_MISMATCH")
        status = LineageAssemblyStatusV1.DENY
    elif risk_qty is None or risk_qty != plan_qty:
        reasons.append("MAPPER_QTY_MISMATCH")
        status = LineageAssemblyStatusV1.DENY

    if status is not LineageAssemblyStatusV1.PASS:
        return _result(status=status, reasons=tuple(reasons) or ("DENIED",))
    if plan_qty is None:
        return _result(status=LineageAssemblyStatusV1.DENY, reasons=("QTY_INVALID",))

    plan_digest = (
        str(intent.semantic_digest)
        if not _missing_token(intent.semantic_digest)
        else str(intent.provenance_digest)
    )
    lineage = CanonicalLineageSnapshotV1(
        instrument_id=str(evidence.instrument_id),
        decision_id=str(evidence.decision_id),
        correlation_id=str(evidence.replay_id),
        cycle_index=int(payload.cycle_index),
        trading_epoch=str(evidence.trading_epoch),
        risk_outcome=str(risk_chain.outcome.value),
        risk_digest=_risk_digest(risk_chain.quantity_provenance),
        safety_hard_blocked=False,
        safety_digest=str(safety_binding.boundary.semantic_digest),
        plan_intent_action=plan_action,
        plan_side=str(intent.side),
        plan_quantity=_qty_text(plan_qty),
        plan_digest=plan_digest,
        plan_execution_eligible=False,
        plan_adapter_compatible=False,
        plan_submission_authorized=False,
        mapper_intended_side=expected_mapper_side,
        mapper_intended_quantity=_qty_text(plan_qty),
        mapper_decision_outcome=expected_outcome,
        mapper_intent_action=plan_action,
        mapper_safety_blocked=False,
        mapper_reason_codes=tuple(mapper.reason_codes),
    )
    assembled = AssembledCanonicalLineageV1(
        lineage=lineage,
        provenance=LINEAGE_PROVENANCE_PRODUCTIVE,
        assembly_digest=_assembly_digest(lineage, provenance=LINEAGE_PROVENANCE_PRODUCTIVE),
        assembler_id=ASSEMBLER_ID,
        assembler_contract_version=ASSEMBLER_CONTRACT_VERSION,
        quantity_unit=REQUIRED_QUANTITY_UNIT,
    )
    return _result(
        status=LineageAssemblyStatusV1.PASS,
        reasons=("CANONICAL_LINEAGE_ASSEMBLED",),
        assembled=assembled,
    )
