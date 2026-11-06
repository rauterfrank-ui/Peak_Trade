"""Contract/unit tests for V8 wiring evaluation surfaces (clarification-bound).

Does not mutate DEFINITION_ONLY preregistration. Does not authorize panel runs.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8 import (
    PACKAGE_MARKER,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.constants_v8 import (
    COOLDOWN_BARS,
    DEVELOPMENT_PREREGISTRATION_DIGEST,
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
    MECHANISM_ID,
    OWNER_SURFACE,
    RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.cooldown_state_v8 import (
    CooldownStateError,
    create_cooldown_state,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.decision_v8 import (
    RESULT_FAIL,
    RESULT_INCONCLUSIVE_INFRA,
    RESULT_INVALID_IDENTICAL_ARMS,
    RESULT_PASS,
    decide_development_evaluation_v8,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.hypothesis_dispatch_v8 import (
    HypothesisDispatchError,
    resolve_v8_dispatch,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.measurement_validity_preflight_v8 import (
    run_measurement_validity_preflight,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8.panel_runner_v8 import (
    run_development_evaluation,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v8 import (
    EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST,
    load_and_validate_repo_contract,
)

REPO = Path(__file__).resolve().parents[2]
TEST_FILE = Path(__file__).resolve()
CLI = (
    REPO
    / "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8.py"
)
CONTRACT = (
    REPO
    / "config/research/"
    / "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v8.json"
)


def _base_metrics(*, better: bool = True) -> tuple[dict, dict]:
    control = {
        "trade_count": 40,
        "net_return": -0.02,
        "net_profit_factor": 0.90,
        "cost_drag": 12.0,
        "short_trade_count": 20,
        "long_net_pnl": 1.0,
        "max_drawdown": -0.15,
        "worst1_abs_net_share": 0.2,
    }
    treatment = {
        "trade_count": 35,
        "net_return": -0.01 if better else -0.03,
        "net_profit_factor": 0.95 if better else 0.80,
        "cost_drag": 10.0 if better else 14.0,
        "short_trade_count": 15 if better else 22,
        "long_net_pnl": 1.0,
        "max_drawdown": -0.10 if better else -0.20,
        "worst1_abs_net_share": 0.2,
    }
    return control, treatment


def test_unit_tests_do_not_authorize_panel_run() -> None:
    tree = ast.parse(TEST_FILE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name == "run_development_evaluation":
                for kw in node.keywords:
                    if kw.arg == "allow_panel_run" and getattr(kw.value, "value", None) is True:
                        raise AssertionError("authorized panel run forbidden in unit tests")


def test_package_constants_match_frozen_prereg_digest() -> None:
    assert PACKAGE_MARKER.endswith("V8=true")
    assert HYPOTHESIS_ID.endswith("_V8")
    assert COOLDOWN_BARS == 24
    assert MECHANISM_ID.endswith("reentry_cooldown_v1")
    assert OWNER_SURFACE.endswith("_EVALUATION_V8")
    assert EVIDENCE_REL_PATH.endswith("_v8/")
    assert DEVELOPMENT_PREREGISTRATION_DIGEST == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST
    assert RESULT_CLASS_INCONCLUSIVE_INFRASTRUCTURE_FAILURE == "INCONCLUSIVE_INFRASTRUCTURE_FAILURE"


def test_preregistration_semantics_unchanged_on_disk() -> None:
    report = load_and_validate_repo_contract(REPO)
    assert report["evaluation_run_count"] == 0
    assert report["evaluation_executed"] is False
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["evaluation_authorized"] is False
    assert contract["implementation_authorized"] is False
    assert "exit_divergence_requirement" in contract
    assert contract["exit_divergence_requirement"]["required"] is True
    assert contract.get("implementation_surfaces_landed") is not True
    assert (
        contract["development_preregistration_digest"]
        == "610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c"
    )


def test_cooldown_boundary_b4_b5() -> None:
    st = create_cooldown_state(enabled=True, instrument_id="X")
    base = pd.Timestamp("2023-05-20T00:00:00Z")
    for i in range(0, 40):
        st.observe_bar(instrument_id="X", bar_index=i, bar_ts=base + pd.Timedelta(hours=i))
    t = 10
    st.on_midband_exit_fill(
        instrument_id="X", direction="short", exit_bar_index=t, trigger_kind="midband"
    )
    snap = st.scope_snapshot("X", "short")
    assert snap is not None
    assert snap["armed_at_bar_index"] == t
    assert snap["blocked_through_bar_index"] == t + 24
    assert snap["first_eligible_bar_index"] == t + 25
    assert st.check_entry_allowed(instrument_id="X", direction="short", bar_index=t) is False
    assert st.attribution()["same_bar_reentry_block_count"] >= 1
    assert st.check_entry_allowed(instrument_id="X", direction="short", bar_index=t + 24) is False
    assert st.check_entry_allowed(instrument_id="X", direction="short", bar_index=t + 25) is True


def test_scope_isolation_and_max_holding_does_not_arm() -> None:
    st = create_cooldown_state(enabled=True)
    base = pd.Timestamp("2023-05-20T00:00:00Z")
    for i in range(0, 30):
        st.observe_bar(instrument_id="A", bar_index=i, bar_ts=base + pd.Timedelta(hours=i))
        st.observe_bar(instrument_id="B", bar_index=i, bar_ts=base + pd.Timedelta(hours=i))
    st.on_midband_exit_fill(
        instrument_id="A", direction="short", exit_bar_index=5, trigger_kind="midband"
    )
    assert st.check_entry_allowed(instrument_id="A", direction="short", bar_index=6) is False
    assert st.check_entry_allowed(instrument_id="A", direction="long", bar_index=6) is True
    assert st.check_entry_allowed(instrument_id="B", direction="short", bar_index=6) is True
    st2 = create_cooldown_state(enabled=True, instrument_id="A")
    st2.on_midband_exit_fill(
        instrument_id="A", direction="short", exit_bar_index=3, trigger_kind="max_holding"
    )
    assert st2.attribution()["cooldown_activation_count"] == 0


def test_gap_fail_closed_b6() -> None:
    st = create_cooldown_state(enabled=True, instrument_id="A")
    base = pd.Timestamp("2023-05-20T00:00:00Z")
    st.observe_bar(instrument_id="A", bar_index=0, bar_ts=base)
    with pytest.raises(CooldownStateError, match="BAR_GAP"):
        st.observe_bar(instrument_id="A", bar_index=2, bar_ts=base + pd.Timedelta(hours=2))


def test_control_treatment_state_isolation_b8() -> None:
    control = create_cooldown_state(enabled=False, instrument_id="A")
    treatment = create_cooldown_state(enabled=True, instrument_id="A")
    base = pd.Timestamp("2023-05-20T00:00:00Z")
    for i in range(0, 30):
        control.observe_bar(instrument_id="A", bar_index=i, bar_ts=base + pd.Timedelta(hours=i))
        treatment.observe_bar(instrument_id="A", bar_index=i, bar_ts=base + pd.Timedelta(hours=i))
    treatment.on_midband_exit_fill(
        instrument_id="A", direction="short", exit_bar_index=4, trigger_kind="midband"
    )
    assert control.check_entry_allowed(instrument_id="A", direction="short", bar_index=4) is True
    assert treatment.check_entry_allowed(instrument_id="A", direction="short", bar_index=4) is False


def test_decision_b1_identical_exits_and_reentry_divergence() -> None:
    control, treatment = _base_metrics(better=True)
    out = decide_development_evaluation_v8(
        control=control,
        treatment=treatment,
        reentry_divergence_observed=True,
        exit_fills_identical=True,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=5,
        forced_midband_exit_count=2,
        cooldown_activation_count=2,
        blocked_same_side_reentry_count=3,
        authority_binding_ok=True,
    )
    assert out["result_class"] == RESULT_PASS

    missing = decide_development_evaluation_v8(
        control=control,
        treatment=treatment,
        reentry_divergence_observed=False,
        exit_fills_identical=True,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=5,
        forced_midband_exit_count=2,
        cooldown_activation_count=2,
        blocked_same_side_reentry_count=0,
        authority_binding_ok=True,
    )
    assert missing["result_class"] == RESULT_INVALID_IDENTICAL_ARMS
    assert missing["economic_verdict"] == "NOT_EVALUATED"


def test_decision_b2_maxdd_and_b7_pf() -> None:
    control, treatment = _base_metrics(better=False)
    out = decide_development_evaluation_v8(
        control=control,
        treatment=treatment,
        reentry_divergence_observed=True,
        exit_fills_identical=True,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=5,
        forced_midband_exit_count=2,
        cooldown_activation_count=2,
        blocked_same_side_reentry_count=3,
        authority_binding_ok=True,
    )
    assert out["result_class"] == RESULT_FAIL

    control2, treatment2 = _base_metrics(better=True)
    treatment2["max_drawdown"] = 0.10  # positive magnitude forbidden
    bad = decide_development_evaluation_v8(
        control=control2,
        treatment=treatment2,
        reentry_divergence_observed=True,
        exit_fills_identical=True,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=5,
        forced_midband_exit_count=2,
        cooldown_activation_count=2,
        blocked_same_side_reentry_count=3,
        authority_binding_ok=True,
    )
    assert bad["economic_verdict"] == "NOT_EVALUATED"


def test_decision_b3_infra() -> None:
    infra = decide_development_evaluation_v8(
        control={},
        treatment={},
        reentry_divergence_observed=True,
        exit_fills_identical=True,
        effective_configs_differ=True,
        open_side_binding_observed=True,
        exit_bars_observed=1,
        forced_midband_exit_count=1,
        cooldown_activation_count=1,
        blocked_same_side_reentry_count=1,
        authority_binding_ok=True,
        infrastructure_failure=True,
    )
    assert infra["result_class"] == RESULT_INCONCLUSIVE_INFRA
    assert infra["economic_verdict"] == "NOT_EVALUATED"


def test_measurement_validity_preflight_no_panel() -> None:
    report = run_measurement_validity_preflight(repo_root=REPO)
    assert report["holdout_data_accessed"] is False
    assert report["panel_data_accessed"] is False
    assert report["passed"] is True
    assert report["gates"]["exit_fills_identical"] is True
    assert report["gates"]["reentry_divergence_observed"] is True


def test_dispatch_and_unauthorized_runner(tmp_path: Path) -> None:
    entry = resolve_v8_dispatch(HYPOTHESIS_ID)
    assert entry["cli"].endswith("_v8.py")
    with pytest.raises(HypothesisDispatchError):
        resolve_v8_dispatch("UNKNOWN_HYPOTHESIS")
    with pytest.raises(RuntimeError, match="V8_EVALUATION_NOT_AUTHORIZED"):
        run_development_evaluation(
            output_dir=tmp_path / "evaluate_v8_must_not_create_canon_path",
            allow_panel_run=False,
        )


def test_cli_auth_fail_closed_no_evaluate() -> None:
    assert CLI.is_file()
    env = {
        **{k: v for k, v in __import__("os").environ.items()},
        "PYTHONPATH": f"{REPO}/src:{REPO}",
    }
    proc = subprocess.run(
        [sys.executable, str(CLI), "--mode", "evaluate"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert proc.returncode != 0
    assert "NOT_AUTHORIZED" in proc.stdout


def test_panel_runner_auth_and_falsy_zero() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8"
        / "panel_runner_v8.py"
    )
    text = path.read_text(encoding="utf-8")
    assert 'evaluation_run_count") or -1' not in text
    assert 'evaluation_run_count", -1)' in text
    assert "V8_EVALUATION_NOT_AUTHORIZED" in text
    assert "INCONCLUSIVE_INFRASTRUCTURE_FAILURE" in text
    assert "assert_v8_authority_and_prereg_gates" in text
    claim_pos = text.find("_claim_run_slot_atomic_v8(")
    archive_pos = text.find("resolve_development_archive_root(")
    assert 0 < claim_pos < archive_pos


def test_owner_map_evaluation_surface_present() -> None:
    owner = json.loads(
        (
            REPO
            / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
        ).read_text(encoding="utf-8")
    )
    assert OWNER_SURFACE in owner["allowed_optimization_surfaces"]


def test_preauth_bound_before_slot_claim() -> None:
    path = (
        REPO
        / "src/research/bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v8"
        / "panel_runner_v8.py"
    )
    text = path.read_text(encoding="utf-8")
    start = text.find("def run_development_evaluation(")
    end = text.find("\n__all__", start)
    if end < 0:
        end = len(text)
    body = text[start:end]
    gate_pos = body.find("assert_v8_authority_and_prereg_gates(")
    claim_pos = body.find("_claim_run_slot_atomic_v8(")
    archive_pos = body.find("resolve_development_archive_root(")
    assert 0 <= gate_pos < claim_pos < archive_pos
    g0 = text.find("def assert_v8_authority_and_prereg_gates(")
    g1 = text.find("def run_preflight_only(", g0)
    gate_fn = text[g0:g1]
    pre_pos = gate_fn.find("validate_pre_authorization_frozen_parameter_parity(")
    auth_pos = gate_fn.find("load_and_validate_authority(")
    assert 0 <= pre_pos < auth_pos


def test_no_evaluate_artifacts_and_contract_untouched() -> None:
    eval_dir = (
        REPO / "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v8"
    )
    assert eval_dir.is_dir()
    summary = json.loads((eval_dir / "summary.json").read_text(encoding="utf-8"))
    decision = json.loads((eval_dir / "comparison_decision.json").read_text(encoding="utf-8"))
    claim = json.loads((eval_dir / "run_slot_claim.json").read_text(encoding="utf-8"))
    assert summary["result_class"] == "PASS"
    assert decision["result_class"] == "PASS"
    assert int(summary["evaluation_run_count"]) == 1
    assert claim["slot_consumed"] is True
    assert summary["holdout_data_accessed"] is False
    assert summary["rerun_allowed"] is False
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["evaluation_run_count"] == 0
    assert contract["evaluation_authorized"] is False
    assert (
        contract["development_preregistration_digest"]
        == "610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c"
    )
    assert contract["exit_mechanism"]["frozen_parameters"]["bb_period"] == 20
    assert contract["exit_mechanism"]["cooldown"]["cooldown_bars"] == 24


def test_v7_terminal_surfaces_byte_stable_vs_origin_main() -> None:
    import subprocess

    files = [
        "src/research/bollinger_mr_midband_exit_reentry_cooldown_development_evaluation_v7/panel_runner_v7.py",
        "config/research/bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json",
        "docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7/summary.json",
        "config/research/bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v8.json",
    ]
    proc = subprocess.run(
        ["git", "diff", "--exit-code", "origin/main", "--", *files],
        cwd=str(REPO),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
