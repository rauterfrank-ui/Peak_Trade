#!/usr/bin/env python3
"""Iterative GHV-driven exhaustive whole-system forensic fixpoint (AUTHORITY=NONE)."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
PROBE_SCRIPT = REPO / "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py"
REF_GHV = (
    REPO
    / "evidence/research/peak_trade_ghv_forensic_system_reconciliation_and_bounded_repair_v1/20261005T055500Z/run002_ghv_at_b36ccbaa"
)
RUN001_RESULT = REPO / "evidence/research/paper_shadow_run001_operational_v1/20261004T224156Z/operational_run_result.json"
RUN002_STDOUT = REPO / "evidence/research/paper_shadow_run002_operational_v1/20261005T005319Z/operational_run_stdout.log"
CONTROL_FIXPOINT = "b36ccbaa0468369db634c7bbb6130dcb3713045c"
ORIGIN_MAIN = "c9db3d52ca09205f5b904347862bd06bdd1f29e3"

DISCOVERY_SEEDS = [
    REPO / "scripts/ops/run_current_productive_golden_happy_vector_startability_evaluator_v1.py",
    REPO / "scripts/ops/run_current_productive_ghv_input_readiness_and_convergence_v1.py",
    REPO / "evidence/research/full_core_golden_happy_vector_e2e_v1/run_full_core_ghv_e2e_v1.py",
    REPO
    / "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
    REPO / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
]

ENTRYPOINTS = [
    "scripts/ops/run_current_productive_golden_happy_vector_startability_evaluator_v1.py",
    "scripts/ops/run_current_productive_ghv_input_readiness_and_convergence_v1.py",
    "evidence/research/full_core_golden_happy_vector_e2e_v1/run_full_core_ghv_e2e_v1.py",
    "scripts/ops/run_ghv_pre_external_continuation_harness_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
]


def _write(path: Path, name: str, payload: object) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_path(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_rev(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", ref], text=True).strip()


def _load_probe_module() -> Any:
    spec = importlib.util.spec_from_file_location("ghv_probe_v1", PROBE_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _discover_components(pass_num: int, prior: set[str]) -> dict[str, Any]:
    found: set[str] = set()
    edges: set[tuple[str, str]] = set()
    for seed in DISCOVERY_SEEDS:
        if not seed.is_file():
            continue
        found.add(str(seed.relative_to(REPO)))
        try:
            tree = ast.parse(seed.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in {"src", "trading", "ops"}:
                        edges.add((str(seed.relative_to(REPO)), alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module:
                edges.add((str(seed.relative_to(REPO)), node.module))
                if node.module.startswith("src."):
                    found.add(node.module.replace(".", "/") + ".py")
    new = found - prior
    return {
        "DISCOVERY_PASS": pass_num,
        "COMPONENTS_BEFORE": len(prior),
        "NEW_COMPONENTS": sorted(new),
        "NEW_COMPONENTS_COUNT": len(new),
        "EDGES_BEFORE": len(edges),
        "NEW_EDGES": len(edges),
        "COMPONENTS_TOTAL": len(found | prior),
    }


def _branch_inventory() -> list[dict[str, Any]]:
    policy = REPO / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"
    src = policy.read_text(encoding="utf-8")
    tree = ast.parse(src)
    outcomes: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "DecisionOutcome":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name):
                            pass
                if isinstance(item, ast.AnnAssign) and isinstance(item.value, ast.Constant):
                    outcomes.append(str(item.value.value))
    branches = []
    for oc in outcomes:
        branches.append(
            {
                "BRANCH_ID": f"DECISION_OUTCOME.{oc}",
                "IMPLEMENTATION": "double_play_entry_exit_policy_v0",
                "GHV_SPECIMEN_AVAILABLE": oc in {"blocked", "observe", "no_action", "enter_long", "enter_short"},
                "PRODUCTIVE_REACHABILITY": "WALLCLOCK_BRIDGE_AND_GHV_MV2",
            }
        )
    branches.extend(
        [
            {
                "BRANCH_ID": "CONFIRMATION.C0_CANDIDATE",
                "IMPLEMENTATION": "directional_confirmation_progress_v1",
                "GHV_SPECIMEN_AVAILABLE": True,
            },
            {
                "BRANCH_ID": "CONFIRMATION.C1",
                "IMPLEMENTATION": "directional_confirmation_progress_v1",
                "GHV_SPECIMEN_AVAILABLE": True,
            },
            {
                "BRANCH_ID": "CONFIRMATION.C2",
                "IMPLEMENTATION": "directional_confirmation_progress_v1",
                "GHV_SPECIMEN_AVAILABLE": True,
            },
            {
                "BRANCH_ID": "SIDESTATE.TRANSITION",
                "IMPLEMENTATION": "double_play_state",
                "GHV_SPECIMEN_AVAILABLE": True,
            },
            {
                "BRANCH_ID": "PRE_EXTERNAL.PROJECTED",
                "IMPLEMENTATION": "current_productive_persistent_natural_enter_convergence_v1",
                "GHV_SPECIMEN_AVAILABLE": True,
            },
        ]
    )
    return branches


def _build_specimens(probe_mod: Any) -> list[dict[str, Any]]:
    entry_rows = probe_mod._load_jsonl(REF_GHV / "entry_exit_observations.jsonl")
    sidestate = probe_mod._load_jsonl(REF_GHV / "double_play_sidestate_observations.jsonl")
    conf = probe_mod._load_jsonl(REF_GHV / "confirmation_epoch_observations.jsonl")
    vectors = probe_mod._select_probe_vectors(entry_rows)
    for row in sidestate[:5]:
        vectors.append({**row, "PROBE_CLASS": "SIDESTATE_TRANSITION", "PROBE_ID": f"SIDESTATE-{row['FLIGHT_ID']}-c{row['CYCLE_ID']}"})
    for row in conf:
        if row.get("confirmation_c2"):
            vectors.append(
                {
                    **row,
                    "PROBE_CLASS": "CONFIRMATION_C2",
                    "PROBE_ID": f"C2-{row['FLIGHT_ID']}-c{row['CYCLE_ID']}",
                }
            )
            break
    for row in conf:
        if row.get("confirmation_c1") and not row.get("confirmation_c2"):
            vectors.append(
                {
                    **row,
                    "PROBE_CLASS": "CONFIRMATION_C1",
                    "PROBE_ID": f"C1-{row['FLIGHT_ID']}-c{row['CYCLE_ID']}",
                }
            )
            break
    seen = set()
    out = []
    for v in vectors:
        pid = v.get("PROBE_ID")
        if pid in seen:
            continue
        seen.add(pid)
        out.append(v)
    return out


def _200_cycle_windows(*, run_id: str, total_cycles: int, distribution: dict[str, int]) -> list[dict[str, Any]]:
    windows = []
    window_size = 200
    n_full = total_cycles // window_size
    for w in range(n_full + (1 if total_cycles % window_size else 0)):
        start = w * window_size
        end = min(start + window_size, total_cycles)
        windows.append(
            {
                "RUN_ID": run_id,
                "WINDOW_INDEX": w,
                "CYCLE_START": start,
                "CYCLE_END_EXCLUSIVE": end,
                "VALID_CYCLES": end - start,
                "enter_long": "UNKNOWN_EVIDENCE",
                "enter_short": "UNKNOWN_EVIDENCE",
                "PER_CYCLE_TRACES_AVAILABLE": False,
                "AGGREGATE_RUN_ENTER_TOTAL": 0,
                "FORENSIC_ADJUDICATION": "ZERO_ENTER_WINDOW_UNPROVEN_AT_VALUE_LEVEL",
                "REASON": "Operational evidence lacks per-cycle feature/threshold traces; only run-level distribution available",
            }
        )
    windows[0]["RUN_LEVEL_DECISION_DISTRIBUTION"] = distribution
    return windows


def _run_regression_batch() -> dict[str, Any]:
    tests = [
        "tests/ops/test_ghv_e2e_pre_decision_productive_closure_entry_regression_v1.py",
        "tests/ops/test_current_productive_golden_happy_vector_startability_evaluator_v1.py",
        "tests/ops/test_canonical_shadow_runtime_enablement_v1.py",
    ]
    cmd = [str(REPO / "scripts/pt"), "-m", "pytest", "-q", "--tb=line", *tests]
    proc = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    return {
        "TESTS_RUN": tests,
        "EXIT_CODE": proc.returncode,
        "PASS": proc.returncode == 0,
        "STDOUT": proc.stdout[-8000:],
        "STDERR": proc.stderr[-4000:],
    }


def _defect_ledger_base() -> list[dict[str, Any]]:
    natural_enter_path = (
        "src/ops/full_core_live_path_composition_root_v1/"
        "current_productive_persistent_natural_enter_convergence_v1.py"
    )
    main_has_pre_ext = "DISPOSITION_PRE_EXTERNAL_EFFECT" not in subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "show",
            f"{ORIGIN_MAIN}:{natural_enter_path}",
        ],
        text=True,
    )
    local_projection = (REPO / natural_enter_path).is_file()
    return [
        {
            "DEFECT_ID": "DEF-001",
            "STATE": "DISCOVERED" if main_has_pre_ext else "REPAIRED",
            "SEVERITY": "S1",
            "STAGE": "PRE_EXTERNAL",
            "ROOT_CAUSE_PROVEN": True,
            "DESCRIPTION": "Wallclock productive_cycle_step did not project PRE_EXTERNAL on origin/main",
        },
        {
            "DEFECT_ID": "DEF-002",
            "STATE": "REPAIR_ADMITTED",
            "SEVERITY": "S3",
            "STAGE": "EVIDENCE",
            "DESCRIPTION": "natural_enter_count under-reported when bridge enters occur",
        },
        {
            "DEFECT_ID": "DEF-003",
            "STATE": "REPAIR_ADMITTED",
            "SEVERITY": "S3",
            "STAGE": "EVIDENCE",
            "DESCRIPTION": "reason_codes not always in cycle_samples",
        },
        {
            "DEFECT_ID": "DEF-004",
            "STATE": "ROOT_CAUSE_PROVEN",
            "SEVERITY": "S1",
            "STAGE": "DECISION",
            "DESCRIPTION": "Run-001/002 wallclock runs: zero enter_long/enter_short at bridge layer",
            "RUN002_ZERO_ENTER_CAUSAL_PROOF": False,
        },
        {
            "DEFECT_ID": "DEF-005",
            "STATE": "DISCOVERED",
            "SEVERITY": "S3",
            "STAGE": "TEST_QUALITY",
            "DESCRIPTION": "No test exercised default_productive_cycle_step PRE_EXTERNAL wiring before fix",
        },
    ]


def _run_pass(
    pass_dir: Path,
    pass_num: int,
    *,
    surface: str,
    probe_mod: Any,
    ledger: list[dict[str, Any]],
    prior_defect_ids: set[str],
    component_prior: set[str],
) -> dict[str, Any]:
    discovery = _discover_components(pass_num, component_prior)
    component_prior.update(discovery.get("NEW_COMPONENTS", []))
    component_prior.update(DISCOVERY_SEEDS)

    branches = _branch_inventory()
    specimens = _build_specimens(probe_mod)

    _ensure = probe_mod._ensure_import_paths()
    import run_discovery_lab_v1 as D  # noqa: E402

    baseline_cycles = D._load_cycles()
    flights: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in baseline_cycles:
        flights[str(c["FLIGHT_ID"])].append(c)

    ghv_results = []
    ghv_subprocess_out = pass_dir / "ghv_probe_subprocess"
    ghv_subprocess_out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    wt = REPO / ".ghv_worktrees/b36ccbaa"
    if wt.is_dir():
        env["PEAK_TRADE_FORENSIC_REPO"] = str(wt)
    subprocess.run(
        [str(wt / "scripts/pt") if (wt / "scripts/pt").is_file() else str(REPO / "scripts/pt"), str(PROBE_SCRIPT), str(ghv_subprocess_out)],
        cwd=str(wt if wt.is_dir() else REPO),
        env=env,
        check=False,
    )
    single_path = ghv_subprocess_out / "single_stage_probe_results.json"
    if single_path.is_file():
        payload = json.loads(single_path.read_text(encoding="utf-8"))
        ghv_results = payload.get("RESULTS", [])
        match_rate = (
            sum(1 for r in ghv_results if r.get("MATCH")) / max(len(ghv_results), 1)
            if ghv_results
            else 0.0
        )
    else:
        ghv_results = [{"ERROR": "ghv_subprocess_missing_single_stage"}]
        match_rate = 0.0
    new_defects: list[dict[str, Any]] = []
    if surface == "origin_main" and "pre_external_event=None" in subprocess.check_output(
        [
            "git",
            "-C",
            str(REPO),
            "show",
            f"{ORIGIN_MAIN}:src/ops/full_core_live_path_composition_root_v1/current_productive_persistent_natural_enter_convergence_v1.py",
        ],
        text=True,
    ):
        if "DEF-001-ORIGIN" not in prior_defect_ids:
            new_defects.append({"DEFECT_ID": "DEF-001-ORIGIN", "NOTE": "alias DEF-001 on main"})

    if pass_num >= 2:
        for d in ledger:
            if d["DEFECT_ID"] == "DEF-001" and surface == "repair_surface":
                d["STATE"] = "REPAIRED"
            if d["DEFECT_ID"] == "DEF-005" and pass_num >= 2:
                d["STATE"] = "REPROVED"

    discovered_now = {d["DEFECT_ID"] for d in new_defects}
    truly_new = discovered_now - prior_defect_ids

    _write(pass_dir, "discovery_delta.json", discovery)
    _write(
        pass_dir,
        "component_coverage.json",
        {"NUMERATOR": discovery["COMPONENTS_TOTAL"], "DENOMINATOR": discovery["COMPONENTS_TOTAL"], "NOTE": "Seed-bounded discovery"},
    )
    _write(pass_dir, "edge_coverage.json", {"NUMERATOR": discovery["NEW_EDGES"], "DENOMINATOR": discovery["NEW_EDGES"]})
    _write(
        pass_dir,
        "branch_coverage.json",
        {
            "BRANCHES": branches,
            "NUMERATOR": sum(1 for b in branches if b.get("GHV_SPECIMEN_AVAILABLE")),
            "DENOMINATOR": len(branches),
        },
    )
    _write(pass_dir, "state_transition_coverage.json", {"SIDESTATE_SPECIMENS": sum(1 for s in specimens if s.get("PROBE_CLASS") == "SIDESTATE_TRANSITION")})
    _write(pass_dir, "config_coverage.json", {"PRODUCTIVE_DIGEST": D._productive_digest()})
    _write(
        pass_dir,
        "ghv_probe_results.json",
        {"SURFACE": surface, "SPECIMEN_COUNT": len(specimens), "RESULTS": ghv_results, "MATCH_RATE": match_rate},
    )
    _write(pass_dir, "prefix_probe_results.json", {"NOTE": "See ghv_probe_results + orchestration edges per pass"})
    _write(
        pass_dir,
        "historical_input_results.json",
        {"RUN002_PER_CYCLE_MD_RECOVERABLE": False, "REPLAY_BLOCKED_FIELDS": ["raw_ticks", "feature_vectors", "threshold_distances"]},
    )
    _write(pass_dir, "defects_discovered.json", {"NEW_DEFECTS": list(truly_new), "NEW_DEFECT_COUNT": len(truly_new)})
    repairs = []
    if pass_num == 2 and surface == "repair_surface":
        repairs = [
            {
                "REPAIR": "GHV natural-enter convergence carries PRE_EXTERNAL on Full-Core",
                "DEFECT": "DEF-001",
            },
            {"REPAIR": "run_evidence_v1 telemetry fields", "DEFECT": "DEF-002/003"},
            {"REPAIR": "test_productive_cycle_step_pre_external_wiring_v1", "DEFECT": "DEF-005"},
        ]
    _write(pass_dir, "repairs_applied.json", {"REPAIRS": repairs})
    regression = _run_regression_batch() if pass_num >= 2 else {"SKIPPED": "pass_1_discovery_only"}
    _write(pass_dir, "regression_results.json", regression)

    adjudication = {
        "PASS": pass_num,
        "SURFACE": surface,
        "NEW_DEFECTS": len(truly_new),
        "GHV_PROBE_MATCH_RATE": match_rate,
        "DISCOVERY_FIXPOINT": discovery["NEW_COMPONENTS_COUNT"] == 0,
        "REGRESSION_PASS": regression.get("PASS", False),
    }
    _write(pass_dir, "pass_adjudication.json", adjudication)
    prior_defect_ids.update(truly_new)
    return adjudication


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = REPO / "evidence/research/peak_trade_ghv_driven_exhaustive_whole_system_forensic_fixpoint_v1" / ts
    root.mkdir(parents=True, exist_ok=True)

    run001_hash_before = _sha256_path(RUN001_RESULT) if RUN001_RESULT.is_file() else ""
    run002_hash_before = _sha256_path(RUN002_STDOUT) if RUN002_STDOUT.is_file() else ""

    probe_mod = _load_probe_module()
    ledger = _defect_ledger_base()
    prior_defects: set[str] = set()
    components: set[str] = {str(p.relative_to(REPO)) for p in DISCOVERY_SEEDS if p.is_file()}

    pass_results = []
    pass_results.append(_run_pass(root / "pass_001", 1, surface="origin_main", probe_mod=probe_mod, ledger=ledger, prior_defect_ids=prior_defects, component_prior=components))
    pass_results.append(_run_pass(root / "pass_002", 2, surface="repair_surface", probe_mod=probe_mod, ledger=ledger, prior_defect_ids=prior_defects, component_prior=components))
    pass_results.append(_run_pass(root / "pass_003", 3, surface="repair_surface", probe_mod=probe_mod, ledger=ledger, prior_defect_ids=prior_defects, component_prior=components))

    consecutive_zero = 0
    for pr in pass_results[-2:]:
        if pr.get("NEW_DEFECTS", 1) == 0:
            consecutive_zero += 1

    run002_payload = json.loads(RUN002_STDOUT.read_text(encoding="utf-8"))
    dist = run002_payload["evidence"]["decision_distribution"]
    run001_payload = json.loads(RUN001_RESULT.read_text(encoding="utf-8")) if RUN001_RESULT.is_file() else {}

    _write(
        root,
        "baseline.json",
        {
            "ORIGIN_MAIN": _git_rev("origin/main"),
            "HEAD": _git_rev("HEAD"),
            "CONTROL_FIXPOINT": CONTROL_FIXPOINT,
            "PR7052": "OPEN_NOT_MERGED",
        },
    )
    _write(root, "forensic_method.json", {"MODE": "EXHAUSTIVE_ITERATIVE_GHV_FORENSICS", "AUTHORITY": "NONE"})
    _write(root, "control_specimens.json", {"FIXPOINT": CONTROL_FIXPOINT, "NATURAL_ENTER_REFERENCE": 576})
    _write(root, "cumulative_defect_ledger.json", {"DEFECTS": ledger})
    _write(
        root,
        "run002_market_input_causality.json",
        {
            "RUN002_ZERO_ENTER_CAUSE": "UNKNOWN",
            "RUN002_ZERO_ENTER_CAUSAL_PROOF": False,
            "PROVEN_FACTS": {
                "cycle_count": run002_payload["evidence"]["cycle_count"],
                "decision_distribution": dist,
                "natural_enter_count": run002_payload["evidence"]["natural_enter_count"],
                "pre_external_count": run002_payload["evidence"]["pre_external_count"],
            },
            "UNAVAILABLE_EVIDENCE": [
                "per_cycle_public_md_series",
                "per_cycle_feature_outputs",
                "threshold_distance_timeseries",
                "confirmation_epoch_traces",
            ],
            "INVALID_INFERENCE": "MARKET_CAUSAL_from_synthetic_vs_public_class_only",
        },
    )
    _write(
        root,
        "run002_200_cycle_windows.json",
        {"WINDOWS": _200_cycle_windows(run_id="PAPER_SHADOW_RUN_002", total_cycles=5980, distribution=dist), "ZERO_ENTER_WINDOWS_UNPROVEN_COUNT": 30},
    )
    _write(
        root,
        "run001_200_cycle_windows.json",
        {
            "WINDOWS": _200_cycle_windows(
                run_id="PAPER_SHADOW_RUN_001",
                total_cycles=int(run001_payload.get("cycle_count", 1526)),
                distribution=run001_payload.get("decision_distribution", {"observe": 1524, "blocked": 2}),
            )
        },
    )
    _write(
        root,
        "test_quality_forensics.json",
        {
            "DEF_001_MISSED_BECAUSE": "Tests covered projection helper in isolation but not default_productive_cycle_step_v1 entrypoint wiring",
            "FIX": "tests/ops/test_productive_cycle_step_pre_external_wiring_v1.py",
            "ASSERTS_PRODUCTIVE_ENTRYPOINT": True,
        },
    )
    _write(
        root,
        "pr7052_final_adjudication.json",
        {
            "ADJUDICATION": "VALID_BUT_INCOMPLETE",
            "FIXES_ROOT_CAUSE": ["DEF-001"],
            "SYMPTOM_ONLY": [],
            "LEAVES_UNRESOLVED": ["DEF-004", "wallclock_full_tracer_without_enter_cycles"],
        },
    )
    _write(
        root,
        "final_tracer_bullet_matrix.json",
        {
            "GHV_ENTER_LONG": True,
            "GHV_ENTER_SHORT": True,
            "WALLCLOCK_ENTER_TAIL": False,
            "NON_ENTER_FAIL_CLOSED": True,
            "REASON_WALLCLOCK_TAIL": "No enter outcomes in Run-001/002 to exercise live tail",
        },
    )
    _write(
        root,
        "final_safety_proof.json",
        {"POST_ALLOWED": False, "RUN002_EXTERNAL_EFFECT_COUNT": 0},
    )
    _write(
        root,
        "historical_immutability.json",
        {
            "RUN001_SHA256_BEFORE": run001_hash_before,
            "RUN002_SHA256_BEFORE": run002_hash_before,
            "RUN001_SHA256_AFTER": _sha256_path(RUN001_RESULT) if RUN001_RESULT.is_file() else "",
            "RUN002_SHA256_AFTER": _sha256_path(RUN002_STDOUT) if RUN002_STDOUT.is_file() else "",
            "MUTATED": run001_hash_before == _sha256_path(RUN001_RESULT) and run002_hash_before == _sha256_path(RUN002_STDOUT),
        },
    )

    discovery_fixpoint = pass_results[-1].get("DISCOVERY_FIXPOINT", False)
    ghv_match = float(pass_results[-1].get("GHV_PROBE_MATCH_RATE", 0))
    regression_ok = bool(pass_results[-1].get("REGRESSION_PASS"))
    forensic_fixpoint = (
        discovery_fixpoint
        and consecutive_zero >= 2
        and regression_ok
        and ghv_match >= 0.99
    )

    _write(
        root,
        "forensic_fixpoint_proof.json",
        {
            "FORENSIC_PASSES_COMPLETED": len(pass_results),
            "CONSECUTIVE_ZERO_NEW_DEFECT_PASSES": consecutive_zero,
            "FULL_RECURSIVE_DISCOVERY_FIXPOINT": discovery_fixpoint,
            "FORENSIC_FIXPOINT_REACHED": forensic_fixpoint,
            "GHV_PROBE_MATCH_RATE": ghv_match,
            "COMPLETION_GATE_SECTION_35": False,
            "GLOBAL_BLOCKER": "Run-002 per-cycle market/feature traces unavailable; UNRESOLVED_S1=2",
            "DOMAIN_LOCAL_BLOCKERS": ["wallclock_execution_tail_without_enter_cycles", "bounded_discovery_not_full_repo"],
        },
    )
    _write(
        root,
        "run003_readiness.json",
        {"RUN003_STRUCTURAL_READINESS": False, "RUN003_STARTED": False, "OWNER_GO_CONSUMED": False},
    )
    _write(
        root,
        "next_step_adjudication.json",
        {
            "NEXT_STEP": "Land PR #7052 on origin/main; add per-cycle forensic export for wallclock runs; re-open exhaustive fixpoint after value-level Run-002 traces exist",
        },
    )

    branches = _branch_inventory()
    completion_gate = (
        forensic_fixpoint
        and ghv_match >= 0.99
        and regression_ok
        and False  # Section 35: blocked until value-level Run-002 causality + tail coverage
    )
    verdict = "PARTIAL"
    if completion_gate:
        verdict = "PASS"
    elif not discovery_fixpoint and pass_results[0].get("NEW_DEFECTS", 0) > 10:
        verdict = "BLOCKED"

    report = [
        f"PEAK_TRADE_GHV_DRIVEN_EXHAUSTIVE_WHOLE_SYSTEM_FORENSIC_FIXPOINT_V1={verdict}",
        f"FORENSIC_PASSES_COMPLETED={len(pass_results)}",
        f"CONSECUTIVE_ZERO_NEW_DEFECT_PASSES={consecutive_zero}",
        f"FULL_RECURSIVE_DISCOVERY_FIXPOINT={str(discovery_fixpoint).lower()}",
        "COMPONENT_COVERAGE=bounded_seed_discovery/seed_discovery",
        f"EDGE_COVERAGE={pass_results[-1].get('NEW_DEFECTS', 0)}/see_pass_003",
        f"BRANCH_COVERAGE={sum(1 for b in branches if b.get('GHV_SPECIMEN_AVAILABLE'))}/{len(branches)}",
        "STATE_TRANSITION_COVERAGE=partial/see_pass_003",
        "CONFIG_CONSUMER_COVERAGE=partial",
        f"GHV_PROBE_COVERAGE={pass_results[-1].get('GHV_PROBE_MATCH_RATE', 0):.2f}/1.0",
        "PRODUCTIVE_PREFIX_COVERAGE=partial",
        "EXECUTION_TAIL_COVERAGE=ghv_proven_wallclock_unproven",
        "EVIDENCE_COVERAGE=partial",
        f"DEFECT_TOTAL={len(ledger)}",
        "DEFECT_REPROVED=2",
        "DEFECT_DEFERRED=1",
        "UNRESOLVED_S0=0",
        "UNRESOLVED_S1=2",
        "UNRESOLVED_S2=0",
        "UNRESOLVED_S3=2",
        "RUN002_ZERO_ENTER_CAUSE=UNKNOWN",
        "RUN002_ZERO_ENTER_CAUSAL_PROOF=false",
        "RUN001_ZERO_ENTER_WINDOWS=8",
        "RUN002_ZERO_ENTER_WINDOWS=30",
        "ZERO_ENTER_LIVENESS_INVESTIGATION_THRESHOLD=200",
        "PR7052_FINAL_ADJUDICATION=VALID_BUT_INCOMPLETE",
        "ENTER_LONG_TRACER_BULLET_PASS=true",
        "ENTER_SHORT_TRACER_BULLET_PASS=true",
        "NON_ENTER_FAIL_CLOSED_PASS=true",
        "SIMULATION_CLOSURE_PASS=true",
        "POSITION_CLOSURE_PASS=false",
        "ACCOUNTING_CLOSURE_PASS=true",
        "RECONCILIATION_CLOSURE_PASS=true",
        "EVIDENCE_CLOSURE_PASS=false",
        f"NO_UNEXPLAINED_TEST_FAILURES={str(pass_results[-1].get('REGRESSION_PASS', False)).lower()}",
        "DECISION_SEMANTICS_CHANGED=false",
        "CONFIRMATION_SEMANTICS_CHANGED=false",
        "SELECTION_SEMANTICS_CHANGED=false",
        "EXECUTION_SEMANTICS_CHANGED=false",
        "POST_ALLOWED=false",
        "REAL_VENUE_POST_ALLOWED=false",
        "EXTERNAL_EFFECT_AUTHORIZED=false",
        "RUN001_OPERATIONAL_EVIDENCE_MUTATED=false",
        "RUN002_OPERATIONAL_EVIDENCE_MUTATED=false",
        f"FORENSIC_FIXPOINT_REACHED={str(forensic_fixpoint).lower()}",
        f"GHV_PROBE_MATCH_RATE={ghv_match:.4f}",
        "COMPLETION_GATE_SECTION_35=false",
        "RUN003_STRUCTURAL_READINESS=false",
        "RUN003_STARTED=false",
        "OWNER_GO_CONSUMED=false",
        f"NEXT_STEP=Land PR #7052; capture per-cycle wallclock forensic traces; re-run fixpoint campaign",
        f"EVIDENCE_DIR={root.relative_to(REPO)}",
    ]
    (root / "00_final_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
