from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from scripts.research.backtest_runtime_decision_parity_trace_matrix_v0 import (
    NO_AUTHORITY_FLAGS,
    build_trace_matrix,
)

SURFACE_ID = "bull_bear_state_switch"
PLAN_TYPE = "NARROW_TRACE_ASSERTION_FIRST"
TRACE_ASSERTION_STATE = "TRACE_ASSERTION_RECORDED_NOT_REWIRED"
FORBIDDEN_RUNTIME_TOKENS = (
    "send_order(",
    "submit_order(",
    "create_order(",
    "cancel_order(",
    "place_order(",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ALLOWED=true",
)


@dataclass(frozen=True)
class TraceAssertionEdge:
    surface_id: str
    canonical_candidate: str
    backtest_candidate: str
    runtime_boundary_candidate: str
    required_status: str
    canonical_trace_markers_found: list[str]
    backtest_trace_markers_found: list[str]
    runtime_boundary_trace_markers_found: list[str]
    trace_assertion_state: str
    functional_rewire_performed: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _edge_for_surface(matrix: dict[str, Any], surface_id: str) -> dict[str, Any]:
    for edge in matrix["trace_edges"]:
        if edge["surface_id"] == surface_id:
            return edge
    raise ValueError(f"surface not found in trace matrix: {surface_id}")


def _markers_in_text(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker in text]


def _assert_read_only_trace(repo_root: Path, edge: dict[str, Any]) -> TraceAssertionEdge:
    canonical_path = repo_root / edge["canonical_candidate"]
    backtest_path = repo_root / edge["backtest_candidate"]
    runtime_path = repo_root / edge["runtime_boundary_candidate"]
    for label, path in (
        ("canonical", canonical_path),
        ("backtest", backtest_path),
        ("runtime_boundary", runtime_path),
    ):
        if not path.is_file():
            raise ValueError(f"{label} candidate missing: {edge[f'{label}_candidate']}")

    canonical_text = canonical_path.read_text(encoding="utf-8")
    backtest_text = backtest_path.read_text(encoding="utf-8")
    runtime_text = runtime_path.read_text(encoding="utf-8")

    canonical_markers = _markers_in_text(
        canonical_text,
        (
            "bull_bear_state_switch_scenario_binding_adapter_v0",
            "evaluate_scenario_state_switch",
            "build_default_bull_bear_bull_scenario_ticks",
        ),
    )
    if not canonical_markers:
        raise ValueError("canonical candidate lacks bull/bear state-switch trace markers")

    backtest_markers = _markers_in_text(
        backtest_text,
        (
            '"surface_id": "bull_bear_state_switch"',
            "BULL_BEAR_STATE_SWITCH_WIRED_TO_BACKTEST",
            "bull",
            "bear",
        ),
    )
    if len(backtest_markers) < 2:
        raise ValueError("backtest candidate lacks bull/bear trace markers")

    runtime_markers = _markers_in_text(
        runtime_text,
        (
            "allow_bull_strategies",
            "allow_bear_strategies",
            "bull",
            "bear",
        ),
    )
    if not runtime_markers:
        raise ValueError("runtime boundary candidate lacks bull/bear boundary markers")

    for token in FORBIDDEN_RUNTIME_TOKENS:
        if token in runtime_text:
            raise ValueError(f"runtime boundary candidate contains forbidden token: {token}")

    return TraceAssertionEdge(
        surface_id=edge["surface_id"],
        canonical_candidate=edge["canonical_candidate"],
        backtest_candidate=edge["backtest_candidate"],
        runtime_boundary_candidate=edge["runtime_boundary_candidate"],
        required_status=edge["required_status"],
        canonical_trace_markers_found=canonical_markers,
        backtest_trace_markers_found=backtest_markers,
        runtime_boundary_trace_markers_found=runtime_markers,
        trace_assertion_state=TRACE_ASSERTION_STATE,
        functional_rewire_performed=False,
    )


def build_narrow_trace_assertion(
    repo_root: Path,
    matrix: dict[str, Any],
) -> dict[str, Any]:
    plan = matrix["selected_next_rewire_plan"]
    if plan["selected_surface_id"] != SURFACE_ID:
        raise ValueError(f"unexpected selected surface: {plan['selected_surface_id']}")
    if plan["plan_type"] != PLAN_TYPE:
        raise ValueError(f"unexpected plan type: {plan['plan_type']}")

    edge = _edge_for_surface(matrix, SURFACE_ID)
    assertion_edge = _assert_read_only_trace(repo_root, edge)

    return {
        "schema": "BullBearStateSwitchNarrowTraceAssertionV1",
        "source_trace_matrix_schema": matrix["schema"],
        "surface_id": SURFACE_ID,
        "plan_type": PLAN_TYPE,
        "trace_assertion_state": TRACE_ASSERTION_STATE,
        "functional_rewire_performed": False,
        "trace_assertion_edge": asdict(assertion_edge),
        "selected_next_rewire_plan": plan,
        "forbidden_claims_remain_false": {
            "FULL_CANONICAL_CHAIN_WIRED": False,
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS": False,
            "RUNTIME_AUTHORITY": False,
            "ORDERS_ALLOWED": False,
            "ECONOMIC_CLAIM": False,
            "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
        },
        **NO_AUTHORITY_FLAGS,
    }


def render_markdown(assertion: dict[str, Any]) -> str:
    edge = assertion["trace_assertion_edge"]
    lines = [
        "# Bull Bear State Switch Narrow Trace Assertion V1",
        "",
        "```text",
        "TRACE_ASSERTION_FIRST=true",
        "FUNCTIONAL_REWIRE_PERFORMED=false",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDERS=true",
        "NO_ECONOMIC_CLAIM=true",
        "FULL_CANONICAL_CHAIN_WIRED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS=false",
        "```",
        "",
        f"- surface_id: `{assertion['surface_id']}`",
        f"- plan_type: `{assertion['plan_type']}`",
        f"- trace_assertion_state: `{assertion['trace_assertion_state']}`",
        f"- canonical_candidate: `{edge['canonical_candidate']}`",
        f"- backtest_candidate: `{edge['backtest_candidate']}`",
        f"- runtime_boundary_candidate: `{edge['runtime_boundary_candidate']}`",
        "",
    ]
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
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--inventory-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    inventory = json.loads(Path(args.inventory_json).read_text(encoding="utf-8"))
    matrix = build_trace_matrix(inventory)
    assertion = build_narrow_trace_assertion(repo_root, matrix)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "bull_bear_state_switch_narrow_trace_assertion_v0.json").write_text(
        json.dumps(assertion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "bull_bear_state_switch_narrow_trace_assertion_v0.md").write_text(
        render_markdown(assertion) + "\n",
        encoding="utf-8",
    )
    verdict = "PASS_BULL_BEAR_STATE_SWITCH_NARROW_TRACE_ASSERTION_RECORDED"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"SURFACE_ID={SURFACE_ID}")
    print(f"PLAN_TYPE={PLAN_TYPE}")
    print(f"FUNCTIONAL_REWIRE_PERFORMED=false")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
