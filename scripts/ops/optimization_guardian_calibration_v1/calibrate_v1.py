"""Run the three Optimization instruments on the provisional scope.

B3 acceptance writes only when the caller supplies a directory outside the
repository. Reachability stays UNKNOWN. The four open findings stay open.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.ops.guardian_instrument_binding_v1.bind_v1 import bind_domain_instrument_v1
from scripts.ops.optimization_guardian_scope_v1.scope_v1 import (
    EXPERIMENT_EVIDENCE,
    F1_M9,
    FULL_CORE_ACK,
    INGRESS,
    MEMBERSHIP_RATIFIED,
    OPEN_FINDINGS,
    UNIVERSE,
    build_optimization_scope_v1,
    optimization_nodes_v1,
    optimization_policies_v1,
    optimization_references_v1,
)
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    CENSUS_EMBEDDED_PIN_KEY,
    CENSUS_RELATIVE_PATH,
    CURRENCY_ABSENT,
    CURRENCY_HISTORICAL,
    GRAPH_ABSENT_PIN,
    LANDSCAPE_EMBEDDED_COMMIT_KEY,
    LANDSCAPE_EMBEDDED_TREE_KEY,
    LANDSCAPE_RELATIVE_PATH,
)
from scripts.ops.scoped_domain_graph_evidence_prelude_v1.build_v1 import (
    build_code_reference_prelude_v1,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
AUTHORIZED_COMMIT = "2f07e9cc6d22400f719b5db26ede746c76a9cce0"
AUTHORIZED_TREE = "069d556cdad7393aaab0bf5d51d67e0220fe8d20"


def run_optimization_calibration_v1(
    *,
    output_dir: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = _REPO_ROOT if repo_root is None else repo_root
    scope = build_optimization_scope_v1()
    provenance = _honest_provenance(root)
    prelude = build_code_reference_prelude_v1(
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        nodes=optimization_nodes_v1(),
        references=optimization_references_v1(),
        repo_root=root,
    )
    shared = {
        "authoritative_commit_sha": AUTHORIZED_COMMIT,
        "authoritative_tree_sha": AUTHORIZED_TREE,
        "declared_commit_sha": AUTHORIZED_COMMIT,
        "declared_tree_sha": AUTHORIZED_TREE,
        "provenance": provenance,
        "scope": scope,
    }
    ghv_bound = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHV",
        requested_instrument_type="DOMAIN_GHV",
        adapter_kwargs={
            **shared,
            "candidate_nodes": list(prelude["candidate_nodes"]),
            "candidate_edges": list(prelude["candidate_edges"]),
            "origin_native_id": INGRESS,
            "reverse_origin_native_id": UNIVERSE,
            "policies": optimization_policies_v1(),
            "evidence_prelude": prelude,
        },
    )
    ghv = ghv_bound["adapter_result"] or {}
    graph_bound: dict[str, Any] | None = None
    graph: dict[str, Any] | None = None
    if (
        output_dir is not None
        and ghv.get("status") == "ACCEPTED"
        and ghv.get("composition_invoked")
    ):
        graph_bound = bind_domain_instrument_v1(
            instrument_id="PARENT_OPTIMIZATION_CURRENT_CAUSAL_GRAPH",
            requested_instrument_type="DOMAIN_CURRENT_CAUSAL_GRAPH",
            adapter_kwargs={
                **shared,
                "wp_a1_result": ghv,
                "output_dir": output_dir,
            },
        )
        graph = graph_bound["adapter_result"]
    ghosv_bound = bind_domain_instrument_v1(
        instrument_id="PARENT_OPTIMIZATION_GHOSV",
        requested_instrument_type="DOMAIN_GHOSV",
        adapter_kwargs={
            **shared,
            "findings": _open_findings(),
            "evidence_refs": ["opt-open-findings"],
        },
    )
    ghosv = ghosv_bound["adapter_result"] or {}
    forward = ghv.get("forward") or {}
    evaluated = set(ghv.get("evaluated_nodes") or [])
    return {
        "authority": "NONE",
        "membership_ratified": MEMBERSHIP_RATIFIED,
        "guardian_ratified": False,
        "open_findings": dict(OPEN_FINDINGS),
        "prelude_ok": bool(prelude["ok"]),
        "prelude_reasons": list(prelude["reasons"]),
        "prelude_edge_count": len(prelude["candidate_edges"]),
        "prelude_current_verified": prelude["current_verified"],
        "ghv_status": ghv.get("status"),
        "ghv_coverage_gap": ghv.get("coverage_gap"),
        "ghv_observation_coverage_gap": ghv.get("observation_coverage_gap"),
        "ghv_coverage_proof": ghv.get("coverage_proof"),
        "ghv_authority": ghv.get("authority"),
        "graph_status": None if graph is None else graph.get("status"),
        "graph_integrator_invoked": None if graph is None else graph.get("integrator_invoked"),
        "graph_coverage_gap": None if graph is None else graph.get("coverage_gap"),
        "graph_global_causal_closure_proven": (
            None if graph is None else graph.get("global_causal_closure_proven")
        ),
        "graph_output_dir": None if graph is None else graph.get("output_dir"),
        "ghosv_status": ghosv.get("status"),
        "ghosv_observation_proof": ghosv.get("observation_proof"),
        "ghosv_authority": ghosv.get("authority"),
        "unresolved_kept": EXPERIMENT_EVIDENCE in scope["unresolved"],
        "f1_m9_out_of_scope": F1_M9 in scope["explicitly_out_of_scope"],
        "instrument_ids": {
            "DOMAIN_GHV": ghv_bound["instrument_id"],
            "DOMAIN_CURRENT_CAUSAL_GRAPH": (
                None if graph_bound is None else graph_bound["instrument_id"]
            ),
            "DOMAIN_GHOSV": ghosv_bound["instrument_id"],
        },
        "instrument_bound": all(
            (
                ghv_bound["instrument_bound"],
                ghosv_bound["instrument_bound"],
                graph_bound is None or graph_bound["instrument_bound"],
            )
        ),
        "domain_bound": ghv_bound["domain_bound"] and ghosv_bound["domain_bound"],
        "domain_calibrated": False,
        "current_validated": False,
        "operationally_ready": False,
        "technical_state": "DOMAIN_BOUND",
        "ghv_forward_coverage_gap": forward.get("coverage_gap"),
        "ghv_forward_traversal_completed": forward.get("traversal_completed"),
        "ghv_forward_reachability_proven": forward.get("reachability_proven"),
        "ghv_causal_closure_proven": forward.get("causal_closure_proven"),
        "full_core_reference": {
            "object_id": FULL_CORE_ACK,
            "projected": FULL_CORE_ACK in evaluated,
            "causal_isolation": "NOT_PROVEN",
            "reachability": "UNKNOWN",
        },
    }


def _honest_provenance(repo_root: Path) -> dict[str, dict[str, str]]:
    census = json.loads((repo_root / CENSUS_RELATIVE_PATH).read_text(encoding="utf-8"))
    landscape = json.loads((repo_root / LANDSCAPE_RELATIVE_PATH).read_text(encoding="utf-8"))
    return {
        "census": {"pin": str(census[CENSUS_EMBEDDED_PIN_KEY]), "currency": CURRENCY_HISTORICAL},
        "landscape": {
            "commit_pin": str(landscape[LANDSCAPE_EMBEDDED_COMMIT_KEY]),
            "tree_pin": str(landscape[LANDSCAPE_EMBEDDED_TREE_KEY]),
            "currency": CURRENCY_HISTORICAL,
        },
        "graph": {"pin": GRAPH_ABSENT_PIN, "currency": CURRENCY_ABSENT},
        "domain_evidence": {
            "commit_pin": AUTHORIZED_COMMIT,
            "tree_pin": AUTHORIZED_TREE,
        },
    }


def _open_findings() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for finding_id, state in OPEN_FINDINGS.items():
        rows.append(
            {
                "finding_id": finding_id.lower(),
                "category": "CONTRADICTION",
                "observed_state": state,
                "evidence_ref": "opt-open-findings",
                "affected_scope": UNIVERSE,
                "status": "UNKNOWN",
                "finding_kind": "POLICY",
                "reachability": "UNKNOWN",
            }
        )
    return rows
