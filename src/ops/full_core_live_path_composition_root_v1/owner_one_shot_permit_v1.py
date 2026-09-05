"""Typed Full-Core OWNER_ONE_SHOT permit seam. Offline. No wire. No GET.

Single existing authority: FullCoreLivePathInputV1.owner_go, whose bound
identity is OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1. This module does not
introduce a second token source, does not consume the token, does not arm
Live, and does not treat canary OWNER_GO_EXECUTE as Full-Core authority.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    OWNER_ONE_SHOT_PERMIT_TOKEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.durable_filegate_join_v1 import (
    join_durable_filegate_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ExecutionAdmissionInputsV1,
    OwnerOneShotPermitStatusV1,
)

JOIN_SEAM_ID = "FULL_CORE_OWNER_ONE_SHOT_TYPED_PERMIT_SEAM_V1"
OWNER_ONE_SHOT_AUTHORITY = "FullCoreLivePathInputV1.owner_go"
CONSUMPTION_SEMANTICS = "NOT_IN_EXISTING_FULL_CORE_CONTRACT"
REUSE_SEMANTICS = "NOT_IN_EXISTING_FULL_CORE_CONTRACT"
REPLAY_PROTECTION_PRESENT = False


@dataclass(frozen=True)
class OwnerOneShotPermitEvidenceV1:
    evidence_status: str
    presented_token: Optional[str]
    expected_token: str
    reason_codes: Tuple[str, ...]
    contradictory: bool
    consumed: bool
    live_enabled: bool
    live_armed: bool
    wire_send_permitted: bool
    join_seam_id: str = JOIN_SEAM_ID
    authority: str = OWNER_ONE_SHOT_AUTHORITY
    consumption_semantics: str = CONSUMPTION_SEMANTICS


def evaluate_owner_one_shot_permit_v1(*, owner_go: Any) -> OwnerOneShotPermitEvidenceV1:
    expected = OWNER_ONE_SHOT_PERMIT_TOKEN
    standing_true = LIVE_ENABLED is True or LIVE_ARMED is True or WIRE_SEND_PERMITTED is True
    extra: Tuple[str, ...] = ("STANDING_LIVE_GATE_TRUE",) if standing_true else ()

    if owner_go is None:
        return OwnerOneShotPermitEvidenceV1(
            evidence_status=OwnerOneShotPermitStatusV1.MISSING.value,
            presented_token=None,
            expected_token=expected,
            reason_codes=("OWNER_ONE_SHOT_PERMIT_MISSING", *extra),
            contradictory=False,
            consumed=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    if not isinstance(owner_go, str):
        return OwnerOneShotPermitEvidenceV1(
            evidence_status=OwnerOneShotPermitStatusV1.MALFORMED.value,
            presented_token=None,
            expected_token=expected,
            reason_codes=("OWNER_ONE_SHOT_PERMIT_MALFORMED", *extra),
            contradictory=False,
            consumed=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    if owner_go == "":
        return OwnerOneShotPermitEvidenceV1(
            evidence_status=OwnerOneShotPermitStatusV1.MISSING.value,
            presented_token="",
            expected_token=expected,
            reason_codes=("OWNER_ONE_SHOT_PERMIT_MISSING", *extra),
            contradictory=False,
            consumed=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    if owner_go != owner_go.strip():
        return OwnerOneShotPermitEvidenceV1(
            evidence_status=OwnerOneShotPermitStatusV1.MALFORMED.value,
            presented_token=owner_go,
            expected_token=expected,
            reason_codes=("OWNER_ONE_SHOT_PERMIT_MALFORMED", *extra),
            contradictory=False,
            consumed=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    if owner_go != expected:
        return OwnerOneShotPermitEvidenceV1(
            evidence_status=OwnerOneShotPermitStatusV1.MISMATCH.value,
            presented_token=owner_go,
            expected_token=expected,
            reason_codes=("OWNER_ONE_SHOT_PERMIT_MISMATCH", *extra),
            contradictory=False,
            consumed=False,
            live_enabled=False,
            live_armed=False,
            wire_send_permitted=False,
        )
    return OwnerOneShotPermitEvidenceV1(
        evidence_status=OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value,
        presented_token=owner_go,
        expected_token=expected,
        reason_codes=("OWNER_ONE_SHOT_PERMIT_TRUSTED_PRESENT", JOIN_SEAM_ID, *extra),
        contradictory=False,
        consumed=False,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
    )


def join_owner_one_shot_permit_into_admission_inputs_v1(
    *,
    plan_identity: str,
    venue_plan_identity: str,
    instrument_identity_ok: bool,
    pretrade_admissible: bool,
    pretrade_source_kind: str,
    pretrade_freshness_status: str,
    capital_risk_mode: str,
    owner_go: Any,
    admission_context: str,
    provenance_refs: Tuple[str, ...] = (),
    state_path: Optional[str] = None,
) -> ExecutionAdmissionInputsV1:
    evidence = evaluate_owner_one_shot_permit_v1(owner_go=owner_go)
    trusted = evidence.evidence_status == OwnerOneShotPermitStatusV1.TRUSTED_PRESENT.value
    inputs = join_durable_filegate_into_admission_inputs_v1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=pretrade_source_kind,
        pretrade_freshness_status=pretrade_freshness_status,
        capital_risk_mode=capital_risk_mode,
        owner_authorization_present=trusted,
        admission_context=admission_context,
        provenance_refs=provenance_refs
        + (
            OFFLINE_BOUNDARY_ROLE,
            JOIN_SEAM_ID,
            OWNER_ONE_SHOT_AUTHORITY,
            *evidence.reason_codes,
        ),
        state_path=state_path,
        owner_one_shot_permit_status=evidence.evidence_status,
    )
    return ExecutionAdmissionInputsV1(
        plan_identity=inputs.plan_identity,
        venue_plan_identity=inputs.venue_plan_identity,
        instrument_identity_ok=inputs.instrument_identity_ok,
        pretrade_admissible=inputs.pretrade_admissible,
        pretrade_source_kind=inputs.pretrade_source_kind,
        pretrade_freshness_status=inputs.pretrade_freshness_status,
        capital_risk_mode=inputs.capital_risk_mode,
        durable_kill_switch_evidence_status=inputs.durable_kill_switch_evidence_status,
        durable_kill_switch_blocked=inputs.durable_kill_switch_blocked,
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        owner_authorization_present=trusted,
        owner_one_shot_permit_status=evidence.evidence_status,
        admission_context=inputs.admission_context,
        fresh_pretrade_get_status=inputs.fresh_pretrade_get_status,
        provenance_refs=inputs.provenance_refs,
    )
