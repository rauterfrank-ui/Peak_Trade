"""Authority / consumer matrix for Cap 6.3 decision-config candidates."""

from __future__ import annotations

from typing import Any

from src.ops.decision_config_ownership_and_consumer_closure_v1.config_loader_v1 import (
    load_canonical_decision_runtime_config_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CONFIG_VERSION,
    EXPECTED_ADVERSE_EXIT_DISTANCE,
    EXPECTED_CONFIRMATION_EPOCHS,
    EXPECTED_REVERSAL_DISTANCE,
    EXPECTED_UP_DISTANCE,
    OWNER,
    PRODUCTIVE_DECISION_OWNER,
    PRODUCTIVE_HOST,
    REVIEW_FEE_RATE_BPS,
    REVIEW_PRICE_PATH_MAX_LEN,
    REVIEW_SLIPPAGE_BPS,
)


def build_config_authority_matrix_v1() -> list[dict[str, Any]]:
    cfg = load_canonical_decision_runtime_config_v1()
    digest = cfg.config_digest()
    migrated = (
        (
            "confirmation_epochs",
            EXPECTED_CONFIRMATION_EPOCHS,
            int(cfg.confirmation_epochs),
            "CANONICAL_RUNTIME_CONFIG",
            True,
            "bridge_local_and_policy_hardcode_confirmed_drift",
            "bridge_local_hardcode_or_default_arg",
            "fail_closed_missing_key_no_default",
        ),
        (
            "up_distance",
            EXPECTED_UP_DISTANCE,
            float(cfg.up_distance),
            "CANONICAL_RUNTIME_CONFIG",
            True,
            "bridge_and_cap62_frozen_local_ownership_confirmed_drift",
            "bridge_or_cap62_frozen_constant",
            "fail_closed_missing_key_no_default",
        ),
        (
            "adverse_exit_distance",
            EXPECTED_ADVERSE_EXIT_DISTANCE,
            float(cfg.adverse_exit_distance),
            "CANONICAL_RUNTIME_CONFIG",
            True,
            "bridge_and_cap62_frozen_local_ownership_confirmed_drift",
            "bridge_or_cap62_frozen_constant",
            "fail_closed_missing_key_no_default",
        ),
        (
            "reversal_distance",
            EXPECTED_REVERSAL_DISTANCE,
            float(cfg.reversal_distance),
            "CANONICAL_RUNTIME_CONFIG",
            True,
            "bridge_and_cap62_frozen_local_ownership_confirmed_drift",
            "bridge_or_cap62_frozen_constant",
            "fail_closed_missing_key_no_default",
        ),
    )
    rows: list[dict[str, Any]] = []
    for (
        key,
        before_value,
        after_value,
        classification,
        migration_required,
        migration_reason,
        fallback_before,
        fallback_after,
    ) in migrated:
        rows.append(
            {
                "CONFIG_KEY": key,
                "CURRENT_OWNER": (
                    "ops.dynamic_scope_persistence_binding_v1.constants_v1"
                    if key != "confirmation_epochs"
                    else (
                        "ops.wallclock_full_canonical_decision_to_simulated_economics_"
                        "runtime_bridge_v1.decision_economics_cycle_bridge_v1"
                    )
                ),
                "CURRENT_DEFINITION_LOCATION": (
                    "src/ops/dynamic_scope_persistence_binding_v1/constants_v1.py"
                    if key != "confirmation_epochs"
                    else (
                        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_"
                        "runtime_bridge_v1/decision_economics_cycle_bridge_v1.py"
                    )
                ),
                "CURRENT_EFFECTIVE_VALUE": before_value,
                "CURRENT_PRODUCTIVE_CONSUMER": PRODUCTIVE_HOST,
                "TARGET_OWNER": AUTHORITY_OWNER,
                "VALUE_CLASSIFICATION": classification,
                "TARGET_PRODUCTIVE_CONSUMER": PRODUCTIVE_HOST,
                "FALLBACK_BEHAVIOR_BEFORE": fallback_before,
                "FALLBACK_BEHAVIOR_AFTER": fallback_after,
                "CONFIG_VERSION_BINDING": CONFIG_VERSION,
                "CONFIG_DIGEST_BINDING": digest,
                "CORE_LOGIC_EFFECT": "NONE",
                "MIGRATION_REQUIRED": migration_required,
                "MIGRATION_REASON": migration_reason,
                "FINAL_EFFECTIVE_VALUE": after_value,
                "PRODUCTIVE_DECISION_OWNER": PRODUCTIVE_DECISION_OWNER,
            }
        )

    # Review-only: no productive ownership gap / fallback ambiguity requiring migration.
    rows.append(
        {
            "CONFIG_KEY": "PRICE_PATH_MAX_LEN",
            "CURRENT_OWNER": (
                "ops.wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_v1.constants_v1"
            ),
            "CURRENT_DEFINITION_LOCATION": (
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_v1/constants_v1.py"
            ),
            "CURRENT_EFFECTIVE_VALUE": REVIEW_PRICE_PATH_MAX_LEN,
            "CURRENT_PRODUCTIVE_CONSUMER": PRODUCTIVE_HOST,
            "TARGET_OWNER": (
                "ops.wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_v1.constants_v1"
            ),
            "VALUE_CLASSIFICATION": "IMMUTABLE_DOMAIN_CONSTANT",
            "TARGET_PRODUCTIVE_CONSUMER": PRODUCTIVE_HOST,
            "FALLBACK_BEHAVIOR_BEFORE": "module_constant_no_fallback_ambiguity",
            "FALLBACK_BEHAVIOR_AFTER": "unchanged_module_constant",
            "CONFIG_VERSION_BINDING": "n/a_not_migrated",
            "CONFIG_DIGEST_BINDING": "n/a_not_migrated",
            "CORE_LOGIC_EFFECT": "NONE",
            "MIGRATION_REQUIRED": False,
            "MIGRATION_REASON": (
                "single_clear_host_buffer_constant_no_productive_ownership_gap_"
                "or_fallback_ambiguity"
            ),
            "FINAL_EFFECTIVE_VALUE": REVIEW_PRICE_PATH_MAX_LEN,
            "PRODUCTIVE_DECISION_OWNER": PRODUCTIVE_DECISION_OWNER,
        }
    )
    rows.append(
        {
            "CONFIG_KEY": "fee_rate_bps",
            "CURRENT_OWNER": (
                "ops.integrated_paper_shadow_observation_session_v1."
                "portfolio_economics_model_v1.PortfolioEconomicsModelParamsV1"
            ),
            "CURRENT_DEFINITION_LOCATION": (
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_hardening_v2/forced_wiring_fixture_v2.py"
            ),
            "CURRENT_EFFECTIVE_VALUE": REVIEW_FEE_RATE_BPS,
            "CURRENT_PRODUCTIVE_CONSUMER": (
                "analytical_portfolio_economics_params_not_decision_path_owner"
            ),
            "TARGET_OWNER": (
                "ops.integrated_paper_shadow_observation_session_v1."
                "portfolio_economics_model_v1.PortfolioEconomicsModelParamsV1"
            ),
            "VALUE_CLASSIFICATION": "EXECUTION_MODEL_CONFIG",
            "TARGET_PRODUCTIVE_CONSUMER": (
                "analytical_portfolio_economics_params_not_decision_path_owner"
            ),
            "FALLBACK_BEHAVIOR_BEFORE": "explicit_fixture_or_params_construction",
            "FALLBACK_BEHAVIOR_AFTER": "unchanged_not_migrated",
            "CONFIG_VERSION_BINDING": "n/a_not_migrated",
            "CONFIG_DIGEST_BINDING": "n/a_not_migrated",
            "CORE_LOGIC_EFFECT": "NONE",
            "MIGRATION_REQUIRED": False,
            "MIGRATION_REASON": (
                "not_on_productive_decision_config_path_no_confirmed_decision_drift"
            ),
            "FINAL_EFFECTIVE_VALUE": REVIEW_FEE_RATE_BPS,
            "PRODUCTIVE_DECISION_OWNER": PRODUCTIVE_DECISION_OWNER,
        }
    )
    rows.append(
        {
            "CONFIG_KEY": "slippage_bps",
            "CURRENT_OWNER": (
                "ops.integrated_paper_shadow_observation_session_v1."
                "portfolio_economics_model_v1.PortfolioEconomicsModelParamsV1"
            ),
            "CURRENT_DEFINITION_LOCATION": (
                "src/ops/wallclock_full_canonical_decision_to_simulated_economics_"
                "runtime_bridge_hardening_v2/forced_wiring_fixture_v2.py"
            ),
            "CURRENT_EFFECTIVE_VALUE": REVIEW_SLIPPAGE_BPS,
            "CURRENT_PRODUCTIVE_CONSUMER": (
                "analytical_portfolio_economics_params_not_decision_path_owner"
            ),
            "TARGET_OWNER": (
                "ops.integrated_paper_shadow_observation_session_v1."
                "portfolio_economics_model_v1.PortfolioEconomicsModelParamsV1"
            ),
            "VALUE_CLASSIFICATION": "EXECUTION_MODEL_CONFIG",
            "TARGET_PRODUCTIVE_CONSUMER": (
                "analytical_portfolio_economics_params_not_decision_path_owner"
            ),
            "FALLBACK_BEHAVIOR_BEFORE": "explicit_fixture_or_params_construction",
            "FALLBACK_BEHAVIOR_AFTER": "unchanged_not_migrated",
            "CONFIG_VERSION_BINDING": "n/a_not_migrated",
            "CONFIG_DIGEST_BINDING": "n/a_not_migrated",
            "CORE_LOGIC_EFFECT": "NONE",
            "MIGRATION_REQUIRED": False,
            "MIGRATION_REASON": (
                "not_on_productive_decision_config_path_no_confirmed_decision_drift"
            ),
            "FINAL_EFFECTIVE_VALUE": REVIEW_SLIPPAGE_BPS,
            "PRODUCTIVE_DECISION_OWNER": PRODUCTIVE_DECISION_OWNER,
        }
    )
    return rows


def build_definition_to_consumer_trace_v1() -> list[dict[str, Any]]:
    cfg = load_canonical_decision_runtime_config_v1()
    return [
        {
            "config_key": key,
            "definition_owner": OWNER,
            "definition_path": cfg.source_path,
            "productive_consumer": PRODUCTIVE_HOST,
            "decision_owner": PRODUCTIVE_DECISION_OWNER,
            "effective_value": value,
            "config_digest": cfg.config_digest(),
            "config_version": cfg.config_version,
        }
        for key, value in (
            ("confirmation_epochs", int(cfg.confirmation_epochs)),
            ("up_distance", float(cfg.up_distance)),
            ("adverse_exit_distance", float(cfg.adverse_exit_distance)),
            ("reversal_distance", float(cfg.reversal_distance)),
        )
    ]


def inventory_decision_config_authority_surfaces_v1() -> dict[str, Any]:
    matrix = build_config_authority_matrix_v1()
    migrated = [r for r in matrix if r["MIGRATION_REQUIRED"] is True]
    not_migrated = [r for r in matrix if r["MIGRATION_REQUIRED"] is False]
    return {
        "owner": OWNER,
        "authority_owner": AUTHORITY_OWNER,
        "parallel_config_authority_created": False,
        "core_logic_changed": False,
        "migrated_keys": [r["CONFIG_KEY"] for r in migrated],
        "not_migrated_keys": [r["CONFIG_KEY"] for r in not_migrated],
        "silent_fallback_allowed": False,
        "one_owner_per_migrated_runtime_value": True,
    }
