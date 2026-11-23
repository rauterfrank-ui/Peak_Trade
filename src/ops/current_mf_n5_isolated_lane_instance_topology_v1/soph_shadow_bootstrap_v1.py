"""Explicit deployment scope for the SOPH shadow genesis only."""

from dataclasses import dataclass
from pathlib import Path

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.i17_shadow_instrument_v1 import (
    SOPH_I17,
)

SOPH_SHADOW_INITIAL_ASSIGNMENT_POLICY = "SHADOW_SOPH_SLOT_2_THEN_LOWEST_FREE_LANES"


@dataclass(frozen=True)
class SophShadowSlot2BootstrapV1:
    deployment_root: Path
    surface: str
    lane_id: str
    canonical_instrument_id: str

    def require_topology_root(self, base: Path | str) -> None:
        root = self.deployment_root
        if (
            (self.surface, self.lane_id, self.canonical_instrument_id)
            != ("SHADOW", SOPH_I17.lane_id, SOPH_I17.canonical_id)
            or not root.is_absolute()
            or not root.name.startswith("wp02-shadow-")
            or Path(base) != root / "topology"
            or Path(base).resolve() != root.resolve() / "topology"
            or root.is_symlink()
        ):
            raise ValueError("SOPH_SHADOW_BOOTSTRAP_SCOPE_MISMATCH")
