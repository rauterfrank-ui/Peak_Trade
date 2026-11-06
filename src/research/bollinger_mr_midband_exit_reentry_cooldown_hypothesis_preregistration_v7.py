"""Definition-only preregistration validator for Bollinger/MR midband reentry-cooldown v7.

Research governance only. No backtest, no economic metrics, no runtime policy,
no holdout access, no productive trading-logic mutation.

V7 introduces a genuine economic change versus terminal V6 FAIL: exact V6 composite
midband/max-hold semantics as control, plus a frozen same-instrument+same-direction
reentry cooldown after forced midband exits. V6 remains terminal FAIL (run count 1).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HYPOTHESIS_PREREGISTRATION_V7=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json"
)
OWNER_MAP_REL_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_DATASET_CLASS = "DEVELOPMENT_ONLY"
REQUIRED_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7"
)
REQUIRED_PREDECESSOR_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V6"
)
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
REQUIRED_TREATMENT_TYPE = "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM"
REQUIRED_MECHANISM_ID = "canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_and_same_side_reentry_cooldown_v1"
REQUIRED_PREREGISTRATION_STATE = "DEFINITION_ONLY_PREREGISTERED"
REQUIRED_OWNER_SURFACE = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HYPOTHESIS_PREREGISTRATION_DEFINITION_ONLY_V7"
)
REQUIRED_OBSERVABILITY_SURFACE = "EVALUATION_RUNNER_LIFECYCLE_OBSERVABILITY_V1"
REQUIRED_FALSY_ZERO_HYGIENE_SURFACE = "PANEL_RUNNER_FALSY_ZERO_PREMEASUREMENT_HYGIENE"
REQUIRED_BINDING_FIX_SURFACE = "MV2_WIRING_MOD_CAPTURE_ALIAS_OPEN_SIDE_BINDING_FIX"
REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE = (
    "BOLLINGER_MR_MIDBAND_EXIT_EFFICIENCY_PROCESS_LIFECYCLE_CHECKPOINT_V5"
)
EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST = (
    "4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680"
)
REQUIRED_PREDECESSOR_PREREGISTRATION_DIGEST = (
    "9ddcd32d78b3b3f60c168321404b2270a770409d46a3bff036f7dbc5eefd8fa5"
)
REQUIRED_PREDECESSOR_RESULT_DIGEST = (
    "608b1ff80333ffdb3f79566b419e57f3aeb2ac51b4edb98071b571e834bf4330"
)
REQUIRED_ATTRIBUTION_REF = (
    "docs/evidence/attribute_bollinger_mr_midband_exit_efficiency_v6_failure/"
)
REQUIRED_EVIDENCE_REF = (
    "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v7/"
)
REQUIRED_COOLDOWN_BARS = 24
REQUIRED_COOLDOWN_SCOPE = ("instrument_id", "direction")
REQUIRED_CAUSAL_BOUNDARY = (
    "forced_exit_execution -> cooldown_state_activation -> subsequent_same_side_entry_eligibility"
)
REQUIRED_COUNTERS = (
    "forced_midband_exit_count",
    "cooldown_activation_count",
    "blocked_same_side_reentry_count",
    "admitted_same_side_reentry_after_cooldown_count",
    "blocked_short_reentry_count",
    "blocked_long_reentry_count",
    "treatment_trade_count",
    "control_trade_count",
    "treatment_short_trade_count",
    "control_short_trade_count",
    "gross_pnl",
    "fees",
    "slippage",
    "total_cost",
    "net_pnl",
    "profit_factor",
    "max_drawdown",
    "instrument_level_attribution",
)
FORBIDDEN_EMBEDDED_RESULT_KEYS = frozenset(
    {
        "baseline_metrics",
        "treatment_metrics",
        "measured_net_return",
        "measured_profit_factor",
        "economic_metrics",
        "probe_summary",
    }
)


class HypothesisPreregistrationError(ValueError):
    """Fail-closed V7 preregistration validation error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_true(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        suffix = f": {detail}" if detail else ""
        raise HypothesisPreregistrationError(f"{code}{suffix}")


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def definition_body_for_preregistration_digest(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in contract.items() if k != "development_preregistration_digest"}


def compute_development_preregistration_digest(contract: Mapping[str, Any]) -> str:
    return canonical_json_sha256(definition_body_for_preregistration_digest(contract))


def reject_holdout_dataset_or_path(dataset_id: str | None = None, path: str | None = None) -> None:
    blob = f"{dataset_id or ''} {path or ''}"
    if HOLDOUT_OPAQUE_ID in blob:
        raise HypothesisPreregistrationError("HOLDOUT_PATH_OR_DATASET_FORBIDDEN")


def _contains_banned_result_keys(obj: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_path = f"{path}.{key}"
            if key in FORBIDDEN_EMBEDDED_RESULT_KEYS:
                found.append(key_path)
            found.extend(_contains_banned_result_keys(value, key_path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.extend(_contains_banned_result_keys(item, f"{path}[{idx}]"))
    return found


def validate_preregistration_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    _assert_true(contract.get("slice_class") == "DEFINITION_ONLY", "SLICE_CLASS")
    _assert_true(contract.get("status") == REQUIRED_PREREGISTRATION_STATE, "STATUS")
    _assert_true(
        contract.get("preregistration_state") == REQUIRED_PREREGISTRATION_STATE,
        "PREREGISTRATION_STATE",
    )
    _assert_true(contract.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID")
    _assert_true(
        contract.get("predecessor_hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "PREDECESSOR_ID",
    )
    _assert_true(contract.get("predecessor_result_class") == "FAIL", "PREDECESSOR_RESULT")
    _assert_true(int(contract.get("predecessor_evaluation_run_count", -1)) == 1, "PREDECESSOR_RUN")
    _assert_true(
        contract.get("predecessor_preregistration_digest")
        == REQUIRED_PREDECESSOR_PREREGISTRATION_DIGEST,
        "PREDECESSOR_PREREG_DIGEST",
    )
    _assert_true(
        contract.get("predecessor_result_digest") == REQUIRED_PREDECESSOR_RESULT_DIGEST,
        "PREDECESSOR_RESULT_DIGEST",
    )
    _assert_true(
        contract.get("source_attribution_evidence_ref") == REQUIRED_ATTRIBUTION_REF,
        "ATTRIBUTION_REF",
    )
    _assert_true(
        contract.get("evidence_ref") == REQUIRED_EVIDENCE_REF,
        "EVIDENCE_REF",
    )
    _assert_true(contract.get("dataset_id") == REQUIRED_DATASET_ID, "DATASET_ID")
    _assert_true(contract.get("dataset_class") == REQUIRED_DATASET_CLASS, "DATASET_CLASS")
    _assert_true(contract.get("development_only") is True, "DEVELOPMENT_ONLY")
    _assert_true(contract.get("holdout_allowed") is False, "HOLDOUT_ALLOWED")
    _assert_true(contract.get("holdout_forbidden") is True, "HOLDOUT_FORBIDDEN")
    _assert_true(contract.get("evaluation_authorized") is False, "EVAL_AUTHORIZED")
    _assert_true(contract.get("backtest_authorized") is False, "BACKTEST_AUTHORIZED")
    _assert_true(contract.get("implementation_authorized") is False, "IMPL_AUTHORIZED")
    _assert_true(contract.get("evaluation_executed") is False, "EVAL_EXECUTED")
    _assert_true(contract.get("evaluation_started") is False, "EVAL_STARTED")
    _assert_true(contract.get("evaluation_completed") is False, "EVAL_COMPLETED")
    _assert_true(int(contract.get("evaluation_run_count", -1)) == 0, "RUN_COUNT")
    _assert_true(int(contract.get("evaluation_run_count_authorized", -1)) == 1, "RUN_LIMIT")
    _assert_true(contract.get("result_class") == "NOT_EVALUATED", "RESULT_CLASS")
    _assert_true(contract.get("economic_verdict") == "NOT_EVALUATED", "ECONOMIC_VERDICT")
    _assert_true(contract.get("pass") is False, "PASS_FLAG")
    _assert_true(contract.get("fail") is False, "FAIL_FLAG")
    _assert_true(contract.get("rerun_allowed") is False, "RERUN")
    _assert_true(contract.get("runtime_implementation_in_this_slice") is False, "RUNTIME_IMPL")
    _assert_true(contract.get("productive_trading_logic_changed") is False, "PRODUCTIVE")

    treatment = contract.get("treatment")
    _assert_true(isinstance(treatment, Mapping), "TREATMENT_MISSING")
    assert isinstance(treatment, Mapping)
    _assert_true(treatment.get("treatment_type") == REQUIRED_TREATMENT_TYPE, "TREATMENT_TYPE")
    _assert_true(
        treatment.get("runtime_implementation_in_this_slice") is False, "TREATMENT_RUNTIME"
    )
    _assert_true(treatment.get("entry_signal_unchanged") is True, "ENTRY_SIGNAL")
    _assert_true(treatment.get("midband_exit_eligibility_unchanged") is True, "MIDBAND_ELIG")
    _assert_true(treatment.get("max_holding_rule_unchanged") is True, "MAX_HOLD")
    _assert_true(
        treatment.get("global_cross_instrument_pause_forbidden") is True, "NO_GLOBAL_PAUSE"
    )
    _assert_true(treatment.get("primary_target_side") == "short", "PRIMARY_SHORT")

    control = contract.get("control_arm")
    _assert_true(isinstance(control, Mapping), "CONTROL_MISSING")
    assert isinstance(control, Mapping)
    _assert_true(control.get("reentry_cooldown_applied") is False, "CONTROL_NO_COOLDOWN")
    _assert_true(
        control.get("source_hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID, "CONTROL_SRC"
    )

    mech = contract.get("exit_mechanism")
    _assert_true(isinstance(mech, Mapping), "MECHANISM_MISSING")
    assert isinstance(mech, Mapping)
    _assert_true(mech.get("mechanism_id") == REQUIRED_MECHANISM_ID, "MECHANISM_ID")
    cooldown = mech.get("cooldown")
    _assert_true(isinstance(cooldown, Mapping), "COOLDOWN_MISSING")
    assert isinstance(cooldown, Mapping)
    _assert_true(int(cooldown.get("cooldown_bars", -1)) == REQUIRED_COOLDOWN_BARS, "COOLDOWN_BARS")
    _assert_true(
        int(cooldown.get("cooldown_hours", -1)) == REQUIRED_COOLDOWN_BARS, "COOLDOWN_HOURS"
    )
    _assert_true(
        tuple(cooldown.get("scope_keys") or ()) == REQUIRED_COOLDOWN_SCOPE, "COOLDOWN_SCOPE"
    )
    _assert_true(cooldown.get("parameter_family") == "SINGLE_FROZEN_VALUE", "COOLDOWN_FAMILY")
    _assert_true(cooldown.get("dynamic_tuning_forbidden") is True, "NO_DYNAMIC_TUNING")
    _assert_true(cooldown.get("no_lookahead") is True, "NO_LOOKAHEAD")
    _assert_true(cooldown.get("no_cross_instrument_state_leak") is True, "NO_LEAK")
    _assert_true("midband" in (cooldown.get("arms_on_triggers") or []), "ARMS_MIDBAND")
    _assert_true(
        "max_holding" in (cooldown.get("does_not_arm_on_triggers") or []), "NO_ARM_MAXHOLD"
    )

    boundary = contract.get("causal_boundary")
    _assert_true(isinstance(boundary, Mapping), "BOUNDARY_MISSING")
    assert isinstance(boundary, Mapping)
    _assert_true(
        boundary.get("earliest_treatment_boundary") == REQUIRED_CAUSAL_BOUNDARY, "BOUNDARY"
    )

    counters = contract.get("required_observability_counters") or []
    for name in REQUIRED_COUNTERS:
        _assert_true(name in counters, f"COUNTER_MISSING:{name}")

    thresholds = contract.get("decision_thresholds")
    _assert_true(isinstance(thresholds, Mapping), "THRESHOLDS_MISSING")
    assert isinstance(thresholds, Mapping)
    _assert_true(thresholds.get("pass_criteria_frozen") is True, "PASS_FROZEN")
    _assert_true(
        thresholds.get("threshold_adjustment_forbidden_after_preregistration") is True, "NO_ADJ"
    )
    _assert_true(thresholds.get("require_net_return_treatment_gt_control") is True, "NET_GT")
    _assert_true(thresholds.get("require_net_profit_factor_treatment_ge_control") is True, "PF_GE")
    _assert_true(thresholds.get("require_cost_drag_treatment_lt_control") is True, "COST_LT")
    _assert_true(
        thresholds.get("require_short_trade_count_treatment_lt_control") is True, "SHORT_LT"
    )
    pass_all = thresholds.get("pass_requires_all") or []
    for needle in (
        "net_return_after_costs_treatment > net_return_after_costs_control",
        "net_profit_factor_treatment >= net_profit_factor_control",
        "cost_drag_treatment < cost_drag_control",
        "short_trade_count_treatment < short_trade_count_control",
        "blocked_same_side_reentry_count >= 1",
        "arms_identical == false",
    ):
        _assert_true(any(needle in str(x) for x in pass_all), f"PASS_NEEDLE:{needle}")

    banned = _contains_banned_result_keys(contract)
    _assert_true(not banned, "EMBEDDED_RESULT_METRICS", ", ".join(banned[:8]))

    digest = compute_development_preregistration_digest(contract)
    _assert_true(contract.get("development_preregistration_digest") == digest, "DIGEST_COMPUTED")
    _assert_true(digest == EXPECTED_DEVELOPMENT_PREREGISTRATION_DIGEST, "DIGEST_EXPECTED", digest)

    runtime = contract.get("runtime_policy")
    _assert_true(isinstance(runtime, Mapping), "RUNTIME_POLICY")
    assert isinstance(runtime, Mapping)
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
    ):
        _assert_true(runtime.get(key) is False, f"RUNTIME_UNLOCKED:{key}")

    promo = contract.get("promotion_and_holdout_policy")
    _assert_true(isinstance(promo, Mapping), "PROMO_POLICY")
    assert isinstance(promo, Mapping)
    _assert_true(promo.get("promotion_eligible") is False, "PROMOTION")
    _assert_true(promo.get("economic_gate_open") is False, "ECON_GATE")

    non_actions = contract.get("explicit_non_actions") or []
    for required in (
        "NO_V6_RERUN",
        "NO_V7_EVALUATION_IN_THIS_SLICE",
        "NO_V8_AUTO_CREATE",
        "NO_HOLDOUT_ACCESS",
        "NO_DYNAMIC_COOLDOWN_TUNING",
        "NO_RUNTIME_ACTIVATION",
        "NO_ORDERS",
    ):
        _assert_true(required in non_actions, f"NON_ACTION:{required}")

    return {
        "valid": True,
        "definition_only": True,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "mechanism_id": REQUIRED_MECHANISM_ID,
        "evaluation_run_count": 0,
        "evaluation_started": False,
        "evaluation_completed": False,
        "evaluation_executed": False,
        "result_class": "NOT_EVALUATED",
        "economic_verdict": "NOT_EVALUATED",
        "rerun_allowed": False,
        "cooldown_bars": REQUIRED_COOLDOWN_BARS,
        "cooldown_scope": list(REQUIRED_COOLDOWN_SCOPE),
        "causal_boundary": REQUIRED_CAUSAL_BOUNDARY,
        "development_preregistration_digest": digest,
        "identical_exit_mechanism_to_development_v6": False,
        "economic_change_vs_development_v6": True,
        "lifecycle_checkpoint_surface": REQUIRED_LIFECYCLE_CHECKPOINT_SURFACE,
        "observability_surface": REQUIRED_OBSERVABILITY_SURFACE,
    }


def load_and_validate_repo_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    path = root / CONTRACT_REL_PATH
    _assert_true(path.is_file(), "CONTRACT_MISSING", str(path))
    contract = _load_json(path)
    report = validate_preregistration_contract(contract)
    owner_map_path = root / OWNER_MAP_REL_PATH
    _assert_true(owner_map_path.is_file(), "OWNER_MAP_MISSING")
    owners = _load_json(owner_map_path).get("allowed_optimization_surfaces") or {}
    _assert_true(REQUIRED_OWNER_SURFACE in owners, "OWNER_SURFACE_MISSING")
    gov = root / (
        "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_PREREGISTERED_HYPOTHESIS_MEASUREMENT_V7.md"
    )
    _assert_true(gov.is_file(), "GOVERNANCE_MISSING")
    evid = (
        root / "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_hypothesis_v7"
    )
    _assert_true(evid.is_dir(), "EVIDENCE_MISSING")
    report["contract_path"] = CONTRACT_REL_PATH
    report["owner_surface"] = REQUIRED_OWNER_SURFACE
    return report
