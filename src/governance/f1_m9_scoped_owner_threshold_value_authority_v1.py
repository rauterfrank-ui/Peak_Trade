"""F1/M9 scoped Owner Threshold Value authority adjudicator v1 (Owner-ratified policy only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationResultV1,
)
from src.governance.f1_m9_owner_threshold_value_authorization_record_v1 import (
    OwnerThresholdValueAuthorizationInputV1,
    OwnerThresholdValueAuthorizationRecordError,
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
    verify_owner_threshold_value_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
    PerIngressBindingStatusV1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    ProductiveApplyLedgerError,
    assert_not_revoked_v1,
    assert_revocation_state_available_v1,
    find_apply_ledger_entry_v1,
)
from src.governance.f1_m9_scoped_owner_apply_constants_v1 import (
    is_f1_m9_scoped_runtime_apply_authority_v1,
)
from src.governance.f1_m9_scoped_owner_threshold_value_constants_v1 import (
    RUNTIME_THRESHOLD_VALUE_AUTHORITY,
)
from src.governance.f1_m9_threshold_value_authorization_ledger_v1 import (
    F1M9ThresholdValueAuthorizationLedgerPathsV1,
    ThresholdValueAuthorizationLedgerError,
    append_threshold_ledger_entry_v1,
    assert_threshold_not_revoked_v1,
    assert_threshold_revocation_state_available_v1,
    find_threshold_ledger_entry_v1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import F1M9ProductiveApplyLedgerPathsV1
from src.governance.governed_productive_configuration_v1 import (
    GovernedProductiveConfigurationResultV1,
    STATUS_MATERIALIZED,
    verify_configuration_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.m9_volatility_numeric_max_age_ratified_threshold_capability_v1 import (
    CAPABILITY_ID as RATIFIED_THRESHOLD_CAPABILITY_ID,
    CAPABILITY_VERSION as RATIFIED_THRESHOLD_CAPABILITY_VERSION,
    ThresholdValueAuthorizationStatusV1,
    validate_numeric_max_age_seconds_domain_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    F1_M9_SCOPE_PAIR_ID,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_scoped_owner_threshold_value_authority/v1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_SCOPED_OWNER_THRESHOLD_VALUE_AUTHORITY_NORMATIVE_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_scoped_owner_threshold_value_authority_v1_decision_v1.json"
)
OWNER_POLICY_DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_owner_threshold_value_policy_owner_adjudication_v1_decision_v1.json"
)

WORKPACKAGE_ID: Final[str] = "F1_M9_THRESHOLD_VALUE_AUTHORITY_AND_HOT_PATH_ADMISSION_CLOSURE_V1"

STATUS_THRESHOLD_AUTHORIZED: Final[str] = "F1_M9_OWNER_THRESHOLD_VALUE_AUTHORIZED"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

GLOBAL_THRESHOLD_VALUE_RATIFIED: Final[bool] = False
ENFORCEMENT_ENABLED: Final[bool] = False
CONCRETE_THRESHOLD_VALUE_AUTHORIZED: Final[bool] = False


class ThresholdValueAdjudicationStatusV1(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED_FAIL_CLOSED = "DENIED_FAIL_CLOSED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"


@dataclass(frozen=True, slots=True)
class F1M9ScopedOwnerThresholdValueAdjudicationRequestV1:
    owner_threshold_input: OwnerThresholdValueAuthorizationInputV1
    per_ingress_binding: PerIngressAuthorizationBindingV1
    authorization: ExplicitProductiveAuthorizationResultV1
    configuration: GovernedProductiveConfigurationResultV1
    registry_digest: str
    apply_ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    threshold_ledger_paths: F1M9ThresholdValueAuthorizationLedgerPathsV1
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class F1M9ScopedOwnerThresholdValueAdjudicationResultV1:
    threshold_status: str
    reason_codes: tuple[str, ...]
    threshold_value_authorized: bool
    runtime_threshold_authority: str
    configuration_after_threshold: GovernedProductiveConfigurationResultV1 | None
    threshold_value_authorization_record_digest: str | None
    threshold_ledger_entry_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "configuration_after_threshold": None,
            "reason_codes": list(self.reason_codes),
            "runtime_threshold_authority": self.runtime_threshold_authority,
            "threshold_ledger_entry_digest": self.threshold_ledger_entry_digest,
            "threshold_status": self.threshold_status,
            "threshold_value_authorization_record_digest": (
                self.threshold_value_authorization_record_digest
            ),
            "threshold_value_authorized": self.threshold_value_authorized,
        }


def _deny(reason_codes: list[str]) -> F1M9ScopedOwnerThresholdValueAdjudicationResultV1:
    return F1M9ScopedOwnerThresholdValueAdjudicationResultV1(
        threshold_status=STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        threshold_value_authorized=False,
        runtime_threshold_authority="NONE",
        configuration_after_threshold=None,
        threshold_value_authorization_record_digest=None,
        threshold_ledger_entry_digest=None,
    )


def _validate_temporal_validity_v1(
    record: Mapping[str, Any],
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    try:
        not_before = parse_aware_utc_datetime_v1(record.get("not_before"), field_name="not_before")
        expires_at = parse_aware_utc_datetime_v1(record.get("expires_at"), field_name="expires_at")
    except OwnerThresholdValueAuthorizationRecordError as exc:
        return [str(exc)]
    if expires_at <= not_before:
        reasons.append("THRESHOLD_EXPIRY_NOT_AFTER_NOT_BEFORE")
    if now < not_before:
        reasons.append("THRESHOLD_NOT_YET_VALID")
    if now >= expires_at:
        reasons.append("THRESHOLD_EXPIRED")
    return reasons


def _validate_lineage_bindings_v1(
    *,
    record: Mapping[str, Any],
    binding: PerIngressAuthorizationBindingV1,
    authorization: ExplicitProductiveAuthorizationResultV1,
    configuration: GovernedProductiveConfigurationResultV1,
    registry_digest: str,
) -> list[str]:
    reasons: list[str] = []
    if binding.status != PerIngressBindingStatusV1.BOUND:
        reasons.append("PER_INGRESS_BINDING_NOT_BOUND")

    config_record = configuration.configuration_record
    auth_record = authorization.authorization_record
    if config_record is None or auth_record is None:
        reasons.append("LINEAGE_RECORD_MISSING")
        return reasons

    if not verify_configuration_record_digest_v1(dict(config_record)):
        reasons.append("CONFIGURATION_DIGEST_INVALID")

    if config_record.get("runtime_applied") is not True:
        reasons.append("PRODUCTIVE_APPLY_REQUIRED_BEFORE_THRESHOLD")
    runtime_apply_authority = str(config_record.get("runtime_apply_authority") or "")
    if not is_f1_m9_scoped_runtime_apply_authority_v1(runtime_apply_authority):
        reasons.append("RUNTIME_APPLY_AUTHORITY_INVALID_FOR_THRESHOLD")

    owner_apply_digest = str(config_record.get("owner_apply_authorization_record_digest") or "")
    if not owner_apply_digest or not is_valid_sha256_hex(owner_apply_digest):
        reasons.append("OWNER_APPLY_AUTHORIZATION_DIGEST_MISSING")

    target_contract = build_productive_target_contract_v1()
    contract_digest = str(target_contract.get("contract_digest") or "")

    checks: tuple[tuple[str, str, str], ...] = (
        ("scoped_join_pair_id", str(record.get("scoped_join_pair_id") or ""), F1_M9_SCOPE_PAIR_ID),
        ("registry_digest", str(record.get("registry_digest") or ""), registry_digest),
        (
            "ingress_digest",
            str(record.get("ingress_digest") or ""),
            str(config_record.get("ingress_digest") or ""),
        ),
        (
            "per_ingress_binding_digest",
            str(record.get("per_ingress_binding_digest") or ""),
            str(binding.binding_digest or ""),
        ),
        (
            "owner_authorization_record_digest",
            str(record.get("owner_authorization_record_digest") or ""),
            str(config_record.get("owner_authorization_record_digest") or ""),
        ),
        (
            "authorization_id",
            str(record.get("authorization_id") or ""),
            str(config_record.get("authorization_id") or ""),
        ),
        (
            "authorization_digest",
            str(record.get("authorization_digest") or ""),
            str(config_record.get("authorization_digest") or ""),
        ),
        (
            "configuration_id",
            str(record.get("configuration_id") or ""),
            str(config_record.get("configuration_id") or ""),
        ),
        (
            "configuration_digest",
            str(record.get("configuration_digest") or ""),
            str(config_record.get("configuration_digest") or ""),
        ),
        (
            "candidate_parameter_value_digest",
            str(record.get("candidate_parameter_value_digest") or ""),
            str(config_record.get("candidate_parameter_value_digest") or ""),
        ),
        (
            "productive_target_id",
            str(record.get("productive_target_id") or ""),
            PRODUCTIVE_TARGET_ID,
        ),
        (
            "productive_target_version",
            str(record.get("productive_target_version") or ""),
            str(config_record.get("productive_target_version") or ""),
        ),
        (
            "productive_target_contract_digest",
            str(record.get("productive_target_contract_digest") or ""),
            contract_digest,
        ),
        (
            "ratified_threshold_capability_id",
            str(record.get("ratified_threshold_capability_id") or ""),
            str(config_record.get("threshold_capability_id") or RATIFIED_THRESHOLD_CAPABILITY_ID),
        ),
        (
            "ratified_threshold_capability_version",
            str(record.get("ratified_threshold_capability_version") or ""),
            str(
                config_record.get("threshold_capability_version")
                or RATIFIED_THRESHOLD_CAPABILITY_VERSION
            ),
        ),
        (
            "owner_apply_authorization_record_digest",
            str(record.get("owner_apply_authorization_record_digest") or ""),
            owner_apply_digest,
        ),
        (
            "productive_apply_authorization_digest",
            str(record.get("productive_apply_authorization_digest") or ""),
            str(config_record.get("productive_apply_authorization_digest") or owner_apply_digest),
        ),
    )
    digest_fields = {
        "registry_digest",
        "ingress_digest",
        "per_ingress_binding_digest",
        "owner_authorization_record_digest",
        "authorization_digest",
        "configuration_digest",
        "candidate_parameter_value_digest",
        "productive_target_contract_digest",
        "owner_apply_authorization_record_digest",
        "productive_apply_authorization_digest",
    }
    for field, record_value, expected in checks:
        if not record_value:
            reasons.append(f"{field.upper()}_MISSING")
            continue
        if field in digest_fields and not is_valid_sha256_hex(record_value):
            reasons.append(f"{field.upper()}_INVALID")
            continue
        if record_value != expected:
            reasons.append(f"{field.upper()}_MISMATCH")

    config_numeric = config_record.get("authorized_candidate_max_age_seconds")
    threshold_numeric = record.get("threshold_numeric_max_age_seconds")
    if not isinstance(threshold_numeric, (int, float)) or isinstance(threshold_numeric, bool):
        reasons.append("THRESHOLD_NUMERIC_INVALID")
    elif float(threshold_numeric) != float(config_numeric):
        reasons.append("THRESHOLD_NUMERIC_CONFIGURATION_MISMATCH")
    elif float(threshold_numeric) != float(config_record.get("numeric_max_age_seconds")):
        reasons.append("THRESHOLD_NUMERIC_INTERNAL_MISMATCH")

    if isinstance(threshold_numeric, (int, float)) and not isinstance(threshold_numeric, bool):
        domain_ok, domain_reason = validate_numeric_max_age_seconds_domain_v1(threshold_numeric)
        if not domain_ok:
            reasons.append(domain_reason)

    if (
        str(record.get("ratified_threshold_capability_id") or "")
        != RATIFIED_THRESHOLD_CAPABILITY_ID
    ):
        reasons.append("RATIFIED_THRESHOLD_CAPABILITY_ID_MISMATCH")

    return reasons


def transition_configuration_for_valid_threshold_v1(
    configuration: GovernedProductiveConfigurationResultV1,
    *,
    threshold_value_authorization_record_digest: str,
    threshold_numeric_max_age_seconds: float,
) -> GovernedProductiveConfigurationResultV1:
    """Threshold boundary transition only; does not enable enforcement or global decided flags."""
    record = configuration.configuration_record
    if record is None or configuration.configuration_status != STATUS_MATERIALIZED:
        raise ValueError("CONFIGURATION_NOT_MATERIALIZED")

    body = dict(record)
    body["runtime_threshold_authority"] = RUNTIME_THRESHOLD_VALUE_AUTHORITY
    body["threshold_value_authorization_status"] = (
        ThresholdValueAuthorizationStatusV1.AUTHORIZED.value
    )
    body["threshold_value_authorization_digest"] = threshold_value_authorization_record_digest
    body["threshold_numeric_max_age_seconds"] = float(threshold_numeric_max_age_seconds)
    body["scoped_owner_threshold_value_authorized"] = True
    body["global_threshold_value_ratified"] = GLOBAL_THRESHOLD_VALUE_RATIFIED
    body["enforcement_enabled"] = ENFORCEMENT_ENABLED

    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body.pop("configuration_digest", None)
    body["configuration_digest"] = compute_content_sha256(body)

    return GovernedProductiveConfigurationResultV1(
        configuration_status=configuration.configuration_status,
        reason_codes=("F1_M9_THRESHOLD_VALUE_RUNTIME_TRANSITION",),
        configuration_disposition=configuration.configuration_disposition,
        configuration_digest=str(body["configuration_digest"]),
        configuration_record=MappingProxyType(body),
        runtime_apply_authority=configuration.runtime_apply_authority,
    )


def evaluate_f1_m9_scoped_owner_threshold_value_authority_v1(
    request: F1M9ScopedOwnerThresholdValueAdjudicationRequestV1,
) -> F1M9ScopedOwnerThresholdValueAdjudicationResultV1:
    """Fail-closed F1/M9 threshold value adjudication; dedicated Owner record required."""
    reason_codes: list[str] = []
    now = request.evaluation_time_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    if request.configuration.configuration_status != STATUS_MATERIALIZED:
        return _deny(["CONFIGURATION_NOT_MATERIALIZED"])

    threshold_input = request.owner_threshold_input
    record = threshold_input.owner_threshold_authorization_record
    if threshold_input.owner_threshold_authorization_record_digest != record.get(
        "threshold_value_authorization_record_digest"
    ):
        reason_codes.append("OWNER_THRESHOLD_INPUT_DIGEST_MISMATCH")
    if not verify_owner_threshold_value_authorization_record_digest_v1(record):
        reason_codes.append("OWNER_THRESHOLD_RECORD_DIGEST_INVALID")

    reason_codes.extend(
        _validate_lineage_bindings_v1(
            record=record,
            binding=request.per_ingress_binding,
            authorization=request.authorization,
            configuration=request.configuration,
            registry_digest=request.registry_digest,
        )
    )
    reason_codes.extend(_validate_temporal_validity_v1(record, now))

    threshold_digest = str(record.get("threshold_value_authorization_record_digest") or "")
    config_digest = str(record.get("configuration_digest") or "")
    apply_digest = str(record.get("owner_apply_authorization_record_digest") or "")

    try:
        assert_revocation_state_available_v1(request.apply_ledger_paths.revocation_ledger_path)
        assert_not_revoked_v1(
            revocation_ledger_path=request.apply_ledger_paths.revocation_ledger_path,
            owner_apply_authorization_record_digest=apply_digest,
            configuration_digest=config_digest,
        )
    except ProductiveApplyLedgerError as exc:
        reason_codes.append(str(exc))

    apply_entry = find_apply_ledger_entry_v1(
        apply_ledger_path=request.apply_ledger_paths.apply_ledger_path,
        owner_apply_authorization_record_digest=apply_digest,
    )
    if apply_entry is None:
        reason_codes.append("OWNER_APPLY_LEDGER_ENTRY_MISSING")
    elif apply_entry["configuration_digest"] != config_digest:
        reason_codes.append("OWNER_APPLY_LEDGER_CONFIGURATION_MISMATCH")

    try:
        assert_threshold_revocation_state_available_v1(
            request.threshold_ledger_paths.threshold_revocation_ledger_path
        )
        assert_threshold_not_revoked_v1(
            revocation_ledger_path=request.threshold_ledger_paths.threshold_revocation_ledger_path,
            threshold_value_authorization_record_digest=threshold_digest,
            configuration_digest=config_digest,
        )
    except ThresholdValueAuthorizationLedgerError as exc:
        reason_codes.append(str(exc))

    if reason_codes:
        return _deny(reason_codes)

    existing = find_threshold_ledger_entry_v1(
        threshold_ledger_path=request.threshold_ledger_paths.threshold_ledger_path,
        threshold_value_authorization_record_digest=threshold_digest,
    )
    threshold_numeric = float(record["threshold_numeric_max_age_seconds"])
    if existing is not None:
        if existing["configuration_digest"] != config_digest:
            return _deny(["THRESHOLD_LEDGER_IDEMPOTENCY_CONFIGURATION_MISMATCH"])
        transitioned = transition_configuration_for_valid_threshold_v1(
            request.configuration,
            threshold_value_authorization_record_digest=threshold_digest,
            threshold_numeric_max_age_seconds=threshold_numeric,
        )
        return F1M9ScopedOwnerThresholdValueAdjudicationResultV1(
            threshold_status=ThresholdValueAdjudicationStatusV1.IDEMPOTENT_REPLAY.value,
            reason_codes=("THRESHOLD_IDEMPOTENT_REPLAY",),
            threshold_value_authorized=True,
            runtime_threshold_authority=RUNTIME_THRESHOLD_VALUE_AUTHORITY,
            configuration_after_threshold=transitioned,
            threshold_value_authorization_record_digest=threshold_digest,
            threshold_ledger_entry_digest=str(existing.get("threshold_ledger_entry_digest") or ""),
        )

    try:
        ledger_entry = append_threshold_ledger_entry_v1(
            threshold_ledger_path=request.threshold_ledger_paths.threshold_ledger_path,
            threshold_value_authorization_record_digest=threshold_digest,
            configuration_digest=config_digest,
            owner_apply_authorization_record_digest=apply_digest,
            authorized_at=format_aware_utc_datetime_v1(now),
        )
    except ThresholdValueAuthorizationLedgerError as exc:
        return _deny([str(exc)])

    transitioned = transition_configuration_for_valid_threshold_v1(
        request.configuration,
        threshold_value_authorization_record_digest=threshold_digest,
        threshold_numeric_max_age_seconds=threshold_numeric,
    )
    return F1M9ScopedOwnerThresholdValueAdjudicationResultV1(
        threshold_status=STATUS_THRESHOLD_AUTHORIZED,
        reason_codes=("F1_M9_OWNER_THRESHOLD_VALUE_OK",),
        threshold_value_authorized=True,
        runtime_threshold_authority=RUNTIME_THRESHOLD_VALUE_AUTHORITY,
        configuration_after_threshold=transitioned,
        threshold_value_authorization_record_digest=threshold_digest,
        threshold_ledger_entry_digest=str(ledger_entry.get("threshold_ledger_entry_digest") or ""),
    )


__all__ = [
    "CONCRETE_THRESHOLD_VALUE_AUTHORIZED",
    "DECISION_CONFIG",
    "F1M9ScopedOwnerThresholdValueAdjudicationRequestV1",
    "F1M9ScopedOwnerThresholdValueAdjudicationResultV1",
    "NORMATIVE_SPEC",
    "OWNER_POLICY_DECISION_CONFIG",
    "RUNTIME_THRESHOLD_VALUE_AUTHORITY",
    "SCHEMA_VERSION",
    "STATUS_DENIED",
    "STATUS_THRESHOLD_AUTHORIZED",
    "ThresholdValueAdjudicationStatusV1",
    "WORKPACKAGE_ID",
    "evaluate_f1_m9_scoped_owner_threshold_value_authority_v1",
    "transition_configuration_for_valid_threshold_v1",
]
