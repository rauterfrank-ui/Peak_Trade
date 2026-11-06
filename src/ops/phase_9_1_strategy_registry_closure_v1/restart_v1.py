"""Restart / deterministic registry reconstruction proof."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.phase_9_1_strategy_registry_closure_v1.inventory_v1 import (
    build_strategy_registry_matrix_v1,
    classification_counts_v1,
    matrix_digest_v1,
)
from src.strategies.registry import build_registry_snapshot, serialize_registry_snapshot


def prove_restart_deterministic_v1(*, config_digest: str) -> Dict[str, Any]:
    snap_a = build_registry_snapshot()
    snap_b = build_registry_snapshot()
    ser_a = serialize_registry_snapshot(snap_a)
    ser_b = serialize_registry_snapshot(snap_b)
    rows_a = build_strategy_registry_matrix_v1(config_digest=config_digest)
    rows_b = build_strategy_registry_matrix_v1(config_digest=config_digest)
    digest_a = matrix_digest_v1(rows_a)
    digest_b = matrix_digest_v1(rows_b)
    counts_a = classification_counts_v1(rows_a)
    counts_b = classification_counts_v1(rows_b)
    ok = (
        snap_a.semantic_digest == snap_b.semantic_digest
        and ser_a == ser_b
        and digest_a == digest_b
        and counts_a == counts_b
        and snap_a.strategy_ids_sorted == snap_b.strategy_ids_sorted
    )
    return {
        "RESTART_DETERMINISTIC": ok,
        "registry_semantic_digest": snap_a.semantic_digest,
        "matrix_digest": digest_a,
        "strategy_ids_sorted": list(snap_a.strategy_ids_sorted),
        "classification_counts": counts_a,
        "serialization_stable": ser_a == ser_b,
        "ok": ok,
    }
