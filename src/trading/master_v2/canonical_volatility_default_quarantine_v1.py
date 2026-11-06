"""Canonical volatility default quarantine v1 (C2).

Policy-only capability: quarantines productive untyped volatility defaults and
numeric-stability leaks outside the C1 typed-binding path. Reuses C1 for typed
validation / adaptation / digests / evidence identity. Does not invent parameter
values, estimators, adapters, or runtime wiring.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Optional

from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    CAPABILITY_ID as C1_CAPABILITY_ID,
    LEGACY_ADAPTATION_BOUNDARY,
    SINGLE_VALIDATION_BOUNDARY,
    TYPED_TRANSPORT_MODEL,
    adapt_validated_typed_estimate_to_legacy_float_v1,
    validate_typed_estimate_for_cmc_binding_v1,
)
from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import (
    FLOOR_POLICY as CANONICAL_FLOOR_POLICY,
    MV2_FALLBACK_0_2_ADMISSIBLE as FEATURE_MV2_FALLBACK_0_2_ADMISSIBLE,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CanonicalVolatilityEstimateV1,
    MV2_FALLBACK_0_2_ADMISSIBLE as TYPED_MV2_FALLBACK_0_2_ADMISSIBLE,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1=true"

CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_DEFAULT_QUARANTINE_V1"
CAPABILITY_VERSION = "canonical_volatility_default_quarantine/v1"
QUARANTINE_OWNER = "trading.master_v2.canonical_volatility_default_quarantine_v1"
QUARANTINE_CONTRACT_VERSION = CAPABILITY_VERSION

RUNTIME_EFFECT = False
TRADING_LOGIC_EFFECT = False
PARAMETER_EFFECT = False
LIVE_AUTHORIZATION = False
RUNTIME_WIRING = False
RUNTIME_PRODUCER_CUTOVER = False
PARAMETER_RESEARCH = False

# Documented legacy numeric identities (must not be replaced by different values).
LEGACY_HISTORICAL_BIND_DEFAULT_VALUE = 0.2
LEGACY_REPLAY_RULES_DEFAULT_VALUE = 0.02
LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE = 1.0
LEGACY_STRATEGY_FLOOR_VALUE = 1e-9

GAPS_CLOSED: tuple[str, ...] = (
    "G1_SILENT_FALLBACK_PATH_EXISTS",
    "G2_UNTYPED_PRODUCTIVE_DEFAULT_EXISTS",
    "G4_FALLBACK_EVIDENCE_MISSING",
    "G5_DEFAULT_DIGEST_MISSING",
    "G9_DEFAULT_CONFLICT_EXISTS",
    "G10_NUMERIC_FLOOR_SEMANTIC_LEAK_EXISTS",
    "G11_TEST_PRODUCTION_SEMANTICS_CONFLATED",
    "G12_CONFIG_CODE_DEFAULT_DRIFT_EXISTS",
    "G13_SPEC_CODE_DEFAULT_DRIFT_EXISTS",
    "G14_UNKNOWN_VOLATILITY_FAILS_OPEN",
)
GAPS_REMAINING: tuple[str, ...] = (
    "G3_UNTYPED_EXPLICIT_LEGACY_STILL_ADMISSIBLE",
    "G6_UNIT_AMBIGUITY_ON_EXPLICIT_LEGACY",
    "G7_HORIZON_AMBIGUITY_ON_EXPLICIT_LEGACY",
    "G8_ESTIMATOR_AMBIGUITY_ON_EXPLICIT_LEGACY",
    "G15_COMPETING_NON_ALIAS_PRODUCERS",
    "C3_TYPED_RUNTIME_PRODUCER_ASSESSMENT",
    "C1_G4_COMPETING_PRODUCERS_DIFFERENT_SCALING",
    "C1_G5_PANEL_1H_REUSES_PT1M_LOOKBACK",
    "C1_G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY",
    "C1_G7_SEPARATE_SURVIVAL_AND_SUITABILITY_VOL_CONCEPTS",
    "C1_G8_LEGACY_PATH_NOT_YET_GLOBALLY_ENFORCED",
    "C1_G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN",
    "C1_G10_NUMERIC_MAX_AGE",
)


class VolatilityQuarantineDispositionV1(str, Enum):
    TYPED_BOUND = "TYPED_BOUND"
    EXPLICIT_LEGACY_QUARANTINED = "EXPLICIT_LEGACY_QUARANTINED"
    TEST_FIXTURE_ALLOWED = "TEST_FIXTURE_ALLOWED"
    NUMERIC_STABILITY_ALLOWED = "NUMERIC_STABILITY_ALLOWED"
    REJECTED_UNKNOWN = "REJECTED_UNKNOWN"
    REJECTED_SILENT_DEFAULT = "REJECTED_SILENT_DEFAULT"
    REJECTED_INVALID = "REJECTED_INVALID"
    REJECTED_POLICY_CONFLICT = "REJECTED_POLICY_CONFLICT"


class CanonicalVolatilityQuarantineErrorCode(str, Enum):
    MISSING_INPUT = "MISSING_INPUT"
    SILENT_DEFAULT_FORBIDDEN = "SILENT_DEFAULT_FORBIDDEN"
    INVALID_VALUE = "INVALID_VALUE"
    POLICY_CONFLICT = "POLICY_CONFLICT"
    TYPED_LEGACY_MISMATCH = "TYPED_LEGACY_MISMATCH"
    FLOOR_FORBIDDEN = "FLOOR_FORBIDDEN"
    UNADMISSIBLE_DISPOSITION = "UNADMISSIBLE_DISPOSITION"
    SECOND_AUTHORITY_FORBIDDEN = "SECOND_AUTHORITY_FORBIDDEN"


class CanonicalVolatilityQuarantineError(ValueError):
    def __init__(self, code: CanonicalVolatilityQuarantineErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}:{message}")


def _raise(code: CanonicalVolatilityQuarantineErrorCode, message: str) -> None:
    raise CanonicalVolatilityQuarantineError(code, message)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanonicalVolatilityQuarantineResultV1:
    """Versioned quarantine outcome for legacy / default volatility inputs."""

    contract_version: str
    disposition: VolatilityQuarantineDispositionV1
    legacy_value: float | None
    semantic_name: str
    source_kind: str
    source_file_or_component: str
    explicit_or_implicit: str
    productive_or_test_only: str
    unit_known: bool
    horizon_known: bool
    estimator_known: bool
    fallback_or_default_or_floor: str
    evidence_required: bool
    source_digest: str
    quarantine_digest: str
    rejection_reason: str
    typed_binding_present: bool = False
    canonical_estimate_present: bool = False
    authority_effect: str = "SCOPE_BAND_PROXY"
    quarantine_contract_version: str = QUARANTINE_CONTRACT_VERSION

    @property
    def admitted(self) -> bool:
        return self.disposition in (
            VolatilityQuarantineDispositionV1.TYPED_BOUND,
            VolatilityQuarantineDispositionV1.EXPLICIT_LEGACY_QUARANTINED,
            VolatilityQuarantineDispositionV1.TEST_FIXTURE_ALLOWED,
            VolatilityQuarantineDispositionV1.NUMERIC_STABILITY_ALLOWED,
        )

    def to_evidence_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "canonical_estimate_present": self.canonical_estimate_present,
            "disposition": self.disposition.value,
            "evidence_required": self.evidence_required,
            "explicit_or_implicit": self.explicit_or_implicit,
            "fallback_or_default_or_floor": self.fallback_or_default_or_floor,
            "legacy_value": self.legacy_value,
            "quarantine_contract_version": self.quarantine_contract_version,
            "quarantine_digest": self.quarantine_digest,
            "rejection_reason": self.rejection_reason,
            "semantic_name": self.semantic_name,
            "source_digest": self.source_digest,
            "source_kind": self.source_kind,
            "typed_binding_present": self.typed_binding_present,
        }


@dataclass(frozen=True)
class CanonicalVolatilityQuarantineEvidenceProvenanceV1:
    """Decision-evidence attachment for quarantined legacy volatility inputs."""

    quarantine_contract_version: str
    disposition: str
    semantic_name: str
    legacy_value: float | None
    source_kind: str
    explicit_or_implicit: str
    fallback_or_default_or_floor: str
    source_digest: str
    quarantine_digest: str
    typed_binding_present: bool
    canonical_estimate_present: bool
    authority_effect: str
    rejection_reason: str

    def __post_init__(self) -> None:
        for digest_name in ("source_digest", "quarantine_digest"):
            digest = getattr(self, digest_name)
            if digest and (
                not isinstance(digest, str)
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
            ):
                msg = f"{digest_name} must be empty or a 64-char lowercase sha256 hex"
                raise ValueError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "canonical_estimate_present": self.canonical_estimate_present,
            "disposition": self.disposition,
            "explicit_or_implicit": self.explicit_or_implicit,
            "fallback_or_default_or_floor": self.fallback_or_default_or_floor,
            "legacy_value": self.legacy_value,
            "quarantine_contract_version": self.quarantine_contract_version,
            "quarantine_digest": self.quarantine_digest,
            "rejection_reason": self.rejection_reason,
            "semantic_name": self.semantic_name,
            "source_digest": self.source_digest,
            "source_kind": self.source_kind,
            "typed_binding_present": self.typed_binding_present,
        }


def compute_quarantine_digest_v1(
    *,
    disposition: VolatilityQuarantineDispositionV1,
    legacy_value: float | None,
    semantic_name: str,
    source_kind: str,
    source_file_or_component: str,
    explicit_or_implicit: str,
    productive_or_test_only: str,
    fallback_or_default_or_floor: str,
    source_digest: str,
    rejection_reason: str,
) -> str:
    return _stable_digest(
        {
            "capability_version": CAPABILITY_VERSION,
            "disposition": disposition.value,
            "explicit_or_implicit": explicit_or_implicit,
            "fallback_or_default_or_floor": fallback_or_default_or_floor,
            "legacy_value": legacy_value,
            "productive_or_test_only": productive_or_test_only,
            "quarantine_owner": QUARANTINE_OWNER,
            "rejection_reason": rejection_reason,
            "semantic_name": semantic_name,
            "source_digest": source_digest,
            "source_file_or_component": source_file_or_component,
            "source_kind": source_kind,
            "typed_transport_model": TYPED_TRANSPORT_MODEL,
        }
    )


def _build_result(
    *,
    disposition: VolatilityQuarantineDispositionV1,
    legacy_value: float | None,
    semantic_name: str,
    source_kind: str,
    source_file_or_component: str,
    explicit_or_implicit: str,
    productive_or_test_only: str,
    unit_known: bool,
    horizon_known: bool,
    estimator_known: bool,
    fallback_or_default_or_floor: str,
    evidence_required: bool,
    source_digest: str,
    rejection_reason: str,
    typed_binding_present: bool = False,
    canonical_estimate_present: bool = False,
    authority_effect: str = "SCOPE_BAND_PROXY",
) -> CanonicalVolatilityQuarantineResultV1:
    q_digest = compute_quarantine_digest_v1(
        disposition=disposition,
        legacy_value=legacy_value,
        semantic_name=semantic_name,
        source_kind=source_kind,
        source_file_or_component=source_file_or_component,
        explicit_or_implicit=explicit_or_implicit,
        productive_or_test_only=productive_or_test_only,
        fallback_or_default_or_floor=fallback_or_default_or_floor,
        source_digest=source_digest,
        rejection_reason=rejection_reason,
    )
    return CanonicalVolatilityQuarantineResultV1(
        contract_version=QUARANTINE_CONTRACT_VERSION,
        disposition=disposition,
        legacy_value=legacy_value,
        semantic_name=semantic_name,
        source_kind=source_kind,
        source_file_or_component=source_file_or_component,
        explicit_or_implicit=explicit_or_implicit,
        productive_or_test_only=productive_or_test_only,
        unit_known=unit_known,
        horizon_known=horizon_known,
        estimator_known=estimator_known,
        fallback_or_default_or_floor=fallback_or_default_or_floor,
        evidence_required=evidence_required,
        source_digest=source_digest,
        quarantine_digest=q_digest,
        rejection_reason=rejection_reason,
        typed_binding_present=typed_binding_present,
        canonical_estimate_present=canonical_estimate_present,
        authority_effect=authority_effect,
    )


def quarantine_result_to_evidence_provenance_v1(
    result: CanonicalVolatilityQuarantineResultV1,
) -> CanonicalVolatilityQuarantineEvidenceProvenanceV1:
    return CanonicalVolatilityQuarantineEvidenceProvenanceV1(
        quarantine_contract_version=result.quarantine_contract_version,
        disposition=result.disposition.value,
        semantic_name=result.semantic_name,
        legacy_value=result.legacy_value,
        source_kind=result.source_kind,
        explicit_or_implicit=result.explicit_or_implicit,
        fallback_or_default_or_floor=result.fallback_or_default_or_floor,
        source_digest=result.source_digest,
        quarantine_digest=result.quarantine_digest,
        typed_binding_present=result.typed_binding_present,
        canonical_estimate_present=result.canonical_estimate_present,
        authority_effect=result.authority_effect,
        rejection_reason=result.rejection_reason,
    )


def quarantine_legacy_volatility_input_v1(
    *,
    raw_value: float | None,
    semantic_name: str,
    source_kind: str,
    source_file_or_component: str,
    explicit_or_implicit: str,
    productive_or_test_only: str,
    fallback_or_default_or_floor: str,
    typed_estimate: CanonicalVolatilityEstimateV1 | None = None,
    source_digest: str | None = None,
    allow_test_fixture: bool = False,
    raise_on_reject: bool = True,
) -> CanonicalVolatilityQuarantineResultV1:
    """Central C2 quarantine boundary for untyped legacy volatility inputs.

    Typed estimates are adapted exclusively via C1. This function never invents
    0.2 / 0.02 / 1.0 / 1e-9 and never spoofs ``canonical_volatility_estimate``.
    """
    if not FEATURE_MV2_FALLBACK_0_2_ADMISSIBLE and not TYPED_MV2_FALLBACK_0_2_ADMISSIBLE:
        pass
    elif FEATURE_MV2_FALLBACK_0_2_ADMISSIBLE or TYPED_MV2_FALLBACK_0_2_ADMISSIBLE:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.POLICY_CONFLICT,
            "mv2_fallback_0_2_admissible_must_remain_false",
        )

    if typed_estimate is not None:
        validated = validate_typed_estimate_for_cmc_binding_v1(typed_estimate)
        legacy = float(
            adapt_validated_typed_estimate_to_legacy_float_v1(
                validated,
                already_validated=True,
            )
        )
        if raw_value is not None and not math.isclose(
            float(raw_value), legacy, rel_tol=0.0, abs_tol=0.0
        ):
            result = _build_result(
                disposition=VolatilityQuarantineDispositionV1.REJECTED_POLICY_CONFLICT,
                legacy_value=float(raw_value),
                semantic_name=semantic_name,
                source_kind=source_kind,
                source_file_or_component=source_file_or_component,
                explicit_or_implicit=explicit_or_implicit,
                productive_or_test_only=productive_or_test_only,
                unit_known=True,
                horizon_known=True,
                estimator_known=True,
                fallback_or_default_or_floor=fallback_or_default_or_floor,
                evidence_required=True,
                source_digest=validated.source_digest,
                rejection_reason="typed_legacy_float_mismatch",
                typed_binding_present=True,
                canonical_estimate_present=True,
            )
            if raise_on_reject:
                _raise(
                    CanonicalVolatilityQuarantineErrorCode.TYPED_LEGACY_MISMATCH,
                    result.rejection_reason,
                )
            return result
        return _build_result(
            disposition=VolatilityQuarantineDispositionV1.TYPED_BOUND,
            legacy_value=legacy,
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit="EXPLICIT",
            productive_or_test_only=productive_or_test_only,
            unit_known=True,
            horizon_known=True,
            estimator_known=True,
            fallback_or_default_or_floor="TYPED",
            evidence_required=True,
            source_digest=validated.source_digest,
            rejection_reason="",
            typed_binding_present=True,
            canonical_estimate_present=True,
        )

    if raw_value is None:
        result = _build_result(
            disposition=VolatilityQuarantineDispositionV1.REJECTED_UNKNOWN,
            legacy_value=None,
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit=explicit_or_implicit,
            productive_or_test_only=productive_or_test_only,
            unit_known=False,
            horizon_known=False,
            estimator_known=False,
            fallback_or_default_or_floor=fallback_or_default_or_floor,
            evidence_required=True,
            source_digest=source_digest or "",
            rejection_reason="volatility_estimate_missing",
        )
        if raise_on_reject:
            _raise(CanonicalVolatilityQuarantineErrorCode.MISSING_INPUT, result.rejection_reason)
        return result

    if explicit_or_implicit == "IMPLICIT":
        result = _build_result(
            disposition=VolatilityQuarantineDispositionV1.REJECTED_SILENT_DEFAULT,
            legacy_value=float(raw_value),
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit="IMPLICIT",
            productive_or_test_only=productive_or_test_only,
            unit_known=False,
            horizon_known=False,
            estimator_known=False,
            fallback_or_default_or_floor=fallback_or_default_or_floor,
            evidence_required=True,
            source_digest=source_digest or "",
            rejection_reason="silent_or_implicit_volatility_default_forbidden",
        )
        if raise_on_reject:
            _raise(
                CanonicalVolatilityQuarantineErrorCode.SILENT_DEFAULT_FORBIDDEN,
                result.rejection_reason,
            )
        return result

    value = float(raw_value)
    if isinstance(raw_value, bool) or not math.isfinite(value) or value < 0.0:
        result = _build_result(
            disposition=VolatilityQuarantineDispositionV1.REJECTED_INVALID,
            legacy_value=value if not isinstance(raw_value, bool) else None,
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit=explicit_or_implicit,
            productive_or_test_only=productive_or_test_only,
            unit_known=False,
            horizon_known=False,
            estimator_known=False,
            fallback_or_default_or_floor=fallback_or_default_or_floor,
            evidence_required=True,
            source_digest=source_digest or "",
            rejection_reason="volatility_estimate_invalid",
        )
        if raise_on_reject:
            _raise(CanonicalVolatilityQuarantineErrorCode.INVALID_VALUE, result.rejection_reason)
        return result

    if value == 0.0:
        result = _build_result(
            disposition=VolatilityQuarantineDispositionV1.REJECTED_INVALID,
            legacy_value=0.0,
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit=explicit_or_implicit,
            productive_or_test_only=productive_or_test_only,
            unit_known=False,
            horizon_known=False,
            estimator_known=False,
            fallback_or_default_or_floor=fallback_or_default_or_floor,
            evidence_required=True,
            source_digest=source_digest or "",
            rejection_reason="volatility_estimate_non_positive",
        )
        if raise_on_reject:
            _raise(CanonicalVolatilityQuarantineErrorCode.INVALID_VALUE, result.rejection_reason)
        return result

    # Enforce policy: silent 0.2 materialization remains inadmissible.
    if (
        fallback_or_default_or_floor in {"FALLBACK", "DEFAULT"}
        and math.isclose(value, LEGACY_HISTORICAL_BIND_DEFAULT_VALUE, rel_tol=0.0, abs_tol=0.0)
        and explicit_or_implicit != "EXPLICIT"
    ):
        result = _build_result(
            disposition=VolatilityQuarantineDispositionV1.REJECTED_SILENT_DEFAULT,
            legacy_value=value,
            semantic_name=semantic_name,
            source_kind=source_kind,
            source_file_or_component=source_file_or_component,
            explicit_or_implicit=explicit_or_implicit,
            productive_or_test_only=productive_or_test_only,
            unit_known=False,
            horizon_known=False,
            estimator_known=False,
            fallback_or_default_or_floor=fallback_or_default_or_floor,
            evidence_required=True,
            source_digest=source_digest or "",
            rejection_reason="mv2_fallback_0_2_admissible_false",
        )
        if raise_on_reject:
            _raise(
                CanonicalVolatilityQuarantineErrorCode.SILENT_DEFAULT_FORBIDDEN,
                result.rejection_reason,
            )
        return result

    disposition = VolatilityQuarantineDispositionV1.EXPLICIT_LEGACY_QUARANTINED
    if allow_test_fixture or productive_or_test_only == "TEST_ONLY":
        disposition = VolatilityQuarantineDispositionV1.TEST_FIXTURE_ALLOWED

    digest = source_digest or _stable_digest(
        {
            "legacy_value": value,
            "semantic_name": semantic_name,
            "source_file_or_component": source_file_or_component,
            "source_kind": source_kind,
        }
    )
    return _build_result(
        disposition=disposition,
        legacy_value=value,
        semantic_name=semantic_name,
        source_kind=source_kind,
        source_file_or_component=source_file_or_component,
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only=productive_or_test_only,
        unit_known=False,
        horizon_known=False,
        estimator_known=False,
        fallback_or_default_or_floor=fallback_or_default_or_floor,
        evidence_required=True,
        source_digest=digest,
        rejection_reason="",
        typed_binding_present=False,
        canonical_estimate_present=False,
    )


def require_admitted_legacy_volatility_float_v1(
    result: CanonicalVolatilityQuarantineResultV1,
) -> float:
    if not result.admitted or result.legacy_value is None:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.UNADMISSIBLE_DISPOSITION,
            result.rejection_reason or result.disposition.value,
        )
    return float(result.legacy_value)


def quarantine_explicit_replay_default_volatility_v1(
    *,
    value: float = LEGACY_REPLAY_RULES_DEFAULT_VALUE,
    source_file_or_component: str,
    semantic_name: str = "legacy_explicit_replay_dynamic_scope_volatility_default",
) -> CanonicalVolatilityQuarantineResultV1:
    """Classify the historical 0.02 replay default as EXPLICIT legacy (not typed)."""
    return quarantine_legacy_volatility_input_v1(
        raw_value=float(value),
        semantic_name=semantic_name,
        source_kind="LEGACY_EXPLICIT_REPLAY_DEFAULT",
        source_file_or_component=source_file_or_component,
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only="PRODUCTIVE",
        fallback_or_default_or_floor="DEFAULT",
    )


def quarantine_explicit_test_fixture_volatility_v1(
    *,
    value: float,
    source_file_or_component: str,
    semantic_name: str = "test_fixture_explicit_dynamic_scope_volatility",
) -> CanonicalVolatilityQuarantineResultV1:
    return quarantine_legacy_volatility_input_v1(
        raw_value=float(value),
        semantic_name=semantic_name,
        source_kind="TEST_FIXTURE_EXPLICIT",
        source_file_or_component=source_file_or_component,
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only="TEST_ONLY",
        fallback_or_default_or_floor="DEFAULT",
        allow_test_fixture=True,
    )


def quarantine_historical_bar_volatility_v1(
    *,
    bar_has_volatility_estimate: bool,
    raw_value: float | None,
    typed_estimate: CanonicalVolatilityEstimateV1 | None = None,
    source_file_or_component: str = (
        "src/backtest/mv2_research_wiring_v1.py:bind_historical_bar_to_canonical_market_context_v1"
    ),
) -> CanonicalVolatilityQuarantineResultV1:
    """Fail-closed historical bind: missing column never materializes 0.2."""
    if typed_estimate is not None:
        return quarantine_legacy_volatility_input_v1(
            raw_value=raw_value,
            semantic_name="historical_bind_typed_volatility_estimate",
            source_kind="TYPED_ESTIMATE",
            source_file_or_component=source_file_or_component,
            explicit_or_implicit="EXPLICIT",
            productive_or_test_only="PRODUCTIVE",
            fallback_or_default_or_floor="TYPED",
            typed_estimate=typed_estimate,
        )
    if not bar_has_volatility_estimate or raw_value is None:
        return quarantine_legacy_volatility_input_v1(
            raw_value=None,
            semantic_name="historical_bind_missing_volatility_estimate",
            source_kind="HISTORICAL_BAR_COLUMN",
            source_file_or_component=source_file_or_component,
            explicit_or_implicit="IMPLICIT",
            productive_or_test_only="PRODUCTIVE",
            fallback_or_default_or_floor="FALLBACK",
        )
    return quarantine_legacy_volatility_input_v1(
        raw_value=float(raw_value),
        semantic_name="historical_bind_explicit_legacy_volatility_estimate",
        source_kind="HISTORICAL_BAR_COLUMN",
        source_file_or_component=source_file_or_component,
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only="PRODUCTIVE",
        fallback_or_default_or_floor="DEFAULT",
    )


def quarantine_research_fleet_join_volatility_v1(
    *,
    value: float = LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
) -> CanonicalVolatilityQuarantineResultV1:
    """Hardcoded research join 0.2 must be explicit legacy, never a silent bind bypass."""
    return quarantine_legacy_volatility_input_v1(
        raw_value=float(value),
        semantic_name="research_fleet_join_explicit_legacy_volatility_estimate",
        source_kind="RESEARCH_FLEET_JOIN_EXPLICIT",
        source_file_or_component=(
            "src/research/offline_final_research_fleet_signal_matrix_"
            "productive_input_join_materializer_v0.py"
        ),
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only="PRODUCTIVE",
        fallback_or_default_or_floor="DEFAULT",
    )


def admit_positive_volatility_without_strategy_floor_v1(
    *,
    value: float,
    source_file_or_component: str,
    semantic_name: str = "integrated_replay_scope_snapshot_volatility",
) -> CanonicalVolatilityQuarantineResultV1:
    """Admit a positive snapshot volatility. Never apply strategy floor 1e-9.

    Aligns with ``floor_policy=NONE``: unknown/zero/invalid fail-closed; admissible
    positive values pass unchanged (no numeric rematerialization).
    """
    if CANONICAL_FLOOR_POLICY != "NONE":
        _raise(
            CanonicalVolatilityQuarantineErrorCode.POLICY_CONFLICT,
            f"floor_policy_expected_NONE:actual={CANONICAL_FLOOR_POLICY!r}",
        )
    return quarantine_legacy_volatility_input_v1(
        raw_value=float(value),
        semantic_name=semantic_name,
        source_kind="SCOPE_SNAPSHOT_EXPLICIT",
        source_file_or_component=source_file_or_component,
        explicit_or_implicit="EXPLICIT",
        productive_or_test_only="PRODUCTIVE",
        fallback_or_default_or_floor="NONE",
    )


def reject_strategy_authority_volatility_floor_v1(
    *,
    proposed_floor: float = LEGACY_STRATEGY_FLOOR_VALUE,
) -> CanonicalVolatilityQuarantineResultV1:
    """Numeric floor must not heal unknown/zero/invalid volatility into strategy input."""
    result = _build_result(
        disposition=VolatilityQuarantineDispositionV1.REJECTED_POLICY_CONFLICT,
        legacy_value=float(proposed_floor),
        semantic_name="strategy_authority_volatility_floor_forbidden",
        source_kind="NUMERIC_FLOOR",
        source_file_or_component=(
            "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py:"
            "_rules_for_cycle_v1"
        ),
        explicit_or_implicit="IMPLICIT",
        productive_or_test_only="PRODUCTIVE",
        unit_known=False,
        horizon_known=False,
        estimator_known=False,
        fallback_or_default_or_floor="FLOOR",
        evidence_required=True,
        source_digest="",
        rejection_reason="floor_policy_none_forbids_strategy_authority_floor",
        authority_effect="NONE",
    )
    _raise(CanonicalVolatilityQuarantineErrorCode.FLOOR_FORBIDDEN, result.rejection_reason)
    return result  # pragma: no cover


def assert_capability_non_goals_v1() -> dict[str, Any]:
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "quarantine_owner": QUARANTINE_OWNER,
        "c1_capability_id": C1_CAPABILITY_ID,
        "typed_transport_model": TYPED_TRANSPORT_MODEL,
        "single_validation_boundary": SINGLE_VALIDATION_BOUNDARY,
        "legacy_adaptation_boundary": LEGACY_ADAPTATION_BOUNDARY,
        "gaps_closed": list(GAPS_CLOSED),
        "gaps_remaining": list(GAPS_REMAINING),
        "runtime_effect": RUNTIME_EFFECT,
        "trading_logic_effect": TRADING_LOGIC_EFFECT,
        "parameter_effect": PARAMETER_EFFECT,
        "live_authorization": LIVE_AUTHORIZATION,
        "runtime_wiring": RUNTIME_WIRING,
        "runtime_producer_cutover": RUNTIME_PRODUCER_CUTOVER,
        "parameter_research": PARAMETER_RESEARCH,
        "mv2_fallback_0_2_admissible": False,
        "floor_policy": CANONICAL_FLOOR_POLICY,
        "legacy_values_unchanged": {
            "historical_bind": LEGACY_HISTORICAL_BIND_DEFAULT_VALUE,
            "replay_rules": LEGACY_REPLAY_RULES_DEFAULT_VALUE,
            "dynamic_scope_constructor": LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE,
            "strategy_floor": LEGACY_STRATEGY_FLOOR_VALUE,
        },
        "package_marker": PACKAGE_MARKER,
    }


def assert_architecture_guards_v1(*, repo_root: Optional[Path] = None) -> dict[str, Any]:
    """Static guards: no silent defaults / strategy floors outside C2."""
    root = repo_root or Path(__file__).resolve().parents[3]
    quarantine_src = (
        root / "src/trading/master_v2/canonical_volatility_default_quarantine_v1.py"
    ).read_text(encoding="utf-8")
    wiring_src = (root / "src/backtest/mv2_research_wiring_v1.py").read_text(encoding="utf-8")
    integrated_src = (
        root / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
    ).read_text(encoding="utf-8")
    double_play_src = (root / "src/trading/master_v2/double_play_state.py").read_text(
        encoding="utf-8"
    )
    typed_src = (
        root
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    binding_src = (
        root / "src/trading/master_v2/canonical_volatility_binding_and_provenance_transport_v1.py"
    ).read_text(encoding="utf-8")

    silent_needle = 'bar.get("volatility_estimate", 0.2)'
    if silent_needle in wiring_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SILENT_DEFAULT_FORBIDDEN,
            "silent_0_2_historical_bind_still_present",
        )

    floor_needle = "max(float(snapshot.volatility_estimate), 1e-9)"
    if floor_needle in integrated_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.FLOOR_FORBIDDEN,
            "strategy_authority_1e_9_floor_still_present",
        )

    if "volatility_estimate: float = 1.0" in double_play_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SILENT_DEFAULT_FORBIDDEN,
            "productive_dynamic_scope_rules_volatility_default_1_0_still_present",
        )

    adapter_def = "def " + "adapt_canonical_volatility_estimate_to_legacy_float_v1("
    if quarantine_src.count(adapter_def) != 0:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SECOND_AUTHORITY_FORBIDDEN,
            "quarantine_must_not_redefine_typed_adapter",
        )
    if typed_src.count(adapter_def) != 1:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SECOND_AUTHORITY_FORBIDDEN,
            "typed_adapter_authority_count_invalid",
        )
    if "adapt_canonical_volatility_estimate_to_legacy_float_v1" not in binding_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SECOND_AUTHORITY_FORBIDDEN,
            "c1_must_remain_sole_binding_adapter_caller",
        )
    if "canonical_volatility_binding_and_provenance_transport_v1" not in quarantine_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.SECOND_AUTHORITY_FORBIDDEN,
            "c2_must_reuse_c1",
        )
    if ("RUNTIME_WIRING = " + "True") in quarantine_src or (
        "LIVE_AUTHORIZATION = " + "True"
    ) in quarantine_src:
        _raise(
            CanonicalVolatilityQuarantineErrorCode.POLICY_CONFLICT,
            "runtime_or_live_flags_must_remain_false",
        )
    if CANONICAL_FLOOR_POLICY != "NONE":
        _raise(
            CanonicalVolatilityQuarantineErrorCode.POLICY_CONFLICT,
            "floor_policy_must_be_none",
        )

    return {
        "guards_pass": True,
        "silent_0_2_removed": True,
        "strategy_floor_removed": True,
        "productive_1_0_default_removed": True,
        "c1_reused": True,
        "runtime_wiring": RUNTIME_WIRING,
        "floor_policy": CANONICAL_FLOOR_POLICY,
    }


__all__ = [
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CANONICAL_FLOOR_POLICY",
    "CanonicalVolatilityQuarantineError",
    "CanonicalVolatilityQuarantineErrorCode",
    "CanonicalVolatilityQuarantineEvidenceProvenanceV1",
    "CanonicalVolatilityQuarantineResultV1",
    "GAPS_CLOSED",
    "GAPS_REMAINING",
    "LEGACY_DYNAMIC_SCOPE_RULES_CONSTRUCTOR_DEFAULT_VALUE",
    "LEGACY_HISTORICAL_BIND_DEFAULT_VALUE",
    "LEGACY_REPLAY_RULES_DEFAULT_VALUE",
    "LEGACY_STRATEGY_FLOOR_VALUE",
    "LIVE_AUTHORIZATION",
    "PACKAGE_MARKER",
    "PARAMETER_EFFECT",
    "PARAMETER_RESEARCH",
    "QUARANTINE_CONTRACT_VERSION",
    "QUARANTINE_OWNER",
    "RUNTIME_EFFECT",
    "RUNTIME_PRODUCER_CUTOVER",
    "RUNTIME_WIRING",
    "TRADING_LOGIC_EFFECT",
    "VolatilityQuarantineDispositionV1",
    "admit_positive_volatility_without_strategy_floor_v1",
    "assert_architecture_guards_v1",
    "assert_capability_non_goals_v1",
    "compute_quarantine_digest_v1",
    "quarantine_explicit_replay_default_volatility_v1",
    "quarantine_explicit_test_fixture_volatility_v1",
    "quarantine_historical_bar_volatility_v1",
    "quarantine_legacy_volatility_input_v1",
    "quarantine_research_fleet_join_volatility_v1",
    "quarantine_result_to_evidence_provenance_v1",
    "reject_strategy_authority_volatility_floor_v1",
    "require_admitted_legacy_volatility_float_v1",
]
