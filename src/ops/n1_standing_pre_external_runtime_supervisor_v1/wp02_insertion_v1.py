"""WP-02 insertion seam (Cap21→Cap22→POLICY_A) — not implemented in WP-01."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

Wp02HookV1 = Callable[["Wp02InsertionContextV1"], None]


@dataclass(frozen=True)
class Wp02InsertionContextV1:
    """Context passed to optional WP-02 hook between economic MD read and continuous admission."""

    public_store_root: Path
    venue_native_id: str
    canonical_instrument_id: str
    economic_md_mark_count: int
    tick_index: int


def noop_wp02_hook_v1(_ctx: Wp02InsertionContextV1) -> None:
    """Default hook: no Cap21/Cap22/POLICY_A wiring in WP-01."""
