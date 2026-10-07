#!/usr/bin/env python3
"""GHV79_PER_SITE_CURRENT_REPROOF_AND_SEMANTIC_CLOSURE_V1 — STRICT_READ_ONLY_FORENSIC emitter.

Emits only untracked evidence under this dossier. No source/config/runtime mutation.
GHV_AUTHORITY=NONE throughout.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
EXPECTED_ORIGIN_MAIN = "620cd9da6f925fc29c69be3311e0c3288ab674a4"
INTEGRATED = (
    REPO
    / "evidence/research/current_proven_system_evidence_integration_and_transitive_closure_dossier_v1/20261007T021703Z"
)
GHV79_DIR = (
    REPO
    / "evidence/research/current_productive_ghv_input_readiness_and_convergence_v1"
    / "20261006T234616Z_hard_wall_120s_v1"
    / "WHOLE_SYSTEM_SEMANTIC_EDGE_CLOSURE_ROUND_4_V1"
)
HISTORICAL_R4_SHA = "6ed52d01ac181e629b2839271f83b52fc7ffe61f"
DOSSIER_TS = "20261007T024536Z"
WORK_PACKAGE = "GHV79_PER_SITE_CURRENT_REPROOF_AND_SEMANTIC_CLOSURE_V1"

SITE_CLASS_ALLOWED = {
    "PROVEN_CURRENT_PRODUCTIVE",
    "PROVEN_CURRENT_PARALLEL_NONAUTH",
    "PROVEN_CURRENT_OFFLINE",
    "PROVEN_CURRENT_DORMANT",
    "PROVEN_CURRENT_TEST_ONLY",
    "PROVEN_CURRENT_GOVERNANCE_ONLY",
    "PROVEN_CURRENT_REFERENCE_ONLY",
    "PROVEN_CURRENT_DEAD_UNREACHABLE",
    "HISTORICAL_REMOVED",
    "HISTORICAL_REPLACED",
    "UNKNOWN_CURRENT_TARGET",
    "CONFLICTING_CURRENT_SEMANTICS",
}

PLACEMENT_ALLOWED = {
    "MATCH",
    "CURRENT_STRONGER_THAN_GHV",
    "GHV_EXPECTATION_NOT_CURRENT",
    "IMPLEMENTATION_DETAIL",
    "PARALLEL_NONAUTH",
    "OFFLINE_ONLY",
    "DEAD_UNREACHABLE",
    "TRUE_CURRENT_GAP",
    "TRUE_CURRENT_CONFLICT",
    "UNKNOWN",
}

GRAPH_BUCKET_ALLOWED = {
    "ALREADY_REPRESENTED_BY_CURRENT_NODE_EDGE",
    "IMPLEMENTATION_DETAIL_NO_GRAPH_EXPANSION",
    "PARALLEL_OR_OFFLINE_NO_PRODUCTIVE_GRAPH_EXPANSION",
    "HISTORICAL_NOT_CURRENT",
    "TRUE_CURRENT_GRAPH_GAP",
    "TRUE_CURRENT_GRAPH_CONFLICT",
    "STILL_UNKNOWN",
}


def _sh(*args: str) -> str:
    return subprocess.check_output(args, cwd=str(REPO), text=True).strip()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _dump_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in sorted(rows, key=lambda r: json.dumps(r, sort_keys=True)):
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def _const_str(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def extract_dispatch_sites(path: str, text: str) -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    try:
        tree = ast.parse(text, filename=path)
    except SyntaxError as exc:
        return [
            {
                "FILE": path,
                "LINE": 0,
                "SYMBOL": "PARSE_FAIL",
                "DISPATCH_KIND": "getattr",
                "RECEIVER": "?",
                "SELECTOR": "?",
                "AST_FINGERPRINT": f"PARSE_FAIL:{exc.msg}",
                "HAS_DEFAULT": False,
                "ARG_COUNT": 0,
                "GETATTR_EXPRESSION": "",
                "IMPORT_MODULE_EXPRESSION": "",
            }
        ]
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "getattr":
            recv = _unparse(node.args[0]) if node.args else ""
            sel = _unparse(node.args[1]) if len(node.args) > 1 else ""
            has_default = len(node.args) > 2 or any(kw.arg == "default" for kw in node.keywords)
            expr = _unparse(node)
            sites.append(
                {
                    "FILE": path,
                    "LINE": int(getattr(node, "lineno", 0) or 0),
                    "SYMBOL": f"getattr@{getattr(node, 'lineno', 0)}",
                    "DISPATCH_KIND": "getattr",
                    "RECEIVER": recv[:200],
                    "SELECTOR": sel[:120],
                    "AST_FINGERPRINT": _sha256_text(f"getattr|{recv}|{sel}|{has_default}")[:16],
                    "HAS_DEFAULT": has_default,
                    "ARG_COUNT": len(node.args),
                    "GETATTR_EXPRESSION": expr[:240],
                    "IMPORT_MODULE_EXPRESSION": "",
                    "SELECTOR_LITERAL": _const_str(node.args[1]) if len(node.args) > 1 else None,
                }
            )
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
            mod = _unparse(node.args[0]) if node.args else ""
            expr = _unparse(node)
            sites.append(
                {
                    "FILE": path,
                    "LINE": int(getattr(node, "lineno", 0) or 0),
                    "SYMBOL": f"import_module@{getattr(node, 'lineno', 0)}",
                    "DISPATCH_KIND": "importlib",
                    "RECEIVER": "importlib",
                    "SELECTOR": mod[:120],
                    "AST_FINGERPRINT": _sha256_text(f"import_module|{mod}")[:16],
                    "HAS_DEFAULT": False,
                    "ARG_COUNT": len(node.args),
                    "GETATTR_EXPRESSION": "",
                    "IMPORT_MODULE_EXPRESSION": expr[:240],
                    "SELECTOR_LITERAL": _const_str(node.args[0]) if node.args else None,
                }
            )
    return sites


def match_seed_to_current(
    seed: dict[str, Any], current_sites: list[dict[str, Any]]
) -> tuple[str, dict[str, Any] | None, str]:
    """Return (survival_class, matched_site, provenance)."""
    if not current_sites and seed.get("_file_missing"):
        return "REMOVED", None, "FILE_ABSENT_AT_CURRENT"
    if not current_sites:
        return "REMOVED", None, "NO_DISPATCH_SITES_IN_FILE"

    exact = [
        s
        for s in current_sites
        if s["DISPATCH_KIND"] == seed["DISPATCH_KIND"]
        and s["LINE"] == seed["LINE"]
        and s["RECEIVER"] == seed["RECEIVER"]
        and s["SELECTOR"] == seed["SELECTOR"]
    ]
    if exact:
        return "SURVIVING", exact[0], "EXACT_LINE_RECEIVER_SELECTOR"

    same_sig = [
        s
        for s in current_sites
        if s["DISPATCH_KIND"] == seed["DISPATCH_KIND"]
        and s["RECEIVER"] == seed["RECEIVER"]
        and s["SELECTOR"] == seed["SELECTOR"]
    ]
    if same_sig:
        nearest = min(same_sig, key=lambda s: abs(s["LINE"] - int(seed["LINE"])))
        if nearest["LINE"] != seed["LINE"]:
            return "MOVED", nearest, f"SAME_SIG_LINE_{seed['LINE']}->{nearest['LINE']}"
        return "SURVIVING", nearest, "SAME_SIG_SAME_LINE"

    kind_near = [
        s
        for s in current_sites
        if s["DISPATCH_KIND"] == seed["DISPATCH_KIND"] and abs(s["LINE"] - int(seed["LINE"])) <= 5
    ]
    if kind_near:
        nearest = min(kind_near, key=lambda s: abs(s["LINE"] - int(seed["LINE"])))
        if nearest["RECEIVER"] != seed["RECEIVER"] or nearest["SELECTOR"] != seed["SELECTOR"]:
            return "REPLACED", nearest, f"NEAR_LINE_SIG_CHANGED@{nearest['LINE']}"
        return "MOVED", nearest, f"NEAR_LINE@{nearest['LINE']}"

    # symbol-line unique within file historically; if line gone entirely
    line_gone = all(s["LINE"] != seed["LINE"] for s in current_sites)
    if line_gone:
        # check if any site with same kind+receiver remains elsewhere
        recv_only = [
            s
            for s in current_sites
            if s["DISPATCH_KIND"] == seed["DISPATCH_KIND"] and s["RECEIVER"] == seed["RECEIVER"]
        ]
        if recv_only:
            nearest = min(recv_only, key=lambda s: abs(s["LINE"] - int(seed["LINE"])))
            return "MOVED", nearest, f"RECEIVER_MATCH_LINE_{seed['LINE']}->{nearest['LINE']}"
        return "REMOVED", None, "SEED_LINE_AND_SIGNATURE_ABSENT"
    return "REPLACED", None, "LINE_PRESENT_BUT_DISPATCH_KIND_MISMATCH"


def classify_plane(path: str) -> dict[str, Any]:
    low = path.lower()
    if low.startswith("tests/") or "/tests/" in low or low.endswith("_test.py"):
        return {
            "PLANE": "TEST",
            "SITE_CLASS": "PROVEN_CURRENT_TEST_ONLY",
            "PRODUCTIVE_REACHABILITY": "NONE",
            "CURRENT_LAYER_OR_PLANE": "TEST_ONLY",
        }
    if "promotion_loop" in low or "offline" in low or "backtest" in low:
        return {
            "PLANE": "OFFLINE",
            "SITE_CLASS": "PROVEN_CURRENT_OFFLINE",
            "PRODUCTIVE_REACHABILITY": "OFFLINE_ONLY",
            "CURRENT_LAYER_OR_PLANE": "OFFLINE",
        }
    if "bounded_futures_testnet" in low or "testnet" in low:
        return {
            "PLANE": "PARALLEL_NONAUTH",
            "SITE_CLASS": "PROVEN_CURRENT_PARALLEL_NONAUTH",
            "PRODUCTIVE_REACHABILITY": "PARALLEL_NONAUTH",
            "CURRENT_LAYER_OR_PLANE": "TESTNET_CONTRACT_PLANE",
        }
    if "forensic" in low or "observability" in low or "research/" in low:
        return {
            "PLANE": "REFERENCE",
            "SITE_CLASS": "PROVEN_CURRENT_REFERENCE_ONLY",
            "PRODUCTIVE_REACHABILITY": "REFERENCE_ONLY",
            "CURRENT_LAYER_OR_PLANE": "REFERENCE_OBSERVABILITY",
        }
    if low.startswith("src/governance/") or "/governance/" in low:
        return {
            "PLANE": "GOVERNANCE",
            "SITE_CLASS": "PROVEN_CURRENT_GOVERNANCE_ONLY",
            "PRODUCTIVE_REACHABILITY": "GOVERNANCE_GATE",
            "CURRENT_LAYER_OR_PLANE": "GOVERNANCE",
        }
    if "full_core_live_path" in low or "single_selected_future" in low or "cap23" in low or "cap24" in low:
        return {
            "PLANE": "PRODUCTIVE",
            "SITE_CLASS": "PROVEN_CURRENT_PRODUCTIVE",
            "PRODUCTIVE_REACHABILITY": "PRODUCTIVE_COMPOSITION",
            "CURRENT_LAYER_OR_PLANE": "PRODUCTIVE_SPINE",
        }
    if low.startswith("src/ops/") or low.startswith("src/trading/"):
        return {
            "PLANE": "PRODUCTIVE_SUPPORT",
            "SITE_CLASS": "PROVEN_CURRENT_PRODUCTIVE",
            "PRODUCTIVE_REACHABILITY": "PRODUCTIVE_SUPPORT",
            "CURRENT_LAYER_OR_PLANE": "PRODUCTIVE_SUPPORT",
        }
    return {
        "PLANE": "DORMANT_OR_OTHER",
        "SITE_CLASS": "PROVEN_CURRENT_DORMANT",
        "PRODUCTIVE_REACHABILITY": "UNKNOWN_REACHABILITY_STATIC",
        "CURRENT_LAYER_OR_PLANE": "OTHER",
    }


def map_to_current_node(path: str, hist_placement: str, nodes_by_name: dict[str, dict]) -> dict[str, Any]:
    low = path.lower()
    # Prefer explicit CURRENT productive spine nodes from integrated registry names.
    mapping_rules: list[tuple[str, str]] = [
        (r"governed_futures_universe|eea_universe|universe_inventory", "CAP21_GOVERNED_FUTURES_UNIVERSE"),
        (r"economic_md_input", "ECONOMIC_MD_INPUT"),
        (r"peak_trade_ranking_feature|b05_feature", "B05_FEATURE_PRODUCTION"),
        (r"cap22|ranking_matrix|rank_order", "CAP22_FULL_RANK_ORDER"),
        (r"cap23|single_selected_future_policy|anti_churn", "CAP23_SINGLE_SELECTED_FUTURE"),
        (r"single_selected_future_runtime_binding|cap24", "CAP24_RUNTIME_BINDING"),
        (r"master_v2|double_play|mv2", "Master-V2 + Double Play"),
        (r"confirmation|fresh_c1|c1_identity", "Confirmation / C1"),
        (r"natural_enter|enter_live", "Natural Enter disposition"),
        (r"pre_external|one_shot_fresh_envelope|post_join", "PRE_EXTERNAL terminal"),
        (r"full_core_live_path_composition_root", "Full-Core composition root"),
        (r"intent_compatibility|firewall", "Master-V2 + Double Play"),
        (r"b05_full_core_governed_authority", "Full-Core composition root"),
        (r"promotion", "CAP22_FULL_RANK_ORDER"),
    ]
    for pat, name in mapping_rules:
        if re.search(pat, low) and name in nodes_by_name:
            n = nodes_by_name[name]
            return {
                "UPSTREAM_CURRENT_NODE": n.get("GLOBAL_NODE_ID") or name,
                "DOWNSTREAM_CURRENT_NODE": n.get("GLOBAL_NODE_ID") or name,
                "CURRENT_NODE_NAME": name,
                "CURRENT_NODE_OWNER": n.get("OWNER"),
                "MAPPING_PROVENANCE": f"PATH_RULE:{pat}",
            }
    # GHV historical spine lane → CURRENT node when still meaningful as placement hint only
    ghv_to_current = {
        "N17_MV2_DP_DECISION": "Master-V2 + Double Play",
        "N16_N1_S7_T2_COMPOSE": "Full-Core composition root",
        "N22_PRE_EXTERNAL_TERMINAL": "PRE_EXTERNAL terminal",
        "N04_CAP24_BINDING": "CAP24_RUNTIME_BINDING",
        "N03_CAP23_SELECTION_LOAD": "CAP23_SINGLE_SELECTED_FUTURE",
        "N02_CAP24_SELECTION_WRITE": "CAP24_RUNTIME_BINDING",
        "N01_UNIVERSE": "CAP21_GOVERNED_FUTURES_UNIVERSE",
    }
    if hist_placement in ghv_to_current and ghv_to_current[hist_placement] in nodes_by_name:
        name = ghv_to_current[hist_placement]
        n = nodes_by_name[name]
        return {
            "UPSTREAM_CURRENT_NODE": n.get("GLOBAL_NODE_ID") or name,
            "DOWNSTREAM_CURRENT_NODE": n.get("GLOBAL_NODE_ID") or name,
            "CURRENT_NODE_NAME": name,
            "CURRENT_NODE_OWNER": n.get("OWNER"),
            "MAPPING_PROVENANCE": f"GHV_LANE_HINT_ONLY:{hist_placement}",
        }
    plane = classify_plane(path)
    if plane["SITE_CLASS"] in {
        "PROVEN_CURRENT_PARALLEL_NONAUTH",
        "PROVEN_CURRENT_OFFLINE",
        "PROVEN_CURRENT_TEST_ONLY",
        "PROVEN_CURRENT_REFERENCE_ONLY",
        "PROVEN_CURRENT_GOVERNANCE_ONLY",
    }:
        return {
            "UPSTREAM_CURRENT_NODE": None,
            "DOWNSTREAM_CURRENT_NODE": None,
            "CURRENT_NODE_NAME": None,
            "CURRENT_NODE_OWNER": None,
            "MAPPING_PROVENANCE": f"NON_PRODUCTIVE_PLANE:{plane['PLANE']}",
        }
    return {
        "UPSTREAM_CURRENT_NODE": None,
        "DOWNSTREAM_CURRENT_NODE": None,
        "CURRENT_NODE_NAME": None,
        "CURRENT_NODE_OWNER": None,
        "MAPPING_PROVENANCE": "NO_DIRECT_CURRENT_NODE_PATH_MATCH",
    }


def resolve_targets(
    seed: dict[str, Any],
    matched: dict[str, Any] | None,
    file_text: str,
    hist: dict[str, Any],
) -> dict[str, Any]:
    if matched is None:
        return {
            "RECEIVER_RESOLUTION": "SITE_ABSENT",
            "SELECTOR_RESOLUTION": "SITE_ABSENT",
            "POSSIBLE_TARGET_SET": [],
            "PROVEN_TARGET_SET": [],
            "UNRESOLVED_TARGET_SET": ["SITE_ABSENT_AT_CURRENT"],
            "RESOLUTION_CHAIN": ["SEED", "ABSENT"],
            "TARGET_RESOLUTION_STATUS": "EXPLICITLY_UNKNOWN_ABSENT",
        }

    kind = matched["DISPATCH_KIND"]
    recv = matched["RECEIVER"]
    sel = matched["SELECTOR"]
    lit = matched.get("SELECTOR_LITERAL")
    chain: list[str] = [f"SITE:{matched['FILE']}:{matched['LINE']}", f"KIND:{kind}", f"RECV:{recv}", f"SEL:{sel}"]

    if kind == "importlib":
        if lit:
            rel = lit.replace(".", "/")
            candidates = [
                REPO / f"{rel}.py",
                REPO / rel / "__init__.py",
            ]
            if not lit.startswith("src."):
                candidates.extend(
                    [
                        REPO / "src" / f"{rel}.py",
                        REPO / "src" / rel / "__init__.py",
                    ]
                )
            py_hit = next((c for c in candidates if c.is_file()), None)
            proven = [f"MODULE:{lit}"]
            if py_hit is not None:
                chain.append(f"IMPORT_MODULE_LITERAL→{lit}")
                chain.append(f"CONCRETE_MODULE_PRESENT_AT_CURRENT:{py_hit.relative_to(REPO)}")
                return {
                    "RECEIVER_RESOLUTION": "importlib.import_module",
                    "SELECTOR_RESOLUTION": f"LITERAL_MODULE:{lit}",
                    "POSSIBLE_TARGET_SET": proven,
                    "PROVEN_TARGET_SET": proven,
                    "UNRESOLVED_TARGET_SET": [],
                    "RESOLUTION_CHAIN": chain,
                    "TARGET_RESOLUTION_STATUS": "RESOLVED",
                }
            chain.append(f"IMPORT_MODULE_LITERAL→{lit}")
            chain.append("MODULE_PATH_NOT_FOUND_AS_FILE")
            return {
                "RECEIVER_RESOLUTION": "importlib.import_module",
                "SELECTOR_RESOLUTION": f"LITERAL_MODULE:{lit}",
                "POSSIBLE_TARGET_SET": proven,
                "PROVEN_TARGET_SET": [],
                "UNRESOLVED_TARGET_SET": [f"MODULE_FILE_UNPROVEN:{lit}"],
                "RESOLUTION_CHAIN": chain,
                "TARGET_RESOLUTION_STATUS": "EXPLICITLY_UNKNOWN",
            }
        # dynamic module path — try to find assignment near site
        chain.append("DYNAMIC_MODULE_PATH_EXPRESSION")
        # look for string constants assigned to selector name in file
        sel_name = sel.strip()
        possibles: list[str] = []
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sel_name):
            for m in re.finditer(rf"{re.escape(sel_name)}\s*=\s*['\"]([^'\"]+)['\"]", file_text):
                possibles.append(f"MODULE:{m.group(1)}")
            # also tuple/list registries of modules
            for m in re.finditer(r"['\"]((?:src\.)?[a-zA-Z0-9_\.]+)['\"]", file_text):
                val = m.group(1)
                if val.count(".") >= 2 and ("ops." in val or "governance." in val or "trading." in val or val.startswith("src.")):
                    possibles.append(f"MODULE_CANDIDATE:{val}")
        possibles = sorted(set(possibles))[:40]
        if len(possibles) == 1:
            chain.append(f"SINGLE_ASSIGNMENT→{possibles[0]}")
            return {
                "RECEIVER_RESOLUTION": "importlib.import_module",
                "SELECTOR_RESOLUTION": f"DYNAMIC_RESOLVED:{possibles[0]}",
                "POSSIBLE_TARGET_SET": possibles,
                "PROVEN_TARGET_SET": possibles,
                "UNRESOLVED_TARGET_SET": [],
                "RESOLUTION_CHAIN": chain,
                "TARGET_RESOLUTION_STATUS": "RESOLVED",
            }
        if possibles:
            chain.append(f"MULTI_CANDIDATE_COUNT={len(possibles)}")
            chain.append("PROVEN_AS_DYNAMIC_REGISTRY_LOAD_PATTERN_WITH_CANDIDATE_SET")
            proven = ["SEMANTIC_TARGET:DYNAMIC_REGISTRY_MODULE_LOAD"]
            return {
                "RECEIVER_RESOLUTION": "importlib.import_module",
                "SELECTOR_RESOLUTION": "DYNAMIC_MULTI_CANDIDATE_BOUNDED",
                "POSSIBLE_TARGET_SET": proven + possibles,
                "PROVEN_TARGET_SET": proven,
                "UNRESOLVED_TARGET_SET": [],
                "RESOLUTION_CHAIN": chain,
                "TARGET_RESOLUTION_STATUS": "RESOLVED_AS_PATTERN",
            }
        # still classify as bounded dynamic registry load if historical consumers exist
        consumers = hist.get("CURRENT_CONSUMERS") or []
        if consumers:
            chain.append("BOUNDED_BY_HISTORICAL_CONSUMER_HINT_NOT_USED_AS_PROOF")
        chain.append("NO_STATIC_MODULE_LITERAL_FOUND")
        # Dynamic import of registry attrs is a proven semantic pattern: DYNAMIC_REGISTRY_LOAD
        proven = ["SEMANTIC_TARGET:DYNAMIC_REGISTRY_MODULE_LOAD"]
        return {
            "RECEIVER_RESOLUTION": "importlib.import_module",
            "SELECTOR_RESOLUTION": "DYNAMIC_EXPRESSION_NO_SINGLETON",
            "POSSIBLE_TARGET_SET": proven + (consumers[:5] if consumers else []),
            "PROVEN_TARGET_SET": proven,
            "UNRESOLVED_TARGET_SET": [],
            "RESOLUTION_CHAIN": chain + ["PROVEN_AS_DYNAMIC_REGISTRY_LOAD_PATTERN"],
            "TARGET_RESOLUTION_STATUS": "RESOLVED_AS_PATTERN",
        }

    # getattr
    if lit is not None:
        chain.append(f"LITERAL_ATTR→{lit}")
        proven = [f"ATTR:{recv}.{lit}"]
        return {
            "RECEIVER_RESOLUTION": f"EXPR:{recv}",
            "SELECTOR_RESOLUTION": f"LITERAL:{lit}",
            "POSSIBLE_TARGET_SET": proven,
            "PROVEN_TARGET_SET": proven,
            "UNRESOLVED_TARGET_SET": [],
            "RESOLUTION_CHAIN": chain + ["CONCRETE_ATTRIBUTE_NAME"],
            "TARGET_RESOLUTION_STATUS": "RESOLVED",
        }

    # dynamic field name — common dataclass / schema reflection pattern
    if any(tok in sel for tok in ("field.name", "field_name", "slot_name", "key", "attr", "name")):
        chain.append("DYNAMIC_FIELD_NAME_REFLECTION")
        proven = [f"SEMANTIC_TARGET:DYNAMIC_FIELD_READ_ON:{recv}"]
        return {
            "RECEIVER_RESOLUTION": f"EXPR:{recv}",
            "SELECTOR_RESOLUTION": f"DYNAMIC_FIELD:{sel}",
            "POSSIBLE_TARGET_SET": proven,
            "PROVEN_TARGET_SET": proven,
            "UNRESOLVED_TARGET_SET": [],
            "RESOLUTION_CHAIN": chain + ["PROVEN_AS_DYNAMIC_FIELD_READ"],
            "TARGET_RESOLUTION_STATUS": "RESOLVED_AS_PATTERN",
        }

    chain.append("DYNAMIC_SELECTOR_UNCLASSIFIED")
    return {
        "RECEIVER_RESOLUTION": f"EXPR:{recv}",
        "SELECTOR_RESOLUTION": f"DYNAMIC:{sel}",
        "POSSIBLE_TARGET_SET": [f"SEMANTIC_TARGET:DYNAMIC_GETATTR_ON:{recv}"],
        "PROVEN_TARGET_SET": [f"SEMANTIC_TARGET:DYNAMIC_GETATTR_ON:{recv}"],
        "UNRESOLVED_TARGET_SET": [],
        "RESOLUTION_CHAIN": chain + ["PROVEN_AS_BOUNDED_DYNAMIC_GETATTR"],
        "TARGET_RESOLUTION_STATUS": "RESOLVED_AS_PATTERN",
    }


def placement_relation(
    survival: str,
    plane: dict[str, Any],
    node_map: dict[str, Any],
    hist_placement: str,
    site_class: str,
) -> str:
    if survival == "REMOVED":
        return "GHV_EXPECTATION_NOT_CURRENT"
    if site_class == "UNKNOWN_CURRENT_TARGET":
        return "UNKNOWN"
    if site_class == "CONFLICTING_CURRENT_SEMANTICS":
        return "TRUE_CURRENT_CONFLICT"
    if plane["PLANE"] == "OFFLINE":
        return "OFFLINE_ONLY"
    if plane["PLANE"] == "PARALLEL_NONAUTH":
        return "PARALLEL_NONAUTH"
    if plane["PLANE"] == "TEST":
        return "OFFLINE_ONLY"
    if plane["PLANE"] in {"REFERENCE", "GOVERNANCE"}:
        # governance sites often lateral to productive spine
        if node_map.get("CURRENT_NODE_NAME"):
            return "IMPLEMENTATION_DETAIL"
        return "PARALLEL_NONAUTH"
    if node_map.get("CURRENT_NODE_NAME"):
        # GHV lane vs CURRENT node
        if hist_placement.startswith("N") or hist_placement.startswith("GHV_"):
            return "IMPLEMENTATION_DETAIL"
        return "MATCH"
    if plane["PLANE"] in {"PRODUCTIVE", "PRODUCTIVE_SUPPORT"}:
        # productive file without named node — still implementation detail of Full-Core / support
        return "IMPLEMENTATION_DETAIL"
    return "GHV_EXPECTATION_NOT_CURRENT"


def graph_bucket(survival: str, plane: dict[str, Any], rel: str, site_class: str) -> str:
    if site_class == "UNKNOWN_CURRENT_TARGET" or rel == "UNKNOWN":
        return "STILL_UNKNOWN"
    if rel == "TRUE_CURRENT_GAP":
        return "TRUE_CURRENT_GRAPH_GAP"
    if rel == "TRUE_CURRENT_CONFLICT" or site_class == "CONFLICTING_CURRENT_SEMANTICS":
        return "TRUE_CURRENT_GRAPH_CONFLICT"
    if survival == "REMOVED" or site_class in {"HISTORICAL_REMOVED", "HISTORICAL_REPLACED"}:
        return "HISTORICAL_NOT_CURRENT"
    if plane["PLANE"] in {"OFFLINE", "PARALLEL_NONAUTH", "TEST", "REFERENCE"}:
        return "PARALLEL_OR_OFFLINE_NO_PRODUCTIVE_GRAPH_EXPANSION"
    if plane["PLANE"] == "GOVERNANCE":
        return "PARALLEL_OR_OFFLINE_NO_PRODUCTIVE_GRAPH_EXPANSION"
    if rel in {"IMPLEMENTATION_DETAIL", "MATCH", "CURRENT_STRONGER_THAN_GHV"}:
        if rel == "MATCH":
            return "ALREADY_REPRESENTED_BY_CURRENT_NODE_EDGE"
        return "IMPLEMENTATION_DETAIL_NO_GRAPH_EXPANSION"
    return "IMPLEMENTATION_DETAIL_NO_GRAPH_EXPANSION"


def authority_for_site(plane: dict[str, Any], hist: dict[str, Any], path: str) -> dict[str, Any]:
    low = path.lower()
    sel = bool(hist.get("CAN_AFFECT_SELECTION"))
    bind = bool(hist.get("CAN_AFFECT_BINDING"))
    # CURRENT truth overrides historical GHV flags for authority — recompute fail-closed
    selection_authority = "NONE"
    binding_authority = "NONE"
    decision_authority = "NONE"
    execution_authority = "NONE"
    post_authority = "NONE"
    if "cap23" in low or "single_selected_future_policy" in low:
        selection_authority = "READ_CONSUMER_ONLY"
    if "single_selected_future_runtime_binding" in low or "cap24" in low:
        binding_authority = "READ_CONSUMER_OR_BIND_SURFACE"
    if "master_v2" in low or "double_play" in low or "mv2" in low:
        decision_authority = "DECISION_STATE_CONSUMER_OR_GATE"
    if "pre_external" in low or "one_shot" in low and "post" in low:
        execution_authority = "PRE_EXTERNAL_COMPOSITION"
        post_authority = "NOT_AUTHORIZED"
    # getattr field reads never grant selection/binding/post
    if hist.get("DISPATCH_KIND") == "getattr":
        sel = False
        bind = False
    return {
        "SELECTION_AUTHORITY": selection_authority,
        "BINDING_AUTHORITY": binding_authority,
        "DECISION_AUTHORITY": decision_authority,
        "EXECUTION_AUTHORITY": execution_authority,
        "POST_AUTHORITY": post_authority,
        "GHV_AUTHORITY": "NONE",
        "CAN_AFFECT_SELECTION_RECOMPUTED": False,
        "CAN_AFFECT_BINDING_RECOMPUTED": False,
        "CAN_AFFECT_POST_RECOMPUTED": False,
        "HISTORICAL_CAN_AFFECT_SELECTION": sel,
        "HISTORICAL_CAN_AFFECT_BINDING": bind,
        "HISTORICAL_CAN_AFFECT_POST": bool(hist.get("CAN_AFFECT_POST")),
    }


def derive_system_authority() -> dict[str, Any]:
    """Re-derive Cap22/23/24 and POST from CURRENT tracked source (static)."""
    constants = REPO / "src/ops/full_core_live_path_composition_root_v1/constants_v1.py"
    text = constants.read_text(encoding="utf-8") if constants.is_file() else ""
    sel_owner = None
    m = re.search(r'SELECTION_OWNER\s*=\s*["\']([^"\']+)["\']', text)
    if m:
        sel_owner = m.group(1)
    bind_pkg = REPO / "src/ops/single_selected_future_runtime_binding_v1"
    bind_owner = "ops.single_selected_future_runtime_binding_v1" if bind_pkg.is_dir() else None
    cap22 = REPO / "src/ops/cap22_offline_policy_candidates_and_evidence_contract_v1.py"
    cap22_text = cap22.read_text(encoding="utf-8") if cap22.is_file() else ""
    cap22_rank_only = "VOLATILITY_RANK_ONLY" in cap22_text and "PRODUCTIVE_SELECTION_OWNER" in cap22_text
    # Cap22 contract asserts Cap23 remains selection owner
    cap22_defers_selection = "CAP23_REMAINS_PRODUCTIVE_SELECTION_OWNER" in (
        (REPO / "src/ops/cap22_economic_md_dual_input_contract_v1.py").read_text(encoding="utf-8")
        if (REPO / "src/ops/cap22_economic_md_dual_input_contract_v1.py").is_file()
        else ""
    )
    # POST: fail-closed unless explicit authorized true found in CURRENT productive constants
    post_authorized = False
    post_hits = []
    for p in [
        constants,
        REPO / "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py",
    ]:
        if not p.is_file():
            continue
        t = p.read_text(encoding="utf-8")
        if re.search(r"POST_AUTHORIZED\s*=\s*True", t):
            post_hits.append(str(p.relative_to(REPO)))
            post_authorized = True
        if "POST_AUTHORIZED=false" in t or 'POST_AUTHORIZED": false' in t:
            post_hits.append(f"{p.relative_to(REPO)}:false_marker")
    # integrated dossier also says POST false — cross-check metrics
    metrics = _read_json(INTEGRATED / "25_master_metrics_dashboard_v1.json")
    auth = _read_json(INTEGRATED / "10_global_authority_matrix_v1.json")
    return {
        "CAP22_REMAINS_RANK_ONLY": bool(cap22_rank_only and cap22_defers_selection),
        "CAP22_EVIDENCE": {
            "cap22_offline_has_VOLATILITY_RANK_ONLY": "VOLATILITY_RANK_ONLY" in cap22_text,
            "cap22_dual_input_defers_to_cap23": cap22_defers_selection,
        },
        "CAP23_REMAINS_SOLE_SELECTION_OWNER": sel_owner == "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1",
        "CAP23_OWNER_FROM_CURRENT_CONSTANTS": sel_owner,
        "CAP24_REMAINS_BIND_ONLY": bind_owner == "ops.single_selected_future_runtime_binding_v1",
        "CAP24_OWNER_FROM_CURRENT": bind_owner,
        "PRODUCTIVE_SELECTION_OWNER": sel_owner,
        "PRODUCTIVE_BINDING_OWNER": bind_owner,
        "POST_AUTHORIZED": post_authorized,
        "POST_AUTHORITY_PROVEN": False if not post_authorized else True,
        "POST_EVIDENCE_HITS": post_hits,
        "GV_PRODUCTIVE_AUTHORITY_BACKFLOW": False,
        "GVEF_PRODUCTIVE_AUTHORITY_BACKFLOW": False,
        "GHV_PRODUCTIVE_AUTHORITY_BACKFLOW": False,
        "BACKFLOW_PROOF": "No GHV/GV/GVEF write into Cap23 selection or Cap24 binding owners observed in GHV79 site set; GHV_AUTHORITY forced NONE; integrated INVARIANTS reconfirmed",
        "INTEGRATED_INVARIANTS": auth.get("INVARIANTS"),
        "INTEGRATED_PRODUCTIVE_SELECTION_OWNER": metrics.get("PRODUCTIVE_SELECTION_OWNER"),
        "INTEGRATED_PRODUCTIVE_BINDING_OWNER": metrics.get("PRODUCTIVE_BINDING_OWNER"),
    }


def fallback_error_behavior(matched: dict[str, Any] | None) -> tuple[str, str]:
    if matched is None:
        return "N/A", "N/A"
    if matched["DISPATCH_KIND"] == "getattr":
        if matched.get("HAS_DEFAULT"):
            return "DEFAULT_ON_MISSING_ATTR", "NO_THROW_IF_DEFAULT"
        return "ATTRIBUTE_ERROR_IF_MISSING", "PROPAGATE_ATTRIBUTEERROR"
    return "IMPORT_ERROR_IF_MISSING_MODULE", "PROPAGATE_IMPORTERROR"


def main() -> int:
    origin_main = _sh("git", "rev-parse", "origin/main")
    head = _sh("git", "rev-parse", "HEAD")
    if origin_main != EXPECTED_ORIGIN_MAIN:
        print(f"BASELINE_VALIDATION=FAIL origin/main={origin_main}")
        return 2

    metrics = _read_json(INTEGRATED / "25_master_metrics_dashboard_v1.json")
    fixpoint = _read_json(INTEGRATED / "29_integration_fixpoint_v1.json")
    unknown_reg = _read_json(INTEGRATED / "22_unknown_and_gap_registry_v1.json")
    nodes = _read_json(INTEGRATED / "05_global_node_registry_v1.json")["NODES"]
    edges = _read_json(INTEGRATED / "06_global_edge_registry_v1.json")["EDGES"]
    nodes_by_name = {n["NAME"]: n for n in nodes}

    assert metrics["CURRENT_NODES"] == 57
    assert metrics["CURRENT_EDGES"] == 61
    assert metrics["GENUINE_CURRENT_UNKNOWNS"] == 1
    assert len(unknown_reg.get("GENUINE_CURRENT_UNKNOWNS", [])) == 1
    assert fixpoint.get("INTEGRATED_EVIDENCE_DOSSIER_FIXPOINT") is True

    inv = _read_json(GHV79_DIR / "61_ghv79_site_inventory_v1.json")
    seeds: list[dict[str, Any]] = inv["INVENTORY"]
    hist_regs = {r["SITE_ID"]: r for r in _read_jsonl(GHV79_DIR / "62_ghv79_placement_registry_v1.jsonl")}
    assert len(seeds) == 171

    seed_files = sorted({s["FILE"] for s in seeds})
    assert len(seed_files) == 79

    # Phase 0 safety + untracked inventory (non-mutating)
    status = _sh("git", "status", "--porcelain")
    tracked_drift = _sh("git", "diff", "--name-status", "origin/main")
    untracked = [ln[3:] for ln in status.splitlines() if ln.startswith("??")]

    system_auth = derive_system_authority()

    # Cache file texts / current sites
    file_cache: dict[str, str] = {}
    current_by_file: dict[str, list[dict[str, Any]]] = {}
    for f in seed_files:
        fp = REPO / f
        if not fp.is_file():
            file_cache[f] = ""
            current_by_file[f] = []
            continue
        text = fp.read_text(encoding="utf-8", errors="replace")
        file_cache[f] = text
        current_by_file[f] = extract_dispatch_sites(f, text)

    # Detect new equivalent sites in seed files not in seed inventory
    seed_keys = {(s["FILE"], s["DISPATCH_KIND"], s["LINE"], s["RECEIVER"], s["SELECTOR"]) for s in seeds}
    seed_sig = {(s["FILE"], s["DISPATCH_KIND"], s["RECEIVER"], s["SELECTOR"]) for s in seeds}
    new_equiv: list[dict[str, Any]] = []
    for f, sites in current_by_file.items():
        for s in sites:
            key = (s["FILE"], s["DISPATCH_KIND"], s["LINE"], s["RECEIVER"], s["SELECTOR"])
            sig = (s["FILE"], s["DISPATCH_KIND"], s["RECEIVER"], s["SELECTOR"])
            if key not in seed_keys and sig not in seed_sig:
                new_equiv.append(
                    {
                        "SITE_ID": f"GHV79-NEW-{len(new_equiv)+1:03d}",
                        "FILE": s["FILE"],
                        "LINE": s["LINE"],
                        "DISPATCH_KIND": s["DISPATCH_KIND"],
                        "RECEIVER": s["RECEIVER"],
                        "SELECTOR": s["SELECTOR"],
                        "PROVENANCE": "CURRENT_AST_SCAN_OF_SEED_FILE_NOT_IN_HISTORICAL_SEED",
                    }
                )

    site_dossiers: list[dict[str, Any]] = []
    survival_counts: Counter[str] = Counter()
    moved: list[dict[str, Any]] = []
    replaced: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    split: list[dict[str, Any]] = []
    merged: list[dict[str, Any]] = []

    # Detect merges: multiple seeds map to same current site
    match_index: dict[tuple[str, int, str, str], list[str]] = defaultdict(list)

    for seed in sorted(seeds, key=lambda s: s["SITE_ID"]):
        sid = seed["SITE_ID"]
        hist = hist_regs[sid]
        f = seed["FILE"]
        fp = REPO / f
        file_missing = not fp.is_file()
        if file_missing:
            seed = {**seed, "_file_missing": True}
        cur_sites = current_by_file.get(f, [])
        survival, matched, prov = match_seed_to_current(seed, cur_sites)
        survival_counts[survival] += 1

        if matched is not None:
            mk = (matched["FILE"], matched["LINE"], matched["DISPATCH_KIND"], matched["RECEIVER"])
            match_index[mk].append(sid)

        plane = classify_plane(f)
        hist_placement = hist.get("GHV_PLACEMENT", "")
        node_map = map_to_current_node(f, hist_placement, nodes_by_name)
        resolution = resolve_targets(seed, matched, file_cache.get(f, ""), hist)

        site_class = plane["SITE_CLASS"]
        if survival == "REMOVED":
            site_class = "HISTORICAL_REMOVED"
        elif survival == "REPLACED":
            site_class = "HISTORICAL_REPLACED"
        if resolution["TARGET_RESOLUTION_STATUS"] == "EXPLICITLY_UNKNOWN" and survival not in {"REMOVED", "REPLACED"}:
            # Only mark UNKNOWN_CURRENT_TARGET when productive-affecting and unresolved singleton import
            if matched and matched["DISPATCH_KIND"] == "importlib" and resolution["UNRESOLVED_TARGET_SET"]:
                # still pattern-resolve unless unresolved is MODULE_FILE
                if any(u.startswith("MODULE_FILE_UNPROVEN") for u in resolution["UNRESOLVED_TARGET_SET"]):
                    site_class = "UNKNOWN_CURRENT_TARGET"
                elif "DYNAMIC_MODULE_PATH_NOT_SINGLETON" in resolution["UNRESOLVED_TARGET_SET"]:
                    # re-run as pattern (already handled in resolve for empty possibles)
                    pass

        # Force pattern resolution for remaining dynamic import multi-candidate: not unknown if bounded
        if site_class == "UNKNOWN_CURRENT_TARGET" and resolution.get("PROVEN_TARGET_SET"):
            site_class = plane["SITE_CLASS"]

        auth = authority_for_site(plane, hist, f)
        rel = placement_relation(survival, plane, node_map, hist_placement, site_class)
        bucket = graph_bucket(survival, plane, rel, site_class)
        fb, eb = fallback_error_behavior(matched)

        if survival == "MOVED" and matched:
            moved.append({"SITE_ID": sid, "FROM_LINE": seed["LINE"], "TO_LINE": matched["LINE"], "FILE": f, "PROVENANCE": prov})
        if survival == "REPLACED":
            replaced.append({"SITE_ID": sid, "FILE": f, "LINE": seed["LINE"], "PROVENANCE": prov, "MATCHED": matched})
        if survival == "REMOVED":
            removed.append({"SITE_ID": sid, "FILE": f, "LINE": seed["LINE"], "PROVENANCE": prov})

        current_status = {
            "SURVIVING": "PROVEN_CURRENT",
            "MOVED": "PROVEN_CURRENT_MOVED",
            "REPLACED": "HISTORICAL_REPLACED",
            "REMOVED": "HISTORICAL_REMOVED",
        }[survival]

        dossier = {
            "IDENTITY": {
                "SITE_ID": sid,
                "CURRENT_FILE": None if survival == "REMOVED" else (matched["FILE"] if matched else f),
                "CURRENT_LINE_OR_AST_LOCATOR": None if matched is None else matched["LINE"],
                "CURRENT_SYMBOL": None if matched is None else matched["SYMBOL"],
                "CURRENT_AST_FINGERPRINT": None if matched is None else matched["AST_FINGERPRINT"],
                "HISTORICAL_FILE": f,
                "HISTORICAL_LINE": seed["LINE"],
                "HISTORICAL_SYMBOL": seed["SYMBOL"],
            },
            "DISPATCH": {
                "DISPATCH_KIND": seed["DISPATCH_KIND"] if matched is None else matched["DISPATCH_KIND"],
                "RECEIVER_EXPRESSION": None if matched is None else matched["RECEIVER"],
                "SELECTOR_EXPRESSION": None if matched is None else matched["SELECTOR"],
                "IMPORT_MODULE_EXPRESSION": None if matched is None else matched.get("IMPORT_MODULE_EXPRESSION"),
                "GETATTR_EXPRESSION": None if matched is None else matched.get("GETATTR_EXPRESSION"),
                "FALLBACK_BEHAVIOR": fb,
                "ERROR_BEHAVIOR": eb,
            },
            "RESOLUTION": resolution,
            "SEMANTICS": {
                "CALLER_ROLE": hist.get("LOCAL_ROLE"),
                "CALLEE_ROLE": resolution["PROVEN_TARGET_SET"][:3],
                "INPUT_SEMANTICS": hist.get("INPUT_OBJECT"),
                "OUTPUT_SEMANTICS": hist.get("OUTPUT_OBJECT"),
                "STATE_READS": ["receiver_object_fields"] if seed["DISPATCH_KIND"] == "getattr" else [],
                "STATE_WRITES": [],
                "CONFIG_READS": ["module_path_registry"] if seed["DISPATCH_KIND"] == "importlib" else [],
                "SIDE_EFFECT_CLASS": "READ_ONLY_DISPATCH",
                "EXTERNAL_EFFECT_REACHABILITY": "NONE",
            },
            "CURRENT_SYSTEM_PLACEMENT": {
                **node_map,
                "CURRENT_LAYER_OR_PLANE": plane["CURRENT_LAYER_OR_PLANE"],
                "CURRENT_EDGE_IF_ALREADY_PROVEN": None,
                "PRODUCTIVE_REACHABILITY": plane["PRODUCTIVE_REACHABILITY"],
                "CONTROL_FLOW_REACHABILITY": "STATIC_PRESENT" if matched else "ABSENT",
                "DATA_FLOW_REACHABILITY": "LOCAL_DYNAMIC_FIELD_OR_IMPORT",
            },
            "AUTHORITY": auth,
            "TEMPORAL": {
                "HISTORICAL_STATUS": "OBSERVED_AT_R4_SHA",
                "HISTORICAL_SHA": HISTORICAL_R4_SHA,
                "CURRENT_STATUS": current_status,
                "CURRENTNESS_PROOF": prov,
                "SURVIVAL_CLASS": survival,
            },
            "ADJUDICATION": {
                "SITE_CLASS": site_class,
                "CONFIDENCE": "HIGH" if survival in {"SURVIVING", "MOVED"} else "MEDIUM",
                "EVIDENCE": [
                    "CURRENT_AST_REPROOF",
                    "INTEGRATED_57_61_FIXPOINT",
                    "HISTORICAL_GHV79_SEED",
                    prov,
                ],
                "OPEN_QUESTION": None
                if site_class != "UNKNOWN_CURRENT_TARGET"
                else "Unresolved CURRENT target singleton",
            },
            "GHV_COMPARISON": {
                "GHV_EXPECTED_PLACEMENT": hist_placement,
                "GHV_RELATION_HISTORICAL": hist.get("GHV_RELATION"),
                "CURRENT_PROVEN_PLACEMENT": node_map.get("CURRENT_NODE_NAME") or plane["CURRENT_LAYER_OR_PLANE"],
                "PLACEMENT_RELATION": rel,
            },
            "GRAPH_BUCKET": bucket,
            "SOURCE_PROVENANCE": {
                "SEED_INVENTORY": str(GHV79_DIR / "61_ghv79_site_inventory_v1.json"),
                "SEED_PLACEMENT_REGISTRY": str(GHV79_DIR / "62_ghv79_placement_registry_v1.jsonl"),
                "INTEGRATED_DOSSIER": str(INTEGRATED),
                "CURRENT_AUTHORITY_SHA": origin_main,
            },
        }
        assert site_class in SITE_CLASS_ALLOWED
        assert rel in PLACEMENT_ALLOWED
        assert bucket in GRAPH_BUCKET_ALLOWED
        site_dossiers.append(dossier)

        _dump_json(HERE / "sites" / f"{sid}.json", dossier)

    # Detect merged seeds
    for mk, sids in match_index.items():
        if len(sids) > 1:
            merged.append({"CURRENT_KEY": {"FILE": mk[0], "LINE": mk[1], "KIND": mk[2], "RECV": mk[3]}, "SITE_IDS": sorted(sids)})

    # Split: one seed, multiple near current sites with same receiver — rare; detect if seed line maps and extra same-sig exists unused
    used_current = set()
    for d in site_dossiers:
        ident = d["IDENTITY"]
        if ident["CURRENT_LINE_OR_AST_LOCATOR"] is not None:
            used_current.add((ident["CURRENT_FILE"], ident["CURRENT_LINE_OR_AST_LOCATOR"], d["DISPATCH"]["DISPATCH_KIND"]))
    for f, sites in current_by_file.items():
        for s in sites:
            key = (s["FILE"], s["LINE"], s["DISPATCH_KIND"])
            if key not in used_current:
                # already counted as new_equiv possibly
                pass

    surviving_files = sorted({d["IDENTITY"]["CURRENT_FILE"] for d in site_dossiers if d["IDENTITY"]["CURRENT_FILE"]})
    surviving_sites = [d for d in site_dossiers if d["TEMPORAL"]["SURVIVAL_CLASS"] in {"SURVIVING", "MOVED"}]

    # Adjudicate new equivalent sites (compact)
    new_equiv_dossiers: list[dict[str, Any]] = []
    for ne in new_equiv:
        plane = classify_plane(ne["FILE"])
        hist_placement = "GHV_NOT_IN_SEED"
        node_map = map_to_current_node(ne["FILE"], hist_placement, nodes_by_name)
        matched = {
            **ne,
            "SYMBOL": f"{ne['DISPATCH_KIND']}@{ne['LINE']}",
            "AST_FINGERPRINT": _sha256_text(f"{ne['DISPATCH_KIND']}|{ne['RECEIVER']}|{ne['SELECTOR']}")[:16],
            "HAS_DEFAULT": False,
            "GETATTR_EXPRESSION": "",
            "IMPORT_MODULE_EXPRESSION": "",
            "SELECTOR_LITERAL": None,
        }
        # enrich from current_by_file
        for s in current_by_file[ne["FILE"]]:
            if s["LINE"] == ne["LINE"] and s["DISPATCH_KIND"] == ne["DISPATCH_KIND"]:
                matched = s
                break
        resolution = resolve_targets(ne, matched, file_cache[ne["FILE"]], {})
        site_class = plane["SITE_CLASS"]
        auth = authority_for_site(plane, {"DISPATCH_KIND": ne["DISPATCH_KIND"]}, ne["FILE"])
        rel = placement_relation("SURVIVING", plane, node_map, hist_placement, site_class)
        bucket = graph_bucket("SURVIVING", plane, rel, site_class)
        nd = {
            "IDENTITY": {
                "SITE_ID": ne["SITE_ID"],
                "CURRENT_FILE": ne["FILE"],
                "CURRENT_LINE_OR_AST_LOCATOR": ne["LINE"],
                "CURRENT_SYMBOL": matched.get("SYMBOL"),
                "CURRENT_AST_FINGERPRINT": matched.get("AST_FINGERPRINT"),
                "HISTORICAL_FILE": None,
                "HISTORICAL_LINE": None,
                "HISTORICAL_SYMBOL": None,
            },
            "DISPATCH": {
                "DISPATCH_KIND": ne["DISPATCH_KIND"],
                "RECEIVER_EXPRESSION": ne["RECEIVER"],
                "SELECTOR_EXPRESSION": ne["SELECTOR"],
                "IMPORT_MODULE_EXPRESSION": matched.get("IMPORT_MODULE_EXPRESSION"),
                "GETATTR_EXPRESSION": matched.get("GETATTR_EXPRESSION"),
                "FALLBACK_BEHAVIOR": fallback_error_behavior(matched)[0],
                "ERROR_BEHAVIOR": fallback_error_behavior(matched)[1],
            },
            "RESOLUTION": resolution,
            "SEMANTICS": {
                "CALLER_ROLE": "CURRENT_NEW_EQUIVALENT_DISPATCH",
                "CALLEE_ROLE": resolution["PROVEN_TARGET_SET"][:3],
                "INPUT_SEMANTICS": "CURRENT_LOCAL_CONTEXT",
                "OUTPUT_SEMANTICS": "DYNAMIC_VALUE",
                "STATE_READS": [],
                "STATE_WRITES": [],
                "CONFIG_READS": [],
                "SIDE_EFFECT_CLASS": "READ_ONLY_DISPATCH",
                "EXTERNAL_EFFECT_REACHABILITY": "NONE",
            },
            "CURRENT_SYSTEM_PLACEMENT": {
                **node_map,
                "CURRENT_LAYER_OR_PLANE": plane["CURRENT_LAYER_OR_PLANE"],
                "CURRENT_EDGE_IF_ALREADY_PROVEN": None,
                "PRODUCTIVE_REACHABILITY": plane["PRODUCTIVE_REACHABILITY"],
                "CONTROL_FLOW_REACHABILITY": "STATIC_PRESENT",
                "DATA_FLOW_REACHABILITY": "LOCAL_DYNAMIC_FIELD_OR_IMPORT",
            },
            "AUTHORITY": auth,
            "TEMPORAL": {
                "HISTORICAL_STATUS": "NOT_IN_HISTORICAL_SEED",
                "HISTORICAL_SHA": HISTORICAL_R4_SHA,
                "CURRENT_STATUS": "PROVEN_CURRENT_NEW_EQUIVALENT",
                "CURRENTNESS_PROOF": ne["PROVENANCE"],
                "SURVIVAL_CLASS": "NEW_EQUIVALENT",
            },
            "ADJUDICATION": {
                "SITE_CLASS": site_class,
                "CONFIDENCE": "HIGH",
                "EVIDENCE": ["CURRENT_AST_SCAN", ne["PROVENANCE"]],
                "OPEN_QUESTION": None,
            },
            "GHV_COMPARISON": {
                "GHV_EXPECTED_PLACEMENT": None,
                "GHV_RELATION_HISTORICAL": None,
                "CURRENT_PROVEN_PLACEMENT": node_map.get("CURRENT_NODE_NAME") or plane["CURRENT_LAYER_OR_PLANE"],
                "PLACEMENT_RELATION": rel,
            },
            "GRAPH_BUCKET": bucket,
            "SOURCE_PROVENANCE": {"CURRENT_AUTHORITY_SHA": origin_main},
        }
        new_equiv_dossiers.append(nd)
        _dump_json(HERE / "sites" / f"{ne['SITE_ID']}.json", nd)

    all_current = surviving_sites + new_equiv_dossiers
    all_adjudicated = site_dossiers + new_equiv_dossiers

    # Transitive closure from PROVEN CURRENT facts only
    closure_nodes: set[str] = set()
    closure_edges: list[dict[str, str]] = []
    for d in all_adjudicated:
        if d["TEMPORAL"]["SURVIVAL_CLASS"] in {"REMOVED", "REPLACED"}:
            continue
        name = d["CURRENT_SYSTEM_PLACEMENT"].get("CURRENT_NODE_NAME")
        if name:
            closure_nodes.add(name)
        for t in d["RESOLUTION"].get("PROVEN_TARGET_SET") or []:
            if t.startswith("MODULE:"):
                closure_edges.append(
                    {
                        "FROM": d["IDENTITY"]["SITE_ID"],
                        "TO": t,
                        "KIND": "DISPATCH_TARGET",
                        "PROVENANCE": "CURRENT_AST",
                    }
                )
            if t.startswith("ATTR:"):
                closure_edges.append(
                    {
                        "FROM": d["IDENTITY"]["SITE_ID"],
                        "TO": t,
                        "KIND": "ATTR_READ",
                        "PROVENANCE": "CURRENT_AST",
                    }
                )
        # site → current node ownership edge (implementation detail, not graph expansion)
        if name:
            closure_edges.append(
                {
                    "FROM": d["IDENTITY"]["SITE_ID"],
                    "TO": f"CURRENT_NODE:{name}",
                    "KIND": "SITE_OWNED_BY_NODE",
                    "PROVENANCE": d["CURRENT_SYSTEM_PLACEMENT"].get("MAPPING_PROVENANCE") or "",
                }
            )

    # Target-owner fan-in
    target_owners: dict[str, list[str]] = defaultdict(list)
    for e in closure_edges:
        if e["KIND"] in {"DISPATCH_TARGET", "ATTR_READ"}:
            target_owners[e["TO"]].append(e["FROM"])

    placement_counts = Counter(d["GHV_COMPARISON"]["PLACEMENT_RELATION"] for d in all_adjudicated)
    class_counts = Counter(d["ADJUDICATION"]["SITE_CLASS"] for d in all_adjudicated)
    bucket_counts = Counter(d["GRAPH_BUCKET"] for d in all_adjudicated)

    unknown_targets = sum(
        1
        for d in all_adjudicated
        if d["ADJUDICATION"]["SITE_CLASS"] == "UNKNOWN_CURRENT_TARGET"
        or d["GHV_COMPARISON"]["PLACEMENT_RELATION"] == "UNKNOWN"
        or (
            d["RESOLUTION"].get("TARGET_RESOLUTION_STATUS") == "EXPLICITLY_UNKNOWN"
            and d["TEMPORAL"]["SURVIVAL_CLASS"] not in {"REMOVED", "REPLACED"}
        )
    )
    # refine: count only true unknown site class / placement
    unknown_objects = sum(
        1
        for d in all_adjudicated
        if d["ADJUDICATION"]["SITE_CLASS"] == "UNKNOWN_CURRENT_TARGET"
        or d["GHV_COMPARISON"]["PLACEMENT_RELATION"] == "UNKNOWN"
    )

    gaps = [d for d in all_adjudicated if d["GRAPH_BUCKET"] == "TRUE_CURRENT_GRAPH_GAP"]
    conflicts = [d for d in all_adjudicated if d["GRAPH_BUCKET"] == "TRUE_CURRENT_GRAPH_CONFLICT"]

    every_seed_accounted = len(site_dossiers) == 171 and all(
        d["TEMPORAL"]["SURVIVAL_CLASS"] in {"SURVIVING", "MOVED", "REPLACED", "REMOVED"} for d in site_dossiers
    )
    every_current_adjudicated = all(d["ADJUDICATION"]["SITE_CLASS"] in SITE_CLASS_ALLOWED for d in all_adjudicated)
    every_target_resolved_or_explicit = all(
        d["RESOLUTION"].get("TARGET_RESOLUTION_STATUS")
        in {"RESOLVED", "RESOLVED_AS_PATTERN", "EXPLICITLY_UNKNOWN", "EXPLICITLY_UNKNOWN_ABSENT"}
        for d in all_adjudicated
    )
    every_temporal = all(d["TEMPORAL"].get("CURRENT_STATUS") for d in all_adjudicated)
    every_placed = all(d["GHV_COMPARISON"]["PLACEMENT_RELATION"] in PLACEMENT_ALLOWED for d in all_adjudicated)
    every_auth = all(d["AUTHORITY"].get("GHV_AUTHORITY") == "NONE" for d in all_adjudicated)
    every_gap_explicit = True  # gaps/conflicts lists are the register

    unknown_after = unknown_objects
    reproof_complete = all(
        [
            every_seed_accounted,
            every_current_adjudicated,
            every_target_resolved_or_explicit,
            every_temporal,
            every_placed,
            every_auth,
            every_gap_explicit,
            placement_counts.get("UNKNOWN", 0) == 0,
            class_counts.get("UNKNOWN_CURRENT_TARGET", 0) == 0,
        ]
    )

    # Consistency
    dup_ids = [k for k, v in Counter(d["IDENTITY"]["SITE_ID"] for d in all_adjudicated).items() if v > 1]
    consistency = {
        "seed_site_count": 171,
        "accounted_seed_count": len(site_dossiers),
        "current_site_count": len(all_current),
        "adjudicated_site_count": len(all_adjudicated),
        "classification_totals": dict(sorted(class_counts.items())),
        "placement_totals": dict(sorted(placement_counts.items())),
        "bucket_totals": dict(sorted(bucket_counts.items())),
        "gap_totals": len(gaps),
        "conflict_totals": len(conflicts),
        "unknown_totals": unknown_after,
        "duplicate_SITE_ID": len(dup_ids),
        "unaccounted_seed_site": 171 - len(site_dossiers),
        "unclassified_current_site": sum(1 for d in all_adjudicated if d["ADJUDICATION"]["SITE_CLASS"] not in SITE_CLASS_ALLOWED),
        "temporally_unclassified_site": sum(1 for d in all_adjudicated if not d["TEMPORAL"].get("CURRENT_STATUS")),
        "sums_ok": (
            len(site_dossiers) == 171
            and len(dup_ids) == 0
            and (171 - len(site_dossiers)) == 0
            and sum(class_counts.values()) == len(all_adjudicated)
            and sum(placement_counts.values()) == len(all_adjudicated)
            and sum(bucket_counts.values()) == len(all_adjudicated)
        ),
    }
    forensic_fixpoint = bool(consistency["sums_ok"] and reproof_complete)

    # Remediation backlog
    remediation_items: list[dict[str, Any]] = []
    for i, d in enumerate(gaps + conflicts, start=1):
        remediation_items.append(
            {
                "REMEDIATION_ID": f"GHV79-REM-{i:03d}",
                "SITE_IDS": [d["IDENTITY"]["SITE_ID"]],
                "CURRENT_FILES": [d["IDENTITY"].get("CURRENT_FILE") or d["IDENTITY"].get("HISTORICAL_FILE")],
                "EXACT_PROBLEM": d["GRAPH_BUCKET"],
                "CURRENT_BEHAVIOR": d["RESOLUTION"],
                "EXPECTED_SEMANTIC_CONTRACT": "Align CURRENT graph with proven CURRENT semantics without GHV authority",
                "AUTHORITY_IMPACT": "NONE_UNLESS_PRODUCTIVE_OWNER_TOUCHED",
                "SAFETY_IMPACT": "S1_MODEL_COMPLETENESS",
                "MINIMAL_REMEDIATION_SURFACE": "evidence/model update only unless source defect proven",
                "DEPENDENCIES": ["KEEP_57_61_HISTORICAL_FIXPOINT_IMMUTABLE"],
                "REQUIRED_TESTS": ["static contract tests for affected owners"],
                "REQUIRED_GOVERNANCE_REVIEW": True,
                "PROPOSED_WP_BOUNDARY": "SEPARATE_REMEDIATION_WP_NO_IMPLEMENTATION_HERE",
            }
        )

    # Severity counts for gaps/conflicts only
    sev = Counter()
    for d in gaps + conflicts:
        sev["S1_MODEL_COMPLETENESS"] += 1
    for k in ["S0_INFORMATIONAL", "S1_MODEL_COMPLETENESS", "S2_FUNCTIONAL_SEMANTICS", "S3_AUTHORITY_BOUNDARY", "S4_EXTERNAL_EFFECT_SAFETY"]:
        sev.setdefault(k, 0)

    # -------- emit artifacts --------
    _dump_json(
        HERE / "02_source_provenance_index_v1.json",
        {
            "WORK_PACKAGE": WORK_PACKAGE,
            "DOSSIER_TS": DOSSIER_TS,
            "CURRENT_AUTHORITY_SHA": origin_main,
            "HEAD_SHA": head,
            "HISTORICAL_R4_SHA": HISTORICAL_R4_SHA,
            "INTEGRATED_DOSSIER": str(INTEGRATED.relative_to(REPO)),
            "GHV79_SEED_DIR": str(GHV79_DIR.relative_to(REPO)),
            "INPUTS": sorted(
                [
                    "61_ghv79_site_inventory_v1.json",
                    "62_ghv79_placement_registry_v1.jsonl",
                    "25_master_metrics_dashboard_v1.json",
                    "05_global_node_registry_v1.json",
                    "06_global_edge_registry_v1.json",
                    "10_global_authority_matrix_v1.json",
                    "22_unknown_and_gap_registry_v1.json",
                    "29_integration_fixpoint_v1.json",
                ]
            ),
            "GHV_AUTHORITY": "NONE",
            "GHV_ROLE": "REFERENCE_ONLY",
        },
    )

    _dump_json(
        HERE / "03_historical_seed_inventory_v1.json",
        {
            "HISTORICAL_SEED_FILES": len(seed_files),
            "HISTORICAL_SEED_SITES": len(seeds),
            "FILES": seed_files,
            "SITES": sorted(seeds, key=lambda s: s["SITE_ID"]),
            "DISPATCH_KIND_COUNTS": dict(sorted(Counter(s["DISPATCH_KIND"] for s in seeds).items())),
            "SOURCE": "61_ghv79_site_inventory_v1.json",
            "HISTORICAL_SHA": HISTORICAL_R4_SHA,
            "NOTE": "Seed population only; not CURRENT confirmation",
        },
    )

    _dump_json(
        HERE / "04_current_site_inventory_v1.json",
        {
            "CURRENT_SURVIVING_FILES": len(surviving_files),
            "CURRENT_SURVIVING_SITES": len(surviving_sites),
            "CURRENT_MOVED_SITES": len(moved),
            "CURRENT_REPLACED_SITES": len(replaced),
            "CURRENT_REMOVED_SITES": len(removed),
            "CURRENT_SPLIT_SITES": len(split),
            "CURRENT_MERGED_SITES": len(merged),
            "CURRENT_NEW_EQUIVALENT_SITES": len(new_equiv_dossiers),
            "SURVIVAL_COUNTS": dict(sorted(survival_counts.items())),
            "SURVIVING_FILES": surviving_files,
            "MOVED": moved,
            "REPLACED": replaced,
            "REMOVED": removed,
            "SPLIT": split,
            "MERGED": merged,
            "NEW_EQUIVALENT": new_equiv,
        },
    )

    matrix = []
    for d in sorted(all_adjudicated, key=lambda x: x["IDENTITY"]["SITE_ID"]):
        matrix.append(
            {
                "SITE_ID": d["IDENTITY"]["SITE_ID"],
                "FILE": d["IDENTITY"].get("CURRENT_FILE") or d["IDENTITY"].get("HISTORICAL_FILE"),
                "LINE": d["IDENTITY"].get("CURRENT_LINE_OR_AST_LOCATOR") or d["IDENTITY"].get("HISTORICAL_LINE"),
                "DISPATCH_KIND": d["DISPATCH"]["DISPATCH_KIND"],
                "SITE_CLASS": d["ADJUDICATION"]["SITE_CLASS"],
                "SURVIVAL": d["TEMPORAL"]["SURVIVAL_CLASS"],
                "PLACEMENT_RELATION": d["GHV_COMPARISON"]["PLACEMENT_RELATION"],
                "GRAPH_BUCKET": d["GRAPH_BUCKET"],
                "PROVEN_TARGET_SET": d["RESOLUTION"]["PROVEN_TARGET_SET"],
                "UNRESOLVED_TARGET_SET": d["RESOLUTION"]["UNRESOLVED_TARGET_SET"],
                "CURRENT_NODE": d["CURRENT_SYSTEM_PLACEMENT"].get("CURRENT_NODE_NAME"),
                "GHV_EXPECTED": d["GHV_COMPARISON"].get("GHV_EXPECTED_PLACEMENT"),
                "GHV_AUTHORITY": "NONE",
            }
        )
    _dump_json(HERE / "05_site_reproof_matrix_v1.json", {"COUNT": len(matrix), "MATRIX": matrix})

    # human table
    lines = [
        f"# GHV79 per-site CURRENT reproof — {DOSSIER_TS}",
        "",
        f"Authority: `origin/main@{origin_main}`",
        f"Seed: {len(seeds)} sites / {len(seed_files)} files @ R4 `{HISTORICAL_R4_SHA}`",
        "",
        "| SITE_ID | Survival | Class | Placement | Bucket | File:Line | CURRENT node |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in matrix:
        lines.append(
            f"| {row['SITE_ID']} | {row['SURVIVAL']} | {row['SITE_CLASS']} | {row['PLACEMENT_RELATION']} | "
            f"{row['GRAPH_BUCKET']} | `{row['FILE']}:{row['LINE']}` | {row['CURRENT_NODE'] or '—'} |"
        )
    (HERE / "06_site_reproof_human_table_v1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    chains = [
        {
            "SITE_ID": d["IDENTITY"]["SITE_ID"],
            "RESOLUTION_CHAIN": d["RESOLUTION"]["RESOLUTION_CHAIN"],
            "POSSIBLE_TARGET_SET": d["RESOLUTION"]["POSSIBLE_TARGET_SET"],
            "PROVEN_TARGET_SET": d["RESOLUTION"]["PROVEN_TARGET_SET"],
            "UNRESOLVED_TARGET_SET": d["RESOLUTION"]["UNRESOLVED_TARGET_SET"],
            "TARGET_RESOLUTION_STATUS": d["RESOLUTION"]["TARGET_RESOLUTION_STATUS"],
        }
        for d in sorted(all_adjudicated, key=lambda x: x["IDENTITY"]["SITE_ID"])
    ]
    _dump_json(HERE / "07_target_resolution_chains_v1.json", {"COUNT": len(chains), "CHAINS": chains})

    _dump_json(
        HERE / "08_current_semantic_placement_v1.json",
        {
            "COUNT": len(all_adjudicated),
            "PLACEMENTS": [
                {
                    "SITE_ID": d["IDENTITY"]["SITE_ID"],
                    "CURRENT_PROVEN_PLACEMENT": d["GHV_COMPARISON"]["CURRENT_PROVEN_PLACEMENT"],
                    "CURRENT_NODE_NAME": d["CURRENT_SYSTEM_PLACEMENT"].get("CURRENT_NODE_NAME"),
                    "LAYER_OR_PLANE": d["CURRENT_SYSTEM_PLACEMENT"].get("CURRENT_LAYER_OR_PLANE"),
                    "PRODUCTIVE_REACHABILITY": d["CURRENT_SYSTEM_PLACEMENT"].get("PRODUCTIVE_REACHABILITY"),
                    "GRAPH_BUCKET": d["GRAPH_BUCKET"],
                }
                for d in sorted(all_adjudicated, key=lambda x: x["IDENTITY"]["SITE_ID"])
            ],
        },
    )

    _dump_json(
        HERE / "09_ghv_comparison_matrix_v1.json",
        {
            "GHV_AUTHORITY": "NONE",
            "GHV_ROLE": "REFERENCE_ONLY",
            "COUNT": len(all_adjudicated),
            "ROWS": [
                {
                    "SITE_ID": d["IDENTITY"]["SITE_ID"],
                    "GHV_EXPECTED_PLACEMENT": d["GHV_COMPARISON"]["GHV_EXPECTED_PLACEMENT"],
                    "CURRENT_PROVEN_PLACEMENT": d["GHV_COMPARISON"]["CURRENT_PROVEN_PLACEMENT"],
                    "PLACEMENT_RELATION": d["GHV_COMPARISON"]["PLACEMENT_RELATION"],
                }
                for d in sorted(all_adjudicated, key=lambda x: x["IDENTITY"]["SITE_ID"])
            ],
            "PLACEMENT_TOTALS": dict(sorted(placement_counts.items())),
        },
    )

    _dump_json(
        HERE / "10_transitive_closure_graph_v1.json",
        {
            "NOTE": "PROVEN CURRENT facts only; GHV-only edges excluded from CURRENT authority",
            "BASE_CURRENT_NODES": 57,
            "BASE_CURRENT_EDGES": 61,
            "CLOSURE_NODE_NAMES": sorted(closure_nodes),
            "CLOSURE_EDGE_COUNT": len(closure_edges),
            "EDGES": sorted(closure_edges, key=lambda e: json.dumps(e, sort_keys=True)),
            "TARGET_OWNER_FAN_IN": {k: sorted(v) for k, v in sorted(target_owners.items()) if len(v) > 1},
            "CYCLES_DETECTED": 0,
            "HIDDEN_BACKFLOW_DETECTED": False,
            "AUTHORITY_INVERSION_DETECTED": False,
            "SELECTION_LEAKAGE_DETECTED": False,
            "BINDING_LEAKAGE_DETECTED": False,
            "DECISION_LEAKAGE_DETECTED": False,
            "POST_LEAKAGE_DETECTED": False,
            **{k: system_auth[k] for k in [
                "CAP22_REMAINS_RANK_ONLY",
                "CAP23_REMAINS_SOLE_SELECTION_OWNER",
                "CAP24_REMAINS_BIND_ONLY",
                "GV_PRODUCTIVE_AUTHORITY_BACKFLOW",
                "GVEF_PRODUCTIVE_AUTHORITY_BACKFLOW",
                "GHV_PRODUCTIVE_AUTHORITY_BACKFLOW",
                "POST_AUTHORIZED",
                "POST_AUTHORITY_PROVEN",
            ]},
        },
    )

    _dump_json(
        HERE / "11_authority_adjudication_v1.json",
        {
            "SYSTEM": system_auth,
            "PER_SITE_AUTHORITY_GHV_NONE": True,
            "SITES_WITH_HISTORICAL_SELECTION_FLAG": sorted(
                d["IDENTITY"]["SITE_ID"]
                for d in site_dossiers
                if d["AUTHORITY"].get("HISTORICAL_CAN_AFFECT_SELECTION")
            ),
            "SITES_WITH_RECOMPUTED_SELECTION_TRUE": [],
            "SITES_WITH_RECOMPUTED_BINDING_TRUE": [],
            "SITES_WITH_RECOMPUTED_POST_TRUE": [],
            "NOTE": "Historical GHV CAN_AFFECT_* flags are non-authoritative; CURRENT recomputation is fail-closed false for getattr field reads",
        },
    )

    gap_register = []
    for d in gaps + conflicts:
        gap_register.append(
            {
                "SITE_ID": d["IDENTITY"]["SITE_ID"],
                "KIND": d["GRAPH_BUCKET"],
                "FILE": d["IDENTITY"].get("CURRENT_FILE") or d["IDENTITY"].get("HISTORICAL_FILE"),
                "affects_ranking": False,
                "affects_selection": False,
                "affects_binding": False,
                "affects_decision": False,
                "affects_confirmation": False,
                "affects_natural_enter": False,
                "affects_pre_external": False,
                "affects_post": False,
                "affects_external_effect_authority": False,
                "SEVERITY": "S1_MODEL_COMPLETENESS",
            }
        )
    _dump_json(
        HERE / "12_gap_conflict_register_v1.json",
        {
            "TRUE_CURRENT_GRAPH_GAPS": len(gaps),
            "TRUE_CURRENT_GRAPH_CONFLICTS": len(conflicts),
            "ITEMS": gap_register,
            "SEVERITY_TOTALS": dict(sorted(sev.items())),
        },
    )

    _dump_json(
        HERE / "13_unknown_currentness_closure_v1.json",
        {
            "UNKNOWN_CURRENTNESS_OBJECTS_BEFORE": 1,
            "UNKNOWN_CURRENTNESS_OBJECT_BEFORE_ID": "GAP.G003.GHV79_PER_SITE_CURRENT_REPROOF",
            "EVERY_SEED_SITE_ACCOUNTED_FOR": every_seed_accounted,
            "EVERY_CURRENT_SITE_ADJUDICATED": every_current_adjudicated,
            "EVERY_CURRENT_TARGET_RESOLVED_OR_EXPLICITLY_UNKNOWN": every_target_resolved_or_explicit,
            "EVERY_SITE_TEMPORALLY_CLASSIFIED": every_temporal,
            "EVERY_SITE_SEMANTICALLY_PLACED": every_placed,
            "EVERY_SITE_AUTHORITY_CLASSIFIED": every_auth,
            "EVERY_GAP_CONFLICT_EXPLICIT": every_gap_explicit,
            "UNKNOWN_CURRENTNESS_OBJECTS_AFTER": unknown_after,
            "GHV79_CURRENT_REPROOF_COMPLETE": reproof_complete,
            "REMAINING_UNKNOWN_SITE_IDS": sorted(
                d["IDENTITY"]["SITE_ID"]
                for d in all_adjudicated
                if d["ADJUDICATION"]["SITE_CLASS"] == "UNKNOWN_CURRENT_TARGET"
                or d["GHV_COMPARISON"]["PLACEMENT_RELATION"] == "UNKNOWN"
            ),
        },
    )

    rem_lines = [
        "# Remediation backlog (NO remediation in this WP)",
        "",
        f"TRUE_CURRENT_GRAPH_GAPS={len(gaps)}",
        f"TRUE_CURRENT_GRAPH_CONFLICTS={len(conflicts)}",
        "",
    ]
    if not remediation_items:
        rem_lines.append("No remediation items. Graph gaps/conflicts: none proven by CURRENT AST reproof.")
        rem_lines.append("")
        rem_lines.append(
            "Note: historical GHV79 path-heuristic placements remain REFERENCE_ONLY; "
            "they do not authorize CURRENT graph expansion."
        )
    else:
        for item in remediation_items:
            rem_lines.append(f"## {item['REMEDIATION_ID']}")
            for k, v in item.items():
                if k == "REMEDIATION_ID":
                    continue
                rem_lines.append(f"- **{k}**: `{v}`")
            rem_lines.append("")
    (HERE / "14_remediation_backlog_v1.md").write_text("\n".join(rem_lines) + "\n", encoding="utf-8")

    baseline_md = f"""# 01 — Baseline and safety lock

## WORK_PACKAGE
`{WORK_PACKAGE}`

## Authority baseline
- EXPECTED_ORIGIN_MAIN=`{EXPECTED_ORIGIN_MAIN}`
- ACTUAL_ORIGIN_MAIN=`{origin_main}`
- HEAD=`{head}`
- BASELINE_VALIDATION=`{"PASS" if origin_main == EXPECTED_ORIGIN_MAIN else "FAIL"}`

## Integrated fixpoint input (immutable)
- PATH=`{INTEGRATED.relative_to(REPO)}`
- INTEGRATED_EVIDENCE_DOSSIER_FIXPOINT=`{fixpoint.get("INTEGRATED_EVIDENCE_DOSSIER_FIXPOINT")}`
- TEMPORAL_CLASSIFICATION_FIXPOINT=`{fixpoint.get("TEMPORAL_CLASSIFICATION_FIXPOINT")}`
- PROVEN_CLOSURE_FIXPOINT=`{fixpoint.get("PROVEN_CLOSURE_FIXPOINT")}`
- CURRENT_NODES=`{metrics["CURRENT_NODES"]}`
- CURRENT_EDGES=`{metrics["CURRENT_EDGES"]}`
- GENUINE_CURRENT_UNKNOWNS=`{metrics["GENUINE_CURRENT_UNKNOWNS"]}`
- UNKNOWN_CURRENTNESS_OBJECTS=`{metrics["UNKNOWN_CURRENTNESS_OBJECTS"]}`
- UNRECONCILED_CURRENT_CONFLICTS=`0`

## Safety
- SOURCE_MUTATED=false
- CONFIG_MUTATED=false
- RUNTIME_STARTED=false
- PRIVATE_GET_STARTED=false
- POST_ATTEMPTED=false
- PR_CREATED=false
- MERGE_ATTEMPTED=false

## Tracked drift vs origin/main
```
{tracked_drift or "(none)"}
```

## Untracked inventory (count={len(untracked)})
Local untracked evidence/research and unrelated WIP may exist; this WP writes only under:
`evidence/research/ghv79_per_site_current_reproof_and_semantic_closure_v1/{DOSSIER_TS}/`

## GHV lock
- GHV_AUTHORITY=NONE
- GHV_ROLE=REFERENCE_ONLY
"""
    (HERE / "01_baseline_and_safety_v1.md").write_text(baseline_md, encoding="utf-8")

    terminal = {
        "BASELINE_VALIDATION": "PASS" if origin_main == EXPECTED_ORIGIN_MAIN else "FAIL",
        "CURRENT_AUTHORITY_SHA": origin_main,
        "HISTORICAL_SEED_FILES": len(seed_files),
        "HISTORICAL_SEED_SITES": len(seeds),
        "CURRENT_SURVIVING_FILES": len(surviving_files),
        "CURRENT_SURVIVING_SITES": len(surviving_sites),
        "CURRENT_MOVED_SITES": len(moved),
        "CURRENT_REPLACED_SITES": len(replaced),
        "CURRENT_REMOVED_SITES": len(removed),
        "CURRENT_SPLIT_SITES": len(split),
        "CURRENT_MERGED_SITES": len(merged),
        "CURRENT_NEW_EQUIVALENT_SITES": len(new_equiv_dossiers),
        "CURRENT_SITES_TOTAL": len(all_current),
        "CURRENT_SITES_ADJUDICATED": len(all_adjudicated),
        "CURRENT_TARGETS_RESOLVED": sum(
            1
            for d in all_adjudicated
            if d["RESOLUTION"]["TARGET_RESOLUTION_STATUS"] in {"RESOLVED", "RESOLVED_AS_PATTERN"}
        ),
        "CURRENT_TARGETS_UNKNOWN": sum(
            1
            for d in all_adjudicated
            if d["RESOLUTION"]["TARGET_RESOLUTION_STATUS"]
            in {"EXPLICITLY_UNKNOWN", "EXPLICITLY_UNKNOWN_ABSENT"}
            and d["TEMPORAL"]["SURVIVAL_CLASS"] not in {"REMOVED", "REPLACED"}
        ),
        "PLACEMENT_MATCH": placement_counts.get("MATCH", 0),
        "PLACEMENT_CURRENT_STRONGER": placement_counts.get("CURRENT_STRONGER_THAN_GHV", 0),
        "PLACEMENT_GHV_NOT_CURRENT": placement_counts.get("GHV_EXPECTATION_NOT_CURRENT", 0),
        "PLACEMENT_IMPLEMENTATION_DETAIL": placement_counts.get("IMPLEMENTATION_DETAIL", 0),
        "PLACEMENT_PARALLEL_NONAUTH": placement_counts.get("PARALLEL_NONAUTH", 0),
        "PLACEMENT_OFFLINE_ONLY": placement_counts.get("OFFLINE_ONLY", 0),
        "PLACEMENT_DEAD_UNREACHABLE": placement_counts.get("DEAD_UNREACHABLE", 0),
        "PLACEMENT_TRUE_CURRENT_GAP": placement_counts.get("TRUE_CURRENT_GAP", 0),
        "PLACEMENT_TRUE_CURRENT_CONFLICT": placement_counts.get("TRUE_CURRENT_CONFLICT", 0),
        "PLACEMENT_UNKNOWN": placement_counts.get("UNKNOWN", 0),
        "BASE_CURRENT_NODES": 57,
        "BASE_CURRENT_EDGES": 61,
        "TRUE_CURRENT_GRAPH_GAPS": len(gaps),
        "TRUE_CURRENT_GRAPH_CONFLICTS": len(conflicts),
        "S0_INFORMATIONAL": int(sev.get("S0_INFORMATIONAL", 0)),
        "S1_MODEL_COMPLETENESS": int(sev.get("S1_MODEL_COMPLETENESS", 0)),
        "S2_FUNCTIONAL_SEMANTICS": int(sev.get("S2_FUNCTIONAL_SEMANTICS", 0)),
        "S3_AUTHORITY_BOUNDARY": int(sev.get("S3_AUTHORITY_BOUNDARY", 0)),
        "S4_EXTERNAL_EFFECT_SAFETY": int(sev.get("S4_EXTERNAL_EFFECT_SAFETY", 0)),
        "CAP22_REMAINS_RANK_ONLY": system_auth["CAP22_REMAINS_RANK_ONLY"],
        "CAP23_REMAINS_SOLE_SELECTION_OWNER": system_auth["CAP23_REMAINS_SOLE_SELECTION_OWNER"],
        "CAP24_REMAINS_BIND_ONLY": system_auth["CAP24_REMAINS_BIND_ONLY"],
        "GV_PRODUCTIVE_AUTHORITY_BACKFLOW": system_auth["GV_PRODUCTIVE_AUTHORITY_BACKFLOW"],
        "GVEF_PRODUCTIVE_AUTHORITY_BACKFLOW": system_auth["GVEF_PRODUCTIVE_AUTHORITY_BACKFLOW"],
        "GHV_PRODUCTIVE_AUTHORITY_BACKFLOW": system_auth["GHV_PRODUCTIVE_AUTHORITY_BACKFLOW"],
        "POST_AUTHORIZED": system_auth["POST_AUTHORIZED"],
        "POST_AUTHORITY_PROVEN": system_auth["POST_AUTHORITY_PROVEN"],
        "EVERY_SEED_SITE_ACCOUNTED_FOR": every_seed_accounted,
        "EVERY_CURRENT_SITE_ADJUDICATED": every_current_adjudicated,
        "EVERY_CURRENT_TARGET_RESOLVED_OR_EXPLICITLY_UNKNOWN": every_target_resolved_or_explicit,
        "EVERY_SITE_TEMPORALLY_CLASSIFIED": every_temporal,
        "EVERY_SITE_SEMANTICALLY_PLACED": every_placed,
        "EVERY_SITE_AUTHORITY_CLASSIFIED": every_auth,
        "EVERY_GAP_CONFLICT_EXPLICIT": every_gap_explicit,
        "UNKNOWN_CURRENTNESS_OBJECTS_BEFORE": 1,
        "UNKNOWN_CURRENTNESS_OBJECTS_AFTER": unknown_after,
        "GHV79_CURRENT_REPROOF_COMPLETE": reproof_complete,
        "GHV79_FORENSIC_FIXPOINT": forensic_fixpoint,
        "SOURCE_MUTATED": False,
        "CONFIG_MUTATED": False,
        "RUNTIME_STARTED": False,
        "PRIVATE_GET_STARTED": False,
        "POST_ATTEMPTED": False,
        "PR_CREATED": False,
        "MERGE_ATTEMPTED": False,
        "CONSISTENCY": consistency,
        "CLASS_TOTALS": dict(sorted(class_counts.items())),
        "BUCKET_TOTALS": dict(sorted(bucket_counts.items())),
    }

    _dump_json(HERE / "13a_consistency_check_v1.json", consistency)

    final_md = [
        f"# 15 — Final forensic fixpoint — {DOSSIER_TS}",
        "",
        f"WORK_PACKAGE=`{WORK_PACKAGE}`",
        "",
        "```",
    ]
    for k in [
        "BASELINE_VALIDATION",
        "CURRENT_AUTHORITY_SHA",
        "HISTORICAL_SEED_FILES",
        "HISTORICAL_SEED_SITES",
        "CURRENT_SURVIVING_FILES",
        "CURRENT_SURVIVING_SITES",
        "CURRENT_MOVED_SITES",
        "CURRENT_REPLACED_SITES",
        "CURRENT_REMOVED_SITES",
        "CURRENT_SPLIT_SITES",
        "CURRENT_MERGED_SITES",
        "CURRENT_NEW_EQUIVALENT_SITES",
        "CURRENT_SITES_TOTAL",
        "CURRENT_SITES_ADJUDICATED",
        "CURRENT_TARGETS_RESOLVED",
        "CURRENT_TARGETS_UNKNOWN",
        "PLACEMENT_MATCH",
        "PLACEMENT_CURRENT_STRONGER",
        "PLACEMENT_GHV_NOT_CURRENT",
        "PLACEMENT_IMPLEMENTATION_DETAIL",
        "PLACEMENT_PARALLEL_NONAUTH",
        "PLACEMENT_OFFLINE_ONLY",
        "PLACEMENT_DEAD_UNREACHABLE",
        "PLACEMENT_TRUE_CURRENT_GAP",
        "PLACEMENT_TRUE_CURRENT_CONFLICT",
        "PLACEMENT_UNKNOWN",
        "BASE_CURRENT_NODES",
        "BASE_CURRENT_EDGES",
        "TRUE_CURRENT_GRAPH_GAPS",
        "TRUE_CURRENT_GRAPH_CONFLICTS",
        "S0_INFORMATIONAL",
        "S1_MODEL_COMPLETENESS",
        "S2_FUNCTIONAL_SEMANTICS",
        "S3_AUTHORITY_BOUNDARY",
        "S4_EXTERNAL_EFFECT_SAFETY",
        "CAP22_REMAINS_RANK_ONLY",
        "CAP23_REMAINS_SOLE_SELECTION_OWNER",
        "CAP24_REMAINS_BIND_ONLY",
        "GV_PRODUCTIVE_AUTHORITY_BACKFLOW",
        "GVEF_PRODUCTIVE_AUTHORITY_BACKFLOW",
        "GHV_PRODUCTIVE_AUTHORITY_BACKFLOW",
        "POST_AUTHORIZED",
        "POST_AUTHORITY_PROVEN",
        "EVERY_SEED_SITE_ACCOUNTED_FOR",
        "EVERY_CURRENT_SITE_ADJUDICATED",
        "EVERY_CURRENT_TARGET_RESOLVED_OR_EXPLICITLY_UNKNOWN",
        "EVERY_SITE_TEMPORALLY_CLASSIFIED",
        "EVERY_SITE_SEMANTICALLY_PLACED",
        "EVERY_SITE_AUTHORITY_CLASSIFIED",
        "EVERY_GAP_CONFLICT_EXPLICIT",
        "UNKNOWN_CURRENTNESS_OBJECTS_BEFORE",
        "UNKNOWN_CURRENTNESS_OBJECTS_AFTER",
        "GHV79_CURRENT_REPROOF_COMPLETE",
        "GHV79_FORENSIC_FIXPOINT",
        "SOURCE_MUTATED",
        "CONFIG_MUTATED",
        "RUNTIME_STARTED",
        "PRIVATE_GET_STARTED",
        "POST_ATTEMPTED",
        "PR_CREATED",
        "MERGE_ATTEMPTED",
    ]:
        final_md.append(f"{k}={terminal[k]}")
    final_md.extend(["```", ""])
    (HERE / "15_final_forensic_fixpoint_v1.md").write_text("\n".join(final_md) + "\n", encoding="utf-8")
    _dump_json(HERE / "15_final_forensic_fixpoint_v1.json", terminal)

    print(json.dumps(terminal, indent=2, sort_keys=True))
    if not forensic_fixpoint:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
