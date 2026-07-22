"""Definition-only holdout confirmation preregistration for frozen Exit V8.

Research governance only. No holdout data access, no backtest, no economic
metrics, no runtime policy mutation, no productive trading-logic mutation.

Successor identity is distinct from V8 DEVELOPMENT. V8 remains TERMINAL_PASS,
unreopened, and must not be holdout-evaluated under its development identity.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_PREREGISTRATION_V1=true"
CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistered_measurement_contract_v1.json"
)
DEV_CONTRACT_REL_PATH = (
    "config/research/"
    "bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v8.json"
)
ACQUISITION_CONTRACT_REL_PATH = (
    "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json"
)
DATASET_SPLIT_POLICY_REL_PATH = (
    "docs/evidence/archive_failed_bollinger_v2_and_next_hypothesis_v1/dataset_split_policy.json"
)
BOLLINGER_ARCHIVE_REL_PATH = "config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json"
EVIDENCE_REL_PATH = (
    "docs/evidence/preregister_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1/"
)
GOVERNANCE_REL_PATH = "docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_HOLDOUT_PREREGISTERED_MEASUREMENT_V1.md"

REQUIRED_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_HOLDOUT_V1"
)
REQUIRED_PREDECESSOR_HYPOTHESIS_ID = (
    "BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V8"
)
REQUIRED_MECHANISM_ID = "canonical_bollinger_side_aware_midband_exit_with_frozen_max_holding_and_same_side_reentry_cooldown_v1"
REQUIRED_V8_PREREGISTRATION_DIGEST = (
    "610460038f56bddda426f4169876a4ead00c186d1601256174033b4e4fca0a0c"
)
REQUIRED_DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1"
HOLDOUT_OPAQUE_ID = "offline_economic_reevaluation_sealed_long_panel_v1"
REQUIRED_PERIOD_START = "2023-08-16T05:55:00Z"
REQUIRED_PERIOD_END_EXCLUSIVE = "2024-09-01T00:00:00Z"
REQUIRED_INSTRUMENT_COUNT = 65
REQUIRED_CONTENT_HASH = "7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb"
REQUIRED_MANIFEST_SHA = "f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56"
REQUIRED_DEV_SPLIT = "a35783bf0268c174dfe585c9839ba45cc6e3835021699786f4490a0d8c9b33db"
REQUIRED_COOLDOWN_BARS = 24
REQUIRED_FROZEN_PARAMETERS = {
    "bb_period": 20,
    "bb_std": 2.0,
    "exit_level": "middle_band",
    "exit_threshold_binding_value": 0.5,
    "long_exit_rule": "close_crosses_middle_from_below_to_at_or_above",
    "short_exit_rule": "close_crosses_middle_from_above_to_at_or_below",
    "stop_loss_remains_active_if_hit_first": True,
    "max_holding_horizon_hours": 48,
    "max_holding_bars": 48,
    "max_holding_frequency": "PT1H",
    "max_holding_source_field": "splits.max_holding_horizon_hours",
    "max_holding_exit_rule": "bars_since_entry_fill_gte_max_holding_bars",
    "composite_trigger_policy": "first_of_midband_cross_or_max_holding",
}
OPERATOR_GO_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_EXECUTION_GO"
OPERATOR_GO_REQUIRED_VALUE = "true"
DECLARED_RUNNER_REL_PATH = (
    "scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_holdout_v1.py"
)
EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST = (
    "a0658fe3fb883939ed2a2de2c426f2e4edf21eeeb91d1b902d45b4d05a38fd1d"
)
EXPECTED_HOLDOUT_SPLIT_DIGEST = "e29eeb4e9d264e1529a0c7419d707ce84df7919ee6ed95a833612fca46a7184d"
DEFINITION_ONLY_STATUS = "DEFINITION_ONLY_HOLDOUT_PREREGISTERED"
DEFINITION_ONLY_VERDICT = (
    "HOLDOUT_HYPOTHESIS_AND_MEASUREMENT_CONTRACT_PREREGISTERED_AWAITING_SEPARATE_EXECUTION_GO"
)
DEFINITION_ONLY_NEXT_CANONICAL_STEP = "REVIEW_AND_MERGE_DEFINITION_ONLY_HOLDOUT_PREREGISTRATION_THEN_SEPARATE_OPERATOR_GO_FOR_EXACTLY_ONE_HOLDOUT_RUN"
TERMINAL_OVERLAY_KEYS = frozenset(
    {
        "holdout_executed",
        "terminal_holdout_result_class",
        "terminal_holdout_reason",
        "evaluation_evidence_ref",
    }
)


class HoldoutPreregistrationError(ValueError):
    """Fail-closed holdout preregistration / execution-gate error."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def definition_body_for_preregistration_digest(contract: Mapping[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in contract.items() if k != "holdout_preregistration_digest"}
    for key in TERMINAL_OVERLAY_KEYS:
        body.pop(key, None)
    body["status"] = DEFINITION_ONLY_STATUS
    body["verdict"] = DEFINITION_ONLY_VERDICT
    body["holdout_run_count"] = 0
    body["next_canonical_step"] = DEFINITION_ONLY_NEXT_CANONICAL_STEP
    return body


def compute_holdout_preregistration_digest(contract: Mapping[str, Any]) -> str:
    return canonical_json_sha256(definition_body_for_preregistration_digest(contract))


def load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise HoldoutPreregistrationError("JSON_ROOT_MUST_BE_OBJECT")
    return raw


def materialize_holdout_split_definition() -> dict[str, Any]:
    intervals = {
        "holdout_final_audit": {
            "start": REQUIRED_PERIOD_START,
            "end_exclusive": REQUIRED_PERIOD_END_EXCLUSIVE,
        }
    }
    return {
        "method": "SEALED_HOLDOUT_SINGLE_FINAL_AUDIT_PANEL_V1",
        "evidence_id": HOLDOUT_OPAQUE_ID,
        "dataset_id": REQUIRED_DATASET_ID,
        "dataset_class": "SEALED_HOLDOUT_FINAL_AUDIT_ONLY",
        "role": "FINAL_AUDIT_ONLY",
        "period_start": REQUIRED_PERIOD_START,
        "period_end_exclusive": REQUIRED_PERIOD_END_EXCLUSIVE,
        "instrument_count": REQUIRED_INSTRUMENT_COUNT,
        "content_hash_from_registry": REQUIRED_CONTENT_HASH,
        "sealed_manifest_sha256_from_registry": REQUIRED_MANIFEST_SHA,
        "decision_segment": "full_sealed_holdout_panel",
        "intervals": intervals,
        "overlap_with_development_forbidden": True,
        "development_panel_end_exclusive": "2023-08-16T05:55:00Z",
        "bitcoin_excluded": True,
        "spot_excluded": True,
        "venue": "OKX",
        "instrument_class": "LINEAR_USDT_PERPETUAL",
        "frequency": "PT1H",
        "source_ssot_refs": [
            "config/research/regime_gated_standaside_mr_independent_dev_panel_acquisition_contract_v1.json#sealed_holdout_opaque_exclusion",
            "docs/evidence/archive_failed_bollinger_v2_and_next_hypothesis_v1/dataset_split_policy.json#sealed_holdout",
            "config/research/bollinger_bands_v2_sealed_long_panel_terminal_economic_fail_archive_and_next_hypothesis_v1.json",
        ],
    }


def expected_holdout_split_digest() -> str:
    return canonical_json_sha256(materialize_holdout_split_definition())


def assert_execution_go_present(*, environ: Mapping[str, str] | None = None) -> None:
    env = environ if environ is not None else os.environ
    if env.get(OPERATOR_GO_ENV) != OPERATOR_GO_REQUIRED_VALUE:
        raise HoldoutPreregistrationError(
            f"HOLDOUT_V1_EXECUTION_GO_REQUIRED:{OPERATOR_GO_ENV}={OPERATOR_GO_REQUIRED_VALUE}"
        )


def assert_holdout_execution_blocked_by_definition_contract(
    contract: Mapping[str, Any],
) -> None:
    if contract.get("evaluation_authorized") is not False:
        raise HoldoutPreregistrationError("EVALUATION_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("backtest_authorized") is not False:
        raise HoldoutPreregistrationError("BACKTEST_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("holdout_execution_authorized") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if contract.get("holdout_data_access_authorized") is not False:
        raise HoldoutPreregistrationError("HOLDOUT_DATA_ACCESS_MUST_REMAIN_UNAUTHORIZED")
    gate = contract.get("execution_gate") or {}
    if gate.get("requires_separate_explicit_operator_go") is not True:
        raise HoldoutPreregistrationError("EXECUTION_GO_REQUIRED_FLAG_MISSING")


def _assert_true(condition: bool, code: str) -> None:
    if not condition:
        raise HoldoutPreregistrationError(code)


def validate_holdout_preregistration_contract(
    contract: Mapping[str, Any],
    *,
    development_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _assert_true(contract.get("slice_class") == "DEFINITION_ONLY", "SLICE_MUST_BE_DEFINITION_ONLY")
    assert_holdout_execution_blocked_by_definition_contract(contract)
    _assert_true(contract.get("status") == DEFINITION_ONLY_STATUS, "STATUS_MISMATCH")
    _assert_true(contract.get("verdict") == DEFINITION_ONLY_VERDICT, "VERDICT_MISMATCH")
    _assert_true(contract.get("hypothesis_id") == REQUIRED_HYPOTHESIS_ID, "HYPOTHESIS_ID_MISMATCH")
    _assert_true(
        contract.get("predecessor_hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "PREDECESSOR_HYPOTHESIS_ID_MISMATCH",
    )
    _assert_true(
        contract.get("hypothesis_id") != REQUIRED_PREDECESSOR_HYPOTHESIS_ID, "ID_MUST_DIFF_V8"
    )
    _assert_true(int(contract.get("hypothesis_count") or 0) == 1, "HYPOTHESIS_COUNT_MUST_BE_1")
    _assert_true(int(contract.get("multiple_testing_budget") or 0) == 1, "BUDGET_MUST_BE_1")
    _assert_true("holdout_run_count" in contract, "HOLDOUT_RUN_COUNT_MISSING")
    _assert_true(int(contract["holdout_run_count"]) == 0, "HOLDOUT_RUN_COUNT_MUST_BE_0")
    _assert_true(int(contract.get("holdout_run_limit") or 0) == 1, "HOLDOUT_RUN_LIMIT_MUST_BE_1")
    _assert_true(
        int(contract.get("holdout_runs_allowed") or 0) == 1, "HOLDOUT_RUNS_ALLOWED_MUST_BE_1"
    )

    for key in (
        "retry_forbidden",
        "restart_forbidden",
        "post_hoc_threshold_adjustment_forbidden",
        "post_result_tuning_forbidden",
        "optimization_forbidden",
        "variants_forbidden",
        "parameter_sweeps_forbidden",
        "repeat_after_result_inspection_forbidden",
        "reopen_after_terminal_result_forbidden_without_new_hypothesis_id",
        "frozen_v8_mechanism_match_required",
    ):
        _assert_true(contract.get(key) is True, f"LOCK_REQUIRED:{key}")

    _assert_true(
        contract.get("frozen_v8_contract_digest_required") == REQUIRED_V8_PREREGISTRATION_DIGEST,
        "V8_DIGEST_BINDING_MISMATCH",
    )
    _assert_true(contract.get("dataset_id") == REQUIRED_DATASET_ID, "DATASET_ID_MISMATCH")
    _assert_true(
        contract.get("sealed_holdout_id") == HOLDOUT_OPAQUE_ID, "SEALED_HOLDOUT_ID_MISMATCH"
    )
    _assert_true(
        contract.get("sealed_holdout_content_inspection_authorized") is False,
        "HOLDOUT_INSPECTION_MUST_BE_FALSE",
    )
    _assert_true(
        contract.get("holdout_content_inspection_in_this_slice") is False,
        "HOLDOUT_INSPECTION_IN_SLICE_MUST_BE_FALSE",
    )

    universe = contract.get("universe_scope") or {}
    _assert_true(universe.get("bitcoin_excluded") is True, "BTC_MUST_BE_EXCLUDED")
    _assert_true(universe.get("spot_excluded") is True, "SPOT_MUST_BE_EXCLUDED")
    _assert_true(universe.get("venue") == "OKX", "VENUE_MUST_BE_OKX")
    _assert_true(
        universe.get("instrument_class") == "LINEAR_USDT_PERPETUAL",
        "INSTRUMENT_CLASS_MISMATCH",
    )

    dev = contract.get("development_binding") or {}
    _assert_true(
        dev.get("development_hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID, "DEV_ID"
    )
    _assert_true(dev.get("development_result_class") == "PASS", "DEVELOPMENT_MUST_BE_PASS")
    _assert_true(
        dev.get("development_preregistration_digest") == REQUIRED_V8_PREREGISTRATION_DIGEST,
        "DEVELOPMENT_DIGEST_MISMATCH",
    )
    _assert_true(dev.get("development_split_intervals_sha256") == REQUIRED_DEV_SPLIT, "DEV_SPLIT")
    _assert_true(dev.get("second_development_run_forbidden") is True, "SECOND_DEV_FORBIDDEN")
    _assert_true(dev.get("v8_reopen_forbidden") is True, "V8_REOPEN_FORBIDDEN")
    _assert_true(dev.get("v8_rerun_forbidden") is True, "V8_RERUN_FORBIDDEN")
    _assert_true(dev.get("identical_mechanism_required") is True, "IDENTICAL_MECHANISM_REQUIRED")

    treatment = contract.get("treatment") or {}
    _assert_true(
        treatment.get("treatment_type") == "POST_ENTRY_EXIT_EFFICIENCY_MECHANISM",
        "TREATMENT_TYPE_INVALID",
    )
    _assert_true(treatment.get("identical_to_development_treatment") is True, "TREATMENT_MATCH")
    _assert_true(treatment.get("identical_to_v8_treatment") is True, "TREATMENT_V8_MATCH")
    for key in (
        "no_new_direction_authority",
        "no_new_switch_authority",
        "no_new_risk_authority",
        "no_new_sizing_authority",
        "no_new_execution_authority",
    ):
        _assert_true(treatment.get(key) is True, f"AUTHORITY_LOCK:{key}")
    _assert_true(treatment.get("runtime_implementation_in_this_slice") is False, "RUNTIME_IMPL")

    mechanism = contract.get("exit_mechanism") or {}
    _assert_true(mechanism.get("mechanism_id") == REQUIRED_MECHANISM_ID, "MECHANISM_ID_MISMATCH")
    frozen = mechanism.get("frozen_parameters") or {}
    for key, value in REQUIRED_FROZEN_PARAMETERS.items():
        _assert_true(frozen.get(key) == value, f"FROZEN_PARAM_MISMATCH:{key}")
    cooldown = mechanism.get("cooldown") or {}
    _assert_true(
        int(cooldown.get("cooldown_bars") or -1) == REQUIRED_COOLDOWN_BARS, "COOLDOWN_BARS"
    )
    _assert_true(
        int(cooldown.get("cooldown_hours") or -1) == REQUIRED_COOLDOWN_BARS, "COOLDOWN_HOURS"
    )

    cost = contract.get("cost_model") or {}
    _assert_true(float(cost.get("fee_bps")) == 10.0, "FEE_BPS")
    _assert_true(float(cost.get("slippage_bps")) == 5.0, "SLIPPAGE_BPS")
    _assert_true(float(cost.get("cost_multiplier")) == 1.0, "COST_MULTIPLIER")

    splits = contract.get("splits") or {}
    expected_split = materialize_holdout_split_definition()
    _assert_true(
        splits.get("holdout_split_definition") == expected_split, "SPLIT_DEFINITION_MISMATCH"
    )
    _assert_true(
        splits.get("split_intervals_sha256") == EXPECTED_HOLDOUT_SPLIT_DIGEST,
        "SPLIT_DIGEST_MISMATCH",
    )
    _assert_true(
        expected_holdout_split_digest() == EXPECTED_HOLDOUT_SPLIT_DIGEST, "SPLIT_DIGEST_DRIFT"
    )

    dig = compute_holdout_preregistration_digest(contract)
    _assert_true(dig == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST, "PREREG_DIGEST_MISMATCH")
    _assert_true(
        contract.get("holdout_preregistration_digest") == EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
        "PREREG_DIGEST_FIELD_MISMATCH",
    )
    _assert_true(
        contract.get("next_canonical_step") == DEFINITION_ONLY_NEXT_CANONICAL_STEP,
        "NEXT_STEP_MISMATCH",
    )

    promo = contract.get("promotion_and_economic_gate_policy") or {}
    _assert_true(promo.get("promotion_eligible") is False, "PROMOTION_ELIGIBLE")
    _assert_true(promo.get("economic_gate_open") is False, "ECONOMIC_GATE_OPEN")
    _assert_true(
        promo.get("economic_validity_offline_gate_pass") is False,
        "ECONOMIC_GATE_PASS",
    )

    runtime = contract.get("runtime_policy") or {}
    for key in (
        "runtime_activated",
        "shadow_activated",
        "paper_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
    ):
        _assert_true(runtime.get(key) is False, f"RUNTIME_UNLOCKED:{key}")

    targets = contract.get("declared_future_evaluation_targets") or {}
    _assert_true(targets.get("authorized_in_this_slice") is False, "FUTURE_TARGETS_AUTHORIZED")

    policy = contract.get("development_contract_holdout_policy_unchanged") or {}
    _assert_true(policy.get("development_contract_ref") == DEV_CONTRACT_REL_PATH, "DEV_REF")
    _assert_true(
        policy.get("v8_identity_holdout_evaluation_forbidden") is True, "V8_HOLDOUT_FORBIDDEN"
    )

    if development_contract is not None:
        _assert_true(
            development_contract.get("hypothesis_id") == REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
            "DEV_CONTRACT_ID",
        )
        _assert_true(development_contract.get("holdout_allowed") is False, "DEV_HOLDOUT_ALLOWED")
        _assert_true(development_contract.get("holdout_forbidden") is True, "DEV_HOLDOUT_FORBIDDEN")
        mech = (development_contract.get("exit_mechanism") or {}).get("mechanism_id")
        _assert_true(mech == REQUIRED_MECHANISM_ID, "DEV_MECHANISM_MISMATCH")
        frozen_dev = (development_contract.get("exit_mechanism") or {}).get(
            "frozen_parameters"
        ) or {}
        for key, value in REQUIRED_FROZEN_PARAMETERS.items():
            _assert_true(frozen_dev.get(key) == value, f"DEV_FROZEN_DRIFT:{key}")
        _assert_true(
            mechanism.get("frozen_parameters") == frozen_dev,
            "HOLDOUT_VS_V8_FROZEN_DRIFT",
        )
        _assert_true(
            (development_contract.get("exit_mechanism") or {}).get("cooldown")
            == mechanism.get("cooldown"),
            "HOLDOUT_VS_V8_COOLDOWN_DRIFT",
        )

    return {
        "valid": True,
        "definition_only": True,
        "holdout_executed": False,
        "hypothesis_id": REQUIRED_HYPOTHESIS_ID,
        "predecessor_hypothesis_id": REQUIRED_PREDECESSOR_HYPOTHESIS_ID,
        "mechanism_id": REQUIRED_MECHANISM_ID,
        "holdout_run_count": 0,
        "holdout_run_limit": 1,
        "execution_authorized": False,
        "holdout_split_digest": EXPECTED_HOLDOUT_SPLIT_DIGEST,
        "holdout_preregistration_digest": EXPECTED_HOLDOUT_PREREGISTRATION_DIGEST,
        "v8_preregistration_digest": REQUIRED_V8_PREREGISTRATION_DIGEST,
        "frozen_mechanism_match": True,
    }


def load_and_validate_repo_holdout_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root if repo_root is not None else _repo_root()
    contract = load_json(root / CONTRACT_REL_PATH)
    development = load_json(root / DEV_CONTRACT_REL_PATH)
    return validate_holdout_preregistration_contract(contract, development_contract=development)
