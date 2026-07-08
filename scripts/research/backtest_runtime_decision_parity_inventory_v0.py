from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {".py", ".md", ".toml", ".yaml", ".yml", ".json", ".txt"}
SCAN_ROOTS = (
    "src",
    "scripts",
    "tests",
    "config",
    "docs",
)
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
}
RUNTIME_FORBIDDEN_TOKENS = (
    "send_order(",
    "submit_order(",
    "create_order(",
    "cancel_order(",
    "place_order(",
    "LIVE_AUTHORIZED=true",
    "ORDERS_ALLOWED=true",
    "READY_FOR_OPERATOR_ARMING=true",
)
SURFACES = [
    {
        "surface_id": "bull_bear_state_switch",
        "required_status": "BULL_BEAR_STATE_SWITCH_WIRED_TO_BACKTEST",
        "keywords": ("bull", "bear", "state switch", "long_selected", "short_selected"),
        "canonical_roots": ("src/trading", "src/strategies", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_bull_bear_state_switch_scenario_replay_binding_parity_rewire_contract_v0.py",
            "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
            "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "scope_adverse_exit_and_reversal_preparation",
        "required_status": "ADVERSE_SCOPE_EXIT_WIRED_TO_BACKTEST",
        "keywords": ("scope", "adverse", "reversal", "flat", "opposite"),
        "canonical_roots": ("src/trading", "src/core", "src/strategies"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
            "tests/research/test_adverse_scope_exit_reversal_preparation_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/scope_event_generator_scenario_binding_adapter_v0.py",
            "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "flat_before_opposite_side",
        "required_status": "FLAT_BEFORE_OPPOSITE_SIDE_WIRED_TO_BACKTEST",
        "keywords": ("reconciled", "flat", "opposite", "position", "reverse"),
        "canonical_roots": ("src/trading", "src/execution", "src/live", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
            "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py",
            "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "survival_and_suitability",
        "required_status": "SURVIVAL_SUITABILITY_WIRED_TO_BACKTEST",
        "keywords": ("survival", "suitability", "cost", "regime", "strategy"),
        "canonical_roots": ("src/trading", "src/strategies", "src/experiments", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
            "tests/research/test_survival_suitability_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/survival_suitability_scenario_binding_adapter_v0.py",
            "src/trading/master_v2/survival_assessment_v1.py",
            "src/trading/master_v2/suitability_binding_v1.py",
            "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "double_play_composition",
        "required_status": "DOUBLE_PLAY_COMPOSITION_WIRED_TO_BACKTEST",
        "keywords": ("double play", "double_play", "composition", "both_sides", "chop"),
        "canonical_roots": ("src/trading", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_double_play_composition_scenario_matrix_parity_contract_v0.py",
            "tests/research/test_double_play_composition_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/double_play_composition_scenario_matrix_adapter_v0.py",
            "src/trading/master_v2/double_play_composition_matrix_v1.py",
            "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "entry_position_exit_policy",
        "required_status": "ENTRY_POSITION_EXIT_POLICY_WIRED_TO_BACKTEST",
        "keywords": ("entry", "exit", "hold", "reduce", "position management"),
        "canonical_roots": ("src/trading", "src/strategies", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_scenario_replay_double_play_entry_exit_policy_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
            "tests/research/test_entry_position_exit_policy_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/double_play_entry_exit_scenario_binding_adapter_v0.py",
            "src/trading/master_v2/flat_before_opposite_side_scenario_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "capital_risk_sizing",
        "required_status": "CAPITAL_RISK_SIZING_WIRED_TO_BACKTEST",
        "keywords": ("risk", "sizing", "quantity", "capital", "notional"),
        "canonical_roots": ("src/governance", "src/risk", "src/trading", "src/core", "src/ops"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_capital_risk_sizing_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_capital_risk_sizing_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/research/test_capital_risk_sizing_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/capital_risk_sizing_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/capital_risk_sizing_boundary_backtest_state_file_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "canonical_order_intent_boundary",
        "required_status": "CANONICAL_ORDER_INTENT_BOUNDARY_REPRESENTED",
        "keywords": ("order intent", "intent", "adapter", "permission", "quantity"),
        "canonical_roots": ("src/execution", "src/trading", "src/core"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
    },
    {
        "surface_id": "safety_kernel_and_killswitch_boundary",
        "required_status": "SAFETY_KERNEL_SEMANTICS_WIRED_TO_BACKTEST",
        "keywords": ("safety", "killswitch", "kill switch", "blocked", "authority"),
        "canonical_roots": (
            "src/meta",
            "src/live",
            "src/execution",
            "src/ops",
            "src/risk",
        ),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_safety_kernel_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_killswitch_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/research/test_safety_kernel_killswitch_boundary_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/killswitch_boundary_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py",
            "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "reconciliation_unknown_outcome",
        "required_status": "RECONCILIATION_SEMANTICS_REPRESENTED_IN_BACKTEST",
        "keywords": ("reconciliation", "unknown outcome", "client_order_id", "fills", "position"),
        "canonical_roots": ("src/execution", "src/live", "src/ops"),
        "backtest_roots": ("src/backtest", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_reconciliation_unknown_outcome_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_reconciliation_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/research/test_reconciliation_unknown_outcome_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/reconciliation_unknown_outcome_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "promotion_gate_boundary",
        "required_status": "PROMOTION_GATE_SEMANTICS_BOUND",
        "keywords": ("promotion", "economic", "viability", "eligible", "gate"),
        "canonical_roots": ("src/experiments", "src/core", "src/ops", "scripts"),
        "backtest_roots": ("src/backtest", "src/experiments", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_promotion_gate_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_promotion_gate_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/research/test_promotion_gate_boundary_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/promotion_gate_boundary_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/promotion_gate_boundary_backtest_state_file_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
    {
        "surface_id": "ai_observability_feedback_boundary",
        "required_status": "AI_LAYER_OBSERVABILITY_BOUNDARY_DOCUMENTED",
        "keywords": ("observability", "explain", "feedback", "ai", "decision"),
        "canonical_roots": ("src/webui", "src/experiments", "docs", "src/core"),
        "backtest_roots": ("src/backtest", "src/experiments", "scripts", "tests"),
        "runtime_roots": ("src/live", "src/execution", "src/runtime", "src/ops", "src/webui"),
        "backtest_binding_pins": (
            "tests/trading/master_v2/test_ai_observability_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_ai_observability_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/trading/master_v2/test_feedback_learning_boundary_offline_replay_binding_parity_rewire_contract_v0.py",
            "tests/trading/master_v2/test_feedback_learning_boundary_backtest_state_file_binding_contract_v0.py",
            "tests/research/test_ai_observability_feedback_boundary_narrow_reuse_first_rewire_v0.py",
            "src/trading/master_v2/ai_observability_boundary_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/ai_observability_boundary_backtest_state_file_binding_adapter_v0.py",
            "src/trading/master_v2/feedback_learning_boundary_offline_replay_binding_adapter_v0.py",
            "src/trading/master_v2/feedback_learning_boundary_backtest_state_file_binding_adapter_v0.py",
        ),
        "trace_rewire_bound": True,
    },
]


@dataclass(frozen=True)
class PathHit:
    path: str
    digest: str
    matched_terms: list[str]


@dataclass(frozen=True)
class SurfaceInventory:
    surface_id: str
    required_status: str
    canonical_owner_candidates: list[PathHit]
    backtest_binding_candidates: list[PathHit]
    runtime_boundary_candidates: list[PathHit]
    offline_replay_candidates: list[PathHit]
    gap_classification: str
    reuse_first_rewire_action: str
    rewire_planning_note: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iter_files(repo_root: Path) -> Iterable[Path]:
    for root in SCAN_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            yield path


def in_any_root(rel: str, roots: Iterable[str]) -> bool:
    return any(rel == root or rel.startswith(root.rstrip("/") + "/") for root in roots)


def merge_backtest_binding_pins(
    repo_root: Path,
    backtest_hits: list[PathHit],
    pins: Iterable[str],
) -> list[PathHit]:
    pinned_hits: list[PathHit] = []
    for rel in pins:
        path = repo_root / rel
        if not path.is_file():
            continue
        text = read_text(path)
        pinned_hits.append(
            PathHit(
                path=rel,
                digest=digest_text(text),
                matched_terms=["rewire_binding_pin"],
            )
        )
    seen = {hit.path for hit in pinned_hits}
    return pinned_hits + [hit for hit in backtest_hits if hit.path not in seen]


def collect_hits(
    files: list[Path], repo_root: Path, roots: Iterable[str], keywords: Iterable[str]
) -> list[PathHit]:
    hits: list[PathHit] = []
    lowered_keywords = tuple(term.lower() for term in keywords)
    for path in files:
        rel = path.relative_to(repo_root).as_posix()
        if not in_any_root(rel, roots):
            continue
        text = read_text(path)
        lowered = text.lower()
        matched = sorted({term for term in lowered_keywords if term in lowered})
        if matched:
            hits.append(PathHit(path=rel, digest=digest_text(text), matched_terms=matched))
    return sorted(hits, key=lambda hit: (len(hit.matched_terms), hit.path), reverse=True)[:12]


def classify(
    canonical: list[PathHit], backtest: list[PathHit], runtime: list[PathHit]
) -> tuple[str, str, str]:
    if not canonical:
        return (
            "OWNER_DISCOVERY_REQUIRED",
            "CONSOLIDATE_TO_EXISTING_OWNER",
            "No canonical owner candidate was discovered by the inventory scan; inspect existing SSOTs before creating code.",
        )
    if canonical and not backtest:
        return (
            "CANONICAL_OWNER_FOUND_BACKTEST_BINDING_GAP",
            "REWIRE_EXISTING_COMPONENT",
            "Canonical candidates exist but no backtest binding candidate was found; plan a narrow reuse-first adapter or wiring test.",
        )
    if canonical and backtest and not runtime:
        return (
            "CANONICAL_AND_BACKTEST_FOUND_RUNTIME_BOUNDARY_UNDISCOVERED",
            "DOCUMENT_RUNTIME_BOUNDARY_OR_REWIRE_EXISTING_COMPONENT",
            "Canonical and backtest candidates exist; runtime boundary representation needs explicit trace or boundary documentation.",
        )
    return (
        "PARITY_TRACE_CANDIDATE_FOUND",
        "TRACE_AND_ASSERT_EXISTING_WIRING",
        "Candidates exist across canonical, backtest, and runtime/boundary surfaces; next slice should assert parity, not add a new owner.",
    )


def runtime_authority_scan_text(path: Path, text: str) -> str:
    if path.name != "backtest_runtime_decision_parity_inventory_v0.py":
        return text
    kept_lines: list[str] = []
    in_denylist_literal = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("RUNTIME_FORBIDDEN_TOKENS = ("):
            in_denylist_literal = True
            continue
        if in_denylist_literal:
            if stripped == ")":
                in_denylist_literal = False
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def assert_no_runtime_authority(repo_root: Path, changed_files: Iterable[str]) -> list[str]:
    violations: list[str] = []
    for rel in changed_files:
        path = repo_root / rel
        if not path.exists() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        scan_text = runtime_authority_scan_text(path, read_text(path))
        for token in RUNTIME_FORBIDDEN_TOKENS:
            if token in scan_text:
                violations.append(f"{rel}: forbidden runtime token {token}")
    return violations


def build_inventory(repo_root: Path) -> dict[str, object]:
    files = list(iter_files(repo_root))
    surfaces: list[SurfaceInventory] = []
    for surface in SURFACES:
        canonical_hits = collect_hits(
            files,
            repo_root,
            surface["canonical_roots"],
            surface["keywords"],
        )
        backtest_hits = collect_hits(
            files,
            repo_root,
            surface["backtest_roots"],
            surface["keywords"],
        )
        backtest_hits = merge_backtest_binding_pins(
            repo_root,
            backtest_hits,
            surface.get("backtest_binding_pins", ()),
        )
        runtime_hits = collect_hits(
            files,
            repo_root,
            surface["runtime_roots"],
            surface["keywords"],
        )
        offline_hits = collect_hits(
            files,
            repo_root,
            ("src/trading", "src/experiments", "scripts", "tests"),
            ("offline", "replay", "canonical", "decision"),
        )
        classification, action, note = classify(canonical_hits, backtest_hits, runtime_hits)
        surfaces.append(
            SurfaceInventory(
                surface_id=surface["surface_id"],
                required_status=surface["required_status"],
                canonical_owner_candidates=canonical_hits,
                backtest_binding_candidates=backtest_hits,
                runtime_boundary_candidates=runtime_hits,
                offline_replay_candidates=offline_hits[:8],
                gap_classification=classification,
                reuse_first_rewire_action=action,
                rewire_planning_note=note,
            )
        )
    counts: dict[str, int] = {}
    for item in surfaces:
        counts[item.gap_classification] = counts.get(item.gap_classification, 0) + 1
    return {
        "schema": "BacktestRuntimeDecisionParityInventoryV1",
        "runtime_authority": False,
        "orders_allowed": False,
        "economic_claim": False,
        "system_economic_evidence_admissible": False,
        "full_canonical_chain_wired_claimed": False,
        "backtest_runtime_decision_parity_pass_claimed": False,
        "inventory_surface_count": len(surfaces),
        "gap_classification_counts": counts,
        "surfaces": [asdict(item) for item in surfaces],
        "next_admissible_slice_rule": (
            "Choose the highest-impact CANONICAL_OWNER_FOUND_BACKTEST_BINDING_GAP or "
            "OWNER_DISCOVERY_REQUIRED surface and implement only a narrow owner-bound reuse-first trace/rewire plan."
        ),
    }


def render_markdown(inventory: dict[str, object]) -> str:
    lines = [
        "# Backtest Runtime Decision Parity Inventory V1",
        "",
        "```text",
        "REUSE_FIRST=true",
        "NO_RUNTIME_AUTHORITY=true",
        "NO_ORDERS=true",
        "NO_ECONOMIC_CLAIM=true",
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
        "FULL_CANONICAL_CHAIN_WIRED_CLAIMED=false",
        "BACKTEST_RUNTIME_DECISION_PARITY_PASS_CLAIMED=false",
        "```",
        "",
        "## Classification counts",
        "",
    ]
    counts = inventory["gap_classification_counts"]
    for key in sorted(counts):
        lines.append(f"- {key}: {counts[key]}")
    lines.extend(["", "## Surface inventory", ""])
    for item in inventory["surfaces"]:
        lines.extend(
            [
                f"### {item['surface_id']}",
                "",
                f"- required_status: `{item['required_status']}`",
                f"- gap_classification: `{item['gap_classification']}`",
                f"- reuse_first_rewire_action: `{item['reuse_first_rewire_action']}`",
                f"- note: {item['rewire_planning_note']}",
                f"- canonical_owner_candidates: {len(item['canonical_owner_candidates'])}",
                f"- backtest_binding_candidates: {len(item['backtest_binding_candidates'])}",
                f"- runtime_boundary_candidates: {len(item['runtime_boundary_candidates'])}",
                "",
            ]
        )
        for bucket in (
            "canonical_owner_candidates",
            "backtest_binding_candidates",
            "runtime_boundary_candidates",
        ):
            lines.append(f"#### {bucket}")
            hits = item[bucket]
            if not hits:
                lines.append("- NONE_DISCOVERED")
            for hit in hits[:5]:
                terms = ",".join(hit["matched_terms"])
                lines.append(f"- `{hit['path']}` `{hit['digest'][:12]}` terms={terms}")
            lines.append("")
    return "\n".join(lines) + "\n"


def write_manifest(output_dir: Path) -> int:
    manifest = output_dir / "MANIFEST.sha256"
    rows: list[str] = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            rows.append(f"{digest}  {path.relative_to(output_dir).as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    for row in rows:
        expected, rel = row.split("  ", 1)
        actual = hashlib.sha256((output_dir / rel).read_bytes()).hexdigest()
        if actual != expected:
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(repo_root)
    changed = (
        "scripts/research/backtest_runtime_decision_parity_inventory_v0.py",
        "tests/research/test_backtest_runtime_decision_parity_inventory_v0.py",
    )
    violations = assert_no_runtime_authority(repo_root, changed)
    inventory["runtime_authority_violations"] = violations
    inventory_path = output_dir / "backtest_runtime_decision_parity_inventory_v0.json"
    report_path = output_dir / "backtest_runtime_decision_parity_inventory_v0.md"
    inventory_path.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report_path.write_text(render_markdown(inventory), encoding="utf-8")
    verdict = "PASS" if not violations else "BLOCKED_RUNTIME_AUTHORITY_TOKEN"
    (output_dir / "verdict.txt").write_text(verdict + "\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    (output_dir / "manifest_verify_rc.txt").write_text(f"{manifest_rc}\n", encoding="utf-8")
    manifest_rc = write_manifest(output_dir)
    print(verdict)
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"EVIDENCE_DIR={output_dir}")
    return 0 if verdict == "PASS" and manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
