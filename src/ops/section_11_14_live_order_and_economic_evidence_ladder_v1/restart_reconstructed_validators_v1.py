"""Validators for the bound LIVE_RESTART_RECONSTRUCTED handoff contract.

Fixture-only evaluation of identity, completeness, temporal order, stale
state, corrupt pos, accounting-only artifacts, and post-restart-only
evidence. Does not GET. Does not POST. Does not execute a restart.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_OWNER_REUSE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
    VENUE_GET_ARTIFACT_NAMES,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_FILL_SZ,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
)


def parse_handoff_pos_v1(raw: object) -> Decimal | None:
    text = str(raw or "").strip()
    if text == "":
        return None
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def validate_handoff_completeness_v1(handoff: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(handoff or {})
    missing = [
        name for name in REQUIRED_HANDOFF_FIELDS if str(payload.get(name) or "").strip() == ""
    ]
    pos = parse_handoff_pos_v1(payload.get("pos"))
    corrupt = bool(str(payload.get("pos") or "").strip() != "" and pos is None)
    complete = not missing and pos is not None and corrupt is False
    return {
        "DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "COMPLETE": complete,
        "MISSING_FIELDS": missing,
        "CORRUPT_POS": corrupt,
        "POS_DECIMAL": str(pos) if pos is not None else None,
        "REASON": (
            "COMPLETE"
            if complete
            else ("CORRUPT_POS" if corrupt else "MISSING_REQUIRED_HANDOFF_FIELDS")
        ),
    }


def validate_handoff_identity_binding_v1(handoff: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = dict(handoff or {})
    pos = parse_handoff_pos_v1(payload.get("pos"))
    fill_sz = parse_handoff_pos_v1(BOUND_FILL_SZ)
    identity_match = bool(
        str(payload.get("clOrdId") or "").strip() == BOUND_CLORDID
        and str(payload.get("ordId") or "").strip() == BOUND_ORDID
        and str(payload.get("instId") or "").strip() == BOUND_INSTID
        and str(payload.get("posSide") or "").strip() == BOUND_POS_SIDE
        and pos is not None
    )
    silent_reinit = bool(pos is None or pos == 0)
    nonzero_fill_requires_nonzero_pos = bool(fill_sz is not None and fill_sz != 0)
    stale_or_mismatch = bool(payload) and identity_match is False
    return {
        "IDENTITY_BOUND": identity_match,
        "NO_SILENT_REINITIALIZATION": bool(silent_reinit is False),
        "NONZERO_FILL_REQUIRES_NONZERO_POS": nonzero_fill_requires_nonzero_pos,
        "STALE_OR_IDENTITY_MISMATCH": stale_or_mismatch,
        "REASON": (
            "IDENTITY_BOUND"
            if identity_match and silent_reinit is False
            else (
                "SILENT_REINITIALIZATION"
                if identity_match and silent_reinit
                else "IDENTITY_MISMATCH"
            )
        ),
    }


def validate_temporal_order_v1(
    *,
    handoff: Mapping[str, Any] | None,
    restart_at_utc: str | None = None,
) -> dict[str, Any]:
    payload = dict(handoff or {})
    captured = str(payload.get("captured_at_utc") or payload.get("written_at_utc") or "").strip()
    restart_at = str(restart_at_utc or "").strip()
    if restart_at and not captured:
        return {
            "TEMPORAL_OK": False,
            "REASON": "PRE_RESTART_TIMESTAMP_MISSING",
            "captured_at_utc": captured,
            "restart_at_utc": restart_at,
        }
    if restart_at and captured and captured >= restart_at:
        return {
            "TEMPORAL_OK": False,
            "REASON": "TEMPORAL_INVERSION_POST_RESTART_ONLY",
            "captured_at_utc": captured,
            "restart_at_utc": restart_at,
        }
    return {
        "TEMPORAL_OK": True,
        "REASON": "NO_INVERSION" if restart_at else "NO_RESTART_TIMESTAMP_PRESENT",
        "captured_at_utc": captured,
        "restart_at_utc": restart_at,
    }


def classify_artifact_role_v1(*, path: str) -> str:
    name = Path(path).name
    normalized = str(path).replace("\\", "/")
    if name in VENUE_GET_ARTIFACT_NAMES or name.startswith("GET_"):
        return "ACCOUNTING_VENUE_GET_NOT_RESTART_HANDOFF"
    if "deterministic_decision_outcome" in normalized or "ddo_" in normalized.lower():
        return "DDO_LEDGER_NOT_THIS_FIELD"
    if "mutation_critical_control_state" in normalized or "/wal_" in normalized:
        return "A1_WAL_NOT_THIS_FIELD"
    if "kill_switch" in normalized or "filegate" in normalized.lower():
        return "FILEGATE_KILL_SWITCH_NOT_THIS_FIELD"
    if "sidestate" in normalized.lower() or "side_state" in normalized.lower():
        return "CAP_72_SIDESTATE_NOT_THIS_FIELD"
    if "durable_state" in normalized and (
        "section_11_12" in normalized or "testnet" in normalized.lower()
    ):
        return "TESTNET_DURABLE_STATE_NOT_THIS_FIELD"
    if "phase_9_2" in normalized or "capability_phase_9_2" in normalized:
        return "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD"
    if "section_11_14_live_order_and_economic_evidence_ladder_v1" in normalized:
        if "durable_state" in normalized or "pre_restart" in name:
            return "CANDIDATE_DURABLE_HANDOFF"
        return "SECTION_11_14_EVIDENCE_PACK_NOT_CONTROL_HANDOFF"
    if "durable_state" in normalized or "pre_restart" in name:
        return "CANDIDATE_DURABLE_HANDOFF"
    return "NOT_A_RESTART_HANDOFF"


def refuse_retroactive_handoff_synthesis_v1(
    *,
    handoff: Mapping[str, Any] | None,
    source_kind: str,
    source_path: str | None = None,
    accounting_only: bool = False,
    synthetic_from_venue_get: bool = False,
    timestamp_backfill: bool = False,
    claimed_owner: str | None = None,
    contemporaneous_capture_proven: bool | None = None,
    provenance_class: str | None = None,
) -> dict[str, Any]:
    payload = dict(handoff or {})
    provenance = str(
        provenance_class or payload.get("provenance_class") or payload.get("PROVENANCE_CLASS") or ""
    ).strip()
    contemporaneous = contemporaneous_capture_proven
    if contemporaneous is None:
        contemporaneous = bool(
            payload.get("contemporaneous_capture_proven") is True
            or payload.get("CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED") is True
        )
    owner = str(claimed_owner or payload.get("claimed_owner") or "").strip()
    role = classify_artifact_role_v1(path=str(source_path or ""))
    identity = validate_handoff_identity_binding_v1(payload)
    forbidden_owner = owner in FORBIDDEN_OWNER_REUSE
    venue_copy = bool(
        synthetic_from_venue_get
        or role == "ACCOUNTING_VENUE_GET_NOT_RESTART_HANDOFF"
        or provenance == "VENUE_GET_COPY"
    )
    pack_reclass = bool(
        role == "SECTION_11_14_EVIDENCE_PACK_NOT_CONTROL_HANDOFF"
        or provenance == "EVIDENCE_PACK_RECLASSIFIED_AS_CONTROL_HANDOFF"
    )
    forbidden_provenance = provenance in FORBIDDEN_PROVENANCE_CLASSES
    reason = "SYNTHESIS_REFUSED"
    if accounting_only or provenance == "ACCOUNTING_ONLY":
        reason = "ACCOUNTING_ONLY_IS_NOT_RESTART"
    elif venue_copy:
        reason = "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF"
    elif timestamp_backfill or provenance == "TIMESTAMP_BACKFILL":
        reason = "NO_TIMESTAMP_BACKFILL"
    elif pack_reclass:
        reason = "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF"
    elif forbidden_owner:
        reason = "FORBIDDEN_OWNER_REUSE"
    elif forbidden_provenance or provenance == "RETROACTIVE_SYNTHESIS":
        reason = "NO_SYNTHETIC_PRE_RESTART_PROVENANCE"
    elif identity["IDENTITY_BOUND"] is True and contemporaneous is not True:
        reason = "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE"
    elif contemporaneous is not True:
        reason = "NO_CONTEMPORANEOUS_PROVENANCE"
    elif provenance and provenance != CONTEMPORANEOUS_PROVENANCE_CLASS:
        reason = "NO_SYNTHETIC_PRE_RESTART_PROVENANCE"
    allowed = bool(
        accounting_only is False
        and venue_copy is False
        and timestamp_backfill is False
        and pack_reclass is False
        and forbidden_owner is False
        and forbidden_provenance is False
        and contemporaneous is True
        and (not provenance or provenance == CONTEMPORANEOUS_PROVENANCE_CLASS)
        and str(source_kind or "").strip() == "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF"
    )
    if allowed:
        reason = "CONTEMPORANEOUS_PROVENANCE_ADMISSIBLE"
    return {
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
        "SYNTHESIS_ALLOWED": allowed,
        "REASON": reason,
        "ACCOUNTING_ONLY_IS_NOT_RESTART": True,
        "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF": True,
        "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE": True,
        "NO_TIMESTAMP_BACKFILL": True,
        "NO_SYNTHETIC_PRE_RESTART_PROVENANCE": True,
        "NO_RECLASSIFICATION_OF_EVIDENCE_PACK_AS_CONTROL_HANDOFF": True,
        "CONTEMPORANEOUS_CAPTURE_PROVEN": contemporaneous,
        "PROVENANCE_CLASS": provenance or None,
        "CLAIMED_OWNER": owner or "NONE",
        "ARTIFACT_ROLE": role,
        "IDENTITY_BOUND_WITHOUT_CONTEMPORANEOUS_PROVENANCE": bool(
            identity["IDENTITY_BOUND"] is True and contemporaneous is not True
        ),
    }


def evaluate_handoff_proof_bundle_v1(
    *,
    handoff: Mapping[str, Any] | None,
    source_kind: str,
    source_path: str | None = None,
    restart_at_utc: str | None = None,
    accounting_only: bool = False,
    synthetic_from_venue_get: bool = False,
    timestamp_backfill: bool = False,
    claimed_owner: str | None = None,
    contemporaneous_capture_proven: bool | None = None,
    provenance_class: str | None = None,
) -> dict[str, Any]:
    completeness = validate_handoff_completeness_v1(handoff)
    identity = validate_handoff_identity_binding_v1(handoff)
    temporal = validate_temporal_order_v1(handoff=handoff, restart_at_utc=restart_at_utc)
    role = classify_artifact_role_v1(path=str(source_path or ""))
    synthesis = refuse_retroactive_handoff_synthesis_v1(
        handoff=handoff,
        source_kind=source_kind,
        source_path=source_path,
        accounting_only=accounting_only,
        synthetic_from_venue_get=synthetic_from_venue_get,
        timestamp_backfill=timestamp_backfill,
        claimed_owner=claimed_owner,
        contemporaneous_capture_proven=contemporaneous_capture_proven,
        provenance_class=provenance_class,
    )
    distinct = bool(
        accounting_only is False
        and role
        not in {
            "ACCOUNTING_VENUE_GET_NOT_RESTART_HANDOFF",
            "TESTNET_DURABLE_STATE_NOT_THIS_FIELD",
            "PHASE_9_2_MD_OR_FIXTURE_NOT_THIS_FIELD",
            "DDO_LEDGER_NOT_THIS_FIELD",
            "A1_WAL_NOT_THIS_FIELD",
            "FILEGATE_KILL_SWITCH_NOT_THIS_FIELD",
            "CAP_72_SIDESTATE_NOT_THIS_FIELD",
            "SECTION_11_14_EVIDENCE_PACK_NOT_CONTROL_HANDOFF",
            "NOT_A_RESTART_HANDOFF",
        }
    )
    admissible = str(source_kind or "").strip() == "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF"
    claim = bool(
        admissible
        and completeness["COMPLETE"] is True
        and identity["IDENTITY_BOUND"] is True
        and identity["NO_SILENT_REINITIALIZATION"] is True
        and temporal["TEMPORAL_OK"] is True
        and distinct is True
        and accounting_only is False
        and synthesis["SYNTHESIS_ALLOWED"] is True
    )
    reason = "RECONSTRUCTED" if claim else "FAIL_CLOSED"
    if accounting_only or role == "ACCOUNTING_VENUE_GET_NOT_RESTART_HANDOFF":
        reason = "ACCOUNTING_ONLY_IS_NOT_RESTART"
    elif not admissible:
        reason = "SOURCE_KIND_NOT_ADMISSIBLE_LIVE_HANDOFF"
    elif completeness["CORRUPT_POS"] is True:
        reason = "CORRUPT_HANDOFF_POS"
    elif completeness["COMPLETE"] is not True:
        reason = "MISSING_DURABLE_STATE"
    elif identity["STALE_OR_IDENTITY_MISMATCH"] is True:
        reason = "IDENTITY_MISMATCH_OR_STALE"
    elif identity["NO_SILENT_REINITIALIZATION"] is not True:
        reason = "SILENT_REINITIALIZATION"
    elif temporal["TEMPORAL_OK"] is not True:
        reason = str(temporal["REASON"])
    elif distinct is not True:
        reason = "HANDOFF_NOT_DISTINCT_FROM_ACCOUNTING_OR_NON_LIVE"
    elif synthesis["SYNTHESIS_ALLOWED"] is not True:
        reason = str(synthesis["REASON"])
    return {
        "claim_value": claim,
        "REASON": reason,
        "completeness": completeness,
        "identity": identity,
        "temporal": temporal,
        "artifact_role": role,
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": distinct,
        "ADMISSIBLE_SOURCE": admissible,
        "ACCOUNTING_ONLY": accounting_only,
        "RETROACTIVE_SYNTHESIS": synthesis,
        "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": False,
    }
