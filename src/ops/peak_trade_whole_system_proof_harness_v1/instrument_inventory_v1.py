"""Catalog of existing Peak_Trade proof / forensic instrumentation (Phase 1)."""

from __future__ import annotations

from typing import Any

# Machine-readable inventory derived from repository inspection at BASELINE_SHA.
EXISTING_INSTRUMENT_INVENTORY: list[dict[str, Any]] = [
    {
        "INSTRUMENT_ID": "INV_V2_FRESH_DISCOVERY",
        "PATH": "scripts/ops/peak_trade_v2_fresh_discovery_v1.py",
        "TYPE": "static_discovery_orchestrator",
        "PURPOSE": "Deterministic multi-root reachability, node/edge universe, authority matrix hashes",
        "INPUTS": ["repo Path", "optional PEAK_TRADE_FORENSIC_SURFACE_CANDIDATES_JSON"],
        "OUTPUTS": ["node_rows", "edge_rows", "flows", "hashes", "union_reach"],
        "STATIC_OR_DYNAMIC": "STATIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": True,
        "MACHINE_READABLE": True,
        "NODE_LEVEL_CAPABILITY": "FULL",
        "EDGE_LEVEL_CAPABILITY": "PARTIAL",
        "GHV_CAPABILITY": "NONE",
        "FIXPOINT_CAPABILITY": "PARTIAL",
        "KNOWN_LIMITATIONS": "Repository-wide union; not operation-scoped semantic graph alone",
    },
    {
        "INSTRUMENT_ID": "INV_FORENSIC_CLOSURE_LOGIC",
        "PATH": "scripts/ops/peak_trade_forensic_closure_logic_v1.py",
        "TYPE": "static_graph_logic",
        "PURPOSE": "Import index, semantic edges, cross-flow reconstruction",
        "INPUTS": ["repo", "py_paths"],
        "OUTPUTS": ["importers", "out_edges", "flows"],
        "STATIC_OR_DYNAMIC": "STATIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": True,
        "MACHINE_READABLE": True,
        "NODE_LEVEL_CAPABILITY": "PARTIAL",
        "EDGE_LEVEL_CAPABILITY": "FULL",
        "KNOWN_LIMITATIONS": "Import/call static only",
    },
    {
        "INSTRUMENT_ID": "INV_CANONICAL_ENTRYPOINT_V2",
        "PATH": "scripts/ops/peak_trade_canonical_entrypoint_discovery_v2.py",
        "TYPE": "entrypoint_scanner",
        "PURPOSE": "Structural root predicate for scripts/src entrypoints",
        "STATIC_OR_DYNAMIC": "STATIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": True,
        "MACHINE_READABLE": True,
        "NODE_LEVEL_CAPABILITY": "PARTIAL",
        "EDGE_LEVEL_CAPABILITY": "NONE",
    },
    {
        "INSTRUMENT_ID": "INV_RECARTography_CONT",
        "PATH": "scripts/ops/run_current_full_repository_recartography_and_whole_system_fixpoint_continuation_v1.py",
        "TYPE": "filesystem_ast_union_builder",
        "PURPOSE": "Filesystem census, AST edges, historical seed reconciliation",
        "STATIC_OR_DYNAMIC": "STATIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": True,
        "MACHINE_READABLE": True,
        "FIXPOINT_CAPABILITY": "PARTIAL",
    },
    {
        "INSTRUMENT_ID": "INV_WHOLE_SYSTEM_CONNECTION_CLOSURE",
        "PATH": "src/ops/whole_system_connection_closure_bounded_wp_v1/proof_v1.py",
        "TYPE": "static_productive_wiring_proof",
        "PURPOSE": "Productive cycle caller census + authority constant guards",
        "STATIC_OR_DYNAMIC": "STATIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": True,
        "MACHINE_READABLE": True,
        "AUTHORITY_CAPABILITY": "PARTIAL",
        "SAFETY_CAPABILITY": "PARTIAL",
        "KNOWN_LIMITATIONS": "Decision→PRE_EXTERNAL wiring slice; not full operation graph",
    },
    {
        "INSTRUMENT_ID": "INV_GHV_SYSTEM_WIDE_CANARY",
        "PATH": "src/ops/full_core_live_path_composition_root_v1/ghv_system_wide_canary_surface_discovery_v1.py",
        "TYPE": "runtime_observability",
        "PURPOSE": "Observed runtime graph, canary events, modeled vs observed reconciliation",
        "STATIC_OR_DYNAMIC": "DYNAMIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "DETERMINISTIC": "bounded",
        "MACHINE_READABLE": True,
        "NODE_LEVEL_CAPABILITY": "PARTIAL",
        "EDGE_LEVEL_CAPABILITY": "PARTIAL",
        "GHV_CAPABILITY": "PARTIAL",
        "KNOWN_LIMITATIONS": "Requires explicit session bind; optional flag on convergence path",
    },
    {
        "INSTRUMENT_ID": "INV_GHV_PRE_EXTERNAL_OBS",
        "PATH": "src/ops/full_core_live_path_composition_root_v1/ghv_pre_external_whole_cycle_causal_observability_v1.py",
        "TYPE": "runtime_observability",
        "PURPOSE": "Pre-external whole-cycle causal observability artifacts",
        "STATIC_OR_DYNAMIC": "DYNAMIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "GHV_CAPABILITY": "PARTIAL",
    },
    {
        "INSTRUMENT_ID": "INV_GHV_FLIGHT_RECORDER",
        "PATH": "src/ops/full_core_live_path_composition_root_v1/ghv_pre_external_runtime_flight_recorder_v1.py",
        "TYPE": "runtime_trace",
        "PURPOSE": "Flight recorder for pre-external runtime transitions",
        "STATIC_OR_DYNAMIC": "DYNAMIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "RUNTIME_PATH": "PARTIAL",
    },
    {
        "INSTRUMENT_ID": "INV_GHV_FORENSIC_PROBE",
        "PATH": "scripts/ops/run_peak_trade_ghv_driven_whole_system_forensic_probe_v1.py",
        "TYPE": "ghv_campaign_orchestrator",
        "PURPOSE": "GHV-driven forensic probe, differential vs productive main",
        "STATIC_OR_DYNAMIC": "MIXED",
        "READ_ONLY_OR_MUTATING": "MUTATING",
        "DETERMINISTIC": False,
        "UNSAFE_FOR_PRODUCTIVE_MEASUREMENT": True,
        "KNOWN_LIMITATIONS": "Uses fixpoint worktree replay; mutates sys.path/env",
    },
    {
        "INSTRUMENT_ID": "INV_GHV_OFFLINE_TESTS",
        "PATH": "tests/ops/test_ghv_pre_external_offline_convergence_v1.py",
        "TYPE": "ghv_semantic_witness_tests",
        "PURPOSE": "Offline GHV synthetic enter → PRE_EXTERNAL contract convergence",
        "STATIC_OR_DYNAMIC": "DYNAMIC",
        "READ_ONLY_OR_MUTATING": "READ_ONLY",
        "GHV_CAPABILITY": "FULL",
        "KNOWN_LIMITATIONS": "Synthetic enter; not productive Natural Enter path",
    },
    {
        "INSTRUMENT_ID": "INV_GVEf_WHOLE_SYSTEM",
        "PATH": "src/evaluation/golden_vectors/integration/whole_system_v1.py",
        "TYPE": "evaluation_integration",
        "PURPOSE": "GVEf whole-system reproof class integration",
        "GOVERNANCE_CAPABILITY": "PARTIAL",
    },
    {
        "INSTRUMENT_ID": "INV_N1_HARD_FACTS",
        "PATH": "src/ops/n1_whole_system_hard_facts_integration_wp_v1/",
        "TYPE": "chain_harness_library",
        "PURPOSE": "N1 hard-facts integration chains and golden happy path trace harness",
        "PERSISTENCE_CAPABILITY": "PARTIAL",
    },
    {
        "INSTRUMENT_ID": "INV_PAPER_SHADOW_FIXPOINT",
        "PATH": "src/ops/paper_shadow_bounded_orchestrator_v1/fixpoint_self_check_v1.py",
        "TYPE": "baseline_pin_checker",
        "PURPOSE": "Fixpoint SHA/tree self-check for paper shadow runs",
        "PROVENANCE_CAPABILITY": "PARTIAL",
    },
]


def required_proof_capabilities_v1() -> list[dict[str, Any]]:
    caps = []
    for pid, name in [
        ("P01", "REPOSITORY_COMPONENT_DISCOVERY"),
        ("P02", "STATIC_FORWARD_CLOSURE"),
        ("P03", "INDEPENDENT_REVERSE_CLOSURE"),
        ("P04", "DYNAMIC_BINDING_DISCOVERY"),
        ("P05", "RUNTIME_PATH_TRACE"),
        ("P06", "CONFIG_CROSS_REFERENCE"),
        ("P07", "STATE_CROSS_REFERENCE"),
        ("P08", "PERSISTENCE_PROOF"),
        ("P09", "AUTHORITY_CROSS_REFERENCE"),
        ("P10", "SAFETY_CROSS_REFERENCE"),
        ("P11", "GOVERNANCE_PROVENANCE_PROOF"),
        ("P12", "GHV_SEMANTIC_WITNESS"),
        ("P13", "GHV_REAL_PATH_DIFFERENTIAL"),
        ("P14", "NODE_COVERAGE_MATRIX"),
        ("P15", "EDGE_COVERAGE_MATRIX"),
        ("P16", "EXCLUSION_LEDGER"),
        ("P17", "FIXPOINT_ENGINE"),
        ("P18", "SETTING_DEPENDENCY_SOLVER"),
        ("P19", "MINIMAL_SETTING_SOLVER"),
        ("P20", "COUNTERFACTUAL_REPAIR_CLOSURE"),
        ("P21", "PROOF_MANIFEST_BUILDER"),
    ]:
        caps.append(
            {
                "CAPABILITY_ID": pid,
                "NAME": name,
                "REQUIRED_DETERMINISM": True,
                "REQUIRED_PROOF_STRENGTH": "evidence-backed claims only",
                "ALLOWED_SIDE_EFFECTS": ["write evidence under AUTHORITY=NONE"],
                "FORBIDDEN_SIDE_EFFECTS": [
                    "venue POST",
                    "productive semantic mutation",
                    "authority expansion",
                ],
            }
        )
    return caps


def build_instrument_capability_matrix_v1() -> dict[str, Any]:
    """Map instruments to P01-P21 with FULL/PARTIAL/NONE/UNSAFE/UNKNOWN."""
    matrix: dict[str, dict[str, str]] = {}
    p_ids = [f"P{i:02d}" for i in range(1, 22)]

    def set_cell(iid: str, mapping: dict[str, str]) -> None:
        matrix[iid] = {p: mapping.get(p, "NONE") for p in p_ids}

    set_cell(
        "INV_V2_FRESH_DISCOVERY",
        {
            "P01": "FULL",
            "P02": "PARTIAL",
            "P14": "PARTIAL",
            "P15": "PARTIAL",
            "P17": "PARTIAL",
        },
    )
    set_cell(
        "INV_FORENSIC_CLOSURE_LOGIC",
        {"P02": "PARTIAL", "P03": "PARTIAL", "P15": "PARTIAL"},
    )
    set_cell("INV_WHOLE_SYSTEM_CONNECTION_CLOSURE", {"P09": "PARTIAL", "P10": "PARTIAL"})
    set_cell(
        "INV_GHV_SYSTEM_WIDE_CANARY",
        {"P05": "PARTIAL", "P12": "PARTIAL", "P13": "PARTIAL"},
    )
    set_cell(
        "INV_GHV_OFFLINE_TESTS",
        {"P12": "FULL", "P13": "PARTIAL", "P05": "PARTIAL"},
    )
    set_cell(
        "INV_GHV_FORENSIC_PROBE",
        {
            "P12": "PARTIAL",
            "P13": "PARTIAL",
            "P05": "PARTIAL",
            "P17": "PARTIAL",
            "P21": "PARTIAL",
        },
    )
    set_cell("INV_GHV_FORENSIC_PROBE", {"P05": "UNSAFE", "P12": "UNSAFE"})

    full: set[str] = set()
    partial: set[str] = set()
    missing: set[str] = set(p_ids)
    unsafe: set[str] = set()
    for iid, row in matrix.items():
        for p, cls in row.items():
            if cls == "FULL":
                full.add(p)
                missing.discard(p)
            elif cls == "PARTIAL":
                partial.add(p)
                missing.discard(p)
            elif cls == "UNSAFE":
                unsafe.add(p)

    # Harness fills gaps (planned in Phase 4)
    harness_covers = {
        "P02",
        "P03",
        "P04",
        "P06",
        "P07",
        "P08",
        "P11",
        "P14",
        "P15",
        "P16",
        "P17",
        "P18",
        "P19",
        "P20",
        "P21",
    }
    for p in harness_covers:
        partial.add(p)
        missing.discard(p)

    return {
        "MATRIX": matrix,
        "FULLY_COVERED_PROOF_CAPABILITIES": sorted(full),
        "PARTIALLY_COVERED_PROOF_CAPABILITIES": sorted(partial),
        "MISSING_PROOF_CAPABILITIES_BEFORE_HARNESS": sorted(
            missing | {"P05", "P09", "P10", "P12", "P13"}
        ),
        "UNSAFE_EXISTING_CAPABILITIES": sorted(unsafe),
        "HARNESS_COMPOSITION_NOTE": "peak_trade_whole_system_proof_harness_v1 composes non-UNSAFE instruments",
    }


def implementation_plan_v1() -> dict[str, Any]:
    strategies = {}
    for pid in [f"P{i:02d}" for i in range(1, 22)]:
        if pid in ("P01", "P02", "P03"):
            strategies[pid] = "COMPOSE_EXISTING"
        elif pid in ("P09", "P10"):
            strategies[pid] = "COMPOSE_EXISTING"
        elif pid in ("P12", "P13", "P05"):
            strategies[pid] = "COMPOSE_EXISTING"
        elif pid == "P04":
            strategies[pid] = "MINIMALLY_EXTEND_EXISTING"
        else:
            strategies[pid] = "BUILD_MISSING"
    return {
        "STRATEGIES": strategies,
        "PACKAGE": "src/ops/peak_trade_whole_system_proof_harness_v1",
        "ORCHESTRATOR": "scripts/ops/run_peak_trade_whole_system_proof_harness_v1.py",
        "JUSTIFICATION": "No single existing owner aggregates operation-scoped proof manifest with fixpoint and coverage",
    }
