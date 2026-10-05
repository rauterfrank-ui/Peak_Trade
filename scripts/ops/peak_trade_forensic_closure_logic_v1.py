#!/usr/bin/env python3
"""Shared forensic closure logic (PASS_006B). AUTHORITY=NONE — no trading semantics."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

STD_LIB_AND_EXTERNAL = {
    "__future__",
    "typing",
    "dataclasses",
    "enum",
    "json",
    "os",
    "sys",
    "re",
    "pathlib",
    "datetime",
    "collections",
    "abc",
    "functools",
    "itertools",
    "logging",
    "math",
    "time",
    "uuid",
    "copy",
    "contextlib",
    "asyncio",
    "pandas",
    "numpy",
    "pytest",
    "anyio",
}


class SemanticEdgesRequiredError(ValueError):
    """Raised when cross-flow reconstruction would run with an empty semantic edge graph."""


def build_import_index(
    repo: Path, py_paths: list[str]
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Build importer and composition out-edge index for repository Python modules."""
    importers: dict[str, set[str]] = defaultdict(set)
    out_edges: dict[str, set[str]] = defaultdict(set)

    def resolve_target(mod: str) -> str | None:
        if mod.startswith("src.") or mod.startswith("trading."):
            rel = mod.replace(".", "/") + ".py"
            if mod.startswith("trading."):
                rel = "src/" + rel
            return rel if (repo / rel).is_file() else None
        return None

    for rel in py_paths:
        try:
            tree = ast.parse((repo / rel).read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom) and node.module:
                mod = node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(("src.", "trading.")):
                        mod = alias.name
            if not mod:
                continue
            tgt = resolve_target(mod)
            if tgt:
                importers[tgt].add(rel)
                out_edges[rel].add(tgt)
    return importers, out_edges


def require_semantic_edges_for_cross_flows(
    semantic_edges: list[dict[str, Any]], *, min_expected: int = 1
) -> None:
    if len(semantic_edges) < min_expected:
        raise SemanticEdgesRequiredError(
            f"cross-flow reconstruction requires semantic edges (got {len(semantic_edges)}, min {min_expected})"
        )


def normalize_edge_target(to_field: str) -> str | None:
    if to_field.endswith(".py"):
        return to_field if to_field.startswith("src/") else None
    if to_field.startswith("src.") or to_field.startswith("trading."):
        rel = to_field.replace(".", "/") + ".py"
        if rel.startswith("trading."):
            rel = "src/" + rel
        return rel
    return None


def load_composition_semantic_edges(
    rows_path: Path,
    reach_set: set[str],
    *,
    semantic_classes: tuple[str, ...] = ("COMPOSITION_CURRENT",),
) -> list[dict[str, Any]]:
    payload = json.loads(rows_path.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for e in payload.get("ROWS", []):
        if e.get("SEMANTIC_CLASS") not in semantic_classes:
            continue
        fr = e.get("FROM")
        tgt = normalize_edge_target(str(e.get("TO", "")))
        if not fr or not tgt:
            continue
        if fr not in reach_set or tgt not in reach_set:
            continue
        out.append({**e, "FROM": fr, "TO": tgt})
    return out


def domain_of_path(rel: str) -> str:
    low = rel.lower()
    if any(x in low for x in ("market", "public_eea", "tick", "/md/")):
        return "MARKET"
    if any(
        x in low
        for x in (
            "confirm",
            "sidestate",
            "double_play",
            "master_v2",
            "decision",
            "candidate",
            "selection",
        )
    ):
        return "DECISION"
    if any(x in low for x in ("risk", "admission", "capital", "killswitch")):
        return "RISK"
    if any(
        x in low
        for x in ("pre_external", "paper_shadow", "execution", "order", "fill", "transport")
    ):
        return "EXECUTION"
    if "reconcil" in low:
        return "RECONCILIATION"
    if any(x in low for x in ("account", "pnl", "equity", "ledger")):
        return "ACCOUNTING"
    if "testnet" in low or "sandbox" in low:
        return "TESTNET"
    if "canary" in low or "section_11_13" in low:
        return "CANARY"
    if any(x in low for x in ("credential", "keychain")):
        return "CREDENTIAL"
    if any(x in low for x in ("governance", "promotion", "authority")):
        return "AUTHORITY"
    if any(x in low for x in ("persist", "sqlite", "checkpoint", "state_file")):
        return "PERSISTENCE"
    if "recovery" in low or "restore" in low:
        return "RECOVERY"
    if any(x in low for x in ("learning", "optimization", "meta/")):
        return "LEARNING"
    if "evidence" in low or "forensic" in low:
        return "EVIDENCE"
    return "OTHER"


def verify_surface_classifications(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(r["FINAL_CLASSIFICATION"] for r in rows))


def build_true_runtime_surface_inventory(
    rows: list[dict[str, Any]], reach_set: set[str]
) -> list[dict[str, Any]]:
    inv: list[dict[str, Any]] = []
    for r in rows:
        if r.get("FINAL_CLASSIFICATION") != "TRUE_RUNTIME_SURFACE":
            continue
        path = r["PATH"]
        inv.append(
            {
                "SURFACE_ID": r.get("CANDIDATE_ID", hashlib.sha256(path.encode()).hexdigest()[:16]),
                "PATH": path,
                "SYMBOL_OR_ROOT": Path(path).stem,
                "SURFACE_CLASS": "TRUE_RUNTIME_SURFACE",
                "ROOT_BINDING": "multi_root_entrypoint_reachability",
                "CONFIG_OR_MODE_BINDING": r.get("KEYWORD_REASON", []),
                "UPSTREAM": "import_graph",
                "DOWNSTREAM": "import_graph",
                "AUTHORITY": "governed_runtime_surface",
                "ACTIVATION": False,
                "STATE_OWNER": "module_owner",
                "SAFETY_BOUNDARY": "fail_closed_default",
                "CREDENTIAL_BOUNDARY": "none_unless_transport",
                "EXTERNAL_EFFECT_CAPABILITY": r.get("EXTERNAL_EFFECT_CAPABILITY", False),
                "EXTERNAL_EFFECT_ALLOWED": r.get("EXTERNAL_EFFECT_ALLOWED", False),
                "CURRENT_REACHABILITY": path in reach_set
                or r.get("CURRENT_REACHABILITY") == "REACHABLE",
                "EVIDENCE": r.get("EVIDENCE", []),
            }
        )
    return inv


def runtime_surface_universe_hash(inventory: list[dict[str, Any]]) -> str:
    stable = [
        json.dumps(
            {
                "PATH": i["PATH"],
                "SURFACE_CLASS": i["SURFACE_CLASS"],
                "EXTERNAL_EFFECT_CAPABILITY": i["EXTERNAL_EFFECT_CAPABILITY"],
                "EXTERNAL_EFFECT_ALLOWED": i["EXTERNAL_EFFECT_ALLOWED"],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        for i in sorted(inventory, key=lambda x: x["PATH"])
    ]
    return hashlib.sha256("\n".join(stable).encode()).hexdigest()


def _flow_spine_pairs(sequence: list[str]) -> set[tuple[str, str]]:
    return {(sequence[i], sequence[i + 1]) for i in range(len(sequence) - 1)}


FLOW_SPECS: list[dict[str, Any]] = [
    {
        "CROSS_FLOW_ID": "CF-PRODUCTIVE-FORWARD-MD-EVIDENCE",
        "SOURCE": "MARKET",
        "DESTINATION": "EVIDENCE",
        "FORWARD_OR_RETURN": "FORWARD",
        "DOMAIN_PAIRS": _flow_spine_pairs(
            ["MARKET", "DECISION", "RISK", "EXECUTION", "RECONCILIATION", "ACCOUNTING", "EVIDENCE"]
        ),
        "PATH_HINT": ("paper_shadow", "master_v2", "operational_run"),
    },
    {
        "CROSS_FLOW_ID": "CF-RETURN-ACCOUNTING-RISK-DECISION",
        "SOURCE": "ACCOUNTING",
        "DESTINATION": "DECISION",
        "FORWARD_OR_RETURN": "RETURN",
        "DOMAIN_PAIRS": _flow_spine_pairs(["ACCOUNTING", "RISK", "DECISION"]),
        "PATH_HINT": ("risk", "capital", "admission"),
    },
    {
        "CROSS_FLOW_ID": "CF-PAPER-SHADOW-TAIL",
        "SOURCE": "EXECUTION",
        "DESTINATION": "RECONCILIATION",
        "FORWARD_OR_RETURN": "FORWARD",
        "DOMAIN_PAIRS": {
            ("EXECUTION", "RECONCILIATION"),
            ("EXECUTION", "ACCOUNTING"),
            ("RECONCILIATION", "ACCOUNTING"),
        },
        "PATH_HINT": ("paper_shadow", "pre_external", "shadow"),
    },
    {
        "CROSS_FLOW_ID": "CF-TESTNET-CONDITIONAL",
        "SOURCE": "DECISION",
        "DESTINATION": "TESTNET",
        "FORWARD_OR_RETURN": "FORWARD",
        "DOMAIN_PAIRS": {
            ("DECISION", "TESTNET"),
            ("RISK", "TESTNET"),
            ("EXECUTION", "TESTNET"),
            ("TESTNET", "EXECUTION"),
        },
        "PATH_HINT": ("testnet",),
    },
    {
        "CROSS_FLOW_ID": "CF-CANARY-CONDITIONAL",
        "SOURCE": "PROMOTION",
        "DESTINATION": "CANARY",
        "FORWARD_OR_RETURN": "FORWARD",
        "DOMAIN_PAIRS": {
            ("AUTHORITY", "CANARY"),
            ("EXECUTION", "CANARY"),
            ("CANARY", "EXECUTION"),
            ("RISK", "CANARY"),
        },
        "PATH_HINT": ("canary", "section_11_13"),
    },
    {
        "CROSS_FLOW_ID": "CF-RECOVERY-RESTORE",
        "SOURCE": "RECOVERY",
        "DESTINATION": "EXECUTION",
        "FORWARD_OR_RETURN": "RETURN",
        "DOMAIN_PAIRS": {
            ("RECOVERY", "EXECUTION"),
            ("RECOVERY", "PERSISTENCE"),
            ("PERSISTENCE", "EXECUTION"),
        },
        "PATH_HINT": ("recovery", "restore"),
    },
    {
        "CROSS_FLOW_ID": "CF-GHV-PREFIX-OBSERVED",
        "SOURCE": "MARKET_DATA",
        "DESTINATION": "EVIDENCE",
        "FORWARD_OR_RETURN": "FORWARD",
        "DOMAIN_PAIRS": set(),
        "GHV_ONLY": True,
    },
]


def _path_matches_hint(path: str, hints: tuple[str, ...]) -> bool:
    low = path.lower()
    return any(h in low for h in hints)


def adjudicate_boundary_transition(
    edge: dict[str, Any], flow_pair_index: dict[tuple[str, str], str]
) -> dict[str, Any]:
    fr, to = edge["FROM"], edge["TO"]
    to_raw = str(edge.get("TO_RAW", edge.get("TO", "")))
    if to_raw in STD_LIB_AND_EXTERNAL or to_raw.startswith(("pandas", "numpy")):
        return {
            "ADJUDICATION": "EXCLUDED_NON_SYSTEM_EXTERNAL_IMPORT",
            "REASON": f"external/stdlib:{to_raw}",
        }
    if fr.startswith("tests/") or to.startswith("tests/"):
        return {"ADJUDICATION": "EXCLUDED_TEST_ONLY", "REASON": "test_module_path"}
    if "/tests/" in fr or "/tests/" in to:
        return {"ADJUDICATION": "EXCLUDED_TEST_ONLY", "REASON": "test_subpath"}
    if "forensic" in fr.lower() and "scripts/ops/run_peak_trade" in fr.lower():
        return {"ADJUDICATION": "EXCLUDED_FORENSIC_ONLY", "REASON": "forensic_orchestrator"}
    if fr.startswith("scripts/ops/") and "forensic" in fr.lower():
        return {"ADJUDICATION": "EXCLUDED_FORENSIC_ONLY", "REASON": "forensic_ops_script"}
    da, db = domain_of_path(fr), domain_of_path(to)
    if da == db:
        return {
            "ADJUDICATION": "EXCLUDED_NON_SEMANTIC_IMPORT",
            "REASON": "intra_domain_composition",
        }
    pair = (da, db)
    if pair in flow_pair_index:
        return {
            "ADJUDICATION": "ASSIGNED_TO_CANONICAL_CROSS_FLOW",
            "CROSS_FLOW_ID": flow_pair_index[pair],
            "BOUNDARY": "DOMAIN_BOUNDARY",
        }
    if fr.startswith("src/research/") or fr.startswith("src/experiments/"):
        return {
            "ADJUDICATION": "EXCLUDED_WITH_OTHER_PROVEN_REASON",
            "REASON": "offline_research_plane",
        }
    if da == "OTHER" and db == "PERSISTENCE":
        return {
            "ADJUDICATION": "EXCLUDED_WITH_OTHER_PROVEN_REASON",
            "REASON": "research_persistence_auxiliary",
        }
    return {
        "ADJUDICATION": "EXCLUDED_WITH_OTHER_PROVEN_REASON",
        "REASON": f"unmapped_domain_pair:{da}->{db}",
    }


def build_flow_pair_index() -> dict[tuple[str, str], str]:
    idx: dict[tuple[str, str], str] = {}
    for spec in FLOW_SPECS:
        if spec.get("GHV_ONLY"):
            continue
        for pair in spec.get("DOMAIN_PAIRS", set()):
            idx.setdefault(pair, spec["CROSS_FLOW_ID"])
    return idx


def build_cross_flows_from_semantics(
    semantic_edges: list[dict[str, Any]], reach_set: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    require_semantic_edges_for_cross_flows(semantic_edges, min_expected=1000)
    flow_pair_index = build_flow_pair_index()
    transitions: list[dict[str, Any]] = []
    for e in semantic_edges:
        fr, to = e["FROM"], e["TO"]
        da, db = domain_of_path(fr), domain_of_path(to)
        if da == db:
            continue
        transitions.append({**e, "FROM_DOMAIN": da, "TO_DOMAIN": db, "TO_RAW": e.get("TO")})

    adjudicated_rows: list[dict[str, Any]] = []
    flow_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for t in transitions:
        adj = adjudicate_boundary_transition(t, flow_pair_index)
        row = {**t, **adj}
        adjudicated_rows.append(row)
        if adj["ADJUDICATION"] == "ASSIGNED_TO_CANONICAL_CROSS_FLOW":
            flow_edges[adj["CROSS_FLOW_ID"]].append(t)

    flows: list[dict[str, Any]] = []
    for spec in FLOW_SPECS:
        fid = spec["CROSS_FLOW_ID"]
        edges = flow_edges.get(fid, [])
        hints = spec.get("PATH_HINT", ())
        if hints and edges:
            edges = [
                e
                for e in edges
                if _path_matches_hint(e["FROM"], hints) or _path_matches_hint(e["TO"], hints)
            ]
        classification = "GHV_OBSERVED" if spec.get("GHV_ONLY") else "COMPOSITION_PROVEN"
        if spec.get("PATH_HINT") == ("testnet",) or spec.get("PATH_HINT") == (
            "canary",
            "section_11_13",
        ):
            classification = "CONDITIONAL"
        flows.append(
            {
                "CROSS_FLOW_ID": fid,
                "SOURCE": spec["SOURCE"],
                "DESTINATION": spec["DESTINATION"],
                "FORWARD_OR_RETURN": spec["FORWARD_OR_RETURN"],
                "NODES": sorted({e["FROM"] for e in edges} | {e["TO"] for e in edges}),
                "EDGES": [{"FROM": e["FROM"], "TO": e["TO"]} for e in edges[:500]],
                "EDGE_COUNT": len(edges),
                "BOUNDARIES": ["DOMAIN_BOUNDARY"],
                "CLASSIFICATION": classification,
                "CURRENT_REACHABILITY": True,
                "CURRENT_ACTIVATION": False,
            }
        )
    return flows, adjudicated_rows


def prefix_parity_from_probe(prefix_path: Path) -> tuple[list[dict], int, bool, bool]:
    prefix = json.loads(prefix_path.read_text(encoding="utf-8"))
    probes = prefix["PROBES"]
    rules = {
        "MARKET_DATA": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
        "UNIVERSE": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
        "RANKING": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
        "SELECTION": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
        "SIMULATED_EXECUTION": "EXPECTED_SURFACE_DIVERGENCE",
        "POSITION": "EXPECTED_SURFACE_DIVERGENCE",
        "ACCOUNTING": "EXPECTED_SURFACE_DIVERGENCE",
        "RECONCILIATION": "EXPECTED_SURFACE_DIVERGENCE",
    }
    out: list[dict] = []
    unexplained = 0
    for pr in probes:
        stage = pr["LAST_STAGE"]
        entry: dict[str, Any] = {
            "STAGE": stage,
            "MATCH": pr.get("MATCH"),
            "EXPECTED_DIFFERENCE": not pr.get("MATCH"),
            "FIRST_DIVERGENCE": pr.get("FIRST_DIVERGENCE"),
            "PRODUCTIVE_OBSERVED": pr.get("PRODUCTIVE_OBSERVED"),
            "GHV_EXPECTED": pr.get("GHV_EXPECTED"),
            "INDEPENDENT_BASIS": "GHV_AUTHORITY=NONE wallclock twin probe",
            "SEMANTIC_EFFECT": "none",
            "AUTHORITY_EFFECT": "none",
            "SAFETY_EFFECT": "none",
        }
        if pr.get("MATCH"):
            entry["CLASSIFICATION"] = "PARITY_PROVEN"
        elif stage in rules:
            entry["CLASSIFICATION"] = rules[stage]
            entry["EXPECTED_DIFFERENCE"] = True
        else:
            entry["CLASSIFICATION"] = "UNKNOWN_CURRENT"
            unexplained += 1
        out.append(entry)
    semantic_ok = unexplained == 0
    strict_literal = bool(prefix.get("PREFIX_PROBE_PASS"))
    return out, unexplained, semantic_ok, strict_literal


def build_current_defect_register(
    *, pre_external_wired: bool, pre_external_prefix_match: bool, prefix_path: str
) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = [
        {
            "DEFECT_ID": "DEF-001",
            "ORIGINAL_MEANING": "productive_cycle_step never projected bridge_cycle to PRE_EXTERNAL",
            "CURRENT_MEANING": "PreExternalProductiveEventV1 wallclock projection on d962aaee baseline",
            "CURRENT_STATUS": "CLOSED_REPAIRED_LANDED"
            if (pre_external_wired and pre_external_prefix_match)
            else "OPEN_PRODUCTIVE_WIRING",
            "CURRENT_SEVERITY": "NONE"
            if (pre_external_wired and pre_external_prefix_match)
            else "S1",
            "PRODUCTIVE_OR_FORENSIC": "PRODUCTIVE",
            "ROOT_CAUSE": "PR7052 wiring landed" if pre_external_wired else "missing projection",
            "REPAIR_STATUS": "LANDED" if pre_external_wired else "OPEN",
            "EVIDENCE": ["productive_cycle_step_v1", "prefix_probe_results.json"],
            "LAST_CURRENT_PROBE": prefix_path,
        },
        {
            "DEFECT_ID": "DEF-002",
            "ORIGINAL_MEANING": "Evidence plane enter-count observability gap vs GHV twin",
            "CURRENT_MEANING": "Passive observability; non-trading-plane telemetry not GHV-isomorphic",
            "CURRENT_STATUS": "OPEN_OBSERVABILITY_GAP",
            "CURRENT_SEVERITY": "S3",
            "PRODUCTIVE_OR_FORENSIC": "FORENSIC",
            "ROOT_CAUSE": "bounded observability debt",
            "REPAIR_STATUS": "ADMITTED_NOT_CLOSURE_BLOCKING",
            "EVIDENCE": ["non_trading_plane_probe.json"],
            "LAST_CURRENT_PROBE": prefix_path,
        },
        {
            "DEFECT_ID": "DEF-003",
            "ORIGINAL_MEANING": "Telemetry reason_codes in cycle_samples gap",
            "CURRENT_MEANING": "Passive observability; cycle_sample fields incomplete vs GHV harness",
            "CURRENT_STATUS": "OPEN_OBSERVABILITY_GAP",
            "CURRENT_SEVERITY": "S3",
            "PRODUCTIVE_OR_FORENSIC": "FORENSIC",
            "ROOT_CAUSE": "bounded observability debt",
            "REPAIR_STATUS": "ADMITTED_NOT_CLOSURE_BLOCKING",
            "EVIDENCE": ["non_trading_plane_probe.json"],
            "LAST_CURRENT_PROBE": prefix_path,
        },
        {
            "DEFECT_ID": "DEF-004",
            "ORIGINAL_MEANING": "Run-002 wallclock zero natural enter vs GHV synthetic regimes",
            "CURRENT_MEANING": "Historical operational input/market class gap — not proven CURRENT wiring defect",
            "CURRENT_STATUS": "BOUNDED_HISTORICAL_EVIDENCE_GAP_NOT_CURRENT_PRODUCTIVE_DEFECT",
            "CURRENT_SEVERITY": "S1_HISTORICAL_OPERATIONAL",
            "PRODUCTIVE_OR_FORENSIC": "FORENSIC",
            "ROOT_CAUSE": "Run-002 market/input distribution unlike GHV corpus",
            "REPAIR_STATUS": "NOT_ADMITTED_STRATEGY_OR_MARKET",
            "EVIDENCE": ["run002_zero_enter_forensics.json"],
            "LAST_CURRENT_PROBE": prefix_path,
        },
    ]
    return defects


def sha256_list(items: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(sorted(set(items)), separators=(",", ":")).encode()
    ).hexdigest()
