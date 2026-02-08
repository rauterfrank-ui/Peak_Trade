"""
LayerEnvelope: canonical boundary object orchestrator → layer runner.

Contract: pointer-only inputs; tooling_allowlist from scope; learnable_surfaces validated (deny-by-default).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


class LayerEnvelopeViolation(RuntimeError):
    """Raised when envelope construction violates contract (e.g. empty tooling_allowlist)."""

    pass


@dataclass(frozen=True)
class LayerEnvelope:
    """
    Canonical boundary object passed from orchestrator → layer runner.

    Contract:
    - pointer-only: no raw/payload/transcript/content/diff fields (enforced at runner)
    - tooling_allowlist: sourced from CapabilityScopeLoader (deny-by-default in scopes)
    - learnable_surfaces: optional; validated via governance allowlist (deny-by-default)
    """

    layer_id: str
    inputs: Dict[str, Any]
    tooling_allowlist: List[str]
    learnable_surfaces: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "tooling_allowlist": list(self.tooling_allowlist),
            "learnable_surfaces": list(self.learnable_surfaces),
            "inputs": dict(self.inputs),
        }


def _coerce_str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if value == []:
        return []
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise LayerEnvelopeViolation(f"expected list[str], got: {type(value).__name__}")
    return list(value)


def build_layer_envelope(
    *,
    layer_id: str,
    inputs: Dict[str, Any],
    tooling_allowlist: Sequence[str],
    learnable_surfaces: Optional[Sequence[str]] = None,
) -> LayerEnvelope:
    """
    Build a LayerEnvelope; learnable_surfaces from explicit arg or from inputs (learnable_surfaces/requested_surfaces).
    """
    ls = (
        list(learnable_surfaces)
        if learnable_surfaces is not None
        else _coerce_str_list(inputs.get("learnable_surfaces", inputs.get("requested_surfaces")))
    )
    ta = list(tooling_allowlist)
    if not ta or not all(isinstance(x, str) for x in ta):
        raise LayerEnvelopeViolation("tooling_allowlist must be non-empty list[str]")
    return LayerEnvelope(
        layer_id=layer_id,
        inputs=dict(inputs),
        tooling_allowlist=ta,
        learnable_surfaces=ls,
    )
