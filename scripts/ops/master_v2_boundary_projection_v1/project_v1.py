"""Read-only, fail-closed projection of evidenced Master V2 direct boundaries.

AUTHORITY=NONE. This module does not import productive trading code, does not
regenerate graphs, and does not modify GHV, causal-graph, or GHOSV semantics.
Default execution writes nothing. A filesystem write happens only when the
caller passes an explicit output path.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "master_v2_boundary_projection.v1"
STALE_GRAPH_GIT_HEAD = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_COARSE_PACKAGE = re.compile(r"^SO-[A-Z0-9]+-PKG:[^/]+$")

SUPPORTED_EDGE_TYPES = frozenset(
    {
        "AUTHORIZES",
        "CALL",
        "DATA_FLOW",
        "HANDOFF",
        "OBSERVES",
    }
)
INTERNAL_SUBJECTS = frozenset({"DOUBLE_PLAY", "DYNAMIC_SCOPE", "MASTER_V2"})
FORBIDDEN_MEMBERSHIP_BASES = frozenset(
    {
        "CENSUS_LABEL_ALONE",
        "GRAPH_REACHABILITY",
        "HISTORICAL_UNIVERSE_MAP",
        "IMPORT_RELATIONSHIP",
        "PACKAGE_NAMING_ALONE",
    }
)
CURRENT_EVIDENCE_BASES = frozenset(
    {
        "BOUNDARY_REFERENCE",
        "CURRENT_CONTRACT",
        "EXPLICIT_ENDPOINT_PROVENANCE",
    }
)
EDGE_ROLES = frozenset(
    {
        "BOUNDARY_REFERENCE",
        "CURRENT_CONTRACT",
        "GHV_GRAPH",
        "UNRESOLVED_EDGES",
    }
)
MEMBERSHIP_ROLES = frozenset({"MEMBERSHIP_EVIDENCE"})
_EMBEDDED_HEAD_KEYS = (
    "ACTUAL_SOURCE_SHA",
    "CODE_REVISION",
    "GHV_SOURCE_SHA",
    "IMPLEMENTATION_SOURCE_SHA",
    "TEST_EXECUTION_SHA",
)

OWNER_ARCHITECTURE_REFERENCE: dict[str, Any] = {
    "authority": "OWNER_WP_MV2_BOUNDARY_PROJECTION_V1",
    "category_3_full_owner_lock": (
        "Double Play CURRENT architecture and trading logic remain protected. "
        "This projection does not modify protected logic, contracts, interfaces, "
        "states, parameters, or decision dependencies."
    ),
    "inventory_effect": "NOT_A_COMPONENT_INVENTORY",
    "level_3_enforcement": "DEFERRED",
    "statements": [
        "Master V2 is an independent architecture universe.",
        "Master V2 is the highest system-internal architecture instance.",
        "Double Play is an internal functional area of Master V2.",
        "Dynamic Scope belongs to Double Play.",
    ],
}

TOOL_LIMITATION_CODES = [
    "ACTIVE_REQUIRES_VALID_RUNTIME_OBSERVATION",
    "AUTHORITY_CONSTANT_IS_NOT_AN_INDEPENDENT_CHECK",
    "BASELINE_IS_CALLER_SUPPLIED",
    "COARSE_PACKAGE_ENDPOINTS_ARE_NOT_PRECISE_BOUNDARIES",
    "COMPLETENESS_IS_NOT_INFERRED_FROM_EXISTING_GLOBAL_CLOSURE_FLAGS",
    "THIS_PROJECTION_DOES_NOT_ADJUDICATE_BOUNDARY_COMPLETENESS",
    "DEFAULT_EXECUTION_WRITES_NO_FILES",
    "FIRST_HOP_ONLY",
    "MEMBERSHIP_NOT_INFERRED_FROM_IMPORT_REACHABILITY_PACKAGE_CENSUS_OR_HISTORY",
    "NO_AUTOMATIC_HISTORICAL_FALLBACK",
    "NO_GRAPH_REGENERATION",
    "NO_PRODUCTIVE_TRADING_IMPORTS",
    "UNKNOWN_STATE_IS_NOT_BOOLEAN",
]


def project_master_v2_boundary_v1(bundle: dict[str, Any]) -> dict[str, Any]:
    """Project one caller-supplied evidence bundle. Does not mutate ``bundle``."""
    requested = bundle.get("requested_baseline")
    requested = requested if isinstance(requested, dict) else {}
    baseline_head = requested.get("git_head")
    baseline_tree = requested.get("tree")
    baseline_status = _baseline_status(baseline_head, baseline_tree)
    artifacts = bundle.get("artifacts")
    artifacts = artifacts if isinstance(artifacts, list) else []

    accepted: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            quarantined.append(
                {
                    "artifact_id": f"MISSING-ARTIFACT-ID:{index}",
                    "git_head": None,
                    "reason": "INVALID_ARTIFACT",
                    "tree": None,
                }
            )
            continue
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id:
            artifact_id = f"MISSING-ARTIFACT-ID:{index}"
        provenance = (
            artifact.get("provenance") if isinstance(artifact.get("provenance"), dict) else {}
        )
        if baseline_status != "ACCEPTED":
            quarantined.append(
                {
                    "artifact_id": artifact_id,
                    "git_head": provenance.get("git_head"),
                    "reason": "BASELINE_REJECTED",
                    "tree": provenance.get("tree"),
                }
            )
            continue
        reason = _artifact_reject_reason(artifact, str(baseline_head), str(baseline_tree))
        if reason is None:
            accepted.append(artifact)
        else:
            quarantined.append(
                {
                    "artifact_id": artifact_id,
                    "git_head": provenance.get("git_head"),
                    "reason": reason,
                    "tree": provenance.get("tree"),
                }
            )

    membership = _membership_index(accepted)
    edge_rows = _collect_edges(accepted)
    for row in edge_rows:
        for ref in (row["source_endpoint_ref"], row["target_endpoint_ref"]):
            membership.setdefault(ref, ("UNCLASSIFIED", "NO_MEMBERSHIP_EVIDENCE"))
    runtime = _runtime_index(accepted)

    inbound: list[dict[str, Any]] = []
    outbound: list[dict[str, Any]] = []
    unclassified: list[dict[str, Any]] = []
    excluded_transitive: list[dict[str, Any]] = []
    internal_non_boundary: list[dict[str, Any]] = []
    authority_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    unsupported: set[str] = set()

    for row in edge_rows:
        view = _edge_view(row, membership, runtime)
        authority_rows.append(view["authority"])
        runtime_rows.append(view["runtime"])
        if view["unsupported_token"] is not None:
            unsupported.add(view["unsupported_token"])
        bucket = view["bucket"]
        rendered = view["rendered"]
        if bucket == "INBOUND":
            inbound.append(rendered)
        elif bucket == "OUTBOUND":
            outbound.append(rendered)
        elif bucket == "TRANSITIVE":
            excluded_transitive.append(rendered)
        elif bucket == "INTERNAL":
            internal_non_boundary.append(rendered)
        else:
            unclassified.append(rendered)

    inbound.sort(key=lambda item: item["edge_id"])
    outbound.sort(key=lambda item: item["edge_id"])
    unclassified.sort(key=lambda item: item["edge_id"])
    excluded_transitive.sort(key=lambda item: item["edge_id"])
    internal_non_boundary.sort(key=lambda item: item["edge_id"])
    authority_rows.sort(key=lambda item: item["edge_id"])
    runtime_rows.sort(key=lambda item: item["edge_id"])
    quarantined.sort(key=lambda item: (item["artifact_id"], item["reason"]))

    proof = _accepted_completeness_proof(accepted)
    completeness, missing = _boundary_completeness(
        proof_artifact_present=proof is not None,
        unclassified_count=len(unclassified),
        quarantined_count=len(quarantined),
        unsupported=unsupported,
        accepted_count=len(accepted),
        baseline_status=baseline_status,
    )
    membership_rows = [
        {
            "endpoint_ref": endpoint_ref,
            "membership": classification,
            "reason": reason,
        }
        for endpoint_ref, (classification, reason) in sorted(membership.items())
    ]
    accepted_rows = [
        {
            "artifact_id": str(artifact.get("artifact_id")),
            "git_head": artifact["provenance"]["git_head"],
            "role": artifact.get("role"),
            "tree": artifact["provenance"]["tree"],
        }
        for artifact in sorted(accepted, key=lambda item: str(item.get("artifact_id")))
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "BASELINE": {
            "baseline_status": baseline_status,
            "caller_supplied": True,
            "requested_git_head": baseline_head if isinstance(baseline_head, str) else None,
            "requested_tree": baseline_tree if isinstance(baseline_tree, str) else None,
            "stale_graph_not_current": STALE_GRAPH_GIT_HEAD,
        },
        "INPUT_PROVENANCE": {
            "accepted": accepted_rows,
            "quarantined": quarantined,
        },
        "OWNER_ARCHITECTURE_REFERENCE": copy.deepcopy(OWNER_ARCHITECTURE_REFERENCE),
        "MEMBERSHIP_CLASSIFICATION": membership_rows,
        "INBOUND_BOUNDARY_EDGES": inbound,
        "OUTBOUND_BOUNDARY_EDGES": outbound,
        "UNCLASSIFIED_BOUNDARY_CANDIDATES": unclassified,
        "EXCLUDED_TRANSITIVE_EDGES": excluded_transitive,
        "NON_BOUNDARY_INTERNAL_EDGES": internal_non_boundary,
        "AUTHORITY_EVIDENCE": authority_rows,
        "RUNTIME_EVIDENCE": runtime_rows,
        "COVERAGE_GAPS": {
            "KNOWN_DIRECT_BOUNDARY_EDGES": len(inbound) + len(outbound),
            "UNCLASSIFIED_BOUNDARY_CANDIDATES": len(unclassified),
            "MISSING_COVERAGE": missing,
            "UNSUPPORTED_EDGE_TYPES": sorted(unsupported),
            "BOUNDARY_COMPLETENESS": completeness,
        },
        "BOUNDARY_COMPLETENESS": completeness,
        "EXISTING_GLOBAL_CLOSURE_FLAGS": _echo_global_flags(bundle.get("global_closure_flags")),
        "TOOL_LIMITATIONS": list(TOOL_LIMITATION_CODES),
    }


def main(argv: list[str] | None = None) -> int:
    """Emit one projection report. Write a file only when ``--output`` is set."""
    parser = argparse.ArgumentParser(prog="master_v2_boundary_projection_v1")
    parser.add_argument("--baseline-head", required=True)
    parser.add_argument("--baseline-tree", required=True)
    parser.add_argument("--input", action="append", default=[])
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    artifacts: list[Any] = []
    flags: Any = None
    for raw_path in args.input:
        loaded, flag_part = _load_input(raw_path)
        artifacts.extend(loaded)
        if flag_part is not None and flags is None:
            flags = flag_part
    bundle: dict[str, Any] = {
        "requested_baseline": {"git_head": args.baseline_head, "tree": args.baseline_tree},
        "artifacts": artifacts,
    }
    if flags is not None:
        bundle["global_closure_flags"] = flags
    report = project_master_v2_boundary_v1(bundle)
    rendered = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


def _baseline_status(head: Any, tree: Any) -> str:
    if not isinstance(head, str) or _SHA40.fullmatch(head) is None:
        return "INVALID"
    if not isinstance(tree, str) or _SHA40.fullmatch(tree) is None:
        return "INVALID"
    if head == STALE_GRAPH_GIT_HEAD or head.startswith("b6ffca1d"):
        return "STALE_NOT_CURRENT"
    return "ACCEPTED"


def _artifact_reject_reason(
    artifact: dict[str, Any], baseline_head: str, baseline_tree: str
) -> str | None:
    provenance = artifact.get("provenance")
    if not isinstance(provenance, dict) or "git_head" not in provenance or "tree" not in provenance:
        return "MISSING_PROVENANCE"
    heads, trees = _embedded_pins(artifact)
    heads = [provenance.get("git_head"), *heads]
    trees = [provenance.get("tree"), *trees]
    for value in [*heads, *trees]:
        if not isinstance(value, str) or _SHA40.fullmatch(value) is None:
            return "INVALID_PROVENANCE_PIN"
        if value == STALE_GRAPH_GIT_HEAD or value.startswith("b6ffca1d"):
            return "STALE_GRAPH_NOT_PROMOTED"
    for head in heads:
        if head != baseline_head:
            return "STALE_PROVENANCE"
    for tree in trees:
        if tree != baseline_tree:
            return "STALE_PROVENANCE"
    return None


def _embedded_pins(artifact: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    payload = artifact.get("payload")
    payload = payload if isinstance(payload, dict) else {}
    heads: list[Any] = []
    trees: list[Any] = []
    snapshot = payload.get("code_snapshot")
    if isinstance(snapshot, dict) and "git_head" in snapshot:
        heads.append(snapshot.get("git_head"))
    for key in _EMBEDDED_HEAD_KEYS:
        if key in payload:
            heads.append(payload.get(key))
    record = payload.get("record")
    if isinstance(record, dict):
        for key in _EMBEDDED_HEAD_KEYS:
            if key in record:
                heads.append(record.get(key))
    for edge in _edge_dicts(payload):
        provenance = edge.get("provenance")
        if isinstance(provenance, dict):
            if "CODE_REVISION" in provenance:
                heads.append(provenance.get("CODE_REVISION"))
            if "git_head" in provenance:
                heads.append(provenance.get("git_head"))
            if "tree" in provenance:
                trees.append(provenance.get("tree"))
        for side in ("source_endpoint_provenance", "target_endpoint_provenance"):
            side_provenance = edge.get(side)
            if isinstance(side_provenance, dict):
                if "git_head" in side_provenance:
                    heads.append(side_provenance.get("git_head"))
                if "tree" in side_provenance:
                    trees.append(side_provenance.get("tree"))
    return heads, trees


def _edge_dicts(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    edges = payload.get("edges")
    if not isinstance(edges, list):
        return []
    return [edge for edge in edges if isinstance(edge, dict)]


def _membership_index(accepted: list[dict[str, Any]]) -> dict[str, tuple[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for artifact in sorted(accepted, key=lambda item: str(item.get("artifact_id"))):
        if artifact.get("role") not in MEMBERSHIP_ROLES:
            continue
        payload = artifact.get("payload") if isinstance(artifact.get("payload"), dict) else {}
        records = payload.get("records")
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, dict):
                continue
            endpoint_ref = record.get("endpoint_ref")
            if not isinstance(endpoint_ref, str) or not endpoint_ref:
                continue
            grouped.setdefault(endpoint_ref, []).append(record)
    return {
        endpoint_ref: _classify_membership(records) for endpoint_ref, records in grouped.items()
    }


def _classify_membership(records: list[dict[str, Any]]) -> tuple[str, str]:
    results = [_classify_membership_record(record) for record in records]
    if any(reason == "COARSE_ENDPOINT" for _, reason in results):
        return "UNCLASSIFIED", "COARSE_ENDPOINT"
    if any(reason == "FORBIDDEN_MEMBERSHIP_BASIS" for _, reason in results):
        return "UNCLASSIFIED", "FORBIDDEN_MEMBERSHIP_BASIS"
    accepted = {classification for classification, reason in results if reason == "ACCEPTED"}
    if len(accepted) == 1:
        return next(iter(accepted)), "ACCEPTED"
    if len(accepted) > 1:
        return "UNCLASSIFIED", "MEMBERSHIP_CONFLICT"
    return "UNCLASSIFIED", results[0][1]


def _classify_membership_record(record: dict[str, Any]) -> tuple[str, str]:
    endpoint_ref = record.get("endpoint_ref")
    precision = record.get("endpoint_precision")
    precision_text = precision if isinstance(precision, str) else None
    if not isinstance(endpoint_ref, str) or not endpoint_ref:
        return "UNCLASSIFIED", "MISSING_ENDPOINT_REF"
    if _is_coarse(endpoint_ref, precision_text):
        return "UNCLASSIFIED", "COARSE_ENDPOINT"
    if not _is_precise(endpoint_ref, precision_text):
        return "UNCLASSIFIED", "ENDPOINT_PRECISION_NOT_PROVEN"
    bases = record.get("evidence_bases")
    if not isinstance(bases, list) or not bases or not all(isinstance(item, str) for item in bases):
        return "UNCLASSIFIED", "MISSING_EVIDENCE_BASES"
    base_set = set(bases)
    if base_set & FORBIDDEN_MEMBERSHIP_BASES:
        return "UNCLASSIFIED", "FORBIDDEN_MEMBERSHIP_BASIS"
    proposed = record.get("proposed_class")
    if proposed == "MASTER_V2_INTERNAL":
        if "OWNER_ARCHITECTURE_BINDING" not in base_set:
            return "UNCLASSIFIED", "OWNER_ARCHITECTURE_BINDING_REQUIRED"
        if record.get("owner_architecture_subject") not in INTERNAL_SUBJECTS:
            return "UNCLASSIFIED", "OWNER_ARCHITECTURE_SUBJECT_NOT_BOUND"
        if not (base_set & CURRENT_EVIDENCE_BASES):
            return "UNCLASSIFIED", "CURRENT_EVIDENCE_REQUIRED"
        return "MASTER_V2_INTERNAL", "ACCEPTED"
    if proposed == "DIRECT_EXTERNAL_COUNTERPARTY":
        if "IMMEDIATE_COUNTERPARTY_EVIDENCE" not in base_set:
            return "UNCLASSIFIED", "IMMEDIATE_COUNTERPARTY_EVIDENCE_REQUIRED"
        if not (base_set & CURRENT_EVIDENCE_BASES):
            return "UNCLASSIFIED", "CURRENT_EVIDENCE_REQUIRED"
        return "DIRECT_EXTERNAL_COUNTERPARTY", "ACCEPTED"
    return "UNCLASSIFIED", "UNKNOWN_OR_MISSING_CLASS"


def _is_coarse(endpoint_ref: str, precision: str | None) -> bool:
    if precision in {"COARSE", "PACKAGE"}:
        return True
    return _COARSE_PACKAGE.fullmatch(endpoint_ref) is not None


def _is_precise(endpoint_ref: str, precision: str | None) -> bool:
    if _is_coarse(endpoint_ref, precision):
        return False
    if precision == "PRECISE":
        return "/" in endpoint_ref or endpoint_ref.endswith(".py")
    return False


def _collect_edges(accepted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in sorted(accepted, key=lambda item: str(item.get("artifact_id"))):
        role = artifact.get("role")
        if role not in EDGE_ROLES:
            continue
        payload = artifact.get("payload") if isinstance(artifact.get("payload"), dict) else {}
        for index, edge in enumerate(_edge_dicts(payload)):
            edge_id = edge.get("edge_id")
            if not isinstance(edge_id, str) or not edge_id:
                edge_id = f"MISSING-EDGE-ID:{artifact.get('artifact_id')}:{index}"
            rows.append(
                {
                    "artifact_id": str(artifact.get("artifact_id")),
                    "edge": edge,
                    "edge_id": edge_id,
                    "force_unresolved": role == "UNRESOLVED_EDGES"
                    or not isinstance(edge.get("edge_id"), str),
                    "role": role,
                    "source_endpoint_ref": _endpoint_ref(edge, "source"),
                    "target_endpoint_ref": _endpoint_ref(edge, "target"),
                }
            )
    return rows


def _endpoint_ref(edge: dict[str, Any], side: str) -> str:
    provenance = edge.get(f"{side}_endpoint_provenance")
    if isinstance(provenance, dict) and isinstance(provenance.get("endpoint_ref"), str):
        return provenance["endpoint_ref"]
    direct = edge.get(f"{side}_endpoint_ref")
    if isinstance(direct, str):
        return direct
    return f"MISSING-{side.upper()}-ENDPOINT"


def _endpoint_precision(edge: dict[str, Any], side: str) -> str | None:
    provenance = edge.get(f"{side}_endpoint_provenance")
    if isinstance(provenance, dict) and isinstance(provenance.get("precision"), str):
        return provenance["precision"]
    return None


def _runtime_index(accepted: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for artifact in accepted:
        if artifact.get("role") != "RUNTIME_OBSERVATION":
            continue
        payload = artifact.get("payload") if isinstance(artifact.get("payload"), dict) else {}
        observations = payload.get("observations")
        if not isinstance(observations, list):
            continue
        for observation in observations:
            if not isinstance(observation, dict):
                continue
            edge_id = observation.get("edge_id")
            if isinstance(edge_id, str) and edge_id:
                grouped.setdefault(edge_id, []).append(observation)
    return grouped


def _edge_view(
    row: dict[str, Any],
    membership: dict[str, tuple[str, str]],
    runtime: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    edge = row["edge"]
    source_ref = row["source_endpoint_ref"]
    target_ref = row["target_endpoint_ref"]
    source_class = membership.get(source_ref, ("UNCLASSIFIED", "NO_MEMBERSHIP_EVIDENCE"))[0]
    target_class = membership.get(target_ref, ("UNCLASSIFIED", "NO_MEMBERSHIP_EVIDENCE"))[0]
    source_precision = _endpoint_precision(edge, "source")
    target_precision = _endpoint_precision(edge, "target")
    coarse = _is_coarse(source_ref, source_precision) or _is_coarse(target_ref, target_precision)
    imprecise = not _is_precise(source_ref, source_precision) or not _is_precise(
        target_ref, target_precision
    )
    typed = edge.get("typed_edge") if isinstance(edge.get("typed_edge"), dict) else {}
    edge_type = typed.get("edge_type")
    if not isinstance(edge_type, str) or not edge_type:
        unsupported_token: str | None = "MISSING_EDGE_TYPE"
    elif edge_type not in SUPPORTED_EDGE_TYPES:
        unsupported_token = edge_type
    else:
        unsupported_token = None
    states = edge.get("state_evidence") if isinstance(edge.get("state_evidence"), dict) else {}
    active = _active_state(runtime.get(row["edge_id"], []))
    rendered = {
        "edge_id": row["edge_id"],
        "source_endpoint_ref": source_ref,
        "target_endpoint_ref": target_ref,
        "source_membership": source_class,
        "target_membership": target_class,
        "edge_type": edge_type if isinstance(edge_type, str) and edge_type else None,
        "EXISTS": _tri_state(states.get("EXISTS")),
        "WIRED": _tri_state(states.get("WIRED")),
        "REACHABLE": _tri_state(states.get("REACHABLE")),
        "ACTIVE": active,
        "data_transfer": _tri_state(states.get("DATA_TRANSFER")),
        "authority_transfer": _authority_transfer(edge),
        "input_artifact_id": row["artifact_id"],
    }
    authority = {
        "edge_id": row["edge_id"],
        "trading_authority_implied_constant": _constant_authority(typed),
        "constant_is_proof": False,
        "authority_transfer": rendered["authority_transfer"],
        "data_transfer": rendered["data_transfer"],
    }
    runtime_row = {
        "edge_id": row["edge_id"],
        "ACTIVE": active,
        "runtime_observation_count": len(runtime.get(row["edge_id"], [])),
        "static_evidence_is_active": False,
    }
    bucket = _bucket(
        edge=edge,
        source_class=source_class,
        target_class=target_class,
        coarse=coarse,
        imprecise=imprecise,
        force_unresolved=row["force_unresolved"],
    )
    if bucket == "INBOUND":
        rendered["classification"] = "INBOUND_BOUNDARY_EDGE"
    elif bucket == "OUTBOUND":
        rendered["classification"] = "OUTBOUND_BOUNDARY_EDGE"
    elif bucket == "TRANSITIVE":
        rendered["classification"] = "EXCLUDED_TRANSITIVE"
    elif bucket == "INTERNAL":
        rendered["classification"] = "NON_BOUNDARY_INTERNAL"
    else:
        rendered["classification"] = "UNCLASSIFIED_BOUNDARY_CANDIDATE"
    return {
        "bucket": bucket,
        "rendered": rendered,
        "authority": authority,
        "runtime": runtime_row,
        "unsupported_token": unsupported_token,
    }


def _bucket(
    *,
    edge: dict[str, Any],
    source_class: str,
    target_class: str,
    coarse: bool,
    imprecise: bool,
    force_unresolved: bool,
) -> str:
    hop = edge.get("hop_distance", 1)
    transitive = edge.get("transitive") is True
    if isinstance(hop, int) and hop > 1:
        transitive = True
    if transitive and isinstance(hop, int):
        return "TRANSITIVE"
    if edge.get("transitive") is True:
        return "TRANSITIVE"
    if (
        source_class == "DIRECT_EXTERNAL_COUNTERPARTY"
        and target_class == "DIRECT_EXTERNAL_COUNTERPARTY"
    ):
        return "TRANSITIVE"
    if not isinstance(hop, int) or hop != 1:
        return "UNCLASSIFIED"
    if coarse or imprecise or force_unresolved:
        return "UNCLASSIFIED"
    if source_class == "DIRECT_EXTERNAL_COUNTERPARTY" and target_class == "MASTER_V2_INTERNAL":
        return "INBOUND"
    if source_class == "MASTER_V2_INTERNAL" and target_class == "DIRECT_EXTERNAL_COUNTERPARTY":
        return "OUTBOUND"
    if source_class == "MASTER_V2_INTERNAL" and target_class == "MASTER_V2_INTERNAL":
        return "INTERNAL"
    return "UNCLASSIFIED"


def _tri_state(block: Any) -> str:
    if not isinstance(block, dict):
        return "UNKNOWN"
    if "supported" not in block or "evidence_ref" not in block:
        return "UNKNOWN"
    evidence_ref = block.get("evidence_ref")
    if not isinstance(evidence_ref, str) or not evidence_ref.strip():
        return "UNKNOWN"
    supported = block.get("supported")
    if supported is True:
        return "TRUE"
    if supported is False:
        return "FALSE"
    return "UNKNOWN"


def _active_state(observations: list[dict[str, Any]]) -> str:
    verdicts: list[str] = []
    for observation in observations:
        if observation.get("evidence_class") != "RUNTIME_OBSERVATION":
            continue
        if observation.get("static_or_contract") is True:
            continue
        if observation.get("observation_valid") is not True:
            continue
        evidence_ref = observation.get("evidence_ref")
        if not isinstance(evidence_ref, str) or not evidence_ref.strip():
            continue
        observed = observation.get("active_observed")
        if observed is True:
            verdicts.append("TRUE")
        elif observed is False:
            verdicts.append("FALSE")
    unique = set(verdicts)
    if len(unique) == 1:
        return next(iter(unique))
    return "UNKNOWN"


def _constant_authority(typed: dict[str, Any]) -> Any:
    if "trading_authority_implied" not in typed:
        return "ABSENT"
    value = typed.get("trading_authority_implied")
    if isinstance(value, bool):
        return value
    return "ABSENT"


def _authority_transfer(edge: dict[str, Any]) -> str:
    check = edge.get("authority_transfer_check")
    if not isinstance(check, dict):
        return "NOT_PROVEN"
    evidence_ref = check.get("evidence_ref")
    if (
        check.get("basis") == "AUTHORITY_TRANSFER_CHECKED"
        and check.get("independent_of_trading_authority_implied_constant") is True
        and isinstance(evidence_ref, str)
        and evidence_ref.strip()
        and check.get("result") in {"NOT_PROVEN", "PROVEN_ABSENT", "PROVEN_PRESENT"}
    ):
        return str(check["result"])
    return "NOT_PROVEN"


def _accepted_completeness_proof(accepted: list[dict[str, Any]]) -> dict[str, Any] | None:
    proofs = [
        artifact.get("payload")
        for artifact in accepted
        if artifact.get("role") == "INDEPENDENT_BOUNDARY_COMPLETENESS_PROOF"
        and isinstance(artifact.get("payload"), dict)
    ]
    if len(proofs) != 1:
        return None
    proof = proofs[0]
    evidence_ref = proof.get("evidence_ref")
    if (
        proof.get("proof_independent") is True
        and proof.get("completeness_claim") == "ALL_DIRECT_TECHNICAL_BOUNDARY_EDGES_KNOWN"
        and isinstance(evidence_ref, str)
        and evidence_ref.strip()
    ):
        return proof
    return None


def _boundary_completeness(
    *,
    proof_artifact_present: bool,
    unclassified_count: int,
    quarantined_count: int,
    unsupported: set[str],
    accepted_count: int,
    baseline_status: str,
) -> tuple[str, list[str]]:
    missing: list[str] = []
    if baseline_status != "ACCEPTED":
        missing.append("BASELINE_REJECTED")
    if accepted_count == 0:
        missing.append("NO_ACCEPTED_EVIDENCE")
    if quarantined_count:
        missing.append("QUARANTINED_EVIDENCE")
    if unclassified_count:
        missing.append("UNCLASSIFIED_BOUNDARY_CANDIDATES_PRESENT")
    if unsupported:
        missing.append("UNSUPPORTED_OR_MISSING_EDGE_TYPES")
    if proof_artifact_present:
        missing.append("COMPLETENESS_PROOF_NOT_ADJUDICATED_BY_THIS_PROJECTION")
    else:
        missing.append("NO_INDEPENDENT_COMPLETENESS_PROOF")
    return "NOT_PROVEN", sorted(set(missing))


def _echo_global_flags(flags: Any) -> dict[str, Any] | None:
    if not isinstance(flags, dict):
        return None
    return {key: copy.deepcopy(flags[key]) for key in sorted(flags)}


def _load_input(raw_path: str) -> tuple[list[Any], Any]:
    path = Path(raw_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return (
            [
                {
                    "artifact_id": f"UNREADABLE:{path.name}",
                    "role": "UNREADABLE_INPUT",
                }
            ],
            None,
        )
    if isinstance(payload, dict) and isinstance(payload.get("artifacts"), list):
        return list(payload["artifacts"]), payload.get("global_closure_flags")
    if isinstance(payload, dict):
        return [payload], None
    if isinstance(payload, list):
        return list(payload), None
    return ([{"artifact_id": f"UNREADABLE:{path.name}", "role": "UNREADABLE_INPUT"}], None)


if __name__ == "__main__":
    raise SystemExit(main())
