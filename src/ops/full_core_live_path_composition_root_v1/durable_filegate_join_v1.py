"""Typed Full-Core join of durable FILEGATE evidence. Offline. No wire. No GET.

Single authority: KillSwitchState persisted by StatePersistence, consumed by
``kill_switch_should_block_trading`` / ``resolve_kill_switch_limit_from_state_file``.
This module does not write state, does not arm Live, and does not treat
``PEAK_KILL_SWITCH`` as durable FILEGATE evidence.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    OFFLINE_BOUNDARY_ROLE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    DurableKillSwitchEvidenceStatusV1,
    ExecutionAdmissionInputsV1,
)
from src.ops.gates.risk_gate import (
    canonical_kill_switch_state_path,
    kill_switch_should_block_trading,
    resolve_kill_switch_limit_from_state_file,
)

_KILL_SWITCH_BLOCKING_STATES = frozenset({"KILLED", "RECOVERING"})
_KILL_SWITCH_NON_BLOCKING_STATES = frozenset({"ACTIVE", "DISABLED"})

JOIN_SEAM_ID = "FULL_CORE_DURABLE_FILEGATE_JOIN_SEAM_V1"
JOIN_SOURCE_READER = "src.ops.gates.risk_gate.resolve_kill_switch_limit_from_state_file"
BOOLEAN_READER = "src.ops.gates.risk_gate.kill_switch_should_block_trading"
DURABLE_FILEGATE_AUTHORITY = "kill_switch_should_block_trading+KillSwitchState+StatePersistence"

_VALID_STATES = _KILL_SWITCH_BLOCKING_STATES | _KILL_SWITCH_NON_BLOCKING_STATES


@dataclass(frozen=True)
class DurableFilegateJoinEvidenceV1:
    evidence_status: str
    blocked: Optional[bool]
    state_name: Optional[str]
    state_path: str
    reason_codes: Tuple[str, ...]
    source_reader: str
    boolean_reader_blocked: Optional[bool]
    contradictory: bool
    env_overlay_used_as_durable_evidence: bool
    join_seam_id: str = JOIN_SEAM_ID


def _load_state_payload(path: Path) -> tuple[Optional[Mapping[str, Any]], Tuple[str, ...]]:
    if not path.is_file():
        return None, ("DURABLE_FILEGATE_STATE_FILE_MISSING",)
    try:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None, ("DURABLE_FILEGATE_STATE_UNREADABLE",)
    if not isinstance(payload, dict):
        return None, ("DURABLE_FILEGATE_STATE_NOT_OBJECT",)
    return payload, ()


def _valid_state_name(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    name = raw.strip().upper()
    if name in _VALID_STATES:
        return name
    return None


def _payload_is_contradictory(payload: Mapping[str, Any], resolved_blocked: bool) -> bool:
    primary = _valid_state_name(payload.get("state"))
    if primary is None:
        return True
    primary_blocks = primary in _KILL_SWITCH_BLOCKING_STATES
    if primary_blocks is not resolved_blocked:
        return True
    alias = payload.get("status")
    if alias is not None:
        alias_name = _valid_state_name(alias)
        if alias_name is not None and alias_name != primary:
            return True
    flag = payload.get("kill_switch")
    if isinstance(flag, bool) and flag is not primary_blocks:
        return True
    return False


def read_durable_filegate_join_evidence_v1(
    *,
    state_path: Optional[str] = None,
) -> DurableFilegateJoinEvidenceV1:
    path = Path(state_path or canonical_kill_switch_state_path())
    path_s = str(path)
    payload, load_reasons = _load_state_payload(path)
    resolved = resolve_kill_switch_limit_from_state_file(path_s)
    boolean_blocked = kill_switch_should_block_trading(explicit_active=False)

    if not path.is_file():
        return DurableFilegateJoinEvidenceV1(
            evidence_status=DurableKillSwitchEvidenceStatusV1.MISSING.value,
            blocked=None,
            state_name=None,
            state_path=path_s,
            reason_codes=("DURABLE_FILEGATE_EVIDENCE_MISSING", *load_reasons),
            source_reader=JOIN_SOURCE_READER,
            boolean_reader_blocked=boolean_blocked,
            contradictory=False,
            env_overlay_used_as_durable_evidence=False,
        )

    if payload is None or resolved is None:
        return DurableFilegateJoinEvidenceV1(
            evidence_status=DurableKillSwitchEvidenceStatusV1.UNKNOWN_BLOCKED.value,
            blocked=None,
            state_name=None,
            state_path=path_s,
            reason_codes=(
                "DURABLE_FILEGATE_UNKNOWN_BLOCKED",
                *(load_reasons or ("DURABLE_FILEGATE_STATE_INVALID",)),
            ),
            source_reader=JOIN_SOURCE_READER,
            boolean_reader_blocked=boolean_blocked,
            contradictory=False,
            env_overlay_used_as_durable_evidence=False,
        )

    state_name = _valid_state_name(payload.get("state"))
    contradictory = _payload_is_contradictory(payload, resolved)
    canonical = canonical_kill_switch_state_path()
    if str(Path(path_s)) == str(Path(canonical)) and boolean_blocked is not resolved:
        contradictory = True
    if contradictory or state_name is None:
        return DurableFilegateJoinEvidenceV1(
            evidence_status=DurableKillSwitchEvidenceStatusV1.CONTRADICTORY.value,
            blocked=None,
            state_name=state_name,
            state_path=path_s,
            reason_codes=("DURABLE_FILEGATE_CONTRADICTORY",),
            source_reader=JOIN_SOURCE_READER,
            boolean_reader_blocked=boolean_blocked,
            contradictory=True,
            env_overlay_used_as_durable_evidence=False,
        )

    return DurableFilegateJoinEvidenceV1(
        evidence_status=DurableKillSwitchEvidenceStatusV1.TRUSTED_PRESENT.value,
        blocked=resolved,
        state_name=state_name,
        state_path=path_s,
        reason_codes=("DURABLE_FILEGATE_TRUSTED_PRESENT", BOOLEAN_READER),
        source_reader=JOIN_SOURCE_READER,
        boolean_reader_blocked=boolean_blocked,
        contradictory=False,
        env_overlay_used_as_durable_evidence=False,
    )


def join_durable_filegate_into_admission_inputs_v1(
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
    state_path: Optional[str] = None,
    owner_one_shot_permit_status: str = "MISSING",
) -> ExecutionAdmissionInputsV1:
    evidence = read_durable_filegate_join_evidence_v1(state_path=state_path)
    return ExecutionAdmissionInputsV1(
        plan_identity=plan_identity,
        venue_plan_identity=venue_plan_identity,
        instrument_identity_ok=instrument_identity_ok,
        pretrade_admissible=pretrade_admissible,
        pretrade_source_kind=pretrade_source_kind,
        pretrade_freshness_status=pretrade_freshness_status,
        capital_risk_mode=capital_risk_mode,
        durable_kill_switch_evidence_status=evidence.evidence_status,
        durable_kill_switch_blocked=evidence.blocked,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        owner_authorization_present=owner_authorization_present,
        owner_one_shot_permit_status=owner_one_shot_permit_status,
        admission_context=admission_context,
        provenance_refs=provenance_refs
        + (
            OFFLINE_BOUNDARY_ROLE,
            JOIN_SEAM_ID,
            DURABLE_FILEGATE_AUTHORITY,
            *evidence.reason_codes,
        ),
    )
