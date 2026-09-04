"""Bound LIVE_RESTART_RECONSTRUCTED proof criterion.

Applies the SSOT phrase "Current Live restart reconstruction from
persisted Live state" onto a Peak_Trade durable pre-restart handoff that
is distinct from the accounting venue-GET path. Accounting closure is not
restart reconstruction. Missing handoff facts fail closed.
"""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
    LIVE_RESTART_RECONSTRUCTED_PRODUCER,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_identity_v1 import (
    BOUND_CLORDID,
    BOUND_INSTID,
    BOUND_ORDID,
    BOUND_POS_SIDE,
    TESTNET_RESTART_PROVEN_ENVIRONMENT,
    TESTNET_RESTART_PROVEN_INSTID,
)

ADMISSIBLE_SOURCE_KIND = "GOVERNED_PERSISTED_LIVE_RESTART_HANDOFF"
INJECTED_EVIDENCE_SOURCE_KIND = "GOVERNED_OFFLINE_CONTRACT"
RESTART_PRODUCER = LIVE_RESTART_RECONSTRUCTED_PRODUCER

RESTART_FIELD_CONSTITUENTS: tuple[str, ...] = (
    "LIVE_ACCOUNTING_RECONSTRUCTED",
    "DURABLE_PRE_RESTART_HANDOFF_PRESENT",
    "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH",
    "POST_RESTART_IDENTITY_RECONSTRUCTABLE",
    "IDENTITY_BOUND_HANDOFF_MATCHES_LIVE_SUBMIT",
    "NO_RESUBMIT",
    "NO_SILENT_REINITIALIZATION",
    "ADMISSIBLE_PERSISTED_LIVE_RESTART_HANDOFF_SOURCE",
    "NOT_FIXTURE_TESTNET_OR_SIMULATED",
    "ACCOUNTING_CLOSURE_IS_NOT_RESTART",
)
RESTART_FIELD_CONSTITUENT_COUNT = 10

RESTART_IDENTITY_EQUATION = (
    "reconstructed_handoff.identity = {clOrdId, ordId, instId, posSide, pos} "
    "from durable pre-restart Peak_Trade state, without re-submit and without "
    "silent reinitialization, Decimal-equal to the bound Live submit/fill/position "
    "identity"
)


def classify_restart_handoff_v1(
    *,
    durable_handoff: Mapping[str, Any] | None,
    census: Mapping[str, Any] | None,
) -> dict[str, Any]:
    handoff = dict(durable_handoff or {})
    observed = dict(census or {})
    present = bool(handoff) and bool(observed.get("DURABLE_PRE_RESTART_HANDOFF_PRESENT") is True)
    distinct = bool(
        present and observed.get("HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH") is True
    )
    testnet_same_identity = bool(
        str(observed.get("testnet_restart_instId") or "") == BOUND_INSTID
        and str(observed.get("testnet_restart_clOrdId") or "") == BOUND_CLORDID
    )
    fixture_or_testnet = bool(observed.get("NOT_FIXTURE_TESTNET_OR_SIMULATED") is not True)
    identity_match = False
    silent_reinit = None
    reconstructable = False
    if present and distinct:
        reconstructed_clordid = str(handoff.get("clOrdId") or "").strip()
        reconstructed_ordid = str(handoff.get("ordId") or "").strip()
        reconstructed_instid = str(handoff.get("instId") or "").strip()
        reconstructed_pos_side = str(handoff.get("posSide") or "").strip()
        reconstructed_pos = str(handoff.get("pos") or "").strip()
        identity_match = bool(
            reconstructed_clordid == BOUND_CLORDID
            and reconstructed_ordid == BOUND_ORDID
            and reconstructed_instid == BOUND_INSTID
            and reconstructed_pos_side == BOUND_POS_SIDE
            and reconstructed_pos != ""
        )
        silent_reinit = bool(reconstructed_pos in {"", "0"})
        reconstructable = bool(identity_match and silent_reinit is False)
    epistemic = "DURABLE_LIVE_PRE_RESTART_HANDOFF_ABSENT"
    if fixture_or_testnet:
        epistemic = "FORBIDDEN_OR_TESTNET_SOURCE"
    elif testnet_same_identity:
        epistemic = "TESTNET_RESTART_IS_NOT_LIVE_RESTART"
    elif not present:
        epistemic = "DURABLE_LIVE_PRE_RESTART_HANDOFF_ABSENT"
    elif not distinct:
        epistemic = "HANDOFF_NOT_DISTINCT_FROM_ACCOUNTING_PATH"
    elif reconstructable:
        epistemic = "RECONSTRUCTED"
    else:
        epistemic = "POST_RESTART_IDENTITY_NOT_RECONSTRUCTABLE"
    claim = bool(
        present
        and distinct
        and reconstructable
        and identity_match
        and silent_reinit is False
        and epistemic == "RECONSTRUCTED"
    )
    return {
        "BOUND_ORDID": BOUND_ORDID,
        "BOUND_CLORDID": BOUND_CLORDID,
        "BOUND_INSTID": BOUND_INSTID,
        "BOUND_POS_SIDE": BOUND_POS_SIDE,
        "RESTART_IDENTITY_EQUATION": RESTART_IDENTITY_EQUATION,
        "DURABLE_PRE_RESTART_HANDOFF_PRESENT": present,
        "HANDOFF_DISTINCT_FROM_ACCOUNTING_VENUE_GET_PATH": distinct,
        "POST_RESTART_IDENTITY_RECONSTRUCTABLE": reconstructable,
        "IDENTITY_BOUND_HANDOFF_MATCHES_LIVE_SUBMIT": identity_match,
        "NO_SILENT_REINITIALIZATION": bool(silent_reinit is False) if present else False,
        "TESTNET_RESTART_PROVEN_INSTID": TESTNET_RESTART_PROVEN_INSTID,
        "TESTNET_RESTART_PROVEN_ENVIRONMENT": TESTNET_RESTART_PROVEN_ENVIRONMENT,
        "TESTNET_RESTART_IS_NOT_THIS_FIELD": True,
        "ACCOUNTING_CLOSURE_IS_NOT_RESTART": True,
        "MISSING_NOT_REPLACED_BY_ACCOUNTING": True,
        "EPISTEMIC_CLASS": epistemic,
        "ACTUAL_RESTART_RECONSTRUCTED": claim,
        "census": observed,
        "handoff": handoff if present else {},
    }


def evaluate_live_restart_reconstructed_conjunction_v1(
    *,
    constituent_values: Mapping[str, bool | None],
    source_kind: str,
) -> dict[str, Any]:
    refuse_forbidden_live_source_v1(
        field_name="LIVE_RESTART_RECONSTRUCTED",
        source_kind=source_kind,
    )
    if str(source_kind or "").strip() != ADMISSIBLE_SOURCE_KIND:
        raise Section1114OfflineSurfaceError("INJECTED_EVIDENCE_CANNOT_SATISFY_LIVE_FIELD")
    missing = [name for name in RESTART_FIELD_CONSTITUENTS if name not in constituent_values]
    if missing:
        raise Section1114OfflineSurfaceError(
            "RESTART_FIELD_CONSTITUENT_MISSING:" + ",".join(missing)
        )
    false_required = [
        name for name in RESTART_FIELD_CONSTITUENTS if constituent_values.get(name) is not True
    ]
    claim = not false_required
    return {
        "canonical_definition": LIVE_RESTART_RECONSTRUCTED_CANONICAL_DEFINITION,
        "adjudication": "TRUE_LIVE_RESTART_RECONSTRUCTED" if claim else "FALSE_FAIL_CLOSED",
        "claim_value": claim,
        "constituent_count": RESTART_FIELD_CONSTITUENT_COUNT,
        "false_required": false_required,
        "source_kind": source_kind,
        "admissible_live_source_kind": ADMISSIBLE_SOURCE_KIND,
        "producer": RESTART_PRODUCER,
    }
