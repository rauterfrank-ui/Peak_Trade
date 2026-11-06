"""WP-02 insertion seam (Cap21→Cap22→POLICY_A) — productive default hook (CURRENT-WP-02)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

Wp02HookV1 = Callable[["Wp02InsertionContextV1"], None]


@dataclass
class Wp02InsertionContextV1:
    """Context passed to WP-02 hook between economic MD read and continuous admission."""

    public_store_root: Path
    venue_native_id: str
    canonical_instrument_id: str
    economic_md_mark_count: int
    tick_index: int
    wp02_result_sink: dict[str, Any] = field(default_factory=dict)


def noop_wp02_hook_v1(_ctx: Wp02InsertionContextV1) -> None:
    """Explicit no-op when productive default chain is disabled."""
