from __future__ import annotations

import argparse
import json
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_inventory_v0 import SURFACES

INVENTORY_SCRIPT = Path("scripts/research/backtest_runtime_decision_parity_inventory_v0.py")

TRACE_PRIORITY = [
    "bull_bear_state_switch",
    "scope_adverse_exit_and_reversal_preparation",
    "flat_before_opposite_side",
    "entry_position_exit_policy",
    "capital_risk_sizing",
    "safety_kernel_and_killswitch_boundary",
    "reconciliation_unknown_outcome",
    "promotion_gate_boundary",
    "ai_observability_feedback_boundary",
    "double_play_composition",
    "survival_and_suitability",
    "canonical_order_intent_boundary",
]

NO_AUTHORITY_FLAGS = {
    "runtime_authority": False,
    "orders_allowed": False,
    "economic_claim": False,
    "full_canonical_chain_wired_claimed": False,
    "backtest_runtime_decision_parity_pass_claimed": False,
    "system_economic_evidence_admissible": False,
}

REWIRE_SELECTION_RULE = (
    "Select the earliest high-priority surface where canonical, backtest, and runtime-boundary candidates exist, "
    "then plan a narrow trace assertion before any functional rewire. The plan may not claim parity pass."
)


@dataclass(frozen=True)
class TraceEdge:
    surface_id: str
    canonical_candidate: str
    backtest_candidate: str
    runtime_boundary_candidate: str
    required_status: str
    trace_state: str
    next_action: str


@dataclass(frozen=True)
class RewirePlan:
    selected_surface_id: str
    plan_type: str
    rationale: str
    allowed_change: str
    forbidden_claims: list[str]
    required_tests: list[str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_path(surface: dict[str, Any], key: str) -> str:
    hits = surface.get(key, [])
    if not hits:
        return "NONE_DISCOVERED"
    return hits[0]["path"]


def _is_rewire_bound_surface(surface: dict[str, Any]) -> bool:
    configured = next(
        (item for item in SURFACES if item["surface_id"] == surface["surface_id"]),
        None,
    )
    if configured is None or not configured.get("trace_rewire_bound"):
        return False
    backtest_hits = surface.get("backtest_binding_candidates", [])
    if not backtest_hits:
        return False
    first = backtest_hits[0]
    return first.get("matched_terms") == ["rewire_binding_pin"]


def _load_inventory_from_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["schema"] != "BacktestRuntimeDecisionParityInventoryV1":
        raise ValueError(f"unexpected inventory schema: {data.get('schema')}")
    for key, expected in NO_AUTHORITY_FLAGS.items():
        if data.get(key) is not expected:
            raise ValueError(f"inventory violates {key}={expected}")
    if data.get("inventory_surface_count") != 12:
        raise ValueError("inventory must contain exactly 12 surfaces")
    return data


def build_trace_matrix(inventory: dict[str, Any]) -> dict[str, Any]:
    by_surface = {surface["surface_id"]: surface for surface in inventory["surfaces"]}
    edges: list[TraceEdge] = []
    for surface_id in TRACE_PRIORITY:
        surface = by_surface[surface_id]
        canonical = _first_path(surface, "canonical_owner_candidates")
        backtest = _first_path(surface, "backtest_binding_candidates")
        runtime = _first_path(surface, "runtime_boundary_candidates")
        if _is_rewire_bound_surface(surface):
            trace_state = "TRACE_REWIRE_BOUND_OFFLINE_PARITY_PATH"
            next_action = "rewire_complete_advance_to_next_surface"
        elif "NONE_DISCOVERED" in {canonical, backtest, runtime}:
            trace_state = "TRACE_INCOMPLETE"
            next_action = "owner_discovery_before_rewire"
        else:
            trace_state = "TRACE_CANDIDATE_READY_NOT_ASSERTED"
            next_action = "add_narrow_trace_assertion_before_rewire"
        edges.append(
            TraceEdge(
                surface_id=surface_id,
                canonical_candidate=canonical,
                backtest_candidate=backtest,
                runtime_boundary_candidate=runtime,
                required_status=surface["required_status"],
                trace_state=trace_state,
                next_action=next_action,
            )
        )
    selected = next(
        edge for edge in edges if edge.trace_state == "TRACE_CANDIDATE_READY_NOT_ASSERTED"
    )
    plan_type = "NARROW_TRACE_ASSERTION_FIRST"
    plan = RewirePlan(
        selected_surface_id=selected.surface_id,
        plan_type=plan_type,
        rationale=(
            "Inventory found candidates on all three surfaces. The next safe move is not a new status contract; "
            "it is an executable trace assertion proving whether the selected canonical owner is actually consumed "
            "by the backtest path and represented at the runtime boundary."
        ),
        allowed_change=(
            "Add tests and read-only trace extraction around existing owners. Only rewire if the trace assertion "
            "exposes a concrete missing edge."
        ),
        forbidden_claims=[
            "FULL_CANONICAL_CHAIN_WIRED=true",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
            "RUNTIME_REWIRE_ADMISSIBLE=true",
            "ORDERS_ALLOWED=true",
            "LIVE_AUTHORIZED=true",
        ],
        required_tests=[
            "trace matrix schema and 12-surface coverage",
            "selected surface has canonical/backtest/runtime-boundary candidates",
            "no authority/economic/parity-pass claims",
            "source inventory manifest is referenced externally in evidence",
        ],
    )
    return {
        "schema": "BacktestRuntimeDecisionParityTraceMatrixV1",
        "source_inventory_schema": inventory["schema"],
        "source_inventory_surface_count": inventory["inventory_surface_count"],
        "trace_edge_count": len(edges),
        "trace_edges": [asdict(edge) for edge in edges],
        "selected_next_rewire_plan": asdict(plan),
        "selection_rule": REWIRE_SELECTION_RULE,
        "runtime_authority": False,
        "orders_allowed": False,
        "economic_claim": False,
        "full_canonical_chain_wired_claimed": False,
        "backtest_runtime_decision_parity_pass_claimed": False,
        "system_economic_evidence_admissible": False,
    }


def render_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Backtest Runtime Decision Parity Trace Matrix V1",
        "",
        "```text",
        "REUSE_FIRST=true",
        "TRACE_ASSERTION_FIRST=true",
        "NO_STATUS_ONLY_PR=true",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDERS=true",
        "NO_ECONOMIC_CLAIM=true",
        "FULL_CANONICAL_CHAIN_WIRED_CLAIMED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS_CLAIMED=false",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "```",
        "",
        "## Selected next narrow plan",
        "",
    ]
    plan = matrix["selected_next_rewire_plan"]
    lines.extend(
        [
            f"- selected_surface_id: `{plan['selected_surface_id']}`",
            f"- plan_type: `{plan['plan_type']}`",
            f"- rationale: {plan['rationale']}",
            f"- allowed_change: {plan['allowed_change']}",
            "",
            "## Trace edges",
            "",
        ]
    )
    for edge in matrix["trace_edges"]:
        lines.extend(
            [
                f"### {edge['surface_id']}",
                f"- required_status: `{edge['required_status']}`",
                f"- trace_state: `{edge['trace_state']}`",
                f"- next_action: `{edge['next_action']}`",
                f"- canonical_candidate: `{edge['canonical_candidate']}`",
                f"- backtest_candidate: `{edge['backtest_candidate']}`",
                f"- runtime_boundary_candidate: `{edge['runtime_boundary_candidate']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_manifest(output_dir: Path) -> int:
    rows: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256(path)}  {path.relative_to(output_dir).as_posix()}")
    (output_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")
    for row in rows:
        digest, rel = row.split("  ", 1)
        if _sha256(output_dir / rel) != digest:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    inventory = _load_inventory_from_file(Path(args.inventory_json))
    matrix = build_trace_matrix(inventory)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "backtest_runtime_decision_parity_trace_matrix_v0.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "backtest_runtime_decision_parity_trace_matrix_v0.md").write_text(
        render_markdown(matrix) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_TRACE_MATRIX_READY_REWIRE_PLAN_SELECTED"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"SELECTED_SURFACE={matrix['selected_next_rewire_plan']['selected_surface_id']}")
    print(f"TRACE_EDGE_COUNT={matrix['trace_edge_count']}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
