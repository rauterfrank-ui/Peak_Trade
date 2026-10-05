"""Assemble whole_system_proof_manifest.json."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.peak_trade_whole_system_proof_harness_v1.constants_v1 import (
    MANIFEST_SCHEMA_VERSION,
)


def build_whole_system_proof_manifest_v1(ctx: Mapping[str, Any]) -> dict[str, Any]:
    readiness = ctx.get("readiness", {})
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "AUTHORITY": "NONE",
        "baseline": ctx.get("baseline"),
        "operation": ctx.get("operation"),
        "launcher": ctx.get("launcher"),
        "terminal_boundary": ctx.get("terminal_boundary"),
        "discovered_components": ctx.get("discovered_components"),
        "discovered_edges": ctx.get("discovered_edges"),
        "required_components": ctx.get("required_components"),
        "required_edges": ctx.get("required_edges"),
        "conditional_components": ctx.get("conditional_components", []),
        "conditional_edges": ctx.get("conditional_edges", []),
        "excluded_components": ctx.get("excluded_components"),
        "static_proof": ctx.get("static_proof"),
        "runtime_proof": ctx.get("runtime_proof"),
        "ghv_proof": ctx.get("ghv_proof"),
        "config_dependencies": ctx.get("config_dependencies"),
        "state_dependencies": ctx.get("state_dependencies"),
        "persistence_dependencies": ctx.get("persistence_dependencies"),
        "authority_dependencies": ctx.get("authority_dependencies"),
        "safety_dependencies": ctx.get("safety_dependencies"),
        "governance_dependencies": ctx.get("governance_dependencies"),
        "provenance_dependencies": ctx.get("provenance_dependencies"),
        "node_coverage": ctx.get("node_coverage"),
        "edge_coverage": ctx.get("edge_coverage"),
        "unknowns": ctx.get("unknowns"),
        "conflicts": ctx.get("conflicts"),
        "violations": ctx.get("violations"),
        "fixpoint": ctx.get("fixpoint"),
        "current_operational_setting": ctx.get("current_operational_setting"),
        "minimal_required_setting": ctx.get("minimal_required_setting"),
        "setting_delta": ctx.get("setting_delta"),
        "runtime_transitions": ctx.get("runtime_transitions", []),
        "operator_actions": ctx.get("operator_actions", []),
        "counterfactual_repairs": ctx.get("counterfactual_repairs"),
        "readiness": readiness,
        "LIVE_ONLY_UNPROVEN": ctx.get("live_only_unproven", []),
        "WHOLE_SYSTEM_PROOF_HARNESS_READY": readiness.get("WHOLE_SYSTEM_PROOF_HARNESS_READY"),
        "CURRENT_READY": readiness.get("CURRENT_READY"),
    }
