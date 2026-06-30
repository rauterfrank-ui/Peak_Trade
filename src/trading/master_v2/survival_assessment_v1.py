# src/trading/master_v2/survival_assessment_v1.py
"""
Pure Survival Assessment v1: shared offline survival contract for STEP 29F Rank-1.

Consumes immutable DirectionalAssessmentV1 evidence and explicit survival inputs.
Produces fachliche survival evidence only — no runtime, authority, order, risk,
sizing, suitability selection, or strategy-registry effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional, Tuple

from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentSide,
    DirectionalAssessmentStatus,
    DirectionalAssessmentV1,
    mirror_price_path_for_short,
)

SURVIVAL_ASSESSMENT_LAYER_VERSION = "v1"
SURVIVAL_ASSESSMENT_POLICY_VERSION = "survival_assessment_policy_v1"

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_RISK_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

_REQUIRED_SUBCHECK_NAMES = (
    "data_completeness_check",
    "cost_survival_check",
    "volatility_survival_check",
    "sequence_survival_check",
    "drawdown_survival_check",
    "liquidation_buffer_check",
)


class SurvivalAssessmentStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"


class SurvivalSubcheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class SurvivalHardFailReason(str, Enum):
    DATA_COMPLETENESS_FAIL = "data_completeness_fail"
    COST_SURVIVAL_FAIL = "cost_survival_fail"
    VOLATILITY_SURVIVAL_FAIL = "volatility_survival_fail"
    SEQUENCE_SURVIVAL_FAIL = "sequence_survival_fail"
    DRAWDOWN_SURVIVAL_FAIL = "drawdown_survival_fail"
    LIQUIDATION_BUFFER_FAIL = "liquidation_buffer_fail"
    NET_EDGE_INSUFFICIENT = "net_edge_insufficient"
    EXPLICIT_HARD_FAIL = "explicit_hard_fail"


class SurvivalBlockedReason(str, Enum):
    DIRECTIONAL_ASSESSMENT_BLOCKED = "directional_assessment_blocked"
    DIRECTIONAL_ASSESSMENT_INVALID = "directional_assessment_invalid"
    DIRECTIONAL_ASSESSMENT_REF_STALE = "directional_assessment_ref_stale"
    INPUT_INCOMPLETE = "input_incomplete"
    INSTRUMENT_KIND_FORBIDDEN = "instrument_kind_forbidden"
    POLICY_VERSION_INVALID = "policy_version_invalid"
    POLICY_MIN_NET_EDGE_INVALID = "policy_min_net_edge_invalid"
    POLICY_VALIDITY_EPOCHS_INVALID = "policy_validity_epochs_invalid"
    TRADING_EPOCH_OUT_OF_ORDER = "trading_epoch_out_of_order"
    TRADING_EPOCH_STALE = "trading_epoch_stale"
    MISSING_ENTRY_FEE = "missing_entry_fee"
    MISSING_EXIT_FEE = "missing_exit_fee"
    MISSING_ENTRY_SLIPPAGE = "missing_entry_slippage"
    MISSING_EXIT_SLIPPAGE = "missing_exit_slippage"
    MISSING_FUNDING_COST = "missing_funding_cost"
    MISSING_GROSS_EDGE = "missing_gross_edge"
    REQUIRED_SUBCHECK_UNKNOWN = "required_subcheck_unknown"
    REQUIRED_SUBCHECK_NOT_APPLICABLE = "required_subcheck_not_applicable"
    EXPLICIT_BLOCKED = "explicit_blocked"


@dataclass(frozen=True)
class DirectionalAssessmentRefV1:
    """Immutable reference to upstream DirectionalAssessmentV1 evidence."""

    assessment_id: str
    semantic_digest: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    status: DirectionalAssessmentStatus

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)


@dataclass(frozen=True)
class SurvivalSubcheckResultV1:
    name: str
    status: SurvivalSubcheckStatus
    reason_code: str = ""


@dataclass(frozen=True)
class SurvivalCostInputsV1:
    """Explicit cost fields; missing required values fail closed as BLOCKED."""

    entry_fee: Optional[float]
    expected_entry_slippage: Optional[float]
    exit_fee: Optional[float]
    expected_exit_slippage: Optional[float]
    expected_funding_cost: Optional[float]
    expected_gross_edge: Optional[float]
    funding_cost_required: bool = True


@dataclass(frozen=True)
class SurvivalMetricInputsV1:
    """Explicit survival metric inputs for non-cost subchecks."""

    data_completeness_complete: Optional[bool]
    volatility_survival_ratio: Optional[float]
    sequence_survival_ratio: Optional[float]
    drawdown_survival_ratio: Optional[float]
    liquidation_buffer_ratio: Optional[float]


@dataclass(frozen=True)
class SurvivalAssessmentPolicyV1:
    min_net_edge: float
    min_volatility_survival_ratio: float
    min_sequence_survival_ratio: float
    min_drawdown_survival_ratio: float
    min_liquidation_buffer_ratio: float
    validity_epochs: int
    policy_version: str = SURVIVAL_ASSESSMENT_POLICY_VERSION


@dataclass(frozen=True)
class SurvivalAssessmentInputV1:
    instrument_id: str
    trading_epoch: int
    side: DirectionalAssessmentSide
    directional_assessment: DirectionalAssessmentV1
    cost_inputs: SurvivalCostInputsV1
    metric_inputs: SurvivalMetricInputsV1
    last_evaluated_trading_epoch: int
    input_complete: bool
    explicit_hard_fail_reasons: Tuple[SurvivalHardFailReason, ...]
    explicit_blocked_reasons: Tuple[SurvivalBlockedReason, ...]
    policy_version: str


@dataclass(frozen=True)
class SurvivalResultV1:
    survival_id: str
    instrument_id: str
    side: DirectionalAssessmentSide
    trading_epoch: int
    directional_assessment_ref: DirectionalAssessmentRefV1
    data_completeness_result: SurvivalSubcheckResultV1
    cost_survival_result: SurvivalSubcheckResultV1
    volatility_survival_result: SurvivalSubcheckResultV1
    sequence_survival_result: SurvivalSubcheckResultV1
    drawdown_survival_result: SurvivalSubcheckResultV1
    liquidation_buffer_result: SurvivalSubcheckResultV1
    expected_gross_edge: Optional[float]
    expected_roundtrip_cost: Optional[float]
    net_expected_edge: Optional[float]
    status: SurvivalAssessmentStatus
    hard_fail_reasons: Tuple[str, ...]
    blocked_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    policy_version: str
    valid_until_epoch: int
    semantic_digest: str
    authority_effect: str = _AUTHORITY_EFFECT_NONE
    runtime_effect: str = _RUNTIME_EFFECT_NONE
    order_effect: str = _ORDER_EFFECT_NONE
    risk_effect: str = _RISK_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.semantic_digest and not _valid_sha256_hex(self.semantic_digest):
            msg = "semantic_digest must be empty or a 64-char lowercase sha256 hex"
            raise ValueError(msg)
        if self.valid_until_epoch <= self.trading_epoch:
            msg = "valid_until_epoch must be strictly greater than trading_epoch"
            raise ValueError(msg)


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _positive_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) > 0.0


def _non_negative_finite(value: object) -> bool:
    return isinstance(value, (int, float)) and float(value) >= 0.0


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and value > 0


def _instrument_id_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def directional_assessment_ref_from_assessment(
    assessment: DirectionalAssessmentV1,
) -> DirectionalAssessmentRefV1:
    return DirectionalAssessmentRefV1(
        assessment_id=assessment.assessment_id,
        semantic_digest=assessment.semantic_digest,
        trading_epoch=assessment.trading_epoch,
        side=assessment.side,
        status=assessment.status,
    )


def validate_survival_assessment_policy(
    policy: SurvivalAssessmentPolicyV1,
    *,
    policy_version: str,
) -> Tuple[SurvivalBlockedReason, ...]:
    blocks: list[SurvivalBlockedReason] = []
    if not policy.policy_version or policy.policy_version != SURVIVAL_ASSESSMENT_POLICY_VERSION:
        blocks.append(SurvivalBlockedReason.POLICY_VERSION_INVALID)
    if policy_version != SURVIVAL_ASSESSMENT_POLICY_VERSION:
        blocks.append(SurvivalBlockedReason.POLICY_VERSION_INVALID)
    if not _non_negative_finite(policy.min_net_edge):
        blocks.append(SurvivalBlockedReason.POLICY_MIN_NET_EDGE_INVALID)
    if not _positive_int(policy.validity_epochs):
        blocks.append(SurvivalBlockedReason.POLICY_VALIDITY_EPOCHS_INVALID)
    return tuple(dict.fromkeys(blocks))


def compute_expected_roundtrip_cost(costs: SurvivalCostInputsV1) -> Optional[float]:
    fields = (
        costs.entry_fee,
        costs.expected_entry_slippage,
        costs.exit_fee,
        costs.expected_exit_slippage,
    )
    if any(v is None for v in fields):
        return None
    funding = costs.expected_funding_cost
    if costs.funding_cost_required and funding is None:
        return None
    total = float(costs.entry_fee) + float(costs.expected_entry_slippage)
    total += float(costs.exit_fee) + float(costs.expected_exit_slippage)
    if funding is not None:
        total += float(funding)
    return total


def compute_net_expected_edge(
    *,
    expected_gross_edge: Optional[float],
    expected_roundtrip_cost: Optional[float],
) -> Optional[float]:
    if expected_gross_edge is None or expected_roundtrip_cost is None:
        return None
    return float(expected_gross_edge) - float(expected_roundtrip_cost)


def _collect_cost_blocked_reasons(costs: SurvivalCostInputsV1) -> Tuple[SurvivalBlockedReason, ...]:
    blocks: list[SurvivalBlockedReason] = []
    if costs.entry_fee is None:
        blocks.append(SurvivalBlockedReason.MISSING_ENTRY_FEE)
    if costs.exit_fee is None:
        blocks.append(SurvivalBlockedReason.MISSING_EXIT_FEE)
    if costs.expected_entry_slippage is None:
        blocks.append(SurvivalBlockedReason.MISSING_ENTRY_SLIPPAGE)
    if costs.expected_exit_slippage is None:
        blocks.append(SurvivalBlockedReason.MISSING_EXIT_SLIPPAGE)
    if costs.funding_cost_required and costs.expected_funding_cost is None:
        blocks.append(SurvivalBlockedReason.MISSING_FUNDING_COST)
    if costs.expected_gross_edge is None:
        blocks.append(SurvivalBlockedReason.MISSING_GROSS_EDGE)
    return tuple(dict.fromkeys(blocks))


def _evaluate_data_completeness(
    metric_inputs: SurvivalMetricInputsV1,
) -> SurvivalSubcheckResultV1:
    if metric_inputs.data_completeness_complete is None:
        return SurvivalSubcheckResultV1(
            name="data_completeness_check",
            status=SurvivalSubcheckStatus.UNKNOWN,
            reason_code="data_completeness_unknown",
        )
    if metric_inputs.data_completeness_complete:
        return SurvivalSubcheckResultV1(
            name="data_completeness_check",
            status=SurvivalSubcheckStatus.PASS,
            reason_code="data_completeness_pass",
        )
    return SurvivalSubcheckResultV1(
        name="data_completeness_check",
        status=SurvivalSubcheckStatus.FAIL,
        reason_code="data_completeness_fail",
    )


def _evaluate_ratio_subcheck(
    *,
    name: str,
    value: Optional[float],
    minimum: float,
    pass_code: str,
    fail_code: str,
) -> SurvivalSubcheckResultV1:
    if value is None:
        return SurvivalSubcheckResultV1(
            name=name,
            status=SurvivalSubcheckStatus.UNKNOWN,
            reason_code=f"{name}_unknown",
        )
    if float(value) >= float(minimum):
        return SurvivalSubcheckResultV1(
            name=name, status=SurvivalSubcheckStatus.PASS, reason_code=pass_code
        )
    return SurvivalSubcheckResultV1(
        name=name, status=SurvivalSubcheckStatus.FAIL, reason_code=fail_code
    )


def _evaluate_cost_survival(
    *,
    costs: SurvivalCostInputsV1,
    policy: SurvivalAssessmentPolicyV1,
    roundtrip_cost: Optional[float],
    net_edge: Optional[float],
) -> Tuple[SurvivalSubcheckResultV1, Tuple[SurvivalBlockedReason, ...]]:
    blocked = _collect_cost_blocked_reasons(costs)
    if blocked:
        return (
            SurvivalSubcheckResultV1(
                name="cost_survival_check",
                status=SurvivalSubcheckStatus.UNKNOWN,
                reason_code="cost_inputs_incomplete",
            ),
            blocked,
        )
    assert net_edge is not None
    if net_edge < float(policy.min_net_edge):
        return (
            SurvivalSubcheckResultV1(
                name="cost_survival_check",
                status=SurvivalSubcheckStatus.FAIL,
                reason_code="net_edge_insufficient",
            ),
            (),
        )
    assert roundtrip_cost is not None
    return (
        SurvivalSubcheckResultV1(
            name="cost_survival_check",
            status=SurvivalSubcheckStatus.PASS,
            reason_code="cost_survival_pass",
        ),
        (),
    )


def aggregate_survival_status(
    subchecks: Tuple[SurvivalSubcheckResultV1, ...],
) -> SurvivalAssessmentStatus:
    required = tuple(s for s in subchecks if s.name in _REQUIRED_SUBCHECK_NAMES)
    if any(s.status is SurvivalSubcheckStatus.FAIL for s in required):
        return SurvivalAssessmentStatus.FAIL
    if any(s.status is SurvivalSubcheckStatus.UNKNOWN for s in required):
        return SurvivalAssessmentStatus.BLOCKED
    if any(s.status is SurvivalSubcheckStatus.NOT_APPLICABLE for s in required):
        return SurvivalAssessmentStatus.BLOCKED
    if all(s.status is SurvivalSubcheckStatus.PASS for s in required):
        return SurvivalAssessmentStatus.PASS
    return SurvivalAssessmentStatus.BLOCKED


def _subcheck_to_hard_fail_reason(name: str) -> Optional[SurvivalHardFailReason]:
    mapping: Mapping[str, SurvivalHardFailReason] = {
        "data_completeness_check": SurvivalHardFailReason.DATA_COMPLETENESS_FAIL,
        "cost_survival_check": SurvivalHardFailReason.COST_SURVIVAL_FAIL,
        "volatility_survival_check": SurvivalHardFailReason.VOLATILITY_SURVIVAL_FAIL,
        "sequence_survival_check": SurvivalHardFailReason.SEQUENCE_SURVIVAL_FAIL,
        "drawdown_survival_check": SurvivalHardFailReason.DRAWDOWN_SURVIVAL_FAIL,
        "liquidation_buffer_check": SurvivalHardFailReason.LIQUIDATION_BUFFER_FAIL,
    }
    return mapping.get(name)


def _derive_survival_id(
    instrument_id: str,
    trading_epoch: int,
    side: DirectionalAssessmentSide,
    status: SurvivalAssessmentStatus,
) -> str:
    return f"survival-{instrument_id}-epoch{trading_epoch}-{side.value}-{status.value}"


def serialize_survival_result_canonical(result: SurvivalResultV1) -> str:
    ref = result.directional_assessment_ref

    def _subcheck_payload(sc: SurvivalSubcheckResultV1) -> dict[str, str]:
        return {"name": sc.name, "reason_code": sc.reason_code, "status": sc.status.value}

    payload = {
        "authority_effect": result.authority_effect,
        "blocked_reasons": sorted(result.blocked_reasons),
        "cost_survival_result": _subcheck_payload(result.cost_survival_result),
        "data_completeness_result": _subcheck_payload(result.data_completeness_result),
        "directional_assessment_id": ref.assessment_id,
        "directional_assessment_digest": ref.semantic_digest,
        "directional_assessment_epoch": ref.trading_epoch,
        "directional_assessment_side": ref.side.value,
        "directional_assessment_status": ref.status.value,
        "drawdown_survival_result": _subcheck_payload(result.drawdown_survival_result),
        "expected_gross_edge": result.expected_gross_edge,
        "expected_roundtrip_cost": result.expected_roundtrip_cost,
        "hard_fail_reasons": sorted(result.hard_fail_reasons),
        "instrument_id": result.instrument_id,
        "layer_version": SURVIVAL_ASSESSMENT_LAYER_VERSION,
        "liquidation_buffer_result": _subcheck_payload(result.liquidation_buffer_result),
        "net_expected_edge": result.net_expected_edge,
        "order_effect": result.order_effect,
        "policy_version": result.policy_version,
        "reason_codes": sorted(result.reason_codes),
        "risk_effect": result.risk_effect,
        "runtime_effect": result.runtime_effect,
        "sequence_survival_result": _subcheck_payload(result.sequence_survival_result),
        "side": result.side.value,
        "status": result.status.value,
        "survival_id": result.survival_id,
        "trading_epoch": result.trading_epoch,
        "valid_until_epoch": result.valid_until_epoch,
        "volatility_survival_result": _subcheck_payload(result.volatility_survival_result),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_survival_result_semantic_digest(result: SurvivalResultV1) -> str:
    canonical = serialize_survival_result_canonical(result)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def with_computed_survival_result_digest(result: SurvivalResultV1) -> SurvivalResultV1:
    digest = compute_survival_result_semantic_digest(result)
    return SurvivalResultV1(
        survival_id=result.survival_id,
        instrument_id=result.instrument_id,
        side=result.side,
        trading_epoch=result.trading_epoch,
        directional_assessment_ref=result.directional_assessment_ref,
        data_completeness_result=result.data_completeness_result,
        cost_survival_result=result.cost_survival_result,
        volatility_survival_result=result.volatility_survival_result,
        sequence_survival_result=result.sequence_survival_result,
        drawdown_survival_result=result.drawdown_survival_result,
        liquidation_buffer_result=result.liquidation_buffer_result,
        expected_gross_edge=result.expected_gross_edge,
        expected_roundtrip_cost=result.expected_roundtrip_cost,
        net_expected_edge=result.net_expected_edge,
        status=result.status,
        hard_fail_reasons=result.hard_fail_reasons,
        blocked_reasons=result.blocked_reasons,
        reason_codes=result.reason_codes,
        policy_version=result.policy_version,
        valid_until_epoch=result.valid_until_epoch,
        semantic_digest=digest,
        authority_effect=result.authority_effect,
        runtime_effect=result.runtime_effect,
        order_effect=result.order_effect,
        risk_effect=result.risk_effect,
    )


def _resolve_epoch_semantics(
    *,
    trading_epoch: int,
    last_evaluated_trading_epoch: int,
    assessment_epoch: int,
) -> Tuple[str, Optional[SurvivalBlockedReason]]:
    if assessment_epoch > trading_epoch:
        return "stale_assessment_ref", SurvivalBlockedReason.DIRECTIONAL_ASSESSMENT_REF_STALE
    if last_evaluated_trading_epoch < 0:
        return "first", None
    if trading_epoch < last_evaluated_trading_epoch:
        return "out_of_order", SurvivalBlockedReason.TRADING_EPOCH_OUT_OF_ORDER
    return "ok", None


def _finalize_result(
    inp: SurvivalAssessmentInputV1,
    policy: SurvivalAssessmentPolicyV1,
    *,
    status: SurvivalAssessmentStatus,
    subchecks: Tuple[SurvivalSubcheckResultV1, ...],
    expected_gross_edge: Optional[float],
    expected_roundtrip_cost: Optional[float],
    net_expected_edge: Optional[float],
    hard_fail_reasons: Tuple[str, ...],
    blocked_reasons: Tuple[str, ...],
    reason_codes: Tuple[str, ...],
) -> SurvivalResultV1:
    data, cost, vol, seq, dd, liq = subchecks
    valid_until = inp.trading_epoch + policy.validity_epochs
    result = SurvivalResultV1(
        survival_id=_derive_survival_id(inp.instrument_id, inp.trading_epoch, inp.side, status),
        instrument_id=inp.instrument_id,
        side=inp.side,
        trading_epoch=inp.trading_epoch,
        directional_assessment_ref=directional_assessment_ref_from_assessment(
            inp.directional_assessment
        ),
        data_completeness_result=data,
        cost_survival_result=cost,
        volatility_survival_result=vol,
        sequence_survival_result=seq,
        drawdown_survival_result=dd,
        liquidation_buffer_result=liq,
        expected_gross_edge=expected_gross_edge,
        expected_roundtrip_cost=expected_roundtrip_cost,
        net_expected_edge=net_expected_edge,
        status=status,
        hard_fail_reasons=hard_fail_reasons,
        blocked_reasons=blocked_reasons,
        reason_codes=reason_codes,
        policy_version=policy.policy_version,
        valid_until_epoch=valid_until,
        semantic_digest="",
    )
    return with_computed_survival_result_digest(result)


def evaluate_survival_assessment_v1(
    inp: SurvivalAssessmentInputV1,
    policy: SurvivalAssessmentPolicyV1,
) -> SurvivalResultV1:
    """
    Deterministic survival evaluator.

    Fail-closed on incomplete, untrusted, or epoch-invalid inputs. Never mutates
    ``inp.directional_assessment`` or upstream directional evidence.
    """
    empty_subchecks = tuple(
        SurvivalSubcheckResultV1(name=name, status=SurvivalSubcheckStatus.UNKNOWN)
        for name in _REQUIRED_SUBCHECK_NAMES
    )

    policy_blocks = validate_survival_assessment_policy(policy, policy_version=inp.policy_version)
    if policy_blocks:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=tuple(sorted(r.value for r in policy_blocks)),
            reason_codes=("policy_validation_failed",),
        )

    if not _instrument_id_allowed(inp.instrument_id):
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=(SurvivalBlockedReason.INSTRUMENT_KIND_FORBIDDEN.value,),
            reason_codes=("instrument_gate_failed",),
        )

    if not inp.input_complete:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=(SurvivalBlockedReason.INPUT_INCOMPLETE.value,),
            reason_codes=("input_gate_failed",),
        )

    if inp.explicit_blocked_reasons:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=tuple(sorted(r.value for r in inp.explicit_blocked_reasons)),
            reason_codes=("explicit_blocked",),
        )

    assessment = inp.directional_assessment
    if assessment.status is DirectionalAssessmentStatus.INVALID:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=(SurvivalBlockedReason.DIRECTIONAL_ASSESSMENT_INVALID.value,),
            reason_codes=("directional_assessment_gate_failed",),
        )
    if assessment.status is DirectionalAssessmentStatus.BLOCKED:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=(SurvivalBlockedReason.DIRECTIONAL_ASSESSMENT_BLOCKED.value,),
            reason_codes=("directional_assessment_gate_failed",),
        )

    epoch_mode, epoch_block = _resolve_epoch_semantics(
        trading_epoch=inp.trading_epoch,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        assessment_epoch=assessment.trading_epoch,
    )
    if epoch_block is not None:
        return _finalize_result(
            inp,
            policy,
            status=SurvivalAssessmentStatus.BLOCKED,
            subchecks=empty_subchecks,
            expected_gross_edge=None,
            expected_roundtrip_cost=None,
            net_expected_edge=None,
            hard_fail_reasons=(),
            blocked_reasons=(epoch_block.value,),
            reason_codes=(f"epoch_semantics_failed:{epoch_mode}",),
        )

    data_result = _evaluate_data_completeness(inp.metric_inputs)
    roundtrip_cost = compute_expected_roundtrip_cost(inp.cost_inputs)
    net_edge = compute_net_expected_edge(
        expected_gross_edge=inp.cost_inputs.expected_gross_edge,
        expected_roundtrip_cost=roundtrip_cost,
    )
    cost_result, cost_blocks = _evaluate_cost_survival(
        costs=inp.cost_inputs,
        policy=policy,
        roundtrip_cost=roundtrip_cost,
        net_edge=net_edge,
    )
    vol_result = _evaluate_ratio_subcheck(
        name="volatility_survival_check",
        value=inp.metric_inputs.volatility_survival_ratio,
        minimum=policy.min_volatility_survival_ratio,
        pass_code="volatility_survival_pass",
        fail_code="volatility_survival_fail",
    )
    seq_result = _evaluate_ratio_subcheck(
        name="sequence_survival_check",
        value=inp.metric_inputs.sequence_survival_ratio,
        minimum=policy.min_sequence_survival_ratio,
        pass_code="sequence_survival_pass",
        fail_code="sequence_survival_fail",
    )
    dd_result = _evaluate_ratio_subcheck(
        name="drawdown_survival_check",
        value=inp.metric_inputs.drawdown_survival_ratio,
        minimum=policy.min_drawdown_survival_ratio,
        pass_code="drawdown_survival_pass",
        fail_code="drawdown_survival_fail",
    )
    liq_result = _evaluate_ratio_subcheck(
        name="liquidation_buffer_check",
        value=inp.metric_inputs.liquidation_buffer_ratio,
        minimum=policy.min_liquidation_buffer_ratio,
        pass_code="liquidation_buffer_pass",
        fail_code="liquidation_buffer_fail",
    )

    subchecks = (
        data_result,
        cost_result,
        vol_result,
        seq_result,
        dd_result,
        liq_result,
    )
    status = aggregate_survival_status(subchecks)

    hard_fail_reasons: list[str] = []
    blocked_reasons: list[str] = list(r.value for r in cost_blocks)
    reason_codes: list[str] = []

    for sc in subchecks:
        if sc.status is SurvivalSubcheckStatus.FAIL:
            hard = _subcheck_to_hard_fail_reason(sc.name)
            if hard is not None:
                hard_fail_reasons.append(hard.value)
            if sc.name == "cost_survival_check" and sc.reason_code == "net_edge_insufficient":
                hard_fail_reasons.append(SurvivalHardFailReason.NET_EDGE_INSUFFICIENT.value)
            reason_codes.append(sc.reason_code)
        elif sc.status is SurvivalSubcheckStatus.UNKNOWN:
            blocked_reasons.append(SurvivalBlockedReason.REQUIRED_SUBCHECK_UNKNOWN.value)
            reason_codes.append(sc.reason_code)
        elif sc.status is SurvivalSubcheckStatus.NOT_APPLICABLE:
            blocked_reasons.append(SurvivalBlockedReason.REQUIRED_SUBCHECK_NOT_APPLICABLE.value)
            reason_codes.append(sc.reason_code)

    if inp.explicit_hard_fail_reasons:
        hard_fail_reasons.extend(sorted(r.value for r in inp.explicit_hard_fail_reasons))
        status = SurvivalAssessmentStatus.FAIL
        reason_codes.append("explicit_hard_fail")

    if status is SurvivalAssessmentStatus.PASS:
        reason_codes.append("all_required_subchecks_pass")

    return _finalize_result(
        inp,
        policy,
        status=status,
        subchecks=subchecks,
        expected_gross_edge=inp.cost_inputs.expected_gross_edge,
        expected_roundtrip_cost=roundtrip_cost,
        net_expected_edge=net_edge,
        hard_fail_reasons=tuple(dict.fromkeys(hard_fail_reasons)),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


def mirror_survival_metric_inputs_for_short(
    metrics: SurvivalMetricInputsV1,
) -> SurvivalMetricInputsV1:
    """Structural mirror helper for Long/Short symmetry tests."""
    return SurvivalMetricInputsV1(
        data_completeness_complete=metrics.data_completeness_complete,
        volatility_survival_ratio=metrics.volatility_survival_ratio,
        sequence_survival_ratio=metrics.sequence_survival_ratio,
        drawdown_survival_ratio=metrics.drawdown_survival_ratio,
        liquidation_buffer_ratio=metrics.liquidation_buffer_ratio,
    )


__all__ = [
    "SURVIVAL_ASSESSMENT_LAYER_VERSION",
    "SURVIVAL_ASSESSMENT_POLICY_VERSION",
    "DirectionalAssessmentRefV1",
    "SurvivalAssessmentInputV1",
    "SurvivalAssessmentPolicyV1",
    "SurvivalAssessmentStatus",
    "SurvivalBlockedReason",
    "SurvivalCostInputsV1",
    "SurvivalHardFailReason",
    "SurvivalMetricInputsV1",
    "SurvivalResultV1",
    "SurvivalSubcheckResultV1",
    "SurvivalSubcheckStatus",
    "aggregate_survival_status",
    "compute_expected_roundtrip_cost",
    "compute_net_expected_edge",
    "compute_survival_result_semantic_digest",
    "directional_assessment_ref_from_assessment",
    "evaluate_survival_assessment_v1",
    "mirror_price_path_for_short",
    "mirror_survival_metric_inputs_for_short",
    "serialize_survival_result_canonical",
    "validate_survival_assessment_policy",
    "with_computed_survival_result_digest",
]
