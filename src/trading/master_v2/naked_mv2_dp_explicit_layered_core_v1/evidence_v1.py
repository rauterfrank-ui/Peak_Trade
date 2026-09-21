"""BWP evidence artifact for explicit layered core L1–L10."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.layer_catalog_v1 import (
    EXPLICIT_LAYERED_CORE_VERSION,
    LAYER_CATALOG_V1,
    LayerIdV1,
)

EVIDENCE_OWNER = "trading.master_v2.naked_mv2_dp_explicit_layered_core_v1.evidence_v1"
DEFAULT_EVIDENCE_REL = (
    "docs/evidence/naked_mv2_dp_explicit_layered_core_v1/layer_separation_evidence_v1.json"
)


def build_layer_separation_evidence_v1() -> dict[str, Any]:
    layers = []
    for layer_id in LayerIdV1:
        entry = LAYER_CATALOG_V1[layer_id]
        layers.append(
            {
                "LAYER_ID": entry.layer_id.value,
                "SEMANTIC_OWNER": entry.semantic_owner,
                "INPUT": entry.input_summary,
                "OUTPUT": entry.output_summary,
                "MUTATES": entry.mutates,
                "DOWNSTREAM_CONSUMER": entry.downstream_consumer,
            }
        )
    return {
        "EVIDENCE_VERSION": "naked_mv2_dp_explicit_layered_core_layer_separation/v1",
        "EVIDENCE_OWNER": EVIDENCE_OWNER,
        "EXPLICIT_LAYERED_CORE_VERSION": EXPLICIT_LAYERED_CORE_VERSION,
        "NULLLINE_SCOPE_SEPARATION": True,
        "NULLLINE_RUNNING_REFERENCE_SEPARATION": True,
        "SCOPE_RUNNING_REFERENCE_SEPARATION": True,
        "SCOPE_GENERATOR_REPLACEABLE": True,
        "FINAL_D_T_FORMULA_SELECTED": False,
        "PRODUCTIVE_D_T_BINDING_PRESENT": False,
        "SOLE_PRICE_SWITCH_RULE": "CM_t>=D_t",
        "LAYERS": layers,
    }


def write_layer_separation_evidence_v1(
    *,
    repo_root: Path,
    rel_path: str = DEFAULT_EVIDENCE_REL,
) -> Path:
    payload = build_layer_separation_evidence_v1()
    out = repo_root / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


__all__ = [
    "EVIDENCE_OWNER",
    "DEFAULT_EVIDENCE_REL",
    "build_layer_separation_evidence_v1",
    "write_layer_separation_evidence_v1",
]
