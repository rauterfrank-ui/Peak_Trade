"""
Learnable surfaces policy: enforce allowlist per layer at runtime.

Rule: Learning is only allowed when a layer has an explicit allowlist of
learnable surfaces. Default: deny if layer not listed or surface not in list.
L0, L4, L5, L6: always deny (no learnable surfaces).

Reference: docs/governance/LAYER_LEARNING_SURFACES_STUB.md
Config: config/learning_surfaces.toml (preferred).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

# Layers that must never have learnable surfaces (deny-all).
DENY_ALL_LAYERS: Set[str] = {"L0", "L4", "L5", "L6"}

VALID_LAYER_IDS: Set[str] = {"L0", "L1", "L2", "L3", "L4", "L5", "L6"}


class LearnableSurfacesViolation(Exception):
    """Raised when a layer requests learning for a surface not on the allowlist."""

    def __init__(self, message: str, layer_id: str, requested: List[str], allowed: List[str]):
        super().__init__(message)
        self.layer_id = layer_id
        self.requested = list(requested)
        self.allowed = list(allowed)


def _repo_root() -> Path:
    """Return repo root (directory containing config/)."""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "config" / "learning_surfaces.toml").exists():
            return parent
        if (parent / "config").is_dir() and (parent / "config" / "model_registry.toml").exists():
            return parent
    return Path.cwd()


def load_policy(config_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Load layer -> list of allowed learnable surfaces from config.

    Returns dict: layer_id -> [surface, ...]. Layers not present have no
    learnable surfaces (deny-all). Config key: [layers.<layer_id>] learnable = [...]
    """
    try:
        import tomllib as tomli  # Python 3.11+
    except ImportError:
        import tomli  # type: ignore

    path = config_path or (_repo_root() / "config" / "learning_surfaces.toml")
    if not path.exists():
        return {}

    with open(path, "rb") as f:
        data = tomli.load(f)

    layers = data.get("layers") or {}
    result: Dict[str, List[str]] = {}
    for layer_id, block in layers.items():
        if not isinstance(block, dict):
            continue
        learnable = block.get("learnable")
        if isinstance(learnable, list):
            result[layer_id] = [str(s) for s in learnable]
        else:
            result[layer_id] = []
    return result


def get_allowed_surfaces(layer_id: str, policy: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """
    Return the list of allowed learnable surfaces for a layer.

    L0/L4/L5/L6 always return []. Unknown layers return [] (deny-by-default).
    """
    if layer_id in DENY_ALL_LAYERS:
        return []
    if policy is None:
        policy = load_policy()
    return list(policy.get(layer_id, []))


def assert_surfaces_allowed(
    layer_id: str,
    requested: List[str],
    policy: Optional[Dict[str, List[str]]] = None,
) -> None:
    """
    Assert that the layer is allowed to learn the requested surfaces.

    - L0, L4, L5, L6: always raises (no learnable surfaces).
    - Unknown layer: raises.
    - Layer not in policy or surface not in allowlist: raises.

    Raises:
        LearnableSurfacesViolation: if any requested surface is not allowed.
        ValueError: if layer_id is not a valid layer id (L0..L6).
    """
    if layer_id not in VALID_LAYER_IDS:
        raise ValueError(
            f"Invalid layer_id: {layer_id!r}. Must be one of {sorted(VALID_LAYER_IDS)}"
        )

    if not requested:
        return  # Nothing to allow/deny

    if layer_id in DENY_ALL_LAYERS:
        raise LearnableSurfacesViolation(
            f"Layer {layer_id} has no learnable surfaces (governance deny-all)",
            layer_id=layer_id,
            requested=requested,
            allowed=[],
        )

    if policy is None:
        policy = load_policy()

    allowed = policy.get(layer_id)
    if allowed is None:
        raise LearnableSurfacesViolation(
            f"Layer {layer_id} has no learnable surfaces in policy (deny-by-default)",
            layer_id=layer_id,
            requested=requested,
            allowed=[],
        )

    allowed_set = set(allowed)
    disallowed = [s for s in requested if s not in allowed_set]
    if disallowed:
        raise LearnableSurfacesViolation(
            f"Layer {layer_id} requested disallowed surfaces: {disallowed}. Allowed: {allowed}",
            layer_id=layer_id,
            requested=requested,
            allowed=allowed,
        )


def validate_envelope_learnable_surfaces(
    envelope: Dict[str, object],
    layer_id: str,
    policy: Optional[Dict[str, List[str]]] = None,
) -> None:
    """
    Envelope boundary gate: if envelope has learnable_surfaces or requested_surfaces,
    assert all are allowlisted for the layer. Missing key => treated as [] (no-op).

    Call this when assembling or accepting a layer envelope so runtime enforces
    the learnable surfaces policy (e.g. L2->L3 handoff with disallowed surface blocks).

    Raises:
        LearnableSurfacesViolation: if any requested surface is not allowed.
        ValueError: if layer_id is not valid.
    """
    requested = envelope.get("learnable_surfaces") or envelope.get("requested_surfaces")
    if requested is None:
        requested = []
    if not isinstance(requested, list):
        requested = []
    requested = [str(s) for s in requested]
    assert_surfaces_allowed(layer_id, requested, policy=policy)
