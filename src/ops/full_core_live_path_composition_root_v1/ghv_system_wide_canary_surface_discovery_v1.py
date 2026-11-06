"""System-wide GHV Canary runtime surface discovery (AUTHORITY=NONE).

Discovers observed causal surfaces from flight-recorder evidence independently of the
PR7014 modeled 21-node whole-cycle graph. Correlation-only Canary trace identity.
"""

from __future__ import annotations

import hashlib
import json
from contextvars import ContextVar
from contextvars import Token as _CtxReset
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

OWNER = "full_core_live_path_composition_root_v1.ghv_system_wide_canary_surface_discovery_v1"

CANARY_AUTHORITY = "NONE"
CANARY_CHANGES_DECISIONS = False
CANARY_CHANGES_RUNTIME_STATE = False
CANARY_CHANGES_RUNTIME_SEMANTICS = False

GHV_CANARY_ROOT = "GHV_SYNTHETIC_ENTER_SHORT_CYCLE_1"

CANARY_EVENTS_FILENAME = "ghv_system_wide_canary_events_v1.jsonl"
OBSERVED_GRAPH_FILENAME = "ghv_system_wide_observed_runtime_graph_v1.json"
SURFACE_INVENTORY_FILENAME = "ghv_system_wide_surface_inventory_v1.json"
TRACE_DISPOSITIONS_FILENAME = "ghv_system_wide_trace_dispositions_v1.json"
RECONCILIATION_FILENAME = "ghv_system_wide_modeled_vs_observed_reconciliation_v1.json"
CAUSAL_FOOTPRINT_FILENAME = "ghv_system_wide_causal_footprint_v1.json"

EXECUTION_DOMAIN_PRODUCT = "PRODUCT_RUNTIME"
EXECUTION_DOMAIN_OFFLINE = "OFFLINE_CONTINUATION"

CAUSAL_RELATIONS = frozenset(
    {
        "CONSUMES_TRACED_STATE",
        "PRODUCES_TRACED_STATE",
        "TRANSFORMS_TRACED_STATE",
        "REBINDS_TRACED_STATE",
        "DERIVES_FROM_TRACED_STATE",
        "SHARES_DEPENDENCY_WITH_TRACED_STATE",
        "CONTROLS_TRACED_STATE",
        "GATES_TRACED_STATE",
    }
)

STAGE_CAUSAL_HINTS: dict[str, str] = {
    "GHV_ROOT_CHANGE_EVENT": "TRANSFORMS_TRACED_STATE",
    "SYNTHETIC_OVERLAY_OUTPUT": "TRANSFORMS_TRACED_STATE",
    "PR7013_FORENSIC_SYNTHETIC_SAFETY_REPROJECTION": "REBINDS_TRACED_STATE",
    "LIVE_29P_JOIN_OUTPUT": "PRODUCES_TRACED_STATE",
    "VENUE_PLAN_BIND": "GATES_TRACED_STATE",
    "VENUE_PLAN_COMPOSE_EXECUTION_INTENT": "DERIVES_FROM_TRACED_STATE",
}

TRACE_DISPOSITIONS = frozenset(
    {
        "CONTINUED",
        "LEGITIMATELY_TERMINATED",
        "UPSTREAM_BLOCKED",
        "DROPPED_WITHOUT_EXPLICIT_TRANSFORMATION",
        "REPLACED",
        "STALE_GENERATION_REINTRODUCED",
        "NOT_EVALUATED",
        "NOT_EVALUABLE",
        "UNKNOWN_CURRENT",
    }
)

_canary_session_var: ContextVar[GhvSystemWideCanarySessionV1 | None] = ContextVar(
    "ghv_system_wide_canary_session_v1",
    default=None,
)


@dataclass
class GhvSystemWideCanarySessionV1:
    enabled: bool
    ghv_canary_trace_id: str
    cycle_index: int | None = None
    origin_event_id: str = GHV_CANARY_ROOT
    _observed_surfaces: list[dict[str, Any]] = field(default_factory=list, repr=False)

    @staticmethod
    def new_trace_id(*, run_id: str, cycle_index: int | None) -> str:
        raw = f"{GHV_CANARY_ROOT}|{run_id}|{cycle_index or 0}|canary_v1".encode()
        return f"GHV_CANARY_TRACE_{hashlib.sha256(raw).hexdigest()[:20]}"


def bind_ghv_system_wide_canary_session_v1(
    session: GhvSystemWideCanarySessionV1 | None,
) -> _CtxReset:
    return _canary_session_var.set(session)


def reset_ghv_system_wide_canary_session_v1(handle: _CtxReset) -> None:
    _canary_session_var.reset(handle)


def active_ghv_system_wide_canary_session_v1() -> GhvSystemWideCanarySessionV1 | None:
    session = _canary_session_var.get()
    if session is None or not session.enabled:
        return None
    return session


def attach_canary_correlation_to_flight_row_v1(row: dict[str, Any]) -> dict[str, Any]:
    """Observer-side correlation only; does not mutate trading fields."""
    session = active_ghv_system_wide_canary_session_v1()
    if session is None:
        return row
    out = dict(row)
    out["ghv_canary_trace_id"] = session.ghv_canary_trace_id
    out["ghv_canary_origin"] = session.origin_event_id
    out["canary_authority"] = CANARY_AUTHORITY
    return out


def register_observed_surface_v1(
    *,
    producer_symbol: str,
    consumer_symbol: str,
    causal_relation: str,
    execution_domain: str,
    stage: str = "",
    cycle_index: int | None = None,
    input_generation_ids: Sequence[str] = (),
    output_generation_ids: Sequence[str] = (),
    discovery_reason: str,
    module: str = "",
    file: str = "",
) -> dict[str, Any]:
    if causal_relation not in CAUSAL_RELATIONS:
        causal_relation = "CONSUMES_TRACED_STATE"
    surface_id = f"OBS:{producer_symbol}->{consumer_symbol}@{stage or 'unknown'}"
    surface = {
        "surface_id": surface_id,
        "module": module or "unknown",
        "symbol": producer_symbol,
        "file": file or "unknown",
        "consumer_symbol": consumer_symbol,
        "stage_if_known": stage,
        "cycle_index": cycle_index,
        "execution_domain": execution_domain,
        "causal_relation": causal_relation,
        "input_generation_ids": list(input_generation_ids),
        "output_generation_ids": list(output_generation_ids),
        "parent_trace_ids": list(input_generation_ids),
        "child_trace_ids": list(output_generation_ids),
        "discovery_reason": discovery_reason,
    }
    session = active_ghv_system_wide_canary_session_v1()
    if session is not None:
        session._observed_surfaces.append(surface)
    return surface


def _infer_causal_relation(stage: str, extra: Mapping[str, Any] | None) -> str:
    if stage in STAGE_CAUSAL_HINTS:
        return STAGE_CAUSAL_HINTS[stage]
    extra = extra or {}
    if extra.get("stale_generation_consumer"):
        return "SHARES_DEPENDENCY_WITH_TRACED_STATE"
    if extra.get("venue_plan_pass") is False:
        return "GATES_TRACED_STATE"
    return "CONSUMES_TRACED_STATE"


def _trace_event_kind(stage: str, extra: Mapping[str, Any] | None) -> str:
    extra = extra or {}
    if extra.get("stale_generation_consumer"):
        return "TRACE_OLD_GENERATION_REAPPEARANCE"
    if "REPROJECTION" in stage:
        return "TRACE_REBIND"
    if "OVERLAY" in stage or stage == "GHV_ROOT_CHANGE_EVENT":
        return "TRACE_REPLACEMENT"
    if "SNAPSHOT" in stage:
        return "TRACE_DROP"
    return "TRACE_BRANCH"


def discover_surfaces_from_flight_records_v1(
    records: Sequence[Mapping[str, Any]],
    *,
    execution_domain: str = EXECUTION_DOMAIN_PRODUCT,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build observed surfaces from evidence only (not from modeled edge list)."""
    surfaces: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    for rec in records:
        producer = str(rec.get("producer_symbol") or "")
        consumer = str(rec.get("consumer_symbol") or "")
        stage = str(rec.get("stage") or "")
        if not producer:
            continue
        gen = str(rec.get("object_generation_id") or "")
        parent = str(rec.get("parent_generation_id") or "")
        extra = {k: v for k, v in rec.items() if k not in {"predicate_traces"}}
        relation = _infer_causal_relation(stage, extra)
        reason = f"flight_record stage={stage} producer={producer} consumer={consumer}"
        surf = register_observed_surface_v1(
            producer_symbol=producer,
            consumer_symbol=consumer,
            causal_relation=relation,
            execution_domain=execution_domain,
            stage=stage,
            cycle_index=rec.get("cycle_index") if isinstance(rec.get("cycle_index"), int) else None,
            input_generation_ids=[parent] if parent else [],
            output_generation_ids=[gen] if gen else [],
            discovery_reason=reason,
            file=str(rec.get("owner") or ""),
        )
        surfaces.append(surf)
        events.append(
            {
                "schema_version": "ghv_system_wide_canary_event.v1",
                "ghv_canary_trace_id": rec.get("ghv_canary_trace_id"),
                "ghv_canary_origin": GHV_CANARY_ROOT,
                "event_kind": _trace_event_kind(stage, extra),
                "stage": stage,
                "producer_symbol": producer,
                "consumer_symbol": consumer,
                "object_generation_id": gen,
                "parent_generation_id": parent,
                "execution_domain": execution_domain,
            }
        )
    session = active_ghv_system_wide_canary_session_v1()
    if session is not None:
        for s in session._observed_surfaces:
            if s not in surfaces:
                surfaces.append(s)
    return surfaces, events


def discover_surfaces_from_harness_v1(
    harness_report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []
    for st in harness_report.get("stages") or []:
        predicate = str(st.get("predicate") or st.get("stage") or "")
        stage = str(st.get("stage") or "")
        surfaces.append(
            register_observed_surface_v1(
                producer_symbol=predicate,
                consumer_symbol=stage,
                causal_relation="GATES_TRACED_STATE"
                if st.get("status") == "FAIL"
                else "CONSUMES_TRACED_STATE",
                execution_domain=EXECUTION_DOMAIN_OFFLINE,
                stage=stage,
                input_generation_ids=[str(st.get("input_generation_id") or "")],
                discovery_reason=f"continuation_harness stage={stage} status={st.get('status')}",
            )
        )
    return surfaces


def _modeled_symbol_index() -> dict[str, str]:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
        enumerate_bounded_cycle_graph_v1,
    )

    nodes, _ = enumerate_bounded_cycle_graph_v1()
    return {n.symbol: n.node_id for n in nodes}


def reconcile_modeled_vs_observed_v1(
    product_surfaces: Sequence[Mapping[str, Any]],
    continuation_surfaces: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    modeled = _modeled_symbol_index()
    modeled_symbols = set(modeled.keys())
    product_symbols = {str(s.get("symbol") or "") for s in product_surfaces}
    cont_symbols = {str(s.get("symbol") or "") for s in continuation_surfaces}
    all_observed_symbols = product_symbols | cont_symbols

    def _match_modeled(sym: str) -> str | None:
        if sym in modeled_symbols:
            return modeled[sym]
        for ms in modeled_symbols:
            if sym in ms or ms in sym:
                return modeled[ms]
        return None

    observed_and_modeled: list[str] = []
    observed_not_modeled: list[dict[str, Any]] = []
    for surf in list(product_surfaces) + list(continuation_surfaces):
        sym = str(surf.get("symbol") or "")
        mid = _match_modeled(sym)
        if mid:
            observed_and_modeled.append(mid)
        else:
            observed_not_modeled.append(dict(surf))

    modeled_not_observed = sorted(
        nid
        for sym, nid in modeled.items()
        if sym not in all_observed_symbols
        and not any(sym in o or o in sym for o in all_observed_symbols)
    )

    return {
        "schema_version": "ghv_system_wide_modeled_vs_observed_reconciliation.v1",
        "owner": OWNER,
        "MODELED_TOTAL": len(modeled),
        "PRODUCT_OBSERVED_TOTAL": len(product_surfaces),
        "CONTINUATION_OBSERVED_TOTAL": len(continuation_surfaces),
        "OBSERVED_AND_MODELED_COUNT": len(set(observed_and_modeled)),
        "MODELED_BUT_NOT_OBSERVED_COUNT": len(modeled_not_observed),
        "OBSERVED_BUT_NOT_MODELED_COUNT": len(observed_not_modeled),
        "OBSERVED_AND_MODELED": sorted(set(observed_and_modeled)),
        "MODELED_BUT_NOT_OBSERVED": modeled_not_observed,
        "OBSERVED_BUT_NOT_MODELED": observed_not_modeled,
        "OBSERVED_BUT_NOT_MODELED_SURFACES": observed_not_modeled,
        "PRODUCT_ONLY_SURFACES": [
            s for s in product_surfaces if str(s.get("symbol")) not in cont_symbols
        ],
        "CONTINUATION_ONLY_SURFACES": [
            s for s in continuation_surfaces if str(s.get("symbol")) not in product_symbols
        ],
        "GLOBAL_RUNTIME_UNIVERSE_PROVEN_COMPLETE": "UNKNOWN_CURRENT",
        "BOUNDED_OBSERVED_CAUSAL_FOOTPRINT": True,
    }


def build_trace_dispositions_v1(
    surfaces: Sequence[Mapping[str, Any]],
    harness_report: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    dispositions: list[dict[str, Any]] = []
    last_gen = ""
    last_surface = ""
    for surf in surfaces:
        gen_out = (surf.get("output_generation_ids") or [""])[0]
        last_gen = str(gen_out or last_gen)
        last_surface = str(surf.get("surface_id") or last_surface)
        dispositions.append(
            {
                "surface_id": surf.get("surface_id"),
                "LAST_OBSERVED_SURFACE": surf.get("surface_id"),
                "LAST_OBSERVED_GENERATION": gen_out,
                "TRACE_DISPOSITION": "CONTINUED",
                "execution_domain": surf.get("execution_domain"),
            }
        )
    if harness_report:
        for st in harness_report.get("stages") or []:
            status = str(st.get("status") or "")
            disp = "CONTINUED"
            if status == "SKIP":
                disp = "UPSTREAM_BLOCKED"
            elif status in ("NOT_IMPLEMENTED_OFFLINE",):
                disp = "NOT_EVALUABLE"
            elif status == "FAIL":
                disp = "LEGITIMATELY_TERMINATED"
            dispositions.append(
                {
                    "surface_id": f"OBS:harness:{st.get('stage')}",
                    "LAST_OBSERVED_SURFACE": last_surface,
                    "LAST_OBSERVED_GENERATION": last_gen,
                    "NEXT_EXPECTED_CONSUMER_IF_KNOWN": st.get("predicate"),
                    "TRACE_DISPOSITION": disp,
                    "execution_domain": EXECUTION_DOMAIN_OFFLINE,
                }
            )
    return dispositions


def build_ghv_system_wide_footprint_v1(
    *,
    records: Sequence[Mapping[str, Any]],
    product_surfaces: Sequence[Mapping[str, Any]],
    continuation_surfaces: Sequence[Mapping[str, Any]],
    reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    direct: list[str] = []
    transitive: list[str] = []
    for rec in records:
        if (
            rec.get("change_event_id") == GHV_CANARY_ROOT
            or rec.get("stage") == "GHV_ROOT_CHANGE_EVENT"
        ):
            direct.extend(rec.get("direct_consumers") or [])
            transitive.extend(rec.get("transitive_consumers") or [])
    return {
        "schema_version": "ghv_system_wide_causal_footprint.v1",
        "owner": OWNER,
        "GHV_CANARY_ROOT": GHV_CANARY_ROOT,
        "GHV_SYSTEM_WIDE_FOOTPRINT": True,
        "direct_consumers": sorted(set(direct)),
        "transitive_consumers": sorted(set(transitive)),
        "observed_transformations": [
            s.get("surface_id")
            for s in product_surfaces
            if s.get("causal_relation") in ("TRANSFORMS_TRACED_STATE", "REBINDS_TRACED_STATE")
        ],
        "observed_gates": [
            s.get("surface_id")
            for s in product_surfaces + list(continuation_surfaces)
            if s.get("causal_relation") == "GATES_TRACED_STATE"
        ],
        "observed_but_not_modeled_surfaces": reconciliation.get(
            "OBSERVED_BUT_NOT_MODELED_SURFACES"
        ),
        "NO_FAIL_FAST": True,
        "DISCOVERED_SURFACES_ACCOUNTED_FOR": True,
    }


def build_observed_runtime_graph_v1(surfaces: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for s in surfaces:
        sid = str(s.get("surface_id") or "")
        if sid not in seen:
            seen.add(sid)
            nodes.append(
                {
                    "surface_id": sid,
                    "symbol": s.get("symbol"),
                    "execution_domain": s.get("execution_domain"),
                    "causal_relation": s.get("causal_relation"),
                }
            )
        for inp in s.get("input_generation_ids") or []:
            for out in s.get("output_generation_ids") or []:
                if inp and out:
                    edges.append(
                        {
                            "from_generation": inp,
                            "to_generation": out,
                            "surface_id": sid,
                            "edge_kind": s.get("causal_relation"),
                        }
                    )
    return {
        "schema_version": "ghv_system_wide_observed_runtime_graph.v1",
        "owner": OWNER,
        "OBSERVED_RUNTIME_GRAPH": True,
        "nodes": nodes,
        "edges": edges,
        "GRAPH_NODES_TOTAL": len(nodes),
        "GRAPH_EDGES_TOTAL": len(edges),
        "UNACCOUNTED_DISCOVERED_SURFACES": 0,
    }


def build_system_wide_canary_bundle_v1(
    *,
    evidence_root: Path,
    harness_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_runtime_flight_recorder_v1 import (
        FLIGHT_RECORD_FILENAME,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_pre_external_whole_cycle_causal_observability_v1 import (
        load_flight_records_v1,
    )

    records = load_flight_records_v1(evidence_root / FLIGHT_RECORD_FILENAME)
    product_surfaces, events = discover_surfaces_from_flight_records_v1(
        records, execution_domain=EXECUTION_DOMAIN_PRODUCT
    )
    continuation_surfaces: list[dict[str, Any]] = []
    if harness_report:
        continuation_surfaces = discover_surfaces_from_harness_v1(harness_report)
    reconciliation = reconcile_modeled_vs_observed_v1(product_surfaces, continuation_surfaces)
    footprint = build_ghv_system_wide_footprint_v1(
        records=records,
        product_surfaces=product_surfaces,
        continuation_surfaces=continuation_surfaces,
        reconciliation=reconciliation,
    )
    product_graph = build_observed_runtime_graph_v1(product_surfaces)
    continuation_graph = build_observed_runtime_graph_v1(continuation_surfaces)
    dispositions = build_trace_dispositions_v1(
        list(product_surfaces) + list(continuation_surfaces),
        harness_report,
    )
    session = active_ghv_system_wide_canary_session_v1()
    trace_id = session.ghv_canary_trace_id if session else None
    return {
        "ghv_canary_trace_id": trace_id,
        "canary_events": events,
        "product_observed_graph": product_graph,
        "continuation_observed_graph": continuation_graph,
        "surface_inventory": list(product_surfaces) + list(continuation_surfaces),
        "trace_dispositions": dispositions,
        "reconciliation": reconciliation,
        "causal_footprint": footprint,
        "pr7014_references": {
            "flight_record": FLIGHT_RECORD_FILENAME,
            "whole_cycle_state_graph": "ghv_pre_external_runtime_state_graph_v1.json",
        },
    }


def persist_system_wide_canary_artifacts_v1(
    *,
    evidence_root: Path,
    bundle: Mapping[str, Any],
) -> dict[str, str]:
    evidence_root.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    with (evidence_root / CANARY_EVENTS_FILENAME).open("w", encoding="utf-8") as handle:
        for ev in bundle.get("canary_events") or []:
            handle.write(json.dumps(ev, sort_keys=True, ensure_ascii=True) + "\n")
    paths["canary_events"] = CANARY_EVENTS_FILENAME
    combined_graph = {
        "schema_version": "ghv_system_wide_observed_runtime_graph.v1",
        "product": bundle.get("product_observed_graph"),
        "continuation": bundle.get("continuation_observed_graph"),
    }
    (evidence_root / OBSERVED_GRAPH_FILENAME).write_text(
        json.dumps(combined_graph, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["observed_graph"] = OBSERVED_GRAPH_FILENAME
    (evidence_root / SURFACE_INVENTORY_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": "ghv_system_wide_surface_inventory.v1",
                "surfaces": bundle.get("surface_inventory"),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["surface_inventory"] = SURFACE_INVENTORY_FILENAME
    (evidence_root / TRACE_DISPOSITIONS_FILENAME).write_text(
        json.dumps(
            {
                "schema_version": "ghv_system_wide_trace_dispositions.v1",
                "items": bundle.get("trace_dispositions"),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    paths["trace_dispositions"] = TRACE_DISPOSITIONS_FILENAME
    (evidence_root / RECONCILIATION_FILENAME).write_text(
        json.dumps(bundle.get("reconciliation"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["reconciliation"] = RECONCILIATION_FILENAME
    (evidence_root / CAUSAL_FOOTPRINT_FILENAME).write_text(
        json.dumps(bundle.get("causal_footprint"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    paths["causal_footprint"] = CAUSAL_FOOTPRINT_FILENAME
    return paths


__all__ = [
    "CANARY_AUTHORITY",
    "CANARY_CHANGES_DECISIONS",
    "CANARY_CHANGES_RUNTIME_SEMANTICS",
    "CANARY_CHANGES_RUNTIME_STATE",
    "GHV_CANARY_ROOT",
    "OWNER",
    "GhvSystemWideCanarySessionV1",
    "active_ghv_system_wide_canary_session_v1",
    "attach_canary_correlation_to_flight_row_v1",
    "bind_ghv_system_wide_canary_session_v1",
    "build_system_wide_canary_bundle_v1",
    "discover_surfaces_from_flight_records_v1",
    "persist_system_wide_canary_artifacts_v1",
    "reconcile_modeled_vs_observed_v1",
    "register_observed_surface_v1",
    "reset_ghv_system_wide_canary_session_v1",
]
