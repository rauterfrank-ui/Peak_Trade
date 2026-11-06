"""Contract/unit tests for composite exit-efficiency DEVELOPMENT evaluation v6 (pre-run).

No real panel evaluation. Does not invoke the panel runner or access archives.
Optional evidence assertions run only if terminal summary exists.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.backtest.backtest_engine_position_feedback_adapter_v1 import (
    LegacyRealisticBarLoopStateV1,
)
from src.backtest.engine import Trade
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v1.midband_exit_mechanism_v1 import (
    short_exit_mask_from_bars,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6 import (
    PACKAGE_MARKER as PACKAGE_MARKER_V6,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_exit_efficiency_gate_v6 import (
    optional_treatment_exit_efficiency_gate,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.composite_midband_max_holding_exit_mechanism_v6 import (
    MECHANISM_ID,
    composite_exit_triggered,
    max_holding_exit_triggered,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.constants_v6 import (
    BINDING_FIX_SURFACE,
    COMPOSITE_TRIGGER_POLICY,
    CONTRACT_REL_PATH,
    DEVELOPMENT_PREREGISTRATION_DIGEST,
    EVALUATION_RUN_ID,
    EVIDENCE_REL_PATH,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    MAX_HOLDING_BARS,
    REQUIRED_FROZEN_EXIT_PARAMETERS,
)
from src.research.bollinger_mr_midband_exit_efficiency_development_evaluation_v6.measurement_validity_preflight_v6 import (
    run_measurement_validity_preflight,
)
from src.research.bollinger_mr_midband_exit_efficiency_hypothesis_preregistration_v6 import (
    load_and_validate_repo_contract as load_v6_repo_contract,
)

REPO = Path(__file__).resolve().parents[2]
TEST_FILE = Path(__file__).resolve()
EVIDENCE = REPO / EVIDENCE_REL_PATH


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


def test_unit_tests_do_not_call_panel_runner_or_start_a_run() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    banned = {
        "run_development_evaluation",
        "run_arm",
        "load_member_bars",
        "resolve_development_archive_root",
        "verify_development_panel_hashes",
        "included_panel_members",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in banned:
                raise AssertionError(f"banned_call:{node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in banned:
                raise AssertionError(f"banned_call:{node.func.attr}")
    imports_os = False
    touches_environ = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "os" for alias in node.names):
            imports_os = True
        if isinstance(node, ast.ImportFrom) and node.module == "os":
            imports_os = True
        if isinstance(node, ast.Attribute) and node.attr == "environ":
            touches_environ = True
    assert imports_os is False
    assert touches_environ is False


def test_package_marker_v6() -> None:
    assert (
        PACKAGE_MARKER_V6 == "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6=true"
    )


def test_constants_v6_identity() -> None:
    assert HYPOTHESIS_ID == (
        "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6"
    )
    assert EVALUATION_RUN_ID == "evaluate_bollinger_mr_midband_exit_efficiency_development_v6"
    assert CONTRACT_REL_PATH.endswith(
        "bollinger_mr_midband_exit_efficiency_preregistered_economic_hypothesis_measurement_contract_v6.json"
    )
    assert (
        EVIDENCE_REL_PATH
        == "docs/evidence/evaluate_bollinger_mr_midband_exit_efficiency_development_v6/"
    )
    assert GOVERNANCE_REL_PATH == (
        "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_DEVELOPMENT_EVALUATION_V6.md"
    )
    assert BINDING_FIX_SURFACE == "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"
    assert MECHANISM_ID == (
        "canonical_bollinger_side_aware_middle_band_exit_with_frozen_max_holding_horizon_v1"
    )
    assert DEVELOPMENT_PREREGISTRATION_DIGEST == (
        "9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5"
    )
    assert REQUIRED_FROZEN_EXIT_PARAMETERS["max_holding_bars"] == 48
    assert REQUIRED_FROZEN_EXIT_PARAMETERS["composite_trigger_policy"] == COMPOSITE_TRIGGER_POLICY


def test_runner_script_exists() -> None:
    script = (
        REPO
        / "scripts/research/run_evaluate_bollinger_mr_midband_exit_efficiency_development_v6.py"
    )
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "run_development_evaluation" in text
    assert "EvaluationRunnerLifecycleObservabilityV1" in text
    assert "AUTO_RERUN_EXECUTED=false" in text
    assert "while True" not in text
    assert "run_slot_claim.json" in text


def test_panel_runner_falsy_zero_hygiene_lifecycle_and_claim() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_efficiency_development_evaluation_v6"
        / "panel_runner_v6.py"
    )
    text = path.read_text(encoding="utf-8")
    assert 'evaluation_run_count") or -1' not in text
    assert 'evaluation_run_count", -1)' in text
    assert "run_measurement_validity_preflight" in text
    assert "_claim_run_slot_atomic_v6" in text
    assert "commit_checkpoint_v5" in text
    assert "predecessor_development_v5" in text
    assert "composite_exit_efficiency_gate_v6" in text
    claim_pos = text.find("_claim_run_slot_atomic_v6(output_dir")
    archive_pos = text.find("resolve_development_archive_root(")
    assert 0 < claim_pos < archive_pos


def test_max_holding_trigger_math() -> None:
    assert max_holding_exit_triggered(entry_fill_index=None, bar_index=100) is False
    assert (
        max_holding_exit_triggered(entry_fill_index=0, bar_index=47, max_holding_bars=48) is False
    )
    assert max_holding_exit_triggered(entry_fill_index=0, bar_index=48, max_holding_bars=48) is True
    assert (
        max_holding_exit_triggered(entry_fill_index=10, bar_index=58, max_holding_bars=48) is True
    )


def test_composite_gate_midband_and_max_holding_synthetic() -> None:
    import src.backtest.mv2_research_wiring_v1 as wiring_mod

    idx = pd.date_range("2023-05-20", periods=40, freq="h", tz="UTC")
    close = [100.0] * 20 + [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 109.0, 100.0]
    close = close + [100.0] * (40 - len(close))
    midband_bars = pd.DataFrame(
        {
            "open": close,
            "high": [c + 1.0 for c in close],
            "low": [c - 1.0 for c in close],
            "close": close,
        },
        index=idx,
    )
    short_mask = short_exit_mask_from_bars(midband_bars)
    trigger_i = next(i for i, v in enumerate(short_mask.tolist()) if v)
    entry_ts = midband_bars.index[max(0, trigger_i - 3)]
    evidence = SimpleNamespace(decision_outcome="hold")

    def _fake_bind_bar(
        *, bar, instrument_id, trading_epoch, profile_binding, research_execution_cost=None
    ):
        return ("context", "l1_status", True)

    def _fake_map(_evidence) -> int:
        return 0

    orig_bind = wiring_mod.bind_bar_for_mv2_wiring_v1
    orig_map = wiring_mod.map_decision_evidence_to_position_signal_v1
    wiring_mod.bind_bar_for_mv2_wiring_v1 = _fake_bind_bar  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _fake_map  # type: ignore[assignment]
    try:
        with optional_treatment_exit_efficiency_gate(enabled=True, bars=midband_bars) as counters:
            wiring_mod.capture_backtest_engine_position_feedback_v1(
                state=_open_short_loop_state(entry_ts=entry_ts),
                feedback_source_bar_epoch=trigger_i - 1,
            )
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=midband_bars.iloc[trigger_i],
                instrument_id="synthetic_test",
                trading_epoch=trigger_i,
                profile_binding=None,
            )
            signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))
        assert int(counters["midband_exit_count"]) >= 1
        assert signal == 1
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = orig_bind  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = orig_map  # type: ignore[assignment]

    flat_n = MAX_HOLDING_BARS + 8
    flat_idx = pd.date_range("2023-06-01", periods=flat_n, freq="h", tz="UTC")
    flat_close = [100.0] * flat_n
    flat_bars = pd.DataFrame(
        {
            "open": flat_close,
            "high": [c + 1.0 for c in flat_close],
            "low": [c - 1.0 for c in flat_close],
            "close": flat_close,
        },
        index=flat_idx,
    )
    wiring_mod.bind_bar_for_mv2_wiring_v1 = _fake_bind_bar  # type: ignore[assignment]
    wiring_mod.map_decision_evidence_to_position_signal_v1 = _fake_map  # type: ignore[assignment]
    try:
        with optional_treatment_exit_efficiency_gate(enabled=True, bars=flat_bars) as counters:
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=flat_bars.iloc[0],
                instrument_id="flat_entry",
                trading_epoch=0,
                profile_binding=None,
            )
            wiring_mod.capture_backtest_engine_position_feedback_v1(
                state=_open_short_loop_state(entry_ts=flat_idx[0]),
                feedback_source_bar_epoch=0,
            )
            for step in range(1, MAX_HOLDING_BARS):
                wiring_mod.bind_bar_for_mv2_wiring_v1(
                    bar=flat_bars.iloc[step],
                    instrument_id="flat_hold",
                    trading_epoch=step,
                    profile_binding=None,
                )
                wiring_mod.map_decision_evidence_to_position_signal_v1(evidence)
            wiring_mod.bind_bar_for_mv2_wiring_v1(
                bar=flat_bars.iloc[MAX_HOLDING_BARS],
                instrument_id="flat_hold",
                trading_epoch=MAX_HOLDING_BARS,
                profile_binding=None,
            )
            signal = int(wiring_mod.map_decision_evidence_to_position_signal_v1(evidence))
        assert int(counters["max_holding_exit_count"]) >= 1
        assert signal == 1
    finally:
        wiring_mod.bind_bar_for_mv2_wiring_v1 = orig_bind  # type: ignore[assignment]
        wiring_mod.map_decision_evidence_to_position_signal_v1 = orig_map  # type: ignore[assignment]


def test_composite_exit_triggered_kinds() -> None:
    idx = pd.date_range("2023-05-20", periods=60, freq="h", tz="UTC")
    close = [100.0] * 30 + [105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 109.0, 100.0]
    close = close + [100.0] * (60 - len(close))
    bars = pd.DataFrame({"close": close}, index=idx)
    long_mask = pd.Series(False, index=idx)
    short_mask = short_exit_mask_from_bars(
        pd.DataFrame(
            {
                "open": close,
                "high": [c + 1.0 for c in close],
                "low": [c - 1.0 for c in close],
                "close": close,
            },
            index=idx,
        )
    )
    trigger_positions = [i for i, v in enumerate(short_mask.tolist()) if v]
    assert trigger_positions
    trigger_ts = idx[int(trigger_positions[0])]
    triggered, kind = composite_exit_triggered(
        open_side="short",
        ts=trigger_ts,
        long_mask=long_mask,
        short_mask=short_mask,
        entry_fill_index=0,
        bar_index=int(idx.get_loc(trigger_ts)),
    )
    assert triggered is True
    assert kind == "midband"

    triggered2, kind2 = composite_exit_triggered(
        open_side="short",
        ts=idx[MAX_HOLDING_BARS],
        long_mask=long_mask,
        short_mask=short_mask,
        entry_fill_index=0,
        bar_index=MAX_HOLDING_BARS,
    )
    assert triggered2 is True
    assert kind2 == "max_holding"


def test_measurement_validity_preflight_passes_without_panel() -> None:
    report = run_measurement_validity_preflight(repo_root=REPO)
    assert report["passed"] is True
    assert report["result_class"] is None
    assert report["midband_exit_count"] >= 1
    assert report["max_holding_exit_count"] >= 1
    assert report["effective_configs_differ"] is True
    assert report["open_side_binding_observed"] is True
    assert report["synthetic_divergence_observed"] is True


def test_v6_contract_terminal_fail() -> None:
    report = load_v6_repo_contract(REPO)
    assert report["valid"] is True
    assert report["evaluation_run_count"] == 1
    assert report["result_class"] == "FAIL"
    assert report["economic_verdict"] == "FAIL"
    assert report["economic_change_vs_development_v5"] is True


def test_terminal_evidence_fail_closeout() -> None:
    import json

    assert (EVIDENCE / "summary.json").is_file()
    summary = json.loads((EVIDENCE / "summary.json").read_text(encoding="utf-8"))
    claim = json.loads((EVIDENCE / "run_slot_claim.json").read_text(encoding="utf-8"))
    decision = json.loads((EVIDENCE / "comparison_decision.json").read_text(encoding="utf-8"))
    assert summary["hypothesis_id"] == HYPOTHESIS_ID
    assert summary["result_class"] == "FAIL"
    assert summary["evaluation_run_count"] == 1
    assert summary["evaluation_completed"] is True
    assert summary["acceptance_criteria_met"] is False
    assert summary["holdout_data_accessed"] is False
    assert summary.get("economic_change_vs_development_v5") is True
    assert summary["treatment_metrics"]["exits_forced_by_gate"] > 0
    assert summary["treatment_metrics"]["midband_exit_count"] > 0
    assert claim["slot_consumed"] is True
    assert decision["result_class"] == "FAIL"
    assert decision["reason"] == "NET_PROFIT_FACTOR_NOT_IMPROVED"
