"""Static bypass census for P5 in-scope producer roots."""

from __future__ import annotations

from pathlib import Path

_LAYERED_CORE_MARKERS: tuple[str, ...] = (
    "naked_mv2_dp_explicit_layered_core_v1",
    "apply_l1_selected_future_v1",
    "apply_l10_bull_bear_switch_v1",
    "orchestrate_naked_layered_core_v1",
    "run_productive_l6_seam_binding_v1",
    "bind_layer_input_from_adjudication_v1",
)

_B_FORBIDDEN: tuple[str, ...] = (
    "master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1",
    "master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1",
)

_PRODUCER_ROOTS: tuple[str, ...] = (
    "src/learning/market_intelligence_forecast_calibration_offline_stack_v1",
    "src/learning/deterministic_decision_outcome_v0",
    "src/experiments",
    "src/meta/learning_loop",
)


def scan_producer_class_bypass_v1(repo_root: Path | None = None) -> tuple[bool, tuple[str, ...]]:
    root = repo_root or Path(__file__).resolve().parents[3]
    hits: list[str] = []
    p5_marker = "master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1"
    for prefix in _PRODUCER_ROOTS:
        base = root / prefix
        if not base.is_dir():
            continue
        for py in base.rglob("*.py"):
            rel = py.relative_to(root).as_posix()
            if p5_marker in rel:
                continue
            try:
                text = py.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for marker in _LAYERED_CORE_MARKERS:
                if marker in text:
                    hits.append(f"{rel}:layered_core:{marker}")
            for marker in _B_FORBIDDEN:
                if marker in text and "p5_producer_productive_ingress" not in text:
                    hits.append(f"{rel}:component_b:{marker}")
    return (len(hits) == 0, tuple(sorted(set(hits))))
