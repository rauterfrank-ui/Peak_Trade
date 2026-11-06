"""Shared CURRENT C1-cycle test fixtures. Not a V5 execute host."""

from __future__ import annotations

from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    V5_OWNER_GO,
)
from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.repository_sha_source_v1 import (
    resolve_repository_sha_from_git_head_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER_GO = V5_OWNER_GO
TRACKED_CURSOR = (
    REPO_ROOT
    / "evidence/ops/full_core_current_productive_sidestate_confirmation_cursor_current_v1"
    / "current_productive_sidestate_confirmation_cursor_v1.json"
)
SATISFIED_TS_MS = 1_789_527_840_000
FLOOR_TS_MS = 1_789_527_780_000
V5_HOST = (
    REPO_ROOT
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)


def _declared_checkout_sha() -> str:
    return resolve_repository_sha_from_git_head_v1(repo_root=REPO_ROOT)


def _candles(*, last_ts_ms: int, confirm: str = "1", count: int = 8) -> dict[str, object]:
    rows: list[list[str]] = []
    close = 0.188
    for index in range(count):
        ts = str(last_ts_ms - (count - 1 - index) * 60_000)
        px = f"{close:.4f}"
        rows.append(
            [ts, px, px, px, px, "10", "100", "USDT", confirm if index == count - 1 else "1"]
        )
    return {"code": "0", "data": rows}
