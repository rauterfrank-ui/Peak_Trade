"""Validate one caller-supplied domain scope manifest. AUTHORITY=NONE.

The only productive dependency is WP-A0. This module does not read git, does
not write repository evidence, and does not derive scope nodes.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

from scripts.ops.guardian_domain_scope_manifest_v1.constants_v1 import (
    FORBIDDEN_CLAIM_KEYS,
    MANIFEST_FIELDS,
    SCHEMA_ID,
    SCHEMA_VERSION,
    STATUS_BINDER_RESULT_REJECTED,
    STATUS_INVALID_MANIFEST,
    STATUS_MANIFEST_RECORDED,
    TOOL_SLOT_NAMES,
    TOOL_SLOT_STATUSES,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    EXECUTION_AUTHORITY,
    GUARDIAN_IDENTITY,
    LIVE_GATE,
    NETWORK_ACCESS,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID as WP_A0_SCHEMA_ID,
    SCOPE_FIELDS,
    STATUS_ACCEPTED,
    STATUS_INPUT_SOURCE_STALE,
    STATUS_INVALID_PROVENANCE,
    STATUS_INVALID_SCOPE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_CONFLICT,
    STATUS_SCOPE_EMPTY,
    TRADING_AUTHORITY,
)

Binder = Callable[..., Any]

_PASSTHROUGH_STATUSES = frozenset(
    {
        STATUS_INPUT_SOURCE_STALE,
        STATUS_INVALID_PROVENANCE,
        STATUS_INVALID_SCOPE,
        STATUS_PIN_MISMATCH,
        STATUS_SCOPE_CONFLICT,
        STATUS_SCOPE_EMPTY,
    }
)


def validate_guardian_domain_scope_manifest_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    manifest: Mapping[str, Any],
    binder: Binder | None = None,
) -> dict[str, Any]:
    """Record one manifest, or return one fail-closed status."""
    if not isinstance(manifest, Mapping):
        return _output(
            status=STATUS_INVALID_MANIFEST,
            manifest_id="",
            reasons=["manifest_not_object"],
            wp_a0_invoked=False,
            wp_a0_status="",
            wp_a0_result={},
            tool_slots={},
            allowed_nodes=[],
            exclusions=[],
            unassigned=[],
            scope_coverage_gap=False,
            graph_coverage_gap=False,
            observation_coverage_gap=False,
            coverage_gap=True,
        )

    missing = [f"manifest_missing:{field}" for field in MANIFEST_FIELDS if field not in manifest]
    if missing:
        return _output(
            status=STATUS_INVALID_MANIFEST,
            manifest_id=_manifest_id(manifest),
            reasons=sorted(missing),
            wp_a0_invoked=False,
            wp_a0_status="",
            wp_a0_result={},
            tool_slots={},
            allowed_nodes=[],
            exclusions=[],
            unassigned=[],
            scope_coverage_gap=False,
            graph_coverage_gap=False,
            observation_coverage_gap=False,
            coverage_gap=True,
        )

    bind = bind_pin_and_scope_v1 if binder is None else binder
    raw = bind(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=manifest["declared_commit_sha"],
        declared_tree_sha=manifest["declared_tree_sha"],
        provenance=manifest["provenance"],
        scope=manifest["scope"],
    )
    if not isinstance(raw, Mapping):
        return _output(
            status=STATUS_BINDER_RESULT_REJECTED,
            manifest_id=_manifest_id(manifest),
            reasons=["binder_result_not_object"],
            wp_a0_invoked=True,
            wp_a0_status="",
            wp_a0_result={},
            tool_slots=_echo_slots(manifest.get("tool_slots")),
            allowed_nodes=[],
            exclusions=[],
            unassigned=[],
            scope_coverage_gap=False,
            graph_coverage_gap=False,
            observation_coverage_gap=False,
            coverage_gap=True,
        )

    stored = deepcopy(dict(raw))
    wp_a0_status = stored.get("status")
    if wp_a0_status != STATUS_ACCEPTED:
        if wp_a0_status not in _PASSTHROUGH_STATUSES:
            return _from_binding(
                stored,
                manifest,
                status=STATUS_BINDER_RESULT_REJECTED,
                reasons=["binder_status_rejected"],
            )
        return _from_binding(
            stored,
            manifest,
            status=str(wp_a0_status),
            reasons=_copied_reasons(stored),
        )

    local_reasons = _local_reasons(manifest)
    if local_reasons:
        return _from_binding(
            stored,
            manifest,
            status=STATUS_INVALID_MANIFEST,
            reasons=local_reasons,
            tool_slots=_parsed_slots_or_echo(manifest.get("tool_slots")),
        )

    binder_reasons = _binder_reasons(
        stored,
        manifest,
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
    )
    if binder_reasons:
        return _from_binding(
            stored,
            manifest,
            status=STATUS_BINDER_RESULT_REJECTED,
            reasons=binder_reasons,
        )

    return _from_binding(
        stored,
        manifest,
        status=STATUS_MANIFEST_RECORDED,
        reasons=[],
    )


def _local_reasons(manifest: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in sorted(set(manifest) - set(MANIFEST_FIELDS)):
        if key in FORBIDDEN_CLAIM_KEYS:
            reasons.append(f"forbidden_claim:{key}")
        else:
            reasons.append(f"manifest_extra:{key}")
    manifest_id = manifest.get("manifest_id")
    if not isinstance(manifest_id, str) or manifest_id.strip() == "":
        reasons.append("manifest_id_malformed")
    slot_reasons, _parsed = _parse_tool_slots(manifest.get("tool_slots"))
    reasons.extend(slot_reasons)
    return sorted(reasons)


def _parse_tool_slots(raw: Any) -> tuple[list[str], dict[str, str]]:
    if not isinstance(raw, Mapping):
        return ["tool_slots_not_object"], {}
    reasons = [f"tool_slot_extra:{name}" for name in sorted(set(raw) - set(TOOL_SLOT_NAMES))]
    parsed: dict[str, str] = {}
    for name in TOOL_SLOT_NAMES:
        if name not in raw:
            reasons.append(f"tool_slot_missing:{name}")
            continue
        value = raw[name]
        if isinstance(value, (Mapping, list)):
            reasons.append(f"tool_slot_evidence_rejected:{name}")
            continue
        if not isinstance(value, str) or value not in TOOL_SLOT_STATUSES:
            reasons.append(f"tool_slot_status_invalid:{name}")
            continue
        parsed[name] = value
    return reasons, parsed


def _binder_reasons(
    result: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
) -> list[str]:
    reasons: list[str] = []
    if result.get("schema_id") != WP_A0_SCHEMA_ID:
        reasons.append("binder_schema_rejected")
    if result.get("authority") != AUTHORITY:
        reasons.append("binder_authority_rejected")
    if result.get("trading_authority") != TRADING_AUTHORITY:
        reasons.append("binder_trading_authority_rejected")
    if result.get("safety_authority") != SAFETY_AUTHORITY:
        reasons.append("binder_safety_authority_rejected")
    if result.get("execution_authority") != EXECUTION_AUTHORITY:
        reasons.append("binder_execution_authority_rejected")
    if result.get("runtime_authorization_effect") != RUNTIME_AUTHORIZATION_EFFECT:
        reasons.append("binder_runtime_authorization_rejected")
    if result.get("guardian_identity") is not GUARDIAN_IDENTITY:
        reasons.append("binder_guardian_identity_rejected")
    if result.get("live_gate") is not LIVE_GATE:
        reasons.append("binder_live_gate_rejected")
    if result.get("network_access") is not NETWORK_ACCESS:
        reasons.append("binder_network_access_rejected")
    if result.get("coverage_proof") is not COVERAGE_PROOF:
        reasons.append("binder_coverage_proof_rejected")
    if result.get("implicit_scope_expansion") is not False:
        reasons.append("binder_implicit_scope_expansion_rejected")
    if result.get("authoritative_commit_sha") != authoritative_commit_sha:
        reasons.append("binder_authoritative_commit_rejected")
    if result.get("authoritative_tree_sha") != authoritative_tree_sha:
        reasons.append("binder_authoritative_tree_rejected")
    if result.get("declared_commit_sha") != manifest["declared_commit_sha"]:
        reasons.append("binder_declared_commit_rejected")
    if result.get("declared_tree_sha") != manifest["declared_tree_sha"]:
        reasons.append("binder_declared_tree_rejected")
    scope = manifest["scope"]
    if not isinstance(scope, Mapping):
        reasons.append("binder_scope_rejected")
        return sorted(reasons)
    for field in SCOPE_FIELDS:
        if result.get(field) != scope.get(field):
            reasons.append(f"binder_scope_rejected:{field}")
    allowed = result.get("allowed_nodes")
    unassigned = result.get("unassigned")
    if isinstance(allowed, list) and isinstance(unassigned, list):
        expected_gap = (not allowed) or bool(unassigned)
        if result.get("scope_coverage_gap") is not expected_gap:
            reasons.append("binder_coverage_rejected:scope_coverage_gap")
        if result.get("graph_coverage_gap") is not False:
            reasons.append("binder_coverage_rejected:graph_coverage_gap")
        if result.get("observation_coverage_gap") is not False:
            reasons.append("binder_coverage_rejected:observation_coverage_gap")
        if result.get("coverage_gap") is not expected_gap:
            reasons.append("binder_coverage_rejected:coverage_gap")
    else:
        reasons.append("binder_scope_rejected")
    return sorted(reasons)


def _from_binding(
    stored: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    status: str,
    reasons: list[str],
    tool_slots: dict[str, Any] | None = None,
) -> dict[str, Any]:
    slots = _echo_slots(manifest.get("tool_slots")) if tool_slots is None else tool_slots
    if status == STATUS_MANIFEST_RECORDED:
        _reasons, parsed = _parse_tool_slots(manifest.get("tool_slots"))
        slots = parsed
    return _output(
        status=status,
        manifest_id=_manifest_id(manifest),
        reasons=list(reasons),
        wp_a0_invoked=True,
        wp_a0_status=str(stored.get("status") or ""),
        wp_a0_result=dict(stored),
        tool_slots=slots,
        allowed_nodes=_list_field(stored, "allowed_nodes"),
        exclusions=_list_field(stored, "exclusions"),
        unassigned=_list_field(stored, "unassigned"),
        scope_coverage_gap=_bool_field(stored, "scope_coverage_gap"),
        graph_coverage_gap=_bool_field(stored, "graph_coverage_gap"),
        observation_coverage_gap=_bool_field(stored, "observation_coverage_gap"),
        coverage_gap=_bool_field(stored, "coverage_gap"),
    )


def _parsed_slots_or_echo(raw: Any) -> dict[str, Any]:
    reasons, parsed = _parse_tool_slots(raw)
    if "tool_slots_not_object" in reasons:
        return {}
    return parsed


def _echo_slots(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    return {name: raw[name] for name in TOOL_SLOT_NAMES if name in raw}


def _manifest_id(manifest: Mapping[str, Any]) -> str:
    value = manifest.get("manifest_id")
    if isinstance(value, str):
        return value
    return ""


def _copied_reasons(stored: Mapping[str, Any]) -> list[str]:
    reasons = stored.get("reasons")
    if isinstance(reasons, list):
        return list(reasons)
    return []


def _list_field(stored: Mapping[str, Any], key: str) -> list[Any]:
    value = stored.get(key)
    if isinstance(value, list):
        return list(value)
    return []


def _bool_field(stored: Mapping[str, Any], key: str) -> bool:
    value = stored.get(key)
    if isinstance(value, bool):
        return value
    return False


def _output(
    *,
    status: str,
    manifest_id: str,
    reasons: list[str],
    wp_a0_invoked: bool,
    wp_a0_status: str,
    wp_a0_result: Mapping[str, Any],
    tool_slots: Mapping[str, Any],
    allowed_nodes: list[Any],
    exclusions: list[Any],
    unassigned: list[Any],
    scope_coverage_gap: bool,
    graph_coverage_gap: bool,
    observation_coverage_gap: bool,
    coverage_gap: bool,
) -> dict[str, Any]:
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "manifest_id": manifest_id,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "guardian_ratification": False,
        "current_proven": False,
        "coverage_proof": COVERAGE_PROOF,
        "live_gate": LIVE_GATE,
        "network_access": NETWORK_ACCESS,
        "implicit_scope_expansion": False,
        "tool_slot_inference": False,
        "wp_a0_invoked": wp_a0_invoked,
        "wp_a0_status": wp_a0_status,
        "wp_a0_result": dict(wp_a0_result),
        "tool_slots": dict(tool_slots),
        "allowed_nodes": list(allowed_nodes),
        "exclusions": list(exclusions),
        "unassigned": list(unassigned),
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "reasons": list(reasons),
    }
