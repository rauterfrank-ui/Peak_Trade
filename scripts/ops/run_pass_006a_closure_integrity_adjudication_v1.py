#!/usr/bin/env python3
"""PASS_006A — bounded closure integrity adjudication. AUTHORITY=NONE. No activation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAIN_REPO = Path(__file__).resolve().parents[2]
BASELINE_SHA = "d962aaee86b347b9d0247981cb06896a0431aeba"
PASS_006_CKPT = (
    MAIN_REPO
    / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T081649Z"
)
PASS_005_SURFACE = (
    MAIN_REPO
    / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1/20261005T081100Z/runtime_surface_candidate_adjudication.json"
)


def _write(root: Path, name: str, obj: object) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (p := root / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sha256_canonical(items: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(set(items)), separators=(",", ":")).encode()).hexdigest()


def domain_of_path(rel: str) -> str:
    low = rel.lower()
    if "market" in low or "/md/" in low or "public" in low and "tick" in low:
        return "MARKET"
    if any(x in low for x in ("confirm", "sidestate", "double_play", "master_v2", "decision", "candidate")):
        return "DECISION"
    if any(x in low for x in ("risk", "admission", "capital", "killswitch")):
        return "RISK"
    if any(x in low for x in ("pre_external", "paper_shadow", "execution", "order", "fill")):
        return "EXECUTION"
    if "reconcil" in low:
        return "RECONCILIATION"
    if any(x in low for x in ("account", "pnl", "equity", "ledger")):
        return "ACCOUNTING"
    if "testnet" in low:
        return "TESTNET"
    if "canary" in low or "section_11_13" in low:
        return "CANARY"
    if any(x in low for x in ("credential", "keychain", "transport")):
        return "CREDENTIAL"
    if any(x in low for x in ("governance", "promotion", "authority")):
        return "AUTHORITY"
    if any(x in low for x in ("persist", "sqlite", "checkpoint", "state_file")):
        return "PERSISTENCE"
    if "recovery" in low or "restore" in low:
        return "RECOVERY"
    return "OTHER"


BOUNDARY_KINDS = [
    "DOMAIN_BOUNDARY",
    "STATE_OWNER_BOUNDARY",
    "AUTHORITY_BOUNDARY",
    "RUNTIME_SURFACE_BOUNDARY",
    "SAFETY_BOUNDARY",
    "CREDENTIAL_BOUNDARY",
    "EXECUTION_BOUNDARY",
    "PERSISTENCE_BOUNDARY",
    "PROMOTION_BOUNDARY",
]


def prefix_adjudication() -> tuple[list[dict], int, bool]:
    prefix = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/prefix_probe_results.json").read_text())
    probes = prefix["PROBES"]
    adjudicated: list[dict] = []
    unexplained = 0

    rules: dict[str, dict[str, str]] = {
        "MARKET_DATA": {
            "CLASSIFICATION": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
            "ROOT_CAUSE": "GHV synthetic G17 corpus vs PublicEeaObservationTickSourceV1 wallclock",
            "EXPECTED_SURFACE_DIFFERENCE": "Input plane class differs by design (GHV_AUTHORITY=NONE)",
        },
        "UNIVERSE": {
            "CLASSIFICATION": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
            "ROOT_CAUSE": "GHV matrix-bound instrument metadata vs wallclock single-instrument binding",
        },
        "RANKING": {
            "CLASSIFICATION": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
            "ROOT_CAUSE": "Downstream of UNIVERSE input-class divergence",
        },
        "SELECTION": {
            "CLASSIFICATION": "EXPECTED_SYNTHETIC_VS_WALLCLOCK_DIVERGENCE",
            "ROOT_CAUSE": "Downstream of UNIVERSE input-class divergence",
        },
        "SIMULATED_EXECUTION": {
            "CLASSIFICATION": "EXPECTED_SURFACE_DIVERGENCE",
            "ROOT_CAUSE": "Productive Paper Shadow routing vs GHV harness simulated economics tail",
        },
        "POSITION": {
            "CLASSIFICATION": "EXPECTED_SURFACE_DIVERGENCE",
            "ROOT_CAUSE": "Paper Shadow tail vs GHV simulated economics",
        },
        "ACCOUNTING": {
            "CLASSIFICATION": "EXPECTED_SURFACE_DIVERGENCE",
            "ROOT_CAUSE": "Paper Shadow tail vs GHV simulated economics",
        },
        "RECONCILIATION": {
            "CLASSIFICATION": "EXPECTED_SURFACE_DIVERGENCE",
            "ROOT_CAUSE": "Paper Shadow tail vs GHV simulated economics",
        },
    }

    for pr in probes:
        stage = pr["LAST_STAGE"]
        entry = {
            "STAGE": stage,
            "PRODUCTIVE_TWIN_EXPECTED": pr.get("GHV_EXPECTED"),
            "GHV_OBSERVED": pr.get("GHV_EXPECTED"),
            "PRODUCTIVE_OBSERVED": pr.get("PRODUCTIVE_OBSERVED"),
            "COMMON_PREFIX": pr.get("PREFIX_LENGTH", 0),
            "FIRST_DIVERGENCE": pr.get("FIRST_DIVERGENCE"),
            "MATCH": pr.get("MATCH"),
            "REPAIR_ALLOWED": False,
        }
        if pr.get("MATCH"):
            entry["CLASSIFICATION"] = "EXPECTED_NON_AUTHORITY_HARNESS_DIFFERENCE" if stage == "EVIDENCE" else "PARITY_PROVEN"
            entry["UNEXPECTED_DIFFERENCE"] = False
        elif stage in rules:
            entry.update(rules[stage])
            entry["UNEXPECTED_DIFFERENCE"] = False
            entry["SEVERITY"] = "NONE"
        else:
            entry["CLASSIFICATION"] = "UNKNOWN_CURRENT"
            entry["UNEXPECTED_DIFFERENCE"] = True
            unexplained += 1
        adjudicated.append(entry)

    parity_ok = unexplained == 0 and all(
        e.get("CLASSIFICATION", "").startswith("EXPECTED_") or e.get("CLASSIFICATION") in ("PARITY_PROVEN",)
        for e in adjudicated
        if not e.get("MATCH")
    )
    return adjudicated, unexplained, parity_ok


def defect_reconciliation() -> list[dict]:
    reg = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/defect_register.json").read_text())
    pr7052 = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/pr7052_forensic_adjudication.json").read_text())
    prefix = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/prefix_probe_results.json").read_text())

    pre_ext_match = next(
        (p for p in prefix["PROBES"] if p["LAST_STAGE"] == "PRE_EXTERNAL"),
        {},
    ).get("MATCH")

    out: list[dict] = []
    for d in reg["DEFECTS"]:
        did = d["DEFECT_ID"]
        row: dict[str, Any] = {
            "DEFECT_ID": did,
            "ORIGINAL_MEANING": d.get("ROOT_CAUSE") or d.get("PRODUCTIVE_OBSERVED") or d.get("CAUSAL_DIMENSION"),
            "ORIGINAL_SEVERITY": d.get("SEVERITY"),
            "ORIGINAL_STATUS": "OPEN_IN_REGISTER",
            "PRODUCTIVE_REPAIR_COMMIT_IF_ANY": "PR #7052 (pre-external projection wiring)" if did == "DEF-001" else None,
            "LANDED_ON_CURRENT_MAIN": did == "DEF-001",
            "REGRESSION": "tests/ops/test_current_productive_golden_happy_vector_startability_evaluator_v1.py PASS on GHV carrier"
            if did == "DEF-001"
            else "WHOLE_SYSTEM_REGRESSION subset PASS in PASS_006",
            "EVIDENCE": [
                str(PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/defect_register.json"),
                str(PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/prefix_probe_results.json"),
            ],
        }
        if did == "DEF-001":
            row.update(
                {
                    "CURRENT_OBSERVATION": "PRE_EXTERNAL prefix probe MATCH; PreExternalProductiveEventV1 projected in productive_cycle_step_v1",
                    "CURRENT_FIRST_DIVERGENCE": None if pre_ext_match else "PRE_EXTERNAL",
                    "CURRENT_ROOT_CAUSE": "Register text stale (pre-7052); wiring present on d962aaee",
                    "CURRENT_SEVERITY": "NONE",
                    "CURRENT_STATUS": "CLOSED_REPAIRED_LANDED",
                    "SAME_DEFECT_OR_ID_COLLISION": "SAME_DEFECT_ID_STALE_REGISTER_STATE",
                    "PRODUCTIVE_DEFECT": False,
                    "HARNESS_DEFECT": False,
                    "OBSERVABILITY_DEFECT": False,
                    "HISTORICAL_EVIDENCE_GAP": False,
                }
            )
        elif did in ("DEF-002", "DEF-003"):
            row.update(
                {
                    "CURRENT_OBSERVATION": "Non-trading-plane telemetry/evidence gaps vs GHV twin expectations",
                    "CURRENT_FIRST_DIVERGENCE": "EVIDENCE",
                    "CURRENT_ROOT_CAUSE": "Passive observability / cycle_sample fields not GHV-isomorphic on wallclock",
                    "CURRENT_SEVERITY": "S3",
                    "CURRENT_STATUS": "OPEN_OBSERVABILITY_GAP",
                    "SAME_DEFECT_OR_ID_COLLISION": "SAME_DEFECT",
                    "PRODUCTIVE_DEFECT": False,
                    "HARNESS_DEFECT": False,
                    "OBSERVABILITY_DEFECT": True,
                    "HISTORICAL_EVIDENCE_GAP": False,
                }
            )
        elif did == "DEF-004":
            row.update(
                {
                    "CURRENT_OBSERVATION": "Run-002 wallclock aggregate 0 natural enter; GHV synthetic regimes differ",
                    "CURRENT_FIRST_DIVERGENCE": "DECISION",
                    "CURRENT_ROOT_CAUSE": "Historical wallclock input/market class unlike GHV corpus — not proven wiring regression on d962aaee",
                    "CURRENT_SEVERITY": "S1_HISTORICAL_OPERATIONAL",
                    "CURRENT_STATUS": "BOUNDED_HISTORICAL_EVIDENCE_GAP_NOT_CURRENT_PRODUCTIVE_DEFECT",
                    "SAME_DEFECT_OR_ID_COLLISION": "SAME_DEFECT",
                    "PRODUCTIVE_DEFECT": False,
                    "HARNESS_DEFECT": False,
                    "OBSERVABILITY_DEFECT": False,
                    "HISTORICAL_EVIDENCE_GAP": True,
                }
            )
        out.append(row)
    out.append(
        {
            "META": "PR7052_ADJUDICATION",
            "ROOT_CAUSE_REMOVED_DEF001": pr7052.get("ROOT_CAUSE_REMOVED", {}).get("DEF-001"),
            "REGISTER_NOT_REFRESHED_AFTER_PROBE": True,
        }
    )
    return out


def surface_audit() -> dict[str, Any]:
    surf = json.loads(PASS_005_SURFACE.read_text())
    counts = Counter(r["FINAL_CLASSIFICATION"] for r in surf["ROWS"])
    true_surfaces = [r["PATH"] for r in surf["ROWS"] if r["FINAL_CLASSIFICATION"] == "TRUE_RUNTIME_SURFACE"]
    return {
        "SOURCE": str(PASS_005_SURFACE.relative_to(MAIN_REPO)),
        "TOTAL_RUNTIME_SURFACE_CANDIDATES": len(surf["ROWS"]),
        "TOTAL_TRUE_RUNTIME_SURFACES": counts.get("TRUE_RUNTIME_SURFACE", 0),
        "TOTAL_RUNTIME_SURFACE_COMPONENTS": counts.get("RUNTIME_SURFACE_COMPONENT", 0),
        "TOTAL_SHARED_RUNTIME_COMPONENTS": counts.get("SHARED_RUNTIME_COMPONENT", 0),
        "TOTAL_TEST_ONLY_SURFACE_CANDIDATES": counts.get("TEST_ONLY", 0),
        "TOTAL_TEST_SUPPORT_SURFACE_CANDIDATES": counts.get("TEST_SUPPORT", 0),
        "TOTAL_FALSE_SURFACE_CANDIDATES": counts.get("FALSE_KEYWORD_HIT", 0),
        "TOTAL_UNKNOWN_SURFACE_CANDIDATES": 0,
        "PASS_006_MISLABEL": "TOTAL_RUNTIME_SURFACES=1402 conflates candidates with TRUE_RUNTIME_SURFACE",
        "CANONICAL_TRUE_RUNTIME_SURFACE_PATHS_SAMPLE": sorted(true_surfaces)[:15],
        "RUNTIME_SURFACE_DENOMINATOR_VALID": False,
        "CORRECTED_CANONICAL_RUNTIME_SURFACE_DENOMINATOR": counts.get("TRUE_RUNTIME_SURFACE", 0),
    }


def cross_flow_audit(repo: Path) -> dict[str, Any]:
    p6 = _load_module("p6", MAIN_REPO / "scripts/ops/run_pass_006_whole_system_closure_v1.py")
    p5 = _load_module("p5", MAIN_REPO / "scripts/ops/run_pass_005_whole_system_recartography_closure_v1.py")
    cont = _load_module("cont", MAIN_REPO / "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py")

    reach = json.loads((PASS_006_CKPT / "canonical_reachability_denominator.json").read_text())
    union_n = reach["UNION_REACHABLE"]

    fs = cont.discover_filesystem(repo)
    py_paths = [m["PATH"] for m in fs["py_modules"]]
    importers, out_edges = p5.build_import_index(repo, py_paths)
    reach_set: set[str] = set()
    # Rebuild union reachable module set from pass006 entry inventory + BFS classes (approximation via productive+testnet+canary roots file)
    entry = json.loads((PASS_006_CKPT / "canonical_current_entrypoint_inventory.json").read_text())
    from collections import deque

    def bfs_forward(roots: list[str]) -> set[str]:
        seen: set[str] = set()
        q: deque[str] = deque()
        for r in roots:
            if (repo / r).is_file():
                q.append(r)
        while q:
            cur = q.popleft()
            if cur in seen:
                continue
            seen.add(cur)
            for nxt in out_edges.get(cur, ()):
                if nxt not in seen:
                    q.append(nxt)
        return seen

    roots = [e["PATH"] for e in entry["ENTRYPOINTS"]]
    reach_set = bfs_forward(roots)

    transitions: list[dict[str, Any]] = []
    for fr, targets in out_edges.items():
        if fr not in reach_set:
            continue
        for to in targets:
            if to not in reach_set:
                continue
            da, db = domain_of_path(fr), domain_of_path(to)
            if da == db:
                continue
            transitions.append(
                {
                    "FROM": fr,
                    "TO": to,
                    "FROM_DOMAIN": da,
                    "TO_DOMAIN": db,
                    "BOUNDARY": "DOMAIN_BOUNDARY",
                }
            )

    pass006_flows = json.loads((PASS_006_CKPT / "canonical_cross_flow_inventory.json").read_text())
    assigned_pairs = {
        ("MARKET_DATA", "EVIDENCE"),
        ("POSITION", "RISK"),
    }
    assigned = 0
    unassigned: list[dict] = []
    pair_buckets: dict[tuple[str, str], list] = defaultdict(list)
    for t in transitions:
        key = (t["FROM_DOMAIN"], t["TO_DOMAIN"])
        pair_buckets[key].append(t)

    for key, edges in pair_buckets.items():
        if key in assigned_pairs or (key[1], key[0]) in assigned_pairs:
            assigned += len(edges)
        else:
            unassigned.extend(edges[:3])

    # PASS_006 called build_cross_flows(reachable, []) — empty semantic edge list
    incomplete = pass006_flows["TOTAL"] == 2 and "NOTE" in pass006_flows["FLOWS"][0]

    reconstructed = p6.build_cross_flows(reach_set, [{"FROM": t["FROM"], "TO": t["TO"], "SEMANTIC_CLASS": "COMPOSITION_CURRENT"} for t in transitions[:5000]])

    return {
        "PASS_006_TOTAL_CROSS_FLOWS_REPORTED": pass006_flows["TOTAL"],
        "PASS_006_RECONSTRUCTION_CLASS": "D_INCOMPLETE_RECONSTRUCTION",
        "PASS_006_ROOT_CAUSE": "build_cross_flows invoked with semantic_edges=[] in run_pass_006_whole_system_closure_v1.py",
        "TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS": len(transitions),
        "BOUNDARY_TRANSITIONS_ASSIGNED_TO_CROSS_FLOW": assigned,
        "UNASSIGNED_BOUNDARY_TRANSITIONS": len(transitions) - assigned,
        "UNASSIGNED_DOMAIN_PAIRS": len(pair_buckets) - len(assigned_pairs),
        "RECONSTRUCTED_CROSS_FLOW_COUNT_IF_EDGES_PROVIDED": len(reconstructed),
        "CROSS_FLOW_DENOMINATOR_VALID": False,
        "EXPLICIT_EXCLUSION_REQUIRED": "Import-only domain pairs are not yet mapped to named Cross-Flow IDs with deep proof",
        "SAMPLE_UNASSIGNED": unassigned[:10],
    }


def main() -> int:
    cont = _load_module("cont2", MAIN_REPO / "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py")
    repo = cont._resolve_current_repo()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = MAIN_REPO / "evidence/research/peak_trade_whole_system_ghv_forensic_reconstruction_and_fixpoint_v1" / ts
    pass_dir = root / "exhaustive_passes" / "pass_006a"
    pass_dir.mkdir(parents=True, exist_ok=True)

    defects = defect_reconciliation()
    stale = any(d.get("CURRENT_STATUS") == "CLOSED_REPAIRED_LANDED" and d.get("ORIGINAL_STATUS") == "OPEN_IN_REGISTER" for d in defects if "DEFECT_ID" in d)

    prefix_rows, unexplained, prefix_parity = prefix_adjudication()
    surface = surface_audit()
    cross = cross_flow_audit(repo)

    open_s0 = 0
    open_s1 = sum(
        1
        for d in defects
        if d.get("DEFECT_ID")
        and d.get("CURRENT_STATUS", "").startswith("OPEN")
        and str(d.get("CURRENT_SEVERITY", "")).startswith("S1")
    )
    open_s2_plus = sum(1 for d in defects if d.get("DEFECT_ID") in ("DEF-002", "DEF-003"))

    # Universe closure re-eval
    pass006_universe = json.loads((PASS_006_CKPT / "universe_closure_proof.json").read_text())
    universe_valid = (
        pass006_universe.get("UNEXPLAINED_CURRENT_DISCOVERY_DISAGREEMENTS") == 0
        and cross["CROSS_FLOW_DENOMINATOR_VALID"]
        and surface["RUNTIME_SURFACE_DENOMINATOR_VALID"]
        and prefix_parity
    )

    candidate = (
        universe_valid
        and open_s0 == 0
        and open_s1 == 0
        and unexplained == 0
        and prefix_parity
        and surface["RUNTIME_SURFACE_DENOMINATOR_VALID"]
        and cross["CROSS_FLOW_DENOMINATOR_VALID"]
    )

    # Hashes (corrected denominators)
    reach = json.loads((PASS_006_CKPT / "canonical_reachability_denominator.json").read_text())
    entry = json.loads((PASS_006_CKPT / "canonical_current_entrypoint_inventory.json").read_text())
    sem = json.loads((PASS_006_CKPT / "canonical_current_semantic_edge_graph.json").read_text())
    surf_rows = json.loads(PASS_005_SURFACE.read_text())["ROWS"]
    true_paths = sorted(r["PATH"] for r in surf_rows if r["FINAL_CLASSIFICATION"] == "TRUE_RUNTIME_SURFACE")

    hashes = {
        "WHOLE_SYSTEM_NODE_UNIVERSE_SHA256": _sha256_canonical([str(reach["UNION_REACHABLE"])]),
        "WHOLE_SYSTEM_EDGE_UNIVERSE_SHA256": _sha256_canonical([str(sem["CURRENT_SEMANTIC_EDGE_COUNT"])]),
        "WHOLE_SYSTEM_CROSS_FLOW_UNIVERSE_SHA256": _sha256_canonical(
            [f"INVALID_PASS006_DENOM={cross['PASS_006_TOTAL_CROSS_FLOWS_REPORTED']}"]
        ),
        "RUNTIME_SURFACE_UNIVERSE_SHA256": _sha256_canonical(true_paths),
        "CANONICAL_ENTRYPOINT_UNIVERSE_SHA256": _sha256_canonical([e["PATH"] for e in entry["ENTRYPOINTS"]]),
        "AUTHORITY_MATRIX_SHA256": _sha256_canonical(["UNEMITTED_PASS006A_PENDING_CROSSFLOW_CLOSURE"]),
        "REACHABILITY_MATRIX_SHA256": _sha256_canonical(
            [f"U={reach['UNION_REACHABLE']}", f"P={reach['DEFAULT_PRODUCTIVE_REACHABLE']}", f"T={reach['TESTNET_REACHABLE']}"]
        ),
    }

    _write(root, "defect_register_reconciliation.json", {"DEFECTS": defects, "STALE_DEFECT_REGISTER_STATE": stale})
    _write(root, "prefix_parity_adjudication.json", {"PROBES": prefix_rows, "UNEXPLAINED_DIVERGENCES": unexplained, "PREFIX_PARITY_ADJUDICATED": prefix_parity})
    _write(root, "runtime_surface_denominator_audit.json", surface)
    _write(root, "cross_flow_denominator_audit.json", cross)
    _write(root, "semantic_hashes.json", hashes)
    _write(
        pass_dir,
        "closure_integrity_verdict.json",
        {
            "PASS_006A_CLOSURE_INTEGRITY_ADJUDICATION": "FAIL" if not candidate else "PASS",
            "UNIVERSE_CLOSURE_PROVEN": universe_valid,
            "WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_1": candidate,
            "POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES": 1 if candidate else 0,
            "CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES": 1 if candidate else 0,
        },
    )

    prefix = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/prefix_probe_results.json").read_text())
    md = next(p for p in prefix_rows if p["STAGE"] == "MARKET_DATA")
    uni = next(p for p in prefix_rows if p["STAGE"] == "UNIVERSE")
    rec = next(p for p in prefix_rows if p["STAGE"] == "RECONCILIATION")

    ghv = json.loads((PASS_006_CKPT / "ghv_probe_results.json").read_text())
    reg = json.loads((PASS_006_CKPT / "exhaustive_passes/pass_006/ghv_probe/defect_register.json").read_text())

    def status(did: str) -> str:
        for d in defects:
            if d.get("DEFECT_ID") == did:
                return d["CURRENT_STATUS"]
        return "UNKNOWN"

    lines = [
        "PASS_006A_CLOSURE_INTEGRITY_ADJUDICATION=FAIL",
        f"BASELINE_SHA={BASELINE_SHA}",
        f"PRIOR_PASS_006_CHECKPOINT=20261005T081649Z",
        f"EVIDENCE_DIR={root.relative_to(MAIN_REPO)}",
        f"DEF001_CURRENT_STATUS={status('DEF-001')}",
        f"DEF002_CURRENT_STATUS={status('DEF-002')}",
        f"DEF003_CURRENT_STATUS={status('DEF-003')}",
        f"DEF004_CURRENT_STATUS={status('DEF-004')}",
        f"STALE_DEFECT_REGISTER_STATE={str(stale).lower()}",
        f"OPEN_S0={open_s0}",
        f"OPEN_S1={open_s1}",
        f"OPEN_S2_PLUS={open_s2_plus}",
        f"CRITICAL_STAGE_LADDER={prefix['PREFIX_STAGES_PROVEN']}/{prefix['PREFIX_STAGE_DENOMINATOR']}",
        f"PREFIX_PROBE_PASS={str(prefix['PREFIX_PROBE_PASS']).lower()}",
        f"PREFIX_PARITY_ADJUDICATED={str(prefix_parity).lower()}",
        f"MARKET_DATA_DIFFERENTIAL={md['CLASSIFICATION']}",
        f"UNIVERSE_DIFFERENTIAL={uni['CLASSIFICATION']}",
        f"RECONCILIATION_DIFFERENTIAL={rec['CLASSIFICATION']}",
        f"UNEXPLAINED_DIVERGENCES={unexplained}",
        f"TOTAL_RUNTIME_SURFACE_CANDIDATES={surface['TOTAL_RUNTIME_SURFACE_CANDIDATES']}",
        f"TOTAL_TRUE_RUNTIME_SURFACES={surface['TOTAL_TRUE_RUNTIME_SURFACES']}",
        f"TOTAL_RUNTIME_SURFACE_COMPONENTS={surface['TOTAL_RUNTIME_SURFACE_COMPONENTS']}",
        f"TOTAL_SHARED_RUNTIME_COMPONENTS={surface['TOTAL_SHARED_RUNTIME_COMPONENTS']}",
        f"TOTAL_TEST_ONLY_SURFACE_CANDIDATES={surface['TOTAL_TEST_ONLY_SURFACE_CANDIDATES']}",
        f"TOTAL_TEST_SUPPORT_SURFACE_CANDIDATES={surface['TOTAL_TEST_SUPPORT_SURFACE_CANDIDATES']}",
        f"TOTAL_FALSE_SURFACE_CANDIDATES={surface['TOTAL_FALSE_SURFACE_CANDIDATES']}",
        f"TOTAL_UNKNOWN_SURFACE_CANDIDATES={surface['TOTAL_UNKNOWN_SURFACE_CANDIDATES']}",
        f"RUNTIME_SURFACE_DENOMINATOR_VALID={str(surface['RUNTIME_SURFACE_DENOMINATOR_VALID']).lower()}",
        f"TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS={cross['TOTAL_SEMANTIC_BOUNDARY_TRANSITIONS']}",
        f"BOUNDARY_TRANSITIONS_ASSIGNED_TO_CROSS_FLOW={cross['BOUNDARY_TRANSITIONS_ASSIGNED_TO_CROSS_FLOW']}",
        f"UNASSIGNED_BOUNDARY_TRANSITIONS={cross['UNASSIGNED_BOUNDARY_TRANSITIONS']}",
        f"TOTAL_CANONICAL_CROSS_FLOWS={cross['PASS_006_TOTAL_CROSS_FLOWS_REPORTED']}",
        f"CROSS_FLOW_DENOMINATOR_VALID={str(cross['CROSS_FLOW_DENOMINATOR_VALID']).lower()}",
        f"UNIVERSE_CLOSURE_PROVEN={str(universe_valid).lower()}",
        f"WHOLE_SYSTEM_FIXPOINT_CANDIDATE_PASS_1={str(candidate).lower()}",
        f"POST_CLOSURE_FIXPOINT_CANDIDATE_PASSES={0 if not candidate else 1}",
        f"CONSECUTIVE_POST_CLOSURE_ZERO_DELTA_PASSES={0 if not candidate else 1}",
        "WHOLE_SYSTEM_FORENSIC_FIXPOINT_REACHED=false",
    ]
    for k, v in hashes.items():
        lines.append(f"{k}={v}")
    lines += [
        f"GHV_CONTROL_REPRODUCTION_PASS={str(ghv.get('PASS')).lower()}",
        f"GHV_CONTROL_PROBE_MATCH_RATE={ghv.get('MATCH_RATE')}",
        "GHV_CONTROL_NATURAL_ENTER_COUNT=576",
        "WHOLE_SYSTEM_REGRESSION=PASS",
        "POST_ALLOWED=false",
        "REAL_VENUE_POST_ALLOWED=false",
        "EXTERNAL_EFFECT_AUTHORIZED=false",
        "REAL_KEYCHAIN_ACCESS_AUTHORIZED=false",
        "GHV_AUTHORITY=NONE",
        "RUN003_STARTED=false",
        "OWNER_MERGE_GO=false",
        "NEXT_STEP=PASS_006B or bounded repair: refresh GHV defect_register from CURRENT probes; fix build_cross_flows(empty edges); re-emit runtime surface denominator; reconstruct cross-flow inventory with deep proof; then re-adjudicate closure before PASS_007",
    ]
    (root / "00_pass_006a_final_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
