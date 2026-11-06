"""Concept v3/v3.1/v3.2 alignment to CURRENT MV2+DP authority — documentation binding only."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    CURRENT_BULL_BEAR_STATE_SWITCH_OWNER,
    CURRENT_COMPOSITION_OWNER,
    CURRENT_DYNAMIC_SCOPE_OWNER,
    CURRENT_ENTRY_EXIT_OWNER,
    CURRENT_MV2_DP_DECISION_SSOT,
    CURRENT_PRODUCTIVE_ENTRYPOINT,
    DECISION_CONFIG as V32_LIFECYCLE_DECISION_CONFIG,
    WORKPACKAGE_ID as V32_LIFECYCLE_WORKPACKAGE_ID,
    adjudicate_v32_baseline_first_requirements_v1,
)

SCHEMA_VERSION: Final[str] = "v32_current_mv2_dp_concept_alignment_v1"
WORKPACKAGE_ID: Final[str] = "V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/V32_CURRENT_MV2_DP_CONCEPT_ALIGNMENT_V1.md"
ALIGNMENT_ADDENDUM_SPEC: Final[str] = (
    "docs/ops/specs/PEAK_TRADE_META_LEARNING_OPTIMIZATION_UNIVERSE_CONCEPT_V3_2_"
    "CURRENT_MV2_DP_ALIGNMENT_ADDENDUM_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/v32_current_mv2_dp_concept_alignment_v1_decision_v1.json"
)

OWNER_SYMBOLS: Final[tuple[str, ...]] = (
    CURRENT_MV2_DP_DECISION_SSOT,
    CURRENT_PRODUCTIVE_ENTRYPOINT,
    CURRENT_DYNAMIC_SCOPE_OWNER,
    CURRENT_BULL_BEAR_STATE_SWITCH_OWNER,
    CURRENT_COMPOSITION_OWNER,
    CURRENT_ENTRY_EXIT_OWNER,
)

PDF_DELTA_INVENTORY_COUNT: Final[int] = 15


def _load_json(repo_root: Path, rel: str) -> Mapping[str, Any]:
    path = repo_root / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_dotted_symbol(module_path: str, attr: str) -> object:
    mod = importlib.import_module(module_path)
    return getattr(mod, attr)


def assert_current_owner_symbols_importable_v1() -> None:
    """Fail closed if any CURRENT owner symbol from #6764 cannot be imported."""
    for qualified in OWNER_SYMBOLS:
        module_path, _, attr = qualified.rpartition(".")
        if not module_path or not attr:
            raise ValueError(f"invalid_qualified_symbol:{qualified}")
        _resolve_dotted_symbol(module_path, attr)


def concept_alignment_binding_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    """Machine-readable alignment record (no runtime authority)."""
    root = repo_root or Path(__file__).resolve().parents[2]
    decision = _load_json(root, DECISION_CONFIG)
    lifecycle_decision = _load_json(root, V32_LIFECYCLE_DECISION_CONFIG)
    addendum_present = (root / ALIGNMENT_ADDENDUM_SPEC).is_file()
    normative_present = (root / NORMATIVE_SPEC).is_file()

    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "workpackage_id": WORKPACKAGE_ID,
            "normative_spec": NORMATIVE_SPEC,
            "alignment_addendum_spec": ALIGNMENT_ADDENDUM_SPEC,
            "normative_spec_present": normative_present,
            "alignment_addendum_present": addendum_present,
            "predecessor_workpackage_id": lifecycle_decision.get("workpackage_id"),
            "current_mv2_dp_decision_ssot": CURRENT_MV2_DP_DECISION_SSOT,
            "current_productive_entrypoint": CURRENT_PRODUCTIVE_ENTRYPOINT,
            "owner_symbols": OWNER_SYMBOLS,
            "pdf_delta_inventory_count": PDF_DELTA_INVENTORY_COUNT,
            "d24_status": decision.get("d24_status"),
            "d25_status": decision.get("d25_status"),
            "d26_status": decision.get("d26_status"),
            "d27_status": decision.get("d27_status"),
            "d26_implemented": decision.get("d26_implemented"),
            "earliest_true_remaining_technical_gap": decision.get(
                "earliest_true_remaining_technical_gap"
            ),
            "documentation_only": True,
            "p5_authority_cutover_authorized": False,
            "external_effect_authorized": False,
        }
    )


def assert_concept_alignment_consistent_with_v32_lifecycle_v1(
    *, repo_root: Path | None = None
) -> None:
    root = repo_root or Path(__file__).resolve().parents[2]
    decision = _load_json(root, DECISION_CONFIG)
    if decision.get("predecessor_workpackage_id") != V32_LIFECYCLE_WORKPACKAGE_ID:
        raise RuntimeError("predecessor_workpackage_mismatch")
    if decision.get("current_mv2_dp_decision_ssot") != CURRENT_MV2_DP_DECISION_SSOT:
        raise RuntimeError("decision_ssot_mismatch")
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=root)
    by_id = {r.requirement_id: r for r in rows}
    if by_id["D24"].verdict.value != decision.get("d24_status"):
        raise RuntimeError("d24_status_mismatch")
    if by_id["D25"].verdict.value != decision.get("d25_status"):
        raise RuntimeError("d25_status_mismatch")
    if by_id["D26"].verdict.value != decision.get("d26_status"):
        raise RuntimeError("d26_status_mismatch")
    if by_id["D27"].verdict.value != decision.get("d27_status"):
        raise RuntimeError("d27_status_mismatch")
    assert_current_owner_symbols_importable_v1()


__all__ = [
    "ALIGNMENT_ADDENDUM_SPEC",
    "DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "OWNER_SYMBOLS",
    "PDF_DELTA_INVENTORY_COUNT",
    "SCHEMA_VERSION",
    "WORKPACKAGE_ID",
    "assert_concept_alignment_consistent_with_v32_lifecycle_v1",
    "assert_current_owner_symbols_importable_v1",
    "concept_alignment_binding_v1",
]
