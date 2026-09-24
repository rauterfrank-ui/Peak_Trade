"""Authorized productive parameter seam v1 (M10 Slice C).

Binds materialized governed productive configuration to the existing MV2 age-policy
consumer boundary. Does not enable enforcement, trading decisions, or external effect.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.f1_m9_scoped_owner_apply_constants_v1 import (
    is_f1_m9_scoped_runtime_apply_authority_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    DISPOSITION_CONFIGURATION_ONLY,
    STATUS_MATERIALIZED,
    GovernedProductiveConfigurationResultV1,
    verify_configuration_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    POLICY_EVALUATOR_SYMBOL,
    PRODUCTIVE_TARGET_ID,
    PRODUCTIVE_TARGET_OWNER,
    PRODUCTIVE_TARGET_VERSION,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
    TARGET_UNIT,
    validate_productive_target_id_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    THRESHOLD_STATUS_RATIFIED_NUMERIC,
    THRESHOLD_STATUS_UNRESOLVED,
    CanonicalVolatilityNumericMaxAgePolicyContractV1,
    build_ratified_numeric_threshold_policy_contract_v1,
    build_ratified_unresolved_max_age_policy_contract_v1,
    evaluate_canonical_volatility_estimate_age_policy_v1,
)

SCHEMA_VERSION: Final[str] = "authorized_productive_parameter_seam_v1"
SEAM_DOMAIN: Final[str] = "peak_trade.governance.authorized_productive_parameter_seam.v1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/AUTHORIZED_PRODUCTIVE_PARAMETER_SEAM_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = (
    "config/governance/authorized_productive_parameter_seam_v1_decision_v1.json"
)

SEAM_DISPOSITION: Final[str] = "AUTHORIZED_PRODUCTIVE_PARAMETER_SEAM_ONLY"
STATUS_BOUND: Final[str] = "BOUND_AUTHORIZED_PRODUCTIVE_PARAMETER_SEAM"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

SEAM_OWNER: Final[str] = "src.governance.authorized_productive_parameter_seam_v1"
POLICY_RESOLVER_SYMBOL: Final[str] = "resolve_canonical_volatility_max_age_policy_for_evaluation_v1"

ENFORCEMENT_AUTHORITY: Final[str] = "NONE"
TRADING_DECISION_AUTHORITY: Final[str] = "MV2_DOUBLE_PLAY"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
OPTIMIZATION_DIRECT_SEAM_AUTHORITY: Final[str] = "NONE"


@dataclass(frozen=True)
class AuthorizedProductiveParameterSeamBindRequestV1:
    configuration: GovernedProductiveConfigurationResultV1


@dataclass(frozen=True)
class AuthorizedProductiveParameterSeamResultV1:
    seam_status: str
    reason_codes: tuple[str, ...]
    seam_disposition: str
    seam_digest: str | None
    seam_record: MappingProxyType[str, Any] | None
    enforcement_authority: str = ENFORCEMENT_AUTHORITY
    trading_decision_authority: str = TRADING_DECISION_AUTHORITY
    external_effect_authorized: bool = EXTERNAL_EFFECT_AUTHORIZED


def bind_authorized_productive_parameter_seam_v1(
    request: AuthorizedProductiveParameterSeamBindRequestV1,
) -> AuthorizedProductiveParameterSeamResultV1:
    """Bind seam only from materialized governed productive configuration."""
    reason_codes: list[str] = []
    configuration = request.configuration

    if configuration.configuration_status != STATUS_MATERIALIZED:
        reason_codes.append("CONFIGURATION_NOT_MATERIALIZED")
    if configuration.configuration_disposition != DISPOSITION_CONFIGURATION_ONLY:
        reason_codes.append("CONFIGURATION_DISPOSITION_INVALID")

    record = configuration.configuration_record
    if record is None:
        reason_codes.append("CONFIGURATION_RECORD_MISSING")
        return _deny(reason_codes)

    if not verify_configuration_record_digest_v1(record):
        reason_codes.append("CONFIGURATION_DIGEST_MISMATCH")

    config_digest = str(record.get("configuration_digest") or "")
    if not is_valid_sha256_hex(config_digest):
        reason_codes.append("CONFIGURATION_DIGEST_INVALID")

    auth_digest = str(record.get("authorization_digest") or "")
    if not is_valid_sha256_hex(auth_digest):
        reason_codes.append("AUTHORIZATION_DIGEST_INVALID")

    owner_digest = str(record.get("owner_authorization_record_digest") or "")
    if not is_valid_sha256_hex(owner_digest):
        reason_codes.append("OWNER_AUTHORIZATION_RECORD_DIGEST_INVALID")

    target_id = str(record.get("productive_target_id") or "")
    target_ok, target_reason = validate_productive_target_id_v1(target_id)
    if not target_ok:
        reason_codes.append(target_reason)
    if target_id != PRODUCTIVE_TARGET_ID:
        reason_codes.append("PRODUCTIVE_TARGET_ID_NOT_EXACT_M9")

    if str(record.get("optimization_surface_id") or "") != OPTIMIZATION_SURFACE_ID:
        reason_codes.append("OPTIMIZATION_SURFACE_MISMATCH")
    if record.get("source_candidate_parameter") != SOURCE_CANDIDATE_PARAMETER:
        reason_codes.append("SOURCE_CANDIDATE_PARAMETER_MISMATCH")
    if record.get("target_policy_parameter") != TARGET_POLICY_PARAMETER:
        reason_codes.append("TARGET_POLICY_PARAMETER_MISMATCH")
    if record.get("target_unit") != TARGET_UNIT:
        reason_codes.append("TARGET_UNIT_MISMATCH")
    if record.get("threshold_capability_id") != RATIFIED_THRESHOLD_CAPABILITY_ID:
        reason_codes.append("THRESHOLD_CAPABILITY_MISMATCH")
    if record.get("enforcement_enabled") is True:
        reason_codes.append("ENFORCEMENT_FORBIDDEN")
    runtime_applied = record.get("runtime_applied") is True
    runtime_apply_authority = str(record.get("runtime_apply_authority") or "")
    if runtime_applied and not is_f1_m9_scoped_runtime_apply_authority_v1(runtime_apply_authority):
        reason_codes.append("RUNTIME_APPLY_FORBIDDEN")
    if runtime_applied and not record.get("owner_apply_authorization_record_digest"):
        reason_codes.append("OWNER_APPLY_AUTHORIZATION_DIGEST_MISSING")

    config_numeric = record.get("numeric_max_age_seconds")
    authorized_numeric = record.get("authorized_candidate_max_age_seconds")
    if config_numeric != authorized_numeric:
        reason_codes.append("CONFIGURATION_NUMERIC_VALUE_INTERNAL_MISMATCH")
    if not isinstance(config_numeric, (int, float)) or isinstance(config_numeric, bool):
        reason_codes.append("CONFIGURATION_NUMERIC_INVALID")

    if reason_codes:
        return _deny(reason_codes)

    numeric = float(config_numeric)
    seam_id = str(uuid.uuid5(uuid.NAMESPACE_URL, config_digest))

    seam_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": SEAM_DOMAIN,
        "seam_id": seam_id,
        "seam_disposition": SEAM_DISPOSITION,
        "seam_status": STATUS_BOUND,
        "seam_owner": SEAM_OWNER,
        "configuration_id": record.get("configuration_id"),
        "configuration_digest": config_digest,
        "authorization_id": record.get("authorization_id"),
        "authorization_digest": auth_digest,
        "owner_authorization_record_digest": owner_digest,
        "owner_authorization_id": record.get("owner_authorization_id"),
        "ingress_digest": record.get("ingress_digest"),
        "productive_target_id": target_id,
        "productive_target_version": record.get("productive_target_version"),
        "productive_target_owner": PRODUCTIVE_TARGET_OWNER,
        "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
        "target_policy_parameter": TARGET_POLICY_PARAMETER,
        "target_unit": TARGET_UNIT,
        "numeric_max_age_seconds": numeric,
        "authorized_candidate_max_age_seconds": numeric,
        "exact_value_preservation": True,
        "threshold_capability_id": RATIFIED_THRESHOLD_CAPABILITY_ID,
        "threshold_capability_version": RATIFIED_THRESHOLD_CAPABILITY_VERSION,
        "threshold_capability_semantic_status": THRESHOLD_STATUS_RATIFIED_NUMERIC,
        "policy_consumer_module": POLICY_CONSUMER_MODULE,
        "policy_evaluator_symbol": POLICY_EVALUATOR_SYMBOL,
        "policy_resolver_symbol": POLICY_RESOLVER_SYMBOL,
        "lineage_chain": record.get("lineage_chain"),
        "optimization_provenance": dict(record.get("optimization_provenance") or {}),
        "candidate_parameter_value_digest": record.get("candidate_parameter_value_digest"),
        "enforcement_enabled": False,
        "enforcement_authority": ENFORCEMENT_AUTHORITY,
        "trading_decision_authority": TRADING_DECISION_AUTHORITY,
        "consumer_bound": runtime_applied,
        "runtime_applied": runtime_applied,
        "runtime_apply_authority": runtime_apply_authority,
        "owner_apply_authorization_record_digest": record.get(
            "owner_apply_authorization_record_digest"
        ),
        "productive_apply_authorization_digest": record.get(
            "productive_apply_authorization_digest"
        ),
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
    seam_digest = compute_content_sha256(seam_body)
    seam_body["seam_digest"] = seam_digest

    return AuthorizedProductiveParameterSeamResultV1(
        seam_status=STATUS_BOUND,
        reason_codes=("BOUND_AUTHORIZED_PRODUCTIVE_PARAMETER_SEAM_ONLY",),
        seam_disposition=SEAM_DISPOSITION,
        seam_digest=seam_digest,
        seam_record=MappingProxyType(seam_body),
    )


def _deny(reason_codes: list[str]) -> AuthorizedProductiveParameterSeamResultV1:
    return AuthorizedProductiveParameterSeamResultV1(
        seam_status=STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        seam_disposition=SEAM_DISPOSITION,
        seam_digest=None,
        seam_record=None,
    )


def verify_seam_record_digest_v1(seam_record: Mapping[str, Any]) -> bool:
    stored = seam_record.get("seam_digest")
    if not isinstance(stored, str) or not is_valid_sha256_hex(stored):
        return False
    body = {key: value for key, value in dict(seam_record).items() if key != "seam_digest"}
    return compute_content_sha256(body) == stored


def resolve_age_policy_from_authorized_seam_record_v1(
    seam_record: Mapping[str, Any] | None,
) -> CanonicalVolatilityNumericMaxAgePolicyContractV1:
    """Fail-closed: invalid/missing seam → unresolved ratified policy."""
    if seam_record is None:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if not verify_seam_record_digest_v1(seam_record):
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if seam_record.get("seam_status") != STATUS_BOUND:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if seam_record.get("productive_target_id") != PRODUCTIVE_TARGET_ID:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if seam_record.get("policy_consumer_module") != POLICY_CONSUMER_MODULE:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if seam_record.get("enforcement_enabled") is True:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    numeric = seam_record.get("numeric_max_age_seconds")
    if not isinstance(numeric, (int, float)) or isinstance(numeric, bool):
        return build_ratified_unresolved_max_age_policy_contract_v1()
    config_numeric = seam_record.get("authorized_candidate_max_age_seconds")
    if float(numeric) != float(config_numeric):
        return build_ratified_unresolved_max_age_policy_contract_v1()
    policy = build_ratified_numeric_threshold_policy_contract_v1(
        numeric_max_age_seconds=float(numeric),
    )
    if policy.enforcement_enabled is not False:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    if policy.threshold_status != THRESHOLD_STATUS_RATIFIED_NUMERIC:
        return build_ratified_unresolved_max_age_policy_contract_v1()
    return policy


def evaluate_age_policy_at_consumer_boundary_v1(
    *,
    seam_record: Mapping[str, Any] | None,
    estimate: Any,
    reference_market_event_time: Any,
    presence_status: Any,
    reuse_status: Any = None,
    restart_status: Any = None,
    clock_trust_status: Any = None,
    data_integrity_status: Any = None,
) -> Any:
    """Evaluate existing age-policy consumer with optional authorized seam policy."""
    from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
        VolatilityRestartStatusV1,
        VolatilityReuseStatusV1,
    )
    from trading.master_v2.canonical_market_context_v1 import (
        ClockTrustStatus,
        DataIntegrityStatus,
    )

    policy = resolve_age_policy_from_authorized_seam_record_v1(seam_record)
    return evaluate_canonical_volatility_estimate_age_policy_v1(
        estimate=estimate,
        reference_market_event_time=reference_market_event_time,
        presence_status=presence_status,
        reuse_status=reuse_status or VolatilityReuseStatusV1.NOT_APPLICABLE,
        restart_status=restart_status or VolatilityRestartStatusV1.NOT_APPLICABLE,
        clock_trust_status=clock_trust_status or ClockTrustStatus.TRUSTED,
        data_integrity_status=data_integrity_status or DataIntegrityStatus.TRUSTED,
        policy=policy,
    )


def optimization_can_bind_seam_directly_v1() -> bool:
    return False
