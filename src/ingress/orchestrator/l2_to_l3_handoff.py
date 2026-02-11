"""
L2→L3 handoff: build LayerEnvelope from L2-style capsule, run L3 dry-run (pointer-only, files-only).

No execution, no learning writes, no external tools. Gates: tooling_allowlist from scope,
learnable_surfaces validated at L3Runner boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

from src.ai_orchestration.capability_scope_loader import CapabilityScopeLoader
from src.ai_orchestration.layer_envelope import build_layer_envelope
from src.ai_orchestration.l3_runner import L3Runner
from src.ai_orchestration.model_registry_loader import ModelRegistryLoader

CapsuleLike = Union[str, Path, Dict[str, Any]]


@dataclass(frozen=True)
class L2ToL3HandoffResult:
    """Result of L2→L3 dry-run handoff (pointer-only, deterministic)."""

    run_id: str
    evidence_pack_id: str
    out_dir: str
    artifacts: Sequence[str]


def _load_capsule_dict(capsule: CapsuleLike) -> Dict[str, Any]:
    if isinstance(capsule, dict):
        return dict(capsule)
    p = Path(capsule)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Capsule must be a JSON object (dict).")
    return data


def run_l3_dry_run_from_l2_capsule(
    capsule: CapsuleLike,
    *,
    out_dir: Union[str, Path],
    registry_loader: Optional[ModelRegistryLoader] = None,
    scope_loader: Optional[CapabilityScopeLoader] = None,
    clock: Optional[Any] = None,
) -> L2ToL3HandoffResult:
    """
    Deterministic, pointer-only L2→L3 handoff.

    Builds a LayerEnvelope for L3 with tooling_allowlist from capability scope.
    Calls L3Runner.run(mode="dry-run") with envelope.inputs (pointer-only).
    No execution, no learning writes, no external tools. Learnable surfaces
    are validated at L3Runner boundary (fail-closed).
    """
    capsule_dict = _load_capsule_dict(capsule)

    registry_loader = registry_loader or ModelRegistryLoader()
    scope_loader = scope_loader or CapabilityScopeLoader()

    # Load L3 scope to derive tooling allowlist
    scope = scope_loader.load("L3")
    tooling_allowlist = list(scope.tooling_allowed or [])
    if not tooling_allowlist:
        raise RuntimeError("L3 tooling allowlist is empty; refusing to run (fail-closed).")

    # Learnable surfaces: from capsule or empty; gate enforced in L3Runner.
    learnable_surfaces = capsule_dict.get("learnable_surfaces") or capsule_dict.get(
        "requested_surfaces"
    )
    if isinstance(learnable_surfaces, list):
        learnable_surfaces = list(learnable_surfaces)
    else:
        learnable_surfaces = None

    envelope = build_layer_envelope(
        layer_id="L3",
        inputs=capsule_dict,
        tooling_allowlist=tooling_allowlist,
        learnable_surfaces=learnable_surfaces,
    )

    l3 = L3Runner(
        registry_loader=registry_loader,
        scope_loader=scope_loader,
        clock=clock,
    )
    out_p = Path(out_dir)
    res = l3.run(
        inputs=envelope.inputs,
        out_dir=out_p,
        mode="dry-run",
        operator_notes="L2->L3 orchestrator handoff (dry-run, pointer-only).",
        findings=[],
        actions=[],
    )
    return L2ToL3HandoffResult(
        run_id=res.run_id,
        evidence_pack_id=res.evidence_pack_id,
        out_dir=str(out_p),
        artifacts=tuple(res.artifacts),
    )
