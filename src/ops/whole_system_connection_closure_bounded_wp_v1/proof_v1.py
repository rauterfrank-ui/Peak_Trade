"""Static whole-system connection proof for productive Decision → PRE_EXTERNAL."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import FrozenSet, Tuple

from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    FINAL_D_T_FORMULA_SELECTED,
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    P5_AUTHORITY_CUTOVER_AUTHORIZED,
    PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED,
    PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED,
    REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    FIRST_TRADING_DECISION_CONSUMER,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.constants_v1 import (
    INTENTIONALLY_LEGACY_CYCLE_CALLERS,
    PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS,
    SOLE_TRADING_DECISION_AUTHORITY,
)

_CYCLE_INVOKE = "run_current_productive_master_v2_runtime_cycle_v1("
_BIND_KWARGS = "productive_layered_core_bind_cycle_kwargs_v1("
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CYCLE_MODULE = (
    _REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_runtime_cycle_v1.py"
)
_BIND_SEAM_MODULE = (
    _REPO_ROOT
    / "src/ops/p5_10_productive_activation_and_binding_v1/productive_cycle_bind_seam_v1.py"
)


@dataclass(frozen=True)
class WholeSystemConnectionProofResultV1:
    ok: bool
    unknown_callers: Tuple[str, ...]
    miswired_productive_callers: Tuple[str, ...]
    guard_failures: Tuple[str, ...]
    competing_p5_seam_in_cycle: bool
    reselection_markers_in_productive_bind: Tuple[str, ...]
    backflow_markers: Tuple[str, ...]


def _rel(path: Path) -> str:
    try:
        return path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _scan_src_cycle_callers() -> FrozenSet[str]:
    src_root = _REPO_ROOT / "src"
    hits: set[str] = set()
    skip_prefix = "src/ops/whole_system_connection_closure_bounded_wp_v1/"
    for path in src_root.rglob("*.py"):
        rel = _rel(path)
        if rel.startswith(skip_prefix):
            continue
        text = path.read_text(encoding="utf-8")
        if _CYCLE_INVOKE in text:
            hits.add(rel)
    return frozenset(hits)


def _grep_file(path: Path, pattern: str) -> bool:
    if not path.is_file():
        return False
    return re.search(pattern, path.read_text(encoding="utf-8")) is not None


def prove_whole_system_connection_closure_v1() -> WholeSystemConnectionProofResultV1:
    """Fail-closed static proof; does not execute productive cycles or network I/O."""
    guard_failures: list[str] = []
    if PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED is not True:
        guard_failures.append("PRODUCTIVE_CYCLE_LAYERED_CORE_BIND_ENABLED")
    if REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED is not True:
        guard_failures.append("REGIME_SIDESTATE_MAPPING_CONTRACT_AUTHORIZED")
    if P5_AUTHORITY_CUTOVER_AUTHORIZED is not False:
        guard_failures.append("P5_AUTHORITY_CUTOVER_AUTHORIZED")
    if PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED is not False:
        guard_failures.append("PRODUCTIVE_DECISION_PATH_CUTOVER_ENABLED")
    if FINAL_D_T_FORMULA_SELECTED is not False:
        guard_failures.append("FINAL_D_T_FORMULA_SELECTED")
    if EXTERNAL_EFFECT_AUTHORIZED is not False:
        guard_failures.append("EXTERNAL_EFFECT_AUTHORIZED")
    if MULTI_FUTURE_RUNTIME_AUTHORIZED is not False:
        guard_failures.append("MULTI_FUTURE_RUNTIME_AUTHORIZED")
    if MAX_POSITIONS_EFFECTIVE != 1:
        guard_failures.append("MAX_POSITIONS_EFFECTIVE")

    if FIRST_TRADING_DECISION_CONSUMER != "run_current_productive_master_v2_runtime_cycle_v1":
        guard_failures.append("FIRST_TRADING_DECISION_CONSUMER")

    cycle_text = _CYCLE_MODULE.read_text(encoding="utf-8")
    competing_p5_seam_in_cycle = "run_p5_layered_core_authority_seam_v1" in cycle_text
    if SOLE_TRADING_DECISION_AUTHORITY.split(".")[-1] not in cycle_text:
        guard_failures.append("SOLE_TRADING_DECISION_REPLAY_OWNER_MISSING")

    bind_text = _BIND_SEAM_MODULE.read_text(encoding="utf-8")
    reselection_hits = tuple(
        marker
        for marker in ("reselect", "single_selected_future_policy")
        if marker.lower() in bind_text.lower()
    )
    backflow_hits = tuple(
        marker for marker in ("sidestate_backflow", "backflow_to_core") if marker in bind_text
    )

    productive_expected = frozenset(PRODUCTIVE_CURSOR_BACKED_CYCLE_CALLERS)
    legacy_expected = frozenset(INTENTIONALLY_LEGACY_CYCLE_CALLERS)
    cycle_module_rel = _rel(_CYCLE_MODULE)
    observed = _scan_src_cycle_callers() - {cycle_module_rel}

    unknown = sorted(observed - productive_expected - legacy_expected)
    miswired: list[str] = []
    for rel_path in sorted(productive_expected):
        path = _REPO_ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        if _CYCLE_INVOKE not in text:
            miswired.append(f"{rel_path}:missing_cycle_invoke")
        elif _BIND_KWARGS not in text:
            miswired.append(f"{rel_path}:missing_layered_bind_kwargs")

    ok = (
        not guard_failures
        and not competing_p5_seam_in_cycle
        and not unknown
        and not miswired
        and not reselection_hits
        and not backflow_hits
    )
    return WholeSystemConnectionProofResultV1(
        ok=ok,
        unknown_callers=tuple(unknown),
        miswired_productive_callers=tuple(miswired),
        guard_failures=tuple(guard_failures),
        competing_p5_seam_in_cycle=competing_p5_seam_in_cycle,
        reselection_markers_in_productive_bind=reselection_hits,
        backflow_markers=backflow_hits,
    )


__all__ = ["WholeSystemConnectionProofResultV1", "prove_whole_system_connection_closure_v1"]
