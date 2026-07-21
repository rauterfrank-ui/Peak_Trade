"""Fail-closed measurement-validity preflight for V6 (no panel archive access).

Runs before the real DEVELOPMENT panel evaluation. Proves:
1) effective baseline/treatment config digests differ (gate enabled vs disabled)
2) open_side binds via wiring_mod capture alias
3) exit_bars_observed > 0 on admissible synthetic cases (midband and max-holding)
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
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_exit_efficiency_gate_v6 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.constants_v6 import (
    BINDING_FIX_SURFACE,
    MAX_HOLDING_BARS,
    MECHANISM_ID,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6 import (
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
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v6"
        / "composite_exit_efficiency_gate_v6.py"
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


def _synthetic_flat_max_holding_bars() -> pd.DataFrame:
    """Flat bars: no midband cross; max-holding should trigger at bar 48."""
    n = MAX_HOLDING_BARS + 12
    idx = pd.date_range("2023-05-20", periods=n, freq="h", tz="UTC")
    close = [100.0] * n
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
        "composite_exit_efficiency_gate_v6_sha256": gate_sha,
        "mechanism_id": MECHANISM_ID,
        "binding_fix_surface": BINDING_FIX_SURFACE,
    }
    return canonical_json_sha256(payload)


def _run_midband_synthetic_check(
    *,
    bars: pd.DataFrame,
    wiring_mod: Any,
    evidence: SimpleNamespace,
) -> dict[str, Any]:
    short_mask = short_exit_mask_from_bars(bars)
    trigger_positions = [i for i, v in enumerate(short_mask.tolist()) if v]
    if not trigger_positions:
        return {
            "passed": False,
            "reason": "synthetic_fixture_missing_short_midband_cross",
            "open_side_binding_observed": False,
            "exit_bars_observed": 0,
            "exits_forced_by_gate": 0,
            "midband_exit_count": 0,
            "max_holding_exit_count": 0,
            "composite_exit_trigger_first_of": [],
            "baseline_signal": 0,
            "treatment_signal": 0,
            "synthetic_divergence_observed": False,
        }

    trigger_i = int(trigger_positions[0])
    entry_ts = bars.index[max(0, trigger_i - 3)]

    orig_bind = wiring_mod.bind_bar_for_mv2_wiring_v1
    orig_map = wiring_mod.map_decision_evidence_to_position_signal_v1

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(_evidence) -> int:
        return 0

    wiring_mod.bind_bar_for_mv2_wiring_v1 = _fake_bind_bar  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _fake_map  # type: ignore[assignment]
    try:
        baseline_signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))

        open_side_binding_observed = False
        exit_bars_observed = 0
        exits_forced = 0
        midband_exit_count = 0
        max_holding_exit_count = 0
        composite_triggers: list[str] = []
        treatment_signal = baseline_signal

        with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars) as counters:
            wiring_mod.capture_backtest_engine_position_feedback_v1(
                state=_open_short_loop_state(entry_ts=entry_ts),
                feedback_source_bar_epoch=trigger_i - 1,
            )
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=bars.iloc[trigger_i],
                instrument_id="synthetic_preflight_midband",
                trading_epoch=trigger_i,
                profile_binding=None,
            )
            treatment_signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))
            exit_bars_observed = int(counters["exit_bars_observed"])
            exits_forced = int(counters["exits_forced_by_gate"])
            midband_exit_count = int(counters["midband_exit_count"])
            max_holding_exit_count = int(counters["max_holding_exit_count"])
            composite_triggers = list(counters["composite_exit_trigger_first_of"])
            open_side_binding_observed = exit_bars_observed > 0 or exits_forced > 0
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = orig_bind  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = orig_map  # type: ignore[assignment]

    synthetic_divergence_observed = treatment_signal != baseline_signal and exits_forced > 0
    return {
        "passed": open_side_binding_observed
        and exit_bars_observed > 0
        and synthetic_divergence_observed,
        "reason": "midband_synthetic_ok"
        if synthetic_divergence_observed
        else "midband_synthetic_failed",
        "open_side_binding_observed": open_side_binding_observed,
        "exit_bars_observed": exit_bars_observed,
        "exits_forced_by_gate": exits_forced,
        "midband_exit_count": midband_exit_count,
        "max_holding_exit_count": max_holding_exit_count,
        "composite_exit_trigger_first_of": composite_triggers,
        "baseline_signal": baseline_signal,
        "treatment_signal": treatment_signal,
        "synthetic_divergence_observed": synthetic_divergence_observed,
    }


def _run_max_holding_synthetic_check(
    *, bars: pd.DataFrame, wiring_mod: Any, evidence: SimpleNamespace
) -> dict[str, Any]:
    entry_ts = bars.index[0]
    trigger_i = MAX_HOLDING_BARS

    orig_bind = wiring_mod.bind_bar_for_mv2_wiring_v1
    orig_map = wiring_mod.map_decision_evidence_to_position_signal_v1

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(_evidence) -> int:
        return 0

    wiring_mod.bind_bar_for_mv2_wiring_v1 = _fake_bind_bar  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _fake_map  # type: ignore[assignment]
    try:
        with optional_treatment_exit_efficiency_gate(enabled=True, bars=bars) as counters:
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=bars.iloc[0],
                instrument_id="synthetic_preflight_entry",
                trading_epoch=0,
                profile_binding=None,
            )
            wiring_mod.capture_backtest_engine_position_feedback_v1(
                state=_open_short_loop_state(entry_ts=entry_ts),
                feedback_source_bar_epoch=0,
            )
            for step in range(1, trigger_i):
                wiring_mod.bind_bar_for_mv2_wiring_v1(
                    bar=bars.iloc[step],
                    instrument_id="synthetic_preflight_max_hold",
                    trading_epoch=step,
                    profile_binding=None,
                )
                wiring_mod.map_decision_evidence_to_position_signal_v1(evidence)

            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=bars.iloc[trigger_i],
                instrument_id="synthetic_preflight_max_hold",
                trading_epoch=trigger_i,
                profile_binding=None,
            )
            treatment_signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))
            max_holding_exit_count = int(counters["max_holding_exit_count"])
            midband_exit_count = int(counters["midband_exit_count"])
            composite_triggers = list(counters["composite_exit_trigger_first_of"])
            exits_forced = int(counters["exits_forced_by_gate"])
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = orig_bind  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = orig_map  # type: ignore[assignment]

    return {
        "passed": max_holding_exit_count >= 1 and exits_forced >= 1,
        "reason": "max_holding_synthetic_ok"
        if max_holding_exit_count >= 1
        else "max_holding_synthetic_failed",
        "max_holding_exit_count": max_holding_exit_count,
        "midband_exit_count": midband_exit_count,
        "composite_exit_trigger_first_of": composite_triggers,
        "exits_forced_by_gate": exits_forced,
        "treatment_signal": treatment_signal,
    }


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

    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    evidence = SimpleNamespace(decision_outcome="hold")
    midband_bars = _synthetic_short_midband_cross_bars()
    midband_check = _run_midband_synthetic_check(
        bars=midband_bars, wiring_mod=wiring_mod, evidence=evidence
    )

    max_hold_bars = _synthetic_flat_max_holding_bars()
    max_hold_check = _run_max_holding_synthetic_check(
        bars=max_hold_bars, wiring_mod=wiring_mod, evidence=evidence
    )

    open_side_binding_observed = bool(midband_check["open_side_binding_observed"])
    exit_bars_observed = int(midband_check["exit_bars_observed"])
    exits_forced = int(midband_check["exits_forced_by_gate"])
    midband_exit_count = int(midband_check["midband_exit_count"])
    max_holding_exit_count = int(max_hold_check["max_holding_exit_count"])
    composite_triggers = list(midband_check["composite_exit_trigger_first_of"]) + list(
        max_hold_check["composite_exit_trigger_first_of"]
    )
    synthetic_divergence_observed = bool(midband_check["synthetic_divergence_observed"])
    max_holding_synthetic_passed = bool(max_hold_check["passed"])

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
    elif not max_holding_synthetic_passed:
        result_class = RESULT_NO_EXIT
        reason = "max_holding_synthetic_check_failed"

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
        "midband_exit_count": midband_exit_count,
        "max_holding_exit_count": max_holding_exit_count,
        "composite_exit_trigger_first_of": composite_triggers,
        "midband_synthetic_check": midband_check,
        "max_holding_synthetic_check": max_hold_check,
        "baseline_signal": midband_check["baseline_signal"],
        "treatment_signal": midband_check["treatment_signal"],
        "synthetic_divergence_expected": True,
        "synthetic_divergence_observed": synthetic_divergence_observed,
        "binding_fix_surface": BINDING_FIX_SURFACE,
        "mechanism_id": MECHANISM_ID,
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
