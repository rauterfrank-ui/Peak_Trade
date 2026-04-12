"""
Transfer / treasury ambiguity observation for Ops Cockpit — read-only.

Aggregates **local** signals only (guard/treasury label, balance semantics, stale
rolls, exposure stale flag, process env role for treasury policy context). Does
**not** query exchanges or assert transfer completion. Does not enforce gates.

Fail-safe: missing or ambiguous inputs → ``unknown`` / ``no_signal``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

READER_SCHEMA_VERSION = "transfer_ambiguity_reader/v0"
RUNBOOK_REF = "RUNBOOK_PILOT_INCIDENT_TRANSFER_AMBIGUITY"


def build_transfer_ambiguity_state(
    *,
    guard_state: Dict[str, Any],
    stale_state: Dict[str, Any],
    balance_semantics_state: Dict[str, Any],
    exposure_state: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build ``transfer_ambiguity_state`` for the Ops Cockpit payload (read-only).

    ``operator_attention_hint`` is an observation-only nudge; it does not lock
    or unlock trading.
    """
    provenance: Dict[str, Any] = {
        "reader_schema_version": READER_SCHEMA_VERSION,
        "treasury_separation": guard_state.get("treasury_separation"),
        "balance_stale_signal": stale_state.get("balance"),
        "balance_semantic_state": balance_semantics_state.get("balance_semantic_state"),
        "exposure_stale_flag": exposure_state.get("stale"),
        "pt_key_role": None,
    }
    try:
        from src.ops.treasury_separation_gate import get_key_role

        provenance["pt_key_role"] = get_key_role()
    except Exception as e:
        logger.debug("transfer_ambiguity_reader: get_key_role: %s", e)

    bal_st = str(stale_state.get("balance") or "unknown")
    sem_raw = balance_semantics_state.get("balance_semantic_state")
    sem = str(sem_raw) if sem_raw is not None else ""
    exp_stale = exposure_state.get("stale")
    treasury_sep = str(guard_state.get("treasury_separation") or "unknown")

    data_parts = ["guard_state", "stale_state", "balance_semantics_state", "exposure_state"]
    if provenance.get("pt_key_role") is not None:
        data_parts.append("process_env_pt_key_role")
    data_source = "+".join(data_parts)

    warning = False
    reasons: list[str] = []

    if bal_st in ("blocked", "warn"):
        warning = True
        reasons.append("balance_stale_not_ok")
    if sem in ("balance_semantics_blocked", "balance_semantics_warning"):
        warning = True
        reasons.append("balance_semantics_not_clear")
    if exp_stale is True:
        warning = True
        reasons.append("exposure_snapshot_stale")

    local_unremarkable = (
        sem == "balance_semantics_clear" and bal_st in ("ok", "unknown") and exp_stale is not True
    )

    if warning:
        status = "warning"
        summary = "local_signals_suggest_operator_review_before_relying_on_transfer_posture"
        operator_hint = True
    elif local_unremarkable and treasury_sep == "enforced":
        status = "ok"
        summary = "local_balance_and_exposure_signals_unremarkable_broker_transfer_truth_not_observed_here"
        operator_hint = False
    elif not sem and bal_st == "unknown" and treasury_sep == "unknown":
        status = "no_signal"
        summary = "insufficient_local_signals"
        operator_hint = False
    else:
        status = "unknown"
        summary = "ambiguous_or_partial_local_signals_transfer_truth_not_observed_here"
        operator_hint = bool(exp_stale is True or bal_st == "unknown")

    return {
        "status": status,
        "summary": summary,
        "data_source": data_source,
        "observation_reason": "; ".join(reasons) if reasons else "artifact_observation",
        "runbook_ref": RUNBOOK_REF,
        "provenance": provenance,
        "reader_schema_version": READER_SCHEMA_VERSION,
        "operator_attention_hint": operator_hint,
    }
