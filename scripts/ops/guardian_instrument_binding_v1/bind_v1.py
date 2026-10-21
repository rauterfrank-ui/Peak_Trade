"""Bind one registered instrument to its generic adapter. AUTHORITY=NONE.

Missing domain evidence does not call an adapter and does not invent nodes.
Optimization calls stay provisional: bound, not calibrated, not current-validated.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Mapping

from scripts.ops.generic_ghosv_kernel_v1.observe_v1 import run_generic_ghosv_v1
from scripts.ops.guardian_instrument_contract_v1.contract_v1 import build_instrument_registry_v1
from scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1 import run_scoped_causal_graph_v1
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1

Adapter = Callable[..., dict[str, Any]]
_CONTROL_KEYS = frozenset(
    {
        "activation",
        "authority",
        "guardian_ratified",
        "instrument_id",
        "requested_instrument_type",
    }
)


def bind_domain_instrument_v1(
    *,
    instrument_id: str,
    requested_instrument_type: str,
    adapter_kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve one instrument id and call only its matching adapter."""
    registry = build_instrument_registry_v1()
    if registry["status"] != "ACCEPTED":
        return _closed(
            "REJECTED",
            instrument_id=instrument_id,
            reasons=list(registry["reasons"]),
        )
    contract = next(
        (item for item in registry["instruments"] if item["instrument_id"] == instrument_id),
        None,
    )
    if contract is None:
        return _closed(
            "UNKNOWN_INSTRUMENT", instrument_id=instrument_id, reasons=["unknown_instrument"]
        )
    payload = dict(adapter_kwargs or {})
    control_reasons = _control_reasons(payload)
    if control_reasons:
        return _closed(
            "REJECTED",
            instrument_id=instrument_id,
            contract=contract,
            reasons=control_reasons,
        )
    if requested_instrument_type != contract["instrument_type"]:
        return _closed(
            "INSTRUMENT_TYPE_MISMATCH",
            instrument_id=instrument_id,
            contract=contract,
            reasons=["instrument_type_mismatch"],
        )
    if contract["evidence_status"] != "PROVISIONAL_SCOPE_PRESENT":
        return _closed(
            "MISSING_DOMAIN_EVIDENCE",
            instrument_id=instrument_id,
            contract=contract,
            reasons=["missing_domain_evidence"],
        )
    adapter = _adapter_for(str(contract["instrument_type"]))
    call = {key: value for key, value in payload.items() if key not in _CONTROL_KEYS}
    adapter_result = adapter(**call)
    return {
        "status": str(adapter_result.get("status") or "REJECTED"),
        "instrument_id": contract["instrument_id"],
        "instrument_type": contract["instrument_type"],
        "parent_id": contract["parent_id"],
        "display_name": contract["display_name"],
        "adapter": contract["adapter"],
        "adapter_invoked": True,
        "instrument_bound": True,
        "technical_state": "DOMAIN_BOUND",
        "domain_bound": True,
        "domain_calibrated": False,
        "current_validated": False,
        "operationally_ready": False,
        "authority": "NONE",
        "activation": "DISABLED",
        "guardian_ratified": False,
        "coverage_proof": False,
        "causal_closure_proven": False,
        "adapter_result": adapter_result,
        "reasons": [],
    }


def _adapter_for(instrument_type: str) -> Adapter:
    if instrument_type == "DOMAIN_GHV":
        return run_scoped_ghv_v1
    if instrument_type == "DOMAIN_CURRENT_CAUSAL_GRAPH":
        return run_scoped_causal_graph_v1
    if instrument_type == "DOMAIN_GHOSV":
        return run_generic_ghosv_v1
    raise KeyError(instrument_type)


def _control_reasons(payload: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if "activation" in payload and payload["activation"] != "DISABLED":
        reasons.append("activation_rejected")
    if "authority" in payload and payload["authority"] != "NONE":
        reasons.append("authority_rejected")
    if "guardian_ratified" in payload and payload["guardian_ratified"] is not False:
        reasons.append("ratification_rejected")
    return reasons


def _closed(
    status: str,
    *,
    instrument_id: str,
    reasons: list[str],
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = contract or {}
    return {
        "status": status,
        "instrument_id": instrument_id,
        "instrument_type": body.get("instrument_type"),
        "parent_id": body.get("parent_id"),
        "display_name": body.get("display_name"),
        "adapter": body.get("adapter"),
        "adapter_invoked": False,
        "instrument_bound": False,
        "technical_state": "TECHNICALLY_PREPARED" if contract else "UNKNOWN",
        "domain_bound": False,
        "domain_calibrated": False,
        "current_validated": False,
        "operationally_ready": False,
        "authority": "NONE",
        "activation": "DISABLED",
        "guardian_ratified": False,
        "coverage_gap": True,
        "coverage_proof": False,
        "causal_closure_proven": False,
        "adapter_result": None,
        "reasons": list(reasons),
    }
