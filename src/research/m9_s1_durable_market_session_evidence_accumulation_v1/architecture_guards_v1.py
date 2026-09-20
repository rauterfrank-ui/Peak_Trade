"""Architecture guards for M9-S1 passive evidence accumulation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from research.m9_s1_durable_market_session_evidence_accumulation_v1.constants_v1 import (
    ENFORCEMENT_ENABLED,
    EXTERNAL_EFFECT_AUTHORIZED,
    NUMERIC_MAX_AGE_DECIDED,
    OBSERVATION_ONLY,
    PRODUCTIVE_PARAMETER_MUTATED,
)


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    passive_src = (
        root
        / "src/research/m9_s1_durable_market_session_evidence_accumulation_v1"
        / "passive_accumulation_v1.py"
    ).read_text(encoding="utf-8")
    bridge_src = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")

    if "trading_behavior_mutated = True" in passive_src:
        raise RuntimeError("TRADING_BEHAVIOR_MUTATION_FORBIDDEN")
    if "enforcement_applied=True" in passive_src:
        raise RuntimeError("ENFORCEMENT_APPLIED_FORBIDDEN")
    if "passive_accumulate_from_bridge_cycle_v1" not in bridge_src:
        raise RuntimeError("BRIDGE_MUST_DELEGATE_TO_M9_S1_PASSIVE_ACCUMULATION")

    return {
        "observation_only": OBSERVATION_ONLY,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "enforcement_enabled": ENFORCEMENT_ENABLED,
        "productive_parameter_mutated": PRODUCTIVE_PARAMETER_MUTATED,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "guards_pass": True,
    }
