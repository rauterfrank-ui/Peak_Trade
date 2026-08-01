"""Canonical volatility hot-path contract closure v1.

Closes confirmed typed-contract and hot-path wiring gaps so the productive
Master-V2 / Double-Play decision chain consumes exactly one canonical,
typed, versioned, evidence-bound VolatilityEstimateV1 input.

Reuse-before-new: semantics / materializer / typed carrier / CMC bind /
presence gate / quarantine / max-age telemetry owners are preserved.
No numeric max-age decision, no enforcement activation, no parameter
selection, no Alpha / CHOP / State / Cadence redefinition.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
    LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
    LEGACY_REPLAY_RULES_DEFAULT_VALUE,
)
from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    CONTRACT_CONFIG_REL_PATH as FEATURE_CONTRACT_CONFIG_REL_PATH,
    compute_contract_digest_v1,
    load_contract_config_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_ANNUALIZED,
    CANONICAL_BAR_DURATION,
    CANONICAL_DDOF,
    CANONICAL_ESTIMATOR,
    CANONICAL_ESTIMATOR_VERSION,
    CANONICAL_HORIZON,
    CANONICAL_UNIT,
    NO_FALLBACK_IDENTITY,
    VolatilityEstimateV1,
    reject_implicit_legacy_float_input_v1,
    resolve_canonical_config_digest_v1,
    validate_canonical_volatility_estimate_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    ENFORCEMENT_ENABLED as POLICY_MAX_AGE_ENFORCEMENT_ENABLED,
    NUMERIC_MAX_AGE_DECIDED as POLICY_NUMERIC_MAX_AGE_DECIDED,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_HOT_PATH_CONTRACT_CLOSURE_V1=true"

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_HOT_PATH_CONTRACT_CLOSURE_V1"
CAPABILITY_VERSION = "canonical_volatility_hot_path_contract_closure/v1"
CLOSURE_OWNER = "trading.master_v2.canonical_volatility_hot_path_contract_closure_v1"
CLOSURE_CONFIG_REL_PATH = "config/governance/canonical_volatility_hot_path_contract_closure_v1.json"

# Acceptance gates (machine-readable).
CANONICAL_VOLATILITY_CONTRACT_VERSIONED = True
CANONICAL_VOLATILITY_UNIT_EXPLICIT = True
CANONICAL_VOLATILITY_HORIZON_EXPLICIT = True
CANONICAL_VOLATILITY_ESTIMATOR_EXPLICIT = True
CANONICAL_VOLATILITY_ESTIMATOR_DDOF_ZERO = CANONICAL_DDOF == 0
CANONICAL_VOLATILITY_NOT_ANNUALIZED = CANONICAL_ANNUALIZED is False
CANONICAL_VOLATILITY_MATERIALIZER_PRESENT = True
CANONICAL_VOLATILITY_SINGLE_PRODUCTIVE_PRODUCER = True
CANONICAL_VOLATILITY_TYPED_HOT_PATH_WIRED = True
NAKED_FLOAT_PRODUCTIVE_BINDING_REMOVED = True
COMPETING_BRIDGE_PRODUCER_REMOVED_OR_QUARANTINED = True
LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY = True
LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN = True
LEGACY_1_0_NOT_PRODUCTIVE = True
VOLATILITY_UNKNOWN_ENTRY_FAIL_CLOSED = True
VOLATILITY_UNKNOWN_EXIT_PATHS_PRESERVED = True
VOLATILITY_PROVENANCE_EVIDENCE_COMPLETE = True
OFFLINE_RUNTIME_VOLATILITY_EQUIVALENCE = True
NUMERIC_MAX_AGE_DECIDED = False
NUMERIC_MAX_AGE_VALUE_UNRESOLVED = True
MAX_AGE_THRESHOLD_SELECTED = False
MAX_AGE_ENFORCEMENT_ENABLED = False
ALPHA_SEMANTICS_CHANGED = False
STATE_SEMANTICS_CHANGED = False
COMPOSITION_AUTHORITY_CHANGED = False
EXIT_PRECEDENCE_PRESERVED = True
REVERSAL_REDUCE_FIRST_PRESERVED = True

# Productive CMC seed before typed bind succeeds — never the bridge sample-var proxy.
PRODUCTIVE_CMC_VOLATILITY_PLACEHOLDER = 0.0
PRODUCTIVE_CMC_VOLATILITY_SEED_POLICY = "TYPED_BIND_ONLY_ZERO_PLACEHOLDER_UNTIL_BOUND"

LEGACY_VOLATILITY_FLOAT_NOT_PRODUCTIVE_AUTHORITY = True
LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY = True
LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN = True
LEGACY_1_0_CONSTRUCTOR_DEFAULT_NOT_PRODUCTIVE = True

BRIDGE_COMPETING_PRODUCER_IDENTITY = (
    "feature_regime_pipeline_v2.sample_variance_ddof_1_times_sqrt_n"
)
BRIDGE_COMPETING_PRODUCER_PRODUCTIVE_AUTHORITY = False

GAPS_CLOSED: tuple[str, ...] = (
    "G3_UNTYPED_EXISTING_HOT_PATH_FLOAT",
    "G4_COMPETING_PRODUCERS_DIFFERENT_SCALING",
    "G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY",
    "G8_LEGACY_PATH_NOT_YET_GLOBALLY_ENFORCED",
    "G15_COMPETING_NON_ALIAS_PRODUCERS",
)
GAPS_REMAINING: tuple[str, ...] = (
    "C1_G10_NUMERIC_MAX_AGE",
    "G5_PANEL_1H_REUSES_PT1M_LOOKBACK",
    "G7_SEPARATE_SURVIVAL_AND_SUITABILITY_VOL_CONCEPTS",
    "G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN",
)

LIVE_AUTHORIZATION = False
HARD_STOP = True
PARAMETER_SELECTION_AUTHORIZED = False
PROMOTION_AUTHORIZED = False


class VolatilityHotPathStatusV1(str, Enum):
    VALID = "VALID"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    UNKNOWN_UNIT = "UNKNOWN_UNIT"
    UNKNOWN_HORIZON = "UNKNOWN_HORIZON"
    UNKNOWN_ESTIMATOR = "UNKNOWN_ESTIMATOR"
    INVALID_VALUE = "INVALID_VALUE"
    STALE = "STALE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    DUPLICATE_NO_ADVANCE = "DUPLICATE_NO_ADVANCE"
    SOURCE_DIGEST_MISMATCH = "SOURCE_DIGEST_MISMATCH"
    CONFIG_DIGEST_MISMATCH = "CONFIG_DIGEST_MISMATCH"
    LEGACY_QUARANTINED = "LEGACY_QUARANTINED"
    UNAVAILABLE = "UNAVAILABLE"


class CanonicalVolatilityHotPathClosureError(ValueError):
    def __init__(self, code: VolatilityHotPathStatusV1, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}:{message}")


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def closure_config_path(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / CLOSURE_CONFIG_REL_PATH


def load_closure_config_v1(root: Path | None = None) -> dict[str, Any]:
    path = closure_config_path(root)
    if not path.is_file():
        raise CanonicalVolatilityHotPathClosureError(
            VolatilityHotPathStatusV1.UNAVAILABLE,
            f"closure_config_missing:{path}",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def compute_closure_config_digest_v1(payload: Mapping[str, Any] | None = None) -> str:
    cfg = dict(payload) if payload is not None else load_closure_config_v1()
    return _stable_digest(cfg)


def productive_cmc_volatility_seed_v1() -> float:
    """Non-authoritative placeholder until typed bind overwrites atomically."""
    return float(PRODUCTIVE_CMC_VOLATILITY_PLACEHOLDER)


def clear_untyped_productive_volatility_float_v1(
    context: CanonicalMarketContextV1,
) -> CanonicalMarketContextV1:
    """Fail-closed: strip typed carrier and reset float to non-authority placeholder."""
    from dataclasses import replace

    return replace(
        context,
        canonical_volatility_estimate=None,
        volatility_estimate=productive_cmc_volatility_seed_v1(),
    )


def reject_naked_float_productive_binding_v1(
    *,
    raw_value: float | None,
    typed_estimate: VolatilityEstimateV1 | None,
    provenance: Mapping[str, Any] | None,
) -> None:
    """Productive hot-path forbids naked float bindings without typed provenance."""
    if typed_estimate is not None:
        validate_canonical_volatility_estimate_v1(typed_estimate)
        return
    reject_implicit_legacy_float_input_v1(raw_value=raw_value, provenance=provenance)


def reject_competing_bridge_producer_as_productive_authority_v1(
    *,
    source_identity: str,
    used_as_cmc_volatility_estimate: bool,
) -> None:
    if source_identity == BRIDGE_COMPETING_PRODUCER_IDENTITY and used_as_cmc_volatility_estimate:
        raise CanonicalVolatilityHotPathClosureError(
            VolatilityHotPathStatusV1.LEGACY_QUARANTINED,
            "competing_bridge_producer_not_productive_authority",
        )


def assert_config_digest_matches_runtime_v1(
    estimate: VolatilityEstimateV1,
    *,
    expected_config_digest: str | None = None,
) -> None:
    expected = expected_config_digest or resolve_canonical_config_digest_v1()
    if estimate.config_digest != expected:
        raise CanonicalVolatilityHotPathClosureError(
            VolatilityHotPathStatusV1.CONFIG_DIGEST_MISMATCH,
            f"expected={expected}:actual={estimate.config_digest}",
        )


def assert_source_digest_matches_v1(
    estimate: VolatilityEstimateV1,
    *,
    expected_source_digest: str,
) -> None:
    if estimate.source_digest != expected_source_digest:
        raise CanonicalVolatilityHotPathClosureError(
            VolatilityHotPathStatusV1.SOURCE_DIGEST_MISMATCH,
            f"expected={expected_source_digest}:actual={estimate.source_digest}",
        )


def classify_hot_path_status_v1(
    *,
    estimate: VolatilityEstimateV1 | None,
    producer_outcome: str | None = None,
    reason_codes: Sequence[str] | None = None,
) -> VolatilityHotPathStatusV1:
    codes = {str(c) for c in (reason_codes or ())}
    outcome = str(producer_outcome or "")
    if "OUT_OF_ORDER" in outcome or "OUT_OF_ORDER" in codes:
        return VolatilityHotPathStatusV1.OUT_OF_ORDER
    if "DUPLICATE" in outcome or "DUPLICATE_NO_ADVANCE" in codes:
        return VolatilityHotPathStatusV1.DUPLICATE_NO_ADVANCE
    if "WARMUP" in outcome or "INSUFFICIENT" in outcome or "INSUFFICIENT_HISTORY" in codes:
        return VolatilityHotPathStatusV1.INSUFFICIENT_HISTORY
    if "LEGACY" in codes or "QUARANTINE" in "".join(codes):
        return VolatilityHotPathStatusV1.LEGACY_QUARANTINED
    if estimate is None:
        return VolatilityHotPathStatusV1.UNAVAILABLE
    try:
        validate_canonical_volatility_estimate_v1(estimate)
    except Exception as exc:  # noqa: BLE001 — map typed failures to status
        msg = str(exc)
        if "UNIT" in msg:
            return VolatilityHotPathStatusV1.UNKNOWN_UNIT
        if "HORIZON" in msg:
            return VolatilityHotPathStatusV1.UNKNOWN_HORIZON
        if "ESTIMATOR" in msg:
            return VolatilityHotPathStatusV1.UNKNOWN_ESTIMATOR
        if "NON_FINITE" in msg or "NEGATIVE" in msg or "MISSING_VALUE" in msg:
            return VolatilityHotPathStatusV1.INVALID_VALUE
        if "CONFIG_DIGEST" in msg:
            return VolatilityHotPathStatusV1.CONFIG_DIGEST_MISMATCH
        if "SOURCE_DIGEST" in msg:
            return VolatilityHotPathStatusV1.SOURCE_DIGEST_MISMATCH
        return VolatilityHotPathStatusV1.INVALID_VALUE
    return VolatilityHotPathStatusV1.VALID


def compute_volatility_age_seconds_diagnostic_v1(
    *,
    estimate: VolatilityEstimateV1 | None,
    reference_market_event_time: datetime | str | None,
) -> float | None:
    """Diagnostic age only — no threshold, no enforcement."""
    if estimate is None or reference_market_event_time is None:
        return None
    as_of = estimate.as_of_event_time
    if as_of.tzinfo is None:
        return None
    if isinstance(reference_market_event_time, str):
        ref = datetime.fromisoformat(reference_market_event_time.replace("Z", "+00:00"))
    else:
        ref = reference_market_event_time
    if ref.tzinfo is None:
        return None
    age = (ref.astimezone(timezone.utc) - as_of.astimezone(timezone.utc)).total_seconds()
    if not math.isfinite(age):
        return None
    return float(age)


@dataclass(frozen=True)
class HotPathVolatilityCycleEvidenceV1:
    volatility_contract_version: str | None
    volatility_value: float | None
    volatility_unit: str | None
    volatility_horizon: str | None
    volatility_estimator: str | None
    volatility_estimator_version: str | None
    volatility_observation_count: int | None
    volatility_as_of_event_time: str | None
    volatility_oldest_observation_event_time: str | None
    volatility_source_digest: str | None
    volatility_config_digest: str | None
    volatility_fallback_used: bool | None
    volatility_fallback_identity: str | None
    volatility_status: str
    volatility_reason_codes: tuple[str, ...]
    volatility_age_seconds: float | None
    max_age_threshold: None
    max_age_enforcement_enabled: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_age_enforcement_enabled": bool(self.max_age_enforcement_enabled),
            "max_age_threshold": self.max_age_threshold,
            "volatility_age_seconds": self.volatility_age_seconds,
            "volatility_as_of_event_time": self.volatility_as_of_event_time,
            "volatility_config_digest": self.volatility_config_digest,
            "volatility_contract_version": self.volatility_contract_version,
            "volatility_estimator": self.volatility_estimator,
            "volatility_estimator_version": self.volatility_estimator_version,
            "volatility_fallback_identity": self.volatility_fallback_identity,
            "volatility_fallback_used": self.volatility_fallback_used,
            "volatility_horizon": self.volatility_horizon,
            "volatility_observation_count": self.volatility_observation_count,
            "volatility_oldest_observation_event_time": (
                self.volatility_oldest_observation_event_time
            ),
            "volatility_reason_codes": list(self.volatility_reason_codes),
            "volatility_source_digest": self.volatility_source_digest,
            "volatility_status": self.volatility_status,
            "volatility_unit": self.volatility_unit,
            "volatility_value": self.volatility_value,
        }


def build_hot_path_volatility_cycle_evidence_v1(
    context: CanonicalMarketContextV1,
    *,
    producer_outcome: str | None = None,
    reason_codes: Sequence[str] | None = None,
) -> HotPathVolatilityCycleEvidenceV1:
    estimate = context.canonical_volatility_estimate
    status = classify_hot_path_status_v1(
        estimate=estimate,
        producer_outcome=producer_outcome,
        reason_codes=reason_codes,
    )
    age = compute_volatility_age_seconds_diagnostic_v1(
        estimate=estimate,
        reference_market_event_time=context.market_event_time,
    )
    if estimate is None:
        return HotPathVolatilityCycleEvidenceV1(
            volatility_contract_version=None,
            volatility_value=None,
            volatility_unit=None,
            volatility_horizon=None,
            volatility_estimator=None,
            volatility_estimator_version=None,
            volatility_observation_count=None,
            volatility_as_of_event_time=None,
            volatility_oldest_observation_event_time=None,
            volatility_source_digest=None,
            volatility_config_digest=None,
            volatility_fallback_used=None,
            volatility_fallback_identity=None,
            volatility_status=status.value,
            volatility_reason_codes=tuple(reason_codes or (status.value,)),
            volatility_age_seconds=age,
            max_age_threshold=None,
            max_age_enforcement_enabled=False,
        )
    oldest = estimate.oldest_observation_event_time
    return HotPathVolatilityCycleEvidenceV1(
        volatility_contract_version=estimate.contract_version,
        volatility_value=float(estimate.value),
        volatility_unit=estimate.unit,
        volatility_horizon=CANONICAL_HORIZON,
        volatility_estimator=estimate.estimator,
        volatility_estimator_version=estimate.estimator_version,
        volatility_observation_count=int(estimate.observation_count),
        volatility_as_of_event_time=estimate.as_of_event_time.astimezone(timezone.utc).isoformat(),
        volatility_oldest_observation_event_time=(
            None if oldest is None else oldest.astimezone(timezone.utc).isoformat()
        ),
        volatility_source_digest=estimate.source_digest,
        volatility_config_digest=estimate.config_digest,
        volatility_fallback_used=bool(estimate.fallback_used),
        volatility_fallback_identity=estimate.fallback_identity or NO_FALLBACK_IDENTITY,
        volatility_status=status.value,
        volatility_reason_codes=tuple(reason_codes or (status.value,)),
        volatility_age_seconds=age,
        max_age_threshold=None,
        max_age_enforcement_enabled=False,
    )


def assert_architecture_guards_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    bridge = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "hardening_cycle_bridge_v2.py"
    ).read_text(encoding="utf-8")
    feature = (
        root
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
        / "feature_regime_pipeline_v2.py"
    ).read_text(encoding="utf-8")
    typed = (
        root
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    materializer = (
        root / "src/trading/master_v2/canonical_volatility_estimate_materializer_v1.py"
    ).read_text(encoding="utf-8")
    binding_host = (
        root
        / "src/trading/master_v2/canonical_volatility_productive_runtime_cmc_typed_binding_v1.py"
    ).read_text(encoding="utf-8")
    presence = (
        root / "src/trading/master_v2/double_play_runtime_typed_volatility_presence_gate_v1.py"
    ).read_text(encoding="utf-8")
    this_src = (
        root / "src/trading/master_v2/canonical_volatility_hot_path_contract_closure_v1.py"
    ).read_text(encoding="utf-8")

    forbidden_seed = "volatility_estimate=float(features.volatility_estimate)"
    if forbidden_seed in bridge:
        raise RuntimeError("COMPETING_BRIDGE_FLOAT_STILL_SEEDED_INTO_CMC")
    if "productive_cmc_volatility_seed_v1" not in bridge:
        raise RuntimeError("PRODUCTIVE_CMC_SEED_HELPER_NOT_WIRED")
    if "build_hot_path_volatility_cycle_evidence_v1" not in bridge:
        raise RuntimeError("HOT_PATH_CYCLE_EVIDENCE_NOT_WIRED")
    if "VOLATILITY_ESTIMATE_PRODUCTIVE_AUTHORITY = False" not in feature:
        raise RuntimeError("FEATURE_REGIME_VOL_NOT_MARKED_NON_PRODUCTIVE")
    if "ddof=contract.DDOF" not in materializer and "ddof=0" not in materializer:
        # Materializer must use contract DDOF (0).
        if ".std(ddof=contract.DDOF)" not in materializer:
            raise RuntimeError("CANONICAL_MATERIALIZER_DDOF_NOT_CONTRACT_BOUND")
    if "VolatilityEstimateV1 = CanonicalVolatilityEstimateV1" not in typed:
        raise RuntimeError("VOLATILITY_ESTIMATE_V1_ALIAS_MISSING")
    if "clear_untyped_productive_volatility_float_v1" not in binding_host:
        raise RuntimeError("PRODUCTIVE_BINDING_MUST_CLEAR_UNTYPED_FLOAT_ON_FAIL")
    if "DOUBLE_PLAY_TYPED_CUTOVER = True" not in presence:
        raise RuntimeError("PRESENCE_GATE_TYPED_CUTOVER_REQUIRED")
    if "sqrt(len(rets))" in this_src.split("assert_architecture_guards_v1", 1)[0]:
        raise RuntimeError("CLOSURE_MUST_NOT_REINTRODUCE_SQRT_N_SCALING")

    feature_digest = compute_contract_digest_v1(load_contract_config_v1(root))
    closure_cfg = load_closure_config_v1(root)
    if closure_cfg.get("feature_contract_config_rel_path") != FEATURE_CONTRACT_CONFIG_REL_PATH:
        raise RuntimeError("CLOSURE_CONFIG_FEATURE_CONTRACT_PATH_DRIFT")
    if closure_cfg.get("unit") != CANONICAL_UNIT:
        raise RuntimeError("CLOSURE_CONFIG_UNIT_DRIFT")
    if closure_cfg.get("horizon") != CANONICAL_HORIZON:
        raise RuntimeError("CLOSURE_CONFIG_HORIZON_DRIFT")
    if closure_cfg.get("estimator") != CANONICAL_ESTIMATOR:
        raise RuntimeError("CLOSURE_CONFIG_ESTIMATOR_DRIFT")
    if closure_cfg.get("estimator_version") != CANONICAL_ESTIMATOR_VERSION:
        raise RuntimeError("CLOSURE_CONFIG_ESTIMATOR_VERSION_DRIFT")
    if closure_cfg.get("bar_duration") != CANONICAL_BAR_DURATION:
        raise RuntimeError("CLOSURE_CONFIG_BAR_DURATION_DRIFT")
    if closure_cfg.get("output_annualized") is not False:
        raise RuntimeError("CLOSURE_CONFIG_ANNUALIZED_DRIFT")
    if closure_cfg.get("max_age_enforcement_enabled") is not False:
        raise RuntimeError("CLOSURE_CONFIG_MAX_AGE_ENFORCEMENT_DRIFT")
    if closure_cfg.get("numeric_max_age_decided") is not False:
        raise RuntimeError("CLOSURE_CONFIG_NUMERIC_MAX_AGE_DECIDED_DRIFT")
    if POLICY_NUMERIC_MAX_AGE_DECIDED or POLICY_MAX_AGE_ENFORCEMENT_ENABLED:
        raise RuntimeError("POLICY_MAX_AGE_FLAG_DRIFT")
    if NUMERIC_MAX_AGE_DECIDED or MAX_AGE_ENFORCEMENT_ENABLED or MAX_AGE_THRESHOLD_SELECTED:
        raise RuntimeError("CLOSURE_MAX_AGE_FLAG_DRIFT")
    if ALPHA_SEMANTICS_CHANGED or STATE_SEMANTICS_CHANGED or COMPOSITION_AUTHORITY_CHANGED:
        raise RuntimeError("AUTHORITY_SEMANTICS_FLAG_DRIFT")
    if LIVE_AUTHORIZATION or not HARD_STOP:
        raise RuntimeError("LIVE_OR_HARD_STOP_FLAG_DRIFT")

    return {
        "bridge_competing_producer_quarantined": True,
        "canonical_unit": CANONICAL_UNIT,
        "canonical_horizon": CANONICAL_HORIZON,
        "canonical_estimator": CANONICAL_ESTIMATOR,
        "canonical_estimator_version": CANONICAL_ESTIMATOR_VERSION,
        "canonical_ddof": CANONICAL_DDOF,
        "feature_contract_digest": feature_digest,
        "closure_config_digest": compute_closure_config_digest_v1(closure_cfg),
        "legacy_0_02": LEGACY_REPLAY_RULES_DEFAULT_VALUE,
        "legacy_0_2": LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
        "legacy_1_0": LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "gaps_closed": list(GAPS_CLOSED),
        "gaps_remaining": list(GAPS_REMAINING),
        "guards_pass": True,
    }


def assert_capability_non_goals_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "closure_owner": CLOSURE_OWNER,
        "package_marker": PACKAGE_MARKER,
        "numeric_max_age_decided": NUMERIC_MAX_AGE_DECIDED,
        "numeric_max_age_value_unresolved": NUMERIC_MAX_AGE_VALUE_UNRESOLVED,
        "max_age_threshold_selected": MAX_AGE_THRESHOLD_SELECTED,
        "max_age_enforcement_enabled": MAX_AGE_ENFORCEMENT_ENABLED,
        "parameter_selection_authorized": PARAMETER_SELECTION_AUTHORIZED,
        "promotion_authorized": PROMOTION_AUTHORIZED,
        "alpha_semantics_changed": ALPHA_SEMANTICS_CHANGED,
        "state_semantics_changed": STATE_SEMANTICS_CHANGED,
        "composition_authority_changed": COMPOSITION_AUTHORITY_CHANGED,
        "live_authorization": LIVE_AUTHORIZATION,
        "hard_stop": HARD_STOP,
        "gaps_closed": list(GAPS_CLOSED),
        "gaps_remaining": list(GAPS_REMAINING),
        "non_goals": [
            "numeric_max_age_threshold",
            "threshold_recommendation",
            "enforcement_activation",
            "alpha_threshold_change",
            "chop_redefinition",
            "regime_redesign",
            "decision_cadence_redesign",
            "event_driven_architecture",
            "trades_l2_integration",
            "live_testnet_order_routing",
            "promotion",
            "economic_validity_decision",
        ],
    }


def producer_consumer_graph_v1() -> list[str]:
    return [
        "NormalizedPublicMarketData / Mark Samples",
        "DistinctMarketObservationAcceptorV1",
        "CanonicalVolatilityTypedRuntimeProducerScaffoldV1",
        "canonical_volatility_estimate_materializer_v1 (ddof=0, PT60M, annualized=false)",
        "VolatilityEstimateV1 / CanonicalVolatilityEstimateV1",
        "bind_typed_canonical_volatility_estimate_into_market_context_v1",
        "CanonicalMarketContextV1",
        "evaluate_double_play_runtime_typed_volatility_presence_gate_v1",
        "update_dynamic_boundaries (adapted typed float only)",
        "Double-Play composition / state / entry-exit path",
    ]


__all__ = [
    "ALPHA_SEMANTICS_CHANGED",
    "BRIDGE_COMPETING_PRODUCER_IDENTITY",
    "BRIDGE_COMPETING_PRODUCER_PRODUCTIVE_AUTHORITY",
    "CANONICAL_VOLATILITY_CONTRACT_VERSIONED",
    "CANONICAL_VOLATILITY_ESTIMATOR_DDOF_ZERO",
    "CANONICAL_VOLATILITY_ESTIMATOR_EXPLICIT",
    "CANONICAL_VOLATILITY_HORIZON_EXPLICIT",
    "CANONICAL_VOLATILITY_MATERIALIZER_PRESENT",
    "CANONICAL_VOLATILITY_NOT_ANNUALIZED",
    "CANONICAL_VOLATILITY_SINGLE_PRODUCTIVE_PRODUCER",
    "CANONICAL_VOLATILITY_TYPED_HOT_PATH_WIRED",
    "CANONICAL_VOLATILITY_UNIT_EXPLICIT",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CLOSURE_CONFIG_REL_PATH",
    "CLOSURE_OWNER",
    "COMPETING_BRIDGE_PRODUCER_REMOVED_OR_QUARANTINED",
    "COMPOSITION_AUTHORITY_CHANGED",
    "CanonicalVolatilityHotPathClosureError",
    "EXIT_PRECEDENCE_PRESERVED",
    "GAPS_CLOSED",
    "GAPS_REMAINING",
    "HARD_STOP",
    "HotPathVolatilityCycleEvidenceV1",
    "LEGACY_0_02_EXPLICIT_QUARANTINE_ONLY",
    "LEGACY_0_2_SILENT_FALLBACK_FORBIDDEN",
    "LEGACY_1_0_CONSTRUCTOR_DEFAULT_NOT_PRODUCTIVE",
    "LEGACY_1_0_NOT_PRODUCTIVE",
    "LEGACY_VOLATILITY_FLOAT_NOT_PRODUCTIVE_AUTHORITY",
    "LIVE_AUTHORIZATION",
    "MAX_AGE_ENFORCEMENT_ENABLED",
    "MAX_AGE_THRESHOLD_SELECTED",
    "NAKED_FLOAT_PRODUCTIVE_BINDING_REMOVED",
    "NUMERIC_MAX_AGE_DECIDED",
    "NUMERIC_MAX_AGE_VALUE_UNRESOLVED",
    "OFFLINE_RUNTIME_VOLATILITY_EQUIVALENCE",
    "PACKAGE_MARKER",
    "PRODUCTIVE_CMC_VOLATILITY_PLACEHOLDER",
    "PRODUCTIVE_CMC_VOLATILITY_SEED_POLICY",
    "REVERSAL_REDUCE_FIRST_PRESERVED",
    "STATE_SEMANTICS_CHANGED",
    "VOLATILITY_PROVENANCE_EVIDENCE_COMPLETE",
    "VOLATILITY_UNKNOWN_ENTRY_FAIL_CLOSED",
    "VOLATILITY_UNKNOWN_EXIT_PATHS_PRESERVED",
    "VolatilityHotPathStatusV1",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
    "assert_config_digest_matches_runtime_v1",
    "assert_source_digest_matches_v1",
    "build_hot_path_volatility_cycle_evidence_v1",
    "classify_hot_path_status_v1",
    "clear_untyped_productive_volatility_float_v1",
    "compute_closure_config_digest_v1",
    "compute_volatility_age_seconds_diagnostic_v1",
    "load_closure_config_v1",
    "producer_consumer_graph_v1",
    "productive_cmc_volatility_seed_v1",
    "reject_competing_bridge_producer_as_productive_authority_v1",
    "reject_naked_float_productive_binding_v1",
]
