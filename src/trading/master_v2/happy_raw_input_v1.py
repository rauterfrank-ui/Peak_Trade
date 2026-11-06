# src/trading/master_v2/happy_raw_input_v1.py
"""
Kanonische Roh-Input-Struktur (v1) fuer den Happy-Pfad aus `SCENARIO_HAPPY_LIVE_GATED`.

Nur Mapping aus der Szenario-Matrix — keine Handelslogik. Verwendet von
Input-/Debug-Tests und dem opt-in Dev-Dry-Smoke.
"""

from __future__ import annotations

from typing import Any

from .scenario_matrix_v1 import SCENARIO_HAPPY_LIVE_GATED, get_master_v2_scenario_case_v1


def build_master_v2_happy_scenario_raw_input_v1() -> dict[str, Any]:
    """
    Baut die flache JSON-affine Struktur, die `adapt_inputs_to_master_v2_flow_v1` fuer
    den voll befuellten happy_live_gated-Fall erwartet.
    """
    c = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = c.packet
    if (
        p.universe is None
        or p.doubleplay is None
        or p.scope_envelope is None
        or p.risk_cap is None
        or p.safety is None
    ):
        raise ValueError("happy scenario must include all handoff layers for wire raw input")
    return {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
        "universe": {
            "layer_version": p.universe.layer_version,
            "symbols": list(p.universe.symbols),
        },
        "doubleplay": {
            "layer_version": p.doubleplay.layer_version,
            "resolution": p.doubleplay.resolution,
        },
        "scope_envelope": {
            "layer_version": p.scope_envelope.layer_version,
            "within_envelope": p.scope_envelope.within_envelope,
        },
        "risk_cap": {
            "layer_version": p.risk_cap.layer_version,
            "cap_satisfied": p.risk_cap.cap_satisfied,
        },
        "safety": {
            "layer_version": p.safety.layer_version,
            "safety_decision_allowed": p.safety.safety_decision_allowed,
        },
    }
