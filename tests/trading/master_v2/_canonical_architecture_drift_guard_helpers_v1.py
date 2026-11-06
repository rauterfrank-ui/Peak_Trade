"""Shared AST helpers for Canonical Architecture Drift Guard v1.

Reuse-first owner for the three SSOT invariants already achieved by the
canonical chain wiring closeout. Complements (does not replace) the
Slice-1…4 durable static contracts under tests/trading/master_v2/.

This is a light architecture rail — not an architecture freeze.
Runbook-4.4.11 extensions, new strategy implementations, and parameter
changes remain allowed while these three invariants hold.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tests.trading.master_v2.test_canonical_replay_input_builder_ssot_contract_v1 import (
    DirectReplayInputConstructionHit,
    assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor,
    collect_direct_replay_input_constructions,
)
from tests.trading.master_v2.test_strategy_suitability_agreement_static_contract_v1 import (
    TotalDecisionOwnerDefinitionHit,
    assert_exactly_one_canonical_total_decision_owner_definition,
    collect_total_decision_owner_definitions,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = REPO_ROOT / "src"

_TOTAL_DECISION_OWNER_NAME = "run_integrated_offline_trading_logic_replay_v1"
_AUTHORIZED_TOTAL_DECISION_OWNER_REL_PATH = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
)
_PUBLIC_BUILDER_NAME = "build_integrated_offline_replay_input_v1"
_AUTHORIZED_CONSTRUCTOR_REL_PATH = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
)

# Core decision stages composed only by the canonical total decision owner.
_PARTIAL_DECISION_STAGE_CALLS = frozenset(
    {
        "evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1",
        "evaluate_directional_assessment_with_confirmation_progress_v1",
        "evaluate_survival_assessment_v1",
        "evaluate_suitability_binding_v1",
        "evaluate_double_play_composition_matrix_v1",
        "evaluate_double_play_entry_exit_policy_v0",
    }
)
# A competing total orchestrator wires most of the canonical decision chain.
_COMPETING_ORCHESTRATOR_MIN_PARTIAL_STAGES = 4

StrategyBypassKind = Literal["position", "order_intent", "trade", "authoritative_engine"]

_STRATEGY_SOURCE_MARKERS = frozenset(
    {
        "StrategySignalBindingResultV1",
        "execute_configured_strategy_signal_series_v1",
        "ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY",
    }
)
_CANONICAL_OR_LEGACY_GATE_CALLS = frozenset(
    {
        "run_integrated_offline_trading_logic_replay_v1",
        "normalize_strategy_signal_to_suitability_agreement_material_v1",
        "map_decision_evidence_to_position_signal_v1",
        "declare_legacy_raw_signal_research_path_v1",
        "assert_legacy_raw_signal_path_blocks_system_economic_evidence_v1",
        "apply_strategy_suitability_agreement_material_v1",
        "declare_legacy_duplicate_decision_path_v0",
    }
)
_POSITION_KEYWORD_ARGS = frozenset(
    {
        "position_series",
        "positions",
        "position",
        "target_position",
        "position_signal",
    }
)
_ORDER_INTENT_NAMES = frozenset(
    {
        "OrderIntent",
        "OrderIntentV1",
        "CanonicalOrderIntentV1",
        "CanonicalOrderIntentBuildInputV1",
        "submit_order",
        "place_order",
        "create_order_intent",
    }
)
_TRADE_NAMES = frozenset(
    {
        "Trade",
        "emit_trade",
        "create_trade",
        "record_trade",
    }
)

# Productive surfaces that legitimately touch strategy signals without being
# a system-relevant authority bypass of the canonical decision owner.
_STRATEGY_BYPASS_ALLOWLIST_REL_PATHS = frozenset(
    {
        "src/backtest/strategy_signal_binding_v1.py",
        "src/backtest/strategy_signal_suitability_agreement_adapter_v1.py",
        "src/backtest/mv2_research_wiring_v1.py",
        "src/trading/master_v2/strategy_suitability_agreement_material_v1.py",
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
    }
)
_STRATEGY_BYPASS_ALLOWLIST_PREFIXES = (
    "src/strategies/",
    "src/research/",
)
_STRATEGY_BYPASS_ALLOWLIST_NAME_SUBSTRINGS = ("economic_evaluation_admissibility_contract",)


@dataclass(frozen=True, order=True)
class CompetingTotalOrchestratorHit:
    relative_path: str
    lineno: int
    function_name: str
    partial_stages: tuple[str, ...]

    def report_line(self) -> str:
        stages = ",".join(self.partial_stages)
        return (
            f"{self.relative_path}:{self.lineno} in {self.function_name} (partial_stages={stages})"
        )


@dataclass(frozen=True, order=True)
class DirectStrategyAuthorityBypassHit:
    relative_path: str
    lineno: int
    function_name: str
    kind: StrategyBypassKind

    def report_line(self) -> str:
        return f"{self.relative_path}:{self.lineno} in {self.function_name} ({self.kind})"


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _call_names(fn: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                names.add(name)
    return names


def _uses_name_or_attr(fn: ast.AST, names: frozenset[str]) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and node.id in names:
            return True
        if isinstance(node, ast.Attribute) and node.attr in names:
            return True
        if isinstance(node, ast.Call):
            call = _call_name(node.func)
            if call is not None and call in names:
                return True
    return False


def _has_keyword_args(fn: ast.AST, keywords: frozenset[str]) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg in keywords:
                return True
    return False


def _uses_signals_attribute(fn: ast.AST) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute) and node.attr == "signals":
            return True
    return False


def _is_strategy_bypass_allowlisted(rel_path: str) -> bool:
    if rel_path in _STRATEGY_BYPASS_ALLOWLIST_REL_PATHS:
        return True
    if any(rel_path.startswith(prefix) for prefix in _STRATEGY_BYPASS_ALLOWLIST_PREFIXES):
        return True
    return any(token in rel_path for token in _STRATEGY_BYPASS_ALLOWLIST_NAME_SUBSTRINGS)


def collect_competing_total_orchestrator_definitions(
    *,
    scan_root: Path,
    path_root: Path,
) -> list[CompetingTotalOrchestratorHit]:
    """Find productive functions that compose nearly the full decision chain."""
    hits: list[CompetingTotalOrchestratorHit] = []
    for path in sorted(p for p in scan_root.rglob("*.py") if p.is_file()):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rel = path.resolve().relative_to(path_root.resolve()).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            stages = tuple(sorted(_call_names(node) & _PARTIAL_DECISION_STAGE_CALLS))
            if len(stages) < _COMPETING_ORCHESTRATOR_MIN_PARTIAL_STAGES:
                continue
            hits.append(
                CompetingTotalOrchestratorHit(
                    relative_path=rel,
                    lineno=int(getattr(node, "lineno", 0) or 0),
                    function_name=node.name,
                    partial_stages=stages,
                )
            )
    return sorted(hits)


def assert_single_canonical_total_decision_owner(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> TotalDecisionOwnerDefinitionHit:
    """INVARIANT A — CANONICAL_TOTAL_DECISION_OWNER_COUNT=1 (+ no competing orchestrator)."""
    root = scan_root if scan_root is not None else SRC_ROOT
    base = path_root if path_root is not None else REPO_ROOT
    sole = assert_exactly_one_canonical_total_decision_owner_definition(
        scan_root=root,
        path_root=base,
    )
    competing = collect_competing_total_orchestrator_definitions(
        scan_root=root,
        path_root=base,
    )
    unauthorized = [
        hit
        for hit in competing
        if not (
            hit.relative_path == _AUTHORIZED_TOTAL_DECISION_OWNER_REL_PATH
            and hit.function_name == _TOTAL_DECISION_OWNER_NAME
        )
    ]
    assert not unauthorized, (
        "INVARIANT_A_TOTAL_DECISION_OWNER: competing productive total "
        "orchestrator(s) detected (canonical partial-stage composition outside "
        f"{_AUTHORIZED_TOTAL_DECISION_OWNER_REL_PATH}::"
        f"{_TOTAL_DECISION_OWNER_NAME}):\n" + "\n".join(hit.report_line() for hit in unauthorized)
    )
    return sole


def assert_single_productive_replay_input_constructor(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> DirectReplayInputConstructionHit:
    """INVARIANT B — PRODUCTIVE_DIRECT_REPLAY_INPUT_CONSTRUCTOR_COUNT=1."""
    try:
        return assert_exactly_one_authorized_src_wide_productive_direct_replay_input_constructor(
            scan_root=scan_root,
            path_root=path_root,
        )
    except AssertionError as exc:
        raise AssertionError(
            "INVARIANT_B_REPLAY_INPUT_CONSTRUCTOR: "
            "productive direct IntegratedOfflineReplayInputV1 construction "
            f"must remain solely inside {_AUTHORIZED_CONSTRUCTOR_REL_PATH}::"
            f"{_PUBLIC_BUILDER_NAME}. Detail: {exc}"
        ) from exc


def _function_touches_strategy_signal_source(fn: ast.AST, file_text: str) -> bool:
    if _uses_name_or_attr(fn, _STRATEGY_SOURCE_MARKERS):
        return True
    if _uses_signals_attribute(fn) and any(
        marker in file_text for marker in _STRATEGY_SOURCE_MARKERS
    ):
        return True
    return False


def _classify_strategy_bypass_kinds(fn: ast.AST) -> list[StrategyBypassKind]:
    kinds: list[StrategyBypassKind] = []
    called = _call_names(fn)
    if _has_keyword_args(fn, _POSITION_KEYWORD_ARGS) or (
        "position" in getattr(fn, "name", "").lower() and _uses_signals_attribute(fn)
    ):
        kinds.append("position")
    if _uses_name_or_attr(fn, _ORDER_INTENT_NAMES):
        kinds.append("order_intent")
    if _uses_name_or_attr(fn, _TRADE_NAMES):
        kinds.append("trade")
    if "run_realistic" in called and _uses_name_or_attr(
        fn,
        frozenset(
            {
                "ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY",
                "execute_configured_strategy_signal_series_v1",
                "StrategySignalBindingResultV1",
            }
        ),
    ):
        kinds.append("authoritative_engine")
    return kinds


def collect_direct_strategy_authority_bypass_hits(
    *,
    scan_root: Path,
    path_root: Path,
) -> list[DirectStrategyAuthorityBypassHit]:
    """AST-scan for system-relevant strategy→position/trade/order authority bypasses."""
    hits: list[DirectStrategyAuthorityBypassHit] = []
    for path in sorted(p for p in scan_root.rglob("*.py") if p.is_file()):
        rel = path.resolve().relative_to(path_root.resolve()).as_posix()
        if _is_strategy_bypass_allowlisted(rel):
            continue
        text = path.read_text(encoding="utf-8")
        if not any(marker in text for marker in _STRATEGY_SOURCE_MARKERS) and (
            ".signals" not in text
        ):
            continue
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _function_touches_strategy_signal_source(node, text):
                continue
            if _call_names(node) & _CANONICAL_OR_LEGACY_GATE_CALLS:
                continue
            for kind in _classify_strategy_bypass_kinds(node):
                hits.append(
                    DirectStrategyAuthorityBypassHit(
                        relative_path=rel,
                        lineno=int(getattr(node, "lineno", 0) or 0),
                        function_name=node.name,
                        kind=kind,
                    )
                )
    return sorted(hits)


def assert_no_direct_strategy_authority_bypass(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> None:
    """INVARIANT C — no productive direct strategy authority bypass paths."""
    root = scan_root if scan_root is not None else SRC_ROOT
    base = path_root if path_root is not None else REPO_ROOT
    hits = collect_direct_strategy_authority_bypass_hits(scan_root=root, path_root=base)
    position = [h for h in hits if h.kind == "position"]
    order_intent = [h for h in hits if h.kind == "order_intent"]
    trade = [h for h in hits if h.kind in {"trade", "authoritative_engine"}]
    assert not hits, (
        "INVARIANT_C_STRATEGY_AUTHORITY_BYPASS: productive direct strategy "
        "signal→position/trade/order (or authoritative engine) bypass path(s) "
        "detected without canonical replay/decision owner or legacy fail-closed "
        "gate:\n"
        + "\n".join(hit.report_line() for hit in hits)
        + f"\nDIRECT_STRATEGY_TO_POSITION_PATH_COUNT={len(position)}"
        + f"\nDIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT={len(order_intent)}"
        + f"\nSYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT={len(trade)}"
    )


def count_strategy_bypass_paths_by_kind(
    *,
    scan_root: Path | None = None,
    path_root: Path | None = None,
) -> dict[str, int]:
    root = scan_root if scan_root is not None else SRC_ROOT
    base = path_root if path_root is not None else REPO_ROOT
    hits = collect_direct_strategy_authority_bypass_hits(scan_root=root, path_root=base)
    return {
        "DIRECT_STRATEGY_TO_POSITION_PATH_COUNT": sum(1 for h in hits if h.kind == "position"),
        "DIRECT_STRATEGY_TO_ORDER_INTENT_PATH_COUNT": sum(
            1 for h in hits if h.kind == "order_intent"
        ),
        "SYSTEM_RELEVANT_DIRECT_STRATEGY_TO_TRADE_PATH_COUNT": sum(
            1 for h in hits if h.kind in {"trade", "authoritative_engine"}
        ),
    }


__all__ = [
    "CompetingTotalOrchestratorHit",
    "DirectReplayInputConstructionHit",
    "DirectStrategyAuthorityBypassHit",
    "REPO_ROOT",
    "SRC_ROOT",
    "TotalDecisionOwnerDefinitionHit",
    "assert_no_direct_strategy_authority_bypass",
    "assert_single_canonical_total_decision_owner",
    "assert_single_productive_replay_input_constructor",
    "collect_competing_total_orchestrator_definitions",
    "collect_direct_replay_input_constructions",
    "collect_direct_strategy_authority_bypass_hits",
    "collect_total_decision_owner_definitions",
    "count_strategy_bypass_paths_by_kind",
]
