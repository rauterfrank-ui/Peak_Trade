"""Typed Full-Core Execution Admission contract.

Single intended join point: halt_at_live_execution_boundary_v1.
Does not read durable FILEGATE StatePersistence.
Does not construct LiveExecutionPort. Does not send wire.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    WIRE_SEND_PERMITTED,
)

EXECUTION_ADMISSION_CONTRACT_VERSION = "v1"
EXECUTION_BOUNDARY_REF = (
    "src.ops.full_core_live_path_composition_root_v1.execution_boundary_v1"
    ".halt_at_live_execution_boundary_v1"
)
RUNTIME_AUTHORITY_EFFECT_NONE = "NONE"

CAPITAL_RISK_MODE_OFFLINE_ALGEBRA = "OFFLINE_ALGEBRA"
CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND = "LIVE_ACCOUNT_BOUND"

PRETRADE_SOURCE_FROZEN_OFFLINE = "FROZEN_OFFLINE_PRETRADE_EVIDENCE"
PRETRADE_SOURCE_FRESH_GET = "FRESH_GET_PER_PRETRADE_DECISION"

ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF = "OFFLINE_FULL_CORE_PROOF"
ADMISSION_CONTEXT_LIVE = "LIVE_ADMISSION"


class PretradeFreshnessStatusV1(str, Enum):
    FROZEN_OFFLINE = "FROZEN_OFFLINE"
    LIVE_FRESH = "LIVE_FRESH"
    MISSING = "MISSING"
    UNKNOWN = "UNKNOWN"


class DurableKillSwitchEvidenceStatusV1(str, Enum):
    TRUSTED_PRESENT = "TRUSTED_PRESENT"
    UNKNOWN_BLOCKED = "UNKNOWN_BLOCKED"
    MISSING = "MISSING"


@dataclass(frozen=True)
class ExecutionAdmissionInputsV1:
    """Caller must inject durable kill-switch evidence. Missing => fail-closed."""

    plan_identity: str
    venue_plan_identity: str
    instrument_identity_ok: bool
    pretrade_admissible: bool
    pretrade_source_kind: str
    pretrade_freshness_status: str
    capital_risk_mode: str
    durable_kill_switch_evidence_status: str
    durable_kill_switch_blocked: Optional[bool]
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    owner_authorization_present: bool
    admission_context: str
    provenance_refs: Tuple[str, ...] = ()
    runtime_authority_effect: str = RUNTIME_AUTHORITY_EFFECT_NONE


@dataclass(frozen=True)
class ExecutionAdmissionDecisionV1:
    admitted: bool
    fail_closed: bool
    reason_codes: Tuple[str, ...]
    execution_boundary_ref: str
    runtime_authority_effect: str = RUNTIME_AUTHORITY_EFFECT_NONE
    contract_version: str = EXECUTION_ADMISSION_CONTRACT_VERSION


def evaluate_execution_admission_v1(
    inputs: ExecutionAdmissionInputsV1,
) -> ExecutionAdmissionDecisionV1:
    """Fail-closed admission. Never a second execution owner."""
    reasons: list[str] = []
    live_context = inputs.admission_context == ADMISSION_CONTEXT_LIVE

    if inputs.runtime_authority_effect != RUNTIME_AUTHORITY_EFFECT_NONE:
        reasons.append("ADMISSION_RUNTIME_AUTHORITY_NOT_NONE")
    if not inputs.instrument_identity_ok:
        reasons.append("INSTRUMENT_IDENTITY_MISMATCH")
    if not inputs.owner_authorization_present:
        reasons.append("MISSING_OWNER_AUTHORIZATION")
    if inputs.live_enabled is not True:
        reasons.append("LIVE_ENABLED_FALSE")
    if inputs.live_armed is not True:
        reasons.append("LIVE_ARMED_FALSE")
    if inputs.wire_send_permitted is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if LIVE_ENABLED is True or inputs.live_enabled is True:
        reasons.append("STANDING_OR_INPUT_LIVE_ENABLED")
    if LIVE_ARMED is True or inputs.live_armed is True:
        reasons.append("STANDING_OR_INPUT_LIVE_ARMED")
    if WIRE_SEND_PERMITTED is True or inputs.wire_send_permitted is True:
        reasons.append("STANDING_OR_INPUT_WIRE_SEND_PERMITTED")

    ks_status = str(inputs.durable_kill_switch_evidence_status or "").strip()
    if ks_status in {
        DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value,
        DurableKillSwitchEvidenceStatusV1.MISSING.value,
        "",
    }:
        reasons.append("DURABLE_FILEGATE_EVIDENCE_MISSING")
        reasons.append("DURABLE_FILEGATE_UNKNOWN_BLOCKED")
    elif ks_status != DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value:
        reasons.append("DURABLE_FILEGATE_EVIDENCE_MISSING")
        reasons.append("DURABLE_FILEGATE_UNKNOWN_BLOCKED")
    if inputs.durable_kill_switch_blocked is not False:
        reasons.append("DURABLE_KILL_SWITCH_BLOCKED_OR_UNTRUSTED")
    if inputs.durable_kill_switch_blocked is True:
        reasons.append("DURABLE_FILEGATE_BLOCKS_TRADING")

    freshness = str(inputs.pretrade_freshness_status or "").strip()
    source_kind = str(inputs.pretrade_source_kind or "").strip()
    if freshness in {
        PretradeFreshnessStatusV1.MISSING.value,
        PretradeFreshnessStatusV1.UNKNOWN.value,
        "",
    }:
        reasons.append("PRETRADE_FRESHNESS_MISSING")
    if source_kind == PRETRADE_SOURCE_FROZEN_OFFLINE or freshness == (
        PretradeFreshnessStatusV1.FROZEN_OFFLINE.value
    ):
        reasons.append("FROZEN_OFFLINE_PRETRADE_NOT_LIVE_FRESH")
    if source_kind == PRETRADE_SOURCE_FRESH_GET:
        reasons.append("FRESH_PRETRADE_GET_NOT_IMPLEMENTED")
    if not inputs.pretrade_admissible:
        reasons.append("PRETRADE_NOT_ADMISSIBLE")

    mode = str(inputs.capital_risk_mode or "").strip()
    if mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
        reasons.append("CAPITAL_RISK_MODE_NOT_LIVE_ACCOUNT_BOUND")
    if mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA:
        reasons.append("OFFLINE_ALGEBRA_NOT_LIVE_CAPITAL_AUTHORITY")

    if live_context:
        if freshness != PretradeFreshnessStatusV1.LIVE_FRESH.value:
            reasons.append("FROZEN_PRETRADE_LIVE_ADMISSION_DENIED")
        if mode != CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND:
            reasons.append("OFFLINE_ALGEBRA_LIVE_ADMISSION_DENIED")
        if source_kind != PRETRADE_SOURCE_FRESH_GET:
            reasons.append("LIVE_ADMISSION_REQUIRES_FRESH_GET_PRETRADE")

    unique = tuple(dict.fromkeys(reasons))
    # Standing package constants and missing FILEGATE keep admission closed.
    admitted = False
    return ExecutionAdmissionDecisionV1(
        admitted=admitted,
        fail_closed=True,
        reason_codes=unique if unique else ("EXECUTION_ADMISSION_FAIL_CLOSED",),
        execution_boundary_ref=EXECUTION_BOUNDARY_REF,
        runtime_authority_effect=RUNTIME_AUTHORITY_EFFECT_NONE,
    )


def default_untrusted_filegate_inputs_v1(
    *,
    plan_identity: str,
    venue_plan_identity: str,
    instrument_identity_ok: bool,
    pretrade_admissible: bool,
    pretrade_source_kind: str,
    pretrade_freshness_status: str,
    capital_risk_mode: str,
    owner_authorization_present: bool,
    admission_context: str,
    provenance_refs: Tuple[str, ...] = (),
) -> ExecutionAdmissionInputsV1:
    """Current Full-Core caller: FILEGATE evidence is not read; inject UNKNOWN_BLOCKED."""
    return ExecutionAdmissionInputsV1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=pretrade_source_kind,
        pretrade_freshness_status=pretrade_freshness_status,
        capital_risk_mode=capital_risk_mode,
        durable_kill_switch_evidence_status=(
            DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value
        ),
        durable_kill_switch_blocked=None,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        owner_authorization_present=owner_authorization_present,
        admission_context=admission_context,
        provenance_refs=provenance_refs + (OFFLINE_BOUNDARY_ROLE,),
    )
