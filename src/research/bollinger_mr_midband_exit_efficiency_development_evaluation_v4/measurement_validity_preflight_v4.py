"""Fail-closed measurement-validity preflight for V4 (no panel archive access).

Runs before the real DEVELOPMENT panel evaluation. Proves:
1) effective baseline/treatment config digests differ (gate enabled vs disabled)
2) open_side binds via wiring_mod capture alias
3) exit_bars_observed > 0 on an admissible synthetic case
4) synthetic baseline-vs-treatment divergence at the exit-decision boundary

Does not load sealed panel members or holdout paths.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    LegacyRealisticBarLoopStateV1,
)
from src.backtest.engine import Trade
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.exit_efficiency_gate_v1 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v4.constants_v4 import (
    BINDING_FIX_SURFACE,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v4 import (
    canonical_json_sha256,
)

RESULT_IDENTICAL = "INVALID_MEASUREMENT_IDENTICAL_EFFECTIVE_CONFIGS"
RESULT_BINDING = "INVALID_MEASUREMENT_BINDING_MISSING"
RESULT_NO_EXIT = "INVALID_MEASUREMENT_NO_EXIT_OBSERVABILITY"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _gate_module_sha256(repo: Path) -> str:
    path = (
        repo
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v1"
        / "exit_efficiency_gate_v1.py"
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_short_midband_cross_bars() -> pd.DataFrame:
    idx = pd.date_range("2023-05-20", periods=40, freq="h", tz="UTC")
    close = [100.0] * 20 + [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 109.0, 100.0]
    close = close + [100.0] * (40 - len(close))
    return pd.DataFrame(
        {
            "open": close,
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
        },
        index=idx,
    )


def _open_short_loop_state(*, entry_ts: pd.Timestamp) -> LegacyRealisticBarLoopStateV1:
    return LegacyRealisticBarLoopStateV1(
        equity=10_000.0,
        current_trade=Trade(
            entry_time=entry_ts,
            entry_price=110.0,
            size=-1.0,
            stop_price=120.0,
        ),
    )


def _effective_digest(*, declared: str, gate_enabled: bool, gate_sha: str) -> str:
    payload = {
        "declared_config_digest": declared,
        "gate_enabled": bool(gate_enabled),
        "exit_efficiency_gate_v1_sha256": gate_sha,
        "binding_fix_surface": BINDING_FIX_SURFACE,
    }
    return canonical_json_sha256(payload)


def run_measurement_validity_preflight(
    *,
    declared_runtime_cfg: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Return diagnostics; result_class is None iff all prerequisites pass."""
    repo = repo_root or _repo_root()
    cfg = (
        declared_runtime_cfg
        if declared_runtime_cfg is not None
        else {"strategy_id": "bollinger_bands", "version": "v2"}
    )
    declared = canonical_json_sha256(cfg)
    gate_sha = _gate_module_sha256(repo)
    baseline_eff = _effective_digest(declared=declared, gate_enabled=False, gate_sha=gate_sha)
    treatment_eff = _effective_digest(declared=declared, gate_enabled=True, gate_sha=gate_sha)
    effective_configs_differ = baseline_eff != treatment_eff

    bars = _synthetic_short_midband_cross_bars()
    short_mask = short_exit_mask_from_bars(bars)
    trigger_positions = [i for i, v in enumerate(short_mask.tolist()) if v]
    if not trigger_positions:
        return {
            "passed": False,
            "result_class": RESULT_NO_EXIT,
            "reason": "synthetic_fixture_missing_short_midband_cross",
            "declared_configs_differ": False,
            "baseline_declared_config_digest": declared,
            "treatment_declared_config_digest": declared,
            "baseline_effective_config_digest": baseline_eff,
            "treatment_effective_config_digest": treatment_eff,
            "effective_configs_differ": effective_configs_differ,
            "open_side_binding_observed": False,
            "exit_bars_observed": 0,
            "synthetic_divergence_expected": True,
            "synthetic_divergence_observed": False,
            "binding_fix_surface": BINDING_FIX_SURFACE,
            "first_divergence_or_collapse_boundary": "synthetic_fixture",
        }

    trigger_i = int(trigger_positions[0])
    entry_ts = bars.index[max(0, trigger_i - 3)]

    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(_evidence) -> int:
        return 0

    # Isolate from live MV2 map/bind while still exercising the gate's wiring_mod
    # capture-alias patch path (same pattern as gate_binding contract tests).
    orig_bind = wiring_mod.bind_bar_for_mv2_wiring_v1
    orig_map = wiring_mod.map_decision_evidence_to_position_signal_v1
    wiring_mod.bind_bar_for_mv2_wiring_v1 = _fake_bind_bar  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _fake_map  # type: ignore[assignment]
    try:
        evidence = SimpleNamespace(decision_outcome="hold")
        baseline_signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))

        open_side_binding_observed = False
        exit_bars_observed = 0
        exits_forced = 0
        treatment_signal = baseline_signal

        with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars) as counters:
            wiring_mod.capture_backtest_engine_position_feedback_v1(
                state=_open_short_loop_state(entry_ts=entry_ts),
                feedback_source_bar_epoch=trigger_i - 1,
            )
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=bars.iloc[trigger_i],
                instrument_id="synthetic_preflight",
                trading_epoch=trigger_i,
                profile_binding=None,
            )
            treatment_signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))
            exit_bars_observed = int(counters["exit_bars_observed"])
            exits_forced = int(counters["exits_forced_by_gate"])
            open_side_binding_observed = exit_bars_observed > 0 or exits_forced > 0
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = orig_bind  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = orig_map  # type: ignore[assignment]

    synthetic_divergence_observed = treatment_signal != baseline_signal and exits_forced > 0

    result_class: str | None = None
    reason = "measurement_validity_prerequisites_passed"
    if not effective_configs_differ:
        result_class = RESULT_IDENTICAL
        reason = "identical_effective_config_digests"
    elif not open_side_binding_observed:
        result_class = RESULT_BINDING
        reason = "open_side_binding_missing"
    elif exit_bars_observed <= 0:
        result_class = RESULT_NO_EXIT
        reason = "exit_bars_observed_le_0"
    elif not synthetic_divergence_observed:
        result_class = RESULT_BINDING
        reason = "synthetic_divergence_absent"

    return {
        "passed": result_class is None,
        "result_class": result_class,
        "reason": reason,
        "declared_configs_differ": False,
        "baseline_declared_config_digest": declared,
        "treatment_declared_config_digest": declared,
        "baseline_effective_config_digest": baseline_eff,
        "treatment_effective_config_digest": treatment_eff,
        "effective_configs_differ": effective_configs_differ,
        "open_side_binding_observed": open_side_binding_observed,
        "exit_bars_observed": exit_bars_observed,
        "exits_forced_by_gate": exits_forced,
        "baseline_signal": baseline_signal,
        "treatment_signal": treatment_signal,
        "synthetic_divergence_expected": True,
        "synthetic_divergence_observed": synthetic_divergence_observed,
        "binding_fix_surface": BINDING_FIX_SURFACE,
        "first_divergence_or_collapse_boundary": (
            "wiring_mod.capture_backtest_engine_position_feedback_v1"
            if open_side_binding_observed
            else "feedback_mod_only_collapse_or_unbound"
        ),
    }


__all__ = [
    "RESULT_BINDING",
    "RESULT_IDENTICAL",
    "RESULT_NO_EXIT",
    "run_measurement_validity_preflight",
]
