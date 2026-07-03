"""Cross-sectional ranking semantics declarative binding schema (v0).

Pure offline schema materialization for ratified policy classes. Does not compute
scores, rank instruments, run backtests, or authorize runtime execution.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from enum import Enum
from typing import Any, Mapping

PACKAGE_MARKER = "CROSS_SECTIONAL_RANKING_SEMANTICS_BINDING_V0=true"
SCHEMA_VERSION = "cross_sectional_ranking_semantics_binding.v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"

# Ratified policy class values (immutable for v0 materialization).
SCORE_FAMILY_POLICY = "volatility_normalized_fixed_lookback_return"
DIRECTION_POLICY = "symmetric_top1_sign"
NEGATIVE_TOP1_MEANS = "SHORT_TOP1"
BOTTOM1_SELECTION_ALLOWED = False
ZERO_SCORE_TARGET = "FLAT"
NON_FINITE_SCORE_TARGET = "FLAT"
WARMUP_INCOMPLETE_TARGET = "FLAT"
PANEL_INSUFFICIENT_TARGET = "FLAT"

SIGNAL_TIMING_POLICY = "finalized_bar_close_epoch"
MINIMUM_SIGNAL_LAG_BARS = 1
SAME_BAR_EXECUTION_ALLOWED = False

REBALANCE_POLICY_CLASS = "fixed_N_bar_cadence"

SWITCH_POLICY = "flat_then_wait_one_epoch_then_enter"
OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT = True
ATOMIC_SIDE_SWITCH_ALLOWED = False

COOLDOWN_POLICY = "no_cooldown"
MINIMUM_HOLD_POLICY = "until_next_rebalance"
RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD = True

PANEL_COMPLETENESS_POLICY = "per_instrument_eligibility_mask"
MINIMUM_ELIGIBLE_COUNT_REQUIRED = True

MISSING_BAR_POLICY = "exclude_non_selected_instrument_for_epoch"
SELECTED_INSTRUMENT_MISSING_ACTION = "FORCE_FLAT"
BAR_CARRY_FORWARD_ALLOWED = False

TIE_BREAK_POLICY = "score_desc_then_instrument_id_asc"
TIE_BREAK_SCORE_SOURCE = "unrounded_internal_score"

THRESHOLD_POLICY = "sign_boundary_only"
NUMERIC_STRENGTH_THRESHOLD_INITIAL = False

ORCHESTRATOR_OWNER = "cross_sectional_single_slot_research_orchestrator_v0"
ORCHESTRATOR_SCOPE = "RESEARCH_ONLY"

NUMERIC_BINDING_KEYS = (
    "lookback_N",
    "vol_window_V",
    "vol_epsilon",
    "vol_return_method",
    "rebalance_interval_bars",
    "signal_lag_bars",
    "min_eligible_members_for_rank",
    "switch_entry_delay_epochs",
    "max_bar_staleness_bars",
    "min_abs_score_strength",
)

EXTERNAL_BINDING_KEYS = (
    "pit_universe_manifest_ref",
    "instrument_id_canonicalization_version",
    "panel_ohlcv_dataset_manifest_ref",
    "admissibility_manifest_ref",
    "evaluation_period_binding",
    "fee_model_version",
    "slippage_model_version",
    "funding_model_version",
    "spread_model_version",
    "execution_model_version",
)

DIGEST_BINDING_KEYS = (
    "implementation_digest",
    "config_digest",
    "data_digest",
)

RATIFICATION_PAYLOAD_VERSION = "cross_sectional_ranking_semantics_operator_ratification_payload.v0"
VERSIONED_BINDING_ARTIFACT_KIND = "cross_sectional_ranking_semantics_versioned_binding"
VERSIONED_BINDING_ARTIFACT_VERSION = "v0"
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_relative_strength_non_bitcoin_perpetuals_v0_"
    "ranking_semantics_binding_v0.json"
)

RATIFIED_OPERATOR_BINDING_VALUES: dict[str, int | float | str] = {
    "lookback_N": 20,
    "vol_window_V": 20,
    "vol_epsilon": 1e-8,
    "rebalance_interval_bars": 1,
    "signal_lag_bars": 1,
    "min_eligible_members_for_rank": 5,
    "switch_entry_delay_epochs": 1,
    "max_bar_staleness_bars": 1,
    "vol_return_method": "log_return",
}

RATIFIED_OPERATOR_RATIONALES: dict[str, str] = {
    "lookback_N": (
        "Ein festes Fenster von 20 finalisierten Trading-Epochen bindet eine "
        "ausreichend begrenzte mittlere Momentum-Historie, ohne einen impliziten "
        "oder adaptiven Default zuzulassen. Die Wahl ist eine neue "
        "Operator-Policy-Bindung und keine automatische Übernahme aus momentum.py."
    ),
    "vol_window_V": (
        "Die Volatilitätsschätzung verwendet ein gleich langes, explizit "
        "versioniertes Fenster wie die Ranking-Historie. Dadurch bleiben "
        "Zeitbasis und Normalisierung nachvollziehbar. Die Wahl ist keine "
        "automatische Übernahme aus vol_regime_filter.py."
    ),
    "vol_epsilon": (
        "Ein strikt positiver numerischer Floor von 1e-8 verhindert Division "
        "durch null beziehungsweise numerisch instabile Skalierung, ohne normale "
        "Volatilitätswerte materiell zu übersteuern."
    ),
    "rebalance_interval_bars": (
        "Das Ranking wird in jeder finalisierten Trading-Epoche neu berechnet. "
        "Order-, Runtime- oder Execution-Wirkung entsteht daraus nicht. Die Wahl "
        "ist eine explizite Operator-Bindung und keine automatische Übernahme aus "
        "backtest/engine.py."
    ),
    "signal_lag_bars": (
        "Ein vollständiger Bar Lag verhindert Look-ahead und bindet Signale "
        "ausschließlich an Informationen, die vor der bewerteten Trading-Epoche "
        "final verfügbar waren."
    ),
    "min_eligible_members_for_rank": (
        "Ein Cross-Sectional Ranking ist nur bei mindestens fünf gleichzeitig "
        "zulässigen Futures-Mitgliedern gültig. Kleinere Querschnitte werden "
        "fail-closed blockiert, statt ein instabiles oder faktisch paarweises "
        "Ranking zu erzeugen."
    ),
    "switch_entry_delay_epochs": (
        "Nach einem Ranking- beziehungsweise Selektionswechsel ist mindestens "
        "eine vollständig finalisierte Trading-Epoche abzuwarten. Dies reduziert "
        "unmittelbares Umschalten und erzeugt keine Reversal-, Order- oder "
        "Runtime-Authority."
    ),
    "max_bar_staleness_bars": (
        "Es wird höchstens eine Bar zeitlicher Rückstand toleriert. Ältere "
        "Mitglieder werden als nicht zulässig behandelt und dürfen weder Ranking "
        "noch Selektion speisen."
    ),
    "vol_return_method": (
        "Die Volatilitätsnormalisierung verwendet logarithmische "
        "Einperiodenrenditen aus finalisierten Bars. Die Methode ist explizit "
        "gebunden, dimensionslos und symmetrisch für positive und negative "
        "Preisbewegungen. Sie ist keine Übernahme eines adjacent Default-Werts."
    ),
}

ATTESTED_OPERATOR_DECISION_DIGEST = (
    "82e4a28813d72f6b9f54db15cb5729763648bc148f6eac3b445be6dab6cc107a"
)

ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND = "REQUIRED_UNBOUND_DIGEST"


class BindingFieldStatus(str, Enum):
    REQUIRED_UNBOUND = "REQUIRED_UNBOUND"
    BOUND = "BOUND"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AggregateBindingStatus(str, Enum):
    BOUND = "BOUND"
    REQUIRED_UNBOUND = "REQUIRED_UNBOUND"
    INCOMPLETE_FAIL_CLOSED = "INCOMPLETE_FAIL_CLOSED"
    COMPLETE = "COMPLETE"


def _field(
    status: BindingFieldStatus,
    *,
    value: Any = None,
    ref: str = "",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"status": status.value}
    if value is not None:
        payload["value"] = value
    if ref:
        payload["ref"] = ref
    return payload


def materialize_cross_sectional_ranking_semantics_binding_v0() -> dict[str, Any]:
    """Materialize ratified policy classes with fail-closed unbound numeric/external fields."""
    numeric_bindings: dict[str, dict[str, Any]] = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in NUMERIC_BINDING_KEYS
    }
    numeric_bindings["min_abs_score_strength"] = _field(BindingFieldStatus.NOT_APPLICABLE)

    external_bindings = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in EXTERNAL_BINDING_KEYS
    }
    digest_bindings = {
        key: _field(BindingFieldStatus.REQUIRED_UNBOUND) for key in DIGEST_BINDING_KEYS
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "policy_classes": {
            "score_family_policy": SCORE_FAMILY_POLICY,
            "direction_policy": DIRECTION_POLICY,
            "signal_timing_policy": SIGNAL_TIMING_POLICY,
            "rebalance_policy_class": REBALANCE_POLICY_CLASS,
            "switch_policy": SWITCH_POLICY,
            "cooldown_policy": COOLDOWN_POLICY,
            "minimum_hold_policy": MINIMUM_HOLD_POLICY,
            "panel_completeness_policy": PANEL_COMPLETENESS_POLICY,
            "missing_bar_policy": MISSING_BAR_POLICY,
            "tie_break_policy": TIE_BREAK_POLICY,
            "threshold_policy": THRESHOLD_POLICY,
        },
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
        },
        "direction_semantics": {
            "selection_mode": "single_top1_by_score_desc",
            "ascending_rank_for_short_selection_forbidden": True,
            "bottom1_selection_allowed": BOTTOM1_SELECTION_ALLOWED,
            "dual_rank_forbidden": True,
            "negative_top1_means": NEGATIVE_TOP1_MEANS,
            "positive_top1_means": "LONG_TOP1",
            "zero_score_target": ZERO_SCORE_TARGET,
            "non_finite_score_target": NON_FINITE_SCORE_TARGET,
            "warmup_incomplete_target": WARMUP_INCOMPLETE_TARGET,
            "panel_insufficient_target": PANEL_INSUFFICIENT_TARGET,
        },
        "timing_semantics": {
            "decision_input": "finalized_bars_only",
            "score_epoch": "finalized_bar_close",
            "minimum_signal_lag_bars": MINIMUM_SIGNAL_LAG_BARS,
            "same_bar_execution": SAME_BAR_EXECUTION_ALLOWED,
            "finalized_bar_required": True,
            "pit_universe_at_score_epoch": True,
            "immutable_score_ledger": True,
        },
        "switch_semantics": {
            "switch_policy": SWITCH_POLICY,
            "opposite_side_requires_reconciled_flat": OPPOSITE_SIDE_REQUIRES_RECONCILED_FLAT,
            "flat_then_wait_one_epoch_then_enter": True,
            "atomic_side_switch": ATOMIC_SIDE_SWITCH_ALLOWED,
        },
        "missing_bar_semantics": {
            "missing_bar_policy": MISSING_BAR_POLICY,
            "non_selected_missing": "exclude_for_epoch",
            "selected_missing": SELECTED_INSTRUMENT_MISSING_ACTION.lower(),
            "carry_forward": BAR_CARRY_FORWARD_ALLOWED,
        },
        "panel_semantics": {
            "eligibility_mode": PANEL_COMPLETENESS_POLICY,
            "minimum_eligible_member_count_required": MINIMUM_ELIGIBLE_COUNT_REQUIRED,
            "insufficient_panel_action": "flat",
        },
        "minimum_hold_semantics": {
            "default_hold": MINIMUM_HOLD_POLICY,
            "risk_exit_override": RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD,
            "safety_exit_override": RISK_AND_SAFETY_EXITS_OVERRIDE_MINIMUM_HOLD,
        },
        "tie_break_semantics": {
            "primary_order": "score_desc",
            "secondary_order": "instrument_id_asc",
            "score_representation": TIE_BREAK_SCORE_SOURCE,
            "tie_break_policy": TIE_BREAK_POLICY,
        },
        "threshold_semantics": {
            "threshold_policy": THRESHOLD_POLICY,
            "numeric_strength_threshold_initial": NUMERIC_STRENGTH_THRESHOLD_INITIAL,
        },
        "orchestrator": {
            "owner": ORCHESTRATOR_OWNER,
            "scope": ORCHESTRATOR_SCOPE,
        },
        "numeric_bindings": numeric_bindings,
        "external_bindings": external_bindings,
        "digest_bindings": digest_bindings,
        "binding_status": {
            "policy_classes_status": AggregateBindingStatus.BOUND.value,
            "numeric_bindings_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "universe_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "dataset_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "period_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "cost_model_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "digest_binding_status": AggregateBindingStatus.REQUIRED_UNBOUND.value,
            "overall_binding_status": AggregateBindingStatus.INCOMPLETE_FAIL_CLOSED.value,
        },
    }


def build_operator_decision_digest_input_v0(
    operator_values: Mapping[str, int | float | str] | None = None,
    operator_rationales: Mapping[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build canonical operator-decision digest payload (sorted slot keys)."""
    values = dict(operator_values or RATIFIED_OPERATOR_BINDING_VALUES)
    rationales = dict(operator_rationales or RATIFIED_OPERATOR_RATIONALES)
    missing = sorted(set(values) - set(rationales))
    if missing:
        raise ValueError(f"missing operator rationales for slots: {missing}")
    return {key: {"value": values[key], "rationale": rationales[key]} for key in sorted(values)}


def compute_operator_decision_digest_v0(
    operator_values: Mapping[str, int | float | str] | None = None,
    operator_rationales: Mapping[str, str] | None = None,
) -> str:
    """SHA-256 digest of ratified operator slot values and rationales."""
    digest_input = build_operator_decision_digest_input_v0(
        operator_values=operator_values,
        operator_rationales=operator_rationales,
    )
    canonical = json.dumps(
        digest_input,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_minimum_history_bars_v0(
    lookback_n: int,
    vol_window_v: int,
    signal_lag_bars: int,
) -> int:
    return max(lookback_n, vol_window_v) + signal_lag_bars


def apply_ratified_operator_bindings_v0(binding: dict[str, Any]) -> dict[str, Any]:
    """Apply ratified operator numeric/enum bindings to a materialized binding."""
    result = deepcopy(binding)
    numeric = result["numeric_bindings"]
    for key, value in RATIFIED_OPERATOR_BINDING_VALUES.items():
        numeric[key] = _field(BindingFieldStatus.BOUND, value=value)
    numeric["min_abs_score_strength"] = _field(BindingFieldStatus.NOT_APPLICABLE)
    status = result["binding_status"]
    status["numeric_bindings_status"] = AggregateBindingStatus.BOUND.value
    status["overall_binding_status"] = AggregateBindingStatus.INCOMPLETE_FAIL_CLOSED.value
    return result


def build_envelope_digests_v0(
    operator_decision_digest: str,
) -> dict[str, dict[str, Any]]:
    return {
        "operator_decision_digest": {
            "status": BindingFieldStatus.BOUND.value,
            "value": operator_decision_digest,
        },
        "semantic_digest": {"status": ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND},
        "config_digest": {"status": ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND},
        "manifest_digest": {"status": ENVELOPE_DIGEST_STATUS_REQUIRED_UNBOUND},
    }


def compute_derived_binding_fields_v0(
    operator_values: Mapping[str, int | float | str] | None = None,
) -> dict[str, int]:
    values = dict(operator_values or RATIFIED_OPERATOR_BINDING_VALUES)
    lookback_n = int(values["lookback_N"])
    vol_window_v = int(values["vol_window_V"])
    signal_lag_bars = int(values["signal_lag_bars"])
    return {
        "minimum_history_bars": compute_minimum_history_bars_v0(
            lookback_n,
            vol_window_v,
            signal_lag_bars,
        ),
        "turnover_cadence_bars": int(values["rebalance_interval_bars"]),
    }


def materialize_versioned_cross_sectional_ranking_semantics_binding_v0() -> dict[str, Any]:
    """Materialize versioned research binding envelope with ratified operator slots."""
    binding = apply_ratified_operator_bindings_v0(
        materialize_cross_sectional_ranking_semantics_binding_v0()
    )
    operator_digest = compute_operator_decision_digest_v0()
    if operator_digest != ATTESTED_OPERATOR_DECISION_DIGEST:
        raise ValueError(
            "operator decision digest mismatch: "
            f"computed={operator_digest} attested={ATTESTED_OPERATOR_DECISION_DIGEST}"
        )
    return {
        "artifact_kind": VERSIONED_BINDING_ARTIFACT_KIND,
        "artifact_version": VERSIONED_BINDING_ARTIFACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "ratification_payload_version": RATIFICATION_PAYLOAD_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "materialization_scope": "NUMERIC_ENUM_RATIFICATION_ONLY",
        "non_authorizing": True,
        "research_binding_only": True,
        "scope_classification": {
            "candidate_binding_effect": "NONE",
            "fleet_binding_effect": "NONE",
            "universe_binding_effect": "DEFERRED_UPSTREAM",
            "economic_policy_effect": "NONE",
            "runtime_effect": "NONE",
        },
        "envelope_digests": build_envelope_digests_v0(operator_digest),
        "derived_fields": compute_derived_binding_fields_v0(),
        "binding": binding,
    }


def serialize_versioned_binding_artifact_json_v0(
    envelope: Mapping[str, Any],
) -> str:
    """Serialize versioned binding artifact with stable key order and indentation."""
    return json.dumps(dict(envelope), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def compute_config_digest_v0(canonical_json_bytes: bytes) -> str:
    return hashlib.sha256(canonical_json_bytes).hexdigest()


def clone_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(binding))
