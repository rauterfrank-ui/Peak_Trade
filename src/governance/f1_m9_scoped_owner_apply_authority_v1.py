"""F1/M9 scoped Owner Productive Apply adjudicator v1 (Owner-ratified policy only)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.governance.explicit_productive_authorization_v1 import (
    ExplicitProductiveAuthorizationResultV1,
)
from src.governance.f1_m9_owner_apply_authorization_record_v1 import (
    OwnerApplyAuthorizationInputV1,
    OwnerApplyAuthorizationRecordError,
    format_aware_utc_datetime_v1,
    parse_aware_utc_datetime_v1,
    verify_owner_apply_authorization_record_digest_v1,
)
from src.governance.f1_m9_per_ingress_productive_authorization_binding_v1 import (
    PerIngressAuthorizationBindingV1,
    PerIngressBindingStatusV1,
)
from src.governance.f1_m9_productive_apply_ledger_v1 import (
    F1M9ProductiveApplyLedgerPathsV1,
    ProductiveApplyLedgerError,
    append_apply_ledger_entry_v1,
    assert_not_revoked_v1,
    assert_revocation_state_available_v1,
    find_apply_ledger_entry_v1,
)
from src.governance.governed_productive_configuration_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    GovernedProductiveConfigurationResultV1,
    STATUS_MATERIALIZED,
    verify_configuration_record_digest_v1,
)
from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    PRODUCTIVE_TARGET_ID,
    build_productive_target_contract_v1,
)
from src.governance.v32_d28_d29_scoped_optimization_productive_join_policy_v1 import (
    F1_M9_SCOPE_PAIR_ID,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "f1_m9_scoped_owner_apply_authority/v1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/F1_M9_SCOPED_OWNER_APPLY_AUTHORITY_NORMATIVE_V1.md"
DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_scoped_owner_apply_authority_v1_decision_v1.json"
)
OWNER_POLICY_DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_owner_apply_policy_owner_adjudication_v1_decision_v1.json"
)

from src.governance.f1_m9_scoped_owner_apply_constants_v1 import (
    RUNTIME_APPLY_AUTHORITY_VALUE,
    is_f1_m9_scoped_runtime_apply_authority_v1,
)

WORKPACKAGE_ID: Final[str] = "F1_M9_SCOPED_OWNER_PRODUCTIVE_APPLY_AUTHORITY_V1"

STATUS_APPLY_AUTHORIZED: Final[str] = "F1_M9_OWNER_APPLY_AUTHORIZED"
STATUS_DENIED: Final[str] = "DENIED_FAIL_CLOSED"

GLOBAL_THRESHOLD_VALUE_RATIFIED: Final[bool] = False
ENFORCEMENT_ENABLED: Final[bool] = False


class ProductiveApplyAdjudicationStatusV1(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED_FAIL_CLOSED = "DENIED_FAIL_CLOSED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"


@dataclass(frozen=True, slots=True)
class F1M9ScopedOwnerApplyAdjudicationRequestV1:
    owner_apply_input: OwnerApplyAuthorizationInputV1
    per_ingress_binding: PerIngressAuthorizationBindingV1
    authorization: ExplicitProductiveAuthorizationResultV1
    configuration: GovernedProductiveConfigurationResultV1
    registry_digest: str
    ledger_paths: F1M9ProductiveApplyLedgerPathsV1
    evaluation_time_utc: datetime | None = None


@dataclass(frozen=True, slots=True)
class F1M9ScopedOwnerApplyAdjudicationResultV1:
    apply_status: str
    reason_codes: tuple[str, ...]
    productive_apply_authorized: bool
    runtime_apply_authority: str
    configuration_after_apply: GovernedProductiveConfigurationResultV1 | None
    owner_apply_authorization_record_digest: str | None
    apply_ledger_entry_digest: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "apply_ledger_entry_digest": self.apply_ledger_entry_digest,
            "apply_status": self.apply_status,
            "owner_apply_authorization_record_digest": (
                self.owner_apply_authorization_record_digest
            ),
            "productive_apply_authorized": self.productive_apply_authorized,
            "reason_codes": list(self.reason_codes),
            "runtime_apply_authority": self.runtime_apply_authority,
        }


def _deny(reason_codes: list[str]) -> F1M9ScopedOwnerApplyAdjudicationResultV1:
    return F1M9ScopedOwnerApplyAdjudicationResultV1(
        apply_status=STATUS_DENIED,
        reason_codes=tuple(reason_codes),
        productive_apply_authorized=False,
        runtime_apply_authority="NONE",
        configuration_after_apply=None,
        owner_apply_authorization_record_digest=None,
        apply_ledger_entry_digest=None,
    )


def _validate_temporal_validity_v1(
    record: Mapping[str, Any],
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    try:
        not_before = parse_aware_utc_datetime_v1(record.get("not_before"), field_name="not_before")
        expires_at = parse_aware_utc_datetime_v1(record.get("expires_at"), field_name="expires_at")
    except OwnerApplyAuthorizationRecordError as exc:
        return [str(exc)]
    if expires_at <= not_before:
        reasons.append("APPLY_EXPIRY_NOT_AFTER_NOT_BEFORE")
    if now < not_before:
        reasons.append("APPLY_NOT_YET_VALID")
    if now >= expires_at:
        reasons.append("APPLY_EXPIRED")
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
            "binding_digest",
            str(record.get("binding_digest") or ""),
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
    )
    digest_fields = {
        "registry_digest",
        "ingress_digest",
        "binding_digest",
        "owner_authorization_record_digest",
        "authorization_digest",
        "configuration_digest",
        "candidate_parameter_value_digest",
        "productive_target_contract_digest",
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

    if str(record.get("productive_target_id") or "") != PRODUCTIVE_TARGET_ID:
        reasons.append("PRODUCTIVE_TARGET_NOT_F1_M9")

    return reasons


def transition_configuration_for_valid_apply_v1(
    configuration: GovernedProductiveConfigurationResultV1,
    *,
    owner_apply_authorization_record_digest: str,
) -> GovernedProductiveConfigurationResultV1:
    """Apply boundary transition only; does not ratify threshold/value for hot path."""
    record = configuration.configuration_record
    if record is None or configuration.configuration_status != STATUS_MATERIALIZED:
        raise ValueError("CONFIGURATION_NOT_MATERIALIZED")

    body = dict(record)
    body["runtime_apply_authority"] = RUNTIME_APPLY_AUTHORITY_VALUE
    body["runtime_applied"] = True
    body["consumer_bound"] = True
    body["owner_apply_authorization_record_digest"] = owner_apply_authorization_record_digest
    body["productive_apply_authorization_digest"] = owner_apply_authorization_record_digest
    body["global_threshold_value_ratified"] = GLOBAL_THRESHOLD_VALUE_RATIFIED
    body["enforcement_enabled"] = ENFORCEMENT_ENABLED
    body["external_effect_authorized"] = EXTERNAL_EFFECT_AUTHORIZED
    body["threshold_value_ratified"] = False
    body["candidate_value_applied"] = False

    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    body.pop("configuration_digest", None)
    body["configuration_digest"] = compute_content_sha256(body)

    return GovernedProductiveConfigurationResultV1(
        configuration_status=configuration.configuration_status,
        reason_codes=("F1_M9_RUNTIME_APPLY_TRANSITION",),
        configuration_disposition=configuration.configuration_disposition,
        configuration_digest=str(body["configuration_digest"]),
        configuration_record=MappingProxyType(body),
        runtime_apply_authority=RUNTIME_APPLY_AUTHORITY_VALUE,
    )


def evaluate_f1_m9_scoped_owner_productive_apply_v1(
    request: F1M9ScopedOwnerApplyAdjudicationRequestV1,
) -> F1M9ScopedOwnerApplyAdjudicationResultV1:
    """Fail-closed F1/M9 apply adjudication; explicit Owner Apply record required."""
    reason_codes: list[str] = []
    now = request.evaluation_time_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    if request.configuration.configuration_status != STATUS_MATERIALIZED:
        return _deny(["CONFIGURATION_NOT_MATERIALIZED"])

    apply_input = request.owner_apply_input
    record = apply_input.owner_apply_authorization_record
    if apply_input.owner_apply_authorization_record_digest != record.get(
        "owner_apply_authorization_record_digest"
    ):
        reason_codes.append("OWNER_APPLY_INPUT_DIGEST_MISMATCH")
    if not verify_owner_apply_authorization_record_digest_v1(record):
        reason_codes.append("OWNER_APPLY_RECORD_DIGEST_INVALID")

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

    apply_digest = str(record.get("owner_apply_authorization_record_digest") or "")
    config_digest = str(record.get("configuration_digest") or "")

    try:
        assert_revocation_state_available_v1(request.ledger_paths.revocation_ledger_path)
        assert_not_revoked_v1(
            revocation_ledger_path=request.ledger_paths.revocation_ledger_path,
            owner_apply_authorization_record_digest=apply_digest,
            configuration_digest=config_digest,
        )
    except ProductiveApplyLedgerError as exc:
        reason_codes.append(str(exc))

    if reason_codes:
        return _deny(reason_codes)

    existing = find_apply_ledger_entry_v1(
        apply_ledger_path=request.ledger_paths.apply_ledger_path,
        owner_apply_authorization_record_digest=apply_digest,
    )
    if existing is not None:
        if existing["configuration_digest"] != config_digest:
            return _deny(["APPLY_LEDGER_IDEMPOTENCY_CONFIGURATION_MISMATCH"])
        applied_config = transition_configuration_for_valid_apply_v1(
            request.configuration,
            owner_apply_authorization_record_digest=apply_digest,
        )
        return F1M9ScopedOwnerApplyAdjudicationResultV1(
            apply_status=ProductiveApplyAdjudicationStatusV1.IDEMPOTENT_REPLAY.value,
            reason_codes=("APPLY_IDEMPOTENT_REPLAY",),
            productive_apply_authorized=True,
            runtime_apply_authority=RUNTIME_APPLY_AUTHORITY_VALUE,
            configuration_after_apply=applied_config,
            owner_apply_authorization_record_digest=apply_digest,
            apply_ledger_entry_digest=str(existing.get("apply_ledger_entry_digest") or ""),
        )

    try:
        ledger_entry = append_apply_ledger_entry_v1(
            apply_ledger_path=request.ledger_paths.apply_ledger_path,
            owner_apply_authorization_record_digest=apply_digest,
            configuration_digest=config_digest,
            authorization_digest=str(record.get("authorization_digest") or ""),
            ingress_digest=str(record.get("ingress_digest") or ""),
            applied_at=format_aware_utc_datetime_v1(now),
        )
    except ProductiveApplyLedgerError as exc:
        return _deny([str(exc)])

    applied_config = transition_configuration_for_valid_apply_v1(
        request.configuration,
        owner_apply_authorization_record_digest=apply_digest,
    )
    return F1M9ScopedOwnerApplyAdjudicationResultV1(
        apply_status=STATUS_APPLY_AUTHORIZED,
        reason_codes=("F1_M9_OWNER_APPLY_OK",),
        productive_apply_authorized=True,
        runtime_apply_authority=RUNTIME_APPLY_AUTHORITY_VALUE,
        configuration_after_apply=applied_config,
        owner_apply_authorization_record_digest=apply_digest,
        apply_ledger_entry_digest=str(ledger_entry.get("apply_ledger_entry_digest") or ""),
    )


__all__ = [
    "DECISION_CONFIG",
    "F1M9ScopedOwnerApplyAdjudicationRequestV1",
    "F1M9ScopedOwnerApplyAdjudicationResultV1",
    "OWNER_POLICY_DECISION_CONFIG",
    "NORMATIVE_SPEC",
    "ProductiveApplyAdjudicationStatusV1",
    "RUNTIME_APPLY_AUTHORITY_VALUE",
    "SCHEMA_VERSION",
    "STATUS_APPLY_AUTHORIZED",
    "STATUS_DENIED",
    "WORKPACKAGE_ID",
    "evaluate_f1_m9_scoped_owner_productive_apply_v1",
    "transition_configuration_for_valid_apply_v1",
]
