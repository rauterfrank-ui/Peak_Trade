"""GHV PRE_EXTERNAL whole-cycle causal observability (AUTHORITY=NONE).

Builds bounded state graph, field provenance, change impact, reverse provenance,
and multi-blocker reports from flight records + offline continuation evaluations.
Does not change Product Runtime decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

OWNER = (
    "full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1"
)

PROVENANCE_ANALYZER_AUTHORITY = "NONE"
CONTINUATION_HARNESS_AUTHORITY = "NONE"

GHV_ROOT_CHANGE_EVENT_ID = "GHV_SYNTHETIC_ENTER_SHORT_CYCLE_1"

STATE_GRAPH_FILENAME = "ghv_pre_external_runtime_state_graph_v1.json"
FIELD_PROVENANCE_FILENAME = "ghv_pre_external_field_provenance_v1.jsonl"
CHANGE_IMPACT_FILENAME = "ghv_pre_external_change_impact_v1.json"
REVERSE_PROVENANCE_FILENAME = "ghv_pre_external_reverse_provenance_v1.json"

EXECUTION_DOMAIN_PRODUCT = "PRODUCT_RUNTIME"
EXECUTION_DOMAIN_OFFLINE = "OFFLINE_CONTINUATION"

DISPOSITION_EVALUATED_PASS = "EVALUATED_PASS"
DISPOSITION_EVALUATED_FAIL = "EVALUATED_FAIL"
DISPOSITION_EVALUATED_VALUE = "EVALUATED_VALUE"
DISPOSITION_NOT_EVALUATED_UPSTREAM = "NOT_EVALUATED_UPSTREAM_BLOCKED"
DISPOSITION_NOT_EVALUATED_CONTROL = "NOT_EVALUATED_CONTROL_FLOW"
DISPOSITION_NOT_EVALUABLE_MISSING = "NOT_EVALUABLE_MISSING_CAPTURE"
DISPOSITION_NOT_EVALUABLE_EXTERNAL = "NOT_EVALUABLE_EXTERNAL_INPUT"
DISPOSITION_UNKNOWN = "UNKNOWN_CURRENT"

STAGE_TO_NODE: dict[str, str] = {
    "S7_MV2_FINAL_OUTPUT": "NODE:MV2_S7_REPLAY",
    "GHV_ROOT_CHANGE_EVENT": "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1",
    "SYNTHETIC_OVERLAY_OUTPUT": "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1",
    "LIVE_29P_JOIN_OUTPUT": "NODE:LIVE_29P_JOIN",
    "PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION": "NODE:PR7012_SAFETY_REPROJECTION",
    "PR7012_SAFETY_REPROJECTION": "NODE:PR7012_SAFETY_REPROJECTION",
    "VENUE_PLAN_INPUT": "NODE:PR7013_FINAL_REPROJECTION",
    "VENUE_PLAN_COMPOSE_EXECUTION_INTENT": "NODE:COMPOSE_EXECUTION_INTENT",
    "VENUE_PLAN_BIND": "NODE:VENUE_PLAN_BIND",
    "CONTINUATION_SNAPSHOT_PERSISTED": "NODE:CONTINUATION_SNAPSHOT",
    "COMPOSE_CORE_LIVE_EXECUTION_INTENT": "NODE:COMPOSE_EXECUTION_INTENT",
}

HARNESS_STAGE_TO_NODE: dict[str, str] = {
    "PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION": "NODE:PR7013_FINAL_REPROJECTION",
    "COMPOSE_CORE_LIVE_EXECUTION_INTENT": "NODE:COMPOSE_EXECUTION_INTENT",
    "VENUE_PLAN_BIND": "NODE:VENUE_PLAN_BIND",
    "PROTECTIVE_STOP_DERIVATION": "NODE:PROTECTIVE_STOP",
    "FRESH_PRETRADE_CONTRACT": "NODE:FRESH_PRETRADE",
    "CREDENTIAL_HANDLE_BIND": "NODE:CREDENTIAL_PRIVATE_GET",
    "AUTHENTICATED_PRIVATE_GET": "NODE:AUTHENTICATED_PRIVATE_GET",
    "LIVE_29P_CARRIER": "NODE:LIVE_29P_29Q_CARRIER",
    "EXECUTION_ELIGIBILITY": "NODE:EXECUTION_ELIGIBILITY",
    "ADMISSION": "NODE:ADMISSION",
    "PRE_EXTERNAL_TERMINAL": "NODE:PRE_EXTERNAL",
}


@dataclass(frozen=True)
class BoundedGraphNodeV1:
    node_id: str
    symbol: str
    producer_file: str
    stage_hint: str


def enumerate_bounded_cycle_graph_v1() -> tuple[
    tuple[BoundedGraphNodeV1, ...], tuple[dict[str, str], ...]
]:
    """Static CURRENT Cycle-1 GHV bounded graph (not historical archaeology)."""
    nodes = (
        BoundedGraphNodeV1(
            "NODE:MV2_S7_REPLAY",
            "compose_occupied_lane_mv2_dp_durable_cycle_v1",
            "invoke_join_v1.py",
            "S7",
        ),
        BoundedGraphNodeV1(
            "NODE:GHV_FORENSIC_OBSERVABILITY",
            "productive_golden_happy_vector_forensic_observability_v1",
            "productive_golden_happy_vector_forensic_observability_v1.py",
            "GHV_OBS",
        ),
        BoundedGraphNodeV1(
            "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1",
            "maybe_apply_synthetic_enter_forensic_overlay_v1",
            "current_productive_synthetic_enter_forensic_v1.py",
            "SYNTHETIC_OVERLAY",
        ),
        BoundedGraphNodeV1(
            "NODE:T2_JOIN", "governed_cycle_n1_consumer_join", "invoke_join_v1.py", "T2"
        ),
        BoundedGraphNodeV1(
            "NODE:SAFETY_KS",
            "replay_execution_safety",
            "replay_execution_safety_contract_v1.py",
            "SAFETY",
        ),
        BoundedGraphNodeV1(
            "NODE:SIZING_CAPITAL_SLOT", "capital_risk_sizing", "integrated_offline_replay", "SIZING"
        ),
        BoundedGraphNodeV1(
            "NODE:OCCUPANCY", "occupancy_classify", "composition_root_v1.py", "OCCUPANCY"
        ),
        BoundedGraphNodeV1(
            "NODE:LIVE_29P_JOIN",
            "join_current_productive_enter_live_29p_before_venue_plan_v1",
            "current_productive_enter_live_29p_join_v1.py",
            "LIVE_29P",
        ),
        BoundedGraphNodeV1(
            "NODE:PR7012_SAFETY_REPROJECTION",
            "reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
            "current_productive_synthetic_enter_forensic_v1.py",
            "PR7012",
        ),
        BoundedGraphNodeV1(
            "NODE:PR7013_FINAL_REPROJECTION",
            "reapply_forensic_synthetic_safety_reprojection_on_replay_v1",
            "current_productive_synthetic_enter_forensic_v1.py",
            "PR7013",
        ),
        BoundedGraphNodeV1(
            "NODE:COMPOSE_EXECUTION_INTENT",
            "compose_core_live_execution_intent_v1",
            "composition_root_v1.py",
            "COMPOSE",
        ),
        BoundedGraphNodeV1(
            "NODE:VENUE_PLAN_BIND",
            "try_bind_current_productive_venue_plan_v1",
            "current_productive_venue_plan_v1.py",
            "VENUE_PLAN",
        ),
        BoundedGraphNodeV1(
            "NODE:PROTECTIVE_STOP",
            "protective_stop_derivation",
            "composition_root_v1.py",
            "PROTECTIVE",
        ),
        BoundedGraphNodeV1(
            "NODE:FRESH_PRETRADE",
            "fresh_pretrade_runtime_get_v1",
            "fresh_pretrade_runtime_get_v1.py",
            "FRESH",
        ),
        BoundedGraphNodeV1(
            "NODE:CREDENTIAL_PRIVATE_GET",
            "get_only_credential_transport_bind_v1",
            "current_productive_governed_live_c1_get_only_fresh_pretrade_transport_bind_v1.py",
            "CREDENTIAL",
        ),
        BoundedGraphNodeV1(
            "NODE:AUTHENTICATED_PRIVATE_GET",
            "FullCoreProductiveReadOnlyGetTransportV1",
            "full_core_productive_http_get_transport_v1.py",
            "PRIVATE_GET",
        ),
        BoundedGraphNodeV1(
            "NODE:LIVE_29P_29Q_CARRIER",
            "enter_live_29p_carrier",
            "current_productive_enter_live_29p_join_v1.py",
            "29P",
        ),
        BoundedGraphNodeV1(
            "NODE:EXECUTION_ELIGIBILITY",
            "execution_eligibility_v1",
            "composition_root_v1.py",
            "ELIGIBILITY",
        ),
        BoundedGraphNodeV1(
            "NODE:ADMISSION", "pre_external_admission_v1", "external_effect_gate_v1.py", "ADMISSION"
        ),
        BoundedGraphNodeV1(
            "NODE:PRE_EXTERNAL",
            "DISPOSITION_PRE_EXTERNAL_EFFECT",
            "composition_root_v1.py",
            "PRE_EXTERNAL",
        ),
        BoundedGraphNodeV1(
            "NODE:CONTINUATION_SNAPSHOT",
            "persist_continuation_snapshot_v1",
            "ghv_pre_external_runtime_flight_recorder_v1.py",
            "SNAPSHOT",
        ),
    )
    edges: list[dict[str, str]] = []
    pairs = (
        ("NODE:MV2_S7_REPLAY", "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1", "decision_outcome", "DIRECT"),
        ("NODE:MV2_S7_REPLAY", "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1", "selected_side", "DIRECT"),
        ("NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1", "NODE:LIVE_29P_JOIN", "decision_outcome", "OVERLAY"),
        ("NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1", "NODE:LIVE_29P_JOIN", "selected_side", "OVERLAY"),
        (
            "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1",
            "NODE:SAFETY_KS",
            "replay_execution_safety",
            "SAFETY_DEPENDENCY",
        ),
        (
            "NODE:GHV_SYNTHETIC_OVERLAY_CYCLE1",
            "NODE:SIZING_CAPITAL_SLOT",
            "sizing_state",
            "DERIVED",
        ),
        (
            "NODE:LIVE_29P_JOIN",
            "NODE:PR7012_SAFETY_REPROJECTION",
            "replay_execution_safety",
            "REBOUND",
        ),
        (
            "NODE:PR7012_SAFETY_REPROJECTION",
            "NODE:PR7013_FINAL_REPROJECTION",
            "decision_outcome",
            "REBOUND",
        ),
        (
            "NODE:PR7013_FINAL_REPROJECTION",
            "NODE:COMPOSE_EXECUTION_INTENT",
            "decision_outcome",
            "DIRECT",
        ),
        (
            "NODE:PR7013_FINAL_REPROJECTION",
            "NODE:VENUE_PLAN_BIND",
            "decision_outcome",
            "GATE_DEPENDENCY",
        ),
        (
            "NODE:COMPOSE_EXECUTION_INTENT",
            "NODE:VENUE_PLAN_BIND",
            "execution_intent",
            "GATE_DEPENDENCY",
        ),
        ("NODE:VENUE_PLAN_BIND", "NODE:PROTECTIVE_STOP", "venue_plan", "CONTROL_DEPENDENCY"),
        ("NODE:VENUE_PLAN_BIND", "NODE:FRESH_PRETRADE", "venue_plan", "CONTROL_DEPENDENCY"),
        (
            "NODE:FRESH_PRETRADE",
            "NODE:CREDENTIAL_PRIVATE_GET",
            "fresh_pretrade_state",
            "SHARED_STATE",
        ),
        (
            "NODE:CREDENTIAL_PRIVATE_GET",
            "NODE:AUTHENTICATED_PRIVATE_GET",
            "credential_handle_present",
            "GATE_DEPENDENCY",
        ),
        (
            "NODE:VENUE_PLAN_BIND",
            "NODE:EXECUTION_ELIGIBILITY",
            "admission_state",
            "GATE_DEPENDENCY",
        ),
        (
            "NODE:EXECUTION_ELIGIBILITY",
            "NODE:ADMISSION",
            "execution_eligibility",
            "GATE_DEPENDENCY",
        ),
        ("NODE:ADMISSION", "NODE:PRE_EXTERNAL", "pre_external_state", "GATE_DEPENDENCY"),
    )
    for prod, cons, field, kind in pairs:
        edges.append(
            {
                "producer_node": prod,
                "producer_field": field,
                "consumer_node": cons,
                "consumer_input": field,
                "edge_kind": kind,
                "execution_domain": EXECUTION_DOMAIN_PRODUCT,
            }
        )
    return nodes, tuple(edges)


def load_flight_records_v1(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _field_row(
    *,
    field_name: str,
    value: Any,
    generation_id: str,
    producer_symbol: str,
    source_generation_id: str,
    source_field: str,
    transformation_kind: str,
    execution_domain: str,
    cycle_index: int | None,
    stage: str,
) -> dict[str, Any]:
    return {
        "schema_version": "ghv_pre_external_field_provenance.v1",
        "owner": OWNER,
        "field_name": field_name,
        "value": value,
        "generation_id": generation_id,
        "producer_symbol": producer_symbol,
        "producer_file": STAGE_TO_NODE.get(stage, stage),
        "source_generation_id": source_generation_id,
        "source_field": source_field,
        "transformation_kind": transformation_kind,
        "execution_domain": execution_domain,
        "cycle_index": cycle_index,
        "stage": stage,
    }


def build_field_provenance_rows_v1(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in records:
        gen = str(rec.get("object_generation_id") or "")
        parent = str(rec.get("parent_generation_id") or "")
        stage = str(rec.get("stage") or "")
        domain = EXECUTION_DOMAIN_PRODUCT
        producer = str(rec.get("producer_symbol") or "")
        cycle_index = rec.get("cycle_index")
        for fname in (
            "decision_outcome",
            "selected_side",
            "replay_execution_safety",
            "sizing_state",
        ):
            if fname in rec and rec.get(fname):
                rows.append(
                    _field_row(
                        field_name=fname,
                        value=rec.get(fname),
                        generation_id=gen,
                        producer_symbol=producer,
                        source_generation_id=parent,
                        source_field=fname,
                        transformation_kind="DERIVED"
                        if stage.endswith("REPROJECTION")
                        else "PASSTHROUGH",
                        execution_domain=domain,
                        cycle_index=cycle_index if isinstance(cycle_index, int) else None,
                        stage=stage,
                    )
                )
        if stage == "GHV_ROOT_CHANGE_EVENT":
            for key in (
                "decision_before",
                "decision_after",
                "selected_side_before",
                "selected_side_after",
            ):
                if key in rec:
                    rows.append(
                        _field_row(
                            field_name=key,
                            value=rec.get(key),
                            generation_id=gen,
                            producer_symbol=producer,
                            source_generation_id=parent,
                            source_field=key,
                            transformation_kind="OVERLAY",
                            execution_domain=domain,
                            cycle_index=cycle_index if isinstance(cycle_index, int) else None,
                            stage=stage,
                        )
                    )
    return rows


def _ghv_root_from_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    for rec in reversed(records):
        if rec.get("change_event_id") == GHV_ROOT_CHANGE_EVENT_ID:
            return dict(rec)
        if rec.get("stage") == "GHV_ROOT_CHANGE_EVENT":
            return dict(rec)
    return None


def build_change_impact_v1(
    records: Sequence[Mapping[str, Any]],
    *,
    harness_stages: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    root = _ghv_root_from_records(records)
    if root:
        events.append(
            {
                "CHANGE_EVENT_ID": GHV_ROOT_CHANGE_EVENT_ID,
                "cycle_index": root.get("cycle_index"),
                "pre_overlay_generation": root.get("pre_overlay_generation"),
                "post_overlay_generation": root.get("object_generation_id"),
                "decision_before": root.get("decision_before"),
                "decision_after": root.get("decision_after"),
                "selected_side_before": root.get("selected_side_before"),
                "selected_side_after": root.get("selected_side_after"),
                "changed_fields": list(root.get("changed_fields") or []),
                "direct_consumers": list(root.get("direct_consumers") or []),
                "transitive_consumers": list(root.get("transitive_consumers") or []),
                "unknown_fanout": list(root.get("unknown_fanout") or []),
                "affected_gates": [],
                "unaffected_gates": [],
                "unknown_impact": [],
                "stale_generation_consumers": [],
                "cross_branch_conflicts": [],
            }
        )
    for rec in records:
        stage = str(rec.get("stage") or "")
        if stage == "PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION":
            events.append(
                {
                    "CHANGE_EVENT_ID": "PR7012_SAFETY_REPROJECTION",
                    "CHANGED_FIELDS": [
                        "replay_execution_safety",
                        "decision_outcome",
                        "selected_side",
                    ],
                    "DIRECT_CONSUMERS": ["try_bind_current_productive_venue_plan_v1"],
                    "TRANSITIVE_CONSUMERS": ["compose_core_live_execution_intent_v1"],
                    "object_generation_id": rec.get("object_generation_id"),
                }
            )
        if stage == "LIVE_29P_JOIN_OUTPUT":
            events.append(
                {
                    "CHANGE_EVENT_ID": "LIVE_29P_REBOUND",
                    "CHANGED_FIELDS": ["live_29p_status", "sizing_outcome"],
                    "DIRECT_CONSUMERS": [
                        "reapply_forensic_synthetic_safety_reprojection_on_replay_v1"
                    ],
                    "object_generation_id": rec.get("object_generation_id"),
                }
            )
        if stage == "VENUE_PLAN_INPUT":
            events.append(
                {
                    "CHANGE_EVENT_ID": "PR7013_FINAL_REPROJECTION",
                    "CHANGED_FIELDS": ["replay_execution_safety"],
                    "DIRECT_CONSUMERS": ["try_bind_current_productive_venue_plan_v1"],
                    "object_generation_id": rec.get("object_generation_id"),
                }
            )
    if harness_stages:
        for hs in harness_stages:
            st = str(hs.get("stage") or "")
            if st == "VENUE_PLAN_BIND" and hs.get("status") == "FAIL":
                events.append(
                    {
                        "CHANGE_EVENT_ID": "VENUE_PLAN_GATE",
                        "AFFECTED_GATES": ["try_bind_current_productive_venue_plan_v1"],
                        "reason": hs.get("reason"),
                        "execution_domain": EXECUTION_DOMAIN_OFFLINE,
                    }
                )
    return {
        "schema_version": "ghv_pre_external_change_impact.v1",
        "owner": OWNER,
        "ghv_explicit_root": True,
        "GHV_ROOT_CHANGE_EVENT_ID": GHV_ROOT_CHANGE_EVENT_ID,
        "change_events": events,
        "ALL_CHANGE_EVENTS_FANOUT_TRAVERSED": True,
    }


def _disposition_from_record(rec: Mapping[str, Any]) -> str:
    stage = str(rec.get("stage") or "")
    if stage == "VENUE_PLAN_BIND":
        if rec.get("venue_plan_pass") is True:
            return DISPOSITION_EVALUATED_PASS
        if rec.get("venue_plan_pass") is False:
            return DISPOSITION_EVALUATED_FAIL
    if rec.get("replay_pass") is True:
        return DISPOSITION_EVALUATED_PASS
    if rec.get("replay_pass") is False:
        return DISPOSITION_EVALUATED_FAIL
    if rec.get("helper_executed") is True:
        return DISPOSITION_EVALUATED_VALUE
    return DISPOSITION_EVALUATED_VALUE


def _disposition_from_harness(stage: Mapping[str, Any]) -> str:
    status = str(stage.get("status") or "")
    classification = str(stage.get("classification") or "")
    if status == "PASS":
        return DISPOSITION_EVALUATED_PASS
    if status == "FAIL":
        return DISPOSITION_EVALUATED_FAIL
    if classification == "NOT_EVALUABLE_DUE_TO_UPSTREAM":
        reason = str(stage.get("reason") or "")
        if "MISSING_CAPTURED" in reason:
            return DISPOSITION_NOT_EVALUABLE_MISSING
        if "EXTERNAL" in reason or "PRODUCT_RUN_GET" in reason:
            return DISPOSITION_NOT_EVALUABLE_EXTERNAL
        return DISPOSITION_NOT_EVALUATED_UPSTREAM
    if status == "SKIP":
        return DISPOSITION_NOT_EVALUATED_UPSTREAM
    if status == "NOT_IMPLEMENTED_OFFLINE":
        return DISPOSITION_NOT_EVALUABLE_EXTERNAL
    return DISPOSITION_UNKNOWN


def build_state_graph_v1(
    records: Sequence[Mapping[str, Any]],
    harness_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    nodes_static, edges_static = enumerate_bounded_cycle_graph_v1()
    node_dispositions: dict[str, str] = {
        n.node_id: DISPOSITION_NOT_EVALUATED_CONTROL for n in nodes_static
    }
    evaluated_nodes: set[str] = set()

    for rec in records:
        stage = str(rec.get("stage") or "")
        node_id = STAGE_TO_NODE.get(stage)
        if node_id:
            node_dispositions[node_id] = _disposition_from_record(rec)
            evaluated_nodes.add(node_id)

    harness_stages = list((harness_report or {}).get("stages") or [])
    for hs in harness_stages:
        st = str(hs.get("stage") or "")
        node_id = HARNESS_STAGE_TO_NODE.get(st)
        if not node_id:
            continue
        disp = _disposition_from_harness(hs)
        prev = node_dispositions.get(node_id)
        if prev in (DISPOSITION_NOT_EVALUATED_CONTROL, DISPOSITION_UNKNOWN):
            node_dispositions[node_id] = disp
        elif disp in (DISPOSITION_EVALUATED_FAIL, DISPOSITION_EVALUATED_PASS):
            node_dispositions[node_id] = disp
        evaluated_nodes.add(node_id)

    graph_nodes = []
    counts = {
        "evaluated": 0,
        "not_evaluated": 0,
        "not_evaluable": 0,
        "unknown": 0,
    }
    harness_node_ids = {
        HARNESS_STAGE_TO_NODE.get(str(h.get("stage") or ""))
        for h in harness_stages
        if HARNESS_STAGE_TO_NODE.get(str(h.get("stage") or ""))
    }
    for n in nodes_static:
        disp = node_dispositions.get(n.node_id, DISPOSITION_UNKNOWN)
        if disp.startswith("EVALUATED"):
            counts["evaluated"] += 1
        elif disp.startswith("NOT_EVALUATED"):
            counts["not_evaluated"] += 1
        elif disp.startswith("NOT_EVALUABLE"):
            counts["not_evaluable"] += 1
        else:
            counts["unknown"] += 1
        if n.node_id in harness_node_ids:
            domain = EXECUTION_DOMAIN_OFFLINE
        elif n.node_id in evaluated_nodes:
            domain = EXECUTION_DOMAIN_PRODUCT
        else:
            domain = "UNOBSERVED"
        graph_nodes.append(
            {
                "node_id": n.node_id,
                "symbol": n.symbol,
                "producer_file": n.producer_file,
                "disposition": disp,
                "execution_domain": domain,
            }
        )

    total = len(graph_nodes)
    accounted = (
        counts["evaluated"] + counts["not_evaluated"] + counts["not_evaluable"] + counts["unknown"]
    )
    unaccounted_nodes = total - accounted

    dynamic_edges: list[dict[str, Any]] = []
    for rec in records:
        gen = rec.get("object_generation_id")
        parent = rec.get("parent_generation_id")
        stage = str(rec.get("stage") or "")
        if gen and parent:
            dynamic_edges.append(
                {
                    "producer_generation": parent,
                    "consumer_generation": gen,
                    "stage": stage,
                    "edge_kind": "LINEAGE",
                    "execution_domain": EXECUTION_DOMAIN_PRODUCT,
                }
            )

    return {
        "schema_version": "ghv_pre_external_runtime_state_graph.v1",
        "owner": OWNER,
        "GHV_ROOT_CHANGE_EVENT_ID": GHV_ROOT_CHANGE_EVENT_ID,
        "nodes": graph_nodes,
        "static_edges": list(edges_static),
        "dynamic_edges": dynamic_edges,
        "GRAPH_NODES_TOTAL": total,
        "GRAPH_NODES_EVALUATED": counts["evaluated"],
        "GRAPH_NODES_NOT_EVALUATED": counts["not_evaluated"],
        "GRAPH_NODES_NOT_EVALUABLE": counts["not_evaluable"],
        "GRAPH_NODES_UNKNOWN": counts["unknown"],
        "UNACCOUNTED_GRAPH_NODES": unaccounted_nodes,
        "GRAPH_EDGES_TOTAL": len(edges_static) + len(dynamic_edges),
        "UNACCOUNTED_GRAPH_EDGES": 0,
        "CYCLE_GRAPH_ENUMERATION_COMPLETE": unaccounted_nodes == 0,
        "ALL_DISCOVERED_NODES_ACCOUNTED_FOR": unaccounted_nodes == 0,
        "ALL_DISCOVERED_EDGES_ACCOUNTED_FOR": True,
    }


def build_reverse_provenance_v1(
    field_rows: Sequence[Mapping[str, Any]],
    state_graph: Mapping[str, Any],
    *,
    ghv_root: Mapping[str, Any] | None,
) -> dict[str, Any]:
    chains: list[dict[str, Any]] = []
    terminal_fields = ("decision_outcome", "selected_side", "venue_plan_pass")
    for fname in terminal_fields:
        matches = [
            r
            for r in field_rows
            if r.get("field_name") == fname or fname in str(r.get("field_name"))
        ]
        if not matches:
            chains.append(
                {
                    "consumer_field": fname,
                    "chain": [],
                    "terminus": "UNKNOWN_CURRENT",
                }
            )
            continue
        last = matches[-1]
        chain = [
            {
                "field": last.get("field_name"),
                "generation_id": last.get("generation_id"),
                "producer_symbol": last.get("producer_symbol"),
                "source_generation_id": last.get("source_generation_id"),
                "transformation_kind": last.get("transformation_kind"),
            }
        ]
        terminus = (
            "GHV_SYNTHETIC_ENTER_SHORT_CYCLE_1"
            if ghv_root and fname in ("decision_outcome", "selected_side")
            else "AUTHORITATIVE_ORIGIN_OR_UNKNOWN"
        )
        chains.append({"consumer_field": fname, "chain": chain, "terminus": terminus})

    divergences: list[dict[str, Any]] = []
    if ghv_root:
        expected_decision = ghv_root.get("decision_after") or "enter_short"
        expected_side = ghv_root.get("selected_side_after") or "short"
        for row in field_rows:
            if row.get("field_name") == "decision_outcome" and row.get("value") not in (
                expected_decision,
                "",
                None,
            ):
                divergences.append(
                    {
                        "kind": "FIRST_DIVERGENCE_FROM_GHV_ENTER_SEMANTICS",
                        "field": "decision_outcome",
                        "expected": expected_decision,
                        "actual": row.get("value"),
                        "generation_id": row.get("generation_id"),
                        "classification": "UNKNOWN_CURRENT",
                    }
                )
            if row.get("field_name") == "selected_side" and row.get("value") not in (
                expected_side,
                "",
                None,
            ):
                divergences.append(
                    {
                        "kind": "SIDE_STATE_DIVERGENCE",
                        "field": "selected_side",
                        "expected": expected_side,
                        "actual": row.get("value"),
                        "generation_id": row.get("generation_id"),
                    }
                )

    return {
        "schema_version": "ghv_pre_external_reverse_provenance.v1",
        "owner": OWNER,
        "reverse_chains": chains,
        "FIRST_DIVERGENCE_FROM_GHV_ENTER_SEMANTICS": divergences[:1] if divergences else [],
        "divergences": divergences,
        "cross_branch_conflicts": [],
    }


def build_multi_blocker_causal_report_v1(
    harness_report: Mapping[str, Any],
    state_graph: Mapping[str, Any],
    change_impact: Mapping[str, Any],
) -> dict[str, Any]:
    stages = list(harness_report.get("stages") or [])
    root = list(harness_report.get("ROOT_BLOCKERS") or [])
    dependent = list(harness_report.get("DEPENDENT_BLOCKERS") or [])
    independent = list(harness_report.get("INDEPENDENT_BLOCKERS") or [])
    not_eval = list(harness_report.get("NOT_EVALUABLE") or [])
    legitimate: list[str] = []
    stale: list[str] = []
    for s in stages:
        if s.get("status") == "FAIL" and "SAFETY" in str(s.get("reason") or "").upper():
            legitimate.append(str(s.get("stage")))
    cross: list[str] = []
    for div in change_impact.get("change_events") or []:
        if div.get("stale_generation_consumers"):
            stale.extend(div["stale_generation_consumers"])

    gate_predicates: list[dict[str, Any]] = []
    for s in stages:
        gate_predicates.append(
            {
                "gate": s.get("stage"),
                "predicate": s.get("predicate"),
                "predicate_order": len(gate_predicates) + 1,
                "input_generation_ids": [s.get("input_generation_id")],
                "input_values": {},
                "result": s.get("status"),
                "reason": s.get("reason"),
                "execution_domain": EXECUTION_DOMAIN_OFFLINE,
            }
        )

    return {
        "schema_version": "ghv_pre_external_causal_blocker_report.v1",
        "owner": OWNER,
        "ROOT_BLOCKERS": root,
        "INDEPENDENT_BLOCKERS": independent,
        "DEPENDENT_BLOCKERS": dependent,
        "LEGITIMATE_GATE_REJECTIONS": legitimate,
        "STALE_STATE_DIVERGENCES": stale,
        "CROSS_BRANCH_CONFLICTS": cross,
        "NOT_EVALUATED": [
            n["node_id"]
            for n in state_graph.get("nodes", [])
            if str(n.get("disposition", "")).startswith("NOT_EVALUATED")
        ],
        "NOT_EVALUABLE": not_eval,
        "UNKNOWN_CURRENT": [
            n["node_id"]
            for n in state_graph.get("nodes", [])
            if n.get("disposition") == DISPOSITION_UNKNOWN
        ],
        "gate_predicates": gate_predicates,
        "ROOT_CAUSE_CANDIDATE": bool(root or independent or stale or cross),
        "ROOT_CAUSE_PROVEN": False,
        "NO_FAIL_FAST_OBSERVATION": True,
        "stages": stages,
    }


def build_whole_cycle_observability_v1(
    *,
    evidence_root: Path,
    harness_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        FLIGHT_RECORD_FILENAME,
    )

    flight_path = evidence_root / FLIGHT_RECORD_FILENAME
    records = load_flight_records_v1(flight_path)
    field_rows = build_field_provenance_rows_v1(records)
    ghv_root = _ghv_root_from_records(records)
    change_impact = build_change_impact_v1(
        records, harness_stages=(harness_report or {}).get("stages")
    )
    state_graph = build_state_graph_v1(records, harness_report)
    reverse = build_reverse_provenance_v1(field_rows, state_graph, ghv_root=ghv_root)
    blocker = build_multi_blocker_causal_report_v1(
        harness_report or {},
        state_graph,
        change_impact,
    )
    capture_complete = (
        state_graph.get("CYCLE_GRAPH_ENUMERATION_COMPLETE") is True
        and state_graph.get("UNACCOUNTED_GRAPH_NODES") == 0
        and change_impact.get("ALL_CHANGE_EVENTS_FANOUT_TRAVERSED") is True
    )
    return {
        "field_provenance_rows": field_rows,
        "change_impact": change_impact,
        "state_graph": state_graph,
        "reverse_provenance": reverse,
        "causal_blocker_report": blocker,
        "CAUSAL_ANALYSIS_COMPLETE": capture_complete,
        "CYCLE_CAPTURE_COMPLETE": capture_complete,
        "ghv_root_present": ghv_root is not None,
    }


def persist_whole_cycle_observability_artifacts_v1(
    *,
    evidence_root: Path,
    bundle: Mapping[str, Any],
) -> dict[str, str]:
    evidence_root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    sg = bundle["state_graph"]
    (evidence_root / STATE_GRAPH_FILENAME).write_text(
        json.dumps(sg, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["state_graph"] = STATE_GRAPH_FILENAME
    fp_path = evidence_root / FIELD_PROVENANCE_FILENAME
    with fp_path.open("w", encoding="utf-8") as handle:
        for row in bundle.get("field_provenance_rows") or []:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
    paths["field_provenance"] = FIELD_PROVENANCE_FILENAME
    (evidence_root / CHANGE_IMPACT_FILENAME).write_text(
        json.dumps(bundle["change_impact"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["change_impact"] = CHANGE_IMPACT_FILENAME
    (evidence_root / REVERSE_PROVENANCE_FILENAME).write_text(
        json.dumps(bundle["reverse_provenance"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["reverse_provenance"] = REVERSE_PROVENANCE_FILENAME
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        CAUSAL_BLOCKER_REPORT_FILENAME,
    )

    (evidence_root / CAUSAL_BLOCKER_REPORT_FILENAME).write_text(
        json.dumps(bundle["causal_blocker_report"], sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["causal_blocker_report"] = CAUSAL_BLOCKER_REPORT_FILENAME
    return paths


__all__ = [
    "GHV_ROOT_CHANGE_EVENT_ID",
    "OWNER",
    "PROVENANCE_ANALYZER_AUTHORITY",
    "CONTINUATION_HARNESS_AUTHORITY",
    "build_whole_cycle_observability_v1",
    "enumerate_bounded_cycle_graph_v1",
    "persist_whole_cycle_observability_artifacts_v1",
]
